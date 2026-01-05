"""
天线可视化服务
将天线方向图和分析结果以丰富的图表形式展示
支持2D、3D、极坐标等多种可视化方式
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
import logging
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import warnings

from models.pattern_models import (
    RadiationPattern, PatternSlice, PatternComponent, 
    PatternFormat, PatternStatistics
)
from services.analysis_service import PatternStatistics as AnalysisPatternStatistics

# 设置日志
logger = logging.getLogger(__name__)

# 忽略matplotlib的警告
warnings.filterwarnings("ignore", category=UserWarning)

class PlotType(str, Enum):
    """绘图类型枚举"""
    SURFACE_3D = "surface_3d"          # 3D曲面图
    CONTOUR = "contour"                # 等高线图
    POLAR = "polar"                    # 极坐标图
    RECTANGULAR = "rectangular"        # 直角坐标图
    HEATMAP = "heatmap"                # 热力图
    WIREFRAME = "wireframe"            # 线框图
    BAR = "bar"                        # 柱状图
    SCATTER = "scatter"                # 散点图
    LINE = "line"                      # 折线图

class ColorMap(str, Enum):
    """颜色映射枚举"""
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"
    CIVIDIS = "cividis"
    JET = "jet"
    RAINBOW = "rainbow"
    COOLWARM = "coolwarm"
    HSV = "hsv"

class VisualizationConfig:
    """可视化配置"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 默认配置
        self.defaults = {
            'plot_type': PlotType.SURFACE_3D,
            'color_map': ColorMap.VIRIDIS,
            'show_colorbar': True,
            'show_contours': True,
            'transparent_bg': False,
            'dark_mode': False,
            'animation_enabled': False,
            'resolution': 'medium',  # low, medium, high
            'auto_range': True,
            'normalize': False,
            'max_gain': 0,
            'min_gain': -40
        }
        
        # 更新配置
        for key, value in self.config.items():
            if key in self.defaults:
                self.defaults[key] = value
    
    def __getattr__(self, name):
        if name in self.defaults:
            return self.defaults[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def update(self, config: Dict[str, Any]):
        """更新配置"""
        self.defaults.update(config)

class PatternVisualizer:
    """方向图可视化器"""
    
    def __init__(self, config: VisualizationConfig = None):
        self.config = config or VisualizationConfig()
        self.figure_cache = {}
    
    def create_radiation_pattern_plot(self, 
                                     pattern: RadiationPattern,
                                     plot_type: PlotType = None,
                                     component: PatternComponent = PatternComponent.TOTAL,
                                     **kwargs) -> go.Figure:
        """创建辐射方向图可视化"""
        if plot_type is None:
            plot_type = self.config.plot_type
        
        # 根据组件选择数据
        if component == PatternComponent.TOTAL:
            data = pattern.gain_data
            title_suffix = " (总场)"
        elif component == PatternComponent.THETA:
            data = 20 * np.log10(np.abs(pattern.e_theta_data) + 1e-10)
            title_suffix = " (Theta分量)"
        elif component == PatternComponent.PHI:
            data = 20 * np.log10(np.abs(pattern.e_phi_data) + 1e-10)
            title_suffix = " (Phi分量)"
        elif component == PatternComponent.CO_POLAR:
            # 这里简化处理，实际应根据极化方向选择
            data = pattern.gain_data
            title_suffix = " (同极化)"
        elif component == PatternComponent.CROSS_POLAR:
            # 这里简化处理，实际应根据极化方向选择
            data = 20 * np.log10(np.abs(pattern.e_phi_data) + 1e-10)
            title_suffix = " (交叉极化)"
        else:
            data = pattern.gain_data
            title_suffix = ""
        
        # 根据绘图类型创建图表
        if plot_type == PlotType.SURFACE_3D:
            return self._create_3d_surface_plot(pattern, data, title_suffix, **kwargs)
        elif plot_type == PlotType.CONTOUR:
            return self._create_contour_plot(pattern, data, title_suffix, **kwargs)
        elif plot_type == PlotType.POLAR:
            return self._create_polar_plot(pattern, data, title_suffix, **kwargs)
        elif plot_type == PlotType.HEATMAP:
            return self._create_heatmap_plot(pattern, data, title_suffix, **kwargs)
        elif plot_type == PlotType.WIREFRAME:
            return self._create_wireframe_plot(pattern, data, title_suffix, **kwargs)
        elif plot_type == PlotType.RECTANGULAR:
            return self._create_rectangular_plot(pattern, data, title_suffix, **kwargs)
        else:
            # 默认使用3D曲面图
            return self._create_3d_surface_plot(pattern, data, title_suffix, **kwargs)
    
    def create_pattern_slice_plot(self, 
                                 pattern_slice: PatternSlice,
                                 show_peaks: bool = True,
                                 show_widths: bool = True,
                                 **kwargs) -> go.Figure:
        """创建方向图切面图"""
        angles = pattern_slice.angles
        values = pattern_slice.values
        
        # 创建基础折线图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=angles,
            y=values,
            mode='lines',
            name=f'{pattern_slice.component}',
            line=dict(width=2, color='blue')
        ))
        
        # 标记峰值
        if show_peaks:
            peak_angle, peak_value = pattern_slice.find_peak()
            
            fig.add_trace(go.Scatter(
                x=[peak_angle],
                y=[peak_value],
                mode='markers',
                name='峰值',
                marker=dict(size=10, color='red', symbol='circle')
            ))
        
        # 标记波束宽度
        if show_widths:
            beamwidth_3db = pattern_slice.find_beamwidth(-3)
            beamwidth_10db = pattern_slice.find_beamwidth(-10)
            
            # 添加波束宽度标记
            if beamwidth_3db > 0:
                fig.add_shape(
                    type="line",
                    x0=angles[0], y0=peak_value-3, x1=angles[-1], y1=peak_value-3,
                    line=dict(color="red", width=1, dash="dash"),
                )
        
        # 更新布局
        fig.update_layout(
            title=f"{pattern_slice.plane}切面 ({pattern_slice.component}) - 固定角度: {pattern_slice.fixed_angle}°",
            xaxis_title="角度 (°)",
            yaxis_title="增益 (dB)",
            showlegend=True,
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def create_multiple_slices_plot(self, 
                                  slices: List[PatternSlice],
                                  slice_names: List[str] = None,
                                  **kwargs) -> go.Figure:
        """创建多个切面的对比图"""
        if slice_names is None:
            slice_names = [f"切面{i+1}" for i in range(len(slices))]
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Plotly
        
        for i, (pattern_slice, name) in enumerate(zip(slices, slice_names)):
            angles = pattern_slice.angles
            values = pattern_slice.values
            
            fig.add_trace(go.Scatter(
                x=angles,
                y=values,
                mode='lines',
                name=name,
                line=dict(width=2, color=colors[i % len(colors)]),
                opacity=0.8
            ))
        
        # 更新布局
        fig.update_layout(
            title="方向图切面对比",
            xaxis_title="角度 (°)",
            yaxis_title="增益 (dB)",
            showlegend=True,
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def create_polarization_plot(self, 
                               pattern: RadiationPattern,
                               **kwargs) -> go.Figure:
        """创建极化特性可视化"""
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("轴比分布", "极化椭圆", "交叉极化鉴别度", "极化纯度"),
            specs=[[{'type': 'surface'}, {'type': 'scatter'}],
                   [{'type': 'surface'}, {'type': 'surface'}]]
        )
        
        # 1. 轴比分布
        fig.add_trace(
            self._create_surface_trace(pattern, pattern.axial_ratio_data, "轴比 (dB)"),
            row=1, col=1
        )
        
        # 2. 极化椭圆（主瓣区域示例）
        fig.add_trace(
            self._create_polarization_ellipse_trace(pattern),
            row=1, col=2
        )
        
        # 3. 交叉极化鉴别度
        xpd = 20 * np.log10(np.abs(pattern.e_theta_data) / (np.abs(pattern.e_phi_data) + 1e-10))
        fig.add_trace(
            self._create_surface_trace(pattern, xpd, "交叉极化鉴别度 (dB)"),
            row=2, col=1
        )
        
        # 4. 极化纯度
        co_pol_power = np.abs(pattern.e_theta_data)**2
        cross_pol_power = np.abs(pattern.e_phi_data)**2
        purity = 1 - cross_pol_power / (co_pol_power + cross_pol_power + 1e-10)
        fig.add_trace(
            self._create_surface_trace(pattern, purity, "极化纯度"),
            row=2, col=2
        )
        
        # 更新布局
        fig.update_layout(
            title="极化特性分析",
            showlegend=False,
            height=800,
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def create_comparison_plot(self, 
                             patterns: List[RadiationPattern],
                             pattern_names: List[str] = None,
                             comparison_type: str = "gain",
                             **kwargs) -> go.Figure:
        """创建方向图对比图"""
        if pattern_names is None:
            pattern_names = [f"方向图{i+1}" for i in range(len(patterns))]
        
        if comparison_type == "gain":
            return self._create_gain_comparison_plot(patterns, pattern_names, **kwargs)
        elif comparison_type == "beamwidth":
            return self._create_beamwidth_comparison_plot(patterns, pattern_names, **kwargs)
        elif comparison_type == "efficiency":
            return self._create_efficiency_comparison_plot(patterns, pattern_names, **kwargs)
        else:
            return self._create_gain_comparison_plot(patterns, pattern_names, **kwargs)
    
    def create_statistics_dashboard(self, 
                                  pattern_stats: PatternStatistics,
                                  analysis_results: Dict[str, Any] = None,
                                  **kwargs) -> go.Figure:
        """创建统计仪表板"""
        # 创建子图布局
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=("关键指标", "波束宽度", "副瓣电平", 
                          "效率指标", "极化指标", "性能评分"),
            specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'bar'}, {'type': 'indicator'}]]
        )
        
        # 1. 关键指标
        key_metrics = {
            '最大增益': pattern_stats.max_gain,
            '方向性': pattern_stats.directivity,
            '前后比': pattern_stats.front_to_back_ratio,
            '轴比': pattern_stats.axial_ratio_3db
        }
        
        fig.add_trace(
            go.Bar(
                x=list(key_metrics.keys()),
                y=list(key_metrics.values()),
                name="关键指标",
                marker_color='royalblue'
            ),
            row=1, col=1
        )
        
        # 2. 波束宽度
        beamwidth_metrics = {
            '3dB E面': pattern_stats.beamwidth_3db_e,
            '3dB H面': pattern_stats.beamwidth_3db_h,
            '10dB E面': pattern_stats.beamwidth_10db_e,
            '10dB H面': pattern_stats.beamwidth_10db_h
        }
        
        fig.add_trace(
            go.Bar(
                x=list(beamwidth_metrics.keys()),
                y=list(beamwidth_metrics.values()),
                name="波束宽度",
                marker_color='lightseagreen'
            ),
            row=1, col=2
        )
        
        # 3. 副瓣电平
        sidelobe_metrics = {
            'E面副瓣': pattern_stats.sidelobe_level_e,
            'H面副瓣': pattern_stats.sidelobe_level_h
        }
        
        fig.add_trace(
            go.Bar(
                x=list(sidelobe_metrics.keys()),
                y=list(sidelobe_metrics.values()),
                name="副瓣电平",
                marker_color='coral'
            ),
            row=1, col=3
        )
        
        # 4. 效率指标
        if analysis_results and 'efficiency' in analysis_results:
            eff_metrics = analysis_results['efficiency']['efficiency_parameters']
            efficiency_data = {
                '辐射效率': eff_metrics.get('radiation_efficiency', 0),
                '孔径效率': eff_metrics.get('aperture_efficiency', 0),
                '波束效率': eff_metrics.get('beam_efficiency', 0),
                '总效率': eff_metrics.get('total_efficiency', 0)
            }
        else:
            efficiency_data = {
                '总效率': pattern_stats.efficiency
            }
        
        fig.add_trace(
            go.Bar(
                x=list(efficiency_data.keys()),
                y=list(efficiency_data.values()),
                name="效率指标",
                marker_color='gold'
            ),
            row=2, col=1
        )
        
        # 5. 极化指标
        if analysis_results and 'polarization' in analysis_results:
            pol_metrics = analysis_results['polarization']['axial_ratio']
            polarization_data = {
                '轴比均值': pol_metrics.get('axial_ratio_mean', 0),
                '轴比波动': pol_metrics.get('axial_ratio_std', 0),
                '主瓣轴比': pol_metrics.get('mainlobe_axial_ratio_mean', 0)
            }
        else:
            polarization_data = {}
        
        if polarization_data:
            fig.add_trace(
                go.Bar(
                    x=list(polarization_data.keys()),
                    y=list(polarization_data.values()),
                    name="极化指标",
                    marker_color='mediumpurple'
                ),
                row=2, col=2
            )
        
        # 6. 性能评分
        if analysis_results and 'overall_assessment' in analysis_results:
            performance_score = analysis_results['overall_assessment'].get('performance_score', 0)
        else:
            performance_score = 0.5  # 默认值
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=performance_score * 100,
                title={'text': "性能评分"},
                domain={'row': 1, 'col': 3},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "red"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ),
            row=2, col=3
        )
        
        # 更新布局
        fig.update_layout(
            title="天线性能统计仪表板",
            showlegend=False,
            height=600,
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_3d_surface_plot(self, 
                              pattern: RadiationPattern,
                              data: np.ndarray,
                              title_suffix: str,
                              **kwargs) -> go.Figure:
        """创建3D曲面图"""
        # 转换为笛卡尔坐标用于3D绘图
        theta_rad = np.deg2rad(pattern.theta_grid)
        phi_rad = np.deg2rad(pattern.phi_grid)
        
        # 球坐标转笛卡尔坐标
        x = data * np.sin(theta_rad) * np.cos(phi_rad)
        y = data * np.sin(theta_rad) * np.sin(phi_rad)
        z = data * np.cos(theta_rad)
        
        # 创建曲面
        fig = go.Figure(data=[
            go.Surface(
                x=x,
                y=y,
                z=z,
                surfacecolor=data,
                colorscale=self.config.color_map.value,
                colorbar=dict(title="增益 (dB)") if self.config.show_colorbar else None,
                contours={
                    "z": {"show": self.config.show_contours, "usecolormap": True}
                }
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title=f"辐射方向图{title_suffix} - 3D视图",
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y", 
                zaxis_title="Z",
                aspectmode="data"
            ),
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_contour_plot(self,
                           pattern: RadiationPattern,
                           data: np.ndarray,
                           title_suffix: str,
                           **kwargs) -> go.Figure:
        """创建等高线图"""
        fig = go.Figure(data=[
            go.Contour(
                z=data,
                x=pattern.phi_grid,
                y=pattern.theta_grid,
                colorscale=self.config.color_map.value,
                colorbar=dict(title="增益 (dB)"),
                contours=dict(
                    coloring='heatmap',
                    showlabels=True,
                    labelfont=dict(size=12, color='white')
                )
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title=f"辐射方向图{title_suffix} - 等高线图",
            xaxis_title="方位角 φ (°)",
            yaxis_title="俯仰角 θ (°)",
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_polar_plot(self,
                         pattern: RadiationPattern,
                         data: np.ndarray,
                         title_suffix: str,
                         **kwargs) -> go.Figure:
        """创建极坐标图"""
        # 选择特定phi切面（通常phi=0）
        phi_idx = np.argmin(np.abs(pattern.phi_grid - 0))
        polar_data = data[:, phi_idx]
        
        # 转换为极坐标
        theta_rad = np.deg2rad(pattern.theta_grid)
        
        fig = go.Figure(data=[
            go.Scatterpolar(
                r=polar_data,
                theta=pattern.theta_grid,
                mode='lines',
                line=dict(width=2, color='blue'),
                fill='toself',
                fillcolor='rgba(0, 0, 255, 0.3)'
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title=f"辐射方向图{title_suffix} - 极坐标图 (φ=0°)",
            polar=dict(
                radialaxis=dict(
                    title=dict(text="增益 (dB)", font=dict(size=12)),
                    angle=90,
                    tickangle=90
                ),
                angularaxis=dict(
                    direction="clockwise",
                    period=360
                )
            ),
            showlegend=False,
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_heatmap_plot(self,
                           pattern: RadiationPattern,
                           data: np.ndarray,
                           title_suffix: str,
                           **kwargs) -> go.Figure:
        """创建热力图"""
        fig = go.Figure(data=[
            go.Heatmap(
                z=data,
                x=pattern.phi_grid,
                y=pattern.theta_grid,
                colorscale=self.config.color_map.value,
                colorbar=dict(title="增益 (dB)")
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title=f"辐射方向图{title_suffix} - 热力图",
            xaxis_title="方位角 φ (°)",
            yaxis_title="俯仰角 θ (°)",
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_wireframe_plot(self,
                             pattern: RadiationPattern,
                             data: np.ndarray,
                             title_suffix: str,
                             **kwargs) -> go.Figure:
        """创建线框图"""
        # 下采样以提高性能
        theta_step = max(1, len(pattern.theta_grid) // 20)
        phi_step = max(1, len(pattern.phi_grid) // 20)
        
        theta_sampled = pattern.theta_grid[::theta_step]
        phi_sampled = pattern.phi_grid[::phi_step]
        data_sampled = data[::theta_step, ::phi_step]
        
        # 转换为笛卡尔坐标
        theta_rad = np.deg2rad(theta_sampled)
        phi_rad = np.deg2rad(phi_sampled)
        
        theta_grid, phi_grid = np.meshgrid(theta_rad, phi_rad, indexing='ij')
        
        x = data_sampled * np.sin(theta_grid) * np.cos(phi_grid)
        y = data_sampled * np.sin(theta_grid) * np.sin(phi_grid)
        z = data_sampled * np.cos(theta_grid)
        
        fig = go.Figure(data=[
            go.Mesh3d(
                x=x.flatten(),
                y=y.flatten(),
                z=z.flatten(),
                intensity=data_sampled.flatten(),
                colorscale=self.config.color_map.value,
                opacity=0.5,
                flatshading=True
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title=f"辐射方向图{title_suffix} - 线框图",
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y", 
                zaxis_title="Z"
            ),
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_rectangular_plot(self,
                               pattern: RadiationPattern,
                               data: np.ndarray,
                               title_suffix: str,
                               **kwargs) -> go.Figure:
        """创建直角坐标图"""
        # 创建多个切面的子图
        phi_values = [0, 45, 90, 135]
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[f"φ = {phi}°" for phi in phi_values]
        )
        
        for i, phi in enumerate(phi_values):
            row = i // 2 + 1
            col = i % 2 + 1
            
            phi_idx = np.argmin(np.abs(pattern.phi_grid - phi))
            slice_data = data[:, phi_idx]
            
            fig.add_trace(
                go.Scatter(
                    x=pattern.theta_grid,
                    y=slice_data,
                    mode='lines',
                    name=f'φ={phi}°',
                    line=dict(width=2)
                ),
                row=row, col=col
            )
        
        # 更新布局
        fig.update_layout(
            title=f"辐射方向图{title_suffix} - 直角坐标图",
            showlegend=False,
            height=600,
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        # 更新坐标轴标签
        for i in range(1, 5):
            fig.update_xaxes(title_text="俯仰角 θ (°)", row=(i+1)//2, col=(i-1)%2+1)
            fig.update_yaxes(title_text="增益 (dB)", row=(i+1)//2, col=(i-1)%2+1)
        
        return fig
    
    def _create_surface_trace(self, 
                            pattern: RadiationPattern,
                            data: np.ndarray,
                            colorbar_title: str) -> go.Surface:
        """创建曲面跟踪数据"""
        # 转换为笛卡尔坐标
        theta_rad = np.deg2rad(pattern.theta_grid)
        phi_rad = np.deg2rad(pattern.phi_grid)
        
        x = data * np.sin(theta_rad) * np.cos(phi_rad)
        y = data * np.sin(theta_rad) * np.sin(phi_rad)
        z = data * np.cos(theta_rad)
        
        return go.Surface(
            x=x,
            y=y,
            z=z,
            surfacecolor=data,
            colorscale=self.config.color_map.value,
            colorbar=dict(title=colorbar_title),
            opacity=0.8
        )
    
    def _create_polarization_ellipse_trace(self, pattern: RadiationPattern) -> go.Scatter:
        """创建极化椭圆跟踪数据"""
        # 在主瓣区域采样几个点
        max_gain, theta_max, phi_max = pattern.get_max_gain()
        
        # 采样角度
        sample_theta = np.linspace(max(0, theta_max-10), min(180, theta_max+10), 5)
        sample_phi = np.linspace(phi_max-10, phi_max+10, 5)
        
        # 创建椭圆数据
        ellipse_data = []
        
        for theta in sample_theta:
            for phi in sample_phi:
                theta_idx = np.argmin(np.abs(pattern.theta_grid - theta))
                phi_idx = np.argmin(np.abs(pattern.phi_grid - phi))
                
                e_theta = pattern.e_theta_data[theta_idx, phi_idx]
                e_phi = pattern.e_phi_data[theta_idx, phi_idx]
                
                # 计算椭圆参数
                a_theta = np.abs(e_theta)
                a_phi = np.abs(e_phi)
                delta = np.angle(e_phi) - np.angle(e_theta)
                
                # 生成椭圆点
                t = np.linspace(0, 2*np.pi, 50)
                x = a_theta * np.cos(t)
                y = a_phi * np.cos(t + delta)
                
                # 添加到数据
                for xi, yi in zip(x, y):
                    ellipse_data.append({
                        'x': xi,
                        'y': yi,
                        'theta': theta,
                        'phi': phi
                    })
        
        # 转换为DataFrame用于绘图
        import pandas as pd
        df = pd.DataFrame(ellipse_data)
        
        return go.Scatter(
            x=df['x'],
            y=df['y'],
            mode='markers',
            marker=dict(
                size=3,
                color=df['theta'],  # 用theta值着色
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="θ (°)")
            ),
            text=[f"θ={row['theta']:.1f}°, φ={row['phi']:.1f}°" for _, row in df.iterrows()],
            hoverinfo='text'
        )
    
    def _create_gain_comparison_plot(self, 
                                   patterns: List[RadiationPattern],
                                   pattern_names: List[str],
                                   **kwargs) -> go.Figure:
        """创建增益对比图"""
        fig = go.Figure()
        
        colors = px.colors.qualitative.Plotly
        
        for i, (pattern, name) in enumerate(zip(patterns, pattern_names)):
            # 获取主切面
            max_gain, theta_max, phi_max = pattern.get_max_gain()
            slice_data = pattern.get_slice(fixed_phi=phi_max)
            
            fig.add_trace(go.Scatter(
                x=slice_data.angles,
                y=slice_data.values,
                mode='lines',
                name=name,
                line=dict(width=2, color=colors[i % len(colors)]),
                opacity=0.8
            ))
        
        # 更新布局
        fig.update_layout(
            title="方向图增益对比",
            xaxis_title="俯仰角 θ (°)",
            yaxis_title="增益 (dB)",
            showlegend=True,
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_beamwidth_comparison_plot(self, 
                                        patterns: List[RadiationPattern],
                                        pattern_names: List[str],
                                        **kwargs) -> go.Figure:
        """创建波束宽度对比图"""
        beamwidths_3db = []
        beamwidths_10db = []
        
        for pattern in patterns:
            max_gain, theta_max, phi_max = pattern.get_max_gain()
            
            beamwidth_3db = pattern.get_beamwidth('elevation', phi_max, -3)
            beamwidth_10db_val = pattern.get_beamwidth('elevation', phi_max, -10)
            
            beamwidths_3db.append(beamwidth_3db)
            beamwidths_10db.append(beamwidth_10db_val)
        
        fig = go.Figure(data=[
            go.Bar(
                x=pattern_names,
                y=beamwidths_3db,
                name='3dB波束宽度',
                marker_color='royalblue'
            ),
            go.Bar(
                x=pattern_names,
                y=beamwidths_10db,
                name='10dB波束宽度',
                marker_color='lightseagreen'
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title="波束宽度对比",
            xaxis_title="方向图",
            yaxis_title="波束宽度 (°)",
            barmode='group',
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig
    
    def _create_efficiency_comparison_plot(self, 
                                         patterns: List[RadiationPattern],
                                         pattern_names: List[str],
                                         **kwargs) -> go.Figure:
        """创建效率对比图"""
        # 这里需要效率数据，简化处理
        efficiencies = []
        
        for pattern in patterns:
            # 简化效率计算
            max_gain, _, _ = pattern.get_max_gain()
            # 假设效率与增益相关
            efficiency = min(1.0, max_gain / 30)
            efficiencies.append(efficiency)
        
        fig = go.Figure(data=[
            go.Bar(
                x=pattern_names,
                y=efficiencies,
                marker_color='coral',
                text=[f'{eff:.1%}' for eff in efficiencies],
                textposition='auto'
            )
        ])
        
        # 更新布局
        fig.update_layout(
            title="效率对比",
            xaxis_title="方向图",
            yaxis_title="效率",
            template="plotly_white" if not self.config.dark_mode else "plotly_dark"
        )
        
        return fig

class AnimationGenerator:
    """动画生成器"""
    
    @staticmethod
    def create_pattern_animation(patterns: List[RadiationPattern],
                               pattern_names: List[str] = None,
                               animation_type: str = "rotation",
                               **kwargs) -> go.Figure:
        """创建方向图动画"""
        if pattern_names is None:
            pattern_names = [f"Frame {i+1}" for i in range(len(patterns))]
        
        if animation_type == "rotation":
            return AnimationGenerator._create_rotation_animation(patterns, pattern_names, **kwargs)
        elif animation_type == "evolution":
            return AnimationGenerator._create_evolution_animation(patterns, pattern_names, **kwargs)
        else:
            return AnimationGenerator._create_rotation_animation(patterns, pattern_names, **kwargs)
    
    @staticmethod
    def _create_rotation_animation(patterns: List[RadiationPattern],
                                 pattern_names: List[str],
                                 **kwargs) -> go.Figure:
        """创建旋转动画"""
        # 这里简化处理，实际应使用plotly的动画功能
        fig = go.Figure()
        
        # 添加第一帧
        first_pattern = patterns[0]
        data = first_pattern.gain_data
        
        # 转换为笛卡尔坐标
        theta_rad = np.deg2rad(first_pattern.theta_grid)
        phi_rad = np.deg2rad(first_pattern.phi_grid)
        
        x = data * np.sin(theta_rad) * np.cos(phi_rad)
        y = data * np.sin(theta_rad) * np.sin(phi_rad)
        z = data * np.cos(theta_rad)
        
        fig.add_trace(go.Surface(
            x=x,
            y=y,
            z=z,
            surfacecolor=data,
            colorscale="Viridis",
            name=pattern_names[0]
        ))
        
        # 创建动画帧
        frames = []
        for i, (pattern, name) in enumerate(zip(patterns, pattern_names)):
            data = pattern.gain_data
            
            theta_rad = np.deg2rad(pattern.theta_grid)
            phi_rad = np.deg2rad(pattern.phi_grid)
            
            x = data * np.sin(theta_rad) * np.cos(phi_rad)
            y = data * np.sin(theta_rad) * np.sin(phi_rad)
            z = data * np.cos(theta_rad)
            
            frames.append(go.Frame(
                data=[go.Surface(
                    x=x,
                    y=y,
                    z=z,
                    surfacecolor=data,
                    colorscale="Viridis"
                )],
                name=name
            ))
        
        fig.frames = frames
        
        # 动画按钮
        fig.update_layout(
            updatemenus=[{
                "buttons": [
                    {
                        "args": [None, {"frame": {"duration": 500, "redraw": True},
                                      "fromcurrent": True, "transition": {"duration": 300}}],
                        "label": "播放",
                        "method": "animate"
                    },
                    {
                        "args": [[None], {"frame": {"duration": 0, "redraw": True},
                                        "mode": "immediate",
                                        "transition": {"duration": 0}}],
                        "label": "暂停",
                        "method": "animate"
                    }
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "showactive": False,
                "type": "buttons",
                "x": 0.1,
                "xanchor": "right",
                "y": 0,
                "yanchor": "top"
            }],
            sliders=[{
                "active": 0,
                "yanchor": "top",
                "xanchor": "left",
                "currentvalue": {
                    "font": {"size": 20},
                    "prefix": "帧: ",
                    "visible": True,
                    "xanchor": "right"
                },
                "transition": {"duration": 300, "easing": "cubic-in-out"},
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [{
                    "args": [[f.name], {"frame": {"duration": 300, "redraw": True},
                                      "mode": "immediate",
                                      "transition": {"duration": 300}}],
                    "label": f.name,
                    "method": "animate"
                } for f in frames]
            }]
        )
        
        return fig
    
    @staticmethod
    def _create_evolution_animation(patterns: List[RadiationPattern],
                                  pattern_names: List[str],
                                  **kwargs) -> go.Figure:
        """创建演化动画"""
        # 简化实现
        return AnimationGenerator._create_rotation_animation(patterns, pattern_names, **kwargs)

# ============================================================================
# 主服务类
# ============================================================================

class VisualizationService:
    """可视化服务主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = VisualizationConfig(config)
        self.visualizer = PatternVisualizer(self.config)
        self.animation_generator = AnimationGenerator()
    
    def plot_radiation_pattern(self, 
                             pattern: RadiationPattern,
                             plot_type: PlotType = None,
                             component: PatternComponent = PatternComponent.TOTAL,
                             **kwargs) -> go.Figure:
        """绘制辐射方向图"""
        return self.visualizer.create_radiation_pattern_plot(
            pattern, plot_type, component, **kwargs
        )
    
    def plot_pattern_slice(self, 
                          pattern_slice: PatternSlice,
                          **kwargs) -> go.Figure:
        """绘制方向图切面"""
        return self.visualizer.create_pattern_slice_plot(pattern_slice, **kwargs)
    
    def plot_multiple_slices(self, 
                           slices: List[PatternSlice],
                           slice_names: List[str] = None,
                           **kwargs) -> go.Figure:
        """绘制多个切面"""
        return self.visualizer.create_multiple_slices_plot(slices, slice_names, **kwargs)
    
    def plot_polarization(self, 
                         pattern: RadiationPattern,
                         **kwargs) -> go.Figure:
        """绘制极化特性"""
        return self.visualizer.create_polarization_plot(pattern, **kwargs)
    
    def plot_comparison(self, 
                       patterns: List[RadiationPattern],
                       pattern_names: List[str] = None,
                       comparison_type: str = "gain",
                       **kwargs) -> go.Figure:
        """绘制对比图"""
        return self.visualizer.create_comparison_plot(
            patterns, pattern_names, comparison_type, **kwargs
        )
    
    def plot_statistics_dashboard(self, 
                                pattern_stats: PatternStatistics,
                                analysis_results: Dict[str, Any] = None,
                                **kwargs) -> go.Figure:
        """绘制统计仪表板"""
        return self.visualizer.create_statistics_dashboard(
            pattern_stats, analysis_results, **kwargs
        )
    
    def create_animation(self, 
                        patterns: List[RadiationPattern],
                        pattern_names: List[str] = None,
                        animation_type: str = "rotation",
                        **kwargs) -> go.Figure:
        """创建动画"""
        return self.animation_generator.create_pattern_animation(
            patterns, pattern_names, animation_type, **kwargs
        )
    
    def get_available_plot_types(self) -> List[str]:
        """获取可用的绘图类型"""
        return [pt.value for pt in PlotType]
    
    def get_available_color_maps(self) -> List[str]:
        """获取可用的颜色映射"""
        return [cm.value for cm in ColorMap]
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)

# 全局服务实例
_visualization_service = None

def get_visualization_service(config: Dict[str, Any] = None) -> VisualizationService:
    """获取可视化服务实例（单例模式）"""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService(config)
    return _visualization_service