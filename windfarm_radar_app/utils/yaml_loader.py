"""
YAML场景配置文件加载器
用于加载和解析风电场评估场景的YAML配置文件
"""

import yaml
import streamlit as st
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import sys
import os

# 添加父目录到路径，以便导入config
sys.path.append(str(Path(__file__).parent.parent))

from config.config import (
    VALIDATION_RULES, TURBINE_MODELS, RADAR_TYPES, 
    COMMUNICATION_SYSTEMS, TARGET_RCS_DB, ANTENNA_TYPES,
    WindTurbine, RadarStation, CommunicationStation, Target, Scenario,
    validate_coordinates, get_band_frequency_range
)

class ScenarioYAMLLoader:
    """场景YAML文件加载器"""
    
    def __init__(self, yaml_path: Optional[Path] = None):
        """
        初始化加载器
        
        参数:
            yaml_path: YAML文件路径
        """
        self.yaml_path = yaml_path
        self.raw_data = None
        self.scenario = None
        self.validation_errors = []
        self.validation_warnings = []
    
    def load_yaml_file(self, yaml_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        加载YAML文件
        
        参数:
            yaml_path: YAML文件路径，如果为None则使用初始化路径
            
        返回:
            解析后的字典数据
        """
        if yaml_path is None:
            yaml_path = self.yaml_path
        
        if yaml_path is None:
            raise ValueError("未提供YAML文件路径")
        
        # 检查文件是否存在
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML文件不存在: {yaml_path}")
        
        # 检查文件扩展名
        if yaml_path.suffix.lower() not in ['.yaml', '.yml']:
            raise ValueError(f"文件格式错误，期望YAML文件: {yaml_path}")
        
        # 读取文件
        try:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                self.raw_data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML文件解析错误: {e}")
        except Exception as e:
            raise IOError(f"读取文件失败: {e}")
        
        return self.raw_data
    
    def validate_scenario_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证场景数据
        
        参数:
            data: 场景数据字典
            
        返回:
            (是否有效, 错误列表, 警告列表)
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # 检查必需字段
        required_sections = ['wind_turbines', 'radar_stations', 'communication_stations', 'targets']
        for section in required_sections:
            if section not in data:
                self.validation_errors.append(f"缺失必需字段: {section}")
        
        # 如果有错误，提前返回
        if self.validation_errors:
            return False, self.validation_errors, self.validation_warnings
        
        # 验证风机数据
        if 'wind_turbines' in data and data['wind_turbines']:
            self._validate_wind_turbines(data['wind_turbines'])
        
        # 验证雷达站数据
        if 'radar_stations' in data and data['radar_stations']:
            self._validate_radar_stations(data['radar_stations'])
        
        # 验证通信站数据
        if 'communication_stations' in data and data['communication_stations']:
            self._validate_communication_stations(data['communication_stations'])
        
        # 验证目标数据
        if 'targets' in data and data['targets']:
            self._validate_targets(data['targets'])
        
        # 检查是否有错误
        is_valid = len(self.validation_errors) == 0
        
        return is_valid, self.validation_errors, self.validation_warnings
    
    def _validate_wind_turbines(self, turbines_data: List[Dict[str, Any]]) -> None:
        """验证风机数据"""
        for i, turbine_data in enumerate(turbines_data):
            turbine_id = turbine_data.get('id', f'unknown_{i}')
            
            # 检查必需字段
            required_fields = ['model', 'position', 'height', 'rotor_diameter']
            for field in required_fields:
                if field not in turbine_data:
                    self.validation_errors.append(f"风机 {turbine_id}: 缺失必需字段 '{field}'")
            
            # 验证坐标
            if 'position' in turbine_data:
                pos = turbine_data['position']
                if not all(key in pos for key in ['lat', 'lon', 'alt']):
                    self.validation_errors.append(f"风机 {turbine_id}: 位置信息不完整，需要 'lat', 'lon', 'alt'")
                else:
                    if not validate_coordinates(pos['lat'], pos['lon'], pos['alt']):
                        self.validation_errors.append(f"风机 {turbine_id}: 坐标值超出有效范围")
            
            # 验证模型是否存在
            if 'model' in turbine_data:
                model = turbine_data['model']
                if model not in TURBINE_MODELS:
                    self.validation_warnings.append(f"风机 {turbine_id}: 未知风机型号 '{model}'，将使用默认参数")
            
            # 验证数值范围
            if 'height' in turbine_data:
                height = turbine_data['height']
                rules = VALIDATION_RULES['height']
                if not (rules['min'] <= height <= rules['max']):
                    self.validation_errors.append(f"风机 {turbine_id}: 高度 {height}m 超出有效范围 [{rules['min']}, {rules['max']}]")
            
            if 'rotor_diameter' in turbine_data:
                diameter = turbine_data['rotor_diameter']
                rules = VALIDATION_RULES['diameter']
                if not (rules['min'] <= diameter <= rules['max']):
                    self.validation_errors.append(f"风机 {turbine_id}: 转子直径 {diameter}m 超出有效范围 [{rules['min']}, {rules['max']}]")
    
    def _validate_radar_stations(self, radars_data: List[Dict[str, Any]]) -> None:
        """验证雷达站数据"""
        for i, radar_data in enumerate(radars_data):
            radar_id = radar_data.get('id', f'unknown_{i}')
            
            # 检查必需字段
            required_fields = ['type', 'frequency_band', 'position', 'peak_power', 'antenna_gain', 'beam_width']
            for field in required_fields:
                if field not in radar_data:
                    self.validation_errors.append(f"雷达站 {radar_id}: 缺失必需字段 '{field}'")
            
            # 验证坐标
            if 'position' in radar_data:
                pos = radar_data['position']
                if not all(key in pos for key in ['lat', 'lon', 'alt']):
                    self.validation_errors.append(f"雷达站 {radar_id}: 位置信息不完整，需要 'lat', 'lon', 'alt'")
                else:
                    if not validate_coordinates(pos['lat'], pos['lon'], pos['alt']):
                        self.validation_errors.append(f"雷达站 {radar_id}: 坐标值超出有效范围")
            
            # 验证雷达类型
            if 'type' in radar_data:
                radar_type = radar_data['type']
                if radar_type not in RADAR_TYPES:
                    self.validation_warnings.append(f"雷达站 {radar_id}: 未知雷达类型 '{radar_type}'，将使用默认参数")
            
            # 验证频率频段
            if 'frequency_band' in radar_data:
                freq_band = radar_data['frequency_band']
                try:
                    get_band_frequency_range(freq_band)
                except ValueError:
                    self.validation_errors.append(f"雷达站 {radar_id}: 未知频率频段 '{freq_band}'")
            
            # 验证数值范围
            if 'peak_power' in radar_data:
                power = radar_data['peak_power']
                rules = VALIDATION_RULES['power']
                if not (rules['min'] <= power <= rules['max']):
                    self.validation_errors.append(f"雷达站 {radar_id}: 峰值功率 {power}W 超出有效范围 [{rules['min']}, {rules['max']}]")
            
            if 'antenna_gain' in radar_data:
                gain = radar_data['antenna_gain']
                rules = VALIDATION_RULES['gain']
                if not (rules['min'] <= gain <= rules['max']):
                    self.validation_errors.append(f"雷达站 {radar_id}: 天线增益 {gain}dBi 超出有效范围 [{rules['min']}, {rules['max']}]")
            
            if 'beam_width' in radar_data:
                beam_width = radar_data['beam_width']
                if beam_width <= 0 or beam_width > 360:
                    self.validation_errors.append(f"雷达站 {radar_id}: 波束宽度 {beam_width}° 超出有效范围 (0, 360]")
    
    def _validate_communication_stations(self, comms_data: List[Dict[str, Any]]) -> None:
        """验证通信站数据"""
        for i, comm_data in enumerate(comms_data):
            comm_id = comm_data.get('id', f'unknown_{i}')
            
            # 检查必需字段
            required_fields = ['frequency', 'position', 'antenna_type', 'eirp', 'antenna_height']
            for field in required_fields:
                if field not in comm_data:
                    self.validation_errors.append(f"通信站 {comm_id}: 缺失必需字段 '{field}'")
            
            # 验证坐标
            if 'position' in comm_data:
                pos = comm_data['position']
                if not all(key in pos for key in ['lat', 'lon', 'alt']):
                    self.validation_errors.append(f"通信站 {comm_id}: 位置信息不完整，需要 'lat', 'lon', 'alt'")
                else:
                    if not validate_coordinates(pos['lat'], pos['lon'], pos['alt']):
                        self.validation_errors.append(f"通信站 {comm_id}: 坐标值超出有效范围")
            
            # 验证天线类型
            if 'antenna_type' in comm_data:
                antenna_type = comm_data['antenna_type']
                if antenna_type not in ANTENNA_TYPES:
                    self.validation_warnings.append(f"通信站 {comm_id}: 未知天线类型 '{antenna_type}'，将使用默认参数")
            
            # 验证频率
            if 'frequency' in comm_data:
                freq = comm_data['frequency']
                rules = VALIDATION_RULES['frequency']
                if not (rules['min'] <= freq <= rules['max']):
                    self.validation_errors.append(f"通信站 {comm_id}: 频率 {freq}GHz 超出有效范围 [{rules['min']}, {rules['max']}]")
            
            # 验证EIRP
            if 'eirp' in comm_data:
                eirp = comm_data['eirp']
                if eirp < 0 or eirp > 1000:
                    self.validation_warnings.append(f"通信站 {comm_id}: EIRP {eirp}dBm 可能超出合理范围")
            
            # 验证天线高度
            if 'antenna_height' in comm_data:
                height = comm_data['antenna_height']
                rules = VALIDATION_RULES['height']
                if not (rules['min'] <= height <= rules['max']):
                    self.validation_errors.append(f"通信站 {comm_id}: 天线高度 {height}m 超出有效范围 [{rules['min']}, {rules['max']}]")
    
    def _validate_targets(self, targets_data: List[Dict[str, Any]]) -> None:
        """验证目标数据"""
        for i, target_data in enumerate(targets_data):
            target_id = target_data.get('id', f'unknown_{i}')
            
            # 检查必需字段
            required_fields = ['type', 'rcs', 'position', 'speed', 'heading', 'altitude']
            for field in required_fields:
                if field not in target_data:
                    self.validation_errors.append(f"目标 {target_id}: 缺失必需字段 '{field}'")
            
            # 验证坐标
            if 'position' in target_data:
                pos = target_data['position']
                if not all(key in pos for key in ['lat', 'lon', 'alt']):
                    self.validation_errors.append(f"目标 {target_id}: 位置信息不完整，需要 'lat', 'lon', 'alt'")
                else:
                    if not validate_coordinates(pos['lat'], pos['lon'], pos['alt']):
                        self.validation_errors.append(f"目标 {target_id}: 坐标值超出有效范围")
            
            # 验证目标类型
            if 'type' in target_data:
                target_type = target_data['type']
                if target_type not in TARGET_RCS_DB:
                    self.validation_warnings.append(f"目标 {target_id}: 未知目标类型 '{target_type}'，将使用默认RCS值")
            
            # 验证RCS
            if 'rcs' in target_data:
                rcs = target_data['rcs']
                rules = VALIDATION_RULES['rcs']
                if not (rules['min'] <= rcs <= rules['max']):
                    self.validation_warnings.append(f"目标 {target_id}: RCS {rcs}m² 超出合理范围 [{rules['min']}, {rules['max']}]")
            
            # 验证速度
            if 'speed' in target_data:
                speed = target_data['speed']
                rules = VALIDATION_RULES['speed']
                if not (rules['min'] <= speed <= rules['max']):
                    self.validation_warnings.append(f"目标 {target_id}: 速度 {speed}m/s 超出合理范围 [{rules['min']}, {rules['max']}]")
            
            # 验证航向
            if 'heading' in target_data:
                heading = target_data['heading']
                if heading < 0 or heading > 360:
                    self.validation_errors.append(f"目标 {target_id}: 航向 {heading}° 超出有效范围 [0, 360]")
            
            # 验证高度
            if 'altitude' in target_data:
                alt = target_data['altitude']
                rules = VALIDATION_RULES['altitude']
                if not (rules['min'] <= alt <= rules['max']):
                    self.validation_errors.append(f"目标 {target_id}: 高度 {alt}m 超出有效范围 [{rules['min']}, {rules['max']}]")
    
    def create_scenario_objects(self, data: Dict[str, Any]) -> Scenario:
        """
        从验证后的数据创建场景对象
        
        参数:
            data: 验证后的场景数据
            
        返回:
            Scenario对象
        """
        # 创建风机对象列表
        wind_turbines = []
        for turbine_data in data.get('wind_turbines', []):
            # 获取风机型号的详细信息
            model_info = TURBINE_MODELS.get(turbine_data['model'], {})
            
            turbine = WindTurbine(
                id=turbine_data.get('id', 'unknown'),
                model=turbine_data['model'],
                position=turbine_data['position'],
                height=turbine_data['height'],
                rotor_diameter=turbine_data['rotor_diameter'],
                orientation=turbine_data.get('orientation', 0.0),
                operational=turbine_data.get('operational', True),
                metadata={
                    'model_info': model_info,
                    'custom_data': turbine_data.get('metadata', {})
                }
            )
            wind_turbines.append(turbine)
        
        # 创建雷达站对象列表
        radar_stations = []
        for radar_data in data.get('radar_stations', []):
            # 获取雷达类型的详细信息
            radar_type_info = RADAR_TYPES.get(radar_data['type'], {})
            
            radar = RadarStation(
                id=radar_data.get('id', 'unknown'),
                radar_type=radar_data['type'],
                frequency_band=radar_data['frequency_band'],
                position=radar_data['position'],
                peak_power=radar_data['peak_power'],
                antenna_gain=radar_data['antenna_gain'],
                beam_width=radar_data['beam_width'],
                antenna_height=radar_data.get('antenna_height', radar_data['position']['alt']),
                polarization=radar_data.get('polarization', 'horizontal'),
                scanning_mode=radar_data.get('scanning_mode', 'mechanical'),
                metadata={
                    'radar_type_info': radar_type_info,
                    'custom_data': radar_data.get('metadata', {})
                }
            )
            radar_stations.append(radar)
        
        # 创建通信站对象列表
        communication_stations = []
        for comm_data in data.get('communication_stations', []):
            # 获取天线类型的详细信息
            antenna_type_info = ANTENNA_TYPES.get(comm_data['antenna_type'], {})
            
            comm = CommunicationStation(
                id=comm_data.get('id', 'unknown'),
                frequency=comm_data['frequency'],
                position=comm_data['position'],
                antenna_type=comm_data['antenna_type'],
                eirp=comm_data['eirp'],
                antenna_height=comm_data['antenna_height'],
                service_type=comm_data.get('service_type', 'mobile'),
                metadata={
                    'antenna_type_info': antenna_type_info,
                    'custom_data': comm_data.get('metadata', {})
                }
            )
            communication_stations.append(comm)
        
        # 创建目标对象列表
        targets = []
        for target_data in data.get('targets', []):
            # 获取目标类型的详细信息
            target_type_info = TARGET_RCS_DB.get(target_data['type'], {})
            
            target = Target(
                id=target_data.get('id', 'unknown'),
                target_type=target_data['type'],
                rcs=target_data['rcs'],
                position=target_data['position'],
                speed=target_data['speed'],
                heading=target_data['heading'],
                altitude=target_data['altitude'],
                metadata={
                    'target_type_info': target_type_info,
                    'custom_data': target_data.get('metadata', {})
                }
            )
            targets.append(target)
        
        # 创建场景对象
        scenario = Scenario(
            name=data.get('name', '未命名场景'),
            description=data.get('description', ''),
            wind_turbines=wind_turbines,
            radar_stations=radar_stations,
            communication_stations=communication_stations,
            targets=targets,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            metadata=data.get('metadata', {})
        )
        
        return scenario
    
    def load_and_validate(self, yaml_path: Optional[Path] = None) -> Tuple[bool, Optional[Scenario], List[str], List[str]]:
        """
        加载并验证YAML文件
        
        参数:
            yaml_path: YAML文件路径
            
        返回:
            (是否成功, Scenario对象, 错误列表, 警告列表)
        """
        try:
            # 加载YAML文件
            data = self.load_yaml_file(yaml_path)
            
            # 验证数据
            is_valid, errors, warnings = self.validate_scenario_data(data)
            
            if not is_valid:
                return False, None, errors, warnings
            
            # 创建场景对象
            scenario = self.create_scenario_objects(data)
            
            return True, scenario, errors, warnings
            
        except Exception as e:
            self.validation_errors.append(f"加载场景文件时发生错误: {str(e)}")
            return False, None, self.validation_errors, self.validation_warnings

# 流式处理函数
def load_scenario_yaml(uploaded_file = None, file_path: Optional[Path] = None) -> Tuple[bool, Optional[Scenario], List[str], List[str]]:
    """
    加载场景YAML文件的流式处理函数
    
    参数:
        uploaded_file: Streamlit上传的文件对象
        file_path: 文件路径（二选一）
        
    返回:
        (是否成功, Scenario对象, 错误列表, 警告列表)
    """
    loader = ScenarioYAMLLoader()
    
    # 如果提供了上传文件
    if uploaded_file is not None:
        # 将上传的文件保存到临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)
        
        try:
            success, scenario, errors, warnings = loader.load_and_validate(tmp_path)
        finally:
            # 清理临时文件
            try:
                tmp_path.unlink()
            except:
                pass
        
        return success, scenario, errors, warnings
    
    # 如果提供了文件路径
    elif file_path is not None:
        return loader.load_and_validate(file_path)
    
    else:
        return False, None, ["未提供文件"], []

# 示例YAML生成函数
def generate_example_yaml() -> str:
    """
    生成示例YAML配置文件
    
    返回:
        示例YAML内容字符串
    """
    example_data = {
        "name": "示例风电场评估场景",
        "description": "这是一个示例场景配置文件，展示了完整的数据结构",
        "created_at": "2024-01-01 00:00:00",
        "updated_at": "2024-01-01 00:00:00",
        
        "wind_turbines": [
            {
                "id": "wt001",
                "model": "Vestas_V150",
                "position": {"lat": 40.123456, "lon": 116.123456, "alt": 50.0},
                "height": 150.0,
                "rotor_diameter": 150.0,
                "orientation": 45.0,
                "operational": True,
                "metadata": {
                    "installation_date": "2023-01-01",
                    "owner": "ABC风电场"
                }
            },
            {
                "id": "wt002",
                "model": "Siemens_Gamesa_SG145",
                "position": {"lat": 40.124000, "lon": 116.124500, "alt": 48.0},
                "height": 120.0,
                "rotor_diameter": 145.0,
                "orientation": 225.0,
                "operational": True
            }
        ],
        
        "radar_stations": [
            {
                "id": "radar1",
                "type": "气象雷达",
                "frequency_band": "S",
                "position": {"lat": 40.100000, "lon": 116.100000, "alt": 100.0},
                "peak_power": 1000000.0,
                "antenna_gain": 40.0,
                "beam_width": 1.0,
                "antenna_height": 30.0,
                "polarization": "horizontal",
                "scanning_mode": "mechanical",
                "metadata": {
                    "operator": "气象局",
                    "frequency": 3000.0
                }
            },
            {
                "id": "radar2",
                "type": "航管雷达",
                "frequency_band": "L",
                "position": {"lat": 40.150000, "lon": 116.150000, "alt": 80.0},
                "peak_power": 2000000.0,
                "antenna_gain": 35.0,
                "beam_width": 1.5,
                "antenna_height": 25.0
            }
        ],
        
        "communication_stations": [
            {
                "id": "comm1",
                "frequency": 1.8,  # GHz
                "position": {"lat": 40.200000, "lon": 116.200000, "alt": 30.0},
                "antenna_type": "sector",
                "eirp": 50.0,
                "antenna_height": 30.0,
                "service_type": "mobile"
            },
            {
                "id": "comm2",
                "frequency": 6.0,  # GHz
                "position": {"lat": 40.050000, "lon": 116.050000, "alt": 50.0},
                "antenna_type": "parabolic",
                "eirp": 40.0,
                "antenna_height": 50.0,
                "service_type": "microwave"
            }
        ],
        
        "targets": [
            {
                "id": "target1",
                "type": "民航飞机",
                "rcs": 10.0,
                "position": {"lat": 40.120000, "lon": 116.120000, "alt": 10000.0},
                "speed": 250.0,
                "heading": 90.0,
                "altitude": 10000.0,
                "metadata": {
                    "flight_number": "CA1234",
                    "aircraft_type": "B737"
                }
            },
            {
                "id": "target2",
                "type": "无人机",
                "rcs": 0.01,
                "position": {"lat": 40.130000, "lon": 116.130000, "alt": 500.0},
                "speed": 30.0,
                "heading": 180.0,
                "altitude": 500.0
            }
        ],
        
        "metadata": {
            "project_id": "WFRA-2024-001",
            "assessor": "风电雷达评估系统",
            "assessment_date": "2024-01-01"
        }
    }
    
    return yaml.dump(example_data, allow_unicode=True, sort_keys=False, indent=2)

# 保存示例文件
def save_example_yaml(file_path: Path) -> None:
    """
    保存示例YAML文件
    
    参数:
        file_path: 保存路径
    """
    yaml_content = generate_example_yaml()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)