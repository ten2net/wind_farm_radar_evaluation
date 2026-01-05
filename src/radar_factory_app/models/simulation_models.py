"""
仿真数据模型模块
定义雷达仿真相关的参数、场景和结果数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import numpy as np
from datetime import datetime
from .radar_models import RadarModel, RadarBand


class TargetType(Enum):
    """目标类型枚举"""
    AIRCRAFT = "飞机"
    MISSILE = "导弹" 
    DRONE = "无人机"
    SHIP = "舰船"
    STEALTH_AIRCRAFT = "隐身飞机"
    BALLISTIC_MISSILE = "弹道导弹"
    GROUND_VEHICLE = "地面车辆"


class RCSModel(Enum):
    """RCS模型类型"""
    CONSTANT = "恒定RCS"
    SWERLING1 = "Swerling I"
    SWERLING2 = "Swerling II"
    SWERLING3 = "Swerling III"
    SWERLING4 = "Swerling IV"


@dataclass
class TargetParameters:
    """目标参数"""
    target_id: str
    target_type: TargetType
    position: np.ndarray  # [x, y, z] 坐标(m)
    velocity: np.ndarray  # [vx, vy, vz] 速度(m/s)
    rcs_sqm: float  # 雷达截面积(m²)
    rcs_model: RCSModel = RCSModel.CONSTANT
    
    def update_position(self, time_step: float):
        """更新目标位置"""
        self.position = self.position + self.velocity * time_step
    
    def get_distance(self, radar_position: np.ndarray) -> float:
        """计算与雷达的距离"""
        return np.linalg.norm(self.position - radar_position) # type: ignore
    
    def get_velocity_radial(self, radar_position: np.ndarray) -> float:
        """计算径向速度"""
        direction = (self.position - radar_position) / self.get_distance(radar_position)
        return np.dot(self.velocity, direction)
    def to_radarsimpy_ideal_target(self) -> Dict[str, Any]:
        """转换为radarsimpy目标对象的参数字典"""
        return {
            "location": self.position,
            "speed": self.velocity,
            "rcs": self.rcs_sqm,
            "phase": 0
        }
    def to_radarsimpy_mesh_target(self) -> Dict[str, Any]:
        """转换为radarsimpy目标对象的参数字典"""
        return {
            "location": self.position.tolist(),
            "speed": self.velocity.tolist(),
            "rcs": self.rcs_sqm,
            "rcs_model": self.rcs_model.name
        }


@dataclass
class SimulationScenario:
    """仿真场景"""
    scenario_id: str
    name: str
    description: str
    duration: float  # 仿真时长(秒)
    time_step: float  # 时间步长(秒)
    radar_positions: Dict[str, np.ndarray]  # 雷达ID到位置的映射
    targets: List[TargetParameters]
    environment: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证场景参数有效性"""
        return (self.duration > 0 and 
                self.time_step > 0 and 
                len(self.radar_positions) > 0 and
                len(self.targets) > 0)


@dataclass
class RadarDetection:
    """雷达检测结果"""
    timestamp: float
    radar_id: str
    target_id: str
    range: float  # 距离(m)
    azimuth: float  # 方位角(度)
    elevation: float  # 俯仰角(度)
    doppler: float  # 多普勒频率(Hz)
    snr: float  # 信噪比(dB)
    detection_confidence: float  # 检测置信度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "radar_id": self.radar_id,
            "target_id": self.target_id,
            "range_km": self.range / 1000,
            "azimuth_deg": self.azimuth,
            "elevation_deg": self.elevation,
            "doppler_hz": self.doppler,
            "snr_db": self.snr,
            "confidence": self.detection_confidence
        }


@dataclass
class SimulationParameters:
    """仿真参数配置"""
    # 基本参数
    simulation_id: str
    scenario: SimulationScenario
    radars: List[RadarModel]
    
    # 信号处理参数
    noise_temperature: float = 290.0  # 噪声温度(K)
    system_losses: float = 3.0  # 系统损耗(dB)
    detection_threshold: float = 12.0  # 检测门限(dB)
    false_alarm_prob: float = 1e-6  # 虚警概率
    
    # 杂波参数
    clutter_enabled: bool = False
    clutter_type: str = "ground"  # ground, sea, weather
    clutter_rcs: float = 0.1  # 杂波RCS(m²/m²)
    
    # 传播效应
    atmospheric_loss: bool = True
    rain_loss: bool = False
    rain_rate: float = 0.0  # 降雨率(mm/h)
    
    def calculate_noise_power(self, bandwidth: float) -> float:
        """计算噪声功率"""
        # P_noise = k * T * B
        boltzmann_constant = 1.38e-23
        return boltzmann_constant * self.noise_temperature * bandwidth


@dataclass
class SimulationResults:
    """仿真结果容器"""
    parameters: SimulationParameters
    detections: List[RadarDetection] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def add_detection(self, detection: RadarDetection):
        """添加检测结果"""
        self.detections.append(detection)
    
    def calculate_metrics(self):
        """计算仿真性能指标"""
        if not self.detections:
            return
            
        # 按雷达分组检测
        radar_detections = {}
        for detection in self.detections:
            if detection.radar_id not in radar_detections:
                radar_detections[detection.radar_id] = []
            radar_detections[detection.radar_id].append(detection)
        
        # 计算各雷达性能指标
        radar_metrics = {}
        for radar_id, dets in radar_detections.items():
            snr_values = [d.snr for d in dets]
            ranges = [d.range for d in dets]
            
            radar_metrics[radar_id] = {
                "detection_count": len(dets),
                "avg_snr_db": np.mean(snr_values) if snr_values else 0,
                "max_range_km": max(ranges) / 1000 if ranges else 0,
                "min_range_km": min(ranges) / 1000 if ranges else 0,
                "detection_consistency": len(set([d.target_id for d in dets]))
            }
        
        # 总体指标
        total_detections = len(self.detections)
        unique_targets = len(set([d.target_id for d in self.detections]))
        
        self.metrics = {
            "total_detections": total_detections,
            "unique_targets_detected": unique_targets,
            "simulation_duration": self.parameters.scenario.duration,
            "detection_rate": total_detections / self.parameters.scenario.duration,
            "radar_performance": radar_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_detection_history(self, target_id: str) -> List[RadarDetection]:
        """获取指定目标的检测历史"""
        return [d for d in self.detections if d.target_id == target_id]
    
    def get_radar_detections(self, radar_id: str) -> List[RadarDetection]:
        """获取指定雷达的检测结果"""
        return [d for d in self.detections if d.radar_id == radar_id]


@dataclass
class PerformanceMetrics:
    """性能指标计算器"""
    
    @staticmethod
    def calculate_probability_detection(snr: float, pfa: float) -> float:
        """计算检测概率（基于SNR和虚警概率）"""
        # 简化检测概率计算（实际应使用更复杂的检测理论）
        if snr < 10:
            return 0.1
        elif snr < 15:
            return 0.5
        else:
            return 0.9
    
    @staticmethod
    def calculate_range_resolution(bandwidth: float) -> float:
        """计算距离分辨率"""
        # ΔR = c / (2B)
        return 3e8 / (2 * bandwidth)
    
    @staticmethod
    def calculate_doppler_resolution(integration_time: float) -> float:
        """计算多普勒分辨率"""
        # Δf = 1 / T
        return 1.0 / integration_time
    
    @staticmethod
    def calculate_radar_range(radar: RadarModel, target_rcs: float, 
                            snr_min: float, losses: float) -> float:
        """计算雷达方程最大作用距离"""
        if not radar.transmitter or not radar.antenna:
            return 0.0
            
        # 雷达方程: R_max = [Pt * G^2 * λ^2 * σ / ((4π)^3 * kT * B * F * L * SNR_min)]^(1/4)
        pt = radar.transmitter.power_w
        g = 10**(radar.antenna.gain_dbi / 10)  # 转换为线性值
        wavelength = radar.get_wavelength()
        sigma = target_rcs
        
        # 简化计算（实际需要更多参数）
        numerator = pt * g**2 * wavelength**2 * sigma
        denominator = (4 * np.pi)**3 * losses * (10**(snr_min/10))
        
        return (numerator / denominator) ** 0.25


class SimulationRecorder:
    """仿真记录器 - 使用观察者模式记录仿真过程"""
    
    def __init__(self):
        self.detection_history: List[RadarDetection] = []
        self.performance_log: List[Dict[str, Any]] = []
        self.callbacks = []
    
    def add_callback(self, callback):
        """添加回调函数"""
        self.callbacks.append(callback)
    
    def record_detection(self, detection: RadarDetection):
        """记录检测事件"""
        self.detection_history.append(detection)
        
        # 通知观察者
        for callback in self.callbacks:
            callback(detection)
    
    def record_performance(self, metrics: Dict[str, Any]):
        """记录性能指标"""
        self.performance_log.append({
            "timestamp": datetime.now(),
            "metrics": metrics
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.detection_history:
            return {}
            
        snr_values = [d.snr for d in self.detection_history]
        ranges = [d.range for d in self.detection_history]
        
        return {
            "total_detections": len(self.detection_history),
            "avg_snr_db": np.mean(snr_values),
            "max_snr_db": max(snr_values) if snr_values else 0,
            "min_snr_db": min(snr_values) if snr_values else 0,
            "max_range_km": max(ranges) / 1000 if ranges else 0,
            "time_span": self.detection_history[-1].timestamp - self.detection_history[0].timestamp 
                         if len(self.detection_history) > 1 else 0
        }


# 预设仿真场景
PRESET_SCENARIOS = {
    "air_defense": SimulationScenario(
        scenario_id="air_defense_001",
        name="区域防空仿真",
        description="多雷达协同防空作战场景",
        duration=300.0,
        time_step=0.1,
        radar_positions={
            "JY-27B_UHF001": np.array([0, 0, 0]),
            "KJ-500_L001": np.array([50e3, 0, 10e3]),
            "346B_S001": np.array([100e3, 0, 0])
        },
        targets=[
            TargetParameters(
                target_id="target_001",
                target_type=TargetType.AIRCRAFT,
                position=np.array([200e3, 50e3, 10e3]),
                velocity=np.array([-300, 0, 0]),
                rcs_sqm=5.0,
                rcs_model=RCSModel.SWERLING1
            ),
            TargetParameters(
                target_id="target_002", 
                target_type=TargetType.MISSILE,
                position=np.array([150e3, -30e3, 5e3]),
                velocity=np.array([-800, 50, 0]),
                rcs_sqm=0.1,
                rcs_model=RCSModel.SWERLING3
            )
        ],
        environment={"weather": "clear", "terrain": "flat"}
    ),
    
    "maritime_surveillance": SimulationScenario(
        scenario_id="maritime_001", 
        name="海上监视仿真",
        description="海上目标探测与跟踪场景",
        duration=600.0,
        time_step=1.0,
        radar_positions={
            "MSR-SLR001": np.array([0, 0, 100]),
            "MSR-P001": np.array([5e3, 0, 100]),
            "MSR-KU001": np.array([10e3, 0, 50])
        },
        targets=[
            TargetParameters(
                target_id="ship_001",
                target_type=TargetType.SHIP,
                position=np.array([30e3, 10e3, 0]),
                velocity=np.array([0, 10, 0]),
                rcs_sqm=1000.0,
                rcs_model=RCSModel.CONSTANT
            )
        ],
        environment={"weather": "rain", "sea_state": 3}
    )
}