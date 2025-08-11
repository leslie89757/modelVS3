"""LLM 适配器模块"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """LLM 适配器基类"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None
    ) -> Dict[str, Any]:
        """聊天完成"""
        pass


class OpenAICompatibleAdapter(BaseLLMAdapter):
    """OpenAI 兼容适配器"""
    
    def __init__(
        self, 
        model_name: str,
        endpoint: str,
        api_key: Optional[str] = None,
        provider: str = "openai",
        custom_headers: Optional[Dict[str, str]] = None
    ):
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_key = api_key
        self.provider = provider
        self.custom_headers = custom_headers or {}
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json",
            **self.custom_headers
        }
        
        if self.api_key:
            if self.provider == "anthropic":
                headers["x-api-key"] = self.api_key
            elif self.provider == "google":
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None
    ) -> Dict[str, Any]:
        """构建请求载荷"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # 添加可选参数
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        return payload
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None
    ) -> Dict[str, Any]:
        """聊天完成"""
        try:
            logger.info(f"🚀 LLM API调用开始")
            logger.info(f"   模型: {self.model_name}")
            logger.info(f"   端点: {self.endpoint}")
            logger.info(f"   提供商: {self.provider}")
            logger.info(f"   工具数量: {len(tools) if tools else 0}")
            
            headers = self._build_headers()
            payload = self._build_payload(
                messages, temperature, max_tokens, tools,
                top_p, frequency_penalty, presence_penalty
            )
            
            logger.info(f"📨 请求载荷: {payload}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )
                
                logger.info(f"📥 API响应状态: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"API请求失败: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                result = response.json()
                logger.info(f"📋 原始响应: {result}")
                
                parsed_result = self._parse_response(result, bool(tools))
                logger.info(f"✅ 解析后响应: {parsed_result}")
                
                return parsed_result
                
        except Exception as e:
            logger.error(f"❌ LLM API调用失败: {e}")
            raise
    
    def _parse_response(self, response: Dict[str, Any], has_tools: bool) -> Dict[str, Any]:
        """解析响应"""
        content = None
        tool_calls = None
        
        if "choices" in response:
            choice = response["choices"][0]
            message = choice.get("message", {})
            
            # 始终尝试获取content，无论是否有工具调用
            content = message.get("content")
            
            # 如果启用了工具且有工具调用，也获取工具调用
            if has_tools and "tool_calls" in message:
                tool_calls = message["tool_calls"]
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "usage": response.get("usage", {}),
            "model": response.get("model", self.model_name)
        }


class LLMAdapterFactory:
    """LLM 适配器工厂"""
    
    def __init__(self):
        self._adapters = {}
    
    async def get_adapter(
        self, 
        model_name: str,
        endpoint: str,
        provider: str = "openai",
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        use_mock: bool = False
    ) -> BaseLLMAdapter:
        """获取 LLM 适配器"""
        
        adapter_key = f"{model_name}:{endpoint}:{provider}"
        
        if adapter_key in self._adapters:
            return self._adapters[adapter_key]
        
        # 创建适配器
        if use_mock:
            raise ValueError("模拟适配器已禁用，请使用真实的LLM适配器")
        else:
            adapter = OpenAICompatibleAdapter(
                model_name=model_name,
                endpoint=endpoint,
                api_key=api_key,
                provider=provider,
                custom_headers=custom_headers
            )
        
        self._adapters[adapter_key] = adapter
        return adapter
    
    def clear_cache(self):
        """清除适配器缓存"""
        self._adapters.clear()


# 全局适配器工厂实例
llm_factory = LLMAdapterFactory() 