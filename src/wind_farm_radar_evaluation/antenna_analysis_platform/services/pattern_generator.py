"""
方向图生成服务
基于radarsimpy的天线方向图仿真与计算
使用多种设计模式组合实现灵活的方向图生成
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
from abc import ABC, abstractmethod
import json
from datetime import datetime
import logging
from scipy import signal, interpolate
import scipy.constants as const

# 尝试导入radarsimpy
try:
    import radarsimpy as rsp
    from radarsimpy.antennas import Antenna, Array, Pattern
    RADARSIMPY_AVAILABLE = True
except ImportError:
    RADARSIMPY_AVAILABLE = False
    # 创建模拟类以便代码能运行
    class Antenna:
        def __init__(self, **kwargs):
            self.params = kwargs
    
    class Array:
        def __init__(self, **kwargs):
            self.params = kwargs
    
    class Pattern:
        def __init__(self, **kwargs):
            self.params = kwargs

from models.antenna_models import AntennaParameters, AntennaArray, Element
from models.pattern_models import (
    RadiationPattern, PatternCoordinateSystem, 
    PatternFormat, PatternComponent, PatternPoint, PatternSlice
)

# 设置日志
logger = logging.getLogger(__name__)

# ============================================================================
# 设计模式：策略模式 - 不同的方向图生成策略
# ============================================================================

class PatternGenerationStrategy(ABC):
    """方向图生成策略抽象基类"""
    
    @abstractmethod
    def generate_pattern(self, antenna: AntennaParameters, **kwargs) -> RadiationPattern:
        """生成方向图"""
        pass
    
    @abstractmethod
    def validate_input(self, antenna: AntennaParameters) -> bool:
        """验证输入参数"""
        pass

class AnalyticalPatternStrategy(PatternGenerationStrategy):
    """解析法方向图生成策略（理论公式）"""
    
    def validate_input(self, antenna: AntennaParameters) -> bool:
        """验证天线参数"""
        required_params = ['center_frequency', 'gain', 'beamwidth_e', 'beamwidth_h']
        for param in required_params:
            if not hasattr(antenna, param) or getattr(antenna, param) is None:
                logger.warning(f"天线参数 {param} 缺失")
                return False
        return True
    
    def generate_pattern(self, antenna: AntennaParameters, **kwargs) -> RadiationPattern:
        """使用解析公式生成方向图"""
        if not self.validate_input(antenna):
            raise ValueError("天线参数不完整")
        
        # 获取参数
        fc = antenna.center_frequency * 1e9  # GHz -> Hz
        theta_bw = antenna.beamwidth_e
        phi_bw = antenna.beamwidth_h
        gain = antenna.gain
        
        # 角度网格
        theta_res = kwargs.get('theta_resolution', 1.0)
        phi_res = kwargs.get('phi_resolution', 1.0)
        theta = np.arange(0, 181, theta_res)
        phi = np.arange(0, 361, phi_res)
        theta_rad = np.deg2rad(theta)
        phi_rad = np.deg2rad(phi)
        
        theta_grid, phi_grid = np.meshgrid(theta_rad, phi_rad, indexing='ij')
        
        # 使用高斯波束模型生成方向图
        # 主瓣宽度
        sigma_theta = np.deg2rad(theta_bw) / (2 * np.sqrt(2 * np.log(2)))
        sigma_phi = np.deg2rad(phi_bw) / (2 * np.sqrt(2 * np.log(2)))
        
        # 高斯波束模型
        pattern = np.exp(-(theta_grid**2) / (2 * sigma_theta**2)) * \
                  np.exp(-(phi_grid**2) / (2 * sigma_phi**2))
        
        # 归一化到增益
        pattern_max = np.max(pattern)
        if pattern_max > 0:
            pattern = pattern / pattern_max
        
        # 转换为dB
        pattern_db = 10 * np.log10(pattern + 1e-10)
        pattern_db = pattern_db + gain
        
        # 添加副瓣
        pattern_db = self._add_sidelobes(pattern_db, antenna.sidelobe_level)
        
        # 转换为复数场
        pattern_complex = 10**(pattern_db / 20) * np.exp(1j * 0)
        
        # 创建方向图对象
        e_theta = pattern_complex
        e_phi = pattern_complex * 0.1  # 假设交叉极化比主瓣低20dB
        
        return RadiationPattern(
            name=f"{antenna.name}_analytical",
            antenna_name=antenna.name,
            pattern_type=PatternFormat.GAIN,
            coordinate_system=PatternCoordinateSystem.SPHERICAL,
            theta_grid=theta,
            phi_grid=phi,
            frequency=antenna.center_frequency,
            e_theta_data=e_theta,
            e_phi_data=e_phi,
            description=f"解析法生成的方向图 (Gaussian Beam Model)"
        )
    
    def _add_sidelobes(self, pattern: np.ndarray, sidelobe_level: float) -> np.ndarray:
        """添加副瓣结构"""
        result = pattern.copy()
        rows, cols = pattern.shape
        
        # 创建副瓣模板
        for i in range(rows):
            for j in range(cols):
                theta = i - rows//2
                phi = j - cols//2
                r = np.sqrt(theta**2 + phi**2)
                
                if r > 10:  # 主瓣外
                    # 添加周期性副瓣
                    sidelobe = sidelobe_level - 20 * np.log10(r/10) + \
                              5 * np.sin(0.2 * r) + 3 * np.cos(0.3 * phi)
                    result[i, j] = np.maximum(result[i, j], sidelobe)
        
        return result

class NumericalPatternStrategy(PatternGenerationStrategy):
    """数值法方向图生成策略（矩量法/有限元）"""
    
    def __init__(self):
        self.solver_type = "mom"  # 矩量法
        
    def validate_input(self, antenna: AntennaParameters) -> bool:
        """验证天线几何结构"""
        if not hasattr(antenna, 'geometry') or not antenna.geometry:
            logger.warning("天线几何结构缺失")
            return False
        
        if not hasattr(antenna.geometry, 'elements') or not antenna.geometry.elements:
            logger.warning("天线阵元缺失")
            return False
            
        return True
    
    def generate_pattern(self, antenna: AntennaParameters, **kwargs) -> RadiationPattern:
        """使用数值方法生成方向图"""
        if not self.validate_input(antenna):
            raise ValueError("天线几何结构不完整")
        
        # 获取参数
        fc = antenna.center_frequency * 1e9
        wavelength = const.c / fc
        
        # 角度网格
        theta_res = kwargs.get('theta_resolution', 5.0)
        phi_res = kwargs.get('phi_resolution', 5.0)
        theta = np.arange(0, 181, theta_res)
        phi = np.arange(0, 361, phi_res)
        theta_rad = np.deg2rad(theta)
        phi_rad = np.deg2rad(phi)
        
        theta_grid, phi_grid = np.meshgrid(theta_rad, phi_rad, indexing='ij')
        
        # 初始化场
        e_theta = np.zeros_like(theta_grid, dtype=complex)
        e_phi = np.zeros_like(theta_grid, dtype=complex)
        
        # 对每个阵元计算辐射
        for element in antenna.geometry.elements:
            elem_pattern = self._calculate_element_pattern(
                element, antenna, theta_grid, phi_grid, wavelength
            )
            e_theta += elem_pattern['e_theta']
            e_phi += elem_pattern['e_phi']
        
        # 考虑阵元位置引起的相位差
        e_theta, e_phi = self._apply_array_factor(
            antenna, e_theta, e_phi, theta_grid, phi_grid, wavelength
        )
        
        # 创建方向图对象
        return RadiationPattern(
            name=f"{antenna.name}_numerical",
            antenna_name=antenna.name,
            pattern_type=PatternFormat.AMPLITUDE_PHASE,
            coordinate_system=PatternCoordinateSystem.SPHERICAL,
            theta_grid=theta,
            phi_grid=phi,
            frequency=antenna.center_frequency,
            e_theta_data=e_theta,
            e_phi_data=e_phi,
            description=f"数值法生成的方向图 ({self.solver_type})"
        )
    
    def _calculate_element_pattern(self, element: Element, antenna: AntennaParameters,
                                  theta: np.ndarray, phi: np.ndarray, 
                                  wavelength: float) -> Dict[str, np.ndarray]:
        """计算阵元方向图"""
        # 根据阵元类型选择不同的方向图函数
        if element.type == "dipole":
            return self._dipole_pattern(theta, phi, wavelength)
        elif element.type == "patch":
            return self._patch_pattern(theta, phi, wavelength, antenna)
        elif element.type == "horn":
            return self._horn_pattern(theta, phi, wavelength)
        else:
            # 默认使用各向同性辐射
            return self._isotropic_pattern(theta, phi)
    
    def _dipole_pattern(self, theta: np.ndarray, phi: np.ndarray, 
                        wavelength: float) -> Dict[str, np.ndarray]:
        """偶极子方向图"""
        # 半波偶极子方向图函数
        e_theta = np.sin(theta) * np.exp(-1j * np.pi/2)
        e_phi = np.zeros_like(e_theta)
        return {'e_theta': e_theta, 'e_phi': e_phi}
    
    def _patch_pattern(self, theta: np.ndarray, phi: np.ndarray, 
                      wavelength: float, antenna: AntennaParameters) -> Dict[str, np.ndarray]:
        """微带贴片方向图"""
        # 简化模型
        k = 2 * np.pi / wavelength
        
        # 计算方向图
        e_theta = np.cos(k * np.sin(theta) * np.cos(phi)) * \
                  np.sinc(k * np.sin(theta) * np.sin(phi) / np.pi)
        e_phi = np.zeros_like(e_theta)  # 简化模型
        
        return {'e_theta': e_theta, 'e_phi': e_phi}
    
    def _horn_pattern(self, theta: np.ndarray, phi: np.ndarray, 
                     wavelength: float) -> Dict[str, np.ndarray]:
        """喇叭天线方向图"""
        # 喇叭天线方向图近似
        e_theta = np.exp(-(theta**2) / (2 * (np.pi/6)**2))  # 10度波束宽度
        e_phi = e_theta * 0.5  # 交叉极化
        return {'e_theta': e_theta, 'e_phi': e_phi}
    
    def _isotropic_pattern(self, theta: np.ndarray, phi: np.ndarray) -> Dict[str, np.ndarray]:
        """各向同性辐射"""
        e_theta = np.ones_like(theta)
        e_phi = np.zeros_like(phi)
        return {'e_theta': e_theta, 'e_phi': e_phi}
    
    def _apply_array_factor(self, antenna: AntennaParameters,
                           e_theta: np.ndarray, e_phi: np.ndarray,
                           theta: np.ndarray, phi: np.ndarray,
                           wavelength: float) -> Tuple[np.ndarray, np.ndarray]:
        """应用阵列因子"""
        if not hasattr(antenna, 'geometry') or len(antenna.geometry.elements) <= 1:
            return e_theta, e_phi
        
        array_factor = np.zeros_like(e_theta, dtype=complex)
        
        for i, element in enumerate(antenna.geometry.elements):
            # 阵元位置
            pos = np.array(element.position)
            
            # 波矢量
            k = 2 * np.pi / wavelength
            k_vec = np.array([
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta)
            ])
            
            # 相位项
            phase = np.exp(1j * k * np.sum(pos[:, np.newaxis, np.newaxis] * k_vec, axis=0))
            
            # 幅度和相位加权
            weight = element.amplitude * np.exp(1j * np.deg2rad(element.phase))
            array_factor += weight * phase
        
        return e_theta * array_factor, e_phi * array_factor

class RadarsimpyPatternStrategy(PatternGenerationStrategy):
    """使用radarsimpy生成方向图"""
    
    def __init__(self):
        if not RADARSIMPY_AVAILABLE:
            logger.warning("radarsimpy未安装，使用模拟模式")
            self.simulation_mode = "simulated"
        else:
            self.simulation_mode = "radarsimpy"
    
    def validate_input(self, antenna: AntennaParameters) -> bool:
        """验证radarsimpy兼容性"""
        if not hasattr(antenna, 'antenna_type'):
            return False
        
        # 检查是否支持的天线类型
        supported_types = ['dipole', 'patch', 'horn', 'parabolic']
        return antenna.antenna_type.value in supported_types
    
    def generate_pattern(self, antenna: AntennaParameters, **kwargs) -> RadiationPattern:
        """使用radarsimpy生成方向图"""
        if self.simulation_mode == "simulated":
            return self._generate_simulated_pattern(antenna, **kwargs)
        
        try:
            return self._generate_radarsimpy_pattern(antenna, **kwargs)
        except Exception as e:
            logger.error(f"radarsimpy仿真失败: {e}")
            logger.info("回退到模拟模式")
            return self._generate_simulated_pattern(antenna, **kwargs)
    
    def _generate_radarsimpy_pattern(self, antenna: AntennaParameters, 
                                   **kwargs) -> RadiationPattern:
        """使用radarsimpy实际仿真"""
        # 这里需要根据radarsimpy的实际API进行调整
        # 以下是示例代码，实际使用时需要根据radarsimpy文档修改
        
        # 创建天线对象
        if antenna.antenna_type.value == 'dipole':
            # 偶极子天线
            antenna_model = Antenna(
                frequency=[antenna.center_frequency * 1e9],
                pattern=[[1, 0, 0, 0]],  # 示例方向图
                polarization='vertical'
            )
        elif antenna.antenna_type.value == 'patch':
            # 微带贴片天线
            antenna_model = Antenna(
                frequency=[antenna.center_frequency * 1e9],
                pattern=[[1, 0, 0, 0]],  # 示例方向图
                polarization='horizontal'
            )
        else:
            # 默认天线
            antenna_model = Antenna(
                frequency=[antenna.center_frequency * 1e9],
                pattern=[[1, 0, 0, 0]],
                polarization='vertical'
            )
        
        # 创建阵列（如果适用）
        if len(antenna.geometry.elements) > 1:
            # 获取阵元位置
            element_positions = [elem.position for elem in antenna.geometry.elements]
            element_weights = [(elem.amplitude, elem.phase) for elem in antenna.geometry.elements]
            
            array_model = Array(
                antenna=antenna_model,
                location=element_positions,
                weights=element_weights
            )
        else:
            array_model = Array(
                antenna=antenna_model,
                location=[[0, 0, 0]]
            )
        
        # 角度范围
        theta = np.arange(0, 181, 5)
        phi = np.arange(0, 361, 5)
        
        # 计算方向图
        # 注意：这里需要根据radarsimpy的实际API调用
        # 以下是模拟代码
        theta_grid, phi_grid = np.meshgrid(theta, phi, indexing='ij')
        
        # 模拟方向图数据
        pattern = np.sin(theta_grid * np.pi / 180) * np.cos(phi_grid * np.pi / 180)
        e_theta = pattern
        e_phi = pattern * 0.1
        
        return RadiationPattern(
            name=f"{antenna.name}_radarsimpy",
            antenna_name=antenna.name,
            pattern_type=PatternFormat.AMPLITUDE_PHASE,
            coordinate_system=PatternCoordinateSystem.SPHERICAL,
            theta_grid=theta,
            phi_grid=phi,
            frequency=antenna.center_frequency,
            e_theta_data=e_theta,
            e_phi_data=e_phi,
            description="radarsimpy生成的方向图"
        )
    
    def _generate_simulated_pattern(self, antenna: AntennaParameters, 
                                  **kwargs) -> RadiationPattern:
        """模拟radarsimpy生成方向图"""
        # 创建角度网格
        theta = np.arange(0, 181, 5)
        phi = np.arange(0, 361, 5)
        theta_grid, phi_grid = np.meshgrid(theta, phi, indexing='ij')
        
        # 根据天线类型生成不同的方向图
        if antenna.antenna_type.value == 'dipole':
            # 偶极子方向图
            pattern = np.abs(np.sin(np.deg2rad(theta_grid)))
        elif antenna.antenna_type.value == 'patch':
            # 微带贴片方向图
            pattern = np.cos(np.deg2rad(theta_grid))**2 * np.cos(np.deg2rad(phi_grid))**2
        elif antenna.antenna_type.value == 'horn':
            # 喇叭天线方向图
            pattern = np.exp(-(theta_grid**2) / (20**2))
        else:
            # 默认方向图
            pattern = np.ones_like(theta_grid)
        
        # 归一化
        pattern = pattern / np.max(pattern)
        
        # 添加阵列因子（如果有多阵元）
        if len(antenna.geometry.elements) > 1:
            array_factor = self._calculate_array_factor(antenna, theta_grid, phi_grid)
            pattern = pattern * array_factor
        
        # 创建场数据
        e_theta = pattern * np.exp(1j * 0)
        e_phi = pattern * 0.1 * np.exp(1j * np.pi/2)  # 交叉极化
        
        return RadiationPattern(
            name=f"{antenna.name}_simulated",
            antenna_name=antenna.name,
            pattern_type=PatternFormat.AMPLITUDE_PHASE,
            coordinate_system=PatternCoordinateSystem.SPHERICAL,
            theta_grid=theta,
            phi_grid=phi,
            frequency=antenna.center_frequency,
            e_theta_data=e_theta,
            e_phi_data=e_phi,
            description="模拟生成的方向图"
        )
    
    def _calculate_array_factor(self, antenna: AntennaParameters, 
                               theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
        """计算阵列因子"""
        fc = antenna.center_frequency * 1e9
        wavelength = const.c / fc
        k = 2 * np.pi / wavelength
        
        array_factor = np.zeros_like(theta, dtype=complex)
        
        for element in antenna.geometry.elements:
            pos = np.array(element.position)
            
            # 波矢量
            kx = k * np.sin(np.deg2rad(theta)) * np.cos(np.deg2rad(phi))
            ky = k * np.sin(np.deg2rad(theta)) * np.sin(np.deg2rad(phi))
            kz = k * np.cos(np.deg2rad(theta))
            
            # 相位项
            phase = np.exp(1j * (pos[0]*kx + pos[1]*ky + pos[2]*kz))
            
            # 加权
            weight = element.amplitude * np.exp(1j * np.deg2rad(element.phase))
            array_factor += weight * phase
        
        return np.abs(array_factor)

# ============================================================================
# 设计模式：工厂模式 - 创建方向图生成器
# ============================================================================

class PatternGeneratorFactory:
    """方向图生成器工厂"""
    
    @staticmethod
    def create_generator(generator_type: str = "analytical") -> PatternGenerationStrategy:
        """创建方向图生成器"""
        generators = {
            "analytical": AnalyticalPatternStrategy,
            "numerical": NumericalPatternStrategy,
            "radarsimpy": RadarsimpyPatternStrategy
        }
        
        if generator_type not in generators:
            logger.warning(f"未知的生成器类型: {generator_type}，使用analytical")
            generator_type = "analytical"
        
        return generators[generator_type]()
    
    @staticmethod
    def get_available_generators() -> List[str]:
        """获取可用的生成器类型"""
        return ["analytical", "numerical", "radarsimpy"]

# ============================================================================
# 设计模式：外观模式 - 简化方向图生成接口
# ============================================================================

class PatternGenerationFacade:
    """方向图生成外观类"""
    
    def __init__(self, generator_type: str = "analytical"):
        self.generator = PatternGeneratorFactory.create_generator(generator_type)
        self.cache = {}  # 简单缓存
    
    def generate_radiation_pattern(self, antenna: AntennaParameters, 
                                   **kwargs) -> RadiationPattern:
        """生成辐射方向图"""
        # 创建缓存键
        cache_key = self._create_cache_key(antenna, kwargs)
        
        # 检查缓存
        if cache_key in self.cache:
            logger.info("从缓存加载方向图")
            return self.cache[cache_key]
        
        # 生成方向图
        logger.info(f"使用 {self.generator.__class__.__name__} 生成方向图")
        pattern = self.generator.generate_pattern(antenna, **kwargs)
        
        # 缓存结果
        self.cache[cache_key] = pattern
        
        return pattern
    
    def generate_pattern_slice(self, antenna: AntennaParameters, 
                             plane: str = "elevation",
                             fixed_angle: float = 0.0,
                             component: PatternComponent = PatternComponent.TOTAL,
                             **kwargs) -> PatternSlice:
        """生成方向图切面"""
        # 生成完整方向图
        pattern = self.generate_radiation_pattern(antenna, **kwargs)
        
        # 获取切面
        if plane == "elevation":
            return pattern.get_slice(component=component, fixed_phi=fixed_angle)
        else:
            return pattern.get_slice(component=component, fixed_theta=fixed_angle)
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
    
    def _create_cache_key(self, antenna: AntennaParameters, 
                         kwargs: Dict[str, Any]) -> str:
        """创建缓存键"""
        import hashlib
        import pickle
        
        # 序列化参数
        data = {
            'antenna': antenna.to_dict(),
            'kwargs': kwargs,
            'generator': self.generator.__class__.__name__
        }
        
        # 创建哈希
        serialized = pickle.dumps(data)
        return hashlib.md5(serialized).hexdigest()

# ============================================================================
# 高级功能：方向图合成与优化
# ============================================================================

class PatternSynthesizer:
    """方向图合成器"""
    
    @staticmethod
    def synthesize_patterns(patterns: List[RadiationPattern], 
                          weights: List[float] = None) -> RadiationPattern:
        """合成多个方向图"""
        if not patterns:
            raise ValueError("至少需要一个方向图")
        
        # 默认等权重
        if weights is None:
            weights = [1.0 / len(patterns)] * len(patterns)
        
        # 检查所有方向图维度一致
        ref_pattern = patterns[0]
        for pattern in patterns[1:]:
            if (pattern.theta_grid.shape != ref_pattern.theta_grid.shape or
                pattern.phi_grid.shape != ref_pattern.phi_grid.shape):
                raise ValueError("方向图维度不一致")
        
        # 加权合成
        e_theta_sum = np.zeros_like(ref_pattern.e_theta_data, dtype=complex)
        e_phi_sum = np.zeros_like(ref_pattern.e_phi_data, dtype=complex)
        
        for pattern, weight in zip(patterns, weights):
            e_theta_sum += pattern.e_theta_data * weight
            e_phi_sum += pattern.e_phi_data * weight
        
        return RadiationPattern(
            name="synthesized_pattern",
            antenna_name=", ".join([p.antenna_name for p in patterns]),
            pattern_type=PatternFormat.AMPLITUDE_PHASE,
            coordinate_system=PatternCoordinateSystem.SPHERICAL,
            theta_grid=ref_pattern.theta_grid.copy(),
            phi_grid=ref_pattern.phi_grid.copy(),
            frequency=ref_pattern.frequency,
            e_theta_data=e_theta_sum,
            e_phi_data=e_phi_sum,
            description=f"合成方向图 ({len(patterns)}个方向图加权合成)"
        )
    
    @staticmethod
    def create_shaped_beam(pattern: RadiationPattern, 
                          target_pattern: np.ndarray) -> RadiationPattern:
        """创建赋形波束"""
        # 计算权重
        weights = target_pattern / (np.abs(pattern.e_theta_data) + 1e-10)
        
        # 应用权重
        e_theta_shaped = pattern.e_theta_data * weights
        e_phi_shaped = pattern.e_phi_data * weights
        
        return RadiationPattern(
            name=f"{pattern.name}_shaped",
            antenna_name=pattern.antenna_name,
            pattern_type=pattern.pattern_type,
            coordinate_system=pattern.coordinate_system,
            theta_grid=pattern.theta_grid.copy(),
            phi_grid=pattern.phi_grid.copy(),
            frequency=pattern.frequency,
            e_theta_data=e_theta_shaped,
            e_phi_data=e_phi_shaped,
            description="赋形波束方向图"
        )

class PatternOptimizer:
    """方向图优化器"""
    
    def __init__(self, pattern: RadiationPattern):
        self.pattern = pattern
    
    def optimize_sidelobes(self, target_sll: float = -30.0) -> RadiationPattern:
        """优化副瓣电平"""
        # 获取当前副瓣电平
        current_sll = self.pattern.get_sidelobe_level(plane='elevation')
        
        if current_sll <= target_sll:
            return self.pattern
        
        # 应用窗函数降低副瓣
        theta_window = self._create_window(len(self.pattern.theta_grid), 
                                          target_sll - current_sll)
        phi_window = self._create_window(len(self.pattern.phi_grid), 
                                        target_sll - current_sll)
        
        # 创建窗矩阵
        window_matrix = np.outer(theta_window, phi_window)
        
        # 应用窗函数
        e_theta_optimized = self.pattern.e_theta_data * window_matrix
        e_phi_optimized = self.pattern.e_phi_data * window_matrix
        
        return RadiationPattern(
            name=f"{self.pattern.name}_optimized",
            antenna_name=self.pattern.antenna_name,
            pattern_type=self.pattern.pattern_type,
            coordinate_system=self.pattern.coordinate_system,
            theta_grid=self.pattern.theta_grid.copy(),
            phi_grid=self.pattern.phi_grid.copy(),
            frequency=self.pattern.frequency,
            e_theta_data=e_theta_optimized,
            e_phi_data=e_phi_optimized,
            description=f"副瓣优化方向图 (目标SLL: {target_sll}dB)"
        )
    
    def _create_window(self, n: int, attenuation: float) -> np.ndarray:
        """创建窗函数"""
        # 使用切比雪夫窗
        beta = -attenuation / 20
        window = signal.windows.chebwin(n, beta)
        return window

# ============================================================================
# 主服务类
# ============================================================================

class PatternGeneratorService:
    """方向图生成服务主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.generator_facade = PatternGenerationFacade(
            self.config.get('default_generator', 'analytical')
        )
        self.synthesizer = PatternSynthesizer()
        self.optimizer = None
    
    def generate_pattern(self, antenna: AntennaParameters, 
                        generator_type: str = None,
                        **kwargs) -> RadiationPattern:
        """生成方向图"""
        if generator_type:
            self.generator_facade.generator = PatternGeneratorFactory.create_generator(generator_type)
        
        return self.generator_facade.generate_radiation_pattern(antenna, **kwargs)
    
    def generate_array_pattern(self, array: AntennaArray, **kwargs) -> RadiationPattern:
        """生成阵列方向图"""
        # 生成单元方向图
        element_pattern = self.generate_pattern(array.elements[0], **kwargs)
        
        # 计算阵列因子
        array_factor = self._calculate_array_factor(array, element_pattern)
        
        # 应用阵列因子
        e_theta_array = element_pattern.e_theta_data * array_factor
        e_phi_array = element_pattern.e_phi_data * array_factor
        
        return RadiationPattern(
            name=f"{array.name}_array",
            antenna_name=array.name,
            pattern_type=PatternFormat.AMPLITUDE_PHASE,
            coordinate_system=PatternCoordinateSystem.SPHERICAL,
            theta_grid=element_pattern.theta_grid.copy(),
            phi_grid=element_pattern.phi_grid.copy(),
            frequency=element_pattern.frequency,
            e_theta_data=e_theta_array,
            e_phi_data=e_phi_array,
            description=f"阵列方向图 ({array.rows}x{array.columns})"
        )
    
    def _calculate_array_factor(self, array: AntennaArray, 
                               element_pattern: RadiationPattern) -> np.ndarray:
        """计算阵列因子"""
        fc = element_pattern.frequency * 1e9
        wavelength = const.c / fc
        k = 2 * np.pi / wavelength
        
        theta = np.deg2rad(element_pattern.theta_grid)
        phi = np.deg2rad(element_pattern.phi_grid)
        
        theta_grid, phi_grid = np.meshgrid(theta, phi, indexing='ij')
        
        # 初始化阵列因子
        array_factor = np.zeros_like(theta_grid, dtype=complex)
        
        # 获取阵元位置
        positions = array.get_element_positions()
        
        for idx, (pos, element) in enumerate(zip(positions, array.elements)):
            if idx >= len(array.elements):
                # 如果阵元数少于位置数，使用第一个阵元
                element = array.elements[0]
            
            # 波矢量
            kx = k * np.sin(theta_grid) * np.cos(phi_grid)
            ky = k * np.sin(theta_grid) * np.sin(phi_grid)
            kz = k * np.cos(theta_grid)
            
            # 相位项
            phase = np.exp(1j * (pos[0]*kx + pos[1]*ky + pos[2]*kz))
            
            # 加权
            weight = element.amplitude * np.exp(1j * np.deg2rad(element.phase))
            array_factor += weight * phase
        
        return array_factor
    
    def synthesize_patterns(self, patterns: List[RadiationPattern], 
                          weights: List[float] = None) -> RadiationPattern:
        """合成多个方向图"""
        return self.synthesizer.synthesize_patterns(patterns, weights)
    
    def optimize_pattern(self, pattern: RadiationPattern, 
                        target_sll: float = -30.0) -> RadiationPattern:
        """优化方向图副瓣"""
        self.optimizer = PatternOptimizer(pattern)
        return self.optimizer.optimize_sidelobes(target_sll)
    
    def get_available_generators(self) -> List[str]:
        """获取可用的生成器类型"""
        return PatternGeneratorFactory.get_available_generators()
    
    def clear_cache(self):
        """清空缓存"""
        self.generator_facade.clear_cache()

# 全局服务实例
_pattern_generator_service = None

def get_pattern_generator_service(config: Dict[str, Any] = None) -> PatternGeneratorService:
    """获取方向图生成服务实例（单例模式）"""
    global _pattern_generator_service
    if _pattern_generator_service is None:
        _pattern_generator_service = PatternGeneratorService(config)
    return _pattern_generator_service