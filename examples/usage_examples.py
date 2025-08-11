#!/usr/bin/env python3
"""
ModelVS3 使用示例
演示如何使用 API 客户端进行各种操作
"""

import asyncio
import json
from typing import List, Dict, Any
from src.utils.api_client import ModelVS3Client, create_simple_agent, quick_chat


async def example_basic_usage():
    """基础使用示例"""
    print("🚀 基础使用示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 健康检查
        health = await client.health_check()
        print(f"✅ 服务状态: {health}")
        
        # 获取模型列表
        models = await client.get_models()
        print(f"📋 可用模型: {len(models)} 个")
        for model in models[:3]:  # 显示前3个
            print(f"  🤖 {model['name']} ({model['provider']})")
        
        # 获取工具列表
        tools = await client.get_tools()
        print(f"🔧 可用工具: {len(tools)} 个")
        for tool in tools:
            print(f"  ⚙️  {tool['name']}: {tool['description']}")


async def example_create_agent():
    """创建 Agent 示例"""
    print("\n🎯 创建 Agent 示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 创建一个简单的数学助手
        agent = await create_simple_agent(
            client=client,
            name="数学助手",
            system_prompt="你是一个专业的数学助手，能够帮助用户解决各种数学问题。请使用计算器工具来确保计算的准确性。",
            model="gpt-4",
            tools=["calculator"]
        )
        
        print(f"✅ Agent 创建成功:")
        print(f"  ID: {agent['id']}")
        print(f"  名称: {agent['name']}")
        print(f"  状态: {agent['status']}")
        
        return agent['id']


async def example_chat_with_agent(agent_id: str):
    """与 Agent 聊天示例"""
    print(f"\n💬 与 Agent 聊天示例 (ID: {agent_id[:8]}...)")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 进行对话
        questions = [
            "请计算 15 * 23 + 78 的结果",
            "如果一个圆的半径是 5cm，它的面积是多少？",
            "解方程 2x + 5 = 15"
        ]
        
        for question in questions:
            print(f"\n👤 问题: {question}")
            response = await quick_chat(client, agent_id, question)
            print(f"🤖 回答: {response}")


async def example_streaming_chat():
    """流式聊天示例"""
    print("\n📡 流式聊天示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 获取第一个可用的 Agent
        agents = await client.get_agents(limit=1)
        if not agents:
            print("❌ 没有可用的 Agent")
            return
        
        agent_id = agents[0]['id']
        messages = [{"role": "user", "content": "请写一首关于人工智能的诗"}]
        
        print(f"🎭 流式生成诗歌 (Agent: {agent_id[:8]}...):")
        print("🤖 ", end="", flush=True)
        
        async for event in client.stream_agent(agent_id, messages):
            if event.get("type") == "llm_response":
                content = event.get("response", {}).get("content", "")
                print(content, end="", flush=True)
        
        print("\n")


async def example_openai_compatibility():
    """OpenAI 兼容接口示例"""
    print("\n🔄 OpenAI 兼容接口示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 使用 OpenAI 兼容的聊天接口
        response = await client.chat_completions(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个有用的助手"},
                {"role": "user", "content": "什么是大型语言模型？"}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        print("✅ OpenAI 兼容接口响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))


async def example_agent_management():
    """Agent 管理示例"""
    print("\n⚙️  Agent 管理示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 获取所有 Agent
        agents = await client.get_agents()
        print(f"📋 当前 Agent 数量: {len(agents)}")
        
        if agents:
            agent = agents[0]
            agent_id = agent['id']
            
            print(f"\n🎯 管理 Agent: {agent['name']}")
            
            # 暂停 Agent
            print("⏸️  暂停 Agent...")
            await client.pause_agent(agent_id)
            
            # 检查状态
            updated_agent = await client.get_agent(agent_id)
            print(f"📊 Agent 状态: {updated_agent['status']}")
            
            # 重新激活
            print("▶️  重新激活 Agent...")
            await client.activate_agent(agent_id)
            
            # 再次检查状态
            updated_agent = await client.get_agent(agent_id)
            print(f"📊 Agent 状态: {updated_agent['status']}")


async def example_run_history():
    """执行历史示例"""
    print("\n📈 执行历史示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 获取执行历史
        runs = await client.get_runs(limit=5)
        
        if runs:
            print(f"📋 最近 {len(runs)} 次执行:")
            for run in runs:
                status_icon = "✅" if run['status'] == 'completed' else "❌" if run['status'] == 'failed' else "🟡"
                print(f"  {status_icon} {run['id'][:8]}... - {run['status']}")
                
                if run.get('input_tokens') and run.get('output_tokens'):
                    print(f"    📊 Token: {run['input_tokens']} 输入 / {run['output_tokens']} 输出")
                
                if run.get('cost_usd'):
                    print(f"    💰 成本: ${run['cost_usd']:.4f}")
        else:
            print("📭 暂无执行历史")


async def example_dashboard_stats():
    """仪表板统计示例"""
    print("\n📊 仪表板统计示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        try:
            # 获取统计数据
            stats = await client.get_dashboard_stats()
            print("📈 平台统计:")
            print(f"  🎯 Agent 总数: {stats.get('total_agents', 0)}")
            print(f"  🤖 模型总数: {stats.get('total_models', 0)}")
            print(f"  🔧 工具总数: {stats.get('total_tools', 0)}")
            print(f"  📝 执行总数: {stats.get('total_runs', 0)}")
            print(f"  💰 总成本: ${stats.get('total_cost_usd', 0):.2f}")
            
            # 获取使用统计
            usage_stats = await client.get_usage_stats(days=7)
            if usage_stats:
                print(f"\n📊 过去7天使用情况:")
                for stat in usage_stats[-3:]:  # 显示最近3天
                    print(f"  📅 {stat.get('date', 'N/A')}: {stat.get('request_count', 0)} 请求")
            
        except Exception as e:
            print(f"⚠️  获取统计数据失败: {e}")


async def example_advanced_agent():
    """高级 Agent 配置示例"""
    print("\n🔬 高级 Agent 配置示例")
    
    async with ModelVS3Client("http://localhost:8000") as client:
        # 创建一个复杂的 Agent 配置
        advanced_agent_config = {
            "name": "高级研究助手",
            "description": "一个具有高级配置的研究助手，支持多种工具和复杂推理",
            "schema": {
                "version": "2025-07",
                "model": "claude-3-opus-20240229",
                "strategy": "react",
                "system_prompt": """你是一个高级研究助手，具备以下能力：
1. 深度网络搜索和信息整合
2. 复杂数学计算和数据分析
3. 文件读取和内容分析

请按照以下步骤处理用户请求：
1. 理解用户需求
2. 规划解决方案
3. 使用适当的工具收集信息
4. 综合分析结果
5. 提供详细、准确的回答

始终保持客观、专业，并提供信息来源。""",
                "max_iterations": 10,
                "timeout": 300,
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "top_p": 0.9
                },
                "tools": [
                    {"name": "web_search", "required": False},
                    {"name": "calculator", "required": False},
                    {"name": "file_reader", "required": False}
                ],
                "memory": {
                    "max_history": 20,
                    "enable_long_term": True
                },
                "constraints": {
                    "max_cost_per_run": 1.0,
                    "rate_limit": "10/minute"
                }
            },
            "status": "active"
        }
        
        # 创建 Agent
        agent = await client.create_agent(advanced_agent_config)
        print(f"✅ 高级 Agent 创建成功:")
        print(f"  ID: {agent['id']}")
        print(f"  配置: {len(agent['schema']['tools'])} 个工具")
        print(f"  最大迭代: {agent['schema']['max_iterations']}")
        
        return agent['id']


async def main():
    """主函数 - 运行所有示例"""
    print("🌟 ModelVS3 使用示例集合")
    print("=" * 50)
    
    try:
        # 基础示例
        await example_basic_usage()
        
        # 创建 Agent
        math_agent_id = await example_create_agent()
        
        # 与 Agent 聊天
        await example_chat_with_agent(math_agent_id)
        
        # 流式聊天
        await example_streaming_chat()
        
        # OpenAI 兼容接口
        await example_openai_compatibility()
        
        # Agent 管理
        await example_agent_management()
        
        # 执行历史
        await example_run_history()
        
        # 仪表板统计
        await example_dashboard_stats()
        
        # 高级 Agent
        advanced_agent_id = await example_advanced_agent()
        
        print("\n🎉 所有示例运行完成！")
        print("\n💡 更多功能:")
        print("  - 访问 http://localhost:8000/docs 查看完整 API 文档")
        print("  - 使用 CLI 工具: python3 cli.py --help")
        print("  - 查看前端界面: http://localhost:3000")
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        print("请确保 ModelVS3 服务正在运行")


if __name__ == "__main__":
    asyncio.run(main()) 