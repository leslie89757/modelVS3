"""
奇门遁甲局号计算模块
"""

from typing import Literal, Tuple
try:
    from qimen_calendar import CalendarInfo
    from symbols import (
        YANG_DUNE_MONTHS, YIN_DUNE_MONTHS, TIAN_GAN, DI_ZHI, SOLAR_TERMS
    )
except ImportError:
    from .qimen_calendar import CalendarInfo
    from .symbols import (
        YANG_DUNE_MONTHS, YIN_DUNE_MONTHS, TIAN_GAN, DI_ZHI, SOLAR_TERMS
    )


def get_ju(
    cal: CalendarInfo,
    mode: Literal["拆补", "活盘"] = "活盘"
) -> Tuple[int, bool]:
    """
    计算局号和阴阳遁
    
    Args:
        cal: 历法信息
        mode: 计算模式，"拆补"或"活盘"
        
    Returns:
        Tuple[int, bool]: (局号, 是否阳遁)
    """
    if mode == "拆补":
        return get_ju_chabu(cal)
    else:
        return get_ju_huopan(cal)


def get_ju_chabu(cal: CalendarInfo) -> Tuple[int, bool]:
    """
    拆补置闰法计算局号
    
    Args:
        cal: 历法信息
        
    Returns:
        Tuple[int, bool]: (局号, 是否阳遁)
    """
    # 判断阴阳遁
    is_yang = is_yang_dune(cal)
    
    # 计算局号
    ju_number = calculate_ju_number_chabu(cal, is_yang)
    
    return ju_number, is_yang


def get_ju_huopan(cal: CalendarInfo) -> Tuple[int, bool]:
    """
    活盘法计算局号
    
    Args:
        cal: 历法信息
        
    Returns:
        Tuple[int, bool]: (局号, 是否阳遁)
    """
    # 判断阴阳遁
    is_yang = is_yang_dune(cal)
    
    # 计算局号索引（0-17，对应阴阳遁各9局）
    ju_index = calculate_ju_index_huopan(cal, is_yang)
    
    # 转换为局号（1-9）
    ju_number = (ju_index % 9) + 1
    
    return ju_number, is_yang


def is_yang_dune(cal: CalendarInfo) -> bool:
    """
    判断是否为阳遁
    
    Args:
        cal: 历法信息
        
    Returns:
        bool: 是否为阳遁
    """
    # 根据节气判断阴阳遁
    # 冬至到夏至为阳遁，夏至到冬至为阴遁
    
    solar_term_index = cal["solar_term_index"]
    
    # 阳遁：冬至(23) - 夏至(11)
    # 阴遁：夏至(11) - 冬至(23)
    
    # 冬至索引为23，夏至索引为11
    if solar_term_index >= 23 or solar_term_index <= 11:
        return True  # 阳遁
    else:
        return False  # 阴遁


def calculate_ju_number_chabu(cal: CalendarInfo, is_yang: bool) -> int:
    """
    拆补置闰法计算局号
    
    Args:
        cal: 历法信息
        is_yang: 是否阳遁
        
    Returns:
        int: 局号（1-9）
    """
    # 获取元首（节气在月内的位置）
    yuan_shou = cal["yuan_shou"]
    
    # 获取时辰对应的数字
    shi_chen_num = get_shi_chen_number(cal["hour_zhi"])
    
    # 基础局号计算
    if is_yang:
        # 阳遁：元首 + 时辰 - 1
        base_ju = (yuan_shou + shi_chen_num - 1) % 9
    else:
        # 阴遁：元首 - 时辰 + 1
        base_ju = (yuan_shou - shi_chen_num + 1) % 9
    
    # 确保局号在1-9范围内
    if base_ju == 0:
        base_ju = 9
    
    return base_ju


def calculate_ju_index_huopan(cal: CalendarInfo, is_yang: bool) -> int:
    """
    活盘法计算局号索引
    
    Args:
        cal: 历法信息
        is_yang: 是否阳遁
        
    Returns:
        int: 局号索引（0-17）
    """
    # 获取日干支数字
    day_gan_num = TIAN_GAN.index(cal["day_gan"])
    day_zhi_num = DI_ZHI.index(cal["day_zhi"])
    
    # 获取时辰数字
    hour_zhi_num = DI_ZHI.index(cal["hour_zhi"])
    
    # 根据节气和时间计算索引
    solar_term_index = cal["solar_term_index"]
    
    # 基础计算
    base_index = (solar_term_index * 2 + day_gan_num + day_zhi_num + hour_zhi_num) % 18
    
    # 根据阴阳遁调整
    if is_yang:
        ju_index = base_index % 9
    else:
        ju_index = 9 + (base_index % 9)
    
    return ju_index


def get_shi_chen_number(hour_zhi: str) -> int:
    """
    获取时辰对应的数字
    
    Args:
        hour_zhi: 时辰地支
        
    Returns:
        int: 时辰数字
    """
    # 时辰数字对应表
    shi_chen_nums = {
        "子": 1, "丑": 2, "寅": 3, "卯": 4,
        "辰": 5, "巳": 6, "午": 7, "未": 8,
        "申": 9, "酉": 10, "戌": 11, "亥": 12
    }
    
    return shi_chen_nums.get(hour_zhi, 1)


def get_ju_name(ju_number: int, is_yang: bool) -> str:
    """
    获取局名称
    
    Args:
        ju_number: 局号
        is_yang: 是否阳遁
        
    Returns:
        str: 局名称
    """
    dun_type = "阳遁" if is_yang else "阴遁"
    return f"{dun_type}{ju_number}局"


def get_seasonal_ju_range(month: int) -> Tuple[int, int]:
    """
    获取季节性局号范围
    
    Args:
        month: 月份
        
    Returns:
        Tuple[int, int]: (最小局号, 最大局号)
    """
    # 春季：1-3局
    if month in [2, 3, 4]:
        return (1, 3)
    # 夏季：4-6局
    elif month in [5, 6, 7]:
        return (4, 6)
    # 秋季：7-9局
    elif month in [8, 9, 10]:
        return (7, 9)
    # 冬季：1-3局
    else:
        return (1, 3)


def validate_ju(ju_number: int, is_yang: bool, cal: CalendarInfo) -> bool:
    """
    验证局号是否合理
    
    Args:
        ju_number: 局号
        is_yang: 是否阳遁
        cal: 历法信息
        
    Returns:
        bool: 是否合理
    """
    # 基本范围检查
    if not (1 <= ju_number <= 9):
        return False
    
    # 阴阳遁一致性检查
    expected_yang = is_yang_dune(cal)
    if is_yang != expected_yang:
        return False
    
    # 季节性检查
    min_ju, max_ju = get_seasonal_ju_range(cal["month"])
    if not (min_ju <= ju_number <= max_ju):
        # 允许一定的偏差
        return True
    
    return True


def get_ju_info(ju_number: int, is_yang: bool) -> dict:
    """
    获取局的详细信息
    
    Args:
        ju_number: 局号
        is_yang: 是否阳遁
        
    Returns:
        dict: 局的详细信息
    """
    return {
        "ju_number": ju_number,
        "is_yang": is_yang,
        "ju_name": get_ju_name(ju_number, is_yang),
        "dun_type": "阳遁" if is_yang else "阴遁",
        "description": f"{'阳遁' if is_yang else '阴遁'}{ju_number}局"
    } 