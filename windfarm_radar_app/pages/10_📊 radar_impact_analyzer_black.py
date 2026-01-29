import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
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
import streamlit.components.v1 as components

# 页面配置
st.set_page_config(
    page_title="海上风电雷达影响专业分析系统",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置plotly中文字体
import plotly.io as pio
# 更新plotly_white模板的字体设置
pio.templates["plotly_white"].update(
    layout=dict(font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12))
)
# 设置默认模板为plotly_white，确保所有图表都使用中文字体
pio.templates.default = "plotly_white"
print("[页面初始化] Plotly中文字体已设置为SimHei，默认模板已设置")

# 设置matplotlib中文字体（确保中文正常显示）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

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
        run_comparison = st.button("🔄 运行对比分析", type="primary")
    
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
            font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12)
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
            font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12)
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
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '散射影响分析':
            fig = px.bar(comparison_data, x='风机数量', y='散射损耗_db',
                        title='散射损耗随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '绕射效应分析':
            fig = px.bar(comparison_data, x='风机数量', y='绕射损耗_db',
                        title='绕射损耗随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '多普勒影响':
            fig = px.line(comparison_data, x='风机数量', y='多普勒扩展_Hz',
                         title='多普勒扩展随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测角误差分析':
            fig = px.scatter(comparison_data, x='风机数量', y='测角误差_度',
                           title='测角误差随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测距误差分析':
            fig = px.area(comparison_data, x='风机数量', y='测距误差_m',
                         title='测距误差随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
                template="plotly_white"
            )
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测速误差分析':
            fig = px.line(comparison_data, x='风机数量', y='测速误差_m/s',
                         title='测速误差随风机数量变化')
            fig.update_layout(
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
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
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
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
        font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12)
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

def create_metric_methods_tab(params):
    """创建指标计算方法与原理标签页"""
    st.markdown("### 📚 指标计算方法与原理")
    
    # 显示当前参数配置（使用传入的参数）
    if params:
        st.markdown("#### 📝 当前参数配置")
        # 将参数转换为DataFrame显示
        param_df = pd.DataFrame([params])
        st.dataframe(param_df, hide_index=True, use_container_width=True)
    
    # 生成详细的指标计算方法说明
    methods_markdown = """
# 海上风电雷达影响分析指标计算方法与原理

## 1. 遮挡损耗 (Shadowing Loss)

### 计算公式

$$
\text{shadow\_loss\_db} = 20 \times \text{shadow\_factor} \times \text{height\_factor}
$$

$$
\text{shadow\_factor} = \min(1.0,\ 0.3 + 0.2 \times \log_{10}(\text{num\_turbines}))
$$

$$
\text{height\_factor} = \max\left(0.1, 1 - \frac{|\text{target\_height} - \text{turbine\_height}|}{2 \times \text{turbine\_height}}\right)
$$

### 物理原理

遮挡效应基于几何光学理论，当风机位于雷达与目标之间时，会形成雷达阴影区。阴影区的深度与风机高度、目标高度、距离以及风机数量相关。

### 参数说明
- **turbine_height**: 风机高度（米）
- **target_height**: 目标高度（米）
- **distance**: 雷达与目标距离（千米）
- **num_turbines**: 风机数量

## 2. 散射损耗 (Scattering Loss)

### 计算公式

$$
\text{effective\_rcs} = \text{base\_rcs} \times \text{incidence\_factor} \times \text{distance\_factor} \times \text{freq\_factor}
$$

$$
\text{scattering\_power} = \text{effective\_rcs} \times \min(\text{num\_turbines},\ 10)
$$

$$
\text{scattering\_loss\_db} = 10 \times \log_{10}\left(1 + \frac{\text{scattering\_power}}{1000}\right)
$$

### 物理原理

散射效应基于雷达截面积（RCS）模型，风机作为散射体会将雷达信号向各个方向散射，造成信号能量损失。散射强度与入射角、距离、频率相关。

### 参数说明
- **radar_band**: 雷达波段（L、S、C、X、Ku）
- **turbine_distance**: 风机与目标距离（千米）
- **incidence_angle**: 入射角（度）
- **num_turbines**: 风机数量

## 3. 绕射损耗 (Diffraction Loss)

### 计算公式

$$
v_{\text{parameter}} = \text{turbine\_height} \times \sqrt{\frac{2}{\text{wavelength} \times \text{turbine\_distance} \times 1000}}
$$

$$
\text{diffraction\_loss\_db} = 
\begin{cases}
6.9 + 20 \times \log_{10}\left(\sqrt{(v_{\text{parameter}} - 0.1)^2 + 1} + v_{\text{parameter}} - 0.1\right), & \text{if } v_{\text{parameter}} > -0.8 \\
0, & \text{otherwise}
\end{cases}
$$

### 物理原理

绕射效应基于刃形绕射模型，当雷达信号遇到风机边缘时会发生绕射，信号能量会绕过障碍物传播，但会产生额外的损耗。

### 参数说明
- **radar_band**: 雷达波段
- **turbine_distance**: 风机距离（千米）
- **turbine_height**: 风机高度（米）
- **num_turbines**: 风机数量

## 4. 多普勒扩展 (Doppler Spread)

### 计算公式

$$
\text{wavelength} = \frac{3 \times 10^8}{\text{freq}}
$$

$$
\text{target\_doppler} = \frac{2 \times \text{target\_speed}}{\text{wavelength}}
$$

$$
\text{blade\_doppler\_max} = \frac{2 \times \text{blade\_tip\_speed}}{\text{wavelength}}
$$

$$
\text{doppler\_spread} = \text{blade\_doppler\_max} \times \sqrt{\text{num\_turbines}}
$$

### 物理原理

多普勒效应由目标运动和风机叶片旋转引起，会导致雷达回波频率发生偏移。多风机环境下，不同风机的叶片旋转会产生多普勒扩展。

### 参数说明
- **freq**: 雷达频率（Hz）
- **target_speed**: 目标速度（m/s）
- **blade_speed**: 叶片尖端速度（m/s）
- **num_turbines**: 风机数量

## 5. 测角误差 (Angle Measurement Error)

### 计算公式

$$
\text{multipath\_phase\_shift} = \frac{2 \times \pi \times \text{turbine\_distance} \times 1000}{\text{wavelength}} \times \sin(\text{incidence\_angle})
$$

$$
\text{angle\_error\_deg} = \text{degrees}\left(\frac{\text{wavelength}}{4 \times \pi \times \text{turbine\_distance} \times 1000}\right) \times 10
$$

$$
\text{multi\_turbine\_error} = \text{angle\_error\_deg} \times \sqrt{\min(\text{num\_turbines},\ 5)}
$$

### 物理原理

测角误差主要由多径效应引起，雷达信号经过风机反射后与直达信号叠加，导致相位畸变，从而影响角度测量精度。

### 参数说明
- **radar_band**: 雷达波段
- **turbine_distance**: 风机距离（千米）
- **incidence_angle**: 入射角（度）
- **num_turbines**: 风机数量

## 6. 测距误差 (Range Measurement Error)

### 计算公式

$$
\text{range\_error} = \text{wavelength} \times 0.01 \times \log(1 + \text{turbine\_distance}) \times \sqrt{\text{num\_turbines}}
$$

### 物理原理

测距误差由多径时延引起，反射路径比直达路径更长，导致时间延迟，影响距离测量精度。多风机环境下时延扩展更显著。

### 参数说明
- **radar_band**: 雷达波段
- **turbine_distance**: 风机距离（千米）
- **num_turbines**: 风机数量

## 7. 测速误差 (Velocity Measurement Error)

### 计算公式

$$
\text{velocity\_error} = \text{doppler\_spread} \times 0.1 \times \sqrt{\text{num\_turbines}}
$$

$$
\text{measurement\_accuracy\_loss} = \min(0.3,\ 0.05 \times \text{num\_turbines})
$$

### 物理原理

测速误差由多普勒扩展引起，频域扩展导致速度测量不确定性增加。风机数量越多，多普勒扩展越宽，测速精度越低。

### 参数说明
- **doppler_spread**: 多普勒扩展（Hz）
- **target_velocity**: 目标速度（m/s）
- **num_turbines**: 风机数量

## 8. 多径衰落 (Multipath Fading)

### 计算公式

$$
\text{multipath\_fading\_depth\_db} = 20 \times \log_{10}\left(1 + 0.5 \times \sqrt{\text{num\_turbines}}\right)
$$

$$
\text{delay\_spread} = \text{time\_delay} \times \sqrt{\text{num\_turbines}} \times 10^6
$$

$$
\text{coherence\_bandwidth} = \frac{1}{2 \times \pi \times \text{delay\_spread} \times 10^{-6}} \div 10^6
$$

### 物理原理

多径衰落由多条传播路径信号干涉引起，当路径差为半波长奇数倍时产生相消干涉，导致深度衰落。多风机环境增加了多径复杂性。

### 参数说明
- **radar_band**: 雷达波段
- **turbine_distance**: 风机距离（千米）
- **incidence_angle**: 入射角（度）
- **num_turbines**: 风机数量

## 9. 总影响评分 (Total Impact Score)

### 计算公式

$$
\begin{aligned}
\text{total\_impact\_score} = & \ \text{遮挡损耗\_db} \times 0.15 \\
& + \ \text{散射损耗\_db} \times 0.2 \\
& + \ \text{绕射损耗\_db} \times 0.1 \\
& + \ |\text{速度测量误差}| \times 0.1 \\
& + \ \text{测角误差\_度} \times 0.1 \\
& + \ \text{测距误差\_m} \times 0.1 \\
& + \ \text{测速误差\_m/s} \times 0.05 \\
& + \ \text{多径衰落\_db} \times 0.2
\end{aligned}
$$

### 物理原理

总影响评分是各项指标的加权综合，反映了风机对雷达性能的总体影响程度。权重分配基于各项指标的相对重要性和影响程度。

### 风险等级划分
- **极高风险**: 总影响评分 > 15
- **高风险**: 总影响评分 > 10
- **中等风险**: 总影响评分 > 5
- **低风险**: 总影响评分 > 2
- **可接受风险**: 总影响评分 ≤ 2
"""
    
    # 显示方法说明
    st.markdown(methods_markdown)
    
    # 复制Markdown源码功能
    st.markdown("---")
    st.markdown("### 📋 Markdown源码")
    
    # 显示源码（可复制）
    st.code(methods_markdown, language="markdown")
    
    # 创建复制按钮（使用HTML/JavaScript） - 改进版
    copy_html = f'''
    <div style="margin: 10px 0;">
        <button id="copyButton" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        ">
            📋 复制Markdown源码
        </button>
        <span id="copyStatus" style="margin-left: 10px; font-weight: bold;"></span>
        <div id="markdownContent" style="display: none;">{methods_markdown}</div>
    </div>
    
    <script>
    document.getElementById('copyButton').addEventListener('click', function() {{
        const markdownContent = document.getElementById('markdownContent').textContent;
        const textArea = document.createElement('textarea');
        textArea.value = markdownContent;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {{
            const successful = document.execCommand('copy');
            if (successful) {{
                document.getElementById('copyStatus').innerHTML = '<span style="color: green;">✅ 已复制到剪贴板！</span>';
                setTimeout(() => {{
                    document.getElementById('copyStatus').textContent = '';
                }}, 3000);
            }} else {{
                document.getElementById('copyStatus').innerHTML = '<span style="color: red;">❌ 复制失败</span>';
            }}
        }} catch (err) {{
            document.getElementById('copyStatus').innerHTML = '<span style="color: red;">❌ 复制错误：' + err + '</span>';
        }}
        
        document.body.removeChild(textArea);
    }});
    </script>
    '''
    
    components.html(copy_html, height=120)
    
    # 下载按钮（备选方案）
    st.download_button(
        label="📥 下载Markdown文件",
        data=methods_markdown,
        file_name="指标计算方法与原理.md",
        mime="text/markdown",
        type="secondary"
    )





def create_distance_based_analysis_interface(analyzer, base_params):
    """创建不同距离目标下细分指标对比分析界面"""
    st.markdown('<div class="section-header">📏 不同距离目标的细分指标对比分析</div>', unsafe_allow_html=True)
    
    # 仿真配置面板
    st.markdown("### 🎛️ 仿真配置")
    config_col1, config_col2, config_col3 = st.columns([1, 1, 1])
    
    with config_col1:
        max_turbines = st.slider("最大风机数量", 1, 50, base_params.get('max_turbines', 30), 
                                help="设置分析中考虑的最大风机数量")
        curve_count = st.slider("曲线条数", 1, 10, 6, 
                               help="选择在图表中显示的风机数量曲线条数")
    
    with config_col2:
        # 距离范围配置
        distance_min = st.number_input("最小距离 (km)", -50.0, 50.0, -50.0, 1.0,
                                      help="目标距风机的最小距离，负值表示目标在风机另一侧")
        distance_max = st.number_input("最大距离 (km)", -50.0, 50.0, 50.0, 1.0,
                                      help="目标距风机的最大距离")
        distance_points = st.slider("距离点数", 10, 200, 101,
                                   help="距离轴上的采样点数")
    
    with config_col3:
        # 指标选择
        st.markdown("**选择分析指标**")
        metrics_options = {
            '遮挡损耗': True,
            '散射损耗': True,
            '绕射损耗': True,
            '多普勒扩展': True,
            '测角误差': True,
            '测距误差': True,
            '测速误差': True,
            '多径衰落': True,
            '总影响评分': True
        }
        
        # 创建多选框
        selected_metrics = []
        for metric in metrics_options:
            if st.checkbox(metric, value=metrics_options[metric], key=f"metric_{metric}"):
                selected_metrics.append(metric)
    
    # 如果未选择任何指标，提示用户
    if not selected_metrics:
        st.warning("请至少选择一个分析指标")
        return
    
    # 生成距离数组
    distances = np.linspace(distance_min, distance_max, distance_points)
    
    # 生成风机数量列表（均匀分布）
    if curve_count == 1:
        num_turbines_list = [1]
    else:
        step = max(1, (max_turbines - 1) // (curve_count - 1))
        num_turbines_list = [1 + i * step for i in range(curve_count)]
        # 确保最后一个元素不超过max_turbines
        num_turbines_list = [n for n in num_turbines_list if n <= max_turbines]
        if num_turbines_list[-1] != max_turbines:
            num_turbines_list.append(max_turbines)
    
    # 运行分析按钮
    if st.button("🚀 运行距离影响分析", type="primary"):
        with st.spinner("正在计算不同距离下的指标影响..."):
            # 存储结果
            results = {}
            
            # 为每个指标预分配结果数组
            for metric in selected_metrics:
                results[metric] = {}
                for num_turbines in num_turbines_list:
                    results[metric][num_turbines] = []
            
            # 为每个距离点计算指标
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, turbine_distance in enumerate(distances):
                status_text.text(f"计算距离点 {i+1}/{len(distances)}: {turbine_distance:.1f} km")
                
                # 更新参数：使用传入的base_params，但替换turbine_distance
                current_params = base_params.copy()
                current_params['turbine_distance'] = turbine_distance
                
                for num_turbines in num_turbines_list:
                    # 计算各项指标
                    shadowing = analyzer.calculate_shadowing_effect(
                        current_params['turbine_height'],
                        current_params['target_height'],
                        turbine_distance,
                        num_turbines
                    )
                    
                    scattering = analyzer.calculate_scattering_effect(
                        current_params['radar_band'],
                        turbine_distance,
                        current_params['incidence_angle'],
                        num_turbines
                    )
                    
                    diffraction = analyzer.calculate_diffraction_effect(
                        current_params['radar_band'],
                        turbine_distance,
                        current_params['turbine_height'],
                        num_turbines
                    )
                    
                    doppler = analyzer.calculate_doppler_effects(
                        analyzer.radar_bands[current_params['radar_band']]["freq"],
                        current_params['target_speed'],
                        num_turbines=num_turbines
                    )
                    
                    angle_error = analyzer.calculate_angle_measurement_error(
                        current_params['radar_band'],
                        turbine_distance,
                        current_params['incidence_angle'],
                        num_turbines
                    )
                    
                    range_error = analyzer.calculate_range_measurement_error(
                        current_params['radar_band'],
                        turbine_distance,
                        num_turbines
                    )
                    
                    velocity_error = analyzer.calculate_velocity_measurement_error(
                        doppler['doppler_spread_hz'],
                        current_params['target_speed'],
                        num_turbines
                    )
                    
                    multipath = analyzer.calculate_multipath_effects(
                        current_params['radar_band'],
                        turbine_distance,
                        current_params['turbine_height'],
                        current_params['incidence_angle'],
                        num_turbines
                    )
                    
                    # 综合影响评分
                    total_impact_score = (
                        shadowing['shadow_loss_db'] * 0.15 +
                        scattering['scattering_loss_db'] * 0.2 +
                        diffraction['diffraction_loss_db'] * 0.1 +
                        abs(doppler['velocity_measurement_error']) * 0.1 +
                        angle_error['angle_error_deg'] * 0.1 +
                        range_error['range_error_m'] * 0.1 +
                        velocity_error['velocity_error_ms'] * 0.05 +
                        multipath['multipath_fading_depth_db'] * 0.2
                    )
                    
                    # 存储结果
                    if '遮挡损耗' in selected_metrics:
                        results['遮挡损耗'][num_turbines].append(shadowing['shadow_loss_db'])
                    if '散射损耗' in selected_metrics:
                        results['散射损耗'][num_turbines].append(scattering['scattering_loss_db'])
                    if '绕射损耗' in selected_metrics:
                        results['绕射损耗'][num_turbines].append(diffraction['diffraction_loss_db'])
                    if '多普勒扩展' in selected_metrics:
                        results['多普勒扩展'][num_turbines].append(doppler['doppler_spread_hz'])
                    if '测角误差' in selected_metrics:
                        results['测角误差'][num_turbines].append(angle_error['angle_error_deg'])
                    if '测距误差' in selected_metrics:
                        results['测距误差'][num_turbines].append(range_error['range_error_m'])
                    if '测速误差' in selected_metrics:
                        results['测速误差'][num_turbines].append(velocity_error['velocity_error_ms'])
                    if '多径衰落' in selected_metrics:
                        results['多径衰落'][num_turbines].append(multipath['multipath_fading_depth_db'])
                    if '总影响评分' in selected_metrics:
                        results['总影响评分'][num_turbines].append(total_impact_score)
                
                # 更新进度条
                progress_bar.progress((i + 1) / len(distances))
            
            status_text.text("✅ 分析完成！")
            
            # 将结果存储到session_state
            st.session_state.distance_analysis_results = results
            st.session_state.distance_analysis_distances = distances
            st.session_state.distance_analysis_turbines = num_turbines_list
    
    # 如果已有分析结果，显示图表
    if 'distance_analysis_results' in st.session_state:
        results = st.session_state.distance_analysis_results
        distances = st.session_state.distance_analysis_distances
        num_turbines_list = st.session_state.distance_analysis_turbines
        
        # 为每个选中的指标创建图表
        for metric in selected_metrics:
            st.markdown(f"### 📈 {metric} vs 距离")
            
            fig = go.Figure()
            
            # 为每个风机数量添加曲线
            for num_turbines in num_turbines_list:
                if num_turbines in results[metric]:
                    fig.add_trace(go.Scatter(
                        x=distances,
                        y=results[metric][num_turbines],
                        mode='lines',
                        name=f'{num_turbines}个风机',
                        line=dict(width=2)
                    ))
            
            # 更新图表布局
            fig.update_layout(
                title=f"{metric}随目标距风机距离的变化",
                xaxis_title="目标距风机距离 (km)",
                yaxis_title=f"{metric}值",
                height=500,
                template="plotly_white",
                font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12),
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 提供数据下载
        st.markdown("### 📥 数据下载")
        
        # 创建DataFrame格式的数据
        download_data = []
        for i, distance in enumerate(distances):
            row = {'距离_km': distance}
            for metric in selected_metrics:
                for num_turbines in num_turbines_list:
                    if num_turbines in results[metric] and i < len(results[metric][num_turbines]):
                        row[f'{metric}_{num_turbines}风机'] = results[metric][num_turbines][i]
            download_data.append(row)
        
        download_df = pd.DataFrame(download_data)
        csv_data = download_df.to_csv(index=False)
        
        st.download_button(
            label="📋 下载分析数据 (CSV)",
            data=csv_data,
            file_name=f"距离影响分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="secondary"
        )


# Kimi API配置
KIMI_API_CONFIG = {
    "base_url": "https://api.moonshot.cn/v1",
    "chat_completion_endpoint": "/chat/completions",
    # "model": "kimi-k2.5",
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
        self.data_dir = self.outputs_dir / "data"
        print(f"[MetricAnalysisEngine] 输出目录: {self.outputs_dir.absolute()}")
        print(f"[MetricAnalysisEngine] 图片目录: {self.images_dir.absolute()}")
        print(f"[MetricAnalysisEngine] 数据目录: {self.data_dir.absolute()}")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        print(f"[MetricAnalysisEngine] 目录创建成功: 图片目录={self.images_dir.exists()}, 数据目录={self.data_dir.exists()}")
        
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
            # 更新plotly_white模板的字体设置
            pio.templates["plotly_white"].update(
                layout=dict(font=dict(family="SimHei, 黑体, Arial, sans-serif", size=12))
            )
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
    
    def analyze_all_metrics(self, comparison_data: pd.DataFrame, scenario_params: dict, enable_ai_analysis: bool = False) -> dict:
        """
        枚举所有细分指标并进行主题分析
        
        参数:
            comparison_data: 包含所有指标数据的DataFrame
            scenario_params: 场景参数
            enable_ai_analysis: 是否启用AI分析，默认为False
            
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
            table_path = self.data_dir / table_filename
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
                    # 使用matplotlib保存图表
                    chart_saved = False
                    saved_with_engine = "matplotlib"
                    
                    try:
                        # 保存为PNG，dpi=200确保高清
                        fig.savefig(str(chart_path), dpi=200, bbox_inches='tight')
                        print(f"[MetricAnalysisEngine] 使用matplotlib保存成功: {chart_path}")
                        # 验证文件是否已创建
                        if chart_path.exists():
                            file_size = chart_path.stat().st_size
                            print(f"[MetricAnalysisEngine] 文件已创建，大小: {file_size} 字节")
                            chart_saved = True
                        else:
                            print(f"[MetricAnalysisEngine] 警告: 文件未创建！")
                    except Exception as write_error:
                        print(f"[MetricAnalysisEngine] matplotlib保存失败: {write_error}")
                    finally:
                        # 关闭图形释放内存
                        import matplotlib.pyplot as plt
                        plt.close(fig)
                    

                    chart_path_str = str(chart_path) if chart_saved else ""
                    if chart_saved:
                        print(f"[MetricAnalysisEngine] 最终保存结果: 使用{saved_with_engine}，路径: {chart_path_str}")
                
                # 调用Kimi API分析图表
                ai_analysis = ""
                if enable_ai_analysis:
                    if self.api_key and chart_path_str:  # 只有API密钥有效且图表路径非空时才分析
                        try:
                            ai_analysis = self._analyze_chart_with_kimi(
                                chart_path_str,
                                f"{metric_config['name']}: {metric_config['description']}。图表显示了{metric_column}随风机数量变化趋势。"
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
                else:
                    ai_analysis = "AI分析未启用（用户选择跳过）"
                
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
                
                # 休眠2秒（避免API调用频率限制）
                if i < total_metrics - 1:  # 不是最后一个指标
                    print(f"休眠2秒后开始下一个指标分析...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"指标 {metric_config['name']} 分析失败: {e}")
                continue
        
        print(f"所有指标分析完成！共分析 {len(results['metrics_analysis'])} 个指标")
        return results
    
    def _create_metric_chart(self, metric_data: pd.DataFrame, metric_config: dict, scenario_params: dict) -> Figure:
        """
        创建指标分析图表 - 使用matplotlib解决中文字体问题
        
        参数:
            metric_data: 指标数据
            metric_config: 指标配置
            scenario_params: 场景参数
            
        返回:
            Matplotlib图形对象
        """
        x_data = metric_data['风机数量']
        y_data = metric_data[metric_config['column']]
        
        # 创建图形和坐标轴，尺寸对应800x500像素（8x5英寸，dpi=100）
        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        
        if metric_config['chart_type'] == 'line':
            ax.plot(x_data, y_data, 
                   marker='o', 
                   linestyle='-', 
                   linewidth=3,
                   markersize=8,
                   color=self.color_scheme['primary'],
                   label=metric_config['name'])
        elif metric_config['chart_type'] == 'scatter':
            scatter = ax.scatter(x_data, y_data,
                               c=y_data,
                               s=100,  # 点大小
                               cmap='viridis',
                               label=metric_config['name'])
            # 添加颜色条
            plt.colorbar(scatter, ax=ax)
        elif metric_config['chart_type'] == 'area':
            ax.fill_between(x_data, y_data,
                           color=self.color_scheme['secondary'],
                           alpha=0.3,
                           label=metric_config['name'])
            ax.plot(x_data, y_data,
                   color=self.color_scheme['secondary'],
                   linewidth=2)
        elif metric_config['chart_type'] == 'bar':
            ax.bar(x_data, y_data,
                  color=self.color_scheme['accent'],
                  label=metric_config['name'])
        
        # 设置标题和标签
        ax.set_title(f"{metric_config['name']} - {scenario_params.get('radar_band', '')}",
                    fontsize=14, fontweight='bold')
        ax.set_xlabel("风机数量", fontsize=12)
        ax.set_ylabel(f"{metric_config['name']} ({metric_config['unit']})", fontsize=12)
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7, color='lightgray')
        
        # 添加图例
        ax.legend(fontsize=10)
        
        # 自动调整布局
        plt.tight_layout()
        
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
        
        # 参数显示映射：英文键 -> (中文显示名, 单位)
        param_display_map = {
            'radar_band': ('雷达波段', ''),
            'target_distance': ('目标距离', ' km'),
            'target_height': ('目标高度', ' m'),
            'target_speed': ('目标速度', ' m/s'),
            'turbine_height': ('风机高度', ' m'),
            'turbine_distance': ('目标-风机距离', ' km'),
            'incidence_angle': ('照射角度', '°'),
            'max_turbines': ('最大风机数量', ' 个'),
            'scenario_id': ('场景ID', '')
        }
        
        # 添加场景参数
        for key, value in scenario_params.items():
            if key in param_display_map:
                display_name, unit = param_display_map[key]
                # 格式化值：如果值是数值且单位不为空，添加单位
                if isinstance(value, (int, float)) and unit:
                    formatted_value = f"{value}{unit}"
                else:
                    formatted_value = f"{value}{unit}" if unit else str(value)
                markdown_content += f"| {display_name} | {formatted_value} |\n"
            else:
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
        
        enable_expert_analysis = st.checkbox(
            "启用专家分析（调用Kimi AI进行智能分析）", 
            value=False,
            help="启用后将对每个细分指标图表调用Kimi API进行智能分析，会增加token消耗和分析时间",
            key="enable_expert_analysis_checkbox"
        )
        
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
                        scenario_params=base_params,
                        enable_ai_analysis=enable_expert_analysis
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
        
        # 报告打包下载
        st.markdown("### 📦 报告打包")
        
        # 检查outputs目录是否存在
        outputs_dir = "outputs"
        if os.path.exists(outputs_dir):
            # 查找所有.md文件
            md_files = []
            for root, dirs, files in os.walk(outputs_dir):
                for file in files:
                    if file.endswith('.md'):
                        md_files.append(os.path.join(root, file))
            
            # 检查是否有.md文件
            if md_files:
                col1, col2 = st.columns([1, 2])
                with col1:
                    if st.button("🛠️ 生成报告ZIP文件", type="primary"):
                        with st.spinner("正在打包报告文件..."):
                            # 创建ZIP文件
                            zip_filename = f"radar_impact_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                            zip_buffer = BytesIO()
                            
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                # 添加所有.md文件
                                for md_file in md_files:
                                    arcname = os.path.relpath(md_file, outputs_dir)
                                    zipf.write(md_file, arcname)
                                
                                # 添加images目录（如果存在）
                                images_dir = os.path.join(outputs_dir, 'images')
                                if os.path.exists(images_dir):
                                    for root, dirs, files in os.walk(images_dir):
                                        for file in files:
                                            file_path = os.path.join(root, file)
                                            arcname = os.path.relpath(file_path, outputs_dir)
                                            zipf.write(file_path, arcname)
                                
                                # 添加data目录（如果存在）
                                data_dir = os.path.join(outputs_dir, 'data')
                                if os.path.exists(data_dir):
                                    for root, dirs, files in os.walk(data_dir):
                                        for file in files:
                                            file_path = os.path.join(root, file)
                                            arcname = os.path.relpath(file_path, outputs_dir)
                                            zipf.write(file_path, arcname)
                            
                            zip_buffer.seek(0)
                            st.session_state.zip_data = zip_buffer.read()
                            st.session_state.zip_filename = zip_filename
                            st.success("ZIP文件生成完成！")
                
                with col2:
                    # 如果已有ZIP数据，显示下载按钮
                    if 'zip_data' in st.session_state and 'zip_filename' in st.session_state:
                        st.download_button(
                            label="📦 下载全部报告 (ZIP)",
                            data=st.session_state.zip_data,
                            file_name=st.session_state.zip_filename,
                            mime="application/zip",
                            width='stretch'
                        )
            else:
                st.warning("outputs目录中没有找到.md报告文件。请先运行分析生成报告。")
        else:
            st.warning("outputs目录不存在。请先运行分析生成报告。")
        
        if clear_analysis:
            if 'metric_analysis_results' in st.session_state:
                del st.session_state.metric_analysis_results
            st.session_state.metric_analysis_complete = False
            st.success("✅ 分析结果已清空")
            st.rerun()


def create_parameter_sensitivity_analysis_interface(analyzer, base_params):
    """
    创建交互式参数敏感性分析界面
    
    参数:
        analyzer: AdvancedRadarImpactAnalyzer实例
        base_params: 基础参数配置
    """
    st.markdown('<div class="section-header">🔍 交互式参数敏感性分析</div>', unsafe_allow_html=True)
    
    # 参数选择面板
    st.markdown("### 🎯 选择分析参数")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 定义可分析的参数
        parameter_options = {
            'radar_band': '雷达波段',
            'target_distance': '目标距离 (km)',
            'target_height': '目标高度 (m)',
            'target_speed': '目标速度 (m/s)',
            'turbine_height': '风机高度 (m)',
            'turbine_distance': '目标-风机距离 (km)',
            'incidence_angle': '照射角度 (°)',
            'max_turbines': '最大风机数量'
        }
        
        selected_param_key = st.selectbox(
            "选择要分析的参数",
            list(parameter_options.keys()),
            format_func=lambda x: parameter_options[x],
            key="sensitivity_param_select"
        )
        
        selected_param_name = parameter_options[selected_param_key]
    
    with col2:
        # 分析点数
        num_points = st.slider("分析点数", 5, 50, 20, help="参数范围内采样点数", key="sensitivity_num_points")
    
    # 参数范围配置
    st.markdown("### 📏 参数范围设置")
    
    # 根据参数类型设置不同的范围控件
    if selected_param_key == 'radar_band':
        # 雷达波段是分类变量，显示所有选项
        band_options = ["L波段", "S波段", "C波段", "X波段", "Ku波段"]
        st.info(f"雷达波段为分类变量，将分析所有可能选项：{', '.join(band_options)}")
        param_values = band_options
        param_display = band_options
    else:
        # 数值参数，设置范围
        col_range1, col_range2, col_range3 = st.columns([1, 1, 1])
        
        # 获取当前值作为默认中心
        current_value = base_params.get(selected_param_key, 0)
        
        with col_range1:
            # 根据参数类型设置合理的默认范围
            if selected_param_key == 'target_distance':
                min_val = st.number_input("最小值 (km)", 0.1, 100.0, max(0.1, current_value * 0.5), 0.1, key=f"sensitivity_{selected_param_key}_min")
            elif selected_param_key == 'target_height':
                min_val = st.number_input("最小值 (m)", 10, 10000, max(10, int(current_value * 0.5)), 10, key=f"sensitivity_{selected_param_key}_min")
            elif selected_param_key == 'target_speed':
                min_val = st.number_input("最小值 (m/s)", 1, 200, max(1, int(current_value * 0.5)), 1, key=f"sensitivity_{selected_param_key}_min")
            elif selected_param_key == 'turbine_height':
                min_val = st.number_input("最小值 (m)", 50, 500, max(50, int(current_value * 0.5)), 10, key=f"sensitivity_{selected_param_key}_min")
            elif selected_param_key == 'turbine_distance':
                min_val = st.number_input("最小值 (km)", 0.1, 50.0, max(0.1, current_value * 0.5), 0.1, key=f"sensitivity_{selected_param_key}_min")
            elif selected_param_key == 'incidence_angle':
                min_val = st.number_input("最小值 (°)", 0, 180, max(0, int(current_value * 0.5)), 1, key=f"sensitivity_{selected_param_key}_min")
            elif selected_param_key == 'max_turbines':
                min_val = st.number_input("最小值", 1, 100, max(1, int(current_value * 0.5)), 1, key=f"sensitivity_{selected_param_key}_min")
            else:
                min_val = st.number_input("最小值", 0.0, 1000.0, max(0.0, current_value * 0.5), 0.1, key=f"sensitivity_{selected_param_key}_min")
        
        with col_range2:
            if selected_param_key == 'target_distance':
                max_val = st.number_input("最大值 (km)", 0.1, 100.0, min(100.0, current_value * 2.0), 0.1, key=f"sensitivity_{selected_param_key}_max")
            elif selected_param_key == 'target_height':
                max_val = st.number_input("最大值 (m)", 10, 10000, min(10000, int(current_value * 2.0)), 10, key=f"sensitivity_{selected_param_key}_max")
            elif selected_param_key == 'target_speed':
                max_val = st.number_input("最大值 (m/s)", 1, 200, min(200, int(current_value * 2.0)), 1, key=f"sensitivity_{selected_param_key}_max")
            elif selected_param_key == 'turbine_height':
                max_val = st.number_input("最大值 (m)", 50, 500, min(500, int(current_value * 2.0)), 10, key=f"sensitivity_{selected_param_key}_max")
            elif selected_param_key == 'turbine_distance':
                max_val = st.number_input("最大值 (km)", 0.1, 50.0, min(50.0, current_value * 2.0), 0.1, key=f"sensitivity_{selected_param_key}_max")
            elif selected_param_key == 'incidence_angle':
                max_val = st.number_input("最大值 (°)", 0, 180, min(180, int(current_value * 2.0)), 1, key=f"sensitivity_{selected_param_key}_max")
            elif selected_param_key == 'max_turbines':
                max_val = st.number_input("最大值", 1, 100, min(100, int(current_value * 2.0)), 1, key=f"sensitivity_{selected_param_key}_max")
            else:
                max_val = st.number_input("最大值", 0.0, 1000.0, min(1000.0, current_value * 2.0), 0.1, key=f"sensitivity_{selected_param_key}_max")
        
        with col_range3:
            st.metric("当前值", current_value)
        
        # 生成参数值序列
        param_values = np.linspace(min_val, max_val, num_points)
        param_display = param_values
    
    # 分析按钮
    st.markdown("### 🚀 运行敏感性分析")
    run_analysis = st.button("开始分析", type="primary", help="运行参数敏感性分析")
    
    if run_analysis:
        with st.spinner(f"正在分析 {selected_param_name} 的敏感性..."):
            # 初始化结果存储
            results = []
            
            # 对每个参数值进行计算
            for i, param_value in enumerate(param_values):
                # 复制基础参数
                modified_params = base_params.copy()
                
                # 更新选定的参数
                if selected_param_key == 'radar_band':
                    modified_params[selected_param_key] = param_value
                else:
                    # 数值参数转换为适当类型
                    if selected_param_key in ['target_distance', 'turbine_distance']:
                        modified_params[selected_param_key] = float(param_value)
                    elif selected_param_key in ['target_height', 'target_speed', 'turbine_height', 'incidence_angle', 'max_turbines']:
                        modified_params[selected_param_key] = int(param_value)
                    else:
                        modified_params[selected_param_key] = param_value
                
                # 计算单风机场景（固定风机数量为1）
                modified_params['max_turbines'] = 1
                
                # 使用分析器计算影响
                try:
                    # 调用现有的对比分析函数，但只计算单风机
                    comparison_df = analyzer.evaluate_single_vs_multiple_turbines(modified_params)
                    
                    # 提取单风机结果（第一个行）
                    if not comparison_df.empty:
                        single_result = comparison_df.iloc[0]
                        
                        result = {
                            '参数值': param_value,
                            '总影响评分': single_result['总影响评分'],
                            '遮挡损耗_db': single_result['遮挡损耗_db'],
                            '散射损耗_db': single_result['散射损耗_db'],
                            '多径衰落_db': single_result['多径衰落_db'],
                            '测角误差_度': single_result['测角误差_度'],
                            '测距误差_m': single_result['测距误差_m']
                        }
                        results.append(result)
                    
                except Exception as e:
                    st.warning(f"参数值 {param_value} 计算失败: {str(e)}")
                    continue
            
            if results:
                # 转换为DataFrame
                results_df = pd.DataFrame(results)
                
                # 保存到session state
                st.session_state.sensitivity_results = results_df
                st.session_state.sensitivity_param = selected_param_key
                st.session_state.sensitivity_param_name = selected_param_name
                st.session_state.sensitivity_param_values = param_display
                
                st.success(f"✅ 敏感性分析完成！共分析 {len(results)} 个参数点。")
                
                # 显示结果
                display_sensitivity_results(results_df, selected_param_key, selected_param_name, param_display)
            else:
                st.error("❌ 无法计算任何结果，请检查参数设置。")
    elif 'sensitivity_results' in st.session_state and st.session_state.sensitivity_param == selected_param_key:
        # 从session state中读取保存的结果
        results_df = st.session_state.sensitivity_results
        param_key = st.session_state.sensitivity_param
        param_name = st.session_state.sensitivity_param_name
        param_display = st.session_state.sensitivity_param_values
        # 显示结果
        display_sensitivity_results(results_df, param_key, param_name, param_display)


def display_sensitivity_results(results_df, param_key, param_name, param_values):
    """
    显示敏感性分析结果
    
    参数:
        results_df: 包含结果的DataFrame
        param_key: 参数键名
        param_name: 参数显示名称
        param_values: 参数值数组
    """
    # 判断是否为分类变量（目前只有雷达波段）
    is_categorical = param_key == 'radar_band'
    
    # 创建子标签页
    subtab1, subtab2, subtab3 = st.tabs(["📈 动态响应曲线", "🔥 敏感性热力图", "💡 参数优化建议"])
    
    with subtab1:
        st.markdown(f"### 📈 {param_name} 对总影响评分的动态响应")
        
        # 创建响应曲线图
        fig = go.Figure()
        
        if is_categorical:
            # 分类变量使用条形图
            fig.add_trace(go.Bar(
                x=results_df['参数值'],
                y=results_df['总影响评分'],
                name='总影响评分',
                marker_color='#1f77b4',
                hovertemplate=(
                    f'{param_name}: %{{x}}<br>'
                    '总影响评分: %{y:.2f}<br>'
                    '<extra></extra>'
                )
            ))
            
            # 添加其他指标曲线（可选）
            metrics_to_plot = st.multiselect(
                "选择要显示的指标",
                ['遮挡损耗_db', '散射损耗_db', '多径衰落_db', '测角误差_度', '测距误差_m'],
                default=['遮挡损耗_db', '散射损耗_db'],
                key=f"metrics_selector_categorical_{param_key}"
            )
            
            # 颜色映射
            colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for i, metric in enumerate(metrics_to_plot):
                if i < len(colors):
                    fig.add_trace(go.Bar(
                        x=results_df['参数值'],
                        y=results_df[metric],
                        name=metric,
                        marker_color=colors[i],
                        yaxis='y2',
                        hovertemplate=(
                            f'{param_name}: %{{x}}<br>'
                            f'{metric}: %{{y:.2f}}<br>'
                            '<extra></extra>'
                        )
                    ))
            
            # 布局配置
            fig.update_layout(
                title=f'{param_name} 敏感性分析 - 条形图',
                xaxis_title=param_name,
                yaxis_title='总影响评分',
                yaxis2=dict(
                    title='指标值',
                    overlaying='y',
                    side='right'
                ),
                barmode='group',
                hovermode='x unified',
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
        else:
            # 数值变量使用折线图
            fig.add_trace(go.Scatter(
                x=results_df['参数值'],
                y=results_df['总影响评分'],
                mode='lines+markers',
                name='总影响评分',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8),
                hovertemplate=(
                    f'{param_name}: %{{x}}<br>'
                    '总影响评分: %{y:.2f}<br>'
                    '<extra></extra>'
                )
            ))
            
            # 添加其他指标曲线（可选）
            metrics_to_plot = st.multiselect(
                "选择要显示的指标",
                ['遮挡损耗_db', '散射损耗_db', '多径衰落_db', '测角误差_度', '测距误差_m'],
                default=['遮挡损耗_db', '散射损耗_db'],
                key=f"metrics_selector_numeric_{param_key}"
            )
            
            # 颜色映射
            colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for i, metric in enumerate(metrics_to_plot):
                if i < len(colors):
                    fig.add_trace(go.Scatter(
                        x=results_df['参数值'],
                        y=results_df[metric],
                        mode='lines',
                        name=metric,
                        line=dict(color=colors[i], width=2, dash='dash'),
                        yaxis='y2',
                        hovertemplate=(
                            f'{param_name}: %{{x}}<br>'
                            f'{metric}: %{{y:.2f}}<br>'
                            '<extra></extra>'
                        )
                    ))
            
            # 布局配置
            fig.update_layout(
                title=f'{param_name} 敏感性分析 - 动态响应曲线',
                xaxis_title=param_name,
                yaxis_title='总影响评分',
                yaxis2=dict(
                    title='指标值',
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified',
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示关键点
        st.markdown("#### 📊 关键分析点")
        col_k1, col_k2, col_k3 = st.columns(3)
        
        with col_k1:
            max_impact_idx = results_df['总影响评分'].idxmax()
            max_impact_value = results_df.loc[max_impact_idx, '参数值']
            max_impact_score = results_df.loc[max_impact_idx, '总影响评分']
            st.metric("最大影响点", f"{max_impact_value}", f"评分: {max_impact_score:.1f}")
        
        with col_k2:
            min_impact_idx = results_df['总影响评分'].idxmin()
            min_impact_value = results_df.loc[min_impact_idx, '参数值']
            min_impact_score = results_df.loc[min_impact_idx, '总影响评分']
            st.metric("最小影响点", f"{min_impact_value}", f"评分: {min_impact_score:.1f}")
        
        with col_k3:
            if not is_categorical and len(results_df) > 1:
                # 计算敏感性指数（导数近似）仅用于数值变量
                try:
                    sensitivity = np.gradient(results_df['总影响评分'], results_df['参数值'].astype(float))
                    max_sensitivity_idx = np.argmax(np.abs(sensitivity))
                    max_sensitivity_value = results_df.loc[max_sensitivity_idx, '参数值']
                    max_sensitivity = sensitivity[max_sensitivity_idx]
                    st.metric("最敏感点", f"{max_sensitivity_value}", f"斜率: {max_sensitivity:.3f}")
                except Exception as e:
                    st.info("无法计算敏感性指数")
            else:
                st.info("分类变量不计算敏感性指数")
    
    with subtab2:
        st.markdown(f"### 🔥 {param_name} 对各指标的敏感性热力图")
        
        if is_categorical:
            # 分类变量显示分组条形图
            metrics = ['总影响评分', '遮挡损耗_db', '散射损耗_db', '多径衰落_db', '测角误差_度', '测距误差_m']
            available_metrics = [m for m in metrics if m in results_df.columns]
            
            if len(available_metrics) > 0:
                # 创建分组条形图
                fig = go.Figure()
                
                # 颜色映射
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
                
                for i, metric in enumerate(available_metrics):
                    if i < len(colors):
                        fig.add_trace(go.Bar(
                            x=results_df['参数值'],
                            y=results_df[metric],
                            name=metric,
                            marker_color=colors[i],
                            hovertemplate=(
                                f'{param_name}: %{{x}}<br>'
                                f'{metric}: %{{y:.2f}}<br>'
                                '<extra></extra>'
                            )
                        ))
                
                fig.update_layout(
                    title=f'{param_name} 对各指标的影响 - 分组条形图',
                    xaxis_title=param_name,
                    yaxis_title='指标值',
                    barmode='group',
                    height=400,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 显示指标排名（按平均值）
                st.markdown("#### 🏆 指标影响排名")
                avg_values = []
                for metric in available_metrics:
                    avg_values.append(results_df[metric].mean())
                
                ranking_df = pd.DataFrame({
                    '指标': available_metrics,
                    '平均值': avg_values
                }).sort_values('平均值', ascending=False)
                
                st.dataframe(ranking_df, width='stretch')
            else:
                st.info("没有可用的指标数据")
        else:
            # 数值变量使用热力图
            metrics = ['总影响评分', '遮挡损耗_db', '散射损耗_db', '多径衰落_db', '测角误差_度', '测距误差_m']
            
            # 只选择存在的指标
            available_metrics = [m for m in metrics if m in results_df.columns]
            
            if len(available_metrics) > 1:
                # 确保参数值为数值类型
                param_array = results_df['参数值'].astype(float).values
                
                # 计算每个指标的敏感性（梯度绝对值）
                sensitivity_matrix = []
                
                for metric in available_metrics:
                    metric_values = results_df[metric].values
                    if len(metric_values) > 1:
                        # 计算梯度并取绝对值
                        try:
                            gradient = np.abs(np.gradient(metric_values, param_array))
                            sensitivity_matrix.append(gradient)
                        except:
                            sensitivity_matrix.append(np.zeros_like(param_array))
                    else:
                        sensitivity_matrix.append(np.zeros_like(param_array))
                
                sensitivity_matrix = np.array(sensitivity_matrix)
                
                # 创建热力图
                fig = go.Figure(data=go.Heatmap(
                    z=sensitivity_matrix,
                    x=param_array,
                    y=available_metrics,
                    colorscale='RdYlBu_r',  # 红色表示高敏感性
                    colorbar=dict(title="敏感性强度"),
                    hovertemplate=(
                        f'{param_name}: %{{x}}<br>'
                        '指标: %{y}<br>'
                        '敏感性: %{z:.4f}<br>'
                        '<extra></extra>'
                    )
                ))
                
                fig.update_layout(
                    title=f'{param_name} 对各指标的敏感性热力图',
                    xaxis_title=param_name,
                    yaxis_title='指标',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 显示敏感性排名
                st.markdown("#### 🏆 敏感性排名")
                
                # 计算平均敏感性
                avg_sensitivity = sensitivity_matrix.mean(axis=1)
                ranking_df = pd.DataFrame({
                    '指标': available_metrics,
                    '平均敏感性': avg_sensitivity
                }).sort_values('平均敏感性', ascending=False)
                
                st.dataframe(ranking_df, width='stretch')
            else:
                st.info("需要至少2个指标来计算敏感性热力图")
    
    with subtab3:
        st.markdown(f"### 💡 {param_name} 优化建议")
        
        # 分析结果并提供建议
        if len(results_df) > 1:
            # 提取关键数据
            param_vals = results_df['参数值'].values
            impact_scores = results_df['总影响评分'].values
            
            if not is_categorical:
                # 寻找最优参数范围（影响评分最低）仅用于数值变量
                optimal_range_threshold = impact_scores.min() * 1.2  # 允许20%的容忍度
                optimal_indices = np.where(impact_scores <= optimal_range_threshold)[0]
                
                if len(optimal_indices) > 0:
                    optimal_min = param_vals[optimal_indices[0]]
                    optimal_max = param_vals[optimal_indices[-1]]
                    
                    st.success(f"✅ **推荐参数范围**: {optimal_min:.2f} ~ {optimal_max:.2f}")
                    st.markdown(f"在此范围内，总影响评分保持在 {optimal_range_threshold:.2f} 以下")
            
            # 提供具体建议
            st.markdown("#### 📋 具体优化建议")
            
            if param_key == 'radar_band':
                # 雷达波段建议
                best_band_idx = impact_scores.argmin()
                best_band = param_vals[best_band_idx]
                worst_band_idx = impact_scores.argmax()
                worst_band = param_vals[worst_band_idx]
                
                st.markdown(f"""
                1. **最佳波段**: **{best_band}** (总影响评分: {impact_scores[best_band_idx]:.1f})
                2. **最差波段**: {worst_band} (总影响评分: {impact_scores[worst_band_idx]:.1f})
                3. **建议**: 优先选择 {best_band}，避免使用 {worst_band}
                """)
            
            elif param_key == 'turbine_distance':
                # 目标-风机距离建议
                st.markdown("""
                1. **安全距离**: 保持至少 2-3 km 的距离可显著降低影响
                2. **临界点**: 距离小于 1 km 时影响急剧增加
                3. **建议**: 规划风电场时，确保雷达视线与风机保持足够距离
                """)
            
            elif param_key == 'incidence_angle':
                # 照射角度建议
                st.markdown("""
                1. **最佳角度**: 0-30° 或 150-180° (侧向照射) 影响较小
                2. **最差角度**: 90° (正面照射) 影响最大
                3. **建议**: 调整雷达部署位置，避免正对风机叶片
                """)
            
            else:
                # 通用建议
                if is_categorical:
                    st.markdown(f"""
                    1. **类别分析**: 不同{param_name}对总影响评分的差异已在上方图表中展示
                    2. **操作建议**: 选择影响评分最低的类别
                    3. **监控建议**: 在实际应用中持续监控不同类别对系统性能的影响
                    """)
                else:
                    st.markdown(f"""
                    1. **趋势分析**: 参数变化与总影响评分的关系已在上方曲线中展示
                    2. **操作建议**: 根据曲线趋势，调整参数至低影响区域
                    3. **监控建议**: 在实际应用中持续监控该参数对系统性能的影响
                    """)
            
            # 提供数据下载
            st.markdown("#### 📥 结果下载")
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                label="下载敏感性分析数据 (CSV)",
                data=csv_data,
                file_name=f"sensitivity_analysis_{param_key}.csv",
                mime="text/csv"
            )
        else:
            st.info("需要足够的数据点来生成优化建议")


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
        target_distance = st.slider("目标距离 (km)", 1.0, 150.0, 12.0, 1.0)
        target_height = st.slider("目标高度 (m)", 10, 5000, 300)
        target_speed = st.slider("目标速度 (m/s)", 1, 100, 20)
    
    with st.sidebar.expander("风机参数"):
        turbine_height = st.slider("风机高度 (m)", 50, 300, 185)
        turbine_distance = st.slider("目标-风机距离 (km)", 0.1, 50.0, 1.0, 0.5)
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
    tab1, tab2, tab3, tab4 = st.tabs(["🔬 单风机vs多风机分析", "📏 不同距离目标的细分指标对比分析", "🔍 交互式参数敏感性分析", "📚 指标计算方法与原理"])
    
    with tab1:
        create_advanced_analysis_interface(analyzer, base_params)

    with tab2:
        create_distance_based_analysis_interface(analyzer, base_params)
        
    with tab3:
        create_parameter_sensitivity_analysis_interface(analyzer, base_params)
    
    with tab4:
        create_metric_methods_tab(base_params)

if __name__ == "__main__":
    main()