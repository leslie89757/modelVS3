"""Remove pricing related fields

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove pricing column from models table
    op.drop_column('models', 'pricing')
    
    # Remove cost_usd column from runs table
    op.drop_column('runs', 'cost_usd')
    
    # Remove cost_usd column from usage table
    op.drop_column('usage', 'cost_usd')


def downgrade() -> None:
    # Add back cost_usd column to usage table
    op.add_column('usage', sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'))
    
    # Add back cost_usd column to runs table
    op.add_column('runs', sa.Column('cost_usd', sa.Float(), nullable=True))
    
    # Add back pricing column to models table
    op.add_column('models', sa.Column('pricing', sa.JSON(), nullable=True)) 