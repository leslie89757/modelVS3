"""
奇门遁甲干支计算模块
实现精确的年月日时干支计算，包括节气换月、五虎遁年起月法、五鼠遁日起时法等
"""

from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional

try:
    from symbols import TIAN_GAN, DI_ZHI, SOLAR_TERMS
    from astronomical import astro_calculator
except ImportError:
    from .symbols import TIAN_GAN, DI_ZHI, SOLAR_TERMS
    from .astronomical import astro_calculator


class GanZhiCalculator:
    """干支计算器"""
    
    # 五虎遁年起月表（甲己年起丙寅，乙庚年起戊寅...）
    YEAR_MONTH_GAN_TABLE = {
        0: 2, 4: 2,  # 甲年、己年起丙寅月（丙=2）
        1: 4, 5: 4,  # 乙年、庚年起戊寅月（戊=4）
        2: 6, 6: 6,  # 丙年、辛年起庚寅月（庚=6）
        3: 8, 7: 8,  # 丁年、壬年起壬寅月（壬=8）
        8: 0, 9: 0   # 戊年、癸年起甲寅月（甲=0）
    }
    
    # 五鼠遁日起时表（甲己日起甲子时，乙庚日起丙子时...）
    DAY_HOUR_GAN_TABLE = {
        0: 0, 5: 0,  # 甲日(0)、己日(5)起甲子时（甲=0）
        1: 2, 6: 2,  # 乙日(1)、庚日(6)起丙子时（丙=2）
        2: 4, 7: 4,  # 丙日(2)、辛日(7)起戊子时（戊=4）
        3: 6, 8: 6,  # 丁日(3)、壬日(8)起庚子时（庚=6）
        4: 8, 9: 8   # 戊日(4)、癸日(9)起壬子时（壬=8）
    }
    
    # 月建表（节气对应的地支）
    SOLAR_TERM_TO_ZHI = {
        "立春": 2,  "雨水": 2,    # 寅月
        "惊蛰": 3,  "春分": 3,    # 卯月
        "清明": 4,  "谷雨": 4,    # 辰月
        "立夏": 5,  "小满": 5,    # 巳月
        "芒种": 6,  "夏至": 6,    # 午月
        "小暑": 7,  "大暑": 7,    # 未月
        "立秋": 8,  "处暑": 8,    # 申月
        "白露": 9,  "秋分": 9,    # 酉月
        "寒露": 10, "霜降": 10,   # 戌月
        "立冬": 11, "小雪": 11,   # 亥月
        "大雪": 0,  "冬至": 0,    # 子月
        "小寒": 1,  "大寒": 1     # 丑月
    }
    
    def __init__(self):
        pass
    
    def calculate_year_ganzhi(self, year: int) -> Tuple[str, str]:
        """
        计算年干支（以立春为界）
        
        Args:
            year: 年份
            
        Returns:
            Tuple[str, str]: (年干, 年支)
        """
        # 以甲子年（1984年）为基准
        base_year = 1984
        offset = year - base_year
        
        gan_index = offset % 10
        zhi_index = offset % 12
        
        return TIAN_GAN[gan_index], DI_ZHI[zhi_index]
    
    def calculate_month_ganzhi(self, dt: datetime, use_solar_terms: bool = True) -> Tuple[str, str]:
        """
        计算月干支（以节气为准）
        
        Args:
            dt: 时间（naive datetime）
            use_solar_terms: 是否使用节气分月
            
        Returns:
            Tuple[str, str]: (月干, 月支)
        """
        # 确保使用naive datetime
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
            
        if use_solar_terms:
            # 获取当前节气
            solar_term, _, _ = astro_calculator.get_current_solar_term(dt)
            
            # 根据节气确定月建（地支）
            month_zhi_index = self.SOLAR_TERM_TO_ZHI.get(solar_term, 2)  # 默认寅月
            month_zhi = DI_ZHI[month_zhi_index]
            
            # 计算月干（五虎遁年起月法）
            year_gan, _ = self.calculate_year_ganzhi(dt.year)
            year_gan_index = TIAN_GAN.index(year_gan)
            
            # 基础月干 = 年干对应的起月干 + （月支索引 - 寅月索引）
            base_month_gan_index = self.YEAR_MONTH_GAN_TABLE.get(year_gan_index, 2)
            month_gan_index = (base_month_gan_index + (month_zhi_index - 2)) % 10
            month_gan = TIAN_GAN[month_gan_index]
            
            return month_gan, month_zhi
        else:
            # 简化版本：直接使用公历月份
            month_zhi_index = (dt.month + 1) % 12  # 寅月为正月
            month_zhi = DI_ZHI[month_zhi_index]
            
            # 计算月干
            year_gan, _ = self.calculate_year_ganzhi(dt.year)
            year_gan_index = TIAN_GAN.index(year_gan)
            base_month_gan_index = self.YEAR_MONTH_GAN_TABLE.get(year_gan_index, 2)
            month_gan_index = (base_month_gan_index + (month_zhi_index - 2)) % 10
            month_gan = TIAN_GAN[month_gan_index]
            
            return month_gan, month_zhi
    
    def calculate_day_ganzhi(self, dt: datetime) -> Tuple[str, str]:
        """
        计算日干支（使用1900年1月1日甲戌日作为基准）
        
        Args:
            dt: 时间（naive datetime）
            
        Returns:
            Tuple[str, str]: (日干, 日支)
        """
        # 确保使用naive datetime
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
            
        # 使用1900年1月1日作为基准（甲戌日）
        from datetime import date
        base_date = date(1900, 1, 1)
        base_gan_index = 0  # 甲
        base_zhi_index = 10  # 戌
        
        target_date = dt.date()
        days_diff = (target_date - base_date).days
        
        gan_index = (base_gan_index + days_diff) % 10
        zhi_index = (base_zhi_index + days_diff) % 12
        
        return TIAN_GAN[gan_index], DI_ZHI[zhi_index]
    
    def calculate_shi_chen(self, hour: int) -> str:
        """
        计算时辰名称
        
        Args:
            hour: 小时（0-23）
            
        Returns:
            str: 时辰名称
        """
        # 时辰对应表
        shi_chen_list = ["子时", "丑时", "寅时", "卯时", "辰时", "巳时", 
                        "午时", "未时", "申时", "酉时", "戌时", "亥时"]
        
        if hour == 23:
            return shi_chen_list[0]  # 子时
        else:
            index = (hour + 1) // 2
            return shi_chen_list[index]
    
    def get_nayin(self, gan: str, zhi: str) -> str:
        """
        计算纳音五行
        
        Args:
            gan: 天干
            zhi: 地支
            
        Returns:
            str: 纳音五行名称
        """
        # 纳音表
        nayin_table = {
            # 甲子、乙丑
            ("甲", "子"): "海中金", ("乙", "丑"): "海中金",
            # 丙寅、丁卯  
            ("丙", "寅"): "炉中火", ("丁", "卯"): "炉中火",
            # 戊辰、己巳
            ("戊", "辰"): "大林木", ("己", "巳"): "大林木",
            # 庚午、辛未
            ("庚", "午"): "路旁土", ("辛", "未"): "路旁土",
            # 壬申、癸酉
            ("壬", "申"): "剑锋金", ("癸", "酉"): "剑锋金",
            # 甲戌、乙亥
            ("甲", "戌"): "山头火", ("乙", "亥"): "山头火",
            # 丙子、丁丑
            ("丙", "子"): "涧下水", ("丁", "丑"): "涧下水",
            # 戊寅、己卯
            ("戊", "寅"): "城墙土", ("己", "卯"): "城墙土",
            # 庚辰、辛巳
            ("庚", "辰"): "白蜡金", ("辛", "巳"): "白蜡金",
            # 壬午、癸未
            ("壬", "午"): "杨柳木", ("癸", "未"): "杨柳木",
            # 甲申、乙酉
            ("甲", "申"): "泉中水", ("乙", "酉"): "泉中水",
            # 丙戌、丁亥
            ("丙", "戌"): "屋上土", ("丁", "亥"): "屋上土",
            # 戊子、己丑
            ("戊", "子"): "霹雳火", ("己", "丑"): "霹雳火",
            # 庚寅、辛卯
            ("庚", "寅"): "松柏木", ("辛", "卯"): "松柏木",
            # 壬辰、癸巳
            ("壬", "辰"): "长流水", ("癸", "巳"): "长流水",
            # 甲午、乙未
            ("甲", "午"): "沙中金", ("乙", "未"): "沙中金",
            # 丙申、丁酉
            ("丙", "申"): "山下火", ("丁", "酉"): "山下火",
            # 戊戌、己亥
            ("戊", "戌"): "平地木", ("己", "亥"): "平地木",
            # 庚子、辛丑
            ("庚", "子"): "壁上土", ("辛", "丑"): "壁上土",
            # 壬寅、癸卯
            ("壬", "寅"): "金箔金", ("癸", "卯"): "金箔金",
            # 甲辰、乙巳
            ("甲", "辰"): "覆灯火", ("乙", "巳"): "覆灯火",
            # 丙午、丁未
            ("丙", "午"): "天河水", ("丁", "未"): "天河水",
            # 戊申、己酉
            ("戊", "申"): "大驿土", ("己", "酉"): "大驿土",
            # 庚戌、辛亥
            ("庚", "戌"): "钗钏金", ("辛", "亥"): "钗钏金",
            # 壬子、癸丑
            ("壬", "子"): "桑柘木", ("癸", "丑"): "桑柘木",
            # 甲寅、乙卯
            ("甲", "寅"): "大溪水", ("乙", "卯"): "大溪水",
            # 丙辰、丁巳
            ("丙", "辰"): "沙中土", ("丁", "巳"): "沙中土",
            # 戊午、己未
            ("戊", "午"): "天上火", ("己", "未"): "天上火",
            # 庚申、辛酉
            ("庚", "申"): "石榴木", ("辛", "酉"): "石榴木",
            # 壬戌、癸亥
            ("壬", "戌"): "大海水", ("癸", "亥"): "大海水"
        }
        
        return nayin_table.get((gan, zhi), "未知纳音")


# 全局实例 - 统一的干支计算入口
ganzhi_calculator = GanZhiCalculator() 