"""OpenAI 兼容的聊天接口"""

import time
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChatCompletionRequest, ChatCompletionResponse
from ..models import Model
from ..config import settings

router = APIRouter()


async def call_llm_api(model: Model, messages: list, temperature: float = 0.7, max_tokens: int = 2000, stream: bool = False):
    """调用LLM API"""
    
    # 检查是否需要mock响应（当API key不可用时）
    use_mock = False
    api_key = None
    
    # 优先使用模型自己的API key，然后回退到全局配置
    if model.api_key:
        api_key = model.api_key
    elif model.provider == 'openai':
        api_key = settings.openai_api_key
    elif model.provider == 'anthropic':
        api_key = settings.anthropic_api_key
    elif model.provider == 'google':
        api_key = settings.google_api_key
    
    if not api_key or api_key == "":
        use_mock = True
    
    # 如果没有API key，返回mock响应
    if use_mock:
        import time
        import uuid
        
        # 模拟处理时间
        await asyncio.sleep(0.5)
        
        # 获取用户的最后一条消息
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        mock_response = f"这是来自 {model.name} 的模拟响应。您发送的消息是：\"{user_message}\"\n\n请注意：这是一个演示响应，因为没有配置相应的API密钥。要获得真实的AI响应，请在系统设置中配置相应的API密钥。"
        
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model.name,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": mock_response
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(str(messages)),
                "completion_tokens": len(mock_response),
                "total_tokens": len(str(messages)) + len(mock_response)
            }
        }
    
    # 正常的API调用
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 根据提供商添加认证头
    if model.provider == 'openai' or model.provider == 'custom':
        # OpenAI和大多数custom提供商都使用Bearer token
        headers['Authorization'] = f'Bearer {api_key}'
    elif model.provider == 'anthropic':
        headers['x-api-key'] = api_key
        headers['anthropic-version'] = '2023-06-01'
    elif model.provider == 'google':
        headers['Authorization'] = f'Bearer {api_key}'
    
    payload = {
        "model": model.name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(str(model.endpoint), headers=headers, json=payload)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"LLM API调用失败: {response.text}"
            )
        
        return response.json()


async def stream_llm_response(model: Model, messages: list, temperature: float = 0.7, max_tokens: int = 2000):
    """流式LLM响应"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 根据提供商添加认证头
    if model.provider == 'openai':
        api_key = settings.openai_api_key
        if api_key is not None and api_key != "":
            headers['Authorization'] = f'Bearer {api_key}'
    elif model.provider == 'anthropic':
        api_key = settings.anthropic_api_key
        if api_key is not None and api_key != "":
            headers['x-api-key'] = api_key
            headers['anthropic-version'] = '2023-06-01'
    elif model.provider == 'google':
        api_key = settings.google_api_key
        if api_key is not None and api_key != "":
            headers['Authorization'] = f'Bearer {api_key}'
    # 其他提供商需要用户自己配置API key
    
    payload = {
        "model": model.name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream('POST', str(model.endpoint), headers=headers, json=payload) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM API调用失败: {error_text}"
                )
            
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        yield f"data: [DONE]\n\n"
                        break
                    try:
                        import json
                        json_data = json.loads(data)
                        yield f"data: {json.dumps(json_data, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        continue


@router.post("/chat/completions", summary="聊天完成接口 (OpenAI 兼容)")
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db)
):
    """OpenAI 兼容的聊天完成接口"""
    
    # 获取模型配置
    model = db.query(Model).filter(Model.name == request.model).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型 {request.model} 不存在"
        )
    
    if model.enabled is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"模型 {request.model} 未启用"
        )
    
    # 转换消息格式
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    if request.stream:
        # 流式响应
        return StreamingResponse(
            stream_llm_response(
                model, 
                messages, 
                request.temperature or 0.7, 
                request.max_tokens or 2000
            ),
            media_type="text/plain"
        )
    else:
        # 非流式响应
        try:
            result = await call_llm_api(
                model,
                messages,
                request.temperature or 0.7,
                request.max_tokens or 2000
            )
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM API调用失败: {str(e)}"
            ) 