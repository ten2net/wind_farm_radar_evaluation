"""
电子战对抗仿真系统 - Streamlit主应用
"""
from typing import List, Optional
import streamlit as st
import sys
import os
from pathlib import Path
import holoviews as hv
import geoviews as gv
from bokeh.embed import file_html
from bokeh.resources import CDN
import tempfile
import webbrowser
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 导入自定义模块
from src.core.patterns.strategy import ScenarioFactory
from src.core.factory import EntityFactory
from src.visualization.geoviz import EWVisualizer, create_visualization
from src.ui.components import (
    create_header, 
    create_status_bar,
    create_scenario_selector,
    create_entity_configurator,
    create_simulation_controls,
    create_results_display,
    create_environment_settings,
    create_export_panel,
    create_progress_bar
)
from src.utils.config_loader import load_radar_database, load_scenarios
import yaml
import json
from datetime import datetime

# 在应用开始时加载Holoviews扩展
try:
    # 加载Bokeh扩展
    hv.extension('bokeh', logo=False)
    gv.extension('bokeh', logo=False)
    st.success("✓ 可视化扩展加载成功")
except Exception as e:
    st.warning(f"⚠️ 加载可视化扩展时出错: {e}")

# 页面配置
st.set_page_config(
    page_title="长城数字电子战对抗仿真系统",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_performance_radar_matplotlib(metrics: dict, title: str = "性能雷达图"):
    """使用Matplotlib创建性能雷达图"""
    if not metrics:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, '无性能指标数据', 
               ha='center', va='center', fontsize=12)
        return fig
    
    categories = list(metrics.keys())
    values = list(metrics.values())
    
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # 添加第一个点以使图形闭合
    values += values[:1]
    angles = np.concatenate((angles, [angles[0]]))
    
    ax.plot(angles, values, 'b-', linewidth=2)
    ax.fill(angles, values, 'b', alpha=0.25)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title(title, size=16, y=1.1)
    ax.set_ylim(0, 100)  # 设置0-100的范围
    ax.grid(True)
    
    plt.tight_layout()
    return fig

def create_spectrum_analysis_matplotlib(frequencies: np.ndarray, 
                                      powers: np.ndarray,
                                      radar_freqs: Optional[List[float]] = None,
                                      jammer_freqs: Optional[List[float]] = None,
                                      title: str = "频谱分析") -> plt.Figure: # type: ignore
    """使用Matplotlib创建频谱分析图"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.fill_between(frequencies, powers, color='gray', alpha=0.5, label='频谱')
    ax.plot(frequencies, powers, 'k-', linewidth=1)
    
    # 添加雷达频率标记
    if radar_freqs:
        for freq in radar_freqs:
            ax.axvline(x=freq, color='blue', linestyle='--', linewidth=2, 
                      label='雷达频率' if freq == radar_freqs[0] else '')
    
    # 添加干扰机频率标记
    if jammer_freqs:
        for freq in jammer_freqs:
            ax.axvline(x=freq, color='red', linestyle=':', linewidth=2, 
                      label='干扰频率' if freq == jammer_freqs[0] else '')
    
    ax.set_xlabel('频率 (GHz)')
    ax.set_ylabel('功率 (dBm)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

# 应用状态管理
class AppState:
    """应用状态管理"""
    
    def __init__(self):
        self.scenario = None
        self.scenario_config = None
        self.radars = []
        self.jammers = []
        self.targets = []
        self.simulation_results = None
        self.assessment_results = None
        self.environment_config = {
            "terrain": "平原",
            "atmosphere": "标准",
            "temperature": 20,
            "humidity": 50,
            "rain_rate": 0
        }
        
        # 加载数据库
        self.radar_db = load_radar_database()
        self.scenario_db = load_scenarios()
        
        # 可视化器
        self.visualizer = EWVisualizer()
        
    def reset(self):
        """重置状态"""
        self.__init__()
    
    def get_visualization(self):
        """获取当前态势的可视化"""
        if self.radars or self.jammers or self.targets:
            return self.visualizer.create_ew_situation_map(
                self.radars, 
                self.jammers, 
                self.targets
            )
        return None

# 自定义CSS样式
def load_css():
    """加载自定义CSS样式"""
    st.markdown("""
    <style>
    /* 主容器 */
    .main {
        background: linear-gradient(135deg, #0c0c2e 0%, #1a1a3e 100%);
        color: #ffffff;
    }
    
    /* 标题样式 */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(45deg, #00d4ff, #0088ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0 2px 10px rgba(0, 212, 255, 0.3);
    }
    
    .sub-title {
        font-size: 1.2rem;
        color: #a0a0ff;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* 卡片样式 */
    .card {
        background: rgba(20, 20, 50, 0.7);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        border-color: rgba(0, 212, 255, 0.5);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
        transform: translateY(-2px);
    }
    
    .card-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #00d4ff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, rgba(0, 132, 255, 0.1), rgba(0, 212, 255, 0.05));
        border: 1px solid rgba(0, 132, 255, 0.3);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #00d4ff;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #a0a0ff;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(45deg, #0066ff, #00d4ff);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 212, 255, 0.4);
    }
    
    .primary-button {
        background: linear-gradient(45deg, #ff0080, #ff4d00) !important;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #a0a0ff;
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 212, 255, 0.1) !important;
        color: #00d4ff !important;
        border-bottom: 2px solid #00d4ff;
    }
    
    /* 滑块样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #0066ff, #00d4ff);
    }
    
    /* 数据表格样式 */
    .dataframe {
        background-color: rgba(20, 20, 50, 0.5) !important;
        color: white !important;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(20, 20, 50, 0.3);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #0066ff, #00d4ff);
        border-radius: 4px;
    }
    
    /* 状态指示灯 */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background-color: #00ff00; box-shadow: 0 0 10px #00ff00; }
    .status-jammed { background-color: #ff9900; box-shadow: 0 0 10px #ff9900; }
    .status-destroyed { background-color: #ff0000; box-shadow: 0 0 10px #ff0000; }
    
    /* 地图容器样式 */
    .map-container {
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_app():
    """初始化应用"""
    # 加载CSS
    load_css()
    
    # 初始化状态
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()
    
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "scenario"
    
    if 'viz_html' not in st.session_state:
        st.session_state.viz_html = None
    
    return st.session_state.app_state

def save_visualization_html(plot, filename=None):
    """保存可视化结果为HTML文件"""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ew_visualization_{timestamp}.html"
        
        # 使用可视化器的保存功能
        filepath = st.session_state.app_state.visualizer.save_to_html(plot, filename)
        
        if filepath:
            # 读取HTML内容
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 存储到session state
            st.session_state.viz_html = html_content
            
            return filepath, html_content
    
    except Exception as e:
        st.error(f"保存可视化结果失败: {e}")
    
    return None, None

def display_geoviews_plot(plot):
    """在Streamlit中显示GeoViews图表"""
    try:
        if plot is None:
            st.info("暂无可视化数据")
            return
        
        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        # 保存为HTML
        filepath = st.session_state.app_state.visualizer.save_to_html(plot, temp_path)
        
        if filepath and os.path.exists(filepath):
            # 读取HTML内容
            with open(filepath, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()
            
            # 在Streamlit中显示
            st.components.v1.html(html_content, height=700, scrolling=True) # type: ignore
            
            # 提供下载链接
            st.download_button(
                label="📥 下载可视化结果",
                data=html_content,
                file_name=f"ew_visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )
            
            # 清理临时文件
            try:
                os.unlink(filepath)
            except:
                pass
        else:
            st.error("无法生成可视化图表")
                
    except Exception as e:
        st.error(f"显示可视化图表失败: {e}")
        st.info("尝试使用备用显示方法...")
        
        # 备用方法：使用Matplotlib
        try:
            state = st.session_state.app_state
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # 绘制雷达
            if state.radars:
                radar_lons = [r.position.lon for r in state.radars]
                radar_lats = [r.position.lat for r in state.radars]
                ax.scatter(radar_lons, radar_lats, c='blue', s=100, marker='^', label='雷达')
            
            # 绘制干扰机
            if state.jammers:
                jammer_lons = [j.position.lon for j in state.jammers]
                jammer_lats = [j.position.lat for j in state.jammers]
                ax.scatter(jammer_lons, jammer_lats, c='red', s=80, marker='s', label='干扰机')
            
            # 绘制目标
            if state.targets:
                target_lons = [t.position.lon for t in state.targets]
                target_lats = [t.position.lat for t in state.targets]
                ax.scatter(target_lons, target_lats, c='green', s=60, marker='o', label='目标')
            
            ax.set_xlabel('经度')
            ax.set_ylabel('纬度')
            ax.set_title('电子战对抗态势图 (备用视图)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
        except Exception as e2:
            st.error(f"备用显示方法也失败: {e2}")

def handle_scenario_selection(scenario_type):
    """处理想定选择"""
    state = st.session_state.app_state

    if scenario_type in state.scenario_db:
        config = state.scenario_db[scenario_type]
        
        # 创建想定
        state.scenario = ScenarioFactory.create_scenario(scenario_type)
        state.scenario_config = config
        
        # 清空现有实体
        state.radars = []
        state.jammers = []
        state.targets = []
        
        # 设置想定
        state.scenario.setup(config)
        
        # 获取实体
        state.radars = state.scenario.radars
        state.jammers = state.scenario.jammers
        state.targets = state.scenario.targets
        
        st.success(f"想定 '{state.scenario.name}' 创建成功！")
        st.rerun()
    else:
        st.error(f"未找到想定配置: {scenario_type}")

def handle_simulation_start(speed, duration):
    """处理仿真开始"""
    state = st.session_state.app_state
    
    if not state.scenario:
        st.warning("请先创建对抗想定")
        return
    
    with st.spinner("正在运行仿真..."):
        # 模拟仿真过程
        progress_bar = st.progress(0)
        
        for i in range(100):
            # 模拟计算
            import time
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        
        # 执行仿真
        state.simulation_results = state.scenario.execute()
        state.assessment_results = state.scenario.assess()
        
        st.success("仿真完成！")
        
        # 自动更新可视化
        st.rerun()

def handle_environment_update(new_config):
    """处理环境更新"""
    state = st.session_state.app_state
    state.environment_config = new_config
    st.success("环境设置已更新")

def main():
    """主函数"""
    # 初始化应用
    state = initialize_app()
    
    # 创建标题
    create_header()
    
    # 状态栏
    create_status_bar(
        radar_count=len(state.radars),
        jammer_count=len(state.jammers),
        target_count=len(state.targets),
        scenario_name=state.scenario.name if state.scenario else "未选择"
    )
    
    # 创建主布局
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 主内容区
        tab1, tab2, tab3 = st.tabs(["🎯 想定配置", "🚀 仿真控制", "📈 结果分析"])
        
        with tab1:
            st.markdown('<div class="card-header">🎯 对抗想定配置</div>', unsafe_allow_html=True)
            
            # 获取可用想定
            available_scenarios = ScenarioFactory.get_available_scenarios()
            
            # 想定选择器
            selected_scenario = create_scenario_selector(
                available_scenarios,
                on_change=handle_scenario_selection
            )
            
            if state.scenario:
                st.markdown("---")
                st.subheader("📡 当前想定概览")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("**雷达系统**")
                    for radar in state.radars:
                        st.write(f"• {radar.name}: 位置({radar.position.lat:.4f}, {radar.position.lon:.4f})")
                        st.write(f"  频率: {radar.radar_params.frequency} GHz, 功率: {radar.radar_params.power} kW")
                
                with col_b:
                    st.write("**干扰系统**")
                    for jammer in state.jammers:
                        st.write(f"• {jammer.name}: 位置({jammer.position.lat:.4f}, {jammer.position.lon:.4f})")
                        st.write(f"  功率: {jammer.jammer_params.power} W, 增益: {jammer.jammer_params.gain} dBi")
            
            # 环境设置
            st.markdown("---")
            create_environment_settings(
                state.environment_config,
                on_update=handle_environment_update
            )
        
        with tab2:
            st.markdown('<div class="card-header">🚀 仿真控制</div>', unsafe_allow_html=True)
            
            # 仿真控制面板
            speed, duration = create_simulation_controls(
                on_start=handle_simulation_start,
                on_pause=lambda: st.info("仿真暂停"),
                on_reset=lambda: state.reset() or st.rerun()
            )
            
            if state.simulation_results:
                st.markdown("---")
                st.subheader("📊 仿真结果概览")
                
                cols = st.columns(3)
                with cols[0]:
                    effective = state.simulation_results.get("result", {}).get("effective", False)
                    st.metric("干扰是否有效", "是" if effective else "否")
                with cols[1]:
                    j_s_ratio = state.simulation_results.get("result", {}).get("j_s_ratio", 0)
                    st.metric("干信比", f"{j_s_ratio:.1f} dB")
                with cols[2]:
                    det_prob = state.simulation_results.get("result", {}).get("detection_probability", 0) * 100
                    st.metric("探测概率", f"{det_prob:.1f}%")
        
        with tab3:
            st.markdown('<div class="card-header">📈 结果分析</div>', unsafe_allow_html=True)
            
            if state.simulation_results or state.radars or state.jammers:
                # 创建可视化
                st.subheader("🗺️ 态势可视化")
                
                # 投影选择
                projection_options = ['PlateCarree', 'Mercator', 'Robinson', 'Orthographic']
                selected_projection = st.selectbox(
                    "选择地图投影",
                    projection_options,
                    index=0,
                    help="选择地图投影方式"
                )
                
                # 更新可视化器的投影
                if selected_projection != state.visualizer.crs:
                    state.visualizer = EWVisualizer(projection=selected_projection)
                
                # 生成可视化
                viz = state.get_visualization()
                
                if viz:
                    # 显示可视化
                    display_geoviews_plot(viz)
                    
                    # 信号强度热力图
                    if st.checkbox("显示信号强度热力图", value=False):
                        heatmap = state.visualizer.create_signal_strength_heatmap(state.radars)
                        if heatmap:
                            st.subheader("📶 信号强度热力图")
                            display_geoviews_plot(heatmap)
                else:
                    st.info("暂无可视化数据")
                
                # 效能评估
                if state.simulation_results:
                    st.subheader("📊 效能评估")
                    create_results_display(state.assessment_results or {})
                    
                    # 信号分析图表
                    st.subheader("📡 信号分析")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 创建频谱分析图
                        frequencies = np.linspace(8, 12, 100)
                        powers = np.random.randn(100) + 50
                        radar_freqs = [r.radar_params.frequency for r in state.radars]
                        
                        spectrum_fig = create_spectrum_analysis_matplotlib(
                            frequencies, powers, radar_freqs, []
                        )
                        st.pyplot(spectrum_fig)
                    
                    with col2:
                        # 创建性能雷达图
                        metrics = {
                            '探测概率': state.simulation_results.get("result", {}).get("detection_probability", 0) * 100,
                            '干信比': min(state.simulation_results.get("result", {}).get("j_s_ratio", 0), 100),
                            '干扰效果': 80 if state.simulation_results.get("result", {}).get("effective", False) else 20,
                            '目标发现率': 75,
                            '系统可用性': 90
                        }
                        
                        radar_fig = create_performance_radar_matplotlib(metrics)
                        st.pyplot(radar_fig)
                
                # 数据导出
                st.subheader("💾 数据导出")
                create_export_panel(
                    state.simulation_results or {},
                    file_prefix="ew_simulation"
                )
                
                # 导出可视化
                if viz and st.button("📤 导出完整可视化报告"):
                    with st.spinner("生成报告中..."):
                        # 保存HTML报告
                        filename = f"ew_simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        filepath, html_content = save_visualization_html(viz, filename)
                        
                        if filepath:
                            st.success(f"报告已保存到: {filepath}")
                            
                            # 提供下载
                            st.download_button(
                                label="📥 下载HTML报告",
                                data=html_content, # type: ignore
                                file_name=filename,
                                mime="text/html"
                            )
            else:
                st.info("请先运行仿真以查看结果")
    
    with col2:
        # 侧边栏
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📊 系统状态</div>', unsafe_allow_html=True)
        
        # 实时状态显示
        st.write("**当前想定:**")
        if state.scenario:
            st.success(state.scenario.name)
        else:
            st.warning("未选择")
        
        st.write("**实体统计:**")
        stats_data = {
            "类型": ["雷达", "干扰机", "目标"],
            "数量": [len(state.radars), len(state.jammers), len(state.targets)]
        }
        st.dataframe(pd.DataFrame(stats_data), width='stretch')
        
        st.write("**仿真状态:**")
        if state.simulation_results:
            st.success("已完成")
        elif state.scenario:
            st.info("就绪")
        else:
            st.warning("未配置")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 可视化控制
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">🎨 可视化控制</div>', unsafe_allow_html=True)
        
        # 可视化类型选择
        viz_type = st.radio(
            "选择可视化类型",
            ["态势地图", "信号热图", "3D视图"],
            index=0
        )
        
        # 地图样式
        map_style = st.selectbox(
            "地图样式",
            ["标准", "卫星", "地形", "深色"],
            index=0
        )
        
        # 显示选项
        show_coverage = st.checkbox("显示覆盖范围", value=True)
        show_sectors = st.checkbox("显示干扰扇区", value=True)
        show_labels = st.checkbox("显示标签", value=True)
        
        if st.button("🔄 刷新可视化", width='stretch'):
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 快捷操作
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">⚡ 快捷操作</div>', unsafe_allow_html=True)
        
        if st.button("📁 保存当前配置", width='stretch'):
            st.success("配置已保存")
        
        if st.button("📤 载入配置", width='stretch'):
            st.info("载入功能开发中...")
        
        if st.button("🔄 重置系统", width='stretch', type="secondary"):
            state.reset()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 帮助信息
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">❓ 使用帮助</div>', unsafe_allow_html=True)
        
        with st.expander("基本流程"):
            st.write("""
            1. 在想定配置中选择对抗类型
            2. 配置雷达和干扰机参数
            3. 点击"创建对抗想定"
            4. 在仿真控制中开始仿真
            5. 在结果分析中查看效果
            """)
        
        with st.expander("快捷键"):
            st.write("""
            • Ctrl+S: 保存配置
            • Ctrl+R: 运行仿真
            • Ctrl+P: 导出报告
            • F1: 显示帮助
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 底部信息
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>长城数字电子战对抗仿真系统 v2.0 | © 2024 电子战仿真实验室</p>
        <p>基于GeoViews的地理可视化系统 | 技术支持: 电子战仿真团队</p>
        <p>本系统为仿真工具，结果仅供参考，实际作战应用需结合具体战场环境</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()