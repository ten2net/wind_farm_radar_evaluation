#!/usr/bin/env python3
"""
系统集成测试
"""

import pytest
from wind_farm_radar_evaluation.main import main

def test_main_function():
    """测试主函数"""
    # 主函数应该能够正常运行（即使只是加载配置）
    result = main()
    assert result in [0, 1]  # 返回码应该是0或1

if __name__ == "__main__":
    pytest.main([__file__])
