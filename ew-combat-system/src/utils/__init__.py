"""
工具函数模块
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime

def load_config(config_path: str) -> Dict[str, Any]:
    """加载YAML配置文件"""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config or {}
    
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """保存配置到YAML文件"""
    try:
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def save_results(results: Dict[str, Any], filepath: str, format: str = "json") -> bool:
    """保存仿真结果"""
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            if "radar_results" in results:
                df = pd.DataFrame(results["radar_results"])
                df.to_csv(filepath, index=False, encoding='utf-8')
            else:
                raise ValueError("结果中没有可保存为CSV的数据")
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        return True
    except Exception as e:
        print(f"保存结果失败: {e}")
        return False

def load_results(filepath: str) -> Optional[Dict[str, Any]]:
    """加载仿真结果"""
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return None
        
        if filepath.suffix == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif filepath.suffix == '.csv':
            df = pd.read_csv(filepath)
            return {"radar_results": df.to_dict('records')}
        else:
            raise ValueError(f"不支持的格式: {filepath.suffix}")
    
    except Exception as e:
        print(f"加载结果失败: {e}")
        return None

def calculate_statistics(data: List[float]) -> Dict[str, float]:
    """计算统计数据"""
    if not data:
        return {}
    
    arr = np.array(data)
    
    stats = {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
        "q1": float(np.percentile(arr, 25)),
        "q3": float(np.percentile(arr, 75))
    }
    
    return stats

def format_lat_lon(lat: float, lon: float) -> str:
    """格式化经纬度显示"""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    
    lat_abs = abs(lat)
    lon_abs = abs(lon)
    
    return f"{lat_abs:.4f}°{lat_dir}, {lon_abs:.4f}°{lon_dir}"

def format_distance(distance_km: float) -> str:
    """格式化距离显示"""
    if distance_km < 1:
        return f"{distance_km*1000:.0f} m"
    elif distance_km < 1000:
        return f"{distance_km:.1f} km"
    else:
        return f"{distance_km/1000:.1f} Mm"

def format_power(power_w: float) -> str:
    """格式化功率显示"""
    if power_w < 1e-3:
        return f"{power_w*1e6:.1f} nW"
    elif power_w < 1:
        return f"{power_w*1e3:.1f} mW"
    elif power_w < 1e3:
        return f"{power_w:.1f} W"
    elif power_w < 1e6:
        return f"{power_w/1e3:.1f} kW"
    else:
        return f"{power_w/1e6:.1f} MW"

def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def create_unique_id(prefix: str = "id") -> str:
    """创建唯一ID"""
    timestamp = get_timestamp()
    random_str = np.random.randint(1000, 9999)
    return f"{prefix}_{timestamp}_{random_str}"

def validate_coordinates(lat: float, lon: float) -> bool:
    """验证坐标有效性"""
    return -90 <= lat <= 90 and -180 <= lon <= 180

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两点间的方位角"""
    from math import atan2, sin, cos, radians, degrees
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    
    bearing = atan2(x, y)
    bearing = degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing
