#!/usr/bin/env python3
"""
风电场雷达影响评估系统 - 基本使用示例
"""

import sys
from pathlib import Path

# 添加源代码路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from wind_farm_radar_evaluation.config.configuration import get_config_manager
from wind_farm_radar_evaluation.main import main

def example_basic_usage():
    """基本使用示例"""
    print("风电场雷达影响评估系统 - 基本使用示例")
    print("=" * 50)
    
    # 1. 加载配置
    config_manager = get_config_manager("../conf/config.yaml")
    
    # 2. 获取配置信息
    radar_config = config_manager.get_radar_config()
    wind_farm_config = config_manager.get_wind_farm_config()
    
    print(f"雷达名称: {radar_config.name}")
    print(f"雷达频率: {radar_config.frequency / 1e9:.2f} GHz")
    print(f"风机数量: {len(wind_farm_config.turbine_coordinates)}")
    
    # 3. 运行评估
    print("\n运行评估...")
    result = main()
    
    if result == 0:
        print("评估完成！")
    else:
        print("评估过程中出现错误")
    
    return result

if __name__ == "__main__":
    example_basic_usage()
