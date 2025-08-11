#!/usr/bin/env python3
"""
完全模拟前端的请求格式来测试kimi----128K Agent
"""

import requests
import json
import time

# 开发环境API (和前端一致)
API_BASE = "http://localhost:8001/api/v1"

def test_frontend_style_request():
    """使用和前端完全一样的请求格式测试Agent"""
    
    print("🧪 使用前端请求格式测试kimi----128K Agent...")
    
    # 开发环境kimi----128K Agent ID
    agent_id = "f810186c-9381-43f3-847d-f034437d1782"
    
    print(f"📋 测试Agent: {agent_id}")
    print(f"🌐 API端点: {API_BASE}")
    
    # 完全模拟前端的请求格式 (非流式)
    run_request = {
        "agent_id": agent_id,
        "messages": [
            {
                "role": "user", 
                "content": "请帮我现在起一个奇门局并分析一下"
            }
        ],
        "stream": False  # ❗ 和前端一样使用非流式
        # 注意：前端没有设置protocol参数
    }
    
    print("🚀 发送非流式执行请求...")
    print(f"📋 请求体: {json.dumps(run_request, indent=2, ensure_ascii=False)}")
    
    # 发送请求
    response = requests.post(f"{API_BASE}/runs/", json=run_request)
    
    print(f"📊 响应状态码: {response.status_code}")
    
    if not response.ok:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"   错误详情: {response.text}")
        return
    
    try:
        result = response.json()
        print(f"📋 响应结构: {list(result.keys())}")
        
        # 分析响应内容
        assistant_content = ""
        tool_calls = None
        
        if 'response' in result:
            # Agent API返回格式：result.response.content
            assistant_content = result['response'].get('content', '') if result.get('response') else ''
            tool_calls = result['response'].get('tool_calls', []) if result.get('response') else []
        elif 'content' in result:
            # 直接格式
            assistant_content = result.get('content', '')
            tool_calls = result.get('tool_calls', [])
        
        print(f"\n🎯 测试结果分析:")
        print(f"   📝 助手回复长度: {len(assistant_content)} 字符")
        print(f"   🔧 工具调用数量: {len(tool_calls) if tool_calls else 0}")
        
        if tool_calls:
            print(f"   🎉 成功：检测到工具调用!")
            for i, tool_call in enumerate(tool_calls):
                tool_name = tool_call.get('function', {}).get('name', 'unknown')
                print(f"     🔧 工具{i+1}: {tool_name}")
                if tool_name == 'qimen_dunjia':
                    print(f"     ✅ 奇门遁甲工具调用成功!")
        else:
            print(f"   ❌ 问题：没有检测到工具调用")
            print(f"   💡 可能原因：")
            print(f"      1. 前端和后端协议不匹配")
            print(f"      2. 非流式请求处理逻辑不同")
            print(f"      3. 缺少protocol参数导致默认协议错误")
        
        # 显示助手回复内容
        if assistant_content:
            print(f"\n📄 助手回复预览:")
            preview = assistant_content[:200] + "..." if len(assistant_content) > 200 else assistant_content
            print(f"   {preview}")
        
        # 显示完整响应用于调试
        print(f"\n🔍 完整响应 (调试用):")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:1000] + "...")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        print(f"   原始响应: {response.text[:500]}...")
    except Exception as e:
        print(f"❌ 处理响应时出错: {e}")

if __name__ == "__main__":
    test_frontend_style_request() 