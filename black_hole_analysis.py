#!/usr/bin/env python3
"""
黑洞质量数据分析
代入您的分形嵌套宇宙模型
"""

import numpy as np
import json

# =========================================================
# 已观测黑洞质量数据 (单位: 太阳质量 M_sun)
# =========================================================

OBSERVED_BLACK_HOLES = {
    # 恒星级黑洞 (Stellar-mass)
    "stellar_mass": {
        "description": "恒星级黑洞 (X射线双星)",
        "mass_min": 3.0,
        "mass_max": 100.0,
        "typical": 10.0,
        "examples": [
            {"name": "Cygnus X-1", "mass": 21.0, "type": "stellar"},
            {"name": "LMC X-3", "mass": 10.0, "type": "stellar"},
            {"name": "GW150914", "mass": 36.0, "type": "binary merger"},
            {"name": "GW170104", "mass": 31.0, "type": "binary merger"},
            {"name": "GW151226", "mass": 14.0, "type": "binary merger"},
        ]
    },

    # 中等质量黑洞 (Intermediate-mass)
    "intermediate_mass": {
        "description": "中等质量黑洞",
        "mass_min": 100.0,
        "mass_max": 1e5,
        "typical": 1e3,
        "examples": [
            {"name": "HL Tau", "mass": 1e4, "type": "possible IMBH"},
            {"name": "NGC 4395", "mass": 1e5, "type": "SMBH candidate"},
        ]
    },

    # 超大质量黑洞 (Supermassive)
    "supermassive": {
        "description": "超大质量黑洞",
        "mass_min": 1e6,
        "mass_max": 1e10,
        "typical": 1e8,
        "examples": [
            {"name": "Sgr A*", "mass": 4.3e6, "type": "galactic center"},
            {"name": "M31 (Andromeda)", "mass": 1.4e8, "type": "galactic center"},
            {"name": "M87", "mass": 6.5e9, "type": "galactic center"},
            {"name": "NGC 1275", "mass": 8.4e8, "type": "galactic center"},
            {"name": "TON 618", "mass": 6.6e10, "type": "largest known"},
            {"name": "Phoenix A*", "mass": 1e10, "type": "cluster center"},
        ]
    },

    # 原始黑洞 (Primordial - 理论预测)
    "primordial": {
        "description": "原始黑洞 (尚未证实)",
        "mass_min": 1e-16,
        "mass_max": 100.0,
        "typical": 1e-8,
        "notes": "仅理论预测，未观测确认"
    }
}

# 物理常数
M_SUN = 1.989e30  # kg
M_PLANCK = 2.176e-8  # kg (普朗克质量)
L_PLANCK = 1.616e-35  # m (普朗克长度)
C = 3.0e8  # 光速 m/s
G = 6.674e-11  # 引力常数

def mass_ratio_analysis():
    """分析黑洞质量比率"""
    print("=" * 70)
    print("黑洞质量层级分析")
    print("=" * 70)

    categories = ["stellar_mass", "intermediate_mass", "supermassive"]

    for i, cat in enumerate(categories):
        data = OBSERVED_BLACK_HOLES[cat]
        print(f"\n【{data['description']}】")
        print(f"  质量范围: {data['mass_min']:.0e} - {data['mass_max']:.0e} M☉")
        print(f"  典型质量: {data['typical']:.0e} M☉")

        if i < len(categories) - 1:
            next_cat = categories[i + 1]
            next_data = OBSERVED_BLACK_HOLES[next_cat]
            ratio = data['mass_max'] / next_data['mass_min']
            print(f"  → {next_cat} 比率: {ratio:.0e}")

def fractal_model_analysis():
    """代入您的分形嵌套模型"""
    print("\n" + "=" * 70)
    print("分形嵌套宇宙模型代入")
    print("=" * 70)

    # 取观测数据的质量级别
    # 恒星质量: ~10 M_sun
    # IMBH: ~10^3 - 10^5 M_sun
    # SMBH: ~10^6 - 10^10 M_sun

    levels = {
        "n=0 (恒星质量)": 10.0,      # M☉
        "n=1 (IMBH?)": 1e4,          # M☉
        "n=2 (SMBH seed?)": 1e7,    # M☉
        "n=3 (SMBH)": 1e9,           # M☉
        "n=4 (最大黑洞)": 1e10,      # M☉
    }

    print("\n层级质量分布:")
    print("-" * 50)
    print(f"{'层级':<20} {'质量(M☉)':<15} {'log₁₀(M)':<10}")
    print("-" * 50)

    for name, mass in levels.items():
        print(f"{name:<20} {mass:<15.0e} {np.log10(mass):<10.1f}")

    # 计算层级间的质量比率
    print("\n层级间质量比率:")
    print("-" * 50)
    masses = list(levels.values())
    names = list(levels.keys())

    for i in range(len(masses) - 1):
        ratio = masses[i+1] / masses[i]
        print(f"{names[i]} → {names[i+1]}: 比率 = {ratio:.0e} = 10^{np.log10(ratio):.1f}")

    # 检验 λ 因子
    print(f"\n如果 M_n = M_0 · λ^n:")
    M_0 = masses[0]
    print(f"  M_0 (n=0) = {M_0:.0e} M☉")

    for n, mass in enumerate(masses[1:], 1):
        lambda_n = (mass / M_0) ** (1.0/n)
        print(f"  λ (n={n}): {lambda_n:.2e}")

def dark_matter_connection():
    """暗物质连接分析"""
    print("\n" + "=" * 70)
    print("暗物质层级分析")
    print("=" * 70)

    # 可观测宇宙总质量
    M_observable_universe = 1e54  # kg
    M_observable_universe_Msun = M_observable_universe / M_SUN

    # 可见物质 vs 暗物质比例
    # 宇宙学观测: 暗物质 ~ 27%, 可见物质 ~ 5%, 暗能量 ~ 68%
    visible_fraction = 0.05
    dm_fraction = 0.27

    M_visible = M_observable_universe * visible_fraction
    M_dm = M_observable_universe * dm_fraction

    print(f"\n可观测宇宙组成:")
    print(f"  总质量: {M_observable_universe:.0e} kg = {M_observable_universe_Msun:.0e} M☉")
    print(f"  可见物质: {M_visible:.0e} kg ({visible_fraction*100:.0f}%)")
    print(f"  暗物质: {M_dm:.0e} kg ({dm_fraction*100:.0f}%)")

    # 如果暗物质来自嵌套层级的贡献
    print(f"\n暗物质解释为嵌套层级贡献:")
    print(f"  如果 '不可见层级' 总质量 = 暗物质总质量")
    print(f"  M_invisible_layers = {M_dm:.0e} kg")

    # 检验分形自洽性
    # 假设每个层级质量递减因子为 λ
    # 总质量 = M_0 + λ*M_0 + λ²*M_0 + ... = M_0 / (1-λ)
    # 如果 M_visible = M_0, 则 M_total = M_visible / (1-λ) = M_observable_universe

    lambda_estimate = 1 - (M_visible / M_observable_universe)
    print(f"\n  如果 sum_n=0_to_inf M_0*lambda^n = M_total:")
    print(f"  则 1/(1-λ) = {M_observable_universe/M_visible:.0f}")
    print(f"  → λ ≈ {lambda_estimate:.2f}")
    print(f"  → 每上升一层，质量乘以 ≈ {1/lambda_estimate:.2f}")

def black_holes_distribution():
    """黑洞质量分布检验"""
    print("\n" + "=" * 70)
    print("黑洞质量分布 - 分形检验")
    print("=" * 70)

    # 观测: 黑洞质量似乎集中在某些区间
    # 恒星级: 3-100 M☉
    # IMBH: 100-10^5 M☉ (稀少)
    # SMBH: 10^6-10^10 M☉

    mass_ranges = [
        ("恒星级", 3, 100),
        ("IMBH候选", 100, 1e5),
        ("SMBH种子?", 1e6, 1e7),
        ("SMBH", 1e8, 1e10),
    ]

    print(f"\n{'类别':<15} {'质量范围(M☉)':<20} {'跨度(数量级)':<15}")
    print("-" * 50)

    for name, m_min, m_max in mass_ranges:
        span = np.log10(m_max) - np.log10(m_min)
        print(f"{name:<15} {m_min:.0e} - {m_max:.0e}   {span:<15.1f}")

    print(f"\n关键发现:")
    print(f"  • IMBH (10²-10⁵ M☉) 观测极少 ← '质量间隙'")
    print(f"  • SMBH种子 (10⁶-10⁷ M☉) 存在吗？")
    print(f"  • 最大黑洞 ~10¹⁰ M☉ 有上限吗？")

def planck_scale_nesting():
    """普朗克尺度嵌套分析"""
    print("\n" + "=" * 70)
    print("普朗克尺度嵌套分析")
    print("=" * 70)

    # 普朗克质量
    print(f"\n普朗克质量: {M_PLANCK:.0e} kg")

    # 太阳质量
    print(f"太阳质量: {M_SUN:.0e} kg")

    # 比率
    ratio_sun_planck = M_SUN / M_PLANCK
    print(f"太阳/普朗克质量比: {ratio_sun_planck:.0e}")

    # 从普朗克质量到太阳质量需要的层级数
    # 如果每层质量乘以 λ
    lambda_test = 1e3  # 假设每层质量增加1000倍

    n_steps = np.log10(ratio_sun_planck) / np.log10(lambda_test)
    print(f"\n如果每层质量增加 {lambda_test:.0e} 倍:")
    print(f"  从 Planck → Sun 需要 ≈ {n_steps:.1f} 层")

    # 从太阳质量到最大黑洞
    M_max = 6.6e10 * M_SUN  # TON 618
    ratio_max_sun = M_max / M_SUN

    n_more = np.log10(ratio_max_sun) / np.log10(lambda_test)
    print(f"  从 Sun → 最大黑洞 需要 ≈ {n_more:.1f} 层")
    print(f"  总计 ≈ {n_steps + n_more:.1f} 层")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║          黑洞观测数据 - 分形嵌套宇宙模型代入分析                   ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)

    mass_ratio_analysis()
    fractal_model_analysis()
    dark_matter_connection()
    black_holes_distribution()
    planck_scale_nesting()

    print("\n" + "=" * 70)
    print("分析结论")
    print("=" * 70)
    print("""
    【观测事实】
    1. 恒星级黑洞: 3-100 M☉ (丰富)
    2. 中等质量黑洞: 100-10⁵ M☉ (稀少 - 质量间隙)
    3. 超大质量黑洞: 10⁶-10¹⁰ M☉ (每个星系中心一个)

    【模型观察】
    1. 如果 λ ~ 10³-10⁴ (每层质量倍数):
       - Planck → Stellar mass: ~5-6 层
       - Stellar → SMBH: ~3-5 层
       - 总计: ~8-11 层

    2. 质量间隙 (10²-10⁵ M☉) 可能对应:
       - 嵌套层级间的"过渡区"
       - 或该层级物理过程导致质量损失

    3. 最大黑洞质量上限 (~10¹⁰ M☉):
       - 可能由宇宙年龄 + 喂养速率决定
       - 或分形嵌套的有限层级数决定
    """)

if __name__ == "__main__":
    main()