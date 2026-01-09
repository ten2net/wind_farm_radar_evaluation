"""
电子战仿真实体模块
定义雷达、干扰机、目标等核心实体类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np
from datetime import datetime
import yaml

class EntityType(Enum):
    """实体类型枚举"""
    RADAR = "radar"
    JAMMER = "jammer"
    TARGET = "target"
    COMM_LINK = "communication_link"
    SENSOR = "sensor"

class EntityState(Enum):
    """实体状态枚举"""
    ACTIVE = "active"
    PASSIVE = "passive"
    JAMMED = "jammed"
    DESTROYED = "destroyed"
    EVADING = "evading"

@dataclass
class Position:
    """三维位置"""
    lat: float
    lon: float
    alt: float = 0.0  # 海拔高度，单位：米
    
    def to_array(self) -> np.ndarray:
        return np.array([self.lat, self.lon, self.alt])
    
    def distance_to(self, other: 'Position') -> float:
        """计算大圆距离（简化）"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # 地球半径，单位：米
        
        lat1, lon1 = radians(self.lat), radians(self.lon)
        lat2, lon2 = radians(other.lat), radians(other.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # 考虑高度差
        horizontal_dist = R * c
        height_diff = abs(self.alt - other.alt)
        
        return sqrt(horizontal_dist**2 + height_diff**2)

@dataclass
class RadarParameters:
    """雷达参数"""
    frequency: float  # GHz
    power: float  # kW
    gain: float  # dBi
    beamwidth: float  # 度
    pulse_width: float = 1.0  # μs
    prf: float = 1000  # Hz
    sensitivity: float = -120  # dBm
    range_max: float = 300  # km
    altitude_max: float = 25000  # m
    scan_pattern: str = "circular"  # circular, sector, raster
    scan_rate: float = 6  # rpm
    
    def wavelength(self) -> float:
        """计算波长"""
        c = 299792458  # 光速，m/s
        return c / (self.frequency * 1e9)
    
    def effective_range(self, target_rcs: float = 1.0) -> float:
        """计算有效探测距离（简化雷达方程）"""
        # 雷达方程: R^4 = (Pt * G^2 * λ^2 * σ) / ((4π)^3 * Smin)
        Pt = self.power * 1e3  # kW to W
        G = 10**(self.gain/10)  # dB to linear
        λ = self.wavelength()
        σ = target_rcs
        Smin = 10**(self.sensitivity/10) * 1e-3  # dBm to W
        
        R4 = (Pt * G**2 * λ**2 * σ) / ((4*np.pi)**3 * Smin)
        return R4**0.25 / 1000  # 转换为km

@dataclass
class JammerParameters:
    """干扰机参数"""
    frequency_range: Tuple[float, float]  # GHz
    power: float  # W
    gain: float  # dBi
    beamwidth: float  # 度
    eirp: float  # dBW
    jam_types: List[str]  # barrage, spot, sweep, deceptive
    response_time: float  # s
    bandwidth: float = 100  # MHz
    
    def effective_radiated_power(self) -> float:
        """计算有效辐射功率"""
        return 10 * np.log10(self.power) + self.gain

@dataclass
class Entity(ABC):
    """抽象基类：所有实体的基类"""
    id: str
    name: str
    entity_type: EntityType
    position: Position
    state: EntityState = EntityState.ACTIVE
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @abstractmethod
    def update(self, dt: float):
        """更新实体状态"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict:
        """转换为字典"""
        pass

@dataclass
class Radar(Entity):
    """雷达实体"""
    radar_params: RadarParameters= field(default_factory=RadarParameters) # type: ignore
    detection_history: List[Dict] = field(default_factory=list)
    coverage_polygon: Optional[Any] = None
    
    def __post_init__(self):
        self.entity_type = EntityType.RADAR
    
    def calculate_coverage(self, n_points: int = 72) -> np.ndarray:
        """计算雷达覆盖范围"""
        # 这里可以调用更复杂的覆盖模型
        # 简化的圆形覆盖
        ranges = np.linspace(0, 2*np.pi, n_points)
        range_km = self.radar_params.effective_range()
        
        # 转换为度
        lat_km = 111.0
        lon_km = 111.0 * np.cos(np.radians(self.position.lat))
        
        lats = self.position.lat + (range_km/lat_km) * np.sin(ranges)
        lons = self.position.lon + (range_km/lon_km) * np.cos(ranges)
        
        return np.column_stack([lats, lons])
    
    def update(self, dt: float):
        """更新雷达状态"""
        # 模拟扫描
        pass
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type.value,
            "position": {
                "lat": self.position.lat,
                "lon": self.position.lon,
                "alt": self.position.alt
            },
            "parameters": self.radar_params.__dict__,
            "state": self.state.value
        }

@dataclass
class Jammer(Entity):
    """干扰机实体"""
    jammer_params: JammerParameters = field(default_factory=JammerParameters) # type: ignore
    jamming_targets: List[str] = field(default_factory=list)
    effective_sector: Optional[Any] = None
    
    def __post_init__(self):
        self.entity_type = EntityType.JAMMER
    
    def calculate_jamming_sector(self, azimuth: float, width: float, range_km: float) -> np.ndarray:
        """计算干扰扇区"""
        # 生成扇形多边形
        angles = np.radians(np.linspace(azimuth - width/2, azimuth + width/2, 30))
        
        points = [(self.position.lon, self.position.lat)]
        for angle in angles:
            # 简化的地理计算
            lat_km = 111.0
            lon_km = 111.0 * np.cos(np.radians(self.position.lat))
            
            lat = self.position.lat + (range_km/lat_km) * np.sin(angle)
            lon = self.position.lon + (range_km/lon_km) * np.cos(angle)
            points.append((lon, lat))
        
        points.append((self.position.lon, self.position.lat))
        return np.array(points)
    
    def update(self, dt: float):
        """更新干扰机状态"""
        pass
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type.value,
            "position": {
                "lat": self.position.lat,
                "lon": self.position.lon,
                "alt": self.position.alt
            },
            "parameters": self.jammer_params.__dict__,
            "state": self.state.value
        }

@dataclass
class Target(Entity):
    """目标实体"""
    rcs: float = 1.0  # 雷达截面积，m²
    speed: float = 300  # m/s
    trajectory: List[Tuple[float, float, float]] = field(default_factory=list)  # [lat, lon, time]
    current_waypoint: int = 0
    
    def __post_init__(self):
        self.entity_type = EntityType.TARGET
    
    def update(self, dt: float):
        """更新目标位置"""
        if self.trajectory and self.current_waypoint < len(self.trajectory) - 1:
            # 简化的线性移动
            current = self.trajectory[self.current_waypoint]
            next_wp = self.trajectory[self.current_waypoint + 1]
            
            # 计算距离
            dist = np.sqrt((next_wp[0] - current[0])**2 + 
                          (next_wp[1] - current[1])**2)
            
            # 如果足够接近下一个航点
            if dist < 0.01:  # 约1km
                self.current_waypoint += 1
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type.value,
            "position": {
                "lat": self.position.lat,
                "lon": self.position.lon,
                "alt": self.position.alt
            },
            "rcs": self.rcs,
            "speed": self.speed,
            "state": self.state.value
        }
