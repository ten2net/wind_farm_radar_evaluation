"""
配置文件
定义系统常量、配置参数和默认值
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# 路径配置
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUTS_DIR = BASE_DIR / "outputs"
EXAMPLES_DIR = BASE_DIR / "examples"
REPORTS_DIR = BASE_DIR / "reports"

# 应用信息
APP_TITLE = "🌪️ 风电场对雷达探测性能影响评估系统"
APP_DESCRIPTION = "基于雷达方程与AI分析的专业评估工具，支持多场景、多频段雷达性能量化分析"

# 雷达频段定义
RADAR_FREQUENCY_BANDS = {
    "VHF": {"freq_min": 30, "freq_max": 300, "unit": "MHz", "description": "甚高频"},
    "UHF": {"freq_min": 300, "freq_max": 1000, "unit": "MHz", "description": "特高频"},
    "L": {"freq_min": 1, "freq_max": 2, "unit": "GHz", "description": "L波段"},
    "S": {"freq_min": 2, "freq_max": 4, "unit": "GHz", "description": "S波段"},
    "C": {"freq_min": 4, "freq_max": 8, "unit": "GHz", "description": "C波段"},
    "X": {"freq_min": 8, "freq_max": 12, "unit": "GHz", "description": "X波段"},
    "Ku": {"freq_min": 12, "freq_max": 18, "unit": "GHz", "description": "Ku波段"},
    "Ka": {"freq_min": 26.5, "freq_max": 40, "unit": "GHz", "description": "Ka波段"}
}

# 天线类型定义
ANTENNA_TYPES = {
    "omnidirectional": {
        "name": "全向天线",
        "gain": 2.15,  # dBi
        "beamwidth_h": 360,  # 水平波束宽度
        "beamwidth_v": 360,  # 垂直波束宽度
        "description": "在各个方向上辐射强度基本一致的天线"
    },
    "directional": {
        "name": "定向天线",
        "gain": 24.0,  # dBi
        "beamwidth_h": 30,  # 水平波束宽度
        "beamwidth_v": 30,  # 垂直波束宽度
        "description": "在特定方向上具有较高增益的天线"
    },
    "sector": {
        "name": "扇区天线",
        "gain": 16.0,  # dBi
        "beamwidth_h": 90,  # 水平波束宽度
        "beamwidth_v": 30,  # 垂直波束宽度
        "description": "覆盖特定扇区范围的天线"
    },
    "parabolic": {
        "name": "抛物面天线",
        "gain": 40.0,  # dBi
        "beamwidth_h": 2.0,  # 水平波束宽度
        "beamwidth_v": 2.0,  # 垂直波束宽度
        "description": "高增益定向天线，常用于雷达和卫星通信"
    }
}

# 风机型号数据库
TURBINE_MODELS = {
    "Vestas_V150": {
        "manufacturer": "Vestas",
        "model": "V150",
        "rated_power": 4200,  # kW
        "hub_height": 105,  # m
        "rotor_diameter": 150,  # m
        "total_height": 180,  # m
        "blade_material": "复合材料",
        "rcs_profile": "medium",  # 雷达散射截面特征
        "image_path": "models/vestas_v150.png",
        "stl_path": "models/vestas_v150.stl"
    },
    "Siemens_Gamesa_SG145": {
        "manufacturer": "Siemens Gamesa",
        "model": "SG145",
        "rated_power": 4500,  # kW
        "hub_height": 120,  # m
        "rotor_diameter": 145,  # m
        "total_height": 192.5,  # m
        "blade_material": "复合材料",
        "rcs_profile": "medium",
        "image_path": "models/siemens_sg145.png",
        "stl_path": "models/siemens_sg145.stl"
    },
    "GE_Cypress_5.3": {
        "manufacturer": "General Electric",
        "model": "Cypress 5.3",
        "rated_power": 5300,  # kW
        "hub_height": 135,  # m
        "rotor_diameter": 158,  # m
        "total_height": 214,  # m
        "blade_material": "复合材料",
        "rcs_profile": "large",
        "image_path": "models/ge_cypress.png",
        "stl_path": "models/ge_cypress.stl"
    },
    "Goldwind_GW155": {
        "manufacturer": "金风科技",
        "model": "GW155",
        "rated_power": 4500,  # kW
        "hub_height": 110,  # m
        "rotor_diameter": 155,  # m
        "total_height": 187.5,  # m
        "blade_material": "复合材料",
        "rcs_profile": "medium",
        "image_path": "models/goldwind_gw155.png",
        "stl_path": "models/goldwind_gw155.stl"
    },
    "Envision_EN156": {
        "manufacturer": "远景能源",
        "model": "EN156",
        "rated_power": 4800,  # kW
        "hub_height": 125,  # m
        "rotor_diameter": 156,  # m
        "total_height": 203,  # m
        "blade_material": "复合材料",
        "rcs_profile": "medium",
        "image_path": "models/envision_en156.png",
        "stl_path": "models/envision_en156.stl"
    }
}

# 目标类型RCS数据库
TARGET_RCS_DB = {
    "民航飞机": {
        "category": "航空器",
        "rcs_min": 1.0,  # m²
        "rcs_max": 100.0,  # m²
        "rcs_typical": 10.0,  # m²
        "speed_typical": 250,  # m/s
        "altitude_typical": 10000,  # m
        "description": "商用客机，如波音737、空客A320等"
    },
    "军用飞机": {
        "category": "航空器",
        "rcs_min": 0.1,  # m²
        "rcs_max": 10.0,  # m²
        "rcs_typical": 1.0,  # m²
        "speed_typical": 300,  # m/s
        "altitude_typical": 8000,  # m
        "description": "战斗机、轰炸机等军用飞机"
    },
    "无人机": {
        "category": "小型航空器",
        "rcs_min": 0.001,  # m²
        "rcs_max": 0.1,  # m²
        "rcs_typical": 0.01,  # m²
        "speed_typical": 30,  # m/s
        "altitude_typical": 500,  # m
        "description": "小型无人机系统"
    },
    "巡航导弹": {
        "category": "导弹",
        "rcs_min": 0.01,  # m²
        "rcs_max": 0.5,  # m²
        "rcs_typical": 0.1,  # m²
        "speed_typical": 250,  # m/s
        "altitude_typical": 100,  # m
        "description": "巡航导弹目标"
    },
    "船舶": {
        "category": "水面目标",
        "rcs_min": 100.0,  # m²
        "rcs_max": 10000.0,  # m²
        "rcs_typical": 1000.0,  # m²
        "speed_typical": 15,  # m/s
        "altitude_typical": 0,  # m
        "description": "各类水面船只"
    },
    "车辆": {
        "category": "地面目标",
        "rcs_min": 1.0,  # m²
        "rcs_max": 100.0,  # m²
        "rcs_typical": 10.0,  # m²
        "speed_typical": 20,  # m/s
        "altitude_typical": 0,  # m
        "description": "地面车辆目标"
    }
}

# 雷达类型定义
RADAR_TYPES = {
    "气象雷达": {
        "frequency_band": "S",
        "peak_power": 1000000,  # W
        "average_power": 1000,  # W
        "pulse_width": 2.0,  # μs
        "prf": 300,  # Hz
        "antenna_gain": 40,  # dBi
        "beam_width": 1.0,  # 度
        "noise_figure": 3.0,  # dB
        "system_losses": 6.0,  # dB
        "description": "用于气象观测的雷达系统"
    },
    "航管雷达": {
        "frequency_band": "L",
        "peak_power": 2000000,  # W
        "average_power": 2000,  # W
        "pulse_width": 1.0,  # μs
        "prf": 1000,  # Hz
        "antenna_gain": 35,  # dBi
        "beam_width": 1.5,  # 度
        "noise_figure": 2.5,  # dB
        "system_losses": 5.0,  # dB
        "description": "空中交通管制雷达"
    },
    "军用监视雷达": {
        "frequency_band": "S",
        "peak_power": 5000000,  # W
        "average_power": 5000,  # W
        "pulse_width": 0.5,  # μs
        "prf": 2000,  # Hz
        "antenna_gain": 45,  # dBi
        "beam_width": 0.8,  # 度
        "noise_figure": 2.0,  # dB
        "system_losses": 4.0,  # dB
        "description": "军用对空监视雷达"
    },
    "导航雷达": {
        "frequency_band": "X",
        "peak_power": 25000,  # W
        "average_power": 25,  # W
        "pulse_width": 0.1,  # μs
        "prf": 3000,  # Hz
        "antenna_gain": 30,  # dBi
        "beam_width": 2.0,  # 度
        "noise_figure": 4.0,  # dB
        "system_losses": 8.0,  # dB
        "description": "船舶导航雷达"
    }
}

# 通信系统类型
COMMUNICATION_SYSTEMS = {
    "基站": {
        "frequency": 1800,  # MHz
        "bandwidth": 20,  # MHz
        "antenna_gain": 18,  # dBi
        "eirp": 50,  # dBm
        "antenna_height": 30,  # m
        "antenna_type": "sector",
        "description": "移动通信基站"
    },
    "微波中继": {
        "frequency": 6000,  # MHz
        "bandwidth": 40,  # MHz
        "antenna_gain": 38,  # dBi
        "eirp": 40,  # dBm
        "antenna_height": 50,  # m
        "antenna_type": "parabolic",
        "description": "微波通信中继站"
    },
    "卫星地球站": {
        "frequency": 14000,  # MHz
        "bandwidth": 50,  # MHz
        "antenna_gain": 50,  # dBi
        "eirp": 75,  # dBm
        "antenna_height": 10,  # m
        "antenna_type": "parabolic",
        "description": "卫星通信地球站"
    },
    "广播发射台": {
        "frequency": 100,  # MHz
        "bandwidth": 0.2,  # MHz
        "antenna_gain": 5,  # dBi
        "eirp": 90,  # dBm
        "antenna_height": 100,  # m
        "antenna_type": "omnidirectional",
        "description": "广播信号发射台"
    }
}

# 物理常数
PHYSICAL_CONSTANTS = {
    "speed_of_light": 299792458,  # 光速，m/s
    "boltzmann_constant": 1.380649e-23,  # 玻尔兹曼常数，J/K
    "standard_temperature": 290,  # 标准温度，K
    "earth_radius": 6371000,  # 地球半径，m
    "standard_atmosphere_pressure": 101325,  # 标准大气压，Pa
    "permittivity_of_free_space": 8.854187817e-12,  # 真空介电常数，F/m
    "permeability_of_free_space": 1.2566370614e-6,  # 真空磁导率，H/m
}

# 评估参数
EVALUATION_PARAMS = {
    "snr_threshold": 13,  # 检测所需最小信噪比，dB
    "range_resolution": 150,  # 距离分辨率，m
    "velocity_resolution": 1.0,  # 速度分辨率，m/s
    "max_range": 500000,  # 最大评估距离，m
    "range_steps": 100,  # 距离分析步数
    "azimuth_steps": 36,  # 方位分析步数
    "elevation_steps": 18,  # 俯仰分析步数
    "frequency_points": 50,  # 频率分析点数
    "doppler_bins": 64,  # 多普勒分析点数
}

# 地图配置
MAP_CONFIG = {
    "default_center": [40.0, 116.0],  # 默认地图中心 [lat, lon]
    "default_zoom": 9,  # 默认缩放级别
    "tile_providers": {
        "OpenStreetMap": "OpenStreetMap",
        "CartoDB Dark": "CartoDB dark_matter",
        "Stamen Terrain": "Stamen Terrain",
        "Esri Satellite": "Esri.WorldImagery"
    },
    "tile_provider_default": "CartoDB dark_matter"
}

# 颜色方案
COLOR_SCHEME = {
    "primary": "#00ccff",  # 主色调 - 科技蓝
    "secondary": "#00ff99",  # 次要色调 - 青绿色
    "accent": "#ff3366",  # 强调色 - 玫红色
    "warning": "#ff9900",  # 警告色 - 橙色
    "success": "#00cc66",  # 成功色 - 绿色
    "danger": "#ff3333",  # 危险色 - 红色
    "info": "#33ccff",  # 信息色 - 浅蓝色
    "dark": "#0c0c0c",  # 深色背景
    "darker": "#080808",  # 更深背景
    "light": "#f0f8ff",  # 浅色文本
    "lighter": "#ffffff",  # 更浅文本
    "wind_turbine": "#00ff99",  # 风机颜色
    "radar_station": "#ff3366",  # 雷达站颜色
    "comm_station": "#33ccff",  # 通信站颜色
    "target": "#ff9900",  # 目标颜色
    "coverage_area": "rgba(0, 204, 255, 0.2)",  # 覆盖区域颜色
    "interference_area": "rgba(255, 51, 102, 0.2)",  # 干扰区域颜色
}

# 图表配置
CHART_CONFIG = {
    "template": "plotly_dark",  # Plotly模板
    "width": 800,  # 图表宽度
    "height": 500,  # 图表高度
    "font_family": "Arial, sans-serif",  # 字体
    "font_size": 12,  # 字体大小
    "title_font_size": 16,  # 标题字体大小
    "color_scale": "Viridis",  # 颜色比例尺
    "color_scale_diverging": "RdBu",  # 发散颜色比例尺
    "marker_size": 8,  # 标记大小
    "line_width": 2,  # 线宽
}

# 报告配置
REPORT_CONFIG = {
    "company_name": "风电雷达影响评估中心",
    "report_title": "风电场对雷达探测性能影响评估报告",
    "report_version": "1.0",
    "author": "风电雷达评估系统",
    "output_format": "markdown",  # 输出格式: markdown, pdf, html
    "include_sections": [
        "executive_summary",  # 执行摘要
        "project_overview",  # 项目概述
        "methodology",  # 评估方法
        "scenario_description",  # 场景描述
        "analysis_results",  # 分析结果
        "impact_assessment",  # 影响评估
        "mitigation_measures",  # 缓解措施
        "conclusions",  # 结论
        "recommendations",  # 建议
        "appendices"  # 附录
    ],
    "max_pages": 50,  # 报告最大页数
    "image_quality": "high",  # 图片质量: low, medium, high
    "toc_depth": 3,  # 目录深度
}

# Kimi API配置
KIMI_API_CONFIG = {
    "base_url": "https://api.moonshot.cn/v1",
    "chat_completion_endpoint": "/chat/completions",
    "model": "moonshot-v1-8k",  # 使用的模型
    "temperature": 0.7,  # 温度参数
    "max_tokens": 2000,  # 最大token数
    "timeout": 30,  # 超时时间，秒
    "retry_attempts": 3,  # 重试次数
    "retry_delay": 1,  # 重试延迟，秒
}

# 数据验证规则
VALIDATION_RULES = {
    "latitude": {"min": -90, "max": 90, "type": "float"},
    "longitude": {"min": -180, "max": 180, "type": "float"},
    "altitude": {"min": -100, "max": 10000, "type": "float"},  # 海拔，米
    "frequency": {"min": 0.01, "max": 100, "type": "float"},  # GHz
    "power": {"min": 0.001, "max": 10000000, "type": "float"},  # W
    "gain": {"min": 0, "max": 60, "type": "float"},  # dBi
    "rcs": {"min": 0.0001, "max": 10000, "type": "float"},  # m²
    "distance": {"min": 0, "max": 1000000, "type": "float"},  # m
    "speed": {"min": 0, "max": 1000, "type": "float"},  # m/s
    "height": {"min": 0, "max": 1000, "type": "float"},  # m
    "diameter": {"min": 0, "max": 200, "type": "float"},  # m
}

# 系统消息
SYSTEM_MESSAGES = {
    "welcome": "欢迎使用风电场对雷达探测性能影响评估系统",
    "scenario_loaded": "场景配置文件加载成功",
    "analysis_started": "开始雷达性能分析",
    "analysis_completed": "雷达性能分析完成",
    "report_generating": "正在生成评估报告",
    "report_completed": "评估报告生成完成",
    "export_completed": "数据导出完成",
    "error_invalid_file": "文件格式无效，请上传YAML格式文件",
    "error_validation": "数据验证失败，请检查输入参数",
    "error_analysis": "分析过程中发生错误",
    "error_export": "导出过程中发生错误",
    "warning_no_scenario": "未加载场景文件，请先加载场景配置文件",
    "warning_no_analysis": "未进行性能分析，请先进行雷达性能分析",
    "warning_no_report": "未生成报告，请先生成评估报告",
    "info_loading": "正在加载数据，请稍候...",
    "info_processing": "正在处理数据，请稍候...",
    "info_exporting": "正在导出数据，请稍候...",
}

# 数据类定义
@dataclass
class WindTurbine:
    """风机数据类"""
    id: str
    model: str
    position: Dict[str, float]  # {lat, lon, alt}
    height: float
    rotor_diameter: float
    orientation: float = 0.0
    operational: bool = True
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RadarStation:
    """雷达站数据类"""
    id: str
    radar_type: str
    frequency_band: str
    position: Dict[str, float]  # {lat, lon, alt}
    peak_power: float
    antenna_gain: float
    beam_width: float
    antenna_height: float
    polarization: str = "horizontal"
    scanning_mode: str = "mechanical"
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CommunicationStation:
    """通信站数据类"""
    id: str
    frequency: float
    position: Dict[str, float]  # {lat, lon, alt}
    antenna_type: str
    eirp: float
    antenna_height: float
    service_type: str = "mobile"
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Target:
    """目标数据类"""
    id: str
    target_type: str
    rcs: float
    position: Dict[str, float]  # {lat, lon, alt}
    speed: float
    heading: float
    altitude: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Scenario:
    """评估场景数据类"""
    name: str
    description: str
    wind_turbines: List[WindTurbine]
    radar_stations: List[RadarStation]
    communication_stations: List[CommunicationStation]
    targets: List[Target]
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None

# 工具函数
def get_band_frequency_range(band: str) -> Tuple[float, float]:
    """获取频段的频率范围（GHz）"""
    band_info = RADAR_FREQUENCY_BANDS.get(band.upper())
    if not band_info:
        raise ValueError(f"未知频段: {band}")
    
    freq_min = band_info["freq_min"]
    freq_max = band_info["freq_max"]
    unit = band_info["unit"]
    
    # 转换为GHz
    if unit == "MHz":
        freq_min /= 1000
        freq_max /= 1000
    elif unit == "GHz":
        pass
    else:
        raise ValueError(f"未知频率单位: {unit}")
    
    return freq_min, freq_max

def get_band_center_frequency(band: str) -> float:
    """获取频段的中心频率（GHz）"""
    freq_min, freq_max = get_band_frequency_range(band)
    return (freq_min + freq_max) / 2

def wavelength_from_frequency(frequency_ghz: float) -> float:
    """从频率计算波长（米）"""
    c = PHYSICAL_CONSTANTS["speed_of_light"]
    frequency_hz = frequency_ghz * 1e9
    return c / frequency_hz

def frequency_from_wavelength(wavelength_m: float) -> float:
    """从波长计算频率（GHz）"""
    c = PHYSICAL_CONSTANTS["speed_of_light"]
    frequency_hz = c / wavelength_m
    return frequency_hz / 1e9

def db_to_linear(db_value: float) -> float:
    """分贝值转换为线性值"""
    return 10 ** (db_value / 10)

def linear_to_db(linear_value: float) -> float:
    """线性值转换为分贝值"""
    if linear_value <= 0:
        return -float('inf')
    return 10 * np.log10(linear_value)

def calculate_free_space_loss(distance_m: float, frequency_ghz: float) -> float:
    """计算自由空间路径损耗（dB）"""
    wavelength = wavelength_from_frequency(frequency_ghz)
    loss = 20 * np.log10(distance_m) + 20 * np.log10(frequency_ghz * 1e9) + 20 * np.log10(4 * np.pi / PHYSICAL_CONSTANTS["speed_of_light"])
    return loss

def validate_coordinates(lat: float, lon: float, alt: float) -> bool:
    """验证坐标值是否在有效范围内"""
    rules = VALIDATION_RULES
    
    lat_ok = rules["latitude"]["min"] <= lat <= rules["latitude"]["max"]
    lon_ok = rules["longitude"]["min"] <= lon <= rules["longitude"]["max"]
    alt_ok = rules["altitude"]["min"] <= alt <= rules["altitude"]["max"]
    
    return lat_ok and lon_ok and alt_ok

# 确保输出目录存在
for directory in [OUTPUTS_DIR, TEMPLATES_DIR, EXAMPLES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)