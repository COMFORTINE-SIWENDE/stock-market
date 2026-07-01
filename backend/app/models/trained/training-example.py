# %% [markdown]
# # CBC Disease Classifier — Model 2: Hierarchical Disease Classifier
#
# Standalone script. Loads data, builds and trains the hierarchical
# multi-task classifier, evaluates, and saves all artifacts.

# %%
# ==================== IMPORTS & SETUP ====================

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR    = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
DATA_PATH  = os.path.join(_BASE_DIR, "data", "kenyan_medical_claims_20260314_002641.csv")
MODEL_DIR  = os.path.join(_BASE_DIR, "models")
PLOTS_DIR  = os.path.join(_BASE_DIR, "visualizations", "plots")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

TEST_MODE = False

print("=" * 60)
print("  CBC Disease Classifier — Model 2")
print("=" * 60)
print(f"  TensorFlow : {tf.__version__}")
print(f"  Data       : {DATA_PATH}")
print(f"  Models dir : {MODEL_DIR}")
print(f"  Plots dir  : {PLOTS_DIR}")
print("=" * 60)

# %%
# ==================== LOAD DATA ====================

print("\n📂 Loading dataset...")
df = pd.read_csv(DATA_PATH)
df['date'] = pd.to_datetime(df['date'])
df = df.dropna(subset=['disease_category', 'diagnosis']).reset_index(drop=True)

print(f"  Total claims  : {len(df):,}")
print(f"  Categories    : {df['disease_category'].nunique()} → {df['disease_category'].unique().tolist()}")
print(f"  Diagnoses     : {df['diagnosis'].nunique()}")
print(f"  Fraud rate    : {df['is_fraud'].mean():.1%}")

# %%
# ==================== FEATURE DEFINITION ====================

LAB_FEATURES  = ['HGB', 'HCT', 'MCV', 'MCHC', 'NEU', 'LYM', 'EOS', 'BAS', 'MON', 'PLT']
ALL_FEATURES  = LAB_FEATURES          # extend here if adding demographics
N_FEATURES    = len(ALL_FEATURES)

X_raw = df[ALL_FEATURES].values

print(f"\n  Input features ({N_FEATURES}): {ALL_FEATURES}")

# %% [markdown]
# ## 6. Model 2: Hierarchical Disease Classifier
# 
# ### Objective
# - Predict both disease category and specific diagnosis from lab values
# - Input: Same 12 features as Model 1
# - Output: 
#   - Primary: Disease category (4 classes)
#   - Secondary: Specific diagnosis (multiple classes per category)
# - Mismatch score: Combined measure of how well labs match claimed diagnosis

# %%
# ==================== MODEL 2 DATA PREPARATION ====================

# Display the hierarchical structure
print("📊 Disease Hierarchy:")
print("\nCategories and their diagnoses:")
for category in df['disease_category'].unique():
    diagnoses = df[df['disease_category'] == category]['diagnosis'].unique()
    print(f"\n  {category} ({len(diagnoses)} diagnoses):")
    for diag in diagnoses[:5]:  # Show first 5
        print(f"    - {diag}")
    if len(diagnoses) > 5:
        print(f"    ... and {len(diagnoses)-5} more")

# %%
# ==================== ENCODE TARGET VARIABLES ====================

# 1. Encode disease category (primary task)
category_encoder = LabelEncoder()
y_category = category_encoder.fit_transform(df['disease_category'])
NUM_CATEGORIES = len(category_encoder.classes_)

# One-hot encode for loss function
y_category_onehot = tf.keras.utils.to_categorical(y_category, num_classes=NUM_CATEGORIES)

print(f"\n🎯 Primary task: Disease Categories ({NUM_CATEGORIES})")
for i, cat in enumerate(category_encoder.classes_):
    count = (df['disease_category'] == cat).sum()
    print(f"  {i}: {cat} ({count:,} samples, {count/len(df):.1%})")

# 2. Encode specific diagnosis (secondary task)
# We need to handle that diagnoses belong to specific categories
diagnosis_encoder = LabelEncoder()
y_diagnosis = diagnosis_encoder.fit_transform(df['diagnosis'])
NUM_DIAGNOSES = len(diagnosis_encoder.classes_)

# Create diagnosis to category mapping
diagnosis_to_category = {}
for diagnosis in df['diagnosis'].unique():
    category = df[df['diagnosis'] == diagnosis]['disease_category'].iloc[0]
    diagnosis_to_category[diagnosis] = category

# Validate that all diagnoses map correctly
print(f"\n🎯 Secondary task: Specific Diagnoses ({NUM_DIAGNOSES})")
print(f"  Sample diagnoses with their categories:")
for diagnosis in df['diagnosis'].unique()[:10]:
    category = diagnosis_to_category[diagnosis]
    print(f"    {diagnosis} → {category}")

# %%
# ==================== FEATURE SCALING ====================

# Use StandardScaler for classifier (better for neural networks)
scaler_model2 = StandardScaler()
X2_scaled = scaler_model2.fit_transform(X_raw)  # X_raw from earlier (ALL_FEATURES)

# Save scaler
scaler2_path = os.path.join(MODEL_DIR, "model2_scaler.pkl")
joblib.dump(scaler_model2, scaler2_path)
print(f"\n✅ Scaler saved to {scaler2_path}")

# %%
# ==================== TRAIN/VAL/TEST SPLIT ====================

# Split data (maintain stratification on category)
X2_train, X2_temp, y_cat_train, y_cat_temp, y_diag_train, y_diag_temp = train_test_split(
    X2_scaled, y_category_onehot, y_diagnosis, 
    test_size=0.3, random_state=RANDOM_SEED, stratify=y_category
)

X2_val, X2_test, y_cat_val, y_cat_test, y_diag_val, y_diag_test = train_test_split(
    X2_temp, y_cat_temp, y_diag_temp,
    test_size=0.5, random_state=RANDOM_SEED, stratify=np.argmax(y_cat_temp, axis=1)
)

print(f"Train set: {X2_train.shape}")
print(f"Validation set: {X2_val.shape}")
print(f"Test set: {X2_test.shape}")

print(f"\nCategory distribution in train set:")
train_cats = np.argmax(y_cat_train, axis=1)
for i, cat in enumerate(category_encoder.classes_):
    print(f"  {cat}: {(train_cats == i).mean():.2%}")

# %%
# ==================== BUILD HIERARCHICAL CLASSIFIER ====================

def build_hierarchical_classifier(input_dim, num_categories, num_diagnoses, diagnosis_to_cat_map):
    """
    Build a neural network with:
    - Shared layers for feature extraction
    - Category prediction head
    - Diagnosis prediction head (with category-aware masking)
    """
    
    # Input layer
    inputs = layers.Input(shape=(input_dim,), name='input')
    
    # Shared feature extraction layers
    x = layers.Dense(128, activation='relu', name='shared_dense1')(inputs)
    x = layers.BatchNormalization(name='shared_bn1')(x)
    x = layers.Dropout(0.3, name='shared_dropout1')(x)
    
    x = layers.Dense(64, activation='relu', name='shared_dense2')(x)
    x = layers.BatchNormalization(name='shared_bn2')(x)
    x = layers.Dropout(0.3, name='shared_dropout2')(x)
    
    x = layers.Dense(32, activation='relu', name='shared_dense3')(x)
    x = layers.BatchNormalization(name='shared_bn3')(x)
    
    # ===== TASK 1: Category Prediction =====
    category_features = layers.Dropout(0.2, name='category_dropout')(x)
    category_output = layers.Dense(num_categories, activation='softmax', name='category_output')(category_features)
    
    # ===== TASK 2: Diagnosis Prediction =====
    # Additional layers specific to diagnosis
    diagnosis_features = layers.Dense(48, activation='relu', name='diagnosis_dense1')(x)
    diagnosis_features = layers.BatchNormalization(name='diagnosis_bn1')(diagnosis_features)
    diagnosis_features = layers.Dropout(0.3, name='diagnosis_dropout1')(diagnosis_features)
    
    diagnosis_features = layers.Dense(32, activation='relu', name='diagnosis_dense2')(diagnosis_features)
    diagnosis_features = layers.BatchNormalization(name='diagnosis_bn2')(diagnosis_features)
    
    # Diagnosis output (full softmax over all diagnoses)
    diagnosis_output = layers.Dense(num_diagnoses, activation='softmax', name='diagnosis_output')(diagnosis_features)
    
    # Create model
    model = models.Model(
        inputs=inputs, 
        outputs=[category_output, diagnosis_output],
        name='hierarchical_disease_classifier'
    )
    
    return model

# Build model
model2 = build_hierarchical_classifier(
    N_FEATURES, 
    NUM_CATEGORIES, 
    NUM_DIAGNOSES,
    diagnosis_to_category
)

# %%
# ==================== CUSTOM LOSS WEIGHTS ====================

# We can weight the losses to prioritize category prediction
# or balance them based on task difficulty
loss_weights = {
    'category_output': 0.4,    # 40% weight on category
    'diagnosis_output': 0.6     # 60% weight on diagnosis
}

# Compile with multiple losses
model2.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss={
        'category_output': 'categorical_crossentropy',
        'diagnosis_output': 'sparse_categorical_crossentropy'  # Use sparse because y_diag_train is integer-encoded
    },
    loss_weights=loss_weights,
    metrics={
        'category_output': ['accuracy', tf.keras.metrics.AUC(name='auc')],
        'diagnosis_output': ['accuracy']
    }
)

model2.summary()

# Plot model architecture
try:
    tf.keras.utils.plot_model(
        model2,
        to_file=os.path.join(PLOTS_DIR, "model2_architecture.png"),
        show_shapes=True,
        show_layer_names=True,
        dpi=100
    )
    print(f"\n✅ Model architecture saved to {PLOTS_DIR}/model2_architecture.png")
except Exception as e:
    print(f"\n⚠️  plot_model skipped (pydot/graphviz not available): {e}")

# %%
# ==================== TRAIN HIERARCHICAL CLASSIFIER ====================

# Training parameters
EPOCHS_CLF = 20 if TEST_MODE else 50
BATCH_SIZE_CLF = 32 if TEST_MODE else 256

# Callbacks
model2_path = os.path.join(MODEL_DIR, "model2_hierarchical_classifier.keras")

callbacks2 = [
    tf.keras.callbacks.ModelCheckpoint(
        model2_path,
        monitor='val_category_output_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=1e-6,
        verbose=1
    ),
    tf.keras.callbacks.CSVLogger(
        os.path.join(MODEL_DIR, "model2_training_log.csv")
    )
]

print("\n🚀 Starting Model 2 (Hierarchical Classifier) training...\n")
history2 = model2.fit(
    X2_train, 
    {
        'category_output': y_cat_train,
        'diagnosis_output': y_diag_train
    },
    validation_data=(
        X2_val,
        {
            'category_output': y_cat_val,
            'diagnosis_output': y_diag_val
        }
    ),
    epochs=EPOCHS_CLF,
    batch_size=BATCH_SIZE_CLF,
    callbacks=callbacks2,
    verbose=1,
    shuffle=True
)

print(f"\n✅ Model 2 training complete!")
print(f"Best val_category_accuracy: {max(history2.history['val_category_output_accuracy']):.4f}")
print(f"Best val_diagnosis_accuracy: {max(history2.history['val_diagnosis_output_accuracy']):.4f}")

# %%
# ==================== PLOT HIERARCHICAL TRAINING ====================

fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1. Total Loss
ax = axes[0, 0]
ax.plot(history2.history['loss'], label='Training Loss', linewidth=2)
ax.plot(history2.history['val_loss'], label='Validation Loss', linewidth=2)
ax.set_xlabel('Epoch')
ax.set_ylabel('Loss')
ax.set_title('Total Loss')
ax.legend()
ax.grid(True, alpha=0.3)

# 2. Category Accuracy
ax = axes[0, 1]
ax.plot(history2.history['category_output_accuracy'], label='Training', linewidth=2)
ax.plot(history2.history['val_category_output_accuracy'], label='Validation', linewidth=2)
best_cat_epoch = np.argmax(history2.history['val_category_output_accuracy'])
ax.scatter(best_cat_epoch, history2.history['val_category_output_accuracy'][best_cat_epoch], 
          color='red', s=100, zorder=5, 
          label=f'Best: {history2.history["val_category_output_accuracy"][best_cat_epoch]:.3f}')
ax.set_xlabel('Epoch')
ax.set_ylabel('Accuracy')
ax.set_title('Category Prediction Accuracy')
ax.legend()
ax.grid(True, alpha=0.3)

# 3. Diagnosis Accuracy
ax = axes[1, 0]
ax.plot(history2.history['diagnosis_output_accuracy'], label='Training', linewidth=2)
ax.plot(history2.history['val_diagnosis_output_accuracy'], label='Validation', linewidth=2)
best_diag_epoch = np.argmax(history2.history['val_diagnosis_output_accuracy'])
ax.scatter(best_diag_epoch, history2.history['val_diagnosis_output_accuracy'][best_diag_epoch], 
          color='red', s=100, zorder=5,
          label=f'Best: {history2.history["val_diagnosis_output_accuracy"][best_diag_epoch]:.3f}')
ax.set_xlabel('Epoch')
ax.set_ylabel('Accuracy')
ax.set_title('Diagnosis Prediction Accuracy')
ax.legend()
ax.grid(True, alpha=0.3)

# 4. Category AUC
ax = axes[1, 1]
ax.plot(history2.history['category_output_auc'], label='Training AUC', linewidth=2)
ax.plot(history2.history['val_category_output_auc'], label='Validation AUC', linewidth=2)
best_auc_epoch = np.argmax(history2.history['val_category_output_auc'])
ax.scatter(best_auc_epoch, history2.history['val_category_output_auc'][best_auc_epoch], 
          color='red', s=100, zorder=5,
          label=f'Best: {history2.history["val_category_output_auc"][best_auc_epoch]:.3f}')
ax.set_xlabel('Epoch')
ax.set_ylabel('AUC')
ax.set_title('Category Prediction AUC')
ax.legend()
ax.grid(True, alpha=0.3)

plt.suptitle('Model 2: Hierarchical Classifier Training History', fontsize=14, fontweight='bold')
plt.tight_layout()

# Save
plot_path = os.path.join(PLOTS_DIR, "model2_training_history.png")
plt.savefig(plot_path, dpi=100, bbox_inches='tight')
plt.close()
print(f"✅ Plot saved to {plot_path}")

# %%
# ==================== EVALUATE HIERARCHICAL CLASSIFIER ====================

# Predict on test set
y_pred_cat_proba, y_pred_diag_proba = model2.predict(X2_test, verbose=0)
y_pred_cat = np.argmax(y_pred_cat_proba, axis=1)
y_pred_diag = np.argmax(y_pred_diag_proba, axis=1)

y_true_cat = np.argmax(y_cat_test, axis=1)
y_true_diag = y_diag_test

# ===== Category Evaluation =====
print("\n" + "="*60)
print("📊 CATEGORY PREDICTION EVALUATION")
print("="*60)
print("\nClassification Report:")
print(classification_report(y_true_cat, y_pred_cat, target_names=category_encoder.classes_))

# Category confusion matrix
cm_cat = confusion_matrix(y_true_cat, y_pred_cat)
plt.figure(figsize=(8, 6))
sns.heatmap(cm_cat, annot=True, fmt='d', cmap='Blues', 
            xticklabels=category_encoder.classes_, 
            yticklabels=category_encoder.classes_)
plt.title('Model 2: Category Confusion Matrix')
plt.ylabel('True Category')
plt.xlabel('Predicted Category')
plt.tight_layout()

# Save
plot_path = os.path.join(PLOTS_DIR, "model2_category_confusion.png")
plt.savefig(plot_path, dpi=100, bbox_inches='tight')
plt.close()
print(f"✅ Category plot saved to {plot_path}")

# ===== Diagnosis Evaluation =====
print("\n" + "="*60)
print("📊 DIAGNOSIS PREDICTION EVALUATION")
print("="*60)
print(f"Overall Diagnosis Accuracy: {np.mean(y_pred_diag == y_true_diag):.4f}")

# Per-category diagnosis accuracy
print("\nDiagnosis Accuracy by Category:")
for category in category_encoder.classes_:
    # Get indices where true category is this category
    cat_indices = np.where(y_true_cat == category_encoder.transform([category])[0])[0]
    if len(cat_indices) > 0:
        cat_diag_accuracy = np.mean(y_pred_diag[cat_indices] == y_true_diag[cat_indices])
        print(f"  {category}: {cat_diag_accuracy:.4f} ({len(cat_indices)} samples)")

# Show top diagnoses by frequency
print("\nTop 10 Most Common Diagnoses:")
diagnosis_counts = pd.Series(y_true_diag).value_counts().head(10)
for idx in diagnosis_counts.index:
    diagnosis_name = diagnosis_encoder.inverse_transform([idx])[0]
    category = diagnosis_to_category[diagnosis_name]
    accuracy = np.mean((y_pred_diag == y_true_diag) & (y_true_diag == idx))
    print(f"  {diagnosis_name} ({category}): {accuracy:.4f} ({diagnosis_counts[idx]} samples)")

# %%
# ==================== CONFUSION MATRIX FOR TOP DIAGNOSES ====================

# Get top N diagnoses for visualization
TOP_N = 15
top_diagnosis_indices = np.argsort(-pd.Series(y_true_diag).value_counts())[:TOP_N].index
top_diagnosis_names = diagnosis_encoder.inverse_transform(top_diagnosis_indices)

# Filter test set to these diagnoses
mask = np.isin(y_true_diag, top_diagnosis_indices)
y_true_top = y_true_diag[mask]
y_pred_top = y_pred_diag[mask]

# Map indices to 0..TOP_N-1 for plotting
idx_map = {orig: new for new, orig in enumerate(top_diagnosis_indices)}
# Keep only samples where BOTH true and pred are in top-N
both_in_top = np.array([y in idx_map and p in idx_map for y, p in zip(y_true_top, y_pred_top)])
y_true_mapped = np.array([idx_map[y] for y in y_true_top[both_in_top]])
y_pred_mapped = np.array([idx_map[p] for p in y_pred_top[both_in_top]])

# Create confusion matrix
cm_diag = confusion_matrix(y_true_mapped, y_pred_mapped, labels=range(TOP_N))

plt.figure(figsize=(14, 12))
sns.heatmap(cm_diag, annot=True, fmt='d', cmap='Blues',
            xticklabels=[f"{name[:20]}..." for name in top_diagnosis_names],
            yticklabels=[f"{name[:20]}..." for name in top_diagnosis_names])
plt.title(f'Model 2: Top {TOP_N} Diagnoses Confusion Matrix')
plt.ylabel('True Diagnosis')
plt.xlabel('Predicted Diagnosis')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()

# Save
plot_path = os.path.join(PLOTS_DIR, "model2_diagnosis_confusion_top15.png")
plt.savefig(plot_path, dpi=100, bbox_inches='tight')
plt.close()
print(f"✅ Diagnosis plot saved to {plot_path}")

# %%
# ==================== HIERARCHICAL ACCURACY METRICS ====================

# Compute hierarchical accuracy metrics
print("\n" + "="*60)
print("📊 HIERARCHICAL ACCURACY METRICS")
print("="*60)

# 1. Exact match (both category and diagnosis correct)
exact_match = (y_pred_cat == y_true_cat) & (y_pred_diag == y_true_diag)
exact_match_rate = np.mean(exact_match)
print(f"Exact Match Rate (category + diagnosis): {exact_match_rate:.4f}")

# 2. Category correct, diagnosis wrong
cat_correct_diag_wrong = (y_pred_cat == y_true_cat) & (y_pred_diag != y_true_diag)
cat_correct_rate = np.mean(cat_correct_diag_wrong)
print(f"Category Correct but Diagnosis Wrong: {cat_correct_rate:.4f}")

# 3. Category wrong
cat_wrong_rate = np.mean(y_pred_cat != y_true_cat)
print(f"Category Wrong: {cat_wrong_rate:.4f}")

# 4. Within-category diagnosis accuracy (when category is correct)
within_cat_acc = np.sum(exact_match) / np.sum(y_pred_cat == y_true_cat) if np.sum(y_pred_cat == y_true_cat) > 0 else 0
print(f"Within-Category Diagnosis Accuracy: {within_cat_acc:.4f}")

# 5. Confusion matrix of category errors
print("\nCategory Error Patterns:")
for i, true_cat in enumerate(category_encoder.classes_):
    true_indices = np.where(y_true_cat == i)[0]
    if len(true_indices) > 0:
        pred_for_this_cat = y_pred_cat[true_indices]
        print(f"\n  True: {true_cat}")
        for j, pred_cat in enumerate(category_encoder.classes_):
            if i != j:
                count = np.sum(pred_for_this_cat == j)
                if count > 0:
                    pct = count / len(true_indices) * 100
                    print(f"    → Predicted as {pred_cat}: {count} ({pct:.1f}%)")

# %%
# ==================== MISMATCH SCORE CALCULATION ====================

def calculate_mismatch_score(y_true_cat, y_true_diag, y_pred_cat_proba, y_pred_diag_proba, 
                             category_encoder, diagnosis_encoder, diagnosis_to_category):
    """
    Calculate mismatch score for a claim:
    - Low if predicted category/diagnosis matches claimed
    - High if there's a mismatch
    """
    # Get predicted class indices
    pred_cat_idx = np.argmax(y_pred_cat_proba)
    pred_diag_idx = np.argmax(y_pred_diag_proba)
    
    # Get predicted names
    pred_cat = category_encoder.inverse_transform([pred_cat_idx])[0]
    pred_diag = diagnosis_encoder.inverse_transform([pred_diag_idx])[0]
    
    # True names
    true_cat = category_encoder.inverse_transform([y_true_cat])[0]
    true_diag = diagnosis_encoder.inverse_transform([y_true_diag])[0]
    
    # Category match score
    cat_match_score = 0 if pred_cat == true_cat else 1
    
    # Diagnosis match score
    diag_match_score = 0 if pred_diag == true_diag else 1
    
    # Check if predicted diagnosis belongs to true category
    pred_diag_category = diagnosis_to_category[pred_diag]
    category_consistency_score = 0 if pred_diag_category == true_cat else 1
    
    # Combined mismatch score (weighted)
    mismatch_score = (
        0.4 * cat_match_score + 
        0.4 * diag_match_score + 
        0.2 * category_consistency_score
    )
    
    return {
        'mismatch_score': mismatch_score,
        'cat_match': cat_match_score,
        'diag_match': diag_match_score,
        'category_consistency': category_consistency_score,
        'true_category': true_cat,
        'true_diagnosis': true_diag,
        'predicted_category': pred_cat,
        'predicted_diagnosis': pred_diag,
        'predicted_diagnosis_category': pred_diag_category,
        'category_confidence': float(y_pred_cat_proba[pred_cat_idx]),
        'diagnosis_confidence': float(y_pred_diag_proba[pred_diag_idx])
    }

# Test on a few samples
print("\n" + "="*60)
print("📊 MISMATCH SCORE EXAMPLES")
print("="*60)

for i in range(min(5, len(X2_test))):
    result = calculate_mismatch_score(
        y_true_cat[i], y_true_diag[i],
        y_pred_cat_proba[i], y_pred_diag_proba[i],
        category_encoder, diagnosis_encoder, diagnosis_to_category
    )
    
    print(f"\nSample {i+1}:")
    print(f"  True: {result['true_category']} → {result['true_diagnosis']}")
    print(f"  Pred: {result['predicted_category']} → {result['predicted_diagnosis']} "
          f"(category: {result['predicted_diagnosis_category']})")
    print(f"  Mismatch Score: {result['mismatch_score']:.3f}")
    print(f"    - Category Match: {'✓' if result['cat_match']==0 else '✗'}")
    print(f"    - Diagnosis Match: {'✓' if result['diag_match']==0 else '✗'}")
    print(f"    - Category Consistency: {'✓' if result['category_consistency']==0 else '✗'}")

# %%
# ==================== SAVE MODEL 2 METADATA ====================

# Create diagnosis-to-category mapping for inference
diagnosis_to_category_map = {}
for diagnosis in diagnosis_encoder.classes_:
    category = diagnosis_to_category[diagnosis]
    diagnosis_to_category_map[diagnosis] = category

metadata2 = {
    'model_name': 'Model 2: Hierarchical Disease Classifier',
    'model_type': 'multi_task_neural_network',
    'input_dim': N_FEATURES,
    'feature_names': ALL_FEATURES,
    'num_categories': NUM_CATEGORIES,
    'category_names': category_encoder.classes_.tolist(),
    'num_diagnoses': NUM_DIAGNOSES,
    'diagnosis_names': diagnosis_encoder.classes_.tolist(),
    'diagnosis_to_category': diagnosis_to_category_map,
    'loss_weights': loss_weights,
    'train_size': len(X2_train),
    'val_size': len(X2_val),
    'test_size': len(X2_test),
    'best_val_category_accuracy': float(max(history2.history['val_category_output_accuracy'])),
    'best_val_diagnosis_accuracy': float(max(history2.history['val_diagnosis_output_accuracy'])),
    'best_val_category_auc': float(max(history2.history['val_category_output_auc'])),
    'test_category_accuracy': float(np.mean(y_pred_cat == y_true_cat)),
    'test_diagnosis_accuracy': float(np.mean(y_pred_diag == y_true_diag)),
    'test_exact_match_rate': float(exact_match_rate),
    'training_date': datetime.now().isoformat(),
    'epochs_trained': len(history2.history['loss']),
    'batch_size': BATCH_SIZE_CLF,
    'learning_rate': 0.001
}

# Save metadata
meta2_path = os.path.join(MODEL_DIR, "model2_hierarchical_classifier_meta.json")
with open(meta2_path, 'w') as f:
    json.dump(metadata2, f, indent=2)

# Save encoders
category_encoder_path = os.path.join(MODEL_DIR, "model2_category_encoder.pkl")
diagnosis_encoder_path = os.path.join(MODEL_DIR, "model2_diagnosis_encoder.pkl")
joblib.dump(category_encoder, category_encoder_path)
joblib.dump(diagnosis_encoder, diagnosis_encoder_path)

print(f"✅ Model 2 saved to: {model2_path}")
print(f"✅ Metadata saved to: {meta2_path}")
print(f"✅ Category encoder saved to: {category_encoder_path}")
print(f"✅ Diagnosis encoder saved to: {diagnosis_encoder_path}")

# %%
# ==================== TEST MODEL 2 LOADING ====================

print("\n🔍 Testing Model 2 loading and inference...")

# Load model
loaded_model2 = tf.keras.models.load_model(model2_path)
print("✅ Model 2 loaded successfully")

# Load metadata
with open(meta2_path, 'r') as f:
    loaded_meta2 = json.load(f)
print("✅ Metadata loaded successfully")

# Load scaler and encoders
loaded_scaler2 = joblib.load(scaler2_path)
loaded_category_encoder = joblib.load(category_encoder_path)
loaded_diagnosis_encoder = joblib.load(diagnosis_encoder_path)
print("✅ Scaler and encoders loaded successfully")

# Test prediction
test_samples2 = X2_scaled[:5]
cat_proba, diag_proba = loaded_model2.predict(test_samples2, verbose=0)

print(f"\n📊 Test inference:")
print(f"  Input shape: {test_samples2.shape}")
print(f"  Category output shape: {cat_proba.shape}")
print(f"  Diagnosis output shape: {diag_proba.shape}")

for i in range(5):
    pred_cat_idx = np.argmax(cat_proba[i])
    pred_diag_idx = np.argmax(diag_proba[i])
    pred_cat = loaded_category_encoder.inverse_transform([pred_cat_idx])[0]
    pred_diag = loaded_diagnosis_encoder.inverse_transform([pred_diag_idx])[0]
    print(f"\n  Sample {i+1}:")
    print(f"    Predicted category: {pred_cat} (confidence: {cat_proba[i][pred_cat_idx]:.3f})")
    print(f"    Predicted diagnosis: {pred_diag} (confidence: {diag_proba[i][pred_diag_idx]:.3f})")