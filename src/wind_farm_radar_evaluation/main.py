#!/usr/bin/env python3
"""
风电场雷达影响评估系统主程序
"""

import os
import sys
import logging
from pathlib import Path

# 添加配置模块路径
sys.path.insert(0, str(Path(__file__).parent))

from config.configuration import get_config_manager
from data_models import RadarParameters, RadarGeolocation, TargetParameters

def setup_logging(config: dict):
    """设置日志系统"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', 'logs/system.log')
    
    # 创建日志目录
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_radar_parameters_from_config(radar_config: dict) -> RadarParameters:
    """从配置创建雷达参数对象"""
    return RadarParameters(
        name=radar_config.get('name', '海岸监视雷达'),
        frequency=radar_config.get('frequency', 9.4e9),
        bandwidth=radar_config.get('bandwidth', 10e6),
        pulse_width=radar_config.get('pulse_width', 50e-6),
        tx_power=radar_config.get('tx_power', 40),
        pulses=radar_config.get('pulses', 512),
        prp=radar_config.get('prp', 1e-3),
        fs=radar_config.get('fs', 20e6),
        noise_figure=radar_config.get('noise_figure', 6),
        rf_gain=radar_config.get('rf_gain', 30),
        baseband_gain=radar_config.get('baseband_gain', 50),
        radar_height=radar_config.get('geolocation', {}).get('altitude', 50),
        antenna_gain=radar_config.get('antenna_gain', 30),
        beamwidth_azimuth=radar_config.get('beamwidth_azimuth', 1.5),
        beamwidth_elevation=radar_config.get('beamwidth_elevation', 20),
        polarization=radar_config.get('polarization', 'horizontal')
    )

def create_radar_geolocation_from_config(radar_config: dict) -> RadarGeolocation:
    """从配置创建雷达地理定位对象"""
    geo = radar_config.get('geolocation', {})
    return RadarGeolocation(
        latitude=geo.get('latitude', 36.5),
        longitude=geo.get('longitude', 120.5),
        altitude=geo.get('altitude', 50),
        heading=geo.get('heading', 90),
        name=geo.get('name', '雷达站')
    )

def create_target_parameters_from_config(target_configs: dict) -> list:
    """从配置创建目标参数对象列表"""
    targets = []
    
    # 处理空中目标
    for air_target in target_configs.get('airborne', []):
        targets.append(TargetParameters(
            name=air_target.get('name', '空中目标'),
            target_type='airborne',
            rcs=air_target.get('rcs', 10.0),
            speed_range=tuple(air_target.get('speed_range', [100, 300])),
            altitude_range=tuple(air_target.get('altitude_range', [1000, 10000])),
            operational_profile=air_target.get('operational_profile', {})
        ))
    
    # 处理海面目标
    for surface_target in target_configs.get('surface', []):
        targets.append(TargetParameters(
            name=surface_target.get('name', '海面目标'),
            target_type='surface',
            rcs=surface_target.get('rcs', 20.0),
            speed_range=tuple(surface_target.get('speed_range', [5, 15])),
            altitude_range=tuple(surface_target.get('altitude_range', [-10, 10])),
            operational_profile=surface_target.get('operational_profile', {})
        ))
    
    return targets

def main():
    """主函数"""
    try:
        # 加载配置
        config_manager = get_config_manager("conf/config.yaml")
        
        if not config_manager.validate_config():
            logging.error("配置验证失败，程序退出")
            return 1
        
        config = config_manager.config
        
        # 设置日志
        setup_logging(config.get('system', {}))
        
        logging.info("风电场雷达影响评估系统启动")
        
        # 创建雷达参数
        radar_params = create_radar_parameters_from_config(config['radar'])
        radar_geolocation = create_radar_geolocation_from_config(config['radar'])
        
        logging.info(f"雷达配置加载完成: {radar_params.name}")
        
        # 创建评估目标
        target_configs = config_manager.get_evaluation_targets()
        targets = create_target_parameters_from_config(target_configs)
        
        logging.info(f"加载了 {len(targets)} 个评估目标")
        
        # 这里可以添加实际的评估逻辑
        # 由于这是一个框架，我们只输出配置信息
        logging.info("系统初始化完成，准备开始评估...")
        
        # 示例：输出配置摘要
        wind_farm_config = config_manager.get_wind_farm_config()
        logging.info(f"风电场配置: {len(wind_farm_config.turbine_coordinates)} 台风机")
        
        simulation_config = config_manager.get_simulation_config()
        logging.info(f"仿真配置: 时长 {simulation_config.duration}s, 步长 {simulation_config.time_step}s")
        
        logging.info("评估完成！")
        return 0
        
    except Exception as e:
        logging.error(f"程序执行错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
