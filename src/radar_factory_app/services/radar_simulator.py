"""
雷达仿真器服务模块 - 使用新重构的CFAR检测和目标匹配功能
基于radarsimpy进行雷达系统仿真
提供目标检测、信号处理和性能评估功能
"""

from pathlib import Path
import pprint
import traceback
import numpy as np
from numpy.typing import NDArray
import radarsimpy as rsp
from radarsimpy.simulator import sim_radar
from radarsimpy import Radar, Transmitter, Receiver
from scipy.fft import fft, fftshift, fftfreq

import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from radar_factory_app.models.radar_models import RadarModel, RadarBand, WindowType
from radar_factory_app.models.simulation_models import (
    TargetParameters, SimulationScenario, RadarDetection, 
    SimulationParameters, SimulationResults, RCSModel, TargetType
)
from radar_factory_app.controllers.radar_controller import RadarController
from radar_factory_app.utils.helpers import (
    db_to_linear, linear_to_db, coordinate_transform_cartesian_to_spherical, # type: ignore
    coordinate_transform_spherical_to_cartesian, format_distance, format_frequency # type: ignore
)
from services.radar_plotter import RadarPlotter

# 导入新重构的模块
from .cfar_processor import CFARProcessor
from .target_matching import (
    _match_target_to_detection_2d, 
    _match_target_to_detection_1d,
    MatchMethod,
    MatchResult,
    match_radar_detections
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
    duration: float = 1.0  # 仿真时长(秒)
    time_step: float = 0.1  # 时间步长(秒)
    noise_temperature: float = 290.0  # 噪声温度(K)
    system_losses_db: float = 3.0  # 系统损耗(dB)
    clutter_enabled: bool = False
    rain_rate: float = 0.0  # 降雨率(mm/h)
    
    # 新重构功能的配置参数
    cfar_config: Dict[str, Any] = None # type: ignore
    matching_config: Dict[str, Any] = None # type: ignore
    
    def __post_init__(self):
        if self.cfar_config is None:
            self.cfar_config = {
                'detector_type': 'squarelaw',
                'guard_cells': 2,
                'trailing_cells': 10,
                'pfa': 1e-6,
                'min_snr': 10.0,
                'target_type': 'Swerling 0'
            }
        
        if self.matching_config is None:
            self.matching_config = {
                'match_method': MatchMethod.NEAREST_NEIGHBOR,
                'range_tolerance': 2.0,
                'doppler_tolerance': 2.0,
                'max_distance': None
            }


class RadarSimulator:
    """雷达仿真器 - 基于radarsimpy，集成新重构功能"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.controller = RadarController()
        self.current_simulation = None
        self.cfar_processor = None
        self.detection_evaluator = None
        self.plotter = RadarPlotter()
        
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
    
    def _initialize_processing_modules(self, config: SimulationConfig):
        """初始化新重构的处理模块"""
        # 初始化CFAR处理器
        self.cfar_processor = CFARProcessor(
            detector_type=config.cfar_config['detector_type']
        )
        
        self.logger.info("新重构的CFAR处理器和目标匹配模块已初始化")
    
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
        运行雷达仿真 - 使用新重构的检测和匹配功能
        
        Args:
            scenario: 仿真场景
            radar_models: 雷达模型列表
            config: 仿真配置
            
        Returns:
            仿真结果
        """
        if config is None:
            config = SimulationConfig()
        
        # 初始化新重构的处理模块
        self._initialize_processing_modules(config)
        
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
        对单个雷达进行仿真 - 使用新重构的检测和匹配功能
        
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
        
        # 创建目标
        targets = []
        for target in scenario.targets:
            targets.append(target.to_radarsimpy_ideal_target())
        
        print(f"仿真目标数量: {len(targets)}")
        print(f"仿真时长: {scenario.duration}秒, 时间步长: {scenario.time_step}秒")
        pprint.pprint(targets)
        
        # 运行仿真
        raw_data = {}
        if len(targets) > 0:  # 防止没有目标时浪费资源  
            timesteps = int(scenario.duration / scenario.time_step)
            
            # for t in range(timesteps):
            # >>>>>>>>>>
            for t in [0]:  # 临时只运行第一个时间步以加快测试速度
                timestamp = t * scenario.time_step
                
                # 运行radarsimpy仿真
                data = sim_radar(radar, targets, density=0.1)                
                # 获取回波数据
                echo_data = data["baseband"] + data["noise"]   

                # 更新目标位置
                self._update_targets_position(scenario.targets, timestamp)
                
                # 信号处理（使用新重构的CFAR检测）
                processed_data = self._process_signals_with_new_cfar(
                    echo_data, radar_model, config, timestamp
                )
                
                # 目标检测和匹配（使用新重构的目标匹配）
                detections = self._detect_and_match_targets(
                    processed_data, radar_model, scenario.targets, timestamp, config
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
    
    def _process_signals_with_new_cfar(self, baseband_data: np.ndarray, 
                                     radar_model: RadarModel,
                                     config: SimulationConfig, 
                                     timestamp: float) -> Dict[str, Any]:
        """
        使用新重构的CFAR处理器进行信号处理
        
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
            'detection_map': None,
            'cfar_threshold': None,
            'detection_stats': None
        }
        
        try:
            # 距离处理
            range_profile = self._range_processing(baseband_data, radar_model)
            processed_data['range_profile'] = range_profile
            
            # 多普勒处理
            doppler_profile = self._doppler_processing(baseband_data, radar_model)
            processed_data['doppler_profile'] = doppler_profile
            
            # 距离-多普勒处理
            rd_map = self._range_doppler_map(baseband_data)
            processed_data['rd_map'] = rd_map
            
            self.plot_radar(radar_model, processed_data)                       
            
            # 使用新重构的CFAR检测
            detection_results = self._apply_new_cfar_detection(
                processed_data, radar_model, config
            )
            
            # 更新处理数据
            processed_data.update(detection_results)
            
        except Exception as e:
            exec_str = traceback.format_exc()
            self.logger.error(f"信号处理失败: {exec_str}")
        
        return processed_data

    def plot_radar(self, radar_model, processed_data, output_dir: str = "./outputs/radar_plots"):
        # 原有初始化代码保持不变...
        outputs_dir = Path(output_dir)
        outputs_dir.mkdir(parents=True, exist_ok=True)        
        self.plotter.plot_range_doppler_map(
                processed_data['rd_map'],
                radar_model,  # 使用第一个雷达
                save_path=f"{outputs_dir}/range_doppler_map_{radar_model.radar_id}.png", # type: ignore
                show=True
            )
            
        self.plotter.plot_range_profile(
                processed_data['range_profile'],
                radar_model,
                # detections=detections,
                # cfar_threshold=processed_data.get('cfar_threshold'),
                # timestamp=first_timestamp,
                save_path=f"{outputs_dir}/range_profile_{radar_model.radar_id}.png", # type: ignore
                show=True
            )            
        self.plotter.plot_doppler_profile(
                processed_data['doppler_profile'],
                radar_model,
                # detections=detections,
                # cfar_threshold=processed_data.get('cfar_threshold'),
                # timestamp=first_timestamp,
                save_path=f"{outputs_dir}/doppler_profile_{radar_model.radar_id}.png", # type: ignore
                show=True
            ) 
            
        self.plotter.plot_antenna_pattern(
                radar_model,
                pattern_type="both",
                save_path=f"{outputs_dir}/antenna_pattern_{radar_model.radar_id}.png", # type: ignore
                show=True
            )
    
    def _apply_new_cfar_detection(self, processed_data: Dict[str, Any],
                                radar_model: RadarModel,
                                config: SimulationConfig) -> Dict[str, Any]:
        """
        应用新重构的CFAR检测
        
        Args:
            processed_data: 处理后的数据
            radar_model: 雷达模型
            config: 仿真配置
            
        Returns:
            检测结果
        """
        cfar_config = config.cfar_config
        
        try:
            # 优先使用距离-多普勒图进行2D检测
            if processed_data['rd_map'] is not None and processed_data['rd_map'].ndim == 2:
                data = processed_data['rd_map']
                
                # 转换为线性功率
                if np.any(data < 0):  # dB单位
                    data_linear = 10 ** (data / 10)
                else:
                    data_linear = data
                
                # 使用新重构的CFAR检测
                detections, threshold, stats = self.cfar_processor.adaptive_cfar_detection( # type: ignore
                    data=data_linear,
                    guard=cfar_config['guard_cells'],
                    trailing=cfar_config['trailing_cells'],
                    pfa=cfar_config['pfa'],
                    min_snr=cfar_config['min_snr'],
                    target_type=cfar_config['target_type']
                )
                
                return {
                    'detection_map': detections,
                    'cfar_threshold': threshold,
                    'detection_stats': stats,
                    'data_type': 'range_doppler_2d'
                }
                
            # 使用1D剖面检测
            elif processed_data['range_profile'] is not None:
                data = processed_data['range_profile']
                
                if np.any(data < 0):  # dB单位
                    data_linear = 10 ** (data / 10)
                else:
                    data_linear = data
                
                # 1D CFAR检测
                cfar_threshold = self.cfar_processor.cfar_ca_1d( # type: ignore
                    data=data_linear,
                    guard=cfar_config['guard_cells'],
                    trailing=cfar_config['trailing_cells'],
                    pfa=cfar_config['pfa'],
                    axis=0
                )
                
                detections = data_linear > cfar_threshold
                
                return {
                    'detection_map': detections,
                    'cfar_threshold': cfar_threshold,
                    'data_type': 'range_1d'
                }
                
            else:
                return {
                    'detection_map': np.array([], dtype=bool),
                    'cfar_threshold': None,
                    'detection_stats': None,
                    'data_type': 'unknown'
                }
                
        except Exception as e:
            self.logger.error(f"新CFAR检测错误: {str(e)}")
            return {
                'detection_map': np.array([], dtype=bool),
                'cfar_threshold': None,
                'detection_stats': None,
                'data_type': 'error'
            }
    
    def _detect_and_match_targets(self, processed_data: Dict[str, Any],
                                radar_model: RadarModel,
                                targets: List[TargetParameters],
                                timestamp: float,
                                config: SimulationConfig) -> List[RadarDetection]:
        """
        使用新重构的目标匹配功能进行目标检测和匹配
        
        Args:
            processed_data: 处理后的数据
            radar_model: 雷达模型
            targets: 目标列表
            timestamp: 时间戳
            config: 仿真配置
            
        Returns:
            检测结果列表
        """
        if processed_data['detection_map'] is None or processed_data['detection_map'].size == 0:
            return []
        
        try:
            # 提取真实目标位置
            true_targets = self._extract_true_target_positions(targets, radar_model)
            
            # 提取检测目标位置
            detected_targets = self._extract_detected_positions(processed_data, radar_model)
            
            # 执行目标匹配
            match_results = self._perform_target_matching(
                true_targets, detected_targets, processed_data, config
            )
            
            # 创建检测对象
            detections = self._create_detections_from_match(
                match_results, processed_data, radar_model, targets, timestamp
            )
            
            return detections
            
        except Exception as e:
            exec_str = traceback.format_exc()
            self.logger.error(f"目标检测和匹配失败: {exec_str}")
            return []
    
    def _extract_true_target_positions(self, targets: List[TargetParameters], 
                                     radar_model: RadarModel) -> Dict[str, NDArray]:
        """提取真实目标位置"""
        true_ranges = []
        true_dopplers = []
        
        for target in targets:
            # 计算目标相对于雷达的距离和速度
            range_val = np.linalg.norm(target.position)
            
            # 简化速度计算（实际应根据雷达-目标几何关系）
            velocity_val = np.linalg.norm(target.velocity)
            
            # 转换为雷达坐标系中的单元索引
            range_bin = self._range_to_bin(range_val, radar_model) # type: ignore
            doppler_bin = self._velocity_to_doppler_bin(velocity_val, radar_model) # type: ignore
            
            true_ranges.append(range_bin)
            true_dopplers.append(doppler_bin)
        
        return {
            'range': np.array(true_ranges),
            'doppler': np.array(true_dopplers)
        }
    
    def _extract_detected_positions(self, processed_data: Dict[str, Any],
                                  radar_model: RadarModel) -> Dict[str, NDArray]:
        """提取检测到的目标位置"""
        detection_map = processed_data['detection_map']
        data_type = processed_data.get('data_type', 'unknown')
        
        if detection_map.size == 0 or not np.any(detection_map):
            return {'range': np.array([]), 'doppler': np.array([])}
        
        detection_indices = np.where(detection_map)
        
        if data_type == 'range_doppler_2d':
            # 2D检测：距离和多普勒索引
            doppler_indices, range_indices = detection_indices
            return {
                'range': range_indices,
                'doppler': doppler_indices
            }
        elif data_type == 'range_1d':
            # 1D距离检测
            range_indices = detection_indices[0]
            return {
                'range': range_indices,
                'doppler': np.zeros_like(range_indices)  # 多普勒未知
            }
        else:
            # 未知类型，返回空
            return {'range': np.array([]), 'doppler': np.array([])}
    
    def _perform_target_matching(self, true_targets: Dict[str, NDArray],
                              detected_targets: Dict[str, NDArray],
                              processed_data: Dict[str, Any],
                              config: SimulationConfig) -> Dict[str, Any]:
        """执行目标匹配"""
        matching_config = config.matching_config
        data_type = processed_data.get('data_type', 'unknown')
        
        if data_type == 'range_doppler_2d':
            # 2D目标匹配
            match_result = match_radar_detections(
                true_targets=true_targets,
                detected_targets=detected_targets,
                range_tolerance=matching_config['range_tolerance'],
                doppler_tolerance=matching_config['doppler_tolerance'],
                match_method=matching_config['match_method']
            )
        else:
            # 1D目标匹配
            if data_type == 'range_1d':
                true_positions = true_targets['range']
                detected_positions = detected_targets['range']
                tolerance = matching_config['range_tolerance']
            else:
                true_positions = true_targets['doppler']
                detected_positions = detected_targets['doppler']
                tolerance = matching_config['doppler_tolerance']
            
            match_result = _match_target_to_detection_1d(
                target_positions=true_positions,
                detection_positions=detected_positions,
                tolerance=tolerance,
                match_method=matching_config['match_method']
            )
        
        return {
            'match_result': match_result,
            'matched_targets': self._process_match_result(match_result, true_targets, detected_targets)
        }
    
    def _process_match_result(self, match_result: MatchResult,
                           true_targets: Dict[str, NDArray],
                           detected_targets: Dict[str, NDArray]) -> List[Dict[str, Any]]:
        """处理匹配结果"""
        matched_targets = []
        
        for target_idx, detection_idx in match_result.matched_pairs:
            matched_target = {
                'target_index': target_idx,
                'detection_index': detection_idx,
                'match_distance': match_result.match_distances[len(matched_targets)],
                'true_range': true_targets['range'][target_idx] if target_idx < len(true_targets['range']) else -1,
                'true_doppler': true_targets['doppler'][target_idx] if target_idx < len(true_targets['doppler']) else -1,
                'detected_range': detected_targets['range'][detection_idx] if detection_idx < len(detected_targets['range']) else -1,
                'detected_doppler': detected_targets['doppler'][detection_idx] if detection_idx < len(detected_targets['doppler']) else -1
            }
            matched_targets.append(matched_target)
        
        return matched_targets
    
    def _create_detections_from_match(self, match_results: Dict[str, Any],
                                   processed_data: Dict[str, Any],
                                   radar_model: RadarModel,
                                   targets: List[TargetParameters],
                                   timestamp: float) -> List[RadarDetection]:
        """从匹配结果创建检测对象"""
        detections = []
        matched_targets = match_results.get('matched_targets', [])
        match_result = match_results.get('match_result')
        
        for matched in matched_targets:
            target_idx = matched['target_index']
            detection_idx = matched['detection_index']
            
            # 获取目标信息
            target = targets[target_idx] if target_idx < len(targets) else None
            
            # 计算检测参数
            range_val, velocity_val = self._calculate_detection_parameters(
                detection_idx, processed_data, radar_model
            )
            
            # 计算信噪比和置信度
            snr_db, confidence = self._calculate_detection_quality(
                detection_idx, processed_data, match_result # type: ignore
            )
            
            # 估计角度
            azimuth, elevation = self._estimate_angles(
                detection_idx, processed_data, radar_model
            )
            
            # 创建检测对象
            detection = RadarDetection(
                timestamp=timestamp,
                radar_id=radar_model.radar_id,
                target_id=getattr(target, 'target_id', f'target_{target_idx}') if target else f'unknown_{detection_idx}',
                range=range_val,
                azimuth=azimuth,
                elevation=elevation,
                doppler=velocity_val * 2 / (3e8 / radar_model.transmitter.frequency_hz) if radar_model.transmitter else 0,
                snr=snr_db,
                detection_confidence=confidence
            )
            
            detections.append(detection)
        
        return detections
    
    def _calculate_detection_parameters(self, detection_idx: int,
                                        processed_data: Dict[str, Any],
                                        radar_model: RadarModel) -> Tuple[float, float]:
            """计算检测参数（距离和速度）"""
            data_type = processed_data.get('data_type', 'unknown')
            
            if data_type == 'range_doppler_2d':
                # 2D检测：从索引计算距离和速度
                detection_indices = np.where(processed_data['detection_map'])
                doppler_idx = detection_indices[0][detection_idx]
                range_idx = detection_indices[1][detection_idx]
                
                range_val = self._bin_to_range(range_idx, radar_model)
                velocity_val = self._doppler_bin_to_velocity(doppler_idx, radar_model)
                
            elif data_type == 'range_1d':
                # 1D距离检测
                range_idx = np.where(processed_data['detection_map'])[0][detection_idx]
                range_val = self._bin_to_range(range_idx, radar_model)
                velocity_val = 0.0  # 未知
                
            else:
                # 未知类型
                range_val = 0.0
                velocity_val = 0.0
            
            return range_val, velocity_val
        
    def _calculate_detection_quality(self, detection_idx: int,
                                processed_data: Dict[str, Any],
                                match_result: MatchResult) -> Tuple[float, float]:
        """计算检测质量（SNR和置信度）"""
        # 从检测统计中获取SNR信息
        detection_stats = processed_data.get('detection_stats', {})
        
        if detection_stats:
            snr_stats = detection_stats.get('snr_analysis', {})
            if snr_stats:
                snr_db = snr_stats.get('mean_snr', 10.0)
            else:
                # 回退到基于检测值的估计
                data_map = processed_data.get('detection_map')
                if data_map is not None and data_map.size > detection_idx:
                    detection_value = data_map.flat[detection_idx] if data_map.ndim > 1 else data_map[detection_idx]
                    snr_db = 10 * np.log10(detection_value) if detection_value > 0 else 0.0
                else:
                    snr_db = 10.0
        else:
            snr_db = 10.0
        
        # 基于SNR和匹配质量计算置信度
        if match_result and match_result.match_distances:
            # 如果有匹配距离信息，结合匹配质量
            avg_match_distance = np.mean(match_result.match_distances)
            match_quality = 1.0 / (1.0 + avg_match_distance)  # 距离越小质量越高
            confidence = min(1.0, (snr_db / 20.0) * 0.7 + match_quality * 0.3)
        else:
            # 仅基于SNR
            confidence = min(1.0, snr_db / 20.0)
        
        return snr_db, confidence # type: ignore
    
    def _estimate_angles(self, detection_idx: int,
                        processed_data: Dict[str, Any],
                        radar_model: RadarModel) -> Tuple[float, float]:
        """估计目标角度（简化实现）"""
        # 这里可以扩展为实际的DOA估计
        # 目前返回固定值
        return 0.0, 0.0
    
    def _range_to_bin(self, range_val: float, radar_model: RadarModel) -> int:
        """将距离值转换为距离单元索引"""
        # 简化实现：假设固定距离分辨率
        tx = radar_model.transmitter
        if not tx:
            return 0
        
        bandwidth = getattr(tx, 'bandwidth_hz', 1e6)
        range_res = 3e8 / (2 * bandwidth) if bandwidth > 0 else 150
        return int(range_val / range_res)
    
    def _bin_to_range(self, range_bin: int, radar_model: RadarModel) -> float:
        """将距离单元索引转换为距离值"""
        tx = radar_model.transmitter
        if not tx:
            return 0.0
        
        bandwidth = getattr(tx, 'bandwidth_hz', 1e6)
        range_res = 3e8 / (2 * bandwidth) if bandwidth > 0 else 150
        return range_bin * range_res
    
    def _velocity_to_doppler_bin(self, velocity: float, radar_model: RadarModel) -> int:
        """将速度值转换为多普勒单元索引"""
        tx = radar_model.transmitter
        if not tx:
            return 0
        
        wavelength = 3e8 / getattr(tx, 'frequency_hz', 1e9)
        prf = getattr(tx, 'prf_hz', 1000)
        
        # 计算多普勒频率
        doppler_freq = 2 * velocity / wavelength
        
        # 转换为索引（假设零频在中心）
        n_doppler_cells = getattr(radar_model.signal_processing, 'doppler_cells', 64)
        doppler_res = prf / n_doppler_cells if n_doppler_cells > 0 else prf
        
        return int(doppler_freq / doppler_res + n_doppler_cells / 2)
    
    def _doppler_bin_to_velocity(self, doppler_bin: int, radar_model: RadarModel) -> float:
        """将多普勒单元索引转换为速度值"""
        tx = radar_model.transmitter
        if not tx:
            return 0.0
        
        wavelength = 3e8 / getattr(tx, 'frequency_hz', 1e9)
        prf = getattr(tx, 'prf_hz', 1000)
        
        n_doppler_cells = getattr(radar_model.signal_processing, 'doppler_cells', 64)
        doppler_res = prf / n_doppler_cells if n_doppler_cells > 0 else prf
        
        # 计算多普勒频率（考虑零频在中心）
        doppler_freq = (doppler_bin - n_doppler_cells / 2) * doppler_res
        
        # 计算速度
        return doppler_freq * wavelength / 2
    
    # 保留原有的信号处理函数（但使用新重构的CFAR检测）
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
    
    def _range_processing(self, baseband_data: np.ndarray, 
                        radar_model: RadarModel) -> np.ndarray:
        """距离处理"""
        try:
            from radarsimpy.processing import range_fft
            
            # 使用radarsimpy的距离FFT
            range_win = self._get_window_array(WindowType.HANNING, baseband_data.shape[2])
            range_profile_3d = range_fft(baseband_data, rwin=range_win)
            
            # 取第一个通道和第一个脉冲的结果
            if range_profile_3d.ndim == 3:
                range_profile = np.abs(range_profile_3d[0, 0, :])  # [通道, 脉冲, 距离]
            else:
                range_profile = np.abs(range_profile_3d[0, :])  # [脉冲, 距离]
            
            # 转换为dB
            range_profile_db = 20 * np.log10(range_profile + 1e-12)
            
            return range_profile_db
            
        except Exception as e:
            self.logger.error(f"距离处理错误: {str(e)}")
            return np.zeros(baseband_data.shape[2])

    def _doppler_processing(self, baseband_data: np.ndarray, 
                        radar_model: RadarModel) -> np.ndarray:
        """多普勒处理"""
        try:
            from radarsimpy.processing import doppler_fft
            
            # 使用radarsimpy的多普勒FFT
            doppler_win = self._get_window_array(WindowType.HANNING, baseband_data.shape[1])
            doppler_profile_3d = doppler_fft(baseband_data, dwin=doppler_win)
            
            # 取第一个通道和第一个距离门的结果
            if doppler_profile_3d.ndim == 3:
                doppler_profile = np.abs(doppler_profile_3d[0, :, 0])  # [通道, 多普勒, 距离]
            else:
                doppler_profile = np.abs(doppler_profile_3d[:, 0])  # [多普勒, 距离]
            
            # 进行fftshift
            doppler_profile_shifted = fftshift(doppler_profile)
            
            # 转换为dB
            doppler_profile_db = 20 * np.log10(doppler_profile_shifted + 1e-12)
            
            return doppler_profile_db
            
        except Exception as e:
            self.logger.error(f"多普勒处理错误: {str(e)}")
            return np.zeros(baseband_data.shape[1])
    
    def _range_doppler_map(self, baseband_data: np.ndarray,
                        range_window: WindowType = WindowType.HANNING,
                        doppler_window: WindowType = WindowType.HANNING) -> np.ndarray:
        """
        计算距离-多普勒图
        """
        try:
            from radarsimpy.processing import range_doppler_fft
            
            # 确保数据形状正确 [通道数, 脉冲数, 采样点数]
            if baseband_data.ndim != 3:
                raise ValueError(f"基带数据维度错误: {baseband_data.shape}")        
            
            # 生成窗函数
            range_win = self._get_window_array(range_window, baseband_data.shape[2])
            doppler_win = self._get_window_array(doppler_window, baseband_data.shape[1])

            # 使用radarsimpy的距离-多普勒FFT
            rd_map = range_doppler_fft(baseband_data, rwin=range_win, dwin=doppler_win)
            
            # 取第一个通道的结果
            if rd_map.ndim == 3:
                rd_map = rd_map[0]  # 取第一个通道
            
            # 沿多普勒维进行fftshift
            rd_map_shifted = fftshift(rd_map, axes=0)
            
            # 转换为幅度（dB）
            rd_map_db = 20 * np.log10(np.abs(rd_map_shifted) + 1e-12)
            
            return rd_map_db   
            
        except Exception as e:
            self.logger.error(f"距离-多普勒图计算错误: {str(e)}")
            return np.zeros((baseband_data.shape[1], baseband_data.shape[2]))
    
    def analyze_performance(self, results: SimulationResults) -> Dict[str, Any]:
        """
        分析仿真性能 - 使用新重构的匹配结果
        
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
            
            # 计算匹配质量指标
            target_ids = [d.target_id for d in dets]
            known_targets = len([tid for tid in target_ids if not tid.startswith('unknown')])
            unknown_targets = len([tid for tid in target_ids if tid.startswith('unknown')])
            
            radar_performance[radar_id] = {
                'detection_count': len(dets),
                'known_targets': known_targets,
                'unknown_targets': unknown_targets,
                'target_recognition_rate': known_targets / len(dets) if dets else 0,
                'avg_snr_db': np.mean(snr_values) if snr_values else 0,
                'max_snr_db': max(snr_values) if snr_values else 0,
                'avg_confidence': np.mean(confidence_values) if confidence_values else 0,
                'detection_rate_hz': len(dets) / time_span if time_span > 0 else 0
            }
        
        # 计算系统级性能
        total_targets = len(set(d.target_id for d in results.detections if not d.target_id.startswith('unknown')))
        expected_targets = len(results.parameters.scenario.targets)
        detection_probability = total_targets / expected_targets if expected_targets > 0 else 0
        
        # 计算总体匹配质量
        all_snr = [d.snr for d in results.detections]
        all_confidence = [d.detection_confidence for d in results.detections]
        
        return {
            'simulation_duration_s': results.parameters.scenario.duration,
            'total_detections': len(results.detections),
            'unique_targets_detected': total_targets,
            'expected_targets': expected_targets,
            'detection_probability': detection_probability,
            'target_recognition_rate': total_targets / len(results.detections) if results.detections else 0,
            'time_span_s': time_span,
            'overall_snr_stats': {
                'mean': np.mean(all_snr) if all_snr else 0,
                'std': np.std(all_snr) if all_snr else 0,
                'max': max(all_snr) if all_snr else 0,
                'min': min(all_snr) if all_snr else 0
            },
            'overall_confidence_stats': {
                'mean': np.mean(all_confidence) if all_confidence else 0,
                'std': np.std(all_confidence) if all_confidence else 0
            },
            'radar_performance': radar_performance,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def export_simulation_data(self, results: SimulationResults, 
                            filename: str) -> bool:
        """
        导出仿真数据 - 包含新重构功能的统计信息
        
        Args:
            results: 仿真结果
            filename: 文件名
            
        Returns:
            成功标志
        """
        try:
            # 分析性能
            performance_analysis = self.analyze_performance(results)
            
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'simulation_id': results.parameters.simulation_id,
                    'scenario_name': results.parameters.scenario.name,
                    'simulator_version': '2.0',  # 标记为新版本
                    'features': ['new_cfar_processor', 'target_matching']
                },
                'parameters': self._serialize_parameters(results.parameters),
                'detections': [d.to_dict() for d in results.detections],
                'metrics': results.metrics,
                'performance_analysis': performance_analysis,
                'new_features_metrics': {
                    'cfar_performance': self._extract_cfar_metrics(results),
                    'matching_quality': self._extract_matching_metrics(results)
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"仿真数据已导出到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出失败: {str(e)}")
            return False
    
    def _extract_cfar_metrics(self, results: SimulationResults) -> Dict[str, Any]:
        """提取CFAR性能指标"""
        if not results.raw_data:
            return {}
        
        cfar_metrics = {}
        for radar_id, radar_data in results.raw_data.items():
            # 从原始数据中提取CFAR统计
            all_stats = []
            for timestamp, data in radar_data.items():
                if 'processed' in data and 'detection_stats' in data['processed']:
                    stats = data['processed']['detection_stats']
                    if stats:
                        all_stats.append(stats)
            
            if all_stats:
                # 计算平均统计
                avg_snr = np.mean([s.get('snr_analysis', {}).get('mean_snr', 0) for s in all_stats])
                avg_detections = np.mean([s.get('detection_statistics', {}).get('total_detections', 0) for s in all_stats])
                
                cfar_metrics[radar_id] = {
                    'average_snr_db': avg_snr,
                    'average_detections_per_frame': avg_detections,
                    'frames_analyzed': len(all_stats)
                }
        
        return cfar_metrics
    
    def _extract_matching_metrics(self, results: SimulationResults) -> Dict[str, Any]:
        """提取目标匹配质量指标"""
        if not results.detections:
            return {}
        
        # 分析目标识别率
        target_ids = [d.target_id for d in results.detections]
        known_targets = len([tid for tid in target_ids if not tid.startswith('unknown')])
        unknown_targets = len([tid for tid in target_ids if tid.startswith('unknown')])
        
        return {
            'total_detections': len(results.detections),
            'known_targets': known_targets,
            'unknown_targets': unknown_targets,
            'target_recognition_rate': known_targets / len(results.detections) if results.detections else 0,
            'matching_quality_score': self._calculate_overall_matching_quality(results)
        }
    
    def _calculate_overall_matching_quality(self, results: SimulationResults) -> float:
        """计算总体匹配质量分数"""
        if not results.detections:
            return 0.0
        
        # 基于SNR和置信度的简单质量评分
        snr_scores = [min(1.0, d.snr / 30.0) for d in results.detections]  # 30dB为满分
        confidence_scores = [d.detection_confidence for d in results.detections]
        
        # 目标识别加分
        recognition_bonus = [0.2 if not d.target_id.startswith('unknown') else 0.0 for d in results.detections]
        
        # 综合评分
        overall_scores = [
            0.4 * snr + 0.4 * conf + 0.2 * bonus 
            for snr, conf, bonus in zip(snr_scores, confidence_scores, recognition_bonus)
        ]
        
        return np.mean(overall_scores) if overall_scores else 0.0 # type: ignore
    
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
            'radar_ids': [r.radar_id for r in parameters.radars],
            'processing_features': ['new_cfar', 'target_matching']
        }
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """获取仿真状态"""
        if self.current_simulation is None:
            return {'status': 'idle', 'message': '没有运行中的仿真'}
        
        return {
            'status': 'completed',
            'simulation_id': self.current_simulation.parameters.simulation_id,
            'detection_count': len(self.current_simulation.detections),
            'completion_time': getattr(self.current_simulation, 'completion_time', '未知'),
            'processing_features': '新重构CFAR检测和目标匹配'
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
        
        # 创建仿真配置（使用新重构功能）
        config = SimulationConfig(
            cfar_config={
                'detector_type': 'squarelaw',
                'guard_cells': 2,
                'trailing_cells': 10,
                'pfa': 1e-6,
                'min_snr': 10.0,
                'target_type': 'Swerling 0'
            },
            matching_config={
                'match_method': MatchMethod.NEAREST_NEIGHBOR,
                'range_tolerance': 2.0,
                'doppler_tolerance': 2.0
            }
        )
        
        # 运行仿真
        try:
            print("开始雷达仿真测试（使用新重构功能）...")
            results = simulator.run_simulation(scenario, [radar], config)
            
            # 显示结果
            print(f"仿真完成，检测到 {len(results.detections)} 个目标")
            
            # 分析性能
            performance = simulator.analyze_performance(results)
            print(f"检测概率: {performance.get('detection_probability', 0):.2f}")
            print(f"目标识别率: {performance.get('target_recognition_rate', 0):.2f}")
            
            # 导出数据
            simulator.export_simulation_data(results, "test_simulation_v2.json")
            print("仿真数据已导出")
            
        except Exception as e:
            print(f"仿真测试失败: {str(e)}")