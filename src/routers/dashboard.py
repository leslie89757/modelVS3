"""仪表板路由"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database import get_db
from ..schemas import DashboardStats, UsageStats
from ..models import Run, Agent, Usage, Model

router = APIRouter()


@router.get("/stats", response_model=DashboardStats, summary="获取仪表板统计")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表板统计数据"""
    
    # 获取总执行数
    total_runs = db.query(func.count(Run.id)).scalar() or 0
    
    # 获取活跃 Agent 数
    active_agents = db.query(func.count(Agent.id)).filter(Agent.status == "active").scalar() or 0
    
    # 计算平均响应时间（从最近的100次执行中计算）
    recent_runs = db.query(Run.execution_time_ms).filter(
        Run.execution_time_ms.isnot(None)
    ).order_by(Run.created_at.desc()).limit(100).all()
    
    if recent_runs:
        avg_response_time_ms = sum(run[0] for run in recent_runs) / len(recent_runs)
    else:
        avg_response_time_ms = 0.0
    
    # 计算总成本（基于token使用量估算）
    total_input_tokens = db.query(func.sum(Run.input_tokens)).filter(
        Run.input_tokens.isnot(None)
    ).scalar() or 0
    
    total_output_tokens = db.query(func.sum(Run.output_tokens)).filter(
        Run.output_tokens.isnot(None)
    ).scalar() or 0
    
    # 简单的成本估算（每1000个token约$0.01）
    estimated_cost = (total_input_tokens + total_output_tokens) * 0.00001
    
    # 获取最近7天的使用统计
    daily_usage = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # 查询当天的执行统计
        day_runs = db.query(Run).filter(
            and_(
                Run.created_at >= start_of_day,
                Run.created_at < end_of_day
            )
        ).all()
        
        request_count = len(day_runs)
        input_tokens = sum(run.input_tokens or 0 for run in day_runs)
        output_tokens = sum(run.output_tokens or 0 for run in day_runs)
        cost_usd = (input_tokens + output_tokens) * 0.00001
        
        daily_usage.append(UsageStats(
            date=date,
            request_count=request_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd
        ))
    
    return DashboardStats(
        total_runs=total_runs,
        active_agents=active_agents,
        total_cost_usd=estimated_cost,
        avg_response_time_ms=avg_response_time_ms,
        daily_usage=daily_usage
    )


@router.get("/usage", response_model=List[UsageStats], summary="获取使用统计")
async def get_usage_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """获取使用统计"""
    usage_stats = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # 查询当天的执行统计
        day_runs = db.query(Run).filter(
            and_(
                Run.created_at >= start_of_day,
                Run.created_at < end_of_day
            )
        ).all()
        
        request_count = len(day_runs)
        input_tokens = sum(run.input_tokens or 0 for run in day_runs)
        output_tokens = sum(run.output_tokens or 0 for run in day_runs)
        cost_usd = (input_tokens + output_tokens) * 0.00001
        
        usage_stats.append(UsageStats(
            date=date,
            request_count=request_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd
        ))
    
    return usage_stats 