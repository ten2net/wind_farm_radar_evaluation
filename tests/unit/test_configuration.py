#!/usr/bin/env python3
"""
配置管理模块测试
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from wind_farm_radar_evaluation.config.configuration import ConfigurationManager

def test_configuration_loading():
    """测试配置加载"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            'version': '1.0',
            'radar': {
                'name': '测试雷达',
                'frequency': 9.4e9,
                'bandwidth': 10e6
            }
        }
        yaml.dump(config_data, f)
        config_file = f.name
    
    try:
        # 测试配置加载
        config_manager = ConfigurationManager(config_file)
        radar_config = config_manager.get_radar_config()
        
        assert radar_config.name == '测试雷达'
        assert radar_config.frequency == 9.4e9
        assert radar_config.bandwidth == 10e6
        
    finally:
        # 清理临时文件
        Path(config_file).unlink()

def test_configuration_validation():
    """测试配置验证"""
    config_manager = ConfigurationManager()
    
    # 应该能够通过验证（有默认配置）
    assert config_manager.validate_config() == True

if __name__ == "__main__":
    pytest.main([__file__])
