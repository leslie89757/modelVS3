"""
奇门遁甲插件式断事分析模块
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Protocol
from dataclasses import dataclass
import json

try:
    from qimen_calendar import CalendarInfo
    from palace import NinePalace, PalaceInfo
    from symbols import (
        TIAN_GAN_WU_XING, DI_ZHI_WU_XING, BA_MEN_WU_XING, JIU_XING_WU_XING,
        GONG_WU_XING, WU_XING
    )
except ImportError:
    from .qimen_calendar import CalendarInfo
    from .palace import NinePalace, PalaceInfo
    from .symbols import (
        TIAN_GAN_WU_XING, DI_ZHI_WU_XING, BA_MEN_WU_XING, JIU_XING_WU_XING,
        GONG_WU_XING, WU_XING
    )


class RulePlugin(Protocol):
    """插件协议定义"""
    
    def apply(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """
        应用插件规则
        
        Args:
            nine_palace: 九宫盘
            cal: 历法信息
            
        Returns:
            List[str]: 分析结果列表
        """
        ...


@dataclass
class PluginResult:
    """插件结果"""
    plugin_name: str
    messages: List[str]
    score: float = 0.0
    confidence: float = 0.0
    

class WangShuaiPlugin:
    """旺衰分析插件"""
    
    def __init__(self):
        self.name = "旺衰分析"
        
    def apply(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析旺衰"""
        messages = []
        
        # 获取用神宫位
        yong_shen_gong = self._get_yong_shen_gong(nine_palace, cal)
        if yong_shen_gong:
            wang_shuai = self._analyze_wang_shuai(yong_shen_gong)
            messages.append(f"用神在{yong_shen_gong['gong_name']}，{wang_shuai}")
        
        # 分析各宫旺衰
        for gong_str, palace_info in nine_palace["palaces"].items():
            wang_shuai = self._get_palace_wang_shuai(palace_info, cal)
            if wang_shuai:
                messages.append(f"{palace_info['gong_name']}{wang_shuai}")
        
        return messages
    
    def _get_yong_shen_gong(self, nine_palace: NinePalace, cal: CalendarInfo) -> Optional[PalaceInfo]:
        """获取用神宫位"""
        # 简化实现：以日干所在宫为用神
        day_gan = cal["day_gan"]
        
        for palace_info in nine_palace["palaces"].values():
            if palace_info["gan"] == day_gan:
                return palace_info
        
        return None
    
    def _analyze_wang_shuai(self, palace_info: PalaceInfo) -> str:
        """分析宫位旺衰"""
        # 根据五行相生相克判断旺衰
        gan_wu_xing = TIAN_GAN_WU_XING.get(palace_info["gan"], "")
        gong_wu_xing = palace_info["wu_xing"]
        
        if self._is_sheng(gong_wu_xing, gan_wu_xing):
            return "得地而旺"
        elif self._is_ke(gong_wu_xing, gan_wu_xing):
            return "受克而衰"
        else:
            return "平和"
    
    def _get_palace_wang_shuai(self, palace_info: PalaceInfo, cal: CalendarInfo) -> str:
        """获取宫位旺衰"""
        # 根据时令判断旺衰
        season_wang_shuai = self._get_season_wang_shuai(palace_info["wu_xing"], cal["month"])
        return f"：{season_wang_shuai}"
    
    def _get_season_wang_shuai(self, wu_xing: str, month: int) -> str:
        """根据季节判断五行旺衰"""
        if month in [3, 4, 5]:  # 春季
            if wu_xing == "木":
                return "旺"
            elif wu_xing == "火":
                return "相"
            elif wu_xing == "土":
                return "死"
            elif wu_xing == "金":
                return "囚"
            elif wu_xing == "水":
                return "休"
        elif month in [6, 7, 8]:  # 夏季
            if wu_xing == "火":
                return "旺"
            elif wu_xing == "土":
                return "相"
            elif wu_xing == "金":
                return "死"
            elif wu_xing == "水":
                return "囚"
            elif wu_xing == "木":
                return "休"
        elif month in [9, 10, 11]:  # 秋季
            if wu_xing == "金":
                return "旺"
            elif wu_xing == "水":
                return "相"
            elif wu_xing == "木":
                return "死"
            elif wu_xing == "火":
                return "囚"
            elif wu_xing == "土":
                return "休"
        else:  # 冬季
            if wu_xing == "水":
                return "旺"
            elif wu_xing == "木":
                return "相"
            elif wu_xing == "火":
                return "死"
            elif wu_xing == "土":
                return "囚"
            elif wu_xing == "金":
                return "休"
        
        return "平"
    
    def _is_sheng(self, sheng_wu_xing: str, bei_sheng_wu_xing: str) -> bool:
        """判断是否相生"""
        sheng_relations = {
            "木": "火", "火": "土", "土": "金", "金": "水", "水": "木"
        }
        return sheng_relations.get(sheng_wu_xing) == bei_sheng_wu_xing
    
    def _is_ke(self, ke_wu_xing: str, bei_ke_wu_xing: str) -> bool:
        """判断是否相克"""
        ke_relations = {
            "木": "土", "土": "水", "水": "火", "火": "金", "金": "木"
        }
        return ke_relations.get(ke_wu_xing) == bei_ke_wu_xing


class GeJuPlugin:
    """格局分析插件"""
    
    def __init__(self):
        self.name = "格局分析"
        
    def apply(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析格局"""
        messages = []
        
        # 分析吉格
        ji_ge = self._analyze_ji_ge(nine_palace, cal)
        messages.extend(ji_ge)
        
        # 分析凶格
        xiong_ge = self._analyze_xiong_ge(nine_palace, cal)
        messages.extend(xiong_ge)
        
        # 分析特殊格局
        te_shu_ge = self._analyze_te_shu_ge(nine_palace, cal)
        messages.extend(te_shu_ge)
        
        return messages
    
    def _analyze_ji_ge(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析吉格"""
        messages = []
        
        # 检查青龙返首
        if self._check_qing_long_fan_shou(nine_palace):
            messages.append("青龙返首：大吉之格，事业有成")
        
        # 检查飞鸟跌穴
        if self._check_fei_niao_die_xue(nine_palace):
            messages.append("飞鸟跌穴：利于求财，投资获利")
        
        # 检查三奇得使
        if self._check_san_qi_de_shi(nine_palace):
            messages.append("三奇得使：贵人相助，事半功倍")
        
        return messages
    
    def _analyze_xiong_ge(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析凶格"""
        messages = []
        
        # 检查白虎猖狂
        if self._check_bai_hu_chang_kuang(nine_palace):
            messages.append("白虎猖狂：易有血光之灾，需谨慎")
        
        # 检查腾蛇夭矫
        if self._check_teng_she_yao_jiao(nine_palace):
            messages.append("腾蛇夭矫：多有虚惊，事多反复")
        
        # 检查门迫
        if self._check_men_po(nine_palace):
            messages.append("门迫：行事受阻，需择时而动")
        
        return messages
    
    def _analyze_te_shu_ge(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析特殊格局"""
        messages = []
        
        # 检查伏吟
        if self._check_fu_yin(nine_palace):
            messages.append("伏吟：事情拖延，进展缓慢")
        
        # 检查反吟
        if self._check_fan_yin(nine_palace):
            messages.append("反吟：事情反复，变化较大")
        
        return messages
    
    def _check_qing_long_fan_shou(self, nine_palace: NinePalace) -> bool:
        """检查青龙返首格"""
        # 简化实现：检查乙奇在一宫
        return nine_palace["palaces"]["1"]["gan"] == "乙"
    
    def _check_fei_niao_die_xue(self, nine_palace: NinePalace) -> bool:
        """检查飞鸟跌穴格"""
        # 简化实现：检查丙奇在九宫
        return nine_palace["palaces"]["9"]["gan"] == "丙"
    
    def _check_san_qi_de_shi(self, nine_palace: NinePalace) -> bool:
        """检查三奇得使格"""
        # 简化实现：检查三奇（乙丙丁）是否在开门、休门、生门
        for palace_info in nine_palace["palaces"].values():
            if palace_info["gan"] in ["乙", "丙", "丁"]:
                if palace_info["men"] in ["开门", "休门", "生门"]:
                    return True
        return False
    
    def _check_bai_hu_chang_kuang(self, nine_palace: NinePalace) -> bool:
        """检查白虎猖狂格"""
        # 简化实现：检查白虎在震宫
        return nine_palace["palaces"]["3"]["shen"] == "白虎"
    
    def _check_teng_she_yao_jiao(self, nine_palace: NinePalace) -> bool:
        """检查腾蛇夭矫格"""
        # 简化实现：检查腾蛇在离宫
        return nine_palace["palaces"]["9"]["shen"] == "腾蛇"
    
    def _check_men_po(self, nine_palace: NinePalace) -> bool:
        """检查门迫格"""
        # 简化实现：检查门宫是否相冲
        for palace_info in nine_palace["palaces"].values():
            if palace_info["men"] == "死门" and palace_info["bagua"] == "坎":
                return True
        return False
    
    def _check_fu_yin(self, nine_palace: NinePalace) -> bool:
        """检查伏吟格"""
        # 简化实现：检查天盘地盘是否相同
        for palace_info in nine_palace["palaces"].values():
            if palace_info["xing"] == "天禽" and palace_info["gong_num"] == 5:
                return True
        return False
    
    def _check_fan_yin(self, nine_palace: NinePalace) -> bool:
        """检查反吟格"""
        # 简化实现：检查对冲宫位
        dui_chong_pairs = [(1, 9), (2, 8), (3, 7), (4, 6)]
        for pair in dui_chong_pairs:
            palace1 = nine_palace["palaces"][str(pair[0])]
            palace2 = nine_palace["palaces"][str(pair[1])]
            if palace1["xing"] == palace2["xing"]:
                return True
        return False


class YingQiPlugin:
    """应期分析插件"""
    
    def __init__(self):
        self.name = "应期分析"
        
    def apply(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析应期"""
        messages = []
        
        # 分析时间应期
        time_ying_qi = self._analyze_time_ying_qi(nine_palace, cal)
        messages.extend(time_ying_qi)
        
        # 分析方位应期
        direction_ying_qi = self._analyze_direction_ying_qi(nine_palace, cal)
        messages.extend(direction_ying_qi)
        
        return messages
    
    def _analyze_time_ying_qi(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析时间应期"""
        messages = []
        
        # 根据用神宫位判断应期
        yong_shen_gong = self._get_yong_shen_gong(nine_palace, cal)
        if yong_shen_gong:
            ying_qi_time = self._calculate_ying_qi_time(yong_shen_gong, cal)
            messages.append(f"应期时间：{ying_qi_time}")
        
        return messages
    
    def _analyze_direction_ying_qi(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """分析方位应期"""
        messages = []
        
        # 分析有利方位
        favorable_directions = self._get_favorable_directions(nine_palace, cal)
        if favorable_directions:
            messages.append(f"有利方位：{', '.join(favorable_directions)}")
        
        return messages
    
    def _get_yong_shen_gong(self, nine_palace: NinePalace, cal: CalendarInfo) -> Optional[PalaceInfo]:
        """获取用神宫位"""
        day_gan = cal["day_gan"]
        for palace_info in nine_palace["palaces"].values():
            if palace_info["gan"] == day_gan:
                return palace_info
        return None
    
    def _calculate_ying_qi_time(self, palace_info: PalaceInfo, cal: CalendarInfo) -> str:
        """计算应期时间"""
        # 简化实现：根据宫位数字推算
        gong_num = palace_info["gong_num"]
        
        if gong_num <= 3:
            return "近期（1-3天内）"
        elif gong_num <= 6:
            return "中期（3-7天内）"
        else:
            return "远期（7-15天内）"
    
    def _get_favorable_directions(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """获取有利方位"""
        favorable_directions = []
        
        # 找出开门、生门、休门的方位
        for palace_info in nine_palace["palaces"].values():
            if palace_info["men"] in ["开门", "生门", "休门"]:
                favorable_directions.append(palace_info["position"])
        
        return favorable_directions


class ZhiFuPlugin:
    """值符专项分析插件"""
    
    def __init__(self):
        self.name = "值符分析"
        
    def apply(self, nine_palace: NinePalace, cal: CalendarInfo) -> List[str]:
        """
        专门分析值符的各种特性
        
        Args:
            nine_palace: 九宫盘
            cal: 历法信息
            
        Returns:
            List[str]: 值符分析结果
        """
        messages = []
        
        # 查找值符位置
        zhi_fu_palace = self._find_zhi_fu(nine_palace)
        if not zhi_fu_palace:
            messages.append("值符位置不明，分析受限")
            return messages
        
        # 基础位置分析
        location_analysis = self._analyze_zhi_fu_location(zhi_fu_palace)
        messages.append(f"值符位置：{location_analysis}")
        
        # 时空匹配分析
        time_match = self._analyze_time_space_match(zhi_fu_palace, cal)
        messages.append(f"时空匹配：{time_match}")
        
        # 格局影响分析
        pattern_influence = self._analyze_pattern_influence(nine_palace, zhi_fu_palace)
        messages.extend(pattern_influence)
        
        # 行运建议
        action_advice = self._get_action_advice(zhi_fu_palace, cal)
        messages.append(f"行运建议：{action_advice}")
        
        # 应期预测
        ying_qi = self._predict_ying_qi(zhi_fu_palace, cal)
        messages.append(f"应期预测：{ying_qi}")
        
        return messages
    
    def _find_zhi_fu(self, nine_palace: NinePalace) -> Optional[PalaceInfo]:
        """查找值符位置"""
        for palace_info in nine_palace["palaces"].values():
            if palace_info["shen"] == "直符":
                return palace_info
        return None
    
    def _analyze_zhi_fu_location(self, zhi_fu_palace: PalaceInfo) -> str:
        """分析值符位置的意义"""
        gong_num = zhi_fu_palace["gong_num"]
        position = zhi_fu_palace["position"]
        
        location_meanings = {
            1: f"坎宫{position}，智慧内敛，利于谋划决策",
            2: f"坤宫{position}，厚德包容，利于合作发展",
            3: f"震宫{position}，生机勃发，利于开创新局",
            4: f"巽宫{position}，进退有序，利于渐进成长",
            5: f"中宫{position}，统领八方，权威居中调度",
            6: f"乾宫{position}，刚健决断，利于领导管理",
            7: f"兑宫{position}，沟通协调，利于交际合作",
            8: f"艮宫{position}，稳重守成，利于积累发展",
            9: f"离宫{position}，光明显达，利于展示宣传"
        }
        
        return location_meanings.get(gong_num, f"{zhi_fu_palace['gong_name']}{position}，位置特殊")
    
    def _analyze_time_space_match(self, zhi_fu_palace: PalaceInfo, cal: CalendarInfo) -> str:
        """分析时空匹配度"""
        # 检查值符天干戊土与当前时空的匹配程度
        month = cal["month"]
        hour_gan = cal["hour_gan"]
        gong_wu_xing = zhi_fu_palace["wu_xing"]
        
        # 戊土在不同季节的状态
        seasonal_status = self._get_seasonal_status(month)
        
        # 时干与值符的关系
        hour_relation = self._analyze_hour_gan_relation(hour_gan)
        
        # 宫位五行与戊土的关系
        gong_relation = self._analyze_gong_relation(gong_wu_xing)
        
        # 综合匹配度
        if "旺" in seasonal_status and "生助" in gong_relation:
            return f"时空俱佳：{seasonal_status}，{gong_relation}，{hour_relation}"
        elif "衰" in seasonal_status and "受制" in gong_relation:
            return f"时空不利：{seasonal_status}，{gong_relation}，{hour_relation}"
        else:
            return f"时空平和：{seasonal_status}，{gong_relation}，{hour_relation}"
    
    def _get_seasonal_status(self, month: int) -> str:
        """获取戊土的季节状态"""
        if month in [6, 7, 8]:  # 夏季
            return "夏季火旺生土，戊土得令而旺"
        elif month in [3, 6, 9, 12]:  # 四季月
            return "四季月土旺，戊土当令而强"
        elif month in [9, 10, 11]:  # 秋季
            return "秋季金旺泄土，戊土有泄但稳"
        elif month in [12, 1, 2]:  # 冬季
            return "冬季水旺克土，戊土受制较弱"
        else:  # 春季
            return "春季木旺克土，戊土受克略衰"
    
    def _analyze_hour_gan_relation(self, hour_gan: str) -> str:
        """分析时干与值符的关系"""
        # 戊土与各天干的关系
        gan_relations = {
            "甲": "甲木克戊土，时干制约值符",
            "乙": "乙木克戊土，时干约束值符", 
            "丙": "丙火生戊土，时干生助值符",
            "丁": "丁火生戊土，时干滋养值符",
            "戊": "戊土比和，时干同助值符",
            "己": "己土比和，时干呼应值符",
            "庚": "戊土生庚金，值符生助时干",
            "辛": "戊土生辛金，值符扶持时干",
            "壬": "戊土克壬水，值符制约时干",
            "癸": "戊土克癸水，值符控制时干"
        }
        return gan_relations.get(hour_gan, "时干关系不明")
    
    def _analyze_gong_relation(self, gong_wu_xing: str) -> str:
        """分析宫位五行与戊土的关系"""
        relations = {
            "土": "戊土居土宫，比和得地而强",
            "火": "戊土居火宫，火生土而得助",
            "金": "戊土居金宫，土生金而有泄",
            "水": "戊土居水宫，土克水而耗力",
            "木": "戊土居木宫，木克土而受制"
        }
        return relations.get(gong_wu_xing, "宫位关系待查")
    
    def _analyze_pattern_influence(self, nine_palace: NinePalace, zhi_fu_palace: PalaceInfo) -> List[str]:
        """分析值符在格局中的影响"""
        influences = []
        
        # 检查值符与三奇的配合
        san_qi_combination = self._check_san_qi_combination(nine_palace, zhi_fu_palace)
        if san_qi_combination:
            influences.extend(san_qi_combination)
        
        # 检查值符与吉门的配合
        ji_men_combination = self._check_ji_men_combination(nine_palace, zhi_fu_palace)
        if ji_men_combination:
            influences.extend(ji_men_combination)
        
        # 检查值符与九星的配合
        jiu_xing_combination = self._check_jiu_xing_combination(zhi_fu_palace)
        if jiu_xing_combination:
            influences.append(jiu_xing_combination)
        
        return influences
    
    def _check_san_qi_combination(self, nine_palace: NinePalace, zhi_fu_palace: PalaceInfo) -> List[str]:
        """检查值符与三奇的配合"""
        combinations = []
        san_qi = ["乙", "丙", "丁"]
        zhi_fu_gong = zhi_fu_palace["gong_num"]
        
        for gong_str, palace_info in nine_palace["palaces"].items():
            if palace_info["gan"] in san_qi:
                if palace_info["gong_num"] == zhi_fu_gong:
                    combinations.append(f"值符与{palace_info['gan']}奇同宫：权威与才华并显，主贵")
                elif abs(palace_info["gong_num"] - zhi_fu_gong) <= 1:
                    combinations.append(f"值符与{palace_info['gan']}奇相邻：权威呼应才华，吉祥")
        
        return combinations
    
    def _check_ji_men_combination(self, nine_palace: NinePalace, zhi_fu_palace: PalaceInfo) -> List[str]:
        """检查值符与吉门的配合"""
        combinations = []
        ji_men = ["开门", "休门", "生门"]
        zhi_fu_gong = zhi_fu_palace["gong_num"]
        
        for palace_info in nine_palace["palaces"].values():
            if palace_info["men"] in ji_men and palace_info["gong_num"] != zhi_fu_gong:
                if abs(palace_info["gong_num"] - zhi_fu_gong) <= 1:
                    combinations.append(f"值符临近{palace_info['men']}：权威配吉门，利于行动")
        
        return combinations
    
    def _check_jiu_xing_combination(self, zhi_fu_palace: PalaceInfo) -> str:
        """检查值符与九星的配合"""
        # 值符固定配天蓬星
        xing = zhi_fu_palace["xing"]
        if xing == "天蓬":
            return "值符配天蓬星：智慧与权威结合，利于谋略策划"
        else:
            return f"值符配{xing}：星符组合特殊，需详察吉凶"
    
    def _get_action_advice(self, zhi_fu_palace: PalaceInfo, cal: CalendarInfo) -> str:
        """获取行运建议"""
        gong_num = zhi_fu_palace["gong_num"]
        position = zhi_fu_palace["position"]
        month = cal["month"]
        
        # 基于值符位置的建议
        position_advice = {
            1: "宜静心思考，制定长远计划",
            2: "宜合作共事，发挥团队优势", 
            3: "宜主动出击，开创新的局面",
            4: "宜循序渐进，稳步推进计划",
            5: "宜统筹全局，发挥领导作用",
            6: "宜果断决策，展现权威风范",
            7: "宜加强沟通，促进合作交流",
            8: "宜稳扎稳打，积累实力资源",
            9: "宜展示才华，扩大影响力度"
        }
        
        base_advice = position_advice.get(gong_num, "宜审时度势")
        
        # 结合时令的建议
        seasonal_advice = self._get_seasonal_advice(month)
        
        return f"{base_advice}，{seasonal_advice}"
    
    def _get_seasonal_advice(self, month: int) -> str:
        """获取季节性建议"""
        if month in [3, 4, 5]:  # 春季
            return "春季生发，宜播种布局"
        elif month in [6, 7, 8]:  # 夏季
            return "夏季繁茂，宜积极行动"
        elif month in [9, 10, 11]:  # 秋季
            return "秋季收获，宜总结完善"
        else:  # 冬季
            return "冬季蛰伏，宜养精蓄锐"
    
    def _predict_ying_qi(self, zhi_fu_palace: PalaceInfo, cal: CalendarInfo) -> str:
        """预测应期"""
        gong_num = zhi_fu_palace["gong_num"]
        
        # 基于宫位数字的应期
        if gong_num in [1, 6]:  # 坎、乾
            period = "7-10天内"
        elif gong_num in [2, 8]:  # 坤、艮
            period = "15-30天内"
        elif gong_num in [3, 4]:  # 震、巽
            period = "3-7天内"
        elif gong_num == 5:  # 中宫
            period = "当即或1-3天内"
        elif gong_num in [7, 9]:  # 兑、离
            period = "5-15天内"
        else:
            period = "时机待定"
        
        return f"根据值符位置，事情应期约在{period}"


class RulesEngine:
    """规则引擎"""
    
    def __init__(self):
        self.plugins: List[RulePlugin] = []
        
    def add_plugin(self, plugin: RulePlugin):
        """添加插件"""
        self.plugins.append(plugin)
        
    def remove_plugin(self, plugin: RulePlugin):
        """移除插件"""
        if plugin in self.plugins:
            self.plugins.remove(plugin)
    
    def apply_all(self, nine_palace: NinePalace, cal: CalendarInfo) -> Dict[str, List[str]]:
        """应用所有插件"""
        results = {}
        
        for plugin in self.plugins:
            plugin_name = getattr(plugin, 'name', plugin.__class__.__name__)
            try:
                messages = plugin.apply(nine_palace, cal)
                results[plugin_name] = messages
            except Exception as e:
                results[plugin_name] = [f"插件执行错误: {str(e)}"]
        
        return results
    
    def get_plugin_names(self) -> List[str]:
        """获取所有插件名称"""
        return [getattr(plugin, 'name', plugin.__class__.__name__) for plugin in self.plugins]
    
    def get_plugin_by_name(self, name: str) -> Optional[RulePlugin]:
        """根据名称获取插件"""
        for plugin in self.plugins:
            plugin_name = getattr(plugin, 'name', plugin.__class__.__name__)
            if plugin_name == name:
                return plugin
        return None


def create_default_engine() -> RulesEngine:
    """创建默认规则引擎"""
    engine = RulesEngine()
    engine.add_plugin(ZhiFuPlugin())      # 值符分析优先
    engine.add_plugin(WangShuaiPlugin())
    engine.add_plugin(GeJuPlugin())
    engine.add_plugin(YingQiPlugin())
    return engine


def get_available_plugins() -> List[str]:
    """获取可用插件列表"""
    return ["zhifu", "wangshuai", "geju", "yingqi"]


def create_plugin_by_name(name: str) -> Optional[RulePlugin]:
    """根据名称创建插件"""
    plugins_map = {
        "zhifu": ZhiFuPlugin,
        "wangshuai": WangShuaiPlugin,
        "geju": GeJuPlugin,
        "yingqi": YingQiPlugin
    }
    
    plugin_class = plugins_map.get(name.lower())
    if plugin_class:
        return plugin_class()
    return None 