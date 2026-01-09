"""
配置加载工具
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

def load_radar_database(config_path: str = "config/radar_database.yaml") -> Dict[str, Any]:
    """加载雷达数据库配置"""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            # 返回默认配置
            return _get_default_radar_database()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    except Exception as e:
        print(f"加载雷达数据库失败: {e}")
        return _get_default_radar_database()

def load_scenarios(config_path: str = "config/scenarios.yaml") -> Dict[str, Any]:
    """加载想定配置"""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            return {}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    except Exception as e:
        print(f"加载想定配置失败: {e}")
        return {}

def load_environment_config(config_path: str = "config/environment.yaml") -> Dict[str, Any]:
    """加载环境配置"""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            return _get_default_environment_config()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    except Exception as e:
        print(f"加载环境配置失败: {e}")
        return _get_default_environment_config()

def _get_default_radar_database() -> Dict[str, Any]:
    """获取默认雷达数据库配置"""
    return {
        "radar_types": {
            "early_warning": {
                "base_params": {
                    "name": "预警雷达",
                    "frequency": 3.0,
                    "power": 200,
                    "gain": 40,
                    "beamwidth": 1.5,
                    "range_max": 450
                },
                "variants": []
            }
        },
        "jammer_types": {
            "standoff_jammer": {
                "base_params": {
                    "name": "远距支援干扰机",
                    "power": 1000,
                    "gain": 15,
                    "beamwidth": 60
                },
                "variants": []
            }
        }
    }

def _get_default_environment_config() -> Dict[str, Any]:
    """获取默认环境配置"""
    return {
        "terrain_types": {
            "flat": {
                "name": "平原",
                "roughness": 0.1
            }
        },
        "atmosphere_types": {
            "standard": {
                "name": "标准大气",
                "refractivity": 1.0
            }
        }
    }
