# radar_station_manager.py
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import uuid
import json
import os

@dataclass
class RadarParameters:
    """雷达参数类（保持原有）"""
    # 发射机参数
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

@dataclass
class Location:
    """部署位置类"""
    latitude: float  # 纬度
    longitude: float  # 经度
    altitude: float  # 高度 (米)
    coordinate_type: str = "WGS84"  # 坐标类型
    mobility: str = "固定"  # 固定/陆地移动/空中平台/海上平台
    speed: float = 0.0  # 移动速度 (m/s)
    heading: float = 0.0  # 移动方向 (度)

@dataclass
class BasicInfo:
    """雷达基本信息"""
    name: str
    radar_type: str
    country: str
    unit: str = ""
    deployment_time: str = ""
    status: str = "在线"  # 在线/离线/维修
    threat_level: str = "中"  # 低/中/高/极高
    priority: int = 3

@dataclass
class Capability:
    """作战能力"""
    detection_range_km: float
    track_targets: int
    update_rate_hz: float
    multi_target: bool = True
    countermeasures: List[str] = field(default_factory=list)
    ecm_level: str = "中"  # 电子对抗等级

@dataclass
class Connectivity:
    """网络连接性"""
    datalink: str = ""
    comm_band: str = ""
    network_node: str = ""
    co_units: List[str] = field(default_factory=list)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    range_resolution_m: float
    max_unambiguous_range_m: float
    velocity_resolution_mps: float
    max_unambiguous_velocity_mps: float
    snr_db: float

@dataclass
class RadarStation:
    """雷达台站类"""
    station_id: str
    basic_info: BasicInfo
    location: Location
    radar_params: RadarParameters
    performance: PerformanceMetrics
    capability: Capability
    connectivity: Connectivity
    created_time: str = ""
    last_updated: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'station_id': self.station_id,
            'basic_info': asdict(self.basic_info),
            'location': asdict(self.location),
            'radar_params': asdict(self.radar_params),
            'performance': asdict(self.performance),
            'capability': asdict(self.capability),
            'connectivity': asdict(self.connectivity),
            'created_time': self.created_time,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RadarStation':
        """从字典创建实例"""
        return cls(
            station_id=data['station_id'],
            basic_info=BasicInfo(**data['basic_info']),
            location=Location(**data['location']),
            radar_params=RadarParameters(**data['radar_params']),
            performance=PerformanceMetrics(**data['performance']),
            capability=Capability(**data['capability']),
            connectivity=Connectivity(**data['connectivity']),
            created_time=data.get('created_time', ''),
            last_updated=data.get('last_updated', '')
        )

@dataclass
class EWScenario:
    """电子战想定"""
    scenario_id: str
    name: str
    time: str
    duration_min: int
    participants: Dict[str, List[str]]  # 红方/蓝方
    description: str = ""
    scenario_file: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'scenario_id': self.scenario_id,
            'name': self.name,
            'time': self.time,
            'duration_min': self.duration_min,
            'participants': self.participants,
            'description': self.description,
            'scenario_file': self.scenario_file
        }

class RadarStationDatabase:
    """雷达台站数据库管理器"""
    
    def __init__(self, db_file: str = "radar_station_database.yaml"):
        self.db_file = db_file
        self.database: Dict[str, Any] = {
            '版本': "2.0",
            '创建时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '最后更新时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '雷达台站': {},
            '作战区域': {},
            '电磁对抗关系': {},
            '电子战单元': {},
            '场景想定': {}
        }
        
    def load_database(self) -> bool:
        """加载数据库"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.database = yaml.safe_load(f)
                return True
            else:
                print(f"数据库文件{self.db_file}不存在")
        except Exception as e:
            print(f"加载数据库失败: {e}")
        return False
    
    def save_database(self) -> bool:
        """保存数据库"""
        try:
            self.database['最后更新时间'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.db_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.database, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"保存数据库失败: {e}")
        return False
    
    def add_radar_station(self, station: RadarStation) -> bool:
        """添加雷达台站"""
        station_id = station.station_id
        station_dict = station.to_dict()
        
        # 转换为YAML友好格式
        yaml_station = {
            '基本信息': station_dict['basic_info'],
            '部署位置': station_dict['location'],
            '雷达参数': {
                '发射机': {
                    '载波频率_Hz': station_dict['radar_params']['frequency_hz'],
                    '带宽_Hz': station_dict['radar_params']['bandwidth_hz'],
                    '脉冲重复频率_Hz': station_dict['radar_params']['prf_hz'],
                    '脉冲宽度_s': station_dict['radar_params']['pulse_width_s'],
                    '脉冲数': station_dict['radar_params']['pulses'],
                    '峰值功率_W': station_dict['radar_params']['peak_power_w']
                },
                '天线': {
                    '增益_dB': station_dict['radar_params']['antenna_gain_db'],
                    '损耗_dB': station_dict['radar_params']['antenna_loss_db'],
                    '波束宽度_deg': station_dict['radar_params']['beamwidth_deg'],
                    '孔径_m2': station_dict['radar_params']['aperture_m2']
                },
                '接收机': {
                    '噪声系数_dB': station_dict['radar_params']['noise_figure_db'],
                    '系统损耗_dB': station_dict['radar_params']['system_loss_db'],
                    '采样率_Hz': station_dict['radar_params']['sampling_rate_hz'],
                    'ADC位数': station_dict['radar_params']['adc_bits'],
                    '基带增益_dB': station_dict['radar_params']['baseband_gain_db'],
                    '负载电阻_Ω': station_dict['radar_params']['load_resistance_ohm']
                },
                '目标': {
                    '雷达截面积_m2': station_dict['radar_params']['target_rcs_m2'],
                    '距离_m': station_dict['radar_params']['target_range_m']
                }
            },
            '性能指标': station_dict['performance'],
            '作战能力': station_dict['capability'],
            '连接性': station_dict['connectivity']
        }
        
        self.database['雷达台站'][station_id] = yaml_station
        return self.save_database()
    
    def get_radar_station(self, station_id: str) -> Optional[Dict]:
        """获取雷达台站"""
        return self.database.get('雷达台站', {}).get(station_id)
    
    def delete_radar_station(self, station_id: str) -> bool:
        """删除雷达台站"""
        if station_id in self.database.get('雷达台站', {}):
            del self.database['雷达台站'][station_id]
            return self.save_database()
        return False
    
    def get_all_stations(self) -> Dict:
        """获取所有雷达台站"""
        return self.database.get('雷达台站', {})
    
    def get_stations_by_country(self, country: str) -> List[Dict]:
        """按国家筛选雷达台站"""
        stations = []
        for station_id, station in self.database.get('雷达台站', {}).items():
            if station.get('基本信息', {}).get('国家') == country:
                stations.append({'id': station_id, **station})
        return stations
    
    def get_stations_by_type(self, radar_type: str) -> List[Dict]:
        """按类型筛选雷达台站"""
        stations = []
        for station_id, station in self.database.get('雷达台站', {}).items():
            if station.get('基本信息', {}).get('类型') == radar_type:
                stations.append({'id': station_id, **station})
        return stations
    
    def get_stations_in_area(self, lat: float, lon: float, radius_km: float) -> List[Dict]:
        """获取指定区域内的雷达台站"""
        import math
        stations = []
        
        for station_id, station in self.database.get('雷达台站', {}).items():
            location = station.get('部署位置', {})
            station_lat = location.get('纬度', 0)
            station_lon = location.get('经度', 0)
            
            # 计算距离（简化球面距离）
            lat_diff = abs(station_lat - lat) * 111.32  # 1度纬度约111.32km
            lon_diff = abs(station_lon - lon) * 111.32 * math.cos(math.radians(lat))
            distance = math.sqrt(lat_diff**2 + lon_diff**2)
            
            if distance <= radius_km:
                stations.append({
                    'id': station_id,
                    'station': station,
                    'distance_km': distance
                })
        
        return stations
    
    def add_ew_scenario(self, scenario: EWScenario) -> bool:
        """添加电子战想定"""
        self.database['场景想定'][scenario.scenario_id] = scenario.to_dict()
        return self.save_database()
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """获取想定"""
        return self.database.get('场景想定', {}).get(scenario_id)
    
    def simulate_engagement(self, red_radars: List[str], blue_radars: List[str], 
                           ew_units: List[str] = None) -> Dict:
        """模拟对抗交战"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'red_radars': red_radars,
            'blue_radars': blue_radars,
            'ew_units': ew_units or [],
            'engagement_result': {}
        }
        
        # 这里可以实现更复杂的交战逻辑
        # 简化的对抗分析
        red_power = 0
        blue_power = 0
        
        for radar_id in red_radars:
            station = self.get_radar_station(radar_id)
            if station:
                # 使用雷达功率作为实力衡量
                power = station.get('雷达参数', {}).get('发射机', {}).get('峰值功率_W', 0)
                red_power += power
        
        for radar_id in blue_radars:
            station = self.get_radar_station(radar_id)
            if station:
                power = station.get('雷达参数', {}).get('发射机', {}).get('峰值功率_W', 0)
                blue_power += power
        
        if red_power > blue_power * 1.5:
            winner = "红方"
        elif blue_power > red_power * 1.5:
            winner = "蓝方"
        else:
            winner = "僵持"
        
        result['engagement_result'] = {
            'red_total_power': red_power,
            'blue_total_power': blue_power,
            'winner': winner,
            'analysis': f"红方总功率: {red_power/1000:.1f}kW, 蓝方总功率: {blue_power/1000:.1f}kW"
        }
        
        return result
    
    def export_to_simulation(self, scenario_id: str, output_file: str = None) -> bool:
        """导出为仿真配置文件"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False
        
        simulation_config = {
            'simulation': {
                'scenario_id': scenario_id,
                'scenario_name': scenario.get('name'),
                'simulation_time': scenario.get('time'),
                'duration_min': scenario.get('duration_min')
            },
            'participants': scenario.get('participants', {}),
            'radar_stations': {},
            'engagement_rules': {
                'detection_range_multiplier': 1.0,
                'jammer_effectiveness': 0.7,
                'environment_loss_db': 5.0
            }
        }
        
        # 添加所有参与的雷达
        all_radars = []
        for side, radars in scenario.get('participants', {}).items():
            all_radars.extend(radars)
        
        for radar_id in all_radars:
            station = self.get_radar_station(radar_id)
            if station:
                simulation_config['radar_stations'][radar_id] = station
        
        if not output_file:
            output_file = f"simulation_{scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(simulation_config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"导出仿真配置失败: {e}")
            return False