"""ModelVS3 API 客户端工具"""

import httpx
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModelVS3Client:
    """ModelVS3 Agent 平台 API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=self._get_headers(),
            timeout=30.0
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ModelVS3-Python-Client/1.0.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # Agent 管理
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建 Agent"""
        response = await self.client.post("/api/v1/agents/", json=agent_data)
        response.raise_for_status()
        return response.json()
    
    async def get_agents(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取 Agent 列表"""
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        
        response = await self.client.get("/api/v1/agents/", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """获取单个 Agent"""
        response = await self.client.get(f"/api/v1/agents/{agent_id}")
        response.raise_for_status()
        return response.json()
    
    async def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新 Agent"""
        response = await self.client.patch(f"/api/v1/agents/{agent_id}", json=agent_data)
        response.raise_for_status()
        return response.json()
    
    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """删除 Agent"""
        response = await self.client.delete(f"/api/v1/agents/{agent_id}")
        response.raise_for_status()
        return response.json()
    
    async def activate_agent(self, agent_id: str) -> Dict[str, Any]:
        """激活 Agent"""
        response = await self.client.post(f"/api/v1/agents/{agent_id}/activate")
        response.raise_for_status()
        return response.json()
    
    async def pause_agent(self, agent_id: str) -> Dict[str, Any]:
        """暂停 Agent"""
        response = await self.client.post(f"/api/v1/agents/{agent_id}/pause")
        response.raise_for_status()
        return response.json()
    
    # 模型管理
    async def create_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建模型"""
        response = await self.client.post("/api/v1/models/", json=model_data)
        response.raise_for_status()
        return response.json()
    
    async def get_models(self, provider: Optional[str] = None, enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取模型列表"""
        params = {}
        if provider:
            params["provider"] = provider
        if enabled is not None:
            params["enabled"] = enabled
        
        response = await self.client.get("/api/v1/models/", params=params)
        response.raise_for_status()
        return response.json()
    
    # 工具管理
    async def create_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建工具"""
        response = await self.client.post("/api/v1/tools/", json=tool_data)
        response.raise_for_status()
        return response.json()
    
    async def get_tools(self, enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取工具列表"""
        params = {}
        if enabled is not None:
            params["enabled"] = enabled
        
        response = await self.client.get("/api/v1/tools/", params=params)
        response.raise_for_status()
        return response.json()
    
    # Agent 执行
    async def run_agent(
        self, 
        agent_id: str, 
        messages: List[Dict[str, Any]], 
        stream: bool = False,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """执行 Agent"""
        
        run_data = {
            "agent_id": agent_id,
            "messages": messages,
            "stream": stream
        }
        
        if max_tokens:
            run_data["max_tokens"] = max_tokens
        if temperature is not None:
            run_data["temperature"] = temperature
        
        response = await self.client.post("/api/v1/runs/", json=run_data)
        response.raise_for_status()
        return response.json()
    
    async def stream_agent(
        self, 
        agent_id: str, 
        messages: List[Dict[str, Any]], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行 Agent"""
        
        run_data = {
            "agent_id": agent_id,
            "messages": messages,
            "stream": True
        }
        
        if max_tokens:
            run_data["max_tokens"] = max_tokens
        if temperature is not None:
            run_data["temperature"] = temperature
        
        async with self.client.stream("POST", "/api/v1/runs/", json=run_data) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # 移除 "data: " 前缀
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        logger.warning(f"无法解析 JSON: {data}")
    
    async def get_runs(
        self, 
        agent_id: Optional[str] = None, 
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取执行列表"""
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status"] = status
        
        response = await self.client.get("/api/v1/runs/", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_run(self, run_id: str) -> Dict[str, Any]:
        """获取单个执行记录"""
        response = await self.client.get(f"/api/v1/runs/{run_id}")
        response.raise_for_status()
        return response.json()
    
    # OpenAI 兼容接口
    async def chat_completions(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """OpenAI 兼容的聊天完成接口"""
        
        data = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens:
            data["max_tokens"] = max_tokens
        if tools:
            data["tools"] = tools
        
        response = await self.client.post("/v1/chat/completions", json=data)
        response.raise_for_status()
        return response.json()
    
    # 仪表板数据
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表板统计"""
        response = await self.client.get("/api/v1/dashboard/stats")
        response.raise_for_status()
        return response.json()
    
    async def get_usage_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取使用统计"""
        response = await self.client.get(f"/api/v1/dashboard/usage?days={days}")
        response.raise_for_status()
        return response.json()
    
    # 系统状态
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()


# 便捷函数
async def create_simple_agent(
    client: ModelVS3Client,
    name: str,
    system_prompt: str,
    model: str = "gpt-4",
    tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """创建简单的 Agent"""
    
    agent_schema = {
        "version": "2025-07",
        "model": model,
        "strategy": "react",
        "system_prompt": system_prompt,
        "max_iterations": 4,
        "timeout": 60,
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
    
    if tools:
        agent_schema["tools"] = [{"name": tool, "required": False} for tool in tools]
    
    agent_data = {
        "name": name,
        "description": f"由 API 客户端创建的 {name}",
        "schema": agent_schema,
        "status": "active"
    }
    
    return await client.create_agent(agent_data)


async def quick_chat(
    client: ModelVS3Client,
    agent_id: str,
    message: str,
    stream: bool = False
) -> str:
    """快速聊天"""
    
    messages = [{"role": "user", "content": message}]
    
    if stream:
        response_text = ""
        async for event in client.stream_agent(agent_id, messages):
            if event.get("type") == "llm_response":
                response_text += event.get("response", {}).get("content", "")
        return response_text
    else:
        response = await client.run_agent(agent_id, messages)
        # 这里需要从执行记录中获取最终响应，暂时返回状态
        return f"执行完成，状态: {response.get('status', 'unknown')}" 