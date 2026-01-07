"""
X波段测试雷达模型
专为调试和测试雷达仿真系统设计
确保能够检测到1000米处、-30m/s速度、RCS=5的目标
"""

import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class RadarBand(Enum):
    """雷达频段枚举"""
    HF = "HF"  # 高频
    VHF = "VHF"  # 甚高频
    UHF = "UHF"  # 特高频
    L = "L"  # L波段
    S = "S"  # S波段
    C = "C"  # C波段
    X = "X"  # X波段
    KU = "Ku"  # Ku波段
    K = "K"  # K波段
    KA = "Ka"  # Ka波段


@dataclass
class TransmitterParameters:
    """发射机参数"""
    frequency_hz: float = 10e9  # 10GHz (X波段)
    bandwidth_hz: float = 100e6  # 10MHz带宽
    power_w: float = 100e3  # 100kW峰值功率
    pulse_width_s: float = 10e-6  # 10μs脉冲宽度
    prf_hz: float = 5000  # 2kHz PRF
    pulses: int = 64  # 64个脉冲


@dataclass
class ReceiverParameters:
    """接收机参数"""
    sampling_rate_hz: float = 20e6  # 20MHz采样率
    noise_figure_db: float = 3.0  # 3dB噪声系数
    rf_gain_dbi: float = 30.0  # 30dB RF增益
    load_resistor: float = 50.0  # 50欧姆负载电阻
    baseband_gain_db: float = 20.0  # 20dB基带增益
    dynamic_range_db: float = 80.0  # 80dB动态范围


@dataclass
class AntennaParameters:
    """天线参数"""
    gain_dbi: float = 35.0  # 35dBi增益
    azimuth_beamwidth: float = 2.0  # 2°方位波束宽度
    elevation_beamwidth: float = 5.0  # 5°俯仰波束宽度
    polarization: str = "水平极化"  # 极化方式


@dataclass
class SignalProcessingParameters:
    """信号处理参数"""
    range_cells: int = 512  # 512个距离单元
    doppler_cells: int = 64  # 64个多普勒单元
    window_type: str = "汉宁窗"  # 窗函数类型
    cfar_method: str = "CA"  # CA-CFAR
    cfar_guard_cells: int = 2  # 2个保护单元
    cfar_training_cells: int = 10  # 10个参考单元
    cfar_pfa: float = 1e-6  # 10^-6虚警概率


class XBandTestRadar:
    """
    X波段测试雷达模型
    专为检测1000米处、-50m/s速度、RCS=5的目标优化
    """
    
    def __init__(self, radar_id: str = "XBand_Test_Radar_001"):
        """
        初始化X波段测试雷达
        
        Args:
            radar_id: 雷达ID
        """
        self.radar_id = radar_id
        self.name = "X波段测试雷达"
        self.model = "XBand-Test-v1.0"
        self.band = RadarBand.X
        
        # 设置雷达参数
        self._setup_parameters()
        
        # 验证参数合理性
        self._validate_parameters()
        
    def _setup_parameters(self):
        """设置雷达参数"""
        # 发射机参数
        self.transmitter = TransmitterParameters()
        
        # 接收机参数
        self.receiver = ReceiverParameters()
        
        # 天线参数
        self.antenna = AntennaParameters()
        
        # 信号处理参数
        self.signal_processing = SignalProcessingParameters()
        
        # 计算并设置性能指标
        self._calculate_performance_metrics()
    
    def _validate_parameters(self):
        """验证参数合理性"""
        # 检查距离模糊
        max_unambiguous_range = 3e8 / (2 * self.transmitter.prf_hz)
        target_range = 1000  # 目标距离1000米
        if target_range > max_unambiguous_range:
            raise ValueError(f"目标距离{target_range}m超过最大不模糊距离{max_unambiguous_range:.1f}m")
        
        # 检查速度模糊
        wavelength = 3e8 / self.transmitter.frequency_hz
        max_unambiguous_velocity = self.transmitter.prf_hz * wavelength / 4
        target_velocity = 30  # 目标速度30m/s
        if abs(target_velocity) > max_unambiguous_velocity:
            raise ValueError(f"目标速度{target_velocity}m/s超过最大不模糊速度{max_unambiguous_velocity:.1f}m/s")
        
        # 检查距离分辨率
        range_resolution = 3e8 / (2 * self.transmitter.bandwidth_hz)
        if range_resolution > 15:  # 要求距离分辨率优于15米
            raise ValueError(f"距离分辨率{range_resolution:.1f}m不满足检测要求")
        
        print("✓ 雷达参数验证通过")
        print(f"  - 最大不模糊距离: {max_unambiguous_range:.1f}m")
        print(f"  - 最大不模糊速度: {max_unambiguous_velocity:.1f}m/s")
        print(f"  - 距离分辨率: {range_resolution:.1f}m")
    
    def _calculate_performance_metrics(self):
        """计算性能指标"""
        # 距离分辨率
        self.range_resolution = 3e8 / (2 * self.transmitter.bandwidth_hz)
        
        # 最大不模糊距离
        self.max_unambiguous_range = 3e8 / (2 * self.transmitter.prf_hz)
        
        # 速度分辨率
        wavelength = 3e8 / self.transmitter.frequency_hz
        doppler_resolution = self.transmitter.prf_hz / self.signal_processing.doppler_cells
        self.velocity_resolution = doppler_resolution * wavelength / 2
        
        # 最大不模糊速度
        self.max_unambiguous_velocity = self.transmitter.prf_hz * wavelength / 4
        
        # 检测信噪比估计（简化模型）
        self.estimated_snr = self._estimate_detection_snr()
    
    def _estimate_detection_snr(self, target_range: float = 1000, 
                              target_rcs: float = 5) -> float:
        """
        估计检测信噪比（简化雷达方程）
        
        Args:
            target_range: 目标距离(m)
            target_rcs: 目标RCS(m²)
            
        Returns:
            估计的信噪比(dB)
        """
        # 雷达方程简化计算
        # SNR = (P_t * G^2 * λ^2 * σ) / ((4π)^3 * R^4 * k * T * B * F * L)
        
        # 雷达参数
        P_t = self.transmitter.power_w  # 发射功率(W)
        G = 10**(self.antenna.gain_dbi/10)  # 天线增益(线性)
        wavelength = 3e8 / self.transmitter.frequency_hz  # 波长(m)
        sigma = target_rcs  # 目标RCS(m²)
        R = target_range  # 距离(m)
        k = 1.38e-23  # 玻尔兹曼常数
        T = 290  # 噪声温度(K)
        B = self.transmitter.bandwidth_hz  # 带宽(Hz)
        F = 10**(self.receiver.noise_figure_db/10)  # 噪声系数(线性)
        L = 10**(2/10)  # 系统损耗(线性，假设2dB)
        
        # 雷达方程
        snr_linear = (P_t * G**2 * wavelength**2 * sigma) / \
                    ((4 * np.pi)**3 * R**4 * k * T * B * F * L)
        
        # 考虑相参积累增益
        n_pulses = self.transmitter.pulses
        snr_linear *= n_pulses
        
        # 转换为dB
        snr_db = 10 * np.log10(snr_linear)
        
        print(f"目标检测SNR估计:")
        print(f"  - 距离: {target_range}m")
        print(f"  - RCS: {target_rcs}m²")
        print(f"  - 估计SNR: {snr_db:.1f}dB")
        print(f"  - 脉冲积累数: {n_pulses}")
        
        return snr_db
    
    def get_radar_parameters(self) -> Dict[str, Any]:
        """获取雷达参数字典"""
        return {
            'radar_id': self.radar_id,
            'name': self.name,
            'model': self.model,
            'band': self.band.value,
            'transmitter': {
                'frequency_hz': self.transmitter.frequency_hz,
                'bandwidth_hz': self.transmitter.bandwidth_hz,
                'power_w': self.transmitter.power_w,
                'pulse_width_s': self.transmitter.pulse_width_s,
                'prf_hz': self.transmitter.prf_hz,
                'pulses': self.transmitter.pulses
            },
            'receiver': {
                'sampling_rate_hz': self.receiver.sampling_rate_hz,
                'noise_figure_db': self.receiver.noise_figure_db,
                'rf_gain_dbi': self.receiver.rf_gain_dbi,
                'load_resistor': self.receiver.load_resistor,
                'baseband_gain_db': self.receiver.baseband_gain_db,
                'dynamic_range_db': self.receiver.dynamic_range_db
            },
            'antenna': {
                'gain_dbi': self.antenna.gain_dbi,
                'azimuth_beamwidth': self.antenna.azimuth_beamwidth,
                'elevation_beamwidth': self.antenna.elevation_beamwidth,
                'polarization': self.antenna.polarization
            },
            'signal_processing': {
                'range_cells': self.signal_processing.range_cells,
                'doppler_cells': self.signal_processing.doppler_cells,
                'window_type': self.signal_processing.window_type,
                'cfar_method': self.signal_processing.cfar_method,
                'cfar_guard_cells': self.signal_processing.cfar_guard_cells,
                'cfar_training_cells': self.signal_processing.cfar_training_cells,
                'cfar_pfa': self.signal_processing.cfar_pfa
            },
            'performance_metrics': {
                'range_resolution_m': self.range_resolution,
                'max_unambiguous_range_m': self.max_unambiguous_range,
                'velocity_resolution_ms': self.velocity_resolution,
                'max_unambiguous_velocity_ms': self.max_unambiguous_velocity,
                'estimated_snr_db': self.estimated_snr
            }
        }
    
    def print_parameters(self):
        """打印雷达参数"""
        params = self.get_radar_parameters()
        
        print("=" * 60)
        print("X波段测试雷达参数")
        print("=" * 60)
        
        print(f"\n基本信息:")
        print(f"  雷达ID: {params['radar_id']}")
        print(f"  名称: {params['name']}")
        print(f"  型号: {params['model']}")
        print(f"  频段: {params['band']}")
        
        print(f"\n发射机参数:")
        tx = params['transmitter']
        print(f"  频率: {tx['frequency_hz']/1e9:.2f} GHz")
        print(f"  带宽: {tx['bandwidth_hz']/1e6:.1f} MHz")
        print(f"  峰值功率: {tx['power_w']/1e3:.1f} kW")
        print(f"  脉冲宽度: {tx['pulse_width_s']*1e6:.1f} μs")
        print(f"  PRF: {tx['prf_hz']/1e3:.1f} kHz")
        print(f"  脉冲数: {tx['pulses']}")
        
        print(f"\n接收机参数:")
        rx = params['receiver']
        print(f"  采样率: {rx['sampling_rate_hz']/1e6:.1f} MHz")
        print(f"  噪声系数: {rx['noise_figure_db']:.1f} dB")
        print(f"  RF增益: {rx['rf_gain_dbi']:.1f} dB")
        print(f"  动态范围: {rx['dynamic_range_db']:.1f} dB")
        
        print(f"\n天线参数:")
        ant = params['antenna']
        print(f"  增益: {ant['gain_dbi']:.1f} dBi")
        print(f"  方位波束宽度: {ant['azimuth_beamwidth']:.1f}°")
        print(f"  俯仰波束宽度: {ant['elevation_beamwidth']:.1f}°")
        print(f"  极化: {ant['polarization']}")
        
        print(f"\n信号处理参数:")
        sp = params['signal_processing']
        print(f"  距离单元数: {sp['range_cells']}")
        print(f"  多普勒单元数: {sp['doppler_cells']}")
        print(f"  CFAR方法: {sp['cfar_method']}")
        print(f"  CFAR虚警概率: {sp['cfar_pfa']:.1e}")
        
        print(f"\n性能指标:")
        pm = params['performance_metrics']
        print(f"  距离分辨率: {pm['range_resolution_m']:.1f} m")
        print(f"  最大不模糊距离: {pm['max_unambiguous_range_m']:.1f} m")
        print(f"  速度分辨率: {pm['velocity_resolution_ms']:.2f} m/s")
        print(f"  最大不模糊速度: {pm['max_unambiguous_velocity_ms']:.1f} m/s")
        print(f"  估计检测SNR: {pm['estimated_snr_db']:.1f} dB")
        
        print("=" * 60)


class TestTarget:
    """测试目标类"""
    
    def __init__(self, target_id: str = "test_target_001"):
        """
        初始化测试目标
        
        Args:
            target_id: 目标ID
        """
        self.target_id = target_id
        self.rcs_sqm = 5.0  # RCS 5m²
        self.position = np.array([1000.0, 0.0, 0.0])  # 1000米距离
        self.velocity = np.array([-30.0, 0.0, 0.0])  # -30m/s速度
        
    def get_target_parameters(self) -> Dict[str, Any]:
        """获取目标参数"""
        return {
            'target_id': self.target_id,
            'rcs_sqm': self.rcs_sqm,
            'position_m': self.position.tolist(),
            'velocity_ms': self.velocity.tolist(),
            'range_m': np.linalg.norm(self.position),
            'speed_ms': np.linalg.norm(self.velocity)
        }
    
    def print_parameters(self):
        """打印目标参数"""
        params = self.get_target_parameters()
        
        print("测试目标参数:")
        print(f"  目标ID: {params['target_id']}")
        print(f"  RCS: {params['rcs_sqm']} m²")
        print(f"  位置: [{params['position_m'][0]:.1f}, {params['position_m'][1]:.1f}, {params['position_m'][2]:.1f}] m")
        print(f"  速度: [{params['velocity_ms'][0]:.1f}, {params['velocity_ms'][1]:.1f}, {params['velocity_ms'][2]:.1f}] m/s")
        print(f"  距离: {params['range_m']:.1f} m")
        print(f"  速度大小: {params['speed_ms']:.1f} m/s")


class RadarSimulationTester:
    """
    雷达仿真测试器
    用于测试雷达仿真系统是否正常工作
    """
    
    def __init__(self):
        """初始化测试器"""
        self.radar = XBandTestRadar()
        self.target = TestTarget()
        
    def run_basic_test(self):
        """运行基本测试"""
        print("开始雷达仿真基本测试")
        print("=" * 60)
        
        # 显示雷达和目标参数
        self.radar.print_parameters()
        print()
        self.target.print_parameters()
        print()
        
        # 验证检测可行性
        self._validate_detection_feasibility()
        
        # 计算目标在雷达坐标系中的参数
        self._calculate_target_parameters()
        
        print("基本测试完成")
        print("=" * 60)
    
    def _validate_detection_feasibility(self):
        """验证检测可行性"""
        print("检测可行性验证:")
        
        # 检查距离是否在最大不模糊范围内
        target_range = self.target.get_target_parameters()['range_m']
        max_range = self.radar.max_unambiguous_range
        
        if target_range <= max_range:
            print(f"  ✓ 目标距离{target_range:.1f}m在最大不模糊距离{max_range:.1f}m内")
        else:
            print(f"  ✗ 目标距离{target_range:.1f}m超过最大不模糊距离{max_range:.1f}m")
            return False
        
        # 检查速度是否在最大不模糊速度内
        target_speed = self.target.get_target_parameters()['speed_ms']
        max_velocity = self.radar.max_unambiguous_velocity
        
        if abs(target_speed) <= max_velocity:
            print(f"  ✓ 目标速度{target_speed:.1f}m/s在最大不模糊速度{max_velocity:.1f}m/s内")
        else:
            print(f"  ✗ 目标速度{target_speed:.1f}m/s超过最大不模糊速度{max_velocity:.1f}m/s")
            return False
        
        # 检查SNR是否足够（假设检测需要至少10dB SNR）
        min_required_snr = 10.0
        estimated_snr = self.radar.estimated_snr
        
        if estimated_snr >= min_required_snr:
            print(f"  ✓ 估计SNR{estimated_snr:.1f}dB大于所需最小SNR{min_required_snr:.1f}dB")
        else:
            print(f"  ✗ 估计SNR{estimated_snr:.1f}dB小于所需最小SNR{min_required_snr:.1f}dB")
            return False
        
        print("  ✓ 所有检测条件满足，目标应该可以被检测到")
        return True
    
    def _calculate_target_parameters(self):
        """计算目标在雷达坐标系中的参数"""
        print("目标在雷达坐标系中的参数:")
        
        # 计算多普勒频率
        wavelength = 3e8 / self.radar.transmitter.frequency_hz
        doppler_frequency = 2 * self.target.velocity[0] / wavelength
        
        # 计算距离单元
        range_resolution = self.radar.range_resolution
        target_range = self.target.get_target_parameters()['range_m']
        range_bin = int(target_range / range_resolution)
        
        # 计算多普勒单元
        doppler_resolution = self.radar.transmitter.prf_hz / self.radar.signal_processing.doppler_cells
        doppler_bin = int(doppler_frequency / doppler_resolution) + self.radar.signal_processing.doppler_cells // 2
        
        print(f"  距离单元: {range_bin}")
        print(f"  多普勒频率: {doppler_frequency:.1f} Hz")
        print(f"  多普勒单元: {doppler_bin}")
        print(f"  预计在距离-多普勒图中的位置: [{doppler_bin}, {range_bin}]")
    
    def create_radarsimpy_compatible_radar(self):
        """
        创建与radarsimpy兼容的雷达配置
        
        Returns:
            radarsimpy兼容的雷达配置字典
        """
        # 发射机配置
        transmitter_config = {
            'f': [self.radar.transmitter.frequency_hz, 
                  self.radar.transmitter.frequency_hz + self.radar.transmitter.bandwidth_hz],
            't': [0, self.radar.transmitter.pulse_width_s],
            'tx_power': self.radar.transmitter.power_w,
            'prp': [1.0 / self.radar.transmitter.prf_hz] * self.radar.transmitter.pulses,
            'pulses': self.radar.transmitter.pulses
        }
        
        # 接收机配置
        receiver_config = {
            'fs': self.radar.receiver.sampling_rate_hz,
            'noise_figure': self.radar.receiver.noise_figure_db,
            'rf_gain': self.radar.receiver.rf_gain_dbi,
            'load_resistor': self.radar.receiver.load_resistor,
            'baseband_gain': self.radar.receiver.baseband_gain_db
        }
        
        # 通道配置
        channels = [{
            'location': [0, 0, 0],
            'polarization': [0, 0, 1]  # 垂直极化
        }]
        
        return {
            'transmitter': transmitter_config,
            'receiver': receiver_config,
            'channels': channels
        }
    
    def create_radarsimpy_compatible_target(self):
        """
        创建与radarsimpy兼容的目标配置
        
        Returns:
            radarsimpy兼容的目标配置字典
        """
        return {
            'model': 'point',
            'location': self.target.position,
            'speed': self.target.velocity,
            'rcs': self.target.rcs_sqm,
            'phase': 0
        }


# 使用示例
if __name__ == "__main__":
    # 创建测试器
    tester = RadarSimulationTester()
    
    # 运行基本测试
    tester.run_basic_test()
    
    # 获取radarsimpy兼容的配置
    radar_config = tester.create_radarsimpy_compatible_radar()
    target_config = tester.create_radarsimpy_compatible_target()
    
    print("\nradarsimpy兼容配置已生成")
    print("可用于您的雷达仿真系统进行测试")