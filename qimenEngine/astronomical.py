"""
奇门遁甲天文算法模块
基于精确天文算法实现节气计算、时差方程、真太阳时等功能
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Tuple, List, Optional
from functools import lru_cache

try:
    from symbols import SOLAR_TERMS
except ImportError:
    from .symbols import SOLAR_TERMS


class AstronomicalCalculator:
    """天文算法计算器"""
    
    # 天文常数
    TROPICAL_YEAR = 365.24219    # 回归年长度（天）
    EPOCH_2000 = 2451545.0       # J2000.0历元（儒略日数）
    DEG_TO_RAD = math.pi / 180   # 度转弧度
    RAD_TO_DEG = 180 / math.pi   # 弧度转度
    
    # 节气对应的太阳黄经（度）
    SOLAR_TERMS_LONGITUDE = {
        "立春": 315, "雨水": 330, "惊蛰": 345, "春分": 0, "清明": 15, "谷雨": 30,
        "立夏": 45, "小满": 60, "芒种": 75, "夏至": 90, "小暑": 105, "大暑": 120,
        "立秋": 135, "处暑": 150, "白露": 165, "秋分": 180, "寒露": 195, "霜降": 210,
        "立冬": 225, "小雪": 240, "大雪": 255, "冬至": 270, "小寒": 285, "大寒": 300
    }
    
    def __init__(self):
        self.cache_enabled = True
    
    def julian_day(self, dt: datetime) -> float:
        """
        计算儒略日数
        
        Args:
            dt: 时间（统一使用naive datetime）
            
        Returns:
            float: 儒略日数
        """
        # 确保使用naive datetime
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
            
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        # 加上时间部分
        jd = jdn + (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
        
        return jd
    
    @lru_cache(maxsize=100)
    def calculate_solar_longitude(self, julian_day: float) -> float:
        """
        计算太阳黄经
        
        Args:
            julian_day: 儒略日数
            
        Returns:
            float: 太阳黄经（度）
        """
        # 计算自J2000.0以来的天数
        T = (julian_day - self.EPOCH_2000) / 36525.0
        
        # 平太阳平近点角（度）
        M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
        M = M % 360
        
        # 平黄经（度）
        L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
        L0 = L0 % 360
        
        # 近点角修正
        C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M * self.DEG_TO_RAD) + \
            (0.019993 - 0.000101 * T) * math.sin(2 * M * self.DEG_TO_RAD) + \
            0.000289 * math.sin(3 * M * self.DEG_TO_RAD)
        
        # 真黄经
        L = L0 + C
        L = L % 360
        
        return L
    
    def find_solar_term_time(self, year: int, term_name: str) -> datetime:
        """
        精确计算节气时间
        
        Args:
            year: 年份
            term_name: 节气名称
            
        Returns:
            datetime: 精确的节气时间（naive datetime）
        """
        target_longitude = self.SOLAR_TERMS_LONGITUDE[term_name]
        
        # 估算初始时间（基于平均值）
        term_index = SOLAR_TERMS.index(term_name)
        approx_day = 6 + (term_index % 2) * 15 + (term_index // 2) * 30
        if term_index >= 20:  # 小寒、大寒在次年1月
            year += 1
            approx_day = 6 + (term_index - 20) * 15
        
        month = (term_index // 2 + 1) % 12
        if month == 0:
            month = 12
        
        # 初始估算
        initial_dt = datetime(year, month, min(approx_day, 28))
        
        # 使用牛顿迭代法精确求解
        dt = initial_dt
        for _ in range(10):  # 最多迭代10次
            jd = self.julian_day(dt)
            current_longitude = self.calculate_solar_longitude(jd)
            
            # 计算角度差
            diff = target_longitude - current_longitude
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            
            # 收敛判断
            if abs(diff) < 0.0001:  # 精度约0.36秒
                break
            
            # 太阳平均每天移动约0.9856度
            day_correction = diff / 0.9856
            dt = dt + timedelta(days=day_correction)
        
        return dt
    
    @lru_cache(maxsize=50)
    def calculate_all_solar_terms(self, year: int) -> Dict[str, datetime]:
        """
        计算一年所有节气的精确时间
        
        Args:
            year: 年份
            
        Returns:
            Dict[str, datetime]: 节气名称到时间的映射（所有datetime都是naive）
        """
        solar_terms = {}
        
        for term_name in SOLAR_TERMS:
            term_time = self.find_solar_term_time(year, term_name)
            solar_terms[term_name] = term_time
        
        return solar_terms
    
    def get_current_solar_term(self, dt: datetime) -> Tuple[str, int, datetime]:
        """
        获取当前时间的节气信息
        
        Args:
            dt: 当前时间（naive datetime）
            
        Returns:
            Tuple[str, int, datetime]: (节气名称, 索引, 精确节气时间)
        """
        # 确保使用naive datetime
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
            
        year = dt.year
        
        # 获取当年和前一年的节气
        current_year_terms = self.calculate_all_solar_terms(year)
        prev_year_terms = self.calculate_all_solar_terms(year - 1)
        
        # 合并所有相关节气
        all_terms = []
        
        # 添加前一年的小寒、大寒（可能在当年1月）
        for term_name in ["小寒", "大寒"]:
            term_time = prev_year_terms[term_name]
            if term_time.year == year:
                all_terms.append((term_name, SOLAR_TERMS.index(term_name), term_time))
        
        # 添加当年所有节气
        for term_name in SOLAR_TERMS:
            term_time = current_year_terms[term_name]
            all_terms.append((term_name, SOLAR_TERMS.index(term_name), term_time))
        
        # 按时间排序
        all_terms.sort(key=lambda x: x[2])
        
        # 找到当前时间对应的节气
        current_term = None
        for i, (term_name, term_index, term_time) in enumerate(all_terms):
            if dt >= term_time:
                current_term = (term_name, term_index, term_time)
            else:
                break
        
        if current_term is None:
            # 如果没有找到，说明在第一个节气之前，取前一年的大寒
            prev_dahan = prev_year_terms["大寒"]
            return ("大寒", SOLAR_TERMS.index("大寒"), prev_dahan)
        
        return current_term
    
    def calculate_equation_of_time(self, julian_day: float) -> float:
        """
        计算时差方程
        
        Args:
            julian_day: 儒略日数
            
        Returns:
            float: 时差（分钟）
        """
        # 计算自J2000.0以来的天数
        n = julian_day - self.EPOCH_2000
        
        # 平黄经（度）
        L = (280.4665 + 0.98564736 * n) % 360
        
        # 平近点角（度）
        g = (357.5291 + 0.98560028 * n) % 360
        
        # 转换为弧度
        L_rad = L * self.DEG_TO_RAD
        g_rad = g * self.DEG_TO_RAD
        
        # 黄赤交角（度，转弧度）
        epsilon = 23.439 * self.DEG_TO_RAD
        
        # 时差方程计算（分钟）
        # 这是一个简化但精确的时差方程公式
        y = math.tan(epsilon / 2) ** 2
        
        E = y * math.sin(2 * L_rad) - 2 * 0.0167 * math.sin(g_rad) + \
            4 * 0.0167 * y * math.sin(g_rad) * math.cos(2 * L_rad) - \
            0.5 * y * y * math.sin(4 * L_rad) - \
            1.25 * (0.0167 ** 2) * math.sin(2 * g_rad)
        
        # 转换为分钟（1弧度 = 229.18分钟）
        E_minutes = E * 229.18
        
        return E_minutes
    
    def calculate_true_solar_time(self, dt: datetime, longitude: float = 116.4667) -> datetime:
        """
        计算真太阳时
        
        Args:
            dt: 标准时间（naive datetime）
            longitude: 地理经度（东经为正）
            
        Returns:
            datetime: 真太阳时（naive datetime）
        """
        # 确保使用naive datetime
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
            
        # 计算儒略日数
        jd = self.julian_day(dt)
        
        # 计算时差方程
        equation_time = self.calculate_equation_of_time(jd)
        
        # 计算经度时差（分钟）
        longitude_correction = (longitude - 120) * 4  # 中国标准时区为东8区，中央经线120°E
        
        # 总时差修正
        total_correction = equation_time + longitude_correction
        
        # 返回修正后的真太阳时
        true_solar_time = dt + timedelta(minutes=total_correction)
        
        return true_solar_time


# 创建全局实例
astro_calculator = AstronomicalCalculator()

# 公开的便捷函数
def get_current_solar_term(dt: datetime) -> Tuple[str, int, datetime]:
    """获取当前节气信息"""
    return astro_calculator.get_current_solar_term(dt)

def get_true_solar_time(dt: datetime, longitude: float = 116.4667) -> datetime:
    """计算真太阳时"""
    return astro_calculator.calculate_true_solar_time(dt, longitude)

def calculate_solar_terms(year: int) -> Dict[str, datetime]:
    """计算一年所有节气"""
    return astro_calculator.calculate_all_solar_terms(year) 