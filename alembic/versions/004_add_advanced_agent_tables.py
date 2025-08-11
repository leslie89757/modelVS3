"""Add advanced agent tables

Revision ID: 004_add_advanced_agent_tables
Revises: 3c63e77f6c23
Create Date: 2024-12-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_advanced_agent_tables'
down_revision: Union[str, None] = '3c63e77f6c23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create advanced_agents table
    op.create_table('advanced_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('personality', sa.String(), nullable=False, default='professional'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='idle'),
        sa.Column('current_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stats', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_advanced_agents_name'), 'advanced_agents', ['name'], unique=False)

    # Create agent_sessions table
    op.create_table('agent_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='active'),
        sa.Column('current_step', sa.String(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True, default=0),
        sa.Column('confidence_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('reasoning_visible', sa.Boolean(), nullable=True, default=True),
        sa.Column('session_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_messages', sa.Integer(), nullable=True, default=0),
        sa.Column('total_tool_calls', sa.Integer(), nullable=True, default=0),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, default=0),
        sa.Column('tokens_used', sa.Integer(), nullable=True, default=0),
        sa.Column('cost_estimate', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['advanced_agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create session_messages table
    op.create_table('session_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('tool_calls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tool_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True, default=0),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, default=0),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create advanced_tools table
    op.create_table('advanced_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('schema', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('implementation', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.String(), nullable=True, default='1.0.0'),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('required_params', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('optional_params', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('success_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_execution_time', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_advanced_tools_name'), 'advanced_tools', ['name'], unique=True)

    # Create agent_memories table
    op.create_table('agent_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('memory_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True, default=0.5),
        sa.Column('access_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['advanced_agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create agent_performance_metrics table
    op.create_table('agent_performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(), nullable=True),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('measurement_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['advanced_agents.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create agent_knowledge_bases table
    op.create_table('agent_knowledge_bases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=True, default='text'),
        sa.Column('embedding', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('categories', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True, default=0),
        sa.Column('relevance_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['advanced_agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add foreign key constraint for current_session_id
    op.create_foreign_key(
        'fk_advanced_agents_current_session', 
        'advanced_agents', 
        'agent_sessions',
        ['current_session_id'], 
        ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint first
    op.drop_constraint('fk_advanced_agents_current_session', 'advanced_agents', type_='foreignkey')
    
    # Drop tables in reverse order
    op.drop_table('agent_knowledge_bases')
    op.drop_table('agent_performance_metrics')
    op.drop_table('agent_memories')
    op.drop_index(op.f('ix_advanced_tools_name'), table_name='advanced_tools')
    op.drop_table('advanced_tools')
    op.drop_table('session_messages')
    op.drop_table('agent_sessions')
    op.drop_index(op.f('ix_advanced_agents_name'), table_name='advanced_agents')
    op.drop_table('advanced_agents') 