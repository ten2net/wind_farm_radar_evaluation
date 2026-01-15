"""
直接YAML验证器 - 基于实际文件结构而非JSON Schema
"""

import yaml
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import re
from datetime import datetime

class YAMLConfigValidator:
    """直接YAML配置验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_scenario(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        直接验证场景配置
        
        参数:
            config_data: 配置数据字典
            
        返回:
            (是否有效, 错误信息列表)
        """
        self.errors = []
        self.warnings = []
        
        try:
            # 1. 验证顶级结构
            self._validate_top_level_structure(config_data)
            
            # 2. 验证必填字段
            self._validate_required_fields(config_data)
            
            # 3. 验证数据类型
            self._validate_data_types(config_data)
            
            # 4. 验证具体内容
            self._validate_wind_turbines(config_data)
            self._validate_radar_stations(config_data)
            self._validate_communication_stations(config_data)
            self._validate_targets(config_data)
            self._validate_metadata(config_data)
            
            # 5. 验证业务逻辑
            self._validate_business_rules(config_data)
            
            return len(self.errors) == 0, self.errors
            
        except Exception as e:
            self.errors.append(f"验证过程中发生错误: {str(e)}")
            return False, self.errors
    
    def _validate_top_level_structure(self, config_data: Dict[str, Any]) -> None:
        """验证顶级结构"""
        if not isinstance(config_data, dict):
            self.errors.append("配置文件必须是字典格式")
            return
        
        expected_sections = ['name', 'description', 'metadata', 'wind_turbines', 
                           'radar_stations', 'communication_stations', 'targets']
        
        for section in expected_sections:
            if section not in config_data:
                self.warnings.append(f"缺少可选部分: {section}")
    
    def _validate_required_fields(self, config_data: Dict[str, Any]) -> None:
        """验证必填字段"""
        required_fields = ['name', 'description']
        
        for field in required_fields:
            if field not in config_data:
                self.errors.append(f"缺少必填字段: {field}")
            elif not config_data[field]:
                self.errors.append(f"字段 {field} 不能为空")
    
    def _validate_data_types(self, config_data: Dict[str, Any]) -> None:
        """验证数据类型"""
        type_checks = [
            ('name', str, "字符串"),
            ('description', str, "字符串"),
            ('metadata', dict, "字典"),
            ('wind_turbines', list, "数组"),
            ('radar_stations', list, "数组"),
            ('communication_stations', list, "数组"),
            ('targets', list, "数组")
        ]
        
        for field, expected_type, type_name in type_checks:
            if field in config_data and not isinstance(config_data[field], expected_type):
                self.errors.append(f"字段 {field} 必须是{type_name}类型")
    
    def _validate_wind_turbines(self, config_data: Dict[str, Any]) -> None:
        """验证风机配置"""
        if 'wind_turbines' not in config_data:
            return
            
        turbines = config_data['wind_turbines']
        if not isinstance(turbines, list):
            self.errors.append("wind_turbines 必须是数组")
            return
        
        required_turbine_fields = ['id', 'model', 'position']
        
        for i, turbine in enumerate(turbines):
            if not isinstance(turbine, dict):
                self.errors.append(f"风机 #{i+1} 必须是字典格式")
                continue
            
            # 检查必填字段
            for field in required_turbine_fields:
                if field not in turbine:
                    self.errors.append(f"风机 #{i+1} 缺少必填字段: {field}")
            
            # 验证ID格式
            if 'id' in turbine:
                if not re.match(r'^[A-Za-z0-9_-]+$', str(turbine['id'])):
                    self.errors.append(f"风机 #{i+1} ID格式无效: {turbine['id']}")
            
            # 验证位置
            if 'position' in turbine:
                self._validate_position(turbine['position'], f"风机 #{turbine.get('id', i+1)}")
            
            # 验证数值范围
            if 'height' in turbine:
                height = turbine['height']
                if not (10 <= height <= 300):
                    self.warnings.append(f"风机 #{i+1} 高度 {height}m 可能不典型")
            
            if 'rotor_diameter' in turbine:
                diameter = turbine['rotor_diameter']
                if not (10 <= diameter <= 200):
                    self.warnings.append(f"风机 #{i+1} 转子直径 {diameter}m 可能不典型")
    
    def _validate_radar_stations(self, config_data: Dict[str, Any]) -> None:
        """验证雷达站配置"""
        if 'radar_stations' not in config_data:
            return
            
        radars = config_data['radar_stations']
        if not isinstance(radars, list):
            self.errors.append("radar_stations 必须是数组")
            return
        
        required_radar_fields = ['id', 'type', 'position']
        
        for i, radar in enumerate(radars):
            if not isinstance(radar, dict):
                self.errors.append(f"雷达站 #{i+1} 必须是字典格式")
                continue
            
            for field in required_radar_fields:
                if field not in radar:
                    self.errors.append(f"雷达站 #{i+1} 缺少必填字段: {field}")
            
            # 验证ID格式
            if 'id' in radar:
                if not re.match(r'^[A-Za-z0-9_-]+$', str(radar['id'])):
                    self.errors.append(f"雷达站 #{i+1} ID格式无效: {radar['id']}")
            
            # 验证位置
            if 'position' in radar:
                self._validate_position(radar['position'], f"雷达站 #{radar.get('id', i+1)}")
            
            # 验证频段
            valid_bands = ['S', 'X', 'C', 'L', 'Ku', 'Ka']
            if 'frequency_band' in radar and radar['frequency_band'] not in valid_bands:
                self.warnings.append(f"雷达站 #{i+1} 频段 {radar['frequency_band']} 不常见")
            
            # 验证功率
            if 'peak_power' in radar:
                power = radar['peak_power']
                if power < 1000:
                    self.warnings.append(f"雷达站 #{i+1} 峰值功率 {power}W 可能过低")
    
    def _validate_communication_stations(self, config_data: Dict[str, Any]) -> None:
        """验证通信站配置"""
        if 'communication_stations' not in config_data:
            return
            
        comms = config_data['communication_stations']
        if not isinstance(comms, list):
            self.errors.append("communication_stations 必须是数组")
            return
        
        required_comm_fields = ['id', 'service_type', 'position']
        
        for i, comm in enumerate(comms):
            if not isinstance(comm, dict):
                self.errors.append(f"通信站 #{i+1} 必须是字典格式")
                continue
            
            for field in required_comm_fields:
                if field not in comm:
                    self.errors.append(f"通信站 #{i+1} 缺少必填字段: {field}")
            
            # 验证ID格式
            if 'id' in comm:
                if not re.match(r'^[A-Za-z0-9_-]+$', str(comm['id'])):
                    self.errors.append(f"通信站 #{i+1} ID格式无效: {comm['id']}")
            
            # 验证位置
            if 'position' in comm:
                self._validate_position(comm['position'], f"通信站 #{comm.get('id', i+1)}")
    
    def _validate_targets(self, config_data: Dict[str, Any]) -> None:
        """验证目标配置"""
        if 'targets' not in config_data:
            return
            
        targets = config_data['targets']
        if not isinstance(targets, list):
            self.errors.append("targets 必须是数组")
            return
        
        required_target_fields = ['id', 'type', 'position']
        
        for i, target in enumerate(targets):
            if not isinstance(target, dict):
                self.errors.append(f"目标 #{i+1} 必须是字典格式")
                continue
            
            for field in required_target_fields:
                if field not in target:
                    self.errors.append(f"目标 #{i+1} 缺少必填字段: {field}")
            
            # 验证ID格式
            if 'id' in target:
                if not re.match(r'^[A-Za-z0-9_-]+$', str(target['id'])):
                    self.errors.append(f"目标 #{i+1} ID格式无效: {target['id']}")
            
            # 验证位置
            if 'position' in target:
                self._validate_position(target['position'], f"目标 #{target.get('id', i+1)}")
            
            # 验证RCS
            if 'rcs' in target:
                rcs = target['rcs']
                if rcs <= 0:
                    self.errors.append(f"目标 #{i+1} RCS必须大于0")
                elif rcs < 0.001:
                    self.warnings.append(f"目标 #{i+1} RCS {rcs}m² 非常小，可能是无人机或鸟类")
    
    def _validate_metadata(self, config_data: Dict[str, Any]) -> None:
        """验证元数据"""
        if 'metadata' not in config_data:
            return
            
        metadata = config_data['metadata']
        if not isinstance(metadata, dict):
            self.errors.append("metadata 必须是字典")
            return
        
        # 验证日期格式
        date_fields = ['created_at', 'updated_at']
        for field in date_fields:
            if field in metadata:
                date_str = metadata[field]
                try:
                    datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    self.warnings.append(f"元数据 {field} 日期格式可能无效: {date_str}")
    
    def _validate_position(self, position: Dict[str, Any], element_name: str) -> None:
        """验证位置数据"""
        if not isinstance(position, dict):
            self.errors.append(f"{element_name} 位置必须是字典")
            return
        
        required_coords = ['lat', 'lon']
        for coord in required_coords:
            if coord not in position:
                self.errors.append(f"{element_name} 位置缺少 {coord}")
            else:
                value = position[coord]
                if not isinstance(value, (int, float)):
                    self.errors.append(f"{element_name} {coord} 必须是数字")
        
        # 验证坐标范围
        if 'lat' in position:
            lat = position['lat']
            if not (-90 <= lat <= 90):
                self.errors.append(f"{element_name} 纬度 {lat} 超出范围 [-90, 90]")
        
        if 'lon' in position:
            lon = position['lon']
            if not (-180 <= lon <= 180):
                self.errors.append(f"{element_name} 经度 {lon} 超出范围 [-180, 180]")
        
        if 'alt' in position:
            alt = position['alt']
            if not isinstance(alt, (int, float)):
                self.errors.append(f"{element_name} 海拔必须是数字")
            elif not (-100 <= alt <= 20000):
                self.warnings.append(f"{element_name} 海拔 {alt}m 可能不准确")
    
    def _validate_business_rules(self, config_data: Dict[str, Any]) -> None:
        """验证业务规则"""
        # 检查元素数量
        turbine_count = len(config_data.get('wind_turbines', []))
        radar_count = len(config_data.get('radar_stations', []))
        target_count = len(config_data.get('targets', []))
        
        if turbine_count == 0 and radar_count == 0:
            self.warnings.append("场景中既没有风机也没有雷达，分析可能无意义")
        
        if target_count == 0:
            self.warnings.append("场景中没有评估目标，分析可能无意义")
        
        # 检查坐标分布
        self._validate_coordinate_distribution(config_data)
    
    def _validate_coordinate_distribution(self, config_data: Dict[str, Any]) -> None:
        """验证坐标分布合理性"""
        all_positions = []
        
        # 收集所有位置
        for element_type in ['wind_turbines', 'radar_stations', 'communication_stations', 'targets']:
            elements = config_data.get(element_type, [])
            for element in elements:
                if 'position' in element and isinstance(element['position'], dict):
                    pos = element['position']
                    if 'lat' in pos and 'lon' in pos:
                        all_positions.append((pos['lat'], pos['lon']))
        
        if len(all_positions) < 2:
            return
        
        # 计算坐标范围
        lats = [p[0] for p in all_positions]
        lons = [p[1] for p in all_positions]
        
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        
        # 检查范围是否过大（约1000km）
        if lat_range > 9 or lon_range > 9:
            self.warnings.append(f"坐标分布范围较大（纬度:{lat_range:.2f}°, 经度:{lon_range:.2f}°），可能影响分析精度")
    
    def get_warnings(self) -> List[str]:
        """获取警告信息"""
        return self.warnings
    
    def get_errors(self) -> List[str]:
        """获取错误信息"""
        return self.errors

class YAMLLoader:
    """YAML文件加载器（使用直接验证）"""
    
    def __init__(self):
        self.validator = YAMLConfigValidator()
    
    def load_file(self, filepath: str) -> Dict[str, Any]:
        """加载并验证YAML文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            config_data = yaml.safe_load(content)
            if config_data is None:
                raise ValueError("YAML文件为空")
            
            # 使用直接验证
            is_valid, errors = self.validator.validate_scenario(config_data)
            
            if not is_valid:
                error_msg = "YAML验证失败:\n" + "\n".join(errors)
                raise ValueError(error_msg)
            
            # 自动补全逻辑（可选）
            config_data = self._auto_complete_config(config_data)
            
            return config_data
            
        except Exception as e:
            raise ValueError(f"文件加载失败: {str(e)}")
    
    def _auto_complete_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """自动补全配置（简化版）"""
        # 添加时间戳
        if 'metadata' not in config_data:
            config_data['metadata'] = {}
        
        if 'loaded_at' not in config_data['metadata']:
            config_data['metadata']['loaded_at'] = datetime.now().isoformat()
        
        return config_data

# 使用示例
def test_yaml_validation():
    """测试YAML验证"""
    validator = YAMLConfigValidator()
    
    # 您的示例YAML数据
    example_yaml = """
    name: "示例风电场场景"
    description: "示例场景用于演示系统功能"
    
    metadata:
      created_at: "2024-01-01"
      updated_at: "2024-01-01"
      author: "系统生成"
      version: "1.0"
    
    wind_turbines:
      - id: "WT001"
        model: "Vestas_V150"
        position: {lat: 40.123, lon: 116.234, alt: 50}
        height: 150
        rotor_diameter: 150
        orientation: 0
        operational: true
    
    radar_stations:
      - id: "RADAR001"
        type: "气象雷达"
        frequency_band: "S"
        position: {lat: 40.1, lon: 116.2, alt: 100}
        peak_power: 1000000
        antenna_gain: 40
    """
    
    config_data = yaml.safe_load(example_yaml)
    is_valid, errors = validator.validate_scenario(config_data)
    
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print("错误信息:")
        for error in errors:
            print(f"  - {error}")
    
    warnings = validator.get_warnings()
    if warnings:
        print("警告信息:")
        for warning in warnings:
            print(f"  - {warning}")

if __name__ == "__main__":
    test_yaml_validation()