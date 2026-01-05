"""
分析视图
提供详细的天线性能分析和交互式分析工具
包括波束特性、极化特性、效率分析、比较分析等功能
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import yaml
from pathlib import Path
import datetime
import sys
import os
from scipy import signal, interpolate

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.antenna_models import AntennaParameters, AntennaType, PolarizationType
from models.pattern_models import (
    RadiationPattern, PatternSlice, PatternComponent, 
    PatternCoordinateSystem, PatternStatistics
)
from services.pattern_generator import get_pattern_generator_service
from services.analysis_service import get_analysis_service, ProgressObserver
from services.visualization_service import get_visualization_service
from utils.config import AppConfig
from utils.helpers import format_frequency, format_gain, format_percentage, format_angle

class AnalysisView:
    """分析视图类"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.pattern_service = get_pattern_generator_service()
        self.analysis_service = get_analysis_service()
        self.viz_service = get_visualization_service()
        self.progress_observer = None
        
    def render(self, sidebar_config: Dict[str, Any]):
        """渲染分析视图"""
        st.title("🔍 天线性能分析")
        
        # 检查是否有可分析的数据
        if not self._check_analysis_data():
            return
        
        # 创建分析标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 波束分析", 
            "🔄 极化分析", 
            "⚡ 效率分析",
            "📡 频域分析",
            "⚖️ 比较分析"
        ])
        
        with tab1:
            self._render_beam_analysis(sidebar_config)
        
        with tab2:
            self._render_polarization_analysis(sidebar_config)
        
        with tab3:
            self._render_efficiency_analysis(sidebar_config)
        
        with tab4:
            self._render_frequency_analysis(sidebar_config)
        
        with tab5:
            self._render_comparative_analysis(sidebar_config)
        
        # 底部工具栏
        self._render_analysis_toolbar()
    
    def _check_analysis_data(self) -> bool:
        """检查是否有可分析的数据"""
        if 'pattern_data' not in st.session_state or st.session_state.pattern_data is None:
            st.warning("⚠️ 没有可用的方向图数据")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("""
                请先运行仿真生成方向图数据：
                1. 在侧边栏配置天线参数
                2. 设置仿真参数
                3. 点击"运行仿真"按钮
                """)
            
            with col2:
                if st.button("🚀 运行示例仿真", width='stretch', type="primary"):
                    self._run_example_simulation()
            
            return False
        
        return True
    
    def _run_example_simulation(self):
        """运行示例仿真"""
        with st.spinner("正在运行示例仿真..."):
            # 使用示例天线
            from models.antenna_models import create_patch_antenna
            example_antenna = create_patch_antenna()
            
            # 生成方向图
            pattern_service = get_pattern_generator_service()
            pattern = pattern_service.generate_pattern(
                example_antenna,
                generator_type='analytical',
                theta_resolution=2,
                phi_resolution=2
            )
            
            # 保存到session
            st.session_state.current_antenna = example_antenna
            st.session_state.pattern_data = pattern
            
            st.success("示例仿真完成！")
            st.rerun()
    
    def _setup_progress_monitor(self):
        """设置进度监视器"""
        if self.progress_observer is None:
            self.progress_observer = ProgressObserver(
                progress_callback=self._update_progress,
                message_callback=self._update_progress_message
            )
            self.analysis_service.add_observer(self.progress_observer)
    
    def _update_progress(self, progress: float):
        """更新进度条"""
        if 'progress_bar' in st.session_state:
            st.session_state.progress_bar.progress(progress)
    
    def _update_progress_message(self, message: str):
        """更新进度消息"""
        if 'progress_text' in st.session_state:
            st.session_state.progress_text.text(message)
    
    def _render_beam_analysis(self, sidebar_config: Dict[str, Any]):
        """渲染波束特性分析"""
        st.markdown("### 📈 波束特性分析")
        
        # 获取当前数据
        pattern = st.session_state.pattern_data
        antenna = st.session_state.get('current_antenna')
        
        # 波束分析控制面板
        with st.expander("⚙️ 分析设置", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                plane = st.radio(
                    "分析平面",
                    ["E面 (固定Phi)", "H面 (固定Theta)", "自定义"],
                    horizontal=True
                )
                
                if plane == "E面 (固定Phi)":
                    fixed_phi = st.number_input("固定Phi角度 (°)", 0.0, 360.0, 0.0, 1.0)
                    fixed_angle = fixed_phi
                    plane_type = 'elevation'
                elif plane == "H面 (固定Theta)":
                    fixed_theta = st.number_input("固定Theta角度 (°)", 0.0, 180.0, 90.0, 1.0)
                    fixed_angle = fixed_theta
                    plane_type = 'azimuth'
                else:
                    col_angle1, col_angle2 = st.columns(2)
                    with col_angle1:
                        fixed_phi = st.number_input("Phi角度 (°)", 0.0, 360.0, 0.0, 1.0)
                    with col_angle2:
                        fixed_theta = st.number_input("Theta角度 (°)", 0.0, 180.0, 90.0, 1.0)
                    fixed_angle = fixed_phi
                    plane_type = 'elevation'
            
            with col2:
                beamwidth_levels = st.multiselect(
                    "波束宽度计算",
                    ["3dB", "6dB", "10dB", "20dB"],
                    default=["3dB", "10dB"]
                )
                
                find_nulls = st.checkbox("查找零陷", value=True)
                find_sidelobes = st.checkbox("分析副瓣", value=True)
            
            with col3:
                component = st.selectbox(
                    "场分量",
                    ["总场", "Theta分量", "Phi分量", "同极化", "交叉极化"],
                    index=0
                )
                
                component_map = {
                    "总场": PatternComponent.TOTAL,
                    "Theta分量": PatternComponent.THETA,
                    "Phi分量": PatternComponent.PHI,
                    "同极化": PatternComponent.CO_POLAR,
                    "交叉极化": PatternComponent.CROSS_POLAR
                }
                selected_component = component_map[component]
        
        # 运行分析按钮
        if st.button("🔍 运行波束分析", type="primary", width='stretch'):
            with st.spinner("正在分析波束特性..."):
                self._run_beam_analysis(pattern, plane_type, fixed_angle, selected_component, 
                                      beamwidth_levels, find_nulls, find_sidelobes)
        
        # 显示分析结果
        if 'beam_analysis_results' in st.session_state:
            self._display_beam_analysis_results(st.session_state.beam_analysis_results)
    
    def _run_beam_analysis(self, pattern: RadiationPattern, plane_type: str, 
                          fixed_angle: float, component: PatternComponent,
                          beamwidth_levels: List[str], find_nulls: bool, 
                          find_sidelobes: bool):
        """运行波束分析"""
        try:
            # 获取方向图切面
            if plane_type == 'elevation':
                slice_data = pattern.get_slice(component=component, fixed_phi=fixed_angle)
            else:
                slice_data = pattern.get_slice(component=component, fixed_theta=fixed_angle)
            
            # 分析结果
            results = {
                'slice_data': slice_data,
                'plane_type': plane_type,
                'fixed_angle': fixed_angle,
                'component': component.value,
                'basic_metrics': {},
                'beamwidths': {},
                'nulls': [],
                'sidelobes': []
            }
            
            # 1. 基本指标
            peak_angle, peak_value = slice_data.find_peak()
            results['basic_metrics']['peak_gain'] = float(peak_value)
            results['basic_metrics']['peak_angle'] = float(peak_angle)
            
            # 2. 波束宽度
            for level_str in beamwidth_levels:
                level = -float(level_str.replace('dB', ''))
                beamwidth = slice_data.find_beamwidth(level)
                results['beamwidths'][level_str] = float(beamwidth)
            
            # 3. 查找零陷
            if find_nulls:
                nulls = self._find_nulls_in_slice(slice_data)
                results['nulls'] = nulls
            
            # 4. 分析副瓣
            if find_sidelobes:
                sidelobes = self._find_sidelobes_in_slice(slice_data)
                results['sidelobes'] = sidelobes
            
            # 保存结果
            st.session_state.beam_analysis_results = results
            
            # 计算对称性
            symmetry = self._analyze_symmetry(slice_data, peak_angle)
            results['basic_metrics']['symmetry'] = symmetry
            
            st.success("波束分析完成！")
            
        except Exception as e:
            st.error(f"波束分析失败: {e}")
            st.exception(e)
    
    def _find_nulls_in_slice(self, slice_data: PatternSlice, min_depth: float = 10.0) -> List[Dict[str, Any]]:
        """在切面中查找零陷"""
        angles = slice_data.angles
        values = slice_data.values
        
        from scipy.signal import find_peaks
        
        # 找到谷值
        valleys, _ = find_peaks(-values)
        
        nulls = []
        for valley_idx in valleys:
            # 找到最近的峰值
            left_idx = max(0, valley_idx - 5)
            right_idx = min(len(values) - 1, valley_idx + 5)
            local_max = max(values[left_idx:right_idx])
            null_depth = local_max - values[valley_idx]
            
            if null_depth >= min_depth:
                nulls.append({
                    'angle': float(angles[valley_idx]),
                    'depth': float(null_depth),
                    'level': float(values[valley_idx])
                })
        
        # 按深度排序
        nulls.sort(key=lambda x: x['depth'], reverse=True)
        return nulls[:5]  # 返回前5个最深的零陷
    
    def _find_sidelobes_in_slice(self, slice_data: PatternSlice, 
                               min_distance: float = 5.0) -> List[Dict[str, Any]]:
        """在切面中查找副瓣"""
        angles = slice_data.angles
        values = slice_data.values
        
        from scipy.signal import find_peaks
        
        # 找到所有峰值
        distance = int(min_distance / np.mean(np.diff(angles)))
        peaks, properties = find_peaks(values, distance=max(1, distance))
        
        # 排除主瓣（最高的峰值）
        if len(peaks) > 0:
            main_lobe_idx = np.argmax(values[peaks])
            main_lobe_peak = peaks[main_lobe_idx]
            
            sidelobes = []
            for i, peak_idx in enumerate(peaks):
                if peak_idx != main_lobe_peak:
                    # 计算相对主瓣的电平
                    relative_level = values[peak_idx] - values[main_lobe_peak]
                    
                    # 计算波束宽度
                    width = 0.0
                    if 'widths' in properties and i < len(properties['widths']):
                        width = float(properties['widths'][i])
                    
                    sidelobes.append({
                        'angle': float(angles[peak_idx]),
                        'level': float(values[peak_idx]),
                        'relative_level': float(relative_level),
                        'width': width
                    })
            
            # 按相对电平排序（从高到低）
            sidelobes.sort(key=lambda x: x['relative_level'], reverse=True)
            return sidelobes[:10]  # 返回前10个副瓣
        
        return []
    
    def _analyze_symmetry(self, slice_data: PatternSlice, peak_angle: float) -> Dict[str, Any]:
        """分析波束对称性"""
        angles = slice_data.angles
        values = slice_data.values
        
        # 对称性分析
        left_idx = np.where(angles < peak_angle)[0]
        right_idx = np.where(angles > peak_angle)[0]
        
        if len(left_idx) > 0 and len(right_idx) > 0:
            # 插值以匹配点数
            left_angles = angles[left_idx] - peak_angle
            right_angles = angles[right_idx] - peak_angle
            
            # 对称角度范围
            max_angle = min(abs(left_angles[-1]), abs(right_angles[0]))
            
            # 创建插值函数
            from scipy import interpolate
            interp_func = interpolate.interp1d(angles, values, kind='cubic', 
                                             bounds_error=False, fill_value=np.nan)
            
            # 对称性误差
            eval_angles = np.linspace(-max_angle, max_angle, 100) + peak_angle
            left_values = interp_func(peak_angle - np.abs(eval_angles - peak_angle))
            right_values = interp_func(peak_angle + np.abs(eval_angles - peak_angle))
            
            # 计算误差
            valid_mask = ~np.isnan(left_values) & ~np.isnan(right_values)
            if np.any(valid_mask):
                symmetry_error = np.mean(np.abs(left_values[valid_mask] - right_values[valid_mask]))
                symmetry_correlation = np.corrcoef(left_values[valid_mask], right_values[valid_mask])[0, 1]
            else:
                symmetry_error = np.nan
                symmetry_correlation = 0.0
        else:
            symmetry_error = np.nan
            symmetry_correlation = 0.0
        
        return {
            'symmetry_error': float(symmetry_error) if not np.isnan(symmetry_error) else 0.0,
            'symmetry_correlation': float(symmetry_correlation)
        }
    
    def _display_beam_analysis_results(self, results: Dict[str, Any]):
        """显示波束分析结果"""
        st.markdown("---")
        
        # 结果概览
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            peak_gain = results['basic_metrics'].get('peak_gain', 0)
            st.metric("峰值增益", f"{peak_gain:.1f} dB")
        
        with col2:
            peak_angle = results['basic_metrics'].get('peak_angle', 0)
            st.metric("峰值角度", f"{peak_angle:.1f}°")
        
        with col3:
            if '3dB' in results['beamwidths']:
                beamwidth = results['beamwidths']['3dB']
                st.metric("3dB波束宽度", f"{beamwidth:.1f}°")
        
        with col4:
            symmetry = results['basic_metrics'].get('symmetry', {})
            error = symmetry.get('symmetry_error', 0)
            st.metric("对称性误差", f"{error:.2f} dB")
        
        # 图表显示
        st.markdown("### 📊 方向图切面")
        
        slice_data = results['slice_data']
        self._plot_slice_with_analysis(slice_data, results)
        
        # 详细结果
        st.markdown("### 📋 详细分析结果")
        
        tab1, tab2, tab3 = st.tabs(["波束宽度", "零陷分析", "副瓣分析"])
        
        with tab1:
            self._display_beamwidth_details(results['beamwidths'])
        
        with tab2:
            self._display_null_analysis(results.get('nulls', []))
        
        with tab3:
            self._display_sidelobe_analysis(results.get('sidelobes', []))
    
    def _plot_slice_with_analysis(self, slice_data: PatternSlice, results: Dict[str, Any]):
        """绘制带分析标记的方向图切面"""
        fig = go.Figure()
        
        # 主方向图
        fig.add_trace(go.Scatter(
            x=slice_data.angles,
            y=slice_data.values,
            mode='lines',
            name='方向图',
            line=dict(color='#636efa', width=2)
        ))
        
        # 标记峰值
        peak_angle = results['basic_metrics'].get('peak_angle')
        peak_gain = results['basic_metrics'].get('peak_gain')
        
        if peak_angle is not None and peak_gain is not None:
            fig.add_trace(go.Scatter(
                x=[peak_angle],
                y=[peak_gain],
                mode='markers+text',
                name='峰值',
                marker=dict(color='red', size=10, symbol='star'),
                text=[f'峰值: {peak_gain:.1f} dB'],
                textposition='top center'
            ))
        
        # 标记波束宽度
        for level_str, beamwidth in results['beamwidths'].items():
            if beamwidth > 0:
                level = -float(level_str.replace('dB', ''))
                threshold = peak_gain + level
                
                # 找到交叉点
                angles = slice_data.angles
                values = slice_data.values
                
                crossing_indices = np.where(np.diff(np.sign(values - threshold)))[0]
                
                if len(crossing_indices) >= 2:
                    angle1 = angles[crossing_indices[0]]
                    angle2 = angles[crossing_indices[-1]]
                    
                    # 添加标记
                    fig.add_shape(
                        type="line",
                        x0=angle1, y0=threshold, x1=angle2, y1=threshold,
                        line=dict(color="green", width=1, dash="dash"),
                    )
                    
                    # 添加文本
                    fig.add_annotation(
                        x=(angle1 + angle2) / 2,
                        y=threshold + 1,
                        text=f"{level_str}: {beamwidth:.1f}°",
                        showarrow=False,
                        font=dict(color="green", size=10)
                    )
        
        # 标记零陷
        for null in results.get('nulls', []):
            fig.add_trace(go.Scatter(
                x=[null['angle']],
                y=[null['level']],
                mode='markers+text',
                name='零陷',
                marker=dict(color='purple', size=8, symbol='triangle-down'),
                text=[f'零陷: {null["depth"]:.1f} dB'],
                textposition='bottom center',
                showlegend=False
            ))
        
        # 标记副瓣
        for i, sidelobe in enumerate(results.get('sidelobes', [])):
            if i < 3:  # 只显示前3个副瓣
                fig.add_trace(go.Scatter(
                    x=[sidelobe['angle']],
                    y=[sidelobe['level']],
                    mode='markers+text',
                    name='副瓣' if i == 0 else '',
                    marker=dict(color='orange', size=6, symbol='circle'),
                    text=[f'副瓣{i+1}: {sidelobe["relative_level"]:.1f} dB'],
                    textposition='top center',
                    showlegend=False
                ))
        
        # 更新布局
        fig.update_layout(
            title=f"{slice_data.plane}面方向图 (固定角度: {slice_data.fixed_angle}°)",
            xaxis_title="角度 (°)",
            yaxis_title="增益 (dB)",
            height=500,
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _display_beamwidth_details(self, beamwidths: Dict[str, float]):
        """显示波束宽度详情"""
        if not beamwidths:
            st.info("没有波束宽度数据")
            return
        
        # 创建表格
        data = []
        for level, width in beamwidths.items():
            data.append({
                '波束宽度': level,
                '宽度 (°)': f"{width:.2f}",
                '评价': self._evaluate_beamwidth(level, width)
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # 可视化
        levels = [float(bw.replace('dB', '')) for bw in beamwidths.keys()]
        widths = list(beamwidths.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(beamwidths.keys()),
                y=widths,
                marker_color=['#636efa', '#00cc96', '#ab63fa', '#ffa15a'][:len(widths)],
                text=[f"{w:.1f}°" for w in widths],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="波束宽度分析",
            xaxis_title="波束宽度电平",
            yaxis_title="宽度 (°)",
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _evaluate_beamwidth(self, level: str, width: float) -> str:
        """评估波束宽度"""
        level_value = float(level.replace('dB', ''))
        
        if level_value == 3:
            if width < 10:
                return "✅ 优秀 (窄波束)"
            elif width < 30:
                return "🟡 良好"
            elif width < 60:
                return "🟠 一般"
            else:
                return "🔴 较差 (宽波束)"
        elif level_value == 10:
            if width < 20:
                return "✅ 优秀"
            elif width < 50:
                return "🟡 良好"
            else:
                return "🟠 一般"
        else:
            return "📊 已测量"
    
    def _display_null_analysis(self, nulls: List[Dict[str, Any]]):
        """显示零陷分析"""
        if not nulls:
            st.info("没有检测到显著的零陷")
            return
        
        # 创建表格
        data = []
        for i, null in enumerate(nulls, 1):
            data.append({
                '序号': i,
                '角度 (°)': f"{null['angle']:.1f}",
                '深度 (dB)': f"{null['depth']:.1f}",
                '电平 (dB)': f"{null['level']:.1f}",
                '评价': self._evaluate_null(null['depth'])
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # 可视化
        angles = [null['angle'] for null in nulls]
        depths = [null['depth'] for null in nulls]
        
        fig = go.Figure(data=[
            go.Bar(
                x=[f"零陷{i+1}" for i in range(len(nulls))],
                y=depths,
                marker_color='purple',
                text=[f"{d:.1f} dB" for d in depths],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="零陷深度分析",
            xaxis_title="零陷",
            yaxis_title="深度 (dB)",
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _evaluate_null(self, depth: float) -> str:
        """评估零陷"""
        if depth > 30:
            return "✅ 优秀 (深零陷)"
        elif depth > 20:
            return "🟡 良好"
        elif depth > 10:
            return "🟠 一般"
        else:
            return "🔴 较差 (浅零陷)"
    
    def _display_sidelobe_analysis(self, sidelobes: List[Dict[str, Any]]):
        """显示副瓣分析"""
        if not sidelobes:
            st.info("没有检测到显著的副瓣")
            return
        
        # 创建表格
        data = []
        for i, sidelobe in enumerate(sidelobes, 1):
            data.append({
                '序号': i,
                '角度 (°)': f"{sidelobe['angle']:.1f}",
                '相对电平 (dB)': f"{sidelobe['relative_level']:.1f}",
                '绝对电平 (dB)': f"{sidelobe['level']:.1f}",
                '宽度 (°)': f"{sidelobe['width']:.1f}" if sidelobe['width'] > 0 else "N/A",
                '评价': self._evaluate_sidelobe(sidelobe['relative_level'])
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # 可视化
        angles = [sl['angle'] for sl in sidelobes]
        levels = [sl['relative_level'] for sl in sidelobes]
        
        fig = go.Figure(data=[
            go.Scatter(
                x=angles,
                y=levels,
                mode='markers+lines',
                marker=dict(color='orange', size=10),
                line=dict(color='orange', width=1, dash='dash')
            )
        ])
        
        fig.update_layout(
            title="副瓣电平分布",
            xaxis_title="角度 (°)",
            yaxis_title="相对主瓣电平 (dB)",
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _evaluate_sidelobe(self, level: float) -> str:
        """评估副瓣"""
        if level < -30:
            return "✅ 优秀 (低副瓣)"
        elif level < -20:
            return "🟡 良好"
        elif level < -15:
            return "🟠 一般"
        else:
            return "🔴 较差 (高副瓣)"
    
    def _render_polarization_analysis(self, sidebar_config: Dict[str, Any]):
        """渲染极化特性分析"""
        st.markdown("### 🔄 极化特性分析")
        
        # 获取当前数据
        pattern = st.session_state.pattern_data
        
        # 极化分析控制面板
        with st.expander("⚙️ 分析设置", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                analysis_type = st.multiselect(
                    "分析类型",
                    ["轴比分析", "极化纯度", "交叉极化鉴别", "极化椭圆"],
                    default=["轴比分析", "极化纯度"]
                )
                
                if "轴比分析" in analysis_type:
                    ar_threshold = st.slider("轴比阈值 (dB)", 0.1, 20.0, 3.0, 0.1)
                
                if "极化椭圆" in analysis_type:
                    ellipse_resolution = st.slider("椭圆分辨率", 10, 100, 30)
            
            with col2:
                region = st.radio(
                    "分析区域",
                    ["主瓣区域", "全方向图", "自定义区域"],
                    horizontal=True
                )
                
                if region == "自定义区域":
                    col_theta1, col_theta2, col_phi1, col_phi2 = st.columns(4)
                    with col_theta1:
                        theta_min = st.number_input("Theta最小 (°)", 0.0, 180.0, 0.0)
                    with col_theta2:
                        theta_max = st.number_input("Theta最大 (°)", 0.0, 180.0, 180.0)
                    with col_phi1:
                        phi_min = st.number_input("Phi最小 (°)", 0.0, 360.0, 0.0)
                    with col_phi2:
                        phi_max = st.number_input("Phi最大 (°)", 0.0, 360.0, 360.0)
        
        # 运行分析按钮
        if st.button("🔍 运行极化分析", type="primary", width='stretch'):
            with st.spinner("正在分析极化特性..."):
                self._run_polarization_analysis(pattern, analysis_type, region, 
                                               locals().get('ar_threshold', 3.0))
        
        # 显示分析结果
        if 'polarization_analysis_results' in st.session_state:
            self._display_polarization_analysis_results(st.session_state.polarization_analysis_results)
    
    def _run_polarization_analysis(self, pattern: RadiationPattern, 
                                  analysis_types: List[str], region: str,
                                  ar_threshold: float = 3.0):
        """运行极化分析"""
        try:
            results = {
                'analysis_types': analysis_types,
                'region': region,
                'axial_ratio': {},
                'polarization_purity': {},
                'cross_polar_discrimination': {},
                'polarization_ellipse': {}
            }
            
            # 1. 轴比分析
            if "轴比分析" in analysis_types:
                ar_results = self._analyze_axial_ratio(pattern, ar_threshold)
                results['axial_ratio'] = ar_results
            
            # 2. 极化纯度
            if "极化纯度" in analysis_types:
                purity_results = self._analyze_polarization_purity(pattern)
                results['polarization_purity'] = purity_results
            
            # 3. 交叉极化鉴别
            if "交叉极化鉴别" in analysis_types:
                xpd_results = self._analyze_cross_polar_discrimination(pattern)
                results['cross_polar_discrimination'] = xpd_results
            
            # 4. 极化椭圆
            if "极化椭圆" in analysis_types:
                ellipse_results = self._analyze_polarization_ellipse(pattern)
                results['polarization_ellipse'] = ellipse_results
            
            # 保存结果
            st.session_state.polarization_analysis_results = results
            
            st.success("极化分析完成！")
            
        except Exception as e:
            st.error(f"极化分析失败: {e}")
            st.exception(e)
    
    def _analyze_axial_ratio(self, pattern: RadiationPattern, threshold: float) -> Dict[str, Any]:
        """分析轴比"""
        if not hasattr(pattern, 'axial_ratio_data'):
            # 计算轴比
            e_theta_mag = np.abs(pattern.e_theta_data)
            e_phi_mag = np.abs(pattern.e_phi_data)
            
            with np.errstate(divide='ignore', invalid='ignore'):
                axial_ratio = 20 * np.log10(
                    np.maximum(e_theta_mag, e_phi_mag) / 
                    np.maximum(np.minimum(e_theta_mag, e_phi_mag), 1e-10)
                )
        else:
            axial_ratio = pattern.axial_ratio_data
        
        # 统计
        ar_flat = axial_ratio.flatten()
        valid_ar = ar_flat[np.isfinite(ar_flat)]
        
        if len(valid_ar) > 0:
            ar_min = np.min(valid_ar)
            ar_max = np.max(valid_ar)
            ar_mean = np.mean(valid_ar)
            ar_std = np.std(valid_ar)
            
            # 轴比小于阈值的比例
            good_ratio = np.sum(valid_ar <= threshold) / len(valid_ar)
            
            # 主瓣区域轴比
            max_gain, theta_max, phi_max = pattern.get_max_gain()
            theta_idx = np.argmin(np.abs(pattern.theta_grid - theta_max))
            phi_idx = np.argmin(np.abs(pattern.phi_grid - phi_max))
            
            # 主瓣区域（±10度）
            theta_range = 10
            phi_range = 10
            
            theta_start = max(0, theta_idx - theta_range)
            theta_end = min(len(pattern.theta_grid), theta_idx + theta_range)
            phi_start = max(0, phi_idx - phi_range)
            phi_end = min(len(pattern.phi_grid), phi_idx + phi_range)
            
            mainlobe_ar = axial_ratio[theta_start:theta_end, phi_start:phi_end]
            mainlobe_ar_flat = mainlobe_ar.flatten()
            valid_mainlobe = mainlobe_ar_flat[np.isfinite(mainlobe_ar_flat)]
            
            if len(valid_mainlobe) > 0:
                mainlobe_ar_mean = np.mean(valid_mainlobe)
                mainlobe_ar_std = np.std(valid_mainlobe)
            else:
                mainlobe_ar_mean = 0
                mainlobe_ar_std = 0
        else:
            ar_min = ar_max = ar_mean = ar_std = 0
            good_ratio = 0
            mainlobe_ar_mean = mainlobe_ar_std = 0
        
        return {
            'min': float(ar_min),
            'max': float(ar_max),
            'mean': float(ar_mean),
            'std': float(ar_std),
            'good_ratio': float(good_ratio),
            'threshold': float(threshold),
            'mainlobe_mean': float(mainlobe_ar_mean),
            'mainlobe_std': float(mainlobe_ar_std)
        }
    
    def _analyze_polarization_purity(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析极化纯度"""
        e_theta = pattern.e_theta_data
        e_phi = pattern.e_phi_data
        
        # 计算极化纯度
        co_pol_power = np.abs(e_theta)**2
        cross_pol_power = np.abs(e_phi)**2
        total_power = co_pol_power + cross_pol_power
        
        with np.errstate(divide='ignore', invalid='ignore'):
            polarization_purity = 1 - cross_pol_power / (total_power + 1e-10)
            polarization_purity = np.nan_to_num(polarization_purity, nan=1.0, posinf=1.0, neginf=1.0)
        
        # 统计
        purity_flat = polarization_purity.flatten()
        valid_purity = purity_flat[np.isfinite(purity_flat)]
        
        if len(valid_purity) > 0:
            purity_min = np.min(valid_purity)
            purity_max = np.max(valid_purity)
            purity_mean = np.mean(valid_purity)
            purity_std = np.std(valid_purity)
        else:
            purity_min = purity_max = purity_mean = purity_std = 0
        
        return {
            'min': float(purity_min),
            'max': float(purity_max),
            'mean': float(purity_mean),
            'std': float(purity_std)
        }
    
    def _analyze_cross_polar_discrimination(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析交叉极化鉴别度"""
        e_theta = pattern.e_theta_data
        e_phi = pattern.e_phi_data
        
        # 计算XPD
        with np.errstate(divide='ignore', invalid='ignore'):
            xpd = 20 * np.log10(np.abs(e_theta) / (np.abs(e_phi) + 1e-10))
            xpd = np.nan_to_num(xpd, nan=0.0, posinf=60.0, neginf=-60.0)
        
        # 统计
        xpd_flat = xpd.flatten()
        valid_xpd = xpd_flat[np.isfinite(xpd_flat)]
        
        if len(valid_xpd) > 0:
            xpd_min = np.min(valid_xpd)
            xpd_max = np.max(valid_xpd)
            xpd_mean = np.mean(valid_xpd)
            xpd_std = np.std(valid_xpd)
        else:
            xpd_min = xpd_max = xpd_mean = xpd_std = 0
        
        return {
            'min': float(xpd_min),
            'max': float(xpd_max),
            'mean': float(xpd_mean),
            'std': float(xpd_std)
        }
    
    def _analyze_polarization_ellipse(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """分析极化椭圆"""
        e_theta = pattern.e_theta_data
        e_phi = pattern.e_phi_data
        
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
        with np.errstate(divide='ignore', invalid='ignore'):
            axial_ratio = major_axis / (minor_axis + 1e-10)
        
        # 倾角
        with np.errstate(divide='ignore', invalid='ignore'):
            tan_2tau = 2 * a_theta * a_phi * np.cos(delta) / (a_theta**2 - a_phi**2)
            tau = 0.5 * np.arctan(tan_2tau)
        
        # 旋转方向
        sin_delta = np.sin(delta)
        rotation_direction = np.sign(sin_delta)
        
        # 统计
        major_flat = major_axis.flatten()
        minor_flat = minor_axis.flatten()
        tau_flat = tau.flatten()
        
        valid_major = major_flat[np.isfinite(major_flat)]
        valid_minor = minor_flat[np.isfinite(minor_flat)]
        valid_tau = tau_flat[np.isfinite(tau_flat)]
        
        if len(valid_major) > 0 and len(valid_minor) > 0:
            major_mean = np.mean(valid_major)
            minor_mean = np.mean(valid_minor)
            ellipticity = np.mean(valid_minor / valid_major)
            
            if len(valid_tau) > 0:
                tilt_mean = np.mean(np.rad2deg(valid_tau))
                tilt_std = np.std(np.rad2deg(valid_tau))
            else:
                tilt_mean = tilt_std = 0
        else:
            major_mean = minor_mean = ellipticity = tilt_mean = tilt_std = 0
        
        return {
            'major_axis_mean': float(major_mean),
            'minor_axis_mean': float(minor_mean),
            'ellipticity': float(ellipticity),
            'tilt_mean': float(tilt_mean),
            'tilt_std': float(tilt_std)
        }
    
    def _display_polarization_analysis_results(self, results: Dict[str, Any]):
        """显示极化分析结果"""
        st.markdown("---")
        
        # 结果概览
        st.markdown("### 📊 极化分析概览")
        
        cols = st.columns(4)
        col_idx = 0
        
        if 'axial_ratio' in results and results['axial_ratio']:
            ar = results['axial_ratio']
            with cols[col_idx % 4]:
                st.metric("平均轴比", f"{ar.get('mean', 0):.1f} dB")
                col_idx += 1
        
        if 'polarization_purity' in results and results['polarization_purity']:
            purity = results['polarization_purity']
            with cols[col_idx % 4]:
                purity_percent = purity.get('mean', 0) * 100
                st.metric("极化纯度", f"{purity_percent:.1f}%")
                col_idx += 1
        
        if 'cross_polar_discrimination' in results and results['cross_polar_discrimination']:
            xpd = results['cross_polar_discrimination']
            with cols[col_idx % 4]:
                st.metric("交叉极化鉴别", f"{xpd.get('mean', 0):.1f} dB")
                col_idx += 1
        
        if 'axial_ratio' in results and results['axial_ratio']:
            ar = results['axial_ratio']
            with cols[col_idx % 4]:
                good_ratio = ar.get('good_ratio', 0) * 100
                st.metric("良好轴比比例", f"{good_ratio:.1f}%")
                col_idx += 1
        
        # 详细分析
        for analysis_type in results['analysis_types']:
            st.markdown(f"### 📈 {analysis_type}")
            
            if analysis_type == "轴比分析" and 'axial_ratio' in results:
                self._display_axial_ratio_analysis(results['axial_ratio'])
            
            elif analysis_type == "极化纯度" and 'polarization_purity' in results:
                self._display_polarization_purity_analysis(results['polarization_purity'])
            
            elif analysis_type == "交叉极化鉴别" and 'cross_polar_discrimination' in results:
                self._display_xpd_analysis(results['cross_polar_discrimination'])
            
            elif analysis_type == "极化椭圆" and 'polarization_ellipse' in results:
                self._display_polarization_ellipse_analysis(results['polarization_ellipse'])
    
    def _display_axial_ratio_analysis(self, ar_results: Dict[str, Any]):
        """显示轴比分析"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 轴比统计")
            
            data = [
                ("最小值", f"{ar_results.get('min', 0):.2f} dB"),
                ("最大值", f"{ar_results.get('max', 0):.2f} dB"),
                ("平均值", f"{ar_results.get('mean', 0):.2f} dB"),
                ("标准差", f"{ar_results.get('std', 0):.2f} dB"),
                ("主瓣平均值", f"{ar_results.get('mainlobe_mean', 0):.2f} dB"),
                ("良好比例", f"{ar_results.get('good_ratio', 0)*100:.1f}%"),
                ("阈值", f"{ar_results.get('threshold', 0):.1f} dB")
            ]
            
            for key, value in data:
                st.markdown(f"**{key}:** {value}")
        
        with col2:
            st.markdown("##### 📈 轴比分布")
            
            # 创建模拟的轴比分布
            np.random.seed(42)
            ar_values = np.random.normal(ar_results.get('mean', 3), 
                                        ar_results.get('std', 1), 1000)
            ar_values = np.clip(ar_values, 0, 20)
            
            fig = go.Figure(data=[
                go.Histogram(
                    x=ar_values,
                    nbinsx=20,
                    marker_color='#636efa',
                    opacity=0.7
                )
            ])
            
            # 添加阈值线
            threshold = ar_results.get('threshold', 3)
            fig.add_shape(
                type="line",
                x0=threshold, y0=0, x1=threshold, y1=1,
                xref="x", yref="paper",
                line=dict(color="red", width=2, dash="dash"),
            )
            
            fig.add_annotation(
                x=threshold, y=0.9,
                xref="x", yref="paper",
                text=f"阈值: {threshold} dB",
                showarrow=True,
                arrowhead=2,
                ax=20, ay=-30
            )
            
            fig.update_layout(
                title="轴比分布",
                xaxis_title="轴比 (dB)",
                yaxis_title="计数",
                height=300
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # 轴比评估
        st.markdown("##### 📋 轴比评估")
        
        ar_mean = ar_results.get('mean', 0)
        if ar_mean < 1:
            evaluation = "✅ 优秀 (近乎完美圆极化)"
        elif ar_mean < 3:
            evaluation = "🟡 良好 (良好圆极化)"
        elif ar_mean < 6:
            evaluation = "🟠 一般 (中等圆极化)"
        else:
            evaluation = "🔴 较差 (接近线极化)"
        
        st.markdown(f"**评估结果:** {evaluation}")
        
        good_ratio = ar_results.get('good_ratio', 0) * 100
        if good_ratio > 90:
            coverage = "✅ 优秀 (高覆盖率)"
        elif good_ratio > 70:
            coverage = "🟡 良好"
        elif good_ratio > 50:
            coverage = "🟠 一般"
        else:
            coverage = "🔴 较差 (低覆盖率)"
        
        st.markdown(f"**良好覆盖率:** {coverage}")
    
    def _display_polarization_purity_analysis(self, purity_results: Dict[str, Any]):
        """显示极化纯度分析"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 极化纯度统计")
            
            data = [
                ("最小值", f"{purity_results.get('min', 0):.3f}"),
                ("最大值", f"{purity_results.get('max', 0):.3f}"),
                ("平均值", f"{purity_results.get('mean', 0):.3f}"),
                ("标准差", f"{purity_results.get('std', 0):.3f}")
            ]
            
            for key, value in data:
                st.markdown(f"**{key}:** {value}")
        
        with col2:
            st.markdown("##### 📈 极化纯度分布")
            
            # 创建模拟的极化纯度分布
            np.random.seed(42)
            purity_mean = purity_results.get('mean', 0.8)
            purity_std = purity_results.get('std', 0.1)
            purity_values = np.random.normal(purity_mean, purity_std, 1000)
            purity_values = np.clip(purity_values, 0, 1)
            
            fig = go.Figure(data=[
                go.Histogram(
                    x=purity_values,
                    nbinsx=20,
                    marker_color='#00cc96',
                    opacity=0.7
                )
            ])
            
            fig.update_layout(
                title="极化纯度分布",
                xaxis_title="极化纯度",
                yaxis_title="计数",
                height=300
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # 极化纯度评估
        st.markdown("##### 📋 极化纯度评估")
        
        purity_mean = purity_results.get('mean', 0)
        if purity_mean > 0.9:
            evaluation = "✅ 优秀 (高纯度极化)"
        elif purity_mean > 0.7:
            evaluation = "🟡 良好"
        elif purity_mean > 0.5:
            evaluation = "🟠 一般"
        else:
            evaluation = "🔴 较差 (低纯度极化)"
        
        st.markdown(f"**评估结果:** {evaluation}")
        st.markdown(f"**纯度百分比:** {purity_mean*100:.1f}%")
    
    def _display_xpd_analysis(self, xpd_results: Dict[str, Any]):
        """显示交叉极化鉴别度分析"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 XPD统计")
            
            data = [
                ("最小值", f"{xpd_results.get('min', 0):.1f} dB"),
                ("最大值", f"{xpd_results.get('max', 0):.1f} dB"),
                ("平均值", f"{xpd_results.get('mean', 0):.1f} dB"),
                ("标准差", f"{xpd_results.get('std', 0):.1f} dB")
            ]
            
            for key, value in data:
                st.markdown(f"**{key}:** {value}")
        
        with col2:
            st.markdown("##### 📈 XPD分布")
            
            # 创建模拟的XPD分布
            np.random.seed(42)
            xpd_mean = xpd_results.get('mean', 20)
            xpd_std = xpd_results.get('std', 5)
            xpd_values = np.random.normal(xpd_mean, xpd_std, 1000)
            xpd_values = np.clip(xpd_values, 0, 60)
            
            fig = go.Figure(data=[
                go.Histogram(
                    x=xpd_values,
                    nbinsx=20,
                    marker_color='#ab63fa',
                    opacity=0.7
                )
            ])
            
            fig.update_layout(
                title="交叉极化鉴别度分布",
                xaxis_title="XPD (dB)",
                yaxis_title="计数",
                height=300
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # XPD评估
        st.markdown("##### 📋 XPD评估")
        
        xpd_mean = xpd_results.get('mean', 0)
        if xpd_mean > 30:
            evaluation = "✅ 优秀 (高鉴别度)"
        elif xpd_mean > 20:
            evaluation = "🟡 良好"
        elif xpd_mean > 15:
            evaluation = "🟠 一般"
        else:
            evaluation = "🔴 较差 (低鉴别度)"
        
        st.markdown(f"**评估结果:** {evaluation}")
    
    def _display_polarization_ellipse_analysis(self, ellipse_results: Dict[str, Any]):
        """显示极化椭圆分析"""
        st.markdown("##### 📊 极化椭圆参数")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("长轴均值", f"{ellipse_results.get('major_axis_mean', 0):.3f}")
            st.metric("短轴均值", f"{ellipse_results.get('minor_axis_mean', 0):.3f}")
        
        with col2:
            ellipticity = ellipse_results.get('ellipticity', 0)
            st.metric("椭圆率", f"{ellipticity:.3f}")
            
            # 计算轴比
            if ellipticity > 0:
                axial_ratio = 1 / ellipticity
                st.metric("对应轴比", f"{axial_ratio:.1f}")
        
        with col3:
            tilt_mean = ellipse_results.get('tilt_mean', 0)
            tilt_std = ellipse_results.get('tilt_std', 0)
            st.metric("倾角均值", f"{tilt_mean:.1f}°")
            st.metric("倾角标准差", f"{tilt_std:.1f}°")
        
        # 椭圆可视化
        st.markdown("##### 📈 极化椭圆可视化")
        
        # 创建示例极化椭圆
        theta = np.linspace(0, 2*np.pi, 100)
        a = ellipse_results.get('major_axis_mean', 1.0)
        b = ellipse_results.get('minor_axis_mean', 0.5)
        tilt = np.deg2rad(ellipse_results.get('tilt_mean', 30))
        
        # 旋转前的椭圆
        x = a * np.cos(theta)
        y = b * np.sin(theta)
        
        # 旋转
        x_rot = x * np.cos(tilt) - y * np.sin(tilt)
        y_rot = x * np.sin(tilt) + y * np.cos(tilt)
        
        fig = go.Figure()
        
        # 椭圆
        fig.add_trace(go.Scatter(
            x=x_rot, y=y_rot,
            mode='lines',
            line=dict(color='#636efa', width=2),
            name='极化椭圆',
            fill='toself',
            fillcolor='rgba(99, 110, 250, 0.3)'
        ))
        
        # 主轴
        fig.add_trace(go.Scatter(
            x=[-a*np.cos(tilt), a*np.cos(tilt)],
            y=[-a*np.sin(tilt), a*np.sin(tilt)],
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name='长轴'
        ))
        
        # 短轴
        fig.add_trace(go.Scatter(
            x=[-b*np.sin(tilt), b*np.sin(tilt)],
            y=[b*np.cos(tilt), -b*np.cos(tilt)],
            mode='lines',
            line=dict(color='green', width=2, dash='dash'),
            name='短轴'
        ))
        
        fig.update_layout(
            title="极化椭圆",
            xaxis_title="Eθ分量",
            yaxis_title="Eφ分量",
            height=400,
            showlegend=True,
            yaxis=dict(scaleanchor="x", scaleratio=1)
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _render_efficiency_analysis(self, sidebar_config: Dict[str, Any]):
        """渲染效率分析"""
        st.markdown("### ⚡ 效率分析")
        
        # 获取当前数据
        pattern = st.session_state.pattern_data
        antenna = st.session_state.get('current_antenna')
        
        # 效率分析控制面板
        with st.expander("⚙️ 分析设置", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                efficiency_types = st.multiselect(
                    "效率类型",
                    ["辐射效率", "孔径效率", "波束效率", "总效率", "匹配效率"],
                    default=["辐射效率", "孔径效率", "总效率"]
                )
            
            with col2:
                include_losses = st.checkbox("包含损耗", value=True)
                calculate_gain = st.checkbox("计算增益相关效率", value=True)
        
        # 运行分析按钮
        if st.button("🔍 运行效率分析", type="primary", width='stretch'):
            with st.spinner("正在分析效率..."):
                self._run_efficiency_analysis(pattern, antenna, efficiency_types, 
                                            include_losses, calculate_gain)
        
        # 显示分析结果
        if 'efficiency_analysis_results' in st.session_state:
            self._display_efficiency_analysis_results(st.session_state.efficiency_analysis_results)
    
    def _run_efficiency_analysis(self, pattern: RadiationPattern, antenna: Optional[AntennaParameters],
                                efficiency_types: List[str], include_losses: bool, 
                                calculate_gain: bool):
        """运行效率分析"""
        try:
            results = {
                'efficiency_types': efficiency_types,
                'include_losses': include_losses,
                'calculate_gain': calculate_gain,
                'efficiencies': {}
            }
            
            # 计算各种效率
            for eff_type in efficiency_types:
                if eff_type == "辐射效率":
                    efficiency = self._calculate_radiation_efficiency(pattern, antenna)
                elif eff_type == "孔径效率":
                    efficiency = self._calculate_aperture_efficiency(pattern, antenna)
                elif eff_type == "波束效率":
                    efficiency = self._calculate_beam_efficiency(pattern)
                elif eff_type == "总效率":
                    # 总效率 = 辐射效率 * 孔径效率
                    rad_eff = self._calculate_radiation_efficiency(pattern, antenna)
                    aper_eff = self._calculate_aperture_efficiency(pattern, antenna)
                    efficiency = rad_eff * aper_eff
                elif eff_type == "匹配效率":
                    efficiency = self._calculate_matching_efficiency(antenna)
                else:
                    efficiency = 0.0
                
                results['efficiencies'][eff_type] = float(efficiency)
            
            # 计算增益相关参数
            if calculate_gain:
                gain_results = self._calculate_gain_related_metrics(pattern, antenna)
                results['gain_metrics'] = gain_results
            
            # 保存结果
            st.session_state.efficiency_analysis_results = results
            
            st.success("效率分析完成！")
            
        except Exception as e:
            st.error(f"效率分析失败: {e}")
            st.exception(e)
    
    def _calculate_radiation_efficiency(self, pattern: RadiationPattern, 
                                       antenna: Optional[AntennaParameters]) -> float:
        """计算辐射效率"""
        # 简化的辐射效率计算
        if antenna and hasattr(antenna, 'efficiency'):
            return antenna.efficiency
        
        # 基于方向图计算
        gain_data = pattern.gain_data
        
        # 假设理想效率
        max_gain = np.max(gain_data)
        if max_gain > 20:
            efficiency = 0.85
        elif max_gain > 10:
            efficiency = 0.75
        else:
            efficiency = 0.65
        
        return efficiency
    
    def _calculate_aperture_efficiency(self, pattern: RadiationPattern, 
                                      antenna: Optional[AntennaParameters]) -> float:
        """计算孔径效率"""
        # 简化的孔径效率计算
        if antenna and hasattr(antenna, 'geometry') and antenna.geometry.ground_plane:
            # 有孔径信息
            return 0.7
        
        # 基于增益估计
        max_gain = np.max(pattern.gain_data)
        
        if max_gain > 25:
            efficiency = 0.8
        elif max_gain > 15:
            efficiency = 0.7
        elif max_gain > 5:
            efficiency = 0.6
        else:
            efficiency = 0.5
        
        return efficiency
    
    def _calculate_beam_efficiency(self, pattern: RadiationPattern) -> float:
        """计算波束效率"""
        # 简化的波束效率计算
        gain_data = pattern.gain_data
        
        # 找到主瓣区域
        max_gain_idx = np.unravel_index(np.argmax(gain_data), gain_data.shape)
        theta_idx, phi_idx = max_gain_idx
        
        # 主瓣区域（假设）
        theta_range = slice(max(0, theta_idx-5), min(gain_data.shape[0], theta_idx+5))
        phi_range = slice(max(0, phi_idx-5), min(gain_data.shape[1], phi_idx+5))
        
        mainlobe_power = np.sum(10**(gain_data[theta_range, phi_range]/10))
        total_power = np.sum(10**(gain_data/10))
        
        if total_power > 0:
            beam_efficiency = mainlobe_power / total_power
        else:
            beam_efficiency = 0.0
        
        return float(beam_efficiency)
    
    def _calculate_matching_efficiency(self, antenna: Optional[AntennaParameters]) -> float:
        """计算匹配效率"""
        if antenna and hasattr(antenna, 'vswr'):
            vswr = antenna.vswr
            # 匹配效率 = 1 - |Γ|²
            reflection_coeff = (vswr - 1) / (vswr + 1)
            matching_efficiency = 1 - reflection_coeff**2
            return float(matching_efficiency)
        
        return 0.8  # 默认值
    
    def _calculate_gain_related_metrics(self, pattern: RadiationPattern, 
                                       antenna: Optional[AntennaParameters]) -> Dict[str, Any]:
        """计算增益相关参数"""
        max_gain = np.max(pattern.gain_data)
        
        # 计算方向性
        gain_linear = 10**(pattern.gain_data/10)
        total_power = np.sum(gain_linear)
        
        if total_power > 0:
            directivity = 4 * np.pi * np.max(gain_linear) / total_power
            directivity_db = 10 * np.log10(directivity)
        else:
            directivity_db = 0
        
        return {
            'max_gain': float(max_gain),
            'directivity': float(directivity_db),
            'gain_directivity_diff': float(max_gain - directivity_db)
        }
    
    def _display_efficiency_analysis_results(self, results: Dict[str, Any]):
        """显示效率分析结果"""
        st.markdown("---")
        
        # 效率概览
        st.markdown("### 📊 效率分析概览")
        
        # 创建效率卡片
        cols = st.columns(len(results['efficiency_types']))
        
        for idx, (eff_type, efficiency) in enumerate(results['efficiencies'].items()):
            with cols[idx % len(cols)]:
                efficiency_percent = efficiency * 100
                
                # 根据效率值设置颜色
                if efficiency > 0.8:
                    delta = "优秀"
                    delta_color = "normal"
                elif efficiency > 0.6:
                    delta = "良好"
                    delta_color = "normal"
                elif efficiency > 0.4:
                    delta = "一般"
                    delta_color = "inverse"
                else:
                    delta = "较差"
                    delta_color = "inverse"
                
                st.metric(
                    eff_type,
                    f"{efficiency_percent:.1f}%",
                    delta=delta,
                    delta_color=delta_color
                )
        
        # 效率图表
        st.markdown("### 📈 效率分布")
        
        eff_types = list(results['efficiencies'].keys())
        eff_values = [results['efficiencies'][t] * 100 for t in eff_types]
        
        fig = go.Figure(data=[
            go.Bar(
                x=eff_types,
                y=eff_values,
                marker_color=['#636efa', '#00cc96', '#ab63fa', '#ffa15a', '#19d3f3'][:len(eff_types)],
                text=[f"{v:.1f}%" for v in eff_values],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="效率分析",
            xaxis_title="效率类型",
            yaxis_title="效率 (%)",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 增益相关参数
        if 'gain_metrics' in results:
            st.markdown("### 📡 增益相关参数")
            
            gain_metrics = results['gain_metrics']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("最大增益", f"{gain_metrics.get('max_gain', 0):.1f} dB")
            
            with col2:
                st.metric("方向性", f"{gain_metrics.get('directivity', 0):.1f} dBi")
            
            with col3:
                diff = gain_metrics.get('gain_directivity_diff', 0)
                st.metric("增益-方向性差", f"{diff:.1f} dB")
            
            # 增益-方向性关系
            st.markdown("##### 📊 增益与方向性关系")
            
            if gain_metrics['max_gain'] > 0 and gain_metrics['directivity'] > 0:
                diff_percent = (gain_metrics['gain_directivity_diff'] / 
                              gain_metrics['max_gain'] * 100)
                
                if diff_percent < 10:
                    evaluation = "✅ 优秀 (高效率)"
                elif diff_percent < 20:
                    evaluation = "🟡 良好"
                elif diff_percent < 30:
                    evaluation = "🟠 一般"
                else:
                    evaluation = "🔴 较差 (低效率)"
                
                st.markdown(f"**评估:** {evaluation}")
                st.markdown(f"**增益利用率:** {100 - diff_percent:.1f}%")
    
    def _render_frequency_analysis(self, sidebar_config: Dict[str, Any]):
        """渲染频域分析"""
        st.markdown("### 📡 频域分析")
        
        # 获取当前数据
        antenna = st.session_state.get('current_antenna')
        
        if antenna is None:
            st.warning("没有天线数据，无法进行频域分析")
            return
        
        # 频域分析控制面板
        with st.expander("⚙️ 分析设置", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                freq_start = st.number_input(
                    "起始频率 (GHz)",
                    value=max(0.1, antenna.center_frequency * 0.5),
                    min_value=0.1,
                    max_value=100.0
                )
                
                freq_end = st.number_input(
                    "结束频率 (GHz)",
                    value=antenna.center_frequency * 1.5,
                    min_value=0.1,
                    max_value=100.0
                )
                
                if freq_end <= freq_start:
                    st.error("结束频率必须大于起始频率")
                    return
            
            with col2:
                freq_points = st.slider("频率点数", 2, 50, 10)
                sweep_type = st.selectbox("扫频类型", ["线性", "对数", "自定义"])
                
                if sweep_type == "自定义":
                    custom_freqs = st.text_area(
                        "自定义频率 (GHz)",
                        value="1.0, 1.5, 2.0, 2.5, 3.0",
                        help="用逗号分隔的频率值"
                    )
        
        # 分析参数
        st.markdown("##### 📊 分析参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            analyze_bandwidth = st.checkbox("分析带宽", value=True)
            if analyze_bandwidth:
                bw_level = st.selectbox("带宽电平", ["-3dB", "-6dB", "-10dB"])
        
        with col2:
            analyze_vswr = st.checkbox("分析VSWR", value=False)
            analyze_gain = st.checkbox("分析增益变化", value=True)
        
        # 运行分析按钮
        if st.button("🔍 运行频域分析", type="primary", width='stretch'):
            with st.spinner("正在分析频率响应..."):
                self._run_frequency_analysis(antenna, freq_start, freq_end, freq_points, 
                                           sweep_type, analyze_bandwidth, bw_level if analyze_bandwidth else "-3dB",
                                           analyze_vswr, analyze_gain)
    
    def _run_frequency_analysis(self, antenna: AntennaParameters, freq_start: float, 
                               freq_end: float, freq_points: int, sweep_type: str,
                               analyze_bandwidth: bool, bw_level: str,
                               analyze_vswr: bool, analyze_gain: bool):
        """运行频域分析"""
        try:
            # 生成频率数组
            if sweep_type == "线性":
                frequencies = np.linspace(freq_start, freq_end, freq_points)
            elif sweep_type == "对数":
                frequencies = np.logspace(np.log10(freq_start), np.log10(freq_end), freq_points)
            else:
                # 自定义频率
                freq_input = st.session_state.get('custom_freqs', "1.0, 2.0, 3.0")
                frequencies = np.array([float(f.strip()) for f in freq_input.split(',')])
            
            results = {
                'frequencies': frequencies.tolist(),
                'sweep_type': sweep_type,
                'gain_data': [],
                'bandwidth': {},
                'vswr_data': []
            }
            
            # 模拟频域分析
            for freq in frequencies:
                # 模拟增益变化
                center_freq = antenna.center_frequency
                freq_ratio = freq / center_freq
                
                if freq_ratio < 0.8 or freq_ratio > 1.2:
                    # 频带外，增益下降
                    gain = antenna.gain - 20 * np.log10(max(freq_ratio, 1/freq_ratio))
                else:
                    # 频带内，小波动
                    gain = antenna.gain + np.random.normal(0, 0.5)
                
                results['gain_data'].append(float(gain))
                
                # 模拟VSWR
                if analyze_vswr:
                    if abs(freq - center_freq) < 0.1:
                        vswr = antenna.vswr
                    else:
                        vswr = antenna.vswr + abs(freq - center_freq) * 0.5
                    results['vswr_data'].append(float(vswr))
            
            # 计算带宽
            if analyze_bandwidth and results['gain_data']:
                max_gain = max(results['gain_data'])
                threshold = max_gain - float(bw_level.replace('dB', ''))
                
                # 找到交叉点
                gain_array = np.array(results['gain_data'])
                freq_array = np.array(frequencies)
                
                above_threshold = gain_array >= threshold
                
                if np.any(above_threshold):
                    lower_idx = np.argmax(above_threshold)
                    upper_idx = len(above_threshold) - np.argmax(above_threshold[::-1]) - 1
                    
                    if lower_idx < upper_idx:
                        lower_freq = freq_array[lower_idx]
                        upper_freq = freq_array[upper_idx]
                        bandwidth = upper_freq - lower_freq
                        bandwidth_percent = bandwidth / center_freq * 100
                        
                        results['bandwidth'] = {
                            'level': bw_level,
                            'value': float(bandwidth),
                            'percent': float(bandwidth_percent),
                            'lower': float(lower_freq),
                            'upper': float(upper_freq)
                        }
            
            # 保存结果
            st.session_state.frequency_analysis_results = results
            
            st.success("频域分析完成！")
            
        except Exception as e:
            st.error(f"频域分析失败: {e}")
            st.exception(e)
            
    def _render_comparative_analysis(self, sidebar_config: Dict[str, Any]):
            """渲染比较分析"""
            st.markdown("### ⚖️ 比较分析")
            
            # 比较分析控制面板
            with st.expander("⚙️ 分析设置", expanded=True):
                comparison_type = st.radio(
                    "比较类型",
                    ["不同天线", "不同参数", "不同频率", "与理论值"],
                    horizontal=True
                )
                
                if comparison_type == "不同天线":
                    self._render_multiple_antenna_comparison()
                elif comparison_type == "不同参数":
                    self._render_parameter_comparison()
                elif comparison_type == "不同频率":
                    self._render_frequency_comparison()
                else:  # 与理论值
                    self._render_theory_comparison()
            
            # 比较指标选择
            st.markdown("##### 📊 比较指标")
            
            metrics = st.multiselect(
                "选择比较指标",
                ["增益", "波束宽度", "副瓣电平", "效率", "轴比", "VSWR"],
                default=["增益", "波束宽度", "效率"]
            )
            
            # 运行比较分析按钮
            if st.button("🔍 运行比较分析", type="primary", width='stretch'):
                with st.spinner("正在进行比较分析..."):
                    self._run_comparative_analysis(comparison_type, metrics)
            
            # 显示比较结果
            if 'comparative_analysis_results' in st.session_state:
                self._display_comparative_analysis_results(
                    st.session_state.comparative_analysis_results
                )
    
    def _render_multiple_antenna_comparison(self):
        """渲染多天线比较设置"""
        st.markdown("##### 📡 天线选择")
        
        # 加载天线数据库
        from views.sidebar_view import load_antenna_database
        database = load_antenna_database()
        antennas = database.get('antennas', [])
        
        if not antennas:
            st.info("数据库中暂无其他天线，请先创建或导入天线")
            return
        
        # 当前天线
        current_antenna = st.session_state.get('current_antenna')
        if current_antenna:
            st.markdown(f"**当前天线:** {current_antenna.name}")
        
        # 选择要比较的天线
        antenna_names = [antenna.get('name', f'天线{i+1}') for i, antenna in enumerate(antennas)]
        
        # 排除当前天线
        if current_antenna and current_antenna.name in antenna_names:
            antenna_names.remove(current_antenna.name)
        
        selected_antennas = st.multiselect(
            "选择比较天线",
            antenna_names,
            default=antenna_names[:min(2, len(antenna_names))]
        )
        
        # 保存选择
        st.session_state.comparison_antennas = selected_antennas
    
    def _render_parameter_comparison(self):
        """渲染参数比较设置"""
        st.markdown("##### ⚙️ 参数变化")
        
        # 当前天线参数
        antenna = st.session_state.get('current_antenna')
        if not antenna:
            st.info("请先设置当前天线")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            param_name = st.selectbox(
                "变化参数",
                ["增益", "波束宽度", "频率", "副瓣电平", "效率"],
                index=0
            )
            
            if param_name == "增益":
                param_values = st.text_input("增益值 (dBi)", "8, 10, 12, 14")
                param_key = "gain"
            elif param_name == "波束宽度":
                param_values = st.text_input("波束宽度值 (°)", "30, 40, 50, 60")
                param_key = "beamwidth_e"
            elif param_name == "频率":
                param_values = st.text_input("频率值 (GHz)", "2.0, 2.5, 3.0, 3.5")
                param_key = "center_frequency"
            elif param_name == "副瓣电平":
                param_values = st.text_input("副瓣电平值 (dB)", "-15, -20, -25, -30")
                param_key = "sidelobe_level"
            else:  # 效率
                param_values = st.text_input("效率值", "0.6, 0.7, 0.8, 0.9")
                param_key = "efficiency"
        
        with col2:
            num_variations = st.slider("变化点数", 2, 10, 4)
            variation_type = st.radio(
                "变化方式",
                ["线性", "对数", "自定义"],
                horizontal=True
            )
        
        # 保存参数设置
        try:
            values_list = [float(v.strip()) for v in param_values.split(',')]
            st.session_state.param_variations = {
                'param_name': param_name,
                'param_key': param_key,
                'values': values_list[:num_variations]
            }
        except:
            st.error("请输入有效的数值，用逗号分隔")
    
    def _render_frequency_comparison(self):
        """渲染频率比较设置"""
        st.markdown("##### 📡 频率设置")
        
        antenna = st.session_state.get('current_antenna')
        if antenna:
            center_freq = antenna.center_frequency
        else:
            center_freq = 2.45
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_freq = st.number_input(
                "起始频率 (GHz)",
                value=center_freq * 0.8,
                min_value=0.1,
                max_value=100.0
            )
        
        with col2:
            end_freq = st.number_input(
                "结束频率 (GHz)",
                value=center_freq * 1.2,
                min_value=0.1,
                max_value=100.0
            )
        
        with col3:
            num_freqs = st.slider("频率点数", 2, 20, 5)
        
        # 保存频率设置
        st.session_state.frequency_comparison = {
            'start': start_freq,
            'end': end_freq,
            'num_points': num_freqs
        }
    
    def _render_theory_comparison(self):
        """渲染理论值比较设置"""
        st.markdown("##### 📐 理论模型")
        
        theory_model = st.selectbox(
            "理论模型",
            ["各向同性辐射器", "半波偶极子", "理想抛物面", "微带贴片", "喇叭天线"],
            index=1
        )
        
        # 理论模型参数
        if theory_model == "各向同性辐射器":
            st.info("各向同性辐射器：增益 = 0 dBi，全向辐射")
        elif theory_model == "半波偶极子":
            col1, col2 = st.columns(2)
            with col1:
                freq = st.number_input("频率 (GHz)", 0.1, 100.0, 1.0)
            with col2:
                length = st.number_input("长度 (m)", 0.01, 10.0, 0.15)
        elif theory_model == "理想抛物面":
            col1, col2 = st.columns(2)
            with col1:
                diameter = st.number_input("直径 (m)", 0.1, 10.0, 1.0)
            with col2:
                freq = st.number_input("频率 (GHz)", 0.1, 100.0, 10.0)
        elif theory_model == "微带贴片":
            col1, col2 = st.columns(2)
            with col1:
                substrate_er = st.number_input("基板介电常数", 1.0, 10.0, 4.4)
            with col2:
                patch_width = st.number_input("贴片宽度 (mm)", 1.0, 100.0, 30.0)
        else:  # 喇叭天线
            col1, col2 = st.columns(2)
            with col1:
                aperture_width = st.number_input("口径宽度 (cm)", 1.0, 100.0, 10.0)
            with col2:
                freq = st.number_input("频率 (GHz)", 1.0, 100.0, 10.0)
        
        # 保存理论模型设置
        st.session_state.theory_model = {
            'model': theory_model,
            'params': locals()
        }
    
    def _run_comparative_analysis(self, comparison_type: str, metrics: List[str]):
        """运行比较分析"""
        try:
            results = {
                'comparison_type': comparison_type,
                'metrics': metrics,
                'data': {},
                'summary': {}
            }
            
            if comparison_type == "不同天线":
                results = self._compare_multiple_antennas(metrics)
            elif comparison_type == "不同参数":
                results = self._compare_parameter_variations(metrics)
            elif comparison_type == "不同频率":
                results = self._compare_frequency_variations(metrics)
            else:  # 与理论值
                results = self._compare_with_theory(metrics)
            
            # 保存结果
            st.session_state.comparative_analysis_results = results
            
            st.success("比较分析完成！")
            
        except Exception as e:
            st.error(f"比较分析失败: {e}")
            st.exception(e)
    
    def _compare_multiple_antennas(self, metrics: List[str]) -> Dict[str, Any]:
        """比较多天线性能"""
        from views.sidebar_view import get_antenna_from_database
        
        # 获取当前天线
        current_antenna = st.session_state.get('current_antenna')
        if not current_antenna:
            raise ValueError("没有当前天线数据")
        
        # 获取要比较的天线
        antenna_names = st.session_state.get('comparison_antennas', [])
        all_antennas = [current_antenna]
        
        for name in antenna_names:
            antenna_data = get_antenna_from_database(name)
            if antenna_data:
                try:
                    from models.antenna_models import AntennaParameters
                    antenna = AntennaParameters.from_dict(antenna_data)
                    all_antennas.append(antenna)
                except:
                    continue
        
        if len(all_antennas) < 2:
            raise ValueError("需要至少2个天线进行比较")
        
        # 分析每个天线
        analysis_results = {}
        for antenna in all_antennas:
            # 生成方向图
            pattern = self.pattern_service.generate_pattern(
                antenna,
                generator_type='analytical',
                theta_resolution=5,
                phi_resolution=5
            )
            
            # 分析方向图
            analysis_result = self.analysis_service.comprehensive_analysis(pattern, antenna)
            
            # 提取关键指标
            key_metrics = self._extract_key_metrics(analysis_result, metrics)
            analysis_results[antenna.name] = {
                'antenna': antenna,
                'pattern': pattern,
                'analysis': analysis_result,
                'metrics': key_metrics
            }
        
        # 生成比较结果
        comparison_results = self._generate_comparison_results(analysis_results, metrics)
        
        return {
            'type': 'multiple_antennas',
            'antennas': all_antennas,
            'analysis_results': analysis_results,
            'comparison': comparison_results
        }
    
    def _compare_parameter_variations(self, metrics: List[str]) -> Dict[str, Any]:
        """比较参数变化"""
        param_variations = st.session_state.get('param_variations')
        if not param_variations:
            raise ValueError("没有参数变化设置")
        
        # 获取当前天线
        base_antenna = st.session_state.get('current_antenna')
        if not base_antenna:
            raise ValueError("没有当前天线数据")
        
        # 创建参数变化的天线
        antennas = []
        param_values = param_variations['values']
        param_key = param_variations['param_key']
        
        for i, value in enumerate(param_values):
            # 复制天线并修改参数
            import copy
            antenna = copy.deepcopy(base_antenna)
            antenna.name = f"{base_antenna.name} ({param_variations['param_name']}={value})"
            
            # 设置参数值
            if hasattr(antenna, param_key):
                setattr(antenna, param_key, value)
            
            antennas.append(antenna)
        
        # 分析每个天线
        analysis_results = {}
        for antenna in antennas:
            pattern = self.pattern_service.generate_pattern(
                antenna,
                generator_type='analytical',
                theta_resolution=5,
                phi_resolution=5
            )
            
            analysis_result = self.analysis_service.comprehensive_analysis(pattern, antenna)
            key_metrics = self._extract_key_metrics(analysis_result, metrics)
            
            analysis_results[antenna.name] = {
                'antenna': antenna,
                'pattern': pattern,
                'analysis': analysis_result,
                'metrics': key_metrics
            }
        
        # 生成比较结果
        comparison_results = self._generate_comparison_results(analysis_results, metrics)
        
        return {
            'type': 'parameter_variations',
            'parameter': param_variations,
            'antennas': antennas,
            'analysis_results': analysis_results,
            'comparison': comparison_results
        }
    
    def _compare_frequency_variations(self, metrics: List[str]) -> Dict[str, Any]:
        """比较频率变化"""
        freq_settings = st.session_state.get('frequency_comparison')
        if not freq_settings:
            raise ValueError("没有频率设置")
        
        # 获取当前天线
        base_antenna = st.session_state.get('current_antenna')
        if not base_antenna:
            raise ValueError("没有当前天线数据")
        
        # 生成频率数组
        frequencies = np.linspace(freq_settings['start'], freq_settings['end'], 
                                 freq_settings['num_points'])
        
        # 分析每个频率
        analysis_results = {}
        for i, freq in enumerate(frequencies):
            # 复制天线并修改频率
            import copy
            antenna = copy.deepcopy(base_antenna)
            antenna.name = f"{base_antenna.name} ({freq:.2f} GHz)"
            antenna.center_frequency = freq
            
            pattern = self.pattern_service.generate_pattern(
                antenna,
                generator_type='analytical',
                theta_resolution=5,
                phi_resolution=5
            )
            
            analysis_result = self.analysis_service.comprehensive_analysis(pattern, antenna)
            key_metrics = self._extract_key_metrics(analysis_result, metrics)
            
            analysis_results[antenna.name] = {
                'antenna': antenna,
                'pattern': pattern,
                'analysis': analysis_result,
                'metrics': key_metrics
            }
        
        # 生成比较结果
        comparison_results = self._generate_comparison_results(analysis_results, metrics)
        
        return {
            'type': 'frequency_variations',
            'frequencies': frequencies.tolist(),
            'analysis_results': analysis_results,
            'comparison': comparison_results
        }
    
    def _compare_with_theory(self, metrics: List[str]) -> Dict[str, Any]:
        """与理论值比较"""
        theory_settings = st.session_state.get('theory_model')
        if not theory_settings:
            raise ValueError("没有理论模型设置")
        
        # 获取当前天线
        current_antenna = st.session_state.get('current_antenna')
        if not current_antenna:
            raise ValueError("没有当前天线数据")
        
        # 分析当前天线
        current_pattern = self.pattern_service.generate_pattern(
            current_antenna,
            generator_type='analytical',
            theta_resolution=5,
            phi_resolution=5
        )
        
        current_analysis = self.analysis_service.comprehensive_analysis(current_pattern, current_antenna)
        current_metrics = self._extract_key_metrics(current_analysis, metrics)
        
        # 生成理论天线
        theory_antenna = self._create_theory_antenna(theory_settings)
        theory_pattern = self.pattern_service.generate_pattern(
            theory_antenna,
            generator_type='analytical',
            theta_resolution=5,
            phi_resolution=5
        )
        
        theory_analysis = self.analysis_service.comprehensive_analysis(theory_pattern, theory_antenna)
        theory_metrics = self._extract_key_metrics(theory_analysis, metrics)
        
        # 比较结果
        analysis_results = {
            '当前天线': {
                'antenna': current_antenna,
                'pattern': current_pattern,
                'analysis': current_analysis,
                'metrics': current_metrics
            },
            '理论模型': {
                'antenna': theory_antenna,
                'pattern': theory_pattern,
                'analysis': theory_analysis,
                'metrics': theory_metrics
            }
        }
        
        comparison_results = self._generate_comparison_results(analysis_results, metrics)
        
        return {
            'type': 'theory_comparison',
            'theory_model': theory_settings,
            'analysis_results': analysis_results,
            'comparison': comparison_results
        }
    
    def _create_theory_antenna(self, theory_settings: Dict[str, Any]) -> AntennaParameters:
        """创建理论天线"""
        from models.antenna_models import create_dipole_antenna, create_patch_antenna
        
        model = theory_settings['model']
        
        if model == "各向同性辐射器":
            from models.antenna_models import AntennaGeometry, FeedNetwork
            geometry = AntennaGeometry()
            feed_network = FeedNetwork(type='coaxial_fed', impedance=50.0)
            
            return AntennaParameters(
                name="各向同性辐射器",
                antenna_type='custom',
                frequency_range=(1.0, 2.0),
                center_frequency=1.5,
                gain=0.0,
                bandwidth=100.0,
                vswr=1.0,
                polarization='vertical',
                geometry=geometry,
                feed_network=feed_network,
                beamwidth_e=360.0,
                beamwidth_h=360.0,
                sidelobe_level=-np.inf,
                front_to_back_ratio=0.0,
                efficiency=1.0,
                description="理想各向同性辐射器"
            )
        
        elif model == "半波偶极子":
            return create_dipole_antenna("理论半波偶极子")
        
        elif model == "微带贴片":
            return create_patch_antenna("理论微带贴片")
        
        elif model == "理想抛物面":
            from models.antenna_models import AntennaGeometry, FeedNetwork
            geometry = AntennaGeometry()
            feed_network = FeedNetwork(type='waveguide', impedance=50.0)
            
            return AntennaParameters(
                name="理想抛物面天线",
                antenna_type='parabolic',
                frequency_range=(8.0, 12.0),
                center_frequency=10.0,
                gain=30.0,
                bandwidth=10.0,
                vswr=1.2,
                polarization='horizontal',
                geometry=geometry,
                feed_network=feed_network,
                beamwidth_e=5.0,
                beamwidth_h=5.0,
                sidelobe_level=-25.0,
                front_to_back_ratio=60.0,
                efficiency=0.7,
                description="理想抛物面天线"
            )
        
        else:  # 喇叭天线
            from models.antenna_models import AntennaGeometry, FeedNetwork
            geometry = AntennaGeometry()
            feed_network = FeedNetwork(type='waveguide', impedance=50.0)
            
            return AntennaParameters(
                name="标准喇叭天线",
                antenna_type='horn',
                frequency_range=(8.0, 12.0),
                center_frequency=10.0,
                gain=20.0,
                bandwidth=20.0,
                vswr=1.2,
                polarization='vertical',
                geometry=geometry,
                feed_network=feed_network,
                beamwidth_e=15.0,
                beamwidth_h=15.0,
                sidelobe_level=-20.0,
                front_to_back_ratio=40.0,
                efficiency=0.9,
                description="标准增益喇叭天线"
            )
    
    def _extract_key_metrics(self, analysis_result: Dict[str, Any], 
                            metrics: List[str]) -> Dict[str, Any]:
        """从分析结果中提取关键指标"""
        key_metrics = {}
        
        for metric in metrics:
            if metric == "增益":
                if 'beam' in analysis_result and 'beam_parameters' in analysis_result['beam']:
                    gain = analysis_result['beam']['beam_parameters'].get('peak_gain', 0)
                    key_metrics['增益'] = gain
            
            elif metric == "波束宽度":
                if 'beam' in analysis_result and 'beam_parameters' in analysis_result['beam']:
                    beamwidth = analysis_result['beam']['beam_parameters'].get('main_lobe_width_3db_e', 0)
                    key_metrics['波束宽度'] = beamwidth
            
            elif metric == "副瓣电平":
                if 'beam' in analysis_result and 'sidelobes' in analysis_result['beam']:
                    sll = analysis_result['beam']['sidelobes'].get('max_sidelobe_level_e', 0)
                    key_metrics['副瓣电平'] = sll
            
            elif metric == "效率":
                if 'efficiency' in analysis_result and 'efficiency_parameters' in analysis_result['efficiency']:
                    efficiency = analysis_result['efficiency']['efficiency_parameters'].get('total_efficiency', 0)
                    key_metrics['效率'] = efficiency
            
            elif metric == "轴比":
                if 'polarization' in analysis_result and 'axial_ratio' in analysis_result['polarization']:
                    ar = analysis_result['polarization']['axial_ratio'].get('mean', 0)
                    key_metrics['轴比'] = ar
            
            elif metric == "VSWR":
                # 从天线参数获取
                key_metrics['VSWR'] = 1.5  # 默认值
        
        return key_metrics
    
    def _generate_comparison_results(self, analysis_results: Dict[str, Dict[str, Any]],
                                    metrics: List[str]) -> Dict[str, Any]:
        """生成比较结果"""
        comparison = {
            'metrics_summary': {},
            'ranking': {},
            'differences': {}
        }
        
        # 对每个指标进行汇总
        for metric in metrics:
            metric_values = {}
            for name, data in analysis_results.items():
                if metric in data['metrics']:
                    metric_values[name] = data['metrics'][metric]
            
            if metric_values:
                comparison['metrics_summary'][metric] = {
                    'values': metric_values,
                    'max': max(metric_values.values()),
                    'min': min(metric_values.values()),
                    'mean': np.mean(list(metric_values.values())),
                    'std': np.std(list(metric_values.values()))
                }
        
        # 生成排名
        ranking = {}
        for name in analysis_results.keys():
            # 计算综合得分
            total_score = 0
            valid_metrics = 0
            
            for metric, metric_data in comparison['metrics_summary'].items():
                if name in metric_data['values']:
                    # 标准化得分
                    if metric in ['增益', '效率']:  # 越高越好
                        value = metric_data['values'][name]
                        max_val = metric_data['max']
                        min_val = metric_data['min']
                        if max_val > min_val:
                            score = (value - min_val) / (max_val - min_val)
                        else:
                            score = 0.5
                    else:  # 波束宽度、副瓣电平、轴比、VSWR - 越低越好
                        value = metric_data['values'][name]
                        max_val = metric_data['max']
                        min_val = metric_data['min']
                        if max_val > min_val:
                            score = 1 - (value - min_val) / (max_val - min_val)
                        else:
                            score = 0.5
                    
                    total_score += score
                    valid_metrics += 1
            
            if valid_metrics > 0:
                ranking[name] = total_score / valid_metrics
        
        # 排序
        sorted_ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
        comparison['ranking'] = {
            'scores': ranking,
            'sorted': sorted_ranking,
            'best': sorted_ranking[0][0] if sorted_ranking else None,
            'worst': sorted_ranking[-1][0] if sorted_ranking else None
        }
        
        return comparison
    
    def _display_comparative_analysis_results(self, results: Optional[Dict[str, Any]] = None):
            """显示比较分析结果"""
            if results is None:
                st.warning("⚠️ 没有可用的比较分析结果")
                st.info("请先运行比较分析以查看结果")
                
                # 提供一个运行分析的按钮
                if st.button("🚀 运行比较分析", type="primary"):
                    st.session_state.run_comparative_analysis = True
                    st.rerun()
                return
            
            st.markdown("---")
            
            # 结果概览
            st.markdown("### 📊 比较分析概览")
            
            comparison_type = results.get('comparison_type', '未指定')
            st.markdown(f"**比较类型:** {comparison_type}")
            
            # 检查是否有比较结果
            if 'comparison' not in results or not results['comparison']:
                st.info("暂无详细的比较分析数据")
                return
            
            # 显示排名
            if 'ranking' in results['comparison']:
                ranking = results['comparison']['ranking']
                
                if ranking:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### 🏆 性能排名")
                        
                        # 检查排序数据
                        if 'sorted' in ranking and ranking['sorted']:
                            for i, (name, score) in enumerate(ranking.get('sorted', []), 1):
                                medal = ""
                                if i == 1:
                                    medal = "🥇"
                                elif i == 2:
                                    medal = "🥈"
                                elif i == 3:
                                    medal = "🥉"
                                
                                st.markdown(f"{medal} **{i}. {name}** - 得分: {score:.3f}")
                        else:
                            st.info("暂无排名数据")
                    
                    with col2:
                        st.markdown("##### 📈 综合评估")
                        
                        best = ranking.get('best')
                        worst = ranking.get('worst')
                        
                        if best:
                            st.success(f"**最佳性能:** {best}")
                        
                        if worst:
                            st.warning(f"**最差性能:** {worst}")
                        
                        # 计算性能差异
                        if best and worst and best != worst and 'scores' in ranking:
                            scores = ranking['scores']
                            if best in scores and worst in scores:
                                best_score = scores[best]
                                worst_score = scores[worst]
                                
                                if best_score > worst_score and worst_score > 0:
                                    difference = (best_score - worst_score) / worst_score * 100
                                    st.metric("性能差异", f"{difference:.1f}%")
                                else:
                                    difference = best_score - worst_score
                                    st.metric("性能差异", f"{difference:.3f} 分")
            
            # 指标比较
            st.markdown("### 📈 指标比较")
            
            if 'metrics_summary' in results['comparison']:
                metrics_summary = results['comparison']['metrics_summary']
                
                if metrics_summary:
                    for metric, metric_data in metrics_summary.items():
                        st.markdown(f"##### 📊 {metric}")
                        
                        # 检查指标数据
                        if not isinstance(metric_data, dict) or 'values' not in metric_data:
                            st.info(f"指标 {metric} 数据格式错误")
                            continue
                        
                        values = metric_data.get('values', {})
                        
                        if not values:
                            st.info(f"指标 {metric} 无数据")
                            continue
                        
                        # 创建数据框
                        df_data = []
                        for name, value in values.items():
                            df_data.append({
                                '名称': name,
                                '值': value,
                                '单位': self._get_metric_unit(metric)
                            })
                        
                        if df_data:
                            df = pd.DataFrame(df_data)
                            st.dataframe(df, width='stretch', hide_index=True)
                            
                            # 创建条形图
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=list(values.keys()),
                                    y=list(values.values()),
                                    marker_color='#636efa',
                                    text=[f"{v:.2f}" for v in values.values()],
                                    textposition='auto'
                                )
                            ])
                            
                            fig.update_layout(
                                title=f"{metric}比较",
                                xaxis_title="天线/配置",
                                yaxis_title=f"{metric} ({self._get_metric_unit(metric)})",
                                height=300
                            )
                            
                            st.plotly_chart(fig, width='stretch')
                else:
                    st.info("暂无指标比较数据")
            else:
                st.info("暂无指标总结数据")
            
            # 详细比较
            st.markdown("### 🔍 详细比较")
            
            if 'analysis_results' in results and results['analysis_results']:
                analysis_results = results['analysis_results']
                
                # 选择要比较的项
                comparison_items = list(analysis_results.keys())
                
                if comparison_items:
                    selected_items = st.multiselect(
                        "选择要详细比较的项",
                        comparison_items,
                        default=comparison_items[:min(2, len(comparison_items))],
                        key="comparative_analysis_multiselect"
                    )
                    
                    if selected_items:
                        # 获取所有可能的指标
                        all_metrics = set()
                        for item in selected_items:
                            if item in analysis_results and 'metrics' in analysis_results[item]:
                                all_metrics.update(analysis_results[item]['metrics'].keys())
                        
                        metrics_list = list(all_metrics)
                        
                        if metrics_list:
                            # 创建比较表格
                            comparison_data = []
                            
                            for item in selected_items:
                                if item in analysis_results:
                                    item_data = analysis_results[item]
                                    row = {'项目': item}
                                    
                                    for metric in metrics_list:
                                        if 'metrics' in item_data and metric in item_data['metrics']:
                                            row[metric] = item_data['metrics'][metric]
                                        else:
                                            row[metric] = None
                                    
                                    comparison_data.append(row)
                            
                            if comparison_data:
                                df_comparison = pd.DataFrame(comparison_data)
                                st.dataframe(df_comparison, width='stretch')
                                
                                # 可视化比较
                                st.markdown("##### 📊 详细比较可视化")
                                
                                # 选择要可视化的指标
                                metrics_to_visualize = st.multiselect(
                                    "选择要可视化的指标",
                                    metrics_list,
                                    default=metrics_list[:min(3, len(metrics_list))],
                                    key="metrics_to_visualize_multiselect"
                                )
                                
                                if metrics_to_visualize:
                                    # 创建分组条形图
                                    fig = go.Figure()
                                    
                                    for item in selected_items:
                                        item_values = []
                                        for metric in metrics_to_visualize:
                                            if item in analysis_results and 'metrics' in analysis_results[item]:
                                                item_values.append(analysis_results[item]['metrics'].get(metric, 0))
                                            else:
                                                item_values.append(0)
                                        
                                        fig.add_trace(go.Bar(
                                            name=item,
                                            x=metrics_to_visualize,
                                            y=item_values
                                        ))
                                    
                                    fig.update_layout(
                                        title="详细指标比较",
                                        xaxis_title="指标",
                                        yaxis_title="值",
                                        barmode='group',
                                        height=400
                                    )
                                    
                                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("暂无详细分析结果")
            else:
                st.info("暂无详细分析数据")
    def _get_metric_unit(self, metric: str) -> str:
            """获取指标的单位"""
            unit_map = {
                '增益': 'dBi',
                '波束宽度': '°',
                '副瓣电平': 'dB',
                '效率': '%',
                'VSWR': '',
                '轴比': 'dB',
                '带宽': '%',
                '频率': 'GHz',
                '尺寸': 'mm',
                '重量': 'g',
                '成本': '元',
                '性能评分': '分',
                '可靠性': '小时',
                '功耗': 'W',
                '灵敏度': 'dBm',
                '动态范围': 'dB',
                '相位噪声': 'dBc/Hz',
                '谐波抑制': 'dB',
                '隔离度': 'dB',
                '交叉极化': 'dB'
            }
            
            # 模糊匹配
            for key, unit in unit_map.items():
                if key in metric or metric in key:
                    return unit
            
            return ''  # 默认无单位
    
    def _render_analysis_toolbar(self):
        """渲染分析工具栏"""
        st.markdown("---")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("💾 保存结果", width='stretch'):
                self._save_analysis_results()
        
        with col2:
            if st.button("📊 生成报告", width='stretch'):
                self._generate_analysis_report()
        
        with col3:
            if st.button("🔄 重新分析", width='stretch'):
                st.rerun()
        
        with col4:
            if st.button("📈 导出图表", width='stretch'):
                self._export_analysis_charts()
        
        with col5:
            if st.button("🏠 返回主页", width='stretch'):
                st.switch_page("app.py")
    
    def _save_analysis_results(self):
        """保存分析结果"""
        try:
            import json
            from datetime import datetime
            
            # 准备保存的数据
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'antenna': st.session_state.current_antenna.to_dict() 
                    if 'current_antenna' in st.session_state else {},
                'pattern': st.session_state.pattern_data.to_dict() 
                    if 'pattern_data' in st.session_state else {},
                'analysis_results': st.session_state.analysis_results 
                    if 'analysis_results' in st.session_state else {},
                'comparative_results': st.session_state.comparative_analysis_results 
                    if 'comparative_analysis_results' in st.session_state else {}
            }
            
            # 保存为JSON文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            st.success(f"分析结果已保存: {filename}")
            
        except Exception as e:
            st.error(f"保存结果失败: {e}")
    
    def _generate_analysis_report(self):
        """生成分析报告"""
        st.info("分析报告生成功能开发中...")
    
    def _export_analysis_charts(self):
        """导出分析图表"""
        st.info("图表导出功能开发中...")

def render_analysis(config: AppConfig, sidebar_config: Dict[str, Any]):
    """
    渲染分析视图的主函数
    """
    try:
        analysis_view = AnalysisView(config)
        analysis_view.render(sidebar_config)
    except Exception as e:
        st.error(f"分析视图渲染错误: {e}")
        st.exception(e)

if __name__ == "__main__":
    # 测试代码
    config = AppConfig()
    sidebar_config = {
        'page': 'analysis',
        'antenna_config': {},
        'simulation_settings': {},
        'analysis_settings': {},
        'visualization_settings': {},
        'actions': {}
    }
    
    st.set_page_config(layout="wide")
    render_analysis(config, sidebar_config)            
    
