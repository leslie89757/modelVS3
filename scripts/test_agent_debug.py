#!/usr/bin/env python3
"""测试Agent调试功能"""

import asyncio
import httpx
import time
import json

async def test_agent_debug():
    """测试Agent调试API调用，模拟前端请求"""
    
    print("🧪 测试Agent调试功能...")
    print("=" * 50)
    
    # 获取可用的Agent
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            print("1️⃣ 获取Agent列表...")
            agents_response = await client.get("http://localhost:3003/api/v1/agents/")
            if agents_response.status_code != 200:
                print(f"❌ 获取Agent列表失败: {agents_response.status_code}")
                return False
                
            agents = agents_response.json()
            if not agents:
                print("❌ 没有可用的Agent")
                return False
                
            agent = agents[0]  # 使用第一个Agent
            print(f"✅ 找到Agent: {agent['name']} ({agent['id']})")
            
        except Exception as e:
            print(f"❌ 获取Agent失败: {e}")
            return False
    
    # 测试Agent调试请求
    test_payload = {
        "agent_id": agent['id'],
        "messages": [
            {
                "role": "user", 
                "content": "你好，这是一个Agent调试测试。请简单回复确认。"
            }
        ],
        "stream": False,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    print("2️⃣ 发送Agent调试请求...")
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5分钟超时
        try:
            response = await client.post(
                "http://localhost:3003/api/v1/runs/",
                headers={"Content-Type": "application/json"},
                json=test_payload
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            print(f"📊 响应状态: {response.status_code}")
            print(f"⏱️  响应时间: {response_time:.2f}ms")
            
            if response.status_code == 201:
                result = response.json()
                print("✅ Agent调试请求成功！")
                print(f"🆔 Run ID: {result['id']}")
                print(f"📊 状态: {result['status']}")
                
                if result.get('response'):
                    print(f"🤖 Assistant回复: {result['response'].get('content', '无内容')}")
                
                return True
                
            elif response.status_code == 504:
                print("❌ 504 Gateway Timeout - Nginx超时配置可能还没生效")
                return False
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误详情: {error_data}")
                except:
                    print(f"错误文本: {response.text}")
                return False
                
        except httpx.TimeoutException:
            print("❌ 请求超时 - 可能需要更长的等待时间")
            return False
            
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False

async def main():
    print("🔧 Agent Designer 504超时问题修复验证")
    print(f"⏰ 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    success = await test_agent_debug()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Agent调试功能正常！504超时问题已修复！")
        print("💡 您现在可以在前端正常使用Agent Designer了")
    else:
        print("❌ 仍存在问题，需要进一步调试")
        print("🔧 可能需要等待更长时间或检查配置")

if __name__ == "__main__":
    asyncio.run(main())
