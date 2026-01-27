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

# 页面配置
st.set_page_config(
    page_title="海上风电雷达影响专业分析系统",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            showlegend=True
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
            height=400
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
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '散射影响分析':
            fig = px.bar(comparison_data, x='风机数量', y='散射损耗_db',
                        title='散射损耗随风机数量变化')
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '绕射效应分析':
            fig = px.bar(comparison_data, x='风机数量', y='绕射损耗_db',
                        title='绕射损耗随风机数量变化')
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '多普勒影响':
            fig = px.line(comparison_data, x='风机数量', y='多普勒扩展_Hz',
                         title='多普勒扩展随风机数量变化')
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测角误差分析':
            fig = px.scatter(comparison_data, x='风机数量', y='测角误差_度',
                           title='测角误差随风机数量变化')
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测距误差分析':
            fig = px.area(comparison_data, x='风机数量', y='测距误差_m',
                         title='测距误差随风机数量变化')
            st.plotly_chart(fig, width='stretch')
            
        elif metric_choice == '测速误差分析':
            fig = px.line(comparison_data, x='风机数量', y='测速误差_m/s',
                         title='测速误差随风机数量变化')
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
            
            fig.update_layout(height=600, showlegend=False)
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
    tab1, tab2 = st.tabs(["🔬 单风机vs多风机分析", "📊 综合影响评估"])
    
    with tab1:
        create_turbine_comparison_interface(analyzer, base_params)
    
    with tab2:
        st.markdown('<div class="section-header">📊 综合影响评估报告</div>', unsafe_allow_html=True)
        st.info("综合影响评估功能开发中...")
        
        # 这里可以添加更多的综合评估功能
        if 'comparison_data' in st.session_state:
            st.dataframe(st.session_state.comparison_data, width='stretch')

if __name__ == "__main__":
    main()