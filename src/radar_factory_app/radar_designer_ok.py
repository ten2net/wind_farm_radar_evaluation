# radar_designer.py
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

# 页面配置必须在任何Streamlit命令之前
st.set_page_config(
    page_title="长城数字雷达参数设计器",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
 
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .warning-box {
        background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
        color: #333;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #ff4757;
    }
    .success-box {
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
        color: #333;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2ecc71;
    }
    .section-divider {
        border: none;
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        margin: 2rem 0;
        opacity: 0.3;
    }
    .preset-card {
        background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
        border: 2px solid #667eea;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .preset-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .preset-title {
        font-weight: 700;
        color: #333;
        font-size: 1.1rem;
    }
    .preset-desc {
        color: #666;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
    .param-value {
        font-weight: 600;
        color: #667eea;
    }
    /* 自定义滑块样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    /* 图表字体颜色增强 */
    .plotly-chart {
        color: #333 !important;
    }
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
        
        # SNR计算 (简化雷达方程)
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
            '模糊数_距离': range_ambiguity_number
        }

def format_units(value: float, unit: str) -> str:
    """格式化单位显示"""
    if unit == 'Hz':
        if value >= 1e9:
            return f"{value/1e9:.2f} GHz"
        elif value >= 1e6:
            return f"{value/1e6:.1f} MHz"
        elif value >= 1e3:
            return f"{value/1e3:.1f} kHz"
        else:
            return f"{value:.0f} Hz"
    elif unit == 'W':
        if value >= 1e6:
            return f"{value/1e6:.2f} MW"
        elif value >= 1e3:
            return f"{value/1e3:.2f} kW"
        else:
            return f"{value:.1f} W"
    elif unit == 's':
        if value < 1e-9:
            return f"{value*1e12:.1f} ps"
        elif value < 1e-6:
            return f"{value*1e9:.1f} ns"
        elif value < 1e-3:
            return f"{value*1e6:.1f} μs"
        elif value < 1:
            return f"{value*1e3:.1f} ms"
        else:
            return f"{value:.3f} s"
    elif unit == 'm':
        if value >= 1000:
            return f"{value/1000:.1f} km"
        else:
            return f"{value:.1f} m"
    elif unit == 'm/s':
        if value >= 1000:
            return f"{value/1000:.1f} km/s"
        else:
            return f"{value:.1f} m/s"
    elif unit == 'dB':
        return f"{value:.1f} dB"
    else:
        return f"{value:.2f} {unit}"

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
    """绘制性能权衡图 - 修复字体颜色"""
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
    
    # 颜色定义
    color1 = '#667eea'  # 蓝色
    color2 = '#764ba2'  # 紫色
    color3 = '#f093fb'  # 粉色
    color4 = '#4facfe'  # 浅蓝
    
    # 图1: 最大不模糊距离 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=max_range/1000, 
            mode='lines',
            line=dict(color=color1, width=3),
            name='最大不模糊距离',
            hovertemplate='<b>PRF</b>: %{x:.0f} Hz<br><b>最大距离</b>: %{y:.1f} km<br><extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"当前: {params.prf_hz/1e3:.1f} kHz",
        annotation_position="top right",
        annotation_font=dict(color="red", size=10),
        row=1, col=1
    )
    
    # 图2: 最大不模糊速度 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=max_velocity*3.6,
            mode='lines',
            line=dict(color=color2, width=3),
            name='最大不模糊速度',
            hovertemplate='<b>PRF</b>: %{x:.0f} Hz<br><b>最大速度</b>: %{y:.0f} km/h<br><extra></extra>'
        ),
        row=1, col=2
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color="red",
        row=1, col=2
    )
    
    # 图3: 速度分辨率 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=velocity_res*3.6,
            mode='lines',
            line=dict(color=color3, width=3),
            name='速度分辨率',
            hovertemplate='<b>PRF</b>: %{x:.0f} Hz<br><b>速度分辨率</b>: %{y:.1f} km/h<br><extra></extra>'
        ),
        row=2, col=1
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color="red",
        row=2, col=1
    )
    
    # 图4: 模糊图
    fig.add_trace(
        go.Scatter(
            x=max_range/1000, 
            y=max_velocity*3.6, 
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(79, 172, 254, 0.3)',
            line=dict(color=color4, width=3),
            name='模糊区域',
            hovertemplate='<b>最大距离</b>: %{x:.1f} km<br><b>最大速度</b>: %{y:.0f} km/h<br><extra></extra>'
        ),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=[current_max_range/1000], 
            y=[current_max_velocity*3.6],
            mode='markers+text',
            marker=dict(size=15, color='red', symbol='star', line=dict(width=2, color='white')),
            text=['当前参数'],
            textposition="top center",
            name='当前参数',
            hovertemplate='<b>当前位置</b><br>距离: %{x:.1f} km<br>速度: %{y:.0f} km/h<br><extra></extra>'
        ),
        row=2, col=2
    )
    
    # 更新布局 - 增强字体对比度
    fig.update_layout(
        height=600,
        showlegend=True,
        template="plotly_white",
        title_text="<b>雷达性能权衡分析</b>",
        title_font=dict(size=20, color='#333333'),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color='#333333'),
        legend=dict(
            font=dict(color='#333333'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#ddd',
            borderwidth=1
        )
    )
    
    # 更新所有坐标轴
    axes_updates = dict(
        title_font=dict(size=13, color='#333333'),
        tickfont=dict(size=11, color='#666666'),
        gridcolor='rgba(0,0,0,0.1)',
        zerolinecolor='rgba(0,0,0,0.2)',
        linecolor='#333333'
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
        annotation['font'] = dict(size=14, color='#333333', family="Arial, sans-serif")
    
    return fig

def main():
    """主应用函数"""
    # 标题
    st.markdown('<h1 class="main-header">📡 长城数字雷达参数设计器</h1>', 
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
        st.markdown('<h3 style="color: #667eea;">⚙️ 参数设置</h3>', unsafe_allow_html=True)
        
        # 预设选择
        st.markdown("**🎯 预设配置**")
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
            col_gain, col_bw_ant = st.columns(2)
            with col_gain:
                antenna_gain_db = st.slider(
                    "天线增益 (dB)",
                    10.0, 50.0,
                    value=default_params.antenna_gain_db,
                    step=0.5,
                    format="%.1f"
                )
            
            with col_bw_ant:
                beamwidth_deg = st.slider(
                    "波束宽度 (°)",
                    0.5, 30.0,
                    value=default_params.beamwidth_deg,
                    step=0.1,
                    format="%.1f"
                )
        
        # 接收机参数
        with st.expander("📡 接收机参数"):
            col_sr, col_nf = st.columns(2)
            with col_sr:
                sampling_rate_mhz = st.slider(
                    "采样率 (MHz)",
                    10.0, 500.0,
                    value=default_params.sampling_rate_hz/1e6,
                    step=10.0,
                    format="%.0f"
                )
            
            with col_nf:
                noise_figure_db = st.slider(
                    "噪声系数 (dB)",
                    1.0, 10.0,
                    value=default_params.noise_figure_db,
                    step=0.1,
                    format="%.1f"
                )
        
        # 目标参数
        with st.expander("🎯 目标参数"):
            col_range, col_rcs = st.columns(2)
            with col_range:
                target_range_km = st.slider(
                    "目标距离 (km)",
                    1.0, 200.0,
                    value=default_params.target_range_m/1000,
                    step=1.0,
                    format="%.0f"
                )
            
            with col_rcs:
                target_rcs_m2 = st.slider(
                    "目标RCS (m²)",
                    0.01, 10.0,
                    value=default_params.target_rcs_m2,
                    step=0.01,
                    format="%.2f"
                )
    
    # 主内容区域
    # 创建参数对象
    params = RadarParameters(
        frequency_hz=frequency_ghz * 1e9,
        bandwidth_hz=bandwidth_mhz * 1e6,
        prf_hz=prf_khz * 1e3,
        pulse_width_s=pulse_width_us * 1e-6,
        pulses=pulses,
        peak_power_w=peak_power_kw * 1e3,
        antenna_gain_db=antenna_gain_db,
        beamwidth_deg=beamwidth_deg,
        sampling_rate_hz=sampling_rate_mhz * 1e6,
        noise_figure_db=noise_figure_db,
        target_range_m=target_range_km * 1000,
        target_rcs_m2=target_rcs_m2
    )
    
    # 计算性能指标
    performance = params.calculate_performance()
    
    # 创建主界面布局
    col_main_left, col_main_right = st.columns([2, 1])
    
    with col_main_left:
        # 性能指标卡片
        st.markdown("### 📊 性能指标概览")
        
        # 第一行指标
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        
        with col_metric1:
            # st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">距离分辨率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["距离分辨率_m"]:.2f} m</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_metric2:
            # st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">速度分辨率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["速度分辨率_m/s"]*3.6:.1f} km/h</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_metric3:
            # st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">最大不模糊距离</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["最大不模糊距离_m"]/1000:.1f} km</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # 第二行指标
        col_metric4, col_metric5, col_metric6 = st.columns(3)
        
        with col_metric4:
            # st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">最大不模糊速度</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["最大不模糊速度_m/s"]*3.6:.0f} km/h</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_metric5:
            # st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">信噪比</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["信噪比_dB"]:.1f} dB</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_metric6:
            # st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均功率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["平均功率_W"]/1000:.1f} kW</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # 性能权衡分析图
        st.markdown("### 📈 性能权衡分析")
        fig = plot_performance_tradeoffs(params)
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': True})
        
        # 详细参数
        st.markdown("### 📋 详细参数表")
        col_param1, col_param2, col_param3 = st.columns(3)
        
        param_details = [
            ("波长", format_units(performance['波长_m'], 'm')),
            ("PRI", format_units(performance['PRI_s'], 's')),
            ("占空比", f"{performance['占空比_百分比']:.2f}%"),
            ("脉冲能量", format_units(performance['脉冲能量_J'], 'J')),
            ("脉冲压缩比", f"{performance['脉冲压缩比']:.0f}"),
            ("最小探测距离", format_units(performance['最小探测距离_m'], 'm')),
            ("模糊数(距离)", f"{performance['模糊数_距离']:.1f}"),
            ("波束驻留时间", f"{performance['PRI_s'] * params.pulses * 1e3:.1f} ms"),
            ("多普勒容限", f"{performance['速度分辨率_m/s']/performance['最大不模糊速度_m/s']*100:.1f}%")
        ]
        
        for i, (name, value) in enumerate(param_details):
            if i < 3:
                with col_param1:
                    # st.markdown(f'<div class="parameter-card" style="padding: 1rem; margin-bottom: 0.5rem;">', unsafe_allow_html=True)
                    st.markdown(f"**{name}**")
                    st.markdown(f'<div style="font-size: 1.2rem; font-weight: 600; color: #667eea;">{value}</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            elif i < 6:
                with col_param2:
                    # st.markdown(f'<div class="parameter-card" style="padding: 1rem; margin-bottom: 0.5rem;">', unsafe_allow_html=True)
                    st.markdown(f"**{name}**")
                    st.markdown(f'<div style="font-size: 1.2rem; font-weight: 600; color: #667eea;">{value}</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                with col_param3:
                    # st.markdown(f'<div class="parameter-card" style="padding: 1rem; margin-bottom: 0.5rem;">', unsafe_allow_html=True)
                    st.markdown(f"**{name}**")
                    st.markdown(f'<div style="font-size: 1.2rem; font-weight: 600; color: #667eea;">{value}</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
    
    with col_main_right:
        # 快速评估
        st.markdown("### ⚡ 快速评估")
        
        # 评估卡片
        evaluation_text = []
        evaluation_color = "success"
        
        # 检查距离模糊
        if performance['模糊数_距离'] > 1:
            evaluation_text.append(f"⚠️ **距离模糊风险**\n目标距离({target_range_km:.0f}km)超过最大不模糊距离({performance['最大不模糊距离_m']/1000:.1f}km)")
            evaluation_color = "warning"
        
        # 检查占空比
        if performance['占空比_百分比'] > 10:
            evaluation_text.append(f"⚠️ **高占空比**: {performance['占空比_百分比']:.1f}%\n注意系统散热")
            evaluation_color = "warning"
        elif performance['占空比_百分比'] < 0.1:
            evaluation_text.append(f"✅ **低占空比**: {performance['占空比_百分比']:.1f}%\n适合高峰值功率应用")
        else:
            evaluation_text.append(f"✅ **合理占空比**: {performance['占空比_百分比']:.1f}%")
        
        # 检查信噪比
        if performance['信噪比_dB'] < 10:
            evaluation_text.append(f"📶 **信噪比低**: {performance['信噪比_dB']:.1f} dB\n考虑增加脉冲数或功率")
            evaluation_color = "warning"
        else:
            evaluation_text.append(f"📶 **良好信噪比**: {performance['信噪比_dB']:.1f} dB")
        
        # 检查采样率
        if params.sampling_rate_hz < 2 * params.bandwidth_hz:
            evaluation_text.append("⚠️ **采样率不足**\n建议提高采样率防止混叠")
            evaluation_color = "warning"
        else:
            evaluation_text.append(f"✅ **采样率合理**: {params.sampling_rate_hz/params.bandwidth_hz:.1f}倍带宽")
        
        # 显示评估
        for text in evaluation_text:
            st.info(text)
        
        # 占空比进度条
        duty_progress = min(performance['占空比_百分比'] / 20, 1.0)
        st.progress(duty_progress, text=f"占空比: {performance['占空比_百分比']:.2f}%")
        
        # 当前参数摘要
        st.markdown("### 🔧 当前参数")
        # st.markdown('<div class="parameter-card">', unsafe_allow_html=True)
        
        param_summary = [
            ("频率", f"{frequency_ghz:.1f} GHz"),
            ("带宽", f"{bandwidth_mhz:.0f} MHz"),
            ("PRF", f"{prf_khz:.1f} kHz"),
            ("脉宽", f"{pulse_width_us:.1f} μs"),
            ("脉冲数", f"{pulses}"),
            ("峰值功率", f"{peak_power_kw:.1f} kW"),
            ("天线增益", f"{antenna_gain_db:.1f} dB"),
            ("波束宽度", f"{beamwidth_deg:.1f}°")
        ]
        
        for name, value in param_summary:
            st.markdown(f"**{name}**: <span class='param-value'>{value}</span>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 导出配置
        st.markdown("### 💾 导出配置")
        # st.markdown('<div class="parameter-card">', unsafe_allow_html=True)
        
        # 生成配置
        radarsimpy_config = params.to_radarsimpy_format()
        config_json = json.dumps(radarsimpy_config, indent=2)
        
        # 显示/隐藏配置
        if st.button("📄 显示JSON配置", width='stretch'):
            st.session_state.show_config = not st.session_state.show_config
        
        if st.session_state.show_config:
            st.code(config_json, language='json')
        
        # 下载按钮
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 JSON",
                data=config_json,
                file_name=f"radar_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                width='stretch'
            )
        
        with col_dl2:
            # 生成Python代码
            python_code = f'''#  仿真代码
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
                label="🐍 Python",
                data=python_code,
                file_name=f"radar_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                mime="text/x-python",
                width='stretch'
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 系统建议
    st.markdown("---")
    st.markdown("### 💡 系统优化建议")
    
    suggestions = []
    
    # 检查PRF选择
    if params.prf_hz < 1000:
        suggestions.append("**低PRF模式**: 适合远程探测，但测速能力有限。考虑使用脉冲多普勒处理提高测速性能。")
    elif params.prf_hz > 10000:
        suggestions.append("**高PRF模式**: 适合测速，但距离模糊严重。建议使用PRF参差或解模糊算法。")
    else:
        suggestions.append("**中PRF模式**: 兼顾距离和速度测量，是现代雷达常用模式。")
    
    # 检查脉冲压缩
    if performance['脉冲压缩比'] < 10:
        suggestions.append("**脉冲压缩增益较低**: 考虑增加带宽或脉宽以提高处理增益。")
    elif performance['脉冲压缩比'] > 1000:
        suggestions.append("**高处理增益**: 需要高性能信号处理器，注意计算复杂度。")
    
    # 检查波形设计
    if params.bandwidth_hz / params.frequency_hz > 0.1:
        suggestions.append("**宽带信号**: 相对带宽较大，注意系统线性度和相位一致性。")
    
    # 显示建议
    for i, suggestion in enumerate(suggestions, 1):
        st.markdown(f"{i}. {suggestion}")
    
    # 性能总结
    st.markdown("---")
    col_summary1, col_summary2 = st.columns(2)
    
    with col_summary1:
        st.markdown("#### 📈 性能总结")
        summary_items = [
            ("雷达类型", f"{'脉冲压缩' if performance['脉冲压缩比'] > 1 else '简单脉冲'}雷达"),
            ("工作模式", f"{'低PRF' if params.prf_hz < 1000 else '高PRF' if params.prf_hz > 10000 else '中PRF'}模式"),
            ("主要应用", f"{'远程监视' if performance['最大不模糊距离_m'] > 50000 else '中程跟踪' if performance['最大不模糊距离_m'] > 20000 else '近程探测'}"),
            ("设计复杂度", f"{'高' if performance['脉冲压缩比'] > 100 else '中' if performance['脉冲压缩比'] > 10 else '低'}")
        ]
        
        for item, value in summary_items:
            st.markdown(f"**{item}**: {value}")
    
    with col_summary2:
        st.markdown("#### 🎯 适用场景")
        
        if performance['最大不模糊距离_m'] > 50000 and performance['信噪比_dB'] > 15:
            st.success("✅ 适合远程警戒雷达、对空搜索雷达")
        elif performance['速度分辨率_m/s'] < 1 and params.prf_hz > 5000:
            st.success("✅ 适合机载火控雷达、气象雷达")
        elif params.frequency_hz > 20e9 and performance['距离分辨率_m'] < 1:
            st.success("✅ 适合合成孔径雷达、精确制导雷达")
        else:
            st.info("ℹ️ 通用雷达配置，可根据具体需求调整")
    
    # 脚注
    st.markdown("---")
    st.caption(f"""
    **长城数字雷达参数设计器 v1.1** | 生成时间: 2026-01-08 | 
    基于简化雷达方程计算 | 仅供教育研究使用
    """)

if __name__ == "__main__":
    main()