"""add_nse_market_support

Revision ID: d21a5db05206
Revises: ab64e6ee03b7
Create Date: 2026-05-16 12:10:31.428286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd21a5db05206'
down_revision: Union[str, Sequence[str], None] = 'ab64e6ee03b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add NSE market support."""
    # Add new columns to stock_symbols table
    op.add_column('stock_symbols', sa.Column('market', sa.String(), nullable=False, server_default='US'))
    op.add_column('stock_symbols', sa.Column('currency', sa.String(), nullable=False, server_default='USD'))
    op.add_column('stock_symbols', sa.Column('base_symbol', sa.String(), nullable=True))
    op.create_index('ix_stock_symbols_market', 'stock_symbols', ['market'])
    
    # Add new columns to stock_data table
    op.add_column('stock_data', sa.Column('market', sa.String(), nullable=False, server_default='US'))
    op.add_column('stock_data', sa.Column('currency', sa.String(), nullable=False, server_default='USD'))
    op.create_index('ix_stock_data_market', 'stock_data', ['market'])
    
    # Add new columns to news_articles table
    op.add_column('news_articles', sa.Column('market', sa.String(), nullable=False, server_default='US'))
    op.add_column('news_articles', sa.Column('language', sa.String(), nullable=False, server_default='en'))
    op.create_index('ix_news_articles_market', 'news_articles', ['market'])
    
    # Create data_quality_metrics table
    op.create_table(
        'data_quality_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('error_type', sa.String(), nullable=False),
        sa.Column('error_details', sa.String(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('market', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['symbol_id'], ['stock_symbols.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dqm_symbol_date', 'data_quality_metrics', ['symbol_id', 'recorded_at'])
    
    # Create nse_holidays table
    op.create_table(
        'nse_holidays',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_recurring', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index('ix_nse_holidays_date', 'nse_holidays', ['date'])


def downgrade() -> None:
    """Downgrade schema to remove NSE market support."""
    # Drop nse_holidays table
    op.drop_index('ix_nse_holidays_date', 'nse_holidays')
    op.drop_table('nse_holidays')
    
    # Drop data_quality_metrics table
    op.drop_index('ix_dqm_symbol_date', 'data_quality_metrics')
    op.drop_table('data_quality_metrics')
    
    # Remove columns from news_articles table
    op.drop_index('ix_news_articles_market', 'news_articles')
    op.drop_column('news_articles', 'language')
    op.drop_column('news_articles', 'market')
    
    # Remove columns from stock_data table
    op.drop_index('ix_stock_data_market', 'stock_data')
    op.drop_column('stock_data', 'currency')
    op.drop_column('stock_data', 'market')
    
    # Remove columns from stock_symbols table
    op.drop_index('ix_stock_symbols_market', 'stock_symbols')
    op.drop_column('stock_symbols', 'base_symbol')
    op.drop_column('stock_symbols', 'currency')
    op.drop_column('stock_symbols', 'market')
