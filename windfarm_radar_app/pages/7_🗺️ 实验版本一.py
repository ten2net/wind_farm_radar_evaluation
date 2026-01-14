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

# 页面配置
st.set_page_config(
    page_title="海上风电雷达影响专业分析系统",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
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
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2e86ab;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        text-align: center;
    }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-medium { color: #ffa500; font-weight: bold; }
    .risk-low { color: #32cd32; font-weight: bold; }
    .sub-header {
        font-size: 1.3rem;
        color: #1f77b4;
        margin: 1rem 0 0.5rem 0;
        font-weight: bold;
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

def create_parameter_sidebar():
    """创建参数侧边栏"""
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
        target_rcs = st.slider("目标RCS (m²)", 0.1, 100.0, 1.0)
    
    with st.sidebar.expander("风机参数"):
        turbine_height = st.slider("风机高度 (m)", 50, 300, 185)
        turbine_distance = st.slider("目标-风机距离 (km)", 0.1, 20.0, 1.0, 0.1)
        incidence_angle = st.slider("照射角度 (°)", 0, 180, 45)
        num_turbines = st.slider("风机数量", 1, 50, 30)
    
    with st.sidebar.expander("环境参数"):
        sea_state = st.selectbox("海况", ["平静", "轻微波浪", "中等波浪", "大浪", "狂浪"])
        weather = st.selectbox("气象条件", ["晴朗", "小雨", "中雨", "大雨", "雾天"])
    
    return {
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

def create_performance_comparison(analyzer, params, analysis):
    """创建性能对比分析 - 已修复量纲不统一问题"""
    st.markdown('<div class="section-header">性能指标对比分析</div>', unsafe_allow_html=True)
    
    # 使用分面布局代替混合量纲的柱状图
    fig = make_subplots(
        rows=2, 
        cols=2,
        specs=[
            [{"type": "xy"}, {"type": "xy"}],  # 第一行：两个 'xy' 子图
            [{"type": "indicator"}, {"type": "xy"}]  # 第二行：(2,1) 为 indicator，(2,2) 为 xy
        ]
    )
    # fig = make_subplots(
    #     rows=2, cols=2,
    #     subplot_titles=(
    #         '信噪比(SNR)对比', 
    #         '探测概率(Pd)对比', 
    #         '多普勒频移对比',
    #         '性能变化百分比'
    #     ),
    #     specs=[[{"secondary_y": False}, {"secondary_y": False}],
    #            [{"secondary_y": False}, {"secondary_y": False}]]
    # )
    
    # SNR对比（左上）
    fig.add_trace(go.Bar(
        name='无风机', x=['SNR'], y=[analysis['base_snr']], 
        marker_color='blue', showlegend=True
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        name='有风机', x=['SNR'], y=[analysis['degraded_snr']], 
        marker_color='red', showlegend=True
    ), row=1, col=1)
    
    # 探测概率对比（右上）
    fig.add_trace(go.Bar(
        name='无风机', x=['探测概率'], y=[analysis['base_pd']], 
        marker_color='blue', showlegend=False
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        name='有风机', x=['探测概率'], y=[analysis['degraded_pd']], 
        marker_color='red', showlegend=False
    ), row=1, col=2)
    
    # 多普勒频移（左下）
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=analysis['doppler_shift'],
        title={"text": "多普勒频移"},
        number={'suffix': " Hz"},
        domain={'row': 1, 'column': 0}
    ), row=2, col=1)
    
    # 性能变化百分比（右下）- 标准化显示
    metrics = ['SNR变化', '探测概率变化']
    changes = [
        analysis['snr_degradation'],
        analysis['pd_reduction'] * 100  # 转换为百分比
    ]
    
    fig.add_trace(go.Bar(
        x=metrics, y=changes,
        marker_color=['red' if x < 0 else 'green' for x in changes],
        showlegend=False
    ), row=2, col=2)
    
    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, width='stretch')
    
    # 单独显示每个指标的详细对比（修复量纲问题）
    st.markdown("#### 分指标详细对比")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # SNR单独显示
        fig_snr = go.Figure()
        fig_snr.add_trace(go.Bar(
            name='无风机', x=['SNR'], y=[analysis['base_snr']], 
            marker_color='blue'
        ))
        fig_snr.add_trace(go.Bar(
            name='有风机', x=['SNR'], y=[analysis['degraded_snr']], 
            marker_color='red'
        ))
        fig_snr.update_layout(
            title='信噪比对比 (dB)',
            yaxis_title="SNR (dB)"
        )
        st.plotly_chart(fig_snr, width='stretch')
    
    with col2:
        # 探测概率单独显示
        fig_pd = go.Figure()
        fig_pd.add_trace(go.Bar(
            name='无风机', x=['探测概率'], y=[analysis['base_pd']], 
            marker_color='blue'
        ))
        fig_pd.add_trace(go.Bar(
            name='有风机', x=['探测概率'], y=[analysis['degraded_pd']], 
            marker_color='red'
        ))
        fig_pd.update_layout(
            title='探测概率对比',
            yaxis_title="探测概率"
        )
        st.plotly_chart(fig_pd, width='stretch')
    
    with col3:
        # 多普勒频移单独显示
        fig_doppler = go.Figure()
        fig_doppler.add_trace(go.Indicator(
            mode="number+delta",
            value=analysis['doppler_shift'],
            title={"text": "多普勒频移"},
            number={'suffix': " Hz"},
            delta={'reference': 0, 'relative': False}
        ))
        fig_doppler.update_layout(title='多普勒频移')
        st.plotly_chart(fig_doppler, width='stretch')

def create_multidimensional_analysis(analyzer, params):
    """创建多维度分析 - 已修复量纲问题"""
    st.markdown('<div class="section-header">多维度影响分析</div>', unsafe_allow_html=True)
    
    # 使用标准化百分比显示替代混合量纲
    st.markdown("#### 各波段影响程度对比（标准化百分比）")
    
    bands = list(analyzer.radar_bands.keys())
    degradations = []
    
    for band in bands:
        _, _, degradation = analyzer.calculate_snr_degradation(
            params['target_distance'], params['turbine_distance'],
            params['incidence_angle'], band
        )
        degradations.append(degradation)
    
    # 标准化到0-100%范围
    max_degradation = max(abs(max(degradations)), abs(min(degradations))) if degradations else 1
    normalized_degradations = [abs(d)/max_degradation * 100 for d in degradations]
    
    fig = go.Figure(data=[go.Bar(
        x=bands, y=normalized_degradations,
        marker_color=['red' if d > 0 else 'green' for d in degradations]
    )])
    fig.update_layout(
        title='各波段SNR恶化程度对比（标准化百分比）',
        xaxis_title='雷达波段',
        yaxis_title='相对影响程度 (%)'
    )
    st.plotly_chart(fig, width='stretch')
    
    # 角度影响分析（单独量纲）
    st.markdown("#### 照射角度对多普勒频移的影响")
    
    angles = np.linspace(0, 180, 50)
    doppler_shifts = []
    
    for angle in angles:
        freq = analyzer.radar_bands[params['radar_band']]["freq"]
        shift = analyzer.calculate_doppler_shift(
            freq, params['target_speed'], angle
        )
        doppler_shifts.append(shift)
    
    fig_angle = go.Figure()
    fig_angle.add_trace(go.Scatter(
        x=angles, y=doppler_shifts, mode='lines',
        name='多普勒频移', line=dict(color='green')
    ))
    fig_angle.update_layout(
        title='多普勒频移 vs 照射角度',
        xaxis_title='照射角度 (°)',
        yaxis_title='多普勒频移 (Hz)'
    )
    st.plotly_chart(fig_angle, width='stretch')

def create_sensitivity_analysis(analyzer, params):
    """创建敏感性分析 - 已修复量纲问题"""
    st.markdown('<div class="section-header">参数敏感性分析</div>', unsafe_allow_html=True)
    
    # 距离敏感性分析 - 分开显示不同量纲的指标
    distances = np.linspace(1, 50, 20)
    snr_changes = []
    pd_changes = []
    
    for dist in distances:
        base_snr, degraded_snr, _ = analyzer.calculate_snr_degradation(
            dist, params['turbine_distance'], params['incidence_angle'], params['radar_band']
        )
        base_pd = analyzer.calculate_detection_probability(base_snr)
        degraded_pd = analyzer.calculate_detection_probability(degraded_snr)
        
        snr_changes.append(degraded_snr - base_snr)
        pd_changes.append((degraded_pd - base_pd) * 100)  # 转换为百分比
    
    # 分开两个图表显示，避免量纲混合
    col1, col2 = st.columns(2)
    
    with col1:
        fig_snr = go.Figure()
        fig_snr.add_trace(go.Scatter(
            x=distances, y=snr_changes, mode='lines',
            name='SNR变化', line=dict(color='blue')
        ))
        fig_snr.update_layout(
            title='SNR变化 vs 距离',
            xaxis_title='距离 (km)',
            yaxis_title='SNR变化 (dB)'
        )
        st.plotly_chart(fig_snr, width='stretch')
    
    with col2:
        fig_pd = go.Figure()
        fig_pd.add_trace(go.Scatter(
            x=distances, y=pd_changes, mode='lines',
            name='探测概率变化', line=dict(color='red')
        ))
        fig_pd.update_layout(
            title='探测概率变化 vs 距离',
            xaxis_title='距离 (km)',
            yaxis_title='探测概率变化 (%)'
        )
        st.plotly_chart(fig_pd, width='stretch')
    
    # 速度敏感性分析 - 单独量纲
    st.markdown("#### 目标速度对多普勒频移的影响")
    
    speeds = np.linspace(1, 100, 20)
    doppler_shifts = []
    
    for speed in speeds:
        freq = analyzer.radar_bands[params['radar_band']]["freq"]
        shift = analyzer.calculate_doppler_shift(
            freq, speed, params['incidence_angle']
        )
        doppler_shifts.append(shift)
    
    fig_speed = go.Figure()
    fig_speed.add_trace(go.Scatter(
        x=speeds, y=doppler_shifts, mode='lines',
        name='多普勒频移', line=dict(color='purple')
    ))
    fig_speed.update_layout(
        title='多普勒频移 vs 目标速度',
        xaxis_title='目标速度 (m/s)',
        yaxis_title='多普勒频移 (Hz)'
    )
    st.plotly_chart(fig_speed, width='stretch')

def create_data_tables(analyzer, params, analysis):
    """创建数据表格"""
    st.markdown('<div class="section-header">详细数据表格</div>', unsafe_allow_html=True)
    
    # 性能对比表 - 保持量纲分离
    comparison_data = {
        '性能指标': ['信噪比(SNR)', '探测概率(Pd)', '多普勒频移'],
        '量纲': ['dB', '无量纲', 'Hz'],
        '无风机基准': [
            f"{analysis['base_snr']:.2f} dB",
            f"{analysis['base_pd']:.3f}",
            f"{analysis['doppler_shift']:.1f} Hz"
        ],
        '有风机影响': [
            f"{analysis['degraded_snr']:.2f} dB",
            f"{analysis['degraded_pd']:.3f}",
            f"{analysis['doppler_shift']:.1f} Hz"
        ],
        '变化量': [
            f"{analysis['snr_degradation']:.2f} dB",
            f"{analysis['pd_reduction']:.3f}",
            "0 Hz"
        ]
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, width='stretch')

def create_professional_report(analyzer, params, analysis):
    """生成专业分析报告"""
    st.markdown('<div class="section-header">专业仿真分析报告</div>', unsafe_allow_html=True)
    
    # 生成Markdown格式报告
    report_content = generate_markdown_report(analyzer, params, analysis)
    
    # 显示报告预览
    with st.expander("📋 查看完整报告"):
        st.markdown(report_content)
    
    # 下载按钮
    st.download_button(
        label="📥 下载完整报告",
        data=report_content,
        file_name=f"海上风电雷达影响分析报告_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown"
    )

def generate_markdown_report(analyzer, params, analysis):
    """生成Markdown格式的完整报告"""
    
    report = f"""
# 海上风力发电厂雷达性能影响仿真分析报告

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**评估系统**: 专业雷达影响分析系统 v2.0

## 执行摘要

基于当前参数配置的分析结果：

### 关键性能指标
- **信噪比(SNR)**: {analysis['base_snr']:.2f} dB → {analysis['degraded_snr']:.2f} dB (变化: {analysis['snr_degradation']:+.2f} dB)
- **探测概率**: {analysis['base_pd']:.3f} → {analysis['degraded_pd']:.3f} (变化: {analysis['pd_reduction']:+.3f})
- **多普勒频移**: {analysis['doppler_shift']:.1f} Hz
- **风险等级**: {analysis['risk_level']}

## 详细分析

### 参数配置
- 雷达波段: {params['radar_band']}
- 目标距离: {params['target_distance']} km
- 目标速度: {params['target_speed']} m/s
- 风机距离: {params['turbine_distance']} km
- 照射角度: {params['incidence_angle']}°

### 技术建议
根据分析结果，建议采取相应的缓解措施以确保雷达系统性能。
"""

    return report

def create_main_dashboard(analyzer, params, analysis):
    """创建主仪表板"""
    
    # 标题区域
    st.markdown('<div class="main-header">🌊 海上风力发电厂雷达性能影响专业分析系统</div>', unsafe_allow_html=True)
    
    # 关键指标卡片 - 保持量纲分离
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <h3>📡 信噪比变化</h3>
            <h2>{analysis["snr_degradation"]:+.1f} dB</h2>
            <p>基准: {analysis["base_snr"]:.1f} dB → 有风机: {analysis["degraded_snr"]:.1f} dB</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <h3>🎯 探测概率变化</h3>
            <h2>{analysis["pd_reduction"]:+.3f}</h2>
            <p>基准: {analysis["base_pd"]:.3f} → 有风机: {analysis["degraded_pd"]:.3f}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <h3>🌀 多普勒频移</h3>
            <h2>{analysis["doppler_shift"]:.1f} Hz</h2>
            <p>等效速度: {analysis["doppler_velocity"]:.1f} m/s</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card">
            <h3>⚠️ 风险等级</h3>
            <h2 class="{analysis["risk_color"]}">{analysis["risk_level"]}</h2>
            <p>风险分数: {analysis["risk_score"]:.2f}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # 标签页布局
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 性能指标对比", "📈 多维度分析", "🎯 敏感性分析", "📋 数据表格", "📄 专业报告"
    ])
    
    with tab1:
        create_performance_comparison(analyzer, params, analysis)
    
    with tab2:
        create_multidimensional_analysis(analyzer, params)
    
    with tab3:
        create_sensitivity_analysis(analyzer, params)
    
    with tab4:
        create_data_tables(analyzer, params, analysis)
    
    with tab5:
        create_professional_report(analyzer, params, analysis)

def main():
    """主函数"""
    # 初始化分析器
    analyzer = RadarImpactAnalyzer()
    
    # 创建参数侧边栏
    params = create_parameter_sidebar()
    
    # 执行分析
    analysis = analyzer.generate_comprehensive_analysis(params)
    
    # 创建主仪表板
    create_main_dashboard(analyzer, params, analysis)
    
    # 页脚信息
    st.markdown("---")
    st.markdown("""
    **技术说明**:
    - 基于简化雷达方程和电磁传播模型
    - 多径效应采用两径模型近似
    - 探测概率基于Swerling目标模型
    - 实际应用需结合具体雷达参数和现场测量数据
    """)

if __name__ == "__main__":
    main()