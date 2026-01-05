"""
可视化服务
将天线方向图和分析结果以多种图表形式展示
使用多种设计模式实现灵活的可视化框架
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.subplots as sp
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from typing import List, Tuple, Optional, Dict, Any, Union, Callable
import pandas as pd
import json
import base64
from io import BytesIO
import logging
from abc import ABC, abstractmethod
from enum import Enum

from models.antenna_models import AntennaParameters, AntennaArray
from models.pattern_models import (
    RadiationPattern, PatternSlice, PatternComponent, 
    PatternFormat, PatternStatistics
)

# 设置日志
logger = logging.getLogger(__name__)

# 设置matplotlib中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================================
# 设计模式：策略模式 - 不同的可视化策略
# ============================================================================

class VisualizationStrategy(ABC):
    """可视化策略抽象基类"""
    
    def __init__(self, figsize=(10, 6), dpi=100):
        self.figsize = figsize
        self.dpi = dpi
        self.color_palette = px.colors.qualitative.Set3
    
    @abstractmethod
    def create_visualization(self, data: Any, **kwargs) -> go.Figure:
        """创建可视化图表"""
        pass
    
    def save_to_file(self, fig: go.Figure, filename: str, **kwargs):
        """保存图表到文件"""
        format = kwargs.get('format', 'png')
        width = kwargs.get('width', 1200)
        height = kwargs.get('height', 800)
        scale = kwargs.get('scale', 2)
        
        if format == 'html':
            fig.write_html(filename)
        elif format == 'png':
            fig.write_image(filename, width=width, height=height, scale=scale)
        elif format == 'pdf':
            fig.write_image(filename, format='pdf', width=width, height=height)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def get_base64_image(self, fig: go.Figure, **kwargs) -> str:
        """获取图表的Base64编码"""
        width = kwargs.get('width', 800)
        height = kwargs.get('height', 600)
        scale = kwargs.get('scale', 1)
        
        # 转换为图片并编码
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=scale)
        base64_str = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/png;base64,{base64_str}"
    
    def _apply_template(self, fig: go.Figure, title: str = None) -> go.Figure:
        """应用模板样式"""
        template = go.layout.Template()
        
        # 设置颜色
        template.layout.colorway = self.color_palette
        
        # 设置字体
        template.layout.font = dict(family="Arial, sans-serif", size=12)
        template.layout.title = dict(font=dict(size=16, color='#2c3e50'))
        
        # 设置坐标轴
        template.layout.xaxis = dict(
            showgrid=True, gridwidth=1, gridcolor='#ecf0f1',
            showline=True, linewidth=2, linecolor='#bdc3c7',
            zeroline=False
        )
        template.layout.yaxis = dict(
            showgrid=True, gridwidth=1, gridcolor='#ecf0f1',
            showline=True, linewidth=2, linecolor='#bdc3c7',
            zeroline=False
        )
        
        # 设置图例
        template.layout.legend = dict(
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#bdc3c7',
            borderwidth=1,
            font=dict(size=10)
        )
        
        fig.update_layout(template=template)
        
        if title:
            fig.update_layout(
                title=dict(
                    text=title,
                    x=0.5,
                    xanchor='center',
                    font=dict(size=18, color='#2c3e50')
                )
            )
        
        return fig

class Pattern2DVisualization(VisualizationStrategy):
    """2D方向图可视化策略"""
    
    def create_visualization(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """创建2D方向图可视化"""
        component = kwargs.get('component', PatternComponent.TOTAL)
        fixed_angle = kwargs.get('fixed_angle', 0.0)
        plane = kwargs.get('plane', 'elevation')
        
        # 获取切面
        if plane == 'elevation':
            pattern_slice = pattern.get_slice(component=component, fixed_phi=fixed_angle)
            plane_label = '俯仰面'
            fixed_label = f'方位角={fixed_angle}°'
        else:
            pattern_slice = pattern.get_slice(component=component, fixed_theta=fixed_angle)
            plane_label = '方位面'
            fixed_label = f'俯仰角={fixed_angle}°'
        
        # 创建图形
        fig = go.Figure()
        
        # 添加主瓣切面
        fig.add_trace(go.Scatter(
            x=pattern_slice.angles,
            y=pattern_slice.values,
            mode='lines',
            name=f'{plane_label} - {component.value}',
            line=dict(width=3, color='#3498db'),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.2)'
        ))
        
        # 标记峰值
        peak_angle, peak_value = pattern_slice.find_peak()
        fig.add_trace(go.Scatter(
            x=[peak_angle],
            y=[peak_value],
            mode='markers+text',
            name='峰值',
            marker=dict(size=12, color='#e74c3c'),
            text=[f'峰值: {peak_value:.1f}dB @ {peak_angle:.1f}°'],
            textposition='top center',
            showlegend=False
        ))
        
        # 标记3dB波束宽度
        beamwidth = pattern_slice.find_beamwidth(-3)
        if beamwidth > 0:
            fig.add_trace(go.Scatter(
                x=[peak_angle - beamwidth/2, peak_angle + beamwidth/2],
                y=[peak_value - 3, peak_value - 3],
                mode='lines+markers',
                name='3dB波束宽度',
                line=dict(width=2, color='#2ecc71', dash='dash'),
                marker=dict(size=8, color='#2ecc71'),
                text=[f'波束宽度: {beamwidth:.1f}°'],
                textposition='top center',
                showlegend=True
            ))
        
        # 更新布局
        fig = self._apply_template(fig, f'{pattern.name} - {plane_label}方向图')
        
        fig.update_layout(
            xaxis_title=f'{plane_label}角 (度)',
            yaxis_title='增益 (dBi)',
            hovermode='x unified',
            plot_bgcolor='white',
            width=kwargs.get('width', 1000),
            height=kwargs.get('height', 600)
        )
        
        # 添加网格
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
        
        # 添加副瓣标记
        sidelobes = self._find_sidelobes(pattern_slice)
        for i, sidelobe in enumerate(sidelobes[:3]):  # 只显示前3个副瓣
            fig.add_annotation(
                x=sidelobe['angle'],
                y=sidelobe['level'],
                text=f"S{i+1}: {sidelobe['level']-peak_value:.1f}dB",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='#f39c12',
                ax=0,
                ay=-40
            )
        
        return fig
    
    def _find_sidelobes(self, pattern_slice: PatternSlice) -> List[Dict[str, float]]:
        """找到副瓣"""
        from scipy.signal import find_peaks
        
        values = pattern_slice.values
        angles = pattern_slice.angles
        
        # 找到所有峰值
        peaks, properties = find_peaks(values, distance=10)
        
        # 排除主瓣（最高峰）
        if len(peaks) > 0:
            main_lobe_idx = np.argmax(values[peaks])
            peaks = np.delete(peaks, main_lobe_idx)
        
        # 创建副瓣信息
        sidelobes = []
        for peak_idx in peaks:
            sidelobes.append({
                'angle': angles[peak_idx],
                'level': values[peak_idx]
            })
        
        # 按电平降序排序
        sidelobes.sort(key=lambda x: x['level'], reverse=True)
        return sidelobes

class Pattern3DVisualization(VisualizationStrategy):
    """3D方向图可视化策略"""
    
    def create_visualization(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """创建3D方向图可视化"""
        component = kwargs.get('component', PatternComponent.TOTAL)
        normalize = kwargs.get('normalize', True)
        
        # 准备数据
        theta = pattern.theta_grid
        phi = pattern.phi_grid
        
        if component == PatternComponent.TOTAL:
            data = pattern.gain_data
        elif component == PatternComponent.THETA:
            data = 20 * np.log10(np.abs(pattern.e_theta_data) + 1e-10)
        elif component == PatternComponent.PHI:
            data = 20 * np.log10(np.abs(pattern.e_phi_data) + 1e-10)
        else:
            data = pattern.gain_data
        
        if normalize:
            data_max = np.max(data)
            data = data - data_max
        
        # 转换为球坐标
        theta_rad = np.deg2rad(theta)
        phi_rad = np.deg2rad(phi)
        
        # 创建网格
        theta_grid, phi_grid = np.meshgrid(theta_rad, phi_rad, indexing='ij')
        
        # 转换为笛卡尔坐标用于3D绘图
        r = np.abs(data)  # 使用绝对值作为半径
        x = r * np.sin(theta_grid) * np.cos(phi_grid)
        y = r * np.sin(theta_grid) * np.sin(phi_grid)
        z = r * np.cos(theta_grid)
        
        # 创建3D表面图
        fig = go.Figure(data=[
            go.Surface(
                x=x, y=y, z=z,
                surfacecolor=data,
                colorscale='Viridis',
                colorbar=dict(title="增益 (dBi)"),
                contours=dict(
                    z=dict(show=True, size=5, color='white'),
                    x=dict(show=False),
                    y=dict(show=False)
                ),
                lighting=dict(
                    ambient=0.8,
                    diffuse=0.8,
                    fresnel=0.1,
                    specular=1,
                    roughness=0.5
                ),
                opacity=0.9
            )
        ])
        
        # 更新布局
        fig = self._apply_template(fig, f'{pattern.name} - 3D方向图')
        
        fig.update_layout(
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
                zaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                aspectmode='cube'
            ),
            width=kwargs.get('width', 1000),
            height=kwargs.get('height', 800)
        )
        
        return fig

class PolarPlotVisualization(VisualizationStrategy):
    """极坐标方向图可视化策略"""
    
    def create_visualization(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """创建极坐标方向图"""
        component = kwargs.get('component', PatternComponent.TOTAL)
        fixed_angle = kwargs.get('fixed_angle', 0.0)
        
        # 获取多个切面
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('E面方向图', 'H面方向图'),
            specs=[[{'type': 'polar'}, {'type': 'polar'}]]
        )
        
        # E面 (phi=0)
        e_slice = pattern.get_slice(component=component, fixed_phi=0)
        fig.add_trace(
            go.Scatterpolar(
                r=e_slice.values,
                theta=e_slice.angles,
                mode='lines',
                name='E面',
                line=dict(width=3, color='#3498db'),
                fill='toself',
                fillcolor='rgba(52, 152, 219, 0.3)'
            ),
            row=1, col=1
        )
        
        # H面 (theta=90)
        h_slice = pattern.get_slice(component=component, fixed_theta=90)
        fig.add_trace(
            go.Scatterpolar(
                r=h_slice.values,
                theta=h_slice.angles,
                mode='lines',
                name='H面',
                line=dict(width=3, color='#e74c3c'),
                fill='toself',
                fillcolor='rgba(231, 76, 60, 0.3)'
            ),
            row=1, col=2
        )
        
        # 更新极坐标图布局
        fig.update_polars(
            angularaxis=dict(
                direction='clockwise',
                rotation=90,
                tickmode='array',
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°']
            ),
            radialaxis=dict(
                angle=90,
                tickangle=90,
                range=[np.min(e_slice.values) - 10, np.max(e_slice.values) + 5]
            )
        )
        
        # 更新整体布局
        fig = self._apply_template(fig, f'{pattern.name} - 极坐标方向图')
        
        fig.update_layout(
            showlegend=True,
            width=kwargs.get('width', 1200),
            height=kwargs.get('height', 600)
        )
        
        return fig

class AxialRatioVisualization(VisualizationStrategy):
    """轴比可视化策略"""
    
    def create_visualization(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """创建轴比可视化"""
        axial_ratio = pattern.axial_ratio_data
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '轴比3D方向图', 
                'E面轴比分布',
                'H面轴比分布', 
                '轴比统计直方图'
            ),
            specs=[
                [{'type': 'surface'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'xy'}]
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. 3D轴比方向图
        theta = pattern.theta_grid
        phi = pattern.phi_grid
        
        theta_rad = np.deg2rad(theta)
        phi_rad = np.deg2rad(phi)
        theta_grid, phi_grid = np.meshgrid(theta_rad, phi_rad, indexing='ij')
        
        r = np.clip(axial_ratio, 0, 20)  # 限制显示范围
        x = r * np.sin(theta_grid) * np.cos(phi_grid)
        y = r * np.sin(theta_grid) * np.sin(phi_grid)
        z = r * np.cos(theta_grid)
        
        fig.add_trace(
            go.Surface(
                x=x, y=y, z=z,
                surfacecolor=axial_ratio,
                colorscale='RdYlGn_r',  # 红色表示轴比差，绿色表示轴比好
                colorbar=dict(title="轴比 (dB)"),
                cmin=0, cmax=20,
                contours_z=dict(show=True, size=5),
                opacity=0.8
            ),
            row=1, col=1
        )
        
        # 2. E面轴比分布
        e_slice_ar = axial_ratio[:, np.argmin(np.abs(pattern.phi_grid - 0))]
        fig.add_trace(
            go.Scatter(
                x=pattern.theta_grid,
                y=e_slice_ar,
                mode='lines',
                name='E面',
                line=dict(width=3, color='#3498db'),
                fill='tozeroy',
                fillcolor='rgba(52, 152, 219, 0.2)'
            ),
            row=1, col=2
        )
        
        # 添加3dB阈值线
        fig.add_hline(
            y=3,
            line=dict(width=2, color='#e74c3c', dash='dash'),
            row=1, col=2
        )
        
        # 3. H面轴比分布
        h_slice_ar = axial_ratio[np.argmin(np.abs(pattern.theta_grid - 90)), :]
        fig.add_trace(
            go.Scatter(
                x=pattern.phi_grid,
                y=h_slice_ar,
                mode='lines',
                name='H面',
                line=dict(width=3, color='#e74c3c'),
                fill='tozeroy',
                fillcolor='rgba(231, 76, 60, 0.2)'
            ),
            row=2, col=1
        )
        
        fig.add_hline(
            y=3,
            line=dict(width=2, color='#3498db', dash='dash'),
            row=2, col=1
        )
        
        # 4. 轴比统计直方图
        ar_flat = axial_ratio.flatten()
        fig.add_trace(
            go.Histogram(
                x=ar_flat,
                nbinsx=50,
                name='轴比分布',
                marker_color='#9b59b6',
                opacity=0.7
            ),
            row=2, col=2
        )
        
        # 更新布局
        fig = self._apply_template(fig, f'{pattern.name} - 轴比分析')
        
        fig.update_layout(
            width=kwargs.get('width', 1200),
            height=kwargs.get('height', 800)
        )
        
        # 更新子图标签
        fig.update_xaxes(title_text="俯仰角 (度)", row=1, col=2)
        fig.update_yaxes(title_text="轴比 (dB)", row=1, col=2)
        fig.update_xaxes(title_text="方位角 (度)", row=2, col=1)
        fig.update_yaxes(title_text="轴比 (dB)", row=2, col=1)
        fig.update_xaxes(title_text="轴比 (dB)", row=2, col=2)
        fig.update_yaxes(title_text="频数", row=2, col=2)
        
        return fig

class ComparisonVisualization(VisualizationStrategy):
    """比较可视化策略"""
    
    def create_visualization(self, patterns: List[RadiationPattern], **kwargs) -> go.Figure:
        """创建比较可视化"""
        pattern_names = kwargs.get('pattern_names', [f'Pattern_{i}' for i in range(len(patterns))])
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '增益方向图对比',
                '波束宽度对比',
                '轴比对比',
                '效率对比'
            ),
            specs=[[{'type': 'xy'}, {'type': 'xy'}],
                   [{'type': 'xy'}, {'type': 'xy'}]]
        )
        
        colors = px.colors.qualitative.Set3
        
        # 1. 增益方向图对比
        for i, (pattern, name) in enumerate(zip(patterns, pattern_names)):
            # 获取E面切面
            e_slice = pattern.get_slice(fixed_phi=0)
            
            fig.add_trace(
                go.Scatter(
                    x=e_slice.angles,
                    y=e_slice.values,
                    mode='lines',
                    name=name,
                    line=dict(width=2, color=colors[i % len(colors)]),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        # 2. 波束宽度对比
        beamwidths_3db = []
        beamwidths_10db = []
        
        for pattern in patterns:
            beamwidth_3db = pattern.get_beamwidth('elevation', 0, -3)
            beamwidth_10db = pattern.get_beamwidth('elevation', 0, -10)
            
            beamwidths_3db.append(beamwidth_3db)
            beamwidths_10db.append(beamwidth_10db)
        
        fig.add_trace(
            go.Bar(
                x=pattern_names,
                y=beamwidths_3db,
                name='3dB波束宽度',
                marker_color='#3498db',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(
                x=pattern_names,
                y=beamwidths_10db,
                name='10dB波束宽度',
                marker_color='#e74c3c',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        # 3. 轴比对比
        axial_ratios = []
        
        for pattern in patterns:
            ar_data = pattern.axial_ratio_data
            # 计算主瓣区域平均轴比
            max_gain, theta_max, phi_max = pattern.get_max_gain()
            
            # 简单平均
            axial_ratios.append(np.mean(ar_data))
        
        fig.add_trace(
            go.Bar(
                x=pattern_names,
                y=axial_ratios,
                name='平均轴比',
                marker_color='#2ecc71',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # 添加3dB阈值线
        fig.add_hline(
            y=3,
            line=dict(width=2, color='red', dash='dash'),
            row=2, col=1
        )
        
        # 4. 效率对比（需要分析结果）
        # 这里使用模拟数据
        efficiencies = np.random.random(len(patterns)) * 0.5 + 0.5
        
        fig.add_trace(
            go.Bar(
                x=pattern_names,
                y=efficiencies,
                name='效率',
                marker_color='#9b59b6',
                opacity=0.7
            ),
            row=2, col=2
        )
        
        # 更新布局
        fig = self._apply_template(fig, '天线性能对比分析')
        
        fig.update_layout(
            width=kwargs.get('width', 1200),
            height=kwargs.get('height', 800),
            barmode='group',
            showlegend=True
        )
        
        # 更新子图标签
        fig.update_xaxes(title_text="角度 (度)", row=1, col=1)
        fig.update_yaxes(title_text="增益 (dBi)", row=1, col=1)
        fig.update_xaxes(title_text="天线", row=1, col=2)
        fig.update_yaxes(title_text="波束宽度 (度)", row=1, col=2)
        fig.update_xaxes(title_text="天线", row=2, col=1)
        fig.update_yaxes(title_text="轴比 (dB)", row=2, col=1)
        fig.update_xaxes(title_text="天线", row=2, col=2)
        fig.update_yaxes(title_text="效率", row=2, col=2)
        
        return fig

class StatisticsVisualization(VisualizationStrategy):
    """统计分析可视化策略"""
    
    def create_visualization(self, analysis_results: Dict[str, Any], **kwargs) -> go.Figure:
        """创建统计分析可视化"""
        # 创建子图
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                '关键指标雷达图',
                '波束参数分布',
                '效率分析',
                '副瓣电平分布',
                '极化参数分布',
                '性能评分'
            ),
            specs=[
                [{'type': 'polar'}, {'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}]
            ]
        )
        
        colors = px.colors.qualitative.Set3
        
        # 1. 关键指标雷达图
        if 'beam' in analysis_results:
            beam_params = analysis_results['beam']['beam_parameters']
            
            categories = ['增益', '波束宽度', '副瓣电平', '对称性', '效率']
            values = [
                beam_params.get('peak_gain', 0) / 30,  # 归一化
                1 - beam_params.get('main_lobe_width_3db_e', 90) / 180,  # 越小越好
                1 - abs(analysis_results.get('beam', {}).get('sidelobes', {}).get('max_sidelobe_level_e', 0)) / 30,
                0.8,  # 模拟对称性
                analysis_results.get('efficiency', {}).get('efficiency_parameters', {}).get('total_efficiency', 0.5)
            ]
            
            fig.add_trace(
                go.Scatterpolar(
                    r=values + [values[0]],  # 闭合曲线
                    theta=categories + [categories[0]],
                    fill='toself',
                    name='性能指标',
                    line=dict(width=3, color=colors[0]),
                    fillcolor='rgba(52, 152, 219, 0.3)'
                ),
            row=1, col=1
            )
        
        # 2. 波束参数分布
        if 'beam' in analysis_results:
            beam_params = analysis_results['beam']['beam_parameters']
            
            param_names = ['峰值增益', 'E面波束宽度', 'H面波束宽度']
            param_values = [
                beam_params.get('peak_gain', 0),
                beam_params.get('main_lobe_width_3db_e', 0),
                beam_params.get('main_lobe_width_3db_h', 0)
            ]
            
            fig.add_trace(
                go.Bar(
                    x=param_names,
                    y=param_values,
                    name='波束参数',
                    marker_color=colors[1],
                    text=[f'{v:.1f}' for v in param_values],
                    textposition='auto'
                ),
                row=1, col=2
            )
        
        # 3. 效率分析
        if 'efficiency' in analysis_results:
            eff_params = analysis_results['efficiency']['efficiency_parameters']
            
            eff_names = ['辐射效率', '孔径效率', '波束效率', '总效率']
            eff_values = [
                eff_params.get('radiation_efficiency', 0),
                eff_params.get('aperture_efficiency', 0),
                eff_params.get('beam_efficiency', 0),
                eff_params.get('total_efficiency', 0)
            ]
            
            fig.add_trace(
                go.Bar(
                    x=eff_names,
                    y=eff_values,
                    name='效率参数',
                    marker_color=colors[2],
                    text=[f'{v:.2f}' for v in eff_values],
                    textposition='auto'
                ),
                row=1, col=3
            )
        
        # 4. 副瓣电平分布
        if 'beam' in analysis_results:
            sidelobes = analysis_results['beam']['sidelobes']
            
            # 创建副瓣电平分布
            sidelobe_levels = [
                sidelobes.get('max_sidelobe_level_e', 0),
                sidelobes.get('max_sidelobe_level_h', 0),
                sidelobes.get('avg_sidelobe_level_e', 0),
                sidelobes.get('avg_sidelobe_level_h', 0)
            ]
            sidelobe_names = ['E面最大', 'H面最大', 'E面平均', 'H面平均']
            
            fig.add_trace(
                go.Bar(
                    x=sidelobe_names,
                    y=sidelobe_levels,
                    name='副瓣电平',
                    marker_color=colors[3],
                    text=[f'{v:.1f}dB' for v in sidelobe_levels],
                    textposition='auto'
                ),
                row=2, col=1
            )
        
        # 5. 极化参数分布
        if 'polarization' in analysis_results:
            pol_params = analysis_results['polarization']['axial_ratio']
            
            pol_names = ['最小轴比', '最大轴比', '平均轴比', '3dB轴比宽度']
            pol_values = [
                pol_params.get('axial_ratio_min', 0),
                pol_params.get('axial_ratio_max', 0),
                pol_params.get('axial_ratio_mean', 0),
                pol_params.get('axial_ratio_3db_beamwidth', 0)
            ]
            
            fig.add_trace(
                go.Bar(
                    x=pol_names,
                    y=pol_values,
                    name='极化参数',
                    marker_color=colors[4],
                    text=[f'{v:.1f}' for v in pol_values],
                    textposition='auto'
                ),
                row=2, col=2
            )
        
        # 6. 性能评分
        if 'overall_assessment' in analysis_results:
            assessment = analysis_results['overall_assessment']
            
            performance_score = assessment.get('performance_score', 0) * 100
            
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=performance_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "性能评分"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': colors[5]},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"},
                            {'range': [80, 100], 'color': "darkgray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ),
                row=2, col=3
            )
        
        # 更新布局
        fig = self._apply_template(fig, '天线性能统计分析')
        
        fig.update_layout(
            width=kwargs.get('width', 1400),
            height=kwargs.get('height', 900),
            showlegend=True
        )
        
        return fig

# ============================================================================
# 设计模式：工厂模式 - 创建可视化器
# ============================================================================

class VisualizationFactory:
    """可视化器工厂"""
    
    @staticmethod
    def create_visualizer(viz_type: str, **kwargs) -> VisualizationStrategy:
        """创建可视化器"""
        visualizers = {
            '2d_pattern': Pattern2DVisualization,
            '3d_pattern': Pattern3DVisualization,
            'polar_pattern': PolarPlotVisualization,
            'axial_ratio': AxialRatioVisualization,
            'comparison': ComparisonVisualization,
            'statistics': StatisticsVisualization
        }
        
        if viz_type not in visualizers:
            raise ValueError(f"未知的可视化类型: {viz_type}")
        
        return visualizers[viz_type](**kwargs)
    
    @staticmethod
    def get_available_visualizers() -> List[str]:
        """获取可用的可视化类型"""
        return [
            '2d_pattern', 
            '3d_pattern', 
            'polar_pattern', 
            'axial_ratio',
            'comparison',
            'statistics'
        ]

# ============================================================================
# 设计模式：外观模式 - 简化可视化接口
# ============================================================================

class VisualizationFacade:
    """可视化外观类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.visualizers = {}
        self.cache = {}
    
    def visualize(self, data: Any, viz_type: str, **kwargs) -> go.Figure:
        """创建可视化"""
        cache_key = self._create_cache_key(data, viz_type, kwargs)
        
        # 检查缓存
        if cache_key in self.cache:
            logger.info("从缓存加载可视化")
            return self.cache[cache_key]
        
        # 创建可视化器
        if viz_type not in self.visualizers:
            self.visualizers[viz_type] = VisualizationFactory.create_visualizer(viz_type)
        
        visualizer = self.visualizers[viz_type]
        
        # 创建可视化
        fig = visualizer.create_visualization(data, **kwargs)
        
        # 缓存结果
        self.cache[cache_key] = fig
        
        return fig
    
    def visualize_multiple(self, data_list: List[Any], viz_types: List[str], **kwargs) -> List[go.Figure]:
        """创建多个可视化"""
        figures = []
        
        for data, viz_type in zip(data_list, viz_types):
            fig = self.visualize(data, viz_type, **kwargs)
            figures.append(fig)
        
        return figures
    
    def save_visualization(self, fig: go.Figure, filename: str, **kwargs):
        """保存可视化到文件"""
        format = kwargs.get('format', 'png')
        
        if format == 'html':
            fig.write_html(filename)
        elif format in ['png', 'jpg', 'pdf', 'svg']:
            fig.write_image(filename, format=format)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def get_embed_html(self, fig: go.Figure, **kwargs) -> str:
        """获取嵌入HTML"""
        width = kwargs.get('width', '100%')
        height = kwargs.get('height', '600px')
        
        return fig.to_html(
            include_plotlyjs='cdn',
            full_html=False,
            default_width=width,
            default_height=height
        )
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
    
    def _create_cache_key(self, data: Any, viz_type: str, kwargs: Dict[str, Any]) -> str:
        """创建缓存键"""
        import hashlib
        import pickle
        
        # 序列化参数
        cache_data = {
            'viz_type': viz_type,
            'kwargs': kwargs,
            'data_hash': self._get_data_hash(data)
        }
        
        # 创建哈希
        serialized = pickle.dumps(cache_data)
        return hashlib.md5(serialized).hexdigest()
    
    def _get_data_hash(self, data: Any) -> str:
        """获取数据哈希"""
        import hashlib
        import pickle
        
        if hasattr(data, 'to_dict'):
            data_dict = data.to_dict()
        elif isinstance(data, dict):
            data_dict = data
        else:
            data_dict = {'data': str(data)}
        
        serialized = pickle.dumps(data_dict)
        return hashlib.md5(serialized).hexdigest()

# ============================================================================
# 主服务类
# ============================================================================

class VisualizationService:
    """可视化服务主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.facade = VisualizationFacade(config)
        self.default_styles = {
            '2d_pattern': {'width': 1000, 'height': 600},
            '3d_pattern': {'width': 1000, 'height': 800},
            'polar_pattern': {'width': 1200, 'height': 600},
            'axial_ratio': {'width': 1200, 'height': 800},
            'comparison': {'width': 1200, 'height': 800},
            'statistics': {'width': 1400, 'height': 900}
        }
    
    def visualize_pattern_2d(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """2D方向图可视化"""
        style = {**self.default_styles['2d_pattern'], **kwargs}
        return self.facade.visualize(pattern, '2d_pattern', **style)
    
    def visualize_pattern_3d(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """3D方向图可视化"""
        style = {**self.default_styles['3d_pattern'], **kwargs}
        return self.facade.visualize(pattern, '3d_pattern', **style)
    
    def visualize_pattern_polar(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """极坐标方向图可视化"""
        style = {**self.default_styles['polar_pattern'], **kwargs}
        return self.facade.visualize(pattern, 'polar_pattern', **style)
    
    def visualize_axial_ratio(self, pattern: RadiationPattern, **kwargs) -> go.Figure:
        """轴比可视化"""
        style = {**self.default_styles['axial_ratio'], **kwargs}
        return self.facade.visualize(pattern, 'axial_ratio', **style)
    
    def visualize_comparison(self, patterns: List[RadiationPattern], **kwargs) -> go.Figure:
        """比较可视化"""
        style = {**self.default_styles['comparison'], **kwargs}
        return self.facade.visualize(patterns, 'comparison', **style)
    
    def visualize_statistics(self, analysis_results: Dict[str, Any], **kwargs) -> go.Figure:
        """统计分析可视化"""
        style = {**self.default_styles['statistics'], **kwargs}
        return self.facade.visualize(analysis_results, 'statistics', **style)
    
    def create_dashboard(self, pattern: RadiationPattern, 
                        analysis_results: Dict[str, Any] = None,
                        **kwargs) -> go.Figure:
        """创建综合仪表板"""
        # 创建子图
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                '3D方向图', 'E面方向图', 'H面方向图',
                '极坐标方向图', '轴比分布', '波束参数',
                '效率分析', '极化分析', '性能评估'
            ),
            specs=[
                [{'type': 'surface'}, {'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'polar'}, {'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'xy'}, {'type': 'indicator'}]
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )
        
        # 1. 3D方向图
        fig_3d = self.visualize_pattern_3d(pattern, width=400, height=300)
        fig.add_trace(fig_3d.data[0], row=1, col=1)
        
        # 2. E面方向图
        e_slice = pattern.get_slice(fixed_phi=0)
        fig.add_trace(
            go.Scatter(
                x=e_slice.angles,
                y=e_slice.values,
                mode='lines',
                name='E面',
                line=dict(width=2, color='#3498db'),
                fill='tozeroy',
                fillcolor='rgba(52, 152, 219, 0.2)'
            ),
            row=1, col=2
        )
        
        # 3. H面方向图
        h_slice = pattern.get_slice(fixed_theta=90)
        fig.add_trace(
            go.Scatter(
                x=h_slice.angles,
                y=h_slice.values,
                mode='lines',
                name='H面',
                line=dict(width=2, color='#e74c3c'),
                fill='tozeroy',
                fillcolor='rgba(231, 76, 60, 0.2)'
            ),
            row=1, col=3
        )
        
        # 4. 极坐标方向图
        fig_polar = self.visualize_pattern_polar(pattern, width=400, height=300)
        # 注意：这里需要适当处理极坐标图的添加
        
        # 5. 轴比分布
        if hasattr(pattern, 'axial_ratio_data'):
            ar_slice = pattern.axial_ratio_data[:, 0]
            fig.add_trace(
                go.Scatter(
                    x=pattern.theta_grid,
                    y=ar_slice,
                    mode='lines',
                    name='轴比',
                    line=dict(width=2, color='#2ecc71')
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title_text=f"{pattern.name} - 综合仪表板",
            showlegend=False,
            width=1400,
            height=900
        )
        
        return fig
    
    def save_figure(self, fig: go.Figure, filename: str, **kwargs):
        """保存图表"""
        self.facade.save_visualization(fig, filename, **kwargs)
    
    def get_embed_code(self, fig: go.Figure, **kwargs) -> str:
        """获取嵌入代码"""
        return self.facade.get_embed_html(fig, **kwargs)
    
    def clear_cache(self):
        """清空缓存"""
        self.facade.clear_cache()

# 全局服务实例
_visualization_service = None

def get_visualization_service(config: Dict[str, Any] = None) -> VisualizationService:
    """获取可视化服务实例（单例模式）"""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService(config)
    return _visualization_service