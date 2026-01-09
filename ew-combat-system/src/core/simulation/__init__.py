"""
电子战仿真引擎
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from ..entities import Radar, Jammer, Target, Position
from scipy import signal, interpolate
import warnings
warnings.filterwarnings('ignore')

@dataclass
class PropagationModel:
    """传播模型"""
    frequency: float  # GHz
    distance: float  # km
    terrain_type: str = "flat"  # flat, urban, mountainous, sea
    atmosphere: str = "standard"  # standard, anomalous, rain
    
    def free_space_loss(self) -> float:
        """自由空间传播损耗"""
        # FSPL(dB) = 20log10(d) + 20log10(f) + 32.44
        # d in km, f in GHz
        return 20 * np.log10(self.distance) + 20 * np.log10(self.frequency) + 32.44
    
    def two_ray_loss(self, ht: float, hr: float) -> float:
        """双径传播模型（考虑地面反射）"""
        # 当距离大于临界距离时
        d_critical = 4 * ht * hr * self.frequency * 1e9 / 299792458
        if self.distance * 1000 > d_critical:
            # 四阶衰减
            return 40 * np.log10(self.distance) - 20 * np.log10(ht) - 20 * np.log10(hr)
        else:
            return self.free_space_loss()
    
    def atmospheric_absorption(self) -> float:
        """大气吸收损耗"""
        # ITU-R P.676建议书简化模型
        f = self.frequency
        if f < 1:
            return 0.1 * self.distance
        elif f < 10:
            return (0.2 + 0.1 * f) * self.distance
        else:
            return (0.5 + 0.05 * f) * self.distance
    
    def total_loss(self, ht: float = 50, hr: float = 10000) -> float:
        """总传播损耗"""
        base_loss = self.two_ray_loss(ht, hr)
        atm_loss = self.atmospheric_absorption()
        
        # 地形因子
        terrain_factors = {
            "flat": 0,
            "urban": 20,
            "mountainous": 30,
            "sea": -5
        }
        terrain_loss = terrain_factors.get(self.terrain_type, 0)
        
        return base_loss + atm_loss + terrain_loss

class EWSimulator:
    """电子战仿真器"""
    
    @staticmethod
    def calculate_jamming_effect(
        radar: Radar,
        jammer: Jammer,
        targets: List[Target] = None,
        environment: Dict = None
    ) -> Dict:
        """
        计算干扰效果
        
        参数:
            radar: 雷达对象
            jammer: 干扰机对象
            targets: 目标列表
            environment: 环境参数
            
        返回:
            干扰效果字典
        """
        if environment is None:
            environment = {}
        
        # 计算距离
        distance_km = radar.position.distance_to(jammer.position) / 1000
        
        # 传播模型
        prop_model = PropagationModel(
            frequency=jammer.parameters.get("frequency", radar.radar_params.frequency),
            distance=distance_km,
            terrain_type=environment.get("terrain", "flat"),
            atmosphere=environment.get("atmosphere", "standard")
        )
        
        propagation_loss = prop_model.total_loss(
            ht=jammer.position.alt,
            hr=radar.position.alt
        )
        
        # 雷达接收到的干扰功率
        jammer_power_w = jammer.jammer_params.power
        jammer_gain_linear = 10**(jammer.jammer_params.gain/10)
        jammer_erp = jammer_power_w * jammer_gain_linear
        
        # 干扰信号到达雷达的功率
        jammer_signal_at_radar = 10 * np.log10(jammer_erp) - propagation_loss
        
        # 雷达接收到的目标回波功率
        if targets and len(targets) > 0:
            target = targets[0]  # 简化为第一个目标
            target_range_km = radar.position.distance_to(target.position) / 1000
            
            # 雷达方程
            radar_power_w = radar.radar_params.power * 1000
            radar_gain_linear = 10**(radar.radar_params.gain/10)
            wavelength = radar.radar_params.wavelength()
            target_rcs = getattr(target, 'rcs', 1.0)
            
            target_signal = (radar_power_w * radar_gain_linear**2 * wavelength**2 * target_rcs) / \
                          ((4*np.pi)**3 * (target_range_km*1000)**4)
            target_signal_db = 10 * np.log10(target_signal) if target_signal > 0 else -200
        else:
            target_signal_db = -200
        
        # 计算干信比(J/S)
        if target_signal_db > -200:
            j_s_ratio = jammer_signal_at_radar - target_signal_db
        else:
            j_s_ratio = 100  # 无目标时干扰占绝对优势
        
        # 判断干扰是否有效
        # 通常J/S > 0dB时开始有效，>10dB时完全压制
        effective = j_s_ratio > 10
        
        # 计算探测概率
        detection_prob = EWSimulator._calculate_detection_probability(
            j_s_ratio, radar.radar_params.sensitivity
        )
        
        return {
            "effective": effective,
            "j_s_ratio": j_s_ratio,
            "detection_probability": detection_prob,
            "propagation_loss": propagation_loss,
            "distance_km": distance_km,
            "jammer_signal_db": jammer_signal_at_radar,
            "target_signal_db": target_signal_db if targets and len(targets) > 0 else None
        }
    
    @staticmethod
    def _calculate_detection_probability(j_s_ratio: float, radar_sensitivity: float) -> float:
        """计算探测概率（简化模型）"""
        # 基于J/S比和雷达灵敏度的简单模型
        if j_s_ratio > 20:
            return 0.1  # 强干扰下探测概率极低
        elif j_s_ratio > 10:
            return 0.3
        elif j_s_ratio > 0:
            return 0.6
        elif j_s_ratio > -10:
            return 0.8
        else:
            return 0.95  # 无干扰时探测概率高
    
    @staticmethod
    def simulate_radar_coverage(
        radar: Radar,
        resolution_km: float = 5,
        include_terrain: bool = False
    ) -> np.ndarray:
        """
        模拟雷达覆盖范围
        
        返回:
            覆盖网格数据 [lat, lon, coverage_strength]
        """
        # 创建网格
        lat_range = 1.0  # 度
        lon_range = 1.0
        lat_step = resolution_km / 111.0
        lon_step = resolution_km / (111.0 * np.cos(np.radians(radar.position.lat)))
        
        lats = np.arange(
            radar.position.lat - lat_range/2,
            radar.position.lat + lat_range/2,
            lat_step
        )
        lons = np.arange(
            radar.position.lon - lon_range/2,
            radar.position.lon + lon_range/2,
            lon_step
        )
        
        # 计算每个网格点的覆盖强度
        coverage = np.zeros((len(lats), len(lons)))
        
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                # 计算距离
                pos = Position(lat, lon, 0)
                distance_km = radar.position.distance_to(pos) / 1000
                
                # 计算覆盖强度（随距离衰减）
                if distance_km <= radar.radar_params.range_max:
                    # 简化模型：随距离四次方衰减
                    strength = 1 / (1 + (distance_km / radar.radar_params.range_max)**4)
                    
                    # 考虑波束方向图
                    if hasattr(radar.radar_params, 'beamwidth'):
                        # 简化的天线方向图
                        strength *= EWSimulator._antenna_pattern(strength)
                    
                    coverage[i, j] = strength
        
        return coverage
    
    @staticmethod
    def _antenna_pattern(angle_deg: float) -> float:
        """天线方向图（简化）"""
        # 高斯波束模型
        beamwidth = 3  # 度
        return np.exp(-2.772 * (angle_deg / beamwidth)**2)

class NetworkEWSimulator:
    """网络化电子战仿真器"""
    
    @staticmethod
    def simulate_network_combat(
        radars: List[Radar],
        jammers: List[Jammer],
        targets: List[Target],
        time_steps: int = 100
    ) -> Dict:
        """
        模拟网络化对抗
        
        返回:
            网络对抗结果
        """
        results = {
            "time_steps": time_steps,
            "radar_performance": [],
            "jammer_performance": [],
            "network_metrics": {}
        }
        
        # 初始化性能记录
        for radar in radars:
            results["radar_performance"].append({
                "id": radar.id,
                "detection_rates": [],
                "jamming_status": []
            })
        
        for jammer in jammers:
            results["jammer_performance"].append({
                "id": jammer.id,
                "effectiveness": [],
                "targets_engaged": []
            })
        
        # 时间步进仿真
        for t in range(time_steps):
            # 更新所有实体位置（如果移动）
            # 计算当前时刻的对抗效果
            
            for i, radar in enumerate(radars):
                # 找出对该雷达最有效的干扰机
                best_jammer = None
                best_effectiveness = 0
                
                for jammer in jammers:
                    effect = EWSimulator.calculate_jamming_effect(
                        radar, jammer, targets
                    )
                    
                    if effect.get("effective", False) and effect.get("j_s_ratio", 0) > best_effectiveness:
                        best_effectiveness = effect["j_s_ratio"]
                        best_jammer = jammer
                
                # 记录雷达性能
                detection_prob = 0.8  # 基础探测概率
                if best_jammer:
                    detection_prob *= (1 - best_effectiveness/50)  # 干扰影响
                
                results["radar_performance"][i]["detection_rates"].append(
                    max(0.1, min(0.95, detection_prob))
                )
                results["radar_performance"][i]["jamming_status"].append(
                    best_jammer.id if best_jammer else None
                )
        
        # 计算网络指标
        results["network_metrics"] = NetworkEWSimulator._calculate_network_metrics(
            results, radars, jammers
        )
        
        return results
    
    @staticmethod
    def _calculate_network_metrics(
        results: Dict,
        radars: List[Radar],
        jammers: List[Jammer]
    ) -> Dict:
        """计算网络化指标"""
        
        # 平均探测概率
        avg_detection_probs = []
        for radar_perf in results["radar_performance"]:
            if radar_perf["detection_rates"]:
                avg_detection_probs.append(np.mean(radar_perf["detection_rates"]))
        
        avg_detection = np.mean(avg_detection_probs) if avg_detection_probs else 0
        
        # 网络覆盖率
        # 简化为雷达数量与区域的函数
        coverage_ratio = min(1.0, len(radars) * 0.3)
        
        # 干扰机利用率
        jammer_utilization = 0
        for jammer_perf in results["jammer_performance"]:
            if jammer_perf["targets_engaged"]:
                utilization = len([t for t in jammer_perf["targets_engaged"] if t is not None])
                utilization /= len(jammer_perf["targets_engaged"])
                jammer_utilization = max(jammer_utilization, utilization)
        
        # 系统生存性
        survivability = 1.0 - (1.0 - avg_detection) * 0.5
        
        # 信息优势
        info_superiority = avg_detection * coverage_ratio
        
        return {
            "avg_detection_probability": avg_detection,
            "coverage_ratio": coverage_ratio,
            "jammer_utilization": jammer_utilization,
            "survivability": survivability,
            "info_superiority": info_superiority
        }
