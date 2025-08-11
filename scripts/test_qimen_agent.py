#!/usr/bin/env python3
"""
测试奇门遁甲工具在Agent中的调用
"""

import asyncio
import json
import requests
import sys
import os

# 添加项目路径
sys.path.append('.')

API_BASE = "http://localhost:8000/api/v1"

async def test_qimen_agent():
    """测试奇门遁甲Agent"""
    
    print("🧪 开始测试奇门遁甲工具调用...")
    
    # 1. 获取可用的模型和工具
    print("\n1️⃣ 获取模型和工具信息...")
    
    # 获取模型
    models_response = requests.get(f"{API_BASE}/models?enabled=true")
    if not models_response.ok:
        print(f"❌ 获取模型失败: {models_response.status_code}")
        return
    
    models = models_response.json()
    if not models:
        print("❌ 没有可用的模型")
        return
    
    print(f"✅ 找到 {len(models)} 个模型")
    
    # 获取工具
    tools_response = requests.get(f"{API_BASE}/tools")
    if not tools_response.ok:
        print(f"❌ 获取工具失败: {tools_response.status_code}")
        return
    
    tools = tools_response.json()
    qimen_tool = None
    for tool in tools:
        if tool['name'] == 'qimen_dunjia':
            qimen_tool = tool
            break
    
    if not qimen_tool:
        print("❌ 没有找到qimen_dunjia工具")
        return
    
    print(f"✅ 找到qimen_dunjia工具: ID={qimen_tool['id']}")
    
    # 2. 创建测试Agent
    print("\n2️⃣ 创建测试Agent...")
    
    agent_config = {
        "name": "奇门遁甲测试Agent",
        "description": "专门测试奇门遁甲工具调用的Agent",
        "category": "其他",
        "tags": ["测试", "奇门遁甲"],
        "status": "active",
        "access_level": "private",
        "llm_config": {
            "primary_model_id": "1da14cec-3437-42d0-b546-71567dc73d52",  # 使用moonshot模型
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "frequency_penalty": 0,
            "presence_penalty": 0
        },
        "system_config": {
            "system_prompt": "你是一个好人，你对每个用户的问题都需要使用基于奇门引擎工具排盘，然后结合奇门遁甲的知识做判断。",
            "conversation_starters": ["请为我现在的时间起一个奇门局"],
            "response_style": "formal",
            "max_context_turns": 10,
            "enable_memory": True
        },
        "tools_config": {
            "enabled_tools": [qimen_tool['id']],  # 使用工具ID
            "tool_configs": {},
            "custom_tools": []
        },
        "knowledge_config": {
            "enabled": False,
            "documents": [],
            "retrieval_config": {
                "top_k": 5,
                "similarity_threshold": 0.7,
                "rerank": True
            }
        },
        "deployment_config": {
            "rate_limits": {
                "requests_per_minute": 60,
                "requests_per_day": 1000
            }
        }
    }
    
    # 创建Agent
    create_response = requests.post(f"{API_BASE}/agents", json=agent_config)
    if not create_response.ok:
        print(f"❌ 创建Agent失败: {create_response.status_code}")
        print(f"   错误详情: {create_response.text}")
        return
    
    agent = create_response.json()
    agent_id = agent['id']
    print(f"✅ 创建Agent成功: ID={agent_id}")
    
    # 激活Agent
    activate_response = requests.post(f"{API_BASE}/agents/{agent_id}/activate")
    if not activate_response.ok:
        print(f"❌ 激活Agent失败: {activate_response.status_code}")
        print(f"   错误详情: {activate_response.text}")
        return
    
    print(f"✅ Agent已激活")
    
    try:
        # 3. 测试Agent执行
        print("\n3️⃣ 测试Agent执行...")
        
        run_request = {
            "agent_id": agent_id,
            "messages": [
                {
                    "role": "user",
                    "content": "请为我现在的时间起一个奇门局并分析"
                }
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000,
            "protocol": "FunctionCall"  # 明确设置协议
        }
        
        # 发送执行请求 - 使用正确的API端点
        run_response = requests.post(f"{API_BASE}/runs", json=run_request, stream=True)
        if not run_response.ok:
            print(f"❌ 执行Agent失败: {run_response.status_code}")
            print(f"   错误详情: {run_response.text}")
            return

        # 处理流式响应
        print("📋 Agent执行日志:")
        has_tool_call = False
        response_content = ""
        tool_call_success = False
        
        for line in run_response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # 处理服务器发送事件格式: "data: {...}"
                if line_str.startswith('data: '):
                    json_str = line_str[6:]  # 移除 "data: " 前缀
                    if json_str.strip() == '[DONE]':
                        print(f"   🏁 流式响应结束")
                        break
                    
                    try:
                        data = json.loads(json_str)
                        event_type = data.get('type', 'unknown')
                        print(f"   📊 事件类型: {event_type}")
                        
                        if event_type == 'tool_call_start':
                            tool_name = data.get('tool_call', {}).get('function', {}).get('name', 'unknown')
                            print(f"   🔧 开始调用工具: {tool_name}")
                            has_tool_call = True
                            
                        elif event_type == 'tool_call_result':
                            tool_name = data.get('tool_call', {}).get('function', {}).get('name', 'unknown')
                            result = data.get('result', {})
                            success = result.get('success', False)
                            print(f"   {'✅' if success else '❌'} 工具调用结果: {tool_name}")
                            if success:
                                tool_call_success = True
                                result_content = str(result.get('result', ''))[:300]
                                print(f"      结果预览: {result_content}...")
                            else:
                                print(f"      错误: {result.get('error', 'unknown')}")
                                
                        elif event_type == 'llm_response':
                            response = data.get('response', {})
                            content = response.get('content', '')
                            if content:
                                response_content += content
                                content_preview = content[:100] + ('...' if len(content) > 100 else '')
                                print(f"   💬 LLM回复: {content_preview}")
                            
                            # 检查是否有工具调用
                            tool_calls = response.get('tool_calls', [])
                            if tool_calls:
                                print(f"   🔧 LLM请求调用 {len(tool_calls)} 个工具")
                                for tool_call in tool_calls:
                                    tool_name = tool_call.get('function', {}).get('name', 'unknown')
                                    print(f"      - {tool_name}")
                                    
                        elif event_type == 'error':
                            error_msg = data.get('error', 'unknown')
                            print(f"   ❌ 错误: {error_msg}")
                            
                        elif event_type == 'execution_complete':
                            iterations = data.get('iterations', 0)
                            print(f"   🏁 执行完成，共 {iterations} 轮")
                            
                        else:
                            print(f"   ℹ️  其他事件: {event_type}")
                            
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  JSON解析失败: {e}")
                        print(f"      原始内容: {json_str[:100]}...")
                        
                else:
                    print(f"   📝 非标准格式: {line_str[:100]}...")
        
        print(f"\n📊 执行总结:")
        print(f"   🔧 是否调用了工具: {'是' if has_tool_call else '否'}")
        print(f"   ✅ 工具调用是否成功: {'是' if tool_call_success else '否'}")
        print(f"   💬 回复内容长度: {len(response_content)} 字符")
        if response_content:
            print(f"   💬 回复预览: {response_content[:200]}...")
        
        if not has_tool_call:
            print(f"   ⚠️  警告: 没有检测到qimen_dunjia工具调用！")
        elif not tool_call_success:
            print(f"   ⚠️  警告: qimen_dunjia工具调用失败！")
        else:
            print(f"   🎉 qimen_dunjia工具调用成功！")
        
        print("\n✅ 测试完成")
        
    finally:
        # 4. 清理测试Agent
        print(f"\n4️⃣ 清理测试Agent: {agent_id}")
        delete_response = requests.delete(f"{API_BASE}/agents/{agent_id}")
        if delete_response.ok:
            print("✅ 测试Agent已删除")
        else:
            print(f"⚠️ 删除测试Agent失败: {delete_response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_qimen_agent()) 