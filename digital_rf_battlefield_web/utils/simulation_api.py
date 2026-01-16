"""
仿真API工具 - 与后端仿真引擎交互
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SimulationEngine:
    """仿真引擎客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化仿真引擎客户端"""
        self.base_url = base_url
        self.session_id = None
        self.is_initialized = False
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化仿真引擎"""
        try:
            response = requests.post(
                f"{self.base_url}/api/simulation/initialize",
                json=config,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                self.is_initialized = True
                logger.info(f"仿真引擎初始化成功，会话ID: {self.session_id}")
                return True
            else:
                logger.error(f"初始化失败: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"初始化请求失败: {e}")
            return False
    
    def step(self) -> Dict[str, Any]:
        """执行一步仿真"""
        if not self.is_initialized or not self.session_id:
            return {"error": "仿真引擎未初始化"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/simulation/step",
                json={"session_id": self.session_id},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"执行步骤失败: {response.text}")
                return {"error": response.text}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"执行步骤请求失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取仿真状态"""
        if not self.session_id:
            return {"status": "未初始化"}
        
        try:
            response = requests.get(
                f"{self.base_url}/api/simulation/status/{self.session_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "未知", "error": response.text}
                
        except requests.exceptions.RequestException:
            return {"status": "连接失败"}
    
    def stop(self) -> bool:
        """停止仿真"""
        if not self.session_id:
            return True
        
        try:
            response = requests.post(
                f"{self.base_url}/api/simulation/stop",
                json={"session_id": self.session_id},
                timeout=5
            )
            
            if response.status_code == 200:
                self.is_initialized = False
                logger.info("仿真已停止")
                return True
            else:
                logger.error(f"停止仿真失败: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"停止仿真请求失败: {e}")
            return False
    
    def get_results(self) -> Dict[str, Any]:
        """获取仿真结果"""
        if not self.session_id:
            return {}
        
        try:
            response = requests.get(
                f"{self.base_url}/api/simulation/results/{self.session_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取结果失败: {e}")
            return {}

# 本地仿真引擎实现（当后端不可用时使用）
class LocalSimulationEngine:
    """本地仿真引擎（模拟）"""
    
    def __init__(self):
        self.current_time = 0.0
        self.is_running = False
        self.radar_data = []
        self.target_data = []
        self.detections = []
        self.tracks = []
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化仿真引擎"""
        logger.info("初始化本地仿真引擎")
        
        # 解析配置
        self.radar_configs = config.get('radars', [])
        self.target_configs = config.get('targets', [])
        sim_config = config.get('simulation', {})
        
        self.time_settings = sim_config.get('time_settings', {})
        self.environment = sim_config.get('environment', {})
        self.performance = sim_config.get('performance', {})
        
        # 初始化数据
        self.initialize_data()
        
        self.is_running = True
        return True
    
    def initialize_data(self):
        """初始化数据"""
        # 初始化雷达数据
        self.radar_data = []
        for radar in self.radar_configs:
            self.radar_data.append({
                'id': radar.get('id'),
                'name': radar.get('name'),
                'type': radar.get('type'),
                'position': radar.get('position', [0, 0]),
                'range_km': radar.get('range_km', 100),
                'status': 'active',
                'load': 0.0,
                'detections': 0
            })
        
        # 初始化目标数据
        self.target_data = []
        for target in self.target_configs:
            self.target_data.append({
                'id': target.get('id'),
                'name': target.get('name'),
                'type': target.get('type'),
                'position': target.get('position', [0, 0]),
                'altitude_m': target.get('altitude_m', 10000),
                'speed_kts': target.get('speed_kts', 300),
                'heading_deg': target.get('heading_deg', 0),
                'rcs_m2': target.get('rcs_m2', 1.0),
                'status': 'active'
            })
    
    def step(self) -> Dict[str, Any]:
        """执行一步仿真"""
        if not self.is_running:
            return {"error": "仿真未运行"}
        
        # 更新时间
        time_step = self.time_settings.get('time_step', 0.1)
        self.current_time += time_step
        
        # 更新目标位置
        self.update_targets(time_step)
        
        # 执行检测
        self.perform_detections()
        
        # 执行跟踪
        self.perform_tracking()
        
        # 计算性能指标
        performance_metrics = self.calculate_metrics()
        
        return {
            'current_time': self.current_time,
            'radar_data': self.radar_data,
            'target_data': self.target_data,
            'detections': self.detections,
            'tracks': self.tracks,
            'performance_metrics': performance_metrics
        }
    
    def update_targets(self, time_step: float):
        """更新目标位置"""
        for target in self.target_data:
            # 简单运动模型
            speed_m_s = target['speed_kts'] * 0.514444  # 节转换为m/s
            heading_rad = np.radians(target['heading_deg'])
            
            # 更新位置（简化计算）
            lat, lon = target['position']
            lat += (speed_m_s * np.sin(heading_rad) * time_step) / 111320
            lon += (speed_m_s * np.cos(heading_rad) * time_step) / (111320 * np.cos(np.radians(lat)))
            
            target['position'] = [lat, lon]
            
            # 随机变化航向
            if np.random.random() < 0.1:
                target['heading_deg'] = (target['heading_deg'] + np.random.uniform(-5, 5)) % 360
    
    def perform_detections(self):
        """执行检测"""
        self.detections = []
        
        for radar in self.radar_data:
            radar_detections = 0
            
            for target in self.target_data:
                # 计算距离
                lat1, lon1 = radar['position']
                lat2, lon2 = target['position']
                
                distance = self.calculate_distance(lat1, lon1, lat2, lon2)
                
                # 判断是否在探测范围内
                if distance <= radar['range_km']:
                    # 计算检测概率
                    detection_prob = self.calculate_detection_probability(distance, target['rcs_m2'])
                    
                    if np.random.random() < detection_prob:
                        # 添加检测
                        detection = {
                            'radar_id': radar['id'],
                            'target_id': target['id'],
                            'position': target['position'],
                            'distance_km': distance,
                            'snr_db': 20 - 10 * np.log10(distance + 1),
                            'timestamp': self.current_time
                        }
                        self.detections.append(detection)
                        radar_detections += 1
            
            # 更新雷达状态
            radar['detections'] = radar_detections
            radar['load'] = min(1.0, radar_detections / 10.0)  # 简化负载计算
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（简化）"""
        # 使用Haversine公式的简化版本
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return 6371 * c  # 地球半径6371km
    
    def calculate_detection_probability(self, distance: float, rcs: float) -> float:
        """计算检测概率"""
        # 简化模型
        max_range = 200  # 最大探测距离
        base_prob = 0.9  # 基础检测概率
        
        if distance > max_range:
            return 0.0
        
        # 距离衰减
        distance_factor = 1.0 - (distance / max_range) ** 2
        
        # RCS影响
        rcs_factor = min(1.0, rcs / 10.0)
        
        return base_prob * distance_factor * rcs_factor
    
    def perform_tracking(self):
        """执行跟踪"""
        # 简化跟踪算法
        self.tracks = []
        
        for detection in self.detections:
            # 检查是否有现有航迹
            track_found = False
            
            for track in self.tracks:
                if track['target_id'] == detection['target_id']:
                    # 更新现有航迹
                    track['positions'].append(detection['position'])
                    track['last_update'] = self.current_time
                    track_found = True
                    break
            
            if not track_found:
                # 创建新航迹
                track = {
                    'track_id': f"track_{len(self.tracks)+1:03d}",
                    'target_id': detection['target_id'],
                    'positions': [detection['position']],
                    'start_time': self.current_time,
                    'last_update': self.current_time,
                    'confidence': 0.8
                }
                self.tracks.append(track)
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        # 计算检测概率
        detection_prob = 0.0
        if self.target_data:
            detected_targets = len(set([d['target_id'] for d in self.detections]))
            detection_prob = detected_targets / len(self.target_data)
        
        # 计算虚警率（简化）
        false_alarm_rate = 1e-4 + np.random.normal(0, 1e-5)
        
        # 计算航迹连续性
        track_continuity = 0.9 + np.random.normal(0, 0.05)
        
        # 计算系统负载
        system_load = np.mean([r['load'] for r in self.radar_data]) if self.radar_data else 0.0
        
        return {
            'detection_probability': detection_prob,
            'false_alarm_rate': false_alarm_rate,
            'track_continuity': track_continuity,
            'system_load': system_load,
            'fps': 10.0,
            'cpu_usage': 0.6,
            'memory_usage': 0.5,
            'update_latency': 0.05
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取仿真状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'current_time': self.current_time,
            'num_radars': len(self.radar_data),
            'num_targets': len(self.target_data),
            'num_detections': len(self.detections),
            'num_tracks': len(self.tracks)
        }
    
    def stop(self) -> bool:
        """停止仿真"""
        self.is_running = False
        return True
    
    def get_results(self) -> Dict[str, Any]:
        """获取仿真结果"""
        return {
            'simulation_time': self.current_time,
            'radar_data': self.radar_data,
            'target_data': self.target_data,
            'detections': self.detections,
            'tracks': self.tracks,
            'performance_metrics': self.calculate_metrics()
        }

# 工厂函数
def get_simulation_engine(use_local: bool = True) -> SimulationEngine:
    """获取仿真引擎实例"""
    if use_local:
        return LocalSimulationEngine()
    else:
        return SimulationEngine()