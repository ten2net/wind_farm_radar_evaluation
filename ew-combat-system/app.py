"""
电子战对抗仿真系统 - Streamlit主应用
"""
import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 导入自定义模块
from src.core.patterns.strategy import ScenarioFactory
from src.core.factory import EntityFactory
from src.visualization.geoviz import EWVisualizer
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
import pandas as pd
import numpy as np

# 页面配置
st.set_page_config(
    page_title="长城数字电子战对抗仿真系统",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        
    def reset(self):
        """重置状态"""
        self.__init__()

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
    
    return st.session_state.app_state

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
                        st.write(f"• {radar.name}: {radar.position.lat:.4f}, {radar.position.lon:.4f}")
                
                with col_b:
                    st.write("**干扰系统**")
                    for jammer in state.jammers:
                        st.write(f"• {jammer.name}: {jammer.position.lat:.4f}, {jammer.position.lon:.4f}")
            
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
            
            if state.simulation_results:
                # 创建可视化
                st.subheader("🗺️ 态势可视化")
                
                if state.radars or state.jammers:
                    viz = EWVisualizer.create_coverage_map(
                        state.radars, state.jammers, state.targets
                    )
                    st.bokeh_chart(viz, width='stretch') # type: ignore
                
                # 结果显示
                st.subheader("📊 效能评估")
                create_results_display(state.assessment_results or {})
                
                # 数据导出
                st.subheader("💾 数据导出")
                create_export_panel(
                    state.simulation_results,
                    file_prefix="ew_simulation"
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
        <p>本系统为仿真工具，结果仅供参考，实际作战应用需结合具体战场环境</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
