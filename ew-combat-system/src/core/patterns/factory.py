"""
工厂模式：实体创建
"""
from typing import Dict, Any
from ..entities import Entity, Radar, Jammer, Position, RadarParameters, JammerParameters
import yaml

class EntityFactory:
    """实体工厂"""
    
    @staticmethod
    def create_entity(entity_type: str, config: Dict[str, Any]) -> Entity:
        """创建实体"""
        if entity_type == "radar":
            return EntityFactory.create_radar(config)
        elif entity_type == "jammer":
            return EntityFactory.create_jammer(config)
        elif entity_type == "target":
            return EntityFactory.create_target(config)
        else:
            raise ValueError(f"未知的实体类型: {entity_type}")
    
    @staticmethod
    def create_radar(config: Dict[str, Any]) -> Radar:
        """创建雷达"""
        # 从配置中提取参数
        position = Position(
            lat=config.get("lat", 0.0),
            lon=config.get("lon", 0.0),
            alt=config.get("alt", 0.0)
        )
        
        radar_params = RadarParameters(
            frequency=config.get("frequency", 3.0),
            power=config.get("power", 100.0),
            gain=config.get("gain", 40.0),
            beamwidth=config.get("beamwidth", 1.5),
            pulse_width=config.get("pulse_width", 1.0),
            prf=config.get("prf", 1000.0),
            sensitivity=config.get("sensitivity", -120.0),
            range_max=config.get("range_max", 300.0),
            altitude_max=config.get("altitude_max", 25000.0),
            scan_pattern=config.get("scan_pattern", "circular"),
            scan_rate=config.get("scan_rate", 6.0)
        )
        
        return Radar(
            id=config.get("id", "radar_001"),
            name=config.get("name", "未知雷达"),
            position=position,
            radar_params=radar_params
        )
    
    @staticmethod
    def create_jammer(config: Dict[str, Any]) -> Jammer:
        """创建干扰机"""
        position = Position(
            lat=config.get("lat", 0.0),
            lon=config.get("lon", 0.0),
            alt=config.get("alt", 0.0)
        )
        
        jammer_params = JammerParameters(
            frequency_range=config.get("frequency_range", (0.5, 18.0)),
            power=config.get("power", 1000.0),
            gain=config.get("gain", 15.0),
            beamwidth=config.get("beamwidth", 60.0),
            eirp=config.get("eirp", 80.0),
            jam_types=config.get("jam_types", ["阻塞", "扫频"]),
            response_time=config.get("response_time", 2.0),
            bandwidth=config.get("bandwidth", 100.0)
        )
        
        return Jammer(
            id=config.get("id", "jammer_001"),
            name=config.get("name", "未知干扰机"),
            position=position,
            jammer_params=jammer_params
        )
    
    @staticmethod
    def create_target(config: Dict[str, Any]):
        """创建目标"""
        from ..entities.target import Aircraft, Missile, Ship
        
        target_type = config.get("type", "aircraft")
        position = Position(
            lat=config.get("lat", 0.0),
            lon=config.get("lon", 0.0),
            alt=config.get("alt", 0.0)
        )
        
        if target_type == "aircraft":
            return Aircraft(
                id=config.get("id", "aircraft_001"),
                name=config.get("name", "未知飞机"),
                position=position,
                rcs=config.get("rcs", 5.0),
                speed=config.get("speed", 300.0),
                altitude=config.get("altitude", 10000.0)
            )
        elif target_type == "missile":
            return Missile(
                id=config.get("id", "missile_001"),
                name=config.get("name", "未知导弹"),
                position=position,
                rcs=config.get("rcs", 0.1),
                speed=config.get("speed", 800.0),
                altitude=config.get("altitude", 1000.0)
            )
        elif target_type == "ship":
            return Ship(
                id=config.get("id", "ship_001"),
                name=config.get("name", "未知舰船"),
                position=position,
                rcs=config.get("rcs", 5000.0),
                speed=config.get("speed", 15.0)
            )
        else:
            raise ValueError(f"未知的目标类型: {target_type}")
