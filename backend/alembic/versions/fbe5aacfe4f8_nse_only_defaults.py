"""nse_only_defaults

Revision ID: fbe5aacfe4f8
Revises: d21a5db05206
Create Date: 2026-06-19 16:53:05.147768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'fbe5aacfe4f8'
down_revision: Union[str, Sequence[str], None] = 'd21a5db05206'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update defaults to NSE-only and clean non-NSE data."""
    # Update default values for stock_symbols
    op.alter_column('stock_symbols', 'market', 
                    server_default='NSE', nullable=False)
    op.alter_column('stock_symbols', 'currency', 
                    server_default='KES', nullable=False)
    op.alter_column('stock_symbols', 'exchange', 
                    server_default='NSE', nullable=True)
    
    # Update default values for stock_data
    op.alter_column('stock_data', 'market', 
                    server_default='NSE', nullable=False)
    op.alter_column('stock_data', 'currency', 
                    server_default='KES', nullable=False)
    
    # Update existing records to NSE
    op.execute("UPDATE stock_symbols SET market = 'NSE', currency = 'KES' WHERE market != 'NSE'")
    op.execute("UPDATE stock_data SET market = 'NSE', currency = 'KES' WHERE market != 'NSE'")
    op.execute("UPDATE news_articles SET market = 'NSE' WHERE market != 'NSE'")
    op.execute("UPDATE data_quality_metrics SET market = 'NSE' WHERE market != 'NSE'")
    
    # Optional: Delete non-NSE data (uncomment if you want to clean)
    # op.execute("DELETE FROM stock_data WHERE symbol_id IN (SELECT id FROM stock_symbols WHERE market != 'NSE')")
    # op.execute("DELETE FROM news_articles WHERE symbol_id IN (SELECT id FROM stock_symbols WHERE market != 'NSE')")
    # op.execute("DELETE FROM stock_symbols WHERE market != 'NSE'")


def downgrade() -> None:
    """Revert to multi-market defaults."""
    # Revert default values for stock_symbols
    op.alter_column('stock_symbols', 'market', 
                    server_default='US', nullable=False)
    op.alter_column('stock_symbols', 'currency', 
                    server_default='USD', nullable=False)
    
    # Revert default values for stock_data
    op.alter_column('stock_data', 'market', 
                    server_default='US', nullable=False)
    op.alter_column('stock_data', 'currency', 
                    server_default='USD', nullable=False)
