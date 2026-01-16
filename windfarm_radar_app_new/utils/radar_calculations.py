## 文件4: utils/radar_calculations.py

"""
雷达计算模块
基于雷达方程的风电场影响量化分析
"""

import numpy as np
from scipy import constants
from scipy import signal
from typing import Dict, List, Tuple, Any, Optional, Union
import math
from dataclasses import dataclass
from config.config import (
    PHYSICAL_CONSTANTS, EVALUATION_PARAMS, RADAR_FREQUENCY_BANDS,
    ANTENNA_TYPES, TURBINE_MODELS, TARGET_RCS_DB
)
import warnings
warnings.filterwarnings('ignore')

@dataclass
class RadarParameters:
    """雷达参数类"""
    frequency_ghz: float
    peak_power_w: float
    antenna_gain_db: float
    beam_width_deg: float
    pulse_width_us: float
    prf_hz: float
    noise_figure_db: float
    system_losses_db: float
    antenna_height_m: float
    
@dataclass
class TargetParameters:
    """目标参数类"""
    rcs_m2: float
    distance_m: float
    velocity_ms: float
    altitude_m: float
    azimuth_deg: float
    elevation_deg: float
    
@dataclass
class TurbineParameters:
    """风机参数类"""
    height_m: float
    rotor_diameter_m: float
    position: Dict[str, float]  # lat, lon, alt
    orientation_deg: float
    rcs_profile: str
    blade_material: str
    
@dataclass
class CalculationResults:
    """计算结果类"""
    snr_db: float
    received_power_db: float
    doppler_frequency_hz: float
    range_resolution_m: float
    velocity_resolution_ms: float
    detection_probability: float
    multipath_loss_db: float
    interference_level_db: float
    clutter_power_db: float
    bistatic_range_m: float
    time_delay_us: float
    phase_shift_rad: float
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'snr_db': self.snr_db,
            'received_power_db': self.received_power_db,
            'doppler_frequency_hz': self.doppler_frequency_hz,
            'range_resolution_m': self.range_resolution_m,
            'velocity_resolution_ms': self.velocity_resolution_ms,
            'detection_probability': self.detection_probability,
            'multipath_loss_db': self.multipath_loss_db,
            'interference_level_db': self.interference_level_db,
            'clutter_power_db': self.clutter_power_db,
            'bistatic_range_m': self.bistatic_range_m,
            'time_delay_us': self.time_delay_us,
            'phase_shift_rad': self.phase_shift_rad
        }

class RadarCalculator:
    """雷达计算器"""
    
    def __init__(self):
        """初始化雷达计算器"""
        self.c = PHYSICAL_CONSTANTS['speed_of_light']
        self.k = PHYSICAL_CONSTANTS['boltzmann_constant']
        self.T0 = PHYSICAL_CONSTANTS['standard_temperature']
        self.earth_radius = PHYSICAL_CONSTANTS['earth_radius']
        
    def wavelength(self, frequency_ghz: float) -> float:
        """计算波长（米）"""
        return self.c / (frequency_ghz * 1e9)
    
    def db_to_linear(self, db_value: float) -> float:
        """分贝转线性值"""
        return 10 ** (db_value / 10)
    
    def linear_to_db(self, linear_value: float) -> float:
        """线性值转分贝"""
        if linear_value <= 0:
            return -np.inf
        return 10 * np.log10(linear_value)
    
    def calculate_free_space_loss(self, distance_m: float, frequency_ghz: float) -> float:
        """计算自由空间路径损耗"""
        wavelength = self.wavelength(frequency_ghz)
        loss = 20 * np.log10(distance_m) + 20 * np.log10(frequency_ghz * 1e9) + 20 * np.log10(4 * np.pi / self.c)
        return loss
    
    def calculate_radar_range_equation(
        self,
        radar: RadarParameters,
        target: TargetParameters,
        include_atmospheric_loss: bool = True
    ) -> Dict[str, float]:
        """
        计算雷达方程
        
        参数:
            radar: 雷达参数
            target: 目标参数
            include_atmospheric_loss: 是否包含大气损耗
            
        返回:
            雷达方程计算结果
        """
        # 波长
        wavelength = self.wavelength(radar.frequency_ghz)
        
        # 距离
        R = target.distance_m
        
        # 转换为线性值
        Pt = radar.peak_power_w
        Gt = self.db_to_linear(radar.antenna_gain_db)
        sigma = target.rcs_m2
        
        # 雷达方程
        Pr = (Pt * Gt**2 * wavelength**2 * sigma) / ((4 * np.pi)**3 * R**4)
        
        # 系统损耗
        Ls = self.db_to_linear(radar.system_losses_db)
        
        # 大气损耗
        if include_atmospheric_loss:
            atmospheric_loss_db = self.calculate_atmospheric_loss(radar.frequency_ghz, R)
            La = self.db_to_linear(atmospheric_loss_db)
        else:
            La = 1.0
        
        # 接收功率
        Pr_total = Pr / (Ls * La)
        
        # 转换回dB
        received_power_db = self.linear_to_db(Pr_total)
        
        return {
            'received_power_w': Pr_total,
            'received_power_db': received_power_db,
            'wavelength_m': wavelength,
            'free_space_loss_db': self.calculate_free_space_loss(R, radar.frequency_ghz),
            'atmospheric_loss_db': atmospheric_loss_db if include_atmospheric_loss else 0.0 # type: ignore
        }
    
    def calculate_snr(
        self,
        radar: RadarParameters,
        target: TargetParameters,
        bandwidth_hz: Optional[float] = None,
        integration_pulses: int = 1
    ) -> float:
        """
        计算信噪比
        
        参数:
            radar: 雷达参数
            target: 目标参数
            bandwidth_hz: 带宽（Hz），如果为None则从脉冲宽度计算
            integration_pulses: 积累脉冲数
            
        返回:
            信噪比（dB）
        """
        # 计算接收功率
        radar_eq = self.calculate_radar_range_equation(radar, target)
        Pr = radar_eq['received_power_w']
        
        # 噪声功率
        if bandwidth_hz is None:
            # 从脉冲宽度计算带宽
            tau = radar.pulse_width_us * 1e-6
            B = 1.0 / tau
        else:
            B = bandwidth_hz
        
        F = self.db_to_linear(radar.noise_figure_db)
        Pn = self.k * self.T0 * B * F
        
        # 单脉冲信噪比
        snr_single = Pr / Pn
        
        # 脉冲积累增益
        if integration_pulses > 1:
            # 理想积累增益
            snr = snr_single * integration_pulses
        else:
            snr = snr_single
        
        # 转换到dB
        snr_db = self.linear_to_db(snr)
        
        return snr_db
    
    def calculate_doppler_frequency(
        self,
        radar_frequency_ghz: float,
        radial_velocity_ms: float
    ) -> float:
        """
        计算多普勒频率
        
        参数:
            radar_frequency_ghz: 雷达频率（GHz）
            radial_velocity_ms: 径向速度（m/s）
            
        返回:
            多普勒频率（Hz）
        """
        wavelength = self.wavelength(radar_frequency_ghz)
        fd = 2 * radial_velocity_ms / wavelength
        return fd
    
    def calculate_multipath_effect(
        self,
        radar_height_m: float,
        target_height_m: float,
        distance_m: float,
        frequency_ghz: float,
        surface_reflection_coeff: float = 0.5
    ) -> Dict[str, float]:
        """
        计算多径效应
        
        参数:
            radar_height_m: 雷达高度（m）
            target_height_m: 目标高度（m）
            distance_m: 距离（m）
            frequency_ghz: 频率（GHz）
            surface_reflection_coeff: 地面反射系数
            
        返回:
            多径效应计算结果
        """
        wavelength = self.wavelength(frequency_ghz)
        
        # 直接路径
        R_direct = distance_m
        
        # 反射路径
        R_reflected = np.sqrt(distance_m**2 + (radar_height_m + target_height_m)**2)
        
        # 路径差
        delta_R = R_reflected - R_direct
        
        # 相位差
        delta_phi = 2 * np.pi * delta_R / wavelength
        
        # 多径损耗因子
        gamma = surface_reflection_coeff
        multipath_loss = 1 + gamma**2 + 2 * gamma * np.cos(delta_phi)
        
        # 转换为dB
        multipath_loss_db = 10 * np.log10(multipath_loss)
        
        # 干涉图样
        interference_pattern = 1 + gamma**2 - 2 * gamma * np.cos(delta_phi)
        
        return {
            'multipath_loss_db': multipath_loss_db,
            'path_difference_m': delta_R,
            'phase_difference_rad': delta_phi,
            'interference_pattern': interference_pattern,
            'direct_path_m': R_direct,
            'reflected_path_m': R_reflected
        }
    
    def calculate_atmospheric_loss(
        self,
        frequency_ghz: float,
        distance_m: float,
        temperature_c: float = 15,
        humidity_percent: float = 50,
        pressure_hpa: float = 1013.25
    ) -> float:
        """
        计算大气损耗
        
        参数:
            frequency_ghz: 频率（GHz）
            distance_m: 距离（m）
            temperature_c: 温度（℃）
            humidity_percent: 相对湿度（%）
            pressure_hpa: 气压（hPa）
            
        返回:
            大气损耗（dB）
        """
        # 简化的ITU大气衰减模型
        # 对于S波段（3GHz）典型值
        if frequency_ghz < 3:
            attenuation_db_per_km = 0.01
        elif frequency_ghz < 6:
            attenuation_db_per_km = 0.02
        elif frequency_ghz < 10:
            attenuation_db_per_km = 0.05
        elif frequency_ghz < 20:
            attenuation_db_per_km = 0.1
        elif frequency_ghz < 30:
            attenuation_db_per_km = 0.2
        else:
            attenuation_db_per_km = 0.5
        
        # 转换为dB/km
        loss_db = attenuation_db_per_km * (distance_m / 1000)
        
        return loss_db
    
    def calculate_turbine_rcs(
        self,
        turbine: TurbineParameters,
        frequency_ghz: float,
        aspect_angle_deg: float
    ) -> float:
        """
        计算风机RCS
        
        参数:
            turbine: 风机参数
            frequency_ghz: 频率（GHz）
            aspect_angle_deg: 视角（度）
            
        返回:
            风机RCS（m²）
        """
        # 根据风机型号和RCS配置文件
        if turbine.rcs_profile == "small":
            base_rcs = 10.0
        elif turbine.rcs_profile == "medium":
            base_rcs = 50.0
        elif turbine.rcs_profile == "large":
            base_rcs = 100.0
        else:
            base_rcs = 30.0
        
        # 频率影响
        wavelength = self.wavelength(frequency_ghz)
        freq_factor = 1.0 + 0.1 * (frequency_ghz - 3)  # 频率越高，RCS可能越小
        
        # 视角影响
        aspect_rad = np.radians(aspect_angle_deg)
        aspect_factor = 1.0 + 0.5 * np.cos(2 * aspect_rad)  # 正面和侧面RCS较大
        
        # 叶片材料影响
        if turbine.blade_material == "复合材料":
            material_factor = 1.0
        elif turbine.blade_material == "金属":
            material_factor = 1.2
        else:
            material_factor = 1.1
        
        # 计算总RCS
        rcs = base_rcs * freq_factor * aspect_factor * material_factor
        
        return rcs
    
    def calculate_turbine_shadowing(
        self,
        radar_position: Dict[str, float],
        turbine_position: Dict[str, float],
        target_position: Dict[str, float],
        turbine_height_m: float,
        turbine_diameter_m: float
    ) -> Dict[str, float]:
        """
        计算风机遮挡效应
        
        参数:
            radar_position: 雷达位置 {lat, lon, alt}
            turbine_position: 风机位置 {lat, lon, alt}
            target_position: 目标位置 {lat, lon, alt}
            turbine_height_m: 风机高度（m）
            turbine_diameter_m: 风机直径（m）
            
        返回:
            遮挡效应计算结果
        """
        # 简化计算：判断目标是否在风机阴影区内
        # 实际应用中应使用更精确的几何计算
        
        # 计算距离
        def distance_3d(pos1, pos2):
            dx = pos1['lat'] - pos2['lat']
            dy = pos1['lon'] - pos2['lon']
            dz = pos1['alt'] - pos2['alt']
            return np.sqrt(dx**2 + dy**2 + dz**2)
        
        R_rt = distance_3d(radar_position, turbine_position)
        R_tt = distance_3d(turbine_position, target_position)
        R_rt_total = distance_3d(radar_position, target_position)
        
        # 计算角度
        # 这里简化处理，实际应计算几何关系
        shadow_angle = np.degrees(np.arctan(turbine_diameter_m / (2 * R_rt)))
        
        # 估算阴影区
        shadow_length = turbine_height_m * R_tt / R_rt
        
        # 遮挡概率（简化模型）
        shadow_probability = min(0.3, turbine_diameter_m / (2 * R_rt_total))
        
        return {
            'shadow_angle_deg': shadow_angle,
            'shadow_length_m': shadow_length,
            'shadow_probability': shadow_probability,
            'radar_turbine_distance_m': R_rt,
            'turbine_target_distance_m': R_tt
        }
    
    def calculate_detection_probability(
        self,
        snr_db: float,
        pfa: float = 1e-6,
        integration_pulses: int = 1
    ) -> float:
        """
        计算检测概率
        
        参数:
            snr_db: 信噪比（dB）
            pfa: 虚警概率
            integration_pulses: 积累脉冲数
            
        返回:
            检测概率
        """
        # Swerling模型（Swerling I）
        snr_linear = self.db_to_linear(snr_db)
        
        # 门限
        threshold = -np.log(pfa)
        
        # 检测概率（简化计算）
        if snr_linear <= 0:
            pd = 0.0
        else:
            # 使用Marcum Q函数近似
            beta = np.sqrt(2 * snr_linear)
            pd = 0.5 * (1 + math.erf((beta - threshold) / np.sqrt(2)))
        
        # 限制在[0,1]范围内
        pd = max(0.0, min(1.0, pd))
        
        return pd
    
    def calculate_range_resolution(
        self,
        pulse_width_us: float,
        bandwidth_hz: Optional[float] = None
    ) -> float:
        """
        计算距离分辨率
        
        参数:
            pulse_width_us: 脉冲宽度（微秒）
            bandwidth_hz: 带宽（Hz），如果为None则从脉冲宽度计算
            
        返回:
            距离分辨率（米）
        """
        if bandwidth_hz is None:
            # 从脉冲宽度计算
            delta_R = self.c * pulse_width_us * 1e-6 / 2
        else:
            # 从带宽计算
            delta_R = self.c / (2 * bandwidth_hz)
        
        return delta_R
    
    def calculate_velocity_resolution(
        self,
        frequency_ghz: float,
        dwell_time_s: float
    ) -> float:
        """
        计算速度分辨率
        
        参数:
            frequency_ghz: 频率（GHz）
            dwell_time_s: 驻留时间（秒）
            
        返回:
            速度分辨率（m/s）
        """
        wavelength = self.wavelength(frequency_ghz)
        delta_v = wavelength / (2 * dwell_time_s)
        return delta_v
    
    def calculate_clutter_power(
        self,
        radar: RadarParameters,
        clutter_rcs_m2: float,
        distance_m: float
    ) -> float:
        """
        计算杂波功率
        
        参数:
            radar: 雷达参数
            clutter_rcs_m2: 杂波RCS（m²）
            distance_m: 距离（m）
            
        返回:
            杂波功率（dB）
        """
        # 使用雷达方程计算杂波功率
        wavelength = self.wavelength(radar.frequency_ghz)
        
        Pt = radar.peak_power_w
        Gt = self.db_to_linear(radar.antenna_gain_db)
        sigma_c = clutter_rcs_m2
        
        Pc = (Pt * Gt**2 * wavelength**2 * sigma_c) / ((4 * np.pi)**3 * distance_m**4)
        
        # 系统损耗
        Ls = self.db_to_linear(radar.system_losses_db)
        
        Pc_total = Pc / Ls
        
        return self.linear_to_db(Pc_total)
    
    def calculate_bistatic_geometry(
        self,
        transmitter_position: Dict[str, float],
        receiver_position: Dict[str, float],
        target_position: Dict[str, float]
    ) -> Dict[str, float]:
        """
        计算双基地几何
        
        参数:
            transmitter_position: 发射机位置
            receiver_position: 接收机位置
            target_position: 目标位置
            
        返回:
            双基地几何参数
        """
        def distance_3d(pos1, pos2):
            dx = pos1['lat'] - pos2['lat']
            dy = pos1['lon'] - pos2['lon']
            dz = pos1['alt'] - pos2['alt']
            return np.sqrt(dx**2 + dy**2 + dz**2)
        
        R_t = distance_3d(transmitter_position, target_position)
        R_r = distance_3d(receiver_position, target_position)
        R_b = distance_3d(transmitter_position, receiver_position)
        
        # 双基地角
        cos_beta = (R_t**2 + R_r**2 - R_b**2) / (2 * R_t * R_r)
        cos_beta = max(-1.0, min(1.0, cos_beta))
        beta = np.degrees(np.arccos(cos_beta))
        
        # 双基地距离
        bistatic_range = R_t + R_r
        
        return {
            'transmitter_range_m': R_t,
            'receiver_range_m': R_r,
            'bistatic_range_m': bistatic_range,
            'bistatic_angle_deg': beta,
            'baseline_m': R_b
        }
    
    def calculate_spectrum_analysis(
        self,
        signal_power_db: float,
        noise_power_db: float,
        bandwidth_hz: float,
        num_samples: int = 1024
    ) -> Dict[str, Any]:
        """
        计算频谱分析
        
        参数:
            signal_power_db: 信号功率（dB）
            noise_power_db: 噪声功率（dB）
            bandwidth_hz: 带宽（Hz）
            num_samples: 采样点数
            
        返回:
            频谱分析结果
        """
        # 生成信号
        signal_power = self.db_to_linear(signal_power_db)
        noise_power = self.db_to_linear(noise_power_db)
        
        # 生成仿真信号
        np.random.seed(42)
        t = np.linspace(0, 1, num_samples)
        
        # 信号成分
        signal = np.sqrt(2 * signal_power) * np.sin(2 * np.pi * 0.1 * t)
        
        # 噪声成分
        noise = np.sqrt(noise_power) * np.random.randn(num_samples)
        
        # 总信号
        total_signal = signal + noise
        
        # 计算频谱
        frequencies = np.fft.fftfreq(num_samples, 1/bandwidth_hz)
        spectrum = np.abs(np.fft.fft(total_signal))
        
        # 找到峰值频率
        peak_idx = np.argmax(spectrum[:num_samples//2])
        peak_frequency = frequencies[peak_idx]
        peak_power = spectrum[peak_idx]
        
        return {
            'frequencies_hz': frequencies[:num_samples//2],
            'spectrum': spectrum[:num_samples//2],
            'peak_frequency_hz': peak_frequency,
            'peak_power': peak_power,
            'signal_to_noise_ratio_db': signal_power_db - noise_power_db
        }
    
    def calculate_interference(
        self,
        desired_signal_power_db: float,
        interference_signal_power_db: float,
        frequency_separation_hz: float,
        bandwidth_hz: float
    ) -> Dict[str, float]:
        """
        计算干扰
        
        参数:
            desired_signal_power_db: 期望信号功率（dB）
            interference_signal_power_db: 干扰信号功率（dB）
            frequency_separation_hz: 频率间隔（Hz）
            bandwidth_hz: 带宽（Hz）
            
        返回:
            干扰计算结果
        """
        # 转换为线性
        P_d = self.db_to_linear(desired_signal_power_db)
        P_i = self.db_to_linear(interference_signal_power_db)
        
        # 计算载干比
        CIR_linear = P_d / P_i
        CIR_db = self.linear_to_db(CIR_linear)
        
        # 计算干扰抑制因子
        if frequency_separation_hz > bandwidth_hz:
            # 频率分离较大，干扰较小
            rejection_factor = frequency_separation_hz / bandwidth_hz
        else:
            # 频率重叠，干扰较大
            rejection_factor = 1.0
        
        # 有效CIR
        effective_CIR_db = CIR_db + 10 * np.log10(rejection_factor)
        
        # 干扰余量
        interference_margin_db = effective_CIR_db - 20  # 假设需要20dB的CIR余量
        
        return {
            'carrier_to_interference_db': CIR_db,
            'effective_cir_db': effective_CIR_db,
            'interference_margin_db': interference_margin_db,
            'rejection_factor': rejection_factor,
            'is_acceptable': interference_margin_db > 0
        }
    
    def perform_comprehensive_analysis(
        self,
        radar: RadarParameters,
        target: TargetParameters,
        turbines: Optional[List[TurbineParameters]] = None,
        include_turbine_effects: bool = True
    ) -> CalculationResults:
        """
        执行综合分析
        
        参数:
            radar: 雷达参数
            target: 目标参数
            turbines: 风机列表
            include_turbine_effects: 是否包含风机影响
            
        返回:
            综合分析结果
        """
        # 基本雷达方程计算
        radar_eq = self.calculate_radar_range_equation(radar, target)
        
        # 信噪比
        snr_db = self.calculate_snr(radar, target)
        
        # 多普勒频率
        doppler_freq = self.calculate_doppler_frequency(
            radar.frequency_ghz,
            target.velocity_ms
        )
        
        # 距离分辨率
        range_res = self.calculate_range_resolution(radar.pulse_width_us)
        
        # 速度分辨率
        # 假设驻留时间为1/PRF
        dwell_time = 1.0 / radar.prf_hz
        velocity_res = self.calculate_velocity_resolution(
            radar.frequency_ghz,
            dwell_time
        )
        
        # 检测概率
        detection_prob = self.calculate_detection_probability(snr_db)
        
        # 多径效应
        multipath = self.calculate_multipath_effect(
            radar.antenna_height_m,
            target.altitude_m,
            target.distance_m,
            radar.frequency_ghz
        )
        
        # 初始化干扰和杂波水平
        interference_level_db = -100  # 默认值
        clutter_power_db = -120  # 默认值
        
        # 如果有风机，计算风机影响
        bistatic_range = 0
        time_delay = 0
        phase_shift = 0
        
        if include_turbine_effects and turbines:
            # 计算风机RCS
            total_turbine_rcs = 0
            for turbine in turbines:
                # 简化：假设所有风机在相同方位
                turbine_rcs = self.calculate_turbine_rcs(
                    turbine,
                    radar.frequency_ghz,
                    target.azimuth_deg
                )
                total_turbine_rcs += turbine_rcs
            
            # 风机引起的额外杂波
            if total_turbine_rcs > 0:
                clutter_power_db = self.calculate_clutter_power(
                    radar,
                    total_turbine_rcs,
                    target.distance_m
                )
            
            # 风机引起的干扰（简化模型）
            interference_level_db = -80 + 10 * np.log10(len(turbines))
            
            # 双基地效应
            bistatic_range = target.distance_m * 1.1  # 增加10%
            time_delay = bistatic_range / self.c * 1e6  # 微秒
            phase_shift = 2 * np.pi * bistatic_range / self.wavelength(radar.frequency_ghz)
        
        # 创建结果对象
        results = CalculationResults(
            snr_db=snr_db,
            received_power_db=radar_eq['received_power_db'],
            doppler_frequency_hz=doppler_freq,
            range_resolution_m=range_res,
            velocity_resolution_ms=velocity_res,
            detection_probability=detection_prob,
            multipath_loss_db=multipath['multipath_loss_db'],
            interference_level_db=interference_level_db,
            clutter_power_db=clutter_power_db,
            bistatic_range_m=bistatic_range,
            time_delay_us=time_delay,
            phase_shift_rad=phase_shift
        )
        
        return results
    
    def calculate_scenario_comparison(
        self,
        scenario_without_turbines: Dict[str, Any],
        scenario_with_turbines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算有/无风机场景对比
        
        参数:
            scenario_without_turbines: 无风机场景数据
            scenario_with_turbines: 有风机场景数据
            
        返回:
            对比分析结果
        """
        comparison = {}
        
        # 提取关键指标
        keys = [
            'snr_db', 'received_power_db', 'detection_probability',
            'multipath_loss_db', 'interference_level_db', 'clutter_power_db'
        ]
        
        for key in keys:
            value_without = scenario_without_turbines.get(key, 0)
            value_with = scenario_with_turbines.get(key, 0)
            
            if isinstance(value_without, (int, float)) and isinstance(value_with, (int, float)):
                # 计算差值
                difference = value_with - value_without
                percent_change = 0
                if value_without != 0:
                    percent_change = (difference / abs(value_without)) * 100
                
                comparison[f'{key}_without'] = value_without
                comparison[f'{key}_with'] = value_with
                comparison[f'{key}_difference'] = difference
                comparison[f'{key}_percent_change'] = percent_change
                
                # 评估影响程度
                if abs(percent_change) > 20:
                    impact_level = "高"
                elif abs(percent_change) > 10:
                    impact_level = "中"
                elif abs(percent_change) > 5:
                    impact_level = "低"
                else:
                    impact_level = "可忽略"
                
                comparison[f'{key}_impact'] = impact_level
        
        return comparison
    
    def generate_performance_metrics(
        self,
        calculation_results: CalculationResults,
        threshold_snr_db: float = 13
    ) -> Dict[str, Any]:
        """
        生成性能指标
        
        参数:
            calculation_results: 计算结果
            threshold_snr_db: 信噪比门限
            
        返回:
            性能指标
        """
        results = calculation_results.to_dict()
        
        # 检测性能
        detection_performance = "可检测" if results['snr_db'] > threshold_snr_db else "不可检测"
        
        # 跟踪性能
        tracking_capability = "可跟踪" if results['detection_probability'] > 0.9 else "可检测但跟踪困难" if results['detection_probability'] > 0.5 else "跟踪困难"
        
        # 分辨率性能
        range_res_quality = "高" if results['range_resolution_m'] < 100 else "中" if results['range_resolution_m'] < 500 else "低"
        velocity_res_quality = "高" if results['velocity_resolution_ms'] < 1 else "中" if results['velocity_resolution_ms'] < 5 else "低"
        
        # 干扰影响
        interference_impact = "严重" if results['interference_level_db'] > -60 else "中等" if results['interference_level_db'] > -80 else "轻微"
        
        # 杂波影响
        clutter_impact = "严重" if results['clutter_power_db'] > -80 else "中等" if results['clutter_power_db'] > -100 else "轻微"
        
        # 总体评估
        overall_performance = []
        if detection_performance == "可检测":
            overall_performance.append("满足基本探测需求")
        if tracking_capability == "可跟踪":
            overall_performance.append("满足跟踪需求")
        if range_res_quality == "高":
            overall_performance.append("距离分辨率高")
        if interference_impact == "轻微":
            overall_performance.append("干扰影响小")
        
        overall_score = len(overall_performance) / 5  # 5个评估维度
        
        return {
            'detection_performance': detection_performance,
            'tracking_capability': tracking_capability,
            'range_resolution_quality': range_res_quality,
            'velocity_resolution_quality': velocity_res_quality,
            'interference_impact': interference_impact,
            'clutter_impact': clutter_impact,
            'overall_performance': overall_performance,
            'overall_score': overall_score,
            'recommendations': self.generate_recommendations(results)
        }
    
    def generate_recommendations(
        self,
        results: Dict[str, float]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于SNR的建议
        if results['snr_db'] < 10:
            recommendations.append("建议增加雷达发射功率或天线增益以提高信噪比")
        
        # 基于检测概率的建议
        if results['detection_probability'] < 0.8:
            recommendations.append("建议增加脉冲积累数以提高检测概率")
        
        # 基于干扰的建议
        if results['interference_level_db'] > -70:
            recommendations.append("建议采取频率捷变或极化滤波以抑制干扰")
        
        # 基于杂波的建议
        if results['clutter_power_db'] > -90:
            recommendations.append("建议采用MTI或STC技术抑制杂波")
        
        # 基于多径的建议
        if abs(results['multipath_loss_db']) > 3:
            recommendations.append("建议优化雷达高度或采用低仰角波束抑制多径效应")
        
        return recommendations

# 实例化全局计算器
radar_calculator = RadarCalculator()

# 辅助函数
def create_radar_parameters_from_config(config: Dict[str, Any]) -> RadarParameters:
    """从配置创建雷达参数"""
    return RadarParameters(
        frequency_ghz=config.get('frequency_ghz', 3.0),
        peak_power_w=config.get('peak_power_w', 1000000),
        antenna_gain_db=config.get('antenna_gain_db', 40),
        beam_width_deg=config.get('beam_width_deg', 1.0),
        pulse_width_us=config.get('pulse_width_us', 2.0),
        prf_hz=config.get('prf_hz', 300),
        noise_figure_db=config.get('noise_figure_db', 3.0),
        system_losses_db=config.get('system_losses_db', 6.0),
        antenna_height_m=config.get('antenna_height_m', 30)
    )

def create_target_parameters_from_config(config: Dict[str, Any]) -> TargetParameters:
    """从配置创建目标参数"""
    return TargetParameters(
        rcs_m2=config.get('rcs_m2', 10.0),
        distance_m=config.get('distance_m', 100000),
        velocity_ms=config.get('velocity_ms', 250),
        altitude_m=config.get('altitude_m', 10000),
        azimuth_deg=config.get('azimuth_deg', 0),
        elevation_deg=config.get('elevation_deg', 5)
    )

def create_turbine_parameters_from_config(config: Dict[str, Any]) -> TurbineParameters:
    """从配置创建风机参数"""
    return TurbineParameters(
        height_m=config.get('height_m', 150),
        rotor_diameter_m=config.get('rotor_diameter_m', 150),
        position=config.get('position', {'lat': 39.0, 'lon': 119.0, 'alt': 0}),
        orientation_deg=config.get('orientation_deg', 0),
        rcs_profile=config.get('rcs_profile', 'medium'),
        blade_material=config.get('blade_material', '复合材料')
    )
