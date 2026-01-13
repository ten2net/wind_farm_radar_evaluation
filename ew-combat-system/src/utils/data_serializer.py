# 文件: src/utils/data_serializer.py
"""
数据序列化工具
处理EnhancedRadar等自定义对象的序列化
"""

import json
import pickle
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np
from pathlib import Path

class DataSerializer:
    """数据序列化工具类"""
    
    @staticmethod
    def serialize_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
        """序列化场景数据"""
        try:
            serialized = scenario.copy()
            
            # 序列化雷达列表
            if 'radars' in serialized:
                serialized['radars'] = [DataSerializer.serialize_radar(radar) 
                                      for radar in serialized['radars']]
            
            # 确保所有数据都是可序列化的
            return DataSerializer._make_serializable(serialized)
            
        except Exception as e:
            raise ValueError(f"序列化场景失败: {e}")
    
    @staticmethod
    def serialize_radar(radar) -> Dict[str, Any]:
        """序列化雷达对象"""
        if hasattr(radar, 'to_dict'):
            return radar.to_dict()
        elif isinstance(radar, dict):
            return radar
        else:
            # 尝试获取属性
            return {
                'id': getattr(radar, 'id', 'unknown'),
                'name': getattr(radar, 'name', 'unknown'),
                'position': getattr(radar, 'position', {}),
                'frequency': getattr(radar, 'frequency', 0),
                'power': getattr(radar, 'power', 0),
                'current_stage': getattr(radar, 'current_stage', 'search'),
                'warning': 'auto_serialized'
            }
    
    @staticmethod
    def _make_serializable(obj: Any) -> Any:
        """确保对象可序列化"""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: DataSerializer._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [DataSerializer._make_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64)): # type: ignore
            return int(obj)
        elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)): # type: ignore
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return DataSerializer._make_serializable(obj.__dict__)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            # 无法序列化的对象转换为字符串
            return str(obj)
    
    @staticmethod
    def save_to_json(data: Any, filepath: str, indent: int = 2) -> bool:
        """保存数据到JSON文件"""
        try:
            filepath = Path(filepath) # type: ignore
            filepath.parent.mkdir(parents=True, exist_ok=True) # type: ignore
            
            serialized_data = DataSerializer._make_serializable(data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, indent=indent, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存JSON失败: {e}")
            return False
    
    @staticmethod
    def load_from_json(filepath: str) -> Any:
        """从JSON文件加载数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载JSON失败: {e}")
            return None