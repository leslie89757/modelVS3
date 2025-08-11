"""
奇门遁甲历法计算模块
负责时间转换、干支计算、节气获取等核心历法功能
支持真太阳时、夏令时、多时区处理
"""

import pytz
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, TypedDict, Union

try:
    from symbols import TIAN_GAN, DI_ZHI, WU_XING, SHI_CHEN, SOLAR_TERMS
    from astronomical import get_current_solar_term, get_true_solar_time
    from config import get_config
    from ganzhi import ganzhi_calculator
except ImportError:
    from .symbols import TIAN_GAN, DI_ZHI, WU_XING, SHI_CHEN, SOLAR_TERMS
    from .astronomical import get_current_solar_term, get_true_solar_time  
    from .config import get_config
    from .ganzhi import ganzhi_calculator


class CalendarInfo(TypedDict):
    """历法信息结构"""
    year: int
    month: int 
    day: int
    hour: int
    minute: int
    second: int
    timezone: str
    solar_term: str
    solar_term_index: int
    year_gan: str
    year_zhi: str
    month_gan: str
    month_zhi: str
    day_gan: str
    day_zhi: str
    hour_gan: str
    hour_zhi: str
    shi_chen: str
    is_early_zi: bool  # 是否早子时
    is_late_zi: bool   # 是否晚子时
    jie_qi_day: int    # 节气日
    yuan_shou: int     # 元首（节气在月内的位置）
    
    # 真太阳时相关信息
    use_true_solar_time: bool  # 是否使用真太阳时
    true_solar_time: Optional[str]  # 真太阳时字符串表示
    time_difference_minutes: float  # 时间差异（分钟）
    standard_time_shi_chen: str  # 标准时间对应的时辰


def from_datetime(
    ts: Union[str, datetime], 
    tz: str = "Asia/Shanghai"
) -> CalendarInfo:
    """
    从datetime对象或字符串转换为历法信息（使用优化后的算法）
    
    Args:
        ts: 时间戳字符串或datetime对象
        tz: 时区字符串
        
    Returns:
        CalendarInfo: 历法信息
    """
    if isinstance(ts, str):
        dt = parser.parse(ts)
    else:
        dt = ts
    
    # 时区处理 - 统一转换为naive datetime以避免时区问题
    if dt.tzinfo is not None:
        # 如果有时区信息，先转换到指定时区，然后移除时区信息
        timezone = pytz.timezone(tz)
        dt = dt.astimezone(timezone).replace(tzinfo=None)
    # 如果没有时区信息，假设已经是指定时区的本地时间，直接使用
    
    # 获取配置
    config = get_config()
    
    # 使用真太阳时（如果配置启用）
    calc_dt = dt
    true_solar_time_dt = None
    time_diff_minutes = 0.0
    
    if config.use_true_solar_time:
        true_solar_time_dt = get_true_solar_time(dt, config.longitude)
        calc_dt = true_solar_time_dt
        time_diff_minutes = (dt - true_solar_time_dt).total_seconds() / 60.0
    
    # 计算标准时间对应的时辰（用于对比）
    standard_hour_zhi_idx = (dt.hour + 1) // 2 if dt.hour != 23 else 0
    standard_shi_chen = DI_ZHI[standard_hour_zhi_idx] + "时"
    
    # 统一使用 ganzhi_calculator 作为唯一入口（避免多种算法干扰）
    year_gan, year_zhi = ganzhi_calculator.calculate_year_ganzhi(calc_dt.year)
    month_gan, month_zhi = ganzhi_calculator.calculate_month_ganzhi(calc_dt)
    day_gan, day_zhi = ganzhi_calculator.calculate_day_ganzhi(calc_dt)
    
    # 时柱需要先获取日干再计算
    hour_zhi_index = 0 if calc_dt.hour == 23 else (calc_dt.hour + 1) // 2
    hour_zhi = DI_ZHI[hour_zhi_index]
    
    # 使用五鼠遁日起时法计算时干
    day_gan_index = TIAN_GAN.index(day_gan)
    DAY_HOUR_GAN_TABLE = {
        0: 0, 5: 0,  # 甲日、己日起甲子时
        1: 2, 6: 2,  # 乙日、庚日起丙子时  
        2: 4, 7: 4,  # 丙日、辛日起戊子时
        3: 6, 8: 6,  # 丁日、壬日起庚子时
        4: 8, 9: 8   # 戊日、癸日起壬子时
    }
    base_hour_gan_index = DAY_HOUR_GAN_TABLE.get(day_gan_index, 0)
    hour_gan_index = (base_hour_gan_index + hour_zhi_index) % 10
    hour_gan = TIAN_GAN[hour_gan_index]
    
    ganzhi_data = {
        "year_gan": year_gan, "year_zhi": year_zhi,
        "month_gan": month_gan, "month_zhi": month_zhi,
        "day_gan": day_gan, "day_zhi": day_zhi,
        "hour_gan": hour_gan, "hour_zhi": hour_zhi,
        "shi_chen": get_shi_chen(calc_dt.hour)
    }
    
    # 使用精确节气计算
    if config.solar_term_algorithm == "astronomical":
        solar_term, solar_term_index, solar_term_time = get_current_solar_term(calc_dt)
        # 计算元首（5天为一元，每个节气最多6元）
        days_diff = (calc_dt - solar_term_time).days if calc_dt >= solar_term_time else 0
        yuan_shou = min(max((days_diff // 5) + 1, 1), 6)
        jie_qi_day = solar_term_time.day
    else:
        # 向后兼容：使用原有算法
        solar_term, solar_term_index = get_solar_term(calc_dt.year, calc_dt.month, calc_dt.day)
        jie_qi_day = get_jie_qi_day(calc_dt.year, calc_dt.month, solar_term)
        yuan_shou = get_yuan_shou(calc_dt.day, jie_qi_day)
    
    # 判断早子时和晚子时
    is_early_zi = (calc_dt.hour == 0) and (calc_dt.minute < 30)
    is_late_zi = (calc_dt.hour == 23) and (calc_dt.minute >= 30)
    
    # 构建历法信息
    calendar_info = CalendarInfo(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        second=dt.second,
        timezone=tz,
        solar_term=solar_term,
        solar_term_index=solar_term_index,
        year_gan=ganzhi_data["year_gan"],
        year_zhi=ganzhi_data["year_zhi"],
        month_gan=ganzhi_data["month_gan"],
        month_zhi=ganzhi_data["month_zhi"],
        day_gan=ganzhi_data["day_gan"],
        day_zhi=ganzhi_data["day_zhi"],
        hour_gan=ganzhi_data["hour_gan"],
        hour_zhi=ganzhi_data["hour_zhi"],
        shi_chen=ganzhi_data["shi_chen"],
        is_early_zi=is_early_zi,
        is_late_zi=is_late_zi,
        jie_qi_day=jie_qi_day,
        yuan_shou=yuan_shou,
        
        # 真太阳时相关信息
        use_true_solar_time=config.use_true_solar_time,
        true_solar_time=true_solar_time_dt.strftime("%H:%M:%S") if true_solar_time_dt else None,
        time_difference_minutes=time_diff_minutes,
        standard_time_shi_chen=standard_shi_chen
    )
    
    return calendar_info


def get_solar_term(year: int, month: int, day: int) -> tuple[str, int]:
    """
    计算节气
    
    Args:
        year: 年份
        month: 月份  
        day: 日期
        
    Returns:
        tuple: (节气名称, 节气索引)
    """
    from astronomical import astro_calculator
    dt = datetime(year, month, day)
    
    solar_term, term_index, _ = astro_calculator.get_current_solar_term(dt)
    
    return solar_term, term_index


def get_shi_chen(hour: int) -> str:
    """
    根据小时获取时辰
    
    Args:
        hour: 小时（0-23）
        
    Returns:
        str: 时辰名称
    """
    time_index = ((hour + 1) // 2) % 12
    return SHI_CHEN[time_index]


def get_jie_qi_day(year: int, month: int, solar_term: str) -> int:
    """
    获取节气日
    
    Args:
        year: 年份
        month: 月份
        solar_term: 节气名称
        
    Returns:
        int: 节气日
    """
    # 简化实现，返回近似日期
    if solar_term in ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]:
        return 6
    else:
        return 21


def get_yuan_shou(day: int, jie_qi_day: int) -> int:
    """
    计算元首（节气在月内的位置）
    
    Args:
        day: 日期
        jie_qi_day: 节气日
        
    Returns:
        int: 元首值
    """
    if day >= jie_qi_day:
        return (day - jie_qi_day) // 5 + 1
    else:
        return (day + 30 - jie_qi_day) // 5 + 1


def is_zi_shi_split(dt: datetime) -> bool:
    """
    判断是否需要分早晚子时
    
    Args:
        dt: 时间对象
        
    Returns:
        bool: 是否分早晚子时
    """
    return dt.hour == 0 or (dt.hour == 23 and dt.minute >= 30) 