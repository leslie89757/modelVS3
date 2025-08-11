"""
奇门遁甲数据验证和错误处理模块
使用Pydantic实现数据验证，提供健壮的错误处理机制
"""
# type: ignore

from datetime import datetime, timezone
from typing import Optional, Union, Dict, Any, List, Generic, TypeVar
from enum import Enum
import traceback

try:
    from pydantic import BaseModel, validator, Field, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    # 如果没有安装pydantic，提供基础的验证
    PYDANTIC_AVAILABLE = False
    
    class BaseModel:  # type: ignore
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def validator(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator
    
    def Field(*args, **kwargs):  # type: ignore
        return None
    
    class ValidationError(Exception):  # type: ignore
        pass

try:
    from symbols import TIAN_GAN, DI_ZHI, SOLAR_TERMS, JIU_GONG, BA_MEN, JIU_XING, JIU_SHEN
except ImportError:
    from .symbols import TIAN_GAN, DI_ZHI, SOLAR_TERMS, JIU_GONG, BA_MEN, JIU_XING, JIU_SHEN


# 自定义异常类
class QimenValidationError(Exception):
    """奇门验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class QimenCalculationError(Exception):
    """奇门计算错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class QimenConfigurationError(Exception):
    """奇门配置错误"""
    pass


# Result类型实现
T = TypeVar('T')
E = TypeVar('E')


class Result(Generic[T, E]):
    """Result类型，用于函数返回值的错误处理"""
    
    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        self._value = value
        self._error = error
        self._is_ok = error is None
    
    @classmethod
    def ok(cls, value: T) -> 'Result[T, E]':
        """创建成功结果"""
        return cls(value=value)  # type: ignore
    
    @classmethod
    def error(cls, error: E) -> 'Result[T, E]':
        """创建错误结果"""
        return cls(error=error)  # type: ignore
    
    def is_ok(self) -> bool:
        """是否成功"""
        return self._is_ok
    
    def is_error(self) -> bool:
        """是否错误"""
        return not self._is_ok
    
    def unwrap(self) -> T:
        """获取值（如果是错误则抛出异常）"""
        if self._is_ok:
            return self._value
        else:
            raise RuntimeError(f"尝试从错误结果中获取值: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """获取值或默认值"""
        return self._value if self._is_ok else default
    
    def error_value(self) -> E:
        """获取错误值"""
        return self._error
    
    def map(self, func):
        """映射值"""
        if self._is_ok:
            try:
                return Result.ok(func(self._value))
            except Exception as e:
                return Result.error(str(e))
        else:
            return self
    
    def and_then(self, func):
        """链式操作"""
        if self._is_ok:
            return func(self._value)
        else:
            return self


# 枚举类型
class JuMode(str, Enum):
    """局号计算模式"""
    CHABU = "拆补"
    HUOPAN = "活盘"
    SHIJIA = "时家"
    RIJIA = "日家"


class PalaceMode(str, Enum):
    """宫位模式"""
    TURN = "turn"  # 转盘
    FLY = "fly"    # 飞盘


class CalculationPrecision(str, Enum):
    """计算精度"""
    HIGH = "high"      # 高精度（使用天文算法）
    MEDIUM = "medium"  # 中精度（使用平均值）
    LOW = "low"        # 低精度（简化计算）


# 验证模型
class TimeInput(BaseModel):
    """时间输入验证"""
    year: int = Field(..., ge=1900, le=2100, description="年份（1900-2100）")
    month: int = Field(..., ge=1, le=12, description="月份（1-12）")
    day: int = Field(..., ge=1, le=31, description="日期（1-31）")
    hour: int = Field(..., ge=0, le=23, description="小时（0-23）")
    minute: int = Field(0, ge=0, le=59, description="分钟（0-59）")
    second: int = Field(0, ge=0, le=59, description="秒（0-59）")
    timezone: str = Field("Asia/Shanghai", description="时区")
    
    @validator('day')
    def validate_day(cls, v, values):
        """验证日期的有效性"""
        if 'year' in values and 'month' in values:
            year = values['year']
            month = values['month']
            
            # 每月天数
            days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            
            # 闰年二月
            if month == 2 and cls.is_leap_year(year):
                max_day = 29
            else:
                max_day = days_in_month[month - 1]
            
            if v > max_day:
                raise ValueError(f"{year}年{month}月最多{max_day}天")
        
        return v
    
    @staticmethod
    def is_leap_year(year: int) -> bool:
        """判断是否为闰年"""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    
    def to_datetime(self) -> datetime:
        """转换为datetime对象"""
        return datetime(self.year, self.month, self.day, 
                       self.hour, self.minute, self.second)


class LocationInput(BaseModel):
    """地理位置输入验证"""
    longitude: float = Field(116.4667, ge=-180, le=180, description="经度（-180到180）")
    latitude: float = Field(39.9042, ge=-90, le=90, description="纬度（-90到90）")
    altitude: float = Field(0, ge=-1000, le=10000, description="海拔米数")
    
    @validator('longitude')
    def validate_longitude(cls, v):
        """验证经度"""
        if not -180 <= v <= 180:
            raise ValueError("经度必须在-180到180之间")
        return v
    
    @validator('latitude')
    def validate_latitude(cls, v):
        """验证纬度"""
        if not -90 <= v <= 90:
            raise ValueError("纬度必须在-90到90之间")
        return v


class QimenCalculationInput(BaseModel):
    """奇门计算输入验证"""
    time_input: TimeInput
    location: LocationInput = Field(default_factory=LocationInput)
    ju_mode: JuMode = Field(JuMode.HUOPAN, description="局号计算模式")
    palace_mode: PalaceMode = Field(PalaceMode.TURN, description="宫位模式")
    precision: CalculationPrecision = Field(CalculationPrecision.HIGH, description="计算精度")
    use_true_solar_time: bool = Field(True, description="是否使用真太阳时")
    plugins: List[str] = Field(default_factory=list, description="启用的分析插件")
    
    @validator('plugins')
    def validate_plugins(cls, v):
        """验证插件名称"""
        available_plugins = ["zhifu", "wangshuai", "geju", "yingqi"]
        invalid_plugins = [p for p in v if p not in available_plugins]
        if invalid_plugins:
            raise ValueError(f"无效的插件: {invalid_plugins}")
        return v


class GanZhiValidated(BaseModel):
    """干支验证模型"""
    gan: str = Field(..., description="天干")
    zhi: str = Field(..., description="地支")
    
    @validator('gan')
    def validate_gan(cls, v):
        """验证天干"""
        if v not in TIAN_GAN:
            raise ValueError(f"无效的天干: {v}")
        return v
    
    @validator('zhi')
    def validate_zhi(cls, v):
        """验证地支"""
        if v not in DI_ZHI:
            raise ValueError(f"无效的地支: {v}")
        return v
    
    @validator('zhi')
    def validate_ganzhi_combination(cls, v, values):
        """验证干支组合"""
        if 'gan' in values:
            gan = values['gan']
            gan_index = TIAN_GAN.index(gan)
            zhi_index = DI_ZHI.index(v)
            
            # 检查奇偶性
            if (gan_index % 2) != (zhi_index % 2):
                raise ValueError(f"干支组合错误: {gan}{v}（奇偶性不匹配）")
        
        return v


class PalaceInfoValidated(BaseModel):
    """宫位信息验证"""
    gong_num: int = Field(..., ge=1, le=9, description="宫位号（1-9）")
    gong_name: str = Field(..., description="宫位名称")
    gan: str = Field(..., description="天干")
    men: str = Field(..., description="八门")
    xing: str = Field(..., description="九星")
    shen: str = Field(..., description="九神")
    
    @validator('gong_name')
    def validate_gong_name(cls, v):
        """验证宫位名称"""
        valid_names = list(JIU_GONG.values())
        if v not in valid_names:
            raise ValueError(f"无效的宫位名称: {v}")
        return v
    
    @validator('gan')
    def validate_gan(cls, v):
        """验证天干"""
        valid_gans = TIAN_GAN + ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
        if v not in valid_gans:
            raise ValueError(f"无效的天干: {v}")
        return v
    
    @validator('men')
    def validate_men(cls, v):
        """验证八门"""
        if v not in BA_MEN:
            raise ValueError(f"无效的八门: {v}")
        return v
    
    @validator('xing')
    def validate_xing(cls, v):
        """验证九星"""
        if v not in JIU_XING:
            raise ValueError(f"无效的九星: {v}")
        return v
    
    @validator('shen')
    def validate_shen(cls, v):
        """验证九神"""
        if v not in JIU_SHEN:
            raise ValueError(f"无效的九神: {v}")
        return v


class JuNumberValidated(BaseModel):
    """局号验证"""
    ju_number: int = Field(..., ge=1, le=9, description="局号（1-9）")
    is_yang: bool = Field(..., description="是否阳遁")
    
    @validator('ju_number')
    def validate_ju_number(cls, v):
        """验证局号范围"""
        if not 1 <= v <= 9:
            raise ValueError(f"局号必须在1-9之间，当前值: {v}")
        return v


# 验证器类
class QimenValidator:
    """奇门遁甲验证器"""
    
    def __init__(self):
        self.enabled = PYDANTIC_AVAILABLE
    
    def validate_time_input(self, data: Dict[str, Any]) -> Result[TimeInput, str]:
        """验证时间输入"""
        try:
            if self.enabled:
                validated = TimeInput(**data)
            else:
                validated = self._basic_time_validation(data)
            return Result.ok(validated)
        except (ValidationError, ValueError) as e:
            return Result.error(f"时间输入验证失败: {str(e)}")
        except Exception as e:
            return Result.error(f"验证过程出错: {str(e)}")
    
    def validate_calculation_input(self, data: Dict[str, Any]) -> Result[QimenCalculationInput, str]:
        """验证计算输入"""
        try:
            if self.enabled:
                validated = QimenCalculationInput(**data)
            else:
                validated = self._basic_calculation_validation(data)
            return Result.ok(validated)
        except (ValidationError, ValueError) as e:
            return Result.error(f"计算输入验证失败: {str(e)}")
        except Exception as e:
            return Result.error(f"验证过程出错: {str(e)}")
    
    def validate_ganzhi(self, gan: str, zhi: str) -> Result[GanZhiValidated, str]:
        """验证干支"""
        try:
            if self.enabled:
                validated = GanZhiValidated(gan=gan, zhi=zhi)
            else:
                validated = self._basic_ganzhi_validation(gan, zhi)
            return Result.ok(validated)
        except (ValidationError, ValueError) as e:
            return Result.error(f"干支验证失败: {str(e)}")
        except Exception as e:
            return Result.error(f"验证过程出错: {str(e)}")
    
    def validate_ju_number(self, ju_number: int, is_yang: bool) -> Result[JuNumberValidated, str]:
        """验证局号"""
        try:
            if self.enabled:
                validated = JuNumberValidated(ju_number=ju_number, is_yang=is_yang)
            else:
                validated = self._basic_ju_validation(ju_number, is_yang)
            return Result.ok(validated)
        except (ValidationError, ValueError) as e:
            return Result.error(f"局号验证失败: {str(e)}")
        except Exception as e:
            return Result.error(f"验证过程出错: {str(e)}")
    
    def _basic_time_validation(self, data: Dict[str, Any]) -> Any:
        """基础时间验证（无pydantic时使用）"""
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour = data.get('hour', 0)
        minute = data.get('minute', 0)
        second = data.get('second', 0)
        
        if not isinstance(year, int) or not 1900 <= year <= 2100:
            raise ValueError("年份必须是1900-2100之间的整数")
        
        if not isinstance(month, int) or not 1 <= month <= 12:
            raise ValueError("月份必须是1-12之间的整数")
        
        if not isinstance(day, int) or not 1 <= day <= 31:
            raise ValueError("日期必须是1-31之间的整数")
        
        if not isinstance(hour, int) or not 0 <= hour <= 23:
            raise ValueError("小时必须是0-23之间的整数")
        
        # 创建一个简单的对象来模拟TimeInput
        class BasicTimeInput:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
            
            def to_datetime(self):
                return datetime(self.year, self.month, self.day,
                              self.hour, self.minute, self.second)
        
        return BasicTimeInput(**data)
    
    def _basic_ganzhi_validation(self, gan: str, zhi: str) -> Any:
        """基础干支验证"""
        if gan not in TIAN_GAN:
            raise ValueError(f"无效的天干: {gan}")
        
        if zhi not in DI_ZHI:
            raise ValueError(f"无效的地支: {zhi}")
        
        # 检查奇偶性
        gan_index = TIAN_GAN.index(gan)
        zhi_index = DI_ZHI.index(zhi)
        if (gan_index % 2) != (zhi_index % 2):
            raise ValueError(f"干支组合错误: {gan}{zhi}")
        
        class BasicGanZhi:
            def __init__(self, gan, zhi):
                self.gan = gan
                self.zhi = zhi
        
        return BasicGanZhi(gan, zhi)
    
    def _basic_ju_validation(self, ju_number: int, is_yang: bool) -> Any:
        """基础局号验证"""
        if not isinstance(ju_number, int) or not 1 <= ju_number <= 9:
            raise ValueError(f"局号必须是1-9之间的整数: {ju_number}")
        
        if not isinstance(is_yang, bool):
            raise ValueError("阴阳遁标志必须是布尔值")
        
        class BasicJu:
            def __init__(self, ju_number, is_yang):
                self.ju_number = ju_number
                self.is_yang = is_yang
        
        return BasicJu(ju_number, is_yang)
    
    def _basic_calculation_validation(self, data: Dict[str, Any]) -> Any:
        """基础计算验证"""
        time_data = data.get('time_input', {})
        time_input = self._basic_time_validation(time_data)
        
        class BasicCalculationInput:
            def __init__(self, time_input, **kwargs):
                self.time_input = time_input
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        return BasicCalculationInput(time_input, **data)


# 错误处理装饰器
def handle_qimen_errors(func):
    """奇门错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QimenValidationError as e:
            return Result.error(f"验证错误: {e.message}")
        except QimenCalculationError as e:
            return Result.error(f"计算错误: {e.message}")
        except Exception as e:
            error_trace = traceback.format_exc()
            return Result.error(f"未知错误: {str(e)}\n{error_trace}")
    
    return wrapper


def safe_calculate(func):
    """安全计算装饰器"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return Result.ok(result)
        except Exception as e:
            return Result.error(str(e))
    
    return wrapper


# 全局验证器实例
validator = QimenValidator()


# 便捷验证函数
def validate_time(data: Dict[str, Any]) -> Result[TimeInput, str]:
    """验证时间输入（便捷函数）"""
    return validator.validate_time_input(data)


def validate_ganzhi(gan: str, zhi: str) -> Result[GanZhiValidated, str]:
    """验证干支（便捷函数）"""
    return validator.validate_ganzhi(gan, zhi)


def validate_ju(ju_number: int, is_yang: bool) -> Result[JuNumberValidated, str]:
    """验证局号（便捷函数）"""
    return validator.validate_ju_number(ju_number, is_yang) 