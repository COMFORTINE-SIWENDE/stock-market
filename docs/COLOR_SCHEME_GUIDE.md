# Color Scheme & Design Guide

## 🎨 Color Palette

### Primary Colors

```
Card Background:    #e1e6e8  ████████  (Light Gray)
Button Primary:     #2baff7  ████████  (Bright Blue)
Button Hover:       #1a9de6  ████████  (Darker Blue)
Text Dark:          #000000  ████████  (Black)
Text Light:         #ffffff  ████████  (White)
Background:         #ffffff  ████████  (White)
```

### Accent Colors

```
Success:            #10b981  ████████  (Green)
Warning:            #f59e0b  ████████  (Orange)
Danger:             #ef4444  ████████  (Red)
```

---

## 🔘 Button Styles

### Fully Rounded Buttons
All buttons use `border-radius: 9999px` for perfect circles on the ends.

```css
.btn {
  border-radius: 9999px;  /* Fully rounded */
  padding: 0.75rem 1.5rem;
}
```

### Button Variants

**Primary Button** (Blue)
```html
<button class="btn btn-primary">
  <span class="icon">🚀</span> Primary Action
</button>
```
Color: #2baff7 (bright blue)

**Secondary Button** (Gray)
```html
<button class="btn btn-secondary">
  <span class="icon">⚙️</span> Secondary Action
</button>
```
Color: #e1e6e8 (light gray)

**Success Button** (Green)
```html
<button class="btn btn-success">
  <span class="icon">✅</span> Success Action
</button>
```
Color: #10b981 (green)

**Warning Button** (Orange)
```html
<button class="btn btn-warning">
  <span class="icon">⚠️</span> Warning Action
</button>
```
Color: #f59e0b (orange)

**Danger Button** (Red)
```html
<button class="btn btn-danger">
  <span class="icon">❌</span> Danger Action
</button>
```
Color: #ef4444 (red)

---

## 🎴 Card Styles

### Standard Card
```html
<div class="card">
  <div class="card-header">
    <span class="icon">📊</span> Card Title
  </div>
  <div class="card-body">
    Content goes here
  </div>
</div>
```

**Styling:**
- Background: #e1e6e8 (light gray)
- Border Radius: 16px
- Shadow: 0 4px 6px rgba(0, 0, 0, 0.1)
- Hover: Lifts up with larger shadow

### Stat Card
```html
<div class="stat-card">
  <div class="stat-icon">📈</div>
  <div class="stat-value">95%</div>
  <div class="stat-label">Accuracy</div>
</div>
```

**Styling:**
- Background: #e1e6e8 (light gray)
- Text Align: Center
- Hover: Lifts up 4px

---

## 📝 Form Elements

### Input Fields
```html
<input type="text" class="form-input" placeholder="Enter text">
```

**Styling:**
- Border: 2px solid #e1e6e8
- Border Radius: 9999px (fully rounded)
- Focus: Border changes to #2baff7 (blue)
- Background: #ffffff (white)

### Select Dropdowns
```html
<select class="form-select">
  <option>Option 1</option>
  <option>Option 2</option>
</select>
```

**Styling:**
- Same as input fields
- Fully rounded borders

---

## 🏷️ Badges

### Badge Variants
```html
<span class="badge badge-primary">Primary</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-danger">Danger</span>
```

**Styling:**
- Border Radius: 9999px (fully rounded)
- Padding: 0.25rem 0.75rem
- Font Size: 0.875rem

---

## 🎯 Icons

### Emoji Icons Used

```
📈 - Stock/Chart (Brand Logo)
🏠 - Home
🔐 - Login/Security
✨ - Register/New
📊 - Dashboard/Analytics
💹 - Stocks
🔮 - Predictions
📰 - Sentiment/News
📜 - History
👤 - Profile/User
🚪 - Logout
🚀 - Action/Submit
📥 - Download/Collect
⚡ - Quick/Fast
🍎 - Apple (AAPL)
🪟 - Microsoft (MSFT)
🔍 - Google (GOOGL)
⚡ - Tesla (TSLA)
✅ - Success
❌ - Error
⚠️ - Warning
ℹ️ - Info
📧 - Email
🔒 - Password
✍️ - Name/Text
💰 - Price/Money
📈 - Trend Up
📉 - Trend Down
🤖 - AI/Machine Learning
💡 - Idea/Interpretation
⚙️ - Settings/Config
```

---

## 📐 Layout Grid

### Grid System
```html
<!-- 2 Columns -->
<div class="grid grid-2">
  <div>Column 1</div>
  <div>Column 2</div>
</div>

<!-- 3 Columns -->
<div class="grid grid-3">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>

<!-- 4 Columns -->
<div class="grid grid-4">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
  <div>Column 4</div>
</div>
```

**Responsive:**
- Desktop: Multiple columns
- Tablet: 2 columns
- Mobile: 1 column (stacked)

---

## 🎨 Typography

### Headings
```css
Page Title:     2rem (32px), Bold
Page Subtitle:  1.125rem (18px), Normal
Card Header:    1.25rem (20px), Bold
Body Text:      1rem (16px), Normal
Small Text:     0.875rem (14px), Normal
```

### Font Family
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
             Roboto, 'Helvetica Neue', Arial, sans-serif;
```

---

## 🌈 Color Usage Guidelines

### When to Use Each Color

**Primary Blue (#2baff7)**
- Main action buttons
- Active navigation items
- Links
- Primary badges
- Focus states

**Gray (#e1e6e8)**
- Card backgrounds
- Secondary buttons
- Disabled states
- Borders
- Subtle backgrounds

**Black (#000000)**
- Main text
- Headings
- Labels
- Important information

**White (#ffffff)**
- Page background
- Button text (on colored buttons)
- Card text backgrounds

**Green (#10b981)**
- Success messages
- Positive trends
- Confirmation actions
- Success badges

**Orange (#f59e0b)**
- Warning messages
- Caution indicators
- Warning badges

**Red (#ef4444)**
- Error messages
- Negative trends
- Destructive actions
- Danger badges

---

## 📱 Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 768px) {
  /* Single column layouts */
  /* Stacked navigation */
  /* Larger touch targets */
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1199px) {
  /* 2-column layouts */
  /* Compact navigation */
}

/* Desktop */
@media (min-width: 1200px) {
  /* Multi-column layouts */
  /* Full navigation */
}
```

---

## ✨ Animations

### Hover Effects
```css
/* Buttons */
.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

/* Cards */
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

/* Stat Cards */
.stat-card:hover {
  transform: translateY(-4px);
}
```

### Transitions
```css
transition: all 0.3s ease;
```

---

## 🎯 Design Principles

### 1. Consistency
- All buttons fully rounded
- Consistent spacing (0.5rem, 1rem, 1.5rem, 2rem)
- Uniform card styling
- Same icon style throughout

### 2. Clarity
- Clear visual hierarchy
- Obvious interactive elements
- Descriptive labels
- Helpful error messages

### 3. Simplicity
- Clean, uncluttered layouts
- Minimal color palette
- Straightforward navigation
- Easy-to-understand icons

### 4. Responsiveness
- Works on all screen sizes
- Touch-friendly on mobile
- Readable text sizes
- Appropriate spacing

---

## 📋 Component Checklist

When creating new components, ensure:

- [ ] Buttons are fully rounded (border-radius: 9999px)
- [ ] Cards use #e1e6e8 background
- [ ] Primary actions use #2baff7 blue
- [ ] Icons are emoji-based
- [ ] Text is black or white
- [ ] Hover effects are smooth
- [ ] Responsive on mobile
- [ ] Consistent spacing
- [ ] Clear labels
- [ ] Accessible

---

## 🎨 Quick Reference

```css
/* Colors */
--card-bg: #e1e6e8;
--button-primary: #2baff7;
--text-dark: #000000;
--text-light: #ffffff;
--bg-white: #ffffff;

/* Border Radius */
--border-radius: 9999px;  /* Fully rounded */
--card-radius: 16px;      /* Card corners */

/* Shadows */
--shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

/* Spacing */
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
```

---

**Design System Complete!** 🎨✨

All components follow this consistent design language for a cohesive, professional appearance.
