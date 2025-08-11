"""聊天历史记录路由"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse, ChatMessageBase, BaseResponse
)
from ..models import ChatSession, ChatMessage

router = APIRouter()


@router.get("/sessions", response_model=List[ChatSessionResponse], summary="获取聊天会话列表")
async def list_chat_sessions(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取聊天会话列表"""
    sessions = db.query(ChatSession).order_by(
        ChatSession.is_pinned.desc(),
        ChatSession.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    return sessions


@router.post("/sessions", response_model=ChatSessionResponse, summary="创建聊天会话", status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """创建新的聊天会话"""
    db_session = ChatSession(**session_data.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse, summary="获取聊天会话详情")
async def get_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取聊天会话详情"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    return session


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse, summary="更新聊天会话")
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
            detail="聊天会话不存在"
        )
    
    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    
    return session


@router.delete("/sessions/{session_id}", response_model=BaseResponse, summary="删除聊天会话")
async def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除聊天会话"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    db.delete(session)
    db.commit()
    
    return BaseResponse(message="聊天会话删除成功")


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse], summary="获取会话消息")
async def get_session_messages(
    session_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取会话消息"""
    # 检查会话是否存在
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()
    
    return messages


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse, summary="添加会话消息", status_code=status.HTTP_201_CREATED)
async def add_session_message(
    session_id: uuid.UUID,
    message_data: ChatMessageBase,
    db: Session = Depends(get_db)
):
    """添加会话消息"""
    # 检查会话是否存在
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    # 创建消息对象，session_id从URL路径获取
    db_message = ChatMessage(
        session_id=session_id,
        role=message_data.role,
        content=message_data.content,
        model_used=message_data.model_used
    )
    db.add(db_message)
    
    # 更新会话的更新时间
    session.updated_at = db_message.created_at
    
    db.commit()
    db.refresh(db_message)
    
    return db_message


@router.delete("/messages/{message_id}", response_model=BaseResponse, summary="删除消息")
async def delete_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除消息"""
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    db.delete(message)
    db.commit()
    
    return BaseResponse(message="消息删除成功") 