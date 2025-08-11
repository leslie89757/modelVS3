"""高级记忆管理器"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models_advanced import AgentMemory

logger = logging.getLogger(__name__)


class AdvancedMemoryManager:
    """高级记忆管理器"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    async def save_conversation_memory(
        self,
        agent_id: str,
        session_id: str,
        user_message: str,
        agent_response: str,
        confidence: float = 0.5
    ):
        """保存对话记忆"""
        
        if not self.db:
            logger.warning("数据库连接未初始化，无法保存记忆")
            return
        
        try:
            # 计算重要性评分
            importance_score = self._calculate_conversation_importance(
                user_message, agent_response, confidence
            )
            
            # 创建对话记忆
            memory_content = f"用户: {user_message}\n助手: {agent_response}"
            
            memory = AgentMemory(
                agent_id=agent_id,
                memory_type="conversation",
                content=memory_content,
                importance_score=importance_score,
                source_session_id=session_id,
                tags=self._extract_conversation_tags(user_message, agent_response)
            )
            
            self.db.add(memory)
            self.db.commit()
            
            # 清理过期记忆
            await self._cleanup_old_memories(agent_id)
            
            logger.info(f"保存对话记忆成功，重要性评分: {importance_score}")
            
        except Exception as e:
            logger.error(f"保存对话记忆失败: {e}")
            self.db.rollback()
    
    async def save_skill_memory(
        self,
        agent_id: str,
        tool_name: str,
        usage_context: str,
        success: bool,
        parameters: Dict[str, Any] = None
    ):
        """保存技能记忆"""
        
        if not self.db:
            return
        
        try:
            # 检查是否已有相似的技能记忆
            existing_memory = self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.memory_type == "skill",
                    AgentMemory.content.contains(tool_name)
                )
            ).first()
            
            if existing_memory:
                # 更新现有记忆
                existing_memory.access_count += 1
                existing_memory.last_accessed = datetime.utcnow()
                if success:
                    existing_memory.importance_score = min(1.0, existing_memory.importance_score + 0.1)
                else:
                    existing_memory.importance_score = max(0.1, existing_memory.importance_score - 0.1)
            else:
                # 创建新的技能记忆
                memory_content = f"工具使用: {tool_name}\n上下文: {usage_context}\n成功: {success}"
                if parameters:
                    memory_content += f"\n参数: {json.dumps(parameters, ensure_ascii=False)}"
                
                memory = AgentMemory(
                    agent_id=agent_id,
                    memory_type="skill",
                    content=memory_content,
                    importance_score=0.7 if success else 0.3,
                    tags=[tool_name, "tool_usage"]
                )
                
                self.db.add(memory)
            
            self.db.commit()
            logger.info(f"保存技能记忆成功: {tool_name}")
            
        except Exception as e:
            logger.error(f"保存技能记忆失败: {e}")
            self.db.rollback()
    
    async def save_preference_memory(
        self,
        agent_id: str,
        preference_type: str,
        preference_value: str,
        context: str = ""
    ):
        """保存偏好记忆"""
        
        if not self.db:
            return
        
        try:
            # 检查是否已有相同类型的偏好
            existing_memory = self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.memory_type == "preference",
                    AgentMemory.content.contains(preference_type)
                )
            ).first()
            
            memory_content = f"偏好类型: {preference_type}\n偏好值: {preference_value}"
            if context:
                memory_content += f"\n上下文: {context}"
            
            if existing_memory:
                # 更新现有偏好
                existing_memory.content = memory_content
                existing_memory.last_accessed = datetime.utcnow()
                existing_memory.importance_score = 0.8  # 偏好通常比较重要
            else:
                # 创建新偏好记忆
                memory = AgentMemory(
                    agent_id=agent_id,
                    memory_type="preference",
                    content=memory_content,
                    importance_score=0.8,
                    tags=[preference_type, "user_preference"]
                )
                
                self.db.add(memory)
            
            self.db.commit()
            logger.info(f"保存偏好记忆成功: {preference_type}")
            
        except Exception as e:
            logger.error(f"保存偏好记忆失败: {e}")
            self.db.rollback()
    
    async def save_fact_memory(
        self,
        agent_id: str,
        fact: str,
        category: str = "general",
        source: str = ""
    ):
        """保存事实记忆"""
        
        if not self.db:
            return
        
        try:
            # 避免重复的事实记忆
            fact_hash = hashlib.md5(fact.encode('utf-8')).hexdigest()
            
            existing_memory = self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.memory_type == "fact",
                    AgentMemory.content.contains(fact_hash)
                )
            ).first()
            
            if not existing_memory:
                memory_content = f"事实: {fact}\n分类: {category}\n哈希: {fact_hash}"
                if source:
                    memory_content += f"\n来源: {source}"
                
                memory = AgentMemory(
                    agent_id=agent_id,
                    memory_type="fact",
                    content=memory_content,
                    importance_score=0.6,
                    tags=[category, "fact", "knowledge"]
                )
                
                self.db.add(memory)
                self.db.commit()
                
                logger.info(f"保存事实记忆成功: {category}")
            
        except Exception as e:
            logger.error(f"保存事实记忆失败: {e}")
            self.db.rollback()
    
    async def get_relevant_memories(
        self,
        agent_id: str,
        query: str,
        memory_types: List[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取相关记忆"""
        
        if not self.db:
            return []
        
        try:
            # 构建查询
            query_filter = [AgentMemory.agent_id == agent_id]
            
            if memory_types:
                query_filter.append(AgentMemory.memory_type.in_(memory_types))
            
            # 简单的关键词匹配（在实际应用中应使用向量相似度搜索）
            query_words = query.lower().split()
            relevant_memories = []
            
            # 获取候选记忆
            memories = self.db.query(AgentMemory).filter(
                and_(*query_filter)
            ).order_by(
                desc(AgentMemory.importance_score),
                desc(AgentMemory.last_accessed)
            ).limit(limit * 2).all()  # 获取更多候选记忆进行筛选
            
            # 计算相关性得分
            for memory in memories:
                relevance_score = self._calculate_relevance(memory.content, query_words)
                
                if relevance_score > 0.1:  # 相关性阈值
                    relevant_memories.append({
                        "id": str(memory.id),
                        "type": memory.memory_type,
                        "content": memory.content,
                        "importance": memory.importance_score,
                        "relevance": relevance_score,
                        "access_count": memory.access_count,
                        "tags": memory.tags or [],
                        "created_at": memory.created_at.isoformat(),
                        "last_accessed": memory.last_accessed.isoformat() if memory.last_accessed else None
                    })
                    
                    # 更新访问记录
                    memory.access_count += 1
                    memory.last_accessed = datetime.utcnow()
            
            # 按相关性和重要性排序
            relevant_memories.sort(
                key=lambda x: x["relevance"] * 0.6 + x["importance"] * 0.4,
                reverse=True
            )
            
            self.db.commit()
            
            return relevant_memories[:limit]
            
        except Exception as e:
            logger.error(f"获取相关记忆失败: {e}")
            return []
    
    async def get_memory_summary(self, agent_id: str) -> Dict[str, Any]:
        """获取记忆摘要"""
        
        if not self.db:
            return {}
        
        try:
            memories = self.db.query(AgentMemory).filter(
                AgentMemory.agent_id == agent_id
            ).all()
            
            summary = {
                "total_memories": len(memories),
                "by_type": {},
                "most_important": [],
                "most_accessed": [],
                "recent_memories": []
            }
            
            # 按类型统计
            for memory in memories:
                memory_type = memory.memory_type
                if memory_type not in summary["by_type"]:
                    summary["by_type"][memory_type] = 0
                summary["by_type"][memory_type] += 1
            
            # 最重要的记忆
            important_memories = sorted(
                memories, 
                key=lambda x: x.importance_score, 
                reverse=True
            )[:5]
            
            summary["most_important"] = [
                {
                    "type": mem.memory_type,
                    "content": mem.content[:100] + "..." if len(mem.content) > 100 else mem.content,
                    "importance": mem.importance_score
                }
                for mem in important_memories
            ]
            
            # 最常访问的记忆
            accessed_memories = sorted(
                [mem for mem in memories if mem.access_count > 0],
                key=lambda x: x.access_count,
                reverse=True
            )[:5]
            
            summary["most_accessed"] = [
                {
                    "type": mem.memory_type,
                    "content": mem.content[:100] + "..." if len(mem.content) > 100 else mem.content,
                    "access_count": mem.access_count
                }
                for mem in accessed_memories
            ]
            
            # 最近的记忆
            recent_memories = sorted(
                memories,
                key=lambda x: x.created_at,
                reverse=True
            )[:5]
            
            summary["recent_memories"] = [
                {
                    "type": mem.memory_type,
                    "content": mem.content[:100] + "..." if len(mem.content) > 100 else mem.content,
                    "created_at": mem.created_at.isoformat()
                }
                for mem in recent_memories
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"获取记忆摘要失败: {e}")
            return {}
    
    async def delete_memory(self, agent_id: str, memory_id: str) -> bool:
        """删除特定记忆"""
        
        if not self.db:
            return False
        
        try:
            memory = self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.id == memory_id,
                    AgentMemory.agent_id == agent_id
                )
            ).first()
            
            if memory:
                self.db.delete(memory)
                self.db.commit()
                logger.info(f"删除记忆成功: {memory_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            self.db.rollback()
            return False
    
    async def clear_agent_memories(self, agent_id: str, memory_type: str = None) -> int:
        """清空Agent的记忆"""
        
        if not self.db:
            return 0
        
        try:
            query = self.db.query(AgentMemory).filter(AgentMemory.agent_id == agent_id)
            
            if memory_type:
                query = query.filter(AgentMemory.memory_type == memory_type)
            
            count = query.count()
            query.delete()
            self.db.commit()
            
            logger.info(f"清空记忆成功，删除了 {count} 条记忆")
            return count
            
        except Exception as e:
            logger.error(f"清空记忆失败: {e}")
            self.db.rollback()
            return 0
    
    async def _cleanup_old_memories(self, agent_id: str):
        """清理过期记忆"""
        
        try:
            # 删除30天前的低重要性记忆
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            old_memories = self.db.query(AgentMemory).filter(
                and_(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.created_at < thirty_days_ago,
                    AgentMemory.importance_score < 0.3
                )
            )
            
            count = old_memories.count()
            if count > 0:
                old_memories.delete()
                self.db.commit()
                logger.info(f"清理了 {count} 条过期低重要性记忆")
            
            # 如果记忆总数超过限制，删除最旧的低重要性记忆
            total_memories = self.db.query(AgentMemory).filter(
                AgentMemory.agent_id == agent_id
            ).count()
            
            if total_memories > 1000:  # 限制每个Agent最多1000条记忆
                excess_memories = self.db.query(AgentMemory).filter(
                    AgentMemory.agent_id == agent_id
                ).order_by(
                    AgentMemory.importance_score,
                    AgentMemory.created_at
                ).limit(total_memories - 1000)
                
                for memory in excess_memories:
                    self.db.delete(memory)
                
                self.db.commit()
                logger.info(f"清理了 {total_memories - 1000} 条多余记忆")
            
        except Exception as e:
            logger.error(f"清理过期记忆失败: {e}")
            self.db.rollback()
    
    def _calculate_conversation_importance(self, user_message: str, agent_response: str, confidence: float) -> float:
        """计算对话重要性评分"""
        
        importance = 0.5  # 基础重要性
        
        # 根据置信度调整
        importance += (confidence - 0.5) * 0.3
        
        # 根据消息长度调整
        total_length = len(user_message) + len(agent_response)
        if total_length > 200:
            importance += 0.1
        if total_length > 500:
            importance += 0.1
        
        # 检查是否包含重要关键词
        important_keywords = [
            "重要", "关键", "问题", "错误", "成功", "失败", 
            "学习", "记住", "偏好", "设置", "配置"
        ]
        
        for keyword in important_keywords:
            if keyword in user_message or keyword in agent_response:
                importance += 0.1
                break
        
        # 限制在0.1-1.0之间
        return max(0.1, min(1.0, importance))
    
    def _extract_conversation_tags(self, user_message: str, agent_response: str) -> List[str]:
        """提取对话标签"""
        
        tags = ["conversation"]
        
        # 检测主题标签
        if any(word in user_message + agent_response for word in ["计算", "数学", "算式"]):
            tags.append("math")
        if any(word in user_message + agent_response for word in ["搜索", "查找", "信息"]):
            tags.append("search")
        if any(word in user_message + agent_response for word in ["文件", "保存", "读取"]):
            tags.append("file")
        if any(word in user_message + agent_response for word in ["代码", "编程", "脚本"]):
            tags.append("code")
        if any(word in user_message + agent_response for word in ["图片", "图像", "生成"]):
            tags.append("image")
        if any(word in user_message + agent_response for word in ["分析", "统计", "数据"]):
            tags.append("analysis")
        
        return tags
    
    def _calculate_relevance(self, memory_content: str, query_words: List[str]) -> float:
        """计算记忆与查询的相关性"""
        
        memory_words = memory_content.lower().split()
        
        # 计算词汇重叠度
        overlap_count = 0
        for word in query_words:
            if word in memory_words:
                overlap_count += 1
        
        if not query_words:
            return 0.0
        
        # 基础相关性评分
        relevance = overlap_count / len(query_words)
        
        # 考虑记忆内容长度，较短的匹配更精确
        if len(memory_words) < 50:
            relevance *= 1.2
        elif len(memory_words) > 200:
            relevance *= 0.8
        
        return min(1.0, relevance) 