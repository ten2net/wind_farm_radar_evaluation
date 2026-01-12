# core_module.py
import numpy as np
import pandas as pd
from math import radians, sin, cos, sqrt, atan2, exp
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json
from datetime import datetime

class GuidanceMode(Enum):
    """导引头工作模式"""
    PASSIVE = "passive"
    ACTIVE = "active"
    COMPOSITE = "composite"

class JammingType(Enum):
    """干扰类型"""
    NOISE = "noise"           # 噪声压制干扰
    DECEPTION = "deception"   # 欺骗式干扰
    SMART_NOISE = "smart_noise"  # 灵巧噪声干扰
    NONE = "none"            # 无干扰

class TargetType(Enum):
    """目标类型"""
    FIGHTER = "fighter"      # 战斗机
    BOMBER = "bomber"        # 轰炸机  
    AWACS = "awacs"          # 预警机
    WARSHIP = "warship"      # 军舰
    RADAR_STATION = "radar_station"  # 雷达站

@dataclass
class Position:
    """地理位置类"""
    lat: float
    lon: float
    alt: float = 0.0  # 海拔高度(米)
    
    def to_array(self):
        return np.array([self.lat, self.lon, self.alt])

@dataclass
class TrajectoryPoint:
    """轨迹点"""
    position: Position
    timestamp: datetime
    performance: float
    distance_to_target: float

class GuidanceSystem:
    """导引头基类"""
    def __init__(self, name: str, color: str, mode: GuidanceMode):
        self.name = name
        self.color = color
        self.mode = mode
        self.detection_range = 0.0  # km
        self.jamming_resistance = 0.0
        self.stealth_level = 0.0
        self.accuracy = 0.0
        self.current_performance = 0.0
        self.trajectory: List[TrajectoryPoint] = []
        
    def calculate_performance(self, target_range: float, jamming_power: float, 
                            terrain_factor: float = 1.0, weather_factor: float = 1.0) -> float:
        """计算导引头性能指标"""
        raise NotImplementedError
        
    def record_trajectory(self, position: Position, target_range: float, performance: float):
        """记录轨迹点"""
        point = TrajectoryPoint(
            position=position,
            timestamp=datetime.now(),
            performance=performance,
            distance_to_target=target_range
        )
        self.trajectory.append(point)
        
    def get_trajectory_data(self) -> pd.DataFrame:
        """获取轨迹数据为DataFrame"""
        data = []
        for point in self.trajectory:
            data.append({
                'timestamp': point.timestamp,
                'lat': point.position.lat,
                'lon': point.position.lon,
                'alt': point.position.alt,
                'performance': point.performance,
                'distance_to_target': point.distance_to_target
            })
        return pd.DataFrame(data)

class PassiveRadarSeeker(GuidanceSystem):
    """被动雷达导引头"""
    def __init__(self):
        super().__init__("被动雷达导引头", "blue", GuidanceMode.PASSIVE)
        self.detection_range = 80.0
        self.jamming_resistance = 0.7
        self.stealth_level = 0.9
        self.accuracy = 0.6
        
    def calculate_performance(self, target_range: float, jamming_power: float,
                            terrain_factor: float = 1.0, weather_factor: float = 1.0) -> float:
        base_range = self.detection_range * terrain_factor * weather_factor
        jamming_effect = jamming_power * (1 - self.jamming_resistance)
        range_factor = max(0, 1 - (target_range / base_range) ** 2)
        performance = range_factor * (1 - jamming_effect)
        self.current_performance = max(0, performance)
        return self.current_performance

class ActiveRadarSeeker(GuidanceSystem):
    """主动雷达导引头"""
    def __init__(self):
        super().__init__("主动雷达导引头", "red", GuidanceMode.ACTIVE)
        self.detection_range = 100.0
        self.jamming_resistance = 0.4
        self.stealth_level = 0.2
        self.accuracy = 0.8
        
    def calculate_performance(self, target_range: float, jamming_power: float,
                            terrain_factor: float = 1.0, weather_factor: float = 1.0) -> float:
        base_range = self.detection_range * terrain_factor * weather_factor
        jamming_effect = jamming_power * (1 - self.jamming_resistance)
        range_factor = max(0, 1 - (target_range / base_range) ** 4)
        performance = range_factor * (1 - jamming_effect)
        self.current_performance = max(0, performance)
        return self.current_performance

class CompositeSeeker(GuidanceSystem):
    """复合制导导引头"""
    def __init__(self):
        super().__init__("复合制导导引头", "green", GuidanceMode.COMPOSITE)
        self.detection_range = 120.0
        self.jamming_resistance = 0.8
        self.stealth_level = 0.7
        self.accuracy = 0.9
        self.current_mode = "passive"  # 当前工作模式
        
    def calculate_performance(self, target_range: float, jamming_power: float,
                            terrain_factor: float = 1.0, weather_factor: float = 1.0) -> float:
        base_range = self.detection_range * terrain_factor * weather_factor
        
        # 模式切换逻辑
        if target_range > base_range * 0.6:
            self.current_mode = "passive"
            jamming_effect = jamming_power * (1 - 0.8)  # 被动模式抗干扰强
            range_factor = max(0, 1 - (target_range / base_range) ** 2)
        else:
            self.current_mode = "active" 
            jamming_effect = jamming_power * (1 - 0.6)  # 主动模式精度高
            range_factor = max(0, 1 - (target_range / base_range) ** 3)
            
        performance = range_factor * (1 - jamming_effect)
        self.current_performance = max(0, performance)
        return self.current_performance

@dataclass
class Target:
    """目标类"""
    target_id: str
    target_type: TargetType
    position: Position
    emission_power: float  # 辐射功率
    rcs: float  # 雷达截面积
    velocity: float = 0.0  # 速度 m/s
    heading: float = 0.0   # 航向 度
    
    def get_characteristics(self) -> Dict:
        """获取目标特性"""
        return {
            'target_id': self.target_id,
            'target_type': self.target_type.value,
            'emission_power': self.emission_power,
            'rcs': self.rcs,
            'velocity': self.velocity,
            'heading': self.heading
        }

@dataclass  
class Jammer:
    """干扰机类"""
    jammer_id: str
    position: Position
    jamming_type: JammingType
    power: float  # 干扰功率
    range: float  # 干扰范围 km
    target_id: Optional[str] = None  # 保护的目标ID
    
    def get_jamming_effectiveness(self, distance: float) -> float:
        """根据距离计算干扰效果"""
        if distance > self.range:
            return 0.0
        return self.power * (1 - distance / self.range)

class TerrainModel:
    """地形模型类"""
    def __init__(self):
        self.terrain_data = {}  # DEM数据缓存
        self.resolution = 0.01  # 度
        
    def get_elevation(self, lat: float, lon: float) -> float:
        """获取海拔高度（简化版本，实际应使用DEM数据）"""
        # 这里使用简单的地理模型，实际应用应接入真实DEM数据
        base_elevation = 100 * sin(lat * 10) * cos(lon * 10)
        return max(0, base_elevation)
    
    def get_terrain_factor(self, pos1: Position, pos2: Position) -> float:
        """计算地形对探测的影响因子"""
        # 简化模型：考虑两点间的地形遮挡
        elevation_diff = abs(pos1.alt - pos2.alt)
        distance = self.calculate_distance(pos1, pos2)
        
        if distance == 0:
            return 1.0
            
        # 地形影响因子：海拔差越大，影响越大
        terrain_effect = exp(-elevation_diff / (distance * 1000))  # 距离转换为米
        return max(0.1, terrain_effect)
    
    @staticmethod
    def calculate_distance(pos1: Position, pos2: Position) -> float:
        """计算两个位置之间的距离(km)"""
        R = 6371  # 地球半径(km)
        
        lat1_rad = radians(pos1.lat)
        lon1_rad = radians(pos1.lon)
        lat2_rad = radians(pos2.lat)
        lon2_rad = radians(pos2.lon)
        
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

class WeatherModel:
    """气象模型类"""
    def __init__(self):
        self.weather_conditions = {
            'clear': {'attenuation': 1.0, 'visibility': 1.0},
            'cloudy': {'attenuation': 0.9, 'visibility': 0.8},
            'rain': {'attenuation': 0.7, 'visibility': 0.5},
            'fog': {'attenuation': 0.6, 'visibility': 0.3},
            'storm': {'attenuation': 0.4, 'visibility': 0.2}
        }
    
    def get_weather_factor(self, weather_condition: str, distance: float) -> float:
        """根据气象条件和距离计算天气影响因子"""
        if weather_condition not in self.weather_conditions:
            return 1.0
            
        base_attenuation = self.weather_conditions[weather_condition]['attenuation']
        # 距离越远，天气影响越大
        distance_effect = exp(-distance / 100)  # 100km尺度
        weather_factor = base_attenuation + (1 - base_attenuation) * distance_effect
        return max(0.1, weather_factor)

class Battlefield:
    """战场环境类"""
    def __init__(self):
        self.missile_position = Position(35.0, 115.0, 1000)
        self.targets: Dict[str, Target] = {}
        self.jammers: Dict[str, Jammer] = {}
        self.terrain_model = TerrainModel()
        self.weather_model = WeatherModel()
        self.weather_condition = 'clear'
        self.start_time = datetime.now()
        
    def add_target(self, target: Target):
        """添加目标"""
        self.targets[target.target_id] = target
        
    def add_jammer(self, jammer: Jammer):
        """添加干扰机"""
        self.jammers[jammer.jammer_id] = jammer
        
    def get_closest_target(self, position: Position) -> Tuple[Optional[Target], float]:
        """获取最近的目标"""
        if not self.targets:
            return None, float('inf')
            
        closest_target = None
        min_distance = float('inf')
        
        for target in self.targets.values():
            distance = self.terrain_model.calculate_distance(position, target.position)
            if distance < min_distance:
                min_distance = distance
                closest_target = target
                
        return closest_target, min_distance
    
    def get_jamming_power(self, position: Position) -> float:
        """计算位置处的总干扰功率"""
        total_jamming = 0.0
        
        for jammer in self.jammers.values():
            distance = self.terrain_model.calculate_distance(position, jammer.position)
            jamming_effect = jammer.get_jamming_effectiveness(distance)
            total_jamming += jamming_effect
            
        return min(1.0, total_jamming)  # 限制在0-1之间
    
    def get_terrain_factor(self, pos1: Position, pos2: Position) -> float:
        """获取地形影响因子"""
        return self.terrain_model.get_terrain_factor(pos1, pos2)
    
    def get_weather_factor(self, distance: float) -> float:
        """获取天气影响因子"""
        return self.weather_model.get_weather_factor(self.weather_condition, distance)
    
    def update_missile_position(self, new_position: Position):
        """更新导弹位置"""
        self.missile_position = new_position

class SimulationEngine:
    """仿真引擎"""
    def __init__(self):
        self.battlefield = Battlefield()
        self.guidance_systems = {
            'passive': PassiveRadarSeeker(),
            'active': ActiveRadarSeeker(), 
            'composite': CompositeSeeker()
        }
        self.current_guidance_system = None
        self.simulation_time = 0
        self.is_running = False
        
    def initialize_battlefield(self, missile_pos: Position, targets: List[Target], jammers: List[Jammer]):
        """初始化战场"""
        self.battlefield.missile_position = missile_pos
        self.battlefield.targets = {t.target_id: t for t in targets}
        self.battlefield.jammers = {j.jammer_id: j for j in jammers}
        
    def set_guidance_system(self, system_type: str):
        """设置当前导引头系统"""
        if system_type in self.guidance_systems:
            self.current_guidance_system = self.guidance_systems[system_type]
        else:
            raise ValueError(f"Unknown guidance system: {system_type}")
            
    def run_simulation_step(self, time_step: float = 1.0) -> Dict:
        """运行仿真单步"""
        if not self.current_guidance_system:
            raise ValueError("Guidance system not set")
            
        # 获取最近目标
        target, distance = self.battlefield.get_closest_target(self.battlefield.missile_position)
        
        if not target:
            return {'performance': 0, 'target_distance': float('inf')}
        
        # 计算干扰功率
        jamming_power = self.battlefield.get_jamming_power(self.battlefield.missile_position)
        
        # 计算地形和天气影响
        terrain_factor = self.battlefield.get_terrain_factor(self.battlefield.missile_position, target.position)
        weather_factor = self.battlefield.get_weather_factor(distance)
        
        # 计算导引头性能
        performance = self.current_guidance_system.calculate_performance(
            distance, jamming_power, terrain_factor, weather_factor
        )
        
        # 记录轨迹
        self.current_guidance_system.record_trajectory(
            self.battlefield.missile_position, distance, performance
        )
        
        self.simulation_time += time_step
        
        return {
            'performance': performance,
            'target_distance': distance,
            'jamming_power': jamming_power,
            'terrain_factor': terrain_factor,
            'weather_factor': weather_factor,
            'target_id': target.target_id
        }

# 工具函数
def create_sample_battlefield() -> Battlefield:
    """创建示例战场"""
    battlefield = Battlefield()
    
    # 添加目标
    target1 = Target(
        target_id="tgt1",
        target_type=TargetType.AWACS,
        position=Position(36.0, 117.0, 8000),
        emission_power=0.9,
        rcs=50.0,
        velocity=250,
        heading=45
    )
    
    # 添加干扰机
    jammer1 = Jammer(
        jammer_id="jam1",
        position=Position(36.5, 116.5, 0),
        jamming_type=JammingType.NOISE,
        power=0.7,
        range=100.0,
        target_id="tgt1"
    )
    
    battlefield.add_target(target1)
    battlefield.add_jammer(jammer1)
    
    return battlefield

def save_simulation_data(simulation_engine: SimulationEngine, filename: str):
    """保存仿真数据"""
    data = {
        'battlefield': {
            'missile_position': {
                'lat': simulation_engine.battlefield.missile_position.lat,
                'lon': simulation_engine.battlefield.missile_position.lon,
                'alt': simulation_engine.battlefield.missile_position.alt
            },
            'weather_condition': simulation_engine.battlefield.weather_condition
        },
        'simulation_time': simulation_engine.simulation_time
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_simulation_data(filename: str) -> Dict:
    """加载仿真数据"""
    with open(filename, 'r') as f:
        return json.load(f)