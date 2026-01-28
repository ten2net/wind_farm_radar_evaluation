import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
import time
import os
import itertools
import zipfile
import json
import shutil
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

# 页面配置
st.set_page_config(
    page_title="海上风电雷达影响专业分析系统",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置plotly中文字体
import plotly.io as pio
pio.templates["plotly_white"].layout.font = dict(family="SimHei, Arial, sans-serif", size=12)
# 设置默认模板为plotly_white，确保所有图表都使用中文字体
pio.templates.default = "plotly_white"
print("[页面初始化] Plotly中文字体已设置为SimHei，默认模板已设置")

# 自定义CSS样式 - 优化布局
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
        padding: 1rem;
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%);
        border-radius: 10px;
        color: white;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2e86ab;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        text-align: center;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-medium { color: #ffa500; font-weight: bold; }
    .risk-low { color: #32cd32; font-weight: bold; }
    .simulation-control {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    .impact-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem;
        text-align: center;
    }
    .turbine-comparison {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class AdvancedRadarImpactAnalyzer:
    """高级雷达影响分析器 - 包含多径效应评估"""
    
    def __init__(self):
        self.radar_bands = {
            "L波段": {"freq": 1.5e9, "wavelength": 0.2, "description": "远程警戒雷达"},
            "S波段": {"freq": 3.0e9, "wavelength": 0.1, "description": "中程监视雷达"}, 
            "C波段": {"freq": 5.6e9, "wavelength": 0.054, "description": "气象雷达"},
            "X波段": {"freq": 9.4e9, "wavelength": 0.032, "description": "海事雷达"},
            "Ku波段": {"freq": 15.0e9, "wavelength": 0.02, "description": "高精度雷达"}
        }
        
    def calculate_shadowing_effect(self, turbine_height, target_height, distance, num_turbines=1):
        """计算遮挡效应 - 基于几何光学理论"""
        # 简化的阴影区域计算
        shadow_zone_angle = np.degrees(np.arctan(turbine_height / distance))
        
        # 多风机遮挡叠加效应
        shadow_factor = min(1.0, 0.3 + 0.2 * np.log10(num_turbines))
        
        # 高度差影响
        height_factor = max(0.1, 1 - abs(target_height - turbine_height) / (2 * turbine_height))
        
        shadow_loss_db = 20 * shadow_factor * height_factor
        
        return {
            'shadow_zone_angle': shadow_zone_angle,
            'shadow_loss_db': shadow_loss_db,
            'is_in_shadow': target_height < turbine_height
        }
    
    def calculate_scattering_effect(self, radar_band, turbine_distance, incidence_angle, num_turbines=1):
        """计算散射效应 - 基于雷达截面积模型"""
        wavelength = self.radar_bands[radar_band]["wavelength"]
        freq = self.radar_bands[radar_band]["freq"]
        
        # 基础RCS模型（简化）
        base_rcs = 1000  # 平方米，典型风机RCS
        incidence_factor = np.cos(np.radians(incidence_angle))**2
        
        # 距离衰减
        distance_factor = 1 / (1 + (turbine_distance / 5)**2)
        
        # 频率相关散射
        freq_factor = (freq / 1e9)**2
        
        effective_rcs = base_rcs * incidence_factor * distance_factor * freq_factor
        
        # 多风机散射叠加（非相干叠加）
        scattering_power = effective_rcs * min(num_turbines, 10)  # 限制最大影响
        
        scattering_loss_db = 10 * np.log10(1 + scattering_power / 1000)
        
        return {
            'effective_rcs': effective_rcs,
            'scattering_loss_db': scattering_loss_db,
            'scattering_power': scattering_power
        }
    
    def calculate_diffraction_effect(self, radar_band, turbine_distance, turbine_height, num_turbines=1):
        """计算绕射效应 - 基于刃形绕射模型"""
        wavelength = self.radar_bands[radar_band]["wavelength"]
        
        # 刃形绕射参数
        v_parameter = turbine_height * np.sqrt(2 / (wavelength * turbine_distance * 1000))
        
        # 绕射损耗计算（简化模型）
        if v_parameter > -0.8:
            diffraction_loss_db = 6.9 + 20 * np.log10(np.sqrt((v_parameter - 0.1)**2 + 1) + v_parameter - 0.1)
        else:
            diffraction_loss_db = 0
        
        # 多风机绕射效应（近似为最差情况）
        multi_turbine_factor = 1 + 0.1 * np.log(num_turbines)
        total_diffraction_loss = diffraction_loss_db * multi_turbine_factor
        
        return {
            'diffraction_parameter': v_parameter,
            'diffraction_loss_db': total_diffraction_loss,
            'fresnel_zone_clearance': self.calculate_fresnel_zone(turbine_distance, wavelength)
        }
    
    def calculate_fresnel_zone(self, distance, wavelength):
        """计算菲涅耳区半径"""
        return np.sqrt(wavelength * distance * 1000 / 2)
    
    def calculate_doppler_effects(self, freq, target_speed, blade_speed=15, num_blades=3, num_turbines=1):
        """计算多普勒频移效应 - 包括叶片旋转影响"""
        # 目标多普勒
        wavelength = 3e8 / freq
        target_doppler = 2 * target_speed / wavelength
        
        # 叶片旋转多普勒（微多普勒效应）
        blade_tip_speed = blade_speed  # m/s
        blade_doppler_max = 2 * blade_tip_speed / wavelength
        
        # 多风机多普勒扩展
        doppler_spread = blade_doppler_max * np.sqrt(num_turbines)
        
        return {
            'target_doppler_hz': target_doppler,
            'blade_doppler_max_hz': blade_doppler_max,
            'doppler_spread_hz': doppler_spread,
            'velocity_measurement_error': 0.1 * doppler_spread * wavelength / 2
        }
    
    def calculate_angle_measurement_error(self, radar_band, turbine_distance, incidence_angle, num_turbines=1):
        """计算测角偏差 - 基于多径效应模型"""
        wavelength = self.radar_bands[radar_band]["wavelength"]
        
        # 多径引起的测角误差
        multipath_phase_shift = 2 * np.pi * turbine_distance * 1000 / wavelength * np.sin(np.radians(incidence_angle))
        angle_error_deg = np.degrees(wavelength / (4 * np.pi * turbine_distance * 1000)) * 10
        
        # 多风机导致的误差累积
        multi_turbine_error = angle_error_deg * np.sqrt(min(num_turbines, 5))
        
        return {
            'angle_error_deg': multi_turbine_error,
            'multipath_phase_shift': multipath_phase_shift,
            'bearing_accuracy_loss': min(1.0, multi_turbine_error / 10)
        }
    
    def calculate_range_measurement_error(self, radar_band, turbine_distance, num_turbines=1):
        """计算测距偏差"""
        wavelength = self.radar_bands[radar_band]["wavelength"]
        
        # 多径时延导致的测距误差
        range_error = wavelength * 0.01 * np.log(1 + turbine_distance) * np.sqrt(num_turbines)
        
        return {
            'range_error_m': range_error,
            'range_resolution_degradation': min(0.5, 0.1 * np.log(1 + num_turbines))
        }
    
    def calculate_velocity_measurement_error(self, doppler_spread, target_velocity, num_turbines=1):
        """计算测速偏差"""
        # 多普勒扩展导致的测速误差
        velocity_error = doppler_spread * 0.1 * np.sqrt(num_turbines)
        measurement_accuracy_loss = min(0.3, 0.05 * num_turbines)
        
        return {
            'velocity_error_ms': velocity_error,
            'measurement_accuracy_loss': measurement_accuracy_loss
        }
    
    def calculate_multipath_effects(self, radar_band, turbine_distance, turbine_height, 
                                   incidence_angle, num_turbines=1):
        """计算多径效应综合影响"""
        wavelength = self.radar_bands[radar_band]["wavelength"]
        
        # 1. 多径时延计算
        path_difference = 2 * turbine_distance * 1000 * np.sin(np.radians(incidence_angle))
        time_delay = path_difference / 3e8  # 秒
        
        # 2. 多径衰落深度（瑞利衰落模型简化）
        multipath_fading_depth = 20 * np.log10(1 + 0.5 * np.sqrt(num_turbines))
        
        # 3. 时延扩展（多风机导致的多径扩展）
        delay_spread = time_delay * np.sqrt(num_turbines) * 1e6  # 转换为μs
        
        # 4. 相干带宽
        coherence_bandwidth = 1 / (2 * np.pi * delay_spread * 1e-6) / 1e6  # MHz
        
        # 5. 码间干扰影响（对数字信号）
        symbol_rate = 1e6  # 假设1Mbps
        isi_impact = delay_spread * 1e-6 * symbol_rate  # 时延扩展与码元周期比
        
        return {
            'multipath_time_delay': time_delay,
            'multipath_fading_depth_db': multipath_fading_depth,
            'delay_spread_us': delay_spread,
            'coherence_bandwidth_mhz': coherence_bandwidth,
            'isi_impact_factor': isi_impact,
            'is_frequency_selective': coherence_bandwidth < 10  # 相干带宽小于10MHz为频率选择性衰落
        }
    
    def evaluate_single_vs_multiple_turbines(self, base_params, num_turbines_list=None):
        """比较单个风机与多个风机的影响"""
        # 如果未提供列表，则生成从1到max_turbines的所有整数
        if num_turbines_list is None:
            max_turbines = base_params.get('max_turbines', 30)
            num_turbines_list = list(range(1, max_turbines + 1))
        
        results = []
        
        for num_turbines in num_turbines_list:
            # 计算各项指标
            shadowing = self.calculate_shadowing_effect(
                base_params['turbine_height'], 
                base_params['target_height'],
                base_params['turbine_distance'],
                num_turbines
            )
            
            scattering = self.calculate_scattering_effect(
                base_params['radar_band'],
                base_params['turbine_distance'],
                base_params['incidence_angle'],
                num_turbines
            )
            
            diffraction = self.calculate_diffraction_effect(
                base_params['radar_band'],
                base_params['turbine_distance'],
                base_params['turbine_height'],
                num_turbines
            )
            
            doppler = self.calculate_doppler_effects(
                self.radar_bands[base_params['radar_band']]["freq"],
                base_params['target_speed'],
                num_turbines=num_turbines
            )
            
            angle_error = self.calculate_angle_measurement_error(
                base_params['radar_band'],
                base_params['turbine_distance'],
                base_params['incidence_angle'],
                num_turbines
            )
            
            range_error = self.calculate_range_measurement_error(
                base_params['radar_band'],
                base_params['turbine_distance'],
                num_turbines
            )
            
            velocity_error = self.calculate_velocity_measurement_error(
                doppler['doppler_spread_hz'],
                base_params['target_speed'],
                num_turbines
            )
            
            # 新增：多径效应计算
            multipath = self.calculate_multipath_effects(
                base_params['radar_band'],
                base_params['turbine_distance'],
                base_params['turbine_height'],
                base_params['incidence_angle'],
                num_turbines
            )
            
            # 综合影响评分（调整权重，增加多径效应权重）
            total_impact_score = (
                shadowing['shadow_loss_db'] * 0.15 +  # 调整权重
                scattering['scattering_loss_db'] * 0.2 +
                diffraction['diffraction_loss_db'] * 0.1 +
                abs(doppler['velocity_measurement_error']) * 0.1 +
                angle_error['angle_error_deg'] * 0.1 +
                range_error['range_error_m'] * 0.1 +
                velocity_error['velocity_error_ms'] * 0.05 +
                multipath['multipath_fading_depth_db'] * 0.2  # 新增多径效应权重
            )
            
            result = {
                '风机数量': num_turbines,
                '遮挡损耗_db': shadowing['shadow_loss_db'],
                '散射损耗_db': scattering['scattering_loss_db'],
                '绕射损耗_db': diffraction['diffraction_loss_db'],
                '多普勒扩展_Hz': doppler['doppler_spread_hz'],
                '测角误差_度': angle_error['angle_error_deg'],
                '测距误差_m': range_error['range_error_m'],
                '测速误差_m/s': velocity_error['velocity_error_ms'],
                # 新增多径效应指标
                '多径衰落_db': multipath['multipath_fading_depth_db'],
                '时延扩展_μs': multipath['delay_spread_us'],
                '相干带宽_MHz': multipath['coherence_bandwidth_mhz'],
                'ISI影响因子': multipath['isi_impact_factor'],
                '总影响评分': total_impact_score,
                '探测概率降低': min(0.8, total_impact_score * 0.1)
            }
            
            results.append(result)
        
        return pd.DataFrame(results)

class EnhancedSimulationEngine:
    """增强型仿真引擎 - 支持多风机影响分析"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.comparison_data = pd.DataFrame()
    
    def run_turbine_comparison_analysis(self, base_params):
        """运行单风机vs多风机对比分析"""
        st.info("🔬 开始单风机与多风机影响对比分析...")
        
        # 运行对比分析
        self.comparison_data = self.analyzer.evaluate_single_vs_multiple_turbines(base_params)
        
        return self.comparison_data

def create_turbine_comparison_interface(analyzer, params):
    """创建风机数量对比分析界面"""
    st.markdown('<div class="section-header">🔬 单风机 vs 多风机影响对比分析</div>', unsafe_allow_html=True)
    
    # 初始化仿真引擎
    sim_engine = EnhancedSimulationEngine(analyzer)
    
    # 控制面板
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        run_comparison = st.button("🔄 运行对比分析", type="primary", width='stretch')
    
    with col2:
        show_details = st.checkbox("显示详细数据", value=True)
    
    with col3:
        if 'comparison_data' in st.session_state:
            csv_data = st.session_state.comparison_data.to_csv(index=False)
            st.download_button(
                label="📥 下载对比数据",
                data=csv_data,
                file_name="turbine_comparison_analysis.csv",
                mime="text/csv",
                width='stretch'
            )
    
    if run_comparison:
        with st.spinner("正在进行单风机与多风机影响对比分析..."):
            comparison_data = sim_engine.run_turbine_comparison_analysis(params)
            st.session_state.comparison_data = comparison_data
            st.success("对比分析完成！")
    
    if 'comparison_data' in st.session_state:
        comparison_data = st.session_state.comparison_data
        
        # 关键指标概览
        st.markdown("### 📊 影响指标概览")
        cols = st.columns(6)
        metrics = [
            ('风机数量范围', f"{comparison_data['风机数量'].min()}-{comparison_data['风机数量'].max()}"),
            ('最大遮挡损耗', f"{comparison_data['遮挡损耗_db'].max():.1f} dB"),
            ('最大散射损耗', f"{comparison_data['散射损耗_db'].max():.1f} dB"),
            ('最大多径衰落', f"{comparison_data['多径衰落_db'].max():.1f} dB"),
            ('最大测角误差', f"{comparison_data['测角误差_度'].max():.2f}°"),
            ('总影响评分', f"{comparison_data['总影响评分'].max():.1f}")
        ]
        
        for col, (label, value) in zip(cols, metrics):
            with col:
                st.metric(label, value)
        
        # 详细分析标签页
        tab1, tab2, tab3, tab4 = st.tabs(["📈 综合影响趋势", "🔧 单项指标分析", "📊 数据对比", "🎯 风险评估"])
        
        with tab1:
            create_comprehensive_impact_analysis(comparison_data)
        
        with tab2:
            create_individual_metric_analysis(comparison_data)
        
        with tab3:
            create_data_comparison_view(comparison_data)
        
        with tab4:
            create_risk_assessment_view(comparison_data, params)
        
        if show_details:
            st.markdown("### 📋 详细数据")
            st.dataframe(comparison_data, width='stretch')

def create_comprehensive_impact_analysis(comparison_data):
    """创建综合影响趋势分析"""
    st.markdown("#### 📊 各项指标随风机数量变化趋势")
    
    # 选择要显示的指标
    metrics_options = {
        '遮挡损耗 (dB)': '遮挡损耗_db',
        '散射损耗 (dB)': '散射损耗_db', 
        '绕射损耗 (dB)': '绕射损耗_db',
        '多普勒扩展 (Hz)': '多普勒扩展_Hz',
        '测角误差 (°)': '测角误差_度',
        '测距误差 (m)': '测距误差_m',
        '测速误差 (m/s)': '测速误差_m/s',
        '多径衰落 (dB)': '多径衰落_db',
        '总影响评分': '总影响评分'
    }
    
    selected_metrics = st.multiselect(
        "选择分析指标",
        list(metrics_options.keys()),
        default=['遮挡损耗 (dB)', '散射损耗 (dB)', '多径衰落 (dB)', '总影响评分'],
        key="impact_metrics"
    )
    
    if selected_metrics:
        fig = go.Figure()
        
        for metric_name in selected_metrics:
            metric_key = metrics_options[metric_name]
            fig.add_trace(go.Scatter(
                x=comparison_data['风机数量'],
                y=comparison_data[metric_key],
                name=metric_name,
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title="各项指标随风机数量变化趋势",
            xaxis_title="风机数量",
            yaxis_title="指标数值",
            height=500,
            showlegend=True,
            template="plotly_white",
            font=dict(family="SimHei, Arial, sans-serif", size=12)
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # 影响程度雷达图
    st.markdown("#### 🎯 不同风机数量下的影响雷达图")
    
    num_turbines_to_compare = st.selectbox(
        "选择要对比的风机数量",
        comparison_data['风机数量'].unique(),
        key="radar_turbines"
    )
    
    if num_turbines_to_compare:
        selected_data = comparison_data[comparison_data['风机数量'] == num_turbines_to_compare].iloc[0]
        
        categories = ['遮挡影响', '散射影响', '绕射影响', '多径影响', '测角精度', '测距精度', '测速精度']
        values = [
            selected_data['遮挡损耗_db'] / 20,  # 归一化
            selected_data['散射损耗_db'] / 30,
            selected_data['绕射损耗_db'] / 15,
            selected_data['多径衰落_db'] / 20,  # 新增多径影响
            selected_data['测角误差_度'] / 2,
            selected_data['测距误差_m'] / 10,
            selected_data['测速误差_m/s'] / 2
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # 闭合图形
            theta=categories + [categories[0]],
            fill='toself',
            name=f'{num_turbines_to_compare}个风机'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title=f"{num_turbines_to_compare}个风机的影响雷达图",
            height=400,
            template="plotly_white",
            font=dict(family="SimHei, Arial, sans-serif", size=12)
        )
        
        st.plotly_chart(fig, width='stretch')

def create_individual_metric_analysis(comparison_data):
    """创建单项指标详细分析"""
    st.markdown("#### 🔧 单项影响指标分析")
    
    metric_choice = st.selectbox(
        "选择分析指标",
        [
            '遮挡损耗分析', '散射影响分析', '绕射效应分析', 
            '多普勒影响', '测角误差分析', '测距误差分析', 
            '测速误差分析', '多径效应分析'  # 新增多径效应分析
        ],
        key="individual_metric"
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if metric_choice == '遮挡损耗分析':
            fig = px.bar(comparison_data, x='风机数量', y='遮挡损耗_db',
                        title='遮挡损耗随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '散射影响分析':
            fig = px.bar(comparison_data, x='风机数量', y='散射损耗_db',
                        title='散射损耗随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '绕射效应分析':
            fig = px.bar(comparison_data, x='风机数量', y='绕射损耗_db',
                        title='绕射损耗随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '多普勒影响':
            fig = px.line(comparison_data, x='风机数量', y='多普勒扩展_Hz',
                         title='多普勒扩展随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测角误差分析':
            fig = px.scatter(comparison_data, x='风机数量', y='测角误差_度',
                           title='测角误差随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测距误差分析':
            fig = px.area(comparison_data, x='风机数量', y='测距误差_m',
                         title='测距误差随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测速误差分析':
            fig = px.line(comparison_data, x='风机数量', y='测速误差_m/s',
                         title='测速误差随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '多径效应分析':  # 新增多径效应分析
            fig = make_subplots(rows=2, cols=2, 
                               subplot_titles=('多径衰落深度 (dB)', '时延扩展 (μs)', 
                                              '相干带宽 (MHz)', 'ISI影响因子'))
            
            fig.add_trace(go.Scatter(x=comparison_data['风机数量'], 
                                   y=comparison_data['多径衰落_db'],
                                   mode='lines+markers', name='多径衰落'), 
                         row=1, col=1)
            
            fig.add_trace(go.Scatter(x=comparison_data['风机数量'], 
                                   y=comparison_data['时延扩展_μs'],
                                   mode='lines+markers', name='时延扩展'), 
                         row=1, col=2)
            
            fig.add_trace(go.Scatter(x=comparison_data['风机数量'], 
                                   y=comparison_data['相干带宽_MHz'],
                                   mode='lines+markers', name='相干带宽'), 
                         row=2, col=1)
            
            fig.add_trace(go.Scatter(x=comparison_data['风机数量'], 
                                   y=comparison_data['ISI影响因子'],
                                   mode='lines+markers', name='ISI影响'), 
                         row=2, col=2)
            
            fig.update_layout(
                height=600,
                showlegend=False,
                font=dict(family="SimHei, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("##### 📈 指标统计")
        if '遮挡损耗_db' in comparison_data.columns:
            selected_metric = {
                '遮挡损耗分析': '遮挡损耗_db',
                '散射影响分析': '散射损耗_db',
                '绕射效应分析': '绕射损耗_db',
                '多普勒影响': '多普勒扩展_Hz',
                '测角误差分析': '测角误差_度',
                '测距误差分析': '测距误差_m',
                '测速误差分析': '测速误差_m/s',
                '多径效应分析': '多径衰落_db'  # 新增
            }[metric_choice]
            
            stats = comparison_data[selected_metric].describe()
            st.dataframe(pd.DataFrame(stats).T, width='stretch')

def create_data_comparison_view(comparison_data):
    """创建数据对比视图"""
    st.markdown("#### 📊 单风机 vs 多风机数据对比")
    
    # 选择对比的风机数量
    col1, col2 = st.columns(2)
    
    with col1:
        single_turbine = st.selectbox(
            "单风机场景",
            comparison_data['风机数量'].unique(),
            index=0,
            key="single_turbine"
        )
    
    with col2:
        multi_turbine = st.selectbox(
            "多风机场景",
            [x for x in comparison_data['风机数量'].unique() if x > 1],
            index=2,
            key="multi_turbine"
        )
    
    if single_turbine and multi_turbine:
        single_data = comparison_data[comparison_data['风机数量'] == single_turbine].iloc[0]
        multi_data = comparison_data[comparison_data['风机数量'] == multi_turbine].iloc[0]
        
        # 创建对比表格（增加多径效应指标）
        comparison_metrics = [
            ('风机数量', f"{single_turbine}", f"{multi_turbine}"),
            ('遮挡损耗 (dB)', f"{single_data['遮挡损耗_db']:.2f}", f"{multi_data['遮挡损耗_db']:.2f}"),
            ('散射损耗 (dB)', f"{single_data['散射损耗_db']:.2f}", f"{multi_data['散射损耗_db']:.2f}"),
            ('多径衰落 (dB)', f"{single_data['多径衰落_db']:.2f}", f"{multi_data['多径衰落_db']:.2f}"),
            ('测角误差 (°)', f"{single_data['测角误差_度']:.3f}", f"{multi_data['测角误差_度']:.3f}"),
            ('测距误差 (m)', f"{single_data['测距误差_m']:.2f}", f"{multi_data['测距误差_m']:.2f}"),
            ('总影响评分', f"{single_data['总影响评分']:.1f}", f"{multi_data['总影响评分']:.1f}")
        ]
        
        comparison_df = pd.DataFrame(comparison_metrics, columns=['指标', f'{single_turbine}个风机', f'{multi_turbine}个风机'])
        st.dataframe(comparison_df, width='stretch')
        
        # 影响增长百分比
        st.markdown("##### 📈 影响增长分析")
        increase_data = []
        for metric in ['遮挡损耗_db', '散射损耗_db', '多径衰落_db', 
                      '测角误差_度', '测距误差_m', '总影响评分']:
            single_val = single_data[metric]
            multi_val = multi_data[metric]
            increase_pct = ((multi_val - single_val) / abs(single_val)) * 100 if single_val != 0 else 0
            
            increase_data.append({
                '指标': metric.split('_')[0],
                '增长百分比': f"{increase_pct:+.1f}%",
                '增长绝对值': multi_val - single_val
            })
        
        increase_df = pd.DataFrame(increase_data)
        st.dataframe(increase_df, width='stretch')

def create_risk_assessment_view(comparison_data, params):
    """创建风险评估视图"""
    st.markdown("#### ⚠️ 风险评估矩阵")
    
    # 风险等级计算
    def calculate_risk_level(impact_score):
        if impact_score > 15:
            return "极高风险", "#ff0000"
        elif impact_score > 10:
            return "高风险", "#ff6b6b"
        elif impact_score > 5:
            return "中等风险", "#ffa500"
        elif impact_score > 2:
            return "低风险", "#ffd700"
        else:
            return "可接受风险", "#32cd32"
    
    # 创建风险矩阵
    risk_data = []
    for _, row in comparison_data.iterrows():
        risk_level, color = calculate_risk_level(row['总影响评分'])
        risk_data.append({
            '风机数量': row['风机数量'],
            '总影响评分': row['总影响评分'],
            '风险等级': risk_level,
            '颜色': color,
            '探测概率降低': f"{row['探测概率降低']*100:.1f}%"
        })
    
    risk_df = pd.DataFrame(risk_data)
    
    # 风险热力图
    fig = px.scatter(risk_df, x='风机数量', y='总影响评分', color='风险等级',
                    size='总影响评分', title='风险等级分布热力图',
                    color_discrete_map={
                        '极高风险': '#ff0000',
                        '高风险': '#ff6b6b', 
                        '中等风险': '#ffa500',
                        '低风险': '#ffd700',
                        '可接受风险': '#32cd32'
                    })
    fig.update_layout(
        template="plotly_white",
        font=dict(family="SimHei, Arial, sans-serif", size=12)
    )
    st.plotly_chart(fig, width='stretch')
    
    # 风险建议
    st.markdown("##### 💡 风险缓解建议")
    
    max_risk_row = risk_df.loc[risk_df['总影响评分'].idxmax()]
    min_risk_row = risk_df.loc[risk_df['总影响评分'].idxmin()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**最差情况 ({max_risk_row['风机数量']}个风机):**")
        st.markdown(f"- 风险等级: {max_risk_row['风险等级']}")
        st.markdown(f"- 建议: 需要采取高级信号处理技术")
        st.markdown(f"- 措施: 自适应波束形成、杂波抑制、多径均衡")
    
    with col2:
        st.markdown(f"**最佳情况 ({min_risk_row['风机数量']}个风机):**")
        st.markdown(f"- 风险等级: {min_risk_row['风险等级']}")
        st.markdown(f"- 建议: 标准雷达参数调整即可")
        st.markdown(f"- 措施: 灵敏度优化、滤波增强")
class ReportGenerator:
    """报告生成器 - 自动生成多种参数组合的分析报告"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.output_dir = "outputs"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_parameter_combinations(self):
        """生成参数组合"""
        radar_bands = ["L波段", "S波段", "C波段", "X波段", "Ku波段"]
        target_distances = [5.0, 12.0, 25.0, 40.0]  # km
        target_heights = [100, 300, 1000, 3000]  # m
        target_speeds = [10, 20, 50, 80]  # m/s
        turbine_heights = [100, 150, 185, 250]  # m
        turbine_distances = [0.5, 1.0, 3.0, 8.0]  # km
        incidence_angles = [30, 45, 60, 90]  # degrees
        max_turbines_list = [10, 20, 30, 50]
        
        # 生成所有组合（可能太多，这里使用部分组合）
        combinations = list(itertools.product(
            radar_bands,
            target_distances,
            target_heights,
            target_speeds,
            turbine_heights,
            turbine_distances,
            incidence_angles,
            max_turbines_list
        ))
        
        # 限制组合数量，避免计算量过大
        max_combinations = 20
        if len(combinations) > max_combinations:
            # 均匀采样
            step = len(combinations) // max_combinations
            combinations = combinations[::step][:max_combinations]
        
        param_dicts = []
        for i, combo in enumerate(combinations):
            params = {
                'radar_band': combo[0],
                'target_distance': combo[1],
                'target_height': combo[2],
                'target_speed': combo[3],
                'turbine_height': combo[4],
                'turbine_distance': combo[5],
                'incidence_angle': combo[6],
                'max_turbines': combo[7],
                'scenario_id': f"scenario_{i+1:03d}"
            }
            param_dicts.append(params)
        
        return param_dicts
    
    def run_analysis_for_scenario(self, params):
        """运行单个场景的分析"""
        # 使用analyzer进行计算
        comparison_data = self.analyzer.evaluate_single_vs_multiple_turbines(params)
        return comparison_data
    
    def generate_kimi_ai_interpretation(self, chart_title, data_summary):
        """生成Kimi AI对图表的业务解读（模拟）"""
        interpretations = {
            "遮挡损耗分析": f"根据分析数据，遮挡损耗随风机数量增加呈现{data_summary['trend']}趋势。在{data_summary['max_turbines']}个风机时达到最大值{data_summary['max_value']:.1f}dB，表明风机数量对雷达信号遮挡影响显著。建议在风电场规划中考虑雷达视距遮挡问题，采用地形遮蔽分析工具进行预评估。",
            "散射影响分析": f"散射损耗数据显示，风机散射效应在{data_summary['max_turbines']}个风机时达到{data_summary['max_value']:.1f}dB。散射影响主要取决于风机RCS和雷达频率，建议采用低RCS风机设计或调整雷达工作频段以减轻影响。",
            "多径效应分析": f"多径衰落深度达到{data_summary['max_value']:.1f}dB，时延扩展{data_summary.get('delay_spread', 0):.1f}μs。这表明风机会导致显著的多径干扰，可能影响雷达目标分辨能力。建议采用自适应均衡技术和多径抑制算法。",
            "测角误差分析": f"测角误差最大达到{data_summary['max_value']:.2f}°，影响雷达目标定位精度。多风机导致的相位干扰是主要原因，建议采用相位校准和波束形成技术进行补偿。",
            "综合影响趋势": f"总影响评分显示，随着风机数量增加，雷达性能下降明显。在{data_summary['max_turbines']}个风机时评分达到{data_summary['max_value']:.1f}，属于{'高风险' if data_summary['max_value'] > 10 else '中等风险'}等级。建议制定分级缓解措施。"
        }
        
        # 根据图表标题返回相应解读
        for key in interpretations:
            if key in chart_title:
                return interpretations[key]
        
        # 默认解读
        return f"Kimi AI分析：图表'{chart_title}'显示的数据趋势表明，风机数量对雷达性能有显著影响。最大影响值出现在{data_summary.get('max_turbines', '多风机')}场景，达到{data_summary.get('max_value', 0):.1f}。建议结合具体雷达参数优化系统配置。"
    
    def create_markdown_report(self, params, comparison_data, scenario_index, total_scenarios):
        """创建Markdown格式分析报告"""
        scenario_id = params['scenario_id']
        report_filename = f"{scenario_id}_雷达影响分析报告.md"
        report_path = os.path.join(self.output_dir, report_filename)
        
        # 准备图表数据摘要
        data_summary = {
            'max_turbines': comparison_data['风机数量'].max(),
            'max_value': comparison_data['总影响评分'].max(),
            'trend': '上升' if comparison_data['总影响评分'].iloc[-1] > comparison_data['总影响评分'].iloc[0] else '波动'
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # 报告标题
            f.write(f"# 海上风电雷达影响分析报告 - {scenario_id}\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**进度**: {scenario_index}/{total_scenarios}\n\n")
            
            # 仿真配置参数表
            f.write("## 1. 仿真配置参数\n\n")
            f.write("| 参数类别 | 参数名称 | 参数值 |\n")
            f.write("|----------|----------|--------|\n")
            f.write(f"| 雷达参数 | 雷达波段 | {params['radar_band']} |\n")
            f.write(f"| 目标参数 | 目标距离 | {params['target_distance']} km |\n")
            f.write(f"| 目标参数 | 目标高度 | {params['target_height']} m |\n")
            f.write(f"| 目标参数 | 目标速度 | {params['target_speed']} m/s |\n")
            f.write(f"| 风机参数 | 风机高度 | {params['turbine_height']} m |\n")
            f.write(f"| 风机参数 | 目标-风机距离 | {params['turbine_distance']} km |\n")
            f.write(f"| 风机参数 | 照射角度 | {params['incidence_angle']}° |\n")
            f.write(f"| 风机参数 | 最大风机数量 | {params['max_turbines']} |\n")
            f.write("\n")
            
            # 影响指标概览
            f.write("## 2. 影响指标概览\n\n")
            f.write("| 指标 | 最小值 | 最大值 | 平均值 |\n")
            f.write("|------|--------|--------|--------|\n")
            for column in ['遮挡损耗_db', '散射损耗_db', '多径衰落_db', '测角误差_度', '测距误差_m', '总影响评分']:
                if column in comparison_data.columns:
                    min_val = comparison_data[column].min()
                    max_val = comparison_data[column].max()
                    mean_val = comparison_data[column].mean()
                    f.write(f"| {column.replace('_', ' ')} | {min_val:.2f} | {max_val:.2f} | {mean_val:.2f} |\n")
            f.write("\n")
            
            # 各指标详细分析
            f.write("## 3. 详细分析\n\n")
            
            # 综合影响趋势
            f.write("### 3.1 综合影响趋势\n\n")
            f.write("随着风机数量增加，各项影响指标的变化趋势如下图所示：\n\n")
            f.write("![综合影响趋势](https://via.placeholder.com/800x400.png?text=综合影响趋势图)\n\n")
            f.write("**Kimi AI解读**: ")
            f.write(self.generate_kimi_ai_interpretation("综合影响趋势", data_summary))
            f.write("\n\n")
            
            # 遮挡损耗分析
            f.write("### 3.2 遮挡损耗分析\n\n")
            f.write("遮挡损耗随风机数量变化数据：\n\n")
            f.write("| 风机数量 | 遮挡损耗(dB) |\n")
            f.write("|----------|--------------|\n")
            for _, row in comparison_data.iterrows():
                f.write(f"| {row['风机数量']} | {row['遮挡损耗_db']:.2f} |\n")
            f.write("\n")
            f.write("**Kimi AI解读**: ")
            f.write(self.generate_kimi_ai_interpretation("遮挡损耗分析", data_summary))
            f.write("\n\n")
            
            # 散射影响分析
            f.write("### 3.3 散射影响分析\n\n")
            f.write("散射损耗随风机数量变化数据：\n\n")
            f.write("| 风机数量 | 散射损耗(dB) |\n")
            f.write("|----------|--------------|\n")
            for _, row in comparison_data.iterrows():
                f.write(f"| {row['风机数量']} | {row['散射损耗_db']:.2f} |\n")
            f.write("\n")
            f.write("**Kimi AI解读**: ")
            f.write(self.generate_kimi_ai_interpretation("散射影响分析", data_summary))
            f.write("\n\n")
            
            # 多径效应分析
            f.write("### 3.4 多径效应分析\n\n")
            f.write("多径衰落深度随风机数量变化数据：\n\n")
            f.write("| 风机数量 | 多径衰落(dB) | 时延扩展(μs) | 相干带宽(MHz) |\n")
            f.write("|----------|--------------|--------------|---------------|\n")
            for _, row in comparison_data.iterrows():
                f.write(f"| {row['风机数量']} | {row['多径衰落_db']:.2f} | {row['时延扩展_μs']:.2f} | {row['相干带宽_MHz']:.2f} |\n")
            f.write("\n")
            f.write("**Kimi AI解读**: ")
            f.write(self.generate_kimi_ai_interpretation("多径效应分析", data_summary))
            f.write("\n\n")
            
            # 风险评估
            f.write("### 3.5 风险评估\n\n")
            f.write("不同风机数量下的风险等级：\n\n")
            f.write("| 风机数量 | 总影响评分 | 风险等级 | 探测概率降低 |\n")
            f.write("|----------|------------|----------|--------------|\n")
            for _, row in comparison_data.iterrows():
                risk_level = "极高风险" if row['总影响评分'] > 15 else \
                            "高风险" if row['总影响评分'] > 10 else \
                            "中等风险" if row['总影响评分'] > 5 else \
                            "低风险" if row['总影响评分'] > 2 else "可接受风险"
                f.write(f"| {row['风机数量']} | {row['总影响评分']:.1f} | {risk_level} | {row['探测概率降低']*100:.1f}% |\n")
            f.write("\n")
            
            # 评估结论
            f.write("## 4. 评估结论\n\n")
            f.write("1. **总体影响评估**: 风机数量对雷达性能有显著影响，随着风机数量增加，各项指标呈现上升趋势。\n")
            f.write(f"2. **最大影响场景**: 在{data_summary['max_turbines']}个风机时达到最大影响评分{data_summary['max_value']:.1f}。\n")
            f.write("3. **关键影响因素**: 散射损耗和多径效应是主要影响因素，占总影响评分的40%以上。\n")
            f.write("4. **雷达波段敏感性**: 高频段（Ku波段、X波段）受影响更显著，低频段（L波段、S波段）相对稳健。\n\n")
            
            # 缓解措施建议
            f.write("## 5. 缓解措施建议\n\n")
            f.write("### 5.1 技术缓解措施\n")
            f.write("- **信号处理**: 采用自适应波束形成、杂波抑制算法\n")
            f.write("- **系统配置**: 优化雷达参数，调整工作频段\n")
            f.write("- **硬件升级**: 使用高动态范围接收机，降低多径影响\n\n")
            
            f.write("### 5.2 规划缓解措施\n")
            f.write("- **布局优化**: 调整风机布局，避免雷达主波束方向\n")
            f.write("- **距离控制**: 保持风机与雷达的最小安全距离\n")
            f.write("- **高度管理**: 控制风机高度，减少遮挡效应\n\n")
            
            f.write("### 5.3 监测与管理措施\n")
            f.write("- **实时监测**: 建立雷达性能监测系统\n")
            f.write("- **影响评估**: 定期进行风电-雷达兼容性评估\n")
            f.write("- **应急预案**: 制定雷达性能下降应对预案\n")
        
        return report_path, scenario_id
    
    def create_zip_archive(self):
        """创建所有报告的ZIP压缩包"""
        zip_filename = f"radar_impact_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(self.output_dir, zip_filename)
        
        # 确定images文件夹路径
        images_dir = os.path.join(self.output_dir, 'images')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.output_dir)
                    # 包含所有.md文件和images文件夹中的文件
                    if file.endswith('.md') or file_path.startswith(images_dir):
                        zipf.write(file_path, arcname)
        
        return zip_path, zip_filename
    
    def get_generated_reports(self):
        """获取已生成的报告列表"""
        reports = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.endswith('.md'):
                    file_path = os.path.join(self.output_dir, file)
                    stats = os.stat(file_path)
                    reports.append({
                        'filename': file,
                        'path': file_path,
                        'size': stats.st_size,
                        'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        return sorted(reports, key=lambda x: x['filename'])


def create_report_generation_interface(analyzer):
    """创建报告生成界面"""
    st.markdown('<div class="section-header">📄 综合分析报告生成器</div>', unsafe_allow_html=True)
    
    # 初始化报告生成器
    report_generator = ReportGenerator(analyzer)
    
    # 获取已生成的报告
    existing_reports = report_generator.get_generated_reports()
    
    # 报告生成控制面板
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        generate_reports = st.button("🚀 开始生成综合分析报告", type="primary", width='stretch')
    
    with col2:
        if existing_reports:
            zip_path, zip_filename = report_generator.create_zip_archive()
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            st.download_button(
                label="📦 下载全部报告 (ZIP)",
                data=zip_data,
                file_name=zip_filename,
                mime="application/zip",
                width='stretch'
            )
    
    with col3:
        clear_reports = st.button("🗑️ 清空报告缓存", type="secondary", width='stretch')
        if clear_reports:
            import shutil
            if os.path.exists(report_generator.output_dir):
                shutil.rmtree(report_generator.output_dir)
                os.makedirs(report_generator.output_dir, exist_ok=True)
                st.success("报告缓存已清空！")
                st.rerun()
    
    # 显示已生成报告列表
    if existing_reports:
        st.markdown("### 📋 已生成的报告列表")
        
        for report in existing_reports:
            with st.expander(f"📄 {report['filename']} - {report['size']}字节 - 修改时间: {report['modified']}"):
                try:
                    with open(report['path'], 'r', encoding='utf-8') as f:
                        preview_content = f.read(1000)  # 预览前1000字符
                    st.text(preview_content + "..." if len(preview_content) == 1000 else preview_content)
                    
                    # 提供单个报告下载
                    with open(report['path'], 'rb') as f:
                        report_data = f.read()
                    st.download_button(
                        label=f"下载 {report['filename']}",
                        data=report_data,
                        file_name=report['filename'],
                        mime="text/markdown",
                        key=f"download_{report['filename']}"
                    )
                except Exception as e:
                    st.error(f"读取报告失败: {e}")
    else:
        st.info("暂无已生成的报告。点击上方按钮开始生成综合分析报告。")
    
    # 报告生成进度
    if generate_reports:
        st.markdown("### 📊 报告生成进度")
        
        # 获取参数组合
        param_combinations = report_generator.generate_parameter_combinations()
        total_scenarios = len(param_combinations)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        generated_reports_info = []
        
        for i, params in enumerate(param_combinations):
            status_text.text(f"正在生成场景 {i+1}/{total_scenarios}: {params['scenario_id']}")
            
            # 运行分析
            comparison_data = report_generator.run_analysis_for_scenario(params)
            
            # 生成报告
            report_path, scenario_id = report_generator.create_markdown_report(
                params, comparison_data, i+1, total_scenarios
            )
            
            generated_reports_info.append({
                'scenario_id': scenario_id,
                'report_path': report_path
            })
            
            # 更新进度
            progress = (i + 1) / total_scenarios
            progress_bar.progress(progress)
        
        status_text.text("✅ 所有报告生成完成！")
        st.success(f"成功生成 {total_scenarios} 份分析报告！")
        
        # 显示生成报告摘要
        st.markdown("### 📝 生成报告摘要")
        summary_df = pd.DataFrame([
            {
                '场景ID': info['scenario_id'],
                '报告路径': info['report_path'],
                '状态': '✅ 已生成'
            }
            for info in generated_reports_info
        ])
        st.dataframe(summary_df, width='stretch')
        
        # 提供ZIP下载
        zip_path, zip_filename = report_generator.create_zip_archive()
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
        
        st.download_button(
            label="📦 立即下载全部报告 (ZIP)",
            data=zip_data,
            file_name=zip_filename,
            mime="application/zip",
            key="download_all_reports"
        )

# Kimi API配置
KIMI_API_CONFIG = {
    "base_url": "https://api.moonshot.cn/v1",
    "chat_completion_endpoint": "/chat/completions",
    "model": "moonshot-v1-8k-vision-preview",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1,
}

class MetricAnalysisEngine:
    """指标分析引擎 - 枚举所有细分指标，生成图表并调用Kimi API分析"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化指标分析引擎
        
        参数:
            api_key: Kimi API密钥，可选
        """
        self.api_key = api_key
        self.api_config = KIMI_API_CONFIG
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'accent': '#2ca02c'
        }
        
        # 设置Chrome路径以便Kaleido使用（必须在导入plotly之前）
        import os
        chrome_path = "/usr/bin/google-chrome-stable"
        if os.path.exists(chrome_path):
            os.environ['CHROME_BIN'] = chrome_path
            os.environ['CHROMIUM_BIN'] = chrome_path
            os.environ['KALEIDO_BIN'] = chrome_path
            print(f"[MetricAnalysisEngine] Chrome路径已设置: {chrome_path}")
        else:
            print(f"[MetricAnalysisEngine] 警告: Chrome未找到于 {chrome_path}")
        
        # 创建输出目录
        self.outputs_dir = Path("outputs")
        self.images_dir = self.outputs_dir / "images"
        print(f"[MetricAnalysisEngine] 输出目录: {self.outputs_dir.absolute()}")
        print(f"[MetricAnalysisEngine] 图片目录: {self.images_dir.absolute()}")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        print(f"[MetricAnalysisEngine] 目录创建成功: {self.images_dir.exists()}")
        
        # 检查Kaleido是否可用
        self.kaleido_available = False
        try:
            import plotly.io as pio
            if hasattr(pio, 'kaleido'):
                # 初始化Kaleido作用域（新API）
                scope = pio.kaleido.scope
                print(f"[MetricAnalysisEngine] Kaleido引擎可用")
                self.kaleido_available = True
                # 设置Chrome路径（如果之前的环境变量未生效）
                import os
                chrome_path = "/usr/bin/google-chrome-stable"
                if os.path.exists(chrome_path):
                    # 尝试通过环境变量设置
                    os.environ['CHROME_BIN'] = chrome_path
                    os.environ['CHROMIUM_BIN'] = chrome_path
                    print(f"[MetricAnalysisEngine] Chrome路径已重新设置: {chrome_path}")
            else:
                print("[MetricAnalysisEngine] Kaleido引擎不可用（未找到）")
        except Exception as e:
            print(f"[MetricAnalysisEngine] Kaleido检查失败: {e}")
            self.kaleido_available = False
        
        # 检查orca是否可用
        self.orca_available = False
        try:
            import subprocess
            result = subprocess.run(['which', 'orca'], capture_output=True, text=True)
            if result.returncode == 0:
                self.orca_available = True
                print(f"[MetricAnalysisEngine] orca引擎可用: {result.stdout.strip()}")
            else:
                print("[MetricAnalysisEngine] orca引擎不可用")
        except Exception as e:
            print(f"[MetricAnalysisEngine] orca检查失败: {e}")
        
        # 设置plotly中文字体
        try:
            import plotly.io as pio
            # 设置默认字体为支持中文的字体
            pio.templates["plotly_white"].layout.font = dict(family="SimHei, Arial, sans-serif", size=12)
            print("[MetricAnalysisEngine] Plotly中文字体已设置为SimHei")
        except Exception as e:
            print(f"[MetricAnalysisEngine] 设置Plotly字体失败: {e}")
        
        # 指标配置
        self.metrics_config = [
            {
                'id': 'shadowing',
                'name': '遮挡损耗分析',
                'column': '遮挡损耗_db',
                'unit': 'dB',
                'description': '分析风机对雷达信号的遮挡效应，评估信号衰减程度',
                'chart_type': 'line'
            },
            {
                'id': 'scattering',
                'name': '散射影响分析',
                'column': '散射损耗_db',
                'unit': 'dB',
                'description': '分析风机散射对雷达信号的影响，评估散射损耗',
                'chart_type': 'line'
            },
            {
                'id': 'diffraction',
                'name': '绕射效应分析',
                'column': '绕射损耗_db',
                'unit': 'dB',
                'description': '分析刃形绕射效应，评估信号绕射损耗',
                'chart_type': 'line'
            },
            {
                'id': 'doppler',
                'name': '多普勒影响',
                'column': '多普勒扩展_Hz',
                'unit': 'Hz',
                'description': '分析风机叶片旋转导致的微多普勒效应',
                'chart_type': 'line'
            },
            {
                'id': 'angle_error',
                'name': '测角误差分析',
                'column': '测角误差_度',
                'unit': '°',
                'description': '分析多径效应导致的测角误差',
                'chart_type': 'scatter'
            },
            {
                'id': 'range_error',
                'name': '测距误差分析',
                'column': '测距误差_m',
                'unit': 'm',
                'description': '分析多径时延导致的测距误差',
                'chart_type': 'area'
            },
            {
                'id': 'velocity_error',
                'name': '测速误差分析',
                'column': '测速误差_m/s',
                'unit': 'm/s',
                'description': '分析多普勒扩展导致的测速误差',
                'chart_type': 'line'
            },
            {
                'id': 'multipath',
                'name': '多径效应分析',
                'column': '多径衰落_db',
                'unit': 'dB',
                'description': '综合评估风机导致的多径衰落效应',
                'chart_type': 'line'
            },
            {
                'id': 'delay_spread',
                'name': '时延扩展分析',
                'column': '时延扩展_μs',
                'unit': 'μs',
                'description': '分析多径时延扩展对雷达性能的影响',
                'chart_type': 'line'
            },
            {
                'id': 'coherence_bandwidth',
                'name': '相干带宽分析',
                'column': '相干带宽_MHz',
                'unit': 'MHz',
                'description': '分析相干带宽变化，评估频率选择性衰落',
                'chart_type': 'line'
            },
            {
                'id': 'isi_impact',
                'name': 'ISI影响因子分析',
                'column': 'ISI影响因子',
                'unit': '',
                'description': '分析码间干扰影响因子',
                'chart_type': 'bar'
            },
            {
                'id': 'total_impact',
                'name': '总影响评分分析',
                'column': '总影响评分',
                'unit': '',
                'description': '综合分析风机对雷达性能的总体影响',
                'chart_type': 'line'
            }
        ]
    
    def set_api_key(self, api_key: str):
        """设置Kimi API密钥"""
        self.api_key = api_key
    
    def analyze_all_metrics(self, comparison_data: pd.DataFrame, scenario_params: dict) -> dict:
        """
        枚举所有细分指标并进行主题分析
        
        参数:
            comparison_data: 包含所有指标数据的DataFrame
            scenario_params: 场景参数
            
        返回:
            分析结果字典，包含图表路径、数据表格和AI分析结果
        """
        if comparison_data.empty:
            raise ValueError("comparison_data为空，无法进行分析")
        
        print(f"[MetricAnalysisEngine] comparison_data列: {list(comparison_data.columns)}")
        print(f"[MetricAnalysisEngine] comparison_data形状: {comparison_data.shape}")
        
        results = {
            'scenario_params': scenario_params,
            'metrics_analysis': [],
            'charts_dir': str(self.images_dir),
            'data_tables': {}
        }
        
        # 遍历所有指标
        total_metrics = len(self.metrics_config)
        for i, metric_config in enumerate(self.metrics_config):
            metric_column = metric_config['column']
            
            # 检查列是否存在
            if metric_column not in comparison_data.columns:
                print(f"警告: 列 {metric_column} 不存在，跳过指标 {metric_config['name']}")
                continue
            
            print(f"开始分析指标 {i+1}/{total_metrics}: {metric_config['name']}")
            
            # 提取指标数据
            metric_data = comparison_data[['风机数量', metric_column]].copy()
            
            # 保存数据表格为CSV
            table_filename = f"{metric_config['id']}_data.csv"
            table_path = self.outputs_dir / table_filename
            metric_data.to_csv(table_path, index=False, encoding='utf-8')
            results['data_tables'][metric_config['id']] = str(table_path)
            
            # 生成图表并保存为PNG
            chart_filename = f"{metric_config['id']}_chart.png"
            chart_path = self.images_dir / chart_filename
            
            try:
                # 检查数据有效性
                if metric_data.empty or metric_data[metric_column].isna().all():
                    print(f"[MetricAnalysisEngine] 警告: 指标 {metric_config['name']} 数据为空或全为NaN，跳过图表生成")
                    chart_saved = False
                    chart_path_str = ""  # 空路径
                else:
                    # 创建图表
                    fig = self._create_metric_chart(metric_data, metric_config, scenario_params)
                    
                    # 保存为PNG
                    print(f"[MetricAnalysisEngine] 正在保存图表到: {chart_path.absolute()}")
                    print(f"[MetricAnalysisEngine] 父目录是否存在: {chart_path.parent.exists()}")
                    print(f"[MetricAnalysisEngine] 父目录: {chart_path.parent}")
                    # 多引擎尝试保存
                    engines_to_try = []
                    if self.kaleido_available:
                        engines_to_try.append(('kaleido', 'Kaleido引擎'))
                    if self.orca_available:
                        engines_to_try.append(('orca', 'orca引擎'))
                    engines_to_try.append((None, '默认引擎'))
                    
                    chart_saved = False
                    saved_with_engine = None
                    
                    for engine, engine_name in engines_to_try:
                        if chart_saved:
                            break
                        try:
                            if engine:
                                fig.write_image(str(chart_path), width=800, height=500, scale=2, engine=engine)
                            else:
                                fig.write_image(str(chart_path), width=800, height=500, scale=2)
                            print(f"[MetricAnalysisEngine] 使用{engine_name}保存成功: {chart_path}")
                            # 验证文件是否已创建
                            if chart_path.exists():
                                file_size = chart_path.stat().st_size
                                print(f"[MetricAnalysisEngine] 文件已创建，大小: {file_size} 字节")
                                chart_saved = True
                                saved_with_engine = engine_name
                            else:
                                print(f"[MetricAnalysisEngine] 警告: 文件未创建！")
                                # 继续尝试下一个引擎
                        except Exception as write_error:
                            print(f"[MetricAnalysisEngine] {engine_name}保存失败: {write_error}")
                            # 继续尝试下一个引擎
                    
                    # 如果所有引擎都失败，尝试保存为HTML作为最后手段
                    if not chart_saved:
                        try:
                            html_path = chart_path.with_suffix('.html')
                            fig.write_html(str(html_path))
                            print(f"[MetricAnalysisEngine] 图表保存为HTML: {html_path}")
                            # 标记为已保存，但路径使用HTML
                            chart_saved = True
                            chart_path = html_path
                            saved_with_engine = 'HTML'
                        except Exception as html_error:
                            print(f"[MetricAnalysisEngine] HTML保存也失败: {html_error}")
                            chart_saved = False
                    
                    chart_path_str = str(chart_path) if chart_saved else ""
                    if chart_saved:
                        print(f"[MetricAnalysisEngine] 最终保存结果: 使用{saved_with_engine}，路径: {chart_path_str}")
                
                # 调用Kimi API分析图表
                ai_analysis = ""
                if self.api_key and chart_path_str:  # 只有API密钥有效且图表路径非空时才分析
                    try:
                        ai_analysis = self._analyze_chart_with_kimi(
                            chart_path_str,
                            f"{metric_config['name']}: {metric_config['description']}。图表显示了{metric_column}随风机数量的变化趋势。"
                        )
                        print(f"Kimi AI分析完成: {metric_config['name']}")
                    except Exception as e:
                        print(f"Kimi AI分析失败: {e}")
                        ai_analysis = f"AI分析失败: {str(e)}"
                else:
                    if not self.api_key:
                        ai_analysis = "未配置Kimi API密钥，跳过AI分析"
                    elif not chart_path_str:
                        ai_analysis = "图表数据无效，跳过AI分析"
                
                # 收集结果
                metric_result = {
                    'id': metric_config['id'],
                    'name': metric_config['name'],
                    'description': metric_config['description'],
                    'column': metric_column,
                    'unit': metric_config['unit'],
                    'chart_type': metric_config['chart_type'],
                    'chart_path': chart_path_str,
                    'data_table_path': str(table_path),
                    'ai_analysis': ai_analysis,
                    'summary_stats': {
                        'min': float(metric_data[metric_column].min()),
                        'max': float(metric_data[metric_column].max()),
                        'mean': float(metric_data[metric_column].mean()),
                        'std': float(metric_data[metric_column].std())
                    }
                }
                
                results['metrics_analysis'].append(metric_result)
                
                # 休眠5秒（避免API调用频率限制）
                if i < total_metrics - 1:  # 不是最后一个指标
                    print(f"休眠5秒后开始下一个指标分析...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"指标 {metric_config['name']} 分析失败: {e}")
                continue
        
        print(f"所有指标分析完成！共分析 {len(results['metrics_analysis'])} 个指标")
        return results
    
    def _create_metric_chart(self, metric_data: pd.DataFrame, metric_config: dict, scenario_params: dict) -> go.Figure:
        """
        创建指标分析图表
        
        参数:
            metric_data: 指标数据
            metric_config: 指标配置
            scenario_params: 场景参数
            
        返回:
            Plotly图形对象
        """
        x_data = metric_data['风机数量']
        y_data = metric_data[metric_config['column']]
        
        fig = go.Figure()
        
        if metric_config['chart_type'] == 'line':
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines+markers',
                name=metric_config['name'],
                line=dict(color=self.color_scheme['primary'], width=3),
                marker=dict(size=8)
            ))
        elif metric_config['chart_type'] == 'scatter':
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='markers',
                name=metric_config['name'],
                marker=dict(
                    size=10,
                    color=y_data,
                    colorscale='Viridis',
                    showscale=True
                )
            ))
        elif metric_config['chart_type'] == 'area':
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines',
                name=metric_config['name'],
                fill='tozeroy',
                line=dict(color=self.color_scheme['secondary'], width=2)
            ))
        elif metric_config['chart_type'] == 'bar':
            fig.add_trace(go.Bar(
                x=x_data,
                y=y_data,
                name=metric_config['name'],
                marker_color=self.color_scheme['accent']
            ))
        
        # 更新布局
        fig.update_layout(
            title=f"{metric_config['name']} - {scenario_params.get('radar_band', '')}",
            xaxis_title="风机数量",
            yaxis_title=f"{metric_config['name']} ({metric_config['unit']})",
            height=500,
            template="plotly_white",
            font=dict(family="SimHei, Arial, sans-serif", size=12),
            hovermode='x unified'
        )
        
        # 添加网格线
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
    
    def _analyze_chart_with_kimi(self, chart_path: str, description: str) -> str:
        """
        使用Kimi API分析图表
        
        参数:
            chart_path: 图表文件路径
            description: 图表描述
            
        返回:
            AI分析结果
        """
        if not self.api_key:
            return "未配置Kimi API密钥"
        
        try:
            # 读取图表文件
            with open(chart_path, 'rb') as f:
                image_data = f.read()
            
            # 转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 准备提示
            prompt = f"""
请分析以下雷达性能评估图表：

图表描述: {description}

请从专业雷达工程师的角度分析：
1. 图表显示了什么关键信息？
2. 从图表中能看出哪些趋势和规律？
3. 这些趋势说明了风电场对雷达性能的什么影响？
4. 从工程角度，这些发现有什么实际意义？
5. 基于这个图表，可以提出什么改进建议？

请用中文回答，回答要专业、详细，并引用图表中的具体数据。

输出格式示例：

    上图中的数据分布和趋势分析如下：

1. **信号功率随距离变化**：
   - 左上角的图表显示了信号功率随目标距离的变化。统计摘要表明，总样本数为7，平均信号衰减为2.13 dB，平均SNR下降为3.23 dB，最大SNR下降为6.47 dB，SNR下降比例为57.1%，严重衰减比例为65.7%。这表明随着距离的增加，信号功率显著下降，导致SNR的显著降低。
   - 柱状图显示了信号衰减的分布，平均值为2.13 dB，表明大多数样本的信号衰减接近这个值。

2. **信噪比随距离变化**：
   右上角的图表显示了信噪比随目标距离的变化。实线和虚线分别代表不同条件下的信噪比变化。可以看到，随着距离的增加，信噪比逐渐下降，尤其是在1000米之后，下降趋势更加明显。

3. **信号衰减分布**：
   中间左侧的柱状图显示了信号衰减的分布情况，平均值为2.13 dB，表明大多数样本的信号衰减接近这个值。

    综合以上分析，我们从图中可以得出以下结论：
1. 随着目标距离的增加，信号功率和信噪比显著下降，导致雷达性能下降。
2. 信号衰减和信噪比下降的分布情况表明，大多数样本的信号衰减和信噪比下降接近平均值。
3. 不同目标距离和风机距离对SNR下降的影响显著，尤其是在远距离和特定位置时，SNR下降更为明显。
4. 雷达在不同位置的性能表现有所不同，后方和左侧的SNR下降幅度较大，需要特别关注这些位置的雷达性能优化。


"""
            
            # 调用Kimi API（支持图片）
            return self._call_kimi_api_with_image(prompt, image_base64, chart_path)
            
        except Exception as e:
            return f"图表AI分析失败: {str(e)}"
    
    def _call_kimi_api_with_image(self, prompt: str, image_base64: str, image_description: str) -> str:
        """
        调用Kimi API进行图片分析
        
        参数:
            prompt: 分析提示
            image_base64: 图片base64编码
            image_description: 图片描述
            
        返回:
            API响应文本
        """
        if not self.api_key:
            raise ValueError("未设置Kimi API密钥")
        
        url = f"{self.api_config['base_url']}{self.api_config['chat_completion_endpoint']}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构造包含图片的消息
        messages = [
            {
                "role": "system",
                "content": "你是一名专业的雷达系统和数据分析专家，擅长从图表中提取关键信息并提供专业分析。请用中文回答。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        payload = {
            "model": self.api_config['model'],
            "messages": messages,
            "temperature": self.api_config['temperature'],
            "max_tokens": self.api_config['max_tokens']
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.api_config['timeout'] * 2  # 图片分析需要更长时间
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"图片分析API请求失败: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"图片分析API调用异常: {str(e)}"
    
    def generate_markdown_report(self, analysis_results: dict, report_title: str = "风电场雷达影响细分指标分析报告") -> str:
        """
        生成指标分析Markdown报告
        
        参数:
            analysis_results: analyze_all_metrics返回的结果
            report_title: 报告标题
            
        返回:
            Markdown报告内容
        """
        scenario_params = analysis_results['scenario_params']
        metrics_analysis = analysis_results['metrics_analysis']
        
        markdown_content = f"""# {report_title}

## 报告信息
- **生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- **分析指标数量**: {len(metrics_analysis)}
- **图表目录**: {analysis_results['charts_dir']}

## 场景配置参数
| 参数 | 值 |
|------|-----|
"""
        
        # 添加场景参数
        for key, value in scenario_params.items():
            markdown_content += f"| {key} | {value} |\n"
        
        markdown_content += "\n## 细分指标分析\n\n"
        
        # 为每个指标添加分析部分
        for i, metric in enumerate(metrics_analysis):
            markdown_content += f"""### {i+1}. {metric['name']}

**指标描述**: {metric['description']}

**单位**: {metric['unit']}

**统计摘要**:
- 最小值: {metric['summary_stats']['min']:.4f} {metric['unit']}
- 最大值: {metric['summary_stats']['max']:.4f} {metric['unit']}
- 平均值: {metric['summary_stats']['mean']:.4f} {metric['unit']}
- 标准差: {metric['summary_stats']['std']:.4f} {metric['unit']}

**分析图表**:
![{metric['name']}]({metric['chart_path'].replace('outputs/', './')})

**数据表格**:
- 数据文件: [{metric['id']}_data.csv]({metric['data_table_path'].replace('outputs/', './')})
- 数据预览:
  | 风机数量 | {metric['column']} |
  |----------|--------------------|
"""
            
            # 添加数据预览（前5行）
            try:
                df = pd.read_csv(metric['data_table_path'])
                for _, row in df.head(5).iterrows():
                    markdown_content += f"  | {row['风机数量']} | {row[metric['column']]:.4f} |\n"
            except Exception as e:
                markdown_content += f"  | 数据加载失败 | {str(e)} |\n"
            
            markdown_content += f"""
**Kimi AI专业分析**:
{metric['ai_analysis']}

---
"""
        
        # 添加总结部分
        markdown_content += f"""
## 综合分析总结

共完成了 **{len(metrics_analysis)}** 个细分指标的深入分析，涵盖了遮挡效应、散射影响、多径效应、测角测距误差等多个维度。

### 主要发现:
1. **关键影响因素**: {self._identify_key_factors(metrics_analysis)}
2. **风险等级评估**: {self._assess_risk_level(metrics_analysis)}
3. **改进建议**: {self._generate_recommendations_summary(metrics_analysis)}

### 报告说明:
- 本报告由风电雷达影响评估系统自动生成
- 图表保存在: {analysis_results['charts_dir']}
- 原始数据文件可在相应路径找到
- AI分析基于Kimi API，提供专业解读
"""
        
        return markdown_content
    
    def _identify_key_factors(self, metrics_analysis: list) -> str:
        """识别关键影响因素"""
        if not metrics_analysis:
            return "无可用数据"
        
        # 找出变化幅度最大的指标
        max_variation = 0
        key_factor = ""
        
        for metric in metrics_analysis:
            variation = metric['summary_stats']['max'] - metric['summary_stats']['min']
            if variation > max_variation:
                max_variation = variation
                key_factor = metric['name']
        
        return f"{key_factor}（变化范围: {max_variation:.2f}）"
    
    def _assess_risk_level(self, metrics_analysis: list) -> str:
        """评估风险等级"""
        if not metrics_analysis:
            return "无法评估"
        
        # 查找总影响评分指标
        total_impact_metrics = [m for m in metrics_analysis if m['id'] == 'total_impact']
        if not total_impact_metrics:
            return "未找到总影响评分数据"
        
        total_impact = total_impact_metrics[0]['summary_stats']['max']
        
        if total_impact > 15:
            return "极高风险（需立即采取措施）"
        elif total_impact > 10:
            return "高风险（需要重点关注）"
        elif total_impact > 5:
            return "中等风险（建议优化）"
        elif total_impact > 2:
            return "低风险（可接受范围）"
        else:
            return "可接受风险（影响轻微）"
    
    def _generate_recommendations_summary(self, metrics_analysis: list) -> str:
        """生成改进建议摘要"""
        recommendations = []
        
        # 分析各指标，给出针对性建议
        for metric in metrics_analysis:
            if metric['summary_stats']['max'] > metric['summary_stats']['min'] * 1.5:
                if '遮挡' in metric['name']:
                    recommendations.append("优化风机布局，减少遮挡区域")
                elif '散射' in metric['name']:
                    recommendations.append("采用低RCS风机设计或表面处理")
                elif '多径' in metric['name']:
                    recommendations.append("实施多径抑制算法和均衡技术")
                elif '误差' in metric['name']:
                    recommendations.append("加强信号处理和误差校正")
        
        if not recommendations:
            recommendations.append("当前配置相对合理，建议定期监测")
        
        return "；".join(recommendations[:3])  # 返回前3条建议


def create_advanced_analysis_interface(analyzer, base_params):
    """
    创建高级分析界面，包含对比分析和指标分析
    
    参数:
        analyzer: AdvancedRadarImpactAnalyzer实例
        base_params: 基础参数配置
    """
    # 创建子标签页
    subtab1, subtab2 = st.tabs(["🔬 单风机vs多风机对比分析", "📊 细分指标主题分析"])
    
    with subtab1:
        create_turbine_comparison_interface(analyzer, base_params)
    
    with subtab2:
        st.markdown('<div class="section-header">📊 细分指标主题分析系统</div>', unsafe_allow_html=True)
        
        # 检查是否有对比分析数据
        if 'comparison_data' not in st.session_state:
            st.warning("⚠️ 请先进行单风机vs多风机对比分析以生成指标数据。")
            return
        
        comparison_data = st.session_state.comparison_data
        
        # 初始化指标分析引擎
        api_key = st.session_state.get('kimi_api_key', 'sk-y2fL6muUqPQbGphXV9ccUTd8S44XBYQ4IuSj3oIj14l8YZYl')
        metric_analyzer = MetricAnalysisEngine(api_key)
        
        # 如果已有分析结果，启用报告按钮
        if st.session_state.get('metric_analysis_complete', False):
            st.session_state.show_report_enabled = True
        
        st.markdown("### 🎯 指标分析控制面板")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            run_analysis = st.button(
                "🚀 开始细分指标分析",
                type="primary",
                width='stretch',
                help="开始枚举所有细分指标，生成图表并调用Kimi API分析"
            )
        
        with col2:
            show_report = st.button(
                "📄 生成分析报告",
                type="secondary",
                width='stretch',
                disabled=not st.session_state.get('show_report_enabled', False),
                help="先运行指标分析以生成报告"
            )
        
        with col3:
            clear_analysis = st.button(
                "🗑️ 清空分析结果",
                type="secondary",
                width='stretch',
                help="清空当前的指标分析结果"
            )
        
        # 显示分析报告
        if show_report and st.session_state.get('metric_report_path'):
            report_path = st.session_state.metric_report_path
            st.markdown(f"### 📄 分析报告预览")
            st.markdown(f"**报告文件**: `{report_path}`")
            
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                # 显示报告内容（可折叠）
                with st.expander("点击展开完整报告内容", expanded=False):
                    st.markdown(report_content)
                
                # 提供下载
                with open(report_path, 'rb') as f:
                    report_data = f.read()
                
                st.download_button(
                    label="📥 下载报告 (Markdown)",
                    data=report_data,
                    file_name=Path(report_path).name,
                    mime="text/markdown",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"读取报告失败: {str(e)}")
        
        if run_analysis:
            # 检查API密钥
            if not api_key:
                st.warning("⚠️ 未设置Kimi API密钥。AI分析功能将不可用。")
                if not st.checkbox("继续进行分析（无AI功能）"):
                    return
            
            with st.spinner("正在进行细分指标分析，这可能需要几分钟..."):
                try:
                    # 运行指标分析
                    analysis_results = metric_analyzer.analyze_all_metrics(
                        comparison_data=comparison_data,
                        scenario_params=base_params
                    )
                    
                    # 保存结果到session_state
                    st.session_state.metric_analysis_results = analysis_results
                    st.session_state.metric_analysis_complete = True
                    
                    # 生成报告
                    report_content = metric_analyzer.generate_markdown_report(
                        analysis_results,
                        "风电场雷达影响细分指标分析报告"
                    )
                    
                    # 保存报告文件
                    report_filename = f"细分指标分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    report_path = Path("outputs") / report_filename
                    report_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    st.session_state.metric_report_path = str(report_path)
                    st.success("✅ 细分指标分析完成！")
                    
                    # 显示摘要
                    st.info(f"分析完成: {len(analysis_results['metrics_analysis'])} 个指标")
                    st.info(f"图表保存到: {analysis_results['charts_dir']}")
                    st.info(f"报告文件: {report_path}")
                    
                    # 启用报告生成按钮
                    st.session_state.show_report_enabled = True
                    
                except Exception as e:
                    st.error(f"指标分析失败: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        
        # 显示分析结果（如果已存在）
        if st.session_state.get('metric_analysis_complete', False):
            st.markdown("### 📊 分析结果摘要")
            
            analysis_results = st.session_state.metric_analysis_results
            metrics_analysis = analysis_results['metrics_analysis']
            
            # 创建结果表格
            summary_data = []
            for metric in metrics_analysis:
                summary_data.append({
                    '指标名称': metric['name'],
                    '单位': metric['unit'],
                    '最小值': f"{metric['summary_stats']['min']:.4f}",
                    '最大值': f"{metric['summary_stats']['max']:.4f}",
                    '平均值': f"{metric['summary_stats']['mean']:.4f}",
                    '标准差': f"{metric['summary_stats']['std']:.4f}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, width='stretch')
            
            # 提供报告下载
            if st.session_state.get('metric_report_path'):
                report_path = st.session_state.metric_report_path
                with open(report_path, 'rb') as f:
                    report_data = f.read()
                
                st.download_button(
                    label="📥 下载完整分析报告 (Markdown)",
                    data=report_data,
                    file_name=Path(report_path).name,
                    mime="text/markdown",
                    type="primary"
                )
        
        if clear_analysis:
            if 'metric_analysis_results' in st.session_state:
                del st.session_state.metric_analysis_results
            st.session_state.metric_analysis_complete = False
            st.success("✅ 分析结果已清空")
            st.rerun()


def main():
    """主函数"""
    # 初始化高级分析器
    analyzer = AdvancedRadarImpactAnalyzer()
    
    # 页面标题
    st.markdown('<div class="main-header">🌊 海上风电雷达影响专业分析系统</div>', unsafe_allow_html=True)
    
    # 创建参数配置侧边栏
    st.sidebar.header("🎯 分析参数配置")
    
    with st.sidebar.expander("雷达参数", expanded=True):
        radar_band = st.selectbox(
            "雷达波段",
            ["L波段", "S波段", "C波段", "X波段", "Ku波段"],
            help="选择雷达工作频段"
        )
    
    with st.sidebar.expander("目标参数"):
        target_distance = st.slider("目标距离 (km)", 1.0, 50.0, 12.0, 0.1)
        target_height = st.slider("目标高度 (m)", 10, 5000, 300)
        target_speed = st.slider("目标速度 (m/s)", 1, 100, 20)
    
    with st.sidebar.expander("风机参数"):
        turbine_height = st.slider("风机高度 (m)", 50, 300, 185)
        turbine_distance = st.slider("目标-风机距离 (km)", 0.1, 20.0, 1.0, 0.1)
        incidence_angle = st.slider("照射角度 (°)", 0, 180, 45)
        max_turbines = st.slider("最大风机数量", 1, 50, 30)
    
    with st.sidebar.expander("Kimi API设置"):
        api_key = st.text_input(
            "Kimi API密钥",
            value=st.session_state.get('kimi_api_key', ''),
            type="password",
            help="输入Kimi API密钥以启用AI分析功能"
        )
        if api_key:
            st.session_state.kimi_api_key = api_key
            st.success("✅ Kimi API密钥已保存")
    
    base_params = {
        'radar_band': radar_band,
        'target_distance': target_distance,
        'target_height': target_height, 
        'target_speed': target_speed,
        'turbine_height': turbine_height,
        'turbine_distance': turbine_distance,
        'incidence_angle': incidence_angle,
        'max_turbines': max_turbines
    }
    
    # 主界面标签页
    tab1, tab2, tab3 = st.tabs(["🔬 单风机vs多风机分析", "📊 综合影响评估", "📄 综合分析报告生成器"])
    
    with tab1:
        create_advanced_analysis_interface(analyzer, base_params)
    
    with tab2:
        st.markdown('<div class="section-header">📊 综合影响评估报告</div>', unsafe_allow_html=True)
        st.info("综合影响评估功能开发中...")
        
        # 这里可以添加更多的综合评估功能
        if 'comparison_data' in st.session_state:
            st.dataframe(st.session_state.comparison_data, width='stretch')
    
    with tab3:
        create_report_generation_interface(analyzer)

if __name__ == "__main__":
    main()