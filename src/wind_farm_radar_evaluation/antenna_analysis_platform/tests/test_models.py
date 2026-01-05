"""
天线分析平台 - 模型单元测试
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.antenna_models import (
    AntennaParameters, AntennaGeometry, FeedNetwork,
    AntennaType, PolarizationType, PatternComponent
)
from models.pattern_models import RadiationPattern, PatternSlice


class TestAntennaModels:
    """天线模型测试类"""
    
    def test_antenna_parameters_creation(self):
        """测试天线参数创建"""
        # 创建基本天线参数
        antenna = AntennaParameters(
            name="测试天线",
            antenna_type=AntennaType.DIPOLE,
            frequency_range=(1.0, 2.0),
            center_frequency=1.5,
            gain=2.15,
            bandwidth=10.0,
            vswr=1.5,
            polarization=PolarizationType.VERTICAL
        )
        
        assert antenna.name == "测试天线"
        assert antenna.antenna_type == AntennaType.DIPOLE
        assert antenna.center_frequency == 1.5
        assert antenna.gain == 2.15
        assert antenna.bandwidth == 10.0
        assert antenna.vswr == 1.5
        assert antenna.polarization == PolarizationType.VERTICAL
    
    def test_antenna_geometry(self):
        """测试天线几何参数"""
        geometry = AntennaGeometry(
            length=0.5,  # 米
            width=0.3,
            height=0.1,
            diameter=0.2,
            focal_length=0.3,
            has_ground_plane=True
        )
        
        assert geometry.length == 0.5
        assert geometry.width == 0.3
        assert geometry.height == 0.1
        assert geometry.has_ground_plane is True
    
    def test_feed_network(self):
        """测试馈电网络"""
        feed = FeedNetwork(
            type='coaxial',
            impedance=50.0,
            has_balun=True,
            matching_network=True
        )
        
        assert feed.type == 'coaxial'
        assert feed.impedance == 50.0
        assert feed.has_balun is True
        assert feed.matching_network is True
    
    def test_antenna_to_dict(self):
        """测试天线参数序列化"""
        antenna = AntennaParameters(
            name="测试天线",
            antenna_type=AntennaType.PATCH,
            center_frequency=2.4
        )
        
        data = antenna.to_dict()
        
        assert isinstance(data, dict)
        assert data['name'] == "测试天线"
        assert data['antenna_type'] == AntennaType.PATCH.value
        assert data['center_frequency'] == 2.4
    
    def test_antenna_from_dict(self):
        """测试天线参数反序列化"""
        data = {
            'name': "从字典创建的天线",
            'antenna_type': 'horn',
            'center_frequency': 10.0,
            'gain': 20.0
        }
        
        antenna = AntennaParameters.from_dict(data)
        
        assert antenna.name == "从字典创建的天线"
        assert antenna.antenna_type == AntennaType.HORN
        assert antenna.center_frequency == 10.0
        assert antenna.gain == 20.0
    
    def test_antenna_validation(self):
        """测试天线参数验证"""
        # 测试无效频率
        with pytest.raises(ValueError):
            AntennaParameters(
                name="无效天线",
                antenna_type=AntennaType.DIPOLE,
                center_frequency=-1.0  # 无效频率
            )
        
        # 测试无效增益
        with pytest.raises(ValueError):
            AntennaParameters(
                name="无效天线",
                antenna_type=AntennaType.DIPOLE,
                center_frequency=1.0,
                gain=-100.0  # 无效增益
            )


class TestPatternModels:
    """方向图模型测试类"""
    
    def test_radiation_pattern_creation(self):
        """测试方向图创建"""
        # 创建测试数据
        theta = np.linspace(0, 180, 37)
        phi = np.linspace(0, 360, 73)
        gain_data = np.random.randn(37, 73) * 10
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data,
            component=PatternComponent.TOTAL
        )
        
        assert pattern.frequency == 2.4
        assert pattern.theta_grid.shape == (37,)
        assert pattern.phi_grid.shape == (73,)
        assert pattern.gain_data.shape == (37, 73)
        assert pattern.component == PatternComponent.TOTAL
    
    def test_pattern_slice(self):
        """测试方向图切片"""
        theta = np.linspace(0, 180, 37)
        phi = np.linspace(0, 360, 73)
        
        # 创建正弦波方向图
        theta_rad = np.deg2rad(theta)
        phi_rad = np.deg2rad(phi)
        
        # 3D方向图数据
        gain_data = np.outer(np.sin(theta_rad), np.cos(phi_rad))
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data
        )
        
        # 测试E面切片
        e_slice = pattern.get_slice(fixed_phi=0)
        assert isinstance(e_slice, PatternSlice)
        assert len(e_slice.angles) == len(theta)
        assert len(e_slice.values) == len(theta)
        
        # 测试H面切片
        h_slice = pattern.get_slice(fixed_theta=90)
        assert len(h_slice.angles) == len(phi)
        assert len(h_slice.values) == len(phi)
    
    def test_pattern_statistics(self):
        """测试方向图统计"""
        # 创建有明确最大值的方向图
        theta = np.linspace(0, 180, 181)
        phi = np.linspace(0, 360, 361)
        
        # 在(90, 0)处创建峰值
        gain_data = np.zeros((181, 361))
        gain_data[90, 0] = 10.0  # 峰值
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data
        )
        
        stats = pattern.calculate_statistics()
        
        assert stats.max_gain == 10.0
        assert stats.mean_gain == pytest.approx(10.0 / (181 * 361))
        assert stats.peak_theta == 90.0
        assert stats.peak_phi == 0.0
    
    def test_pattern_normalization(self):
        """测试方向图归一化"""
        theta = np.linspace(0, 180, 10)
        phi = np.linspace(0, 360, 10)
        gain_data = np.random.randn(10, 10) * 5 + 10
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data
        )
        
        normalized = pattern.normalize()
        
        # 检查归一化后的最大值是否为0
        assert np.max(normalized.gain_data) == pytest.approx(0.0, abs=1e-10)
        
        # 检查原始数据是否未被修改
        assert not np.array_equal(pattern.gain_data, normalized.gain_data)
    
    def test_pattern_save_load(self, tmp_path):
        """测试方向图保存和加载"""
        # 创建测试方向图
        theta = np.linspace(0, 180, 10)
        phi = np.linspace(0, 360, 10)
        gain_data = np.random.randn(10, 10)
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data
        )
        
        # 保存到临时文件
        filepath = tmp_path / "test_pattern.npy"
        pattern.save(filepath)
        
        # 检查文件是否存在
        assert filepath.exists()
        
        # 加载文件
        loaded_pattern = RadiationPattern.load(filepath)
        
        # 检查数据一致性
        assert loaded_pattern.frequency == pattern.frequency
        assert np.array_equal(loaded_pattern.theta_grid, pattern.theta_grid)
        assert np.array_equal(loaded_pattern.phi_grid, pattern.phi_grid)
        assert np.array_equal(loaded_pattern.gain_data, pattern.gain_data)
    
    def test_pattern_interpolation(self):
        """测试方向图插值"""
        theta = np.linspace(0, 180, 10)
        phi = np.linspace(0, 360, 10)
        
        # 创建简单方向图
        gain_data = np.outer(np.sin(np.deg2rad(theta)), np.cos(np.deg2rad(phi)))
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data
        )
        
        # 插值到更高分辨率
        interpolated = pattern.interpolate(theta_factor=2, phi_factor=2)
        
        assert interpolated.theta_grid.shape == (19,)  # 2 * 10-1
        assert interpolated.phi_grid.shape == (19,)
        assert interpolated.gain_data.shape == (19, 19)
        
        # 检查插值是否平滑
        # 原始数据的最大值应该在插值数据中也能找到
        max_original = np.max(pattern.gain_data)
        max_interpolated = np.max(interpolated.gain_data)
        assert abs(max_original - max_interpolated) < 0.1


class TestPatternAnalysis:
    """方向图分析测试类"""
    
    def test_beamwidth_calculation(self):
        """测试波束宽度计算"""
        # 创建高斯波束方向图
        theta = np.linspace(-90, 90, 181)
        phi = np.linspace(0, 360, 1)  # 单一切面
        
        # 高斯波束，3dB波束宽度约30度
        sigma = 15 / (2 * np.sqrt(2 * np.log(2)))  # 转换为高斯标准差
        gain_data = np.exp(-(theta**2) / (2 * sigma**2))
        gain_data = 20 * np.log10(gain_data + 1e-10)  # 转换为dB
        gain_data = gain_data.reshape(-1, 1)  # 转换为2D数组
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta + 90,  # 转换为0-180度
            phi_grid=phi,
            gain_data=gain_data
        )
        
        # 计算波束宽度
        beamwidths = pattern.calculate_beamwidths(levels=[-3, -10])
        
        assert -3 in beamwidths
        assert -10 in beamwidths
        
        # 检查3dB波束宽度是否接近30度
        bw_3db = beamwidths[-3]
        assert abs(bw_3db - 30.0) < 5.0  # 允许5度误差
    
    def test_sidelobe_detection(self):
        """测试副瓣检测"""
        # 创建有副瓣的方向图
        theta = np.linspace(0, 180, 181)
        phi = np.linspace(0, 360, 1)
        
        # 主瓣在90度，副瓣在60和120度
        angles = np.deg2rad(theta - 90)
        mainlobe = np.exp(-(angles**2) / 0.1)
        sidelobe1 = 0.3 * np.exp(-((angles - np.deg2rad(30))**2) / 0.2)
        sidelobe2 = 0.2 * np.exp(-((angles + np.deg2rad(30))**2) / 0.2)
        
        gain_data = 20 * np.log10(mainlobe + sidelobe1 + sidelobe2 + 1e-10)
        gain_data = gain_data.reshape(-1, 1)
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data
        )
        
        # 检测副瓣
        sidelobes = pattern.find_sidelobes()
        
        assert len(sidelobes) >= 2  # 至少有两个副瓣
        
        # 检查副瓣位置
        sidelobe_positions = [sl['angle'] for sl in sidelobes]
        assert any(abs(pos - 60) < 10 for pos in sidelobe_positions)
        assert any(abs(pos - 120) < 10 for pos in sidelobe_positions)
    
    def test_null_detection(self):
        """测试零陷检测"""
        # 创建有零陷的方向图
        theta = np.linspace(0, 180, 181)
        phi = np.linspace(0, 360, 1)
        
        # 正弦波方向图，在45度和135度有零陷
        gain_data = np.abs(np.sin(2 * np.deg2rad(theta)))
        gain_data = 20 * np.log10(gain_data + 1e-10)
        gain_data = gain_data.reshape(-1, 1)
        
        pattern = RadiationPattern(
            frequency=2.4,
            theta_grid=theta,
            phi_grid=phi,
            gain_data=gain_data
        )
        
        # 检测零陷
        nulls = pattern.find_nulls(threshold=-40)
        
        assert len(nulls) >= 2  # 至少有两个零陷
        
        # 检查零陷位置
        null_positions = [null['angle'] for null in nulls]
        assert any(abs(pos - 45) < 5 for pos in null_positions)
        assert any(abs(pos - 135) < 5 for pos in null_positions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])