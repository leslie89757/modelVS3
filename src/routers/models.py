"""模型管理路由"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ModelCreate, ModelUpdate, ModelResponse, BaseResponse
from ..models import Model

router = APIRouter()


@router.get("/", response_model=List[ModelResponse], summary="获取模型列表")
async def list_models(
    provider: Optional[str] = Query(None, description="按提供商筛选"),
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取模型列表"""
    query = db.query(Model)
    
    if provider:
        query = query.filter(Model.provider == provider)
    if enabled is not None:
        query = query.filter(Model.enabled == enabled)
    
    models = query.offset(skip).limit(limit).all()
    return models


@router.post("/", response_model=ModelResponse, summary="创建模型", status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    db: Session = Depends(get_db)
):
    """创建新模型"""
    # 检查模型名称是否已存在
    existing_model = db.query(Model).filter(Model.name == model_data.name).first()
    if existing_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"模型名称 '{model_data.name}' 已存在"
        )
    
    # 创建模型
    db_model = Model(**model_data.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model


@router.get("/{model_id}", response_model=ModelResponse, summary="获取模型详情")
async def get_model(
    model_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取模型详情"""
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    return model


@router.patch("/{model_id}", response_model=ModelResponse, summary="更新模型")
async def update_model(
    model_id: uuid.UUID,
    model_update: ModelUpdate,
    db: Session = Depends(get_db)
):
    """更新模型"""
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 更新字段
    update_data = model_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    db.commit()
    db.refresh(model)
    
    return model


@router.delete("/{model_id}", response_model=BaseResponse, summary="删除模型")
async def delete_model(
    model_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除模型"""
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    db.delete(model)
    db.commit()
    
    return BaseResponse(message="模型删除成功")


@router.post("/{model_id}/enable", response_model=BaseResponse, summary="启用模型")
async def enable_model(
    model_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """启用模型"""
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    model.enabled = True
    db.commit()
    
    return BaseResponse(message="模型已启用")


@router.post("/{model_id}/disable", response_model=BaseResponse, summary="禁用模型")
async def disable_model(
    model_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """禁用模型"""
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    model.enabled = False
    db.commit()
    
    return BaseResponse(message="模型已禁用") 