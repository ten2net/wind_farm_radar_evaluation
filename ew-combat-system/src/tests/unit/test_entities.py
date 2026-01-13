"""
实体类单元测试
"""
import pytest
import numpy as np
from src.core.entities import Position, RadarParameters, JammerParameters, Radar, Jammer
from src.core.entities.target import Aircraft, Missile, Ship

class TestPosition:
    """测试Position类"""
    
    def test_position_creation(self):
        """测试位置创建"""
        pos = Position(39.9, 116.4, 100.0)
        assert pos.lat == 39.9
        assert pos.lon == 116.4
        assert pos.alt == 100.0
    
    def test_position_to_array(self):
        """测试转换为数组"""
        pos = Position(39.9, 116.4, 100.0)
        arr = pos.to_array()
        assert np.array_equal(arr, np.array([39.9, 116.4, 100.0]))
    
    def test_distance_calculation(self):
        """测试距离计算"""
        pos1 = Position(39.9, 116.4, 0)
        pos2 = Position(40.0, 116.5, 0)
        
        distance = pos1.distance_to(pos2)
        assert distance > 0
        assert isinstance(distance, float)

class TestRadarParameters:
    """测试RadarParameters类"""
    
    def test_radar_params_creation(self):
        """测试雷达参数创建"""
        params = RadarParameters(
            frequency=3.0,
            power=100.0,
            gain=40.0,
            beamwidth=1.5
        )
        
        assert params.frequency == 3.0
        assert params.power == 100.0
        assert params.gain == 40.0
        assert params.beamwidth == 1.5
    
    def test_wavelength_calculation(self):
        """测试波长计算"""
        params = RadarParameters(frequency=3.0, power=100, gain=40, beamwidth=1.5)
        wavelength = params.wavelength()
        
        # 3 GHz对应的波长约为0.1米
        assert wavelength > 0.09 and wavelength < 0.11
    
    def test_effective_range(self):
        """测试有效距离计算"""
        params = RadarParameters(
            frequency=3.0,
            power=100.0,
            gain=40.0,
            beamwidth=1.5,
            sensitivity=-120.0
        )
        
        range_km = params.effective_range()
        assert range_km > 0
        assert isinstance(range_km, float)

class TestJammerParameters:
    """测试JammerParameters类"""
    
    def test_jammer_params_creation(self):
        """测试干扰机参数创建"""
        params = JammerParameters(
            frequency_range=(0.5, 18.0),
            power=1000.0,
            gain=15.0,
            beamwidth=60.0,
            eirp=80.0,
            jam_types=["阻塞", "扫频"],
            response_time=2.0
        )
        
        assert params.power == 1000.0
        assert params.gain == 15.0
        assert params.beamwidth == 60.0
        assert "阻塞" in params.jam_types
    
    def test_effective_radiated_power(self):
        """测试有效辐射功率计算"""
        params = JammerParameters(
            frequency_range=(0.5, 18.0),
            power=1000.0,
            gain=15.0,
            beamwidth=60.0,
            eirp=80.0,
            jam_types=["阻塞"],
            response_time=2.0
        )
        
        erp = params.effective_radiated_power()
        assert erp > 0
        assert isinstance(erp, float)

class TestRadarEntity:
    """测试Radar实体类"""
    
    def test_radar_creation(self):
        """测试雷达实体创建"""
        pos = Position(39.9, 116.4, 50.0)
        radar_params = RadarParameters(
            frequency=3.0,
            power=100.0,
            gain=40.0,
            beamwidth=1.5
        )
        
        radar = Radar(
            id="radar_001",
            name="测试雷达",
            position=pos,
            radar_params=radar_params
        )
        
        assert radar.id == "radar_001"
        assert radar.name == "测试雷达"
        assert radar.position == pos
        assert radar.radar_params == radar_params
    
    def test_radar_to_dict(self):
        """测试雷达转换为字典"""
        pos = Position(39.9, 116.4, 50.0)
        radar_params = RadarParameters(
            frequency=3.0,
            power=100.0,
            gain=40.0,
            beamwidth=1.5
        )
        
        radar = Radar(
            id="radar_001",
            name="测试雷达",
            position=pos,
            radar_params=radar_params
        )
        
        radar_dict = radar.to_dict()
        assert isinstance(radar_dict, dict)
        assert radar_dict["id"] == "radar_001"
        assert radar_dict["name"] == "测试雷达"

class TestJammerEntity:
    """测试Jammer实体类"""
    
    def test_jammer_creation(self):
        """测试干扰机实体创建"""
        pos = Position(40.0, 116.5, 10000.0)
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
            id="jammer_001",
            name="测试干扰机",
            position=pos,
            jammer_params=jammer_params
        )
        
        assert jammer.id == "jammer_001"
        assert jammer.name == "测试干扰机"
        assert jammer.position == pos
        assert jammer.jammer_params == jammer_params
    
    def test_jammer_to_dict(self):
        """测试干扰机转换为字典"""
        pos = Position(40.0, 116.5, 10000.0)
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
            id="jammer_001",
            name="测试干扰机",
            position=pos,
            jammer_params=jammer_params
        )
        
        jammer_dict = jammer.to_dict()
        assert isinstance(jammer_dict, dict)
        assert jammer_dict["id"] == "jammer_001"
        assert jammer_dict["name"] == "测试干扰机"

class TestTargetEntities:
    """测试目标实体类"""
    
    def test_aircraft_creation(self):
        """测试飞机实体创建"""
        pos = Position(40.0, 116.5, 10000.0)
        
        aircraft = Aircraft(
            id="ac_001",
            name="测试飞机",
            position=pos,
            rcs=5.0,
            speed=300.0
        )
        
        assert aircraft.id == "ac_001"
        assert aircraft.name == "测试飞机"
        assert aircraft.rcs == 5.0
        assert aircraft.speed == 300.0
    
    def test_missile_creation(self):
        """测试导弹实体创建"""
        pos = Position(40.1, 116.6, 1000.0)
        
        missile = Missile(
            id="missile_001",
            name="测试导弹",
            position=pos,
            rcs=0.1,
            speed=800.0
        )
        
        assert missile.id == "missile_001"
        assert missile.name == "测试导弹"
        assert missile.rcs == 0.1
        assert missile.speed == 800.0
    
    def test_ship_creation(self):
        """测试舰船实体创建"""
        pos = Position(40.2, 116.7, 0.0)
        
        ship = Ship(
            id="ship_001",
            name="测试舰船",
            position=pos,
            rcs=5000.0,
            speed=15.0
        )
        
        assert ship.id == "ship_001"
        assert ship.name == "测试舰船"
        assert ship.rcs == 5000.0
        assert ship.speed == 15.0
