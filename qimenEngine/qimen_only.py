#!/usr/bin/env python3
"""
奇门遁甲排盘系统
仅基于当前时间的核心实现
"""

import pytz
from datetime import datetime
import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import qimen_calendar as calendar, ju, palace, rules
    from palace import PalaceEngine
    from zhishi_calculator import zhishi_calculator
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def display_calendar_info(cal_info):
    """显示历法信息"""
    print("📋 历法信息:")
    print(f"   📅 公历: {cal_info['year']}年{cal_info['month']}月{cal_info['day']}日 {cal_info['hour']}时{cal_info['minute']}分")
    print(f"   🕐 时辰: {cal_info['shi_chen']}")
    print(f"   📆 节气: {cal_info['solar_term']}")
    print(f"   🌟 干支: {cal_info['year_gan']}{cal_info['year_zhi']}年 {cal_info['month_gan']}{cal_info['month_zhi']}月 {cal_info['day_gan']}{cal_info['day_zhi']}日 {cal_info['hour_gan']}{cal_info['hour_zhi']}时")
    
    # 添加真太阳时信息（如果启用）
    if cal_info.get('use_true_solar_time', False):
        time_diff = cal_info.get('time_difference_minutes', 0)
        true_solar_time = cal_info.get('true_solar_time', '')
        standard_shi_chen = cal_info.get('standard_time_shi_chen', '')
        
        print()
        print("📝 时间对比信息:")
        print(f"   ☀️  真太阳时: {true_solar_time} (用于排盘)")
        print(f"   ⏰ 时间差异: {time_diff:+.1f} 分钟")
        print(f"   📊 对比: 标准时间→{standard_shi_chen} / 真太阳时→{cal_info['shi_chen']}")
        
        # 如果时辰发生变化，特别标注
        if standard_shi_chen != cal_info['shi_chen']:
            print(f"   🎯 注意: 由于真太阳时影响，时辰从 {standard_shi_chen} 变为 {cal_info['shi_chen']}")
        
        print(f"   💡 说明: 奇门遁甲使用真太阳时确保天文准确性")
    
    print()

# 修改display_ju_info函数签名和实现

def display_ju_info(ju_number, is_yang, nine_palace, cal_info=None):
    """显示奇门局信息"""
    print("🏰 奇门局信息:")
    print(f"   🎯 局数: {ju_number}")
    print(f"   ⚊ 阴阳: {'阳遁' if is_yang else '阴遁'}")
    print(f"   📜 局名: {nine_palace.get('ju_name', '未知')}")
    
    # 查找值符
    zhi_fu_info = "未知"
    zhi_fu_gong = None
    
    for gong_str, palace_info in nine_palace.get("palaces", {}).items():
        # 查找值符（直符）
        if palace_info.get("shen") == "直符":
            zhi_fu_info = f"{palace_info.get('gong_name', '')}({palace_info.get('gan', '')})"
            zhi_fu_gong = gong_str
            break
    
    print(f"   🧭 值符: {zhi_fu_info}")
    
    # 计算并显示值使
    if cal_info:
        hour_zhi = cal_info.get('hour_zhi', '')
        zhishi_men = zhishi_calculator.calculate_zhishi_by_time(hour_zhi)
        zhishi_gong, zhishi_palace = zhishi_calculator.find_zhishi_gong(nine_palace, zhishi_men)
        
        if zhishi_gong and zhishi_palace:
            zhi_shi_info = f"{zhishi_palace.get('gong_name', '')}({zhishi_men})"
        else:
            zhi_shi_info = f"{zhishi_men}(未在盘中)"
    else:
        zhi_shi_info = "需要时辰信息"
    
    print(f"   ⭐ 值使: {zhi_shi_info}")
    print()

def display_nine_palace(nine_palace):
    """显示九宫排盘"""
    print("🏯 九宫排盘:")
    
    palaces = nine_palace.get("palaces", {})
    if not palaces:
        print("   九宫排盘信息缺失")
        print()
        return
    
    # 找到值符位置用于标记
    zhi_fu_gong = None
    for gong_str, palace_info in palaces.items():
        if palace_info.get("shen") == "直符":
            zhi_fu_gong = int(gong_str)
            break
    
    # 九宫格布局显示
    print("   ┌─────────────┬─────────────┬─────────────┐")
    
    # 上排：巽4 离9 坤2
    for gong_num in [4, 9, 2]:
        gong_info = palaces.get(str(gong_num), {})
        content = f"{gong_info.get('gan', '?')}{gong_info.get('men', '?')}{gong_info.get('xing', '?')}{gong_info.get('shen', '?')}"
        if gong_num == zhi_fu_gong:
            content = f"【{content}】"  # 标记值符
        gong_name = gong_info.get('gong_name', f'{gong_num}宫')
        print(f"   │ {gong_name:^9} │", end="")
    print()
    
    for gong_num in [4, 9, 2]:
        gong_info = palaces.get(str(gong_num), {})
        content = f"{gong_info.get('gan', '?')}{gong_info.get('men', '?')}{gong_info.get('xing', '?')}{gong_info.get('shen', '?')}"
        if gong_num == zhi_fu_gong:
            content = f"【{content}】"
        print(f"   │ {content:^11} │", end="")
    print()
    
    print("   ├─────────────┼─────────────┼─────────────┤")
    
    # 中排：震3 中5 兑7  
    for gong_num in [3, 5, 7]:
        gong_info = palaces.get(str(gong_num), {})
        content = f"{gong_info.get('gan', '?')}{gong_info.get('men', '?')}{gong_info.get('xing', '?')}{gong_info.get('shen', '?')}"
        if gong_num == zhi_fu_gong:
            content = f"【{content}】"
        gong_name = gong_info.get('gong_name', f'{gong_num}宫')
        print(f"   │ {gong_name:^9} │", end="")
    print()
    
    for gong_num in [3, 5, 7]:
        gong_info = palaces.get(str(gong_num), {})
        content = f"{gong_info.get('gan', '?')}{gong_info.get('men', '?')}{gong_info.get('xing', '?')}{gong_info.get('shen', '?')}"
        if gong_num == zhi_fu_gong:
            content = f"【{content}】"
        print(f"   │ {content:^11} │", end="")
    print()
    
    print("   ├─────────────┼─────────────┼─────────────┤")
    
    # 下排：艮8 坎1 乾6
    for gong_num in [8, 1, 6]:
        gong_info = palaces.get(str(gong_num), {})
        content = f"{gong_info.get('gan', '?')}{gong_info.get('men', '?')}{gong_info.get('xing', '?')}{gong_info.get('shen', '?')}"
        if gong_num == zhi_fu_gong:
            content = f"【{content}】"
        gong_name = gong_info.get('gong_name', f'{gong_num}宫')
        print(f"   │ {gong_name:^9} │", end="")
    print()
    
    for gong_num in [8, 1, 6]:
        gong_info = palaces.get(str(gong_num), {})
        content = f"{gong_info.get('gan', '?')}{gong_info.get('men', '?')}{gong_info.get('xing', '?')}{gong_info.get('shen', '?')}"
        if gong_num == zhi_fu_gong:
            content = f"【{content}】"
        print(f"   │ {content:^11} │", end="")
    print()
    
    print("   └─────────────┴─────────────┴─────────────┘")
    
    # 添加说明
    if zhi_fu_gong:
        zhi_fu_palace = palaces.get(str(zhi_fu_gong), {})
        print(f"   ※ 【】标记为值符位置：{zhi_fu_palace.get('gong_name', '未知宫位')}")
    
    print("   📝 排盘格式：天干+八门+九星+九神")
    print()

def display_analysis(analysis):
    """显示断事分析"""
    print("📊 奇门断事分析:")
    for analysis_type, results in analysis.items():
        if results:
            print(f"   📈 {analysis_type} ({len(results)} 项):")
            for i, result in enumerate(results, 1):
                print(f"      {i}. {result}")
    print()

def _core_qimen_calculation(dt, timezone_str="Asia/Shanghai"):
    """
    核心奇门排盘计算逻辑
    
    Args:
        dt: datetime对象（带时区信息）
        timezone_str: 时区字符串
        
    Returns:
        tuple: (cal_info, ju_number, is_yang, nine_palace, analysis, palace_engine)
    """
    # 验证输入（使用validation模块）
    from validation import validate_time
    time_data = {
        'year': dt.year,
        'month': dt.month, 
        'day': dt.day,
        'hour': dt.hour,
        'minute': dt.minute,
        'timezone': timezone_str
    }
    
    time_validation = validate_time(time_data)
    if time_validation.is_error():
        print(f"⚠️  时间验证警告: {time_validation.error_value()}")
    
    # 奇门排盘
    cal_info = calendar.from_datetime(dt, timezone_str)
    ju_number, is_yang = ju.get_ju(cal_info, "活盘")
    palace_engine = PalaceEngine()
    nine_palace = palace_engine.turn_pan(ju_number, is_yang)
    
    # 断事分析
    rules_engine = rules.create_default_engine()
    analysis = rules_engine.apply_all(nine_palace, cal_info)
    
    return cal_info, ju_number, is_yang, nine_palace, analysis, palace_engine

def _display_full_results(cal_info, ju_number, is_yang, nine_palace, analysis, palace_engine, dt):
    """
    显示完整的奇门排盘结果
    
    Args:
        cal_info: 历法信息
        ju_number: 局数
        is_yang: 是否阳遁
        nine_palace: 九宫数据
        analysis: 断事分析
        palace_engine: 宫位引擎
        dt: 原始datetime对象
    """
    display_calendar_info(cal_info)
    display_detailed_calendar_info(cal_info)  # 详细历法信息
    display_ju_info(ju_number, is_yang, nine_palace, cal_info)
    display_zhishi_info(cal_info, nine_palace)  # 值使详细信息
    display_detailed_ju_info(ju_number, is_yang)  # 详细局信息
    display_nine_palace(nine_palace)
    display_palace_details(nine_palace)  # 宫位详细信息
    display_zhi_fu_comprehensive_analysis(palace_engine, nine_palace, cal_info)  # 值符综合分析
    display_ganzhi_details(cal_info)  # 干支详细信息
    display_astronomical_details(dt)  # 天文算法详情
    display_alternative_methods(cal_info, palace_engine)  # 其他方法对比
    display_analysis(analysis)

def qimen_now():
    """当前时间奇门排盘 - 核心函数"""
    print("🎯 奇门遁甲排盘")
    print("=" * 50)
    
    # 获取当前上海时间
    shanghai_tz = pytz.timezone("Asia/Shanghai")
    current_time = datetime.now(shanghai_tz)
    
    # 使用核心计算函数
    cal_info, ju_number, is_yang, nine_palace, analysis, palace_engine = _core_qimen_calculation(current_time)
    
    # 显示完整结果
    _display_full_results(cal_info, ju_number, is_yang, nine_palace, analysis, palace_engine, current_time)
    
    return cal_info, ju_number, is_yang, nine_palace, analysis

def display_detailed_calendar_info(cal_info):
    """显示详细历法信息"""
    print("📅 详细历法信息:")
    print(f"   🌅 早晚子时: {'早子时' if cal_info.get('is_early_zi') else '晚子时' if cal_info.get('is_late_zi') else '非子时'}")
    print(f"   📊 节气日: {cal_info.get('jie_qi_day', '未知')}日")
    print(f"   🎯 元首: 第{cal_info.get('yuan_shou', '未知')}元")
    print(f"   🕐 时区: {cal_info.get('timezone', 'Asia/Shanghai')}")
    print()

def display_detailed_ju_info(ju_number, is_yang):
    """显示详细局信息"""
    print("🏰 详细局信息:")
    ju_info = ju.get_ju_info(ju_number, is_yang)
    print(f"   📝 局名: {ju_info.get('ju_name', '未知')}")
    print(f"   📖 描述: {ju_info.get('description', '未知')}")
    print(f"   🎭 遁甲类型: {ju_info.get('dun_type', '未知')}")
    print()

def display_palace_details(nine_palace):
    """显示宫位详细信息"""
    print("🏯 宫位详细信息:")
    palace_engine = PalaceEngine()
    palace_analysis = palace_engine.get_palace_analysis(nine_palace)
    
    for key, value in palace_analysis.items():
        if key not in ["基本信息", "排盘方式", "阴阳遁"]:  # 基础信息已经显示过
            print(f"   🏛️  {key}: {value}")
    
    print("\n🔍 各宫五行属性:")
    for gong_str, palace_info in nine_palace.get("palaces", {}).items():
        wu_xing = palace_info.get('wu_xing', '未知')
        bagua = palace_info.get('bagua', '未知')
        position = palace_info.get('position', '未知')
        print(f"   {palace_info.get('gong_name', f'{gong_str}宫')}: {wu_xing}行 {bagua}卦 {position}")
    print()

def display_zhi_fu_comprehensive_analysis(palace_engine, nine_palace, cal_info):
    """显示值符综合分析"""
    print("🎭 值符综合分析:")
    
    # 值符详细分析
    zhi_fu_analysis = palace_engine.get_zhi_fu_analysis(nine_palace, cal_info)
    for key, value in zhi_fu_analysis.items():
        if key != "错误":
            print(f"   🔸 {key}: {value}")
    
    # 值符影响分析
    zhi_fu_influence = palace_engine.get_zhi_fu_influence_analysis(nine_palace)
    if zhi_fu_influence:
        print("   🌟 值符影响:")
        for influence in zhi_fu_influence:
            print(f"      • {influence}")
    
    # 值符摘要
    print("\n📋 值符摘要:")
    zhi_fu_summary = palace_engine.format_zhi_fu_summary(nine_palace, cal_info)
    # 去掉装饰线，只显示核心内容
    summary_lines = zhi_fu_summary.split('\n')
    for line in summary_lines:
        if line.strip() and not line.startswith('═'):
            print(f"   {line.strip()}")
    print()

def display_ganzhi_details(cal_info):
    """显示干支详细信息"""
    print("🌟 干支详细信息:")
    
    # 干支五行
    from symbols import TIAN_GAN_WU_XING, DI_ZHI_WU_XING
    
    print(f"   年柱: {cal_info['year_gan']}{cal_info['year_zhi']} " +
          f"({TIAN_GAN_WU_XING.get(cal_info['year_gan'], '?')}{DI_ZHI_WU_XING.get(cal_info['year_zhi'], '?')})")
    
    print(f"   月柱: {cal_info['month_gan']}{cal_info['month_zhi']} " +
          f"({TIAN_GAN_WU_XING.get(cal_info['month_gan'], '?')}{DI_ZHI_WU_XING.get(cal_info['month_zhi'], '?')})")
    
    print(f"   日柱: {cal_info['day_gan']}{cal_info['day_zhi']} " +
          f"({TIAN_GAN_WU_XING.get(cal_info['day_gan'], '?')}{DI_ZHI_WU_XING.get(cal_info['day_zhi'], '?')})")
    
    print(f"   时柱: {cal_info['hour_gan']}{cal_info['hour_zhi']} " +
          f"({TIAN_GAN_WU_XING.get(cal_info['hour_gan'], '?')}{DI_ZHI_WU_XING.get(cal_info['hour_zhi'], '?')})")
    
    # 纳音（如果有的话）
    try:
        from ganzhi import ganzhi_calculator
        year_nayin = ganzhi_calculator.get_nayin(cal_info['year_gan'], cal_info['year_zhi'])
        day_nayin = ganzhi_calculator.get_nayin(cal_info['day_gan'], cal_info['day_zhi'])
        print(f"   年纳音: {year_nayin}")
        print(f"   日纳音: {day_nayin}")
    except:
        pass
    
    print()

def display_alternative_methods(cal_info, palace_engine):
    """显示其他方法对比"""
    print("🔄 方法对比:")
    
    # 拆补法对比
    try:
        ju_number_chabu, is_yang_chabu = ju.get_ju_chabu(cal_info)
        print(f"   📐 拆补法: {ju.get_ju_name(ju_number_chabu, is_yang_chabu)}")
    except:
        print("   📐 拆补法: 计算失败")
    
    # 飞盘法
    try:
        fly_palace = palace_engine.fly_pan(cal_info)
        print(f"   🕊️  飞盘法: {fly_palace.get('ju_name', '飞盘')}")
    except:
        print("   🕊️  飞盘法: 计算失败")
    
    # 真太阳时信息
    try:
        from astronomical import astro_calculator
        from datetime import datetime
        import pytz
        
        current_time = datetime.now(pytz.timezone("Asia/Shanghai")).replace(tzinfo=None)
        true_solar_time = astro_calculator.calculate_true_solar_time(current_time, 116.4667)
        time_diff = (true_solar_time - current_time).total_seconds() / 60
        print(f"   ☀️  真太阳时差: {time_diff:.1f}分钟")
    except:
        print("   ☀️  真太阳时差: 计算失败")
    
    print()

def display_astronomical_details(dt):
    """显示天文算法详细信息"""
    print("🌌 天文算法详情:")
    
    try:
        from astronomical import AstronomicalCalculator
        astro = AstronomicalCalculator()
        
        # 儒略日
        julian_day = astro.julian_day(dt.replace(tzinfo=None))
        print(f"   📅 儒略日: {julian_day:.6f}")
        
        # 太阳黄经
        solar_longitude = astro.calculate_solar_longitude(julian_day)
        print(f"   ☀️  太阳黄经: {solar_longitude:.6f}°")
        
        # 时差
        equation_of_time = astro.calculate_equation_of_time(julian_day)
        print(f"   ⏰ 时差: {equation_of_time:.2f}分钟")
        
        # 真太阳时
        true_solar_time = astro.calculate_true_solar_time(dt.replace(tzinfo=None))
        time_diff = (true_solar_time - dt.replace(tzinfo=None)).total_seconds() / 60
        print(f"   🌅 真太阳时差: {time_diff:.1f}分钟")
        
    except Exception as e:
        print(f"   ❌ 天文算法计算失败: {str(e)}")
    
    print()

def display_zhishi_info(cal_info, nine_palace):
    """显示值使详细信息"""
    print("⭐ 值使详细信息:")
    
    # 获取时辰地支
    hour_zhi = cal_info.get('hour_zhi', '')
    
    # 根据时辰地支计算值使门
    zhishi_men = zhishi_calculator.calculate_zhishi_by_time(hour_zhi)
    
    # 在九宫盘中找到值使门所在的宫位
    zhishi_gong, zhishi_palace = zhishi_calculator.find_zhishi_gong(nine_palace, zhishi_men)
    
    print(f"   🕐 时辰地支: {hour_zhi}")
    print(f"   🚪 值使门: {zhishi_men}")
    
    if zhishi_gong and zhishi_palace:
        print(f"   🏛️  值使宫位: {zhishi_palace.get('gong_name', '')}({zhishi_gong}宫)")
        print(f"   📍 宫位方位: {zhishi_palace.get('position', '')}")
        print(f"   🌟 宫位组合: {zhishi_palace.get('gan', '')}{zhishi_men}{zhishi_palace.get('xing', '')}{zhishi_palace.get('shen', '')}")
        
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
        
        men_meaning = men_meanings.get(zhishi_men, "门意未明")
        print(f"   💡 门意: {men_meaning}")
        
        # 检查值符值使是否同宫
        zhi_fu_gong = None
        for gong_str, palace_info in nine_palace.get("palaces", {}).items():
            if palace_info.get("shen") == "直符":
                zhi_fu_gong = gong_str
                break
        
        if zhi_fu_gong == zhishi_gong:
            print(f"   🎯 特殊格局: 值符值使同宫，主事顺利通达")
        else:
            print(f"   📊 宫位关系: 值符在{zhi_fu_gong}宫，值使在{zhishi_gong}宫")
    else:
        print(f"   ⚠️  警告: 在当前九宫盘中未找到值使门 {zhishi_men}")
    
    print()

def qimen_custom_time(time_str):
    """指定时间奇门排盘 - 简化版本"""
    print(f"🎯 奇门遁甲排盘: {time_str}")
    print("=" * 50)
    
    try:
        # 解析时间
        if isinstance(time_str, str):
            from dateutil import parser
            dt = parser.parse(time_str)
            # 如果没有时区信息，假设为上海时间
            if dt.tzinfo is None:
                shanghai_tz = pytz.timezone("Asia/Shanghai")
                dt = shanghai_tz.localize(dt)
        
        # 使用核心计算函数
        cal_info, ju_number, is_yang, nine_palace, analysis, palace_engine = _core_qimen_calculation(dt)
        
        # 简化显示 - 只显示基本信息
        display_calendar_info(cal_info)
        display_ju_info(ju_number, is_yang, nine_palace, cal_info)
        display_zhishi_info(cal_info, nine_palace)
        display_nine_palace(nine_palace)
        display_analysis(analysis)
        
        return cal_info, ju_number, is_yang, nine_palace, analysis
        
    except Exception as e:
        print(f"❌ 时间解析错误: {e}")
        print("📝 支持的时间格式:")
        print("   - '2025-01-01 10:30:00'")
        print("   - '2025-01-01T10:30'")
        print("   - '2025/1/1 10:30'")
        return None

def interactive_qimen():
    """交互式奇门系统"""
    print("🔮 奇门遁甲交互式系统")
    print("=" * 50)
    
    while True:
        print("\n📋 选择操作:")
        print("1. 当前时间排盘")
        print("2. 指定时间排盘")
        print("3. 退出")
        
        choice = input("\n请输入选项 (1-3): ").strip()
        
        if choice == '1':
            print()
            qimen_now()
        elif choice == '2':
            time_input = input("\n请输入时间 (如: 2025-01-01 10:30): ").strip()
            if time_input:
                print()
                qimen_custom_time(time_input)
        elif choice == '3':
            print("\n👋 再见！")
            break
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # 无参数，启动交互模式
        interactive_qimen()
    elif len(sys.argv) == 2:
        if sys.argv[1] in ["--help", "-h", "help"]:
            # 显示帮助信息
            print("📖 奇门遁甲排盘系统 使用方法:")
            print("   python3 qimen_only.py              # 交互模式")
            print("   python3 qimen_only.py now          # 当前时间排盘（完整功能）")
            print("   python3 qimen_only.py '2025-01-01 10:30'  # 指定时间排盘（简化版）")
            print("   python3 qimen_only.py --help       # 显示此帮助信息")
        elif sys.argv[1] == "now":
            # 当前时间排盘
            qimen_now()
        else:
            # 指定时间排盘
            qimen_custom_time(sys.argv[1])
    else:
        print("📖 使用方法:")
        print("   python3 qimen_only.py              # 交互模式")
        print("   python3 qimen_only.py now          # 当前时间排盘")
        print("   python3 qimen_only.py '2025-01-01 10:30'  # 指定时间排盘") 