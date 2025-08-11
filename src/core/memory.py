"""记忆管理器"""

import json
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """初始化记忆管理器"""
        self.redis_client = None
        self._memory_store: Dict[str, List[Dict[str, Any]]] = {}
        
        try:
            import redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # 测试连接
            if self.redis_client:
                self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存存储: {e}")
            self.redis_client = None
    
    async def save_conversation(
        self,
        agent_id: str,
        run_id: str,
        messages: List[Dict[str, Any]]
    ):
        """保存对话历史"""
        
        try:
            # 使用 agent_id 作为键，保存最近的对话历史
            key = f"agent_memory:{agent_id}"
            
            # 只保存用户和助手的消息
            filtered_messages = [
                msg for msg in messages 
                if msg.get("role") in ["user", "assistant"]
            ]
            
            if self.redis_client:
                # 使用Redis存储
                try:
                    existing_data = self.redis_client.get(key)
                    if existing_data:
                        existing_messages = json.loads(existing_data)
                    else:
                        existing_messages = []
                    
                    existing_messages.extend(filtered_messages)
                    
                    # 只保留最近的 50 条消息
                    if len(existing_messages) > 50:
                        existing_messages = existing_messages[-50:]
                    
                    self.redis_client.setex(key, 86400, json.dumps(existing_messages))  # 24小时过期
                except Exception as e:
                    logger.error(f"Redis操作失败: {e}")
                    # 使用内存存储作为备选方案
                    self._save_to_memory(key, filtered_messages)
            else:
                # 使用内存存储
                self._save_to_memory(key, filtered_messages)
            
            logger.info(f"保存了 {len(filtered_messages)} 条对话记录到 {key}")
            
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")
    
    def _save_to_memory(self, key: str, filtered_messages: List[Dict[str, Any]]):
        """保存到内存"""
        if key in self._memory_store:
            existing_messages = self._memory_store[key]
        else:
            existing_messages = []
        
        existing_messages.extend(filtered_messages)
        
        # 只保留最近的 50 条消息
        if len(existing_messages) > 50:
            existing_messages = existing_messages[-50:]
        
        self._memory_store[key] = existing_messages
    
    async def get_conversation_history(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        
        try:
            key = f"agent_memory:{agent_id}"
            
            if self.redis_client:
                # 从Redis获取
                try:
                    data = self.redis_client.get(key)
                    if data:
                        messages = json.loads(data)
                        return messages[-limit:] if limit else messages
                except Exception as e:
                    logger.error(f"Redis读取失败: {e}")
            
            # 从内存获取
            messages = self._memory_store.get(key, [])
            return messages[-limit:] if limit else messages
                
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    async def clear_conversation_history(self, agent_id: str):
        """清除对话历史"""
        
        try:
            key = f"agent_memory:{agent_id}"
            
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                except Exception as e:
                    logger.error(f"Redis删除失败: {e}")
            else:
                self._memory_store.pop(key, None)
            
            logger.info(f"清除了 {key} 的对话历史")
            
        except Exception as e:
            logger.error(f"清除对话历史失败: {e}")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        
        try:
            if self.redis_client:
                # Redis统计
                try:
                    keys = self.redis_client.keys("agent_memory:*")
                    total_agents = len(keys)
                    total_messages = 0
                    
                    for key in keys:
                        data = self.redis_client.get(key)
                        if data:
                            messages = json.loads(data)
                            total_messages += len(messages)
                    
                    return {
                        "storage_type": "redis",
                        "total_agents": total_agents,
                        "total_messages": total_messages,
                        "memory_size_mb": 0
                    }
                except Exception as e:
                    logger.error(f"Redis统计失败: {e}")
            
            # 内存统计
            total_agents = len(self._memory_store)
            total_messages = sum(len(messages) for messages in list(self._memory_store.values()))
            
            return {
                "storage_type": "memory",
                "total_agents": total_agents,
                "total_messages": total_messages,
                "memory_size_mb": 0
            }
                
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {
                "storage_type": "unknown",
                "total_agents": 0,
                "total_messages": 0,
                "memory_size_mb": 0
            } 