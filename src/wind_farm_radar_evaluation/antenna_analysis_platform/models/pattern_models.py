"""
方向图数据模型定义
存储和描述天线方向图的数学模型和分析结果
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np
from enum import Enum
import json
from datetime import datetime
from scipy import signal
import scipy.constants as const

class PatternCoordinateSystem(str, Enum):
    """方向图坐标系"""
    SPHERICAL = "spherical"  # 球坐标系 (theta, phi)
    CARTESIAN = "cartesian"  # 笛卡尔坐标系 (x, y, z)
    UV = "uv"  # UV坐标系
    ELEVATION_AZIMUTH = "elevation_azimuth"  # 俯仰方位坐标系

class PatternFormat(str, Enum):
    """方向图数据格式"""
    AMPLITUDE_PHASE = "amplitude_phase"  # 幅度和相位
    REAL_IMAGINARY = "real_imaginary"  # 实部和虚部
    POWER = "power"  # 功率
    GAIN = "gain"  # 增益
    DIRECTIVITY = "directivity"  # 方向性

class PatternComponent(str, Enum):
    """方向图分量"""
    TOTAL = "total"  # 总场
    THETA = "theta"  # Theta分量
    PHI = "phi"  # Phi分量
    CO_POLAR = "co_polar"  # 同极化
    CROSS_POLAR = "cross_polar"  # 交叉极化
    VERTICAL = "vertical"  # 垂直极化
    HORIZONTAL = "horizontal"  # 水平极化

@dataclass
class PatternPoint:
    """方向图数据点"""
    theta: float  # 俯仰角 (度)
    phi: float  # 方位角 (度)
    frequency: float  # 频率 (GHz)
    
    # 场值
    e_theta: complex = 0j  # E_theta场分量
    e_phi: complex = 0j  # E_phi场分量
    
    # 功率/增益
    power: float = 0.0  # 功率 (dB)
    gain: float = 0.0  # 增益 (dBi)
    directivity: float = 0.0  # 方向性系数 (dBi)
    
    # 相位
    phase_theta: float = 0.0  # E_theta相位 (度)
    phase_phi: float = 0.0  # E_phi相位 (度)
    phase_difference: float = 0.0  # 相位差 (度)
    
    # 极化参数
    axial_ratio: float = 0.0  # 轴比
    tilt_angle: float = 0.0  # 倾角 (度)
    polarization_ratio: float = 0.0  # 极化比
    
    # 波束参数
    beam_width_3db: Optional[float] = None  # 3dB波束宽度 (度)
    beam_width_10db: Optional[float] = None  # 10dB波束宽度 (度)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'theta': self.theta,
            'phi': self.phi,
            'frequency': self.frequency,
            'e_theta': {'real': float(self.e_theta.real), 'imag': float(self.e_theta.imag)},
            'e_phi': {'real': float(self.e_phi.real), 'imag': float(self.e_phi.imag)},
            'power': self.power,
            'gain': self.gain,
            'directivity': self.directivity,
            'phase_theta': self.phase_theta,
            'phase_phi': self.phase_phi,
            'phase_difference': self.phase_difference,
            'axial_ratio': self.axial_ratio,
            'tilt_angle': self.tilt_angle,
            'polarization_ratio': self.polarization_ratio,
            'beam_width_3db': self.beam_width_3db,
            'beam_width_10db': self.beam_width_10db
        }
    
    @classmethod
    def from_field_data(cls, 
                       theta: float, 
                       phi: float, 
                       frequency: float,
                       e_theta: complex,
                       e_phi: complex) -> 'PatternPoint':
        """从场数据创建点"""
        # 计算功率
        power_theta = 20 * np.log10(np.abs(e_theta) + 1e-10)
        power_phi = 20 * np.log10(np.abs(e_phi) + 1e-10)
        total_power = 10 * np.log10((np.abs(e_theta)**2 + np.abs(e_phi)**2) + 1e-20)
        
        # 计算相位
        phase_theta = np.angle(e_theta, deg=True)
        phase_phi = np.angle(e_phi, deg=True)
        phase_difference = phase_phi - phase_theta
        
        # 计算极化参数
        e_theta_abs = np.abs(e_theta)
        e_phi_abs = np.abs(e_phi)
        
        if e_theta_abs > 0 and e_phi_abs > 0:
            # 轴比
            axial_ratio = 20 * np.log10(max(e_theta_abs, e_phi_abs) / 
                                      min(e_theta_abs, e_phi_abs) + 1e-10)
            
            # 倾角
            tilt_angle = 0.5 * np.arctan2(2 * e_theta_abs * e_phi_abs * 
                                        np.cos(np.deg2rad(phase_difference)),
                                        e_theta_abs**2 - e_phi_abs**2)
            tilt_angle = np.rad2deg(tilt_angle)
            
            # 极化比
            polarization_ratio = e_phi_abs / (e_theta_abs + 1e-10)
        else:
            axial_ratio = 0.0
            tilt_angle = 0.0
            polarization_ratio = 0.0
        
        return cls(
            theta=theta,
            phi=phi,
            frequency=frequency,
            e_theta=e_theta,
            e_phi=e_phi,
            power=float(total_power),
            gain=float(total_power),  # 假设增益=功率，实际需校准
            directivity=float(total_power),  # 假设方向性=功率
            phase_theta=float(phase_theta),
            phase_phi=float(phase_phi),
            phase_difference=float(phase_difference),
            axial_ratio=float(axial_ratio),
            tilt_angle=float(tilt_angle),
            polarization_ratio=float(polarization_ratio)
        )

@dataclass
class PatternSlice:
    """方向图切面（固定phi或theta）"""
    angles: np.ndarray  # 角度数组 (度)
    values: np.ndarray  # 值数组
    component: PatternComponent
    frequency: float
    plane: str  # 'elevation' 或 'azimuth'
    fixed_angle: float  # 固定角度
    
    def find_peak(self, threshold: float = -3.0) -> Tuple[float, float]:
        """查找峰值点"""
        peak_idx = np.argmax(self.values)
        peak_angle = self.angles[peak_idx]
        peak_value = self.values[peak_idx]
        return float(peak_angle), float(peak_value)
    
    def find_beamwidth(self, level: float = -3.0) -> float:
        """计算波束宽度"""
        peak_angle, peak_value = self.find_peak()
        threshold_value = peak_value + level
        
        # 找到交叉点
        crossing_indices = np.where(np.diff(np.sign(self.values - threshold_value)))[0]
        
        if len(crossing_indices) >= 2:
            beamwidth = self.angles[crossing_indices[-1]] - self.angles[crossing_indices[0]]
            return float(beamwidth)
        return 0.0
    
    def find_sidelobe_level(self) -> float:
        """计算副瓣电平"""
        peak_angle, peak_value = self.find_peak()
        
        # 排除主瓣区域（±20度）
        mainlobe_mask = np.abs(self.angles - peak_angle) > 20.0
        if np.any(mainlobe_mask):
            sidelobe_value = np.max(self.values[mainlobe_mask])
            return float(sidelobe_value - peak_value)
        return -np.inf

@dataclass
class RadiationPattern:
    """辐射方向图主类"""
    # 基本信息
    name: str
    antenna_name: str
    pattern_type: PatternFormat
    coordinate_system: PatternCoordinateSystem
    
    # 数据网格
    theta_grid: np.ndarray  # 俯仰角网格 (度)
    phi_grid: np.ndarray  # 方位角网格 (度)
    frequency: float  # 频率 (GHz)
    
    # 场数据
    e_theta_data: np.ndarray  # E_theta场 (复数)
    e_phi_data: np.ndarray  # E_phi场 (复数)
    
    # 计算数据
    gain_data: Optional[np.ndarray] = None
    directivity_data: Optional[np.ndarray] = None
    axial_ratio_data: Optional[np.ndarray] = None
    
    # 元数据
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后计算派生数据"""
        self._calculate_derived_data()
    
    def _calculate_derived_data(self):
        """计算增益、方向性和轴比"""
        # 计算增益 (dBi)
        power = np.abs(self.e_theta_data)**2 + np.abs(self.e_phi_data)**2
        self.gain_data = 10 * np.log10(power + 1e-20)
        
        # 计算方向性
        total_power = np.sum(power * np.sin(np.deg2rad(self.theta_grid[:, np.newaxis])))
        if total_power > 0:
            self.directivity_data = 10 * np.log10(4 * np.pi * power / total_power)
        else:
            self.directivity_data = np.zeros_like(power)
        
        # 计算轴比
        e_theta_mag = np.abs(self.e_theta_data)
        e_phi_mag = np.abs(self.e_phi_data)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            self.axial_ratio_data = 20 * np.log10(
                np.maximum(e_theta_mag, e_phi_mag) / 
                np.maximum(np.minimum(e_theta_mag, e_phi_mag), 1e-10)
            )
            self.axial_ratio_data = np.nan_to_num(self.axial_ratio_data, nan=0.0, posinf=0.0, neginf=0.0)
    
    def get_slice(self, 
                  component: PatternComponent = PatternComponent.TOTAL,
                  fixed_phi: Optional[float] = None,
                  fixed_theta: Optional[float] = None) -> PatternSlice:
        """获取方向图切面"""
        if fixed_phi is not None:
            # 固定phi，得到theta切面
            phi_idx = np.argmin(np.abs(self.phi_grid - fixed_phi))
            
            if component == PatternComponent.TOTAL:
                values = self.gain_data[:, phi_idx]
            elif component == PatternComponent.THETA:
                values = 20 * np.log10(np.abs(self.e_theta_data[:, phi_idx]) + 1e-10)
            elif component == PatternComponent.PHI:
                values = 20 * np.log10(np.abs(self.e_phi_data[:, phi_idx]) + 1e-10)
            else:
                values = self.gain_data[:, phi_idx]
            
            return PatternSlice(
                angles=self.theta_grid,
                values=values,
                component=component,
                frequency=self.frequency,
                plane='elevation',
                fixed_angle=float(fixed_phi)
            )
        
        elif fixed_theta is not None:
            # 固定theta，得到phi切面
            theta_idx = np.argmin(np.abs(self.theta_grid - fixed_theta))
            
            if component == PatternComponent.TOTAL:
                values = self.gain_data[theta_idx, :]
            elif component == PatternComponent.THETA:
                values = 20 * np.log10(np.abs(self.e_theta_data[theta_idx, :]) + 1e-10)
            elif component == PatternComponent.PHI:
                values = 20 * np.log10(np.abs(self.e_phi_data[theta_idx, :]) + 1e-10)
            else:
                values = self.gain_data[theta_idx, :]
            
            return PatternSlice(
                angles=self.phi_grid,
                values=values,
                component=component,
                frequency=self.frequency,
                plane='azimuth',
                fixed_angle=float(fixed_theta)
            )
        
        else:
            raise ValueError("必须指定fixed_phi或fixed_theta")
    
    def get_max_gain(self) -> Tuple[float, float, float]:
        """获取最大增益及其位置"""
        max_idx = np.unravel_index(np.argmax(self.gain_data), self.gain_data.shape)
        max_gain = float(self.gain_data[max_idx])
        theta = float(self.theta_grid[max_idx[0]])
        phi = float(self.phi_grid[max_idx[1]])
        return max_gain, theta, phi
    
    def get_beamwidth(self, 
                     plane: str = 'elevation',
                     fixed_angle: float = 0.0,
                     level: float = -3.0) -> float:
        """计算波束宽度"""
        if plane == 'elevation':
            pattern_slice = self.get_slice(fixed_phi=fixed_angle)
        else:
            pattern_slice = self.get_slice(fixed_theta=fixed_angle)
        
        return pattern_slice.find_beamwidth(level)
    
    def get_sidelobe_level(self, 
                          plane: str = 'elevation',
                          fixed_angle: float = 0.0) -> float:
        """计算副瓣电平"""
        if plane == 'elevation':
            pattern_slice = self.get_slice(fixed_phi=fixed_angle)
        else:
            pattern_slice = self.get_slice(fixed_theta=fixed_angle)
        
        return pattern_slice.find_sidelobe_level()
    
    def normalize(self, target_max: float = 0.0) -> 'RadiationPattern':
        """归一化方向图"""
        max_gain = np.max(self.gain_data)
        gain_offset = target_max - max_gain
        
        normalized_gain = self.gain_data + gain_offset
        normalized_e_theta = self.e_theta_data * 10**(gain_offset / 20)
        normalized_e_phi = self.e_phi_data * 10**(gain_offset / 20)
        
        return RadiationPattern(
            name=f"{self.name}_normalized",
            antenna_name=self.antenna_name,
            pattern_type=self.pattern_type,
            coordinate_system=self.coordinate_system,
            theta_grid=self.theta_grid.copy(),
            phi_grid=self.phi_grid.copy(),
            frequency=self.frequency,
            e_theta_data=normalized_e_theta,
            e_phi_data=normalized_e_phi,
            description=f"Normalized pattern (max = {target_max} dB)"
        )
    
    def interpolate(self, 
                   theta_resolution: float = 1.0,
                   phi_resolution: float = 1.0) -> 'RadiationPattern':
        """插值到更高分辨率"""
        from scipy import interpolate
        
        # 创建插值函数
        interp_e_theta_real = interpolate.RegularGridInterpolator(
            (self.theta_grid, self.phi_grid),
            self.e_theta_data.real,
            method='cubic',
            bounds_error=False,
            fill_value=0.0
        )
        
        interp_e_theta_imag = interpolate.RegularGridInterpolator(
            (self.theta_grid, self.phi_grid),
            self.e_theta_data.imag,
            method='cubic',
            bounds_error=False,
            fill_value=0.0
        )
        
        interp_e_phi_real = interpolate.RegularGridInterpolator(
            (self.theta_grid, self.phi_grid),
            self.e_phi_data.real,
            method='cubic',
            bounds_error=False,
            fill_value=0.0
        )
        
        interp_e_phi_imag = interpolate.RegularGridInterpolator(
            (self.theta_grid, self.phi_grid),
            self.e_phi_data.imag,
            method='cubic',
            bounds_error=False,
            fill_value=0.0
        )
        
        # 创建新网格
        new_theta = np.arange(0, 181, theta_resolution)
        new_phi = np.arange(0, 361, phi_resolution)
        
        theta_mesh, phi_mesh = np.meshgrid(new_theta, new_phi, indexing='ij')
        points = np.column_stack([theta_mesh.ravel(), phi_mesh.ravel()])
        
        # 插值
        e_theta_real_interp = interp_e_theta_real(points).reshape(theta_mesh.shape)
        e_theta_imag_interp = interp_e_theta_imag(points).reshape(theta_mesh.shape)
        e_phi_real_interp = interp_e_phi_real(points).reshape(theta_mesh.shape)
        e_phi_imag_interp = interp_e_phi_imag(points).reshape(theta_mesh.shape)
        
        e_theta_interp = e_theta_real_interp + 1j * e_theta_imag_interp
        e_phi_interp = e_phi_real_interp + 1j * e_phi_imag_interp
        
        return RadiationPattern(
            name=f"{self.name}_interpolated",
            antenna_name=self.antenna_name,
            pattern_type=self.pattern_type,
            coordinate_system=self.coordinate_system,
            theta_grid=new_theta,
            phi_grid=new_phi,
            frequency=self.frequency,
            e_theta_data=e_theta_interp,
            e_phi_data=e_phi_interp,
            description=f"Interpolated pattern ({theta_resolution}°x{phi_resolution}°)"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（保存关键数据）"""
        return {
            'name': self.name,
            'antenna_name': self.antenna_name,
            'pattern_type': self.pattern_type.value,
            'coordinate_system': self.coordinate_system.value,
            'frequency': self.frequency,
            'theta_grid': self.theta_grid.tolist(),
            'phi_grid': self.phi_grid.tolist(),
            'e_theta_data': {
                'real': self.e_theta_data.real.tolist(),
                'imag': self.e_theta_data.imag.tolist()
            },
            'e_phi_data': {
                'real': self.e_phi_data.real.tolist(),
                'imag': self.e_phi_data.imag.tolist()
            },
            'description': self.description,
            'created_at': self.created_at,
            'parameters': self.parameters
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def save_to_file(self, filename: str):
        """保存到文件"""
        with open(filename, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RadiationPattern':
        """从字典创建"""
        e_theta_real = np.array(data['e_theta_data']['real'])
        e_theta_imag = np.array(data['e_theta_data']['imag'])
        e_phi_real = np.array(data['e_phi_data']['real'])
        e_phi_imag = np.array(data['e_phi_data']['imag'])
        
        pattern = cls(
            name=data['name'],
            antenna_name=data['antenna_name'],
            pattern_type=PatternFormat(data['pattern_type']),
            coordinate_system=PatternCoordinateSystem(data['coordinate_system']),
            theta_grid=np.array(data['theta_grid']),
            phi_grid=np.array(data['phi_grid']),
            frequency=data['frequency'],
            e_theta_data=e_theta_real + 1j * e_theta_imag,
            e_phi_data=e_phi_real + 1j * e_phi_imag,
            description=data.get('description', ''),
            parameters=data.get('parameters', {})
        )
        
        if 'created_at' in data:
            pattern.created_at = data['created_at']
        
        return pattern

@dataclass
class PatternStatistics:
    """方向图统计信息"""
    max_gain: float
    max_gain_theta: float
    max_gain_phi: float
    
    beamwidth_3db_e: float
    beamwidth_3db_h: float
    beamwidth_10db_e: float
    beamwidth_10db_h: float
    
    sidelobe_level_e: float
    sidelobe_level_h: float
    
    front_to_back_ratio: float
    front_to_side_ratio: float
    
    directivity: float
    efficiency: float
    axial_ratio_3db: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}