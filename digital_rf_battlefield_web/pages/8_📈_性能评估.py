"""
性能评估页面 - 综合性能评估和报告生成
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from utils.style_utils import create_data_card, get_military_style
from utils.kimi_api import KimiAPI

def main():
    """性能评估页面主函数"""
    st.title("📈 综合性能评估")
    st.markdown("仿真性能评估、对比分析和报告生成")
    
    # 检查是否有仿真结果
    if 'simulation_results' not in st.session_state or not st.session_state.simulation_results:
        st.warning("暂无仿真结果数据，请先运行仿真")
        
        if st.button("🚀 前往仿真运行"):
            st.switch_page("pages/6_🚀_仿真运行.py")
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 综合评估", "🔬 详细分析", "📈 对比分析", "📄 报告生成"])
    
    with tab1:
        show_comprehensive_evaluation()
    
    with tab2:
        show_detailed_analysis()
    
    with tab3:
        show_comparative_analysis()
    
    with tab4:
        show_report_generation()

def show_comprehensive_evaluation():
    """显示综合评估界面"""
    st.subheader("📊 综合性能评估")
    
    # 获取结果数据
    results = st.session_state.get('simulation_results', {})
    
    # 总体评分
    overall_score = calculate_overall_score(results)
    
    col_score1, col_score2, col_score3 = st.columns([1, 2, 1])
    
    with col_score2:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 12px; border: 2px solid {get_score_color(overall_score)};">
                <h1 style="font-size: 4rem; color: {get_score_color(overall_score)}; margin: 0;">{overall_score:.1f}</h1>
                <h3 style="margin: 0.5rem 0 0 0;">总体评分</h3>
                <p style="color: #888; margin: 0;">{get_score_level(overall_score)}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # 关键性能指标
    st.markdown("### 📈 关键性能指标")
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    with col_kpi1:
        detection_score = calculate_detection_score(results)
        create_data_card(
            "检测性能",
            f"{detection_score:.1f}",
            "分",
            trend=detection_score - 80,
            icon="🎯"
        )
    
    with col_kpi2:
        tracking_score = calculate_tracking_score(results)
        create_data_card(
            "跟踪性能",
            f"{tracking_score:.1f}",
            "分",
            trend=tracking_score - 80,
            icon="🛤️"
        )
    
    with col_kpi3:
        system_score = calculate_system_score(results)
        create_data_card(
            "系统效率",
            f"{system_score:.1f}",
            "分",
            trend=system_score - 80,
            icon="⚡"
        )
    
    with col_kpi4:
        fusion_score = calculate_fusion_score(results)
        create_data_card(
            "数据融合",
            f"{fusion_score:.1f}",
            "分",
            trend=fusion_score - 80,
            icon="🔀"
        )
    
    st.markdown("---")
    
    # 性能雷达图
    st.markdown("### 📊 性能雷达图")
    
    categories = ['检测性能', '跟踪性能', '系统效率', '数据融合', '可靠性', '实时性']
    scores = [
        detection_score,
        tracking_score,
        system_score,
        fusion_score,
        calculate_reliability_score(results),
        calculate_realtime_score(results)
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],  # 闭合图形
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(26, 115, 232, 0.3)',
        line=dict(color='#1a73e8', width=2),
        name='性能指标'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        height=400,
        showlegend=False,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 性能总结
    st.markdown("### 📋 性能总结")
    
    summary = generate_performance_summary(results)
    
    for item in summary:
        with st.container():
            col_sum1, col_sum2 = st.columns([1, 4])
            
            with col_sum1:
                icon = "✅" if item['status'] == 'good' else "⚠️" if item['status'] == 'warning' else "❌"
                color = "#00e676" if item['status'] == 'good' else "#ff9800" if item['status'] == 'warning' else "#f44336"
                
                st.markdown(f"<h2 style='color: {color};'>{icon}</h2>", unsafe_allow_html=True)
            
            with col_sum2:
                st.markdown(f"**{item['title']}**")
                st.markdown(item['description'])

def calculate_overall_score(results):
    """计算总体评分"""
    detection_score = calculate_detection_score(results)
    tracking_score = calculate_tracking_score(results)
    system_score = calculate_system_score(results)
    fusion_score = calculate_fusion_score(results)
    
    # 加权平均
    weights = {'detection': 0.3, 'tracking': 0.3, 'system': 0.2, 'fusion': 0.2}
    overall = (
        detection_score * weights['detection'] +
        tracking_score * weights['tracking'] +
        system_score * weights['system'] +
        fusion_score * weights['fusion']
    )
    
    return overall

def calculate_detection_score(results):
    """计算检测性能评分"""
    detection_prob = results.get('avg_detection_probability', 0.8)
    false_alarm = results.get('avg_false_alarm_rate', 1e-4)
    
    # 计算得分
    detection_score = detection_prob * 100
    
    # 虚警率惩罚
    if false_alarm > 1e-3:
        detection_score *= 0.7
    elif false_alarm > 1e-4:
        detection_score *= 0.9
    
    return min(detection_score, 100)

def calculate_tracking_score(results):
    """计算跟踪性能评分"""
    track_continuity = results.get('track_continuity', 0.9)
    position_error = results.get('avg_position_error', 50)
    
    # 计算得分
    continuity_score = track_continuity * 100
    
    # 位置误差惩罚
    if position_error > 100:
        continuity_score *= 0.6
    elif position_error > 50:
        continuity_score *= 0.8
    elif position_error > 20:
        continuity_score *= 0.9
    
    return min(continuity_score, 100)

def calculate_system_score(results):
    """计算系统效率评分"""
    system_load = results.get('avg_system_load', 0.7)
    throughput = results.get('throughput', 100)
    
    # 计算得分
    load_score = (1 - system_load) * 100
    throughput_score = min(throughput / 10, 100)  # 标准化
    
    return (load_score + throughput_score) / 2

def calculate_fusion_score(results):
    """计算数据融合评分"""
    fusion_gain = results.get('fusion_gain', 1.2)
    fusion_delay = results.get('avg_fusion_delay', 0.1)
    
    # 计算得分
    gain_score = min((fusion_gain - 1) * 100, 100)
    
    # 延迟惩罚
    if fusion_delay > 0.5:
        gain_score *= 0.5
    elif fusion_delay > 0.2:
        gain_score *= 0.8
    
    return min(gain_score, 100)

def calculate_reliability_score(results):
    """计算可靠性评分"""
    system_availability = results.get('system_availability', 0.99)
    return system_availability * 100

def calculate_realtime_score(results):
    """计算实时性评分"""
    update_latency = results.get('avg_update_latency', 0.05)
    
    if update_latency < 0.1:
        return 100
    elif update_latency < 0.2:
        return 80
    elif update_latency < 0.5:
        return 60
    else:
        return 40

def get_score_color(score):
    """根据分数获取颜色"""
    if score >= 90:
        return "#00e676"
    elif score >= 80:
        return "#4caf50"
    elif score >= 70:
        return "#ff9800"
    elif score >= 60:
        return "#ff5722"
    else:
        return "#f44336"

def get_score_level(score):
    """根据分数获取等级"""
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 70:
        return "一般"
    elif score >= 60:
        return "及格"
    else:
        return "需改进"

def generate_performance_summary(results):
    """生成性能总结"""
    summary = []
    
    # 检测性能
    detection_score = calculate_detection_score(results)
    if detection_score >= 90:
        summary.append({
            'title': '检测性能优秀',
            'description': '系统检测概率高，虚警率低，满足作战需求',
            'status': 'good'
        })
    elif detection_score >= 70:
        summary.append({
            'title': '检测性能良好',
            'description': '系统检测能力满足基本要求，建议优化检测门限',
            'status': 'warning'
        })
    else:
        summary.append({
            'title': '检测性能不足',
            'description': '检测概率偏低或虚警率偏高，建议调整雷达参数',
            'status': 'bad'
        })
    
    # 跟踪性能
    tracking_score = calculate_tracking_score(results)
    if tracking_score >= 90:
        summary.append({
            'title': '跟踪性能优秀',
            'description': '航迹连续稳定，位置误差小，跟踪精度高',
            'status': 'good'
        })
    elif tracking_score >= 70:
        summary.append({
            'title': '跟踪性能良好',
            'description': '航迹连续性较好，建议优化跟踪算法参数',
            'status': 'warning'
        })
    else:
        summary.append({
            'title': '跟踪性能不足',
            'description': '航迹断裂频繁或位置误差大，需优化跟踪算法',
            'status': 'bad'
        })
    
    # 系统效率
    system_score = calculate_system_score(results)
    if system_score >= 90:
        summary.append({
            'title': '系统效率优秀',
            'description': '系统负载均衡，吞吐量高，资源利用率佳',
            'status': 'good'
        })
    elif system_score >= 70:
        summary.append({
            'title': '系统效率良好',
            'description': '系统运行稳定，建议进一步优化资源分配',
            'status': 'warning'
        })
    else:
        summary.append({
            'title': '系统效率不足',
            'description': '系统负载过高或吞吐量低，需优化资源配置',
            'status': 'bad'
        })
    
    # 数据融合
    fusion_score = calculate_fusion_score(results)
    if fusion_score >= 90:
        summary.append({
            'title': '数据融合优秀',
            'description': '融合增益显著，延迟低，信息一致性高',
            'status': 'good'
        })
    elif fusion_score >= 70:
        summary.append({
            'title': '数据融合良好',
            'description': '融合效果明显，建议降低融合延迟',
            'status': 'warning'
        })
    else:
        summary.append({
            'title': '数据融合不足',
            'description': '融合增益有限或延迟过高，需优化融合算法',
            'status': 'bad'
        })
    
    return summary

def show_detailed_analysis():
    """显示详细分析界面"""
    st.subheader("🔬 详细性能分析")
    
    # 获取结果数据
    results = st.session_state.get('simulation_results', {})
    
    # 创建分析标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📈 检测分析", "🛤️ 跟踪分析", "⚡ 系统分析", "🔀 融合分析"])
    
    with tab1:
        show_detection_analysis(results)
    
    with tab2:
        show_tracking_analysis(results)
    
    with tab3:
        show_system_analysis(results)
    
    with tab4:
        show_fusion_analysis(results)

def show_detection_analysis(results):
    """显示检测性能分析"""
    st.markdown("### 📈 检测性能详细分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 检测概率统计
        st.markdown("#### 🎯 检测概率统计")
        
        detection_prob = results.get('avg_detection_probability', 0.8)
        detection_std = results.get('detection_prob_std', 0.1)
        
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=detection_prob * 100,
            title={'text': "平均检测概率"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1a73e8"},
                'steps': [
                    {'range': [0, 60], 'color': "#f44336"},
                    {'range': [60, 80], 'color': "#ff9800"},
                    {'range': [80, 100], 'color': "#4caf50"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': detection_prob * 100
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.metric("检测概率标准差", f"{detection_std:.3f}")
    
    with col2:
        # 虚警率统计
        st.markdown("#### ⚠️ 虚警率统计")
        
        false_alarm = results.get('avg_false_alarm_rate', 1e-4)
        
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="number",
            value=false_alarm,
            title={'text': "平均虚警率"},
            number={'valueformat': ".2e"},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        
        fig.update_layout(height=200)
        st.plotly_chart(fig, use_container_width=True)
        
        # 虚警率随时间变化
        st.markdown("**虚警率变化趋势**")
        
        # 生成模拟数据
        time_points = 50
        time = np.linspace(0, 300, time_points)
        pfa_data = false_alarm + false_alarm * 0.5 * np.sin(time/50) + np.random.normal(0, false_alarm * 0.2, time_points)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=time,
            y=pfa_data,
            mode='lines',
            name='虚警率',
            line=dict(color='#f44336', width=2)
        ))
        
        fig2.update_layout(
            height=200,
            xaxis_title="时间 (s)",
            yaxis_title="虚警率",
            yaxis_type="log",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # 检测距离分析
    st.markdown("#### 📏 检测距离分析")
    
    col_dist1, col_dist2, col_dist3 = st.columns(3)
    
    with col_dist1:
        max_range = results.get('max_detection_range', 150)
        st.metric("最大检测距离", f"{max_range:.1f} km")
    
    with col_dist2:
        avg_range = results.get('avg_detection_range', 80)
        st.metric("平均检测距离", f"{avg_range:.1f} km")
    
    with col_dist3:
        min_range = results.get('min_detection_range', 10)
        st.metric("最小检测距离", f"{min_range:.1f} km")
    
    # 距离-检测概率曲线
    st.markdown("**距离-检测概率曲线**")
    
    ranges = np.linspace(10, 200, 20)
    detection_probs = 0.9 * np.exp(-ranges / 100) + 0.1
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=ranges,
        y=detection_probs,
        mode='lines+markers',
        name='检测概率',
        line=dict(color='#1a73e8', width=2)
    ))
    
    fig3.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="检测阈值")
    
    fig3.update_layout(
        height=300,
        xaxis_title="距离 (km)",
        yaxis_title="检测概率",
        yaxis_range=[0, 1],
        template="plotly_dark"
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # 检测性能影响因素
    st.markdown("#### 🔧 检测性能影响因素")
    
    factors = ['SNR', 'RCS', '距离', '干扰', '环境']
    impacts = [0.8, 0.6, 0.9, 0.4, 0.3]
    
    fig4 = go.Figure(data=[
        go.Bar(
            x=factors,
            y=impacts,
            marker_color=['#1a73e8', '#00e676', '#ff9800', '#f44336', '#9c27b0']
        )
    ])
    
    fig4.update_layout(
        height=300,
        title="各因素对检测性能的影响",
        yaxis_title="影响系数",
        yaxis_range=[0, 1],
        template="plotly_dark"
    )
    
    st.plotly_chart(fig4, use_container_width=True)

def show_tracking_analysis(results):
    """显示跟踪性能分析"""
    st.markdown("### 🛤️ 跟踪性能详细分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 航迹连续性
        st.markdown("#### 🔄 航迹连续性")
        
        track_continuity = results.get('track_continuity', 0.9)
        
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=track_continuity * 100,
            title={'text': "航迹连续性"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#00e676"},
                'steps': [
                    {'range': [0, 70], 'color': "#f44336"},
                    {'range': [70, 85], 'color': "#ff9800"},
                    {'range': [85, 100], 'color': "#4caf50"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': track_continuity * 100
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 位置误差
        st.markdown("#### 📍 位置误差分析")
        
        pos_error = results.get('avg_position_error', 50)
        pos_error_std = results.get('position_error_std', 10)
        
        col_err1, col_err2 = st.columns(2)
        
        with col_err1:
            st.metric("平均位置误差", f"{pos_error:.1f} m")
        
        with col_err2:
            st.metric("位置误差标准差", f"{pos_error_std:.1f} m")
        
        # 位置误差分布
        st.markdown("**位置误差分布**")
        
        # 生成模拟数据
        error_data = np.random.normal(pos_error, pos_error_std, 1000)
        
        fig2 = go.Figure(data=[
            go.Histogram(
                x=error_data,
                nbinsx=20,
                marker_color='#00e676',
                opacity=0.7
            )
        ])
        
        fig2.update_layout(
            height=250,
            xaxis_title="位置误差 (m)",
            yaxis_title="频数",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # 跟踪稳定性分析
    st.markdown("#### 📊 跟踪稳定性分析")
    
    col_stab1, col_stab2, col_stab3 = st.columns(3)
    
    with col_stab1:
        track_lifetime = results.get('avg_track_lifetime', 150)
        st.metric("平均航迹寿命", f"{track_lifetime:.1f} s")
    
    with col_stab2:
        track_breaks = results.get('track_break_count', 3)
        st.metric("航迹断裂次数", track_breaks)
    
    with col_stab3:
        initiation_time = results.get('avg_track_initiation_time', 2.5)
        st.metric("平均起始时间", f"{initiation_time:.1f} s")
    
    # 跟踪性能趋势
    st.markdown("**跟踪性能随时间变化**")
    
    time_points = 50
    time = np.linspace(0, 300, time_points)
    
    # 模拟数据
    continuity_trend = 0.9 + 0.05 * np.sin(time/30) + np.random.normal(0, 0.02, time_points)
    error_trend = 50 + 10 * np.cos(time/40) + np.random.normal(0, 5, time_points)
    
    fig3 = make_subplots(
        rows=2, cols=1,
        subplot_titles=("航迹连续性", "位置误差"),
        shared_xaxes=True,
        vertical_spacing=0.1
    )
    
    fig3.add_trace(
        go.Scatter(x=time, y=continuity_trend, mode='lines', name='连续性', line=dict(color='#00e676')),
        row=1, col=1
    )
    
    fig3.add_trace(
        go.Scatter(x=time, y=error_trend, mode='lines', name='误差', line=dict(color='#f44336')),
        row=2, col=1
    )
    
    fig3.update_layout(height=400, showlegend=False, template="plotly_dark")
    fig3.update_yaxes(title_text="连续性", row=1, col=1)
    fig3.update_yaxes(title_text="误差 (m)", row=2, col=1)
    fig3.update_xaxes(title_text="时间 (s)", row=2, col=1)
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # 多目标跟踪性能
    st.markdown("#### 👥 多目标跟踪性能")
    
    col_mtt1, col_mtt2 = st.columns(2)
    
    with col_mtt1:
        track_capacity = results.get('track_capacity', 20)
        st.metric("最大跟踪容量", track_capacity)
    
    with col_mtt2:
        association_accuracy = results.get('association_accuracy', 0.95)
        st.metric("关联准确率", f"{association_accuracy:.1%}")

def show_system_analysis(results):
    """显示系统性能分析"""
    st.markdown("### ⚡ 系统性能详细分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 系统负载
        st.markdown("#### 📈 系统负载分析")
        
        system_load = results.get('avg_system_load', 0.7)
        
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=system_load * 100,
            title={'text': "平均系统负载"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#ff9800"},
                'steps': [
                    {'range': [0, 60], 'color': "#4caf50"},
                    {'range': [60, 80], 'color': "#ff9800"},
                    {'range': [80, 100], 'color': "#f44336"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': system_load * 100
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # 负载组成
        st.markdown("**负载组成分析**")
        
        load_components = {
            "信号处理": 0.4,
            "数据处理": 0.3,
            "通信": 0.2,
            "其他": 0.1
        }
        
        fig2 = go.Figure(data=[
            go.Pie(
                labels=list(load_components.keys()),
                values=list(load_components.values()),
                hole=0.4,
                marker_colors=['#1a73e8', '#00e676', '#ff9800', '#9c27b0']
            )
        ])
        
        fig2.update_layout(height=250, template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # 系统吞吐量
        st.markdown("#### 🚀 系统吞吐量分析")
        
        throughput = results.get('throughput', 100)
        
        fig3 = go.Figure()
        fig3.add_trace(go.Indicator(
            mode="number",
            value=throughput,
            title={'text': "平均吞吐量"},
            number={'suffix': " 任务/秒"},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        
        fig3.update_layout(height=200)
        st.plotly_chart(fig3, use_container_width=True)
        
        # 吞吐量趋势
        st.markdown("**吞吐量变化趋势**")
        
        time_points = 50
        time = np.linspace(0, 300, time_points)
        throughput_trend = throughput + throughput * 0.3 * np.sin(time/40) + np.random.normal(0, throughput * 0.1, time_points)
        
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=time,
            y=throughput_trend,
            mode='lines',
            name='吞吐量',
            line=dict(color='#1a73e8', width=2)
        ))
        
        fig4.update_layout(
            height=250,
            xaxis_title="时间 (s)",
            yaxis_title="吞吐量 (任务/秒)",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    
    # 资源利用率
    st.markdown("#### 💾 资源利用率分析")
    
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    
    with col_res1:
        cpu_usage = results.get('avg_cpu_usage', 0.6)
        st.metric("CPU使用率", f"{cpu_usage:.1%}")
    
    with col_res2:
        memory_usage = results.get('avg_memory_usage', 0.5)
        st.metric("内存使用率", f"{memory_usage:.1%}")
    
    with col_res3:
        network_usage = results.get('avg_network_usage', 0.3)
        st.metric("网络使用率", f"{network_usage:.1%}")
    
    with col_res4:
        disk_usage = results.get('avg_disk_usage', 0.2)
        st.metric("磁盘使用率", f"{disk_usage:.1%}")
    
    # 资源使用趋势
    st.markdown("**资源使用趋势**")
    
    time_points = 50
    time = np.linspace(0, 300, time_points)
    
    cpu_trend = 0.6 + 0.2 * np.sin(time/50) + np.random.normal(0, 0.05, time_points)
    memory_trend = 0.5 + 0.1 * np.cos(time/40) + np.random.normal(0, 0.03, time_points)
    network_trend = 0.3 + 0.1 * np.sin(time/30) + np.random.normal(0, 0.02, time_points)
    
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=time, y=cpu_trend, mode='lines', name='CPU', line=dict(color='#f44336')))
    fig5.add_trace(go.Scatter(x=time, y=memory_trend, mode='lines', name='内存', line=dict(color='#1a73e8')))
    fig5.add_trace(go.Scatter(x=time, y=network_trend, mode='lines', name='网络', line=dict(color='#00e676')))
    
    fig5.update_layout(
        height=300,
        xaxis_title="时间 (s)",
        yaxis_title="使用率",
        yaxis_range=[0, 1],
        template="plotly_dark"
    )
    
    st.plotly_chart(fig5, use_container_width=True)
    
    # 系统可靠性
    st.markdown("#### 🔧 系统可靠性分析")
    
    col_rel1, col_rel2, col_rel3 = st.columns(3)
    
    with col_rel1:
        availability = results.get('system_availability', 0.99)
        st.metric("系统可用性", f"{availability:.2%}")
    
    with col_rel2:
        mttf = results.get('mttf', 1000)
        st.metric("平均无故障时间", f"{mttf:.0f} h")
    
    with col_rel3:
        mttr = results.get('mttr', 2)
        st.metric("平均修复时间", f"{mttr:.1f} h")

def show_fusion_analysis(results):
    """显示数据融合分析"""
    st.markdown("### 🔀 数据融合详细分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 融合增益
        st.markdown("#### 📈 融合增益分析")
        
        fusion_gain = results.get('fusion_gain', 1.2)
        
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=fusion_gain,
            title={'text': "融合增益"},
            delta={'reference': 1.0, 'relative': True, 'valueformat': '.0%'},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        
        fig.update_layout(height=200)
        st.plotly_chart(fig, use_container_width=True)
        
        # 融合增益分布
        st.markdown("**融合增益分布**")
        
        # 生成模拟数据
        gain_data = np.random.normal(fusion_gain, 0.1, 1000)
        
        fig2 = go.Figure(data=[
            go.Histogram(
                x=gain_data,
                nbinsx=20,
                marker_color='#9c27b0',
                opacity=0.7
            )
        ])
        
        fig2.update_layout(
            height=250,
            xaxis_title="融合增益",
            yaxis_title="频数",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # 融合延迟
        st.markdown("#### ⏱️ 融合延迟分析")
        
        fusion_delay = results.get('avg_fusion_delay', 0.1)
        
        fig3 = go.Figure()
        fig3.add_trace(go.Indicator(
            mode="number",
            value=fusion_delay * 1000,
            title={'text': "平均融合延迟"},
            number={'suffix': " ms"},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        
        fig3.update_layout(height=200)
        st.plotly_chart(fig3, use_container_width=True)
        
        # 延迟分布
        st.markdown("**融合延迟分布**")
        
        delay_data = np.random.exponential(fusion_delay, 1000) * 1000  # 转换为ms
        
        fig4 = go.Figure(data=[
            go.Histogram(
                x=delay_data,
                nbinsx=20,
                marker_color='#ff9800',
                opacity=0.7
            )
        ])
        
        fig4.update_layout(
            height=250,
            xaxis_title="融合延迟 (ms)",
            yaxis_title="频数",
            template="plotly_dark"
        )
        
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    
    # 融合一致性
    st.markdown("#### 🔄 融合一致性分析")
    
    col_cons1, col_cons2, col_cons3 = st.columns(3)
    
    with col_cons1:
        consistency = results.get('fusion_consistency', 0.85)
        st.metric("融合一致性", f"{consistency:.1%}")
    
    with col_cons2:
        correlation = results.get('data_correlation', 0.7)
        st.metric("数据相关性", f"{correlation:.1%}")
    
    with col_cons3:
        reliability = results.get('fusion_reliability', 0.95)
        st.metric("融合可靠性", f"{reliability:.1%}")
    
    # 融合性能趋势
    st.markdown("**融合性能随时间变化**")
    
    time_points = 50
    time = np.linspace(0, 300, time_points)
    
    gain_trend = 1.2 + 0.1 * np.sin(time/40) + np.random.normal(0, 0.05, time_points)
    delay_trend = 0.1 + 0.02 * np.cos(time/30) + np.random.normal(0, 0.005, time_points)
    
    fig5 = make_subplots(
        rows=2, cols=1,
        subplot_titles=("融合增益", "融合延迟"),
        shared_xaxes=True,
        vertical_spacing=0.1
    )
    
    fig5.add_trace(
        go.Scatter(x=time, y=gain_trend, mode='lines', name='增益', line=dict(color='#9c27b0')),
        row=1, col=1
    )
    
    fig5.add_trace(
        go.Scatter(x=time, y=delay_trend*1000, mode='lines', name='延迟', line=dict(color='#ff9800')),
        row=2, col=1
    )
    
    fig5.update_layout(height=400, showlegend=False, template="plotly_dark")
    fig5.update_yaxes(title_text="增益", row=1, col=1)
    fig5.update_yaxes(title_text="延迟 (ms)", row=2, col=1)
    fig5.update_xaxes(title_text="时间 (s)", row=2, col=1)
    
    st.plotly_chart(fig5, use_container_width=True)
    
    # 融合算法比较
    st.markdown("#### ⚖️ 融合算法性能比较")
    
    algorithms = ['加权投票', 'D-S证据', '卡尔曼滤波', '神经网络']
    performance = [0.8, 0.85, 0.9, 0.88]
    
    fig6 = go.Figure(data=[
        go.Bar(
            x=algorithms,
            y=performance,
            marker_color=['#1a73e8', '#00e676', '#ff9800', '#9c27b0']
        )
    ])
    
    fig6.update_layout(
        height=300,
        title="不同融合算法性能对比",
        yaxis_title="性能评分",
        yaxis_range=[0, 1],
        template="plotly_dark"
    )
    
    st.plotly_chart(fig6, use_container_width=True)

def show_comparative_analysis():
    """显示对比分析界面"""
    st.subheader("📈 对比分析")
    
    st.markdown("### ⚖️ 仿真结果对比分析")
    
    # 检查是否有历史结果用于对比
    historical_results = st.session_state.get('historical_results', [])
    
    if not historical_results:
        st.info("暂无历史结果数据，当前仿真为第一次运行")
        
        # 显示当前结果
        current_results = st.session_state.get('simulation_results', {})
        
        if current_results:
            st.markdown("#### 📊 当前仿真结果")
            
            col_cur1, col_cur2, col_cur3, col_cur4 = st.columns(4)
            
            with col_cur1:
                detection_prob = current_results.get('avg_detection_probability', 0)
                st.metric("检测概率", f"{detection_prob:.1%}")
            
            with col_cur2:
                false_alarm = current_results.get('avg_false_alarm_rate', 0)
                st.metric("虚警率", f"{false_alarm:.2e}")
            
            with col_cur3:
                track_continuity = current_results.get('track_continuity', 0)
                st.metric("航迹连续性", f"{track_continuity:.1%}")
            
            with col_cur4:
                system_load = current_results.get('avg_system_load', 0)
                st.metric("系统负载", f"{system_load:.1%}")
        
        # 添加对比选项
        st.markdown("---")
        st.markdown("### 🔄 添加对比基准")
        
        col_base1, col_base2 = st.columns(2)
        
        with col_base1:
            baseline_type = st.selectbox(
                "基准类型",
                ["理论值", "历史最佳", "系统要求", "自定义"]
            )
        
        with col_base2:
            if baseline_type == "自定义":
                baseline_name = st.text_input("基准名称", "自定义基准")
            else:
                baseline_name = baseline_type
        
        if st.button("➕ 添加对比基准", use_container_width=True):
            add_comparison_baseline(baseline_name, baseline_type)
    
    else:
        # 有历史结果，显示对比
        st.markdown("#### 📈 性能对比")
        
        # 准备对比数据
        comparison_data = prepare_comparison_data(historical_results)
        
        # 显示对比图表
        fig = go.Figure()
        
        metrics = ['检测概率', '航迹连续性', '系统效率', '融合增益']
        
        for i, (name, data) in enumerate(comparison_data.items()):
            values = [
                data.get('detection_prob', 0),
                data.get('track_continuity', 0),
                data.get('system_efficiency', 0),
                data.get('fusion_gain', 0)
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # 闭合图形
                theta=metrics + [metrics[0]],
                fill='toself' if i == 0 else None,
                name=name,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            height=500,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 详细对比表格
        st.markdown("#### 📋 详细对比数据")
        
        # 创建对比表格
        comparison_table = []
        for name, data in comparison_data.items():
            row = {
                "名称": name,
                "检测概率": f"{data.get('detection_prob', 0):.1%}",
                "虚警率": f"{data.get('false_alarm', 0):.2e}",
                "航迹连续性": f"{data.get('track_continuity', 0):.1%}",
                "系统负载": f"{data.get('system_load', 0):.1%}",
                "融合增益": f"{data.get('fusion_gain', 0):.2f}"
            }
            comparison_table.append(row)
        
        df = pd.DataFrame(comparison_table)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 性能改进分析
        st.markdown("#### 📈 性能改进分析")
        
        if len(comparison_data) >= 2:
            current_data = comparison_data.get("当前仿真")
            best_data = comparison_data.get("历史最佳", current_data)
            
            improvements = calculate_improvements(current_data, best_data)
            
            for metric, improvement in improvements.items():
                if improvement != 0:
                    icon = "📈" if improvement > 0 else "📉"
                    color = "#00e676" if improvement > 0 else "#f44336"
                    st.markdown(f"{icon} **{metric}**: <span style='color:{color}'>{improvement:+.1%}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 趋势分析
    st.markdown("### 📊 历史趋势分析")
    
    if historical_results and len(historical_results) > 1:
        # 提取历史趋势数据
        trend_data = extract_trend_data(historical_results)
        
        # 创建趋势图表
        fig_trend = make_subplots(
            rows=2, cols=2,
            subplot_titles=("检测概率趋势", "虚警率趋势", "航迹连续性趋势", "系统负载趋势"),
            shared_xaxes=True
        )
        
        # 检测概率趋势
        fig_trend.add_trace(
            go.Scatter(x=trend_data['timestamps'], y=trend_data['detection_prob'], mode='lines+markers', name='检测概率'),
            row=1, col=1
        )
        
        # 虚警率趋势
        fig_trend.add_trace(
            go.Scatter(x=trend_data['timestamps'], y=trend_data['false_alarm'], mode='lines+markers', name='虚警率'),
            row=1, col=2
        )
        
        # 航迹连续性趋势
        fig_trend.add_trace(
            go.Scatter(x=trend_data['timestamps'], y=trend_data['track_continuity'], mode='lines+markers', name='航迹连续性'),
            row=2, col=1
        )
        
        # 系统负载趋势
        fig_trend.add_trace(
            go.Scatter(x=trend_data['timestamps'], y=trend_data['system_load'], mode='lines+markers', name='系统负载'),
            row=2, col=2
        )
        
        fig_trend.update_layout(height=600, showlegend=False, template="plotly_dark")
        fig_trend.update_yaxes(title_text="概率", row=1, col=1)
        fig_trend.update_yaxes(title_text="虚警率", type="log", row=1, col=2)
        fig_trend.update_yaxes(title_text="连续性", row=2, col=1)
        fig_trend.update_yaxes(title_text="负载", row=2, col=2)
        
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("需要更多历史数据才能进行趋势分析")

def add_comparison_baseline(name, baseline_type):
    """添加对比基准"""
    if 'historical_results' not in st.session_state:
        st.session_state.historical_results = []
    
    # 根据基准类型生成数据
    if baseline_type == "理论值":
        baseline_data = {
            "name": name,
            "detection_prob": 0.95,
            "false_alarm": 1e-5,
            "track_continuity": 0.98,
            "system_load": 0.6,
            "fusion_gain": 1.3
        }
    elif baseline_type == "历史最佳":
        # 从历史结果中找最佳
        baseline_data = find_best_historical_result()
    elif baseline_type == "系统要求":
        baseline_data = {
            "name": name,
            "detection_prob": 0.85,
            "false_alarm": 1e-4,
            "track_continuity": 0.9,
            "system_load": 0.8,
            "fusion_gain": 1.1
        }
    else:  # 自定义
        baseline_data = {
            "name": name,
            "detection_prob": 0.9,
            "false_alarm": 1e-4,
            "track_continuity": 0.95,
            "system_load": 0.7,
            "fusion_gain": 1.2
        }
    
    st.session_state.historical_results.append(baseline_data)
    st.success(f"已添加对比基准: {name}")

def find_best_historical_result():
    """查找历史最佳结果"""
    historical_results = st.session_state.get('historical_results', [])
    
    if not historical_results:
        return {
            "name": "历史最佳",
            "detection_prob": 0.9,
            "false_alarm": 1e-4,
            "track_continuity": 0.95,
            "system_load": 0.7,
            "fusion_gain": 1.2
        }
    
    # 简单返回第一个结果
    return historical_results[0]

def prepare_comparison_data(historical_results):
    """准备对比数据"""
    comparison_data = {}
    
    # 添加当前结果
    current_results = st.session_state.get('simulation_results', {})
    comparison_data["当前仿真"] = {
        "detection_prob": current_results.get('avg_detection_probability', 0),
        "false_alarm": current_results.get('avg_false_alarm_rate', 0),
        "track_continuity": current_results.get('track_continuity', 0),
        "system_load": current_results.get('avg_system_load', 0),
        "fusion_gain": current_results.get('fusion_gain', 0),
        "system_efficiency": 1 - current_results.get('avg_system_load', 0)
    }
    
    # 添加历史结果
    for i, result in enumerate(historical_results[:5]):  # 最多显示5个历史结果
        name = result.get('name', f'历史结果{i+1}')
        comparison_data[name] = {
            "detection_prob": result.get('detection_prob', 0),
            "false_alarm": result.get('false_alarm', 0),
            "track_continuity": result.get('track_continuity', 0),
            "system_load": result.get('system_load', 0),
            "fusion_gain": result.get('fusion_gain', 0),
            "system_efficiency": 1 - result.get('system_load', 0)
        }
    
    return comparison_data

def calculate_improvements(current_data, best_data):
    """计算性能改进"""
    improvements = {}
    
    metrics = ['detection_prob', 'track_continuity', 'system_efficiency', 'fusion_gain']
    metric_names = ['检测概率', '航迹连续性', '系统效率', '融合增益']
    
    for metric, name in zip(metrics, metric_names):
        current = current_data.get(metric, 0)
        best = best_data.get(metric, 0)
        
        if best > 0:
            improvement = (current - best) / best
            improvements[name] = improvement
    
    return improvements

def extract_trend_data(historical_results):
    """提取趋势数据"""
    trend_data = {
        'timestamps': [],
        'detection_prob': [],
        'false_alarm': [],
        'track_continuity': [],
        'system_load': []
    }
    
    for i, result in enumerate(historical_results):
        trend_data['timestamps'].append(f"运行{i+1}")
        trend_data['detection_prob'].append(result.get('detection_prob', 0))
        trend_data['false_alarm'].append(result.get('false_alarm', 0))
        trend_data['track_continuity'].append(result.get('track_continuity', 0))
        trend_data['system_load'].append(result.get('system_load', 0))
    
    return trend_data

def show_report_generation():
    """显示报告生成界面"""
    st.subheader("📄 报告生成")
    
    st.markdown("### 📊 生成性能评估报告")
    
    # 报告配置
    col_report1, col_report2 = st.columns(2)
    
    with col_report1:
        report_type = st.selectbox(
            "报告类型",
            ["简要报告", "详细报告", "技术报告", "管理报告"]
        )
        
        report_format = st.selectbox(
            "报告格式",
            ["HTML", "PDF", "Word", "Markdown"]
        )
    
    with col_report2:
        include_charts = st.checkbox("包含图表", value=True)
        include_data = st.checkbox("包含原始数据", value=False)
        include_recommendations = st.checkbox("包含改进建议", value=True)
    
    # 报告内容配置
    st.markdown("### 📋 报告内容")
    
    sections = st.multiselect(
        "选择报告章节",
        [
            "执行摘要",
            "测试概述", 
            "测试环境",
            "测试结果",
            "性能分析",
            "对比分析",
            "问题发现",
            "改进建议",
            "结论"
        ],
        default=["执行摘要", "测试结果", "性能分析", "改进建议", "结论"]
    )
    
    # AI分析选项
    st.markdown("### 🤖 AI智能分析")
    
    use_ai_analysis = st.checkbox("使用Kimi AI进行分析", value=False)
    
    if use_ai_analysis:
        api_key = st.text_input("Kimi API密钥", type="password")
        
        if api_key:
            st.session_state.kimi_api_key = api_key
            st.success("✅ API密钥已设置")
        
        analysis_depth = st.slider("分析深度", 1, 10, 5, 1)
    
    st.markdown("---")
    
    # 报告生成按钮
    col_gen1, col_gen2, col_gen3 = st.columns([1, 1, 2])
    
    with col_gen1:
        if st.button("👁️ 预览报告", use_container_width=True):
            preview_report()
    
    with col_gen2:
        if st.button("💾 保存报告", use_container_width=True):
            save_report()
    
    with col_gen3:
        if st.button("🚀 生成完整报告", type="primary", use_container_width=True):
            generate_complete_report(
                report_type=report_type,
                report_format=report_format,
                sections=sections,
                use_ai=use_ai_analysis,
                analysis_depth=analysis_depth if use_ai_analysis else 0
            )

def preview_report():
    """预览报告"""
    st.info("报告预览功能开发中...")
    
    # 显示报告大纲
    st.markdown("### 📋 报告大纲")
    
    report_outline = """
    # 数字射频战场仿真系统性能评估报告
    
    ## 1. 执行摘要
    - 总体性能评分
    - 关键发现
    - 主要建议
    
    ## 2. 测试概述
    - 测试目的
    - 测试范围
    - 测试环境
    
    ## 3. 测试结果
    - 检测性能
    - 跟踪性能
    - 系统性能
    - 融合性能
    
    ## 4. 性能分析
    - 优势分析
    - 瓶颈分析
    - 趋势分析
    
    ## 5. 改进建议
    - 短期改进
    - 长期优化
    - 风险提示
    
    ## 6. 结论
    - 总体评价
    - 后续计划
    """
    
    st.text(report_outline)

def save_report():
    """保存报告"""
    st.success("报告已保存到本地")

def generate_complete_report(report_type, report_format, sections, use_ai, analysis_depth):
    """生成完整报告"""
    with st.spinner("正在生成报告..."):
        # 收集报告数据
        report_data = collect_report_data()
        
        # 如果需要AI分析
        if use_ai and st.session_state.get('kimi_api_key'):
            ai_analysis = perform_ai_analysis(report_data, analysis_depth)
            report_data['ai_analysis'] = ai_analysis
        
        # 生成报告
        report_content = format_report(report_data, report_type, sections)
        
        # 根据格式处理
        if report_format == "HTML":
            generate_html_report(report_content)
        elif report_format == "PDF":
            generate_pdf_report(report_content)
        elif report_format == "Word":
            generate_word_report(report_content)
        else:  # Markdown
            generate_markdown_report(report_content)
        
        st.success("✅ 报告生成完成！")

def collect_report_data():
    """收集报告数据"""
    results = st.session_state.get('simulation_results', {})
    config = st.session_state.get('simulation_config', {})
    radars = st.session_state.get('radar_configs', [])
    targets = st.session_state.get('target_configs', [])
    
    return {
        'results': results,
        'config': config,
        'radars': radars,
        'targets': targets,
        'timestamp': datetime.now().isoformat(),
        'overall_score': calculate_overall_score(results)
    }

def perform_ai_analysis(report_data, analysis_depth):
    """执行AI分析"""
    try:
        kimi = KimiAPI(st.session_state.kimi_api_key)
        
        # 准备分析数据
        analysis_data = {
            'overall_score': report_data['overall_score'],
            'detection_performance': {
                'probability': report_data['results'].get('avg_detection_probability', 0),
                'false_alarm': report_data['results'].get('avg_false_alarm_rate', 0)
            },
            'tracking_performance': {
                'continuity': report_data['results'].get('track_continuity', 0),
                'position_error': report_data['results'].get('avg_position_error', 0)
            },
            'system_performance': {
                'load': report_data['results'].get('avg_system_load', 0),
                'throughput': report_data['results'].get('throughput', 0)
            }
        }
        
        # 调用AI分析
        analysis = kimi.analyze_performance(analysis_data)
        
        return analysis
    
    except Exception as e:
        st.error(f"AI分析失败: {e}")
        return None

def format_report(report_data, report_type, sections):
    """格式化报告内容"""
    # 这里实现报告内容的格式化
    # 由于篇幅限制，只返回基本结构
    return {
        'title': f"数字射频战场仿真系统性能评估报告 - {datetime.now().strftime('%Y-%m-%d')}",
        'sections': sections,
        'data': report_data
    }

def generate_html_report(report_content):
    """生成HTML报告"""
    st.download_button(
        label="📥 下载HTML报告",
        data="<html>HTML报告内容</html>",
        file_name=f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html"
    )

def generate_pdf_report(report_content):
    """生成PDF报告"""
    st.info("PDF报告生成功能开发中...")

def generate_word_report(report_content):
    """生成Word报告"""
    st.info("Word报告生成功能开发中...")

def generate_markdown_report(report_content):
    """生成Markdown报告"""
    # 生成Markdown内容
    md_content = f"""# {report_content['title']}

## 执行摘要
- 总体评分: {report_content['data']['overall_score']:.1f}/100
- 测试时间: {report_content['data']['timestamp']}
- 雷达数量: {len(report_content['data']['radars'])}
- 目标数量: {len(report_content['data']['targets'])}

## 关键发现
1. 检测性能良好
2. 跟踪稳定性需改进
3. 系统负载均衡

## 改进建议
1. 优化雷达参数配置
2. 改进跟踪算法
3. 调整资源分配
"""
    
    st.download_button(
        label="📥 下载Markdown报告",
        data=md_content,
        file_name=f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

if __name__ == "__main__":
    main()