"""
雷达参数配置页面
功能：配置雷达参数、频段、扫描模式等
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import constants

# 页面配置
st.set_page_config(
    page_title="雷达参数配置 | 雷达影响评估系统",
    layout="wide"
)

# 标题
st.title("📡 雷达参数配置")
st.markdown("配置雷达系统参数、频段选择和扫描模式")

# 初始化会话状态
if 'radar_config' not in st.session_state:
    st.session_state.radar_config = {}

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "雷达参数", 
    "频段配置", 
    "扫描模式", 
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
    st.header("扫描与跟踪模式")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("扫描模式")
        
        scan_type = st.selectbox(
            "扫描类型",
            ["机械扫描", "相控阵扫描", "频率扫描", "混合扫描"],
            index=1
        )
        
        if scan_type == "相控阵扫描":
            num_elements = st.slider(
                "阵元数量",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100
            )
            
            beam_width = st.slider(
                "波束宽度 (°)",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1
            )
        
        scan_rate = st.slider(
            "扫描速率 (rpm)",
            min_value=1,
            max_value=60,
            value=12,
            step=1
        )
        
        elevation_range = st.slider(
            "俯仰角范围 (°)",
            min_value=0,
            max_value=90,
            value=(0, 60)
        )
        
        azimuth_range = st.slider(
            "方位角范围 (°)",
            min_value=0,
            max_value=360,
            value=(0, 360)
        )
    
    with col2:
        st.subheader("跟踪模式")
        
        track_mode = st.multiselect(
            "跟踪模式选择",
            ["单目标跟踪", "多目标跟踪", "边扫描边跟踪", "自适应跟踪", "预测跟踪"],
            default=["单目标跟踪", "多目标跟踪"]
        )
        
        max_targets = st.slider(
            "最大跟踪目标数",
            min_value=1,
            max_value=200,
            value=50,
            step=1
        )
        
        update_rate = st.slider(
            "数据更新率 (Hz)",
            min_value=0.1,
            max_value=100.0,
            value=10.0,
            step=0.1
        )
        
        track_accuracy = st.select_slider(
            "跟踪精度",
            options=['低', '中', '高', '极高'],
            value='高'
        )
        
        # 跟踪性能指标
        st.metric("跟踪数据率", f"{update_rate} Hz")
        st.metric("可跟踪目标数", max_targets)
    
    # 扫描模式可视化
    st.subheader("扫描模式可视化")
    
    # 创建波束扫描示意图
    fig = go.Figure()
    
    # 天线波束
    theta = np.linspace(0, 2*np.pi, 100)
    
    for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
        r = 1
        x = r * np.cos(theta + angle) * 0.5
        y = r * np.sin(theta + angle) * 0.5
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color='blue', width=1),
            fill='toself',
            fillcolor='rgba(0, 0, 255, 0.2)',
            name=f'波束 {int(np.degrees(angle))}°'
        ))
    
    fig.update_layout(
        title="天线波束扫描示意图",
        xaxis_title="方位角",
        yaxis_title="俯仰角",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, width='stretch')

with tab4:
    st.header("雷达性能评估")
    
    if st.button("🔍 开始性能评估", type="primary"):
        with st.spinner("正在计算雷达性能..."):
            # 模拟性能计算
            import time
            time.sleep(1)
            
            # 计算性能指标
            detection_probability = 0.95
            false_alarm_rate = 1e-6
            range_resolution = constants.c * pulse_width * 1e-6 / 2
            doppler_resolution = 1 / (pulse_width * 1e-6)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("探测性能")
                
                metrics_data = {
                    '指标': ['探测概率', '虚警概率', '检测信噪比', '作用距离'],
                    '数值': [
                        f"{detection_probability*100:.1f}%",
                        f"{false_alarm_rate:.2e}",
                        f"{snr_min} dB",
                        f"{max_detect_range/1000:.1f} km"
                    ]
                }
                
                st.dataframe(pd.DataFrame(metrics_data), width='stretch', hide_index=True)
                
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
                
                res_data = {
                    '指标': ['距离分辨率', '多普勒分辨率', '角度分辨率', '速度分辨率'],
                    '数值': [
                        f"{range_resolution:.1f} m",
                        f"{doppler_resolution:.0f} Hz",
                        f"{beam_width}°",
                        "待计算"
                    ]
                }
                
                st.dataframe(pd.DataFrame(res_data), width='stretch', hide_index=True)
                
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
