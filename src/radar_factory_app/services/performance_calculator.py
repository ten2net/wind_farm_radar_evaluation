"""
雷达性能计算服务模块
提供雷达系统性能指标计算和分析功能
基于雷达方程和信号检测理论
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import special
from enum import Enum
import math

from models.radar_models import RadarModel, RadarBand
from models.simulation_models import TargetParameters
from utils.helpers import db_to_linear, linear_to_db, calculate_radar_range


class DetectionModel(Enum):
    """检测模型类型"""
    SINGLE_PULSE = "单脉冲检测"
    COHERENT_INTEGRATION = "相干积累"
    NON_COHERENT_INTEGRATION = "非相干积累"


class ClutterModel(Enum):
    """杂波模型类型"""
    RAYLEIGH = "瑞利分布"
    LOG_NORMAL = "对数正态分布"
    WEIBULL = "韦布尔分布"
    K_DISTRIBUTION = "K分布"


class RadarPerformanceCalculator:
    """雷达性能计算器"""
    
    def __init__(self):
        self.boltzmann_constant = 1.38e-23  # 玻尔兹曼常数
        self.light_speed = 3e8  # 光速(m/s)
    
    def calculate_system_performance(self, radar: RadarModel, target_rcs: float = 1.0) -> Dict[str, Any]:
        """
        计算雷达系统综合性能
        
        Args:
            radar: 雷达模型
            target_rcs: 目标RCS(m²)
            
        Returns:
            性能指标字典
        """
        if not radar.transmitter or not radar.antenna:
            return {}
        
        # 基本参数
        wavelength = radar.get_wavelength()
        frequency = radar.transmitter.frequency_hz
        
        # 计算各项性能指标
        max_range = self.calculate_max_detection_range(radar, target_rcs)
        range_resolution = self.calculate_range_resolution(radar)
        doppler_resolution = self.calculate_doppler_resolution(radar)
        angular_resolution = self.calculate_angular_resolution(radar)
        snr_at_reference = self.calculate_snr_at_range(radar, target_rcs, 100e3)  # 100km处SNR
        
        # 检测性能
        detection_performance = self.calculate_detection_performance(radar, target_rcs)
        
        return {
            "max_detection_range_km": max_range / 1000,
            "range_resolution_m": range_resolution,
            "doppler_resolution_hz": doppler_resolution,
            "angular_resolution_deg": angular_resolution,
            "snr_at_100km_db": snr_at_reference,
            "wavelength_m": wavelength,
            "frequency_ghz": frequency / 1e9,
            "detection_probability": detection_performance.get("detection_probability", 0),
            "false_alarm_rate": detection_performance.get("false_alarm_rate", 0),
            "minimum_detectable_rcs_m2": self.calculate_minimum_detectable_rcs(radar)
        }
    
    def calculate_max_detection_range(self, radar: RadarModel, target_rcs: float, 
                                    snr_min_db: float = 12.0, losses_db: float = 3.0) -> float:
        """
        计算最大探测距离
        
        Args:
            radar: 雷达模型
            target_rcs: 目标RCS(m²)
            snr_min_db: 最小可检测信噪比(dB)
            losses_db: 系统损耗(dB)
            
        Returns:
            最大探测距离(m)
        """
        if not radar.transmitter or not radar.antenna:
            return 0.0
        
        pt = radar.transmitter.power_w
        g = db_to_linear(radar.antenna.gain_dbi)
        wavelength = radar.get_wavelength()
        snr_min = db_to_linear(snr_min_db)
        losses = db_to_linear(losses_db)
        
        # 计算噪声功率
        if radar.transmitter.bandwidth_hz:
            bandwidth = radar.transmitter.bandwidth_hz
        else:
            # 如果没有指定带宽，使用脉冲宽度的倒数作为近似
            bandwidth = 1.0 / radar.transmitter.pulse_width_s
        
        noise_power = self.boltzmann_constant * 290 * bandwidth  # 标准噪声温度290K
        
        return calculate_radar_range(snr_min, pt, g, target_rcs, wavelength, losses, noise_power)
    
    def calculate_snr_at_range(self, radar: RadarModel, target_rcs: float, 
                             range_m: float, losses_db: float = 3.0) -> float:
        """
        计算指定距离处的信噪比
        
        Args:
            radar: 雷达模型
            target_rcs: 目标RCS(m²)
            range_m: 距离(m)
            losses_db: 系统损耗(dB)
            
        Returns:
            信噪比(dB)
        """
        if not radar.transmitter or not radar.antenna or range_m <= 0:
            return -np.inf
        
        pt = radar.transmitter.power_w
        g = db_to_linear(radar.antenna.gain_dbi)
        wavelength = radar.get_wavelength()
        losses = db_to_linear(losses_db)
        
        # 计算噪声功率
        if radar.transmitter.bandwidth_hz:
            bandwidth = radar.transmitter.bandwidth_hz
        else:
            bandwidth = 1.0 / radar.transmitter.pulse_width_s
        
        noise_power = self.boltzmann_constant * 290 * bandwidth
        
        # 雷达方程计算SNR
        numerator = pt * (g ** 2) * (wavelength ** 2) * target_rcs
        denominator = (4 * np.pi) ** 3 * (range_m ** 4) * losses * noise_power
        
        if denominator <= 0:
            return -np.inf
        
        snr_linear = numerator / denominator
        return linear_to_db(snr_linear)
    
    def calculate_range_resolution(self, radar: RadarModel) -> float:
        """
        计算距离分辨率
        
        Args:
            radar: 雷达模型
            
        Returns:
            距离分辨率(m)
        """
        if not radar.transmitter:
            return 0.0
        
        if radar.transmitter.bandwidth_hz:
            bandwidth = radar.transmitter.bandwidth_hz
        else:
            # 使用脉冲宽度估算带宽
            bandwidth = 1.0 / radar.transmitter.pulse_width_s
        
        return self.light_speed / (2 * bandwidth)
    
    def calculate_doppler_resolution(self, radar: RadarModel, 
                                   integration_time: float = 0.1) -> float:
        """
        计算多普勒分辨率
        
        Args:
            radar: 雷达模型
            integration_time: 积分时间(s)
            
        Returns:
            多普勒分辨率(Hz)
        """
        wavelength = radar.get_wavelength()
        return 1.0 / integration_time
    
    def calculate_angular_resolution(self, radar: RadarModel) -> float:
        """
        计算角分辨率
        
        Args:
            radar: 雷达模型
            
        Returns:
            角分辨率(度)
        """
        if not radar.antenna:
            return 0.0
        
        # 使用方位和俯仰波束宽度的平均值作为角分辨率
        return (radar.antenna.azimuth_beamwidth + radar.antenna.elevation_beamwidth) / 2
    
    def calculate_detection_performance(self, radar: RadarModel, target_rcs: float,
                                      range_m: float = 100e3, pfa: float = 1e-6,
                                      n_pulses: int = 10) -> Dict[str, Any]:
        """
        计算检测性能（检测概率和虚警概率）
        
        Args:
            radar: 雷达模型
            target_rcs: 目标RCS(m²)
            range_m: 目标距离(m)
            pfa: 虚警概率
            n_pulses: 积累脉冲数
            
        Returns:
            检测性能字典
        """
        # 计算SNR
        snr_db = self.calculate_snr_at_range(radar, target_rcs, range_m)
        snr_linear = db_to_linear(snr_db)
        
        # 计算检测概率（使用Swerling模型）
        pd_sw1 = self.calculate_detection_probability(snr_linear, pfa, n_pulses, "swerling1")
        pd_sw3 = self.calculate_detection_probability(snr_linear, pfa, n_pulses, "swerling3")
        
        # 计算检测距离
        max_range_sw1 = self.calculate_max_detection_range(radar, target_rcs, 12.0, 3.0)
        max_range_sw3 = self.calculate_max_detection_range(radar, target_rcs, 12.0, 3.0)
        
        return {
            "snr_db": snr_db,
            "detection_probability_sw1": pd_sw1,
            "detection_probability_sw3": pd_sw3,
            "false_alarm_probability": pfa,
            "max_range_sw1_km": max_range_sw1 / 1000,
            "max_range_sw3_km": max_range_sw3 / 1000,
            "pulses_integrated": n_pulses
        }
    
    def calculate_detection_probability(self, snr_linear: float, pfa: float,
                                      n_pulses: int, target_model: str = "swerling1") -> float:
        """
        计算检测概率
        
        Args:
            snr_linear: 信噪比(线性值)
            pfa: 虚警概率
            n_pulses: 积累脉冲数
            target_model: 目标起伏模型
            
        Returns:
            检测概率
        """
        if snr_linear <= 0 or pfa <= 0:
            return 0.0
        
        # 计算检测门限
        threshold = self.calculate_detection_threshold(pfa, n_pulses)
        
        if target_model == "swerling1":
            # Swerling I模型（慢起伏，瑞利分布）
            return self._swerling1_detection_probability(snr_linear, threshold, n_pulses)
        elif target_model == "swerling3":
            # Swerling III模型（慢起伏，卡方分布）
            return self._swerling3_detection_probability(snr_linear, threshold, n_pulses)
        else:
            # 非起伏目标（恒定RCS）
            return self._non_fluctuating_detection_probability(snr_linear, threshold, n_pulses)
    
    def calculate_detection_threshold(self, pfa: float, n_pulses: int) -> float:
        """
        计算检测门限
        
        Args:
            pfa: 虚警概率
            n_pulses: 积累脉冲数
            
        Returns:
            检测门限
        """
        if n_pulses == 1:
            # 单脉冲情况
            return -np.log(pfa)
        else:
            # 多脉冲积累，使用近似公式
            return np.power(pfa, -1.0 / n_pulses) - 1
    
    def _non_fluctuating_detection_probability(self, snr: float, threshold: float, 
                                            n_pulses: int) -> float:
        """非起伏目标检测概率计算"""
        if n_pulses == 1:
            # 单脉冲检测
            return np.exp(-threshold / (1 + snr))
        else:
            # 多脉冲非相干积累（近似计算）
            effective_snr = n_pulses * snr
            return 1 - special.gammainc(n_pulses, threshold / (1 + effective_snr/n_pulses))
    
    def _swerling1_detection_probability(self, snr: float, threshold: float, 
                                       n_pulses: int) -> float:
        """Swerling I模型检测概率计算"""
        if n_pulses == 1:
            return np.exp(-threshold / (1 + snr))
        else:
            # 多脉冲Swerling I检测
            return 1 - special.gammainc(n_pulses, threshold / (1 + snr))
    
    def _swerling3_detection_probability(self, snr: float, threshold: float, 
                                       n_pulses: int) -> float:
        """Swerling III模型检测概率计算"""
        if n_pulses == 1:
            return (1 + 2/(3*snr)) * np.exp(-threshold/(1+snr/2))
        else:
            # 简化计算（实际应使用更精确的公式）
            effective_threshold = threshold / (1 + snr/2)
            return 1 - (1 + effective_threshold) * np.exp(-effective_threshold)
    
    def calculate_minimum_detectable_rcs(self, radar: RadarModel, 
                                       range_m: float = 100e3, 
                                       snr_min_db: float = 12.0) -> float:
        """
        计算最小可检测RCS
        
        Args:
            radar: 雷达模型
            range_m: 距离(m)
            snr_min_db: 最小可检测信噪比(dB)
            
        Returns:
            最小可检测RCS(m²)
        """
        if not radar.transmitter or not radar.antenna:
            return 0.0
        
        # 从雷达方程反推最小RCS
        pt = radar.transmitter.power_w
        g = db_to_linear(radar.antenna.gain_dbi)
        wavelength = radar.get_wavelength()
        snr_min = db_to_linear(snr_min_db)
        losses = db_to_linear(3.0)  # 假设3dB损耗
        
        # 计算噪声功率
        if radar.transmitter.bandwidth_hz:
            bandwidth = radar.transmitter.bandwidth_hz
        else:
            bandwidth = 1.0 / radar.transmitter.pulse_width_s
        
        noise_power = self.boltzmann_constant * 290 * bandwidth
        
        # 雷达方程反推：σ_min = (SNR_min * (4π)^3 * R^4 * L * kTBF) / (Pt * G^2 * λ^2)
        numerator = snr_min * (4 * np.pi) ** 3 * (range_m ** 4) * losses * noise_power
        denominator = pt * (g ** 2) * (wavelength ** 2)
        
        if denominator <= 0:
            return np.inf
        
        return numerator / denominator
    
    def calculate_ambiguity_range(self, radar: RadarModel) -> float:
        """
        计算模糊距离
        
        Args:
            radar: 雷达模型
            
        Returns:
            模糊距离(m)
        """
        if not radar.transmitter:
            return 0.0
        
        prf = radar.transmitter.prf_hz
        if prf <= 0:
            # 如果没有指定PRF，使用脉冲宽度的倒数作为近似
            prf = 1.0 / radar.transmitter.pulse_width_s
        
        return self.light_speed / (2 * prf)
    
    def calculate_doppler_ambiguity(self, radar: RadarModel) -> float:
        """
        计算多普勒模糊
        
        Args:
            radar: 雷达模型
            
        Returns:
            最大不模糊多普勒频率(Hz)
        """
        if not radar.transmitter:
            return 0.0
        
        prf = radar.transmitter.prf_hz
        if prf <= 0:
            prf = 1.0 / radar.transmitter.pulse_width_s
        
        return prf / 2
    
    def calculate_power_aperture_product(self, radar: RadarModel) -> float:
        """
        计算功率孔径积
        
        Args:
            radar: 雷达模型
            
        Returns:
            功率孔径积(W·m²)
        """
        if not radar.transmitter or not radar.antenna:
            return 0.0
        
        # 估算天线孔径面积
        wavelength = radar.get_wavelength()
        g_linear = db_to_linear(radar.antenna.gain_dbi)
        aperture_area = (wavelength ** 2) * g_linear / (4 * np.pi)
        
        return radar.transmitter.power_w * aperture_area
    
    def calculate_search_performance(self, radar: RadarModel, search_volume: float,
                                  scan_time: float) -> Dict[str, Any]:
        """
        计算搜索性能
        
        Args:
            radar: 雷达模型
            search_volume: 搜索空域(立体角, sr)
            scan_time: 扫描时间(s)
            
        Returns:
            搜索性能字典
        """
        if not radar.antenna:
            return {}
        
        # 计算波束立体角
        azimuth_rad = np.radians(radar.antenna.azimuth_beamwidth)
        elevation_rad = np.radians(radar.antenna.elevation_beamwidth)
        beam_solid_angle = azimuth_rad * elevation_rad  # 近似计算
        
        # 计算波束数量
        n_beams = search_volume / beam_solid_angle
        
        # 计算驻留时间
        dwell_time = scan_time / n_beams
        
        # 计算搜索性能因子
        power_aperture = self.calculate_power_aperture_product(radar)
        search_factor = power_aperture * scan_time / search_volume
        
        return {
            "beam_solid_angle_sr": beam_solid_angle,
            "number_of_beams": n_beams,
            "dwell_time_per_beam_s": dwell_time,
            "search_factor": search_factor,
            "search_volume_sr": search_volume,
            "scan_time_s": scan_time
        }
    
    def calculate_tracking_performance(self, radar: RadarModel, target: TargetParameters,
                                     update_rate: float) -> Dict[str, Any]:
        """
        计算跟踪性能
        
        Args:
            radar: 雷达模型
            target: 目标参数
            update_rate: 更新率(Hz)
            
        Returns:
            跟踪性能字典
        """
        # 计算SNR
        range_m = np.linalg.norm(target.position)  # 简化计算，假设雷达在原点
        snr_db = self.calculate_snr_at_range(radar, target.rcs_sqm, range_m)
        
        # 计算跟踪精度（简化模型）
        range_resolution = self.calculate_range_resolution(radar)
        angular_resolution = self.calculate_angular_resolution(radar)
        
        # 距离跟踪精度
        range_accuracy = range_resolution / np.sqrt(2 * snr_db) if snr_db > 0 else range_resolution
        
        # 角度跟踪精度
        angle_accuracy_rad = np.radians(angular_resolution) / np.sqrt(2 * snr_db) if snr_db > 0 else np.radians(angular_resolution)
        angle_accuracy_deg = np.degrees(angle_accuracy_rad)
        
        # 多普勒精度
        wavelength = radar.get_wavelength()
        integration_time = 1.0 / update_rate
        doppler_resolution = 1.0 / integration_time
        doppler_accuracy = doppler_resolution / np.sqrt(2 * snr_db) if snr_db > 0 else doppler_resolution
        velocity_accuracy = doppler_accuracy * wavelength / 2
        
        return {
            "snr_db": snr_db,
            "range_accuracy_m": range_accuracy,
            "angle_accuracy_deg": angle_accuracy_deg,
            "doppler_accuracy_hz": doppler_accuracy,
            "velocity_accuracy_mps": velocity_accuracy,
            "update_rate_hz": update_rate,
            "tracking_range_km": range_m / 1000
        }
    
    def compare_radars(self, radars: List[RadarModel], target_rcs: float = 1.0) -> Dict[str, Any]:
        """
        比较多个雷达的性能
        
        Args:
            radars: 雷达模型列表
            target_rcs: 目标RCS(m²)
            
        Returns:
            比较结果字典
        """
        comparison_results = {}
        
        for radar in radars:
            radar_id = radar.radar_id
            performance = self.calculate_system_performance(radar, target_rcs)
            comparison_results[radar_id] = {
                "name": radar.name,
                "performance": performance,
                "band": radar.get_band().value,
                "platform": radar.platform.value
            }
        
        # 计算综合排名
        ranked_radars = self._rank_radars(comparison_results)
        
        return {
            "comparison": comparison_results,
            "rankings": ranked_radars,
            "target_rcs_m2": target_rcs
        }
    
    def _rank_radars(self, comparison_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        对雷达进行综合排名
        
        Args:
            comparison_results: 比较结果
            
        Returns:
            排名列表
        """
        rankings = []
        
        for radar_id, data in comparison_results.items():
            perf = data["performance"]
            
            # 综合评分（加权平均）
            score = (
                0.4 * perf.get("max_detection_range_km", 0) / 100 +  # 探测距离权重40%
                0.3 * (100 - perf.get("range_resolution_m", 100)) / 10 +  # 分辨率权重30%
                0.2 * perf.get("snr_at_100km_db", 0) / 20 +  # 信噪比权重20%
                0.1 * perf.get("detection_probability", 0)  # 检测概率权重10%
            )
            
            rankings.append({
                "radar_id": radar_id,
                "name": data["name"],
                "score": score,
                "max_range_km": perf.get("max_detection_range_km", 0),
                "range_resolution_m": perf.get("range_resolution_m", 0),
                "band": data["band"],
                "platform": data["platform"]
            })
        
        # 按分数排序
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        # 添加排名
        for i, rank in enumerate(rankings):
            rank["rank"] = i + 1
        
        return rankings


# 性能分析器类
class PerformanceAnalyzer:
    """性能分析器 - 提供高级性能分析功能"""
    
    def __init__(self, calculator: RadarPerformanceCalculator):
        self.calculator = calculator
    
    def analyze_coverage(self, radar: RadarModel, altitude_km: float = 0, 
                        elevation_angle: float = 0) -> Dict[str, Any]:
        """
        分析雷达覆盖范围
        
        Args:
            radar: 雷达模型
            altitude_km: 雷达海拔高度(km)
            elevation_angle: 仰角(度)
            
        Returns:
            覆盖范围分析结果
        """
        # 计算最大探测距离
        max_range_km = self.calculator.calculate_max_detection_range(radar, 1.0) / 1000
        
        # 计算覆盖面积（简化模型）
        if radar.antenna:
            azimuth_cover = 360  # 假设全方位覆盖
            elevation_cover = radar.antenna.elevation_beamwidth
            
            # 计算覆盖立体角
            coverage_solid_angle = np.radians(azimuth_cover) * np.radians(elevation_cover)
            
            # 计算覆盖面积（球面近似）
            coverage_area = (max_range_km ** 2) * coverage_solid_angle
        else:
            coverage_area = 0
        
        return {
            "max_range_km": max_range_km,
            "coverage_area_km2": coverage_area,
            "altitude_km": altitude_km,
            "elevation_angle_deg": elevation_angle,
            "horizon_range_km": self._calculate_horizon_range(altitude_km * 1000) / 1000
        }
    
    def _calculate_horizon_range(self, altitude: float) -> float:
        """计算视距"""
        earth_radius = 6371000  # 地球半径(m)
        return np.sqrt(2 * earth_radius * altitude + altitude ** 2)
    
    def analyze_frequency_advantages(self, radar: RadarModel) -> Dict[str, Any]:
        """
        分析频段优势
        
        Args:
            radar: 雷达模型
            
        Returns:
            频段优势分析
        """
        band = radar.get_band()
        advantages = []
        disadvantages = []
        
        if band == RadarBand.UHF:
            advantages.extend(["反隐身能力强", "大气衰减小", "远程探测优势"])
            disadvantages.extend(["分辨率较低", "天线尺寸大", "易受电离层影响"])
        elif band == RadarBand.L:
            advantages.extend(["平衡性好", "中等分辨率", "适合预警机"])
            disadvantages.extend(["天线尺寸较大", "中等反隐身能力"])
        elif band in [RadarBand.S, RadarBand.C]:
            advantages.extend(["分辨率高", "跟踪精度好", "多功能性"])
            disadvantages.extend(["大气衰减增加", "反隐身能力有限"])
        elif band in [RadarBand.X, RadarBand.KU]:
            advantages.extend(["高分辨率", "小型化", "适合精密跟踪"])
            disadvantages.extend(["大气衰减大", "作用距离受限"])
        
        return {
            "band": band.value,
            "advantages": advantages,
            "disadvantages": disadvantages,
            "typical_applications": self._get_typical_applications(band)
        }
    
    def _get_typical_applications(self, band: RadarBand) -> List[str]:
        """获取典型应用"""
        applications = {
            RadarBand.UHF: ["远程预警", "反隐身探测", "太空监视"],
            RadarBand.L: ["空中预警", "指挥控制", "战场监视"],
            RadarBand.S: ["区域防空", "舰载雷达", "气象雷达"],
            RadarBand.C: ["火控雷达", "导弹制导", "精密跟踪"],
            RadarBand.X: ["机载雷达", "海事雷达", "合成孔径雷达"],
            RadarBand.KU: ["近程监视", "导航雷达", "汽车雷达"]
        }
        return applications.get(band, ["通用雷达"])
    
    def generate_performance_report(self, radar: RadarModel) -> Dict[str, Any]:
        """
        生成性能报告
        
        Args:
            radar: 雷达模型
            
        Returns:
            性能报告
        """
        # 计算基本性能
        basic_performance = self.calculator.calculate_system_performance(radar)
        
        # 分析覆盖范围
        coverage = self.analyze_coverage(radar)
        
        # 分析频段优势
        frequency_analysis = self.analyze_frequency_advantages(radar)
        
        # 检测性能分析
        detection_performance = self.calculator.calculate_detection_performance(radar, 1.0)
        
        # 搜索性能分析
        search_performance = self.calculator.calculate_search_performance(
            radar, search_volume=4*np.pi, scan_time=10.0
        )
        
        return {
            "radar_info": {
                "name": radar.name,
                "id": radar.radar_id,
                "band": radar.get_band().value,
                "platform": radar.platform.value,
                "mission_types": [mission.value for mission in radar.mission_types]
            },
            "basic_performance": basic_performance,
            "coverage_analysis": coverage,
            "frequency_analysis": frequency_analysis,
            "detection_performance": detection_performance,
            "search_performance": search_performance,
            "summary": self._generate_summary(basic_performance, frequency_analysis)
        }
    
    def _generate_summary(self, performance: Dict[str, Any], frequency_analysis: Dict[str, Any]) -> str:
        """生成性能摘要"""
        max_range = performance.get("max_detection_range_km", 0)
        resolution = performance.get("range_resolution_m", 0)
        
        summary = f"最大探测距离: {max_range:.1f} km, 距离分辨率: {resolution:.2f} m\n"
        summary += f"频段优势: {', '.join(frequency_analysis.get('advantages', []))}\n"
        summary += f"典型应用: {', '.join(frequency_analysis.get('typical_applications', []))}"
        
        return summary


# 多雷达协同性能分析器
class MultiRadarPerformanceAnalyzer:
    """多雷达协同性能分析器"""
    
    def __init__(self, calculator: RadarPerformanceCalculator):
        self.calculator = calculator
    
    def analyze_cooperative_performance(self, radars: List[RadarModel], 
                                      target_rcs: float = 1.0) -> Dict[str, Any]:
        """
        分析多雷达协同性能
        
        Args:
            radars: 雷达列表
            target_rcs: 目标RCS(m²)
            
        Returns:
            协同性能分析结果
        """
        # 计算各雷达独立性能
        individual_performance = {}
        for radar in radars:
            individual_performance[radar.radar_id] = {
                "performance": self.calculator.calculate_system_performance(radar, target_rcs),
                "radar_info": {
                    "name": radar.name,
                    "band": radar.get_band().value,
                    "platform": radar.platform.value
                }
            }
        
        # 计算协同性能
        cooperative_range = self._calculate_cooperative_range(radars, target_rcs)
        coverage_overlap = self._calculate_coverage_overlap(radars)
        frequency_diversity = self._analyze_frequency_diversity(radars)
        redundancy_analysis = self._analyze_redundancy(radars)
        
        return {
            "individual_performance": individual_performance,
            "cooperative_performance": {
                "extended_range_km": cooperative_range / 1000,
                "coverage_overlap_percent": coverage_overlap,
                "frequency_diversity_score": frequency_diversity,
                "redundancy_level": redundancy_analysis,
                "synergy_advantages": self._identify_synergy_advantages(radars)
            },
            "recommendations": self._generate_recommendations(radars)
        }
    
    def _calculate_cooperative_range(self, radars: List[RadarModel], target_rcs: float) -> float:
        """计算协同探测距离"""
        if not radars:
            return 0.0
        
        # 使用最远探测距离作为协同距离
        max_range = 0
        for radar in radars:
            range_m = self.calculator.calculate_max_detection_range(radar, target_rcs)
            max_range = max(max_range, range_m)
        
        # 协同效应增加10-30%的距离
        synergy_factor = 1.2  # 20%增加
        return max_range * synergy_factor
    
    def _calculate_coverage_overlap(self, radars: List[RadarModel]) -> float:
        """计算覆盖重叠度"""
        if len(radars) < 2:
            return 0.0
        
        # 简化计算：基于雷达部署位置和波束宽度估算重叠度
        # 这里使用固定值作为示例
        return min(80.0, 30.0 * len(radars))  # 最大80%重叠
    
    def _analyze_frequency_diversity(self, radars: List[RadarModel]) -> float:
        """分析频率分集效果"""
        bands = set()
        frequencies = []
        
        for radar in radars:
            bands.add(radar.get_band())
            if radar.transmitter:
                frequencies.append(radar.transmitter.frequency_hz)
        
        # 计算频率分集得分（0-100）
        band_diversity = len(bands) / 6.0 * 50  # 频段多样性占50分
        freq_spread = 0
        
        if frequencies:
            min_freq = min(frequencies)
            max_freq = max(frequencies)
            if min_freq > 0:
                freq_spread = (max_freq - min_freq) / min_freq * 50  # 频率跨度占50分
        
        return min(100.0, band_diversity + freq_spread)
    
    def _analyze_redundancy(self, radars: List[RadarModel]) -> str:
        """分析冗余度"""
        n_radars = len(radars)
        
        if n_radars >= 5:
            return "高冗余度"
        elif n_radars >= 3:
            return "中等冗余度"
        elif n_radars >= 2:
            return "低冗余度"
        else:
            return "无冗余"
    
    def _identify_synergy_advantages(self, radars: List[RadarModel]) -> List[str]:
        """识别协同优势"""
        advantages = []
        bands = [radar.get_band() for radar in radars]
        
        if RadarBand.UHF in bands and RadarBand.S in bands:
            advantages.append("反隐身与精密跟踪协同")
        
        if any(radar.platform.value == "机载" for radar in radars):
            advantages.append("空地协同探测")
        
        if len(bands) >= 3:
            advantages.append("多频段抗干扰")
        
        if len(radars) >= 3:
            advantages.append("多基地定位精度提升")
        
        return advantages if advantages else ["基础协同探测"]
    
    def _generate_recommendations(self, radars: List[RadarModel]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        n_radars = len(radars)
        
        if n_radars < 3:
            recommendations.append("建议增加雷达数量以提高系统冗余度")
        
        bands = [radar.get_band() for radar in radars]
        if RadarBand.UHF not in bands:
            recommendations.append("考虑增加UHF波段雷达以增强反隐身能力")
        
        platforms = [radar.platform.value for radar in radars]
        if "机载" not in platforms:
            recommendations.append("建议增加机载雷达平台以扩展探测高度")
        
        return recommendations


# 测试代码
if __name__ == "__main__":
    # 创建性能计算器实例
    calculator = RadarPerformanceCalculator()
    
    # 创建示例雷达（使用工厂模式）
    from models.radar_models import RadarFactory, PRESET_RADARS
    
    radar_config = PRESET_RADARS["JY-27B_UHF001"]
    radar = RadarFactory.create_from_config(radar_config)
    
    if radar:
        # 计算性能
        performance = calculator.calculate_system_performance(radar)
        print("雷达性能分析:")
        for key, value in performance.items():
            print(f"{key}: {value}")
        
        # 检测性能分析
        detection = calculator.calculate_detection_performance(radar, 1.0)
        print(f"\n检测性能: SNR={detection['snr_db']:.1f}dB, Pd(Sw1)={detection['detection_probability_sw1']:.3f}")
        
        # 创建性能分析器
        analyzer = PerformanceAnalyzer(calculator)
        report = analyzer.generate_performance_report(radar)
        print(f"\n性能报告摘要:\n{report['summary']}")        