"""
仿真引擎 - 数字射频战场仿真系统的核心引擎
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time
import threading
import logging
from dataclasses import dataclass, field
from enum import Enum
import json

from .models import (
    SimulationConfig, RadarConfig, TargetConfig,
    DetectionResult, TrackResult, PerformanceMetrics
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulationState(Enum):
    """仿真状态枚举"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class SimulationData:
    """仿真数据容器"""
    detections: List[DetectionResult] = field(default_factory=list)
    tracks: List[TrackResult] = field(default_factory=list)
    performance_metrics: PerformanceMetrics = field(default_factory=dict)
    radar_data: List[Dict[str, Any]] = field(default_factory=list)
    target_data: List[Dict[str, Any]] = field(default_factory=list)
    time_series_data: List[Dict[str, Any]] = field(default_factory=list)

class SimulationEngine:
    """仿真引擎主类"""
    
    def __init__(self):
        """初始化仿真引擎"""
        self.state = SimulationState.STOPPED
        self.current_time = 0.0
        self.progress = 0.0
        self.simulation_config = None
        self.radars = []
        self.targets = []
        self.data = SimulationData()
        self.performance_history = []
        
        # 线程控制
        self.simulation_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()  # 初始为运行状态
        
        # 随机种子
        np.random.seed(42)
        
        logger.info("仿真引擎初始化完成")
    
    def initialize(self, config: SimulationConfig) -> bool:
        """初始化仿真"""
        try:
            self.simulation_config = config
            self.radars = []
            self.targets = []
            self.data = SimulationData()
            self.current_time = 0.0
            self.progress = 0.0
            self.state = SimulationState.INITIALIZED
            self.stop_event.clear()
            self.pause_event.set()
            
            logger.info(f"仿真初始化完成: {config.simulation_name}")
            return True
            
        except Exception as e:
            logger.error(f"仿真初始化失败: {e}")
            self.state = SimulationState.ERROR
            return False
    
    def add_radar(self, radar: RadarConfig) -> bool:
        """添加雷达"""
        try:
            self.radars.append(radar)
            logger.info(f"雷达添加成功: {radar.radar_name}")
            return True
        except Exception as e:
            logger.error(f"雷达添加失败: {e}")
            return False
    
    def add_target(self, target: TargetConfig) -> bool:
        """添加目标"""
        try:
            self.targets.append(target)
            logger.info(f"目标添加成功: {target.target_name}")
            return True
        except Exception as e:
            logger.error(f"目标添加失败: {e}")
            return False
    
    def run(self, config: Optional[SimulationConfig] = None) -> bool:
        """运行仿真"""
        if config:
            self.initialize(config)
        
        if self.state != SimulationState.INITIALIZED:
            logger.error("仿真未初始化")
            return False
        
        try:
            self.state = SimulationState.RUNNING
            self.stop_event.clear()
            self.pause_event.set()
            
            # 启动仿真线程
            self.simulation_thread = threading.Thread(
                target=self._run_simulation_loop,
                daemon=True
            )
            self.simulation_thread.start()
            
            logger.info("仿真开始运行")
            return True
            
        except Exception as e:
            logger.error(f"仿真启动失败: {e}")
            self.state = SimulationState.ERROR
            return False
    
    def _run_simulation_loop(self):
        """仿真主循环"""
        try:
            start_time = time.time()
            last_update_time = start_time
            
            while not self.stop_event.is_set() and self.current_time < self.simulation_config.duration:
                # 检查暂停
                self.pause_event.wait()
                
                # 计算时间步长
                current_real_time = time.time()
                real_time_elapsed = current_real_time - last_update_time
                simulation_time_elapsed = real_time_elapsed * self.simulation_config.real_time_factor
                
                # 更新仿真时间
                time_step = min(simulation_time_elapsed, self.simulation_config.time_step)
                self.current_time += time_step
                
                # 更新进度
                self.progress = self.current_time / self.simulation_config.duration
                
                # 执行仿真步骤
                self._simulation_step(time_step)
                
                # 记录性能数据
                if self.current_time % self.simulation_config.log_interval < time_step:
                    self._record_performance_data()
                
                # 更新上次更新时间
                last_update_time = current_real_time
                
                # 控制仿真速度
                if self.simulation_config.real_time_factor > 0:
                    time.sleep(max(0, time_step / self.simulation_config.real_time_factor - real_time_elapsed))
            
            # 仿真完成
            if self.current_time >= self.simulation_config.duration:
                self.state = SimulationState.COMPLETED
                logger.info("仿真完成")
            else:
                self.state = SimulationState.STOPPED
                logger.info("仿真停止")
                
        except Exception as e:
            logger.error(f"仿真运行错误: {e}")
            self.state = SimulationState.ERROR
    
    def _simulation_step(self, time_step: float):
        """执行仿真步骤"""
        # 更新目标位置
        self._update_targets(time_step)
        
        # 执行雷达检测
        self._perform_detections()
        
        # 执行目标跟踪
        self._perform_tracking()
        
        # 计算性能指标
        self._calculate_performance_metrics()
    
    def _update_targets(self, time_step: float):
        """更新目标位置"""
        for target in self.targets:
            # 简化运动模型
            speed_m_s = target.speed_kts * 0.514444  # 节转换为m/s
            heading_rad = np.radians(target.heading_deg)
            
            # 计算位移
            dx = speed_m_s * np.sin(heading_rad) * time_step
            dy = speed_m_s * np.cos(heading_rad) * time_step
            dz = target.vertical_rate * time_step
            
            # 更新位置（简化地理坐标计算）
            target.position.latitude += dx / 111320  # 1度纬度约111.32km
            target.position.longitude += dy / (111320 * np.cos(np.radians(target.position.latitude)))
            target.position.altitude += dz
            
            # 边界检查
            target.position.latitude = np.clip(target.position.latitude, -90, 90)
            target.position.longitude = np.clip(target.position.longitude, -180, 180)
            
            # 记录目标数据
            self.data.target_data.append({
                'target_id': target.target_id,
                'timestamp': self.current_time,
                'position': target.position.dict(),
                'speed_kts': target.speed_kts,
                'heading_deg': target.heading_deg,
                'altitude_m': target.position.altitude
            })
    
    def _perform_detections(self):
        """执行雷达检测"""
        for radar in self.radars:
            if not radar.enabled:
                continue
            
            radar_detections = 0
            
            for target in self.targets:
                if target.status != "active":
                    continue
                
                # 计算目标相对于雷达的距离
                distance_km = self._calculate_distance(
                    radar.position.latitude, radar.position.longitude,
                    target.position.latitude, target.position.longitude
                )
                
                # 计算高度差
                altitude_diff = abs(radar.position.altitude - target.position.altitude)
                
                # 计算斜距
                slant_range_km = np.sqrt(distance_km**2 + (altitude_diff/1000)**2)
                
                # 检查是否在探测范围内
                if slant_range_km <= radar.range_km:
                    # 计算检测概率
                    detection_prob = self._calculate_detection_probability(
                        slant_range_km, target.rcs_m2, radar
                    )
                    
                    # 随机检测
                    if np.random.random() < detection_prob:
                        # 计算信噪比
                        snr_db = self._calculate_snr(slant_range_km, target.rcs_m2, radar)
                        
                        # 计算方位角
                        azimuth_deg = self._calculate_azimuth(
                            radar.position.latitude, radar.position.longitude,
                            target.position.latitude, target.position.longitude
                        )
                        
                        # 计算俯仰角
                        elevation_deg = np.degrees(np.arctan2(
                            altitude_diff/1000, distance_km
                        ))
                        
                        # 创建检测结果
                        detection = DetectionResult(
                            detection_id=f"det_{len(self.data.detections)+1:06d}",
                            radar_id=radar.radar_id,
                            target_id=target.target_id,
                            timestamp=self.current_time,
                            position=target.position,
                            snr_db=snr_db,
                            range_km=slant_range_km,
                            azimuth_deg=azimuth_deg,
                            elevation_deg=elevation_deg,
                            confidence=detection_prob
                        )
                        
                        self.data.detections.append(detection)
                        radar_detections += 1
            
            # 记录雷达数据
            self.data.radar_data.append({
                'radar_id': radar.radar_id,
                'timestamp': self.current_time,
                'detections': radar_detections,
                'load': min(1.0, radar_detections / 20.0)  # 简化负载计算
            })
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（km）"""
        # 使用Haversine公式
        R = 6371  # 地球半径（km）
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def _calculate_detection_probability(self, range_km: float, rcs_m2: float, radar: RadarConfig) -> float:
        """计算检测概率"""
        # 简化雷达方程
        max_range = radar.range_km
        base_prob = 0.9
        
        # 距离衰减
        range_factor = 1.0 - (range_km / max_range) ** 2
        
        # RCS影响
        rcs_factor = min(1.0, rcs_m2 / 10.0)
        
        # 环境因素
        environment_factor = 1.0
        
        return base_prob * range_factor * rcs_factor * environment_factor
    
    def _calculate_snr(self, range_km: float, rcs_m2: float, radar: RadarConfig) -> float:
        """计算信噪比"""
        # 简化雷达方程计算SNR
        # SNR = (P_t * G^2 * λ^2 * σ) / ((4π)^3 * R^4 * k * T * B * F * L)
        
        # 简化计算
        max_snr = 30  # dB
        range_factor = 20 * np.log10(radar.range_km / (range_km + 1e-6))
        rcs_factor = 10 * np.log10(rcs_m2)
        
        snr = max_snr + range_factor + rcs_factor + np.random.normal(0, 2)
        
        return max(0, snr)
    
    def _calculate_azimuth(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算方位角"""
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lon = np.radians(lon2 - lon1)
        
        x = np.sin(delta_lon) * np.cos(lat2_rad)
        y = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(delta_lon)
        
        azimuth_rad = np.arctan2(x, y)
        azimuth_deg = np.degrees(azimuth_rad)
        
        return (azimuth_deg + 360) % 360
    
    def _perform_tracking(self):
        """执行目标跟踪"""
        # 简化跟踪算法
        current_detections = [d for d in self.data.detections 
                             if abs(d.timestamp - self.current_time) < 1.0]
        
        for detection in current_detections:
            # 查找现有航迹
            track_found = False
            for track in self.data.tracks:
                if track.target_id == detection.target_id and self.current_time - track.last_update < 5.0:
                    # 更新现有航迹
                    track.positions.append(detection.position)
                    track.timestamps.append(self.current_time)
                    track.last_update = self.current_time
                    track.confidence = 0.9
                    track_found = True
                    break
            
            if not track_found:
                # 创建新航迹
                track = TrackResult(
                    track_id=f"trk_{len(self.data.tracks)+1:06d}",
                    target_id=detection.target_id,
                    positions=[detection.position],
                    timestamps=[self.current_time],
                    confidence=0.7,
                    start_time=self.current_time,
                    last_update=self.current_time,
                    status="active"
                )
                self.data.tracks.append(track)
        
        # 更新航迹状态
        for track in self.data.tracks:
            if self.current_time - track.last_update > 5.0:
                track.status = "lost"
                track.confidence *= 0.9
    
    def _calculate_performance_metrics(self):
        """计算性能指标"""
        if not self.data.detections:
            return
        
        # 计算检测性能
        total_targets = len(self.targets)
        detected_targets = len(set([d.target_id for d in self.data.detections 
                                   if abs(d.timestamp - self.current_time) < 1.0]))
        detection_prob = detected_targets / total_targets if total_targets > 0 else 0.0
        
        # 计算虚警率（简化）
        false_alarm_rate = 1e-4 + np.random.normal(0, 1e-5)
        
        # 计算跟踪性能
        active_tracks = [t for t in self.data.tracks if t.status == "active"]
        track_continuity = len(active_tracks) / total_targets if total_targets > 0 else 0.0
        
        # 计算位置误差（简化）
        position_error = 50.0 + np.random.normal(0, 10)
        
        # 计算系统性能
        system_load = np.mean([r.get('load', 0) for r in self.data.radar_data[-10:]]) if self.data.radar_data else 0.0
        
        # 创建性能指标
        metrics = PerformanceMetrics(
            detection_probability=detection_prob,
            false_alarm_rate=false_alarm_rate,
            snr_threshold_db=13.0,
            track_continuity=track_continuity,
            position_error_m=position_error,
            track_lifetime_s=150.0,
            initiation_time_s=2.5,
            system_load=system_load,
            throughput=100.0,
            cpu_usage=0.6,
            memory_usage=0.5,
            fusion_gain=1.2,
            fusion_delay_s=0.1,
            fusion_consistency=0.85
        )
        
        self.data.performance_metrics = metrics
        self.performance_history.append({
            'timestamp': self.current_time,
            'metrics': metrics.dict()
        })
    
    def _record_performance_data(self):
        """记录性能数据"""
        time_series_point = {
            'timestamp': self.current_time,
            'detection_probability': self.data.performance_metrics.detection_probability,
            'false_alarm_rate': self.data.performance_metrics.false_alarm_rate,
            'track_continuity': self.data.performance_metrics.track_continuity,
            'system_load': self.data.performance_metrics.system_load,
            'cpu_usage': self.data.performance_metrics.cpu_usage,
            'memory_usage': self.data.performance_metrics.memory_usage
        }
        
        self.data.time_series_data.append(time_series_point)
    
    def pause(self):
        """暂停仿真"""
        if self.state == SimulationState.RUNNING:
            self.pause_event.clear()
            self.state = SimulationState.PAUSED
            logger.info("仿真已暂停")
    
    def resume(self):
        """恢复仿真"""
        if self.state == SimulationState.PAUSED:
            self.pause_event.set()
            self.state = SimulationState.RUNNING
            logger.info("仿真已恢复")
    
    def stop(self):
        """停止仿真"""
        self.stop_event.set()
        self.state = SimulationState.STOPPED
        logger.info("仿真停止")
    
    def step(self) -> Dict[str, Any]:
        """执行一步仿真（手动控制）"""
        if self.state not in [SimulationState.INITIALIZED, SimulationState.PAUSED]:
            logger.error("仿真未就绪")
            return {"error": "Simulation not ready"}
        
        try:
            time_step = self.simulation_config.time_step
            self.current_time += time_step
            self.progress = self.current_time / self.simulation_config.duration
            
            # 执行仿真步骤
            self._simulation_step(time_step)
            
            # 记录性能数据
            if self.current_time % self.simulation_config.log_interval < time_step:
                self._record_performance_data()
            
            return {
                'current_time': self.current_time,
                'progress': self.progress,
                'radar_data': self.data.radar_data[-len(self.radars):] if self.data.radar_data else [],
                'target_data': self.data.target_data[-len(self.targets):] if self.data.target_data else [],
                'detections': [d.dict() for d in self.data.detections[-100:]],
                'tracks': [t.dict() for t in self.data.tracks[-50:]],
                'performance_metrics': self.data.performance_metrics.dict() if self.data.performance_metrics else {}
            }
            
        except Exception as e:
            logger.error(f"执行仿真步骤失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取仿真状态"""
        return {
            'state': self.state.value,
            'current_time': self.current_time,
            'progress': self.progress,
            'radar_count': len(self.radars),
            'target_count': len(self.targets),
            'detection_count': len(self.data.detections),
            'track_count': len(self.data.tracks)
        }
    
    def get_results(self) -> Dict[str, Any]:
        """获取仿真结果"""
        return {
            'simulation_config': self.simulation_config.dict() if self.simulation_config else {},
            'performance_metrics': self.data.performance_metrics.dict() if self.data.performance_metrics else {},
            'time_series_data': self.data.time_series_data,
            'detections': [d.dict() for d in self.data.detections],
            'tracks': [t.dict() for t in self.data.tracks],
            'radar_data': self.data.radar_data,
            'target_data': self.data.target_data,
            'performance_history': self.performance_history
        }