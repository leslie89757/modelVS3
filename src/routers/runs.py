"""执行管理路由"""

import uuid
import logging
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from datetime import datetime

from ..database import get_db
from ..schemas import RunRequest, RunResponse, BaseResponse, MessageResponse, MultiModelRunRequest, MultiModelRunResponse
from ..models import Run, Agent, RunStatus, Message
from ..core.agent_executor import AgentExecutor
from ..core.multi_model_executor import MultiModelExecutor

logger = logging.getLogger(__name__)

router = APIRouter()

# 统一的工具调用数据格式化函数
def format_tool_call_for_frontend(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化工具调用数据，确保与前端ToolCallDisplay组件完全兼容
    """
    # 标准化工具调用格式
    formatted = {
        "id": tool_call.get("id", str(uuid.uuid4())),
        "name": tool_call.get("name") or tool_call.get("function", {}).get("name"),
        "function": tool_call.get("function", {}),
        "arguments": tool_call.get("arguments") or tool_call.get("function", {}).get("arguments"),
        "result": tool_call.get("result"),
        "status": tool_call.get("status", "success"),  # 默认成功
        "execution_time": tool_call.get("execution_time"),
        "error_message": tool_call.get("error_message"),
        "startTime": tool_call.get("startTime"),
        "endTime": tool_call.get("endTime"),
        "index": tool_call.get("index")
    }
    
    # 确保arguments是对象格式（如果是字符串则解析）
    if isinstance(formatted["arguments"], str):
        try:
            formatted["arguments"] = json.loads(formatted["arguments"])
        except (json.JSONDecodeError, TypeError):
            # 如果解析失败，包装为对象
            formatted["arguments"] = {"raw": formatted["arguments"]}
    
    # 计算执行时间（如果没有但有开始和结束时间）
    if not formatted["execution_time"] and formatted["startTime"] and formatted["endTime"]:
        formatted["execution_time"] = formatted["endTime"] - formatted["startTime"]
    
    # 移除None值以减少数据传输
    return {k: v for k, v in formatted.items() if v is not None}

def format_message_for_frontend(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化消息数据，确保工具调用格式统一
    """
    formatted_message = {
        "id": message.get("id", str(uuid.uuid4())),
        "role": message.get("role"),
        "content": message.get("content", ""),
        "created_at": message.get("created_at") or datetime.now().isoformat(),
        "tool_call_id": message.get("tool_call_id")
    }
    
    # 格式化工具调用
    if message.get("tool_calls"):
        formatted_tool_calls = []
        for i, tool_call in enumerate(message["tool_calls"]):
            # 确保每个工具调用都有索引
            if "index" not in tool_call:
                tool_call["index"] = i
            formatted_tool_calls.append(format_tool_call_for_frontend(tool_call))
        formatted_message["tool_calls"] = formatted_tool_calls
    
    return formatted_message

@router.get("/", response_model=List[RunResponse], summary="获取执行列表")
async def list_runs(
    agent_id: Optional[str] = Query(None, description="Agent ID 筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取执行列表"""
    query = db.query(Run).order_by(Run.created_at.desc())
    
    if agent_id:
        query = query.filter(Run.agent_id == agent_id)
        
    if status_filter:
        query = query.filter(Run.status == status_filter)
    
    runs = query.offset(skip).limit(limit).all()
    
    # 为每个运行添加消息统计
    run_responses = []
    for run in runs:
        message_count = db.query(Message).filter(Message.run_id == run.id).count()
        
        run_data = {
            "id": run.id,
            "agent_id": run.agent_id,
            "model_id": run.model_id,
            "status": run.status,
            "input_tokens": run.input_tokens,
            "output_tokens": run.output_tokens,
            "execution_time_ms": run.execution_time_ms,
            "error_message": run.error_message,
            "created_at": run.created_at,
            "completed_at": run.completed_at,
            "message_count": message_count
        }
        
        run_responses.append(RunResponse(**run_data))
    
    return run_responses

@router.post("/", response_model=RunResponse, summary="创建执行", status_code=status.HTTP_201_CREATED)
async def create_run(
    run_data: RunRequest,
    db: Session = Depends(get_db)
):
    """创建新执行"""
    # 检查 Agent 是否存在
    agent = db.query(Agent).filter(Agent.id == run_data.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    if getattr(agent, 'status', None) != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent 未激活，无法执行"
        )
    
    # 验证指定的模型（如果有）
    if run_data.model_id:
        from ..models import Model
        model = db.query(Model).filter(
            Model.id == run_data.model_id,
            Model.enabled == True
        ).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"指定的模型 {run_data.model_id} 不存在或已禁用"
            )
    
    # 创建执行记录
    db_run = Run(
        agent_id=run_data.agent_id,
        run_metadata={
            "messages": [msg.model_dump() for msg in run_data.messages],
            "stream": run_data.stream,
            "max_tokens": run_data.max_tokens,
            "temperature": run_data.temperature,
            "model_id": run_data.model_id,
            "temporary_config": run_data.temporary_config.model_dump() if run_data.temporary_config else None
        }
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    
    if run_data.stream:
        # 流式响应
        return StreamingResponse(
            stream_agent_execution(agent, run_data, db_run, db),
            media_type="text/plain"
        )
    else:
        # 非流式响应，执行Agent
        try:
            # 真实Agent执行
            start_time = datetime.utcnow()
            
            # 使用Function Call协议
            executor = AgentExecutor(db)
            logger.info(f"🔧 使用Function Call协议执行Agent: {agent.name}")
            
            # 执行Agent
            result = None
            async for chunk in executor.execute_agent(agent, run_data, db_run):
                if chunk.get("type") == "final":
                    result = chunk.get("data", {})
                    break
            
            end_time = datetime.utcnow()
            
            # 更新执行记录
            db_run.status = "completed"
            db_run.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            db_run.completed_at = end_time
            
            # 更新token使用量和执行元数据
            if result and result.get("usage"):
                db_run.input_tokens = result["usage"].get("prompt_tokens")
                db_run.output_tokens = result["usage"].get("completion_tokens")
            
            # 记录执行元数据
            run_metadata = {
                "model": result.get("model") if result else None,
                "iterations": result.get("iterations") if result else 1,
                "request_params": {
                    "temperature": run_data.temperature,
                    "max_tokens": run_data.max_tokens,
                    "stream": run_data.stream
                },
                "agent_config": {
                    "primary_model_id": agent.llm_config.get("primary_model_id") if agent.llm_config else None,
                    "system_prompt": agent.system_config.get("system_prompt") if agent.system_config else None
                }
            }
            db_run.run_metadata = run_metadata
            
            db.commit()
            db.refresh(db_run)
            
            # 构造AI回复的MessageResponse - 从数据库查找
            ai_response = None
            
            # 查找所有assistant消息
            assistant_messages = db.query(Message).filter(
                Message.run_id == db_run.id,
                Message.role == "assistant"
            ).order_by(Message.created_at).all()
            
            logger.info(f"🔍 找到 {len(assistant_messages)} 条assistant消息")
            
            if assistant_messages:
                # 智能合并assistant消息：获取最终content和所有tool_calls
                final_content = ""
                all_tool_calls = None
                
                # 遍历所有assistant消息，收集信息
                for msg in assistant_messages:
                    # 获取最后一条有实际内容的消息作为final_content
                    if msg.content and msg.content.strip():
                        final_content = msg.content
                    
                    # 获取第一条有tool_calls的消息（通常是工具调用消息）
                    if msg.tool_calls and not all_tool_calls:
                        all_tool_calls = msg.tool_calls
                
                # 使用最后一条消息作为基础
                response_message = assistant_messages[-1]
                
                logger.info(f"📝 合并消息内容: content={bool(final_content)}, tool_calls={bool(all_tool_calls)}")
                logger.info(f"🔧 工具调用数据: {all_tool_calls}")
                
                ai_response = MessageResponse(
                    id=response_message.id,
                    role=response_message.role,
                    content=final_content or "执行完成",
                    tool_calls=all_tool_calls,
                    tool_call_id=response_message.tool_call_id,
                    created_at=response_message.created_at
                )
            else:
                logger.warning("❌ 没有找到assistant消息")
            
            # 获取完整的消息历史并格式化
            all_messages = db.query(Message).filter(
                Message.run_id == db_run.id
            ).order_by(Message.created_at).all()
            
            # 🎯 使用格式化函数确保前端兼容性
            message_responses = []
            for msg in all_messages:
                msg_dict = {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                    "created_at": msg.created_at.isoformat()
                }
                formatted_msg = format_message_for_frontend(msg_dict)
                message_responses.append(formatted_msg)
            
            # 如果有tool_calls，增强工具调用信息
            if ai_response and ai_response.tool_calls:
                logger.info(f"🔄 开始增强工具调用信息，数量: {len(ai_response.tool_calls)}")
                
                # 创建工具结果映射
                tool_results = {}
                for msg in all_messages:
                    if msg.role == "tool" and msg.tool_call_id:
                        try:
                            parsed_result = json.loads(msg.content) if msg.content else None
                            tool_results[msg.tool_call_id] = parsed_result
                        except json.JSONDecodeError:
                            tool_results[msg.tool_call_id] = msg.content
                
                # 增强tool_calls信息
                enhanced_tool_calls = []
                for tool_call in ai_response.tool_calls:
                    enhanced_call = dict(tool_call)
                    tool_call_id = tool_call.get("id")
                    if tool_call_id and tool_call_id in tool_results:
                        enhanced_call["status"] = "success"
                        enhanced_call["result"] = tool_results[tool_call_id]
                        enhanced_call["startTime"] = int(time.time() * 1000) - 2000
                        enhanced_call["endTime"] = int(time.time() * 1000)
                        # 🎯 使用格式化函数确保一致性
                        enhanced_call = format_tool_call_for_frontend(enhanced_call)
                    else:
                        enhanced_call["status"] = "error"
                        enhanced_call["error"] = "工具执行失败"
                        enhanced_call = format_tool_call_for_frontend(enhanced_call)
                    enhanced_tool_calls.append(enhanced_call)
                
                # 直接更新tool_calls字段
                ai_response_dict = {
                    "id": str(ai_response.id),
                    "role": ai_response.role,
                    "content": ai_response.content,
                    "tool_calls": enhanced_tool_calls,
                    "tool_call_id": ai_response.tool_call_id,
                    "created_at": ai_response.created_at.isoformat()
                }
                logger.info("🎯 工具调用信息增强完成")
            
            # 准备最终的response数据
            final_response = None
            if ai_response:
                if 'ai_response_dict' in locals():
                    final_response = ai_response_dict
                else:
                    final_response = {
                        "id": str(ai_response.id),
                        "role": ai_response.role,
                        "content": ai_response.content,
                        "tool_calls": ai_response.tool_calls,
                        "tool_call_id": ai_response.tool_call_id,
                        "created_at": ai_response.created_at.isoformat()
                    }

            # 创建RunResponse对象
            run_response = RunResponse(
                id=db_run.id,
                agent_id=db_run.agent_id,
                model_id=db_run.model_id,
                status=db_run.status,
                input_tokens=db_run.input_tokens,
                output_tokens=db_run.output_tokens,
                execution_time_ms=db_run.execution_time_ms,
                error_message=db_run.error_message,
                created_at=db_run.created_at,
                completed_at=db_run.completed_at,
                response=final_response,
                messages=message_responses
            )
            
            return run_response
        
        except Exception as e:
            # 更新错误状态
            db_run.status = "failed"
            db_run.error_message = str(e)
            db_run.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(db_run)
        
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent执行失败: {str(e)}"
            )


@router.get("/{run_id}", response_model=RunResponse, summary="获取执行详情")
def get_run(run_id: str, db: Session = Depends(get_db)):
    """获取特定执行的详情信息，包含工具调用数据"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 获取关联的消息并格式化
    messages = db.query(Message).filter(Message.run_id == run_id).order_by(Message.created_at).all()
    
    # 🎯 使用格式化函数确保前端兼容性
    formatted_messages = []
    for msg in messages:
        msg_dict = {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content or "",
            "created_at": msg.created_at.isoformat(),
            "tool_call_id": msg.tool_call_id,
            "tool_calls": msg.tool_calls
        }
        formatted_msg = format_message_for_frontend(msg_dict)
        formatted_messages.append(formatted_msg)
    
    response_data = {
        "id": run.id,
        "agent_id": run.agent_id,
        "model_id": run.model_id,
        "status": run.status,
        "input_tokens": run.input_tokens or 0,
        "output_tokens": run.output_tokens or 0,
        "execution_time_ms": run.execution_time_ms or 0,
        "error_message": run.error_message,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "messages": formatted_messages
    }
    
    return RunResponse(**response_data)


@router.delete("/{run_id}", summary="删除执行记录")
def delete_run(run_id: str, db: Session = Depends(get_db)):
    """删除执行记录"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="执行记录不存在"
        )
    
    # 删除关联的消息
    db.query(Message).filter(Message.run_id == run_id).delete()
    
    # 删除执行记录
    db.delete(run)
    db.commit()
    
    return {"message": "执行记录已删除"}


# 流式执行（保持原有逻辑）
async def stream_agent_execution(agent: Agent, run_data: RunRequest, db_run: Run, db: Session):
    """流式执行Agent"""
    try:
        yield f"data: {json.dumps({'type': 'start', 'run_id': str(db_run.id)})}\n\n"
        
        executor = AgentExecutor(db)
        final_result = None
        
        async for chunk in executor.execute_agent(agent, run_data, db_run):
            yield f"data: {json.dumps(chunk)}\n\n"
            
            if chunk.get("type") == "final":
                final_result = chunk.get("data", {})
        
        # 更新执行状态
        db_run.status = "completed"
        db_run.completed_at = datetime.utcnow()
        
        if final_result and final_result.get("usage"):
            db_run.input_tokens = final_result["usage"].get("prompt_tokens")
            db_run.output_tokens = final_result["usage"].get("completion_tokens")
        
        db.commit()
        
        yield f"data: {json.dumps({'type': 'end', 'run_id': str(db_run.id)})}\n\n"
        
    except Exception as e:
        # 更新错误状态
        db_run.status = "failed"
        db_run.error_message = str(e)
        db_run.completed_at = datetime.utcnow()
        db.commit()
        
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# 多模型批量执行
@router.post("/multi-model", response_model=MultiModelRunResponse, summary="多模型批量执行")
async def create_multi_model_run(
    run_data: MultiModelRunRequest,
    db: Session = Depends(get_db)
):
    """批量创建多个模型的执行"""
    try:
        executor = MultiModelExecutor(db)
        result = await executor.execute_multi_model(run_data)
        return result
    except Exception as e:
        logger.error(f"多模型执行失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"多模型执行失败: {str(e)}"
        ) 