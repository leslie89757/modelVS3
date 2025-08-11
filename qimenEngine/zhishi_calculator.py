"""
奇门遁甲值使计算模块
实现正确的值使计算逻辑
"""

from typing import Dict, Tuple, Optional
from symbols import BA_MEN, DI_ZHI

class ZhiShiCalculator:
    """值使计算器"""
    
    # 八门与十二地支的对应关系（传统奇门遁甲规则）
    # 基于时辰地支确定值使门
    MEN_DIZHI_MAP = {
        # 子时、午时对应
        "子": "休门",  # 子时 - 休门
        "午": "景门",  # 午时 - 景门
        
        # 丑时、未时对应  
        "丑": "死门",  # 丑时 - 死门
        "未": "开门",  # 未时 - 开门
        
        # 寅时、申时对应
        "寅": "伤门",  # 寅时 - 伤门
        "申": "惊门",  # 申时 - 惊门
        
        # 卯时、酉时对应
        "卯": "杜门",  # 卯时 - 杜门
        "酉": "生门",  # 酉时 - 生门
        
        # 辰时、戌时对应
        "辰": "景门",  # 辰时 - 景门  
        "戌": "休门",  # 戌时 - 休门
        
        # 巳时、亥时对应
        "巳": "生门",  # 巳时 - 生门
        "亥": "伤门",  # 亥时 - 伤门
    }
    
    def __init__(self):
        """初始化值使计算器"""
        pass
    
    def calculate_zhishi_by_time(self, hour_zhi: str) -> str:
        """
        根据时辰地支计算值使门
        
        Args:
            hour_zhi: 时辰地支
            
        Returns:
            str: 值使门名称
        """
        return self.MEN_DIZHI_MAP.get(hour_zhi, "未知")
    
    def find_zhishi_gong(self, nine_palace: Dict, zhishi_men: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        在九宫盘中找到值使门所在的宫位
        
        Args:
            nine_palace: 九宫盘数据
            zhishi_men: 值使门名称
            
        Returns:
            Tuple[Optional[str], Optional[Dict]]: (宫位编号, 宫位信息)
        """
        palaces = nine_palace.get("palaces", {})
        
        for gong_str, palace_info in palaces.items():
            if palace_info.get("men") == zhishi_men:
                return gong_str, palace_info
        
        return None, None
    
    def get_zhishi_analysis(self, hour_zhi: str, zhishi_men: str, 
                          zhishi_gong: Optional[str], zhishi_palace: Optional[Dict]) -> Dict[str, str]:
        """
        获取值使分析信息
        
        Args:
            hour_zhi: 时辰地支
            zhishi_men: 值使门
            zhishi_gong: 值使宫位
            zhishi_palace: 值使宫位信息
            
        Returns:
            Dict[str, str]: 值使分析
        """
        analysis = {
            "时辰地支": hour_zhi,
            "值使门": zhishi_men,
            "值使宫位": zhishi_gong or "未找到",
        }
        
        if zhishi_palace:
            analysis["宫位信息"] = f"{zhishi_palace.get('gong_name', '')}({zhishi_palace.get('position', '')})"
            analysis["天干"] = zhishi_palace.get('gan', '')
            analysis["九星"] = zhishi_palace.get('xing', '')
            analysis["九神"] = zhishi_palace.get('shen', '')
        
        # 添加值使门的意义解释
        men_meanings = {
            "休门": "休养生息，宜静不宜动，利于休息调养",
            "死门": "死气沉沉，不利开始，但利于结束旧事",
            "伤门": "刑伤损害，不利健康，但利于竞争争斗",
            "杜门": "闭塞不通，宜隐藏秘密，不利公开事务",
            "中门": "中宫之门，五行属土，性情稳重",
            "开门": "开启新机，大吉之门，利于开创事业",
            "惊门": "惊慌失措，多有变化，利于诉讼官司",
            "生门": "生机勃勃，大吉之门，利于求财谋事",
            "景门": "文书考试，利于学习文化艺术"
        }
        
        analysis["门意"] = men_meanings.get(zhishi_men, "门意未明")
        
        return analysis

# 创建全局值使计算器实例
zhishi_calculator = ZhiShiCalculator() 