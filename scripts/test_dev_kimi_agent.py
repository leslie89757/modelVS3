#!/usr/bin/env python3
"""
测试开发环境kimi----128K Agent的奇门遁甲工具调用
"""

import requests
import json
import time

# 开发环境API
API_BASE = "http://localhost:8001/api/v1"

def test_dev_kimi_agent():
    """测试开发环境的kimi----128K Agent"""
    
    print("🧪 测试开发环境kimi----128K Agent的奇门遁甲工具调用...")
    
    # 开发环境kimi----128K Agent ID
    agent_id = "f810186c-9381-43f3-847d-f034437d1782"
    
    print(f"📋 测试Agent: {agent_id}")
    print(f"🌐 API端点: {API_BASE}")
    
    # 构建测试请求
    run_request = {
        "agent_id": agent_id,
        "messages": [
            {
                "role": "user", 
                "content": "请帮我现在起一个奇门局并分析一下"
            }
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2000,
        "protocol": "FunctionCall"
    }
    
    print("🚀 发送执行请求...")
    
    # 发送请求
    response = requests.post(f"{API_BASE}/runs", json=run_request, stream=True)
    
    if not response.ok:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"   错误详情: {response.text}")
        return
    
    print("📋 Agent执行日志:")
    tool_called = False
    qimen_tool_called = False
    response_content = ""
    
    try:
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # 处理服务器发送事件格式
                if line_str.startswith('data: '):
                    json_str = line_str[6:]  # 去掉 'data: ' 前缀
                    if json_str.strip() == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(json_str)
                        event_type = data.get('type', 'unknown')
                        
                        print(f"   📊 事件: {event_type}")
                        
                        if event_type == 'tool_call_start':
                            tool_name = data.get('tool_call', {}).get('function', {}).get('name', 'unknown')
                            args = data.get('tool_call', {}).get('function', {}).get('arguments', {})
                            print(f"   🔧 开始调用工具: {tool_name}")
                            print(f"       参数: {args}")
                            tool_called = True
                            if tool_name == 'qimen_dunjia':
                                qimen_tool_called = True
                                
                        elif event_type == 'tool_call_result':
                            tool_name = data.get('tool_call', {}).get('function', {}).get('name', 'unknown')
                            result = data.get('result', {})
                            print(f"   ✅ 工具调用结果: {tool_name}")
                            if tool_name == 'qimen_dunjia':
                                print(f"       🔮 奇门排盘结果长度: {len(str(result))} 字符")
                                # 显示部分结果
                                if isinstance(result, dict) and 'result' in result:
                                    print(f"       📋 排盘预览: {str(result['result'])[:200]}...")
                            
                        elif event_type == 'content':
                            content = data.get('content', '')
                            response_content += content
                            if len(content) > 50:
                                print(f"   📝 内容: {content[:50]}...")
                            else:
                                print(f"   📝 内容: {content}")
                                
                        elif event_type == 'error':
                            error_msg = data.get('error', 'Unknown error')
                            print(f"   ❌ 错误: {error_msg}")
                            
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️ JSON解析错误: {e}")
                        print(f"       原始数据: {json_str[:100]}...")
                        
    except Exception as e:
        print(f"❌ 处理响应时出错: {e}")
    
    # 总结测试结果
    print(f"\n🎯 开发环境测试结果总结:")
    print(f"   📊 是否调用了工具: {'✅ 是' if tool_called else '❌ 否'}")
    print(f"   🔮 是否调用了qimen_dunjia工具: {'✅ 是' if qimen_tool_called else '❌ 否'}")
    print(f"   📝 响应内容长度: {len(response_content)} 字符")
    
    if not tool_called:
        print(f"   🚨 问题：Agent没有调用任何工具！")
        print(f"   💡 可能原因：")
        print(f"      1. 模型不理解系统提示词")
        print(f"      2. 工具描述不清楚")
        print(f"      3. Function Call格式问题")
    elif not qimen_tool_called:
        print(f"   🚨 问题：Agent调用了工具，但不是qimen_dunjia工具！")
    else:
        print(f"   🎉 成功：开发环境qimen_dunjia工具正常调用！")
        print(f"   🔮 这证明你的kimi----128K Agent配置完全正确！")

if __name__ == "__main__":
    test_dev_kimi_agent() 