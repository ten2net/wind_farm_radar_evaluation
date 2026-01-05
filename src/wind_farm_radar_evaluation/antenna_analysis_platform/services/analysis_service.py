"""
天线分析服务
对天线方向图进行深度分析和性能评估
使用多种设计模式实现灵活的分析框架
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass, field
from enum import Enum
from scipy import signal, interpolate, integrate, optimize
import scipy.constants as const
from scipy.signal import find_peaks
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

from models.antenna_models import AntennaParameters, AntennaArray
from models.pattern_models import (
    RadiationPattern, PatternSlice, PatternComponent, 
    PatternFormat, PatternStatistics
)

# 设置日志
logger = logging.getLogger(__name__)

# ============================================================================
# 设计模式：观察者模式 - 分析结果监听
# ============================================================================

class AnalysisObserver(ABC):
    """分析观察者抽象基类"""
    
    @abstractmethod
    def on_analysis_started(self, analysis_name: str, parameters: Dict[str, Any]):
        """分析开始回调"""
        pass
    
    @abstractmethod
    def on_analysis_progress(self, progress: float, message: str):
        """分析进度回调"""
        pass
    
    @abstractmethod
    def on_analysis_completed(self, results: Dict[str, Any], metadata: Dict[str, Any]):
        """分析完成回调"""
        pass
    
    @abstractmethod
    def on_analysis_error(self, error: Exception):
        """分析错误回调"""
        pass

class LoggingObserver(AnalysisObserver):
    """日志记录观察者"""
    
    def __init__(self, level: int = logging.INFO):
        self.level = level
    
    def on_analysis_started(self, analysis_name: str, parameters: Dict[str, Any]):
        logger.log(self.level, f"开始分析: {analysis_name}")
        logger.log(self.level, f"参数: {parameters}")
    
    def on_analysis_progress(self, progress: float, message: str):
        logger.log(self.level, f"进度: {progress:.1%} - {message}")
    
    def on_analysis_completed(self, results: Dict[str, Any], metadata: Dict[str, Any]):
        logger.log(self.level, f"分析完成: {metadata.get('analysis_name', '未知分析')}")
    
    def on_analysis_error(self, error: Exception):
        logger.error(f"分析错误: {error}", exc_info=True)

class ProgressObserver(AnalysisObserver):
    """进度显示观察者（用于UI）"""
    
    def __init__(self, progress_callback=None, message_callback=None):
        self.progress_callback = progress_callback
        self.message_callback = message_callback
    
    def on_analysis_started(self, analysis_name: str, parameters: Dict[str, Any]):
        if self.message_callback:
            self.message_callback(f"开始 {analysis_name}")
    
    def on_analysis_progress(self, progress: float, message: str):
        if self.progress_callback:
            self.progress_callback(progress)
        if self.message_callback:
            self.message_callback(message)
    
    def on_analysis_completed(self, results: Dict[str, Any], metadata: Dict[str, Any]):
        if self.progress_callback:
            self.progress_callback(1.0)
        if self.message_callback:
            self.message_callback("分析完成")
    
    def on_analysis_error(self, error: Exception):
        if self.message_callback:
            self.message_callback(f"错误: {str(error)}")

# ============================================================================
# 设计模式：策略模式 - 不同的分析方法
# ============================================================================

class AnalysisStrategy(ABC):
    """分析策略抽象基类"""
    
    def __init__(self, observers: List[AnalysisObserver] = None):
        self.observers = observers or []
        self.results = {}
        self.metadata = {}
    
    def add_observer(self, observer: AnalysisObserver):
        """添加观察者"""
        self.observers.append(observer)
    
    def notify_start(self, analysis_name: str, parameters: Dict[str, Any]):
        """通知分析开始"""
        self.metadata['analysis_name'] = analysis_name
        self.metadata['start_time'] = pd.Timestamp.now()
        
        for observer in self.observers:
            observer.on_analysis_started(analysis_name, parameters)
    
    def notify_progress(self, progress: float, message: str = ""):
        """通知分析进度"""
        for observer in self.observers:
            observer.on_analysis_progress(progress, message)
    
    def notify_complete(self):
        """通知分析完成"""
        self.metadata['end_time'] = pd.Timestamp.now()
        self.metadata['duration'] = (self.metadata['end_time'] - 
                                    self.metadata['start_time']).total_seconds()
        
        for observer in self.observers:
            observer.on_analysis_completed(self.results, self.metadata)
    
    def notify_error(self, error: Exception):
        """通知分析错误"""
        for observer in self.observers:
            observer.on_analysis_error(error)
    
    @abstractmethod
    def analyze(self, pattern: RadiationPattern, **kwargs) -> Dict[str, Any]:
        """执行分析"""
        pass

class BeamAnalysisStrategy(AnalysisStrategy):
    """波束特性分析策略"""
    
    def analyze(self, pattern: RadiationPattern, **kwargs) -> Dict[str, Any]:
        """分析波束特性"""
        try:
            self.notify_start("波束特性分析", kwargs)
            
            # 初始化结果
            self.results = {
                'beam_parameters': {},
                'beamwidths': {},
                'sidelobes': {},
                'nulls': {}
            }
            
            # 1. 分析主瓣特性
            self.notify_progress(0.2, "分析主瓣特性...")
            main_lobe_results = self._analyze_main_lobe(pattern)
            self.results['beam_parameters'].update(main_lobe_results)
            
            # 2. 分析波束宽度
            self.notify_progress(0.4, "分析波束宽度...")
            beamwidth_results = self._analyze_beamwidths(pattern)
            self.results['beamwidths'].update(beamwidth_results)
            
            # 3. 分析副瓣
            self.notify_progress(0.6, "分析副瓣特性...")
            sidelobe_results = self._analyze_sidelobes(pattern)
            self.results['sidelobes'].update(sidelobe_results)
            
            # 4. 分析零陷
            self.notify_progress(0.8, "分析零陷...")
            null_results = self._analyze_nulls(pattern)
            self.results['nulls'].update(null_results)
            
            # 5. 波束形状因子
            self.notify_progress(0.9, "计算波束形状因子...")
            shape_results = self._analyze_beam_shape(pattern)
            self.results['beam_parameters'].update(shape_results)
            
            self.notify_complete()
            return self.results
            
        except Exception as e:
            self.notify_error(e)
            raise
    
    def _analyze_main_lobe(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析主瓣特性"""
        # 找到最大增益点
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        
        # 获取主瓣切面
        elevation_slice = pattern.get_slice(fixed_phi=phi_max)
        azimuth_slice = pattern.get_slice(fixed_theta=theta_max)
        
        # 分析主瓣对称性
        symmetry_e = self._analyze_symmetry(elevation_slice)
        symmetry_h = self._analyze_symmetry(azimuth_slice)
        
        # 主瓣宽度
        main_lobe_width_e = elevation_slice.find_beamwidth(-3)
        main_lobe_width_h = azimuth_slice.find_beamwidth(-3)
        
        return {
            'peak_gain': float(max_gain),
            'peak_theta': float(theta_max),
            'peak_phi': float(phi_max),
            'main_lobe_width_3db_e': float(main_lobe_width_e),
            'main_lobe_width_3db_h': float(main_lobe_width_h),
            'symmetry_e': symmetry_e,
            'symmetry_h': symmetry_h,
            'beam_pointing_error': 0.0,  # 可扩展
            'beam_squint': 0.0  # 可扩展
        }
    
    def _analyze_beamwidths(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析波束宽度"""
        beamwidths = {}
        
        # 不同电平的波束宽度
        for level in [-3, -6, -10, -20]:
            beamwidth_e = pattern.get_beamwidth('elevation', 0, level)
            beamwidth_h = pattern.get_beamwidth('azimuth', 0, level)
            
            beamwidths[f'beamwidth_{abs(level)}db_e'] = float(beamwidth_e)
            beamwidths[f'beamwidth_{abs(level)}db_h'] = float(beamwidth_h)
        
        # 分析波束宽度变化（频率扫描时）
        beamwidths['beamwidth_variation_e'] = 0.0
        beamwidths['beamwidth_variation_h'] = 0.0
        
        return beamwidths
    
    def _analyze_sidelobes(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析副瓣特性"""
        # 获取切面
        elevation_slice = pattern.get_slice(fixed_phi=0)
        azimuth_slice = pattern.get_slice(fixed_theta=0)
        
        # 找到副瓣峰值
        sidelobes_e = self._find_sidelobes(elevation_slice)
        sidelobes_h = self._find_sidelobes(azimuth_slice)
        
        # 计算副瓣电平
        peak_e = elevation_slice.find_peak()[1]
        peak_h = azimuth_slice.find_peak()[1]
        
        max_sidelobe_level_e = sidelobes_e[0]['level'] - peak_e if sidelobes_e else -np.inf
        max_sidelobe_level_h = sidelobes_h[0]['level'] - peak_h if sidelobes_h else -np.inf
        
        # 计算副瓣平均电平
        avg_sidelobe_level_e = np.mean([sl['level'] - peak_e for sl in sidelobes_e]) if sidelobes_e else -np.inf
        avg_sidelobe_level_h = np.mean([sl['level'] - peak_h for sl in sidelobes_h]) if sidelobes_h else -np.inf
        
        return {
            'max_sidelobe_level_e': float(max_sidelobe_level_e),
            'max_sidelobe_level_h': float(max_sidelobe_level_h),
            'avg_sidelobe_level_e': float(avg_sidelobe_level_e),
            'avg_sidelobe_level_h': float(avg_sidelobe_level_h),
            'sidelobe_count_e': len(sidelobes_e),
            'sidelobe_count_h': len(sidelobes_h),
            'first_sidelobe_level_e': float(sidelobes_e[0]['level'] - peak_e) if sidelobes_e else -np.inf,
            'first_sidelobe_level_h': float(sidelobes_h[0]['level'] - peak_h) if sidelobes_h else -np.inf
        }
    
    def _analyze_nulls(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析零陷特性"""
        # 获取切面
        elevation_slice = pattern.get_slice(fixed_phi=0)
        azimuth_slice = pattern.get_slice(fixed_theta=0)
        
        # 找到零陷
        nulls_e = self._find_nulls(elevation_slice)
        nulls_h = self._find_nulls(azimuth_slice)
        
        # 分析零陷深度
        null_depths_e = [null['depth'] for null in nulls_e]
        null_depths_h = [null['depth'] for null in nulls_h]
        
        return {
            'null_count_e': len(nulls_e),
            'null_count_h': len(nulls_h),
            'max_null_depth_e': float(max(null_depths_e)) if nulls_e else 0.0,
            'max_null_depth_h': float(max(null_depths_h)) if nulls_h else 0.0,
            'avg_null_depth_e': float(np.mean(null_depths_e)) if nulls_e else 0.0,
            'avg_null_depth_h': float(np.mean(null_depths_h)) if nulls_h else 0.0
        }
    
    def _analyze_beam_shape(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析波束形状"""
        # 计算波束形状因子
        gain_data = pattern.gain_data
        
        # 1. 波束效率
        total_power = np.sum(10**(gain_data/10) * np.sin(np.deg2rad(pattern.theta_grid[:, np.newaxis])))
        main_lobe_power = self._calculate_mainlobe_power(pattern)
        
        if total_power > 0:
            beam_efficiency = main_lobe_power / total_power
        else:
            beam_efficiency = 0.0
        
        # 2. 波束圆度
        beam_circularity = self._calculate_beam_circularity(pattern)
        
        # 3. 波束偏心率
        beam_eccentricity = self._calculate_beam_eccentricity(pattern)
        
        return {
            'beam_efficiency': float(beam_efficiency),
            'beam_circularity': float(beam_circularity),
            'beam_eccentricity': float(beam_eccentricity),
            'shape_factor': 1.0  # 可扩展
        }
    
    def _analyze_symmetry(self, pattern_slice: PatternSlice) -> Dict[str, Any]:
        """分析波束对称性"""
        angles = pattern_slice.angles
        values = pattern_slice.values
        
        # 找到主瓣中心
        peak_idx = np.argmax(values)
        peak_angle = angles[peak_idx]
        
        # 对称性分析
        left_idx = np.where(angles < peak_angle)[0]
        right_idx = np.where(angles > peak_angle)[0]
        
        if len(left_idx) > 0 and len(right_idx) > 0:
            # 插值以匹配点数
            left_values = values[left_idx]
            right_values = values[right_idx[::-1]]  # 反转以匹配
            
            min_len = min(len(left_values), len(right_values))
            left_values = left_values[:min_len]
            right_values = right_values[:min_len]
            
            # 计算对称性误差
            symmetry_error = np.mean(np.abs(left_values - right_values))
            symmetry_correlation = np.corrcoef(left_values, right_values)[0, 1]
        else:
            symmetry_error = np.inf
            symmetry_correlation = 0.0
        
        return {
            'symmetry_error': float(symmetry_error),
            'symmetry_correlation': float(symmetry_correlation)
        }
    
    def _find_sidelobes(self, pattern_slice: PatternSlice, 
                        min_distance: float = 10.0) -> List[Dict[str, Any]]:
            """找到副瓣"""
            angles = pattern_slice.angles
            values = pattern_slice.values
            
            # 计算角度分辨率（假设角度是等间距的）
            if len(angles) > 1:
                angle_resolution = abs(angles[1] - angles[0])
            else:
                angle_resolution = 1.0  # 默认值
            
            # 将角度距离转换为索引距离
            index_distance = int(min_distance / angle_resolution) if angle_resolution > 0 else 1
            
            # 找到所有峰值
            try:
                from scipy.signal import find_peaks
                peaks, properties = find_peaks(values, distance=index_distance)
            except ImportError:
                # 如果scipy不可用，使用简单方法
                peaks = self._simple_peak_finding(values, min_distance=index_distance)
                properties = {'widths': [0.0] * len(peaks)}
            
            # 找到主瓣位置（假设主瓣是最大值）
            mainlobe_idx = np.argmax(values)
            
            # 按幅度排序
            sidelobes = []
            for peak_idx in peaks:
                # 排除主瓣
                if peak_idx == mainlobe_idx:
                    continue
                
                # 获取副瓣信息
                sidelobe_info = {
                    'angle': float(angles[peak_idx]),
                    'level': float(values[peak_idx]),
                    'width': 0.0
                }
                
                # 尝试获取宽度
                try:
                    if 'widths' in properties and len(properties['widths']) > 0:
                        # 找到当前峰值对应的宽度
                        peak_positions = list(peaks)
                        if peak_idx in peak_positions:
                            idx = peak_positions.index(peak_idx)
                            if idx < len(properties['widths']):
                                sidelobe_info['width'] = float(properties['widths'][idx] * angle_resolution)
                except Exception:
                    pass
                
                sidelobes.append(sidelobe_info)
            
            # 按电平降序排序
            sidelobes.sort(key=lambda x: x['level'], reverse=True)
            return sidelobes
    
    def _simple_peak_finding(self, values: np.ndarray, min_distance: int = 1) -> List[int]:
        """简单的峰值检测方法，用于没有scipy的情况"""
        peaks = []
        
        for i in range(1, len(values) - 1):
            # 检查是否是峰值
            if values[i] > values[i-1] and values[i] > values[i+1]:
                # 检查是否与已有峰值距离太近
                too_close = False
                for peak in peaks:
                    if abs(i - peak) < min_distance:
                        too_close = True
                        break
                
                if not too_close:
                    peaks.append(i)
        
        return np.array(peaks, dtype=int)     # type: ignore
    def _find_nulls(self, pattern_slice: PatternSlice, 
                   min_depth: float = 10.0) -> List[Dict[str, Any]]:
        """找到零陷"""
        angles = pattern_slice.angles
        values = pattern_slice.values
        
        # 找到所有谷值
        valleys, _ = find_peaks(-values)
        
        nulls = []
        for valley_idx in valleys:
            # 计算零陷深度（相对于最近峰值）
            left_idx = max(0, valley_idx - 5)
            right_idx = min(len(values) - 1, valley_idx + 5)
            local_peak = max(values[left_idx:right_idx])
            null_depth = local_peak - values[valley_idx]
            
            if null_depth >= min_depth:
                nulls.append({
                    'angle': float(angles[valley_idx]),
                    'depth': float(null_depth),
                    'level': float(values[valley_idx])
                })
        
        # 按深度降序排序
        nulls.sort(key=lambda x: x['depth'], reverse=True)
        return nulls
    
    def _calculate_mainlobe_power(self, pattern: RadiationPattern) -> float:
        """计算主瓣功率"""
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        
        # 主瓣区域（假设±波束宽度）
        beamwidth_e = pattern.get_beamwidth('elevation', phi_max, -3)
        beamwidth_h = pattern.get_beamwidth('azimuth', theta_max, -3)
        
        theta_range = (theta_max - beamwidth_e/2, theta_max + beamwidth_e/2)
        phi_range = (phi_max - beamwidth_h/2, phi_max + beamwidth_h/2)
        
        # 计算主瓣内功率
        theta_mask = (pattern.theta_grid >= theta_range[0]) & (pattern.theta_grid <= theta_range[1])
        phi_mask = (pattern.phi_grid >= phi_range[0]) & (pattern.phi_grid <= phi_range[1])
        
        theta_idx = np.where(theta_mask)[0]
        phi_idx = np.where(phi_mask)[0]
        
        if len(theta_idx) == 0 or len(phi_idx) == 0:
            return 0.0
        
        mainlobe_gain = pattern.gain_data[theta_idx[0]:theta_idx[-1]+1, phi_idx[0]:phi_idx[-1]+1]
        mainlobe_power = np.sum(10**(mainlobe_gain/10) * 
                               np.sin(np.deg2rad(pattern.theta_grid[theta_idx[0]:theta_idx[-1]+1, np.newaxis])))
        
        return float(mainlobe_power)
    
    def _calculate_beam_circularity(self, pattern: RadiationPattern) -> float:
        """计算波束圆度"""
        # 在固定增益电平上分析波束形状
        contour_level = -3  # 3dB轮廓
        
        # 找到3dB等高线
        contour_points = self._find_contour(pattern, contour_level)
        
        if len(contour_points) < 3:
            return 0.0
        
        # 计算圆度（1表示完美圆形）
        from scipy.spatial import ConvexHull
        
        points = np.array([[p['theta'], p['phi']] for p in contour_points])
        hull = ConvexHull(points)
        
        # 计算面积和周长
        hull_area = hull.volume
        hull_perimeter = hull.area
        
        # 计算等效圆面积
        equivalent_circle_radius = np.sqrt(hull_area / np.pi)
        equivalent_circle_perimeter = 2 * np.pi * equivalent_circle_radius
        
        # 圆度 = 等效圆周长 / 实际周长
        circularity = equivalent_circle_perimeter / hull_perimeter if hull_perimeter > 0 else 0.0
        
        return float(circularity)
    
    def _calculate_beam_eccentricity(self, pattern: RadiationPattern) -> float:
        """计算波束偏心率"""
        # 找到3dB等高线
        contour_points = self._find_contour(pattern, -3)
        
        if len(contour_points) < 3:
            return 0.0
        
        points = np.array([[p['theta'], p['phi']] for p in contour_points])
        
        # 计算主轴
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        pca.fit(points)
        
        # 偏心率 = sqrt(1 - (次要轴方差/主要轴方差)^2)
        variances = pca.explained_variance_
        if variances[0] > 0:
            eccentricity = np.sqrt(1 - (variances[1] / variances[0])**2)
        else:
            eccentricity = 0.0
        
        return float(eccentricity)
    
    def _find_contour(self, pattern: RadiationPattern, level: float) -> List[Dict[str, Any]]:
        """找到等高线点"""
        from skimage import measure
        
        # 找到等高线
        contours = measure.find_contours(pattern.gain_data, level)
        
        if len(contours) == 0:
            return []
        
        # 取最长的等高线
        main_contour = max(contours, key=len)
        
        # 转换为角度坐标
        contour_points = []
        for point in main_contour:
            theta_idx, phi_idx = point
            theta = pattern.theta_grid[int(theta_idx)]
            phi = pattern.phi_grid[int(phi_idx)]
            
            contour_points.append({
                'theta': float(theta),
                'phi': float(phi),
                'gain': float(pattern.gain_data[int(theta_idx), int(phi_idx)])
            })
        
        return contour_points

class PolarizationAnalysisStrategy(AnalysisStrategy):
    """极化特性分析策略"""
    
    def analyze(self, pattern: RadiationPattern, **kwargs) -> Dict[str, Any]:
        """分析极化特性"""
        try:
            self.notify_start("极化特性分析", kwargs)
            
            self.results = {
                'polarization_parameters': {},
                'axial_ratio': {},
                'polarization_purity': {},
                'polarization_ellipse': {}
            }
            
            # 1. 分析轴比
            self.notify_progress(0.25, "分析轴比...")
            axial_ratio_results = self._analyze_axial_ratio(pattern)
            self.results['axial_ratio'].update(axial_ratio_results)
            
            # 2. 分析极化纯度
            self.notify_progress(0.5, "分析极化纯度...")
            purity_results = self._analyze_polarization_purity(pattern)
            self.results['polarization_purity'].update(purity_results)
            
            # 3. 分析极化椭圆
            self.notify_progress(0.75, "分析极化椭圆...")
            ellipse_results = self._analyze_polarization_ellipse(pattern)
            self.results['polarization_ellipse'].update(ellipse_results)
            
            # 4. 交叉极化鉴别
            self.notify_progress(0.9, "计算交叉极化鉴别...")
            xpd_results = self._analyze_cross_polar_discrimination(pattern)
            self.results['polarization_parameters'].update(xpd_results)
            
            self.notify_complete()
            return self.results
            
        except Exception as e:
            self.notify_error(e)
            raise
    
    def _analyze_axial_ratio(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析轴比"""
        axial_ratio = pattern.axial_ratio_data
        
        # 主瓣区域轴比
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        main_lobe_mask = self._create_mainlobe_mask(pattern, theta_max, phi_max)
        
        main_lobe_ar = axial_ratio[main_lobe_mask]
        
        return {
            'axial_ratio_min': float(np.min(axial_ratio)),
            'axial_ratio_max': float(np.max(axial_ratio)),
            'axial_ratio_mean': float(np.mean(axial_ratio)),
            'axial_ratio_std': float(np.std(axial_ratio)),
            'mainlobe_axial_ratio_mean': float(np.mean(main_lobe_ar)) if len(main_lobe_ar) > 0 else 0.0,
            'mainlobe_axial_ratio_std': float(np.std(main_lobe_ar)) if len(main_lobe_ar) > 0 else 0.0,
            'axial_ratio_3db_beamwidth': self._calculate_ar_beamwidth(pattern, 3.0),
            'axial_ratio_6db_beamwidth': self._calculate_ar_beamwidth(pattern, 6.0)
        }
    
    def _analyze_polarization_purity(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析极化纯度"""
        e_theta = pattern.e_theta_data
        e_phi = pattern.e_phi_data
        
        # 计算极化比
        polarization_ratio = np.abs(e_phi) / (np.abs(e_theta) + 1e-10)
        
        # 计算极化纯度
        # 纯度 = 1 - 交叉极化功率 / 总功率
        co_pol_power = np.abs(e_theta)**2
        cross_pol_power = np.abs(e_phi)**2
        total_power = co_pol_power + cross_pol_power
        
        with np.errstate(divide='ignore', invalid='ignore'):
            polarization_purity = 1 - cross_pol_power / (total_power + 1e-10)
            polarization_purity = np.nan_to_num(polarization_purity, nan=1.0, posinf=1.0, neginf=1.0)
        
        # 主瓣区域
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        main_lobe_mask = self._create_mainlobe_mask(pattern, theta_max, phi_max)
        
        main_lobe_purity = polarization_purity[main_lobe_mask]
        
        return {
            'polarization_purity_min': float(np.min(polarization_purity)),
            'polarization_purity_max': float(np.max(polarization_purity)),
            'polarization_purity_mean': float(np.mean(polarization_purity)),
            'polarization_purity_std': float(np.std(polarization_purity)),
            'mainlobe_polarization_purity_mean': float(np.mean(main_lobe_purity)) if len(main_lobe_purity) > 0 else 0.0,
            'polarization_ratio_mean': float(np.mean(polarization_ratio)),
            'polarization_ratio_std': float(np.std(polarization_ratio))
        }
    
    def _analyze_polarization_ellipse(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析极化椭圆参数"""
        e_theta = pattern.e_theta_data
        e_phi = pattern.e_phi_data
        
        # 提取极化椭圆参数
        ellipse_params = self._calculate_polarization_ellipse(e_theta, e_phi)
        
        # 主瓣区域
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        main_lobe_mask = self._create_mainlobe_mask(pattern, theta_max, phi_max)
        
        main_lobe_params = {}
        for key, value in ellipse_params.items():
            if isinstance(value, np.ndarray):
                main_lobe_value = value[main_lobe_mask]
                main_lobe_params[f'mainlobe_{key}_mean'] = float(np.mean(main_lobe_value)) if len(main_lobe_value) > 0 else 0.0
                main_lobe_params[f'mainlobe_{key}_std'] = float(np.std(main_lobe_value)) if len(main_lobe_value) > 0 else 0.0
        
        return {**ellipse_params, **main_lobe_params}
    
    def _analyze_cross_polar_discrimination(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析交叉极化鉴别"""
        e_theta = pattern.e_theta_data
        e_phi = pattern.e_phi_data
        
        # 交叉极化鉴别度
        xpd = 20 * np.log10(np.abs(e_theta) / (np.abs(e_phi) + 1e-10))
        
        # 主瓣区域
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        main_lobe_mask = self._create_mainlobe_mask(pattern, theta_max, phi_max)
        
        main_lobe_xpd = xpd[main_lobe_mask]
        
        return {
            'xpd_min': float(np.min(xpd)),
            'xpd_max': float(np.max(xpd)),
            'xpd_mean': float(np.mean(xpd)),
            'xpd_std': float(np.std(xpd)),
            'mainlobe_xpd_mean': float(np.mean(main_lobe_xpd)) if len(main_lobe_xpd) > 0 else 0.0,
            'mainlobe_xpd_std': float(np.std(main_lobe_xpd)) if len(main_lobe_xpd) > 0 else 0.0
        }
    
    def _calculate_polarization_ellipse(self, e_theta: np.ndarray, e_phi: np.ndarray) -> Dict[str, Any]:
        """计算极化椭圆参数"""
        # 幅度和相位
        a_theta = np.abs(e_theta)
        a_phi = np.abs(e_phi)
        delta_theta = np.angle(e_theta)
        delta_phi = np.angle(e_phi)
        delta = delta_phi - delta_theta
        
        # 椭圆参数
        a_sq = a_theta**2 + a_phi**2
        b_sq = np.sqrt((a_theta**2 - a_phi**2)**2 + 4 * a_theta**2 * a_phi**2 * np.cos(delta)**2)
        
        # 椭圆轴长
        major_axis = np.sqrt((a_sq + b_sq) / 2)
        minor_axis = np.sqrt((a_sq - b_sq) / 2)
        
        # 轴比
        axial_ratio = major_axis / (minor_axis + 1e-10)
        
        # 倾角
        tan_2tau = 2 * a_theta * a_phi * np.cos(delta) / (a_theta**2 - a_phi**2)
        tau = 0.5 * np.arctan(tan_2tau)
        
        # 旋转方向
        sin_delta = np.sin(delta)
        rotation_direction = np.sign(sin_delta)
        
        return {
            'major_axis_mean': float(np.mean(major_axis)),
            'minor_axis_mean': float(np.mean(minor_axis)),
            'ellipticity': float(np.mean(minor_axis / (major_axis + 1e-10))),
            'tilt_angle_mean': float(np.mean(np.rad2deg(tau))),
            'rotation_direction_mean': float(np.mean(rotation_direction))
        }
    
    def _create_mainlobe_mask(self, pattern: RadiationPattern, 
                            theta_center: float, phi_center: float) -> np.ndarray:
        """创建主瓣掩码"""
        beamwidth_e = pattern.get_beamwidth('elevation', phi_center, -3)
        beamwidth_h = pattern.get_beamwidth('azimuth', theta_center, -3)
        
        theta_mask = np.abs(pattern.theta_grid[:, np.newaxis] - theta_center) <= beamwidth_e/2
        phi_mask = np.abs(pattern.phi_grid - phi_center) <= beamwidth_h/2
        
        return theta_mask & phi_mask
    
    def _calculate_ar_beamwidth(self, pattern: RadiationPattern, 
                              ar_threshold: float) -> float:
        """计算轴比波束宽度"""
        axial_ratio = pattern.axial_ratio_data
        
        # 找到最大增益点
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        
        # 获取轴比切面
        theta_idx = np.argmin(np.abs(pattern.theta_grid - theta_max))
        ar_slice = axial_ratio[theta_idx, :]
        
        # 找到轴比小于阈值的区域
        valid_mask = ar_slice <= ar_threshold
        
        if np.any(valid_mask):
            valid_indices = np.where(valid_mask)[0]
            beamwidth = pattern.phi_grid[valid_indices[-1]] - pattern.phi_grid[valid_indices[0]]
            return float(beamwidth)
        
        return 0.0

class EfficiencyAnalysisStrategy(AnalysisStrategy):
    """效率分析策略"""
    
    def analyze(self, pattern: RadiationPattern, antenna: AntennaParameters = None, **kwargs) -> Dict[str, Any]:
        """分析效率"""
        try:
            self.notify_start("效率分析", kwargs)
            
            self.results = {
                'efficiency_parameters': {},
                'power_parameters': {},
                'matching_parameters': {}
            }
            
            # 1. 辐射效率
            self.notify_progress(0.25, "计算辐射效率...")
            radiation_efficiency = self._calculate_radiation_efficiency(pattern, antenna)
            self.results['efficiency_parameters']['radiation_efficiency'] = radiation_efficiency
            
            # 2. 孔径效率
            self.notify_progress(0.5, "计算孔径效率...")
            aperture_efficiency = self._calculate_aperture_efficiency(pattern, antenna)
            self.results['efficiency_parameters']['aperture_efficiency'] = aperture_efficiency
            
            # 3. 波束效率
            self.notify_progress(0.75, "计算波束效率...")
            beam_efficiency = self._calculate_beam_efficiency(pattern)
            self.results['efficiency_parameters']['beam_efficiency'] = beam_efficiency
            
            # 4. 总效率
            self.notify_progress(0.9, "计算总效率...")
            total_efficiency = radiation_efficiency * aperture_efficiency
            self.results['efficiency_parameters']['total_efficiency'] = total_efficiency
            
            self.notify_complete()
            return self.results
            
        except Exception as e:
            self.notify_error(e)
            raise
    
    def _calculate_radiation_efficiency(self, pattern: RadiationPattern, 
                                       antenna: AntennaParameters = None) -> float:
        """计算辐射效率"""
        # 辐射效率 = 辐射功率 / 输入功率
        
        # 计算总辐射功率
        gain_data = pattern.gain_data
        theta_rad = np.deg2rad(pattern.theta_grid)
        
        # 积分计算总辐射功率
        power_density = 10**(gain_data/10)  # 功率密度
        integrand = power_density * np.sin(theta_rad[:, np.newaxis])
        
        # 数值积分
        total_power = np.trapz(np.trapz(integrand, pattern.phi_grid, axis=1), theta_rad)
        
        # 输入功率（如果已知）
        if antenna and hasattr(antenna, 'input_power'):
            input_power = antenna.input_power
        else:
            # 假设输入功率为1W
            input_power = 1.0
        
        # 辐射效率
        radiation_efficiency = total_power / (4 * np.pi * input_power)
        
        return float(radiation_efficiency)
    
    def _calculate_aperture_efficiency(self, pattern: RadiationPattern, 
                                      antenna: AntennaParameters = None) -> float:
        """计算孔径效率"""
        # 孔径效率 = 实际增益 / 理论最大增益
        
        # 实际增益
        actual_gain, _, _ = pattern.get_max_gain()
        actual_gain_linear = 10**(actual_gain/10)
        
        # 理论最大增益（均匀照射）
        if antenna and hasattr(antenna, 'geometry') and antenna.geometry.ground_plane:
            # 有孔径尺寸
            aperture_width, aperture_height = antenna.geometry.ground_plane
            aperture_area = aperture_width * aperture_height * 1e-6  # mm² -> m²
            
            frequency = pattern.frequency * 1e9
            wavelength = const.c / frequency
            
            theoretical_gain = 4 * np.pi * aperture_area / wavelength**2
        else:
            # 无法计算孔径效率
            return 1.0
        
        aperture_efficiency = actual_gain_linear / theoretical_gain
        
        return float(aperture_efficiency)
    
    def _calculate_beam_efficiency(self, pattern: RadiationPattern) -> float:
        """计算波束效率"""
        # 波束效率 = 主瓣功率 / 总功率
        
        # 计算总功率
        gain_data = pattern.gain_data
        theta_rad = np.deg2rad(pattern.theta_grid)
        
        power_density = 10**(gain_data/10)
        integrand = power_density * np.sin(theta_rad[:, np.newaxis])
        total_power = np.trapz(np.trapz(integrand, pattern.phi_grid, axis=1), theta_rad)
        
        # 计算主瓣功率
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        
        # 主瓣区域（±1.5倍波束宽度）
        beamwidth_e = pattern.get_beamwidth('elevation', phi_max, -3)
        beamwidth_h = pattern.get_beamwidth('azimuth', theta_max, -3)
        
        theta_range = (max(0, theta_max - 1.5*beamwidth_e/2), 
                      min(180, theta_max + 1.5*beamwidth_e/2))
        phi_range = (phi_max - 1.5*beamwidth_h/2, phi_max + 1.5*beamwidth_h/2)
        
        theta_mask = (pattern.theta_grid >= theta_range[0]) & (pattern.theta_grid <= theta_range[1])
        phi_mask = (pattern.phi_grid >= phi_range[0]) & (pattern.phi_grid <= phi_range[1])
        
        theta_idx = np.where(theta_mask)[0]
        phi_idx = np.where(phi_mask)[0]
        
        if len(theta_idx) == 0 or len(phi_idx) == 0:
            return 0.0
        
        mainlobe_integrand = integrand[theta_idx[0]:theta_idx[-1]+1, phi_idx[0]:phi_idx[-1]+1]
        mainlobe_theta = theta_rad[theta_idx[0]:theta_idx[-1]+1]
        mainlobe_phi = pattern.phi_grid[phi_idx[0]:phi_idx[-1]+1]
        
        mainlobe_power = np.trapz(np.trapz(mainlobe_integrand, mainlobe_phi, axis=1), mainlobe_theta)
        
        # 波束效率
        beam_efficiency = mainlobe_power / total_power if total_power > 0 else 0.0
        
        return float(beam_efficiency)

# ============================================================================
# 设计模式：工厂模式 - 创建分析器
# ============================================================================

class AnalysisFactory:
    """分析器工厂"""
    
    @staticmethod
    def create_analyzer(analyzer_type: str, 
                       observers: List[AnalysisObserver] = None) -> AnalysisStrategy:
        """创建分析器"""
        analyzers = {
            "beam": BeamAnalysisStrategy,
            "polarization": PolarizationAnalysisStrategy,
            "efficiency": EfficiencyAnalysisStrategy
        }
        
        if analyzer_type not in analyzers:
            raise ValueError(f"未知的分析器类型: {analyzer_type}")
        
        return analyzers[analyzer_type](observers)
    
    @staticmethod
    def get_available_analyzers() -> List[str]:
        """获取可用的分析器类型"""
        return ["beam", "polarization", "efficiency"]

# ============================================================================
# 设计模式：外观模式 - 简化分析接口
# ============================================================================

class AnalysisFacade:
    """分析外观类"""
    
    def __init__(self, observers: List[AnalysisObserver] = None):
        self.observers = observers or []
        self.analyzers = {}
        self.results_cache = {}
    
    def analyze(self, pattern: RadiationPattern, 
                analyzer_types: List[str] = None,
                **kwargs) -> Dict[str, Any]:
        """执行综合分析"""
        if analyzer_types is None:
            analyzer_types = AnalysisFactory.get_available_analyzers()
        
        all_results = {}
        
        for analyzer_type in analyzer_types:
            if analyzer_type not in self.analyzers:
                self.analyzers[analyzer_type] = AnalysisFactory.create_analyzer(
                    analyzer_type, self.observers
                )
            
            analyzer = self.analyzers[analyzer_type]
            results = analyzer.analyze(pattern, **kwargs)
            all_results[analyzer_type] = results
        
        # 合并结果
        merged_results = self._merge_results(all_results)
        
        return merged_results
    
    def analyze_comprehensive(self, pattern: RadiationPattern, 
                            antenna: AntennaParameters = None,
                            **kwargs) -> Dict[str, Any]:
        """执行全面分析"""
        # 所有分析类型
        analyzer_types = AnalysisFactory.get_available_analyzers()
        
        all_results = self.analyze(pattern, analyzer_types, **kwargs)
        
        # 添加总体评估
        overall_assessment = self._assess_overall_performance(all_results, antenna)
        all_results['overall_assessment'] = overall_assessment
        
        # 创建PatternStatistics对象
        pattern_stats = self._create_pattern_statistics(all_results, pattern)
        all_results['pattern_statistics'] = pattern_stats
        
        return all_results
    
    def _merge_results(self, results_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果"""
        merged = {}
        
        for analyzer_type, results in results_dict.items():
            merged[analyzer_type] = results
        
        return merged
    
    def _assess_overall_performance(self, 
                                  results: Dict[str, Any],
                                  antenna: AntennaParameters = None) -> Dict[str, Any]:
        """评估总体性能"""
        assessment = {
            'performance_score': 0.0,
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # 波束特性评分
        if 'beam' in results:
            beam_results = results['beam']['beam_parameters']
            
            # 增益评分
            peak_gain = beam_results.get('peak_gain', 0)
            gain_score = min(peak_gain / 30, 1.0)  # 假设30dB为满分
            
            # 波束宽度评分
            beamwidth_e = beam_results.get('main_lobe_width_3db_e', 90)
            beamwidth_score = max(0, 1 - beamwidth_e / 180)  # 越窄越好
            
            assessment['performance_score'] += (gain_score + beamwidth_score) / 2
            
            if peak_gain > 20:
                assessment['strengths'].append("高增益")
            if beamwidth_e < 30:
                assessment['strengths'].append("窄波束")
        
        # 极化特性评分
        if 'polarization' in results:
            pol_results = results['polarization']['axial_ratio']
            ar_mean = pol_results.get('mainlobe_axial_ratio_mean', 0)
            
            if ar_mean < 3:
                assessment['strengths'].append("良好圆极化")
                assessment['performance_score'] += 0.2
            elif ar_mean > 6:
                assessment['weaknesses'].append("轴比较差")
        
        # 效率评分
        if 'efficiency' in results:
            eff_results = results['efficiency']['efficiency_parameters']
            total_efficiency = eff_results.get('total_efficiency', 0)
            
            efficiency_score = total_efficiency
            assessment['performance_score'] += efficiency_score
            
            if total_efficiency > 0.7:
                assessment['strengths'].append("高效率")
            elif total_efficiency < 0.3:
                assessment['weaknesses'].append("低效率")
        
        # 归一化性能分数
        assessment['performance_score'] = min(1.0, assessment['performance_score'])
        
        # 生成建议
        if 'weaknesses' in assessment and assessment['weaknesses']:
            for weakness in assessment['weaknesses']:
                if "低效率" in weakness:
                    assessment['recommendations'].append("优化阻抗匹配以提高效率")
                if "轴比较差" in weakness:
                    assessment['recommendations'].append("优化馈电结构以改善极化纯度")
        
        return assessment
    
    def _create_pattern_statistics(self, 
                                 results: Dict[str, Any],
                                 pattern: RadiationPattern) -> PatternStatistics:
        """创建方向图统计对象"""
        beam_results = results.get('beam', {}).get('beam_parameters', {})
        pol_results = results.get('polarization', {}).get('axial_ratio', {})
        eff_results = results.get('efficiency', {}).get('efficiency_parameters', {})
        
        stats = PatternStatistics(
            max_gain=beam_results.get('peak_gain', 0),
            max_gain_theta=beam_results.get('peak_theta', 0),
            max_gain_phi=beam_results.get('peak_phi', 0),
            
            beamwidth_3db_e=beam_results.get('main_lobe_width_3db_e', 0),
            beamwidth_3db_h=beam_results.get('main_lobe_width_3db_h', 0),
            beamwidth_10db_e=results.get('beam', {}).get('beamwidths', {}).get('beamwidth_10db_e', 0),
            beamwidth_10db_h=results.get('beam', {}).get('beamwidths', {}).get('beamwidth_10db_h', 0),
            
            sidelobe_level_e=results.get('beam', {}).get('sidelobes', {}).get('max_sidelobe_level_e', 0),
            sidelobe_level_h=results.get('beam', {}).get('sidelobes', {}).get('max_sidelobe_level_h', 0),
            
            front_to_back_ratio=0,  # 需要专门计算
            front_to_side_ratio=0,  # 需要专门计算
            
            directivity=beam_results.get('peak_gain', 0),  # 近似
            efficiency=eff_results.get('total_efficiency', 0),
            axial_ratio_3db=pol_results.get('axial_ratio_3db_beamwidth', 0)
        )
        
        return stats

# ============================================================================
# 主服务类
# ============================================================================

class AnalysisService:
    """分析服务主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.facade = AnalysisFacade()
        self.observers = []
        
        # 添加默认观察者
        self.add_observer(LoggingObserver())
    
    def add_observer(self, observer: AnalysisObserver):
        """添加观察者"""
        self.observers.append(observer)
        self.facade.observers = self.observers
    
    def analyze_pattern(self, pattern: RadiationPattern, 
                       analyzer_types: List[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """分析方向图"""
        return self.facade.analyze(pattern, analyzer_types, **kwargs)
    
    def comprehensive_analysis(self, pattern: RadiationPattern, 
                             antenna: AntennaParameters = None,
                             **kwargs) -> Dict[str, Any]:
        """全面分析"""
        return self.facade.analyze_comprehensive(pattern, antenna, **kwargs)
    
    def compare_patterns(self, patterns: List[RadiationPattern],
                        pattern_names: List[str] = None,
                        **kwargs) -> Dict[str, Any]:
        """比较多个方向图"""
        if pattern_names is None:
            pattern_names = [f"Pattern_{i}" for i in range(len(patterns))]
        
        comparison_results = {
            'patterns': {},
            'comparison_metrics': {},
            'ranking': {}
        }
        
        # 分析每个方向图
        for i, (pattern, name) in enumerate(zip(patterns, pattern_names)):
            results = self.comprehensive_analysis(pattern, **kwargs)
            comparison_results['patterns'][name] = results
        
        # 计算比较指标
        comparison_results['comparison_metrics'] = self._calculate_comparison_metrics(
            comparison_results['patterns']
        )
        
        # 生成排名
        comparison_results['ranking'] = self._rank_patterns(
            comparison_results['patterns']
        )
        
        return comparison_results
    
    def _calculate_comparison_metrics(self, 
                                    pattern_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """计算比较指标"""
        metrics = {
            'gain_comparison': {},
            'beamwidth_comparison': {},
            'efficiency_comparison': {},
            'similarity_matrix': {}
        }
        
        # 提取关键指标
        gains = {}
        beamwidths = {}
        efficiencies = {}
        
        for name, results in pattern_results.items():
            beam_params = results.get('beam', {}).get('beam_parameters', {})
            eff_params = results.get('efficiency', {}).get('efficiency_parameters', {})
            
            gains[name] = beam_params.get('peak_gain', 0)
            beamwidths[name] = beam_params.get('main_lobe_width_3db_e', 0)
            efficiencies[name] = eff_params.get('total_efficiency', 0)
        
        # 比较指标
        if gains:
            metrics['gain_comparison'] = {
                'max': max(gains.values()),
                'min': min(gains.values()),
                'mean': np.mean(list(gains.values())),
                'std': np.std(list(gains.values()))
            }
        
        if beamwidths:
            metrics['beamwidth_comparison'] = {
                'max': max(beamwidths.values()),
                'min': min(beamwidths.values()),
                'mean': np.mean(list(beamwidths.values())),
                'std': np.std(list(beamwidths.values()))
            }
        
        if efficiencies:
            metrics['efficiency_comparison'] = {
                'max': max(efficiencies.values()),
                'min': min(efficiencies.values()),
                'mean': np.mean(list(efficiencies.values())),
                'std': np.std(list(efficiencies.values()))
            }
        
        # 计算相似度矩阵
        pattern_names = list(pattern_results.keys())
        similarity_matrix = np.zeros((len(pattern_names), len(pattern_names)))
        
        for i, name1 in enumerate(pattern_names):
            for j, name2 in enumerate(pattern_names):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    # 简化相似度计算
                    gain_sim = 1 - abs(gains[name1] - gains[name2]) / max(abs(gains[name1]), abs(gains[name2]), 1)
                    beamwidth_sim = 1 - abs(beamwidths[name1] - beamwidths[name2]) / max(abs(beamwidths[name1]), abs(beamwidths[name2]), 1)
                    
                    similarity_matrix[i, j] = (gain_sim + beamwidth_sim) / 2
        
        metrics['similarity_matrix'] = {
            'names': pattern_names,
            'matrix': similarity_matrix.tolist()
        }
        
        return metrics
    
    def _rank_patterns(self, pattern_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """对方向图进行排名"""
        scores = {}
        
        for name, results in pattern_results.items():
            assessment = results.get('overall_assessment', {})
            score = assessment.get('performance_score', 0)
            scores[name] = score
        
        # 按分数排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        ranking = {
            'ranked_patterns': [name for name, _ in sorted_scores],
            'scores': dict(sorted_scores),
            'best_pattern': sorted_scores[0][0] if sorted_scores else None,
            'worst_pattern': sorted_scores[-1][0] if sorted_scores else None
        }
        
        return ranking

# 全局服务实例
_analysis_service = None

def get_analysis_service(config: Dict[str, Any] = None) -> AnalysisService:
    """获取分析服务实例（单例模式）"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService(config)
    return _analysis_service