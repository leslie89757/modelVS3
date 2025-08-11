#!/usr/bin/env python3
"""测试DeepSeek模型连接"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Model
import httpx

async def test_deepseek_connection():
    # 连接数据库
    database_url = "postgresql://postgres:password@postgres:5432/modelvs3"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 查询DeepSeek模型
        deepseek_model = db.query(Model).filter(Model.name == "deepseek-chat").first()
        
        if not deepseek_model:
            print("❌ 未找到DeepSeek模型配置")
            return
            
        print(f"🔍 测试模型: {deepseek_model.name}")
        print(f"🌐 API端点: {deepseek_model.endpoint}")
        print(f"🔑 API密钥: {'已配置' if deepseek_model.api_key else '未配置'}")
        print("=" * 60)
        
        if not deepseek_model.api_key:
            print("❌ 缺少API密钥，无法测试连接")
            return
            
        # 准备测试请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {deepseek_model.api_key}"
        }
        
        test_payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "你好，这是一个连接测试。请简单回复一下。"}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        print("🚀 发送测试请求...")
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    deepseek_model.endpoint,
                    headers=headers,
                    json=test_payload
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                print(f"📊 响应状态: {response.status_code}")
                print(f"⏱️  响应时间: {response_time:.2f}ms")
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ 连接成功！")
                    print(f"🤖 模型响应: {result.get('choices', [{}])[0].get('message', {}).get('content', '无响应内容')}")
                    
                    # 显示使用量信息
                    if 'usage' in result:
                        usage = result['usage']
                        print(f"📈 Token使用: 输入{usage.get('prompt_tokens', 0)}, 输出{usage.get('completion_tokens', 0)}, 总计{usage.get('total_tokens', 0)}")
                    
                    return True
                    
                elif response.status_code == 401:
                    print("❌ 认证失败 - API密钥可能无效或已过期")
                    print(f"错误响应: {response.text}")
                    
                elif response.status_code == 429:
                    print("❌ 请求过于频繁 - 触发限流")
                    print(f"错误响应: {response.text}")
                    
                elif response.status_code == 500:
                    print("❌ 服务器内部错误")
                    print(f"错误响应: {response.text}")
                    
                else:
                    print(f"❌ 连接失败，状态码: {response.status_code}")
                    print(f"错误响应: {response.text}")
                    
                return False
                
            except httpx.TimeoutException:
                print("❌ 请求超时 - 网络连接可能有问题")
                return False
                
            except httpx.ConnectError:
                print("❌ 连接错误 - 无法连接到DeepSeek服务器")
                print("可能原因：")
                print("  1. 网络连接问题")
                print("  2. DNS解析问题") 
                print("  3. 防火墙阻止")
                print("  4. 代理设置问题")
                return False
                
            except Exception as e:
                print(f"❌ 未知错误: {e}")
                return False
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        return False
    finally:
        db.close()

async def test_network():
    """测试基础网络连接"""
    print("\n🌐 测试基础网络连接...")
    
    test_urls = [
        "https://www.baidu.com",
        "https://api.deepseek.com",
        "https://www.google.com"
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in test_urls:
            try:
                start_time = time.time()
                response = await client.get(url)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code < 400:
                    print(f"✅ {url} - {response.status_code} ({response_time:.2f}ms)")
                else:
                    print(f"⚠️  {url} - {response.status_code} ({response_time:.2f}ms)")
                    
            except Exception as e:
                print(f"❌ {url} - 连接失败: {e}")

async def main():
    print("🔧 DeepSeek连接测试工具")
    print("⏰ 开始时间:", time.strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # 测试网络连接
    await test_network()
    
    print("\n" + "=" * 60)
    
    # 测试DeepSeek连接
    success = await test_deepseek_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DeepSeek连接测试成功！")
    else:
        print("❌ DeepSeek连接测试失败")
        print("\n🔧 故障排除建议：")
        print("1. 检查网络连接是否正常")
        print("2. 确认API密钥是否有效")
        print("3. 检查是否有代理或防火墙设置")
        print("4. 尝试在浏览器中访问 https://api.deepseek.com")
        print("5. 检查API调用频率是否超限")

if __name__ == "__main__":
    asyncio.run(main())
