"""
奇门遁甲缓存系统
提供内存LRU缓存和Redis缓存支持，优化计算性能
"""
# type: ignore

import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, Protocol, List, Tuple
from functools import wraps, lru_cache
from dataclasses import dataclass
import threading
import weakref

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    size: int = 0
    max_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate
        }


class CacheProtocol(Protocol):
    """缓存协议"""
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        ...
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        ...
    
    def clear(self) -> bool:
        """清空缓存"""
        ...
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        ...
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        ...


class LRUCacheNode:
    """LRU缓存节点"""
    
    def __init__(self, key: str = "", value: Any = None):
        self.key = key
        self.value = value
        self.expire_time: Optional[float] = None
        self.prev: Optional['LRUCacheNode'] = None
        self.next: Optional['LRUCacheNode'] = None


class ThreadSafeLRUCache:
    """线程安全的LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, LRUCacheNode] = {}
        self._stats = CacheStats(max_size=max_size)
        self._lock = threading.RLock()
        
        # 创建双向链表头尾节点
        self._head = LRUCacheNode()
        self._tail = LRUCacheNode()
        self._head.next = self._tail
        self._tail.prev = self._head
    
    def _add_node(self, node: LRUCacheNode) -> None:
        """在头部添加节点"""
        node.prev = self._head
        node.next = self._head.next
        if self._head.next:
            self._head.next.prev = node
        self._head.next = node
    
    def _remove_node(self, node: LRUCacheNode) -> None:
        """移除节点"""
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
    
    def _move_to_head(self, node: LRUCacheNode) -> None:
        """移动节点到头部"""
        self._remove_node(node)
        self._add_node(node)
    
    def _pop_tail(self) -> Optional[LRUCacheNode]:
        """移除尾部节点"""
        last_node = self._tail.prev
        if last_node and last_node != self._head:
            self._remove_node(last_node)
            return last_node
        return None
    
    def _is_expired(self, node: LRUCacheNode) -> bool:
        """检查节点是否过期"""
        if node.expire_time is None:
            return False
        return time.time() > node.expire_time
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            node = self._cache.get(key)
            if node is None:
                self._stats.misses += 1
                return None
            
            # 检查是否过期
            if self._is_expired(node):
                self.delete(key)
                self._stats.misses += 1
                return None
            
            # 移动到头部（最近使用）
            self._move_to_head(node)
            self._stats.hits += 1
            return node.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self._lock:
            node = self._cache.get(key)
            
            # 计算过期时间
            expire_time = None
            if ttl is not None:
                expire_time = time.time() + ttl
            elif self.default_ttl is not None:
                expire_time = time.time() + self.default_ttl
            
            if node:
                # 更新现有节点
                node.value = value
                node.expire_time = expire_time
                self._move_to_head(node)
            else:
                # 创建新节点
                new_node = LRUCacheNode(key, value)
                new_node.expire_time = expire_time
                
                self._cache[key] = new_node
                self._add_node(new_node)
                
                # 检查是否超过最大容量
                if len(self._cache) > self.max_size:
                    tail = self._pop_tail()
                    if tail:
                        del self._cache[tail.key]
                        self._stats.deletes += 1
            
            self._stats.sets += 1
            self._stats.size = len(self._cache)
            return True
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            node = self._cache.get(key)
            if node:
                self._remove_node(node)
                del self._cache[key]
                self._stats.deletes += 1
                self._stats.size = len(self._cache)
                return True
            return False
    
    def clear(self) -> bool:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
            self._stats.size = 0
            return True
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            node = self._cache.get(key)
            if node and not self._is_expired(node):
                return True
            return False
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                sets=self._stats.sets,
                deletes=self._stats.deletes,
                size=self._stats.size,
                max_size=self._stats.max_size
            )
    
    def cleanup_expired(self) -> int:
        """清理过期项"""
        expired_keys = []
        with self._lock:
            for key, node in self._cache.items():
                if self._is_expired(node):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.delete(key)
        
        return len(expired_keys)


class RedisCache:
    """Redis缓存实现"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", 
                 prefix: str = "qimen:", encoding: str = "utf-8"):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis不可用，请安装redis包")
        
        self.redis_client = redis.from_url(redis_url, decode_responses=False)  # type: ignore
        self.prefix = prefix
        self.encoding = encoding
        self._stats = CacheStats()
        self._lock = threading.RLock()
    
    def _make_key(self, key: str) -> str:
        """生成Redis键"""
        return f"{self.prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """反序列化值"""
        return pickle.loads(data)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            redis_key = self._make_key(key)
            data = self.redis_client.get(redis_key)  # type: ignore
            
            with self._lock:
                if data is None:
                    self._stats.misses += 1
                    return None
                
                self._stats.hits += 1
                return self._deserialize(data)
        
        except Exception as e:
            print(f"Redis get error: {e}")
            with self._lock:
                self._stats.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            redis_key = self._make_key(key)
            data = self._serialize(value)
            
            if ttl is not None:
                self.redis_client.setex(redis_key, ttl, data)
            else:
                self.redis_client.set(redis_key, data)
            
            with self._lock:
                self._stats.sets += 1
            return True
        
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            redis_key = self._make_key(key)
            result = self.redis_client.delete(redis_key)
            
            with self._lock:
                if result > 0:
                    self._stats.deletes += 1
                    return True
            return False
        
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """清空缓存"""
        try:
            keys = self.redis_client.keys(f"{self.prefix}*")
            if keys:
                self.redis_client.delete(*keys)
            return True
        
        except Exception as e:
            print(f"Redis clear error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            redis_key = self._make_key(key)
            return bool(self.redis_client.exists(redis_key))
        
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        with self._lock:
            try:
                info = self.redis_client.info('memory')
                used_memory = info.get('used_memory', 0)
                
                return CacheStats(
                    hits=self._stats.hits,
                    misses=self._stats.misses,
                    sets=self._stats.sets,
                    deletes=self._stats.deletes,
                    size=used_memory,
                    max_size=0
                )
            except:
                return self._stats


class MultiLevelCache:
    """多级缓存系统"""
    
    def __init__(self, l1_cache: CacheProtocol, l2_cache: Optional[CacheProtocol] = None):
        self.l1_cache = l1_cache  # 内存缓存
        self.l2_cache = l2_cache  # Redis缓存
        self._stats = CacheStats()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（先查L1，再查L2）"""
        # 先查L1缓存
        value = self.l1_cache.get(key)
        if value is not None:
            with self._lock:
                self._stats.hits += 1
            return value
        
        # 再查L2缓存
        if self.l2_cache:
            value = self.l2_cache.get(key)
            if value is not None:
                # 回填到L1缓存
                self.l1_cache.set(key, value)
                with self._lock:
                    self._stats.hits += 1
                return value
        
        with self._lock:
            self._stats.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值（同时设置L1和L2）"""
        l1_success = self.l1_cache.set(key, value, ttl)
        l2_success = True
        
        if self.l2_cache:
            l2_success = self.l2_cache.set(key, value, ttl)
        
        with self._lock:
            self._stats.sets += 1
        
        return l1_success and l2_success
    
    def delete(self, key: str) -> bool:
        """删除缓存值（同时删除L1和L2）"""
        l1_success = self.l1_cache.delete(key)
        l2_success = True
        
        if self.l2_cache:
            l2_success = self.l2_cache.delete(key)
        
        with self._lock:
            if l1_success or l2_success:
                self._stats.deletes += 1
        
        return l1_success or l2_success
    
    def clear(self) -> bool:
        """清空缓存"""
        l1_success = self.l1_cache.clear()
        l2_success = True
        
        if self.l2_cache:
            l2_success = self.l2_cache.clear()
        
        return l1_success and l2_success
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self.l1_cache.exists(key):
            return True
        
        if self.l2_cache and self.l2_cache.exists(key):
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, CacheStats]:
        """获取所有级别的缓存统计"""
        stats = {
            "total": self._stats,
            "l1": self.l1_cache.get_stats()
        }
        
        if self.l2_cache:
            stats["l2"] = self.l2_cache.get_stats()
        
        return stats


class CacheKeyGenerator:
    """缓存键生成器"""
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """生成缓存键"""
        # 构建键的组成部分
        key_parts = []
        
        # 处理位置参数
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, datetime):
                key_parts.append(arg.isoformat())
            else:
                key_parts.append(str(hash(str(arg))))
        
        # 处理关键字参数
        sorted_kwargs = sorted(kwargs.items())
        for key, value in sorted_kwargs:
            key_parts.append(f"{key}={value}")
        
        # 生成最终键
        key_string = "|".join(key_parts)
        
        # 使用MD5哈希避免键过长
        if len(key_string) > 100:
            return hashlib.md5(key_string.encode()).hexdigest()
        
        return key_string
    
    @staticmethod
    def generate_time_key(dt: datetime, precision: str = "hour") -> str:
        """生成基于时间的缓存键"""
        if precision == "year":
            return f"time:{dt.year}"
        elif precision == "month":
            return f"time:{dt.year}-{dt.month:02d}"
        elif precision == "day":
            return f"time:{dt.year}-{dt.month:02d}-{dt.day:02d}"
        elif precision == "hour":
            return f"time:{dt.year}-{dt.month:02d}-{dt.day:02d}-{dt.hour:02d}"
        elif precision == "minute":
            return f"time:{dt.year}-{dt.month:02d}-{dt.day:02d}-{dt.hour:02d}-{dt.minute:02d}"
        else:
            return f"time:{dt.isoformat()}"


class QimenCache:
    """奇门遁甲专用缓存管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # 创建L1缓存（内存LRU）
        l1_size = config.get("l1_max_size", 1000)
        l1_ttl = config.get("l1_ttl", 3600)  # 1小时
        self.l1_cache = ThreadSafeLRUCache(max_size=l1_size, default_ttl=l1_ttl)
        
        # 创建L2缓存（Redis，可选）
        self.l2_cache = None
        if config.get("enable_redis", False) and REDIS_AVAILABLE:
            redis_url = config.get("redis_url", "redis://localhost:6379/0")
            redis_prefix = config.get("redis_prefix", "qimen:")
            try:
                self.l2_cache = RedisCache(redis_url, redis_prefix)
            except Exception as e:
                print(f"Redis初始化失败: {e}")
        
        # 创建多级缓存
        self.cache = MultiLevelCache(self.l1_cache, self.l2_cache)
        
        # 缓存配置
        self.cache_solar_terms = config.get("cache_solar_terms", True)
        self.cache_ganzhi = config.get("cache_ganzhi", True)
        self.cache_ju_numbers = config.get("cache_ju_numbers", True)
        self.cache_palace_data = config.get("cache_palace_data", True)
        
        # 启动定期清理任务
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动定期清理任务"""
        def cleanup_task():
            while True:
                time.sleep(300)  # 5分钟清理一次
                try:
                    expired_count = self.l1_cache.cleanup_expired()
                    if expired_count > 0:
                        print(f"清理了{expired_count}个过期缓存项")
                except Exception as e:
                    print(f"缓存清理出错: {e}")
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def cache_solar_term_data(self, year: int, data: Dict[str, datetime], ttl: int = 86400) -> bool:
        """缓存节气数据（24小时）"""
        if not self.cache_solar_terms:
            return False
        
        key = f"solar_terms:{year}"
        return self.cache.set(key, data, ttl)
    
    def get_solar_term_data(self, year: int) -> Optional[Dict[str, datetime]]:
        """获取节气数据"""
        if not self.cache_solar_terms:
            return None
        
        key = f"solar_terms:{year}"
        return self.cache.get(key)
    
    def cache_ganzhi_data(self, dt: datetime, ganzhi_data: Dict[str, str], ttl: int = 3600) -> bool:
        """缓存干支数据（1小时）"""
        if not self.cache_ganzhi:
            return False
        
        time_key = CacheKeyGenerator.generate_time_key(dt, "day")
        key = f"ganzhi:{time_key}"
        return self.cache.set(key, ganzhi_data, ttl)
    
    def get_ganzhi_data(self, dt: datetime) -> Optional[Dict[str, str]]:
        """获取干支数据"""
        if not self.cache_ganzhi:
            return None
        
        time_key = CacheKeyGenerator.generate_time_key(dt, "day")
        key = f"ganzhi:{time_key}"
        return self.cache.get(key)
    
    def cache_ju_data(self, dt: datetime, ju_number: int, is_yang: bool, ttl: int = 1800) -> bool:
        """缓存局号数据（30分钟）"""
        if not self.cache_ju_numbers:
            return False
        
        time_key = CacheKeyGenerator.generate_time_key(dt, "hour")
        key = f"ju:{time_key}"
        data = {"ju_number": ju_number, "is_yang": is_yang}
        return self.cache.set(key, data, ttl)
    
    def get_ju_data(self, dt: datetime) -> Optional[Dict[str, Union[int, bool]]]:
        """获取局号数据"""
        if not self.cache_ju_numbers:
            return None
        
        time_key = CacheKeyGenerator.generate_time_key(dt, "hour")
        key = f"ju:{time_key}"
        return self.cache.get(key)
    
    def cache_palace_data(self, ju_key: str, palace_data: Any, ttl: int = 7200) -> bool:
        """缓存宫位数据（2小时）"""
        if not self.cache_palace_data:
            return False
        
        key = f"palace:{ju_key}"
        return self.cache.set(key, palace_data, ttl)
    
    def get_palace_data(self, ju_key: str) -> Optional[Any]:
        """获取宫位数据"""
        if not self.cache_palace_data:
            return None
        
        key = f"palace:{ju_key}"
        return self.cache.get(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = self.cache.get_stats()
        return {level: stat.to_dict() for level, stat in stats.items()}
    
    def clear_all_cache(self) -> bool:
        """清空所有缓存"""
        return self.cache.clear()


# 缓存装饰器
def qimen_cache(cache_key: Optional[str] = None, ttl: Optional[int] = None):
    """奇门计算缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取全局缓存实例
            global_cache = getattr(wrapper, '_cache', None)
            if global_cache is None:
                return func(*args, **kwargs)
            
            # 生成缓存键
            if cache_key:
                key = f"{cache_key}:{CacheKeyGenerator.generate_key(*args, **kwargs)}"
            else:
                key = f"{func.__name__}:{CacheKeyGenerator.generate_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            result = global_cache.cache.get(key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            global_cache.cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# 全局缓存实例
_global_cache: Optional[QimenCache] = None


def get_global_cache() -> QimenCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = QimenCache()
    return _global_cache


def init_cache(config: Dict[str, Any]) -> None:
    """初始化全局缓存"""
    global _global_cache
    _global_cache = QimenCache(config)


def clear_global_cache() -> bool:
    """清空全局缓存"""
    global _global_cache
    if _global_cache:
        return _global_cache.clear_all_cache()
    return True 