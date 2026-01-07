"""
雷达数据模型模块
定义雷达系统的基础数据结构和业务逻辑
使用工厂模式创建不同类型的雷达实例
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod


class RadarBand(Enum):
    """雷达频段枚举"""
    UHF = "UHF"
    L = "L"
    S = "S"
    C = "C"
    X = "X"
    KU = "Ku"


class PlatformType(Enum):
    """平台类型枚举"""
    GROUND_MOBILE = "地面机动"
    AIRBORNE = "机载"
    SHIPBORNE = "舰载"
    FIXED = "固定阵地"


class MissionType(Enum):
    """任务类型枚举"""
    EARLY_WARNING = "远程预警"
    ANTI_STEALTH = "反隐身"
    AIRBORNE_AWACS = "空中预警"
    COMMAND_CONTROL = "指挥控制"
    AREA_DEFENSE = "区域防空"
    FIRE_CONTROL = "火控"
    MARITIME_SURVEILLANCE = "海事监视"


class WindowType(Enum):
    """窗函数类型枚举"""
    RECTANGULAR = "rectangular"     # 矩形窗
    HANNING = "hanning"             # 汉宁窗
    HAMMING = "hamming"             # 海明窗
    BLACKMAN = "blackman"           # 布莱克曼窗
    KAISER = "kaiser"               # 凯泽窗
    BARTLETT = "bartlett"           # 巴特利特窗
    
@dataclass
class SignalProcessing:
    """信号处理参数"""
    mti_filter: str
    doppler_channels: int
    max_tracking_targets: int
    processing_gain: float = 0.0
    # CFAR参数
    cfar_guard_cells = (2, 2)  # 2D保护单元
    cfar_training_cells = (10, 10)  # 2D训练单元
    cfar_range_guard_cells = 2  # 1D距离保护单元
    cfar_range_training_cells = 10  # 1D距离训练单元
    cfar_doppler_guard_cells = 2  # 1D多普勒保护单元
    cfar_doppler_training_cells = 10  # 1D多普勒训练单元
    cfar_pfa = 1e-6  # 虚警概率
    cfar_method = 'CA'  # CFAR方法: 'CA' 或 'OS'
    cfar_os_rank = 8  # OS-CFAR的排序秩 
@dataclass
class AntennaParameters:
    """天线参数"""
    gain_dbi: float
    azimuth_beamwidth: float  # 方位波束宽度(度)
    elevation_beamwidth: float  # 俯仰波束宽度(度)
    scan_rate: float = 60.0  # 扫描速率(度/秒)


@dataclass
class TransmitterParameters:
    """发射机参数"""
    frequency_hz: float = 9.4e9  # 工作频率(Hz)
    power_w: float =100.0  # 发射功率(W)
    pulses: int = 128  # 脉冲个数
    pulse_width_s: float = 1e6  # 脉冲宽度(秒)
    prf_hz: float = 1000.0  # 脉冲重复频率(Hz)
    bandwidth_hz: Optional[float] = 500e6  # 带宽(Hz)

@dataclass
class ReceiverParameters:
    """接收机参数"""
    noise_figure_db: float = 6.0  # 噪声系数(dB)
    sampling_rate_hz: float = 1e6  # 采样率(Hz)
    rf_gain_dbi: float = 35.0  # 天线增益(dBi)
    load_resistor: float = 50.0  # 负载电阻(Ω)
    baseband_gain_db: float = 40.0  # 基带增益(dB)

class RadarModel(ABC):
    """雷达模型抽象基类"""
    
    def __init__(self, radar_id: str, name: str, platform: PlatformType):
        self.radar_id = radar_id
        self.name = name
        self.platform = platform
        self.mission_types: List[MissionType] = []
        self.transmitter: TransmitterParameters = None # type: ignore
        self.receiver: ReceiverParameters = None # type: ignore
        self.antenna: Optional[AntennaParameters] = None
        self.signal_processing: Optional[SignalProcessing] = None
        self.theoretical_range_km: float = 0.0
        self.deployment_method: str = ""
    
    def basic_info(self) -> Dict[str, Any]:
        """获取雷达基本信息"""
        return {
            "radar_id": self.radar_id,
            "name": self.name,
            "platform": self.platform.value,
            "mission_types": [mt.value for mt in self.mission_types],
            "theoretical_range_km": self.theoretical_range_km,
            "deployment_method": self.deployment_method
        }
        
    @abstractmethod
    def calculate_performance(self) -> Dict[str, Any]:
        """计算雷达性能指标"""
        pass
    
    @abstractmethod
    def validate_parameters(self) -> bool:
        """验证雷达参数有效性"""
        pass
    
    def get_wavelength(self) -> float:
        """计算波长"""
        if self.transmitter:
            return 3e8 / self.transmitter.frequency_hz
        return 0.0
    
    def get_band(self) -> RadarBand:
        """获取频段"""
        freq_ghz = self.transmitter.frequency_hz / 1e9 if self.transmitter else 0
        
        if freq_ghz < 0.3:
            return RadarBand.UHF
        elif 0.3 <= freq_ghz < 1:
            return RadarBand.L
        elif 1 <= freq_ghz < 2:
            return RadarBand.S
        elif 2 <= freq_ghz < 4:
            return RadarBand.C
        elif 4 <= freq_ghz < 8:
            return RadarBand.X
        else:
            return RadarBand.KU


class EarlyWarningRadar(RadarModel):
    """早期预警雷达模型"""
    
    def __init__(self, radar_id: str, name: str):
        super().__init__(radar_id, name, PlatformType.GROUND_MOBILE)
        self.mission_types = [MissionType.EARLY_WARNING, MissionType.ANTI_STEALTH]
        self.update_rate_hz = 0.1  # 低更新率
    
    def calculate_performance(self) -> Dict[str, Any]:
        """计算预警雷达性能"""
        if not self.transmitter or not self.antenna:
            return {}
            
        wavelength = self.get_wavelength()
        # 简化雷达方程计算
        range_km = (self.transmitter.power_w * self.antenna.gain_dbi ** 2 * 
                   wavelength ** 2) ** 0.25 / 1000
        
        return {
            "max_range_km": range_km,
            "resolution_m": wavelength / 2,
            "update_rate_hz": self.update_rate_hz,
            "detection_probability": 0.9
        }
    
    def validate_parameters(self) -> bool:
        return (self.transmitter is not None and 
                self.antenna is not None and
                self.transmitter.frequency_hz < 1e9)  # UHF频段


class AirborneRadar(RadarModel):
    """机载预警雷达模型"""
    
    def __init__(self, radar_id: str, name: str):
        super().__init__(radar_id, name, PlatformType.AIRBORNE)
        self.mission_types = [MissionType.AIRBORNE_AWACS, MissionType.COMMAND_CONTROL]
        self.altitude_km = 10.0  # 典型飞行高度
    
    def calculate_performance(self) -> Dict[str, Any]:
        """计算机载雷达性能"""
        if not self.transmitter or not self.antenna:
            return {}
            
        # 考虑平台高度的雷达方程
        horizon_range = 4.12 * np.sqrt(self.altitude_km * 1000) / 1000  # 视距(km)
        wavelength = self.get_wavelength()
        
        return {
            "max_range_km": min(horizon_range, 350),  # 受视距限制
            "resolution_m": wavelength / 2,
            "update_rate_hz": 2.0,
            "altitude_advantage_km": self.altitude_km
        }
    
    def validate_parameters(self) -> bool:
        return (self.transmitter is not None and 
                self.antenna is not None and
                1e9 <= self.transmitter.frequency_hz < 2e9)  # L频段


class FireControlRadar(RadarModel):
    """火控雷达模型"""
    
    def __init__(self, radar_id: str, name: str):
        super().__init__(radar_id, name, PlatformType.GROUND_MOBILE)
        self.mission_types = [MissionType.FIRE_CONTROL]
        self.tracking_accuracy = 0.1  # 跟踪精度(米)
    
    def calculate_performance(self) -> Dict[str, Any]:
        """计算火控雷达性能"""
        if not self.transmitter or not self.antenna:
            return {}
            
        wavelength = self.get_wavelength()
        # 高精度要求
        range_km = (self.transmitter.power_w * self.antenna.gain_dbi ** 2 * 
                   wavelength ** 2) ** 0.25 / 1000
        
        return {
            "max_range_km": range_km,
            "resolution_m": wavelength / 10,  # 更高分辨率
            "update_rate_hz": 10.0,  # 高更新率
            "tracking_accuracy_m": self.tracking_accuracy
        }
    
    def validate_parameters(self) -> bool:
        return (self.transmitter is not None and 
                self.antenna is not None and
                self.transmitter.frequency_hz >= 4e9)  # C/X频段


class MaritimeRadar(RadarModel):
    """海事监视雷达模型"""
    
    def __init__(self, radar_id: str, name: str):
        super().__init__(radar_id, name, PlatformType.FIXED)
        self.mission_types = [MissionType.MARITIME_SURVEILLANCE]
        self.clutter_rejection = 40  # 杂波抑制(dB)
    
    def calculate_performance(self) -> Dict[str, Any]:
        """计算海事雷达性能"""
        if not self.transmitter or not self.antenna:
            return {}
            
        wavelength = self.get_wavelength()
        # 海事雷达考虑海杂波影响
        range_km = (self.transmitter.power_w * self.antenna.gain_dbi ** 2 * 
                   wavelength ** 2) ** 0.25 / 1000 * 0.8  # 海杂波衰减因子
        
        return {
            "max_range_km": range_km,
            "resolution_m": wavelength / 2,
            "update_rate_hz": 5.0,
            "clutter_rejection_db": self.clutter_rejection
        }
    
    def validate_parameters(self) -> bool:
        return (self.transmitter is not None and 
                self.antenna is not None)


class RadarFactory:
    """雷达工厂类 - 使用工厂模式创建雷达实例"""
    
    @staticmethod
    def create_radar(radar_type: str, radar_id: str, name: str) -> Optional[RadarModel]:
        """创建雷达实例"""
        radar_map = {
            "early_warning": EarlyWarningRadar,
            "airborne": AirborneRadar,
            "fire_control": FireControlRadar,
            "maritime": MaritimeRadar
        }
        
        radar_class = radar_map.get(radar_type)
        if radar_class:
            return radar_class(radar_id, name)
        return None
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Optional[RadarModel]:
        """从配置字典创建雷达"""
        radar_type = config.get("type")
        radar_id = config.get("radar_id")
        name = config.get("name")
        
        radar = RadarFactory.create_radar(radar_type, radar_id, name) # type: ignore
        if radar:
            # 设置发射机参数
            if "transmitter" in config:
                tx_config = config["transmitter"]
                radar.transmitter = TransmitterParameters(
                    frequency_hz=tx_config.get("frequency_hz"),
                    power_w=tx_config.get("power_w", 0),
                    pulse_width_s=tx_config.get("pulse_width_s"),
                    prf_hz=1.0 / tx_config.get("prp"), # 脉冲重复频率 
                    pulses=tx_config.get("pulses"),
                    bandwidth_hz=tx_config.get("bandwidth_hz")
                )
            if "receiver" in config:
                rx_config = config["receiver"]
                radar.receiver = ReceiverParameters(
                    noise_figure_db=rx_config.get("noise_figure_db", 6.0),
                    sampling_rate_hz=rx_config.get("sampling_rate_hz"),
                    rf_gain_dbi=rx_config.get("rf_gain_dbi",30.0),
                    load_resistor=rx_config.get("load_resistor",1000),
                    baseband_gain_db=rx_config.get("baseband_gain_db")                    
                )
            
            # 设置天线参数
            if "antenna" in config:
                ant_config = config["antenna"]
                radar.antenna = AntennaParameters(
                    gain_dbi=ant_config.get("gain_dbi", 0),
                    azimuth_beamwidth=ant_config.get("azimuth_beamwidth", 0),
                    elevation_beamwidth=ant_config.get("elevation_beamwidth", 0)
                )
            
            # 设置信号处理参数
            if "signal_processing" in config:
                sp_config = config["signal_processing"]
                radar.signal_processing = SignalProcessing(
                    mti_filter=sp_config.get("mti_filter", ""),
                    doppler_channels=sp_config.get("doppler_channels", 0),
                    max_tracking_targets=sp_config.get("max_tracking_targets", 0)
                )
            
            radar.theoretical_range_km = config.get("theoretical_range_km", 0)
            radar.deployment_method = config.get("deployment_method", "")
        
        return radar


# 预设雷达配置
PRESET_RADARS = {
    "JY-27B_UHF001": {
        "type": "early_warning",
        "radar_id": "JY-27B_UHF001",
        "name": "AA远程预警雷达-UHF波段（JY-27B）",
        "transmitter": {
            "frequency_hz": 0.3e9,
            "pulse_width_s": 200e-6,
            "power_w": 200,
            "prp": 0.0002,
            "pulses": 256,
            "bandwidth_hz": 200e6  # 带宽 
        },
        "receiver": {
            "noise_figure_db": 6.0,
            "sampling_rate_hz": 200e6,
            "rf_gain_dbi": 35.0,
            "baseband_gain_db": 35.0
        },
        "antenna": {
            "gain_dbi": 30.0,
            "azimuth_beamwidth": 12.0,
            "elevation_beamwidth": 24.0
        },
        "signal_processing": {
            "mti_filter": "3脉冲对消器",
            "doppler_channels": 256,
            "max_tracking_targets": 512
        },
        "theoretical_range_km": 224,
        "deployment_method": "TEL运输车"
    },
    "KJ-500_L001": {
        "type": "airborne", 
        "radar_id": "KJ-500_L001",
        "name": "AA预警机雷达-L波段（空警-500）",
        "transmitter": {
            "frequency_hz": 1.4e9,
            "pulse_width_s": 100e-6,
            "power_w": 700,
            "prp": 0.0002,
            "pulses": 256,
            "bandwidth_hz": 200e6  # 带宽             
        },
        "receiver": {
            "noise_figure_db": 6.0,
            "sampling_rate_hz": 200e6,
            "rf_gain_dbi": 41.0,
            "baseband_gain_db": 35.0
        },
        "antenna": {
            "gain_dbi": 38.0,
            "azimuth_beamwidth": 5,
            "elevation_beamwidth": 10
        },
        "signal_processing": {
            "mti_filter": "自适应MTI",
            "doppler_channels": 512,
            "max_tracking_targets": 1024
        },
        "theoretical_range_km": 55,
        "deployment_method": "空中机动"
    }
}


class RadarSystem:
    """雷达系统管理类"""
    
    def __init__(self):
        self.radars: Dict[str, RadarModel] = {}
        self.load_preset_radars()
    
    def load_preset_radars(self):
        """加载预设雷达配置"""
        for radar_id, config in PRESET_RADARS.items():
            radar = RadarFactory.create_from_config(config)
            if radar and radar.validate_parameters():
                self.radars[radar_id] = radar
    
    def add_radar(self, radar: RadarModel) -> bool:
        """添加雷达到系统"""
        if radar.validate_parameters():
            self.radars[radar.radar_id] = radar
            return True
        return False
    
    def get_radar(self, radar_id: str) -> Optional[RadarModel]:
        """获取指定雷达"""
        return self.radars.get(radar_id)
    
    def get_radars_by_band(self, band: RadarBand) -> List[RadarModel]:
        """按频段获取雷达列表"""
        return [radar for radar in self.radars.values() 
                if radar.get_band() == band]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取系统性能摘要"""
        total_radars = len(self.radars)
        bands = {}
        total_power = 0
        
        for radar in self.radars.values():
            band = radar.get_band().value
            bands[band] = bands.get(band, 0) + 1
            if radar.transmitter:
                total_power += radar.transmitter.power_w
        
        return {
            "total_radars": total_radars,
            "band_distribution": bands,
            "total_power_w": total_power,
            "frequency_coverage_hz": {
                "min": min([r.transmitter.frequency_hz for r in self.radars.values() 
                          if r.transmitter]),
                "max": max([r.transmitter.frequency_hz for r in self.radars.values() 
                          if r.transmitter])
            }
        }
