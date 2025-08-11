#!/usr/bin/env python3
"""测试Agent工具配置问题"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Agent, Run
from src.schemas import RunRequest, MessageRequest
from src.core.agent_executor import AgentExecutor

async def test_agent_tools():
    # 连接数据库
    database_url = "postgresql://postgres:password@postgres:5432/modelvs3"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 查找特定Agent
        agent_id = 'b6d3226b-239b-4e8f-8770-48148dc12d6b'
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        print(f"📊 Agent: {agent.name}")
        print(f"🔧 Agent tools_config: {agent.tools_config}")
        
        # 创建测试Run
        db_run = Run(
            agent_id=agent.id,
            run_metadata={
                "messages": [{"role": "user", "content": "测试工具调用"}],
                "stream": False
            }
        )
        db.add(db_run)
        db.commit()
        db.refresh(db_run)
        
        # 创建RunRequest
        run_request = RunRequest(
            agent_id=agent.id,
            messages=[MessageRequest(role="user", content="测试工具调用")],
            stream=False
        )
        
        # 创建AgentExecutor并测试
        executor = AgentExecutor(db)
        
        print("\n🧪 开始测试Agent执行...")
        
        # 模拟execute_agent中的配置解析
        llm_config = agent.llm_config if isinstance(agent.llm_config, dict) else {}
        system_config = agent.system_config if isinstance(agent.system_config, dict) else {}
        tools_config = agent.tools_config if isinstance(agent.tools_config, dict) else {}
        
        print(f"📋 解析后的tools_config: {tools_config}")
        
        # 测试工具加载
        available_tools = await executor._get_available_tools(tools_config)
        print(f"🔧 加载的工具数量: {len(available_tools)}")
        
        for tool in available_tools:
            tool_name = tool.get("function", {}).get("name", "unknown")
            print(f"   - 工具: {tool_name}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_agent_tools())
