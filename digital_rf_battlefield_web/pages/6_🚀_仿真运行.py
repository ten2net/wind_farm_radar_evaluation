"""
仿真运行页面 - 控制仿真运行和监控界面
"""

import streamlit as st
import time
import threading
import queue
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.style_utils import create_data_card, create_gauge_chart, get_military_style
from utils.simulation_api import SimulationEngine

def main():
    """仿真运行页面主函数"""
    st.title("🚀 仿真运行控制")
    st.markdown("控制仿真运行、监控状态和查看实时数据")
    
    # 初始化仿真引擎
    if 'simulation_engine' not in st.session_state:
        st.session_state.simulation_engine = SimulationEngine()
    
    if 'simulation_status' not in st.session_state:
        st.session_state.simulation_status = "stopped"  # stopped, running, paused
    
    if 'simulation_data' not in st.session_state:
        st.session_state.simulation_data = {
            "current_time": 0.0,
            "progress": 0.0,
            "radar_data": [],
            "target_data": [],
            "detections": [],
            "tracks": [],
            "performance_metrics": {}
        }
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 运行控制", "📊 实时监控", "📈 性能面板", "📋 运行日志"])
    
    with tab1:
        show_simulation_control()
    
    with tab2:
        show_realtime_monitoring()
    
    with tab3:
        show_performance_panel()
    
    with tab4:
        show_run_logs()

def show_simulation_control():
    """显示仿真控制界面"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎮 仿真控制")
        
        # 仿真状态显示
        status = st.session_state.simulation_status
        status_color = {
            "stopped": "gray",
            "running": "green",
            "paused": "orange"
        }.get(status, "gray")
        print(st.session_state)
        print(">>>>>>>>>>>>>>>>",st.session_state.simulation_data)
        st.markdown(
            f"""
            <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid {status_color}; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0;">仿真状态: <span style="color: {status_color};">{status}</span></h3>
                        
                    </div>
                    <div style="font-size: 2rem;">
                        {"⏸️" if status == "paused" else "▶️" if status == "running" else "⏹️"}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # st.markdown(
        #     f"""
        #     <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid {status_color}; margin-bottom: 1rem;">
        #         <div style="display: flex; justify-content: space-between; align-items: center;">
        #             <div>
        #                 <h3 style="margin: 0;">仿真状态: <span style="color: {status_color};">{status}</span></h3>
        #                 <p style="margin: 0.5rem 0 0 0; color: #888;">当前时间: {st.session_state.simulation_data['current_time']:.1f}s</p>
        #             </div>
        #             <div style="font-size: 2rem;">
        #                 {"⏸️" if status == "paused" else "▶️" if status == "running" else "⏹️"}
        #             </div>
        #         </div>
        #     </div>
        #     """,
        #     unsafe_allow_html=True
        # )
        
        # 进度条
        progress = st.session_state.simulation_data.get('progress', 0.0)
        st.progress(progress, text=f"进度: {progress:.1%}")
        
        # 仿真信息
        if 'simulation_config' in st.session_state:
            config = st.session_state.simulation_config.get('time_settings', {})
            duration = config.get('duration_seconds', 300)
            time_step = config.get('time_step', 0.1)
            real_time_factor = config.get('real_time_factor', 1.0)
            
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.metric("总时长", f"{duration}s")
            
            with col_info2:
                st.metric("时间步长", f"{time_step}s")
            
            with col_info3:
                st.metric("实时因子", f"{real_time_factor}x")
        
        # 控制按钮
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            if st.button("▶️ 开始仿真", type="primary", use_container_width=True, 
                        disabled=status == "running"):
                start_simulation()
        
        with col_btn2:
            if st.button("⏸️ 暂停仿真", use_container_width=True,
                        disabled=status != "running"):
                pause_simulation()
        
        with col_btn3:
            if st.button("⏯️ 继续仿真", use_container_width=True,
                        disabled=status != "paused"):
                resume_simulation()
        
        with col_btn4:
            if st.button("⏹️ 停止仿真", use_container_width=True,
                        disabled=status == "stopped"):
                stop_simulation()
    
    with col2:
        st.subheader("⚙️ 运行设置")
        
        # 运行模式
        run_mode = st.selectbox(
            "运行模式",
            ["标准模式", "快速模式", "调试模式", "静默模式"]
        )
        
        # 实时更新频率
        update_rate = st.slider(
            "界面更新频率 (Hz)",
            1, 30, 10, 1
        )
        
        # 数据记录选项
        st.markdown("**数据记录**")
        record_data = st.checkbox("记录仿真数据", value=True)
        
        if record_data:
            col_rec1, col_rec2 = st.columns(2)
            with col_rec1:
                record_interval = st.number_input("记录间隔", 0.1, 10.0, 1.0, 0.1)
            with col_rec2:
                record_format = st.selectbox("格式", ["JSON", "CSV", "HDF5"])
        
        # 预警设置
        st.markdown("**预警设置**")
        enable_alerts = st.checkbox("启用实时预警", value=True)
        
        if enable_alerts:
            alert_level = st.slider("预警敏感度", 1, 10, 5, 1)
        
        # 保存设置
        if st.button("💾 保存运行设置", use_container_width=True):
            save_run_settings({
                "run_mode": run_mode,
                "update_rate": update_rate,
                "record_data": record_data,
                "record_interval": record_interval if record_data else None,
                "record_format": record_format if record_data else None,
                "enable_alerts": enable_alerts,
                "alert_level": alert_level if enable_alerts else None
            })

def start_simulation():
    """开始仿真"""
    # 检查必要配置
    if not st.session_state.get('radar_configs'):
        st.error("请先配置雷达系统")
        return
    
    if not st.session_state.get('target_configs'):
        st.error("请先配置目标")
        return
    
    if not st.session_state.get('simulation_config'):
        st.error("请先配置仿真参数")
        return
    
    # 启动仿真引擎
    try:
        engine = st.session_state.simulation_engine
        
        # 准备配置
        config = {
            "radars": st.session_state.radar_configs,
            "targets": st.session_state.target_configs,
            "simulation": st.session_state.simulation_config
        }
        
        # 初始化引擎
        engine.initialize(config)
        
        # 启动仿真线程
        st.session_state.simulation_status = "running"
        st.session_state.simulation_thread = threading.Thread(
            target=run_simulation_thread,
            args=(engine,),
            daemon=True
        )
        st.session_state.simulation_thread.start()
        
        st.success("仿真已启动")
        st.rerun()
        
    except Exception as e:
        st.error(f"启动仿真失败: {e}")

def pause_simulation():
    """暂停仿真"""
    st.session_state.simulation_status = "paused"
    st.success("仿真已暂停")

def resume_simulation():
    """继续仿真"""
    st.session_state.simulation_status = "running"
    st.success("仿真已继续")

def stop_simulation():
    """停止仿真"""
    st.session_state.simulation_status = "stopped"
    
    # 停止仿真引擎
    if 'simulation_engine' in st.session_state:
        st.session_state.simulation_engine.stop()
    
    st.success("仿真已停止")
    st.rerun()

def run_simulation_thread(engine):
    """运行仿真线程"""
    try:
        while st.session_state.simulation_status == "running":
            # 执行一步仿真
            data = engine.step()
            
            # 更新会话状态
            st.session_state.simulation_data.update(data)
            
            # 计算进度
            if 'simulation_config' in st.session_state:
                duration = st.session_state.simulation_config.get('time_settings', {}).get('duration_seconds', 300)
                st.session_state.simulation_data['progress'] = data['current_time'] / duration
            
            # 短暂休眠
            time.sleep(0.1)  # 控制更新频率
            
    except Exception as e:
        st.error(f"仿真运行错误: {e}")
        st.session_state.simulation_status = "stopped"

def save_run_settings(settings):
    """保存运行设置"""
    if 'run_settings' not in st.session_state:
        st.session_state.run_settings = {}
    
    st.session_state.run_settings.update(settings)
    st.success("运行设置已保存")

def show_realtime_monitoring():
    """显示实时监控界面"""
    st.subheader("📊 实时监控面板")
    
    # 创建监控仪表板
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 当前时间
        current_time = st.session_state.simulation_data.get('current_time', 0.0)
        create_data_card(
            "仿真时间",
            f"{current_time:.1f}",
            "秒",
            icon="⏱️"
        )
    
    with col2:
        # 雷达数量
        radar_count = len(st.session_state.simulation_data.get('radar_data', []))
        create_data_card(
            "在线雷达",
            radar_count,
            "部",
            icon="📡"
        )
    
    with col3:
        # 目标数量
        target_count = len(st.session_state.simulation_data.get('target_data', []))
        create_data_card(
            "活动目标",
            target_count,
            "个",
            icon="🛰️"
        )
    
    with col4:
        # 跟踪数量
        track_count = len(st.session_state.simulation_data.get('tracks', []))
        create_data_card(
            "跟踪航迹",
            track_count,
            "条",
            icon="🎯"
        )
    
    st.markdown("---")
    
    # 实时图表
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 📶 检测概率趋势")
        plot_detection_probability()
    
    with col_chart2:
        st.markdown("#### 📡 雷达负载")
        plot_radar_load()
    
    st.markdown("---")
    
    # 实时数据表格
    st.markdown("#### 📋 实时数据")
    
    col_data1, col_data2 = st.columns(2)
    
    with col_data1:
        show_radar_status_table()
    
    with col_data2:
        show_target_status_table()

def plot_detection_probability():
    """绘制检测概率趋势"""
    # 模拟数据
    times = np.linspace(0, 10, 100)
    probs = 0.8 + 0.1 * np.sin(times) + np.random.normal(0, 0.05, 100)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=probs,
        mode='lines',
        name='检测概率',
        line=dict(color='#1a73e8', width=2)
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="时间 (s)",
        yaxis_title="概率",
        yaxis=dict(range=[0, 1])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_radar_load():
    """绘制雷达负载"""
    # 模拟数据
    radars = ['雷达1', '雷达2', '雷达3', '雷达4']
    load = [0.3, 0.6, 0.4, 0.8]
    
    fig = go.Figure(data=[
        go.Bar(
            x=radars,
            y=load,
            marker_color=['#1a73e8', '#00e676', '#ff9800', '#f44336']
        )
    ])
    
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis_title="负载率",
        yaxis=dict(range=[0, 1])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_radar_status_table():
    """显示雷达状态表格"""
    radar_data = st.session_state.simulation_data.get('radar_data', [])
    
    if not radar_data:
        st.info("暂无雷达数据")
        return
    
    # 提取显示数据
    display_data = []
    for radar in radar_data[:5]:  # 只显示前5个
        display_data.append({
            "名称": radar.get('name', '未知'),
            "状态": radar.get('status', '未知'),
            "负载": f"{radar.get('load', 0):.0%}",
            "探测数": radar.get('detections', 0)
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def show_target_status_table():
    """显示目标状态表格"""
    target_data = st.session_state.simulation_data.get('target_data', [])
    
    if not target_data:
        st.info("暂无目标数据")
        return
    
    # 提取显示数据
    display_data = []
    for target in target_data[:5]:  # 只显示前5个
        display_data.append({
            "名称": target.get('name', '未知'),
            "类型": target.get('type', '未知'),
            "速度": f"{target.get('speed_kts', 0)}节",
            "高度": f"{target.get('altitude_m', 0)}m"
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def show_performance_panel():
    """显示性能面板"""
    st.subheader("📈 仿真性能分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ 实时性能")
        
        # 性能指标
        metrics = st.session_state.simulation_data.get('performance_metrics', {})
        
        col_metric1, col_metric2 = st.columns(2)
        
        with col_metric1:
            fps = metrics.get('fps', 0)
            create_gauge_chart(
                min(fps, 60),
                max_value=60,
                label="帧率 (FPS)",
                color="#1a73e8"
            )
            
            cpu_usage = metrics.get('cpu_usage', 0)
            create_gauge_chart(
                cpu_usage * 100,
                label="CPU使用率",
                color="#00e676"
            )
        
        with col_metric2:
            memory_usage = metrics.get('memory_usage', 0)
            create_gauge_chart(
                memory_usage * 100,
                label="内存使用率",
                color="#ff9800"
            )
            
            update_latency = metrics.get('update_latency', 0)
            create_gauge_chart(
                min(update_latency * 1000, 100),
                max_value=100,
                label="更新延迟 (ms)",
                color="#f44336"
            )
    
    with col2:
        st.markdown("### 📊 性能趋势")
        
        # 生成性能趋势图
        fig = go.Figure()
        
        # 模拟数据
        times = np.linspace(0, 10, 50)
        cpu_data = 0.5 + 0.2 * np.sin(times) + np.random.normal(0, 0.05, 50)
        memory_data = 0.6 + 0.1 * np.cos(times) + np.random.normal(0, 0.03, 50)
        
        fig.add_trace(go.Scatter(
            x=times,
            y=cpu_data * 100,
            mode='lines',
            name='CPU使用率',
            line=dict(color='#00e676', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=times,
            y=memory_data * 100,
            mode='lines',
            name='内存使用率',
            line=dict(color='#ff9800', width=2)
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="时间 (s)",
            yaxis_title="使用率 (%)",
            yaxis=dict(range=[0, 100]),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 性能建议
    st.markdown("### 💡 性能建议")
    
    # 根据当前性能指标生成建议
    suggestions = generate_performance_suggestions()
    
    for suggestion in suggestions:
        st.info(suggestion)

def generate_performance_suggestions():
    """生成性能建议"""
    metrics = st.session_state.simulation_data.get('performance_metrics', {})
    suggestions = []
    
    if metrics.get('fps', 0) < 10:
        suggestions.append("帧率较低，考虑减少目标数量或降低仿真精度")
    
    if metrics.get('cpu_usage', 0) > 0.8:
        suggestions.append("CPU使用率较高，可尝试启用并行处理或减少仿真复杂度")
    
    if metrics.get('memory_usage', 0) > 0.8:
        suggestions.append("内存使用率较高，考虑减少数据记录间隔或目标数量")
    
    if metrics.get('update_latency', 0) > 0.1:
        suggestions.append("更新延迟较高，可降低界面更新频率")
    
    if not suggestions:
        suggestions.append("当前性能表现良好，建议保持当前配置")
    
    return suggestions

def show_run_logs():
    """显示运行日志"""
    st.subheader("📋 仿真运行日志")
    
    # 日志控制
    col_log1, col_log2, col_log3 = st.columns([1, 1, 2])
    
    with col_log1:
        log_level = st.selectbox(
            "日志级别",
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=1
        )
    
    with col_log2:
        if st.button("🔄 刷新日志", use_container_width=True):
            refresh_logs()
    
    with col_log3:
        if st.button("🗑️ 清除日志", use_container_width=True):
            clear_logs()
    
    st.markdown("---")
    
    # 日志显示区域
    log_container = st.container()
    
    with log_container:
        # 模拟日志数据
        log_data = [
            {"time": "12:00:00", "level": "INFO", "message": "仿真系统初始化完成"},
            {"time": "12:00:01", "level": "INFO", "message": "加载雷达配置: 3个雷达"},
            {"time": "12:00:02", "level": "INFO", "message": "加载目标配置: 5个目标"},
            {"time": "12:00:03", "level": "WARNING", "message": "目标#3 RCS参数缺失，使用默认值"},
            {"time": "12:00:05", "level": "INFO", "message": "仿真引擎启动成功"},
            {"time": "12:00:10", "level": "INFO", "message": "仿真运行中: 时间=10.0s, 进度=3.3%"},
            {"time": "12:00:20", "level": "INFO", "message": "检测到目标#1, SNR=15.2dB"},
            {"time": "12:00:25", "level": "ERROR", "message": "雷达#1通信超时，尝试重连"},
            {"time": "12:00:26", "level": "INFO", "message": "雷达#1重连成功"},
        ]
        
        # 过滤日志级别
        level_order = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        min_level = level_order.get(log_level, 1)
        
        for log in log_data:
            if level_order.get(log["level"], 1) >= min_level:
                level_color = {
                    "DEBUG": "#666",
                    "INFO": "#1a73e8",
                    "WARNING": "#ff9800",
                    "ERROR": "#f44336",
                    "CRITICAL": "#d32f2f"
                }.get(log["level"], "#666")
                
                st.markdown(
                    f"""
                    <div style="
                        padding: 0.5rem;
                        margin: 0.25rem 0;
                        background: rgba(255,255,255,0.05);
                        border-radius: 4px;
                        border-left: 3px solid {level_color};
                        font-family: monospace;
                    ">
                        <span style="color: #888;">[{log['time']}]</span>
                        <span style="color: {level_color}; font-weight: bold;"> {log['level']}</span>
                        <span style="color: #fff;">: {log['message']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

def refresh_logs():
    """刷新日志"""
    st.success("日志已刷新")

def clear_logs():
    """清除日志"""
    st.success("日志已清除")

if __name__ == "__main__":
    main()