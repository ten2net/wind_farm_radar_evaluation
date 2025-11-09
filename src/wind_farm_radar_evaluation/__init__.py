"""
风电场雷达影响评估系统

一个用于评估风电场对海岸监视雷达影响的专业仿真分析工具。
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from wind_farm_radar_evaluation.config.configuration import (
    ConfigurationManager, 
    get_config_manager
)
from wind_farm_radar_evaluation.main import main

__all__ = [
    "ConfigurationManager",
    "get_config_manager", 
    "main"
]
