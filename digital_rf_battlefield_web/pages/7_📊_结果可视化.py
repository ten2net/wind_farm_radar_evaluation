"""
结果可视化页面 - 仿真结果分析和可视化
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime
import json
from utils.style_utils import create_data_card, get_military_style
import folium
from streamlit_folium import st_folium
from components.maps import create_military_map, add_radar_to_map, add_target_to_map

def main():
    """结果可视化页面主函数"""
    st.title("📊 仿真结果可视化")
    st.markdown("分析和可视化仿真结果数据")
    
    # 检查是否有仿真结果
    if 'simulation_results' not in st.session_state or not st.session_state.simulation_results:
        st.warning("暂无仿真结果数据，请先运行仿真")
        
        if st.button("🚀 前往仿真运行"):
            st.switch_page("pages/6_🚀_仿真运行.py")
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📈 数据分析", "🗺️ 地理视图", "📡 雷达性能", "🎯 目标分析"])
    
    with tab1:
        show_data_analysis()
    
    with tab2:
        show_geographic_view()
    
    with tab3:
        show_radar_performance()
    
    with tab4:
        show_target_analysis()

def show_data_analysis():
    """显示数据分析界面"""
    st.subheader("📈 综合数据分析")
    
    # 获取结果数据
    results = st.session_state.get('simulation_results', {})
    
    # 关键指标概览
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_detections = results.get('total_detections', 0)
        create_data_card(
            "总检测次数",
            f"{total_detections:,}",
            "次",
            icon="🎯"
        )
    
    with col2:
        avg_detection_prob = results.get('avg_detection_probability', 0)
        create_data_card(
            "平均检测概率",
            f"{avg_detection_prob:.1%}",
            "",
            icon="📈"
        )
    
    with col3:
        avg_false_alarm = results.get('avg_false_alarm_rate', 0)
        create_data_card(
            "平均虚警率",
            f"{avg_false_alarm:.2e}",
            "",
            icon="⚠️"
        )
    
    with col4:
        track_continuity = results.get('track_continuity', 0)
        create_data_card(
            "航迹连续性",
            f"{track_continuity:.1%}",
            "",
            icon="🛤️"
        )
    
    st.markdown("---")
    
    # 时间序列图表
    st.markdown("### 📊 检测性能趋势")
    
    # 生成模拟数据
    time_data = generate_time_series_data()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # 检测概率时间序列
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=time_data['time'],
            y=time_data['detection_prob'],
            mode='lines+markers',
            name='检测概率',
            line=dict(color='#1a73e8', width=2)
        ))
        
        fig1.update_layout(
            height=300,
            title="检测概率时间序列",
            xaxis_title="时间 (s)",
            yaxis_title="检测概率",
            yaxis=dict(range=[0, 1]),
            template="plotly_dark"
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        # 虚警率时间序列
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=time_data['time'],
            y=time_data['false_alarm_rate'],
            mode='lines+markers',
            name='虚警率',
            line=dict(color='#f44336', width=2)
        ))
        
        fig2.update_layout(
            height=300,
            title="虚警率时间序列",
            xaxis_title="时间 (s)",
            yaxis_title="虚警率",
            yaxis_type="log",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # 统计分布
    st.markdown("### 📊 统计分布分析")
    
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        # SNR分布
        st.markdown("#### 📶 SNR分布")
        
        snr_data = generate_snr_distribution()
        
        fig3 = go.Figure(data=[
            go.Histogram(
                x=snr_data,
                nbinsx=20,
                marker_color='#1a73e8',
                opacity=0.7
            )
        ])
        
        fig3.update_layout(
            height=300,
            xaxis_title="SNR (dB)",
            yaxis_title="频数",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig3, use_container_width=True)
    
    with col_dist2:
        # 距离分布
        st.markdown("#### 📏 检测距离分布")
        
        range_data = generate_range_distribution()
        
        fig4 = go.Figure(data=[
            go.Histogram(
                x=range_data,
                nbinsx=20,
                marker_color='#00e676',
                opacity=0.7
            )
        ])
        
        fig4.update_layout(
            height=300,
            xaxis_title="距离 (km)",
            yaxis_title="频数",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    
    # 数据导出
    st.markdown("### 📤 数据导出")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        if st.button("📊 导出图表数据", use_container_width=True):
            export_chart_data()
    
    with col_exp2:
        if st.button("📈 导出统计报告", use_container_width=True):
            export_statistics_report()
    
    with col_exp3:
        if st.button("📋 导出原始数据", use_container_width=True):
            export_raw_data()

def generate_time_series_data():
    """生成时间序列数据"""
    time = np.linspace(0, 300, 100)
    detection_prob = 0.8 + 0.1 * np.sin(time/50) + np.random.normal(0, 0.05, 100)
    false_alarm_rate = 1e-4 + 5e-5 * np.cos(time/30) + np.random.normal(0, 1e-5, 100)
    
    return {
        'time': time,
        'detection_prob': np.clip(detection_prob, 0, 1),
        'false_alarm_rate': np.clip(false_alarm_rate, 1e-6, 1e-3)
    }

def generate_snr_distribution():
    """生成SNR分布数据"""
    return np.random.normal(15, 5, 1000)

def generate_range_distribution():
    """生成距离分布数据"""
    return np.random.exponential(50, 1000)

def export_chart_data():
    """导出图表数据"""
    time_data = generate_time_series_data()
    df = pd.DataFrame(time_data)
    
    st.download_button(
        label="📥 下载CSV文件",
        data=df.to_csv(index=False),
        file_name=f"chart_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def export_statistics_report():
    """导出统计报告"""
    results = st.session_state.get('simulation_results', {})
    
    report = {
        "summary": {
            "total_detections": results.get('total_detections', 0),
            "avg_detection_probability": results.get('avg_detection_probability', 0),
            "avg_false_alarm_rate": results.get('avg_false_alarm_rate', 0),
            "track_continuity": results.get('track_continuity', 0)
        },
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    st.download_button(
        label="📥 下载JSON报告",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name=f"statistics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def export_raw_data():
    """导出原始数据"""
    st.info("原始数据导出功能开发中...")

def show_geographic_view():
    """显示地理视图"""
    st.subheader("🗺️ 地理视图分析")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 创建结果地图
        st.markdown("### 🗺️ 仿真结果地图")
        
        # 创建地图
        m = create_military_map(
            center=[39.9042, 116.4074],
            zoom_start=6
        )
        
        # 添加雷达
        radars = st.session_state.get('radar_configs', [])
        for radar in radars:
            if 'position' in radar:
                add_radar_to_map(
                    m,
                    position=radar['position'],
                    radar_type=radar.get('type', 'phased_array'),
                    name=radar.get('name', '雷达'),
                    range_km=radar.get('range_km', 100)
                )
        
        # 添加检测结果
        results = st.session_state.get('simulation_results', {})
        detections = results.get('detections', [])
        
        for det in detections[:100]:  # 限制显示数量
            if 'position' in det:
                folium.CircleMarker(
                    location=det['position'],
                    radius=3,
                    color='#ff9800',
                    fill=True,
                    fill_color='#ff9800',
                    fill_opacity=0.7,
                    popup=f"检测点 SNR={det.get('snr', 0):.1f}dB"
                ).add_to(m)
        
        # 显示地图
        st_folium(m, width=600, height=500)
    
    with col2:
        # 地图控制
        st.markdown("### 🎮 地图控制")
        
        # 显示选项
        st.markdown("**显示选项**")
        show_radars = st.checkbox("显示雷达", value=True)
        show_coverage = st.checkbox("显示覆盖范围", value=True)
        show_detections = st.checkbox("显示检测点", value=True)
        show_tracks = st.checkbox("显示航迹", value=False)
        
        # 颜色设置
        st.markdown("**颜色设置**")
        radar_color = st.color_picker("雷达颜色", "#1a73e8")
        detection_color = st.color_picker("检测点颜色", "#ff9800")
        
        # 过滤选项
        st.markdown("**过滤选项**")
        min_snr = st.slider("最小SNR (dB)", 0, 30, 10, 1)
        max_range = st.slider("最大距离 (km)", 10, 500, 200, 10)
        
        if st.button("🔄 更新视图", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # 覆盖分析
    st.markdown("### 📊 覆盖分析")
    
    col_cov1, col_cov2, col_cov3 = st.columns(3)
    
    with col_cov1:
        # 总覆盖面积
        total_area = calculate_coverage_area(radars)
        st.metric("总覆盖面积", f"{total_area:,.0f} km²")
    
    with col_cov2:
        # 重叠覆盖率
        overlap = calculate_overlap_coverage(radars)
        st.metric("重叠覆盖率", f"{overlap:.1%}")
    
    with col_cov3:
        # 盲区面积
        blind_area = calculate_blind_area(radars)
        st.metric("盲区面积", f"{blind_area:,.0f} km²")
    
    # 覆盖热力图
    st.markdown("#### 🔥 覆盖热力图")
    
    # 生成模拟热力图数据
    heatmap_data = generate_coverage_heatmap(radars)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        colorscale='Viridis',
        showscale=True
    ))
    
    fig.update_layout(
        height=400,
        title="雷达覆盖热力图",
        xaxis_title="经度",
        yaxis_title="纬度",
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def calculate_coverage_area(radars):
    """计算覆盖面积"""
    total_area = 0
    for radar in radars:
        range_km = radar.get('range_km', 100)
        area = np.pi * (range_km ** 2)
        total_area += area
    
    return total_area

def calculate_overlap_coverage(radars):
    """计算重叠覆盖率"""
    # 简化计算
    if len(radars) < 2:
        return 0.0
    
    return min(0.3, len(radars) * 0.1)

def calculate_blind_area(radars):
    """计算盲区面积"""
    # 简化计算
    total_area = 1000000  # 假设总区域面积
    covered_area = calculate_coverage_area(radars)
    return max(0, total_area - covered_area)

def generate_coverage_heatmap(radars):
    """生成覆盖热力图"""
    # 生成模拟数据
    x = np.linspace(110, 120, 50)
    y = np.linspace(30, 40, 50)
    
    heatmap = np.zeros((50, 50))
    
    for radar in radars:
        if 'position' in radar:
            lat, lon = radar['position']
            range_km = radar.get('range_km', 100)
            
            # 简化计算每个点的信号强度
            for i in range(50):
                for j in range(50):
                    dist = np.sqrt((x[i] - lon)**2 + (y[j] - lat)**2) * 111  # 转换为km
                    if dist <= range_km:
                        signal_strength = 1 - (dist / range_km) ** 2
                        heatmap[j, i] = max(heatmap[j, i], signal_strength)
    
    return heatmap

def show_radar_performance():
    """显示雷达性能分析"""
    st.subheader("📡 雷达性能分析")
    
    # 获取雷达数据
    radars = st.session_state.get('radar_configs', [])
    results = st.session_state.get('simulation_results', {})
    
    if not radars:
        st.warning("暂无雷达数据")
        return
    
    # 选择雷达进行分析
    radar_names = [r.get('name', f'雷达{i+1}') for i, r in enumerate(radars)]
    selected_radar = st.selectbox("选择雷达", radar_names)
    
    radar_index = next(i for i, r in enumerate(radars) if r.get('name') == selected_radar)
    radar = radars[radar_index]
    
    # 雷达性能概览
    st.markdown(f"### 📊 {selected_radar} 性能概览")
    
    col_radar1, col_radar2, col_radar3, col_radar4 = st.columns(4)
    
    with col_radar1:
        # 检测次数
        detections = results.get('radar_detections', {}).get(str(radar_index), 0)
        create_data_card(
            "检测次数",
            detections,
            "次",
            icon="🎯"
        )
    
    with col_radar2:
        # 平均SNR
        avg_snr = results.get('radar_snr', {}).get(str(radar_index), 15)
        create_data_card(
            "平均SNR",
            f"{avg_snr:.1f}",
            "dB",
            icon="📶"
        )
    
    with col_radar3:
        # 虚警率
        false_alarm = results.get('radar_false_alarm', {}).get(str(radar_index), 1e-4)
        create_data_card(
            "虚警率",
            f"{false_alarm:.2e}",
            "",
            icon="⚠️"
        )
    
    with col_radar4:
        # 负载率
        load = results.get('radar_load', {}).get(str(radar_index), 0.5)
        create_data_card(
            "平均负载",
            f"{load:.1%}",
            "",
            icon="📈"
        )
    
    st.markdown("---")
    
    # 性能图表
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 📶 检测概率 vs 距离")
        plot_detection_vs_range(radar_index)
    
    with col_chart2:
        st.markdown("#### 🎯 方位角性能")
        plot_azimuth_performance(radar_index)
    
    st.markdown("---")
    
    # 详细性能分析
    st.markdown("### 🔍 详细性能分析")
    
    with st.expander("📊 性能指标详情", expanded=False):
        # 生成详细性能指标
        performance_metrics = generate_detailed_metrics(radar_index)
        
        for metric, value in performance_metrics.items():
            col_met1, col_met2 = st.columns([2, 1])
            with col_met1:
                st.text(metric)
            with col_met2:
                st.text(str(value))
    
    with st.expander("📈 ROC曲线", expanded=False):
        plot_roc_curve(radar_index)
    
    with st.expander("🔧 参数影响分析", expanded=False):
        plot_parameter_sensitivity(radar_index)

def plot_detection_vs_range(radar_index):
    """绘制检测概率 vs 距离"""
    ranges = np.linspace(10, 200, 20)
    detection_probs = 0.9 * np.exp(-ranges / 100) + 0.1
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ranges,
        y=detection_probs,
        mode='lines+markers',
        name='检测概率',
        line=dict(color='#1a73e8', width=2)
    ))
    
    fig.update_layout(
        height=300,
        xaxis_title="距离 (km)",
        yaxis_title="检测概率",
        yaxis=dict(range=[0, 1]),
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_azimuth_performance(radar_index):
    """绘制方位角性能"""
    angles = np.linspace(0, 360, 36)
    performance = 0.8 + 0.1 * np.sin(np.radians(angles * 2))
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=performance,
        theta=angles,
        mode='lines',
        name='检测性能',
        line=dict(color='#00e676', width=2)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 1])
        ),
        height=300,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def generate_detailed_metrics(radar_index):
    """生成详细性能指标"""
    return {
        "最大探测距离": "150 km",
        "距离分辨率": "15 m",
        "方位分辨率": "1.5°",
        "更新率": "10 Hz",
        "最小可检测信号": "-120 dBm",
        "动态范围": "80 dB",
        "距离精度": "5 m",
        "方位精度": "0.5°"
    }

def plot_roc_curve(radar_index):
    """绘制ROC曲线"""
    pfa = np.logspace(-6, 0, 100)
    pd = 1 - (1 + 10**(15/10))**(-np.log(1/pfa))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pfa,
        y=pd,
        mode='lines',
        name='ROC曲线',
        line=dict(color='#1a73e8', width=3)
    ))
    
    fig.update_layout(
        height=400,
        xaxis_title="虚警概率 (Pfa)",
        yaxis_title="检测概率 (Pd)",
        xaxis_type="log",
        yaxis_range=[0, 1],
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_parameter_sensitivity(radar_index):
    """绘制参数灵敏度分析"""
    parameters = ['频率', '功率', '脉冲宽度', '带宽', 'PRF']
    sensitivity = [0.8, 0.9, 0.7, 0.6, 0.5]
    
    fig = go.Figure(data=[
        go.Bar(
            x=parameters,
            y=sensitivity,
            marker_color=['#1a73e8', '#00e676', '#ff9800', '#f44336', '#9c27b0']
        )
    ])
    
    fig.update_layout(
        height=300,
        title="参数对检测性能的影响",
        yaxis_title="灵敏度",
        yaxis_range=[0, 1],
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_target_analysis():
    """显示目标分析"""
    st.subheader("🎯 目标分析")
    
    # 获取目标数据
    targets = st.session_state.get('target_configs', [])
    results = st.session_state.get('simulation_results', {})
    
    if not targets:
        st.warning("暂无目标数据")
        return
    
    # 目标概览
    col_target1, col_target2, col_target3, col_target4 = st.columns(4)
    
    with col_target1:
        total_targets = len(targets)
        create_data_card(
            "目标总数",
            total_targets,
            "个",
            icon="🛰️"
        )
    
    with col_target2:
        detected_targets = results.get('detected_targets', len(targets) * 0.8)
        create_data_card(
            "检测目标数",
            int(detected_targets),
            "个",
            icon="🎯"
        )
    
    with col_target3:
        avg_track_time = results.get('avg_track_time', 150)
        create_data_card(
            "平均跟踪时间",
            f"{avg_track_time:.0f}",
            "秒",
            icon="⏱️"
        )
    
    with col_target4:
        track_break_count = results.get('track_break_count', 3)
        create_data_card(
            "航迹断裂次数",
            track_break_count,
            "次",
            icon="🔀"
        )
    
    st.markdown("---")
    
    # 目标类型分析
    st.markdown("### 📊 目标类型分析")
    
    # 统计目标类型
    target_types = {}
    for target in targets:
        ttype = target.get('type', 'unknown')
        target_types[ttype] = target_types.get(ttype, 0) + 1
    
    col_type1, col_type2 = st.columns(2)
    
    with col_type1:
        # 饼图
        fig1 = go.Figure(data=[
            go.Pie(
                labels=list(target_types.keys()),
                values=list(target_types.values()),
                hole=0.4,
                marker_colors=['#1a73e8', '#00e676', '#ff9800', '#f44336', '#9c27b0']
            )
        ])
        
        fig1.update_layout(
            height=300,
            title="目标类型分布",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_type2:
        # 检测率按类型
        st.markdown("#### 📈 各类目标检测率")
        
        # 模拟数据
        type_detection_rates = {
            "fighter": 0.85,
            "bomber": 0.95,
            "uav": 0.65,
            "missile": 0.75,
            "transport": 0.90
        }
        
        for ttype, rate in type_detection_rates.items():
            if ttype in target_types:
                st.progress(rate, text=f"{ttype}: {rate:.1%}")
    
    st.markdown("---")
    
    # 目标运动分析
    st.markdown("### 🛩️ 目标运动分析")
    
    col_motion1, col_motion2 = st.columns(2)
    
    with col_motion1:
        st.markdown("#### 📏 距离分布")
        
        # 生成距离分布
        ranges = np.random.exponential(50, 1000)
        
        fig2 = go.Figure(data=[
            go.Histogram(
                x=ranges,
                nbinsx=20,
                marker_color='#1a73e8',
                opacity=0.7
            )
        ])
        
        fig2.update_layout(
            height=300,
            xaxis_title="距离 (km)",
            yaxis_title="频数",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with col_motion2:
        st.markdown("#### 📈 高度分布")
        
        # 生成高度分布
        altitudes = np.random.normal(10000, 3000, 1000)
        
        fig3 = go.Figure(data=[
            go.Histogram(
                x=altitudes,
                nbinsx=20,
                marker_color='#00e676',
                opacity=0.7
            )
        ])
        
        fig3.update_layout(
            height=300,
            xaxis_title="高度 (m)",
            yaxis_title="频数",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    
    # 目标轨迹分析
    st.markdown("### 🛤️ 目标轨迹分析")
    
    # 选择目标查看轨迹
    target_names = [t.get('name', f'目标{i+1}') for i, t in enumerate(targets)]
    selected_target = st.selectbox("选择目标查看轨迹", target_names)
    
    if selected_target:
        target_index = next(i for i, t in enumerate(targets) if t.get('name') == selected_target)
        
        # 生成轨迹数据
        trajectory = generate_trajectory_data(target_index)
        
        # 3D轨迹图
        fig4 = go.Figure(data=[
            go.Scatter3d(
                x=trajectory['x'],
                y=trajectory['y'],
                z=trajectory['z'],
                mode='lines+markers',
                marker=dict(
                    size=4,
                    color=trajectory['time'],
                    colorscale='Viridis',
                    showscale=True
                ),
                line=dict(
                    color='white',
                    width=2
                )
            )
        ])
        
        fig4.update_layout(
            height=500,
            title=f"{selected_target} 轨迹",
            scene=dict(
                xaxis_title="经度",
                yaxis_title="纬度",
                zaxis_title="高度 (m)"
            ),
            template="plotly_dark"
        )
        
        st.plotly_chart(fig4, use_container_width=True)
        
        # 轨迹统计数据
        col_traj1, col_traj2, col_traj3 = st.columns(3)
        
        with col_traj1:
            st.metric("轨迹长度", f"{len(trajectory['x'])} 点")
        
        with col_traj2:
            total_distance = calculate_trajectory_distance(trajectory)
            st.metric("总飞行距离", f"{total_distance:.1f} km")
        
        with col_traj3:
            avg_speed = calculate_average_speed(trajectory)
            st.metric("平均速度", f"{avg_speed:.0f} 节")

def generate_trajectory_data(target_index):
    """生成轨迹数据"""
    n_points = 100
    time = np.linspace(0, 300, n_points)
    
    # 生成螺旋上升轨迹
    t = np.linspace(0, 4*np.pi, n_points)
    x = 116.4 + 0.1 * np.sin(t)
    y = 39.9 + 0.1 * np.cos(t)
    z = 5000 + 2000 * (t / (4*np.pi))
    
    return {
        'x': x,
        'y': y,
        'z': z,
        'time': time
    }

def calculate_trajectory_distance(trajectory):
    """计算轨迹距离"""
    x = trajectory['x']
    y = trajectory['y']
    
    # 将经纬度转换为距离（简化计算）
    total_distance = 0
    for i in range(1, len(x)):
        # 使用Haversine公式的简化版本
        dx = (x[i] - x[i-1]) * 111.32  # 1度经度约111km
        dy = (y[i] - y[i-1]) * 111.32
        distance = np.sqrt(dx**2 + dy**2)
        total_distance += distance
    
    return total_distance

def calculate_average_speed(trajectory):
    """计算平均速度"""
    total_distance = calculate_trajectory_distance(trajectory)
    total_time = trajectory['time'][-1] - trajectory['time'][0]
    
    if total_time > 0:
        speed_km_s = total_distance / total_time
        speed_kts = speed_km_s * 0.539957  # 转换为节
        return speed_kts
    
    return 0

if __name__ == "__main__":
    main()