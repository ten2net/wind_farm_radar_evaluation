#!/usr/bin/env python3
"""
配置文件加载和管理模块
"""

import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

@dataclass
class RadarConfig:
    """雷达配置数据类"""
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
    load_resistor: float
    antenna_gain: float
    beamwidth_azimuth: float
    beamwidth_elevation: float
    polarization: str
    geolocation: Dict[str, Any]

@dataclass
class WindFarmConfig:
    """风电场配置数据类"""
    turbine_common: Dict[str, Any]
    data_source: Dict[str, Any]
    turbine_coordinates: list

@dataclass
class SimulationConfig:
    """仿真配置数据类"""
    duration: float
    time_step: float
    multipath: Dict[str, Any]
    signal_processing: Dict[str, Any]
    accuracy: Dict[str, Any]

@dataclass
class VisualizationConfig:
    """可视化配置数据类"""
    output: Dict[str, Any]
    style: Dict[str, Any]
    plots: Dict[str, Any]

@dataclass
class SystemConfig:
    """系统配置数据类"""
    parallel: Dict[str, Any]
    memory: Dict[str, Any]
    logging: Dict[str, Any]

class ConfigurationManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "conf/config.yaml"):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logging.info(f"配置文件加载成功: {config_path}")
            return self.config
            
        except Exception as e:
            logging.error(f"配置文件加载失败: {e}")
            # 使用默认配置
            self._create_default_config()
            return self.config
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config = {
            "version": "1.0",
            "description": "默认配置",
            "radar": {
                "name": "默认雷达",
                "frequency": 9.4e9,
                "bandwidth": 10e6,
                "pulse_width": 50e-6,
                "tx_power": 40,
                "pulses": 512,
                "prp": 1e-3,
                "fs": 20e6,
                "noise_figure": 6,
                "rf_gain": 30,
                "baseband_gain": 50,
                "load_resistor": 1000,
                "antenna_gain": 30,
                "beamwidth_azimuth": 1.5,
                "beamwidth_elevation": 20,
                "polarization": "horizontal",
                "geolocation": {
                    "latitude": 36.5,
                    "longitude": 120.5,
                    "altitude": 50,
                    "heading": 90,
                    "name": "默认雷达站"
                }
            },
            "wind_farm": {
                "turbine_common": {
                    "height": 100,
                    "rotor_diameter": 120,
                    "blade_length": 60,
                    "rotation_speed": 15,
                    "tower_diameter": 8,
                    "material": "steel",
                    "rcs_model": "complex"
                },
                "data_source": {
                    "type": "array",
                    "file_path": "data/turbine_coordinates.csv",
                    "file_format": "csv",
                    "coordinate_format": "wgs84"
                },
                "turbine_coordinates": []
            }
        }
        logging.warning("使用默认配置")
    
    def get_radar_config(self) -> RadarConfig:
        """获取雷达配置"""
        radar_data = self.config.get('radar', {})
        return RadarConfig(
            name=radar_data.get('name', '默认雷达'),
            frequency=radar_data.get('frequency', 9.4e9),
            bandwidth=radar_data.get('bandwidth', 10e6),
            pulse_width=radar_data.get('pulse_width', 50e-6),
            tx_power=radar_data.get('tx_power', 40),
            pulses=radar_data.get('pulses', 512),
            prp=radar_data.get('prp', 1e-3),
            fs=radar_data.get('fs', 20e6),
            noise_figure=radar_data.get('noise_figure', 6),
            rf_gain=radar_data.get('rf_gain', 30),
            baseband_gain=radar_data.get('baseband_gain', 50),
            load_resistor=radar_data.get('load_resistor', 1000),
            antenna_gain=radar_data.get('antenna_gain', 30),
            beamwidth_azimuth=radar_data.get('beamwidth_azimuth', 1.5),
            beamwidth_elevation=radar_data.get('beamwidth_elevation', 20),
            polarization=radar_data.get('polarization', 'horizontal'),
            geolocation=radar_data.get('geolocation', {})
        )
    
    def get_wind_farm_config(self) -> WindFarmConfig:
        """获取风电场配置"""
        wind_farm_data = self.config.get('wind_farm', {})
        return WindFarmConfig(
            turbine_common=wind_farm_data.get('turbine_common', {}),
            data_source=wind_farm_data.get('data_source', {}),
            turbine_coordinates=wind_farm_data.get('turbine_coordinates', [])
        )
    
    def get_simulation_config(self) -> SimulationConfig:
        """获取仿真配置"""
        sim_data = self.config.get('simulation', {})
        return SimulationConfig(
            duration=sim_data.get('duration', 600),
            time_step=sim_data.get('time_step', 10.0),
            multipath=sim_data.get('multipath', {}),
            signal_processing=sim_data.get('signal_processing', {}),
            accuracy=sim_data.get('accuracy', {})
        )
    
    def get_visualization_config(self) -> VisualizationConfig:
        """获取可视化配置"""
        viz_data = self.config.get('visualization', {})
        return VisualizationConfig(
            output=viz_data.get('output', {}),
            style=viz_data.get('style', {}),
            plots=viz_data.get('plots', {})
        )
    
    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        sys_data = self.config.get('system', {})
        return SystemConfig(
            parallel=sys_data.get('parallel', {}),
            memory=sys_data.get('memory', {}),
            logging=sys_data.get('logging', {})
        )
    
    def get_evaluation_targets(self) -> Dict[str, list]:
        """获取评估目标配置"""
        return self.config.get('evaluation_targets', {})
    
    def get_signal_processing_config(self) -> Dict[str, Any]:
        """获取信号处理配置"""
        return self.config.get('signal_processing', {})
    
    def get_reporting_config(self) -> Dict[str, Any]:
        """获取报告生成配置"""
        return self.config.get('reporting', {})
    
    def save_config(self, file_path: str = None):
        """保存配置到文件"""
        if file_path is None:
            file_path = self.config_file
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        logging.info(f"配置已保存到: {file_path}")
    
    def update_config(self, section: str, key: str, value: Any):
        """更新配置项"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        # 这里可以添加配置验证逻辑
        required_sections = ['radar', 'wind_farm', 'simulation']
        
        for section in required_sections:
            if section not in self.config:
                logging.error(f"缺少必要配置节: {section}")
                return False
        
        # 验证雷达配置
        radar = self.config.get('radar', {})
        if radar.get('frequency', 0) <= 0:
            logging.error("雷达频率必须大于0")
            return False
        
        # 可以添加更多验证规则...
        
        return True

# 全局配置实例
_config_manager = None

def get_config_manager(config_file: str = "conf/config.yaml") -> ConfigurationManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_file)
    return _config_manager

def reload_config(config_file: str = None) -> ConfigurationManager:
    """重新加载配置"""
    global _config_manager
    if config_file:
        _config_manager = ConfigurationManager(config_file)
    else:
        _config_manager.load_config()
    return _config_manager
