"""
简化的X波段雷达配置
可以直接在您的雷达仿真系统中使用
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SimpleXBandRadar:
    """简化的X波段雷达配置"""
    
    # 雷达基本信息
    radar_id: str = "XBand_Simple_001"
    name: str = "简化X波段雷达"
    band: str = "X"
    
    # 发射机参数
    frequency_hz: float = 9.4e9          # 10 GHz
    bandwidth_hz: float = 10e6          # 10 MHz
    power_w: float = 100e3              # 100 kW
    pulse_width_s: float = 10e-6        # 10 μs
    prf_hz: float = 10000                # 2 kHz
    pulses: int = 64                    # 64个脉冲
    
    # 接收机参数
    sampling_rate_hz: float = 20e6      # 20 MHz
    noise_figure_db: float = 3.0        # 3 dB
    rf_gain_dbi: float = 30.0           # 30 dB
    load_resistor: float = 50.0         # 50 欧姆
    
    # 天线参数
    antenna_gain_dbi: float = 35.0      # 35 dBi
    azimuth_beamwidth: float = 2.0     # 2°
    elevation_beamwidth: float = 5.0   # 5°
    
    # 信号处理参数
    range_cells: int = 512              # 512个距离单元
    doppler_cells: int = 64             # 64个多普勒单元
    
    def __post_init__(self):
        """初始化后计算性能指标"""
        self._calculate_performance()
    
    def _calculate_performance(self):
        """计算性能指标"""
        # 距离分辨率
        self.range_resolution = 3e8 / (2 * self.bandwidth_hz)
        
        # 最大不模糊距离
        self.max_unambiguous_range = 3e8 / (2 * self.prf_hz)
        
        # 波长
        self.wavelength = 3e8 / self.frequency_hz
        
        # 最大不模糊速度
        self.max_unambiguous_velocity = self.prf_hz * self.wavelength / 4
        
        # 速度分辨率
        doppler_resolution = self.prf_hz / self.doppler_cells
        self.velocity_resolution = doppler_resolution * self.wavelength / 2
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数字典"""
        return {
            'radar_id': self.radar_id,
            'name': self.name,
            'band': self.band,
            'transmitter': {
                'frequency_hz': self.frequency_hz,
                'bandwidth_hz': self.bandwidth_hz,
                'power_w': self.power_w,
                'pulse_width_s': self.pulse_width_s,
                'prf_hz': self.prf_hz,
                'pulses': self.pulses
            },
            'receiver': {
                'sampling_rate_hz': self.sampling_rate_hz,
                'noise_figure_db': self.noise_figure_db,
                'rf_gain_dbi': self.rf_gain_dbi,
                'load_resistor': self.load_resistor
            },
            'antenna': {
                'gain_dbi': self.antenna_gain_dbi,
                'azimuth_beamwidth': self.azimuth_beamwidth,
                'elevation_beamwidth': self.elevation_beamwidth
            },
            'signal_processing': {
                'range_cells': self.range_cells,
                'doppler_cells': self.doppler_cells
            },
            'performance': {
                'range_resolution': self.range_resolution,
                'max_unambiguous_range': self.max_unambiguous_range,
                'wavelength': self.wavelength,
                'max_unambiguous_velocity': self.max_unambiguous_velocity,
                'velocity_resolution': self.velocity_resolution
            }
        }
    
    def print_parameters(self):
        """打印参数"""
        params = self.get_parameters()
        
        print("简化X波段雷达参数:")
        print("=" * 50)
        
        for category, values in params.items():
            if category == 'performance':
                continue  # 后面单独处理
            
            print(f"\n{category.upper()}:")
            
            # 检查值的类型
            if isinstance(values, dict):
                for key, value in values.items():
                    if key.endswith('_hz'):
                        print(f"  {key}: {value/1e9:.2f} GHz" if value >= 1e9 else 
                              f"  {key}: {value/1e6:.1f} MHz" if value >= 1e6 else 
                              f"  {key}: {value/1e3:.0f} kHz" if value >= 1e3 else 
                              f"  {key}: {value:.0f} Hz")
                    elif key.endswith('_w'):
                        print(f"  {key}: {value/1e3:.1f} kW")
                    elif key.endswith('_s'):
                        print(f"  {key}: {value*1e6:.1f} μs")
                    else:
                        print(f"  {key}: {value}")
            else:
                # 如果不是字典，直接打印
                print(f"  {values}")
        
        print("\n性能指标:")
        perf = params['performance']
        if isinstance(perf, dict):
            print(f"  距离分辨率: {perf.get('range_resolution', 'N/A'):.1f} m")
            print(f"  最大不模糊距离: {perf.get('max_unambiguous_range', 'N/A'):.1f} m")
            print(f"  最大不模糊速度: {perf.get('max_unambiguous_velocity', 'N/A'):.1f} m/s")
            print(f"  速度分辨率: {perf.get('velocity_resolution', 'N/A'):.2f} m/s")
        else:
            print(f"  {perf}")


# 使用示例
if __name__ == "__main__":
    # 创建简化雷达
    radar = SimpleXBandRadar()
    radar.print_parameters()
    
    # 验证目标检测可行性
    target_range = 1000  # 1000米
    target_velocity = -50  # -50m/s
    
    print(f"\n目标检测验证:")
    print(f"  目标距离: {target_range} m")
    print(f"  目标速度: {target_velocity} m/s")
    
    if target_range <= radar.max_unambiguous_range:
        print("  ✓ 目标在最大不模糊距离内")
    else:
        print("  ✗ 目标超出最大不模糊距离")
    
    if abs(target_velocity) <= radar.max_unambiguous_velocity:
        print("  ✓ 目标在最大不模糊速度内")
    else:
        print("  ✗ 目标超出最大不模糊速度")