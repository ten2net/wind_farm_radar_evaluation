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
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
        padding: 1rem;
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%);
        border-radius: 10px;
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
    }
    .wide-container {
        width: 100%;
        margin: 0 auto;
    }
    .full-width {
        width: 100% !important;
    }
    /* 调整标签页样式 */

    /* 调整图表容器 */
    .plotly-chart {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

class RadarImpactAnalyzer:
    """雷达影响分析器"""
    
    def __init__(self):
        self.radar_bands = {
            "L波段": {"freq": 1.5e9, "description": "远程警戒雷达"},
            "S波段": {"freq": 3.0e9, "description": "中程监视雷达"}, 
            "C波段": {"freq": 5.6e9, "description": "气象雷达"},
            "X波段": {"freq": 9.4e9, "description": "海事雷达"},
            "Ku波段": {"freq": 15.0e9, "description": "高精度雷达"}
        }
        
    def calculate_doppler_shift(self, freq, speed, angle_deg):
        """计算多普勒频移"""
        wavelength = 3e8 / freq
        angle_rad = np.radians(angle_deg)
        doppler_shift = 2 * speed * np.cos(angle_rad) / wavelength
        return doppler_shift
    
    def calculate_snr_degradation(self, distance, turbine_distance, incidence_angle, radar_band):
        """计算SNR恶化"""
        # 基于距离的基准SNR
        base_snr = 20 * np.log10(100/distance) if distance > 0 else 0
        
        # 风机引起的附加损耗模型
        angle_factor = 0.5 * (1 - np.cos(np.radians(incidence_angle)))
        distance_factor = 10 * np.log10(max(turbine_distance, 0.1))
        freq = self.radar_bands[radar_band]["freq"]
        freq_factor = 20 * np.log10(freq / 1e9) * 0.1
        
        turbine_loss = angle_factor + distance_factor + freq_factor
        degraded_snr = base_snr - turbine_loss
        
        return base_snr, degraded_snr, turbine_loss
    
    def calculate_detection_probability(self, snr_db):
        """计算探测概率"""
        if snr_db < -10:
            return 0.1
        elif snr_db > 10:
            return 0.95
        else:
            return 0.1 + 0.85 * (snr_db + 10) / 20
    
    def generate_comprehensive_analysis(self, params):
        """生成综合分析报告"""
        analysis = {}
        
        # 多普勒分析
        freq = self.radar_bands[params['radar_band']]["freq"]
        analysis['doppler_shift'] = self.calculate_doppler_shift(
            freq, params['target_speed'], params['incidence_angle']
        )
        analysis['doppler_velocity'] = analysis['doppler_shift'] * 3e8 / (2 * freq)
        
        # SNR分析
        base_snr, degraded_snr, snr_loss = self.calculate_snr_degradation(
            params['target_distance'], params['turbine_distance'], 
            params['incidence_angle'], params['radar_band']
        )
        analysis.update({
            'base_snr': base_snr,
            'degraded_snr': degraded_snr,
            'snr_degradation': snr_loss,
            'snr_reduction_percent': (base_snr - degraded_snr) / abs(base_snr) * 100 if base_snr != 0 else 0
        })
        
        # 探测概率分析
        analysis['base_pd'] = self.calculate_detection_probability(base_snr)
        analysis['degraded_pd'] = self.calculate_detection_probability(degraded_snr)
        analysis['pd_reduction'] = analysis['base_pd'] - analysis['degraded_pd']
        
        # 风险等级评估
        risk_score = min(1.0, max(0, (snr_loss/20 + analysis['pd_reduction']/0.3) / 2))
        if risk_score > 0.7:
            analysis['risk_level'] = "高风险"
            analysis['risk_color'] = "risk-high"
        elif risk_score > 0.4:
            analysis['risk_level'] = "中风险" 
            analysis['risk_color'] = "risk-medium"
        else:
            analysis['risk_level'] = "低风险"
            analysis['risk_color'] = "risk-low"
            
        analysis['risk_score'] = risk_score
        
        return analysis

class SimulationEngine:
    """仿真引擎类"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.simulation_data = pd.DataFrame()
        
    def define_parameter_ranges(self, base_params, simulation_step_size=1.0):
        """定义参数扫描范围"""
        param_ranges = {
            'radar_band': ['L波段', 'S波段', 'C波段', 'X波段', 'Ku波段'],
            'target_distance': np.arange(1.0, 50.0 + simulation_step_size, simulation_step_size * 5),
            'target_height': np.arange(10, 5000 + 500, 500),
            'target_speed': np.arange(1, 100 + 5, 5),
            'target_rcs': np.arange(0.1, 100.0 + 5, 5),
            'turbine_height': np.arange(50, 300 + 25, 25),
            'turbine_distance': np.arange(0.1, 20.0 + simulation_step_size, simulation_step_size),
            'incidence_angle': np.arange(0, 180 + 10, 10),
            'num_turbines': np.arange(1, 50 + 5, 5),
            'sea_state': ["平静", "轻微波浪", "中等波浪", "大浪", "狂浪"],
            'weather': ["晴朗", "小雨", "中雨", "大雨", "雾天"]
        }
        return param_ranges
    
    def run_simulation(self, base_params, simulation_step_size=1.0, max_iterations=1000):
        """运行参数扫描仿真"""
        param_ranges = self.define_parameter_ranges(base_params, simulation_step_size)
        
        # 计算总迭代次数
        total_iterations = np.prod([len(v) for v in param_ranges.values()])
        st.info(f"预计总仿真次数: {total_iterations:,} (将限制在{max_iterations}次以内)")
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        iteration = 0
        
        # 使用嵌套循环进行参数扫描（限制最大迭代次数）
        for radar_band in param_ranges['radar_band'][:2]:
            for target_distance in param_ranges['target_distance'][::3]:
                for target_speed in param_ranges['target_speed'][::5]:
                    for turbine_distance in param_ranges['turbine_distance'][::2]:
                        for incidence_angle in param_ranges['incidence_angle'][::3]:
                            
                            if iteration >= max_iterations:
                                break
                                
                            # 构建参数组合
                            sim_params = base_params.copy()
                            sim_params.update({
                                'radar_band': radar_band,
                                'target_distance': target_distance,
                                'target_speed': target_speed,
                                'turbine_distance': turbine_distance,
                                'incidence_angle': incidence_angle
                            })
                            
                            try:
                                # 运行分析
                                analysis = self.analyzer.generate_comprehensive_analysis(sim_params)
                                
                                # 合并参数和分析结果
                                result_row = {**sim_params, **analysis}
                                results.append(result_row)
                                
                                iteration += 1
                                
                                # 更新进度
                                progress = iteration / min(total_iterations, max_iterations)
                                progress_bar.progress(progress)
                                status_text.text(f"仿真进度: {iteration}/{min(total_iterations, max_iterations)} "
                                               f"({progress*100:.1f}%)")
                                
                            except Exception as e:
                                st.warning(f"参数组合分析失败: {e}")
                                continue
                
                if iteration >= max_iterations:
                    break
            if iteration >= max_iterations:
                break
                
        # 转换为DataFrame
        self.simulation_data = pd.DataFrame(results)
        
        # 显示完成信息
        status_text.text(f"仿真完成！共生成 {len(self.simulation_data)} 条数据")
        progress_bar.empty()
        
        return self.simulation_data
    
    def save_simulation_data(self, filename=None):
        """保存仿真数据到CSV文件"""
        if filename is None:
            filename = f"radar_simulation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        csv = self.simulation_data.to_csv(index=False)
        return csv, filename

def create_simulation_analysis_wide(analyzer, params, simulation_data):
    """创建宽幅仿真分析报告 - 优化布局"""
    st.markdown('<div class="section-header">📈 仿真数据分析报告</div>', unsafe_allow_html=True)
    
    if simulation_data.empty:
        st.warning("没有仿真数据可用，请先运行仿真")
        return
    
    # 基本信息统计 - 使用全宽度
    st.markdown("### 📊 仿真数据概览")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总数据量", f"{len(simulation_data):,} 条")
    with col2:
        avg_snr_loss = simulation_data['snr_degradation'].mean()
        st.metric("平均SNR损失", f"{avg_snr_loss:.2f} dB")
    with col3:
        high_risk_count = len(simulation_data[simulation_data['risk_score'] > 0.7])
        st.metric("高风险场景", f"{high_risk_count} 个")
    with col4:
        max_snr_loss = simulation_data['snr_degradation'].max()
        st.metric("最大SNR损失", f"{max_snr_loss:.2f} dB")
    
    # 使用全宽度标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 参数影响分析", "📈 性能分布", "🎯 风险分析", "🔍 相关性分析", "📋 数据探索"
    ])
    
    with tab1:
        _create_parameter_impact_analysis_wide(simulation_data)
    
    with tab2:
        _create_performance_distribution_wide(simulation_data)
    
    with tab3:
        _create_risk_analysis_wide(simulation_data)
    
    with tab4:
        _create_correlation_analysis_wide(simulation_data)
    
    with tab5:
        _create_data_exploration_wide(simulation_data)

def _create_parameter_impact_analysis_wide(simulation_data):
    """创建宽幅参数影响分析"""
    st.markdown("#### 🎯 参数对SNR损失的影响")
    
    # 使用两列布局，但每个图表占满列宽
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 参数选择
        param_options = ['target_distance', 'turbine_distance', 'incidence_angle', 'target_speed']
        selected_param = st.selectbox("选择分析参数", param_options, key="param_select")
        
        # 创建散点图 - 使用全宽度
        if selected_param in param_options:
            fig = px.scatter(
                simulation_data, 
                x=selected_param, 
                y='snr_degradation',
                color='radar_band',
                title=f'{selected_param} 对SNR损失的影响',
                labels={selected_param: _get_param_label(selected_param), 
                       'snr_degradation': 'SNR损失 (dB)'},
                width=800,  # 设置更大宽度
                height=400
            )
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        # 参数统计信息
        st.markdown("##### 参数统计")
        if selected_param in simulation_data.columns:
            param_stats = simulation_data[selected_param].describe()
            st.dataframe(pd.DataFrame(param_stats).T, width='stretch')
    
    # 多参数影响热力图 - 使用全宽度
    st.markdown("#### 🔥 多参数组合影响热力图")
    
    col1, col2 = st.columns(2)
    with col1:
        x_param = st.selectbox("X轴参数", ['target_distance', 'turbine_distance', 'incidence_angle', 'target_speed'], 
                              index=0, key="x_param")
    with col2:
        y_param = st.selectbox("Y轴参数", ['target_distance', 'turbine_distance', 'incidence_angle', 'target_speed'], 
                              index=1, key="y_param")
    
    # 创建热力图数据
    heatmap_data = simulation_data.groupby([x_param, y_param])['snr_degradation'].mean().reset_index()
    heatmap_pivot = heatmap_data.pivot(index=y_param, columns=x_param, values='snr_degradation')
    
    fig = px.imshow(
        heatmap_pivot,
        title=f"{_get_param_label(x_param)} vs {_get_param_label(y_param)} - 平均SNR损失热力图",
        labels=dict(x=_get_param_label(x_param), 
                   y=_get_param_label(y_param),
                   color="SNR损失 (dB)"),
        width=1000,
        height=500
    )
    st.plotly_chart(fig, width='stretch')

def _create_performance_distribution_wide(simulation_data):
    """创建宽幅性能分布分析"""
    st.markdown("#### 📊 性能指标分布分析")
    
    # 使用两列布局，每个图表占满列宽
    col1, col2 = st.columns(2)
    
    with col1:
        # SNR损失分布
        fig1 = px.histogram(
            simulation_data, 
            x='snr_degradation',
            nbins=50,
            title='SNR损失分布',
            labels={'snr_degradation': 'SNR损失 (dB)'},
            width=500,
            height=400
        )
        st.plotly_chart(fig1, width='stretch')
    
    with col2:
        # 探测概率变化分布
        fig2 = px.histogram(
            simulation_data, 
            x='pd_reduction',
            nbins=50,
            title='探测概率变化分布',
            labels={'pd_reduction': '探测概率变化'},
            width=500,
            height=400
        )
        st.plotly_chart(fig2, width='stretch')
    
    # 按雷达波段的性能对比 - 使用全宽度
    st.markdown("#### 📡 各雷达波段性能对比")
    fig = px.box(
        simulation_data, 
        x='radar_band', 
        y='snr_degradation',
        title='各雷达波段的SNR损失分布',
        width=1000,
        height=400
    )
    st.plotly_chart(fig, width='stretch')

def _create_risk_analysis_wide(simulation_data):
    """创建宽幅风险分析"""
    st.markdown("#### ⚠️ 风险等级分布")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 风险等级统计
        risk_counts = simulation_data['risk_level'].value_counts()
        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title='风险等级分布',
            width=600,
            height=400
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # 风险统计表格
        st.markdown("##### 风险统计")
        risk_summary = simulation_data['risk_level'].value_counts().reset_index()
        risk_summary.columns = ['风险等级', '数量']
        st.dataframe(risk_summary, width='stretch')
    
    # 风险与参数关系 - 使用全宽度
    st.markdown("#### 📈 风险与操作参数的关系")
    param = st.selectbox("选择分析参数", 
                        ['target_distance', 'turbine_distance', 'incidence_angle'],
                        key="risk_param")
    
    fig = px.scatter(
        simulation_data,
        x=param,
        y='risk_score',
        color='risk_level',
        title=f'{_get_param_label(param)} 与风险分数的关系',
        labels={param: _get_param_label(param), 'risk_score': '风险分数'},
        width=1000,
        height=400
    )
    st.plotly_chart(fig, width='stretch')

def _create_correlation_analysis_wide(simulation_data):
    """创建宽幅相关性分析"""
    st.markdown("#### 🔗 参数相关性矩阵")
    
    # 选择数值型参数
    numeric_columns = simulation_data.select_dtypes(include=[np.number]).columns
    selected_columns = st.multiselect(
        "选择分析参数", 
        numeric_columns, 
        default=['snr_degradation', 'pd_reduction', 'risk_score', 'target_distance', 'turbine_distance'],
        key="corr_params"
    )
    
    if len(selected_columns) >= 2:
        corr_matrix = simulation_data[selected_columns].corr()
        
        fig = px.imshow(
            corr_matrix,
            title="参数相关性热力图",
            color_continuous_scale='RdBu',
            aspect="auto",
            width=800,
            height=600
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.warning("请至少选择2个参数进行相关性分析")

def _create_data_exploration_wide(simulation_data):
    """创建宽幅数据探索界面"""
    st.markdown("#### 📋 仿真数据探索")
    
    # 数据显示
    st.dataframe(simulation_data, width='stretch')
    
    # 数据统计
    st.markdown("#### 📊 数据统计摘要")
    st.write(simulation_data.describe())

def _get_param_label(param_name):
    """获取参数显示标签"""
    labels = {
        'target_distance': '目标距离 (km)',
        'turbine_distance': '风机距离 (km)', 
        'incidence_angle': '照射角度 (°)',
        'target_speed': '目标速度 (m/s)',
        'snr_degradation': 'SNR损失 (dB)',
        'pd_reduction': '探测概率变化',
        'risk_score': '风险分数'
    }
    return labels.get(param_name, param_name)

def create_parameter_sidebar():
    """创建参数侧边栏"""
    st.sidebar.header("🎯 分析参数配置")
    
    # 仿真模式开关
    simulation_mode = st.sidebar.checkbox("启用仿真模式", value=True)
    
    simulation_params = {}
    if simulation_mode:
        st.sidebar.header("🔬 仿真参数设置")
        simulation_params['simulation_step_size'] = st.sidebar.slider(
            "仿真步长", 0.5, 5.0, 2.0, 0.5,
            help="控制参数扫描的步长，较小的步长会产生更多数据点"
        )
        simulation_params['max_iterations'] = st.sidebar.slider(
            "最大迭代次数", 100, 5000, 1000, 100,
            help="限制总仿真次数，避免计算时间过长"
        )
    
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
        target_rcs = st.slider("目标RCS (m²)", 0.1, 100.0, 1.0)
    
    with st.sidebar.expander("风机参数"):
        turbine_height = st.slider("风机高度 (m)", 50, 300, 185)
        turbine_distance = st.slider("目标-风机距离 (km)", 0.1, 20.0, 1.0, 0.1)
        incidence_angle = st.slider("照射角度 (°)", 0, 180, 45)
        num_turbines = st.slider("风机数量", 1, 50, 30)
    
    with st.sidebar.expander("环境参数"):
        sea_state = st.selectbox("海况", ["平静", "轻微波浪", "中等波浪", "大浪", "狂浪"])
        weather = st.selectbox("气象条件", ["晴朗", "小雨", "中雨", "大雨", "雾天"])
    
    base_params = {
        'radar_band': radar_band,
        'target_distance': target_distance,
        'target_height': target_height, 
        'target_speed': target_speed,
        'target_rcs': target_rcs,
        'turbine_height': turbine_height,
        'turbine_distance': turbine_distance,
        'incidence_angle': incidence_angle,
        'num_turbines': num_turbines,
        'sea_state': sea_state,
        'weather': weather
    }
    
    return {**base_params, 'simulation_mode': simulation_mode, **simulation_params}

def create_simulation_interface_wide(analyzer, params):
    """创建宽幅仿真界面 - 优化布局"""
    st.markdown('<div class="main-header">🔬 海上风电雷达影响仿真分析系统</div>', unsafe_allow_html=True)
    
    # 初始化仿真引擎
    simulation_engine = SimulationEngine(analyzer)
    
    # 仿真控制区域 - 使用全宽度
    st.markdown('<div class="simulation-control">', unsafe_allow_html=True)
    st.markdown("### 🎮 仿真控制")
    
    # 使用三列布局，但按钮占满宽度
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        start_sim = st.button("🚀 开始仿真", type="primary", width='stretch')
    
    with col2:
        gen_report = st.button("📊 生成分析报告", width='stretch')
    
    with col3:
        if 'simulation_data' in st.session_state:
            csv_data, filename = simulation_engine.save_simulation_data()
            st.download_button(
                label="💾 下载仿真数据CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                width='stretch'
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 处理仿真开始
    if start_sim:
        with st.spinner("仿真运行中，请稍候..."):
            start_time = time.time()
            
            # 运行仿真
            simulation_data = simulation_engine.run_simulation(
                params, 
                params.get('simulation_step_size', 2.0),
                params.get('max_iterations', 1000)
            )
            
            end_time = time.time()
            st.success(f"仿真完成！耗时 {end_time-start_time:.1f} 秒")
            
            # 保存仿真状态到session state
            st.session_state.simulation_data = simulation_data
            st.session_state.simulation_engine = simulation_engine
    
    # 显示仿真状态和数据概览
    if 'simulation_data' in st.session_state:
        simulation_data = st.session_state.simulation_data
        
        st.markdown("---")
        st.markdown("### 📈 仿真数据概览")
        
        # 统计数据卡片 - 使用全宽度
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总数据量", f"{len(simulation_data):,}")
        with col2:
            st.metric("参数维度", f"{len(simulation_data.columns)}")
        with col3:
            avg_snr = simulation_data['snr_degradation'].mean()
            st.metric("平均SNR损失", f"{avg_snr:.2f} dB")
        with col4:
            high_risk = len(simulation_data[simulation_data['risk_score'] > 0.7])
            st.metric("高风险场景", high_risk)
    
    # 生成分析报告
    if gen_report and 'simulation_data' in st.session_state:
        simulation_data = st.session_state.simulation_data
        create_simulation_analysis_wide(analyzer, params, simulation_data)
    
    # 快速数据预览
    if 'simulation_data' in st.session_state:
        with st.expander("📋 数据预览", expanded=False):
            st.dataframe(st.session_state.simulation_data.head(10), width='stretch')

def main():
    """主函数"""
    # 初始化分析器
    analyzer = RadarImpactAnalyzer()
    
    # 创建参数侧边栏
    params = create_parameter_sidebar()
    
    # 根据模式选择界面
    if params.get('simulation_mode', False):
        create_simulation_interface_wide(analyzer, params)
    else:
        # 单点分析功能
        analysis = analyzer.generate_comprehensive_analysis(params)
        create_single_analysis_interface(analyzer, params, analysis)
    
    # 页脚信息
    st.markdown("---")
    st.markdown("""
    **技术说明**:
    - 基于简化雷达方程和电磁传播模型
    - 多径效应采用两径模型近似  
    - 探测概率基于Swerling目标模型
    - 实际应用需结合具体雷达参数和现场测量数据
    """)

def create_single_analysis_interface(analyzer, params, analysis):
    """创建单点分析界面"""
    st.markdown('<div class="main-header">🌊 海上风力发电厂雷达性能影响专业分析系统</div>', unsafe_allow_html=True)
    
    # 关键指标显示
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("SNR变化", f"{analysis['snr_degradation']:+.1f} dB")
    with col2:
        st.metric("探测概率变化", f"{analysis['pd_reduction']:+.3f}")
    with col3:
        st.metric("多普勒频移", f"{analysis['doppler_shift']:.1f} Hz")
    with col4:
        st.metric("风险等级", analysis['risk_level'])
    
    st.info("当前为单点分析模式。启用侧边栏的'仿真模式'可进行参数扫描仿真。")

if __name__ == "__main__":
    main()