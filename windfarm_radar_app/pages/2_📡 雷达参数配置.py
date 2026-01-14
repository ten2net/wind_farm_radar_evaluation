"""
雷达参数配置页面
功能：配置雷达参数、频段、扫描模式等
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import constants
from scipy.special import j1
import time

# 页面配置
st.set_page_config(
    page_title="雷达参数配置 | 雷达影响评估系统",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    .stMetric {
        padding: 8px 0;
    }
    
    .stMetric label {
        font-size: 0.9rem !important;
    }
    
    .stMetric div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    .stMetric div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }  
    
    .stSlider > div {
        padding: 0.5rem 0;
    }
    
    /* 滑块轨道 */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, rgba(0, 150, 255, 0.1), rgba(0, 150, 255, 0.3));
        height: 6px;
        border-radius: 3px;
    }
    
    /* 滑块轨道填充部分（已选择部分） */
    .stSlider > div > div > div > div > div {
        background: linear-gradient(90deg, 
            rgba(0, 200, 255, 0.7), 
            rgba(0, 150, 255, 0.9));
        height: 6px;
        border-radius: 3px 0 0 3px;
    }
    
    /* 滑块轨道未填充部分 */
    .stSlider > div > div > div > div > div > div {
        background: rgba(100, 100, 150, 0.3);
        height: 6px;
        border-radius: 0 3px 3px 0;
    }
    
    /* 滑块圆点 */
    .stSlider > div > div > div > div > div > div > div {
        background: linear-gradient(135deg, 
            rgba(0, 200, 255, 1), 
            rgba(0, 100, 200, 1));
        border: 2px solid rgba(200, 220, 255, 0.8);
        box-shadow: 0 0 10px rgba(0, 150, 255, 0.5);
        width: 20px;
        height: 20px;
        transform: translateY(-7px);
    }
    
    /* 滑块圆点悬停效果 */
    .stSlider > div > div > div > div > div > div > div:hover {
        background: linear-gradient(135deg, 
            rgba(0, 220, 255, 1), 
            rgba(0, 120, 220, 1));
        box-shadow: 0 0 15px rgba(0, 180, 255, 0.8);
        transform: translateY(-7px) scale(1.1);
        transition: all 0.2s ease;
    }
    
    /* 滑块标签样式 */
    .stSlider label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #a0c8ff;
        margin-bottom: 0.3rem;
    }
    
    /* 滑块数值显示 */
    .stSlider > div > div > div + div {
        color: #00ccff;
        font-size: 0.9rem;
        font-weight: 600;
        text-shadow: 0 0 5px rgba(0, 150, 255, 0.5);
    }
    
    /* 滑块容器的背景 */
    .stSlider {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    /* 滑块容器悬停效果 */
    .stSlider:hover {
        background: rgba(25, 30, 50, 0.4);
        border-color: rgba(0, 150, 255, 0.3);
        box-shadow: 0 0 20px rgba(0, 100, 200, 0.1);
    }
    
    /* 数字输入框样式 */
    .stNumberInput {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
    }
    
    .stNumberInput label {
        color: #a0c8ff;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .stNumberInput input {
        color: #00ccff;
        background: rgba(10, 20, 40, 0.5);
        border: 1px solid rgba(0, 100, 200, 0.3);
        border-radius: 4px;
    }
    
    /* 选择框样式 */
    .stSelectbox {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
    }
    
    .stSelectbox label {
        color: #a0c8ff;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .stSelectbox > div > div {
        background: rgba(10, 20, 40, 0.5);
        border: 1px solid rgba(0, 100, 200, 0.3);
        color: #00ccff;
    }
    
    /* 选项卡样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: rgba(20, 25, 45, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        color: #a0c8ff;
        font-weight: 500;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, 
            rgba(0, 150, 255, 0.3), 
            rgba(0, 100, 200, 0.5));
        color: #00ccff;
        box-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
    }
    
    /* 调整间距 */
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 100, 200, 0.2);
    }
    
    /* 调整整体容器间距 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #a0d8ff;
        text-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
    }
    
    /* 分隔线样式 */
    hr {
        border-color: rgba(0, 100, 200, 0.2);
        margin: 1.5rem 0;
    }      
</style>
""", unsafe_allow_html=True)

# 标题
st.title("📡 雷达参数配置")
st.markdown("配置雷达系统参数、频段选择和扫描模式")

# 初始化会话状态
if 'radar_config' not in st.session_state:
    st.session_state.radar_config = {}
if 'beam_angle' not in st.session_state:
    st.session_state.beam_angle = 0

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "雷达参数", 
    "频段配置", 
    "天线方向图与波束成形分析", 
    "性能评估"
])

with tab1:
    st.header("雷达系统参数")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本参数")
        
        radar_type = st.selectbox(
            "雷达类型",
            ["预警雷达", "火控雷达", "搜索雷达", "跟踪雷达", "气象雷达", "自定义雷达"],
            index=0
        )
        
        radar_x = st.number_input(
            "雷达X坐标 (米)",
            min_value=-10000,
            max_value=10000,
            value=0,
            step=100
        )
        
        radar_y = st.number_input(
            "雷达Y坐标 (米)",
            min_value=-10000,
            max_value=10000,
            value=0,
            step=100
        )
        
        radar_z = st.number_input(
            "雷达高度 (米)",
            min_value=0,
            max_value=1000,
            value=50,
            step=10
        )
        
        max_range = st.slider(
            "最大探测距离 (km)",
            min_value=10,
            max_value=500,
            value=100,
            step=10
        )
        
        min_range = st.slider(
            "最小探测距离 (m)",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100
        )
    
    with col2:
        st.subheader("性能参数")
        
        peak_power = st.select_slider(
            "峰值功率 (kW)",
            options=[10, 50, 100, 500, 1000, 5000, 10000],
            value=1000
        )
        
        average_power = st.number_input(
            "平均功率 (kW)",
            min_value=1.0,
            max_value=1000.0,
            value=10.0,
            step=1.0
        )
        
        pulse_width = st.select_slider(
            "脉冲宽度 (μs)",
            options=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
            value=1.0
        )
        
        prf = st.select_slider(
            "脉冲重复频率 (Hz)",
            options=[100, 500, 1000, 2000, 5000, 10000],
            value=1000
        )
        
        antenna_gain = st.slider(
            "天线增益 (dB)",
            min_value=20,
            max_value=60,
            value=40,
            step=1
        )
        
        noise_figure = st.slider(
            "噪声系数 (dB)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.1
        )
    
    # 雷达方程计算
    st.subheader("雷达方程参数")
    
    col3, col4 = st.columns(2)
    
    with col3:
        wavelength = st.number_input(
            "波长 (m)",
            min_value=0.01,
            max_value=1.0,
            value=0.1,
            step=0.01,
            format="%.3f"
        )
        
        target_rcs = st.number_input(
            "目标RCS (m²)",
            min_value=0.01,
            max_value=100.0,
            value=1.0,
            step=0.1
        )
        
        system_loss = st.slider(
            "系统损耗 (dB)",
            min_value=0,
            max_value=20,
            value=6,
            step=1
        )
    
    with col4:
        # 计算雷达探测距离
        freq = constants.c / wavelength
        
        # 简化的雷达方程
        snr_min = 13  # dB，最小可检测信噪比
        pulse_energy = peak_power * 1000 * pulse_width * 1e-6
        avg_power_w = average_power * 1000
        
        # 计算最大探测距离
        max_detect_range = ((pulse_energy * antenna_gain**2 * wavelength**2 * target_rcs) / 
                           ((4*np.pi)**3 * 10**(snr_min/10) * 10**(noise_figure/10) * 10**(system_loss/10)))**(1/4)
        
        st.metric("雷达频率", f"{freq/1e9:.2f} GHz")
        st.metric("脉冲能量", f"{pulse_energy:.2f} J")
        st.metric("理论最大探测距离", f"{max_detect_range/1000:.1f} km")

with tab2:
    st.header("雷达频段配置")
    
    # 频段信息
    frequency_bands = {
        'L波段': {'freq_range': (1e9, 2e9), 'wavelength': (0.15, 0.3), 'applications': '远程预警'},
        'S波段': {'freq_range': (2e9, 4e9), 'wavelength': (0.075, 0.15), 'applications': '中程搜索'},
        'C波段': {'freq_range': (4e9, 8e9), 'wavelength': (0.0375, 0.075), 'applications': '火控跟踪'},
        'X波段': {'freq_range': (8e9, 12e9), 'wavelength': (0.025, 0.0375), 'applications': '精确制导'},
        'Ku波段': {'freq_range': (12e9, 18e9), 'wavelength': (0.0167, 0.025), 'applications': '高分辨率'},
        'Ka波段': {'freq_range': (26.5e9, 40e9), 'wavelength': (0.0075, 0.0113), 'applications': '卫星通信'}
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("频段选择")
        
        selected_band = st.selectbox(
            "选择雷达频段",
            list(frequency_bands.keys()),
            index=1
        )
        
        band_info = frequency_bands[selected_band]
        
        # 频段参数调整
        freq_min, freq_max = band_info['freq_range']
        center_freq = st.slider(
            "中心频率 (GHz)",
            min_value=freq_min/1e9,
            max_value=freq_max/1e9,
            value=(freq_min + freq_max)/(2 * 1e9),
            step=0.1
        )
        
        bandwidth = st.slider(
            "带宽 (MHz)",
            min_value=1,
            max_value=int((freq_max - freq_min)/1e6),
            value=int((freq_max - freq_min)/(4 * 1e6)),
            step=1
        )
        
        # 计算波长
        wavelength_calc = constants.c / (center_freq * 1e9)
        
        st.metric("中心频率", f"{center_freq:.2f} GHz")
        st.metric("对应波长", f"{wavelength_calc*100:.2f} cm")
        st.metric("带宽", f"{bandwidth} MHz")
    
    with col2:
        st.subheader("频段特性")
        
        st.markdown(f"""
        **{selected_band} 特性:**
        
        - 频率范围: {freq_min/1e9:.1f}-{freq_max/1e9:.1f} GHz
        - 波长范围: {band_info['wavelength'][0]*100:.1f}-{band_info['wavelength'][1]*100:.1f} cm
        - 主要应用: {band_info['applications']}
        
        **传播特性:**
        - 大气衰减: {'低' if selected_band in ['L', 'S'] else '中' if selected_band in ['C', 'X'] else '高'}
        - 雨衰减: {'低' if selected_band in ['L', 'S'] else '中' if selected_band == 'C' else '高'}
        - 分辨率: {'低' if selected_band in ['L', 'S'] else '中' if selected_band == 'C' else '高'}
        """)
    
    # 频段比较图
    st.subheader("雷达频段比较")
    
    fig = go.Figure()
    
    bands = list(frequency_bands.keys())
    center_freqs = [(freq_min + freq_max)/(2 * 1e9) for freq_min, freq_max in 
                   [band_info['freq_range'] for band_info in frequency_bands.values()]]
    
    fig.add_trace(go.Bar(
        x=bands,
        y=center_freqs,
        marker_color='indianred',
        text=[f"{freq:.1f} GHz" for freq in center_freqs],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="雷达频段中心频率比较",
        xaxis_title="频段",
        yaxis_title="中心频率 (GHz)",
        height=400
    )
    
    st.plotly_chart(fig, width='stretch')

with tab3:
    st.header("天线方向图与波束成形分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("天线参数配置")
        
        # 天线类型
        antenna_type = st.selectbox(
            "天线类型",
            ["抛物面天线", "阵列天线", "平板裂缝天线", "相控阵天线", "喇叭天线"],
            index=1,
            key="tab3_antenna_type"
        )
        
        # 阵列天线参数
        if antenna_type in ["阵列天线", "相控阵天线"]:
            st.markdown("**阵列参数**")
            
            col_array1, col_array2 = st.columns(2)
            
            with col_array1:
                n_elements_x = st.slider(
                    "X方向阵元数",
                    min_value=1,
                    max_value=50,
                    value=8,
                    step=1,
                    key="tab3_n_elements_x"
                )
            
            with col_array2:
                n_elements_y = st.slider(
                    "Y方向阵元数",
                    min_value=1,
                    max_value=50,
                    value=8,
                    step=1,
                    key="tab3_n_elements_y"
                )
            
            element_spacing = st.slider(
                "阵元间距 (波长)",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.1,
                key="tab3_element_spacing"
            )
        
        st.markdown("**天线特性**")
        
        antenna_gain_db = st.slider(
            "天线增益 (dB)",
            min_value=20,
            max_value=60,
            value=40,
            step=1,
            key="tab3_antenna_gain"
        )
        
        hpbw = st.slider(
            "3dB波束宽度 (°)",
            min_value=0.1,
            max_value=20.0,
            value=3.0,
            step=0.1,
            key="tab3_hpbw"
        )
        
        # 频率设置
        freq_ghz = st.slider(
            "工作频率 (GHz)",
            min_value=1.0,
            max_value=100.0,
            value=3.0,
            step=0.1,
            key="tab3_freq_ghz"
        )
        
        # 极化方式
        polarization = st.selectbox(
            "极化方式",
            ["水平极化", "垂直极化", "圆极化", "线极化"],
            key="tab3_polarization"
        )
    
    with col2:
        st.subheader("波束成形参数")
        
        # 波束指向控制
        steer_azimuth = st.slider(
            "方位指向 (°)",
            min_value=-60,
            max_value=60,
            value=0,
            step=1,
            key="tab3_steer_azimuth"
        )
        
        steer_elevation = st.slider(
            "俯仰指向 (°)",
            min_value=-60,
            max_value=60,
            value=0,
            step=1,
            key="tab3_steer_elevation"
        )
        
        # 副瓣电平
        sidelobe_level = st.slider(
            "副瓣电平 (dB)",
            min_value=-50,
            max_value=-10,
            value=-20,
            step=1,
            key="tab3_sidelobe_level"
        )
        
        # 波束形状控制
        st.markdown("**波束形状控制**")
        
        # 修复1：添加Sinc函数选项
        beam_shape = st.selectbox(
            "波束形状",
            ["高斯波束", "切比雪夫波束", "泰勒加权", "均匀分布", "Sinc波束"],
            key="tab3_beam_shape"
        )
        
        if beam_shape == "切比雪夫波束":
            sidelobe_ratio = st.slider(
                "主副瓣比 (dB)",
                min_value=20,
                max_value=50,
                value=30,
                step=1,
                key="tab3_sidelobe_ratio"
            )
        
        # 扫描模式
        st.markdown("**扫描特性**")
        
        col_scan1, col_scan2 = st.columns(2)
        
        with col_scan1:
            scan_type = st.selectbox(
                "扫描方式",
                ["机械扫描", "电子扫描", "混合扫描"],
                key="tab3_scan_type"
            )
        
        with col_scan2:
            scan_rate = st.number_input(
                "扫描速率 (°/s)",
                min_value=1,
                max_value=1000,
                value=100,
                step=10,
                key="tab3_scan_rate"
            )
        
        # 波束宽度统计
        st.markdown("**波束特性**")
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.metric("波束宽度", f"{hpbw:.1f}°")
            st.metric("增益", f"{antenna_gain_db:.0f} dB")
        
        with col_stats2:
            st.metric("波长", f"{300/freq_ghz:.1f} mm")
            st.metric("指向", f"({steer_azimuth}°, {steer_elevation}°)")
    
    # 3D天线方向图
    st.subheader("3D天线方向图")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**3D波束方向图**")
        
        # 创建网格
        theta = np.linspace(-np.pi/2, np.pi/2, 60)  # 方位角
        phi = np.linspace(-np.pi/2, np.pi/2, 60)    # 俯仰角
        Theta, Phi = np.meshgrid(theta, phi)
        
        # 波束指向（弧度）- 在所有天线类型中都需要
        theta0 = np.radians(steer_azimuth)
        phi0 = np.radians(steer_elevation)
        
        # 计算天线方向图（基于天线类型）
        if antenna_type in ["阵列天线", "相控阵天线"]:
            # 阵列天线方向图
            # 阵列因子
            d = element_spacing * constants.c / (freq_ghz * 1e9)  # type: ignore # 物理间距
            
            # 简化阵列因子计算
            k = 2 * np.pi * freq_ghz * 1e9 / constants.c
            u = np.sin(Theta) * np.cos(Phi) - np.sin(theta0) * np.cos(phi0)
            v = np.sin(Theta) * np.sin(Phi) - np.sin(theta0) * np.sin(phi0)
            
            # 阵列因子
            AF_x = np.sin(n_elements_x * k * d * u / 2) / (n_elements_x * np.sin(k * d * u / 2) + 1e-10) # type: ignore
            AF_y = np.sin(n_elements_y * k * d * v / 2) / (n_elements_y * np.sin(k * d * v / 2) + 1e-10) # type: ignore
            
            AF = AF_x * AF_y
            
            # 修复2：根据波束形状应用不同的加权
            if beam_shape == "切比雪夫波束":
                # 简化切比雪夫加权
                R = 10**(sidelobe_ratio/20) # type: ignore
                n = np.arange(-n_elements_x/2, n_elements_x/2) # type: ignore
                w = np.cos(np.pi * n / (n_elements_x-1))  # type: ignore # 简化切比雪夫
                w = w / np.sum(w)
                AF = AF * w[:, np.newaxis]
            elif beam_shape == "Sinc波束":
                # Sinc函数波束
                # 计算归一化的角度偏移
                u_norm = (Theta - theta0) / (np.radians(hpbw)/2)
                v_norm = (Phi - phi0) / (np.radians(hpbw)/2)
                
                # 计算Sinc函数
                AF = np.sinc(u_norm) * np.sinc(v_norm)
            elif beam_shape == "泰勒加权":
                # 简化泰勒加权
                n_bar = 4
                SLL = 10**(sidelobe_level/20)
                sigma = n_bar / np.sqrt(np.log(SLL) + n_bar**2)
                n = np.arange(-n_elements_x/2, n_elements_x/2) # type: ignore
                w = 1 + 0.5 * np.cos(2*np.pi*n/(n_elements_x-1)) # type: ignore
                w = w / np.sum(w)
                AF = AF * w[:, np.newaxis]
            elif beam_shape == "均匀分布":
                # 均匀分布，不需要额外加权
                pass
            
            # 添加阵元方向图
            element_pattern = np.cos(Theta)  # 简化阵元方向图
            
            # 总方向图
            pattern = AF * element_pattern
            
        else:
            # 抛物面天线方向图（根据波束形状选择不同模型）
            theta_bw = np.radians(hpbw)
            theta_offset = Theta - theta0
            phi_offset = Phi - phi0
            
            if beam_shape == "高斯波束":
                pattern = np.exp(-2.77 * (theta_offset**2 + phi_offset**2) / theta_bw**2)
            elif beam_shape == "Sinc波束":
                # Sinc函数波束
                u = np.pi * theta_offset / (theta_bw/2)
                v = np.pi * phi_offset / (theta_bw/2)
                pattern = np.sinc(u/np.pi) * np.sinc(v/np.pi)
            else:
                # 默认高斯波束
                pattern = np.exp(-2.77 * (theta_offset**2 + phi_offset**2) / theta_bw**2)
        
        # 转换为dB
        pattern_db = 20 * np.log10(np.abs(pattern) + 1e-10)
        
        # 归一化
        pattern_db = pattern_db - np.max(pattern_db)
        
        # 限制副瓣电平
        pattern_db = np.maximum(pattern_db, sidelobe_level)
        
        # 转换为直角坐标
        R = 10**(pattern_db/20)  # 转换为线性
        X = R * np.sin(Theta) * np.cos(Phi)
        Y = R * np.sin(Theta) * np.sin(Phi)
        Z = R * np.cos(Theta)
        
        # 创建3D图
        fig_3d = go.Figure(data=[
            go.Surface(
                x=X, y=Y, z=Z,
                surfacecolor=pattern_db,
                colorscale='Viridis',
                opacity=0.8,
                contours={
                    "z": {"show": True, "usecolormap": True, "highlightcolor": "limegreen"}
                },
                # 修复4：修正colorbar配置
                colorbar=dict(
                    title="增益 (dB)",
                    tickfont=dict(size=10)  # 使用tickfont
                )
            )
        ])
        
        # 添加坐标轴
        axis_len = 1.5
        fig_3d.add_trace(go.Scatter3d(
            x=[0, axis_len], y=[0, 0], z=[0, 0],
            mode='lines+text',
            line=dict(color='red', width=4),
            text=['', 'X'],
            textposition="top center",
            showlegend=False
        ))
        fig_3d.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, axis_len], z=[0, 0],
            mode='lines+text',
            line=dict(color='green', width=4),
            text=['', 'Y'],
            textposition="top center",
            showlegend=False
        ))
        fig_3d.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[0, axis_len],
            mode='lines+text',
            line=dict(color='blue', width=4),
            text=['', 'Z'],
            textposition="top center",
            showlegend=False
        ))
        
        fig_3d.update_layout(
            title=f"3D波束方向图 (方位: {steer_azimuth}°, 俯仰: {steer_elevation}°)",
            scene=dict(
                xaxis_title="X (归一化)",
                yaxis_title="Y (归一化)", 
                zaxis_title="Z (归一化)",
                aspectmode="cube",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.0)
                )
            ),
            height=500
        )
        
        st.plotly_chart(fig_3d, width='stretch')
    
    with col4:
        st.markdown("**天线方向剖面图**")
        
        # 创建子图
        from plotly.subplots import make_subplots
        
        # 方位方向图切片
        phi_slice = np.radians(steer_elevation)
        theta_range = np.linspace(-90, 90, 181)
        theta_rad = np.radians(theta_range)
        
        if antenna_type in ["阵列天线", "相控阵天线"]:
            # 计算方位切片
            u_slice = np.sin(theta_rad) * np.cos(phi_slice) - np.sin(np.radians(steer_azimuth)) * np.cos(phi_slice)
            v_slice = np.sin(theta_rad) * np.sin(phi_slice) - np.sin(np.radians(steer_azimuth)) * np.sin(phi_slice)
            
            AF_x_slice = np.sin(n_elements_x * k * d * u_slice / 2) / (n_elements_x * np.sin(k * d * u_slice / 2) + 1e-10) # type: ignore
            AF_y_slice = np.sin(n_elements_y * k * d * v_slice / 2) / (n_elements_y * np.sin(k * d * v_slice / 2) + 1e-10) # type: ignore
            
            AF_slice = AF_x_slice * AF_y_slice
            element_pattern_slice = np.cos(theta_rad)
            pattern_slice = AF_slice * element_pattern_slice
            
            # 应用波束形状
            if beam_shape == "Sinc波束":
                # Sinc函数波束
                u_norm = (theta_rad - np.radians(steer_azimuth)) / (np.radians(hpbw)/2)
                pattern_slice = np.sinc(u_norm/np.pi)
                
        else:
            # 高斯近似
            theta_bw = np.radians(hpbw)
            
            if beam_shape == "高斯波束":
                pattern_slice = np.exp(-2.77 * (theta_rad - np.radians(steer_azimuth))**2 / theta_bw**2)
            elif beam_shape == "Sinc波束":
                u = np.pi * (theta_rad - np.radians(steer_azimuth)) / (theta_bw/2)
                pattern_slice = np.sinc(u/np.pi)
            else:
                pattern_slice = np.exp(-2.77 * (theta_rad - np.radians(steer_azimuth))**2 / theta_bw**2)
        
        pattern_slice_db = 20 * np.log10(np.abs(pattern_slice) + 1e-10)
        pattern_slice_db = pattern_slice_db - np.max(pattern_slice_db)
        
        # 俯仰方向图切片
        theta_slice = np.radians(steer_azimuth)
        phi_range = np.linspace(-90, 90, 181)
        phi_rad = np.radians(phi_range)
        
        if antenna_type in ["阵列天线", "相控阵天线"]:
            u_slice2 = np.sin(theta_slice) * np.cos(phi_rad) - np.sin(theta_slice) * np.cos(np.radians(steer_elevation))
            v_slice2 = np.sin(theta_slice) * np.sin(phi_rad) - np.sin(theta_slice) * np.sin(np.radians(steer_elevation))
            
            AF_x_slice2 = np.sin(n_elements_x * k * d * u_slice2 / 2) / (n_elements_x * np.sin(k * d * u_slice2 / 2) + 1e-10) # type: ignore
            AF_y_slice2 = np.sin(n_elements_y * k * d * v_slice2 / 2) / (n_elements_y * np.sin(k * d * v_slice2 / 2) + 1e-10) # type: ignore
            
            AF_slice2 = AF_x_slice2 * AF_y_slice2
            element_pattern_slice2 = np.cos(phi_rad)
            pattern_slice2 = AF_slice2 * element_pattern_slice2
            
            # 应用波束形状
            if beam_shape == "Sinc波束":
                v_norm = (phi_rad - np.radians(steer_elevation)) / (np.radians(hpbw)/2)
                pattern_slice2 = np.sinc(v_norm/np.pi)
                
        else:
            theta_bw = np.radians(hpbw)  # 重新定义theta_bw
            
            if beam_shape == "高斯波束":
                pattern_slice2 = np.exp(-2.77 * (phi_rad - np.radians(steer_elevation))**2 / theta_bw**2)
            elif beam_shape == "Sinc波束":
                v = np.pi * (phi_rad - np.radians(steer_elevation)) / (theta_bw/2)
                pattern_slice2 = np.sinc(v/np.pi)
            else:
                pattern_slice2 = np.exp(-2.77 * (phi_rad - np.radians(steer_elevation))**2 / theta_bw**2)
        
        pattern_slice2_db = 20 * np.log10(np.abs(pattern_slice2) + 1e-10)
        pattern_slice2_db = pattern_slice2_db - np.max(pattern_slice2_db)
        
        # 创建子图
        fig_slices = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f"方位方向图 ({beam_shape})", f"俯仰方向图 ({beam_shape})"),
            vertical_spacing=0.15
        )
        
        # 添加方位切片
        fig_slices.add_trace(
            go.Scatter(
                x=theta_range, 
                y=pattern_slice_db,
                mode='lines',
                line=dict(color='cyan', width=2),
                name='方位方向图',
                fill='tozeroy',
                fillcolor='rgba(0, 255, 255, 0.2)'
            ),
            row=1, col=1
        )
        
        # 添加-3dB线
        fig_slices.add_hline(y=-3, line_dash="dash", line_color="red", 
                            annotation_text="-3dB", annotation_position="top right",
                            row=1, col=1) # type: ignore
        
        # 添加波束中心线
        fig_slices.add_vline(x=steer_azimuth, line_dash="dash", line_color="white",
                           annotation_text="波束中心", annotation_position="top right",
                           row=1, col=1) # type: ignore
        
        # 计算3dB波束宽度
        az_3db_idx = np.where(pattern_slice_db >= -3)[0]
        if len(az_3db_idx) > 1:
            az_3db_width = theta_range[az_3db_idx[-1]] - theta_range[az_3db_idx[0]]
        else:
            az_3db_width = hpbw
        
        # 添加3dB波束宽度标注
        if len(az_3db_idx) > 1:
            center_idx = len(theta_range) // 2
            fig_slices.add_annotation(
                x=theta_range[center_idx],
                y=-5,
                text=f"3dB宽度: {az_3db_width:.1f}°",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=30,
                row=1, col=1
            )
        
        # 添加俯仰切片
        fig_slices.add_trace(
            go.Scatter(
                x=phi_range, 
                y=pattern_slice2_db,
                mode='lines',
                line=dict(color='magenta', width=2),
                name='俯仰方向图',
                fill='tozeroy',
                fillcolor='rgba(255, 0, 255, 0.2)'
            ),
            row=2, col=1
        )
        
        # 添加-3dB线
        fig_slices.add_hline(y=-3, line_dash="dash", line_color="red", 
                            annotation_text="-3dB", annotation_position="top right",
                            row=2, col=1) # type: ignore
        
        # 添加波束中心线
        fig_slices.add_vline(x=steer_elevation, line_dash="dash", line_color="white",
                           annotation_text="波束中心", annotation_position="top right",
                           row=2, col=1) # type: ignore
        
        # 计算3dB波束宽度
        el_3db_idx = np.where(pattern_slice2_db >= -3)[0]
        if len(el_3db_idx) > 1:
            el_3db_width = phi_range[el_3db_idx[-1]] - phi_range[el_3db_idx[0]]
        else:
            el_3db_width = hpbw
        
        # 添加3dB波束宽度标注
        if len(el_3db_idx) > 1:
            center_idx = len(phi_range) // 2
            fig_slices.add_annotation(
                x=phi_range[center_idx],
                y=-5,
                text=f"3dB宽度: {el_3db_width:.1f}°",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=30,
                row=2, col=1
            )
        
        # 更新布局
        fig_slices.update_layout(
            height=500,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        # 更新子图样式
        for i in [1, 2]:
            fig_slices.update_xaxes(
                title_text="角度 (°)",
                gridcolor='rgba(100, 100, 100, 0.3)',
                linecolor='rgba(200, 200, 200, 0.5)',
                row=i, col=1
            )
            fig_slices.update_yaxes(
                title_text="增益 (dB)",
                gridcolor='rgba(100, 100, 100, 0.3)',
                linecolor='rgba(200, 200, 200, 0.5)',
                row=i, col=1
            )
        
        st.plotly_chart(fig_slices, width='stretch')
    
    # 极坐标波束图
    st.subheader("极坐标波束图")
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("**极坐标方向图**")
        
        # 创建极坐标方向图
        theta_polar = np.linspace(0, 2*np.pi, 360)
        
        # 根据波束形状创建不同的波束
        beam_width_rad = np.radians(hpbw)
        beam_center = np.radians(steer_azimuth)
        
        if beam_shape == "高斯波束":
            pattern_polar = np.exp(-4 * np.log(2) * (theta_polar - beam_center)**2 / beam_width_rad**2)
        elif beam_shape == "Sinc波束":
            u = np.pi * (theta_polar - beam_center) / (beam_width_rad/2)
            pattern_polar = np.abs(np.sinc(u/np.pi))
        elif beam_shape == "切比雪夫波束":
            pattern_polar = np.exp(-4 * np.log(2) * (theta_polar - beam_center)**2 / beam_width_rad**2)
            # 简化切比雪夫波束
            pattern_polar = pattern_polar + 0.2 * np.exp(-4 * np.log(2) * (theta_polar - beam_center - beam_width_rad*1.5)**2 / (beam_width_rad/2)**2)
            pattern_polar = pattern_polar + 0.2 * np.exp(-4 * np.log(2) * (theta_polar - beam_center + beam_width_rad*1.5)**2 / (beam_width_rad/2)**2)
        else:
            pattern_polar = np.exp(-4 * np.log(2) * (theta_polar - beam_center)**2 / beam_width_rad**2)
        
        # 转换为dB
        pattern_polar_db = 20 * np.log10(pattern_polar + 1e-10)
        pattern_polar_db = pattern_polar_db - np.max(pattern_polar_db)
        
        # 创建极坐标图
        fig_polar = go.Figure()
        
        # 添加方向图
        fig_polar.add_trace(go.Scatterpolar(
            r=10**(pattern_polar_db/20),  # 转换为线性
            theta=np.degrees(theta_polar),
            mode='lines',
            line=dict(color='lime', width=2),
            fill='toself',
            fillcolor='rgba(0, 255, 0, 0.2)',
            name=f'{beam_shape}'
        ))
        
        # 添加波束中心线
        fig_polar.add_trace(go.Scatterpolar(
            r=[0, 1],
            theta=[steer_azimuth, steer_azimuth],
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name='波束中心'
        ))
        
        # 添加-3dB线
        fig_polar.add_trace(go.Scatterpolar(
            r=[0.5, 0.5],
            theta=np.linspace(0, 360, 100),
            mode='lines',
            line=dict(color='white', width=1, dash='dot'),
            name='-3dB线'
        ))
        
        fig_polar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    gridcolor='rgba(100, 100, 100, 0.3)',
                    linecolor='rgba(200, 200, 200, 0.5)'
                ),
                angularaxis=dict(
                    gridcolor='rgba(100, 100, 100, 0.3)',
                    linecolor='rgba(200, 200, 200, 0.5)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=True,
            title=f"极坐标波束方向图 ({beam_shape})",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig_polar, width='stretch')
    
    with col6:
        st.markdown("**波束特性分析**")
        st.markdown("---")
        
        # 波束参数统计
        stats_col1, stats_col2 = st.columns(2)
        
        with stats_col1:
            st.markdown("**基本参数**")
            st.metric("波束形状", beam_shape)
            st.metric("波束宽度", f"{hpbw:.1f}°")
            st.metric("增益", f"{antenna_gain_db:.0f} dB")
            st.metric("频率", f"{freq_ghz:.1f} GHz")
        
        with stats_col2:
            st.markdown("**方向图特性**")
            st.metric("方位3dB宽度", f"{az_3db_width:.1f}°")
            st.metric("俯仰3dB宽度", f"{el_3db_width:.1f}°")
            st.metric("副瓣电平", f"{sidelobe_level:.0f} dB")
            st.metric("指向精度", "±0.1°")
        
        st.markdown("---")
    col7, col8 = st.columns(2)

    with col7:

        st.markdown("**天线信息**")
        array_config = f'{n_elements_x if antenna_type in ["阵列天线", "相控阵天线"] else "N/A"} × {n_elements_y if antenna_type in ["阵列天线", "相控阵天线"] else "N/A"}' # type: ignore
        st.markdown(f"""
        **天线类型**: {antenna_type}
        
        **阵列配置**: {array_config}
        
        **极化方式**: {polarization}
        
        **波束形状**: {beam_shape}
        
        **扫描方式**: {scan_type}
        """)

    with col8:
        # 波束成形技术说明
        st.markdown("**波束成形技术**")
        
        st.markdown("""
        波束成形通过控制阵列天线中每个阵元的相位和幅度，实现波束的指向和形状控制。
        
        主要技术参数：
        - 波束指向：方位{steer_azimuth}°，俯仰{steer_elevation}°
        - 波束形状：{beam_shape}
        - 副瓣抑制：{sidelobe_level}dB
        """.format(
            steer_azimuth=steer_azimuth,
            steer_elevation=steer_elevation,
            beam_shape=beam_shape,
            sidelobe_level=abs(sidelobe_level)
        ))
with tab4:
    st.header("雷达性能评估")
    
    if st.button("🔍 开始性能评估", type="primary"):
        with st.spinner("正在计算雷达性能..."):
            # 模拟性能计算
            import time
            time.sleep(1)
            
            # 从会话状态或其他选项卡获取变量
            # 如果beam_width未定义，使用默认值
            beam_width_val = beam_width_rad if 'beam_width' in locals() else 1.0
            
            # 计算性能指标
            detection_probability = 0.95
            false_alarm_rate = 1e-6
            range_resolution = constants.c * pulse_width * 1e-6 / 2
            doppler_resolution = 1 / (pulse_width * 1e-6)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("探测性能")
                
                # 确保所有值都是字符串
                metrics_data = {
                    '指标': ['探测概率', '虚警概率', '检测信噪比', '作用距离'],
                    '数值': [
                        f"{detection_probability*100:.1f}%",
                        f"{false_alarm_rate:.2e}",
                        f"{snr_min} dB",
                        f"{max_detect_range/1000:.1f} km"
                    ]
                }
                
                metrics_df = pd.DataFrame(metrics_data)
                # 确保数值列是字符串
                metrics_df['数值'] = metrics_df['数值'].astype(str)
                
                st.dataframe(metrics_df, width='stretch', hide_index=True)
                
                # 探测概率曲线
                ranges = np.linspace(10, max_range, 100)
                prob = detection_probability * np.exp(-ranges/(max_range/2))
                
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(
                    x=ranges, y=prob,
                    mode='lines',
                    line=dict(color='green', width=3),
                    name='探测概率'
                ))
                
                fig1.update_layout(
                    title="探测概率 vs 距离",
                    xaxis_title="距离 (km)",
                    yaxis_title="探测概率",
                    height=300
                )
                
                st.plotly_chart(fig1, width='stretch')
            
            with col2:
                st.subheader("分辨率性能")
                
                # 确保所有值都是字符串
                res_data = {
                    '指标': ['距离分辨率', '多普勒分辨率', '角度分辨率', '速度分辨率'],
                    '数值': [
                        f"{range_resolution:.1f} m",
                        f"{doppler_resolution:.0f} Hz",
                        f"{beam_width_val}°",
                        "待计算"
                    ]
                }
                
                res_df = pd.DataFrame(res_data)
                # 确保数值列是字符串
                res_df['数值'] = res_df['数值'].astype(str)
                
                st.dataframe(res_df, width='stretch', hide_index=True)
                
                # 性能评分
                performance_score = 85
                st.subheader("综合性能评分")
                st.progress(performance_score/100, text=f"综合性能: {performance_score}/100")
                
                if performance_score >= 80:
                    st.success("✅ 雷达性能优秀，适合当前任务")
                elif performance_score >= 60:
                    st.warning("⚠️ 雷达性能良好，可满足基本需求")
                else:
                    st.error("❌ 雷达性能不足，建议优化参数")
            
            st.success("性能评估完成！")

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **雷达参数**: 配置基本雷达参数
    2. **频段配置**: 选择雷达工作频段
    3. **扫描模式**: 设置扫描和跟踪模式
    4. **性能评估**: 评估雷达综合性能
    
    **重要参数:**
    - 峰值功率: 决定探测距离
    - 天线增益: 影响波束形状
    - 频率: 影响分辨率和衰减
    """)
    
    st.markdown("---")
    
    # 雷达方程计算器
    st.markdown("## ⚡ 雷达方程计算器")
    
    pt = st.number_input("发射功率 (W)", value=1e6)
    g = st.number_input("天线增益", value=1000.0)
    sigma = st.number_input("目标RCS (m²)", value=1.0)
    r = st.number_input("距离 (m)", value=10000.0)
    
    if st.button("计算接收功率"):
        # 简化雷达方程
        # 使用当前波长或默认值
        lambda_val = wavelength_calc if 'wavelength_calc' in locals() else 0.1
        pr = (pt * g**2 * lambda_val**2 * sigma) / ((4*np.pi)**3 * r**4)
        st.info(f"接收功率: {pr:.2e} W")
        st.info(f"接收功率(dBm): {10*np.log10(pr*1000):.1f} dBm")
    
    st.markdown("---")
    
    if st.button("🚀 进入下一步: 目标设置", type="primary", width='stretch'):
        st.switch_page("pages/3_🎯 目标设置.py")

# 保存配置
if st.button("💾 保存雷达配置到会话", type="primary", width='stretch'):
    st.session_state.radar_config = {
        'type': radar_type,
        'position': [radar_x, radar_y, radar_z],
        'max_range': max_range * 1000,  # 转换为米
        'peak_power': peak_power * 1000,  # 转换为瓦
        'frequency': center_freq * 1e9,  # 转换为Hz
        'wavelength': wavelength_calc,
        'antenna_gain': antenna_gain,
        'scan_type': scan_type
    }
    st.success("雷达配置已保存！")

# 页脚
st.markdown("---")
st.caption("雷达参数配置模块 | 用于雷达影响评估的雷达参数配置")