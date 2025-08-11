"""多模型并行执行器"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .agent_executor import AgentExecutor
from ..models import Agent, Run, Model
from ..schemas import RunRequest

logger = logging.getLogger(__name__)


class MultiModelExecutor:
    """多模型并行执行器 - 为每个模型创建独立的执行器实例"""
    
    def __init__(self, db: Session):
        self.db = db
        self.model_executors: Dict[str, AgentExecutor] = {}
        self.execution_results: Dict[str, Any] = {}
    
    async def execute_multi_model(
        self, 
        agent: Agent,
        base_request: RunRequest,
        model_ids: List[str],
        db_runs: Dict[str, Run]
    ) -> Dict[str, Any]:
        """
        并行执行多个模型
        
        Args:
            agent: Agent配置
            base_request: 基础请求（不包含model_id）
            model_ids: 要执行的模型ID列表
            db_runs: 每个模型对应的Run记录
        
        Returns:
            Dict[model_id, execution_result]
        """
        logger.info(f"🚀 开始多模型并行执行: {len(model_ids)} 个模型")
        
        # 为每个模型创建独立的执行器和请求
        tasks = []
        for model_id in model_ids:
            # 创建该模型专用的执行器
            executor = AgentExecutor(self.db)
            self.model_executors[model_id] = executor
            
            # 创建该模型的专用请求
            model_request = self._create_model_request(base_request, model_id)
            db_run = db_runs[model_id]
            
            # 创建异步任务
            task = asyncio.create_task(
                self._execute_single_model(
                    model_id=model_id,
                    executor=executor,
                    agent=agent,
                    request=model_request,
                    db_run=db_run
                )
            )
            tasks.append(task)
        
        # 并行执行所有模型，等待全部完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        execution_results = {}
        for i, (model_id, result) in enumerate(zip(model_ids, results)):
            if isinstance(result, Exception):
                logger.error(f"❌ 模型 {model_id} 执行失败: {result}")
                execution_results[model_id] = {
                    "success": False,
                    "error": str(result),
                    "model_id": model_id
                }
            else:
                logger.info(f"✅ 模型 {model_id} 执行成功")
                execution_results[model_id] = {
                    "success": True,
                    "result": result,
                    "model_id": model_id
                }
        
        # 清理执行器实例
        await self._cleanup_executors()
        
        logger.info(f"🎯 多模型执行完成: {len(execution_results)} 个结果")
        return execution_results
    
    async def _execute_single_model(
        self,
        model_id: str,
        executor: AgentExecutor,
        agent: Agent,
        request: RunRequest,
        db_run: Run
    ) -> Any:
        """执行单个模型的专用方法"""
        logger.info(f"🎯 开始执行模型: {model_id}")
        start_time = datetime.now()
        
        try:
            # 使用专用执行器执行
            result = None
            async for chunk in executor.execute_agent(agent, request, db_run):
                if chunk.get("type") == "final":
                    result = chunk.get("data", {})
                    break
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            logger.info(f"✅ 模型 {model_id} 执行成功，耗时: {execution_time:.2f}ms")
            
            return {
                "response": result,
                "execution_time": execution_time,
                "model_id": model_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            logger.error(f"❌ 模型 {model_id} 执行失败: {e}")
            raise Exception(f"模型 {model_id} 执行失败: {str(e)}")
    
    def _create_model_request(self, base_request: RunRequest, model_id: str) -> RunRequest:
        """为特定模型创建专用请求"""
        # 创建请求副本
        model_request_data = base_request.model_dump()
        model_request_data['model_id'] = model_id
        
        # 返回新的RunRequest实例
        return RunRequest(**model_request_data)
    
    async def _cleanup_executors(self):
        """清理执行器实例，释放资源"""
        logger.info("🧹 清理执行器实例")
        
        for model_id, executor in self.model_executors.items():
            try:
                # 清理执行器资源（如果有的话）
                if hasattr(executor, 'cleanup'):
                    await executor.cleanup()
            except Exception as e:
                logger.warning(f"⚠️ 清理执行器 {model_id} 时出错: {e}")
        
        self.model_executors.clear()
    
    def get_model_executor(self, model_id: str) -> Optional[AgentExecutor]:
        """获取特定模型的执行器实例"""
        return self.model_executors.get(model_id)
    
    async def validate_models(self, model_ids: List[str]) -> Dict[str, bool]:
        """验证所有模型是否可用"""
        logger.info(f"🔍 验证模型可用性: {model_ids}")
        
        validation_results = {}
        for model_id in model_ids:
            try:
                # 检查模型是否存在且启用
                model = self.db.query(Model).filter(
                    Model.id == model_id,
                    Model.enabled == True
                ).first()
                
                validation_results[model_id] = model is not None
                if model:
                    logger.info(f"✅ 模型验证通过: {model.name} ({model_id})")
                else:
                    logger.warning(f"❌ 模型验证失败: {model_id}")
                    
            except Exception as e:
                logger.error(f"❌ 模型 {model_id} 验证出错: {e}")
                validation_results[model_id] = False
        
        return validation_results


class ModelExecutorPool:
    """模型执行器池 - 复用执行器实例以提高性能"""
    
    def __init__(self, max_pool_size: int = 10):
        self.max_pool_size = max_pool_size
        self.executor_pool: Dict[str, List[AgentExecutor]] = {}
        self.active_executors: Dict[str, AgentExecutor] = {}
    
    async def get_executor(self, model_id: str, db: Session) -> AgentExecutor:
        """获取或创建模型执行器"""
        # 尝试从池中获取空闲执行器
        if model_id in self.executor_pool and self.executor_pool[model_id]:
            executor = self.executor_pool[model_id].pop()
            logger.info(f"♻️ 复用执行器: {model_id}")
        else:
            # 创建新执行器
            executor = AgentExecutor(db)
            logger.info(f"🆕 创建新执行器: {model_id}")
        
        self.active_executors[f"{model_id}_{id(executor)}"] = executor
        return executor
    
    async def return_executor(self, model_id: str, executor: AgentExecutor):
        """归还执行器到池中"""
        executor_key = f"{model_id}_{id(executor)}"
        if executor_key in self.active_executors:
            del self.active_executors[executor_key]
        
        # 检查池大小限制
        if model_id not in self.executor_pool:
            self.executor_pool[model_id] = []
        
        if len(self.executor_pool[model_id]) < self.max_pool_size:
            self.executor_pool[model_id].append(executor)
            logger.info(f"♻️ 执行器归还到池: {model_id}")
        else:
            # 池已满，清理执行器
            if hasattr(executor, 'cleanup'):
                await executor.cleanup()
            logger.info(f"🗑️ 执行器池已满，清理执行器: {model_id}")
    
    async def cleanup_all(self):
        """清理所有执行器"""
        logger.info("🧹 清理所有执行器池")
        
        # 清理活跃执行器
        for executor in self.active_executors.values():
            try:
                if hasattr(executor, 'cleanup'):
                    await executor.cleanup()
            except Exception as e:
                logger.warning(f"⚠️ 清理活跃执行器时出错: {e}")
        
        # 清理池中执行器
        for model_executors in self.executor_pool.values():
            for executor in model_executors:
                try:
                    if hasattr(executor, 'cleanup'):
                        await executor.cleanup()
                except Exception as e:
                    logger.warning(f"⚠️ 清理池中执行器时出错: {e}")
        
        self.active_executors.clear()
        self.executor_pool.clear()


# 全局执行器池实例
global_executor_pool = ModelExecutorPool() 