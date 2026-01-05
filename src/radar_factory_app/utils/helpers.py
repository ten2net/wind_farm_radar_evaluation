"""
辅助工具函数模块
提供格式化、转换、计算等通用工具函数
"""

import numpy as np
from typing import Union, List, Dict, Any, Optional
import math
from datetime import datetime, timedelta
import json
import re


def format_frequency(frequency_hz: float) -> str:
    """
    格式化频率显示
    
    Args:
        frequency_hz: 频率值(Hz)
        
    Returns:
        格式化后的频率字符串
    """
    if frequency_hz >= 1e9:
        return f"{frequency_hz / 1e9:.2f} GHz"
    elif frequency_hz >= 1e6:
        return f"{frequency_hz / 1e6:.2f} MHz"
    elif frequency_hz >= 1e3:
        return f"{frequency_hz / 1e3:.2f} kHz"
    else:
        return f"{frequency_hz:.2f} Hz"


def format_distance(distance_m: float) -> str:
    """
    格式化距离显示
    
    Args:
        distance_m: 距离值(米)
        
    Returns:
        格式化后的距离字符串
    """
    if distance_m >= 1000:
        return f"{distance_m / 1000:.2f} km"
    else:
        return f"{distance_m:.2f} m"


def format_power(power_w: float) -> str:
    """
    格式化功率显示
    
    Args:
        power_w: 功率值(瓦)
        
    Returns:
        格式化后的功率字符串
    """
    if power_w >= 1e6:
        return f"{power_w / 1e6:.2f} MW"
    elif power_w >= 1e3:
        return f"{power_w / 1e3:.2f} kW"
    else:
        return f"{power_w:.2f} W"


def format_time_duration(seconds: float) -> str:
    """
    格式化时间间隔显示
    
    Args:
        seconds: 时间间隔(秒)
        
    Returns:
        格式化后的时间字符串
    """
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f} ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:.0f}m {seconds:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"


def db_to_linear(db_value: float) -> float:
    """
    分贝值转换为线性值
    
    Args:
        db_value: 分贝值
        
    Returns:
        线性值
    """
    return 10 ** (db_value / 10)


def linear_to_db(linear_value: float) -> float:
    """
    线性值转换为分贝值
    
    Args:
        linear_value: 线性值
        
    Returns:
        分贝值
    """
    if linear_value <= 0:
        return -np.inf
    return 10 * np.log10(linear_value)


def wavelength_to_frequency(wavelength_m: float) -> float:
    """
    波长转换为频率
    
    Args:
        wavelength_m: 波长(米)
        
    Returns:
        频率(Hz)
    """
    return 3e8 / wavelength_m


def frequency_to_wavelength(frequency_hz: float) -> float:
    """
    频率转换为波长
    
    Args:
        frequency_hz: 频率(Hz)
        
    Returns:
        波长(米)
    """
    return 3e8 / frequency_hz


def calculate_radar_range(snr_min: float, pt: float, g: float, sigma: float, 
                         wavelength: float, losses: float = 1.0, 
                         noise_power: float = None) -> float: # type: ignore
    """
    计算雷达方程最大作用距离
    
    Args:
        snr_min: 最小信噪比(线性值)
        pt: 发射功率(W)
        g: 天线增益(线性值)
        sigma: 目标RCS(m²)
        wavelength: 波长(m)
        losses: 系统损耗(线性值)
        noise_power: 噪声功率(W)，如果提供则使用
        
    Returns:
        最大作用距离(m)
    """
    # 雷达方程: R^4 = (Pt * G^2 * λ^2 * σ) / ((4π)^3 * L * SNR_min * kTBF)
    numerator = pt * (g ** 2) * (wavelength ** 2) * sigma
    
    if noise_power is not None:
        # 使用噪声功率计算
        denominator = (4 * np.pi) ** 3 * losses * snr_min * noise_power
    else:
        # 简化计算
        denominator = (4 * np.pi) ** 3 * losses * snr_min
    
    if denominator <= 0:
        return 0.0
    
    return (numerator / denominator) ** 0.25


def calculate_doppler_frequency(velocity: float, wavelength: float) -> float:
    """
    计算多普勒频率
    
    Args:
        velocity: 径向速度(m/s)
        wavelength: 波长(m)
        
    Returns:
        多普勒频率(Hz)
    """
    return 2 * velocity / wavelength


def calculate_range_resolution(bandwidth: float) -> float:
    """
    计算距离分辨率
    
    Args:
        bandwidth: 信号带宽(Hz)
        
    Returns:
        距离分辨率(m)
    """
    return 3e8 / (2 * bandwidth)


def calculate_velocity_resolution(wavelength: float, integration_time: float) -> float:
    """
    计算速度分辨率
    
    Args:
        wavelength: 波长(m)
        integration_time: 积分时间(s)
        
    Returns:
        速度分辨率(m/s)
    """
    return wavelength / (2 * integration_time)


def calculate_beamwidth_from_aperture(aperture_size: float, wavelength: float) -> float:
    """
    根据孔径尺寸计算波束宽度
    
    Args:
        aperture_size: 孔径尺寸(m)
        wavelength: 波长(m)
        
    Returns:
        波束宽度(度)
    """
    # 近似公式: θ ≈ 70 * λ / D (度)
    return 70 * wavelength / aperture_size


def calculate_aperture_from_beamwidth(beamwidth_deg: float, wavelength: float) -> float:
    """
    根据波束宽度计算孔径尺寸
    
    Args:
        beamwidth_deg: 波束宽度(度)
        wavelength: 波长(m)
        
    Returns:
        孔径尺寸(m)
    """
    return 70 * wavelength / beamwidth_deg


def calculate_antenna_gain(aperture_size: float, wavelength: float, efficiency: float = 0.6) -> float:
    """
    计算天线增益
    
    Args:
        aperture_size: 孔径尺寸(m)
        wavelength: 波长(m)
        efficiency: 天线效率
        
    Returns:
        天线增益(dBi)
    """
    # G = 4π * A_eff / λ^2
    effective_aperture = aperture_size * efficiency
    gain_linear = 4 * np.pi * effective_aperture / (wavelength ** 2)
    return linear_to_db(gain_linear)


def calculate_snr_at_range(pt: float, g: float, sigma: float, wavelength: float,
                          range_m: float, losses: float = 1.0, 
                          noise_power: float = None) -> float: # type: ignore
    """
    计算指定距离处的信噪比
    
    Args:
        pt: 发射功率(W)
        g: 天线增益(线性值)
        sigma: 目标RCS(m²)
        wavelength: 波长(m)
        range_m: 距离(m)
        losses: 系统损耗(线性值)
        noise_power: 噪声功率(W)
        
    Returns:
        信噪比(线性值)
    """
    if range_m <= 0:
        return 0.0
    
    # 雷达方程: SNR = (Pt * G^2 * λ^2 * σ) / ((4π)^3 * R^4 * L * kTBF)
    numerator = pt * (g ** 2) * (wavelength ** 2) * sigma
    denominator = (4 * np.pi) ** 3 * (range_m ** 4) * losses
    
    if noise_power is not None:
        denominator *= noise_power
    
    if denominator <= 0:
        return 0.0
    
    return numerator / denominator


def coordinate_transform_cartesian_to_spherical(x: float, y: float, z: float) -> tuple:
    """
    笛卡尔坐标转换为球坐标
    
    Args:
        x, y, z: 笛卡尔坐标
        
    Returns:
        (range, azimuth, elevation) - 距离(m), 方位角(度), 俯仰角(度)
    """
    range_m = np.sqrt(x**2 + y**2 + z**2)
    
    if range_m == 0:
        return 0, 0, 0
    
    # 计算方位角 (0-360度，正东为0度，逆时针增加)
    azimuth_deg = np.degrees(np.arctan2(y, x))
    if azimuth_deg < 0:
        azimuth_deg += 360
    
    # 计算俯仰角
    elevation_deg = np.degrees(np.arcsin(z / range_m))
    
    return range_m, azimuth_deg, elevation_deg


def coordinate_transform_spherical_to_cartesian(range_m: float, azimuth_deg: float, 
                                              elevation_deg: float) -> tuple:
    """
    球坐标转换为笛卡尔坐标
    
    Args:
        range_m: 距离(m)
        azimuth_deg: 方位角(度)
        elevation_deg: 俯仰角(度)
        
    Returns:
        (x, y, z) 笛卡尔坐标
    """
    azimuth_rad = np.radians(azimuth_deg)
    elevation_rad = np.radians(elevation_deg)
    
    x = range_m * np.cos(elevation_rad) * np.cos(azimuth_rad)
    y = range_m * np.cos(elevation_rad) * np.sin(azimuth_rad)
    z = range_m * np.sin(elevation_rad)
    
    return x, y, z


def calculate_ground_range(slant_range: float, altitude: float) -> float:
    """
    计算斜距对应的地距
    
    Args:
        slant_range: 斜距(m)
        altitude: 高度(m)
        
    Returns:
        地距(m)
    """
    if slant_range < altitude:
        return 0.0
    return np.sqrt(slant_range**2 - altitude**2)


def calculate_horizon_range(altitude: float, earth_radius: float = 6371000) -> float:
    """
    计算雷达视距
    
    Args:
        altitude: 雷达高度(m)
        earth_radius: 地球半径(m)
        
    Returns:
        视距(m)
    """
    return np.sqrt(2 * earth_radius * altitude + altitude**2)


def atmospheric_attenuation(frequency_hz: float, range_km: float, 
                          temperature: float = 15, humidity: float = 60,
                          rain_rate: float = 0) -> float:
    """
    计算大气衰减
    
    Args:
        frequency_hz: 频率(Hz)
        range_km: 距离(km)
        temperature: 温度(℃)
        humidity: 湿度(%)
        rain_rate: 降雨率(mm/h)
        
    Returns:
        衰减值(dB)
    """
    frequency_ghz = frequency_hz / 1e9
    
    # 氧气衰减 (dB/km)
    oxygen_att = 0.007 * frequency_ghz**2 / (frequency_ghz**2 + 0.3) + \
                0.0005 * frequency_ghz**2
    
    # 水蒸气衰减 (dB/km)
    vapor_att = 0.0001 * frequency_ghz**2 * humidity / 100
    
    # 降雨衰减 (dB/km)
    if rain_rate > 0:
        if frequency_ghz < 10:
            rain_att = 0.0001 * rain_rate**1.5
        else:
            rain_att = 0.001 * rain_rate**1.2
    else:
        rain_att = 0
    
    total_att_per_km = oxygen_att + vapor_att + rain_att
    return total_att_per_km * range_km


def validate_radar_parameters(frequency: float, power: float, pulse_width: float) -> Dict[str, Any]:
    """
    验证雷达参数合理性
    
    Args:
        frequency: 频率(Hz)
        power: 功率(W)
        pulse_width: 脉冲宽度(s)
        
    Returns:
        验证结果字典
    """
    results = {
        "valid": True,
        "warnings": [],
        "errors": []
    }
    
    # 频率验证
    if frequency < 100e6:
        results["warnings"].append("频率低于100MHz，可能受电离层影响")
    elif frequency > 100e9:
        results["errors"].append("频率高于100GHz，大气衰减严重")
        results["valid"] = False
    
    # 功率验证
    if power > 10e6:
        results["warnings"].append("发射功率超过10MW，需考虑散热和安全问题")
    elif power < 100:
        results["warnings"].append("发射功率较低，探测距离受限")
    
    # 脉冲宽度验证
    if pulse_width > 1e-3:
        results["warnings"].append("脉冲宽度较大，距离分辨率较低")
    elif pulse_width < 1e-9:
        results["errors"].append("脉冲宽度过小，技术实现困难")
        results["valid"] = False
    
    return results


def generate_radar_id(name: str, band: str, platform: str) -> str:
    """
    生成雷达ID
    
    Args:
        name: 雷达名称
        band: 频段
        platform: 平台类型
        
    Returns:
        雷达ID字符串
    """
    # 提取名称中的字母和数字
    name_clean = re.sub(r'[^a-zA-Z0-9]', '', name)
    
    # 取前4个字符（如果存在）
    name_part = name_clean[:4].upper() if name_clean else "RAD"
    
    # 频段代码
    band_code = band.upper() if band else "X"
    
    # 平台代码
    platform_map = {
        "地面机动": "GM", "机载": "AB", "舰载": "SB", "固定阵地": "FX"
    }
    platform_code = platform_map.get(platform, "OT")
    
    # 时间戳（确保唯一性）
    timestamp = datetime.now().strftime("%m%d%H%M")
    
    return f"{name_part}_{band_code}{platform_code}{timestamp}"


def save_radar_config(radar_config: Dict[str, Any], filename: str) -> bool:
    """
    保存雷达配置到文件
    
    Args:
        radar_config: 雷达配置字典
        filename: 文件名
        
    Returns:
        成功返回True，失败返回False
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(radar_config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存雷达配置失败: {e}")
        return False


def load_radar_config(filename: str) -> Optional[Dict[str, Any]]:
    """
    从文件加载雷达配置
    
    Args:
        filename: 文件名
        
    Returns:
        雷达配置字典，失败返回None
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载雷达配置失败: {e}")
        return None


class Timer:
    """简单的计时器类"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = datetime.now()
        self.end_time = None
    
    def stop(self) -> float:
        """停止计时并返回耗时(秒)"""
        self.end_time = datetime.now()
        return self.elapsed()
    
    def elapsed(self) -> float:
        """返回已耗时(秒)"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else datetime.now()
        return (end - self.start_time).total_seconds()
    
    def reset(self):
        """重置计时器"""
        self.start_time = None
        self.end_time = None


def create_progress_callback(total_steps: int):
    """
    创建进度回调函数
    
    Args:
        total_steps: 总步数
        
    Returns:
        进度回调函数
    """
    def callback(current_step: int, message: str = ""):
        progress = current_step / total_steps
        print(f"\r进度: {progress:.1%} - {message}", end="", flush=True)
        if current_step >= total_steps:
            print()  # 换行
    
    return callback


# 测试代码
if __name__ == "__main__":
    # 测试频率格式化
    print("频率格式化测试:")
    print(f"300e6 Hz = {format_frequency(300e6)}")
    print(f"1.4e9 Hz = {format_frequency(1.4e9)}")
    print(f"3.7e9 Hz = {format_frequency(3.7e9)}")
    
    # 测试距离计算
    print("\n雷达距离计算测试:")
    range_km = calculate_radar_range(
        snr_min=10,  # 10dB -> 10倍线性值
        pt=100000,   # 100kW
        g=db_to_linear(35),  # 35dBi
        sigma=1.0,   # 1m² RCS
        wavelength=0.1,  # 10cm波长
        losses=db_to_linear(3)  # 3dB损耗
    ) / 1000  # 转换为km
    
    print(f"计算探测距离: {range_km:.2f} km")
    
    # 测试坐标转换
    print("\n坐标转换测试:")
    x, y, z = 1000, 2000, 3000
    r, az, el = coordinate_transform_cartesian_to_spherical(x, y, z)
    print(f"笛卡尔坐标({x}, {y}, {z}) -> 球坐标(距离:{r:.1f}m, 方位:{az:.1f}°, 俯仰:{el:.1f}°)")
    
    # 测试参数验证
    print("\n参数验证测试:")
    validation = validate_radar_parameters(10e9, 1e6, 1e-6)
    print(f"验证结果: {validation}")