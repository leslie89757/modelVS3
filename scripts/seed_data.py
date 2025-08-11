#!/usr/bin/env python3
"""
数据种子脚本 - 初始化默认数据
运行此脚本将创建默认的模型、工具和示例 Agent
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_db_connection():
    """创建数据库连接"""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost/modelvs3")
    engine = create_async_engine(database_url)
    return engine


async def seed_users(conn) -> List[str]:
    """创建初始用户"""
    users = []
    
    # 创建管理员用户
    admin_id = str(uuid.uuid4())
    admin_password = pwd_context.hash("admin123")
    
    await conn.execute(text("""
        INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, created_at)
        VALUES (:id, :email, :password, :full_name, true, true, :created_at)
        ON CONFLICT (email) DO NOTHING
    """), {
        "id": admin_id,
        "email": "admin@example.com",
        "password": admin_password,
        "full_name": "系统管理员",
        "created_at": datetime.utcnow()
    })
    
    users.append(admin_id)
    
    # 创建演示用户
    demo_id = str(uuid.uuid4())
    demo_password = pwd_context.hash("demo123")
    
    await conn.execute(text("""
        INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, created_at)
        VALUES (:id, :email, :password, :full_name, true, false, :created_at)
        ON CONFLICT (email) DO NOTHING
    """), {
        "id": demo_id,
        "email": "demo@example.com",
        "password": demo_password,
        "full_name": "演示用户",
        "created_at": datetime.utcnow()
    })
    
    users.append(demo_id)
    
    print("✅ 用户数据已创建")
    return users


async def seed_models(conn) -> List[str]:
    """创建默认模型"""
    models = []
    
    model_configs = [
        {
            "name": "gpt-4",
            "provider": "openai",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "context_len": 8192,
            "enabled": True
        },
        {
            "name": "gpt-3.5-turbo",
            "provider": "openai",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "context_len": 4096,
            "enabled": True
        },
        {
            "name": "claude-3-opus-20240229",
            "provider": "anthropic",
            "endpoint": "https://api.anthropic.com/v1/messages",
            "context_len": 200000,
            "enabled": True
        },
        {
            "name": "claude-3-sonnet-20240229",
            "provider": "anthropic",
            "endpoint": "https://api.anthropic.com/v1/messages",
            "context_len": 200000,
            "enabled": True
        },
        {
            "name": "gemini-pro",
            "provider": "google",
            "endpoint": "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent",
            "context_len": 30720,
            "enabled": True
        }
    ]
    
    for config in model_configs:
        model_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO models (id, name, provider, endpoint, context_len, enabled, created_at)
            VALUES (:id, :name, :provider, :endpoint, :context_len, :enabled, :created_at)
            ON CONFLICT (name) DO NOTHING
        """), {
            "id": model_id,
            "name": config["name"],
            "provider": config["provider"],
            "endpoint": config["endpoint"],
            "context_len": config["context_len"],
            "enabled": config["enabled"],
            "created_at": datetime.utcnow()
        })
        models.append(model_id)
    
    print("✅ 模型数据已创建")
    return models


async def seed_tools(conn) -> List[str]:
    """创建默认工具"""
    tools = []
    
    tool_configs = [
        {
            "name": "calculator",
            "description": "数学计算器，支持基本的数学运算",
            "schema": {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "执行数学计算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "要计算的数学表达式"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            "enabled": True
        },
        {
            "name": "web_search",
            "description": "网络搜索工具，可以搜索实时信息",
            "schema": {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "搜索网络信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "最大结果数量",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "enabled": True
        },
        {
            "name": "file_reader",
            "description": "文件读取工具，可以读取文本文件内容",
            "schema": {
                "type": "function",
                "function": {
                    "name": "file_reader",
                    "description": "读取文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            "enabled": True
        }
    ]
    
    for config in tool_configs:
        tool_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO tools (id, name, description, schema, enabled, created_at)
            VALUES (:id, :name, :description, :schema, :enabled, :created_at)
            ON CONFLICT (name) DO NOTHING
        """), {
            "id": tool_id,
            "name": config["name"],
            "description": config["description"],
            "schema": json.dumps(config["schema"]),
            "enabled": config["enabled"],
            "created_at": datetime.utcnow()
        })
        tools.append(tool_id)
    
    print("✅ 工具数据已创建")
    return tools


async def seed_agents(conn, owner_id: str) -> List[str]:
    """创建示例 Agent"""
    agents = []
    
    agent_configs = [
        {
            "name": "通用助手",
            "description": "一个通用的 AI 助手，可以回答各种问题和协助完成任务",
            "schema": {
                "version": "2025-07",
                "model": "gpt-4",
                "strategy": "react",
                "system_prompt": "你是一个专业、友好的 AI 助手。请尽力帮助用户解决问题，提供准确和有用的信息。如果需要最新信息，请使用搜索工具。如果需要进行计算，请使用计算器工具。",
                "max_iterations": 5,
                "timeout": 120,
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "tools": [
                    {"name": "web_search", "required": False},
                    {"name": "calculator", "required": False}
                ]
            },
            "status": "active"
        },
        {
            "name": "数据分析师",
            "description": "专门用于数据分析和数学计算的 Agent",
            "schema": {
                "version": "2025-07",
                "model": "gpt-4",
                "strategy": "react",
                "system_prompt": "你是一个专业的数据分析师。你的任务是帮助用户进行数据分析、统计计算和数学问题解决。请仔细分析数据，提供准确的计算结果和专业的见解。",
                "max_iterations": 8,
                "timeout": 180,
                "parameters": {
                    "temperature": 0.2,
                    "max_tokens": 3000
                },
                "tools": [
                    {"name": "calculator", "required": True}
                ]
            },
            "status": "active"
        },
        {
            "name": "研究助手",
            "description": "专门用于信息搜索和研究的 Agent",
            "schema": {
                "version": "2025-07",
                "model": "claude-3-sonnet-20240229",
                "strategy": "react",
                "system_prompt": "你是一个专业的研究助手。你的任务是帮助用户搜索和整理信息，进行深入的研究分析。请提供准确、客观的信息，并注明信息来源。",
                "max_iterations": 6,
                "timeout": 150,
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 4000
                },
                "tools": [
                    {"name": "web_search", "required": True}
                ]
            },
            "status": "active"
        }
    ]
    
    for config in agent_configs:
        agent_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO agents (id, name, description, schema, status, owner_id, created_at)
            VALUES (:id, :name, :description, :schema, :status, :owner_id, :created_at)
        """), {
            "id": agent_id,
            "name": config["name"],
            "description": config["description"],
            "schema": json.dumps(config["schema"]),
            "status": config["status"],
            "owner_id": owner_id,
            "created_at": datetime.utcnow()
        })
        agents.append(agent_id)
    
    print("✅ Agent 数据已创建")
    return agents


async def main():
    """主函数"""
    print("🚀 开始初始化数据库种子数据...")
    
    try:
        engine = await create_db_connection()
        
        async with engine.begin() as conn:
            # 创建用户
            user_ids = await seed_users(conn)
            
            # 创建模型
            model_ids = await seed_models(conn)
            
            # 创建工具
            tool_ids = await seed_tools(conn)
            
            # 创建 Agent（使用第一个用户作为所有者）
            if user_ids:
                agent_ids = await seed_agents(conn, user_ids[0])
            
            print("\n🎉 数据库种子数据初始化完成！")
            print("\n📋 已创建的数据:")
            print(f"  👥 用户: {len(user_ids)} 个")
            print(f"  🤖 模型: {len(model_ids)} 个")
            print(f"  🔧 工具: {len(tool_ids)} 个")
            print(f"  🎯 Agent: {len(agent_ids) if 'agent_ids' in locals() else 0} 个")
            
            print("\n🔑 默认账户:")
            print("  管理员: admin@example.com / admin123")
            print("  演示用户: demo@example.com / demo123")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 