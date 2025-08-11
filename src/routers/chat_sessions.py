"""聊天会话管理路由"""

import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from ..database import get_db
from ..schemas import ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse, ChatMessageCreate, ChatMessageResponse
from ..models import ChatSession, ChatMessage, Model, Agent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ChatSessionResponse], summary="获取聊天会话列表")
async def list_chat_sessions(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取聊天会话列表"""
    sessions = db.query(ChatSession).order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()
    return sessions


@router.post("/", response_model=ChatSessionResponse, summary="创建聊天会话", status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """创建新聊天会话"""
    
    # 验证模型或Agent存在
    if session_data.model_type == "model" and session_data.model_id:
        model = db.query(Model).filter(Model.id == session_data.model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
    elif session_data.model_type == "agent" and session_data.agent_id:
        agent = db.query(Agent).filter(Agent.id == session_data.agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent不存在"
            )
    
    # 创建会话
    db_session = ChatSession(
        title=session_data.title,
        model_id=session_data.model_id,
        agent_id=session_data.agent_id,
        model_type=session_data.model_type,
        is_pinned=session_data.is_pinned,
        tags=session_data.tags
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/{session_id}", response_model=ChatSessionResponse, summary="获取指定聊天会话")
async def get_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取指定聊天会话"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    return session


@router.put("/{session_id}", response_model=ChatSessionResponse, summary="更新聊天会话")
async def update_chat_session(
    session_id: uuid.UUID,
    session_update: ChatSessionUpdate,
    db: Session = Depends(get_db)
):
    """更新聊天会话"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 更新字段
    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", summary="删除聊天会话")
async def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除聊天会话"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    db.delete(session)
    db.commit()
    return {"message": "会话删除成功"}


@router.get("/{session_id}/messages", response_model=List[ChatMessageResponse], summary="获取会话消息")
async def get_session_messages(
    session_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取会话消息列表"""
    # 验证会话存在
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()
    return messages


@router.post("/{session_id}/messages", response_model=ChatMessageResponse, summary="添加会话消息", status_code=status.HTTP_201_CREATED)
async def create_session_message(
    session_id: uuid.UUID,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """添加会话消息"""
    # 验证会话存在
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 创建消息
    db_message = ChatMessage(
        session_id=session_id,
        role=message_data.role,
        content=message_data.content,
        model_used=message_data.model_used,
        tool_calls=message_data.tool_calls,
        tool_call_id=message_data.tool_call_id
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # 更新会话的更新时间
    from sqlalchemy import func
    session.updated_at = func.now()
    db.commit()
    
    return db_message