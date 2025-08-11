#!/usr/bin/env python3
"""
ModelVS3 命令行工具
提供平台管理和快速操作功能
"""

import asyncio
import json
import sys
from typing import Optional, List
import click
import subprocess
import os

from src.utils.api_client import ModelVS3Client, create_simple_agent, quick_chat


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """ModelVS3 Agent 平台命令行工具"""
    pass


@cli.group()
def server():
    """服务器管理命令"""
    pass


@server.command()
@click.option("--port", default=8000, help="服务器端口")
@click.option("--host", default="0.0.0.0", help="服务器地址")
@click.option("--reload", is_flag=True, help="启用热重载")
def start(port: int, host: str, reload: bool):
    """启动 ModelVS3 服务器"""
    click.echo(f"🚀 正在启动 ModelVS3 服务器 {host}:{port}")
    
    cmd = ["uvicorn", "src.main:app", f"--host={host}", f"--port={port}"]
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\n✅ 服务器已停止")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 启动失败: {e}")


@server.command()
def stop():
    """停止 ModelVS3 服务器"""
    click.echo("🛑 正在停止服务器...")
    # 这里可以添加停止服务器的逻辑
    click.echo("✅ 服务器已停止")


@cli.group()
def db():
    """数据库管理命令"""
    pass


@db.command()
def init():
    """初始化数据库"""
    click.echo("🔧 正在初始化数据库...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        click.echo("✅ 数据库初始化完成")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 数据库初始化失败: {e}")


@db.command()
def seed():
    """填充种子数据"""
    click.echo("🌱 正在填充种子数据...")
    try:
        subprocess.run(["python3", "scripts/seed_data.py"], check=True)
        click.echo("✅ 种子数据填充完成")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 种子数据填充失败: {e}")


@db.command()
def reset():
    """重置数据库（危险操作）"""
    if click.confirm("⚠️  这将删除所有数据，确定要继续吗？"):
        click.echo("🔄 正在重置数据库...")
        try:
            subprocess.run(["alembic", "downgrade", "base"], check=True)
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            click.echo("✅ 数据库重置完成")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ 数据库重置失败: {e}")


@cli.group()
def agent():
    """Agent 管理命令"""
    pass


@agent.command()
@click.option("--url", default="http://localhost:8000", help="API 地址")
@click.option("--token", help="API 令牌")
def list_agents(url: str, token: Optional[str]):
    """列出所有 Agent"""
    async def _list():
        async with ModelVS3Client(url, token) as client:
            agents = await client.get_agents()
            
            if not agents:
                click.echo("📭 暂无 Agent")
                return
            
            click.echo("🎯 Agent 列表:")
            for agent in agents:
                status_icon = "🟢" if agent["status"] == "active" else "🔴"
                click.echo(f"  {status_icon} {agent['name']} ({agent['id'][:8]}...)")
                click.echo(f"     {agent.get('description', '无描述')}")
    
    asyncio.run(_list())


@agent.command()
@click.argument("name")
@click.argument("system_prompt")
@click.option("--model", default="gpt-4", help="使用的模型")
@click.option("--tools", help="工具列表，用逗号分隔")
@click.option("--url", default="http://localhost:8000", help="API 地址")
@click.option("--token", help="API 令牌")
def create(name: str, system_prompt: str, model: str, tools: Optional[str], url: str, token: Optional[str]):
    """创建新 Agent"""
    async def _create():
        tool_list = tools.split(",") if tools else None
        
        async with ModelVS3Client(url, token) as client:
            agent = await create_simple_agent(client, name, system_prompt, model, tool_list)
            click.echo(f"✅ Agent '{name}' 创建成功")
            click.echo(f"   ID: {agent['id']}")
    
    asyncio.run(_create())


@agent.command()
@click.argument("agent_id")
@click.argument("message")
@click.option("--stream", is_flag=True, help="启用流式输出")
@click.option("--url", default="http://localhost:8000", help="API 地址")
@click.option("--token", help="API 令牌")
def chat(agent_id: str, message: str, stream: bool, url: str, token: Optional[str]):
    """与 Agent 聊天"""
    async def _chat():
        async with ModelVS3Client(url, token) as client:
            click.echo(f"💬 与 Agent {agent_id[:8]}... 聊天:")
            click.echo(f"👤 {message}")
            
            response = await quick_chat(client, agent_id, message, stream)
            click.echo(f"🤖 {response}")
    
    asyncio.run(_chat())


@cli.group()
def model():
    """模型管理命令"""
    pass


@model.command()
@click.option("--url", default="http://localhost:8000", help="API 地址")
@click.option("--token", help="API 令牌")
def list_models(url: str, token: Optional[str]):
    """列出所有模型"""
    async def _list():
        async with ModelVS3Client(url, token) as client:
            models = await client.get_models()
            
            if not models:
                click.echo("📭 暂无模型")
                return
            
            click.echo("🤖 模型列表:")
            for model in models:
                status_icon = "🟢" if model["enabled"] else "🔴"
                pricing = model.get("pricing", {})
                price_info = f"${pricing.get('input', 0)}/{pricing.get('output', 0)}" if pricing else "无定价"
                
                click.echo(f"  {status_icon} {model['name']} ({model['provider']})")
                click.echo(f"     Context: {model['context_len']} tokens | Price: {price_info}")
    
    asyncio.run(_list())


@cli.group()
def tool():
    """工具管理命令"""
    pass


@tool.command()
@click.option("--url", default="http://localhost:8000", help="API 地址")
@click.option("--token", help="API 令牌")
def list_tools(url: str, token: Optional[str]):
    """列出所有工具"""
    async def _list():
        async with ModelVS3Client(url, token) as client:
            tools = await client.get_tools()
            
            if not tools:
                click.echo("📭 暂无工具")
                return
            
            click.echo("🔧 工具列表:")
            for tool in tools:
                status_icon = "🟢" if tool["enabled"] else "🔴"
                click.echo(f"  {status_icon} {tool['name']}")
                click.echo(f"     {tool.get('description', '无描述')}")
    
    asyncio.run(_list())


@cli.group()
def deploy():
    """部署管理命令"""
    pass


@deploy.command()
@click.option("--env", default="production", help="部署环境")
def docker(env: str):
    """使用 Docker 部署"""
    click.echo(f"🐳 正在使用 Docker 部署到 {env} 环境...")
    
    try:
        # 构建镜像
        click.echo("📦 构建 Docker 镜像...")
        subprocess.run(["docker", "build", "-t", "modelvs3:latest", "."], check=True)
        
        # 启动服务
        click.echo("🚀 启动服务...")
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        
        click.echo("✅ 部署完成！")
        click.echo("🌐 访问地址: http://localhost:8000")
        click.echo("📊 监控地址: http://localhost:3000")
        
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 部署失败: {e}")


@deploy.command()
def status():
    """查看部署状态"""
    click.echo("📊 检查部署状态...")
    
    try:
        result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
        click.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 获取状态失败: {e}")


@deploy.command()
def logs():
    """查看部署日志"""
    click.echo("📋 查看部署日志...")
    
    try:
        subprocess.run(["docker-compose", "logs", "-f"], check=True)
    except KeyboardInterrupt:
        click.echo("\n✅ 停止查看日志")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 获取日志失败: {e}")


@cli.command()
@click.option("--url", default="http://localhost:8000", help="API 地址")
def health(url: str):
    """健康检查"""
    async def _health():
        try:
            async with ModelVS3Client(url) as client:
                status = await client.health_check()
                
                if status.get("status") == "healthy":
                    click.echo("✅ 服务运行正常")
                    click.echo(f"   版本: {status.get('version', 'unknown')}")
                    click.echo(f"   时间: {status.get('timestamp', 'unknown')}")
                else:
                    click.echo("⚠️  服务状态异常")
                    
        except Exception as e:
            click.echo(f"❌ 服务不可用: {e}")
    
    asyncio.run(_health())


@cli.command()
def version():
    """显示版本信息"""
    click.echo("ModelVS3 Agent Platform")
    click.echo("Version: 1.0.0")
    click.echo("Build: 2025-01-15")


if __name__ == "__main__":
    cli() 