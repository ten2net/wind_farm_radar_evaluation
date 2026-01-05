"""
Pytest配置和测试工具
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.antenna_models import AntennaParameters, AntennaType, PolarizationType


@pytest.fixture
def sample_antenna():
    """提供示例天线"""
    return AntennaParameters(
        name="测试天线",
        antenna_type=AntennaType.DIPOLE,
        frequency_range=(1.0, 2.0),
        center_frequency=1.5,
        gain=2.15,
        bandwidth=10.0,
        vswr=1.5,
        polarization=PolarizationType.VERTICAL,
        beamwidth_e=78.0,
        beamwidth_h=360.0,
        sidelobe_level=-12.0,
        front_to_back_ratio=0.0,
        efficiency=0.95
    )


@pytest.fixture
def patch_antenna():
    """提供微带贴片天线"""
    return AntennaParameters(
        name="测试微带贴片",
        antenna_type=AntennaType.PATCH,
        frequency_range=(2.4, 2.5),
        center_frequency=2.45,
        gain=7.0,
        bandwidth=3.0,
        vswr=1.8,
        polarization=PolarizationType.LINEAR,
        beamwidth_e=75.0,
        beamwidth_h=75.0,
        sidelobe_level=-15.0,
        front_to_back_ratio=20.0,
        efficiency=0.85
    )


@pytest.fixture
def horn_antenna():
    """提供喇叭天线"""
    return AntennaParameters(
        name="测试喇叭天线",
        antenna_type=AntennaType.HORN,
        frequency_range=(8.0, 12.0),
        center_frequency=10.0,
        gain=20.0,
        bandwidth=40.0,
        vswr=1.3,
        polarization=PolarizationType.HORIZONTAL,
        beamwidth_e=15.0,
        beamwidth_h=15.0,
        sidelobe_level=-20.0,
        front_to_back_ratio=35.0,
        efficiency=0.9
    )


@pytest.fixture
def sample_pattern(sample_antenna):
    """提供示例方向图"""
    from services.pattern_generator import get_pattern_generator_service
    
    service = get_pattern_generator_service()
    return service.generate_pattern(
        antenna=sample_antenna,
        generator_type='analytical',
        theta_resolution=5,
        phi_resolution=5
    )


@pytest.fixture
def high_res_pattern(sample_antenna):
    """提供高分辨率方向图"""
    from services.pattern_generator import get_pattern_generator_service
    
    service = get_pattern_generator_service()
    return service.generate_pattern(
        antenna=sample_antenna,
        generator_type='analytical',
        theta_resolution=1,
        phi_resolution=1
    )


@pytest.fixture
def temp_dir():
    """提供临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_analysis_results(sample_pattern, sample_antenna):
    """提供示例分析结果"""
    from services.analysis_service import get_analysis_service
    
    service = get_analysis_service()
    return service.comprehensive_analysis(
        pattern=sample_pattern,
        antenna=sample_antenna
    )


def pytest_configure(config):
    """Pytest配置"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试（需要较长时间）"
    )
    config.addinivalue_line(
        "markers", "integration: 标记为集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 标记为性能测试"
    )


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="运行慢速测试"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="运行集成测试"
    )
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="运行性能测试"
    )


def pytest_collection_modifyitems(config, items):
    """根据标记过滤测试项"""
    skip_slow = pytest.mark.skip(reason="需要 --run-slow 选项来运行")
    skip_integration = pytest.mark.skip(reason="需要 --run-integration 选项来运行")
    skip_performance = pytest.mark.skip(reason="需要 --run-performance 选项来运行")
    
    for item in items:
        if "slow" in item.keywords and not config.getoption("--run-slow"):
            item.add_marker(skip_slow)
        if "integration" in item.keywords and not config.getoption("--run-integration"):
            item.add_marker(skip_integration)
        if "performance" in item.keywords and not config.getoption("--run-performance"):
            item.add_marker(skip_performance)