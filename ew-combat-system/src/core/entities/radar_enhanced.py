# 文件: src/core/entities/radar_enhanced.py
"""
可序列化的增强雷达实体
添加JSON序列化支持
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np

class EnhancedRadar:
    """增强雷达实体 - 支持JSON序列化"""
    
    def __init__(self, radar_id: str, name: str, position: Dict[str, float], 
                 frequency: float, power: float, advanced_level: int = 1):
        """初始化雷达"""
        self.id = radar_id
        self.name = name
        self.position = position
        self.frequency = frequency
        self.power = power
        self.advanced_level = advanced_level
        
        # 雷达阶段参数
        self.current_stage = 'search'
        self.stage_progress = 0.0
        self.performance_level = 1.0
        self.interruption_threshold = 0.3
        
        # 阶段持续时间
        self.stage_duration = {
            'search': 30.0,
            'acquisition': 10.0,
            'tracking': 60.0,
            'guidance': 20.0
        }
        
        # 动态属性
        self.radar_type = None
        self.stage_history = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式 - 支持JSON序列化"""
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'frequency': self.frequency,
            'power': self.power,
            'advanced_level': self.advanced_level,
            'current_stage': self.current_stage,
            'stage_progress': self.stage_progress,
            'performance_level': self.performance_level,
            'interruption_threshold': self.interruption_threshold,
            'stage_duration': self.stage_duration,
            'radar_type': self.radar_type,
            'stage_history': self.stage_history,
            'class_name': 'EnhancedRadar'  # 用于反序列化识别
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedRadar':
        """从字典创建雷达对象"""
        radar = cls(
            radar_id=data['id'],
            name=data['name'],
            position=data['position'],
            frequency=data['frequency'],
            power=data['power'],
            advanced_level=data.get('advanced_level', 1)
        )
        
        # 恢复其他属性
        radar.current_stage = data.get('current_stage', 'search')
        radar.stage_progress = data.get('stage_progress', 0.0)
        radar.performance_level = data.get('performance_level', 1.0)
        radar.interruption_threshold = data.get('interruption_threshold', 0.3)
        radar.stage_duration = data.get('stage_duration', {
            'search': 30.0, 'acquisition': 10.0, 'tracking': 60.0, 'guidance': 20.0
        })
        radar.radar_type = data.get('radar_type')
        radar.stage_history = data.get('stage_history', [])
        
        return radar
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def __repr__(self) -> str:
        return f"EnhancedRadar(id='{self.id}', name='{self.name}', stage='{self.current_stage}')"

class EnhancedRadarEncoder(json.JSONEncoder):
    """EnhancedRadar的JSON编码器"""
    
    def default(self, o):
        obj = o
        if isinstance(obj, EnhancedRadar):
            return obj.to_dict()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)