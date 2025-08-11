"""Agent 管理路由"""

import uuid
import secrets
import string
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import AgentCreate, AgentUpdate, AgentResponse, BaseResponse
from ..models import Agent, AgentStatus
from ..config import settings

router = APIRouter()


@router.get("/", response_model=List[AgentResponse], summary="获取 Agent 列表")
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    category_filter: Optional[str] = Query(None, alias="category", description="按分类筛选"),
    access_level: Optional[str] = Query(None, description="按访问级别筛选 (public, private, team)"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取 Agent 列表"""
    query = db.query(Agent)
    
    if status_filter:
        query = query.filter(Agent.status == status_filter)
    
    if category_filter:
        query = query.filter(Agent.category == category_filter)
    
    if access_level:
        query = query.filter(Agent.access_level == access_level)
    
    agents = query.offset(skip).limit(limit).all()
    return agents


@router.get("/public", response_model=List[AgentResponse], summary="获取公开 Agent 列表")
async def list_public_agents(
    category_filter: Optional[str] = Query(None, alias="category", description="按分类筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: Session = Depends(get_db)
):
    """获取公开 Agent 列表，无需认证"""
    query = db.query(Agent).filter(
        Agent.access_level == "public",
        Agent.status == AgentStatus.ACTIVE
    )
    
    if category_filter:
        query = query.filter(Agent.category == category_filter)
    
    agents = query.order_by(Agent.created_at.desc()).offset(skip).limit(limit).all()
    return agents


@router.post("/", response_model=AgentResponse, summary="创建 Agent", status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db)
):
    """创建新 Agent"""
    # 检查 Agent 名称是否已存在
    existing_agent = db.query(Agent).filter(Agent.name == agent_data.name).first()
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent 名称 '{agent_data.name}' 已存在"
        )
    
    # 验证必需配置
    if not agent_data.llm_config or not agent_data.llm_config.primary_model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须配置主要模型"
        )
    
    if not agent_data.system_config or not agent_data.system_config.system_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须配置系统提示词"
        )
    
    # 创建 Agent
    agent_dict = agent_data.model_dump()
    
    # 处理嵌套的配置对象，确保它们被正确序列化为JSON
    if 'llm_config' in agent_dict and agent_dict['llm_config']:
        agent_dict['llm_config'] = agent_dict['llm_config']
    if 'system_config' in agent_dict and agent_dict['system_config']:
        agent_dict['system_config'] = agent_dict['system_config']
    if 'tools_config' in agent_dict and agent_dict['tools_config']:
        agent_dict['tools_config'] = agent_dict['tools_config']
    if 'knowledge_config' in agent_dict and agent_dict['knowledge_config']:
        agent_dict['knowledge_config'] = agent_dict['knowledge_config']
    if 'deployment_config' in agent_dict and agent_dict['deployment_config']:
        agent_dict['deployment_config'] = agent_dict['deployment_config']
    
    db_agent = Agent(**agent_dict)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return db_agent


@router.get("/{agent_id}", response_model=AgentResponse, summary="获取 Agent 详情")
async def get_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取 Agent 详情"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse, summary="更新 Agent")
async def update_agent(
    agent_id: uuid.UUID,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db)
):
    """更新 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    # 更新字段
    update_data = agent_update.model_dump(exclude_unset=True)
    
    # 处理嵌套的配置对象
    for field, value in update_data.items():
        if field in ['llm_config', 'system_config', 'tools_config', 'knowledge_config', 'deployment_config'] and value:
            # 确保嵌套对象被正确处理
            setattr(agent, field, value)
        else:
            setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    
    return agent


@router.delete("/{agent_id}", response_model=BaseResponse, summary="删除 Agent")
async def delete_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """删除 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    db.delete(agent)
    db.commit()
    
    return BaseResponse(message=f"Agent '{agent.name}' 已删除")


@router.post("/{agent_id}/activate", response_model=BaseResponse, summary="激活 Agent")
async def activate_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """激活 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    setattr(agent, 'status', 'active')
    db.commit()
    
    return BaseResponse(message=f"Agent '{agent.name}' 已激活")


@router.post("/{agent_id}/pause", response_model=BaseResponse, summary="暂停 Agent")
async def pause_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """暂停 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    setattr(agent, 'status', 'paused')
    db.commit()
    
    return BaseResponse(message=f"Agent '{agent.name}' 已暂停")


@router.post("/{agent_id}/archive", response_model=BaseResponse, summary="归档 Agent")
async def archive_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """归档 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    setattr(agent, 'status', 'archived')
    db.commit()
    
    return BaseResponse(message=f"Agent '{agent.name}' 已归档")


@router.post("/{agent_id}/publish", response_model=BaseResponse, summary="发布 Agent")
async def publish_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """将 Agent 发布为公开可访问"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    # 检查Agent状态
    if agent.status != AgentStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有激活状态的 Agent 才能发布"
        )
    
    # 验证必要配置
    if not agent.description or len(agent.description.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="发布的 Agent 必须有详细描述（至少10个字符）"
        )
    
    # 更新访问级别为公开
    agent.access_level = "public"
    db.commit()
    
    return BaseResponse(
        success=True,
        message=f"Agent '{agent.name}' 已成功发布为公开可访问"
    )


@router.post("/{agent_id}/unpublish", response_model=BaseResponse, summary="取消发布 Agent")
async def unpublish_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """取消发布 Agent，改为私有"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    # 更新访问级别为私有
    agent.access_level = "private"
    db.commit()
    
    return BaseResponse(
        success=True,
        message=f"Agent '{agent.name}' 已取消发布"
    )


@router.get("/{agent_id}/share-link", summary="获取 Agent 分享链接")
async def get_agent_share_link(
    agent_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取 Agent 的分享链接"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    if agent.access_level != "public":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有公开的 Agent 才能生成分享链接"
        )
    
    # 从请求头获取主机地址
    request_host = request.headers.get("host", "localhost:3003")
    
    # 判断是否为正式环境（3003端口）
    if str(settings.production_port) in request_host:
        # 正式环境使用公网地址
        host = f"{settings.public_host}:{settings.production_port}"
        scheme = "http"  # 根据实际情况调整，如果使用https请改为https
    else:
        # 开发环境使用请求的host
        host = request_host
        # 确保包含端口号
        if ":" not in host:
            host = f"{host}:{settings.production_port}"
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    base_url = f"{scheme}://{host}"
    experience_link = f"/experience/{agent_id}"
    public_link = f"{base_url}{experience_link}"
    
    return {
        "success": True,
        "data": {
            "agent_id": str(agent_id),
            "agent_name": agent.name,
            "share_link": experience_link,
            "public_link": public_link,
            "embed_code": f'<iframe src="{public_link}" width="100%" height="600" frameborder="0" style="border-radius: 8px;"></iframe>',
            "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={public_link}",
            "description": f"与 {agent.name} AI助手开始对话",
            "type": "client_experience"
        }
    }


@router.get("/{agent_id}/stats", summary="获取 Agent 使用统计")
async def get_agent_stats(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """获取 Agent 的使用统计信息"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 不存在"
        )
    
    # 这里可以从runs表中统计数据
    from ..models import Run
    
    total_runs = db.query(Run).filter(Run.agent_id == agent_id).count()
    successful_runs = db.query(Run).filter(
        Run.agent_id == agent_id,
        Run.status == "completed"
    ).count()
    
    # 计算成功率
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    return {
        "success": True,
        "data": {
            "agent_id": str(agent_id),
            "agent_name": agent.name,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": round(success_rate, 2),
            "access_level": agent.access_level,
            "status": agent.status,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at
        }
    }


@router.post("/generate-api-key", summary="生成API密钥")
async def generate_api_key(
    agent_id: str = "new",
    db: Session = Depends(get_db)
):
    """生成API密钥"""
    # 生成安全的API密钥
    alphabet = string.ascii_letters + string.digits
    api_key = 'mv3_' + ''.join(secrets.choice(alphabet) for _ in range(32))
    
    return {
        "api_key": api_key,
        "message": "API密钥生成成功"
    }


@router.post("/upload", summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传文件到知识库"""
    # 验证文件类型
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain", "text/markdown"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型"
        )
    
    # 验证文件大小（10MB）
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过限制（10MB）"
        )
    
    # 保存文件
    import os
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    if file.filename:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "filename": file.filename,
            "size": file.size,
            "message": "文件上传成功"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )


@router.get("/categories/list", summary="获取所有分类")
async def get_categories(db: Session = Depends(get_db)):
    """获取所有 Agent 分类"""
    categories = db.query(Agent.category).distinct().all()
    return [cat[0] for cat in categories]


@router.get("/stats/summary", summary="获取 Agent 统计摘要")
async def get_agent_stats(db: Session = Depends(get_db)):
    """获取 Agent 统计摘要"""
    total_agents = db.query(Agent).count()
    active_agents = db.query(Agent).filter(Agent.status == "active").count()
    paused_agents = db.query(Agent).filter(Agent.status == "paused").count()
    draft_agents = db.query(Agent).filter(Agent.status == "draft").count()
    
    return {
        "total": total_agents,
        "active": active_agents,
        "paused": paused_agents,
        "draft": draft_agents
    } 