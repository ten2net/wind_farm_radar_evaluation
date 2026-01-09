"""
设计模式单元测试
"""
import pytest
from src.core.patterns.strategy import (
    ScenarioFactory, 
    OneVsOneScenario, 
    ManyVsOneScenario, 
    ManyVsManyScenario
)
from src.core.patterns.factory import EntityFactory
from src.core.patterns.observer import SimulationSubject, StatusObserver, ResultsObserver

class TestScenarioFactory:
    """测试想定工厂"""
    
    def test_create_scenario(self):
        """测试想定创建"""
        # 测试一对一对抗
        scenario = ScenarioFactory.create_scenario("one_vs_one")
        assert isinstance(scenario, OneVsOneScenario)
        assert scenario.name == "一对一对抗"
        
        # 测试多对一对抗
        scenario = ScenarioFactory.create_scenario("many_vs_one")
        assert isinstance(scenario, ManyVsOneScenario)
        assert scenario.name == "多对一对抗"
        
        # 测试多对多对抗
        scenario = ScenarioFactory.create_scenario("many_vs_many")
        assert isinstance(scenario, ManyVsManyScenario)
        assert scenario.name == "多对多对抗"
    
    def test_invalid_scenario_type(self):
        """测试无效的想定类型"""
        with pytest.raises(ValueError) as exc_info:
            ScenarioFactory.create_scenario("invalid_type")
        
        assert "未知的想定类型" in str(exc_info.value)
    
    def test_get_available_scenarios(self):
        """测试获取可用想定"""
        scenarios = ScenarioFactory.get_available_scenarios()
        
        assert len(scenarios) == 3
        
        # 验证想定信息
        scenario_ids = [s["id"] for s in scenarios]
        assert "one_vs_one" in scenario_ids
        assert "many_vs_one" in scenario_ids
        assert "many_vs_many" in scenario_ids
        
        for scenario in scenarios:
            assert "id" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "icon" in scenario

class TestOneVsOneScenario:
    """测试一对一对抗想定"""
    
    def test_scenario_setup(self):
        """测试想定设置"""
        scenario = OneVsOneScenario()
        
        config = {
            "radar": {
                "id": "radar_001",
                "name": "测试雷达",
                "lat": 39.9,
                "lon": 116.4,
                "alt": 50.0,
                "frequency": 3.0,
                "power": 100.0
            },
            "jammer": {
                "id": "jammer_001",
                "name": "测试干扰机",
                "lat": 40.0,
                "lon": 116.5,
                "alt": 10000.0,
                "power": 1000.0,
                "beamwidth": 60.0
            }
        }
        
        scenario.setup(config)
        
        # 验证实体创建
        assert len(scenario.radars) == 1
        assert len(scenario.jammers) == 1
        
        radar = scenario.radars[0]
        jammer = scenario.jammers[0]
        
        assert radar.id == "radar_001"
        assert radar.name == "测试雷达"
        assert jammer.id == "jammer_001"
        assert jammer.name == "测试干扰机"
    
    def test_scenario_execution(self):
        """测试想定执行"""
        scenario = OneVsOneScenario()
        
        # 设置简单配置
        config = {
            "radar": {
                "id": "radar_001",
                "name": "测试雷达",
                "lat": 39.9,
                "lon": 116.4
            },
            "jammer": {
                "id": "jammer_001",
                "name": "测试干扰机",
                "lat": 40.0,
                "lon": 116.5
            }
        }
        
        scenario.setup(config)
        result = scenario.execute()
        
        # 验证结果结构
        assert "scenario" in result
        assert "radar" in result
        assert "jammer" in result
        assert "result" in result
        
        assert result["scenario"] == "一对一对抗"
    
    def test_scenario_assessment(self):
        """测试想定评估"""
        scenario = OneVsOneScenario()
        
        config = {
            "radar": {
                "id": "radar_001",
                "name": "测试雷达",
                "lat": 39.9,
                "lon": 116.4
            },
            "jammer": {
                "id": "jammer_001",
                "name": "测试干扰机",
                "lat": 40.0,
                "lon": 116.5
            }
        }
        
        scenario.setup(config)
        assessment = scenario.assess()
        
        # 验证评估结果
        assert "jam_success_rate" in assessment
        assert "detection_probability" in assessment
        assert "j_s_ratio" in assessment
        assert "suggested_tactics" in assessment
        
        assert isinstance(assessment["suggested_tactics"], list)

class TestManyVsOneScenario:
    """测试多对一对抗想定"""
    
    def test_scenario_setup(self):
        """测试想定设置"""
        scenario = ManyVsOneScenario()
        
        config = {
            "radars": [
                {
                    "id": "radar_001",
                    "name": "雷达1",
                    "lat": 39.9,
                    "lon": 116.4
                },
                {
                    "id": "radar_002",
                    "name": "雷达2",
                    "lat": 40.0,
                    "lon": 116.5
                }
            ],
            "jammer": {
                "id": "jammer_001",
                "name": "测试干扰机",
                "lat": 40.1,
                "lon": 116.6
            }
        }
        
        scenario.setup(config)
        
        # 验证实体创建
        assert len(scenario.radars) == 2
        assert len(scenario.jammers) == 1
        
        assert scenario.radars[0].id == "radar_001"
        assert scenario.radars[1].id == "radar_002"
        assert scenario.jammers[0].id == "jammer_001"

class TestManyVsManyScenario:
    """测试多对多对抗想定"""
    
    def test_scenario_setup(self):
        """测试想定设置"""
        scenario = ManyVsManyScenario()
        
        config = {
            "radar_network": [
                {
                    "id": "radar_001",
                    "name": "雷达1",
                    "lat": 39.9,
                    "lon": 116.4
                },
                {
                    "id": "radar_002",
                    "name": "雷达2",
                    "lat": 40.0,
                    "lon": 116.5
                }
            ],
            "jammer_network": [
                {
                    "id": "jammer_001",
                    "name": "干扰机1",
                    "lat": 40.1,
                    "lon": 116.6
                },
                {
                    "id": "jammer_002",
                    "name": "干扰机2",
                    "lat": 40.2,
                    "lon": 116.7
                }
            ]
        }
        
        scenario.setup(config)
        
        # 验证实体创建
        assert len(scenario.radars) == 2
        assert len(scenario.jammers) == 2
        
        assert scenario.radars[0].id == "radar_001"
        assert scenario.radars[1].id == "radar_002"
        assert scenario.jammers[0].id == "jammer_001"
        assert scenario.jammers[1].id == "jammer_002"

class TestEntityFactory:
    """测试实体工厂"""
    
    def test_create_radar(self):
        """测试创建雷达"""
        config = {
            "id": "test_radar",
            "name": "测试雷达",
            "lat": 39.9,
            "lon": 116.4,
            "alt": 50.0,
            "frequency": 3.0,
            "power": 100.0,
            "gain": 40.0,
            "beamwidth": 1.5
        }
        
        radar = EntityFactory.create_radar(config)
        
        assert radar.id == "test_radar"
        assert radar.name == "测试雷达"
        assert radar.position.lat == 39.9
        assert radar.position.lon == 116.4
        assert radar.radar_params.frequency == 3.0
        assert radar.radar_params.power == 100.0
    
    def test_create_jammer(self):
        """测试创建干扰机"""
        config = {
            "id": "test_jammer",
            "name": "测试干扰机",
            "lat": 40.0,
            "lon": 116.5,
            "alt": 10000.0,
            "power": 1000.0,
            "gain": 15.0,
            "beamwidth": 60.0,
            "jam_types": ["阻塞", "扫频"]
        }
        
        jammer = EntityFactory.create_jammer(config)
        
        assert jammer.id == "test_jammer"
        assert jammer.name == "测试干扰机"
        assert jammer.position.lat == 40.0
        assert jammer.position.lon == 116.5
        assert jammer.jammer_params.power == 1000.0
        assert jammer.jammer_params.beamwidth == 60.0
    
    def test_create_target(self):
        """测试创建目标"""
        config = {
            "id": "test_target",
            "name": "测试目标",
            "type": "aircraft",
            "lat": 40.0,
            "lon": 116.5,
            "alt": 10000.0,
            "rcs": 5.0,
            "speed": 300.0
        }
        
        target = EntityFactory.create_target(config)
        
        assert target.id == "test_target"
        assert target.name == "测试目标"
        assert target.position.lat == 40.0
        assert target.position.lon == 116.5
        assert target.rcs == 5.0
        assert target.speed == 300.0

class TestObserverPattern:
    """测试观察者模式"""
    
    def test_observer_attachment(self):
        """测试观察者附加"""
        subject = SimulationSubject()
        observer = StatusObserver()
        
        subject.attach(observer)
        
        # 验证观察者已被附加
        assert observer in subject._observers
    
    def test_observer_detachment(self):
        """测试观察者分离"""
        subject = SimulationSubject()
        observer = StatusObserver()
        
        subject.attach(observer)
        subject.detach(observer)
        
        # 验证观察者已被分离
        assert observer not in subject._observers
    
    def test_notification(self):
        """测试通知机制"""
        subject = SimulationSubject()
        observer = StatusObserver()
        
        subject.attach(observer)
        
        # 发送通知
        event = {
            "event": "test_event",
            "data": "test_data"
        }
        subject.notify(event)
        
        # 验证观察者接收到通知
        assert len(observer.status_history) > 0
        assert observer.status_history[-1]["event"] == "test_event"
    
    def test_results_observer(self):
        """测试结果观察者"""
        subject = SimulationSubject()
        observer = ResultsObserver()
        
        subject.attach(observer)
        
        # 发送完成通知
        results = {"test": "results"}
        subject.complete_simulation(results)
        
        # 验证结果观察者接收到结果
        assert len(observer.results) > 0
        assert observer.results[-1]["results"] == results
