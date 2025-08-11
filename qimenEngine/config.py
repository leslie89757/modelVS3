"""
奇门遁甲配置管理系统
支持多种配置格式、环境变量覆盖、配置验证和热重载
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import configparser
    INI_AVAILABLE = True
except ImportError:
    INI_AVAILABLE = False


class ConfigFormat(str, Enum):
    """配置文件格式"""
    JSON = "json"
    YAML = "yaml"
    INI = "ini"
    ENV = "env"


@dataclass
class ConfigSource:
    """配置源定义"""
    path: Optional[str] = None
    format: ConfigFormat = ConfigFormat.JSON
    required: bool = False
    watch: bool = False
    env_prefix: Optional[str] = None


@dataclass 
class QimenConfig:
    """奇门遁甲配置结构"""
    
    # 计算精度设置
    calculation_precision: str = "high"  # high, medium, low
    use_true_solar_time: bool = False
    longitude: float = 116.4667  # 北京经度
    latitude: float = 39.9042    # 北京纬度
    
    # 默认起局方法
    default_ju_mode: str = "活盘"  # 活盘, 拆补, 时家, 日家
    default_palace_mode: str = "turn"  # turn, fly
    
    # 节气计算设置
    solar_term_algorithm: str = "astronomical"  # astronomical, average, simple
    cache_solar_terms: bool = True
    
    # 干支计算设置
    use_solar_terms_for_month: bool = True
    ganzhi_precision: str = "standard"  # standard, precise
    cache_ganzhi: bool = True
    
    # 缓存设置
    cache_enabled: bool = True
    cache_l1_max_size: int = 1000
    cache_l1_ttl: int = 3600
    cache_enable_redis: bool = False
    cache_redis_url: str = "redis://localhost:6379/0"
    cache_redis_prefix: str = "qimen:"
    
    # 插件设置
    enabled_plugins: List[str] = field(default_factory=lambda: ["zhifu", "wangshuai", "geju", "yingqi"])
    plugin_config: Dict[str, Any] = field(default_factory=dict)
    
    # 输出设置
    output_format: str = "json"  # json, yaml, text
    output_encoding: str = "utf-8"
    enable_rich_output: bool = True
    
    # 日志设置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # 性能设置
    enable_profiling: bool = False
    max_calculation_time: float = 30.0  # 最大计算时间（秒）
    
    # 验证设置
    strict_validation: bool = True
    allow_invalid_dates: bool = False
    
    # API设置
    api_enabled: bool = False
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_debug: bool = False
    
    # 安全设置
    rate_limiting: bool = False
    max_requests_per_minute: int = 60


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_sources: Optional[List[ConfigSource]] = None):
        self.config_sources = config_sources or []
        self.config = QimenConfig()
        self.watchers: Dict[str, threading.Thread] = {}
        self.change_callbacks: List[Callable[[QimenConfig], None]] = []
        self._lock = threading.RLock()
        self._last_modified: Dict[str, float] = {}
        
        # 设置默认配置源
        if not self.config_sources:
            self._setup_default_sources()
        
        # 加载配置
        self.load_config()
    
    def _setup_default_sources(self):
        """设置默认配置源"""
        # 1. 默认配置文件
        default_config_paths = [
            "qimen_config.yaml",
            "qimen_config.json", 
            "config/qimen.yaml",
            "config/qimen.json",
            os.path.expanduser("~/.qimen/config.yaml"),
            "/etc/qimen/config.yaml"
        ]
        
        for path in default_config_paths:
            if os.path.exists(path):
                if path.endswith('.yaml') and YAML_AVAILABLE:
                    self.config_sources.append(ConfigSource(
                        path=path, 
                        format=ConfigFormat.YAML,
                        watch=True
                    ))
                elif path.endswith('.json'):
                    self.config_sources.append(ConfigSource(
                        path=path,
                        format=ConfigFormat.JSON,
                        watch=True
                    ))
                break
        
        # 2. 环境变量
        self.config_sources.append(ConfigSource(
            format=ConfigFormat.ENV,
            env_prefix="QIMEN_"
        ))
    
    def load_config(self):
        """加载配置"""
        with self._lock:
            for source in self.config_sources:
                try:
                    if source.format == ConfigFormat.ENV:
                        self._load_from_env(source)
                    elif source.path:
                        self._load_from_file(source)
                        
                        # 启动文件监视
                        if source.watch and source.path and source.path not in self.watchers:
                            self._start_file_watcher(source)
                            
                except Exception as e:
                    if source.required:
                        raise ConfigError(f"无法加载必需的配置源 {source.path}: {e}")
                    else:
                        logging.warning(f"跳过配置源 {source.path}: {e}")
        
        # 验证配置
        self._validate_config()
        
        # 通知回调
        self._notify_callbacks()
    
    def _load_from_file(self, source: ConfigSource):
        """从文件加载配置"""
        if not source.path or not os.path.exists(source.path):
            return
        
        # 检查文件修改时间
        mtime = os.path.getmtime(source.path)
        if source.path in self._last_modified and self._last_modified[source.path] >= mtime:
            return
        
        self._last_modified[source.path] = mtime
        
        with open(source.path, 'r', encoding='utf-8') as f:
            if source.format == ConfigFormat.JSON:
                data = json.load(f)
            elif source.format == ConfigFormat.YAML and YAML_AVAILABLE:
                data = yaml.safe_load(f)
            elif source.format == ConfigFormat.INI and INI_AVAILABLE:
                parser = configparser.ConfigParser()
                parser.read(source.path)
                data = self._ini_to_dict(parser)
            else:
                raise ConfigError(f"不支持的配置格式: {source.format}")
        
        # 合并配置
        self._merge_config(data)
        
        logging.info(f"已加载配置文件: {source.path}")
    
    def _load_from_env(self, source: ConfigSource):
        """从环境变量加载配置"""
        prefix = source.env_prefix or "QIMEN_"
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                
                # 处理嵌套键（使用下划线分隔）
                keys = config_key.split('_')
                current = env_config
                
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                # 尝试转换类型
                current[keys[-1]] = self._convert_env_value(value)
        
        if env_config:
            self._merge_config(env_config)
            logging.info("已加载环境变量配置")
    
    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值类型"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON
        if value.startswith(('{', '[', '"')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 字符串
        return value
    
    def _ini_to_dict(self, parser: 'configparser.ConfigParser') -> Dict[str, Any]:
        """将INI解析器转换为字典"""
        result = {}
        
        for section_name in parser.sections():
            section = {}
            for key, value in parser.items(section_name):
                section[key] = self._convert_env_value(value)
            result[section_name] = section
        
        return result
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """合并配置"""
        def deep_merge(target: Dict[str, Any], source: Dict[str, Any]):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        # 转换为字典
        config_dict = self.config.__dict__.copy()
        
        # 合并新配置
        deep_merge(config_dict, new_config)
        
        # 更新配置对象
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def _validate_config(self):
        """验证配置"""
        # 验证精度设置
        if self.config.calculation_precision not in ["high", "medium", "low"]:
            raise ConfigError(f"无效的计算精度: {self.config.calculation_precision}")
        
        # 验证起局方法
        if self.config.default_ju_mode not in ["活盘", "拆补", "时家", "日家"]:
            raise ConfigError(f"无效的起局方法: {self.config.default_ju_mode}")
        
        # 验证宫位模式
        if self.config.default_palace_mode not in ["turn", "fly"]:
            raise ConfigError(f"无效的宫位模式: {self.config.default_palace_mode}")
        
        # 验证经纬度
        if not -180 <= self.config.longitude <= 180:
            raise ConfigError(f"无效的经度: {self.config.longitude}")
        
        if not -90 <= self.config.latitude <= 90:
            raise ConfigError(f"无效的纬度: {self.config.latitude}")
        
        # 验证缓存设置
        if self.config.cache_l1_max_size <= 0:
            raise ConfigError(f"缓存大小必须大于0: {self.config.cache_l1_max_size}")
        
        # 验证插件
        available_plugins = ["zhifu", "wangshuai", "geju", "yingqi"]
        invalid_plugins = [p for p in self.config.enabled_plugins if p not in available_plugins]
        if invalid_plugins:
            logging.warning(f"无效的插件: {invalid_plugins}")
    
    def _start_file_watcher(self, source: ConfigSource):
        """启动文件监视器"""
        def watch_file():
            while True:
                try:
                    time.sleep(1)  # 每秒检查一次
                    if source.path and os.path.exists(source.path):
                        mtime = os.path.getmtime(source.path)
                        if source.path in self._last_modified:
                            if mtime > self._last_modified[source.path]:
                                logging.info(f"检测到配置文件变化: {source.path}")
                                self._load_from_file(source)
                                self._validate_config()
                                self._notify_callbacks()
                except Exception as e:
                    logging.error(f"文件监视出错: {e}")
        
        watcher = threading.Thread(target=watch_file, daemon=True)
        watcher.start()
        if source.path:
            self.watchers[source.path] = watcher
    
    def _notify_callbacks(self):
        """通知配置变更回调"""
        for callback in self.change_callbacks:
            try:
                callback(self.config)
            except Exception as e:
                logging.error(f"配置变更回调出错: {e}")
    
    def add_change_callback(self, callback: Callable[[QimenConfig], None]):
        """添加配置变更回调"""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[QimenConfig], None]):
        """移除配置变更回调"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
    
    def get_config(self) -> QimenConfig:
        """获取当前配置"""
        with self._lock:
            return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            with self._lock:
                old_config = self.config.__dict__.copy()
                
                # 应用更新
                for key, value in updates.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                    else:
                        logging.warning(f"未知的配置项: {key}")
                
                # 验证配置
                self._validate_config()
                
                # 通知回调
                self._notify_callbacks()
                
                logging.info(f"配置已更新: {updates}")
                return True
                
        except Exception as e:
            # 回滚配置
            for key, value in old_config.items():
                setattr(self.config, key, value)
            
            logging.error(f"配置更新失败: {e}")
            return False
    
    def save_config(self, path: str, format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """保存配置到文件"""
        try:
            config_dict = self.config.__dict__.copy()
            
            # 移除不可序列化的字段
            if 'change_callbacks' in config_dict:
                del config_dict['change_callbacks']
            
            with open(path, 'w', encoding='utf-8') as f:
                if format == ConfigFormat.JSON:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                elif format == ConfigFormat.YAML and YAML_AVAILABLE:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ConfigError(f"不支持的保存格式: {format}")
            
            logging.info(f"配置已保存到: {path}")
            return True
            
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
            return False
    
    def get_effective_config(self) -> Dict[str, Any]:
        """获取有效配置（包含来源信息）"""
        config_dict = self.config.__dict__.copy()
        
        return {
            "config": config_dict,
            "sources": [
                {
                    "path": source.path,
                    "format": source.format.value,
                    "required": source.required,
                    "watch": source.watch
                }
                for source in self.config_sources
            ],
            "last_loaded": datetime.now().isoformat(),
            "validation_status": "valid"
        }


class ConfigError(Exception):
    """配置错误"""
    pass


# 全局配置管理器
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def get_config() -> QimenConfig:
    """获取当前配置"""
    return get_config_manager().get_config()


def init_config(config_sources: Optional[List[ConfigSource]] = None) -> ConfigManager:
    """初始化配置管理器"""
    global _global_config_manager
    _global_config_manager = ConfigManager(config_sources)
    return _global_config_manager


def update_config(updates: Dict[str, Any]) -> bool:
    """更新全局配置"""
    return get_config_manager().update_config(updates)


def save_config(path: str, format: ConfigFormat = ConfigFormat.JSON) -> bool:
    """保存全局配置"""
    return get_config_manager().save_config(path, format)


# 配置装饰器
def require_config(config_key: str, default_value: Any = None):
    """配置依赖装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            config = get_config()
            if hasattr(config, config_key):
                value = getattr(config, config_key)
                if value is None and default_value is not None:
                    setattr(config, config_key, default_value)
                    value = default_value
                kwargs[config_key] = value
            elif default_value is not None:
                kwargs[config_key] = default_value
            else:
                raise ConfigError(f"缺少必需的配置项: {config_key}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 预定义配置模板
class ConfigTemplates:
    """配置模板"""
    
    @staticmethod
    def get_high_precision_config() -> Dict[str, Any]:
        """高精度配置模板"""
        return {
            "calculation_precision": "high",
            "use_true_solar_time": True,
            "solar_term_algorithm": "astronomical",
            "ganzhi_precision": "precise",
            "cache_enabled": True,
            "strict_validation": True
        }
    
    @staticmethod
    def get_performance_config() -> Dict[str, Any]:
        """性能优化配置模板"""
        return {
            "calculation_precision": "medium",
            "cache_enabled": True,
            "cache_l1_max_size": 2000,
            "cache_enable_redis": True,
            "enabled_plugins": ["zhifu", "wangshuai"],
            "strict_validation": False
        }
    
    @staticmethod
    def get_minimal_config() -> Dict[str, Any]:
        """最小配置模板"""
        return {
            "calculation_precision": "low",
            "cache_enabled": False,
            "enabled_plugins": ["zhifu"],
            "strict_validation": False,
            "enable_rich_output": False
        }
    
    @staticmethod
    def get_api_config() -> Dict[str, Any]:
        """API服务配置模板"""
        return {
            "api_enabled": True,
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "cache_enabled": True,
            "cache_enable_redis": True,
            "rate_limiting": True,
            "max_requests_per_minute": 100,
            "log_level": "INFO"
        } 