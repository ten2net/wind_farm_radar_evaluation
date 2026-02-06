"""
军用相控阵雷达波束成形及实时仿真工具
使用Streamlit和Plotly构建
支持多款经典军用雷达型号仿真
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from scipy import signal
from scipy.linalg import inv
import json

# --- 军用雷达型号数据库 ---
RADAR_DATABASE = {
    "自定义配置": {
        "band": "Ku",
        "freq_ghz": 14.0,
        "freq_range": "12-18 GHz",
        "array_size": "32×32",
        "N": 32,
        "M": 32,
        "element_spacing": 0.5,
        "description": "用户自定义参数配置",
        "country": "通用",
        "platform": "地面/舰载/机载"
    },
    "AN/SPY-1 宙斯盾": {
        "band": "S",
        "freq_ghz": 3.0,
        "freq_range": "2-4 GHz",
        "array_size": "约4350单元",
        "N": 66,
        "M": 66,
        "element_spacing": 0.55,
        "description": "美国海军宙斯盾系统核心雷达，固定四面阵",
        "country": "美国",
        "platform": "提康德罗加级巡洋舰/阿利伯克级驱逐舰"
    },
    "AN/MPQ-53 爱国者": {
        "band": "C",
        "freq_ghz": 5.6,
        "freq_range": "4-8 GHz",
        "array_size": "约5000单元",
        "N": 71,
        "M": 71,
        "element_spacing": 0.55,
        "description": "MIM-104爱国者防空导弹系统火控雷达",
        "country": "美国",
        "platform": "陆基防空导弹系统"
    },
    "AN/APG-77 (F-22)": {
        "band": "X",
        "freq_ghz": 9.5,
        "freq_range": "8-12 GHz",
        "array_size": "约1500单元",
        "N": 39,
        "M": 39,
        "element_spacing": 0.55,
        "description": "F-22猛禽战斗机有源相控阵雷达，首款机载AESA",
        "country": "美国",
        "platform": "F-22 Raptor"
    },
    "AN/APG-81 (F-35)": {
        "band": "X",
        "freq_ghz": 9.6,
        "freq_range": "8-12 GHz",
        "array_size": "约1200单元",
        "N": 35,
        "M": 35,
        "element_spacing": 0.55,
        "description": "F-35闪电II联合攻击战斗机AESA雷达",
        "country": "美国",
        "platform": "F-35 Lightning II"
    },
    "AN/APG-79 (F/A-18E/F)": {
        "band": "X",
        "freq_ghz": 9.4,
        "freq_range": "8-12 GHz",
        "array_size": "约1000单元",
        "N": 32,
        "M": 32,
        "element_spacing": 0.55,
        "description": "超级大黄蜂升级用AESA雷达",
        "country": "美国",
        "platform": "F/A-18E/F Super Hornet"
    },
    "RBE2 (阵风)": {
        "band": "X",
        "freq_ghz": 10.0,
        "freq_range": "8-12 GHz",
        "array_size": "约1000单元",
        "N": 32,
        "M": 32,
        "element_spacing": 0.55,
        "description": "法国阵风战斗机有源相控阵雷达",
        "country": "法国",
        "platform": "Rafale战斗机"
    },
    "Captor-E (台风)": {
        "band": "X",
        "freq_ghz": 9.5,
        "freq_range": "8-12 GHz",
        "array_size": "约1400单元",
        "N": 38,
        "M": 38,
        "element_spacing": 0.55,
        "description": "欧洲台风战斗机AESA雷达",
        "country": "欧洲",
        "platform": "Typhoon战斗机"
    },
    "N036 Byelka (Su-57)": {
        "band": "X",
        "freq_ghz": 10.0,
        "freq_range": "8-12 GHz",
        "array_size": "约1500单元",
        "N": 39,
        "M": 39,
        "element_spacing": 0.55,
        "description": "苏-57战斗机N036松鼠雷达，五阵面AESA",
        "country": "俄罗斯",
        "platform": "Su-57 Felon"
    },
    "346型 海之星": {
        "band": "S/C",
        "freq_ghz": 3.5,
        "freq_range": "2-4 GHz",
        "array_size": "约4000单元",
        "N": 64,
        "M": 64,
        "element_spacing": 0.55,
        "description": "中国052C/D驱逐舰舰载相控阵雷达",
        "country": "中国",
        "platform": "052C/D型驱逐舰"
    },
    "KLJ-7A 枭龙": {
        "band": "X",
        "freq_ghz": 10.0,
        "freq_range": "8-12 GHz",
        "array_size": "约800单元",
        "N": 28,
        "M": 28,
        "element_spacing": 0.55,
        "description": "中巴JF-17 Block III战斗机AESA雷达",
        "country": "中国/巴基斯坦",
        "platform": "JF-17 Thunder Block III"
    },
    "JY-27A 警戒": {
        "band": "VHF/UHF",
        "freq_ghz": 0.25,
        "freq_range": "100-400 MHz",
        "array_size": "米波大型阵列",
        "N": 24,
        "M": 24,
        "element_spacing": 0.6,
        "description": "中国米波反隐身警戒雷达，对隐身目标有良好探测能力",
        "country": "中国",
        "platform": "陆基远程警戒"
    },
    "EL/M-2075 费尔康": {
        "band": "L",
        "freq_ghz": 1.3,
        "freq_range": "1-2 GHz",
        "array_size": "相控阵预警雷达",
        "N": 40,
        "M": 20,
        "element_spacing": 0.55,
        "description": "以色列ELTA相控阵预警雷达，共形阵列",
        "country": "以色列",
        "platform": "预警机"
    }
}

# 频段参数定义
BAND_PARAMETERS = {
    "VHF": {"freq_min": 0.03, "freq_max": 0.3, "default": 0.15, "wavelength_m": 2.0},
    "UHF": {"freq_min": 0.3, "freq_max": 1.0, "default": 0.5, "wavelength_m": 0.6},
    "L": {"freq_min": 1.0, "freq_max": 2.0, "default": 1.5, "wavelength_m": 0.2},
    "S": {"freq_min": 2.0, "freq_max": 4.0, "default": 3.0, "wavelength_m": 0.1},
    "C": {"freq_min": 4.0, "freq_max": 8.0, "default": 5.5, "wavelength_m": 0.055},
    "X": {"freq_min": 8.0, "freq_max": 12.0, "default": 10.0, "wavelength_m": 0.03},
    "Ku": {"freq_min": 12.0, "freq_max": 18.0, "default": 14.0, "wavelength_m": 0.021},
    "K": {"freq_min": 18.0, "freq_max": 27.0, "default": 22.0, "wavelength_m": 0.014},
    "Ka": {"freq_min": 27.0, "freq_max": 40.0, "default": 33.0, "wavelength_m": 0.009}
}

# --- 主题配置 ---
THEMES = {
    "科技蓝 (Tech Blue)": {
        "plotly_template": "plotly_dark",
        "primary_color": "#00D4FF",
        "secondary_color": "#0099CC",
        "accent_color": "#00FF88",
        "warning_color": "#FFB800",
        "danger_color": "#FF4757",
        "background_color": "#0A1929",
        "paper_color": "#132F4C",
        "grid_color": "rgba(0, 212, 255, 0.1)",
        "text_color": "#E0F7FF",
        "secondary_text": "#8BADC4",
        "gradient_start": "#00D4FF",
        "gradient_end": "#0099CC",
        "fill_alpha": 0.15,
        "line_width": 3,
        "marker_size": 12,
        "colorscale": "Blues",
        "heatmap_colorscale": "YlGnBu",
        "surface_colorscale": "Blues",
        "chart_colors": ["#00D4FF", "#00FF88", "#FFB800", "#FF6B6B", "#A78BFA", "#4ECDC4"],
        "description": "现代科技蓝配色，冷色调，适合雷达监控场景"
    },
    "暗色经典 (Dark Classic)": {
        "plotly_template": "plotly_dark",
        "primary_color": "#636EFA",
        "secondary_color": "#EF553B",
        "accent_color": "#00CC96",
        "warning_color": "#FFA15A",
        "danger_color": "#FF6692",
        "background_color": "#1a1a2e",
        "paper_color": "#16213e",
        "grid_color": "rgba(255, 255, 255, 0.1)",
        "text_color": "#FFFFFF",
        "secondary_text": "#A0A0A0",
        "gradient_start": "#636EFA",
        "gradient_end": "#EF553B",
        "fill_alpha": 0.1,
        "line_width": 2,
        "marker_size": 10,
        "colorscale": "Viridis",
        "heatmap_colorscale": "RdYlBu",
        "surface_colorscale": "Jet",
        "chart_colors": ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"],
        "description": "经典暗色主题，高对比度，适合长时间使用"
    },
    "明亮专业 (Light Pro)": {
        "plotly_template": "plotly_white",
        "primary_color": "#0066CC",
        "secondary_color": "#0052A3",
        "accent_color": "#00AA44",
        "warning_color": "#CC7700",
        "danger_color": "#CC3333",
        "background_color": "#FFFFFF",
        "paper_color": "#F8FAFC",
        "grid_color": "rgba(0, 0, 0, 0.05)",
        "text_color": "#1a1a2e",
        "secondary_text": "#4a5568",
        "gradient_start": "#0066CC",
        "gradient_end": "#0052A3",
        "fill_alpha": 0.2,
        "line_width": 2.5,
        "marker_size": 10,
        "colorscale": "Blues",
        "heatmap_colorscale": "RdYlBu",
        "surface_colorscale": "Viridis",
        "chart_colors": ["#0066CC", "#00AA44", "#CC7700", "#CC3333", "#663399", "#008B8B"],
        "description": "明亮专业主题，清晰易读，适合演示和报告"
    },
    "军事绿 (Military Green)": {
        "plotly_template": "plotly_dark",
        "primary_color": "#39FF14",
        "secondary_color": "#00C851",
        "accent_color": "#FFD700",
        "warning_color": "#FFA500",
        "danger_color": "#FF4444",
        "background_color": "#0d1f0d",
        "paper_color": "#1a331a",
        "grid_color": "rgba(57, 255, 20, 0.1)",
        "text_color": "#E8F5E9",
        "secondary_text": "#81C784",
        "gradient_start": "#39FF14",
        "gradient_end": "#00C851",
        "fill_alpha": 0.15,
        "line_width": 3,
        "marker_size": 12,
        "colorscale": "Greens",
        "heatmap_colorscale": "YlGn",
        "surface_colorscale": "Greens",
        "chart_colors": ["#39FF14", "#00C851", "#FFD700", "#FFA500", "#FF4444", "#00FFFF"],
        "description": "军事风格绿色主题，荧光绿配色，战术监控风格"
    },
    "赛博朋克 (Cyberpunk)": {
        "plotly_template": "plotly_dark",
        "primary_color": "#FF00FF",
        "secondary_color": "#00FFFF",
        "accent_color": "#FFFF00",
        "warning_color": "#FF6600",
        "danger_color": "#FF0066",
        "background_color": "#0a0a0f",
        "paper_color": "#1a0a2e",
        "grid_color": "rgba(255, 0, 255, 0.1)",
        "text_color": "#FFE0FF",
        "secondary_text": "#B080B0",
        "gradient_start": "#FF00FF",
        "gradient_end": "#00FFFF",
        "fill_alpha": 0.2,
        "line_width": 3,
        "marker_size": 12,
        "colorscale": "Plasma",
        "heatmap_colorscale": "Plasma",
        "surface_colorscale": "Plasma",
        "chart_colors": ["#FF00FF", "#00FFFF", "#FFFF00", "#FF6600", "#FF0066", "#00FF00"],
        "description": "赛博朋克风格，霓虹色彩，未来科技感"
    }
}

# --- 页面配置 ---
st.set_page_config(
    page_title="军用相控阵雷达全链路仿真平台",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 主题选择 (必须在页面渲染前设置) ---
def get_theme():
    """获取当前主题配置"""
    theme_name = st.session_state.get('selected_theme', '科技蓝 (Tech Blue)')
    return THEMES.get(theme_name, THEMES['科技蓝 (Tech Blue)'])

# 侧边栏主题选择器
with st.sidebar:
    st.header("🎨 界面主题")
    selected_theme_name = st.selectbox(
        "选择主题配色",
        list(THEMES.keys()),
        index=0,
        key='selected_theme',
        help="选择不同的界面配色方案"
    )
    theme = get_theme()
    
    with st.expander("📋 主题说明"):
        st.markdown(f"**{selected_theme_name}**: {theme['description']}")
        st.markdown(f"- 主色: `{theme['primary_color']}`")
        st.markdown(f"- 强调色: `{theme['accent_color']}`")
    
    st.divider()

# --- 标题和描述 ---
st.title("🎯 军用相控阵雷达全链路仿真与效能评估平台")
st.markdown("这是一个**专业级**军用相控阵雷达系统级仿真平台，覆盖从天线阵列设计到信号处理的全链路仿真。")

# 使用可折叠组件组织系统特点和用途
col1, col2 = st.columns(2)

with col1:
    with st.expander("📋 核心能力", expanded=False):
        st.markdown("""
- 🛩️ **多型号雷达库**  
  支持宙斯盾、F-22/F-35、苏-57、346型等12款经典雷达

- 📡 **阵列设计与波束控制**  
  阵元配置、加权优化、自适应波束成形、3D方向图可视化

- 🎯 **目标探测与跟踪**  
  多目标模拟、RCS建模、距离-多普勒分析、跟踪滤波

- 🛡️ **电子对抗与干扰抑制**  
  干扰机建模、MVDR自适应零陷、抗干扰效能评估

- 📊 **信号处理与检测**  
  LFM脉冲压缩、匹配滤波、信噪比分析、检测概率计算

- ⚡ **系统级仿真**  
  雷达方程、作战效能评估、扫描策略优化、实时动态仿真
""")

with col2:
    with st.expander("🎯 主要用途", expanded=False):
        st.markdown("""
- 🎓 **教学演示**  
  相控阵雷达原理可视化、波束扫描动态演示、阵列信号处理算法教学

- 🔬 **科研分析**  
  波束成形算法研究、抗干扰策略验证、新型雷达体制探索

- 🛠️ **工程设计**  
  雷达参数优化、阵列配置选型、作战性能预估、系统方案验证

- 📈 **效能评估**  
  探测性能分析、电子对抗效果评估、作战场景仿真
""")

st.divider()

# --- 雷达型号选择 ---
st.sidebar.header("🛩️ 雷达型号选择")
selected_radar = st.sidebar.selectbox(
    "选择雷达型号",
    list(RADAR_DATABASE.keys()),
    index=0,
    help="选择预定义的军用雷达型号或自定义配置"
)

# 获取选中雷达的参数
radar_config = RADAR_DATABASE[selected_radar]

# 显示雷达信息
with st.sidebar.expander("📋 雷达详情", expanded=True):
    st.markdown(f"**型号**: {selected_radar}")
    st.markdown(f"**频段**: {radar_config['band']} ({radar_config['freq_range']})")
    st.markdown(f"**阵元数**: {radar_config['array_size']}")
    st.markdown(f"**载台**: {radar_config['platform']}")
    st.markdown(f"**国家**: {radar_config['country']}")
    st.markdown(f"**简介**: {radar_config['description']}")

# --- 数据类定义 ---
@dataclass
class Target:
    """目标类"""
    theta: float  # 俯仰角
    phi: float    # 方位角
    rcs: float    # 雷达截面积
    range_km: float  # 距离
    velocity: float = 0.0  # 径向速度 m/s
    
@dataclass
class Jammer:
    """干扰机类"""
    theta: float
    phi: float
    power: float  # 干扰功率 dBm
    bandwidth: float  # 干扰带宽 MHz

# --- 缓存装饰器以提高性能 ---
@st.cache_data
def calculate_wavelength_cached(frequency_ghz: float) -> float:
    """计算波长"""
    c = 3e8  # 光速 m/s
    return c / (frequency_ghz * 1e9)

@st.cache_data
def generate_array_positions_cached(N: int, M: int, d: float, wavelength: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """生成阵列位置"""
    x = np.arange(-(N-1)/2, (N-1)/2 + 1) * d * wavelength
    y = np.arange(-(M-1)/2, (M-1)/2 + 1) * d * wavelength
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)
    return X, Y, Z

@st.cache_data
def calculate_phase_shift_cached(theta_deg: float, phi_deg: float, X: np.ndarray, Y: np.ndarray, 
                                 Z: np.ndarray, wavelength: float) -> np.ndarray:
    """计算相位偏移"""
    theta = np.radians(theta_deg)
    phi = np.radians(phi_deg)
    
    k = 2 * np.pi / wavelength
    u = np.sin(theta) * np.cos(phi)
    v = np.sin(theta) * np.sin(phi)
    w = np.cos(theta)
    
    phase = k * (u * X + v * Y + w * Z)
    return phase

@st.cache_data
def calculate_array_factor_cached(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, phase_shift: np.ndarray,
                                 theta_scan: float, phi_scan: float, wavelength: float) -> float:
    """计算阵列因子（归一化）
    
    返回归一化的阵列因子 (0-1范围)
    """
    theta = np.radians(theta_scan)
    phi = np.radians(phi_scan)
    
    k = 2 * np.pi / wavelength
    u_obs = np.sin(theta) * np.cos(phi)
    v_obs = np.sin(theta) * np.sin(phi)
    w_obs = np.cos(theta)
    
    N, M = X.shape
    
    # 确保phase_shift是实数
    phase_shift_real = np.real(phase_shift)
    
    spatial_phase = k * (u_obs * X + v_obs * Y + w_obs * Z)
    total_phase = spatial_phase - phase_shift_real
    array_factor = np.sum(np.exp(1j * total_phase))
    
    # 归一化到0-1范围
    return np.abs(array_factor) / (N * M)

def calculate_radiation_pattern_vectorized(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                                           phase_shift: np.ndarray, wavelength: float, 
                                           theta_range: np.ndarray, phi_fixed: float = 0) -> np.ndarray:
    """向量化计算辐射方向图 - 性能优化版
    
    参数:
        X, Y, Z: 阵元位置坐标 (N, M)
        phase_shift: 波束指向所需的相位补偿 (N, M)，实数数组
        wavelength: 波长
        theta_range: 观察角度范围
        phi_fixed: 固定的方位角
    
    返回:
        方向图 (dB) - 相对于各向同性辐射的增益
    """
    k = 2 * np.pi / wavelength
    theta_rad = np.radians(theta_range)
    phi_rad = np.radians(phi_fixed)
    
    u_obs = np.sin(theta_rad) * np.cos(phi_rad)
    v_obs = np.sin(theta_rad) * np.sin(phi_rad)
    w_obs = np.cos(theta_rad)
    
    # 向量化计算
    N, M = X.shape
    n_elements = N * M
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = Z.flatten()
    phase_shift_flat = np.real(phase_shift).flatten()  # 确保是实数
    
    # 计算所有角度的空间相位 [n_angles, n_elements]
    # spatial_phase: 观察方向带来的空间相位
    spatial_phase = k * (np.outer(u_obs, X_flat) + np.outer(v_obs, Y_flat) + np.outer(w_obs, Z_flat))
    
    # total_phase: 总相位差 = 观察方向相位 - 波束指向补偿相位
    total_phase = spatial_phase - phase_shift_flat
    
    # 计算阵列因子
    # 不归一化，直接计算合成幅度，然后转换为增益
    array_factor = np.abs(np.sum(np.exp(1j * total_phase), axis=1))
    
    # 计算增益 (dBi) = 20*log10(array_factor) - 10*log10(n_elements)
    # 这样最大增益约为 10*log10(n_elements) dBi
    pattern_db = 20 * np.log10(np.maximum(array_factor, 1e-10)) - 10 * np.log10(n_elements)
    
    return pattern_db

@st.cache_data
def calculate_radiation_pattern_cached(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, phase_shift: np.ndarray,
                                      wavelength: float, theta_range: np.ndarray, phi_fixed: float = 0) -> np.ndarray:
    """计算辐射方向图 - 使用向量化版本"""
    return calculate_radiation_pattern_vectorized(X, Y, Z, phase_shift, wavelength, theta_range, phi_fixed)

# --- 新增：自适应波束成形 ---
def calculate_mvdr_weights(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, wavelength: float,
                           target_theta: float, target_phi: float, 
                           jammers: List[Jammer] = None, snr_db: float = 20) -> np.ndarray:
    """
    计算MVDR (Minimum Variance Distortionless Response) 波束成形权重
    
    参数:
        X, Y, Z: 阵元位置
        wavelength: 波长
        target_theta, target_phi: 目标方向
        jammers: 干扰机列表
        snr_db: 信噪比(dB)
    """
    N, M = X.shape
    n_elements = N * M
    
    # 导向矢量
    k = 2 * np.pi / wavelength
    theta_t = np.radians(target_theta)
    phi_t = np.radians(target_phi)
    u_t = np.sin(theta_t) * np.cos(phi_t)
    v_t = np.sin(theta_t) * np.sin(phi_t)
    w_t = np.cos(theta_t)
    
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = Z.flatten()
    
    steering_vector = np.exp(1j * k * (u_t * X_flat + v_t * Y_flat + w_t * Z_flat))
    
    # 构建协方差矩阵
    R = np.eye(n_elements, dtype=complex) * (10**(-snr_db/10))  # 噪声协方差
    
    if jammers:
        for jammer in jammers:
            theta_j = np.radians(jammer.theta)
            phi_j = np.radians(jammer.phi)
            u_j = np.sin(theta_j) * np.cos(phi_j)
            v_j = np.sin(theta_j) * np.sin(phi_j)
            w_j = np.cos(theta_j)
            
            jammer_steering = np.exp(1j * k * (u_j * X_flat + v_j * Y_flat + w_j * Z_flat))
            jammer_power = 10**((jammer.power + 30)/10)  # 转换为线性功率
            R += jammer_power * np.outer(jammer_steering, jammer_steering.conj())
    
    # MVDR权重: w = R^-1 * a / (a^H * R^-1 * a)
    R_inv = inv(R + 0.001 * np.eye(n_elements))  # 对角加载保证可逆
    denominator = steering_vector.conj().T @ R_inv @ steering_vector
    weights = (R_inv @ steering_vector) / denominator
    
    return weights.reshape(N, M)

# --- 新增：3D波束方向图 ---
def calculate_3d_pattern(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, phase_shift: np.ndarray,
                        wavelength: float, theta_range: np.ndarray, phi_range: np.ndarray) -> np.ndarray:
    """计算3D辐射方向图"""
    k = 2 * np.pi / wavelength
    N, M = X.shape
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = Z.flatten()
    phase_shift_flat = phase_shift.flatten()
    
    theta_grid, phi_grid = np.meshgrid(np.radians(theta_range), np.radians(phi_range))
    
    u = np.sin(theta_grid) * np.cos(phi_grid)
    v = np.sin(theta_grid) * np.sin(phi_grid)
    w = np.cos(theta_grid)
    
    pattern = np.zeros_like(theta_grid)
    
    for i in range(len(phi_range)):
        for j in range(len(theta_range)):
            spatial_phase = k * (u[i,j] * X_flat + v[i,j] * Y_flat + w[i,j] * Z_flat)
            total_phase = spatial_phase - phase_shift_flat
            pattern[i, j] = np.abs(np.sum(np.exp(1j * total_phase))) / (N * M)
    
    return 20 * np.log10(pattern + 1e-10)

# --- 新增：脉冲压缩 (LFM信号) ---
def generate_lfm_pulse(bandwidth: float, pulse_width: float, fs: float, target_delays: List[float], 
                      target_amplitudes: List[float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成LFM脉冲并模拟回波
    
    参数:
        bandwidth: 带宽 (Hz)
        pulse_width: 脉宽 (s)
        fs: 采样率 (Hz)
        target_delays: 目标时延列表 (s)
        target_amplitudes: 目标幅度列表
    """
    t = np.arange(0, pulse_width, 1/fs)
    k = bandwidth / pulse_width  # 调频斜率
    
    # 发射信号
    tx_signal = np.exp(1j * np.pi * k * t**2)
    
    # 接收信号 (多个目标的回波叠加)
    rx_signal = np.zeros(len(t) + int(max(target_delays) * fs) + 100, dtype=complex)
    
    for delay, amp in zip(target_delays, target_amplitudes):
        delay_samples = int(delay * fs)
        if delay_samples + len(t) < len(rx_signal):
            rx_signal[delay_samples:delay_samples + len(t)] += amp * tx_signal
    
    # 脉冲压缩 (匹配滤波)
    matched_filter = np.conj(tx_signal[::-1])
    compressed = signal.convolve(rx_signal[:len(t)*2], matched_filter, mode='same')
    
    return tx_signal, compressed

# --- 新增：阵列误差模拟 ---
def apply_array_errors(weights: np.ndarray, amp_error_std: float = 0.0, 
                      phase_error_std: float = 0.0, element_failure_rate: float = 0.0) -> np.ndarray:
    """
    应用阵列误差
    
    参数:
        weights: 原始权重
        amp_error_std: 幅度误差标准差 (dB)
        phase_error_std: 相位误差标准差 (度)
        element_failure_rate: 阵元失效比例
    """
    N, M = weights.shape
    
    # 幅度误差
    if amp_error_std > 0:
        amp_error = 10**(np.random.normal(0, amp_error_std, (N, M)) / 20)
        weights = weights * amp_error
    
    # 相位误差
    if phase_error_std > 0:
        phase_error = np.exp(1j * np.radians(np.random.normal(0, phase_error_std, (N, M))))
        weights = weights * phase_error
    
    # 阵元失效
    if element_failure_rate > 0:
        failure_mask = np.random.random((N, M)) > element_failure_rate
        weights = weights * failure_mask
    
    return weights

# --- 新增：参数预设 ---
PRESETS = {
    "标准搜索": {"theta": 0, "phi": 0, "weighting": "均匀", "sidelobe": -30},
    "低副瓣": {"theta": 0, "phi": 0, "weighting": "切比雪夫", "sidelobe": -40},
    "低旁瓣泰勒": {"theta": 0, "phi": 0, "weighting": "泰勒", "sidelobe": -35},
    "大角度扫描": {"theta": 45, "phi": 30, "weighting": "切比雪夫", "sidelobe": -30},
    "抗干扰模式": {"theta": 0, "phi": 0, "weighting": "均匀", "sidelobe": -30, "adaptive": True},
}

# --- 分析函数 ---
def analyze_pattern(pattern: np.ndarray, angles: np.ndarray) -> Tuple[float, float, List[Tuple[float, float]]]:
    """分析方向图特性"""
    mainlobe_idx = np.argmax(pattern)
    mainlobe_gain = pattern[mainlobe_idx]
    mainlobe_angle = angles[mainlobe_idx]
    
    # 查找副瓣
    sidelobes = []
    for i in range(1, len(pattern)-1):
        if pattern[i] > pattern[i-1] and pattern[i] > pattern[i+1] and i != mainlobe_idx:
            sidelobes.append((angles[i], pattern[i]))
    
    sidelobes.sort(key=lambda x: x[1], reverse=True)
    return mainlobe_gain, mainlobe_angle, sidelobes[:3]

def calculate_scan_loss(theta_deg: float, phi_deg: float, d: float, wavelength: float) -> float:
    """计算扫描损失
    
    波束偏离法向时产生的增益损失
    法向(theta=0, phi=0): 0 dB 损失
    扫描角度越大，损失越大
    """
    theta_rad = np.radians(theta_deg)
    phi_rad = np.radians(phi_deg)
    
    # 计算扫描角度（与法向的夹角）
    # cos(scan_angle) = cos(theta) 当phi任意时
    scan_angle = theta_rad  # 简化为俯仰角
    
    # 使用余弦损失模型: L = 20*log10(cos(theta_scan))
    # 确保cos值不小于一个很小的数，避免log(0)
    cos_scan = np.cos(scan_angle)
    if cos_scan < 0.01:  # 限制最大损失约-40dB
        cos_scan = 0.01
    
    scan_loss = 20 * np.log10(cos_scan)
    
    # 确保损失为负值或零
    return min(0.0, float(scan_loss))

# --- 权重函数 ---
def calculate_weighting(window_type: str, N: int, M: int, sidelobe_level: float = -30) -> np.ndarray:
    """计算加权系数"""
    if window_type == "均匀":
        return np.ones((N, M))
    
    elif window_type == "切比雪夫":
        # 切比雪夫权重近似计算
        n = np.arange(N)
        m = np.arange(M)
        Wx = np.cos(np.pi * (2*n - N + 1) / (2*N))
        Wy = np.cos(np.pi * (2*m - M + 1) / (2*M))
        Wx, Wy = np.meshgrid(Wx, Wy)
        
        # 调整副瓣电平
        R = 10**(sidelobe_level/20)
        w = R + (1 - R) * Wx * Wy
        return w / np.max(w)
    
    elif window_type == "泰勒":
        # 泰勒权重近似
        nx = np.linspace(-1, 1, N)
        ny = np.linspace(-1, 1, M)
        nx, ny = np.meshgrid(nx, ny)
        r = np.sqrt(nx**2 + ny**2)
        
        # 泰勒分布参数
        n_bar = 4
        sigma = 1.5
        w = np.zeros_like(r)
        mask = r <= 1
        w[mask] = 1 + 0.5 * np.cos(np.pi * r[mask]) - 0.5 * np.cos(3 * np.pi * r[mask])
        w[~mask] = 0
        
        return w
    
    elif window_type == "汉明":
        # 汉明窗
        nx = np.arange(N)
        my = np.arange(M)
        Wx = 0.54 - 0.46 * np.cos(2 * np.pi * nx / (N - 1))
        Wy = 0.54 - 0.46 * np.cos(2 * np.pi * my / (M - 1))
        Wx, Wy = np.meshgrid(Wx, Wy)
        return Wx * Wy
    
    elif window_type == "汉宁":
        # 汉宁窗
        nx = np.arange(N)
        my = np.arange(M)
        Wx = 0.5 - 0.5 * np.cos(2 * np.pi * nx / (N - 1))
        Wy = 0.5 - 0.5 * np.cos(2 * np.pi * my / (M - 1))
        Wx, Wy = np.meshgrid(Wx, Wy)
        return Wx * Wy
    
    elif window_type == "布莱克曼":
        # 布莱克曼窗
        nx = np.arange(N)
        my = np.arange(M)
        Wx = 0.42 - 0.5 * np.cos(2 * np.pi * nx / (N - 1)) + 0.08 * np.cos(4 * np.pi * nx / (N - 1))
        Wy = 0.42 - 0.5 * np.cos(2 * np.pi * my / (M - 1)) + 0.08 * np.cos(4 * np.pi * my / (M - 1))
        Wx, Wy = np.meshgrid(Wx, Wy)
        return Wx * Wy
    
    return np.ones((N, M))

# --- 新增：导出功能 ---
def export_configuration(config: Dict) -> str:
    """导出配置为JSON"""
    return json.dumps(config, indent=2, ensure_ascii=False)

def create_download_link(data: str, filename: str) -> str:
    """创建下载链接"""
    import base64
    b64 = base64.b64encode(data.encode()).decode()
    return f'<a href="data:file/json;base64,{b64}" download="{filename}">点击下载 {filename}</a>'

# --- 主题颜色工具函数 ---
def get_theme_color(color_type: str, alpha: float = 1.0) -> str:
    """获取主题颜色"""
    theme = get_theme()
    color = theme.get(color_type, theme['primary_color'])
    if alpha < 1.0:
        # 转换hex为rgba
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {alpha})"
    return color

def get_chart_color(index: int) -> str:
    """获取图表颜色序列"""
    theme = get_theme()
    colors = theme['chart_colors']
    return colors[index % len(colors)]

def apply_theme_to_fig(fig, is_3d: bool = False):
    """应用主题到Plotly图表"""
    theme = get_theme()
    fig.update_layout(
        template=theme['plotly_template'],
        paper_bgcolor=theme['paper_color'],
        plot_bgcolor=theme['background_color'] if not is_3d else None,
        font=dict(color=theme['text_color']),
        title_font=dict(color=theme['text_color']),
        legend_font=dict(color=theme['text_color']),
    )
    if not is_3d:
        fig.update_xaxes(
            gridcolor=theme['grid_color'],
            zerolinecolor=theme['grid_color'],
            tickfont=dict(color=theme['secondary_text']),
            title_font=dict(color=theme['text_color'])
        )
        fig.update_yaxes(
            gridcolor=theme['grid_color'],
            zerolinecolor=theme['grid_color'],
            tickfont=dict(color=theme['secondary_text']),
            title_font=dict(color=theme['text_color'])
        )
    return fig

# --- 侧边栏控制参数 ---
st.sidebar.header("🎛️ 参数设置")

# 根据选择的雷达型号获取频段参数
default_freq = radar_config['freq_ghz']
band_name = radar_config['band'].split('/')[0]  # 取第一个频段
band_params = BAND_PARAMETERS.get(band_name, BAND_PARAMETERS['X'])

# 新增：预设配置
st.sidebar.subheader("📋 快速预设")
preset = st.sidebar.selectbox(
    "选择预设配置",
    list(PRESETS.keys()),
    index=0,
    help="快速加载常用配置"
)
if st.sidebar.button("应用预设"):
    preset_config = PRESETS[preset]
    st.session_state['preset_theta'] = preset_config.get("theta", 0)
    st.session_state['preset_phi'] = preset_config.get("phi", 0)
    st.session_state['preset_weighting'] = preset_config.get("weighting", "均匀")
    st.session_state['preset_sidelobe'] = preset_config.get("sidelobe", -30)
    st.rerun()

st.sidebar.divider()

# 动态频率范围
st.sidebar.subheader("📡 频率参数")
freq_col1, freq_col2 = st.sidebar.columns(2)
with freq_col1:
    st.markdown(f"**频段**: {radar_config['band']}")
    st.markdown(f"**默认**: {default_freq} GHz")
with freq_col2:
    use_custom_freq = st.checkbox("自定义频率", value=False)

if use_custom_freq:
    frequency = st.sidebar.slider(
        "工作频率 (GHz)",
        min_value=float(band_params['freq_min']),
        max_value=float(band_params['freq_max']),
        value=float(default_freq),
        step=0.1,
        help=f"{radar_config['band']}波段频率范围"
    )
else:
    frequency = default_freq
    st.sidebar.info(f"使用标准频率: {frequency} GHz")

# 动态阵列规模
st.sidebar.subheader("📐 阵列配置")
array_col1, array_col2 = st.sidebar.columns(2)
with array_col1:
    use_custom_array = st.checkbox("自定义阵元数", value=False)

if use_custom_array:
    N_elements = st.sidebar.slider("阵元数 N", 4, 128, radar_config['N'])
    M_elements = st.sidebar.slider("阵元数 M", 4, 128, radar_config['M'])
else:
    N_elements = radar_config['N']
    M_elements = radar_config['M']
    st.sidebar.info(f"标准配置: {N_elements}×{M_elements} = {N_elements*M_elements}单元")

# 波束方向
theta = st.sidebar.slider(
    "俯仰角 (度)",
    min_value=-60,
    max_value=60,
    value=st.session_state.get('preset_theta', 0),
    step=1,
    help="波束在垂直方向的指向"
)

phi = st.sidebar.slider(
    "方位角 (度)",
    min_value=-60,
    max_value=60,
    value=st.session_state.get('preset_phi', 0),
    step=1,
    help="波束在水平方向的指向"
)

# 阵元间距
d = st.sidebar.slider(
    "阵元间距 (λ)",
    min_value=0.3,
    max_value=1.0,
    value=float(radar_config['element_spacing']),
    step=0.05,
    help="以波长为单位的阵元间距"
)

# 波束赋形权重
st.sidebar.subheader("📐 波束赋形设置")
weighting_type = st.sidebar.selectbox(
    "权重函数",
    ["均匀", "切比雪夫", "泰勒", "汉明", "汉宁", "布莱克曼"],
    index=["均匀", "切比雪夫", "泰勒", "汉明", "汉宁", "布莱克曼"].index(
        st.session_state.get('preset_weighting', '均匀')
    ),
    help="选择加权函数以控制副瓣电平"
)

if weighting_type != "均匀":
    sidelobe_level = st.sidebar.slider(
        "副瓣电平 (dB)",
        -50.0, -20.0,
        float(st.session_state.get('preset_sidelobe', -30)),
        step=1.0,
        help="目标副瓣电平（仅适用于切比雪夫加权）"
    )

# 新增：自适应波束成形
st.sidebar.subheader("🎯 自适应波束成形")
enable_adaptive = st.sidebar.checkbox("启用MVDR自适应波束成形", value=False)
if enable_adaptive:
    adaptive_snr = st.sidebar.slider("信噪比 SNR (dB)", 0, 40, 20)
    st.sidebar.info("自适应波束成形将在目标方向形成波束，在干扰方向形成零陷")

# 新增：干扰机设置
st.sidebar.subheader("🚨 干扰机设置")
num_jammers = st.sidebar.number_input("干扰机数量", 0, 5, 0)
jammers = []
for i in range(num_jammers):
    with st.sidebar.expander(f"干扰机 {i+1}"):
        jam_theta = st.slider(f"干扰俯仰角 {i+1}", -60, 60, -20 + i*10)
        jam_phi = st.slider(f"干扰方位角 {i+1}", -60, 60, -30 + i*10)
        jam_power = st.slider(f"干扰功率 {i+1} (dBm)", -50, 50, 0)
        jammers.append(Jammer(jam_theta, jam_phi, jam_power, 10))

# 目标设置
st.sidebar.subheader("🎯 多目标模拟")
num_targets = st.sidebar.number_input("目标数量", 1, 5, 1)
targets = []
for i in range(num_targets):
    with st.sidebar.expander(f"目标 {i+1}"):
        tgt_theta = st.slider(f"目标{i+1}俯仰角", -60, 60, 20 + i*5)
        tgt_phi = st.slider(f"目标{i+1}方位角", -60, 60, 30 + i*5)
        tgt_rcs = st.slider(f"目标{i+1} RCS (m²)", 0.1, 10.0, 1.0, step=0.1)
        tgt_range = st.slider(f"目标{i+1}距离 (km)", 1, 100, 10 + i*5)
        tgt_vel = st.slider(f"目标{i+1}速度 (m/s)", -500, 500, 0)
        targets.append(Target(tgt_theta, tgt_phi, tgt_rcs, tgt_range, tgt_vel))

# 新增：阵列误差设置
st.sidebar.subheader("⚠️ 阵列误差模拟")
with st.sidebar.expander("误差参数"):
    enable_errors = st.checkbox("启用阵列误差")
    amp_error_std = st.slider("幅度误差标准差 (dB)", 0.0, 3.0, 0.0, step=0.1)
    phase_error_std = st.slider("相位误差标准差 (度)", 0.0, 10.0, 0.0, step=0.5)
    element_failure_rate = st.slider("阵元失效比例 (%)", 0, 20, 0, step=1) / 100

# 仿真控制
st.sidebar.subheader("🎬 仿真控制")
animate = st.sidebar.checkbox("启用动画仿真", value=True)
if animate:
    scan_mode = st.sidebar.selectbox(
        "扫描模式",
        ["线性扫描", "圆形扫描", "螺旋扫描", "跟踪目标", "扇形扫描", "光栅扫描"],
        index=0
    )
    speed = st.sidebar.slider("动画速度", 1, 10, 5)

# 新增：可视化选项
st.sidebar.subheader("📊 可视化选项")
show_3d_pattern = st.sidebar.checkbox("显示3D波束方向图", value=False)
show_range_doppler = st.sidebar.checkbox("显示距离-多普勒图", value=False)
show_pulse_compression = st.sidebar.checkbox("显示脉冲压缩", value=False)

# 高级设置
with st.sidebar.expander("🔧 高级设置"):
    show_grating_lobes = st.checkbox("显示栅瓣", value=False)
    show_null_locations = st.checkbox("显示零点位置", value=False)
    resolution = st.slider("角度分辨率 (度)", 0.1, 2.0, 0.5, step=0.1)
    
    # 新增：导出配置
    if st.button("📥 导出当前配置"):
        config = {
            "frequency_ghz": frequency,
            "theta": theta,
            "phi": phi,
            "element_spacing": d,
            "weighting_type": weighting_type,
            "sidelobe_level": sidelobe_level if weighting_type != "均匀" else None,
            "adaptive_enabled": enable_adaptive,
            "num_targets": num_targets,
            "num_jammers": num_jammers,
            "array_errors": {
                "enabled": enable_errors,
                "amp_error_std": amp_error_std,
                "phase_error_std": phase_error_std,
                "failure_rate": element_failure_rate
            }
        }
        config_json = export_configuration(config)
        st.sidebar.markdown(create_download_link(config_json, "radar_config.json"), unsafe_allow_html=True)

# --- 主计算逻辑 ---
# 计算波长
wavelength = calculate_wavelength_cached(frequency)

# 生成阵列位置 (使用选定的雷达配置)
N, M = N_elements, M_elements
X, Y, Z = generate_array_positions_cached(N, M, d, wavelength)

# 计算基础加权系数
weights = calculate_weighting(
    weighting_type, 
    N, M, 
    sidelobe_level if weighting_type != "均匀" else -30
)

# 如果启用自适应波束成形且存在干扰机
if enable_adaptive and jammers:
    weights = calculate_mvdr_weights(X, Y, Z, wavelength, theta, phi, jammers, adaptive_snr)

# 应用阵列误差
if enable_errors and (amp_error_std > 0 or phase_error_std > 0 or element_failure_rate > 0):
    weights = apply_array_errors(weights, amp_error_std, phase_error_std, element_failure_rate)

# 计算相位偏移 (波束指向相位)
phase_shift = calculate_phase_shift_cached(theta, phi, X, Y, Z, wavelength)

# 应用加权 - 正确处理复数权重
# 将相位偏移转换为复数形式，然后与权重相乘
if np.iscomplexobj(weights):
    # 如果weights是复数（自适应波束成形），直接相乘
    weighted_phase_shift = phase_shift + np.angle(weights)
else:
    # 如果weights是实数（传统加权），权重只影响幅度，不影响相位
    # 对于方向图计算，我们只需要相位信息，幅度权重在计算后应用
    weighted_phase_shift = phase_shift

# 计算方向图
theta_range = np.linspace(-90, 90, int(180/resolution) + 1)
phi_range = np.linspace(-180, 180, int(360/resolution) + 1)

# 使用向量化计算
pattern_elevation = calculate_radiation_pattern_vectorized(
    X, Y, Z, weighted_phase_shift, wavelength, theta_range, phi
)

# 计算方位角方向图
pattern_azimuth = calculate_radiation_pattern_vectorized(
    X, Y, Z, weighted_phase_shift, wavelength, phi_range, theta
)

# 分析方向图
mainlobe_gain, mainlobe_angle, sidelobes = analyze_pattern(pattern_elevation, theta_range)

# 计算波束宽度
half_power = np.max(pattern_elevation) - 3
mainlobe_idx = np.argmax(pattern_elevation)

left_idx = mainlobe_idx
while left_idx > 0 and pattern_elevation[left_idx] > half_power:
    left_idx -= 1

right_idx = mainlobe_idx
while right_idx < len(pattern_elevation) - 1 and pattern_elevation[right_idx] > half_power:
    right_idx += 1

beamwidth = theta_range[right_idx] - theta_range[left_idx]

# 计算扫描损失
scan_loss = calculate_scan_loss(theta, phi, d, wavelength)

# 计算各目标的接收增益
target_gains = []
for tgt in targets:
    gain = calculate_array_factor_cached(X, Y, Z, weighted_phase_shift, tgt.theta, tgt.phi, wavelength)
    gain_db = 20 * np.log10(gain + 1e-10)
    target_gains.append(gain_db)

# --- 可视化 ---
# 创建选项卡
tabs = st.tabs(["📊 基础方向图", "🎲 3D波束方向图", "🎯 目标分析", "📡 脉冲压缩", "📡 距离-多普勒", "📈 性能对比"])

with tabs[0]:  # 基础方向图
    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("阵列布局与相位分布", "俯仰角方向图 (E面)", "波束加权系数", "方位角方向图 (H面)"),
        specs=[
            [{"type": "scatter3d"}, {"type": "scatter"}],
            [{"type": "heatmap"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    # 1. 阵列布局（3D）- 添加相位颜色
    fig.add_trace(
        go.Scatter3d(
            x=X.flatten(),
            y=Y.flatten(),
            z=Z.flatten(),
            mode='markers',
            marker=dict(
                size=4,
                color=phase_shift.flatten(),
                colorscale='Rainbow',
                showscale=True,
                colorbar=dict(title="相位 (rad)", x=0.45, len=0.7)
            ),
            name='阵元',
            hovertemplate='X: %{x:.3f}m<br>Y: %{y:.3f}m<br>Z: %{z:.3f}m<br>相位: %{marker.color:.2f}rad<extra></extra>'
        ),
        row=1, col=1
    )

    # 阵列网格
    for i in range(N):
        fig.add_trace(
            go.Scatter3d(
                x=X[i, :],
                y=Y[i, :],
                z=Z[i, :],
                mode='lines',
                line=dict(color='rgba(128,128,128,0.3)', width=1),
                showlegend=False,
                hoverinfo='skip'
            ),
            row=1, col=1
        )
    for j in range(M):
        fig.add_trace(
            go.Scatter3d(
                x=X[:, j],
                y=Y[:, j],
                z=Z[:, j],
                mode='lines',
                line=dict(color='rgba(128,128,128,0.3)', width=1),
                showlegend=False,
                hoverinfo='skip'
            ),
            row=1, col=1
        )

    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        )
    )

    # 2. 俯仰角方向图
    fig.add_trace(
        go.Scatter(
            x=theta_range,
            y=pattern_elevation,
            mode='lines',
            line=dict(color='blue', width=3),
            name='方向图',
            fill='tozeroy',
            fillcolor='rgba(0, 100, 255, 0.1)',
            hovertemplate='角度: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
        ),
        row=1, col=2
    )

    # 标记主瓣方向
    fig.add_trace(
        go.Scatter(
            x=[theta],
            y=[mainlobe_gain],
            mode='markers+text',
            marker=dict(size=14, color='red', symbol='star'),
            text=['主瓣'],
            textposition="top center",
            name=f'主瓣 ({theta}°)',
            hovertemplate='俯仰角: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
        ),
        row=1, col=2
    )

    # 标记-3dB点
    fig.add_trace(
        go.Scatter(
            x=[theta_range[left_idx], theta_range[right_idx]],
            y=[half_power, half_power],
            mode='markers+lines',
            marker=dict(size=8, color='orange'),
            line=dict(color='orange', width=2, dash='dash'),
            name=f'波束宽度: {beamwidth:.1f}°',
            hovertemplate='角度: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
        ),
        row=1, col=2
    )

    # 标记副瓣
    if sidelobes:
        for i, (angle, gain) in enumerate(sidelobes[:3]):
            fig.add_trace(
                go.Scatter(
                    x=[angle],
                    y=[gain],
                    mode='markers+text',
                    marker=dict(size=8, color='green', symbol='triangle-up'),
                    text=[f'SL{i+1}'],
                    textposition="top center",
                    showlegend=False,
                    hovertemplate='角度: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
                ),
                row=1, col=2
            )

    # 标记多目标
    for i, (tgt, gain_db) in enumerate(zip(targets, target_gains)):
        fig.add_trace(
            go.Scatter(
                x=[tgt.theta],
                y=[gain_db],
                mode='markers+text',
                marker=dict(size=12, color='purple', symbol='diamond'),
                text=[f'T{i+1}'],
                textposition="top center",
                name=f'目标{i+1}',
                hovertemplate=f'目标{i+1}<br>角度: %{{x:.1f}}°<br>增益: %{{y:.2f}} dB<extra></extra>'
            ),
            row=1, col=2
        )

    # 标记干扰机位置
    for i, jam in enumerate(jammers):
        # 计算干扰方向的增益
        jam_gain = calculate_array_factor_cached(X, Y, Z, weighted_phase_shift, jam.theta, jam.phi, wavelength)
        jam_gain_db = 20 * np.log10(jam_gain + 1e-10)
        fig.add_trace(
            go.Scatter(
                x=[jam.theta],
                y=[jam_gain_db],
                mode='markers+text',
                marker=dict(size=12, color='red', symbol='x'),
                text=[f'J{i+1}'],
                textposition="top center",
                name=f'干扰{i+1}',
                hovertemplate=f'干扰{i+1}<br>角度: %{{x:.1f}}°<br>增益: %{{y:.2f}} dB<extra></extra>'
            ),
            row=1, col=2
        )

    fig.update_xaxes(title_text="俯仰角 (度)", row=1, col=2, range=[-90, 90])
    fig.update_yaxes(title_text="增益 (dB)", row=1, col=2)

    # 3. 加权系数（热图）
    fig.add_trace(
        go.Heatmap(
            z=np.abs(weights),
            colorscale='RdYlBu',
            showscale=True,
            colorbar=dict(title="|权重|", x=1.02, len=0.7),
            hovertemplate='X: %{x}<br>Y: %{y}<br>权重: %{z:.3f}<extra></extra>',
            name='加权系数'
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="X 阵元", row=2, col=1, tickmode='linear', dtick=4)
    fig.update_yaxes(title_text="Y 阵元", row=2, col=1, tickmode='linear', dtick=4)

    # 4. 方位角方向图
    fig.add_trace(
        go.Scatter(
            x=phi_range,
            y=pattern_azimuth,
            mode='lines',
            line=dict(color='green', width=3),
            name='方位方向图',
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.1)',
            hovertemplate='方位角: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
        ),
        row=2, col=2
    )

    # 标记主瓣方向
    azimuth_mainlobe_gain = calculate_array_factor_cached(
        X, Y, Z, weighted_phase_shift, theta, phi, wavelength
    )
    azimuth_mainlobe_gain_db = 20 * np.log10(azimuth_mainlobe_gain + 1e-10)

    fig.add_trace(
        go.Scatter(
            x=[phi],
            y=[azimuth_mainlobe_gain_db],
            mode='markers+text',
            marker=dict(size=12, color='red', symbol='star'),
            text=['主瓣'],
            textposition="top center",
            showlegend=False,
            hovertemplate='方位角: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
        ),
        row=2, col=2
    )

    # 在方位图上也标记目标
    for i, tgt in enumerate(targets):
        az_gain = calculate_array_factor_cached(X, Y, Z, weighted_phase_shift, theta, tgt.phi, wavelength)
        az_gain_db = 20 * np.log10(az_gain + 1e-10)
        fig.add_trace(
            go.Scatter(
                x=[tgt.phi],
                y=[az_gain_db],
                mode='markers',
                marker=dict(size=10, color='purple', symbol='diamond'),
                showlegend=False,
                hovertemplate=f'目标{i+1}<br>方位角: %{{x:.1f}}°<extra></extra>'
            ),
            row=2, col=2
        )

    fig.update_xaxes(title_text="方位角 (度)", row=2, col=2, range=[-180, 180])
    fig.update_yaxes(title_text="增益 (dB)", row=2, col=2)

    # 更新布局 - 应用主题
    fig.update_layout(
        height=900,
        showlegend=True,
        template=theme['plotly_template'],
        paper_bgcolor=theme['paper_color'],
        plot_bgcolor=theme['background_color'],
        font=dict(color=theme['text_color']),
        title_font=dict(color=theme['text_color']),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            font=dict(color=theme['text_color'])
        ),
        margin=dict(l=50, r=100, t=50, b=50)
    )
    
    # 应用主题到坐标轴
    fig.update_xaxes(gridcolor=theme['grid_color'], zerolinecolor=theme['grid_color'])
    fig.update_yaxes(gridcolor=theme['grid_color'], zerolinecolor=theme['grid_color'])

    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:  # 3D波束方向图
    if show_3d_pattern:
        st.subheader("🎲 3D波束方向图 (球坐标)")
        
        with st.spinner("正在计算3D方向图..."):
            # 计算粗粒度的3D方向图以提高性能
            theta_3d = np.linspace(-90, 90, 60)
            phi_3d = np.linspace(-180, 180, 120)
            
            pattern_3d = np.zeros((len(phi_3d), len(theta_3d)))
            k = 2 * np.pi / wavelength
            X_flat = X.flatten()
            Y_flat = Y.flatten()
            Z_flat = Z.flatten()
            phase_flat = weighted_phase_shift.flatten()
            
            for i, p in enumerate(phi_3d):
                for j, t in enumerate(theta_3d):
                    theta_rad = np.radians(t)
                    phi_rad = np.radians(p)
                    u = np.sin(theta_rad) * np.cos(phi_rad)
                    v = np.sin(theta_rad) * np.sin(phi_rad)
                    w = np.cos(theta_rad)
                    
                    spatial_phase = k * (u * X_flat + v * Y_flat + w * Z_flat)
                    total_phase = spatial_phase - phase_flat
                    af = np.abs(np.sum(np.exp(1j * total_phase))) / (N * M)
                    pattern_3d[i, j] = 20 * np.log10(af + 1e-10)
            
            # 转换为球坐标
            theta_grid, phi_grid = np.meshgrid(np.radians(theta_3d), np.radians(phi_3d))
            r = pattern_3d - np.min(pattern_3d) + 1  # 归一化半径
            x_3d = r * np.sin(theta_grid) * np.cos(phi_grid)
            y_3d = r * np.sin(theta_grid) * np.sin(phi_grid)
            z_3d = r * np.cos(theta_grid)
            
            fig_3d = go.Figure(data=[go.Surface(
                x=x_3d, y=y_3d, z=z_3d,
                surfacecolor=pattern_3d,
                colorscale='Jet',
                colorbar=dict(title="增益 (dB)"),
                hovertemplate='增益: %{surfacecolor:.1f} dB<extra></extra>'
            )])
            
            fig_3d.update_layout(
                title="3D波束方向图",
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z",
                    aspectmode='cube',
                    bgcolor=theme['background_color'],
                    xaxis=dict(gridcolor=theme['grid_color'], tickfont=dict(color=theme['secondary_text'])),
                    yaxis=dict(gridcolor=theme['grid_color'], tickfont=dict(color=theme['secondary_text'])),
                    zaxis=dict(gridcolor=theme['grid_color'], tickfont=dict(color=theme['secondary_text']))
                ),
                template=theme['plotly_template'],
                paper_bgcolor=theme['paper_color'],
                font=dict(color=theme['text_color']),
                height=700
            )
            
            st.plotly_chart(fig_3d, use_container_width=True)
    else:
        st.info("请在侧边栏启用'显示3D波束方向图'以查看此内容")

with tabs[2]:  # 目标分析
    st.subheader("🎯 多目标检测分析")
    
    if targets:
        # 目标信息表格
        target_data = []
        for i, (tgt, gain) in enumerate(zip(targets, target_gains)):
            # 计算信噪比
            snr = gain + 10*np.log10(tgt.rcs) - 20*np.log10(tgt.range_km) - 40  # 简化的SNR计算
            target_data.append({
                "目标": f"目标{i+1}",
                "俯仰角(°)": tgt.theta,
                "方位角(°)": tgt.phi,
                "距离(km)": tgt.range_km,
                "RCS(m²)": tgt.rcs,
                "速度(m/s)": tgt.velocity,
                "接收增益(dB)": f"{gain:.2f}",
                "估计SNR(dB)": f"{snr:.1f}"
            })
        
        st.dataframe(target_data, use_container_width=True)
        
        # 目标位置极坐标图
        fig_polar = go.Figure()
        
        for i, tgt in enumerate(targets):
            fig_polar.add_trace(go.Scatterpolar(
                r=[tgt.range_km],
                theta=[tgt.phi],
                mode='markers+text',
                marker=dict(size=15, symbol='diamond'),
                name=f'目标{i+1}',
                text=[f'T{i+1}'],
                textposition="top center"
            ))
        
        for i, jam in enumerate(jammers):
            fig_polar.add_trace(go.Scatterpolar(
                r=[50],  # 固定距离显示
                theta=[jam.phi],
                mode='markers+text',
                marker=dict(size=12, color='red', symbol='x'),
                name=f'干扰{i+1}',
                text=[f'J{i+1}'],
                textposition="top center"
            ))
        
        # 添加波束指向
        fig_polar.add_trace(go.Scatterpolar(
            r=[100],
            theta=[phi],
            mode='lines',
            line=dict(color='green', width=2, dash='dash'),
            name='波束指向'
        ))
        
        fig_polar.update_layout(
            polar=dict(
                radialaxis=dict(
                    range=[0, 100], 
                    title="距离 (km)",
                    gridcolor=theme['grid_color'],
                    tickfont=dict(color=theme['secondary_text'])
                ),
                angularaxis=dict(
                    direction="clockwise", 
                    rotation=90,
                    gridcolor=theme['grid_color'],
                    tickfont=dict(color=theme['secondary_text'])
                ),
                bgcolor=theme['background_color']
            ),
            title="目标相对位置 (方位面)",
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            font=dict(color=theme['text_color']),
            height=500
        )
        
        st.plotly_chart(fig_polar, use_container_width=True)
    else:
        st.warning("请在侧边栏添加目标以查看分析")

with tabs[3]:  # 脉冲压缩
    if show_pulse_compression:
        st.subheader("📡 LFM脉冲压缩仿真")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            lfm_bw = st.number_input("LFM带宽 (MHz)", 1.0, 500.0, 10.0) * 1e6
        with col2:
            lfm_pw = st.number_input("脉宽 (μs)", 1.0, 100.0, 10.0) * 1e-6
        with col3:
            lfm_fs = st.number_input("采样率 (MHz)", 10.0, 1000.0, 100.0) * 1e6
        
        # 生成目标时延和幅度
        target_delays = [tgt.range_km * 2 * 1000 / 3e8 for tgt in targets] if targets else [10e-6]
        target_amps = [np.sqrt(tgt.rcs) for tgt in targets] if targets else [1.0]
        
        tx_signal, compressed = generate_lfm_pulse(lfm_bw, lfm_pw, lfm_fs, target_delays, target_amps)
        
        # 绘制结果
        fig_lfm = make_subplots(rows=2, cols=1, subplot_titles=("发射信号 (实部)", "脉冲压缩结果"))
        
        t_tx = np.arange(len(tx_signal)) / lfm_fs * 1e6  # 转换为微秒
        fig_lfm.add_trace(
            go.Scatter(x=t_tx, y=np.real(tx_signal), mode='lines', name='发射信号', line=dict(color='blue')),
            row=1, col=1
        )
        
        t_rx = np.arange(len(compressed)) / lfm_fs * 1e6
        fig_lfm.add_trace(
            go.Scatter(x=t_rx, y=20*np.log10(np.abs(compressed) + 1e-10), mode='lines', name='压缩后(dB)', line=dict(color='red')),
            row=2, col=1
        )
        
        fig_lfm.update_xaxes(title_text="时间 (μs)", row=1, col=1, gridcolor=theme['grid_color'])
        fig_lfm.update_yaxes(title_text="幅度", row=1, col=1, gridcolor=theme['grid_color'])
        fig_lfm.update_xaxes(title_text="时间 (μs)", row=2, col=1, gridcolor=theme['grid_color'])
        fig_lfm.update_yaxes(title_text="幅度 (dB)", row=2, col=1, gridcolor=theme['grid_color'])
        
        fig_lfm.update_layout(
            height=600, 
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            plot_bgcolor=theme['background_color'],
            font=dict(color=theme['text_color']),
            showlegend=False
        )
        st.plotly_chart(fig_lfm, use_container_width=True)
        
        # 距离分辨率信息
        range_res = 3e8 / (2 * lfm_bw)  # 米
        st.info(f"理论距离分辨率: {range_res:.1f} m ({range_res/1000:.3f} km)")
    else:
        st.info("请在侧边栏启用'显示脉冲压缩'以查看此内容")

with tabs[4]:  # 距离-多普勒图
    if show_range_doppler:
        st.subheader("📡 距离-多普勒图 (Range-Doppler Map)")
        
        # 业界常用配色方案
        COLORSCALES = {
            "Jet (标准雷达)": "Jet",
            "Hot (热力图)": "Hot",
            "Turbo (Google改进)": "Turbo",
            "Plasma (现代推荐)": "Plasma",
            "Cividis (感知均匀)": "Cividis",
            "Viridis (色盲友好)": "Viridis",
            "RdYlGn (红-黄-绿)": "RdYlGn",
            "Greys (灰度)": "Greys",
            "Electric (高对比)": "Electric",
            "Portland (蓝-紫-红)": "Portland"
        }
        
        col_rd1, col_rd2, col_rd3, col_rd4 = st.columns(4)
        with col_rd1:
            prf = st.number_input("PRF (Hz)", 100, 10000, 1000)
        with col_rd2:
            num_pulses = st.number_input("脉冲数", 8, 128, 64)
        with col_rd3:
            snr_rd = st.slider("信噪比 (dB)", -10, 30, 10)
        with col_rd4:
            colorscale_name = st.selectbox(
                "配色方案",
                list(COLORSCALES.keys()),
                index=0,
                help="选择业界标准的RDM显示配色"
            )
        
        # 配色说明
        with st.expander("🎨 配色方案说明"):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown("""
                **传统雷达配色：**
                - **Jet**: 最经典的雷达显示配色，蓝→青→黄→红，对比度强
                - **Hot**: 黑→红→黄→白，热力图标准，适合弱信号检测
                - **Turbo**: Google改进版Jet，减少感知不均匀问题
                """)
            with col_info2:
                st.markdown("""
                **现代推荐配色：**
                - **Plasma**: 感知均匀，从黑→红→黄→白，适合连续数据
                - **Cividis**: 色盲友好，适合专业出版物
                - **Viridis**: 蓝→绿→黄，色盲友好，科学计算标准
                """)
        
        with st.spinner("正在生成距离-多普勒图..."):
            # 生成距离-多普勒图数据
            # 距离轴
            max_range = 3e8 / (2 * prf)  # 最大不模糊距离
            range_bins = np.linspace(0, max_range/1000, 200)  # km
            
            # 多普勒轴
            max_doppler = prf / 2
            velocity_bins = np.linspace(-max_doppler * wavelength / 2, 
                                         max_doppler * wavelength / 2, 128)  # m/s
            
            # 生成RDM数据
            rdm = np.random.randn(len(velocity_bins), len(range_bins)) * (10**(-snr_rd/20))
            
            # 添加目标
            for tgt in targets:
                # 找到目标在RDM中的位置
                range_idx = np.argmin(np.abs(range_bins - tgt.range_km))
                vel_idx = np.argmin(np.abs(velocity_bins - tgt.velocity))
                
                # 添加目标响应 (高斯形状)
                for i in range(len(velocity_bins)):
                    for j in range(len(range_bins)):
                        range_diff = (j - range_idx) / 5.0
                        vel_diff = (i - vel_idx) / 3.0
                        rdm[i, j] += np.sqrt(tgt.rcs) * np.exp(-(range_diff**2 + vel_diff**2))
            
            # 获取选中的配色
            selected_colorscale = COLORSCALES[colorscale_name]
            
            # 绘制RDM
            fig_rdm = go.Figure(data=go.Heatmap(
                z=20*np.log10(np.abs(rdm) + 1e-10),
                x=range_bins,
                y=velocity_bins,
                colorscale=selected_colorscale,
                colorbar=dict(
                    title="功率 (dB)",
                    # titleside="right",
                    # titlefont=dict(size=12),
                    tickfont=dict(size=10)
                ),
                hovertemplate='距离: %{x:.2f} km<br>速度: %{y:.1f} m/s<br>功率: %{z:.1f} dB<extra></extra>'
            ))
            
            fig_rdm.update_layout(
                title=dict(
                    text=f"距离-多普勒图 - {colorscale_name}",
                    x=0.5,
                    font=dict(size=16, color=theme['text_color'])
                ),
                xaxis_title="距离 (km)",
                yaxis_title="径向速度 (m/s)",
                template=theme['plotly_template'],
                paper_bgcolor=theme['paper_color'],
                font=dict(color=theme['text_color']),
                height=650,
                xaxis=dict(gridcolor=theme['grid_color'], zeroline=False, tickfont=dict(color=theme['secondary_text'])),
                yaxis=dict(gridcolor=theme['grid_color'], zeroline=False, tickfont=dict(color=theme['secondary_text']))
            )
            
            st.plotly_chart(fig_rdm, use_container_width=True)
            
            # 显示目标信息
            if targets:
                st.subheader("🎯 目标在RDM中的位置")
                tgt_info = []
                for tgt in targets:
                    tgt_info.append({
                        "目标": f"目标{targets.index(tgt)+1}",
                        "距离(km)": f"{tgt.range_km:.1f}",
                        "速度(m/s)": f"{tgt.velocity:.1f}",
                        "RCS(m²)": f"{tgt.rcs:.1f}"
                    })
                st.dataframe(tgt_info, use_container_width=True)
            
            # 参数信息
            col_param1, col_param2, col_param3 = st.columns(3)
            with col_param1:
                st.metric("最大不模糊距离", f"{max_range/1000:.1f} km")
            with col_param2:
                st.metric("最大不模糊速度", f"±{max_doppler * wavelength / 2:.1f} m/s")
            with col_param3:
                range_res = 3e8 / (2 * lfm_bw) if 'lfm_bw' in locals() else max_range/200
                st.metric("距离分辨率", f"{range_res/1000:.3f} km")
    else:
        st.info("请在侧边栏启用'显示距离-多普勒图'以查看此内容")

with tabs[5]:  # 性能对比
    st.subheader("📈 不同加权函数性能对比")
    
    if st.button("生成对比分析"):
        with st.spinner("计算中..."):
            window_types = ["均匀", "切比雪夫", "泰勒", "汉明", "汉宁"]
            comparison_data = []
            
            for wt in window_types:
                w = calculate_weighting(wt, N, M, -30)
                wps = phase_shift * w
                
                pat = calculate_radiation_pattern_vectorized(X, Y, Z, wps, wavelength, theta_range, phi)
                
                # 计算指标
                ml_gain = np.max(pat)
                ml_idx = np.argmax(pat)
                
                # 波束宽度
                hp = ml_gain - 3
                li = ml_idx
                while li > 0 and pat[li] > hp:
                    li -= 1
                ri = ml_idx
                while ri < len(pat) - 1 and pat[ri] > hp:
                    ri += 1
                bw = theta_range[ri] - theta_range[li]
                
                # 峰值副瓣
                sidelobes_temp = []
                for i in range(1, len(pat)-1):
                    if pat[i] > pat[i-1] and pat[i] > pat[i+1] and i != ml_idx:
                        sidelobes_temp.append(pat[i])
                psl = max(sidelobes_temp) if sidelobes_temp else -100
                
                comparison_data.append({
                    "加权函数": wt,
                    "主瓣增益(dB)": f"{ml_gain:.2f}",
                    "波束宽度(°)": f"{bw:.2f}",
                    "峰值副瓣(dB)": f"{psl:.2f}",
                    "副瓣抑制": f"{ml_gain - psl:.1f} dB"
                })
            
            st.dataframe(comparison_data, use_container_width=True)
            
            # 绘制对比图
            fig_comp = go.Figure()
            colors = ['blue', 'red', 'green', 'orange', 'purple']
            
            for i, wt in enumerate(window_types):
                w = calculate_weighting(wt, N, M, -30)
                wps = phase_shift * w
                pat = calculate_radiation_pattern_vectorized(X, Y, Z, wps, wavelength, theta_range, phi)
                
                fig_comp.add_trace(go.Scatter(
                    x=theta_range,
                    y=pat,
                    mode='lines',
                    name=wt,
                    line=dict(color=colors[i], width=2)
                ))
            
            fig_comp.update_layout(
                title="不同加权函数方向图对比",
                xaxis_title="角度 (°)",
                yaxis_title="增益 (dB)",
                template=theme['plotly_template'],
                paper_bgcolor=theme['paper_color'],
                plot_bgcolor=theme['background_color'],
                font=dict(color=theme['text_color']),
                height=500,
                xaxis=dict(range=[-30, 30], gridcolor=theme['grid_color']),
                yaxis=dict(gridcolor=theme['grid_color'])
            )
            
            st.plotly_chart(fig_comp, use_container_width=True)

# --- 性能指标 ---
st.header("📊 系统性能指标")

# 主要指标
metric_cols = st.columns(6)

# 计算理论最大增益
theoretical_gain = 10 * np.log10(N * M)

with metric_cols[0]:
    st.metric(
        label="主瓣增益",
        value=f"{mainlobe_gain:.2f} dBi",
        delta=f"理论值: {theoretical_gain:.1f} dBi",
        help="相对于各向同性辐射的增益"
    )

with metric_cols[1]:
    # 计算理论波束宽度 (近似公式: BW ≈ 51° * λ/(N*d*λ) = 51°/N 对于半波长间距)
    theoretical_bw = 51.0 / N
    st.metric(
        label="波束宽度",
        value=f"{beamwidth:.2f}°",
        delta=f"理论值: {theoretical_bw:.1f}°",
        help="-3dB 波束宽度"
    )

with metric_cols[2]:
    scan_loss_text = f"{scan_loss:.2f} dB"
    if abs(scan_loss) < 0.01:
        scan_loss_text = "0.00 dB (法向)"
    st.metric(
        label="扫描损失",
        value=scan_loss_text,
        help="由于波束扫描引起的增益损失 (法向为0 dB)"
    )

with metric_cols[3]:
    directivity = 10 * np.log10(N * M) + 10 * np.log10(4 * np.pi * d**2)
    st.metric(
        label="理论定向性",
        value=f"{directivity:.1f} dBi",
        help="理想阵列定向性估计"
    )

with metric_cols[4]:
    st.metric(
        label="工作波长",
        value=f"{wavelength*100:.2f} cm",
        delta=f"{frequency} GHz"
    )

with metric_cols[5]:
    active_elements = np.sum(np.abs(weights) > 1e-6)
    st.metric(
        label="有效阵元数",
        value=f"{int(active_elements)}/{N*M}",
        help="非零权重阵元数量"
    )

# 详细分析
analysis_cols = st.columns(2)

with analysis_cols[0]:
    st.subheader("📐 波束特性")
    
    # 副瓣信息
    if sidelobes:
        for i, (angle, gain) in enumerate(sidelobes[:5]):
            level = mainlobe_gain - gain
            st.progress(min(level/50, 1.0), text=f"副瓣{i+1}: {gain:.2f} dB @ {angle:.1f}° (抑制 {level:.1f} dB)")
    
    # 第一零点波束宽度估计
    fnbw = 2 * np.degrees(np.arcsin(0.61 * wavelength / (N * d * wavelength)))
    st.info(f"理论第一零点波束宽度 (FNBW): ~{fnbw:.1f}°")
    
    # 栅瓣检查
    if d > 0.5:
        grating_angle = np.degrees(np.arcsin(wavelength / (d * wavelength) - 1))
        st.warning(f"⚠️ 阵元间距 d/λ = {d:.2f} > 0.5，可能出现栅瓣在 ±{grating_angle:.1f}°")

with analysis_cols[1]:
    st.subheader("🎯 目标检测分析")
    
    if targets:
        for i, (tgt, gain) in enumerate(zip(targets, target_gains)):
            # 计算接收功率
            Pt = 1000  # 假设发射功率1kW
            Gt = 10**(mainlobe_gain/10)
            Gr = 10**(gain/10)
            lambda_val = wavelength
            R = tgt.range_km * 1000
            sigma = tgt.rcs
            
            Pr = (Pt * Gt * Gr * lambda_val**2 * sigma) / ((4*np.pi)**3 * R**4)
            Pr_dBm = 10 * np.log10(Pr * 1000)
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.metric(f"目标{i+1}接收功率", f"{Pr_dBm:.1f} dBm")
            with col_t2:
                detectable = "✅ 可检测" if Pr_dBm > -100 else "❌ 信号弱"
                st.write(f"检测状态: {detectable}")
    
    if jammers:
        st.divider()
        st.write("**干扰抑制分析**")
        for i, jam in enumerate(jammers):
            # 计算干扰方向的零陷深度
            jam_gain = calculate_array_factor_cached(X, Y, Z, weighted_phase_shift, jam.theta, jam.phi, wavelength)
            jam_gain_db = 20 * np.log10(jam_gain + 1e-10)
            null_depth = mainlobe_gain - jam_gain_db
            
            if null_depth > 20:
                st.success(f"干扰{i+1}: 零陷深度 {null_depth:.1f} dB - 有效抑制")
            else:
                st.info(f"干扰{i+1}: 零陷深度 {null_depth:.1f} dB")
    else:
        st.info("未配置干扰机")

# --- 实时动画仿真 ---
if animate:
    st.header("🎬 实时波束扫描仿真")
    
    # 添加扫描参数设置
    scan_cols = st.columns(3)
    with scan_cols[0]:
        scan_range = st.slider("扫描范围 (°)", 5, 60, 30)
    with scan_cols[1]:
        scan_speed = st.slider("扫描速度 (°/s)", 1, 100, 30)
    with scan_cols[2]:
        show_trajectory = st.checkbox("显示扫描轨迹", value=True)
    
    # 创建动画图表
    if scan_mode == "线性扫描":
        theta_range_anim = np.linspace(-scan_range, scan_range, 60)
        
        frames = []
        for t in theta_range_anim:
            phase = calculate_phase_shift_cached(t, phi, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, theta_range, phi_fixed=phi
            )
            
            # 检测目标
            detected_targets = []
            for tgt in targets:
                if abs(tgt.theta - t) < beamwidth/2:
                    detected_targets.append(tgt)
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=theta_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='blue', width=2),
                        name='方向图'
                    ),
                    go.Scatter(
                        x=[t],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=12, color='red', symbol='star'),
                        name='波束指向'
                    ),
                    go.Scatter(
                        x=[tgt.theta for tgt in targets],
                        y=[np.interp(tgt.theta, theta_range, pattern) for tgt in targets],
                        mode='markers',
                        marker=dict(size=10, color='purple', symbol='diamond'),
                        name='目标'
                    ) if targets else go.Scatter(x=[], y=[])
                ],
                name=f"θ={t:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title=f"俯仰角线性扫描 (范围: ±{scan_range}°)",
            xaxis_title="俯仰角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                x=0.1,
                y=1.15,
                buttons=[
                    dict(
                        label="▶️ 播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}, "fromcurrent": True}]
                    ),
                    dict(
                        label="⏸️ 暂停",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]
                    )
                ]
            )],
            sliders=[dict(
                steps=[
                    dict(
                        args=[[f.name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                        label=f"{t:.1f}°",
                        method="animate"
                    )
                    for f, t in zip(frames, theta_range_anim)
                ],
                x=0.1,
                y=0,
                len=0.9,
                xanchor="left",
                yanchor="top",
                active=0,
            )],
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            plot_bgcolor=theme['background_color'],
            font=dict(color=theme['text_color']),
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
        
    elif scan_mode == "圆形扫描":
        phi_range_anim = np.linspace(0, 360, 60)
        
        frames = []
        for p in phi_range_anim:
            phase = calculate_phase_shift_cached(theta, p, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, phi_range, theta
            )
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=phi_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='green', width=2),
                        name='方向图'
                    ),
                    go.Scatter(
                        x=[p],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=12, color='red', symbol='star'),
                        name='波束指向'
                    ),
                    go.Scatter(
                        x=[tgt.phi for tgt in targets],
                        y=[np.interp(tgt.phi, phi_range, pattern) for tgt in targets],
                        mode='markers',
                        marker=dict(size=10, color='purple', symbol='diamond'),
                        name='目标'
                    ) if targets else go.Scatter(x=[], y=[])
                ],
                name=f"φ={p:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title="方位角圆形扫描 (360°)",
            xaxis_title="方位角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="▶️ 播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="⏸️ 暂停", method="animate", args=[[None]])
                ]
            )],
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            plot_bgcolor=theme['background_color'],
            font=dict(color=theme['text_color']),
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
        
    elif scan_mode == "螺旋扫描":
        n_frames = 60
        frames = []
        
        for i in range(n_frames):
            t = -scan_range/2 + scan_range * i / n_frames
            p = 360 * i / n_frames
            
            phase = calculate_phase_shift_cached(t, p, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, theta_range, phi_fixed=p
            )
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=theta_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='purple', width=2),
                        name='方向图'
                    ),
                    go.Scatter(
                        x=[t],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=12, color='red', symbol='star'),
                        name='波束指向'
                    )
                ],
                name=f"θ={t:.1f}°, φ={p:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title=f"螺旋扫描 (范围: ±{scan_range/2}° × 360°)",
            xaxis_title="俯仰角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="▶️ 播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="⏸️ 暂停", method="animate", args=[[None]])
                ]
            )],
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            plot_bgcolor=theme['background_color'],
            font=dict(color=theme['text_color']),
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
        
    elif scan_mode == "扇形扫描":
        # 扇形扫描：在指定扇区内往复扫描
        n_frames = 60
        frames = []
        
        for i in range(n_frames):
            # 往复运动
            progress = (i % 30) / 30
            if (i // 30) % 2 == 0:
                p = phi - scan_range/2 + scan_range * progress
            else:
                p = phi + scan_range/2 - scan_range * progress
            
            phase = calculate_phase_shift_cached(theta, p, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, phi_range, theta
            )
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=phi_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='orange', width=2),
                        name='方向图'
                    ),
                    go.Scatter(
                        x=[p],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=12, color='red', symbol='star'),
                        name='波束指向'
                    )
                ],
                name=f"φ={p:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title=f"扇形扫描 (中心: {phi}°, 范围: ±{scan_range/2}°)",
            xaxis_title="方位角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="▶️ 播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="⏸️ 暂停", method="animate", args=[[None]])
                ]
            )],
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            plot_bgcolor=theme['background_color'],
            font=dict(color=theme['text_color']),
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
        
    elif scan_mode == "光栅扫描":
        # 光栅扫描：二维扫描
        n_frames = 60
        frames = []
        
        for i in range(n_frames):
            row = i // 10
            col = i % 10
            
            # 锯齿形扫描
            if row % 2 == 0:
                t = -scan_range/2 + scan_range * col / 10
            else:
                t = scan_range/2 - scan_range * col / 10
            
            p = phi - scan_range/2 + scan_range * row / 6
            
            phase = calculate_phase_shift_cached(t, p, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, theta_range, phi_fixed=p
            )
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=theta_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='cyan', width=2),
                        name='方向图'
                    ),
                    go.Scatter(
                        x=[t],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=12, color='red', symbol='star'),
                        name='波束指向'
                    )
                ],
                name=f"θ={t:.1f}°, φ={p:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title=f"光栅扫描 (θ范围: ±{scan_range/2}°, φ范围: ±{scan_range/2}°)",
            xaxis_title="俯仰角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="▶️ 播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="⏸️ 暂停", method="animate", args=[[None]])
                ]
            )],
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            plot_bgcolor=theme['background_color'],
            font=dict(color=theme['text_color']),
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
    
    elif scan_mode == "跟踪目标" and targets:
        # 目标跟踪仿真 - 跟踪第一个目标
        target_to_track = targets[0]
        scan_range_track = 15
        n_frames = 40
        frames = []
        
        for i in range(n_frames):
            # 在目标周围小范围扫描（圆锥扫描）
            angle = 2 * np.pi * i / n_frames
            offset_theta = scan_range_track * np.cos(angle) * np.sin(np.radians(target_to_track.theta))
            offset_phi = scan_range_track * np.sin(angle)
            
            current_theta = target_to_track.theta + offset_theta
            current_phi = target_to_track.phi + offset_phi
            
            phase = calculate_phase_shift_cached(current_theta, current_phi, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, theta_range, phi_fixed=current_phi
            )
            
            # 计算目标增益
            target_current_gain = calculate_array_factor_cached(
                X, Y, Z, weighted_phase, target_to_track.theta, target_to_track.phi, wavelength
            )
            target_current_gain_db = 20 * np.log10(target_current_gain + 1e-10)
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=theta_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='orange', width=2),
                        name='扫描方向图'
                    ),
                    go.Scatter(
                        x=[current_theta],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=12, color='red', symbol='star'),
                        name='波束指向'
                    ),
                    go.Scatter(
                        x=[target_to_track.theta],
                        y=[target_current_gain_db],
                        mode='markers',
                        marker=dict(size=14, color='purple', symbol='x', line=dict(width=2)),
                        name='目标位置'
                    )
                ],
                name=f"扫描 {i+1}"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1], frames[0].data[2]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title=f"目标跟踪扫描 - 跟踪目标1 (θ={target_to_track.theta}°, φ={target_to_track.phi}°)",
            xaxis_title="俯仰角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="▶️ 播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="⏸️ 暂停", method="animate", args=[[None]])
                ]
            )],
            template=theme['plotly_template'],
            paper_bgcolor=theme['paper_color'],
            plot_bgcolor=theme['background_color'],
            font=dict(color=theme['text_color']),
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
    
    st.plotly_chart(fig_anim, use_container_width=True)

# --- 技术说明 ---
with st.expander("📖 技术说明"):
    st.markdown("""
### 相控阵雷达原理

相控阵雷达通过控制每个阵元的相位来改变波束方向，而不需要机械转动。

**核心公式：**

1. **相位偏移计算：**
$$
Δφ = k · (u·x + v·y + w·z)
$$
其中 k = 2π/λ 是波数，(u, v, w) 是方向向量。

2. **阵列因子：**
$$
AF(θ, φ) = Σ w_n exp[j(k·(u·x_n + v·y_n + w·z_n) - Δφ_n)]
$$
其中 w_n 是阵元加权系数。

3. **扫描损失：**
$$
L_{scan} = 20·log_{10}(cos(θ_{scan}))
$$
其中 θ_scan 是波束扫描角度。

**波束赋形技术：**

| 加权函数 | 主瓣宽度 | 副瓣电平 | 应用场景 |
|---------|---------|---------|---------|
| 均匀 | 最窄 | -13.2 dB | 高分辨率要求 |
| 切比雪夫 | 中等 | 可设计 | 副瓣控制严格 |
| 泰勒 | 中等 | 渐近衰减 | 大阵列天线 |
| 汉明 | 稍宽 | -42 dB | 一般用途 |
| 汉宁 | 宽 | -31 dB | 频谱分析 |

**自适应波束成形 (MVDR)：**

最小方差无失真响应 (Minimum Variance Distortionless Response) 算法：

$$
w_{MVDR} = \frac{R^{-1}a(θ_0)}{a^H(θ_0)R^{-1}a(θ_0)}
$$

其中 R 是协方差矩阵，a(θ₀) 是目标方向导向矢量。

**干扰抑制：**
- 在干扰方向形成零陷 (null)
- 零陷深度可达 40-60 dB
- 不影响目标方向的增益

**各频段雷达应用：**

| 频段 | 频率范围 | 主要应用 | 代表雷达 |
|------|----------|----------|----------|
| VHF/UHF | 30-1000 MHz | 远程警戒、反隐身 | JY-27A |
| L | 1-2 GHz | 远程监视、预警机 | EL/M-2075 |
| S | 2-4 GHz | 舰载雷达、远程监视 | AN/SPY-1、346型 |
| C | 4-8 GHz | 中程防空、火控 | AN/MPQ-53 |
| X | 8-12 GHz | 机载火控、导航 | AN/APG-77/81、RBE2 |
| Ku | 12-18 GHz | 高分辨率、卫星通信 | 民用/商用 |

**相控阵雷达优势：**
- 高增益（与阵元数成正比）
- 窄波束宽度（高角度分辨率）
- 快速波束扫描（微秒级）
- 多波束形成能力
- 自适应波束成形与干扰抑制
""")

# --- 使用说明 ---
with st.expander("🎮 使用说明"):
    st.markdown("""
### 快速入门

1. **选择雷达型号**：
   - 从下拉菜单选择预定义军用雷达（宙斯盾、F-22/F-35、346型等）
   - 查看雷达详情：频段、阵元数、载台平台
   - 选择"自定义配置"进行自由参数设置

2. **参数配置**：
   - 勾选"自定义频率"调整工作频率（按选定雷达频段范围）
   - 勾选"自定义阵元数"修改阵列规模
   - 设置波束指向的俯仰角和方位角
   - 调整阵元间距（建议0.5λ以避免栅瓣）

2. **波束赋形设置**：
   - 选择不同的加权函数控制副瓣电平
   - 支持均匀、切比雪夫、泰勒、汉明、汉宁、布莱克曼窗
   - 切比雪夫加权可指定目标副瓣电平

3. **🎯 自适应波束成形**：
   - 启用MVDR自适应波束成形
   - 设置信噪比参数
   - 系统自动在干扰方向形成零陷

4. **🚨 干扰机设置**：
   - 添加多个干扰机
   - 设置干扰机的角度和功率
   - 观察自适应波束的零陷形成

5. **🎯 多目标模拟**：
   - 添加最多5个目标
   - 设置目标的角度、RCS、距离和速度
   - 在极坐标图中查看目标相对位置

6. **⚠️ 阵列误差模拟**：
   - 启用阵列误差功能
   - 设置幅度和相位误差
   - 模拟阵元失效情况

7. **🎬 扫描模式**：
   - **线性扫描**：在俯仰面线性扫描
   - **圆形扫描**：360°方位扫描
   - **螺旋扫描**：俯仰和方位同时扫描
   - **扇形扫描**：在指定扇区内往复扫描
   - **光栅扫描**：二维光栅扫描模式
   - **跟踪目标**：对目标进行圆锥扫描跟踪

8. **📊 高级可视化**：
   - **3D波束方向图**：球坐标3D可视化
   - **脉冲压缩**：LFM信号脉压仿真
   - **性能对比**：不同加权函数对比分析

9. **💾 配置管理**：
   - 点击"导出当前配置"保存参数
   - 下载JSON配置文件
   - 方便后续复现分析

**交互操作：**
- 鼠标悬停在图表上查看详细数据
- 使用滑块实时调整参数
- 点击动画播放按钮启动仿真
- 切换选项卡查看不同分析结果
""")

# --- 雷达方程计算 ---
with st.expander("📐 雷达方程计算"):
    st.markdown("""
### 雷达方程
    
雷达方程用于估计雷达的探测性能：
""")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transmit_power = st.number_input("发射功率 (W)", 100.0, 10000.0, 1000.0, 100.0)
        antenna_gain = st.number_input("天线增益 (dB)", 20.0, 50.0, 30.0, 1.0)
        frequency_input = st.number_input("频率 (GHz)", 0.1, 100.0, float(frequency), 0.1)
    
    with col2:
        target_rcs_input = st.number_input("目标RCS (m²)", 0.1, 100.0, 1.0, 0.1)
        target_range_input = st.number_input("目标距离 (km)", 1.0, 1000.0, 10.0, 1.0)
        noise_figure = st.number_input("噪声系数 (dB)", 1.0, 10.0, 3.0, 0.5)
    
    if st.button("计算雷达性能"):
        # 转换为线性值
        G_linear = 10**(antenna_gain/10)
        RCS_linear = target_rcs_input
        R = target_range_input * 1000  # 转换为米
        wavelength_calc = 3e8 / (frequency_input * 1e9)
        
        # 雷达方程
        received_power = (transmit_power * G_linear**2 * wavelength_calc**2 * RCS_linear) / ((4 * np.pi)**3 * R**4)
        received_power_dBm = 10 * np.log10(received_power * 1000)  # 转换为dBm
        
        # 热噪声
        T0 = 290  # 标准温度 (K)
        k = 1.38e-23  # 玻尔兹曼常数
        B = 10e6  # 带宽 10MHz
        
        noise_power = k * T0 * B * 10**(noise_figure/10)
        noise_power_dBm = 10 * np.log10(noise_power * 1000)
        
        SNR = received_power_dBm - noise_power_dBm
        
        col3, col4, col5 = st.columns(3)
        with col3:
            st.metric("接收功率", f"{received_power_dBm:.2f} dBm")
        with col4:
            st.metric("噪声功率", f"{noise_power_dBm:.2f} dBm")
        with col5:
            st.metric("信噪比", f"{SNR:.2f} dB", 
                     delta="良好" if SNR > 10 else "临界" if SNR > 0 else "不足",
                     delta_color="normal" if SNR > 10 else "off" if SNR > 0 else "inverse")

st.markdown("---")
st.markdown(f"💡 **当前配置**: {selected_radar} | {radar_config['band']}波段 {frequency} GHz | {N}×{M}={N*M}单元 | 平台: {radar_config['platform']} | 主题: {selected_theme_name}")
