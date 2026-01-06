"""
仿真结果可视化视图模块
展示雷达仿真结果，包括检测性能、信号处理结果和性能分析
使用Streamlit和Plotly进行交互式可视化
"""

import logging
import time
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.simulation_models import SimulationResults, RadarDetection
from services.radar_simulator import RadarSimulator
from controllers.radar_controller import RadarController
from utils.helpers import format_distance, format_frequency, format_time_duration # type: ignore

logger = logging.getLogger(__name__)
class SimulationView:
    """仿真结果可视化视图类"""
    
    def __init__(self):
        self.simulator = RadarSimulator()
        self.controller = RadarController()
        self.setup_page_config()
    
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="仿真结果分析 - 雷达工厂",
            page_icon="📊",
            layout="wide"
        )
        
        # 自定义CSS样式
        st.markdown("""
        <style>
        .simulation-header {
            font-size: 2rem;
            color: #2E86AB;
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #2E86AB;
            margin-bottom: 1rem;
        }
        .detection-card {
            background-color: #e8f4f8;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #2E86AB;
            margin-bottom: 1rem;
        }
        .radar-highlight {
            background-color: #fff3cd;
            padding: 0.5rem;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """渲染页面头部"""
        st.markdown('<div class="simulation-header">📊 雷达仿真结果分析</div>', 
                   unsafe_allow_html=True)
        
        # 显示当前仿真状态
        sim_status = self.simulator.get_simulation_status()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if sim_status['status'] == 'completed':
                st.success(f"仿真完成: {sim_status.get('simulation_id', '未知')}")
                st.write(f"检测目标数: {sim_status.get('detection_count', 0)}")
            else:
                st.info("暂无仿真结果")
        
        with col2:
            if st.button("🔄 重新仿真", width='stretch'):
                st.session_state.current_view = "simulation_setup"
                st.rerun()
        
        with col3:
            if st.button("🏠 返回主界面", width='stretch'):
                st.session_state.current_view = "dashboard"
                st.rerun()
    
    def render_simulation_results(self, results: SimulationResults):
        """渲染仿真结果"""
        if not results or not results.detections:
            st.warning("没有可用的仿真数据")
            return
        
        # 创建选项卡布局
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 性能概览", 
            "🎯 目标检测", 
            "📡 雷达性能", 
            "📊 信号分析",
            "💾 数据导出"
        ])
        
        with tab1:
            self._render_performance_overview(results)
        
        with tab2:
            self._render_target_detection(results)
        
        with tab3:
            self._render_radar_performance(results)
        
        with tab4:
            self._render_signal_analysis(results)
        
        with tab5:
            self._render_data_export(results)
    
    def _render_performance_overview(self, results: SimulationResults):
        """渲染性能概览"""
        st.subheader("📈 仿真性能概览")
        
        # 关键指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_detections = len(results.detections)
            st.metric("总检测次数", f"{total_detections}")
        
        with col2:
            unique_targets = len(set(d.target_id for d in results.detections))
            st.metric("检测目标数", f"{unique_targets}")
        
        with col3:
            expected_targets = len(results.parameters.scenario.targets)
            detection_rate = unique_targets / expected_targets if expected_targets > 0 else 0
            st.metric("检测率", f"{detection_rate:.1%}")
        
        with col4:
            sim_duration = results.parameters.scenario.duration
            detection_freq = total_detections / sim_duration if sim_duration > 0 else 0
            st.metric("检测频率", f"{detection_freq:.1f} Hz")
        
        # 检测时间线
        st.subheader("⏱️ 检测时间线")
        self._render_detection_timeline(results)
        
        # 距离-多普勒分布
        st.subheader("📊 距离-多普勒分布")
        self._render_range_doppler_distribution(results)
    
    def _render_detection_timeline(self, results: SimulationResults):
        """渲染检测时间线"""
        if not results.detections:
            return
        
        # 按时间分组检测
        time_bins = np.linspace(0, results.parameters.scenario.duration, 50)
        detection_counts = []
        
        for i in range(len(time_bins) - 1):
            start_time = time_bins[i]
            end_time = time_bins[i + 1]
            count = sum(1 for d in results.detections if start_time <= d.timestamp < end_time)
            detection_counts.append(count)
        
        # 创建时间线图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=time_bins[:-1],
            y=detection_counts,
            mode='lines+markers',
            name='检测次数',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="检测时间分布",
            xaxis_title="时间 (秒)",
            yaxis_title="检测次数",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 按雷达统计
        radar_detections = {}
        for detection in results.detections:
            radar_id = detection.radar_id
            if radar_id not in radar_detections:
                radar_detections[radar_id] = []
            radar_detections[radar_id].append(detection)
        
        # 显示雷达检测统计
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**雷达检测统计:**")
            for radar_id, detections in radar_detections.items():
                radar = self.controller.get_radar_by_id(radar_id)
                radar_name = radar.name if radar else radar_id
                st.write(f"- {radar_name}: {len(detections)} 次检测")
        
        with col2:
            # 检测质量统计
            snr_values = [d.snr for d in results.detections]
            if snr_values:
                avg_snr = np.mean(snr_values)
                st.metric("平均信噪比", f"{avg_snr:.1f} dB")
            
            confidence_values = [d.detection_confidence for d in results.detections]
            if confidence_values:
                avg_confidence = np.mean(confidence_values)
                st.metric("平均置信度", f"{avg_confidence:.2f}")
    
    def _render_range_doppler_distribution(self, results: SimulationResults):
        """渲染距离-多普勒分布"""
        if not results.detections:
            return
        
        # 准备数据
        ranges = [d.range / 1000 for d in results.detections]  # 转换为km
        dopplers = [d.doppler for d in results.detections]
        snr_values = [d.snr for d in results.detections]
        
        # 创建散点图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=ranges,
            y=dopplers,
            mode='markers',
            marker=dict(
                size=8,
                color=snr_values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="SNR (dB)")
            ),
            text=[f"目标: {d.target_id}<br>置信度: {d.detection_confidence:.2f}" 
                  for d in results.detections],
            hoverinfo='text',
            name="检测点"
        ))
        
        fig.update_layout(
            title="距离-多普勒分布",
            xaxis_title="距离 (km)",
            yaxis_title="多普勒频率 (Hz)",
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if ranges:
                avg_range = np.mean(ranges)
                st.metric("平均检测距离", f"{avg_range:.1f} km")
        
        with col2:
            if dopplers:
                avg_doppler = np.mean(dopplers)
                st.metric("平均多普勒", f"{avg_doppler:.1f} Hz")
        
        with col3:
            if ranges and dopplers:
                # 计算检测区域覆盖率
                max_range = max(ranges) if ranges else 0
                max_doppler = max(abs(d) for d in dopplers) if dopplers else 0
                coverage = (max_range * max_doppler) / 1000  # 简化覆盖率指标
                st.metric("检测区域指标", f"{coverage:.1f}")
    
    def _render_target_detection(self, results: SimulationResults):
        """渲染目标检测详情"""
        st.subheader("🎯 目标检测分析")
        
        if not results.detections:
            st.info("没有检测到目标")
            return
        
        # 目标选择器
        target_ids = list(set(d.target_id for d in results.detections))
        selected_target = st.selectbox("选择目标", target_ids)
        
        # 过滤选定目标的检测
        target_detections = [d for d in results.detections if d.target_id == selected_target]
        
        if not target_detections:
            st.warning("选定目标无检测数据")
            return
        
        # 目标检测统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            detection_count = len(target_detections)
            st.metric("检测次数", detection_count)
        
        with col2:
            time_span = max(d.timestamp for d in target_detections) - min(d.timestamp for d in target_detections)
            st.metric("跟踪时长", format_time_duration(time_span))
        
        with col3:
            avg_snr = np.mean([d.snr for d in target_detections])
            st.metric("平均SNR", f"{avg_snr:.1f} dB")
        
        with col4:
            avg_confidence = np.mean([d.detection_confidence for d in target_detections])
            st.metric("平均置信度", f"{avg_confidence:.2f}")
        
        # 目标轨迹图
        st.subheader("🛤️ 目标运动轨迹")
        self._render_target_trajectory(target_detections, selected_target)
        
        # 检测质量分析
        st.subheader("📈 检测质量分析")
        self._render_detection_quality(target_detections, selected_target)
    
    def _render_target_trajectory(self, detections: List[RadarDetection], target_id: str):
        """渲染目标运动轨迹"""
        # 提取位置信息（简化处理，实际应根据方位和距离计算）
        times = [d.timestamp for d in detections]
        ranges = [d.range / 1000 for d in detections]  # km
        azimuths = [d.azimuth for d in detections]
        
        # 创建轨迹图
        fig = go.Figure()
        
        # 距离-时间轨迹
        fig.add_trace(go.Scatter(
            x=times,
            y=ranges,
            mode='lines+markers',
            name='距离变化',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"目标 {target_id} 距离变化",
            xaxis_title="时间 (秒)",
            yaxis_title="距离 (km)",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 方位角变化
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(
            x=times,
            y=azimuths,
            mode='lines+markers',
            name='方位角变化',
            line=dict(color='#A23B72', width=3),
            marker=dict(size=6)
        ))
        
        fig2.update_layout(
            title=f"目标 {target_id} 方位角变化",
            xaxis_title="时间 (秒)",
            yaxis_title="方位角 (度)",
            height=400
        )
        
        st.plotly_chart(fig2, width='stretch')
        
        # 运动参数统计
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(ranges) > 1:
                range_rate = (ranges[-1] - ranges[0]) / (times[-1] - times[0]) * 1000  # m/s
                st.metric("径向速度", f"{range_rate:.1f} m/s")
        
        with col2:
            if len(azimuths) > 1:
                azimuth_rate = (azimuths[-1] - azimuths[0]) / (times[-1] - times[0])
                st.metric("方位角变化率", f"{azimuth_rate:.1f} °/s")
        
        with col3:
            if ranges:
                min_range = min(ranges)
                max_range = max(ranges)
                st.metric("距离范围", f"{min_range:.1f} - {max_range:.1f} km")
    
    def _render_detection_quality(self, detections: List[RadarDetection], target_id: str):
        """渲染检测质量分析"""
        times = [d.timestamp for d in detections]
        snr_values = [d.snr for d in detections]
        confidence_values = [d.detection_confidence for d in detections]
        
        # 创建质量指标图
        fig = go.Figure()
        
        # SNR趋势
        fig.add_trace(go.Scatter(
            x=times,
            y=snr_values,
            mode='lines+markers',
            name='信噪比 (dB)',
            line=dict(color='#2E86AB', width=3),
            yaxis='y1'
        ))
        
        # 置信度趋势（次坐标轴）
        fig.add_trace(go.Scatter(
            x=times,
            y=confidence_values,
            mode='lines+markers',
            name='检测置信度',
            line=dict(color='#F18F01', width=3),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f"目标 {target_id} 检测质量",
            xaxis_title="时间 (秒)",
            yaxis=dict(
                title="信噪比 (dB)",
                # titlefont=dict(color="#2E86AB"),
                tickfont=dict(color="#2E86AB")
            ),
            yaxis2=dict(
                title="检测置信度",
                # titlefont=dict(color="#F18F01"),
                tickfont=dict(color="#F18F01"),
                overlaying="y",
                side="right"
            ),
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 质量统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_snr = np.mean(snr_values)
            st.metric("平均SNR", f"{avg_snr:.1f} dB")
        
        with col2:
            snr_std = np.std(snr_values)
            st.metric("SNR标准差", f"{snr_std:.1f} dB")
        
        with col3:
            avg_confidence = np.mean(confidence_values)
            st.metric("平均置信度", f"{avg_confidence:.2f}")
        
        with col4:
            low_confidence_count = sum(1 for c in confidence_values if c < 0.7)
            st.metric("低置信度检测", low_confidence_count)
    
    def _render_radar_performance(self, results: SimulationResults):
        """渲染雷达性能对比"""
        st.subheader("📡 雷达性能对比分析")
        
        if not results.detections:
            return
        
        # 按雷达分组检测数据
        radar_stats = {}
        for detection in results.detections:
            radar_id = detection.radar_id
            if radar_id not in radar_stats:
                radar_stats[radar_id] = {
                    'detections': [],
                    'snr_values': [],
                    'ranges': [],
                    'confidences': []
                }
            
            radar_stats[radar_id]['detections'].append(detection)
            radar_stats[radar_id]['snr_values'].append(detection.snr)
            radar_stats[radar_id]['ranges'].append(detection.range)
            radar_stats[radar_id]['confidences'].append(detection.detection_confidence)
        
        # 准备对比数据
        radar_names = []
        detection_counts = []
        avg_snrs = []
        avg_ranges = []
        max_ranges = []
        
        for radar_id, stats in radar_stats.items():
            radar = self.controller.get_radar_by_id(radar_id)
            radar_name = radar.name if radar else radar_id
            
            radar_names.append(radar_name)
            detection_counts.append(len(stats['detections']))
            avg_snrs.append(np.mean(stats['snr_values']) if stats['snr_values'] else 0)
            avg_ranges.append(np.mean(stats['ranges']) / 1000 if stats['ranges'] else 0)  # km
            max_ranges.append(max(stats['ranges']) / 1000 if stats['ranges'] else 0)  # km
        
        # 雷达性能对比图
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=radar_names,
            y=detection_counts,
            name='检测次数',
            marker_color='#2E86AB'
        ))
        
        fig.add_trace(go.Scatter(
            x=radar_names,
            y=avg_snrs,
            name='平均SNR (dB)',
            marker=dict(color='#F18F01', size=10),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="雷达检测性能对比",
            xaxis_title="雷达型号",
            yaxis=dict(
                title="检测次数",
                # titlefont=dict(color="#2E86AB"),
                tickfont=dict(color="#2E86AB")
            ),
            yaxis2=dict(
                title="平均SNR (dB)",
                # titlefont=dict(color="#F18F01"),
                tickfont=dict(color="#F18F01"),
                overlaying="y",
                side="right"
            ),
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 距离性能对比
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=radar_names,
            y=avg_ranges,
            name='平均检测距离',
            marker_color='#2E86AB'
        ))
        
        fig2.add_trace(go.Scatter(
            x=radar_names,
            y=max_ranges,
            name='最远检测距离',
            marker=dict(color='#C73E1D', size=10, symbol='diamond'),
            line=dict(width=3)
        ))
        
        fig2.update_layout(
            title="雷达距离性能对比",
            xaxis_title="雷达型号",
            yaxis_title="距离 (km)",
            height=400
        )
        
        st.plotly_chart(fig2, width='stretch')
        
        # 雷达详细性能表
        st.subheader("📋 雷达详细性能")
        
        performance_data = []
        for radar_id, stats in radar_stats.items():
            radar = self.controller.get_radar_by_id(radar_id)
            
            performance_data.append({
                '雷达名称': radar.name if radar else radar_id,
                '检测次数': len(stats['detections']),
                '平均SNR (dB)': f"{np.mean(stats['snr_values']):.1f}" if stats['snr_values'] else "0",
                '平均距离 (km)': f"{np.mean(stats['ranges']) / 1000:.1f}" if stats['ranges'] else "0",
                '最远距离 (km)': f"{max(stats['ranges']) / 1000:.1f}" if stats['ranges'] else "0",
                '平均置信度': f"{np.mean(stats['confidences']):.2f}" if stats['confidences'] else "0"
            })
        
        df = pd.DataFrame(performance_data)
        st.dataframe(df, width='stretch')
    
    def _render_signal_analysis(self, results: SimulationResults):
        """渲染信号分析"""
        st.subheader("📊 信号处理分析")
        
        if not results.raw_data:
            st.info("无原始信号数据可用")
            return
        
        # 选择雷达和时间的信号数据
        radar_ids = list(results.raw_data.keys())
        selected_radar = st.selectbox("选择雷达", radar_ids)
        
        if selected_radar not in results.raw_data:
            st.warning("选定雷达无信号数据")
            return
        
        radar_data = results.raw_data[selected_radar]
        timestamps = list(radar_data.keys())
        
        if not timestamps:
            st.warning("无时间点数据")
            return
        
        selected_time = st.select_slider(
            "选择时间点",
            options=timestamps,
            value=timestamps[len(timestamps)//2]
        )
        
        time_data = radar_data[selected_time]
        
        # 显示信号处理结果
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("距离像")
            if 'range_profile' in time_data['processed'] and time_data['processed']['range_profile'] is not None:
                range_profile = time_data['processed']['range_profile']
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=np.abs(range_profile),
                    mode='lines',
                    name='距离像',
                    line=dict(color='#2E86AB', width=2)
                ))
                
                fig.update_layout(
                    title=f"时间 {selected_time:.1f}s 的距离像",
                    xaxis_title="距离单元",
                    yaxis_title="幅度",
                    height=300
                )
                
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("无距离像数据")
        
        with col2:
            st.subheader("检测图")
            if 'detection_map' in time_data['processed'] and time_data['processed']['detection_map'] is not None:
                detection_map = time_data['processed']['detection_map']
                
                fig = go.Figure()
                fig.add_trace(go.Heatmap(
                    z=detection_map.astype(int),
                    colorscale='Viridis',
                    showscale=False
                ))
                
                fig.update_layout(
                    title=f"时间 {selected_time:.1f}s 的检测图",
                    xaxis_title="距离单元",
                    yaxis_title="多普勒单元",
                    height=300
                )
                
                st.plotly_chart(fig, width='stretch')
                
                # 检测统计
                detection_count = np.sum(detection_map)
                st.metric("检测点数量", int(detection_count))
            else:
                st.info("无检测图数据")
        
        # 信号统计信息
        st.subheader("📈 信号统计")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'baseband' in time_data:
                signal_power = np.mean(np.abs(time_data['baseband'])**2)
                st.metric("信号功率", f"{signal_power:.2e}")
        
        with col2:
            if 'baseband' in time_data:
                noise_power = np.var(time_data['baseband'])
                st.metric("噪声功率", f"{noise_power:.2e}")
        
        with col3:
            if 'baseband' in time_data and noise_power > 0: # type: ignore
                snr_linear = signal_power / noise_power # type: ignore
                snr_db = 10 * np.log10(snr_linear)
                st.metric("信噪比", f"{snr_db:.1f} dB")
        
        with col4:
            if 'processed' in time_data and 'detection_map' in time_data['processed']:
                detection_map = time_data['processed']['detection_map']
                if detection_map is not None:
                    false_alarms = np.sum(detection_map) - len(time_data['detections'])
                    st.metric("虚警数", max(0, false_alarms))
    
    def _render_data_export(self, results: SimulationResults):
        """渲染数据导出功能"""
        st.subheader("💾 仿真数据导出")
        
        # 导出选项
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "导出格式",
                options=["JSON", "CSV", "Excel"]
            )
            
            include_raw_data = st.checkbox("包含原始信号数据", value=False)
            include_analysis = st.checkbox("包含性能分析", value=True)
        
        with col2:
            filename = st.text_input(
                "文件名",
                value=f"radar_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # 添加文件扩展名
            if export_format == "JSON":
                filename += ".json"
            elif export_format == "CSV":
                filename += ".csv"
            elif export_format == "Excel":
                filename += ".xlsx"
        
        # 导出按钮
        if st.button("📥 导出数据", type="primary", width='stretch'):
            with st.spinner("正在导出数据..."):
                try:
                    if export_format == "JSON":
                        success = self.simulator.export_simulation_data(results, filename)
                        if success:
                            st.success(f"数据已导出为 {filename}")
                            
                            # 提供下载链接（在Streamlit中通常通过文件读取实现）
                            with open(filename, "r") as f:
                                st.download_button(
                                    label="下载JSON文件",
                                    data=f,
                                    file_name=filename,
                                    mime="application/json"
                                )
                        else:
                            st.error("导出失败")
                    
                    elif export_format == "CSV":
                        # 转换为CSV格式
                        df_detections = pd.DataFrame([d.to_dict() for d in results.detections])
                        csv_data = df_detections.to_csv(index=False)
                        
                        st.download_button(
                            label="下载CSV文件",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv"
                        )
                        st.success("CSV数据准备完成")
                    
                    elif export_format == "Excel":
                        # 转换为Excel格式
                        df_detections = pd.DataFrame([d.to_dict() for d in results.detections])
                        
                        # 使用BytesIO创建内存文件
                        import io
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_detections.to_excel(writer, sheet_name='检测数据', index=False)
                            
                            # 可以添加更多sheet
                            if results.metrics:
                                df_metrics = pd.DataFrame([results.metrics])
                                df_metrics.to_excel(writer, sheet_name='性能指标', index=False)
                        
                        st.download_button(
                            label="下载Excel文件",
                            data=buffer.getvalue(),
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success("Excel数据准备完成")
                
                except Exception as e:
                    st.error(f"导出过程中发生错误: {str(e)}")
        
        # 显示数据预览
        st.subheader("👀 数据预览")
        
        preview_option = st.selectbox(
            "预览内容",
            options=["检测数据", "性能指标", "雷达统计"]
        )
        
        if preview_option == "检测数据":
            if results.detections:
                # 显示前100条检测数据
                preview_data = [d.to_dict() for d in results.detections[:100]]
                df_preview = pd.DataFrame(preview_data)
                st.dataframe(df_preview, width='stretch')
                
                if len(results.detections) > 100:
                    st.info(f"显示前100条数据，共{len(results.detections)}条")
            else:
                st.info("无检测数据")
        
        elif preview_option == "性能指标":
            if results.metrics:
                # 将指标转换为适合显示的格式
                metrics_flat = {}
                
                def flatten_dict(d, prefix=''):
                    for k, v in d.items():
                        if isinstance(v, dict):
                            flatten_dict(v, f"{prefix}{k}.")
                        else:
                            metrics_flat[f"{prefix}{k}"] = v
                
                flatten_dict(results.metrics)
                df_metrics = pd.DataFrame(list(metrics_flat.items()), columns=['指标', '值'])
                st.dataframe(df_metrics, width='stretch')
            else:
                st.info("无性能指标数据")
        
        elif preview_option == "雷达统计":
            if results.detections:
                # 按雷达统计
                radar_stats = {}
                for detection in results.detections:
                    radar_id = detection.radar_id
                    if radar_id not in radar_stats:
                        radar_stats[radar_id] = {
                            '检测次数': 0,
                            '平均SNR': [],
                            '平均距离': [],
                            '平均置信度': []
                        }
                    
                    radar_stats[radar_id]['检测次数'] += 1
                    radar_stats[radar_id]['平均SNR'].append(detection.snr)
                    radar_stats[radar_id]['平均距离'].append(detection.range)
                    radar_stats[radar_id]['平均置信度'].append(detection.detection_confidence)
                
                # 计算平均值
                stats_list = []
                for radar_id, stats in radar_stats.items():
                    radar = self.controller.get_radar_by_id(radar_id)
                    stats_list.append({
                        '雷达ID': radar_id,
                        '雷达名称': radar.name if radar else radar_id,
                        '检测次数': stats['检测次数'],
                        '平均SNR(dB)': np.mean(stats['平均SNR']) if stats['平均SNR'] else 0,
                        '平均距离(km)': np.mean(stats['平均距离']) / 1000 if stats['平均距离'] else 0,
                        '平均置信度': np.mean(stats['平均置信度']) if stats['平均置信度'] else 0
                    })
                
                df_stats = pd.DataFrame(stats_list)
                st.dataframe(df_stats, width='stretch')
            else:
                st.info("无雷达统计数据")
    
    def render_simulation_setup(self):
        """渲染仿真设置界面（如果没有仿真结果时）"""
        st.subheader("⚙️ 仿真参数设置")
        
        # 检查是否有待执行的仿真参数
        if st.session_state.get('simulation_params') and not st.session_state.get('simulation_results'):
            # 自动执行仿真
            self._execute_simulation(st.session_state.simulation_params)
            return
        
        # 仿真参数设置
        col1, col2 = st.columns(2)
        
        with col1:
            sim_duration = st.slider(
                "仿真时长 (秒)",
                min_value=1.0,
                max_value=300.0,
                value=1.0,
                step=1.0
            )
            
            time_step = st.select_slider(
                "时间步长 (秒)",
                options=[0.01, 0.05, 0.1, 0.5, 1.0],
                value=0.1
            )
        
        with col2:
            processing_mode = st.selectbox(
                "信号处理模式",
                options=["基础处理", "MTI处理", "MTD处理", "高级处理"],
                index=0
            )
            
            noise_level = st.slider(
                "噪声水平 (dB)",
                min_value=-20,
                max_value=20,
                value=0,
                step=1
            )
        
        # 雷达选择
        controller = st.session_state.radar_controller
        available_radars = list(controller.get_all_radars().keys())
        selected_radars = st.multiselect(
            "选择参与仿真的雷达",
            options=available_radars,
            default=available_radars[:min(3, len(available_radars))] if available_radars else []
        )
        
        # 目标参数设置
        st.subheader("🎯 目标参数")
        col3, col4 = st.columns(2)
        
        with col3:
            target_rcs = st.selectbox(
                "目标RCS (m²)",
                options=[0.01, 0.1, 1.0, 5.0, 10.0, 100.0],
                index=2,
                help="选择目标雷达截面积"
            )
            
            target_type = st.selectbox(
                "目标类型",
                options=["飞机", "导弹", "无人机", "舰船", "地面车辆"],
                index=0
            )
        
        with col4:
            initial_range = st.slider(
                "初始距离 (km)",
                min_value=1.0,
                max_value=500.0,
                value=5.0,
                step=5.0
            )
            
            target_speed = st.slider(
                "目标速度 (m/s)",
                min_value=0.0,
                max_value=1000.0,
                value=300.0,
                step=50.0
            )
        
        # 开始仿真按钮
        if st.button("🚀 开始仿真", type="primary", use_container_width=True):
            if not selected_radars:
                st.error("请选择至少一个雷达")
            else:
                # 创建仿真参数
                simulation_params = {
                    "radars": selected_radars,
                    "duration": sim_duration,
                    "time_step": time_step,
                    "processing_mode": processing_mode,
                    "noise_level": noise_level,
                    "target_rcs": target_rcs,
                    "target_type": target_type,
                    "initial_range": initial_range * 1000,  # 转换为米
                    "target_speed": target_speed
                }
                
                # 保存参数
                st.session_state.simulation_params = simulation_params
                
                # 执行仿真
                self._execute_simulation(simulation_params)

    def _execute_simulation(self, params: Dict[str, Any]):
        """执行仿真"""
        with st.spinner("正在运行仿真，请稍候..."):
            try:
                # 获取控制器和仿真器
                controller = st.session_state.radar_controller
                simulator = st.session_state.radar_simulator
                
                # 获取雷达对象
                radar_ids = params.get('radars', [])
                radars = []
                for radar_id in radar_ids:
                    radar = controller.get_radar_by_id(radar_id)
                    if radar:
                        radars.append(radar)
                
                if not radars:
                    st.error("没有有效的雷达进行仿真")
                    return
                
                # 创建仿真场景
                from models.simulation_models import (
                    SimulationScenario, TargetParameters, TargetType, RCSModel
                )
                import numpy as np
                
                # 映射目标类型
                target_type_map = {
                    "飞机": TargetType.AIRCRAFT,
                    "导弹": TargetType.MISSILE, 
                    "无人机": TargetType.DRONE,
                    "舰船": TargetType.SHIP,
                    "地面车辆": TargetType.GROUND_VEHICLE
                }
                
                # 创建目标
                target = TargetParameters(
                    target_id="sim_target_001",
                    target_type=target_type_map.get(params.get('target_type', '飞机'), TargetType.AIRCRAFT),
                    position=np.array([params.get('initial_range', 1000), 0, 300]),  # 100km距离，10km高度
                    velocity=np.array([-params.get('target_speed', 100), 0, 0]),  # 朝向雷达飞行
                    rcs_sqm=params.get('target_rcs', 5.0),
                    rcs_model=RCSModel.SWERLING1
                )
                
                # 创建场景
                scenario = SimulationScenario(
                    scenario_id=f"sim_{int(time.time())}",
                    name="用户仿真场景",
                    description="基于用户设置的仿真场景",
                    duration=params.get('duration', 2.0),
                    time_step=params.get('time_step', 1.0),
                    radar_positions={r.radar_id: np.array([0, 0, 0]) for r in radars},
                    targets=[target]
                )
                
                # 运行仿真
                results = simulator.run_simulation(scenario, radars)
                
                # 保存结果
                st.session_state.simulation_results = results
                
                # 清除待执行参数
                if 'simulation_params' in st.session_state:
                    del st.session_state.simulation_params
                
                st.success("仿真完成！")
                st.rerun()
                
            except Exception as e:
                import traceback
                logger.error(f"仿真执行错误: {traceback.format_exc()}")
                st.error(f"仿真执行失败: {str(e)}")
                
                # 提供重试选项
                if st.button("重试仿真"):
                    st.rerun()
    
    def render(self, simulation_results: Optional[SimulationResults] = None):
        """渲染完整仿真结果视图"""
        self.render_header()
        
        # 检查是否有仿真结果
        if simulation_results is None:
            # 尝试从session state获取
            if 'simulation_results' in st.session_state:
                simulation_results = st.session_state.simulation_results
        
        if simulation_results:
            self.render_simulation_results(simulation_results)
        else:
            # 如果没有仿真结果，显示设置界面
            self.render_simulation_setup()


# 辅助函数
def create_sample_results() -> SimulationResults:
    """创建示例仿真结果（用于测试）"""
    from models.simulation_models import (
        SimulationParameters, SimulationScenario, TargetParameters,
        TargetType, RCSModel, RadarDetection
    )
    import numpy as np
    from datetime import datetime
    
    # 创建示例场景
    scenario = SimulationScenario(
        scenario_id="sample_001",
        name="示例仿真场景",
        description="多目标测试场景",
        duration=1.0,
        time_step=0.1,
        radar_positions={
            "JY-27B_UHF001": np.array([0, 0, 0]),
            "KJ-500_L001": np.array([50e3, 0, 10e3])
        },
        targets=[
            TargetParameters(
                target_id="target_001",
                target_type=TargetType.AIRCRAFT,
                position=np.array([100e3, 20e3, 10e3]),
                velocity=np.array([-300, 50, 0]),
                rcs_sqm=5.0,
                rcs_model=RCSModel.SWERLING1
            ),
            TargetParameters(
                target_id="target_002",
                target_type=TargetType.MISSILE,
                position=np.array([80e3, -30e3, 5e3]),
                velocity=np.array([-500, 0, 0]),
                rcs_sqm=0.5,
                rcs_model=RCSModel.SWERLING3
            )
        ]
    )
    
    # 创建仿真参数
    params = SimulationParameters(
        simulation_id=f"SAMPLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        scenario=scenario,
        radars=[]  # 这里应该是雷达模型列表
    )
    
    # 创建示例检测数据
    detections = []
    np.random.seed(42)
    
    targets = ["target_001", "target_002"]
    radars = ["JY-27B_UHF001", "KJ-500_L001"]
    
    for t in np.arange(0, 60, 0.5):  # 每0.5秒一个检测
        for radar_id in radars:
            for target_id in targets:
                # 随机决定是否检测到
                if np.random.random() > 0.3:  # 70%检测概率
                    # 创建检测
                    detection = RadarDetection(
                        timestamp=t + np.random.uniform(-0.1, 0.1), # type: ignore
                        radar_id=radar_id,
                        target_id=target_id,
                        range=np.random.uniform(50e3, 150e3),
                        azimuth=np.random.uniform(-30, 30),
                        elevation=np.random.uniform(-5, 5),
                        doppler=np.random.uniform(-1000, 1000),
                        snr=np.random.uniform(10, 25),
                        detection_confidence=np.random.uniform(0.6, 0.95)
                    )
                    detections.append(detection)
    
    # 创建仿真结果
    results = SimulationResults(
        parameters=params,
        detections=detections,
        metrics={
            "total_detections": len(detections),
            "unique_targets_detected": 2,
            "simulation_duration": 60.0,
            "detection_rate": len(detections) / 60.0,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    return results


def main():
    """主函数"""
    # 初始化仿真视图
    view = SimulationView()
    
    # 使用示例数据或真实数据
    if 'simulation_results' in st.session_state:
        results = st.session_state.simulation_results
    else:
        # 使用示例数据
        results = create_sample_results()
        st.session_state.simulation_results = results
    
    # 渲染视图
    view.render(results)


if __name__ == "__main__":
    main()            