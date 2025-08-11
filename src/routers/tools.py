"""工具管理路由"""

import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..schemas import ToolCreate, ToolUpdate, ToolResponse, BaseResponse
from ..models import Tool

router = APIRouter()


class ToolTestRequest(BaseModel):
    """工具测试请求"""
    parameters: Dict[str, Any] = {}


class ToolTestResponse(BaseModel):
    """工具测试响应"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    timestamp: str


@router.get("/", response_model=List[ToolResponse], summary="获取工具列表")
async def list_tools(
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取工具列表"""
    query = db.query(Tool)
    
    if enabled is not None:
        query = query.filter(Tool.enabled == enabled)
    
    tools = query.offset(skip).limit(limit).all()
    return tools


@router.post("/", response_model=ToolResponse, summary="创建工具", status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    db: Session = Depends(get_db)
):
    """创建新工具"""
    # 检查工具名称是否已存在
    existing_tool = db.query(Tool).filter(Tool.name == tool_data.name).first()
    if existing_tool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工具名称 '{tool_data.name}' 已存在"
        )
    
    # 创建工具
    db_tool = Tool(**tool_data.model_dump())
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    
    return db_tool


@router.get("/{tool_id}", response_model=ToolResponse, summary="获取工具详情")
async def get_tool(
    tool_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取工具详情"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    return tool


@router.patch("/{tool_id}", response_model=ToolResponse, summary="更新工具")
async def update_tool(
    tool_id: uuid.UUID,
    tool_update: ToolUpdate,
    db: Session = Depends(get_db)
):
    """更新工具"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    # 更新字段
    update_data = tool_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)
    
    db.commit()
    db.refresh(tool)
    
    return tool


@router.delete("/{tool_id}", response_model=BaseResponse, summary="删除工具")
async def delete_tool(
    tool_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除工具"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    db.delete(tool)
    db.commit()
    
    return BaseResponse(message="工具删除成功") 


@router.post("/{tool_id}/test", response_model=ToolTestResponse, summary="测试工具")
async def test_tool(
    tool_id: uuid.UUID,
    test_request: ToolTestRequest,
    db: Session = Depends(get_db)
):
    """测试工具执行"""
    import time
    import asyncio
    from datetime import datetime
    
    # 获取工具
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工具不存在"
        )
    
    if not tool.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工具已禁用，无法测试"
        )
    
    start_time = time.time()
    
    try:
        # 使用Function Call工具执行器
        async def execute_tool_directly():
            from ..core.tool_executor import ToolExecutor
            tool_executor = ToolExecutor()
            return await tool_executor.execute_tool(tool.name, test_request.parameters)
        
        # 设置10秒超时
        result = await asyncio.wait_for(execute_tool_directly(), timeout=10.0)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return ToolTestResponse(
            success=result["success"],
            result=result.get("result") if result["success"] else None,
            error=result.get("error") if not result["success"] else None,
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat()
        )
        
    except asyncio.TimeoutError:
        execution_time = int((time.time() - start_time) * 1000)
        
        return ToolTestResponse(
            success=False,
            error="工具执行超时（10秒），请检查工具实现或网络连接",
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        
        return ToolTestResponse(
            success=False,
            error=f"测试执行失败: {str(e)}",
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat()
        ) 