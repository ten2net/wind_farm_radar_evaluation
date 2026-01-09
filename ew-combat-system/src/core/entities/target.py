"""
目标实体实现
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np
from . import Entity, Position, EntityType, EntityState

@dataclass
class Aircraft(Entity):
    """飞机目标"""
    rcs: float = 5.0
    speed: float = 300.0
    altitude: float = 10000.0
    heading: float = 0.0
    fuel: float = 100.0
    weapons: List[str] = None
    
    def __post_init__(self):
        self.entity_type = EntityType.TARGET
        if self.weapons is None:
            self.weapons = []
    
    def update(self, dt: float):
        """更新飞机状态"""
        # 简化的运动模型
        self.position.lat += (self.speed * dt / 111000) * np.cos(np.radians(self.heading))
        self.position.lon += (self.speed * dt / (111000 * np.cos(np.radians(self.position.lat)))) * np.sin(np.radians(self.heading))
        
        # 燃料消耗
        self.fuel -= 0.1 * dt
        if self.fuel <= 0:
            self.state = EntityState.DESTROYED
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": "aircraft",
            "position": self.position.__dict__,
            "rcs": self.rcs,
            "speed": self.speed,
            "altitude": self.altitude,
            "fuel": self.fuel
        }

@dataclass
class Missile(Entity):
    """导弹目标"""
    rcs: float = 0.1
    speed: float = 800.0
    altitude: float = 1000.0
    heading: float = 0.0
    fuel: float = 100.0
    guidance_type: str = "INS"
    
    def __post_init__(self):
        self.entity_type = EntityType.TARGET
    
    def update(self, dt: float):
        """更新导弹状态"""
        self.position.lat += (self.speed * dt / 111000) * np.cos(np.radians(self.heading))
        self.position.lon += (self.speed * dt / (111000 * np.cos(np.radians(self.position.lat)))) * np.sin(np.radians(self.heading))
        
        # 燃料消耗
        self.fuel -= 0.5 * dt
        if self.fuel <= 0:
            self.state = EntityState.DESTROYED
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": "missile",
            "position": self.position.__dict__,
            "rcs": self.rcs,
            "speed": self.speed,
            "altitude": self.altitude,
            "guidance_type": self.guidance_type
        }

@dataclass
class Ship(Entity):
    """舰船目标"""
    rcs: float = 5000.0
    speed: float = 15.0
    heading: float = 0.0
    ship_type: str = "destroyer"
    displacement: float = 8000.0
    
    def __post_init__(self):
        self.entity_type = EntityType.TARGET
    
    def update(self, dt: float):
        """更新舰船状态"""
        self.position.lat += (self.speed * dt / 111000) * np.cos(np.radians(self.heading))
        self.position.lon += (self.speed * dt / (111000 * np.cos(np.radians(self.position.lat)))) * np.sin(np.radians(self.heading))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": "ship",
            "position": self.position.__dict__,
            "rcs": self.rcs,
            "speed": self.speed,
            "ship_type": self.ship_type
        }
