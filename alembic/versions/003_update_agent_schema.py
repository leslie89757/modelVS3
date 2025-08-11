"""Update Agent schema for advanced configuration

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加新字段
    op.add_column('agents', sa.Column('avatar', sa.String(), nullable=True))
    op.add_column('agents', sa.Column('category', sa.String(), nullable=False, server_default='其他'))
    op.add_column('agents', sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'))
    op.add_column('agents', sa.Column('access_level', sa.String(), nullable=False, server_default='private'))
    op.add_column('agents', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # 添加新的配置字段
    op.add_column('agents', sa.Column('llm_config', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('agents', sa.Column('system_config', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('agents', sa.Column('tools_config', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('agents', sa.Column('knowledge_config', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('agents', sa.Column('deployment_config', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('agents', sa.Column('stats', sa.JSON(), nullable=False, server_default='{"total_conversations": 0, "total_messages": 0, "avg_response_time": 0, "user_satisfaction": 0}'))
    
    # 迁移现有的schema数据到新结构
    # 这里我们将现有的schema字段数据迁移到新的字段中
    op.execute("""
        UPDATE agents 
        SET 
            llm_config = CASE 
                WHEN schema->>'model_id' IS NOT NULL THEN 
                    json_build_object(
                        'primary_model_id', schema->>'model_id',
                        'temperature', COALESCE((schema->>'temperature')::float, 0.7),
                        'max_tokens', COALESCE((schema->>'max_tokens')::int, 2000),
                        'top_p', 0.9,
                        'frequency_penalty', 0,
                        'presence_penalty', 0
                    )
                ELSE '{}'::json
            END,
            system_config = CASE 
                WHEN schema->>'system_prompt' IS NOT NULL THEN 
                    json_build_object(
                        'system_prompt', schema->>'system_prompt',
                        'conversation_starters', '[]'::json,
                        'response_style', 'formal',
                        'max_context_turns', 10,
                        'enable_memory', true
                    )
                ELSE '{}'::json
            END,
            tools_config = CASE 
                WHEN schema->'tools' IS NOT NULL THEN 
                    json_build_object(
                        'enabled_tools', schema->'tools',
                        'tool_configs', '{}'::json,
                        'custom_tools', '[]'::json
                    )
                ELSE '{}'::json
            END
        WHERE schema IS NOT NULL
    """)
    
    # 删除旧的schema字段
    op.drop_column('agents', 'schema')


def downgrade() -> None:
    # 恢复schema字段
    op.add_column('agents', sa.Column('schema', sa.JSON(), nullable=False, server_default='{}'))
    
    # 将新字段的数据迁移回schema字段
    op.execute("""
        UPDATE agents 
        SET schema = json_build_object(
            'model_id', llm_config->>'primary_model_id',
            'temperature', (llm_config->>'temperature')::float,
            'max_tokens', (llm_config->>'max_tokens')::int,
            'system_prompt', system_config->>'system_prompt',
            'tools', tools_config->'enabled_tools'
        )
        WHERE llm_config IS NOT NULL AND system_config IS NOT NULL
    """)
    
    # 删除新字段
    op.drop_column('agents', 'stats')
    op.drop_column('agents', 'deployment_config')
    op.drop_column('agents', 'knowledge_config')
    op.drop_column('agents', 'tools_config')
    op.drop_column('agents', 'system_config')
    op.drop_column('agents', 'llm_config')
    op.drop_column('agents', 'version')
    op.drop_column('agents', 'access_level')
    op.drop_column('agents', 'tags')
    op.drop_column('agents', 'category')
    op.drop_column('agents', 'avatar') 