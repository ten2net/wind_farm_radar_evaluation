"""
集成测试
"""
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.patterns.strategy import ScenarioFactory
from src.utils.config_loader import load_radar_database, load_scenarios
import yaml
import tempfile

class TestIntegration:
    """集成测试"""
    
    def test_config_loading(self):
        """测试配置加载集成"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "test_section": {
                    "key1": "value1",
                    "key2": 123
                }
            }
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # 测试配置加载
            from src.utils.config_loader import load_config
            loaded_config = load_config(config_path)
            
            assert loaded_config["test_section"]["key1"] == "value1"
            assert loaded_config["test_section"]["key2"] == 123
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    def test_scenario_with_config(self):
        """测试想定与配置集成"""
        # 加载默认配置
        radar_db = load_radar_database()
        scenarios_db = load_scenarios()
        
        # 验证配置加载成功
        assert radar_db is not None
        assert isinstance(radar_db, dict)
        
        assert scenarios_db is not None
        assert isinstance(scenarios_db, dict)
        
        # 测试创建想定
        if "one_vs_one" in scenarios_db:
            scenario = ScenarioFactory.create_scenario("one_vs_one")
            
            # 使用配置文件设置想定
            scenario.setup(scenarios_db["one_vs_one"])
            
            # 验证想定设置成功
            assert scenario.radars is not None
            assert scenario.jammers is not None
    
    def test_full_simulation_flow(self):
        """测试完整仿真流程"""
        # 创建一对一对抗想定
        scenario = ScenarioFactory.create_scenario("one_vs_one")
        
        # 设置简单配置
        config = {
            "radar": {
                "id": "test_radar",
                "name": "测试雷达",
                "lat": 39.9,
                "lon": 116.4,
                "alt": 50.0,
                "frequency": 3.0,
                "power": 100.0
            },
            "jammer": {
                "id": "test_jammer",
                "name": "测试干扰机",
                "lat": 40.0,
                "lon": 116.5,
                "alt": 10000.0,
                "power": 1000.0
            }
        }
        
        # 1. 设置想定
        scenario.setup(config)
        
        # 验证实体创建
        assert len(scenario.radars) == 1
        assert len(scenario.jammers) == 1
        
        # 2. 执行仿真
        results = scenario.execute()
        
        # 验证仿真结果
        assert "scenario" in results
        assert "radar" in results
        assert "jammer" in results
        assert "result" in results
        
        # 3. 评估结果
        assessment = scenario.assess()
        
        # 验证评估结果
        assert "jam_success_rate" in assessment
        assert "detection_probability" in assessment
        assert "j_s_ratio" in assessment
        assert "suggested_tactics" in assessment
    
    def test_multiple_scenarios(self):
        """测试多个想定"""
        scenarios = ["one_vs_one", "many_vs_one", "many_vs_many"]
        
        for scenario_type in scenarios:
            # 创建想定
            scenario = ScenarioFactory.create_scenario(scenario_type)
            
            # 验证想定类型
            if scenario_type == "one_vs_one":
                from src.core.patterns.strategy import OneVsOneScenario
                assert isinstance(scenario, OneVsOneScenario)
            elif scenario_type == "many_vs_one":
                from src.core.patterns.strategy import ManyVsOneScenario
                assert isinstance(scenario, ManyVsOneScenario)
            elif scenario_type == "many_vs_many":
                from src.core.patterns.strategy import ManyVsManyScenario
                assert isinstance(scenario, ManyVsManyScenario)
            
            # 验证想定名称
            assert scenario.name is not None
            assert scenario.description is not None
    
    def test_entity_serialization(self):
        """测试实体序列化"""
        from src.core.entities import Radar, Position, RadarParameters
        
        # 创建雷达实体
        pos = Position(39.9, 116.4, 50.0)
        radar_params = RadarParameters(
            frequency=3.0,
            power=100.0,
            gain=40.0,
            beamwidth=1.5
        )
        
        radar = Radar(
            id="test_radar",
            name="测试雷达",
            position=pos,
            radar_params=radar_params
        )
        
        # 序列化为字典
        radar_dict = radar.to_dict()
        
        # 验证序列化结果
        assert radar_dict["id"] == "test_radar"
        assert radar_dict["name"] == "测试雷达"
        assert radar_dict["position"]["lat"] == 39.9
        assert radar_dict["position"]["lon"] == 116.4
        assert radar_dict["position"]["alt"] == 50.0
        assert radar_dict["parameters"]["frequency"] == 3.0
        assert radar_dict["parameters"]["power"] == 100.0
