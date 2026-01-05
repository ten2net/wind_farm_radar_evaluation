"""
雷达仿真器服务模块
基于radarsimpy进行雷达系统仿真
提供目标检测、信号处理和性能评估功能
"""

import numpy as np
import radarsimpy as rsp
from radarsimpy.simulator import sim_radar
from radarsimpy import Radar, Transmitter, Receiver
from radarsimpy.processing import range_doppler_fft,range_fft,doppler_fft
from scipy.fft import fft, fftshift, fftfreq

import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from models.radar_models import RadarModel, RadarBand, WindowType
from models.simulation_models import (
    TargetParameters, SimulationScenario, RadarDetection, 
    SimulationParameters, SimulationResults, RCSModel, TargetType
)
from controllers.radar_controller import RadarController
from utils.helpers import (
    db_to_linear, linear_to_db, coordinate_transform_cartesian_to_spherical, # type: ignore
    coordinate_transform_spherical_to_cartesian, format_distance, format_frequency # type: ignore
)


class SimulationMode(Enum):
    """仿真模式"""
    SINGLE_TARGET = "单目标"
    MULTI_TARGET = "多目标"
    TRACKING = "跟踪"
    CLUTTER = "杂波环境"


class ProcessingChain(Enum):
    """处理链类型"""
    BASIC = "基础处理"
    MTI = "动目标显示"
    MTD = "动目标检测"
    ADVANCED = "高级处理"


@dataclass
class SimulationConfig:
    """仿真配置"""
    mode: SimulationMode = SimulationMode.SINGLE_TARGET
    processing: ProcessingChain = ProcessingChain.BASIC
    duration: float = 10.0  # 仿真时长(秒)
    time_step: float = 0.1  # 时间步长(秒)
    noise_temperature: float = 290.0  # 噪声温度(K)
    system_losses_db: float = 3.0  # 系统损耗(dB)
    clutter_enabled: bool = False
    rain_rate: float = 0.0  # 降雨率(mm/h)


class RadarSimulator:
    """雷达仿真器 - 基于radarsimpy"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.controller = RadarController()
        self.current_simulation = None
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('RadarSimulator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_radarsimpy_radar(self, radar_model: RadarModel) -> Radar:
        """
        将我们的雷达模型转换为radarsimpy的Radar对象
        
        Args:
            radar_model: 雷达模型
            
        Returns:
            radarsimpy雷达对象
        """
        if not radar_model.transmitter:
            raise ValueError("雷达缺少发射机参数")
        
        # 构建发射机参数
        transmitter = self._build_transmitter(radar_model)
        
        # 构建接收机参数
        receiver = self._build_receiver(radar_model)
        
        # 构建雷达位置和方向
        location = [0.0, 0.0, 0.0]  # 默认位置，可以在场景中调整
        speed = [0.0, 0.0, 0.0]  # 静止雷达
        
        # 创建radarsimpy雷达对象
        additional_params = radar_model.basic_info()
        radar = Radar(
            transmitter=transmitter,
            receiver=receiver,
            location=location,
            speed=speed,
            rotation=[0.0, 0.0, 0.0],  # 默认方向，可以在场景中调整
            rotation_rate=[0.0, 0.0, 0.0],  # 静止雷达
            **additional_params
        )
        
        return radar
    
    def _build_transmitter(self, radar_model: RadarModel) -> Transmitter:
        """构建发射机参数"""
        tx = radar_model.transmitter
        
        # 计算带宽（如果没有指定，使用脉冲宽度的倒数）
        if hasattr(tx, 'bandwidth_hz') and tx.bandwidth_hz: # type: ignore
            bandwidth_hz = tx.bandwidth_hz # type: ignore
        else:
            bandwidth_hz = 1.0 / tx.pulse_width_s if tx.pulse_width_s > 0 else 1e6 # type: ignore
            
        # 计算频率范围
        freq_start = tx.frequency_hz - bandwidth_hz / 2 # type: ignore
        freq_end = tx.frequency_hz + bandwidth_hz / 2 # type: ignore                   
        
        # 创建发射通道
        tx_channel = {
            'location': [0, 0, 0],
            'speed': [0, 0, 0],
            **self._build_antenna_pattern(radar_model)
        } 
        
        # 创建发射机
        transmitter = Transmitter(
            f=[freq_start, freq_end],
            t=tx.pulse_width_s, # type: ignore
            tx_power=tx.power_w, # type: ignore
            prp=1.0 / tx.prf_hz, # type: ignore
            pulses=tx.pulses, # type: ignore
            channels=[tx_channel]
        )
        
        return transmitter
    
    def _build_receiver(self, radar_model: RadarModel) -> Receiver:
        """构建接收机参数"""
        if not radar_model.antenna:
            raise ValueError("雷达缺少天线参数")
        
        rx = radar_model.receiver
        rx_channel = {
            'location': [0, 0, 0],       # 接收机位置，可以在场景中调整
            'speed': [0, 0, 0],     # 接收机速度，可以在场景中调整
            **self._build_antenna_pattern(radar_model)
        }
        
        # 创建接收机
        receiver = Receiver(
            fs=rx.sampling_rate_hz, # type: ignore
            noise_figure=rx.noise_figure_db, # type: ignore
            rf_gain=rx.rf_gain_dbi,
            load_resistor=rx.load_resistor,
            baseband_gain=rx.baseband_gain_db,
            channels=[rx_channel]
        ) 
        return receiver
    def _build_antenna_pattern(self, radar_model: RadarModel) -> Dict[str, Any]:
        """构建天线方向图（简化模型）"""
        if not radar_model.antenna:
            return {}
        
        ant = radar_model.antenna
        
        # 创建简化的天线方向图
        az_beamwidth = np.radians(ant.azimuth_beamwidth)
        el_beamwidth = np.radians(ant.elevation_beamwidth)
        
        # 生成方向图数据（简化模型）
        az_angles = np.linspace(-az_beamwidth*2, az_beamwidth*2, 100)
        el_angles = np.linspace(-el_beamwidth*2, el_beamwidth*2, 100)
        
        az_pattern = 10 * np.log10(np.sinc(az_angles / az_beamwidth)**2)
        el_pattern = 10 * np.log10(np.sinc(el_angles / el_beamwidth)**2)
        
        return {
            'azimuth_angle': az_angles,
            'azimuth_pattern': az_pattern,
            'elevation_angle': el_angles,
            'elevation_pattern': el_pattern
        }
    
    def run_simulation(self, scenario: SimulationScenario, 
                      radar_models: List[RadarModel],
                      config: SimulationConfig = None) -> SimulationResults: # type: ignore
        """
        运行雷达仿真
        
        Args:
            scenario: 仿真场景
            radar_models: 雷达模型列表
            config: 仿真配置
            
        Returns:
            仿真结果
        """
        if config is None:
            config = SimulationConfig()
        
        self.logger.info(f"开始仿真: {scenario.name}")
        start_time = datetime.now()
        
        # 验证场景
        if not scenario.validate():
            raise ValueError("仿真场景参数无效")
        
        # 创建仿真参数
        sim_params = SimulationParameters(
            simulation_id=f"SIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            scenario=scenario,
            radars=radar_models
        )
        
        # 初始化结果容器
        results = SimulationResults(parameters=sim_params)
        
        try:
            # 对每个雷达运行仿真
            for radar_model in radar_models:
                radar_results = self._simulate_single_radar(
                    radar_model, scenario, config, results
                )
                results.raw_data[radar_model.radar_id] = radar_results
            
            # 计算性能指标
            results.calculate_metrics()
            
            # 记录仿真统计
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"仿真完成，耗时: {duration:.2f}秒")
            self.logger.info(f"检测到 {len(results.detections)} 个目标")
            
        except Exception as e:
            self.logger.error(f"仿真失败: {str(e)}")
            raise
        
        self.current_simulation = results
        return results
    
    def _simulate_single_radar(self, radar_model: RadarModel, 
                             scenario: SimulationScenario,
                             config: SimulationConfig,
                             results: SimulationResults) -> Dict[str, Any]:
        """
        对单个雷达进行仿真
        
        Args:
            radar_model: 雷达模型
            scenario: 仿真场景
            config: 仿真配置
            results: 结果容器
            
        Returns:
            原始仿真数据
        """
        radar_id = radar_model.radar_id
        self.logger.info(f"仿真雷达: {radar_model.name}")
        
        # 创建radarsimpy雷达
        radar = self.create_radarsimpy_radar(radar_model)
        
        # # 设置雷达位置
        # if radar_id in scenario.radar_positions:
        #     radar.location = scenario.radar_positions[radar_id].tolist()
        
        # 创建目标
        targets = []
        for target in scenario.targets:
            targets.append(target.to_radarsimpy_ideal_target())
        
        # 运行仿真
        raw_data = {}
        # 创建场景
        if len(targets) > 0:  # 防止没有目标时浪费资源  
            timesteps = int(scenario.duration / scenario.time_step)
            
            for t in range(timesteps):
                timestamp = t * scenario.time_step
                data = sim_radar(radar, targets, density=0.1)                
                # 获取回波数据
                echo_data = data["baseband"] + data["noise"]   
                # 更新目标位置
                self._update_targets_position(scenario.targets, timestamp)
                
                # 信号处理
                processed_data = self._process_signals(
                    echo_data, radar_model, config, timestamp
                )
                
                # 目标检测
                detections = self._detect_targets(
                    processed_data, radar_model, scenario.targets, timestamp
                )
                
                # 记录检测结果
                for detection in detections:
                    results.add_detection(detection)
                
                # 保存原始数据
                raw_data[timestamp] = {
                    'baseband':  data["baseband"],
                    'noise_data': data['noise'],
                    'echo_data': echo_data,
                    'processed': processed_data,
                    'detections': [d.to_dict() for d in detections]
                }
        
        return raw_data
    
    def _update_targets_position(self, targets: List[TargetParameters], 
                               timestamp: float):
        """更新目标位置"""
        for i, target in enumerate(targets):
            # 计算新位置
            new_position = target.position + target.velocity * timestamp
            
            target.position = new_position.tolist()

    
    # def _simulate_baseband_data(self, scene: Scene, radar: Radar) -> np.ndarray:
    #     """模拟基带数据生成"""
    #     # 这里应该使用radarsimpy的实际仿真功能
    #     # 由于时间关系，我们创建一个简化的模拟数据
        
    #     # 模拟参数
    #     n_pulses = radar.transmitter.pulses
    #     n_samples = 1024  # 采样点数
        
    #     # 创建噪声基底
    #     noise_power = 1e-12  # 噪声功率
    #     baseband_data = np.random.normal(0, np.sqrt(noise_power), 
    #                                    (n_pulses, n_samples)) + \
    #                   1j * np.random.normal(0, np.sqrt(noise_power), 
    #                                      (n_pulses, n_samples))
        
    #     # 添加目标回波（简化模型）
    #     for target in scene.targets:
    #         # 计算目标距离和速度
    #         target_range = np.linalg.norm(target.location)
    #         target_velocity = np.linalg.norm(target.speed)
            
    #         # 计算时延和多普勒频移
    #         time_delay = 2 * target_range / 3e8  # 往返时延
    #         doppler_freq = 2 * target_velocity / radar.transmitter.wavelength
            
    #         # 在基带数据中添加目标信号
    #         for pulse in range(n_pulses):
    #             # 计算目标信号幅度（与距离和RCS相关）
    #             signal_power = target.rcs / (target_range ** 4)  # 简化雷达方程
    #             signal_amplitude = np.sqrt(signal_power)
                
    #             # 计算目标所在的距离单元
    #             range_bin = int(time_delay * radar.receiver.fs)
    #             if 0 <= range_bin < n_samples:
    #                 # 添加目标信号（考虑多普勒相位）
    #                 phase = 2 * np.pi * doppler_freq * pulse / radar.transmitter.prp
    #                 baseband_data[pulse, range_bin] += signal_amplitude * np.exp(1j * phase)
        
    #     return baseband_data
    
    def _create_dummy_baseband_data(self, radar: Radar) -> np.ndarray:
        """创建虚拟基带数据（用于测试）"""
        n_pulses = radar.transmitter.pulses
        n_samples = 1024
        
        # 创建随机噪声数据
        return np.random.randn(n_pulses, n_samples) + \
               1j * np.random.randn(n_pulses, n_samples)
    
    def _process_signals(self, baseband_data: np.ndarray, 
                        radar_model: RadarModel,
                        config: SimulationConfig, 
                        timestamp: float) -> Dict[str, Any]:
        """
        信号处理链
        
        Args:
            baseband_data: 基带数据
            radar_model: 雷达模型
            config: 仿真配置
            timestamp: 时间戳
            
        Returns:
            处理后的数据
        """
        processed_data = {
            'timestamp': timestamp,
            'range_profile': None,
            'doppler_profile': None,
            'rd_map': None,
            'detection_map': None
        }
        
        try:
            # 距离处理（脉冲压缩）
            range_profile = self._range_processing(baseband_data, radar_model)
            processed_data['range_profile'] = range_profile
            # 多普勒处理（脉冲压缩）
            range_profile = self._doppler_processing(baseband_data, radar_model)
            processed_data['doppler_profile'] = range_profile
            
            # 多普勒处理
            if config.processing in [ProcessingChain.MTI, ProcessingChain.MTD, ProcessingChain.ADVANCED]:
                doppler_map = self._range_doppler_map(baseband_data)
                processed_data['rd_map'] = doppler_map
            
            # 恒虚警检测
            if config.processing in [ProcessingChain.MTD, ProcessingChain.ADVANCED]:
                detection_map = self._cfar_detection(processed_data, radar_model)
                processed_data['detection_map'] = detection_map
            
        except Exception as e:
            self.logger.error(f"信号处理失败: {str(e)}")
        
        return processed_data
    
    def _get_window_array(self, window_type: WindowType, n: int, beta: float = 14.0) -> np.ndarray:
        """生成窗函数数组"""
        if window_type == WindowType.RECTANGULAR:
            window = np.ones(n)
        elif window_type == WindowType.HANNING:
            window = np.hanning(n)
        elif window_type == WindowType.HAMMING:
            window = np.hamming(n)
        elif window_type == WindowType.BLACKMAN:
            window = np.blackman(n)
        elif window_type == WindowType.KAISER:
            window = np.kaiser(n, beta)
        elif window_type == WindowType.BARTLETT:
            window = np.bartlett(n)
        else:
            window = np.ones(n)
        return window    
    
    def _range_profile(self, echo_data: np.ndarray, window_type: WindowType = WindowType.HANNING,
                      db_scale: bool = True) -> np.ndarray:
        """
        计算距离剖面（使用radarsimpy.processing.range_fft）

        Args:
            echo_data: 雷达回波数据 [脉冲数, 距离门数] 或 [通道数, 脉冲数, 距离门数]
            window_type: 距离维窗函数
            db_scale: 是否使用dB尺度

        Returns:
            ranges: 距离数组
            profile: 距离剖面
        """
        # 生成窗函数
        range_win = self._get_window_array(window_type, echo_data.shape[2])

        # 使用radarsimpy的距离FFT
        range_profile_3d = range_fft(echo_data, rwin=range_win)
        range_profile = np.abs(range_profile_3d)

        if db_scale:
            range_profile = 20 * np.log10(range_profile + 1e-12)

        # # # 计算距离轴
        # # 从雷达系统获取每脉冲采样点数
        # samples_per_pulse = self.radar.sample_prop["samples_per_pulse"]

        # # 计算派生参数
        # self.center_frequency = np.mean(self.frequency)  # 中心频率 (Hz)
        # self.wavelength = speed_of_light / self.center_frequency  # 波长 (m)
        # self.range_resolution = speed_of_light / \
        #     (2 * self.bandwidth)  # 距离分辨率 (m)
        # self.max_unambiguous_range = speed_of_light / \
        #     (2 * self.prf)  # 最大不模糊距离 (m)
        # self.max_unambiguous_velocity = self.wavelength * \
        #     self.prf / 4  # 最大不模糊速度 (m/s)        
        # _, n_pulses, n_samples = echo_data.shape
        # ranges = np.arange(n_samples) * \
        #     self.max_unambiguous_range / n_samples

        return range_profile
    
    def _range_processing(self, baseband_data: np.ndarray, 
                         radar_model: RadarModel) -> np.ndarray:
        """距离处理（脉冲压缩）"""
        # 简化实现 - 实际应使用匹配滤波等算法
        n_pulses, n_samples = baseband_data.shape
        
        # 对每个脉冲进行FFT得到距离像
        range_profiles =self._range_profile(baseband_data, window_type=WindowType.HANNING, db_scale=True)
        
        # 计算距离标度
        range_resolution = 3e8 / (2 * radar_model.transmitter.bandwidth_hz) \
            if radar_model.transmitter.bandwidth_hz else 150  # 默认150m
        
        return np.mean(np.abs(range_profiles), axis=0)  # 平均距离像
    
    def _doppler_profile(self, echo_data: np.ndarray,
                                 window_type: WindowType = WindowType.HANNING,
                                 db_scale: bool = True) -> np.ndarray:
        """
        计算多普勒速度剖面（使用radarsimpy.processing.doppler_fft）

        Args:
            echo_data: 雷达回波数据 [脉冲数, 距离门数] 或 [通道数, 脉冲数, 距离门数]
            window_type: 多普勒维窗函数
            db_scale: 是否使用dB尺度

        Returns:
            velocities: 速度数组
            profile: 多普勒剖面
        """

        # 提取指定距离门的数据
        # doppler_data = echo_data[:, :, range_bin:range_bin+1]  # 保持3D形状

        # 生成窗函数
        doppler_win = self._get_window_array(window_type, echo_data.shape[1])

        # 使用radarsimpy的多普勒FFT
        doppler_profile_3d = doppler_fft(echo_data, dwin=doppler_win)
        doppler_profile = np.abs(doppler_profile_3d)
        doppler_profile_shifted = fftshift(doppler_profile, axes=1)

        if db_scale:
            doppler_profile_shifted = 20 * \
                np.log10(doppler_profile_shifted + 1e-12)

        # # 计算速度轴
        # velocities = fftshift(fftfreq(echo_data.shape[1], 1/self.prf))
        # velocities = velocities * self.wavelength / 2  # 转换为速度
        
        return doppler_profile_shifted

    
    def _doppler_processing(self, baseband_data: np.ndarray, 
                         radar_model: RadarModel) -> np.ndarray:
        """多普勒处理"""
        # 对每个脉冲进行FFT得到距离像
        doppler_profiles =self._doppler_profile(baseband_data, window_type=WindowType.HANNING, db_scale=True)
        
        # 计算距离标度
        range_resolution = 3e8 / (2 * radar_model.transmitter.bandwidth_hz) \
            if radar_model.transmitter.bandwidth_hz else 150  # 默认150m
        
        return np.mean(np.abs(doppler_profiles), axis=1)  # 平均多普勒像        
    def _range_doppler_map(self, echo_data: np.ndarray,
                          range_window: WindowType = WindowType.HANNING,
                          doppler_window: WindowType = WindowType.HANNING,
                          db_scale: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        计算距离-多普勒图（使用radarsimpy.processing.range_doppler_fft）

        Args:
            echo_data: 雷达回波数据 [脉冲数, 距离门数] 或 [通道数, 脉冲数, 距离门数]
            range_window: 距离维窗函数
            doppler_window: 多普勒维窗函数
            db_scale: 是否使用dB尺度

        Returns:
            ranges: 距离数组
            velocities: 速度数组
            rd_map: 距离-多普勒图
        """
        # 生成窗函数
        range_win = self._get_window_array(range_window, echo_data.shape[2])
        doppler_win = self._get_window_array(doppler_window, echo_data.shape[1])

        # 使用radarsimpy的距离-多普勒FFT
        rd_map_3d = range_doppler_fft(
            echo_data, rwin=range_win, dwin=doppler_win)
        rd_map = np.abs(rd_map_3d)
        
        rd_map_shifted = fftshift(rd_map, axes=1)  # 多普勒维fftshift

        if db_scale:
            rd_map_shifted = 20 * np.log10(rd_map_shifted + 1e-12)

        # 计算距离轴和速度轴
        # ranges = np.arange(self.range_bins) * \
        #     self.max_unambiguous_range / self.range_bins
        # velocities = fftshift(fftfreq(data_3d.shape[1], 1/self.prf))
        # velocities = velocities * self.wavelength / 2

        return rd_map_shifted[0]  # 返回第一个通道的结果     

    
    def _cfar_detection(self, processed_data: Dict[str, Any],
                       radar_model: RadarModel) -> np.ndarray:
        """恒虚警检测"""
        # 简化CFAR实现
        if processed_data['doppler_map'] is not None:
            data = np.abs(processed_data['doppler_map'])
        else:
            data = np.abs(processed_data['range_profile'])
        
        # 简单的阈值检测
        threshold = np.mean(data) + 3 * np.std(data)  # 3sigma阈值
        detection_map = data > threshold
        
        return detection_map
    
    def _detect_targets(self, processed_data: Dict[str, Any],
                       radar_model: RadarModel,
                       targets: List[TargetParameters],
                       timestamp: float) -> List[RadarDetection]:
        """
        目标检测
        
        Args:
            processed_data: 处理后的数据
            radar_model: 雷达模型
            targets: 目标列表
            timestamp: 时间戳
            
        Returns:
            检测结果列表
        """
        detections = []
        
        if processed_data['detection_map'] is None:
            return detections
        
        try:
            detection_map = processed_data['detection_map']
            
            # 查找检测点
            detection_points = np.where(detection_map)
            
            for i in range(len(detection_points[0])):
                # 创建检测结果
                range_idx = detection_points[1][i] if len(detection_points) > 1 else detection_points[0][i] # type: ignore
                doppler_idx = detection_points[0][i] if len(detection_points) > 1 else 0
                
                # 计算实际距离和速度
                range_res = 3e8 / (2 * radar_model.transmitter.bandwidth_hz) if radar_model.transmitter.bandwidth_hz else 150
                range_val = range_idx * range_res
                
                doppler_res = 1 / (radar_model.transmitter.pulse_width_s * radar_model.transmitter.pulses) \
                    if radar_model.transmitter.pulse_width_s > 0 else 100
                doppler_val = doppler_idx * doppler_res
                
                # 计算信噪比（简化）
                signal_power = np.abs(processed_data['range_profile'][range_idx]) if processed_data['range_profile'] is not None else 1
                noise_power = np.mean(np.abs(processed_data['range_profile'])) if processed_data['range_profile'] is not None else 1
                snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0
                
                # 匹配目标（简化匹配逻辑）
                target_id = self._match_target_to_detection(
                    range_val, doppler_val, targets, radar_model.radar_id
                )
                
                detection = RadarDetection(
                    timestamp=timestamp,
                    radar_id=radar_model.radar_id,
                    target_id=target_id,
                    range=range_val,
                    azimuth=0,  # 简化处理
                    elevation=0,  # 简化处理
                    doppler=doppler_val,
                    snr=snr_db,
                    detection_confidence=min(1.0, snr_db / 20)  # 置信度基于SNR
                )
                
                detections.append(detection)
                
        except Exception as e:
            self.logger.error(f"目标检测失败: {str(e)}")
        
        return detections
    
    def _match_target_to_detection(self, range_val: float, doppler_val: float,
                                  targets: List[TargetParameters], radar_id: str) -> str:
        """将检测与目标匹配"""
        # 简化匹配逻辑 - 实际应使用更复杂的关联算法
        for target in targets:
            # 计算预期距离和速度
            expected_range = np.linalg.norm(target.position)
            expected_doppler = 2 * np.linalg.norm(target.velocity) / \
                             (3e8 / self.controller.get_radar_by_id(radar_id).transmitter.frequency_hz) # type: ignore
            
            range_tolerance = 1000  # 1km容差
            doppler_tolerance = 100  # 100Hz容差
            
            if (abs(range_val - expected_range) < range_tolerance and
                abs(doppler_val - expected_doppler) < doppler_tolerance):
                return target.target_id
        
        return f"unknown_{int(range_val)}_{int(doppler_val)}"
    
    def analyze_performance(self, results: SimulationResults) -> Dict[str, Any]:
        """
        分析仿真性能
        
        Args:
            results: 仿真结果
            
        Returns:
            性能分析结果
        """
        if not results.detections:
            return {"error": "没有检测数据"}
        
        # 计算检测统计
        detection_times = [d.timestamp for d in results.detections]
        time_span = max(detection_times) - min(detection_times) if detection_times else 0
        
        # 按雷达分组
        radar_detections = {}
        for detection in results.detections:
            if detection.radar_id not in radar_detections:
                radar_detections[detection.radar_id] = []
            radar_detections[detection.radar_id].append(detection)
        
        # 计算各雷达性能
        radar_performance = {}
        for radar_id, dets in radar_detections.items():
            snr_values = [d.snr for d in dets]
            confidence_values = [d.detection_confidence for d in dets]
            
            radar_performance[radar_id] = {
                'detection_count': len(dets),
                'avg_snr_db': np.mean(snr_values) if snr_values else 0,
                'max_snr_db': max(snr_values) if snr_values else 0,
                'avg_confidence': np.mean(confidence_values) if confidence_values else 0,
                'detection_rate_hz': len(dets) / time_span if time_span > 0 else 0
            }
        
        # 计算系统级性能
        total_targets = len(set(d.target_id for d in results.detections))
        expected_targets = len(results.parameters.scenario.targets)
        detection_probability = total_targets / expected_targets if expected_targets > 0 else 0
        
        return {
            'simulation_duration_s': results.parameters.scenario.duration,
            'total_detections': len(results.detections),
            'unique_targets_detected': total_targets,
            'expected_targets': expected_targets,
            'detection_probability': detection_probability,
            'time_span_s': time_span,
            'radar_performance': radar_performance,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def export_simulation_data(self, results: SimulationResults, 
                             filename: str) -> bool:
        """
        导出仿真数据
        
        Args:
            results: 仿真结果
            filename: 文件名
            
        Returns:
            成功标志
        """
        try:
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'simulation_id': results.parameters.simulation_id,
                    'scenario_name': results.parameters.scenario.name
                },
                'parameters': self._serialize_parameters(results.parameters),
                'detections': [d.to_dict() for d in results.detections],
                'metrics': results.metrics,
                'performance_analysis': self.analyze_performance(results)
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"仿真数据已导出到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出失败: {str(e)}")
            return False
    
    def _serialize_parameters(self, parameters: SimulationParameters) -> Dict[str, Any]:
        """序列化仿真参数"""
        return {
            'simulation_id': parameters.simulation_id,
            'scenario': {
                'name': parameters.scenario.name,
                'duration': parameters.scenario.duration,
                'target_count': len(parameters.scenario.targets)
            },
            'radar_count': len(parameters.radars),
            'radar_ids': [r.radar_id for r in parameters.radars]
        }
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """获取仿真状态"""
        if self.current_simulation is None:
            return {'status': 'idle', 'message': '没有运行中的仿真'}
        
        return {
            'status': 'completed',
            'simulation_id': self.current_simulation.parameters.simulation_id,
            'detection_count': len(self.current_simulation.detections),
            'completion_time': getattr(self.current_simulation, 'completion_time', '未知')
        }

# 测试代码
if __name__ == "__main__":
    # 创建仿真器实例
    simulator = RadarSimulator()
    
    # 创建测试雷达
    from models.radar_models import RadarFactory, PRESET_RADARS
    
    radar_config = PRESET_RADARS["JY-27B_UHF001"]
    radar = RadarFactory.create_from_config(radar_config)
    
    if radar:
        # 创建测试目标
        target = TargetParameters(
            target_id="test_target_001",
            target_type=TargetType.AIRCRAFT,
            position=np.array([50e3, 0, 10e3]),  # 50km距离
            velocity=np.array([-300, 0, 0]),  # 300m/s速度
            rcs_sqm=5.0,
            rcs_model=RCSModel.SWERLING1
        )
        
        # 创建测试场景
        scenario = SimulationScenario(
            scenario_id="test_scenario_001",
            name="测试仿真场景",
            description="单目标测试场景",
            duration=5.0,
            time_step=0.1,
            radar_positions={"JY-27B_UHF001": np.array([0, 0, 0])},
            targets=[target]
        )
        
        # 运行仿真
        try:
            print("开始雷达仿真测试...")
            results = simulator.run_simulation(scenario, [radar])
            
            # 显示结果
            print(f"仿真完成，检测到 {len(results.detections)} 个目标")
            
            # 分析性能
            performance = simulator.analyze_performance(results)
            print(f"检测概率: {performance.get('detection_probability', 0):.2f}")
            
            # 导出数据
            simulator.export_simulation_data(results, "test_simulation.json")
            print("仿真数据已导出")
            
        except Exception as e:
            print(f"仿真测试失败: {str(e)}")