"""
仿真引擎单元测试
"""
import pytest
import numpy as np
from src.core.simulation import EWSimulator, PropagationModel, NetworkEWSimulator
from src.core.entities import Radar, Jammer, Position, RadarParameters, JammerParameters
from src.core.entities.target import Aircraft

class TestPropagationModel:
    """测试传播模型"""
    
    def test_free_space_loss(self):
        """测试自由空间损耗计算"""
        model = PropagationModel(frequency=3.0, distance=100.0)
        loss = model.free_space_loss()
        
        # 验证损耗是正数
        assert loss > 0
        assert isinstance(loss, float)
    
    def test_two_ray_loss(self):
        """测试双径模型损耗计算"""
        model = PropagationModel(frequency=3.0, distance=100.0)
        loss = model.two_ray_loss(ht=50.0, hr=10000.0)
        
        assert loss > 0
        assert isinstance(loss, float)
    
    def test_total_loss(self):
        """测试总损耗计算"""
        model = PropagationModel(
            frequency=3.0,
            distance=100.0,
            terrain_type="flat",
            atmosphere="standard"
        )
        
        total_loss = model.total_loss(ht=50.0, hr=10000.0)
        assert total_loss > 0
        assert isinstance(total_loss, float)

class TestEWSimulator:
    """测试电子战仿真器"""
    
    def setup_entities(self):
        """设置测试实体"""
        # 创建雷达
        radar_pos = Position(39.9, 116.4, 50.0)
        radar_params = RadarParameters(
            frequency=3.0,
            power=100.0,
            gain=40.0,
            beamwidth=1.5,
            sensitivity=-120.0,
            range_max=300.0
        )
        
        radar = Radar(
            id="test_radar",
            name="测试雷达",
            position=radar_pos,
            radar_params=radar_params
        )
        
        # 创建干扰机
        jammer_pos = Position(40.1, 116.6, 10000.0)
        jammer_params = JammerParameters(
            frequency_range=(0.5, 18.0),
            power=1000.0,
            gain=15.0,
            beamwidth=60.0,
            eirp=80.0,
            jam_types=["阻塞"],
            response_time=2.0
        )
        
        jammer = Jammer(
            id="test_jammer",
            name="测试干扰机",
            position=jammer_pos,
            jammer_params=jammer_params
        )
        
        return radar, jammer
    
    def test_jamming_effect_calculation(self):
        """测试干扰效果计算"""
        radar, jammer = self.setup_entities()
        
        result = EWSimulator.calculate_jamming_effect(
            radar, jammer, environment={"terrain": "flat"}
        )
        
        # 验证结果包含必要的字段
        assert "effective" in result
        assert "j_s_ratio" in result
        assert "detection_probability" in result
        assert "propagation_loss" in result
        assert "distance_km" in result
        
        # 验证数据类型
        assert isinstance(result["effective"], bool)
        assert isinstance(result["j_s_ratio"], float)
        assert isinstance(result["detection_probability"], float)
        assert isinstance(result["propagation_loss"], float)
        assert isinstance(result["distance_km"], float)
    
    def test_jamming_with_targets(self):
        """测试包含目标的干扰效果计算"""
        radar, jammer = self.setup_entities()
        
        # 创建目标
        target = Aircraft(
            id="test_target",
            name="测试目标",
            position=Position(40.0, 116.5, 10000.0),
            rcs=5.0,
            speed=300.0
        )
        
        result = EWSimulator.calculate_jamming_effect(
            radar, jammer, targets=[target]
        )
        
        assert "target_signal_db" in result
        assert result["target_signal_db"] is not None
    
    def test_simulate_radar_coverage(self):
        """测试雷达覆盖范围模拟"""
        radar, _ = self.setup_entities()
        
        coverage = EWSimulator.simulate_radar_coverage(
            radar, resolution_km=10.0
        )
        
        # 验证返回的覆盖数据
        assert isinstance(coverage, np.ndarray)
        assert len(coverage.shape) == 2  # 应该是二维数组
        
        # 覆盖值应该在0到1之间
        assert coverage.min() >= 0
        assert coverage.max() <= 1

class TestNetworkEWSimulator:
    """测试网络化电子战仿真器"""
    
    def test_network_combat_simulation(self):
        """测试网络对抗仿真"""
        # 创建多个雷达
        radars = []
        for i in range(3):
            pos = Position(39.9 + i*0.1, 116.4 + i*0.1, 50.0)
            radar_params = RadarParameters(
                frequency=3.0 + i,
                power=100.0 + i*50,
                gain=40.0,
                beamwidth=1.5
            )
            
            radar = Radar(
                id=f"radar_{i}",
                name=f"雷达{i}",
                position=pos,
                radar_params=radar_params
            )
            radars.append(radar)
        
        # 创建多个干扰机
        jammers = []
        for i in range(2):
            pos = Position(40.2 + i*0.1, 116.7 + i*0.1, 10000.0)
            jammer_params = JammerParameters(
                frequency_range=(0.5, 18.0),
                power=1000.0 + i*500,
                gain=15.0,
                beamwidth=60.0,
                eirp=80.0,
                jam_types=["阻塞"],
                response_time=2.0
            )
            
            jammer = Jammer(
                id=f"jammer_{i}",
                name=f"干扰机{i}",
                position=pos,
                jammer_params=jammer_params
            )
            jammers.append(jammer)
        
        # 运行网络对抗仿真
        result = NetworkEWSimulator.simulate_network_combat(
            radars, jammers, [], time_steps=10
        )
        
        # 验证结果结构
        assert "time_steps" in result
        assert "radar_performance" in result
        assert "jammer_performance" in result
        assert "network_metrics" in result
        
        # 验证雷达性能数据
        assert len(result["radar_performance"]) == len(radars)
        
        # 验证网络指标
        metrics = result["network_metrics"]
        assert "avg_detection_probability" in metrics
        assert "coverage_ratio" in metrics
        assert "jammer_utilization" in metrics
        assert "survivability" in metrics
        assert "info_superiority" in metrics
