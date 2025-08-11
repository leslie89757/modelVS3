"""聊天测试路由"""

import time
import httpx
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChatCompletionRequest, ChatCompletionResponse
from ..models import Model
from ..config import settings

router = APIRouter()


async def call_llm_api_for_test(model: Model, messages: list, temperature: float = 0.7, max_tokens: int = 2000, stream: bool = False):
    """调用LLM API进行测试"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 优先使用模型配置中的API密钥，然后使用系统设置中的API密钥
    api_key = None
    if model.api_key and model.api_key.strip():
        api_key = model.api_key.strip()
    elif model.provider == 'openai':
        api_key = settings.openai_api_key
    elif model.provider == 'anthropic':
        api_key = settings.anthropic_api_key
    elif model.provider == 'google':
        api_key = settings.google_api_key
    
    # 根据提供商添加认证头
    if api_key:
        if model.provider == 'openai' or model.provider == 'custom':
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


async def stream_llm_response_for_test(model: Model, messages: list, temperature: float = 0.7, max_tokens: int = 2000):
    """流式LLM响应测试"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 优先使用模型配置中的API密钥，然后使用系统设置中的API密钥
    api_key = None
    if model.api_key and model.api_key.strip():
        api_key = model.api_key.strip()
    elif model.provider == 'openai':
        api_key = settings.openai_api_key
    elif model.provider == 'anthropic':
        api_key = settings.anthropic_api_key
    elif model.provider == 'google':
        api_key = settings.google_api_key
    
    # 根据提供商添加认证头
    if api_key:
        if model.provider == 'openai' or model.provider == 'custom':
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
                elif line.strip():
                    # 处理非SSE格式的响应
                    yield f"data: {line}\n\n"


@router.post("/test", response_model=ChatCompletionResponse, summary="测试聊天接口")
async def test_chat(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db)
):
    """测试聊天接口"""
    
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
            stream_llm_response_for_test(
                model, 
                messages, 
                request.temperature or 0.7, 
                request.max_tokens or 2000
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    else:
        # 非流式响应
        try:
            result = await call_llm_api_for_test(
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