"""
数据模型定义 - 使用Pydantic进行数据验证
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime

class RadarType(str, Enum):
    """雷达类型枚举"""
    PHASED_ARRAY = "phased_array"
    MECHANICAL_SCAN = "mechanical"
    MIMO = "mimo"
    PASSIVE = "passive"

class TargetType(str, Enum):
    """目标类型枚举"""
    FIGHTER = "fighter"
    BOMBER = "bomber"
    UAV = "uav"
    MISSILE = "missile"
    TRANSPORT = "transport"
    SHIP = "ship"
    VEHICLE = "vehicle"

class MotionMode(str, Enum):
    """运动模式枚举"""
    STRAIGHT = "straight"
    CIRCLE = "circle"
    RANDOM = "random"
    WAYPOINTS = "waypoints"

class CoordinationMode(str, Enum):
    """协同模式枚举"""
    TDM = "tdm"
    FDM = "fdm"
    SDM = "sdm"
    ADAPTIVE = "adaptive"

class FusionMethod(str, Enum):
    """融合方法枚举"""
    WEIGHTED_VOTING = "weighted_voting"
    DS_EVIDENCE = "ds_evidence"
    KALMAN_FILTER = "kalman_filter"
    NEURAL_NETWORK = "neural_network"

class Position(BaseModel):
    """位置模型"""
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    altitude: float = Field(default=0.0, ge=0, description="高度（米）")
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v < -180 or v > 180:
            raise ValueError('经度必须在-180到180之间')
        return v
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v < -90 or v > 90:
            raise ValueError('纬度必须在-90到90之间')
        return v

class RadarConfig(BaseModel):
    """雷达配置模型"""
    radar_id: str = Field(..., description="雷达ID")
    radar_name: str = Field(..., description="雷达名称")
    radar_type: RadarType = Field(default=RadarType.PHASED_ARRAY, description="雷达类型")
    
    # 位置信息
    position: Position = Field(..., description="雷达位置")
    
    # 发射机参数
    frequency_mhz: float = Field(default=3000.0, gt=0, description="中心频率（MHz）")
    bandwidth_mhz: float = Field(default=10.0, gt=0, description="带宽（MHz）")
    peak_power_kw: float = Field(default=500.0, gt=0, description="峰值功率（kW）")
    prf_hz: float = Field(default=1000.0, gt=0, description="脉冲重复频率（Hz）")
    pulse_width_us: float = Field(default=10.0, gt=0, description="脉冲宽度（μs）")
    
    # 天线参数
    antenna_gain_db: float = Field(default=30.0, description="天线增益（dB）")
    beamwidth_az_deg: float = Field(default=2.5, gt=0, description="方位波束宽度（度）")
    beamwidth_el_deg: float = Field(default=2.5, gt=0, description="俯仰波束宽度（度）")
    scan_sector_az: tuple = Field(default=(0, 360), description="方位扫描扇区（度）")
    scan_sector_el: tuple = Field(default=(-10, 10), description="俯仰扫描扇区（度）")
    
    # 处理参数
    cfar_type: str = Field(default="CA-CFAR", description="CFAR类型")
    false_alarm_rate: float = Field(default=1e-6, gt=0, lt=1, description="虚警概率")
    integration_pulses: int = Field(default=10, gt=0, description="累积脉冲数")
    
    # 性能参数
    range_km: float = Field(default=100.0, gt=0, description="探测距离（km）")
    range_resolution_m: float = Field(default=15.0, gt=0, description="距离分辨率（m）")
    azimuth_resolution_deg: float = Field(default=1.5, gt=0, description="方位分辨率（度）")
    
    # 状态参数
    status: str = Field(default="active", description="雷达状态")
    enabled: bool = Field(default=True, description="是否启用")
    
    class Config:
        schema_extra = {
            "example": {
                "radar_id": "radar_001",
                "radar_name": "主雷达",
                "radar_type": "phased_array",
                "position": {
                    "latitude": 39.9042,
                    "longitude": 116.4074,
                    "altitude": 0.0
                },
                "frequency_mhz": 3000.0,
                "bandwidth_mhz": 10.0,
                "peak_power_kw": 500.0,
                "range_km": 150.0
            }
        }

class TargetConfig(BaseModel):
    """目标配置模型"""
    target_id: str = Field(..., description="目标ID")
    target_name: str = Field(..., description="目标名称")
    target_type: TargetType = Field(default=TargetType.FIGHTER, description="目标类型")
    
    # 位置和运动参数
    position: Position = Field(..., description="初始位置")
    altitude_m: float = Field(default=10000.0, ge=0, description="高度（米）")
    speed_kts: float = Field(default=300.0, ge=0, description="速度（节）")
    heading_deg: float = Field(default=0.0, ge=0, lt=360, description="航向（度）")
    vertical_rate: float = Field(default=0.0, description="爬升率（m/s）")
    
    # 运动模式
    motion_mode: MotionMode = Field(default=MotionMode.STRAIGHT, description="运动模式")
    waypoints: Optional[List[Position]] = Field(default=None, description="航点列表")
    circle_radius_km: Optional[float] = Field(default=None, description="盘旋半径（km）")
    circle_direction: Optional[str] = Field(default="clockwise", description="盘旋方向")
    
    # 电磁特性
    rcs_m2: float = Field(default=1.0, gt=0, description="雷达散射截面（m²）")
    rcs_freq_dependency: str = Field(default="constant", description="RCS频率相关性")
    rcs_azimuth_variation_db: float = Field(default=10.0, ge=0, description="RCS方位变化（dB）")
    
    # 辐射特性
    emitter_types: List[str] = Field(default=["radar", "iff"], description="辐射源类型")
    radar_freq_min_mhz: Optional[float] = Field(default=None, description="雷达最小频率（MHz）")
    radar_freq_max_mhz: Optional[float] = Field(default=None, description="雷达最大频率（MHz）")
    radar_prf_hz: Optional[float] = Field(default=None, description="雷达PRF（Hz）")
    
    # 状态参数
    status: str = Field(default="active", description="目标状态")
    
    class Config:
        schema_extra = {
            "example": {
                "target_id": "target_001",
                "target_name": "目标1",
                "target_type": "fighter",
                "position": {
                    "latitude": 40.0,
                    "longitude": 117.0,
                    "altitude": 10000.0
                },
                "speed_kts": 300.0,
                "rcs_m2": 1.0
            }
        }

class SimulationConfig(BaseModel):
    """仿真配置模型"""
    simulation_id: str = Field(..., description="仿真ID")
    simulation_name: str = Field(..., description="仿真名称")
    
    # 时间参数
    time_step: float = Field(default=0.1, gt=0, description="时间步长（秒）")
    duration: float = Field(default=300.0, gt=0, description="仿真时长（秒）")
    real_time_factor: float = Field(default=1.0, gt=0, description="实时因子")
    
    # 环境参数
    weather: str = Field(default="clear", description="天气状况")
    visibility_km: float = Field(default=20.0, gt=0, description="能见度（km）")
    temperature_c: float = Field(default=15.0, description="温度（℃）")
    humidity_percent: float = Field(default=60.0, ge=0, le=100, description="湿度（%）")
    wind_speed_kts: float = Field(default=10.0, ge=0, description="风速（节）")
    wind_direction_deg: float = Field(default=0.0, ge=0, lt=360, description="风向（度）")
    
    # 性能参数
    simulation_speed: str = Field(default="normal", description="仿真速度")
    data_logging: bool = Field(default=True, description="是否记录数据")
    log_interval: float = Field(default=1.0, gt=0, description="记录间隔（秒）")
    max_memory_mb: int = Field(default=4096, gt=0, description="最大内存（MB）")
    parallel_processing: bool = Field(default=True, description="是否并行处理")
    num_threads: int = Field(default=4, gt=0, description="线程数")
    
    # 高级参数
    random_seed: Optional[int] = Field(default=None, description="随机种子")
    enable_interference: bool = Field(default=True, description="是否启用干扰")
    enable_multipath: bool = Field(default=False, description="是否启用多径效应")
    signal_attenuation_model: str = Field(default="free_space", description="信号衰减模型")
    atmospheric_model: str = Field(default="standard", description="大气模型")
    
    class Config:
        schema_extra = {
            "example": {
                "simulation_id": "sim_001",
                "simulation_name": "测试仿真",
                "duration": 300.0,
                "time_step": 0.1,
                "real_time_factor": 1.0
            }
        }

class SimulationRequest(BaseModel):
    """仿真请求模型"""
    simulation_name: str = Field(..., description="仿真名称")
    time_step: float = Field(default=0.1, description="时间步长")
    duration: float = Field(default=300.0, description="仿真时长")
    real_time_factor: float = Field(default=1.0, description="实时因子")
    
    # 雷达和目标配置
    radars: List[Dict[str, Any]] = Field(..., description="雷达配置列表")
    targets: List[Dict[str, Any]] = Field(..., description="目标配置列表")
    
    # 可选的环境和性能配置
    environment_config: Optional[Dict[str, Any]] = Field(default=None, description="环境配置")
    performance_config: Optional[Dict[str, Any]] = Field(default=None, description="性能配置")

class SimulationResponse(BaseModel):
    """仿真响应模型"""
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="仿真状态")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

class SimulationStatus(BaseModel):
    """仿真状态模型"""
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态")
    progress: float = Field(..., ge=0, le=1, description="进度")
    current_time: float = Field(..., ge=0, description="当前时间")
    message: Optional[str] = Field(default=None, description="状态消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="状态数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

class DetectionResult(BaseModel):
    """检测结果模型"""
    detection_id: str = Field(..., description="检测ID")
    radar_id: str = Field(..., description="雷达ID")
    target_id: str = Field(..., description="目标ID")
    timestamp: float = Field(..., description="时间戳")
    position: Position = Field(..., description="检测位置")
    snr_db: float = Field(..., description="信噪比（dB）")
    range_km: float = Field(..., description="距离（km）")
    azimuth_deg: float = Field(..., description="方位角（度）")
    elevation_deg: float = Field(..., description="俯仰角（度）")
    confidence: float = Field(..., ge=0, le=1, description="置信度")

class TrackResult(BaseModel):
    """航迹结果模型"""
    track_id: str = Field(..., description="航迹ID")
    target_id: str = Field(..., description="目标ID")
    positions: List[Position] = Field(..., description="位置序列")
    timestamps: List[float] = Field(..., description="时间序列")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    start_time: float = Field(..., description="起始时间")
    last_update: float = Field(..., description="最后更新时间")
    status: str = Field(..., description="航迹状态")

class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    # 检测性能
    detection_probability: float = Field(..., ge=0, le=1, description="检测概率")
    false_alarm_rate: float = Field(..., ge=0, le=1, description="虚警率")
    snr_threshold_db: float = Field(..., description="SNR阈值（dB）")
    
    # 跟踪性能
    track_continuity: float = Field(..., ge=0, le=1, description="航迹连续性")
    position_error_m: float = Field(..., ge=0, description="位置误差（m）")
    track_lifetime_s: float = Field(..., ge=0, description="航迹寿命（秒）")
    initiation_time_s: float = Field(..., ge=0, description="起始时间（秒）")
    
    # 系统性能
    system_load: float = Field(..., ge=0, le=1, description="系统负载")
    throughput: float = Field(..., ge=0, description="吞吐量")
    cpu_usage: float = Field(..., ge=0, le=1, description="CPU使用率")
    memory_usage: float = Field(..., ge=0, le=1, description="内存使用率")
    
    # 融合性能
    fusion_gain: float = Field(..., ge=1, description="融合增益")
    fusion_delay_s: float = Field(..., ge=0, description="融合延迟（秒）")
    fusion_consistency: float = Field(..., ge=0, le=1, description="融合一致性")
    
    class Config:
        schema_extra = {
            "example": {
                "detection_probability": 0.85,
                "false_alarm_rate": 1.2e-4,
                "track_continuity": 0.92,
                "position_error_m": 45.3,
                "system_load": 0.65
            }
        }

class AnalysisRequest(BaseModel):
    """分析请求模型"""
    data: Dict[str, Any] = Field(..., description="分析数据")
    analysis_type: str = Field(..., description="分析类型")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="分析参数")

class OptimizationRequest(BaseModel):
    """优化请求模型"""
    current_config: Dict[str, Any] = Field(..., description="当前配置")
    performance_data: Dict[str, Any] = Field(..., description="性能数据")
    optimization_goal: str = Field(..., description="优化目标")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="约束条件")