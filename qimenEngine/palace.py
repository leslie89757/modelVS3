"""
奇门遁甲宫位排盘模块
"""

import json
from typing import Dict, List, Optional, Union, TypedDict
from dataclasses import dataclass
from pathlib import Path

try:
    from qimen_calendar import CalendarInfo
    from symbols import (
        JIU_GONG, LUOSHU, TIAN_GAN, DI_ZHI, BA_MEN, JIU_XING, JIU_SHEN,
        GONG_POSITION, BAGUA_GONG
    )
except ImportError:
    from .qimen_calendar import CalendarInfo
    from .symbols import (
        JIU_GONG, LUOSHU, TIAN_GAN, DI_ZHI, BA_MEN, JIU_XING, JIU_SHEN,
        GONG_POSITION, BAGUA_GONG
    )


class PalaceInfo(TypedDict):
    """单宫信息"""
    gong_num: int
    gong_name: str
    position: str
    bagua: str
    gan: str
    men: str
    xing: str
    shen: str
    wu_xing: str
    

class NinePalace(TypedDict):
    """九宫盘信息"""
    ju_number: int
    is_yang: bool
    ju_name: str
    palaces: Dict[str, PalaceInfo]
    calendar_info: Optional[CalendarInfo]
    mode: str  # "turn" or "fly"
    

class PalaceEngine:
    """宫位排盘引擎"""
    
    def __init__(self, palace_data_path: str = "data/palace_18.json"):
        """
        初始化宫位引擎
        
        Args:
            palace_data_path: 18活盘数据文件路径
        """
        self.palace_data = self._load_palace_data(palace_data_path)
        
    def _load_palace_data(self, data_path: str) -> dict:
        """加载18活盘数据"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果文件不存在，使用默认数据
            return self._get_default_palace_data()
    
    def _get_default_palace_data(self) -> dict:
        """获取默认活盘数据"""
        return {
            "description": "默认奇门遁甲18活盘数据",
            "palaces": {}
        }
    
    def turn_pan(self, ju_number: int, is_yang: bool) -> NinePalace:
        """
        转盘排盘
        
        Args:
            ju_number: 局号（1-9）
            is_yang: 是否阳遁
            
        Returns:
            NinePalace: 九宫盘结果
        """
        # 获取局名
        dun_type = "阳遁" if is_yang else "阴遁"
        ju_name = f"{dun_type}{ju_number}局"
        
        # 从数据中获取对应的活盘
        palace_key = ju_name
        if palace_key not in self.palace_data.get("palaces", {}):
            # 如果没有数据，使用计算方法
            return self._calculate_turn_pan(ju_number, is_yang)
        
        base_palace = self.palace_data["palaces"][palace_key]
        
        # 构建九宫盘
        palaces = {}
        for gong_num in range(1, 10):
            gong_str = str(gong_num)
            base_info = base_palace["palaces"].get(gong_str, {})
            
            palaces[gong_str] = PalaceInfo(
                gong_num=gong_num,
                gong_name=JIU_GONG[gong_num],
                position=GONG_POSITION[gong_num],
                bagua=BAGUA_GONG[gong_num],
                gan=base_info.get("gan", ""),
                men=base_info.get("men", ""),
                xing=base_info.get("xing", ""),
                shen=base_info.get("shen", ""),
                wu_xing=self._get_gong_wu_xing(gong_num)
            )
        
        return NinePalace(
            ju_number=ju_number,
            is_yang=is_yang,
            ju_name=ju_name,
            palaces=palaces,
            calendar_info=None,
            mode="turn"
        )
    
    def fly_pan(self, cal: CalendarInfo) -> NinePalace:
        """
        飞盘排盘
        
        Args:
            cal: 历法信息
            
        Returns:
            NinePalace: 九宫盘结果
        """
        # 根据时间计算飞盘位置
        year_gan_idx = TIAN_GAN.index(cal["year_gan"])
        month_zhi_idx = DI_ZHI.index(cal["month_zhi"])
        day_gan_idx = TIAN_GAN.index(cal["day_gan"])
        hour_zhi_idx = DI_ZHI.index(cal["hour_zhi"])
        
        # 计算飞盘起始位置
        start_gong = self._calculate_fly_start_gong(
            year_gan_idx, month_zhi_idx, day_gan_idx, hour_zhi_idx
        )
        
        # 构建飞盘
        palaces = {}
        for gong_num in range(1, 10):
            gong_str = str(gong_num)
            
            # 计算飞到的位置
            fly_pos = self._calculate_fly_position(start_gong, gong_num)
            
            palaces[gong_str] = PalaceInfo(
                gong_num=gong_num,
                gong_name=JIU_GONG[gong_num],
                position=GONG_POSITION[gong_num],
                bagua=BAGUA_GONG[gong_num],
                gan=self._get_fly_gan(fly_pos),
                men=self._get_fly_men(fly_pos),
                xing=self._get_fly_xing(fly_pos),
                shen=self._get_fly_shen(fly_pos),
                wu_xing=self._get_gong_wu_xing(gong_num)
            )
        
        return NinePalace(
            ju_number=0,  # 飞盘没有固定局号
            is_yang=True,  # 根据时间判断
            ju_name="飞盘",
            palaces=palaces,
            calendar_info=cal,
            mode="fly"
        )
    
    def _calculate_turn_pan(self, ju_number: int, is_yang: bool) -> NinePalace:
        """计算转盘（当没有数据时使用）"""
        # 基础转盘计算逻辑
        dun_type = "阳遁" if is_yang else "阴遁"
        ju_name = f"{dun_type}{ju_number}局"
        
        # 默认排列
        base_sequence = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
        men_sequence = ["休门", "死门", "伤门", "杜门", "中门", "开门", "惊门", "生门", "景门"]
        xing_sequence = ["天蓬", "天任", "天冲", "天辅", "天禽", "天心", "天柱", "天英", "天芮"]
        shen_sequence = ["直符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天", "太常"]
        
        # 根据局号和阴阳遁调整序列
        if is_yang:
            # 阳遁：正序
            offset = ju_number - 1
        else:
            # 阴遁：逆序
            offset = 9 - ju_number
            base_sequence = base_sequence[::-1]
            men_sequence = men_sequence[::-1]
            xing_sequence = xing_sequence[::-1]
            shen_sequence = shen_sequence[::-1]
        
        palaces = {}
        for gong_num in range(1, 10):
            gong_str = str(gong_num)
            idx = (gong_num - 1 + offset) % 9
            
            palaces[gong_str] = PalaceInfo(
                gong_num=gong_num,
                gong_name=JIU_GONG[gong_num],
                position=GONG_POSITION[gong_num],
                bagua=BAGUA_GONG[gong_num],
                gan=base_sequence[idx],
                men=men_sequence[idx],
                xing=xing_sequence[idx],
                shen=shen_sequence[idx],
                wu_xing=self._get_gong_wu_xing(gong_num)
            )
        
        return NinePalace(
            ju_number=ju_number,
            is_yang=is_yang,
            ju_name=ju_name,
            palaces=palaces,
            calendar_info=None,
            mode="turn"
        )
    
    def _calculate_fly_start_gong(self, year_gan: int, month_zhi: int, 
                                 day_gan: int, hour_zhi: int) -> int:
        """计算飞盘起始宫位"""
        # 飞盘起始位置计算公式
        start_pos = (year_gan + month_zhi + day_gan + hour_zhi) % 9
        return start_pos if start_pos != 0 else 9
    
    def _calculate_fly_position(self, start_gong: int, gong_num: int) -> int:
        """计算飞盘位置"""
        # 飞盘位置计算
        fly_pos = (start_gong + gong_num - 1) % 9
        return fly_pos if fly_pos != 0 else 9
    
    def _get_fly_gan(self, fly_pos: int) -> str:
        """获取飞盘天干"""
        gan_sequence = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
        return gan_sequence[fly_pos - 1]
    
    def _get_fly_men(self, fly_pos: int) -> str:
        """获取飞盘八门"""
        men_sequence = ["休门", "死门", "伤门", "杜门", "中门", "开门", "惊门", "生门", "景门"]
        return men_sequence[fly_pos - 1]
    
    def _get_fly_xing(self, fly_pos: int) -> str:
        """获取飞盘九星"""
        xing_sequence = ["天蓬", "天任", "天冲", "天辅", "天禽", "天心", "天柱", "天英", "天芮"]
        return xing_sequence[fly_pos - 1]
    
    def _get_fly_shen(self, fly_pos: int) -> str:
        """获取飞盘九神"""
        shen_sequence = ["直符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天", "太常"]
        return shen_sequence[fly_pos - 1]
    
    def _get_gong_wu_xing(self, gong_num: int) -> str:
        """获取宫位五行"""
        wu_xing_map = {
            1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 
            6: "金", 7: "金", 8: "土", 9: "火"
        }
        return wu_xing_map.get(gong_num, "土")
    
    def get_palace_analysis(self, nine_palace: NinePalace) -> Dict[str, str]:
        """
        获取宫位分析
        
        Args:
            nine_palace: 九宫盘
            
        Returns:
            Dict[str, str]: 分析结果
        """
        analysis = {
            "基本信息": f"{nine_palace['ju_name']}",
            "排盘方式": "转盘" if nine_palace["mode"] == "turn" else "飞盘",
            "阴阳遁": "阳遁" if nine_palace["is_yang"] else "阴遁"
        }
        
        # 分析各宫位
        for gong_str, palace_info in nine_palace["palaces"].items():
            gong_analysis = (
                f"{palace_info['gong_name']}({palace_info['position']}): "
                f"{palace_info['gan']}{palace_info['men']}{palace_info['xing']}{palace_info['shen']}"
            )
            analysis[f"{gong_str}宫"] = gong_analysis
        
        return analysis

    def find_zhi_fu(self, nine_palace: NinePalace) -> Optional[PalaceInfo]:
        """
        查找值符(直符)所在宫位
        
        Args:
            nine_palace: 九宫盘
            
        Returns:
            Optional[PalaceInfo]: 值符宫位信息，若未找到则返回None
        """
        for palace_info in nine_palace["palaces"].values():
            if palace_info["shen"] == "直符":
                return palace_info
        return None
    
    def get_zhi_fu_analysis(self, nine_palace: NinePalace, cal: Optional[CalendarInfo] = None) -> Dict[str, str]:
        """
        获取值符详细分析
        
        Args:
            nine_palace: 九宫盘
            cal: 历法信息（可选）
            
        Returns:
            Dict[str, str]: 值符分析结果
        """
        zhi_fu_palace = self.find_zhi_fu(nine_palace)
        if not zhi_fu_palace:
            return {"错误": "未找到值符位置"}
        
        analysis = {
            "值符位置": f"{zhi_fu_palace['gong_name']}({zhi_fu_palace['position']})",
            "值符组合": f"{zhi_fu_palace['gan']}{zhi_fu_palace['men']}{zhi_fu_palace['xing']}{zhi_fu_palace['shen']}",
            "宫位八卦": zhi_fu_palace['bagua'],
            "宫位五行": zhi_fu_palace['wu_xing'],
            "值符意义": self._get_zhi_fu_meaning(zhi_fu_palace)
        }
        
        # 如果有历法信息，添加时令分析
        if cal:
            analysis["时令影响"] = self._analyze_zhi_fu_seasonal_influence(zhi_fu_palace, cal)
            analysis["值符旺衰"] = self._analyze_zhi_fu_wang_shuai(zhi_fu_palace, cal)
        
        return analysis
    
    def _get_zhi_fu_meaning(self, zhi_fu_palace: PalaceInfo) -> str:
        """
        获取值符在特定宫位的含义
        
        Args:
            zhi_fu_palace: 值符宫位信息
            
        Returns:
            str: 值符含义
        """
        gong_num = zhi_fu_palace["gong_num"]
        meanings = {
            1: "值符居坎宫，主智慧谋略，利于策划思考",
            2: "值符居坤宫，主厚德载物，利于合作共事", 
            3: "值符居震宫，主振奋向上，利于开创事业",
            4: "值符居巽宫，主进退有度，利于渐进发展",
            5: "值符居中宫，主居中调和，统领全局",
            6: "值符居乾宫，主刚健有力，利于领导决策",
            7: "值符居兑宫，主言语交流，利于社交商谈",
            8: "值符居艮宫，主稳重止静，利于守成积蓄",
            9: "值符居离宫，主光明正大，利于宣传展示"
        }
        return meanings.get(gong_num, "值符含义待解")
    
    def _analyze_zhi_fu_seasonal_influence(self, zhi_fu_palace: PalaceInfo, cal: CalendarInfo) -> str:
        """
        分析值符的时令影响
        
        Args:
            zhi_fu_palace: 值符宫位信息
            cal: 历法信息
            
        Returns:
            str: 时令影响分析
        """
        month = cal["month"]
        gong_wu_xing = zhi_fu_palace["wu_xing"]
        
        # 根据月份判断季节对值符的影响
        if month in [3, 4, 5]:  # 春季
            if gong_wu_xing in ["木"]:
                return "春季木旺，值符得时而强"
            elif gong_wu_xing in ["金"]:
                return "春季金衰，值符失时需谨慎"
            else:
                return "春季时令，值符力量平稳"
        elif month in [6, 7, 8]:  # 夏季
            if gong_wu_xing in ["火"]:
                return "夏季火旺，值符得时而强"
            elif gong_wu_xing in ["水"]:
                return "夏季水衰，值符失时需谨慎"
            else:
                return "夏季时令，值符力量平稳"
        elif month in [9, 10, 11]:  # 秋季
            if gong_wu_xing in ["金"]:
                return "秋季金旺，值符得时而强"
            elif gong_wu_xing in ["木"]:
                return "秋季木衰，值符失时需谨慎"
            else:
                return "秋季时令，值符力量平稳"
        else:  # 冬季
            if gong_wu_xing in ["水"]:
                return "冬季水旺，值符得时而强"
            elif gong_wu_xing in ["火"]:
                return "冬季火衰，值符失时需谨慎"
            else:
                return "冬季时令，值符力量平稳"
    
    def _analyze_zhi_fu_wang_shuai(self, zhi_fu_palace: PalaceInfo, cal: CalendarInfo) -> str:
        """
        分析值符的旺衰状态
        
        Args:
            zhi_fu_palace: 值符宫位信息
            cal: 历法信息
            
        Returns:
            str: 旺衰分析
        """
        # 值符天干为戊土，分析戊土在当前宫位的旺衰
        gong_wu_xing = zhi_fu_palace["wu_xing"]
        
        # 戊土在不同宫位的旺衰
        if gong_wu_xing == "土":
            return "戊土居土宫，比和而旺"
        elif gong_wu_xing == "火":
            return "戊土居火宫，火生土旺"
        elif gong_wu_xing == "金":
            return "戊土居金宫，土生金泄"
        elif gong_wu_xing == "水":
            return "戊土居水宫，土克水耗力"
        elif gong_wu_xing == "木":
            return "戊土居木宫，木克土受制"
        else:
            return "值符旺衰状态需详查"
    
    def get_zhi_fu_influence_analysis(self, nine_palace: NinePalace) -> List[str]:
        """
        分析值符对整个格局的影响
        
        Args:
            nine_palace: 九宫盘
            
        Returns:
            List[str]: 影响分析列表
        """
        zhi_fu_palace = self.find_zhi_fu(nine_palace)
        if not zhi_fu_palace:
            return ["值符位置未明，无法分析影响"]
        
        influences = []
        
        # 分析值符对相邻宫位的影响
        zhi_fu_gong_num = zhi_fu_palace["gong_num"]
        adjacent_gongs = self._get_adjacent_gongs(zhi_fu_gong_num)
        
        for adj_gong_num in adjacent_gongs:
            adj_palace = nine_palace["palaces"][str(adj_gong_num)]
            influence = self._analyze_zhi_fu_to_palace_influence(zhi_fu_palace, adj_palace)
            if influence:
                influences.append(f"值符对{adj_palace['gong_name']}：{influence}")
        
        # 分析值符与特殊格局的关系
        special_patterns = self._check_zhi_fu_special_patterns(nine_palace, zhi_fu_palace)
        influences.extend(special_patterns)
        
        return influences
    
    def _get_adjacent_gongs(self, gong_num: int) -> List[int]:
        """
        获取相邻宫位
        
        Args:
            gong_num: 宫位号
            
        Returns:
            List[int]: 相邻宫位号列表
        """
        # 九宫相邻关系（基于洛书排列）
        adjacent_map = {
            1: [2, 4, 6],      # 坎宫
            2: [1, 3, 5],      # 坤宫
            3: [2, 4, 8],      # 震宫
            4: [1, 3, 7, 9],   # 巽宫
            5: [2, 6, 8],      # 中宫
            6: [1, 5, 7],      # 乾宫
            7: [4, 6, 8],      # 兑宫
            8: [3, 5, 7, 9],   # 艮宫
            9: [4, 8]          # 离宫
        }
        return adjacent_map.get(gong_num, [])
    
    def _analyze_zhi_fu_to_palace_influence(self, zhi_fu_palace: PalaceInfo, target_palace: PalaceInfo) -> str:
        """
        分析值符对目标宫位的影响
        
        Args:
            zhi_fu_palace: 值符宫位
            target_palace: 目标宫位
            
        Returns:
            str: 影响描述
        """
        # 简化实现：主要看五行关系和门神配合
        zhi_fu_wu_xing = zhi_fu_palace["wu_xing"]
        target_wu_xing = target_palace["wu_xing"]
        
        if self._is_sheng_relation(zhi_fu_wu_xing, target_wu_xing):
            return "生助有力，加强吉祥"
        elif self._is_ke_relation(zhi_fu_wu_xing, target_wu_xing):
            return "制约有度，化解凶煞"
        else:
            return "关系平和，影响中性"
    
    def _is_sheng_relation(self, wu_xing1: str, wu_xing2: str) -> bool:
        """判断五行相生关系"""
        sheng_map = {
            "木": "火", "火": "土", "土": "金", "金": "水", "水": "木"
        }
        return sheng_map.get(wu_xing1) == wu_xing2
    
    def _is_ke_relation(self, wu_xing1: str, wu_xing2: str) -> bool:
        """判断五行相克关系"""
        ke_map = {
            "木": "土", "土": "水", "水": "火", "火": "金", "金": "木"
        }
        return ke_map.get(wu_xing1) == wu_xing2
    
    def _check_zhi_fu_special_patterns(self, nine_palace: NinePalace, zhi_fu_palace: PalaceInfo) -> List[str]:
        """
        检查值符相关的特殊格局
        
        Args:
            nine_palace: 九宫盘
            zhi_fu_palace: 值符宫位
            
        Returns:
            List[str]: 特殊格局列表
        """
        patterns = []
        
        # 检查值符是否在中宫
        if zhi_fu_palace["gong_num"] == 5:
            patterns.append("值符居中宫：统领全局，权威显著")
        
        # 检查值符与三奇的关系
        san_qi = ["乙", "丙", "丁"]
        for gong_str, palace_info in nine_palace["palaces"].items():
            if palace_info["gan"] in san_qi:
                if palace_info["gong_num"] == zhi_fu_palace["gong_num"]:
                    patterns.append(f"值符与{palace_info['gan']}奇同宫：奇仪相合，大吉之象")
                elif abs(palace_info["gong_num"] - zhi_fu_palace["gong_num"]) == 1:
                    patterns.append(f"值符与{palace_info['gan']}奇相邻：奇仪呼应，吉祥有应")
        
        # 检查值符与开门的关系
        for palace_info in nine_palace["palaces"].values():
            if palace_info["men"] == "开门":
                if palace_info["gong_num"] == zhi_fu_palace["gong_num"]:
                    patterns.append("值符与开门同宫：开启良机，事业发达")
                break
        
        return patterns
    
    def format_palace_display(self, nine_palace: NinePalace, highlight_zhi_fu: bool = True) -> str:
        """
        格式化显示九宫盘
        
        Args:
            nine_palace: 九宫盘
            highlight_zhi_fu: 是否突出显示值符
            
        Returns:
            str: 格式化的九宫盘显示
        """
        palaces = nine_palace["palaces"]
        
        # 找到值符位置
        zhi_fu_gong = None
        if highlight_zhi_fu:
            zhi_fu_palace = self.find_zhi_fu(nine_palace)
            if zhi_fu_palace:
                zhi_fu_gong = zhi_fu_palace["gong_num"]
        
        # 九宫格布局
        layout = """
        ┌─────────┬─────────┬─────────┐
        │  {p4}  │  {p9}  │  {p2}  │
        │  {p4_content}  │  {p9_content}  │  {p2_content}  │
        ├─────────┼─────────┼─────────┤
        │  {p3}  │  {p5}  │  {p7}  │
        │  {p3_content}  │  {p5_content}  │  {p7_content}  │
        ├─────────┼─────────┼─────────┤
        │  {p8}  │  {p1}  │  {p6}  │
        │  {p8_content}  │  {p1_content}  │  {p6_content}  │
        └─────────┴─────────┴─────────┘
        """
        
        # 填充内容
        content = {}
        for i in range(1, 10):
            palace = palaces[str(i)]
            content[f"p{i}"] = palace["gong_name"]
            palace_content = f"{palace['gan']}{palace['men']}{palace['xing']}{palace['shen']}"
            
            # 如果是值符宫位，添加标记
            if highlight_zhi_fu and i == zhi_fu_gong:
                palace_content = f"【{palace_content}】"  # 用方括号突出显示值符
            
            content[f"p{i}_content"] = palace_content
        
        # 添加值符说明
        result = layout.format(**content)
        if highlight_zhi_fu and zhi_fu_gong:
            result += f"\n※ 【】标记为值符位置：{palaces[str(zhi_fu_gong)]['gong_name']}"
        
        return result
    
    def format_zhi_fu_summary(self, nine_palace: NinePalace, cal: Optional[CalendarInfo] = None) -> str:
        """
        格式化值符摘要信息
        
        Args:
            nine_palace: 九宫盘
            cal: 历法信息（可选）
            
        Returns:
            str: 值符摘要显示
        """
        zhi_fu_analysis = self.get_zhi_fu_analysis(nine_palace, cal)
        
        if "错误" in zhi_fu_analysis:
            return "值符信息：未找到值符位置"
        
        summary = f"""
═══════════════════════════════════════
                值符分析摘要
═══════════════════════════════════════
{zhi_fu_analysis['值符位置']}
{zhi_fu_analysis['值符组合']}
{zhi_fu_analysis['值符意义']}
"""
        
        if cal:
            summary += f"""
时令分析：{zhi_fu_analysis.get('时令影响', '无')}
旺衰状态：{zhi_fu_analysis.get('值符旺衰', '无')}
"""
        
        # 添加影响分析
        influences = self.get_zhi_fu_influence_analysis(nine_palace)
        if influences:
            summary += "\n格局影响：\n"
            for influence in influences[:3]:  # 只显示前3条
                summary += f"  • {influence}\n"
        
        summary += "═══════════════════════════════════════"
        
        return summary
    
    def validate_palace(self, nine_palace: NinePalace) -> bool:
        """
        验证九宫盘是否合理
        
        Args:
            nine_palace: 九宫盘
            
        Returns:
            bool: 是否合理
        """
        # 检查宫位完整性
        if len(nine_palace["palaces"]) != 9:
            return False
        
        # 检查每个宫位的信息是否完整
        for gong_str, palace_info in nine_palace["palaces"].items():
            if not all([
                palace_info["gan"], palace_info["men"], 
                palace_info["xing"], palace_info["shen"]
            ]):
                return False
        
        return True 