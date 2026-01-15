"""
雷达性能分析页面
功能：进行有/无风机条件下的雷达性能量化分析
"""

import streamlit as st
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
from datetime import datetime
import time

# 添加utils路径
sys.path.append(str(Path(__file__).parent.parent / "config"))
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from config.config import (
    COLOR_SCHEME, EVALUATION_PARAMS, RADAR_FREQUENCY_BANDS,
    PHYSICAL_CONSTANTS, TARGET_RCS_DB
)
from utils.radar_calculations import (
    RadarCalculator, RadarParameters, TargetParameters, TurbineParameters,
    CalculationResults, create_radar_parameters_from_config,
    create_target_parameters_from_config, create_turbine_parameters_from_config
)
from utils.visualization import VisualizationTools

# 页面配置
st.set_page_config(
    page_title="雷达性能分析 | 风电雷达影响评估系统",
    page_icon="📡",
    layout="wide"
)

# 页面标题
st.title("📡 雷达性能分析")
st.markdown("量化分析有/无风机条件下的雷达探测性能")

# 检查场景是否加载
if 'scenario_data' not in st.session_state or not st.session_state.get('scenario_loaded', False):
    st.warning("⚠️ 请先加载场景配置文件")
    
    if st.button("📁 前往场景配置页面", width='stretch'):
        st.switch_page("pages/1_场景配置.py")
    
    st.stop()

# 获取场景数据
scenario_data = st.session_state.scenario_data
scenario_name = st.session_state.scenario_name

# 初始化会话状态
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
    st.session_state.calculation_complete = False
    st.session_state.analysis_progress = 0

# 初始化工具
viz_tools = VisualizationTools()
calculator = RadarCalculator()

def perform_comprehensive_analysis(
    scenario_data: Dict[str, Any],
    analysis_config: Dict[str, Any],
    calculator: RadarCalculator
) -> Dict[str, Any]:
    """执行综合分析"""
    results = {
        'analysis_config': analysis_config,
        'scenario_info': {
            'name': scenario_data.get('name', ''),
            'description': scenario_data.get('description', ''),
            'num_turbines': len(scenario_data.get('wind_turbines', [])),
            'num_radars': len(scenario_data.get('radar_stations', [])),
            'num_targets': len(scenario_data.get('targets', []))
        },
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'comparison_results': {},
        'detailed_analysis': {},
        'performance_metrics': {}
    }
    
    # 提取配置
    min_range_km = analysis_config['min_range_km']
    max_range_km = analysis_config['max_range_km']
    range_steps = analysis_config['range_steps']
    
    selected_radar = analysis_config['selected_radar']
    selected_target = analysis_config['selected_target']
    
    # 生成距离数组
    distances_km = np.linspace(min_range_km, max_range_km, range_steps)
    distances_m = distances_km * 1000
    
    # 创建雷达参数
    radar_params = create_radar_parameters_from_config(selected_radar)
    
    # 创建目标参数
    target_params = create_target_parameters_from_config(selected_target)
    
    # 创建风机参数列表
    turbines_params = []
    for turbine in scenario_data.get('wind_turbines', []):
        turbine_params = create_turbine_parameters_from_config(turbine)
        turbines_params.append(turbine_params)
    
    # 分析有/无风机条件
    print("开始分析有/无风机条件...")
    
    # 存储结果
    snr_without = []
    snr_with = []
    received_power_without = []
    received_power_with = []
    detection_prob_without = []
    detection_prob_with = []
    multipath_loss_without = []
    multipath_loss_with = []
    doppler_freq = []
    
    for i, distance_m in enumerate(distances_m):
        # 更新目标距离
        target_params.distance_m = distance_m
        
        # 无风机条件
        result_without = calculator.perform_comprehensive_analysis(
            radar_params, target_params, turbines=None, include_turbine_effects=False
        )
        
        # 有风机条件
        result_with = calculator.perform_comprehensive_analysis(
            radar_params, target_params, turbines=turbines_params, include_turbine_effects=True
        )
        
        # 保存结果
        snr_without.append(result_without.snr_db)
        snr_with.append(result_with.snr_db)
        received_power_without.append(result_without.received_power_db)
        received_power_with.append(result_with.received_power_db)
        detection_prob_without.append(result_without.detection_probability)
        detection_prob_with.append(result_with.detection_probability)
        multipath_loss_without.append(result_without.multipath_loss_db)
        multipath_loss_with.append(result_with.multipath_loss_db)
        
        # 计算多普勒频率
        doppler = calculator.calculate_doppler_frequency(
            radar_params.frequency_ghz, target_params.velocity_ms
        )
        doppler_freq.append(doppler)
    
    # 保存对比结果
    results['comparison_results'] = {
        'distances_km': distances_km.tolist(),
        'snr_without_turbines': snr_without,
        'snr_with_turbines': snr_with,
        'received_power_without_turbines': received_power_without,
        'received_power_with_turbines': received_power_with,
        'detection_prob_without_turbines': detection_prob_without,
        'detection_prob_with_turbines': detection_prob_with,
        'multipath_loss_without_turbines': multipath_loss_without,
        'multipath_loss_with_turbines': multipath_loss_with,
        'doppler_frequencies': doppler_freq
    }
    
    # 计算性能指标
    print("计算性能指标...")
    performance_metrics = calculator.generate_performance_metrics(
        result_with, threshold_snr_db=13
    )
    results['performance_metrics'] = performance_metrics
    
    # 计算场景对比
    print("计算场景对比...")
    scenario_comparison = calculator.calculate_scenario_comparison(
        {'snr_db': np.mean(snr_without), 'received_power_db': np.mean(received_power_without),
         'detection_probability': np.mean(detection_prob_without), 'multipath_loss_db': np.mean(multipath_loss_without)},
        {'snr_db': np.mean(snr_with), 'received_power_db': np.mean(received_power_with),
         'detection_probability': np.mean(detection_prob_with), 'multipath_loss_db': np.mean(multipath_loss_with)}
    )
    results['scenario_comparison'] = scenario_comparison
    
    return results


# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "⚙️ 分析设置", 
    "📈 性能对比", 
    "🎯 目标分析", 
    "📊 综合报告"
])

with tab1:
    st.header("分析参数设置")
    
    col_set1, col_set2 = st.columns(2)
    
    with col_set1:
        st.subheader("分析范围设置")
        
        # 分析距离范围
        min_range = st.number_input(
            "最小距离 (km)",
            min_value=1.0,
            max_value=1000.0,
            value=10.0,
            step=10.0,
            help="分析的最小距离"
        )
        
        max_range = st.number_input(
            "最大距离 (km)",
            min_value=10.0,
            max_value=1000.0,
            value=200.0,
            step=10.0,
            help="分析的最大距离"
        )
        
        range_steps = st.slider(
            "距离分析点数",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="距离方向的分析点数"
        )
        
        # 分析频段
        st.subheader("频段分析设置")
        
        frequency_bands = st.multiselect(
            "选择分析频段",
            options=list(RADAR_FREQUENCY_BANDS.keys()),
            default=["S", "X", "L"],
            help="选择要分析的雷达频段"
        )
    
    with col_set2:
        st.subheader("分析条件设置")
        
        # 大气条件
        temperature = st.number_input(
            "温度 (°C)",
            min_value=-50.0,
            max_value=50.0,
            value=15.0,
            step=1.0,
            help="环境温度"
        )
        
        humidity = st.slider(
            "相对湿度 (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="环境相对湿度"
        )
        
        pressure = st.number_input(
            "气压 (hPa)",
            min_value=800.0,
            max_value=1100.0,
            value=1013.25,
            step=1.0,
            help="大气压力"
        )
        
        # 分析模式
        analysis_mode = st.selectbox(
            "分析模式",
            ["快速分析", "详细分析", "专家分析"],
            help="选择分析的计算深度和精度"
        )
        
        # 脉冲积累数
        integration_pulses = st.slider(
            "脉冲积累数",
            min_value=1,
            max_value=100,
            value=10,
            help="脉冲积累数量"
        )
    
    st.markdown("---")
    st.subheader("雷达选择")
    
    # 获取雷达列表
    radars = scenario_data.get('radar_stations', [])
    if not radars:
        st.error("场景中没有雷达配置，请先添加雷达")
    else:
        radar_options = {f"{r.get('id', '')} ({r.get('type', '')})": r for r in radars}
        selected_radar_label = st.selectbox(
            "选择分析雷达",
            options=list(radar_options.keys()),
            help="选择要分析的雷达站"
        )
        
        selected_radar = radar_options[selected_radar_label]
        
        # 显示雷达信息
        col_radar1, col_radar2, col_radar3 = st.columns(3)
        
        with col_radar1:
            st.metric("雷达ID", selected_radar.get('id', ''))
            st.metric("雷达类型", selected_radar.get('type', ''))
        
        with col_radar2:
            st.metric("工作频段", selected_radar.get('frequency_band', ''))
            st.metric("峰值功率", f"{selected_radar.get('peak_power', 0) / 1000:.0f} kW")
        
        with col_radar3:
            st.metric("天线增益", f"{selected_radar.get('antenna_gain', 0)} dBi")
            st.metric("波束宽度", f"{selected_radar.get('beam_width', 0)}°")
    
    st.markdown("---")
    st.subheader("目标选择")
    
    # 获取目标列表
    targets = scenario_data.get('targets', [])
    if not targets:
        st.error("场景中没有目标配置，请先添加目标")
    else:
        target_options = {f"{t.get('id', '')} ({t.get('type', '')})": t for t in targets}
        selected_target_label = st.selectbox(
            "选择分析目标",
            options=list(target_options.keys()),
            help="选择要分析的目标"
        )
        
        selected_target = target_options[selected_target_label]
        
        # 显示目标信息
        col_target1, col_target2, col_target3 = st.columns(3)
        
        with col_target1:
            st.metric("目标ID", selected_target.get('id', ''))
            st.metric("目标类型", selected_target.get('type', ''))
        
        with col_target2:
            st.metric("RCS", f"{selected_target.get('rcs', 0)} m²")
            st.metric("速度", f"{selected_target.get('speed', 0)} m/s")
        
        with col_target3:
            st.metric("高度", f"{selected_target.get('position', {}).get('alt', 0):.0f} m")
            st.metric("航向", f"{selected_target.get('heading', 0)}°")
    
    st.markdown("---")
    
    # 分析按钮
    if st.button("🚀 开始性能分析", type="primary", width='stretch'):
        with st.spinner("正在进行雷达性能分析..."):
            # 初始化进度
            st.session_state.analysis_progress = 0
            progress_bar = st.progress(0)
            
            try:
                # 准备分析数据
                analysis_config = {
                    'min_range_km': min_range,
                    'max_range_km': max_range,
                    'range_steps': range_steps,
                    'frequency_bands': frequency_bands,
                    'temperature': temperature,
                    'humidity': humidity,
                    'pressure': pressure,
                    'analysis_mode': analysis_mode,
                    'integration_pulses': integration_pulses,
                    'selected_radar': selected_radar,
                    'selected_target': selected_target
                }
                
                # 执行分析
                results = perform_comprehensive_analysis(
                    scenario_data, analysis_config, calculator
                )
                
                # 保存结果
                st.session_state.analysis_results = results
                st.session_state.calculation_complete = True
                st.session_state.analysis_config = analysis_config
                
                # 完成进度
                st.session_state.analysis_progress = 100
                progress_bar.progress(100)
                
                st.success("✅ 雷达性能分析完成！")
                
                # 显示完成时间
                st.info(f"分析完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
            except Exception as e:
                st.error(f"分析过程中发生错误: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

with tab2:
    st.header("性能对比分析")
    
    if not st.session_state.get('calculation_complete', False):
        st.warning("请先进行性能分析")
    else:
        results = st.session_state.analysis_results
        comparison = results['comparison_results']
        
        # 创建子选项卡
        subtab1, subtab2, subtab3, subtab4 = st.tabs([
            "📶 信噪比对比", 
            "⚡ 接收功率对比", 
            "🎯 检测概率对比", 
            "🌊 多径效应对比"
        ])
        
        with subtab1:
            st.subheader("信噪比对比分析")
            
            # 创建图表
            fig_snr = go.Figure()
            
            fig_snr.add_trace(go.Scatter(
                x=comparison['distances_km'],
                y=comparison['snr_without_turbines'],
                mode='lines',
                name='无风机',
                line=dict(color=COLOR_SCHEME['success'], width=3),
                hovertemplate='距离: %{x:.1f}km<br>SNR: %{y:.1f}dB<extra></extra>'
            ))
            
            fig_snr.add_trace(go.Scatter(
                x=comparison['distances_km'],
                y=comparison['snr_with_turbines'],
                mode='lines',
                name='有风机',
                line=dict(color=COLOR_SCHEME['warning'], width=3, dash='dash'),
                hovertemplate='距离: %{x:.1f}km<br>SNR: %{y:.1f}dB<extra></extra>'
            ))
            
            # 添加检测门限线
            fig_snr.add_hline(
                y=13,
                line_dash="dot",
                line_color="red",
                annotation_text="检测门限 (13dB)",
                annotation_position="bottom right"
            )
            
            fig_snr.update_layout(
                title=dict(
                    text="有/无风机条件下信噪比对比",
                    font=dict(size=16, color=COLOR_SCHEME['primary']),
                    x=0.5
                ),
                xaxis_title=dict(
                    text="距离 (km)",
                    font=dict(color=COLOR_SCHEME['light'])
                ),
                yaxis_title=dict(
                    text="信噪比 (dB)",
                    font=dict(color=COLOR_SCHEME['light'])
                ),
                plot_bgcolor='rgba(20, 25, 50, 0.1)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLOR_SCHEME['light']),
                hovermode='x unified',
                height=500,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(30, 30, 50, 0.7)',
                    bordercolor=COLOR_SCHEME['primary'],
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig_snr, width='stretch')
            
            # 统计分析
            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            
            with col_stats1:
                snr_without_mean = np.mean(comparison['snr_without_turbines'])
                st.metric("无风机平均SNR", f"{snr_without_mean:.1f} dB")
            
            with col_stats2:
                snr_with_mean = np.mean(comparison['snr_with_turbines'])
                st.metric("有风机平均SNR", f"{snr_with_mean:.1f} dB")
            
            with col_stats3:
                snr_diff = snr_with_mean - snr_without_mean
                st.metric("SNR差值", f"{snr_diff:.1f} dB")
            
            with col_stats4:
                snr_percent_change = (snr_diff / abs(snr_without_mean)) * 100 if snr_without_mean != 0 else 0
                st.metric("变化率", f"{snr_percent_change:.1f}%")
            
            # 解释分析
            st.markdown("### 📊 信噪比分析解读")
            
            if snr_diff < -5:
                st.error("**严重影响**: 风机导致信噪比显著下降，可能严重影响雷达探测性能")
            elif snr_diff < -2:
                st.warning("**中等影响**: 风机导致信噪比有一定程度下降，需要关注")
            elif snr_diff < 0:
                st.info("**轻微影响**: 风机对信噪比影响较小，基本在可接受范围内")
            else:
                st.success("**无负面影响**: 风机未对信噪比产生负面影响")
        
        with subtab2:
            st.subheader("接收功率对比分析")
            
            # 创建图表
            fig_power = go.Figure()
            
            fig_power.add_trace(go.Scatter(
                x=comparison['distances_km'],
                y=comparison['received_power_without_turbines'],
                mode='lines',
                name='无风机',
                line=dict(color=COLOR_SCHEME['info'], width=3),
                hovertemplate='距离: %{x:.1f}km<br>功率: %{y:.1f}dB<extra></extra>'
            ))
            
            fig_power.add_trace(go.Scatter(
                x=comparison['distances_km'],
                y=comparison['received_power_with_turbines'],
                mode='lines',
                name='有风机',
                line=dict(color=COLOR_SCHEME['accent'], width=3, dash='dash'),
                hovertemplate='距离: %{x:.1f}km<br>功率: %{y:.1f}dB<extra></extra>'
            ))
            
            fig_power.update_layout(
                title=dict(
                    text="有/无风机条件下接收功率对比",
                    font=dict(size=16, color=COLOR_SCHEME['primary']),
                    x=0.5
                ),
                xaxis_title=dict(
                    text="距离 (km)",
                    font=dict(color=COLOR_SCHEME['light'])
                ),
                yaxis_title=dict(
                    text="接收功率 (dB)",
                    font=dict(color=COLOR_SCHEME['light'])
                ),
                plot_bgcolor='rgba(20, 25, 50, 0.1)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLOR_SCHEME['light']),
                hovermode='x unified',
                height=500,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(30, 30, 50, 0.7)',
                    bordercolor=COLOR_SCHEME['primary'],
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig_power, width='stretch')
            
            # 功率损失分析
            col_power1, col_power2, col_power3, col_power4 = st.columns(4)
            
            with col_power1:
                power_without_mean = np.mean(comparison['received_power_without_turbines'])
                st.metric("无风机平均功率", f"{power_without_mean:.1f} dB")
            
            with col_power2:
                power_with_mean = np.mean(comparison['received_power_with_turbines'])
                st.metric("有风机平均功率", f"{power_with_mean:.1f} dB")
            
            with col_power3:
                power_loss = power_with_mean - power_without_mean
                st.metric("功率损失", f"{power_loss:.1f} dB")
            
            with col_power4:
                # 计算有效探测距离
                threshold_snr = 13
                try:
                    # 找到SNR高于门限的最远距离
                    valid_distances_without = [d for d, s in zip(comparison['distances_km'], comparison['snr_without_turbines']) if s >= threshold_snr]
                    valid_distances_with = [d for d, s in zip(comparison['distances_km'], comparison['snr_with_turbines']) if s >= threshold_snr]
                    
                    max_range_without = max(valid_distances_without) if valid_distances_without else 0
                    max_range_with = max(valid_distances_with) if valid_distances_with else 0
                    
                    st.metric("探测距离损失", f"{max_range_without - max_range_with:.1f} km")
                except:
                    st.metric("探测距离损失", "N/A")
        
        with subtab3:
            st.subheader("检测概率对比分析")
            
            # 创建图表
            fig_prob = go.Figure()
            
            fig_prob.add_trace(go.Scatter(
                x=comparison['distances_km'],
                y=[p * 100 for p in comparison['detection_prob_without_turbines']],
                mode='lines',
                name='无风机',
                line=dict(color=COLOR_SCHEME['success'], width=3),
                hovertemplate='距离: %{x:.1f}km<br>检测概率: %{y:.1f}%<extra></extra>'
            ))
            
            fig_prob.add_trace(go.Scatter(
                x=comparison['distances_km'],
                y=[p * 100 for p in comparison['detection_prob_with_turbines']],
                mode='lines',
                name='有风机',
                line=dict(color=COLOR_SCHEME['warning'], width=3, dash='dash'),
                hovertemplate='距离: %{x:.1f}km<br>检测概率: %{y:.1f}%<extra></extra>'
            ))
            
            # 添加90%检测概率线
            fig_prob.add_hline(
                y=90,
                line_dash="dot",
                line_color="green",
                annotation_text="高检测概率 (90%)",
                annotation_position="top right"
            )
            
            # 添加50%检测概率线
            fig_prob.add_hline(
                y=50,
                line_dash="dot",
                line_color="orange",
                annotation_text="中等检测概率 (50%)",
                annotation_position="top right"
            )
            
            fig_prob.update_layout(
                title=dict(
                    text="有/无风机条件下检测概率对比",
                    font=dict(size=16, color=COLOR_SCHEME['primary']),
                    x=0.5
                ),
                xaxis_title=dict(
                    text="距离 (km)",
                    font=dict(color=COLOR_SCHEME['light'])
                ),
                yaxis_title=dict(
                    text="检测概率 (%)",
                    font=dict(color=COLOR_SCHEME['light'])
                ),
                plot_bgcolor='rgba(20, 25, 50, 0.1)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLOR_SCHEME['light']),
                hovermode='x unified',
                height=500,
                yaxis_range=[0, 105],
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(30, 30, 50, 0.7)',
                    bordercolor=COLOR_SCHEME['primary'],
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig_prob, width='stretch')
            
            # 检测概率分析
            col_prob1, col_prob2, col_prob3, col_prob4 = st.columns(4)
            
            with col_prob1:
                prob_without_mean = np.mean(comparison['detection_prob_without_turbines']) * 100
                st.metric("无风机平均检测概率", f"{prob_without_mean:.1f}%")
            
            with col_prob2:
                prob_with_mean = np.mean(comparison['detection_prob_with_turbines']) * 100
                st.metric("有风机平均检测概率", f"{prob_with_mean:.1f}%")
            
            with col_prob3:
                prob_diff = (prob_with_mean - prob_without_mean)
                st.metric("检测概率差值", f"{prob_diff:.1f}%")
            
            with col_prob4:
                # 计算有效检测距离
                try:
                    distances = comparison['distances_km']
                    probs_without = comparison['detection_prob_without_turbines']
                    probs_with = comparison['detection_prob_with_turbines']
                    
                    # 找到检测概率>90%的距离
                    high_prob_dist_without = max([d for d, p in zip(distances, probs_without) if p >= 0.9], default=0)
                    high_prob_dist_with = max([d for d, p in zip(distances, probs_with) if p >= 0.9], default=0)
                    
                    st.metric("高检测概率距离损失", f"{high_prob_dist_without - high_prob_dist_with:.1f} km")
                except:
                    st.metric("高检测概率距离损失", "N/A")
        
        with subtab4:
            st.subheader("多径效应对比分析")
            
            # 创建多图表
            fig_multipath = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "多径损耗对比", 
                    "路径差分析",
                    "干涉图样分析", 
                    "影响程度评估"
                ),
                vertical_spacing=0.15,
                horizontal_spacing=0.15
            )
            
            # 1. 多径损耗对比
            fig_multipath.add_trace(
                go.Scatter(
                    x=comparison['distances_km'],
                    y=comparison['multipath_loss_without_turbines'],
                    mode='lines',
                    name='无风机',
                    line=dict(color=COLOR_SCHEME['info'], width=2)
                ),
                row=1, col=1
            )
            
            fig_multipath.add_trace(
                go.Scatter(
                    x=comparison['distances_km'],
                    y=comparison['multipath_loss_with_turbines'],
                    mode='lines',
                    name='有风机',
                    line=dict(color=COLOR_SCHEME['accent'], width=2, dash='dash')
                ),
                row=1, col=1
            )
            
            # 2. 路径差分析（模拟数据）
            path_difference = [d * 0.1 for d in comparison['distances_km']]  # 模拟数据
            fig_multipath.add_trace(
                go.Scatter(
                    x=comparison['distances_km'],
                    y=path_difference,
                    mode='lines',
                    name='路径差',
                    line=dict(color=COLOR_SCHEME['warning'], width=2)
                ),
                row=1, col=2
            )
            
            # 3. 干涉图样分析（模拟数据）
            interference_pattern = [1 + 0.5 * np.sin(d/10) for d in comparison['distances_km']]  # 模拟数据
            fig_multipath.add_trace(
                go.Scatter(
                    x=comparison['distances_km'],
                    y=interference_pattern,
                    mode='lines',
                    name='干涉图样',
                    line=dict(color=COLOR_SCHEME['primary'], width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0, 204, 255, 0.2)'
                ),
                row=2, col=1
            )
            
            # 4. 影响程度评估
            impact_levels = []
            for loss_with, loss_without in zip(comparison['multipath_loss_with_turbines'], 
                                              comparison['multipath_loss_without_turbines']):
                loss_diff = abs(loss_with - loss_without)
                if loss_diff > 3:
                    impact_levels.append(3)  # 高影响
                elif loss_diff > 1:
                    impact_levels.append(2)  # 中影响
                else:
                    impact_levels.append(1)  # 低影响
            
            fig_multipath.add_trace(
                go.Histogram(
                    x=impact_levels,
                    name='影响程度分布',
                    marker_color=COLOR_SCHEME['warning'],
                    nbinsx=3
                ),
                row=2, col=2
            )
            
            # 更新布局
            fig_multipath.update_layout(
                title=dict(
                    text="多径效应综合分析",
                    font=dict(size=18, color=COLOR_SCHEME['primary']),
                    x=0.5
                ),
                plot_bgcolor='rgba(20, 25, 50, 0.1)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLOR_SCHEME['light']),
                height=700,
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(30, 30, 50, 0.7)',
                    bordercolor=COLOR_SCHEME['primary'],
                    borderwidth=1
                )
            )
            
            # 更新子图轴标签
            fig_multipath.update_xaxes(title_text="距离 (km)", row=1, col=1)
            fig_multipath.update_yaxes(title_text="多径损耗 (dB)", row=1, col=1)
            
            fig_multipath.update_xaxes(title_text="距离 (km)", row=1, col=2)
            fig_multipath.update_yaxes(title_text="路径差 (m)", row=1, col=2)
            
            fig_multipath.update_xaxes(title_text="距离 (km)", row=2, col=1)
            fig_multipath.update_yaxes(title_text="干涉强度", row=2, col=1)
            
            fig_multipath.update_xaxes(title_text="影响等级", row=2, col=2)
            fig_multipath.update_yaxes(title_text="频数", row=2, col=2)
            
            st.plotly_chart(fig_multipath, width='stretch')
            
            # 多径效应分析
            st.markdown("### 📊 多径效应分析解读")
            
            col_mp1, col_mp2, col_mp3 = st.columns(3)
            
            with col_mp1:
                avg_loss_without = np.mean(comparison['multipath_loss_without_turbines'])
                st.metric("无风机平均多径损耗", f"{avg_loss_without:.1f} dB")
            
            with col_mp2:
                avg_loss_with = np.mean(comparison['multipath_loss_with_turbines'])
                st.metric("有风机平均多径损耗", f"{avg_loss_with:.1f} dB")
            
            with col_mp3:
                max_loss_diff = max([abs(w - wo) for w, wo in 
                                   zip(comparison['multipath_loss_with_turbines'], 
                                       comparison['multipath_loss_without_turbines'])])
                st.metric("最大多径损耗差异", f"{max_loss_diff:.1f} dB")

with tab3:
    st.header("目标详细分析")
    
    if not st.session_state.get('calculation_complete', False):
        st.warning("请先进行性能分析")
    else:
        results = st.session_state.analysis_results
        comparison = results['comparison_results']
        analysis_config = st.session_state.get('analysis_config', {})
        
        # 获取选中的雷达和目标
        selected_radar = analysis_config.get('selected_radar', {})
        selected_target = analysis_config.get('selected_target', {})
        
        col_target_info1, col_target_info2 = st.columns(2)
        
        with col_target_info1:
            st.subheader("雷达信息")
            st.write(f"**ID**: {selected_radar.get('id', '')}")
            st.write(f"**类型**: {selected_radar.get('type', '')}")
            st.write(f"**频段**: {selected_radar.get('frequency_band', '')}")
            st.write(f"**峰值功率**: {selected_radar.get('peak_power', 0) / 1000:.0f} kW")
            st.write(f"**天线增益**: {selected_radar.get('antenna_gain', 0)} dBi")
        
        with col_target_info2:
            st.subheader("目标信息")
            st.write(f"**ID**: {selected_target.get('id', '')}")
            st.write(f"**类型**: {selected_target.get('type', '')}")
            st.write(f"**RCS**: {selected_target.get('rcs', 0)} m²")
            st.write(f"**速度**: {selected_target.get('speed', 0)} m/s")
            st.write(f"**高度**: {selected_target.get('position', {}).get('alt', 0):.0f} m")
        
        st.markdown("---")
        
        # 多普勒分析
        st.subheader("多普勒分析")
        
        # 计算多普勒频移
        radar_freq_ghz = selected_radar.get('frequency_ghz', 3.0)
        if not radar_freq_ghz:
            # 从频段估算频率
            band = selected_radar.get('frequency_band', 'S')
            band_info = RADAR_FREQUENCY_BANDS.get(band, {})
            radar_freq_ghz = (band_info.get('freq_min', 2) + band_info.get('freq_max', 4)) / 2
        
        target_speed = selected_target.get('speed', 0)
        doppler_freq_hz = calculator.calculate_doppler_frequency(radar_freq_ghz, target_speed)
        
        col_doppler1, col_doppler2, col_doppler3 = st.columns(3)
        
        with col_doppler1:
            st.metric("雷达频率", f"{radar_freq_ghz} GHz")
        
        with col_doppler2:
            st.metric("目标速度", f"{target_speed} m/s")
        
        with col_doppler3:
            st.metric("多普勒频移", f"{doppler_freq_hz:.1f} Hz")
        
        # 多普勒频谱图
        st.markdown("### 多普勒频谱")
        
        # 生成模拟频谱数据
        freq_range = np.linspace(-doppler_freq_hz*2, doppler_freq_hz*2, 100)
        spectrum = np.exp(-((freq_range - doppler_freq_hz)**2) / (2*(doppler_freq_hz/3)**2))
        
        fig_doppler = go.Figure()
        
        fig_doppler.add_trace(go.Scatter(
            x=freq_range,
            y=spectrum,
            mode='lines',
            name='多普勒频谱',
            line=dict(color=COLOR_SCHEME['primary'], width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 204, 255, 0.2)'
        ))
        
        # 标记目标多普勒频率
        fig_doppler.add_vline(
            x=doppler_freq_hz,
            line_dash="dash",
            line_color=COLOR_SCHEME['warning'],
            annotation_text=f"目标: {doppler_freq_hz:.1f}Hz",
            annotation_position="top right"
        )
        
        fig_doppler.update_layout(
            title=dict(
                text="目标多普勒频谱",
                font=dict(size=16, color=COLOR_SCHEME['primary']),
                x=0.5
            ),
            xaxis_title=dict(
                text="频率 (Hz)",
                font=dict(color=COLOR_SCHEME['light'])
            ),
            yaxis_title=dict(
                text="幅度",
                font=dict(color=COLOR_SCHEME['light'])
            ),
            plot_bgcolor='rgba(20, 25, 50, 0.1)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_SCHEME['light']),
            height=400
        )
        
        st.plotly_chart(fig_doppler, width='stretch')
        
        st.markdown("---")
        
        # 距离-速度分析
        st.subheader("距离-速度分析")
        
        # 生成距离-速度网格
        ranges = np.array(comparison['distances_km'])
        velocities = np.linspace(-500, 500, 50)  # m/s
        
        # 计算每个距离-速度点的SNR
        snr_grid = []
        for r in ranges:
            r_m = r * 1000
            row = []
            for v in velocities:
                # 简化计算：SNR随距离增加而减小，速度影响多普勒
                base_snr = 30 - 20 * np.log10(r)  # 简化模型
                doppler_factor = np.exp(-((v - target_speed)**2) / (2 * 100**2))
                snr = base_snr + 10 * np.log10(doppler_factor + 1e-6)
                row.append(max(snr, 0))
            snr_grid.append(row)
        
        fig_range_vel = go.Figure(data=
            go.Contour(
                z=snr_grid,
                x=velocities,
                y=ranges,
                colorscale='Viridis',
                contours=dict(
                    showlabels=True,
                    labelfont=dict(size=12, color='white')
                ),
                colorbar=dict(
                    title="SNR (dB)"
                )
            )
        )
        
        # 标记目标位置
        fig_range_vel.add_trace(go.Scatter(
            x=[target_speed],
            y=[selected_target.get('position', {}).get('distance_km', 100)],
            mode='markers',
            name='目标位置',
            marker=dict(
                size=15,
                color=COLOR_SCHEME['warning'],
                symbol='star',
                line=dict(width=2, color='white')
            )
        ))
        
        fig_range_vel.update_layout(
            title=dict(
                text="距离-速度平面SNR分布",
                font=dict(size=16, color=COLOR_SCHEME['primary']),
                x=0.5
            ),
            xaxis_title=dict(
                text="径向速度 (m/s)",
                font=dict(color=COLOR_SCHEME['light'])
            ),
            yaxis_title=dict(
                text="距离 (km)",
                font=dict(color=COLOR_SCHEME['light'])
            ),
            plot_bgcolor='rgba(20, 25, 50, 0.1)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_SCHEME['light']),
            height=500
        )
        
        st.plotly_chart(fig_range_vel, width='stretch')

with tab4:
    st.header("综合分析报告")
    
    if not st.session_state.get('calculation_complete', False):
        st.warning("请先进行性能分析")
    else:
        results = st.session_state.analysis_results
        
        # 性能指标汇总
        st.subheader("性能指标汇总")
        
        performance = results.get('performance_metrics', {})
        comparison = results.get('scenario_comparison', {})
        
        col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
        
        with col_perf1:
            detection_perf = performance.get('detection_performance', '未知')
            color = "green" if detection_perf == "可检测" else "orange" if detection_perf == "可检测但跟踪困难" else "red"
            st.metric("检测性能", detection_perf)
        
        with col_perf2:
            tracking_cap = performance.get('tracking_capability', '未知')
            color = "green" if tracking_cap == "可跟踪" else "orange" if tracking_cap == "可检测但跟踪困难" else "red"
            st.metric("跟踪能力", tracking_cap)
        
        with col_perf3:
            range_res = performance.get('range_resolution_quality', '未知')
            color = "green" if range_res == "高" else "orange" if range_res == "中" else "red"
            st.metric("距离分辨率", range_res)
        
        with col_perf4:
            interference = performance.get('interference_impact', '未知')
            color = "green" if interference == "轻微" else "orange" if interference == "中等" else "red"
            st.metric("干扰影响", interference)
        
        st.markdown("---")
        
        # 影响评估
        st.subheader("影响评估")
        
        # 创建影响评估表格
        impact_data = []
        
        metrics = [
            ("信噪比", comparison.get('snr_db_percent_change', 0)),
            ("检测概率", comparison.get('detection_probability_percent_change', 0)),
            ("多径损耗", comparison.get('multipath_loss_db_percent_change', 0))
        ]
        
        for name, change in metrics:
            abs_change = abs(change)
            if abs_change > 20:
                level = "严重"
                color = "🔴"
            elif abs_change > 10:
                level = "显著"
                color = "🟡"
            elif abs_change > 5:
                level = "中等"
                color = "🟠"
            else:
                level = "轻微"
                color = "🟢"
            
            impact_data.append({
                "指标": name,
                "变化率": f"{change:+.1f}%",
                "影响程度": level,
                "等级": color
            })
        
        impact_df = pd.DataFrame(impact_data)
        st.dataframe(impact_df, width='stretch', hide_index=True)
        
        st.markdown("---")
        
        # 建议措施
        st.subheader("建议措施")
        
        recommendations = performance.get('recommendations', [])
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                st.info(f"{i}. {rec}")
        else:
            st.info("基于当前分析结果，系统运行状况良好，无需特殊建议")
        
        st.markdown("---")
        
        # 导出选项
        st.subheader("导出分析结果")
        
        col_export1, col_export2, col_export3 = st.columns(3)
        
        with col_export1:
            if st.button("📊 导出数据表格", width='stretch'):
                # 准备导出数据
                export_data = {
                    '分析配置': st.session_state.analysis_config,
                    '性能指标': performance,
                    '场景对比': comparison
                }
                
                # 转换为DataFrame
                dfs = []
                for key, data in export_data.items():
                    if isinstance(data, dict):
                        df = pd.DataFrame(list(data.items()), columns=['参数', '值'])
                        dfs.append((key, df))
                
                # 创建Excel文件
                import io
                buffer = io.BytesIO()
                
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    for sheet_name, df in dfs:
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                    
                    # 添加详细数据
                    if 'comparison_results' in results:
                        comp_data = results['comparison_results']
                        for key, values in comp_data.items():
                            if isinstance(values, list):
                                pd.DataFrame({key: values}).to_excel(
                                    writer, sheet_name=f"详细数据_{key}"[:31], index=False
                                )
                
                buffer.seek(0)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 下载Excel文件",
                    data=buffer,
                    file_name=f"雷达性能分析_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col_export2:
            if st.button("📈 导出分析图表", width='stretch'):
                st.info("图表导出功能开发中...")
        
        with col_export3:
            if st.button("📄 生成详细报告", width='stretch'):
                st.info("详细报告生成功能在报告生成页面可用")
                if st.button("前往报告生成页面"):
                    st.switch_page("pages/4_报告生成.py")

# 侧边栏
with st.sidebar:
    st.markdown("## 📊 分析状态")
    
    if st.session_state.get('calculation_complete', False):
        st.success("✅ 分析已完成")
        
        # 显示分析时间
        if 'analysis_results' in st.session_state:
            results = st.session_state.analysis_results
            analysis_time = results.get('analysis_time', '未知')
            st.info(f"分析时间: {analysis_time}")
        
        # 显示分析配置
        if 'analysis_config' in st.session_state:
            config = st.session_state.analysis_config
            st.info(f"分析距离: {config.get('min_range_km', 0)}-{config.get('max_range_km', 0)} km")
            st.info(f"分析点数: {config.get('range_steps', 0)}")
        
        # 快速查看关键指标
        st.markdown("### 🎯 关键指标")
        
        if 'analysis_results' in st.session_state:
            results = st.session_state.analysis_results
            comparison = results.get('scenario_comparison', {})
            
            snr_change = comparison.get('snr_db_percent_change', 0)
            detection_change = comparison.get('detection_probability_percent_change', 0)
            
            col_metric1, col_metric2 = st.columns(2)
            
            with col_metric1:
                st.metric("SNR变化", f"{snr_change:+.1f}%")
            
            with col_metric2:
                st.metric("检测概率变化", f"{detection_change:+.1f}%")
    
    else:
        st.warning("⚠️ 未进行分析")
    
    st.markdown("---")
    
    # 快速操作
    st.markdown("## ⚡ 快速操作")
    
    if st.button("🔄 重新分析", width='stretch'):
        st.session_state.calculation_complete = False
        st.session_state.analysis_results = None
        st.rerun()
    
    if st.button("🧹 清除结果", width='stretch', type="secondary"):
        st.session_state.calculation_complete = False
        st.session_state.analysis_results = None
        st.session_state.analysis_progress = 0
        st.rerun()
    
    st.markdown("---")
    
    # 导航
    st.markdown("## 🧭 页面导航")
    
    if st.button("📁 场景配置", width='stretch'):
        st.switch_page("pages/1_场景配置.py")
    
    if st.button("🗺️ 场景可视化", width='stretch'):
        st.switch_page("pages/2_场景可视化.py")
    
    if st.button("📊 报告生成", width='stretch'):
        st.switch_page("pages/4_报告生成.py")

# 页脚
st.markdown("---")
st.caption("风电雷达影响评估系统 | 雷达性能分析模块")