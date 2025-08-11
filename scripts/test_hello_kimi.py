#!/usr/bin/env python3
"""
测试更新系统提示词后的kimi----128K Agent是否会对"你好"也调用奇门工具
"""

import requests
import json

# 开发环境API
API_BASE = "http://localhost:8001/api/v1"

def test_hello_with_qimen():
    """测试简单问候是否会触发奇门工具调用"""
    
    print("🧪 测试更新后的kimi----128K Agent对'你好'的响应...")
    
    # 开发环境kimi----128K Agent ID
    agent_id = "f810186c-9381-43f3-847d-f034437d1782"
    
    # 用简单的"你好"测试
    run_request = {
        "agent_id": agent_id,
        "messages": [
            {
                "role": "user", 
                "content": "你好"  # 简单问候
            }
        ],
        "stream": False
    }
    
    print("🚀 发送问候请求...")
    
    # 发送请求
    response = requests.post(f"{API_BASE}/runs/", json=run_request)
    
    if not response.ok:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"   错误详情: {response.text}")
        return
    
    try:
        result = response.json()
        
        # 分析响应
        assistant_content = result.get('response', {}).get('content', '')
        tool_calls = result.get('response', {}).get('tool_calls', [])
        
        print(f"\n🎯 测试结果:")
        print(f"   📝 回复长度: {len(assistant_content)} 字符")
        print(f"   🔧 工具调用数量: {len(tool_calls)}")
        
        if tool_calls:
            print(f"   🎉 成功：检测到工具调用!")
            for tool_call in tool_calls:
                tool_name = tool_call.get('function', {}).get('name', 'unknown')
                print(f"     🔧 调用工具: {tool_name}")
                if tool_name == 'qimen_dunjia':
                    print(f"     ✅ 强制奇门工具调用成功！")
        else:
            print(f"   ❌ 失败：仍然没有调用工具")
        
        # 显示回复内容
        print(f"\n📄 Agent回复:")
        print(f"   {assistant_content}")
        
        # 判断成功标准
        has_qimen_tool = any(tc.get('function', {}).get('name') == 'qimen_dunjia' for tc in tool_calls)
        has_qimen_terms = any(term in assistant_content for term in ['值符', '值使', '九宫', '奇门', '遁甲', '干支'])
        
        if has_qimen_tool and has_qimen_terms:
            print(f"\n🎊 完美！Agent现在会对任何输入都先调用奇门工具！")
        elif has_qimen_tool:
            print(f"\n✅ 进步！Agent调用了奇门工具，但回复中可能没有充分体现")
        else:
            print(f"\n❌ 问题：Agent仍然没有调用奇门工具")
            print(f"   💡 可能需要进一步调整系统提示词")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
    except Exception as e:
        print(f"❌ 处理响应时出错: {e}")

if __name__ == "__main__":
    test_hello_with_qimen() 