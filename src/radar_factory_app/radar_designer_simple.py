# radar_designer_refined.py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from dataclasses import dataclass
from typing import Dict
import logging
from datetime import datetime

# 设置日志级别
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('plotly').setLevel(logging.WARNING)

# 现在导入Streamlit
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="RadarSimPy 参数设计器",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS样式 - 优化配色方案
st.markdown("""
<style>
    :root {
        --primary-color: #1a73e8;      /* Google蓝色 */
        --secondary-color: #34a853;    /* Google绿色 */
        --accent-color: #ea4335;       /* Google红色 */
        --warning-color: #fbbc04;      /* Google黄色 */
        --text-primary: #202124;       /* 深灰色 */
        --text-secondary: #5f6368;     /* 中灰色 */
        --bg-light: #f8f9fa;           /* 浅灰背景 */
        --bg-white: #ffffff;           /* 白色 */
        --border-color: #dadce0;       /* 边框颜色 */
    }
    
    .main-header {
        font-size: 2.5rem;
        color: var(--primary-color);
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .sub-header {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* 优化后的参数表格样式 */
    .param-table-container {
        background: var(--bg-white);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid var(--border-color);
        box-shadow: 0 1px 2px rgba(60,64,67,0.1), 0 2px 6px rgba(60,64,67,0.15);
    }
    
    .param-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-family: 'Roboto Mono', 'Consolas', monospace;
    }
    
    .param-row {
        border-bottom: 1px solid #f1f3f4;
    }
    
    .param-row:last-child {
        border-bottom: none;
    }
    
    .param-cell {
        padding: 1.2rem 1rem;
        vertical-align: middle;
    }
    
    .param-name {
        color: var(--text-primary);
        font-weight: 500;
        font-size: 0.95rem;
        padding-right: 1rem;
        white-space: nowrap;
    }
    
    /* 类似图片的数值显示框，但优化了配色 */
    .param-value-display {
        background: linear-gradient(135deg, #f1f3f4 0%, #e8eaed 100%);
        border: 2px solid #dadce0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Roboto Mono', monospace;
        text-align: center;
        min-width: 140px;
        display: inline-block;
        transition: all 0.2s ease;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .param-value-display:hover {
        border-color: var(--primary-color);
        box-shadow: 0 1px 3px rgba(26,115,232,0.2);
    }
    
    /* 数值根据内容重要性着色 */
    .value-critical {
        color: var(--accent-color);
        font-weight: 700;
    }
    
    .value-important {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    .value-normal {
        color: var(--text-primary);
    }
    
    /* 指标卡片 - 现代化设计 */
    .metric-card {
        background: var(--bg-white);
        border-radius: 10px;
        padding: 1.2rem;
        margin: 0.5rem;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: var(--text-primary);
        font-size: 1.8rem;
        font-weight: 700;
        font-family: 'Roboto Mono', monospace;
    }
    
    .metric-unit {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-left: 0.25rem;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div > div {
        background-color: var(--primary-color);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #0d62d9;
        box-shadow: 0 2px 8px rgba(26,115,232,0.3);
        transform: translateY(-1px);
    }
    
    /* 滑块样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, #4285f4 100%);
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* 标签样式 */
    .stExpander > summary {
        color: var(--primary-color) !important;
        font-weight: 600 !important;
    }
    
    /* 警告和信息框样式 */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    .stAlert [data-testid="stMarkdownContainer"] {
        font-weight: 400;
    }
    
    /* 代码块样式 */
    .stCodeBlock {
        border-radius: 8px;
        border: 1px solid var(--border-color);
        background-color: #f8f9fa;
    }
    
    /* 分割线 */
    .stHorizontalBlock hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
    }
    
    /* 图表容器 */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* 参数值颜色编码 */
    .param-unit-hz { color: #1a73e8; }
    .param-unit-m { color: #34a853; }
    .param-unit-s { color: #ea4335; }
    .param-unit-w { color: #fbbc04; }
    .param-unit-db { color: #673ab7; }
    .param-unit-percent { color: #009688; }
</style>
""", unsafe_allow_html=True)

@dataclass
class RadarParameters:
    """雷达参数数据类"""
    # 系统参数
    frequency_hz: float = 10e9
    bandwidth_hz: float = 100e6
    prf_hz: float = 7000
    pulse_width_s: float = 10e-6
    pulses: int = 64
    peak_power_w: float = 100e3
    
    # 天线参数
    antenna_gain_db: float = 35.0
    antenna_loss_db: float = 2.0
    beamwidth_deg: float = 2.5
    aperture_m2: float = 0.5
    
    # 接收机参数
    noise_figure_db: float = 3.0
    system_loss_db: float = 5.0
    sampling_rate_hz: float = 150e6
    adc_bits: int = 12
    
    # 目标参数
    target_rcs_m2: float = 1.0
    target_range_m: float = 10000
    
    def to_radarsimpy_format(self) -> Dict:
        """转换为RadarSimPy格式"""
        return {
            'transmitter': {
                'freq_hz': self.frequency_hz,
                'bandwidth_hz': self.bandwidth_hz,
                'prf_hz': self.prf_hz,
                'pulse_width_s': self.pulse_width_s,
                'pulses': self.pulses,
                'power_w': self.peak_power_w
            },
            'antenna': {
                'gain_db': self.antenna_gain_db,
                'loss_db': self.antenna_loss_db,
                'beamwidth_deg': self.beamwidth_deg,
                'aperture_m2': self.aperture_m2
            },
            'receiver': {
                'noise_figure_db': self.noise_figure_db,
                'system_loss_db': self.system_loss_db,
                'sampling_rate_hz': self.sampling_rate_hz,
                'adc_bits': self.adc_bits
            },
            'target': {
                'rcs_m2': self.target_rcs_m2,
                'range_m': self.target_range_m
            }
        }
    
    def calculate_performance(self) -> Dict:
        """计算雷达性能指标"""
        c = 3e8
        
        # 基本参数
        wavelength = c / self.frequency_hz
        pri = 1 / self.prf_hz
        duty_cycle = self.pulse_width_s * self.prf_hz
        
        # 距离相关
        range_resolution = c / (2 * self.bandwidth_hz)
        max_unambiguous_range = c / (2 * self.prf_hz)
        min_range = c * self.pulse_width_s / 2
        
        # 速度相关
        max_unambiguous_velocity = wavelength * self.prf_hz / 4
        velocity_resolution = wavelength * self.prf_hz / (2 * self.pulses)
        
        # 功率相关
        avg_power = self.peak_power_w * duty_cycle
        pulse_energy = self.peak_power_w * self.pulse_width_s
        
        # 脉冲压缩比
        compression_ratio = self.pulse_width_s * self.bandwidth_hz
        
        # 模糊数
        range_ambiguity_number = self.target_range_m / max_unambiguous_range if max_unambiguous_range > 0 else 0
        
        # SNR计算
        k = 1.38e-23
        T0 = 290
        antenna_gain_linear = 10**(self.antenna_gain_db/10)
        system_loss_linear = 10**(self.system_loss_db/10)
        noise_figure_linear = 10**(self.noise_figure_db/10)
        
        snr = (self.peak_power_w * antenna_gain_linear**2 * wavelength**2 * 
               self.target_rcs_m2 * self.pulses) / (
               (4*np.pi)**3 * self.target_range_m**4 * k * T0 * 
               self.bandwidth_hz * noise_figure_linear * system_loss_linear)
        snr_db = 10 * np.log10(snr) if snr > 0 else -np.inf
        
        # 波束驻留时间
        dwell_time = pri * self.pulses
        # 多普勒容限
        doppler_tolerance = velocity_resolution / max_unambiguous_velocity * 100 if max_unambiguous_velocity > 0 else 0
        
        return {
            '波长_m': wavelength,
            'PRI_s': pri,
            '占空比_百分比': duty_cycle * 100,
            '距离分辨率_m': range_resolution,
            '最大不模糊距离_m': max_unambiguous_range,
            '最小探测距离_m': min_range,
            '最大不模糊速度_m/s': max_unambiguous_velocity,
            '速度分辨率_m/s': velocity_resolution,
            '平均功率_W': avg_power,
            '脉冲能量_J': pulse_energy,
            '脉冲压缩比': compression_ratio,
            '信噪比_dB': snr_db,
            '模糊数_距离': range_ambiguity_number,
            '波束驻留时间_s': dwell_time,
            '多普勒容限_百分比': doppler_tolerance
        }

def format_units_with_color(value: float, unit: str) -> str:
    """格式化单位显示并添加颜色类"""
    value_str = ""
    unit_class = ""
    
    if unit == 'Hz':
        if value >= 1e9:
            value_str = f"{value/1e9:.2f}"
            unit_str = "GHz"
        elif value >= 1e6:
            value_str = f"{value/1e6:.1f}"
            unit_str = "MHz"
        elif value >= 1e3:
            value_str = f"{value/1e3:.1f}"
            unit_str = "kHz"
        else:
            value_str = f"{value:.0f}"
            unit_str = "Hz"
        unit_class = "param-unit-hz"
    
    elif unit == 'W':
        if value >= 1e6:
            value_str = f"{value/1e6:.2f}"
            unit_str = "MW"
        elif value >= 1e3:
            value_str = f"{value/1e3:.2f}"
            unit_str = "kW"
        else:
            value_str = f"{value:.1f}"
            unit_str = "W"
        unit_class = "param-unit-w"
    
    elif unit == 's':
        if value < 1e-9:
            value_str = f"{value*1e12:.1f}"
            unit_str = "ps"
        elif value < 1e-6:
            value_str = f"{value*1e9:.1f}"
            unit_str = "ns"
        elif value < 1e-3:
            value_str = f"{value*1e6:.1f}"
            unit_str = "μs"
        elif value < 1:
            value_str = f"{value*1e3:.1f}"
            unit_str = "ms"
        else:
            value_str = f"{value:.3f}"
            unit_str = "s"
        unit_class = "param-unit-s"
    
    elif unit == 'm':
        if value >= 1000:
            value_str = f"{value/1000:.1f}"
            unit_str = "km"
        else:
            value_str = f"{value:.1f}"
            unit_str = "m"
        unit_class = "param-unit-m"
    
    elif unit == 'm/s':
        if value >= 1000:
            value_str = f"{value/1000:.1f}"
            unit_str = "km/s"
        else:
            value_str = f"{value:.1f}"
            unit_str = "m/s"
        unit_class = "param-unit-m"
    
    elif unit == 'dB':
        value_str = f"{value:.1f}"
        unit_str = "dB"
        unit_class = "param-unit-db"
    
    else:
        value_str = f"{value:.2f}"
        unit_str = unit
    
    return f'<span class="{unit_class}">{value_str} {unit_str}</span>'

def create_radar_preset(name: str) -> RadarParameters:
    """创建雷达预设"""
    presets = {
        "气象雷达": RadarParameters(
            frequency_hz=3e9,
            bandwidth_hz=1e6,
            prf_hz=1000,
            pulse_width_s=1e-6,
            pulses=128,
            peak_power_w=250e3,
            beamwidth_deg=1.0,
            antenna_gain_db=40.0
        ),
        "机载火控雷达": RadarParameters(
            frequency_hz=10e9,
            bandwidth_hz=100e6,
            prf_hz=10000,
            pulse_width_s=1e-6,
            pulses=256,
            peak_power_w=10e3,
            beamwidth_deg=3.0,
            antenna_gain_db=35.0
        ),
        "舰载搜索雷达": RadarParameters(
            frequency_hz=3e9,
            bandwidth_hz=10e6,
            prf_hz=500,
            pulse_width_s=100e-6,
            pulses=32,
            peak_power_w=1e6,
            beamwidth_deg=1.5,
            antenna_gain_db=45.0
        ),
        "汽车毫米波雷达": RadarParameters(
            frequency_hz=77e9,
            bandwidth_hz=500e6,
            prf_hz=2000,
            pulse_width_s=50e-9,
            pulses=256,
            peak_power_w=10,
            beamwidth_deg=20.0,
            antenna_gain_db=25.0
        )
    }
    return presets.get(name, RadarParameters())

def plot_performance_tradeoffs(params: RadarParameters):
    """绘制性能权衡图 - 优化配色"""
    c = 3e8
    
    # 计算不同PRF下的性能
    prf_range = np.logspace(2, 5, 50)
    wavelength = c / params.frequency_hz
    
    max_range = c / (2 * prf_range)
    max_velocity = wavelength * prf_range / 4
    velocity_res = wavelength * prf_range / (2 * params.pulses)
    
    # 当前参数点
    current_max_range = c / (2 * params.prf_hz)
    current_max_velocity = wavelength * params.prf_hz / 4
    current_velocity_res = wavelength * params.prf_hz / (2 * params.pulses)
    
    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '<b>最大不模糊距离 vs PRF</b>',
            '<b>最大不模糊速度 vs PRF</b>',
            '<b>速度分辨率 vs PRF</b>',
            '<b>距离-速度模糊区域</b>'
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.15
    )
    
    # 使用Material Design配色
    colors = ['#4285f4', '#34a853', '#ea4335', '#fbbc04']
    
    # 图1: 最大不模糊距离 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=max_range/1000, 
            mode='lines',
            line=dict(color=colors[0], width=2.5),
            name='最大不模糊距离',
            hovertemplate='PRF: %{x:.0f} Hz<br>最大距离: %{y:.1f} km<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color=colors[3],
        annotation_text=f"当前: {params.prf_hz/1e3:.1f} kHz",
        annotation_position="top right",
        annotation_font=dict(color=colors[3], size=10),
        row=1, col=1
    )
    
    # 图2: 最大不模糊速度 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=max_velocity*3.6,
            mode='lines',
            line=dict(color=colors[1], width=2.5),
            name='最大不模糊速度',
            hovertemplate='PRF: %{x:.0f} Hz<br>最大速度: %{y:.0f} km/h<extra></extra>'
        ),
        row=1, col=2
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color=colors[3],
        row=1, col=2
    )
    
    # 图3: 速度分辨率 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=velocity_res*3.6,
            mode='lines',
            line=dict(color=colors[2], width=2.5),
            name='速度分辨率',
            hovertemplate='PRF: %{x:.0f} Hz<br>速度分辨率: %{y:.1f} km/h<extra></extra>'
        ),
        row=2, col=1
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color=colors[3],
        row=2, col=1
    )
    
    # 图4: 模糊图
    fig.add_trace(
        go.Scatter(
            x=max_range/1000, 
            y=max_velocity*3.6, 
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(66, 133, 244, 0.1)',
            line=dict(color=colors[0], width=2.5),
            name='模糊区域',
            hovertemplate='最大距离: %{x:.1f} km<br>最大速度: %{y:.0f} km/h<extra></extra>'
        ),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=[current_max_range/1000], 
            y=[current_max_velocity*3.6],
            mode='markers',
            marker=dict(size=12, color=colors[3], symbol='diamond', 
                       line=dict(width=2, color='white')),
            name='当前参数',
            hovertemplate='距离: %{x:.1f} km<br>速度: %{y:.0f} km/h<extra></extra>'
        ),
        row=2, col=2
    )
    
    # 更新布局
    fig.update_layout(
        height=550,
        showlegend=True,
        template="plotly_white",
        title_text="<b>雷达性能权衡分析</b>",
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Roboto, Arial, sans-serif", size=12, color='#202124'),
        legend=dict(
            font=dict(color='#5f6368'),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#dadce0',
            borderwidth=1
        )
    )
    
    # 更新所有坐标轴
    axes_updates = dict(
        title_font=dict(size=13, color='#202124'),
        tickfont=dict(size=11, color='#5f6368'),
        gridcolor='rgba(0,0,0,0.1)',
        zerolinecolor='rgba(0,0,0,0.2)',
        linecolor='#202124'
    )
    
    fig.update_xaxes(**axes_updates, row=1, col=1, title_text="PRF (Hz)", type="log")
    fig.update_xaxes(**axes_updates, row=1, col=2, title_text="PRF (Hz)", type="log")
    fig.update_xaxes(**axes_updates, row=2, col=1, title_text="PRF (Hz)", type="log")
    fig.update_xaxes(**axes_updates, row=2, col=2, title_text="最大不模糊距离 (km)")
    
    fig.update_yaxes(**axes_updates, row=1, col=1, title_text="距离 (km)", type="log")
    fig.update_yaxes(**axes_updates, row=1, col=2, title_text="速度 (km/h)")
    fig.update_yaxes(**axes_updates, row=2, col=1, title_text="速度分辨率 (km/h)")
    fig.update_yaxes(**axes_updates, row=2, col=2, title_text="速度 (km/h)")
    
    # 更新子图标题
    for i, annotation in enumerate(fig['layout']['annotations']):
        annotation['font'] = dict(size=14, color='#202124', family="Roboto, sans-serif")
    
    return fig

def main():
    """主应用函数"""
    # 标题
    st.markdown('<h1 class="main-header">📡 RadarSimPy 雷达参数设计器</h1>', 
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">交互式设计雷达参数，优化性能指标，导出为RadarSimPy仿真配置</p>', 
                unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'current_preset' not in st.session_state:
        st.session_state.current_preset = "自定义"
    if 'show_config' not in st.session_state:
        st.session_state.show_config = False
    
    # 侧边栏 - 参数设置
    with st.sidebar:
        st.markdown('<h3 style="color: #1a73e8;">⚙️ 参数设置</h3>', unsafe_allow_html=True)
        
        # 预设选择
        st.markdown("**预设配置**")
        preset = st.selectbox(
            "选择雷达类型",
            ["自定义", "气象雷达", "机载火控雷达", "舰载搜索雷达", "汽车毫米波雷达"],
            index=0,
            label_visibility="collapsed"
        )
        
        if preset != "自定义":
            default_params = create_radar_preset(preset)
            st.success(f"已加载预设: **{preset}**")
        else:
            default_params = RadarParameters()
        
        st.markdown("---")
        
        # 发射机参数
        with st.expander("📡 发射机参数", expanded=True):
            col_freq, col_bw = st.columns(2)
            with col_freq:
                frequency_ghz = st.slider(
                    "载波频率 (GHz)",
                    1.0, 100.0,
                    value=default_params.frequency_hz/1e9,
                    step=0.1,
                    format="%.1f",
                    help="雷达工作频率"
                )
            
            with col_bw:
                bandwidth_mhz = st.slider(
                    "带宽 (MHz)",
                    1.0, 1000.0,
                    value=default_params.bandwidth_hz/1e6,
                    step=1.0,
                    format="%.0f",
                    help="发射信号带宽"
                )
            
            col_prf, col_pw = st.columns(2)
            with col_prf:
                prf_khz = st.slider(
                    "PRF (kHz)",
                    0.1, 50.0,
                    value=default_params.prf_hz/1e3,
                    step=0.1,
                    format="%.1f",
                    help="脉冲重复频率"
                )
            
            with col_pw:
                pulse_width_us = st.slider(
                    "脉冲宽度 (μs)",
                    0.01, 1000.0,
                    value=default_params.pulse_width_s*1e6,
                    step=0.1,
                    format="%.1f",
                    help="单个脉冲的持续时间"
                )
            
            pulses = st.slider(
                "脉冲数",
                8, 1024,
                value=default_params.pulses,
                step=8,
                help="一个CPI内的脉冲数量"
            )
            
            peak_power_kw = st.slider(
                "峰值功率 (kW)",
                0.1, 1000.0,
                value=default_params.peak_power_w/1e3,
                step=0.1,
                format="%.1f",
                help="发射脉冲的峰值功率"
            )
        
        # 天线参数
        with st.expander("📡 天线参数"):
            antenna_gain_db = st.slider(
                "天线增益 (dB)",
                10.0, 50.0,
                value=default_params.antenna_gain_db,
                step=0.5,
                format="%.1f"
            )
        
        # 目标参数
        with st.expander("🎯 目标参数"):
            target_range_km = st.slider(
                "目标距离 (km)",
                1.0, 200.0,
                value=default_params.target_range_m/1000,
                step=1.0,
                format="%.0f"
            )
    
    # 创建参数对象
    params = RadarParameters(
        frequency_hz=frequency_ghz * 1e9,
        bandwidth_hz=bandwidth_mhz * 1e6,
        prf_hz=prf_khz * 1e3,
        pulse_width_s=pulse_width_us * 1e-6,
        pulses=pulses,
        peak_power_w=peak_power_kw * 1e3,
        antenna_gain_db=antenna_gain_db,
        beamwidth_deg=default_params.beamwidth_deg,
        sampling_rate_hz=default_params.sampling_rate_hz,
        noise_figure_db=default_params.noise_figure_db,
        system_loss_db=default_params.system_loss_db,
        target_range_m=target_range_km * 1000,
        target_rcs_m2=default_params.target_rcs_m2
    )
    
    # 计算性能指标
    performance = params.calculate_performance()
    
    # 主界面布局
    col_main_left, col_main_right = st.columns([2, 1])
    
    with col_main_left:
        # 关键性能指标 - 现代化卡片设计
        st.markdown("### 📊 关键性能指标")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">距离分辨率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["距离分辨率_m"]:.2f}<span class="metric-unit">m</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">速度分辨率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["速度分辨率_m/s"]*3.6:.1f}<span class="metric-unit">km/h</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">最大距离</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["最大不模糊距离_m"]/1000:.1f}<span class="metric-unit">km</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">信噪比</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["信噪比_dB"]:.1f}<span class="metric-unit">dB</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # 性能权衡分析图
        st.markdown("### 📈 性能权衡分析")
        fig = plot_performance_tradeoffs(params)
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': True})
        
        # 详细参数表 - 优化版（模仿图片但改进配色）
        st.markdown("### 📋 详细参数表")
        
        # 创建HTML表格
        html_table = '''
        <div class="param-table-container">
        <table class="param-table">
        '''
        
        # 定义参数分组
        param_groups = [
            [
                ("波长", performance['波长_m'], "m"),
                ("PRI", performance['PRI_s'], "s"),
                ("占空比", performance['占空比_百分比'], "%"),
                ("脉冲能量", performance['脉冲能量_J'], "J"),
                ("脉冲压缩比", performance['脉冲压缩比'], ""),
                ("最小探测距离", performance['最小探测距离_m'], "m")
            ],
            [
                ("模糊数(距离)", performance['模糊数_距离'], ""),
                ("波束驻留时间", performance['波束驻留时间_s'], "s"),
                ("多普勒容限", performance['多普勒容限_百分比'], "%"),
                ("最大速度", performance['最大不模糊速度_m/s'] * 3.6, "km/h"),
                ("平均功率", performance['平均功率_W'], "W"),
                ("峰值功率", params.peak_power_w, "W")
            ]
        ]
        
        # 创建两列布局的表格
        for row_idx in range(0, len(param_groups[0]), 2):
            html_table += '<tr class="param-row">'
            
            # 第一列
            for col_idx in range(2):
                if row_idx < len(param_groups[0]):
                    name1, value1, unit1 = param_groups[0][row_idx]
                    value_str1 = format_units_with_color(value1, unit1)
                    html_table += f'''
                    <td class="param-cell">
                        <div class="param-name">{name1}</div>
                        <div class="param-value-display">{value_str1}</div>
                    </td>
                    '''
                
                # 第二列
                if row_idx + 1 < len(param_groups[0]):
                    name2, value2, unit2 = param_groups[0][row_idx + 1]
                    value_str2 = format_units_with_color(value2, unit2)
                    html_table += f'''
                    <td class="param-cell">
                        <div class="param-name">{name2}</div>
                        <div class="param-value-display">{value_str2}</div>
                    </td>
                    '''
                
                # 第三列（第二组的参数）
                if row_idx < len(param_groups[1]):
                    name3, value3, unit3 = param_groups[1][row_idx]
                    value_str3 = format_units_with_color(value3, unit3)
                    html_table += f'''
                    <td class="param-cell">
                        <div class="param-name">{name3}</div>
                        <div class="param-value-display">{value_str3}</div>
                    </td>
                    '''
                
                # 第四列
                if row_idx + 1 < len(param_groups[1]):
                    name4, value4, unit4 = param_groups[1][row_idx + 1]
                    value_str4 = format_units_with_color(value4, unit4)
                    html_table += f'''
                    <td class="param-cell">
                        <div class="param-name">{name4}</div>
                        <div class="param-value-display">{value_str4}</div>
                    </td>
                    '''
            
            html_table += '</tr>'
        
        html_table += '''
        </table>
        </div>
        '''
        
        st.markdown(html_table, unsafe_allow_html=True)
    
    with col_main_right:
        # 当前参数摘要
        st.markdown("### ⚙️ 当前参数")
        
        current_params = [
            ("频率", f"{frequency_ghz:.1f} GHz", "param-unit-hz"),
            ("带宽", f"{bandwidth_mhz:.0f} MHz", "param-unit-hz"),
            ("PRF", f"{prf_khz:.1f} kHz", "param-unit-hz"),
            ("脉宽", f"{pulse_width_us:.1f} μs", "param-unit-s"),
            ("脉冲数", f"{pulses}", ""),
            ("峰值功率", f"{peak_power_kw:.1f} kW", "param-unit-w"),
            ("天线增益", f"{antenna_gain_db:.1f} dB", "param-unit-db"),
            ("目标距离", f"{target_range_km:.0f} km", "param-unit-m")
        ]
        
        # 显示当前参数
        for name, value, unit_class in current_params:
            col_name, col_value = st.columns([2, 1])
            with col_name:
                st.markdown(f"**{name}**")
            with col_value:
                if unit_class:
                    st.markdown(f'<span class="{unit_class}">{value}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f"`{value}`")
        
        st.markdown("---")
        
        # 系统评估
        st.markdown("### 📈 系统评估")
        
        # 距离模糊评估
        if performance['模糊数_距离'] > 1:
            st.error(f"⚠️ **距离模糊风险**\n目标距离超过最大不模糊距离 {performance['模糊数_距离']:.1f}倍")
        else:
            st.success("✅ **距离无模糊**")
        
        # 占空比评估
        duty_cycle = performance['占空比_百分比']
        st.progress(min(duty_cycle / 20, 1.0), text=f"占空比: {duty_cycle:.2f}%")
        
        if duty_cycle > 10:
            st.warning("⚠️ 高占空比，注意系统散热")
        elif duty_cycle < 0.1:
            st.info("ℹ️ 低占空比，适合高峰值功率应用")
        else:
            st.success("✅ 占空比合理")
        
        # 采样率评估
        sampling_ratio = params.sampling_rate_hz / params.bandwidth_hz
        if sampling_ratio < 2:
            st.error(f"⚠️ **采样率不足** ({sampling_ratio:.1f}倍带宽)")
        else:
            st.success(f"✅ **采样率合理** ({sampling_ratio:.1f}倍带宽)")
        
        st.markdown("---")
        
        # 导出配置
        st.markdown("### 💾 导出配置")
        
        # 生成配置
        radarsimpy_config = params.to_radarsimpy_format()
        config_json = json.dumps(radarsimpy_config, indent=2)
        
        # 显示/隐藏配置
        if st.button("📄 显示JSON配置"):
            st.session_state.show_config = not st.session_state.show_config
        
        if st.session_state.show_config:
            st.code(config_json, language='json')
        
        # 下载按钮
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 下载JSON",
                data=config_json,
                file_name=f"radar_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                width='stretch'
            )
        
        with col_dl2:
            # 生成Python代码
            python_code = f'''# RadarSimPy 仿真代码
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import radarsimpy as rs
import numpy as np

# 雷达参数
radar = rs.Radar(
    transmitter={{
        'freq_hz': {params.frequency_hz},
        'bandwidth_hz': {params.bandwidth_hz},
        'prf_hz': {params.prf_hz},
        'pulse_width_s': {params.pulse_width_s},
        'pulses': {params.pulses},
        'power_w': {params.peak_power_w}
    }},
    antenna={{
        'gain_db': {params.antenna_gain_db},
        'loss_db': {params.antenna_loss_db},
        'beamwidth_deg': {params.beamwidth_deg},
        'aperture_m2': {params.aperture_m2}
    }},
    receiver={{
        'noise_figure_db': {params.noise_figure_db},
        'system_loss_db': {params.system_loss_db},
        'sampling_rate_hz': {params.sampling_rate_hz},
        'adc_bits': {params.adc_bits}
    }}
)

# 目标设置
target = {{
    'range_m': {params.target_range_m},
    'rcs_m2': {params.target_rcs_m2}
}}

print("雷达配置完成!")
print(f"频率: {{params.frequency_hz/1e9:.1f}} GHz")
print(f"带宽: {{params.bandwidth_hz/1e6:.0f}} MHz")
print(f"距离分辨率: {{3e8/(2*params.bandwidth_hz):.1f}} m")
print(f"最大不模糊距离: {{3e8/(2*params.prf_hz)/1000:.1f}} km")
'''
            
            st.download_button(
                label="🐍 下载Python",
                data=python_code,
                file_name=f"radar_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                mime="text/x-python",
                width='stretch'
            )
    
    # 系统建议
    st.markdown("---")
    st.markdown("### 💡 设计建议")
    
    col_advice1, col_advice2 = st.columns(2)
    
    with col_advice1:
        st.markdown("**雷达类型分析**")
        
        if params.frequency_hz < 3e9:
            radar_type = "🔴 低频雷达 (UHF/L波段)"
            advice = "适合远程监视、气象观测，但分辨率较低"
        elif params.frequency_hz < 10e9:
            radar_type = "🟡 中频雷达 (S/C波段)"
            advice = "平衡作用距离和分辨率，通用型雷达"
        elif params.frequency_hz < 30e9:
            radar_type = "🟢 高频雷达 (X/Ku波段)"
            advice = "高分辨率，适合精确跟踪和火控"
        else:
            radar_type = "🔵 毫米波雷达 (Ka/W波段)"
            advice = "极高分辨率，但作用距离有限"
        
        st.info(f"{radar_type}\n\n{advice}")
        
        # PRF模式分析
        if params.prf_hz < 1000:
            prf_mode = "低PRF模式"
            prf_advice = "适合远程探测，测速能力有限"
        elif params.prf_hz > 10000:
            prf_mode = "高PRF模式"
            prf_advice = "适合测速，距离模糊严重"
        else:
            prf_mode = "中PRF模式"
            prf_advice = "兼顾测距测速，需解模糊处理"
        
        st.info(f"**{prf_mode}**\n\n{prf_advice}")
    
    with col_advice2:
        st.markdown("**优化建议**")
        
        suggestions = []
        
        # 检查脉冲压缩比
        if performance['脉冲压缩比'] < 10:
            suggestions.append("考虑增加带宽以提高距离分辨率")
        elif performance['脉冲压缩比'] > 1000:
            suggestions.append("高脉冲压缩比需要高性能处理器")
        
        # 检查信噪比
        if performance['信噪比_dB'] < 10:
            suggestions.append("增加脉冲数或提高发射功率以改善信噪比")
        
        # 检查距离模糊
        if performance['模糊数_距离'] > 1:
            suggestions.append("使用PRF参差或中PRF模式解决距离模糊")
        
        # 检查占空比
        if performance['占空比_百分比'] > 10:
            suggestions.append("高占空比设计，注意热管理和功率消耗")
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(f"{i}. {suggestion}")
        else:
            st.success("当前参数配置合理，可直接用于仿真。")
    
    # 脚注
    st.markdown("---")
    st.caption(f"""
    **RadarSimPy参数设计器** • 基于简化雷达方程计算 • 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

if __name__ == "__main__":
    main()