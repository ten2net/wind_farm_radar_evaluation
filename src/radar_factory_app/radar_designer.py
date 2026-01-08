# radar_designer_final_filter.py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
from dataclasses import dataclass, fields
from typing import Dict, Optional, List
import logging
from datetime import datetime
import os

# 设置日志级别
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('plotly').setLevel(logging.WARNING)

# 现在导入Streamlit
import streamlit as st
import re

class ScientificFloatLoader(yaml.SafeLoader):
    """优化版YAML加载器，优雅处理科学计数法"""
    def __init__(self, stream):
        super().__init__(stream)
        # 添加自定义类型解析
        self.add_implicit_resolver('!sci_float', re.compile(r'^\d*\.?\d+[eE][-+]?\d+$'), None)
        self.add_constructor('!sci_float', self.construct_sci_float)
    
    def construct_sci_float(self, loader, node):
        """科学计数法转换为浮点数"""
        return float(node.value)

# 页面配置
st.set_page_config(
    page_title="长城数字雷达参数优化专家系统",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入配置函数
def load_yaml_config(file_path="config.yaml"):
    """从YAML文件加载配置"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                # config = yaml.safe_load(f)
                config = yaml.load(f, Loader=ScientificFloatLoader)
            return config
        else:
            # 创建默认的YAML配置文件
            default_config = {
                '预设雷达': {
                    '气象雷达': {
                        'frequency_hz': 3e9,
                        'bandwidth_hz': 1e6,
                        'prf_hz': 1000,
                        'pulse_width_s': 1e-6,
                        'pulses': 128,
                        'peak_power_w': 250e3,
                        'antenna_gain_db': 40.0,
                        'beamwidth_deg': 1.0,
                        'sampling_rate_hz': 5e6,
                        'noise_figure_db': 2.0,
                        'system_loss_db': 4.0,
                        'target_rcs_m2': 10.0,
                        'target_range_m': 50000,
                        'baseband_gain_db': 20.0,
                        'load_resistance_ohm': 50.0
                    },
                    '机载火控雷达': {
                        'frequency_hz': 10e9,
                        'bandwidth_hz': 100e6,
                        'prf_hz': 10000,
                        'pulse_width_s': 1e-6,
                        'pulses': 256,
                        'peak_power_w': 10e3,
                        'antenna_gain_db': 35.0,
                        'beamwidth_deg': 3.0,
                        'sampling_rate_hz': 250e6,
                        'noise_figure_db': 3.0,
                        'system_loss_db': 5.0,
                        'target_rcs_m2': 5.0,
                        'target_range_m': 20000,
                        'baseband_gain_db': 30.0,
                        'load_resistance_ohm': 50.0
                    },
                    '舰载搜索雷达': {
                        'frequency_hz': 3e9,
                        'bandwidth_hz': 10e6,
                        'prf_hz': 500,
                        'pulse_width_s': 100e-6,
                        'pulses': 32,
                        'peak_power_w': 1e6,
                        'antenna_gain_db': 45.0,
                        'beamwidth_deg': 1.5,
                        'sampling_rate_hz': 30e6,
                        'noise_figure_db': 2.5,
                        'system_loss_db': 6.0,
                        'target_rcs_m2': 100.0,
                        'target_range_m': 100000,
                        'baseband_gain_db': 25.0,
                        'load_resistance_ohm': 50.0
                    },
                    '汽车毫米波雷达': {
                        'frequency_hz': 77e9,
                        'bandwidth_hz': 500e6,
                        'prf_hz': 2000,
                        'pulse_width_s': 50e-9,
                        'pulses': 256,
                        'peak_power_w': 10,
                        'antenna_gain_db': 25.0,
                        'beamwidth_deg': 20.0,
                        'sampling_rate_hz': 1e9,
                        'noise_figure_db': 6.0,
                        'system_loss_db': 8.0,
                        'target_rcs_m2': 1.0,
                        'target_range_m': 200,
                        'baseband_gain_db': 40.0,
                        'load_resistance_ohm': 50.0
                    }
                }
            }
            # 保存默认配置
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            return default_config
    except Exception as e:
        st.error(f"加载配置文件失败: {str(e)}")
        return None

# CSS样式 - 完全保持原始样式不变
st.markdown("""
<style>
    /* 主背景和字体 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    
    /* 标题样式 - 匹配图片中的渐变 */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        text-align: center;
        font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
    }
    
    .sub-header {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
        text-align: center;
        font-weight: 300;
        letter-spacing: 1px;
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    /* 筛选器样式 */
    .filter-container {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 0.02rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .filter-title {
        color: #60a5fa;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .filter-badge {
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* 雷达信息卡片 */
    .radar-info-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.02rem;
        margin: 0.5rem 0;
    }
    
    .radar-info-title {
        color: #60a5fa;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .radar-info-desc {
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* 参数卡片 - 匹配图片中的参数表样式 */
    .param-container {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 0.02rem;
        margin: 0.01rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .param-table {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        width: 100%;
    }
    
    .param-row {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .param-label {
        color: #60a5fa;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .param-value-box {
        background: rgba(30, 41, 59, 0.8);
        border: 2px solid #475569;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        color: #e2e8f0;
        font-size: 1.2rem;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        text-align: center;
        min-width: 150px;
        transition: all 0.2s ease;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .param-value-box:hover {
        border-color: #60a5fa;
        box-shadow: 0 0 15px rgba(96, 165, 250, 0.3);
    }
    
    /* 性能指标卡片 - 匹配图片中的渐变卡片 */
    .metric-card {
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.15) 0%, rgba(167, 139, 250, 0.15) 50%, rgba(244, 114, 182, 0.15) 100%);
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 12px;
        padding: 0.02rem;
        margin: 0.5rem;
        text-align: center;
        backdrop-filter: blur(5px);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(96, 165, 250, 0.2);
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .metric-unit {
        color: #60a5fa;
        font-size: 1rem;
        font-weight: 500;
        margin-left: 0.3rem;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(90deg, #2563eb 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #6d28d9 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    /* 滑块样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%);
    }
    
    /* 扩展器样式 */
    .stExpander {
        border: 1px solid #334155;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .stExpander summary {
        color: #60a5fa !important;
        font-weight: 600 !important;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 10px !important;
    }
    
    /* 分割线 */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #475569, transparent);
        margin: 2rem 0;
        border: none;
    }
    
    /* 图表容器 */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    /* 标签样式 */
    label {
        color: #cbd5e1 !important;
    }
    
    /* 警告和成功框样式 */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid #334155 !important;
    }
    
    /* 代码块样式 */
    .stCodeBlock {
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px;
    }
    
    /* 选择框样式 */
    .stSelectbox div[data-baseweb="select"] {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid #475569;
        border-radius: 6px;
    }
    
    /* 多选按钮样式 */
    .stMultiSelect div[data-baseweb="select"] {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
    }
    
    .stMultiSelect span[data-baseweb="tag"] {
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%) !important;
        color: white !important;
        border-radius: 4px !important;
    }
    
    /* 表格样式 */
    .dataframe {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid #334155 !important;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #60a5fa;
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
    baseband_gain_db: float = 20.0
    load_resistance_ohm: float = 50.0
    
    # 目标参数
    target_rcs_m2: float = 1.0
    target_range_m: float = 10000
    
    def to_yaml(self) -> str:
        """转换为YAML格式字符串"""
        data = {
            '雷达参数': {
                '发射机': {
                    '载波频率_Hz': self.frequency_hz,
                    '带宽_Hz': self.bandwidth_hz,
                    '脉冲重复频率_Hz': self.prf_hz,
                    '脉冲宽度_s': self.pulse_width_s,
                    '脉冲数': self.pulses,
                    '峰值功率_W': self.peak_power_w
                },
                '天线': {
                    '增益_dB': self.antenna_gain_db,
                    '损耗_dB': self.antenna_loss_db,
                    '波束宽度_deg': self.beamwidth_deg,
                    '孔径_m2': self.aperture_m2
                },
                '接收机': {
                    '噪声系数_dB': self.noise_figure_db,
                    '系统损耗_dB': self.system_loss_db,
                    '采样率_Hz': self.sampling_rate_hz,
                    'ADC位数': self.adc_bits,
                    '基带增益_dB': self.baseband_gain_db,
                    '负载电阻_Ω': self.load_resistance_ohm
                },
                '目标': {
                    '雷达截面积_m2': self.target_rcs_m2,
                    '距离_m': self.target_range_m
                }
            }
        }
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def calculate_performance(self) -> Dict:
        """计算雷达性能指标"""
        c = 3e8
        
        wavelength = c / self.frequency_hz
        pri = 1 / self.prf_hz if self.prf_hz > 0 else 0
        duty_cycle = self.pulse_width_s * self.prf_hz
        
        range_resolution = c / (2 * self.bandwidth_hz) if self.bandwidth_hz > 0 else 0
        max_unambiguous_range = c / (2 * self.prf_hz) if self.prf_hz > 0 else 0
        min_range = c * self.pulse_width_s / 2
        
        max_unambiguous_velocity = wavelength * self.prf_hz / 4 if self.prf_hz > 0 else 0
        velocity_resolution = wavelength * self.prf_hz / (2 * self.pulses) if self.pulses > 0 else 0
        
        avg_power = self.peak_power_w * duty_cycle
        pulse_energy = self.peak_power_w * self.pulse_width_s
        
        compression_ratio = self.pulse_width_s * self.bandwidth_hz
        range_ambiguity_number = self.target_range_m / max_unambiguous_range if max_unambiguous_range > 0 else 0
        
        try:
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
        except:
            snr_db = -np.inf
        
        dwell_time = pri * self.pulses
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
            return f"{value/1000:.2f} km"
        else:
            return f"{value:.2f} m"
    elif unit == 'm/s':
        if value >= 1000:
            return f"{value/1000:.1f} km/s"
        else:
            return f"{value:.1f} m/s"
    elif unit == 'dB':
        return f"{value:.1f} dB"
    elif unit == 'Ω':
        return f"{value:.0f} Ω"
    else:
        return f"{value:.2f} {unit}"

def create_radar_preset(name: str, config: Optional[Dict] = None) -> RadarParameters:
    """从YAML配置创建雷达预设"""
    if config and '预设雷达' in config and name in config['预设雷达']:
        # 从YAML配置加载
        preset_data = config['预设雷达'][name]
        
        # 获取RadarParameters类的字段名
        radar_param_fields = {field.name for field in fields(RadarParameters)}
        
        # 只保留RadarParameters类中定义的字段
        filtered_data = {k: v for k, v in preset_data.items() if k in radar_param_fields}
        
        # 返回过滤后的参数
        return RadarParameters(**filtered_data)
    else:
        # 默认预设（如果没有配置文件）
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

def filter_presets_by_country(preset_names: List[str], country: str, config: Dict) -> List[str]:
    """按国家筛选预设雷达"""
    if not country or country == "全部" or '雷达分类' not in config or country not in config['雷达分类']:
        return preset_names
    
    return [preset for preset in preset_names if preset in config['雷达分类'].get(country, [])]

def filter_presets_by_type(preset_names: List[str], radar_type: str, config: Dict) -> List[str]:
    """按雷达类型筛选预设雷达"""
    if not radar_type or radar_type == "全部" or '雷达类型分类' not in config or radar_type not in config['雷达类型分类']:
        return preset_names
    
    return [preset for preset in preset_names if preset in config['雷达类型分类'].get(radar_type, [])]

def get_all_countries(config: Dict) -> List[str]:
    """获取所有国家列表"""
    if '雷达分类' in config:
        return ["全部"] + list(config['雷达分类'].keys())
    return ["全部"]

def get_all_radar_types(config: Dict) -> List[str]:
    """获取所有雷达类型列表"""
    if '雷达类型分类' in config:
        return ["全部"] + list(config['雷达类型分类'].keys())
    return ["全部"]

def get_radar_info(preset_name: str, config: Dict) -> Dict:
    """获取雷达的额外信息（描述、国家、类型）"""
    if not config or '预设雷达' not in config or preset_name not in config['预设雷达']:
        return {}
    
    preset_data = config['预设雷达'][preset_name]
    return {
        'description': preset_data.get('description', ''),
        'country': preset_data.get('country', ''),
        'type': preset_data.get('type', '')
    }
    
# 定义绘制性能权衡图的函数
def plot_performance_tradeoffs(params: RadarParameters, performance: Dict):
    """绘制性能权衡图"""
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
            '最大不模糊距离 vs PRF',
            '最大不模糊速度 vs PRF',
            '速度分辨率 vs PRF',
            '距离-速度模糊区域'
        ),
        vertical_spacing=0.25,
        horizontal_spacing=0.15
    )
    
    # 使用渐变色
    colors = ['#60a5fa', '#a78bfa', '#f472b6', '#34d399']
    
    # 图1: 最大不模糊距离 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=max_range/1000, 
            mode='lines',
            line=dict(color=colors[0], width=3),
            name='最大不模糊距离',
            hovertemplate='PRF: %{x:.0f} Hz<br>最大距离: %{y:.1f} km<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color="#fbbf24",
        annotation_text=f"当前: {params.prf_hz/1e3:.1f} kHz",
        annotation_position="top right",
        annotation_font=dict(color="#fbbf24", size=10),
        row=1, col=1 # type: ignore
    )
    
    # 图2: 最大不模糊速度 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=max_velocity*3.6,
            mode='lines',
            line=dict(color=colors[1], width=3),
            name='最大不模糊速度',
            hovertemplate='PRF: %{x:.0f} Hz<br>最大速度: %{y:.0f} km/h<extra></extra>'
        ),
        row=1, col=2
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color="#fbbf24",
        row=1, col=2 # type: ignore
    )
    
    # 图3: 速度分辨率 vs PRF
    fig.add_trace(
        go.Scatter(
            x=prf_range, 
            y=velocity_res*3.6,
            mode='lines',
            line=dict(color=colors[2], width=3),
            name='速度分辨率',
            hovertemplate='PRF: %{x:.0f} Hz<br>速度分辨率: %{y:.1f} km/h<extra></extra>'
        ),
        row=2, col=1
    )
    fig.add_vline(
        x=params.prf_hz, 
        line_dash="dash", 
        line_color="#fbbf24",
        row=2, col=1 # type: ignore
    )
    
    # 图4: 模糊图
    fig.add_trace(
        go.Scatter(
            x=max_range/1000, 
            y=max_velocity*3.6, 
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(96, 165, 250, 0.2)',
            line=dict(color=colors[0], width=3),
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
            marker=dict(size=12, color='#fbbf24', symbol='diamond',
                       line=dict(width=2, color='white')),
            name='当前参数',
            hovertemplate='距离: %{x:.1f} km<br>速度: %{y:.0f} km/h<extra></extra>'
        ),
        row=2, col=2
    )
    
    # 更新布局 - 深色主题
    fig.update_layout(
        height=550,
        showlegend=True,
        template="plotly_dark",
        title_text="雷达性能权衡分析图",
        title_font=dict(size=20, color='#ffffff'),
        hovermode='x unified',
        plot_bgcolor='rgba(30, 41, 59, 0.5)',
        paper_bgcolor='rgba(15, 23, 42, 0.8)',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        legend=dict(
            font=dict(color='#e2e8f0'),
            bgcolor='rgba(15, 23, 42, 0.8)',
            bordercolor='#475569',
            borderwidth=1
        )
    )
    
    # 更新所有坐标轴
    axes_updates = dict(
        title_font=dict(size=13, color='#94a3b8'),
        tickfont=dict(size=11, color='#cbd5e1'),
        gridcolor='rgba(148, 163, 184, 0.3)',
        zerolinecolor='rgba(148, 163, 184, 0.3)',
        linecolor='#94a3b8'
    )
    
    fig.update_xaxes(**axes_updates, row=1, col=1, title_text="PRF (Hz)", type="log") # type: ignore
    fig.update_xaxes(**axes_updates, row=1, col=2, title_text="PRF (Hz)", type="log") # type: ignore
    fig.update_xaxes(**axes_updates, row=2, col=1, title_text="PRF (Hz)", type="log") # type: ignore
    fig.update_xaxes(**axes_updates, row=2, col=2, title_text="最大不模糊距离 (km)") # type: ignore
    
    fig.update_yaxes(**axes_updates, row=1, col=1, title_text="距离 (km)", type="log") # type: ignore
    fig.update_yaxes(**axes_updates, row=1, col=2, title_text="速度 (km/h)") # type: ignore
    fig.update_yaxes(**axes_updates, row=2, col=1, title_text="速度分辨率 (km/h)") # type: ignore
    fig.update_yaxes(**axes_updates, row=2, col=2, title_text="速度 (km/h)") # type: ignore
    
    # 更新子图标题
    for i, annotation in enumerate(fig['layout']['annotations']):
        annotation['font'] = dict(size=14, color='#ffffff', family="Arial, sans-serif") # type: ignore
    
    return fig  

# 计算雷达图数据
def calculate_radar_chart_data(performance, params):
    """计算雷达图数据"""
    
    # 距离性能 (0-100)
    # 距离分辨率越小越好，我们转换为越大越好
    range_res_optimal = 0.1  # 最佳距离分辨率
    range_res_max = 100.0    # 最大距离分辨率
    range_score = max(0, 100 - ((performance['距离分辨率_m'] - range_res_optimal) / 
                               (range_res_max - range_res_optimal)) * 100)
    range_score = min(100, max(0, range_score))
    
    # 速度性能
    # 速度分辨率越小越好
    vel_res_optimal = 0.1    # 最佳速度分辨率
    vel_res_max = 100.0      # 最大速度分辨率
    velocity_score = max(0, 100 - ((performance['速度分辨率_m/s'] - vel_res_optimal) / 
                                  (vel_res_max - vel_res_optimal)) * 100)
    velocity_score = min(100, max(0, velocity_score))
    
    # 探测范围性能
    # 最大不模糊距离越大越好
    max_range_optimal = 500000  # 最佳最大距离
    max_range_score = min(100, (performance['最大不模糊距离_m'] / max_range_optimal) * 100)
    
    # 速度范围性能
    # 最大不模糊速度越大越好
    max_vel_optimal = 1000  # 最佳最大速度 m/s
    max_velocity_score = min(100, (performance['最大不模糊速度_m/s'] / max_vel_optimal) * 100)
    
    # 信噪比性能
    # 信噪比越大越好
    snr_optimal = 30  # 最佳信噪比 dB
    snr_current = max(performance['信噪比_dB'], 0)  # 避免负值
    snr_score = min(100, (snr_current / snr_optimal) * 100)
    
    # 占空比性能
    # 理想占空比在1-10%之间
    duty_cycle = performance['占空比_百分比']
    if duty_cycle < 1:
        duty_score = (duty_cycle / 1) * 50  # 太低占空比
    elif duty_cycle <= 10:
        duty_score = 50 + ((duty_cycle - 1) / 9) * 50  # 理想范围
    else:
        duty_score = max(0, 100 - (duty_cycle - 10) * 2)  # 太高占空比
    
    # 脉冲压缩性能
    # 脉冲压缩比适中最好
    compression_ratio = performance['脉冲压缩比']
    if compression_ratio < 10:
        compression_score = (compression_ratio / 10) * 50
    elif compression_ratio <= 1000:
        compression_score = 50 + ((min(compression_ratio, 1000) - 10) / 990) * 50
    else:
        compression_score = 100  # 很高
    
    # 采样率性能
    # 采样率越高越好，但也要合理
    sampling_ratio = params.sampling_rate_hz / params.bandwidth_hz
    sampling_score = min(100, (sampling_ratio / 2.5) * 50)  # 2.5倍为理想
    
    return {
        '距离分辨率': range_score,
        '速度分辨率': velocity_score,
        '最大距离': max_range_score,
        '最大速度': max_velocity_score,
        '信噪比': snr_score,
        '占空比': duty_score,
        '脉冲压缩': compression_score,
        '采样率': sampling_score
    }

def main():
    """主应用函数"""
    # 标题
    st.markdown('<h1 class="main-header">长城数字雷达参数优化专家系统</h1>', 
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">交互式设计雷达参数，优化性能指标，导出为仿真配置文件</p>', 
                unsafe_allow_html=True)
    
    # 加载配置文件
    config = load_yaml_config("config.yaml")
    if config is None:
        st.warning("⚠️ 无法加载配置文件，使用默认预设")
    
    # 初始化会话状态
    if 'current_preset' not in st.session_state:
        st.session_state.current_preset = "自定义"
    if 'show_config' not in st.session_state:
        st.session_state.show_config = False
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = "全部"
    if 'selected_radar_type' not in st.session_state:
        st.session_state.selected_radar_type = "全部"
    
    # 侧边栏 - 参数设置
    with st.sidebar:
        # st.markdown('<h3 style="color: #60a5fa;">⚙️ 参数设置</h3>', unsafe_allow_html=True)
        
        # 预设雷达筛选器
        st.markdown("### 🎯 预设雷达筛选")
        
        # 获取所有预设雷达
        all_preset_names = []
        if config and '预设雷达' in config:
            all_preset_names = list(config['预设雷达'].keys())
        
        # 添加基本的预设
        basic_presets = ["气象雷达", "机载火控雷达", "舰载搜索雷达", "汽车毫米波雷达"]
        for preset in basic_presets:
            if preset not in all_preset_names:
                all_preset_names.append(preset)
        
        # 如果配置文件有分类信息，添加筛选器
        if config and ('雷达分类' in config or '雷达类型分类' in config):
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            
            # 国家筛选
            if '雷达分类' in config:
                countries = get_all_countries(config)
                st.markdown('<div class="filter-title">🌍 按国家筛选</div>', unsafe_allow_html=True)
                selected_country = st.selectbox(
                    "选择国家",
                    countries,
                    index=countries.index(st.session_state.selected_country) if st.session_state.selected_country in countries else 0,
                    key="country_filter",
                    label_visibility="collapsed"
                )
                st.session_state.selected_country = selected_country
            
            # 雷达类型筛选
            if '雷达类型分类' in config:
                radar_types = get_all_radar_types(config)
                st.markdown('<div class="filter-title">📡 按类型筛选</div>', unsafe_allow_html=True)
                selected_radar_type = st.selectbox(
                    "选择雷达类型",
                    radar_types,
                    index=radar_types.index(st.session_state.selected_radar_type) if st.session_state.selected_radar_type in radar_types else 0,
                    key="type_filter",
                    label_visibility="collapsed"
                )
                st.session_state.selected_radar_type = selected_radar_type
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 应用筛选
        filtered_presets = all_preset_names.copy()
        
        if config:
            # 按国家筛选
            if st.session_state.selected_country and st.session_state.selected_country != "全部":
                filtered_presets = filter_presets_by_country(filtered_presets, st.session_state.selected_country, config)
            
            # 按类型筛选
            if st.session_state.selected_radar_type and st.session_state.selected_radar_type != "全部":
                filtered_presets = filter_presets_by_type(filtered_presets, st.session_state.selected_radar_type, config)
        
        # 添加自定义选项
        preset_options = ["自定义"] + filtered_presets
        
        # 显示筛选结果统计
        if len(filtered_presets) < len(all_preset_names):
            st.markdown(f'<div class="filter-title">🔍 筛选结果: <span class="filter-badge">{len(filtered_presets)}/{len(all_preset_names)}</span></div>', unsafe_allow_html=True)
        
        # 预设选择
        preset = st.selectbox(
            "选择雷达预设",
            preset_options,
            index=0,
            help="从列表中选择一个雷达预设，或选择'自定义'手动设置参数"
        )
        
        if preset != "自定义":
            default_params = create_radar_preset(preset, config)
            # 显示雷达详细信息
            if config and '预设雷达' in config and preset in config['预设雷达']:
                radar_info = get_radar_info(preset, config)
                if radar_info.get('description') or radar_info.get('country') or radar_info.get('type'):
                    st.markdown('<div class="radar-info-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="radar-info-title">{preset}</div>', unsafe_allow_html=True)
                    
                    if radar_info.get('description'):
                        st.markdown(f'<div class="radar-info-desc">{radar_info["description"]}</div>', unsafe_allow_html=True)
                    
                    info_parts = []
                    if radar_info.get('country'):
                        info_parts.append(f"国家: {radar_info['country']}")
                    if radar_info.get('type'):
                        info_parts.append(f"类型: {radar_info['type']}")
                    
                    if info_parts:
                        st.markdown(f'<div class="radar-info-desc" style="margin-top: 0.5rem; font-size: 0.85rem; color: #94a3b8;">{" | ".join(info_parts)}</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
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
                    format="%.1f"
                )
            
            with col_bw:
                bandwidth_mhz = st.slider(
                    "带宽 (MHz)",
                    1.0, 1000.0,
                    value=default_params.bandwidth_hz/1e6,
                    step=1.0,
                    format="%.0f"
                )
            
            col_prf, col_pw = st.columns(2)
            with col_prf:
                prf_khz = st.slider(
                    "PRF (kHz)",
                    0.1, 50.0,
                    value=default_params.prf_hz/1e3,
                    step=0.1,
                    format="%.1f"
                )
            
            with col_pw:
                pulse_width_us = st.slider(
                    "脉冲宽度 (μs)",
                    0.01, 1000.0,
                    value=default_params.pulse_width_s * 1e6,
                    step=0.1,
                    format="%.1f"
                )
            
            pulses = st.slider(
                "脉冲数",
                8, 1024,
                value=default_params.pulses,
                step=8
            )
            
            peak_power_kw = st.slider(
                "峰值功率 (kW)",
                0.1, 1000.0,
                value=default_params.peak_power_w/1e3,
                step=0.1,
                format="%.1f"
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
                    10.0, 1000.0,
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
            
            col_bb, col_rl = st.columns(2)
            with col_bb:
                baseband_gain_db = st.slider(
                    "基带增益 (dB)",
                    0.0, 60.0,
                    value=default_params.baseband_gain_db,
                    step=1.0,
                    format="%.0f"
                )
            
            with col_rl:
                load_resistance_ohm = st.slider(
                    "负载电阻 (Ω)",
                    1.0, 1000.0,
                    value=default_params.load_resistance_ohm,
                    step=1.0,
                    format="%.0f"
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
        system_loss_db=default_params.system_loss_db,
        adc_bits=default_params.adc_bits,
        baseband_gain_db=baseband_gain_db,
        load_resistance_ohm=load_resistance_ohm,
        target_range_m=target_range_km * 1000,
        target_rcs_m2=target_rcs_m2
    )
    
    # 计算性能指标
    performance = params.calculate_performance()
    
    # 主界面布局
    col_main_left, col_main_right = st.columns([2, 1])
    
    with col_main_left:
        # 性能指标卡片
        st.markdown("### 📊 性能指标概览")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">距离分辨率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["距离分辨率_m"]:.2f}<span class="metric-unit">m</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">最大不模糊距离</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["最大不模糊距离_m"]/1000:.1f}<span class="metric-unit">km</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">速度分辨率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["速度分辨率_m/s"]*3.6:.1f}<span class="metric-unit">km/h</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">最大不模糊速度</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["最大不模糊速度_m/s"]*3.6:.0f}<span class="metric-unit">km/h</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">信噪比</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["信噪比_dB"]:.1f}<span class="metric-unit">dB</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均功率</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{performance["平均功率_W"]/1000:.1f}<span class="metric-unit">kW</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # 性能权衡分析图
        st.markdown("### 📈 性能权衡分析")
        
        fig_tradeoff = plot_performance_tradeoffs(params, performance)
        st.plotly_chart(fig_tradeoff, width='stretch', config={'displayModeBar': True})  
        # 性能权衡分析图看点  
        with st.expander("⚖️ 指南：如何解读上面的性能权衡分析图"):
            st.markdown("""                                    
             1. **左上：** PRF越高，最大不模糊距离越小，存在距离模糊风险;
             2. **右上：** PRF越高，最大不模糊速度越大，测速能力越强;
             3. **左下：** PRF越高，速度分辨率越差;
             4. **右下：** 距离和速度的权衡关系，雷达需要在这两者之间做出选择。
             """)
        # 详细参数表
        st.markdown("### 📋 派生参数表")
        
        st.markdown('<div class="param-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">波长</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{format_units(performance["波长_m"], "m")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">脉冲能量</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{format_units(performance["脉冲能量_J"], "J")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">占空比</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{performance["占空比_百分比"]:.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">波束驻留时间</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{performance["波束驻留时间_s"]*1e3:.1f} ms</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)            
        
        with col2:
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">PRI</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{format_units(performance["PRI_s"], "s")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">脉冲压缩比</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{performance["脉冲压缩比"]:.0f}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">最小探测距离</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{format_units(performance["最小探测距离_m"], "m")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="param-row">', unsafe_allow_html=True)
            st.markdown('<div class="param-label">多普勒容限</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="param-value-box">{performance["多普勒容限_百分比"]:.1f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)            
        
        # with col3:
        #     st.markdown('<div class="param-row">', unsafe_allow_html=True)
        #     st.markdown('<div class="param-label">占空比</div>', unsafe_allow_html=True)
        #     st.markdown(f'<div class="param-value-box">{performance["占空比_百分比"]:.2f}%</div>', unsafe_allow_html=True)
        #     st.markdown('</div>', unsafe_allow_html=True)
            
        #     st.markdown('<div class="param-row">', unsafe_allow_html=True)
        #     st.markdown('<div class="param-label">波束驻留时间</div>', unsafe_allow_html=True)
        #     st.markdown(f'<div class="param-value-box">{performance["波束驻留时间_s"]*1e3:.1f} ms</div>', unsafe_allow_html=True)
        #     st.markdown('</div>', unsafe_allow_html=True)
        
        # with col4:
        #     st.markdown('<div class="param-row">', unsafe_allow_html=True)
        #     st.markdown('<div class="param-label">最小探测距离</div>', unsafe_allow_html=True)
        #     st.markdown(f'<div class="param-value-box">{format_units(performance["最小探测距离_m"], "m")}</div>', unsafe_allow_html=True)
        #     st.markdown('</div>', unsafe_allow_html=True)
            
        #     st.markdown('<div class="param-row">', unsafe_allow_html=True)
        #     st.markdown('<div class="param-label">多普勒容限</div>', unsafe_allow_html=True)
        #     st.markdown(f'<div class="param-value-box">{performance["多普勒容限_百分比"]:.1f}%</div>', unsafe_allow_html=True)
        #     st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        # 性能指标雷达图
        st.markdown("### 📈 性能指标雷达图")
        
        # 获取雷达图数据
        radar_data = calculate_radar_chart_data(performance, params)

        # 创建雷达图
        fig_radar = go.Figure()

        # 添加雷达图数据
        categories = list(radar_data.keys())
        values = list(radar_data.values())

        # 确保图形闭合
        categories_with_closure = categories + [categories[0]]
        values_with_closure = values + [values[0]]

        fig_radar.add_trace(go.Scatterpolar(
            r=values_with_closure,
            theta=categories_with_closure,
            fill='toself',
            fillcolor='rgba(96, 165, 250, 0.3)',
            line_color='#60a5fa',
            line_width=3,
            name='当前性能',
            hovertemplate='%{theta}: %{r:.1f}%<extra></extra>'
        ))

        # 添加基准线（60%为良好，80%为优秀）
        fig_radar.add_trace(go.Scatterpolar(
            r=[60] * len(categories_with_closure),
            theta=categories_with_closure,
            line_color='#fbbf24',
            line_width=2,
            line_dash='dash',
            name='良好基准',
            hovertemplate='良好基准: 60%<extra></extra>'
        ))

        fig_radar.add_trace(go.Scatterpolar(
            r=[80] * len(categories_with_closure),
            theta=categories_with_closure,
            line_color='#34d399',
            line_width=2,
            line_dash='dash',
            name='优秀基准',
            hovertemplate='优秀基准: 80%<extra></extra>'
        ))

        # 更新布局
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10, color='#94a3b8'),
                    gridcolor='rgba(148, 163, 184, 0.3)',
                    angle=45
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color='#cbd5e1'),
                    rotation=90,
                    direction='clockwise'
                ),
                bgcolor='rgba(15, 23, 42, 0.5)'
            ),
            showlegend=True,
            legend=dict(
                font=dict(color='#cbd5e1'),
                bgcolor='rgba(15, 23, 42, 0.8)',
                bordercolor='#334155',
                borderwidth=1
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            height=500,
            margin=dict(l=50, r=50, t=30, b=30)
        )
        # 创建选项卡
        tab1, tab2, tab3 = st.tabs(["📊 雷达图", "📈 性能分布", "📋 详细评分"])

        with tab1:
            # 雷达图
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # 图例说明
            col_legend1, col_legend2, col_legend3 = st.columns(3)
            with col_legend1:
                st.markdown('<div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0;">'
                        '<div style="width: 20px; height: 4px; background: #60a5fa; border-radius: 2px;"></div>'
                        '<span style="color: #94a3b8; font-size: 0.9rem;">当前性能</span>'
                        '</div>', unsafe_allow_html=True)
            
            with col_legend2:
                st.markdown('<div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0;">'
                        '<div style="width: 20px; height: 2px; background: #fbbf24; border-radius: 2px; border: 1px dashed #fbbf24;"></div>'
                        '<span style="color: #94a3b8; font-size: 0.9rem;">良好基准</span>'
                        '</div>', unsafe_allow_html=True)
            
            with col_legend3:
                st.markdown('<div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0;">'
                        '<div style="width: 20px; height: 2px; background: #34d399; border-radius: 2px; border: 1px dashed #34d399;"></div>'
                        '<span style="color: #94a3b8; font-size: 0.9rem;">优秀基准</span>'
                        '</div>', unsafe_allow_html=True)

        with tab2:
            # 性能分布柱状图
            fig_bar = go.Figure()
            
            # 颜色映射
            colors = []
            for score in values:
                if score >= 80:
                    colors.append('#34d399')  # 优秀 - 绿色
                elif score >= 60:
                    colors.append('#fbbf24')  # 良好 - 黄色
                elif score >= 40:
                    colors.append('#fb923c')  # 一般 - 橙色
                else:
                    colors.append('#ef4444')  # 需改进 - 红色
            
            fig_bar.add_trace(go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=[f"{v:.1f}%" for v in values],
                textposition='outside',
                hovertemplate='%{x}: %{y:.1f}%<extra></extra>',
                name='性能分数'
            ))
            
            # 添加基准线
            fig_bar.add_hline(y=60, line_dash="dash", line_color="#fbbf24", 
                            annotation_text="良好基准", 
                            annotation_position="top right",
                            annotation_font=dict(color="#fbbf24", size=10))
            fig_bar.add_hline(y=80, line_dash="dash", line_color="#34d399", 
                            annotation_text="优秀基准", 
                            annotation_position="top right",
                            annotation_font=dict(color="#34d399", size=10))
            
            fig_bar.update_layout(
                title=dict(text="性能指标分布", font=dict(color='#ffffff', size=16)),
                xaxis=dict(
                    title="性能指标",
                    title_font=dict(color='#94a3b8'),
                    tickfont=dict(color='#cbd5e1'),
                    gridcolor='rgba(148, 163, 184, 0.2)'
                ),
                yaxis=dict(
                    title="分数 (%)",
                    title_font=dict(color='#94a3b8'),
                    tickfont=dict(color='#cbd5e1'),
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    range=[0, 100]
                ),
                paper_bgcolor='rgba(15, 23, 42, 0)',
                plot_bgcolor='rgba(15, 23, 42, 0.3)',
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # 性能统计
            avg_score = np.mean(values)
            max_score = np.max(values)
            min_score = np.min(values)
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("平均分", f"{avg_score:.1f}%", 
                        delta="优秀" if avg_score >= 80 else "良好" if avg_score >= 60 else "一般")
            with col_stat2:
                st.metric("最高分", f"{max_score:.1f}%")
            with col_stat3:
                st.metric("最低分", f"{min_score:.1f}%")
            
            # 添加雷达性能指标说明
            with st.expander("📋 指南：如何解读上面的性能指标"):
                st.markdown("""                
                1. **距离分辨率**: 雷达能够分辨的两个目标之间的最小距离差
                2. **速度分辨率**: 雷达能够分辨的两个目标之间的最小速度差
                3. **最大距离**: 雷达理论上能够探测到目标的最大距离
                4. **最大速度**: 雷达理论上能够测量的最大目标速度
                5. **信噪比**: 信号与噪声的功率比值，影响探测概率
                6. **占空比**: 发射脉冲时间占脉冲重复周期的时间比例
                7. **脉冲压缩**: 通过脉冲压缩技术获得的时间带宽积
                8. **采样率**: ADC采样率与信号带宽的比值
                """)
        with tab3:
            # 准备数据
            table_data = []
            for metric, score in radar_data.items():
                # 获取当前值
                if metric == '距离分辨率':
                    current_value = f"{performance['距离分辨率_m']:.2f} m"
                elif metric == '速度分辨率':
                    current_value = f"{performance['速度分辨率_m/s']:.2f} m/s"
                elif metric == '最大距离':
                    current_value = f"{performance['最大不模糊距离_m']/1000:.1f} km"
                elif metric == '最大速度':
                    current_value = f"{performance['最大不模糊速度_m/s']:.2f} m/s"
                elif metric == '信噪比':
                    current_value = f"{performance['信噪比_dB']:.1f} dB"
                elif metric == '占空比':
                    current_value = f"{performance['占空比_百分比']:.2f}%"
                elif metric == '脉冲压缩':
                    current_value = f"{performance['脉冲压缩比']:.0f}"
                elif metric == '采样率':
                    current_value = f"{(params.sampling_rate_hz / params.bandwidth_hz):.1f}x"
                else:
                    current_value = "-"
                
                # 评分等级
                if score >= 80:
                    rating = "优秀"
                    advice = "保持当前设置"
                elif score >= 60:
                    rating = "良好"
                    advice = "可继续优化"
                elif score >= 40:
                    rating = "一般"
                    advice = "建议调整参数"
                else:
                    rating = "需改进"
                    advice = "重点优化"
                
                table_data.append({
                    '性能指标': metric,
                    '当前值': current_value,
                    '分数': f"{score:.1f}%",
                    '评价': rating,
                    '建议': advice
                })
            
            # 创建DataFrame
            df = pd.DataFrame(table_data)
            
            # 定义HTML样式
            html_table = '''
            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; backdrop-filter: blur(10px);">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: rgba(96, 165, 250, 0.2);">
                            <th style="color: #60a5fa; padding: 12px 15px; text-align: left; font-weight: 600;">性能指标</th>
                            <th style="color: #60a5fa; padding: 12px 15px; text-align: center; font-weight: 600;">当前值</th>
                            <th style="color: #60a5fa; padding: 12px 15px; text-align: center; font-weight: 600;">分数</th>
                            <th style="color: #60a5fa; padding: 12px 15px; text-align: center; font-weight: 600;">评价</th>
                            <th style="color: #60a5fa; padding: 12px 15px; text-align: left; font-weight: 600;">建议</th>
                        </tr>
                    </thead>
                    <tbody>
            '''
            
            # 添加行
            for _, row in df.iterrows():
                # 确定颜色
                score_val = float(row['分数'].replace('%', ''))
                if score_val >= 80:
                    score_color = "#34d399"
                    rating_color = "#34d399"
                elif score_val >= 60:
                    score_color = "#fbbf24"
                    rating_color = "#fbbf24"
                elif score_val >= 40:
                    score_color = "#fb923c"
                    rating_color = "#fb923c"
                else:
                    score_color = "#ef4444"
                    rating_color = "#ef4444"
                
                html_table += f'''
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="color: #cbd5e1; padding: 10px 15px;">{row['性能指标']}</td>
                    <td style="color: #cbd5e1; padding: 10px 15px; text-align: center;">{row['当前值']}</td>
                    <td style="color: {score_color}; font-weight: 600; padding: 10px 15px; text-align: center; font-family: 'Courier New', monospace;">{row['分数']}</td>
                    <td style="color: {rating_color}; font-weight: 600; padding: 10px 15px; text-align: center;">{row['评价']}</td>
                    <td style="color: #cbd5e1; padding: 10px 15px;">{row['建议']}</td>
                </tr>
                '''
            
            html_table += '''
                    </tbody>
                </table>
            </div>
            '''
            
            # 显示HTML表格
            # st.markdown(html_table, unsafe_allow_html=True)
            # 使用st.components.v1.html渲染
            from streamlit import components    
            components.v1.html(html_table, height=400, scrolling=False) # type: ignore
            
            # 总体建议
            st.markdown("---")
            st.markdown("### 💡 性能优化建议")
            
            suggestions = []
            avg_score = np.mean(list(radar_data.values()))
            
            if avg_score >= 80:
                suggestions.append("✅ **整体性能优秀**：当前参数配置非常合理，各项性能指标均衡")
            elif avg_score >= 60:
                suggestions.append("📈 **整体性能良好**：大部分指标表现良好，部分指标有优化空间")
            else:
                suggestions.append("⚠️ **整体性能需提升**：多个关键指标有待优化，建议调整参数配置")
            
            # 找出最低分的指标
            min_metric = min(radar_data.items(), key=lambda x: x[1])
            if min_metric[1] < 40:
                suggestions.append(f"🔧 **重点关注**：{min_metric[0]}得分较低({min_metric[1]:.1f}%)，是主要性能瓶颈")
            
            # 检查信噪比
            if radar_data['信噪比'] < 40:
                suggestions.append("📶 **信噪比不足**：考虑增加脉冲数、提高发射功率或使用脉冲压缩")
            
            # 检查距离分辨率
            if radar_data['距离分辨率'] < 40 and performance['距离分辨率_m'] > 10:
                suggestions.append("📏 **距离分辨率偏低**：可考虑增加带宽以提高距离分辨率")
            
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(f"{i}. {suggestion}")        
    
    with col_main_right:
        # 快速评估
        st.markdown("### ⚡ 快速评估")
        
        if performance['模糊数_距离'] > 1:
            st.error(f"⚠️ **距离模糊风险**\n目标距离({target_range_km:.0f}km)超过最大不模糊距离({performance['最大不模糊距离_m']/1000:.1f}km)")
        else:
            st.success("✅ **距离无模糊**")
        
        duty_cycle = performance['占空比_百分比']
        st.progress(min(duty_cycle / 20, 1.0), text=f"占空比: {duty_cycle:.2f}%")
        
        if duty_cycle > 10:
            st.warning("⚠️ 高占空比，注意系统散热")
        elif duty_cycle < 0.1:
            st.info("ℹ️ 低占空比，适合高峰值功率应用")
        else:
            st.success("✅ 占空比合理")
        
        sampling_ratio = params.sampling_rate_hz / params.bandwidth_hz
        if sampling_ratio < 2:
            st.error(f"⚠️ **采样率不足** ({sampling_ratio:.1f}倍带宽)")
        else:
            st.success(f"✅ **采样率合理** ({sampling_ratio:.1f}倍带宽)")
            
        with st.expander("📋 指南：出现警告时，调节左侧栏中相关参数"): 
            st.markdown("""
                        
                        1. **距离模糊风险**：目标距离超过最大不模糊距离时，目标可能无法被清晰识别。
                        2. **占空比**：高占空比可能导致系统过热，低占空比可能不适合峰值功率应用。
                        3. **采样率不足**：采样率低于2倍带宽时，可能导致信号失真,建议2.5倍。
                        """)
        st.markdown("---")
        
        # 当前参数摘要
        st.markdown("### 🔧 当前参数")
        
        param_summary = [
            ("频率", f"{frequency_ghz:.1f} GHz"),
            ("带宽", f"{bandwidth_mhz:.0f} MHz"),
            ("PRF", f"{prf_khz:.1f} kHz"),
            ("脉宽", f"{pulse_width_us:.1f} μs"),
            ("脉冲数", f"{pulses}"),
            ("峰值功率", f"{peak_power_kw:.1f} kW"),
            ("天线增益", f"{antenna_gain_db:.1f} dB"),
            ("波束宽度", f"{beamwidth_deg:.1f}°"),
            ("采样率", f"{sampling_rate_mhz:.0f} MHz"),
            ("噪声系数", f"{noise_figure_db:.1f} dB"),
            ("基带增益", f"{baseband_gain_db:.0f} dB"),
            ("负载电阻", f"{load_resistance_ohm:.0f} Ω"),
            ("目标距离", f"{target_range_km:.0f} km"),
            ("目标RCS", f"{target_rcs_m2:.2f} m²")
        ]        

        for name, value in param_summary:
            col_name, col_value = st.columns([2, 1])
            with col_name:
                st.markdown(f"**{name}**")
            with col_value:
                st.markdown(f"`{value}`")
        
        st.markdown("---")
        
        # 导出配置
        st.markdown("### 💾 导出配置")
        
        yaml_config = params.to_yaml()
        
        if st.button("📄 显示YAML配置", width='stretch'):
            st.session_state.show_config = not st.session_state.show_config
        
        if st.session_state.show_config:
            st.code(yaml_config, language='yaml')
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 YAML",
                data=yaml_config,
                file_name=f"radar_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
                mime="text/yaml",
                width='stretch'
            )
        
        with col_dl2:
            python_code = f'''# 长城数字雷达仿真代码
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import radarsimpy as rs
import numpy as np

# 雷达参数配置
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
        'adc_bits': {params.adc_bits},
        'baseband_gain_db': {params.baseband_gain_db},
        'load_resistance_ohm': {params.load_resistance_ohm}
    }}
)

# 目标设置
target = {{
    'rcs_m2': {params.target_rcs_m2},
    'range_m': {params.target_range_m}
}}

print("长城数字雷达配置完成!")
print(f"频率: {{params.frequency_hz/1e9:.1f}} GHz")
print(f"带宽: {{params.bandwidth_hz/1e6:.0f}} MHz")
print(f"PRF: {{params.prf_hz/1e3:.1f}} kHz")
print(f"脉冲宽度: {{params.pulse_width_s*1e6:.1f}} μs")
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
    
    # 系统建议
    st.markdown("---")
    st.markdown("### 💡 系统优化建议")
    
    suggestions = []
    
    if params.prf_hz < 1000:
        suggestions.append("**低PRF模式**: 适合远程探测，但测速能力有限。考虑使用脉冲多普勒处理提高测速性能。")
    elif params.prf_hz > 10000:
        suggestions.append("**高PRF模式**: 适合测速，但距离模糊严重。建议使用PRF参差或解模糊算法。")
    else:
        suggestions.append("**中PRF模式**: 兼顾距离和速度测量，是现代雷达常用模式。")
    
    if performance['脉冲压缩比'] < 10:
        suggestions.append("**脉冲压缩增益较低**: 考虑增加带宽或脉宽以提高处理增益。")
    elif performance['脉冲压缩比'] > 1000:
        suggestions.append("**高处理增益**: 需要高性能信号处理器，注意计算复杂度。")
    
    if params.bandwidth_hz / params.frequency_hz > 0.1:
        suggestions.append("**宽带信号**: 相对带宽较大，注意系统线性度和相位一致性。")
    
    if performance['信噪比_dB'] < 10:
        suggestions.append("**信噪比低**: 考虑增加脉冲数、提高发射功率或使用脉冲压缩技术。")
    
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
    **长城数字雷达参数优化专家系统** • 基于简化雷达方程计算 • 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

if __name__ == "__main__":
    if 'current_preset' not in st.session_state:
        st.session_state.current_preset = "自定义"
    if 'show_config' not in st.session_state:
        st.session_state.show_config = False
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = "全部"
    if 'selected_radar_type' not in st.session_state:
        st.session_state.selected_radar_type = "全部"
    
    main()