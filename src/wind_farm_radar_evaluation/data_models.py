#!/usr/bin/env python3
"""
数据模型定义
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any

@dataclass
class RadarParameters:
    """雷达参数类"""
    name: str
    frequency: float
    bandwidth: float
    pulse_width: float
    tx_power: float
    pulses: int
    prp: float
    fs: float
    noise_figure: float
    rf_gain: float
    baseband_gain: float
    radar_height: float
    antenna_gain: float = 30
    beamwidth_azimuth: float = 1.5
    beamwidth_elevation: float = 20
    polarization: str = "horizontal"

@dataclass
class RadarGeolocation:
    """雷达地理定位类"""
    latitude: float
    longitude: float
    altitude: float
    heading: float
    name: str = "雷达站"

@dataclass
class TargetParameters:
    """目标参数类"""
    name: str
    target_type: str
    rcs: float
    speed_range: Tuple[float, float]
    altitude_range: Tuple[float, float]
    operational_profile: Dict[str, Any]

@dataclass
class SimulationParameters:
    """仿真参数类"""
    duration: float
    time_step: float
    enable_multipath: bool = True
    reflection_coeff: float = 0.4
    sea_level: float = 0.0

@dataclass
class VisualizationParameters:
    """可视化参数类"""
    output_dir: str = "results/figures"
    format: str = "png"
    dpi: int = 300
    theme: str = "plotly_white"
    color_map: str = "Viridis"

@dataclass
class CoordinateConverter:
    """坐标转换器类"""
    wgs84_a: float = 6378137.0
    wgs84_b: float = 6356752.314245
    wgs84_f: float = 1 / 298.257223563
    
    @staticmethod
    def wgs84_to_ecef(lat: float, lon: float, alt: float = 0.0) -> Tuple[float, float, float]:
        """将WGS84经纬度坐标转换为地心地固坐标系(ECEF)"""
        import math
        
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # 计算卯酉圈曲率半径
        e2 = 2 * CoordinateConverter.wgs84_f - CoordinateConverter.wgs84_f**2
        N = CoordinateConverter.wgs84_a / math.sqrt(1 - e2 * math.sin(lat_rad)**2)
        
        # 计算ECEF坐标
        x = (N + alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - e2) + alt) * math.sin(lat_rad)
        
        return (x, y, z)
    
    @staticmethod
    def ecef_to_enu(ref_lat: float, ref_lon: float, ref_alt: float, 
                   x_ecef: float, y_ecef: float, z_ecef: float) -> Tuple[float, float, float]:
        """将ECEF坐标转换为东北天坐标系(ENU)"""
        import math
        
        # 将参考点转换为ECEF
        ref_x, ref_y, ref_z = CoordinateConverter.wgs84_to_ecef(ref_lat, ref_lon, ref_alt)
        
        # 计算相对于参考点的ECEF坐标差
        dx = x_ecef - ref_x
        dy = y_ecef - ref_y
        dz = z_ecef - ref_z
        
        # 将角度转换为弧度
        ref_lat_rad = math.radians(ref_lat)
        ref_lon_rad = math.radians(ref_lon)
        
        # 计算旋转矩阵（ECEF到ENU）
        e_x = -math.sin(ref_lon_rad)
        e_y = math.cos(ref_lon_rad)
        e_z = 0
        
        n_x = -math.sin(ref_lat_rad) * math.cos(ref_lon_rad)
        n_y = -math.sin(ref_lat_rad) * math.sin(ref_lon_rad)
        n_z = math.cos(ref_lat_rad)
        
        u_x = math.cos(ref_lat_rad) * math.cos(ref_lon_rad)
        u_y = math.cos(ref_lat_rad) * math.sin(ref_lon_rad)
        u_z = math.sin(ref_lat_rad)
        
        # 应用旋转矩阵
        e = e_x * dx + e_y * dy + e_z * dz
        n = n_x * dx + n_y * dy + n_z * dz
        u = u_x * dx + u_y * dy + u_z * dz
        
        return (e, n, u)
    
    @staticmethod
    def wgs84_to_enu(ref_lat: float, ref_lon: float, ref_alt: float,
                    lat: float, lon: float, alt: float = 0.0) -> Tuple[float, float, float]:
        """将WGS84经纬度坐标直接转换为以参考点为原点的ENU坐标"""
        x_ecef, y_ecef, z_ecef = CoordinateConverter.wgs84_to_ecef(lat, lon, alt)
        return CoordinateConverter.ecef_to_enu(ref_lat, ref_lon, ref_alt, x_ecef, y_ecef, z_ecef)
