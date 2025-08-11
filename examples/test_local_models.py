#!/usr/bin/env python3
"""
测试本地模型配置的示例

这个脚本演示如何配置和使用本地部署的模型，包括：
- Ollama
- LocalAI
- vLLM
- 自定义 OpenAI 兼容 API
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_adapters import OpenAICompatibleAdapter


async def test_ollama():
    """测试 Ollama 本地模型"""
    print("🦙 测试 Ollama 本地模型...")
    
    adapter = OpenAICompatibleAdapter(
        model_name="llama2:7b",
        endpoint="http://localhost:11434/v1/chat/completions",
        provider="ollama"
    )
    
    try:
        response = await adapter.chat_completion(
            messages=[
                {"role": "user", "content": "Hello! Please respond briefly."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        print("✅ Ollama 响应成功:")
        print(f"   Content: {response.get('content', 'No content')}")
        print(f"   Model: {response.get('model', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Ollama 连接失败: {str(e)}")
        print("   请确保 Ollama 服务正在运行: ollama serve")


async def test_localai():
    """测试 LocalAI"""
    print("\n🤖 测试 LocalAI...")
    
    adapter = OpenAICompatibleAdapter(
        model_name="gpt-3.5-turbo",
        endpoint="http://localhost:8080/v1/chat/completions",
        provider="localai"
    )
    
    try:
        response = await adapter.chat_completion(
            messages=[
                {"role": "user", "content": "Hello! Please respond briefly."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        print("✅ LocalAI 响应成功:")
        print(f"   Content: {response.get('content', 'No content')}")
        print(f"   Model: {response.get('model', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ LocalAI 连接失败: {str(e)}")
        print("   请确保 LocalAI 服务正在运行")


async def test_vllm():
    """测试 vLLM 推理服务器"""
    print("\n⚡ 测试 vLLM...")
    
    adapter = OpenAICompatibleAdapter(
        model_name="microsoft/DialoGPT-medium",
        endpoint="http://localhost:8000/v1/chat/completions",
        provider="vllm"
    )
    
    try:
        response = await adapter.chat_completion(
            messages=[
                {"role": "user", "content": "Hello! Please respond briefly."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        print("✅ vLLM 响应成功:")
        print(f"   Content: {response.get('content', 'No content')}")
        print(f"   Model: {response.get('model', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ vLLM 连接失败: {str(e)}")
        print("   请确保 vLLM 服务正在运行")


async def test_custom_api():
    """测试自定义 API（带自定义 headers）"""
    print("\n🔧 测试自定义 API...")
    
    custom_headers = {
        "X-Custom-Auth": "my-secret-token",
        "User-Agent": "ModelVS3/1.0"
    }
    
    adapter = OpenAICompatibleAdapter(
        model_name="custom-model",
        endpoint="http://localhost:9000/v1/chat/completions",
        provider="custom",
        custom_headers=custom_headers
    )
    
    try:
        response = await adapter.chat_completion(
            messages=[
                {"role": "user", "content": "Hello! Please respond briefly."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        print("✅ 自定义 API 响应成功:")
        print(f"   Content: {response.get('content', 'No content')}")
        print(f"   Model: {response.get('model', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ 自定义 API 连接失败: {str(e)}")
        print("   请确保您的自定义 API 服务正在运行")


async def test_tool_calling():
    """测试工具调用功能"""
    print("\n🔨 测试工具调用...")
    
    # 使用 Ollama 测试工具调用
    adapter = OpenAICompatibleAdapter(
        model_name="llama2:7b",
        endpoint="http://localhost:11434/v1/chat/completions",
        provider="ollama"
    )
    
    tools = [
        {
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
        }
    ]
    
    try:
        response = await adapter.chat_completion(
            messages=[
                {"role": "user", "content": "请计算 15 + 27 = ?"}
            ],
            temperature=0.1,
            max_tokens=100,
            tools=tools
        )
        
        print("✅ 工具调用测试:")
        if response.get("tool_calls"):
            print(f"   工具调用: {response['tool_calls']}")
        else:
            print(f"   普通响应: {response.get('content', 'No content')}")
        
    except Exception as e:
        print(f"❌ 工具调用测试失败: {str(e)}")


def print_setup_instructions():
    """打印设置说明"""
    print("📋 本地模型设置说明:")
    print()
    print("1. Ollama 设置:")
    print("   - 安装: https://ollama.ai/")
    print("   - 启动: ollama serve")
    print("   - 下载模型: ollama pull llama2:7b")
    print()
    print("2. LocalAI 设置:")
    print("   - 项目: https://github.com/go-skynet/LocalAI")
    print("   - Docker: docker run -p 8080:8080 localai/localai")
    print()
    print("3. vLLM 设置:")
    print("   - 安装: pip install vllm")
    print("   - 启动: python -m vllm.entrypoints.openai.api_server \\")
    print("            --model microsoft/DialoGPT-medium --port 8000")
    print()
    print("4. 自定义 API:")
    print("   - 任何兼容 OpenAI Chat Completions API 的服务")
    print("   - 支持自定义认证和 headers")
    print()


async def main():
    """主函数"""
    print("🚀 ModelVS3 本地模型配置测试")
    print("=" * 50)
    
    print_setup_instructions()
    
    print("开始测试本地模型连接...")
    print("=" * 50)
    
    # 按顺序测试各种本地模型配置
    await test_ollama()
    await test_localai() 
    await test_vllm()
    await test_custom_api()
    await test_tool_calling()
    
    print("\n" + "=" * 50)
    print("✨ 测试完成！")
    print()
    print("💡 提示:")
    print("- 如果某个服务连接失败，请检查该服务是否正在运行")
    print("- 您可以在 ModelVS3 前端界面中添加这些本地模型")
    print("- 本地模型通常不需要 API 密钥")


if __name__ == "__main__":
    asyncio.run(main()) 