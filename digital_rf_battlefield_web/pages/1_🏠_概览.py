"""
概览页面 - 系统概览和仪表板
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.style_utils import create_data_card, create_gauge_chart, get_military_style

def main():
    """概览页面主函数"""
    st.title("🏠 系统概览")
    st.markdown("数字射频战场仿真系统 - 综合仪表板")
    
    # 快速状态概览
    show_quick_status()
    
    # 关键指标
    show_key_metrics()
    
    # 近期活动
    show_recent_activity()
    
    # 系统健康状态
    show_system_health()
    
    # 快速操作
    show_quick_actions()

def show_quick_status():
    """显示快速状态"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 系统状态
        system_status = "在线" if check_system_status() else "离线"
        status_color = "#00e676" if system_status == "在线" else "#f44336"
        
        st.markdown(
            f"""
            <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid {status_color};">
                <h3 style="margin: 0; color: {status_color};">{system_status}</h3>
                <p style="margin: 0; color: #888;">系统状态</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        # 仿真状态
        sim_status = st.session_state.get('simulation_status', 'stopped')
        status_text = {
            'stopped': '已停止',
            'running': '运行中',
            'paused': '已暂停'
        }.get(sim_status, '未知')
        
        status_color = {
            'stopped': '#f44336',
            'running': '#00e676',
            'paused': '#ff9800'
        }.get(sim_status, '#888')
        
        st.markdown(
            f"""
            <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid {status_color};">
                <h3 style="margin: 0; color: {status_color};">{status_text}</h3>
                <p style="margin: 0; color: #888;">仿真状态</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        # 数据状态
        data_count = count_data_points()
        
        st.markdown(
            f"""
            <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid #1a73e8;">
                <h3 style="margin: 0; color: #1a73e8;">{data_count:,}</h3>
                <p style="margin: 0; color: #888;">数据点数</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col4:
        # 用户活动
        active_users = 1  # 单用户模式
        
        st.markdown(
            f"""
            <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid #9c27b0;">
                <h3 style="margin: 0; color: #9c27b0;">{active_users}</h3>
                <p style="margin: 0; color: #888;">活跃用户</p>
            </div>
            """,
            unsafe_allow_html=True
        )

def check_system_status():
    """检查系统状态"""
    # 这里可以添加实际的系统状态检查
    return True

def count_data_points():
    """统计数据点数"""
    count = 0
    
    # 统计雷达数据
    radars = st.session_state.get('radar_configs', [])
    count += len(radars)
    
    # 统计目标数据
    targets = st.session_state.get('target_configs', [])
    count += len(targets)
    
    # 统计仿真结果
    results = st.session_state.get('simulation_results', {})
    if results:
        count += results.get('total_detections', 0)
    
    return count

def show_key_metrics():
    """显示关键指标"""
    st.markdown("### 📊 关键性能指标")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 检测概率
        results = st.session_state.get('simulation_results', {})
        detection_prob = results.get('avg_detection_probability', 0)
        
        create_data_card(
            "检测概率",
            f"{detection_prob:.1%}",
            "",
            icon="🎯"
        )
    
    with col2:
        # 虚警率
        false_alarm = results.get('avg_false_alarm_rate', 0)
        
        create_data_card(
            "虚警率",
            f"{false_alarm:.2e}",
            "",
            icon="⚠️"
        )
    
    with col3:
        # 航迹连续性
        track_continuity = results.get('track_continuity', 0)
        
        create_data_card(
            "航迹连续性",
            f"{track_continuity:.1%}",
            "",
            icon="🛤️"
        )
    
    with col4:
        # 系统负载
        system_load = results.get('avg_system_load', 0)
        
        create_data_card(
            "系统负载",
            f"{system_load:.1%}",
            "",
            icon="⚡"
        )
    
    st.markdown("---")

def show_recent_activity():
    """显示近期活动"""
    st.markdown("### 📅 近期活动")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 活动时间线
        activities = get_recent_activities()
        
        for activity in activities:
            with st.container():
                col_act1, col_act2, col_act3 = st.columns([1, 3, 1])
                
                with col_act1:
                    st.markdown(f"<div style='text-align: center;'>{activity['icon']}</div>", unsafe_allow_html=True)
                
                with col_act2:
                    st.markdown(f"**{activity['title']}**")
                    st.markdown(f"<small>{activity['description']}</small>", unsafe_allow_html=True)
                
                with col_act3:
                    st.markdown(f"<small style='color: #888;'>{activity['time']}</small>", unsafe_allow_html=True)
                
                st.markdown("---")
    
    with col2:
        # 统计图表
        st.markdown("#### 📈 活动统计")
        
        # 生成模拟数据
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        activities_count = [5, 8, 12, 9, 15, 7, 4]
        
        fig = go.Figure(data=[
            go.Bar(
                x=days,
                y=activities_count,
                marker_color='#1a73e8'
            )
        ])
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="日期",
            yaxis_title="活动数"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 今日统计
        st.markdown("#### 📊 今日统计")
        
        col_today1, col_today2 = st.columns(2)
        
        with col_today1:
            st.metric("仿真运行", "2次")
        
        with col_today2:
            st.metric("配置修改", "5次")

def get_recent_activities():
    """获取近期活动"""
    activities = [
        {
            'icon': '🚀',
            'title': '仿真运行完成',
            'description': '多雷达协同仿真运行完成，时长300秒',
            'time': '10分钟前'
        },
        {
            'icon': '⚙️',
            'title': '参数配置更新',
            'description': '更新雷达检测参数和波形参数',
            'time': '30分钟前'
        },
        {
            'icon': '📡',
            'title': '雷达部署调整',
            'description': '新增2部相控阵雷达到东北区域',
            'time': '1小时前'
        },
        {
            'icon': '🛰️',
            'title': '目标配置更新',
            'description': '添加3个高速机动目标',
            'time': '2小时前'
        },
        {
            'icon': '📊',
            'title': '性能报告生成',
            'description': '生成详细性能评估报告',
            'time': '3小时前'
        }
    ]
    
    return activities

def show_system_health():
    """显示系统健康状态"""
    st.markdown("### 💊 系统健康状态")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CPU使用率
        import psutil
        cpu_percent = psutil.cpu_percent()
        create_gauge_chart(
            cpu_percent,
            label="CPU使用率",
            color="#1a73e8"
        )
    
    with col2:
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        create_gauge_chart(
            memory_percent,
            label="内存使用率",
            color="#00e676"
        )
    
    with col3:
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        create_gauge_chart(
            disk_percent,
            label="磁盘使用率",
            color="#ff9800"
        )
    
    st.markdown("---")
    
    # 系统资源趋势
    st.markdown("#### 📈 资源使用趋势")
    
    # 生成模拟数据
    time_points = 24
    time_labels = [f"{i}:00" for i in range(time_points)]
    
    cpu_trend = 50 + 20 * np.sin(np.linspace(0, 2*np.pi, time_points)) + np.random.normal(0, 5, time_points)
    memory_trend = 60 + 10 * np.cos(np.linspace(0, 2*np.pi, time_points)) + np.random.normal(0, 3, time_points)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_labels,
        y=cpu_trend,
        mode='lines+markers',
        name='CPU',
        line=dict(color='#1a73e8', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=time_labels,
        y=memory_trend,
        mode='lines+markers',
        name='内存',
        line=dict(color='#00e676', width=2)
    ))
    
    fig.update_layout(
        height=300,
        xaxis_title="时间",
        yaxis_title="使用率 (%)",
        yaxis_range=[0, 100],
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 系统告警
    st.markdown("#### ⚠️ 系统告警")
    
    alerts = get_system_alerts()
    
    if alerts:
        for alert in alerts:
            alert_color = {
                'high': '#f44336',
                'medium': '#ff9800',
                'low': '#ffc107'
            }.get(alert['level'], '#888')
            
            st.markdown(
                f"""
                <div style="padding: 0.75rem; margin: 0.5rem 0; background: rgba(255,255,255,0.05); border-radius: 4px; border-left: 4px solid {alert_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{alert['title']}</strong><br>
                            <small>{alert['description']}</small>
                        </div>
                        <span style="color: {alert_color}; font-weight: bold;">{alert['level'].upper()}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("无系统告警")

def get_system_alerts():
    """获取系统告警"""
    alerts = []
    
    # 检查系统状态
    import psutil
    memory = psutil.virtual_memory()
    
    if memory.percent > 90:
        alerts.append({
            'title': '内存使用过高',
            'description': f'内存使用率已达到 {memory.percent:.1f}%',
            'level': 'high'
        })
    elif memory.percent > 80:
        alerts.append({
            'title': '内存使用较高',
            'description': f'内存使用率已达到 {memory.percent:.1f}%',
            'level': 'medium'
        })
    
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        alerts.append({
            'title': '磁盘空间不足',
            'description': f'磁盘使用率已达到 {disk.percent:.1f}%',
            'level': 'high'
        })
    
    # 检查仿真数据
    if not st.session_state.get('radar_configs'):
        alerts.append({
            'title': '未配置雷达',
            'description': '请至少配置一个雷达系统',
            'level': 'medium'
        })
    
    if not st.session_state.get('target_configs'):
        alerts.append({
            'title': '未配置目标',
            'description': '请至少配置一个目标',
            'level': 'medium'
        })
    
    return alerts

def show_quick_actions():
    """显示快速操作"""
    st.markdown("### ⚡ 快速操作")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 开始新仿真", use_container_width=True, type="primary"):
            st.switch_page("pages/6_🚀_仿真运行.py")
    
    with col2:
        if st.button("🎯 AI想定生成", use_container_width=True):
            st.switch_page("pages/2_🎯_想定生成.py")
    
    with col3:
        if st.button("📡 雷达配置", use_container_width=True):
            st.switch_page("pages/3_📡_雷达配置.py")
    
    with col4:
        if st.button("🛰️ 目标配置", use_container_width=True):
            st.switch_page("pages/4_🛰️_目标配置.py")
    
    st.markdown("---")
    
    # 快速工具
    st.markdown("### 🛠️ 快速工具")
    
    col_tool1, col_tool2, col_tool3, col_tool4 = st.columns(4)
    
    with col_tool1:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()
    
    with col_tool2:
        if st.button("💾 保存配置", use_container_width=True):
            save_all_configurations()
    
    with col_tool3:
        if st.button("📥 导入配置", use_container_width=True):
            st.info("导入功能开发中")
    
    with col_tool4:
        if st.button("📤 导出数据", use_container_width=True):
            export_all_data()

def save_all_configurations():
    """保存所有配置"""
    import json
    from pathlib import Path
    
    config_data = {
        "radar_configs": st.session_state.get('radar_configs', []),
        "target_configs": st.session_state.get('target_configs', []),
        "simulation_config": st.session_state.get('simulation_config', {}),
        "user_settings": st.session_state.get('user_settings', {}),
        "save_time": datetime.now().isoformat()
    }
    
    config_dir = Path("data/configs")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    st.success(f"所有配置已保存: {config_file.name}")

def export_all_data():
    """导出所有数据"""
    export_data = {
        "radar_configs": st.session_state.get('radar_configs', []),
        "target_configs": st.session_state.get('target_configs', []),
        "simulation_config": st.session_state.get('simulation_config', {}),
        "simulation_results": st.session_state.get('simulation_results', {}),
        "export_time": datetime.now().isoformat()
    }
    
    st.download_button(
        label="📥 下载所有数据",
        data=json.dumps(export_data, indent=2, ensure_ascii=False),
        file_name=f"export_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

if __name__ == "__main__":
    main()