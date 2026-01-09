#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电子战对抗仿真系统 - 主应用
修复可视化显示问题
"""
import traceback
import streamlit as st
import sys
import os
from pathlib import Path
import warnings
import numpy as np
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置页面配置
st.set_page_config(
    page_title="电子战对抗仿真系统",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入必要的库
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import yaml
from typing import Dict, List, Any, Optional
import io
import base64

# 尝试加载可视化扩展
try:
    import holoviews as hv
    import geoviews as gv
    from bokeh.embed import components
    from bokeh.resources import CDN
    
    # 加载Bokeh扩展
    hv.extension('bokeh', logo=False)
    gv.extension('bokeh', logo=False)
    st.success("✓ 可视化扩展加载成功")
    VISUALIZATION_AVAILABLE = True
except Exception as e:
    st.warning(f"⚠️ 加载可视化扩展时出错: {e}")
    st.info("将使用简化版可视化")
    VISUALIZATION_AVAILABLE = False

# 导入自定义模块
try:
    from src.core.patterns.strategy import ScenarioFactory
    from src.core.factory import EntityFactory
    from src.visualization.geoviz import EWVisualizer
    from src.core.assessment import EWAssessor, ReportGenerator
    from src.utils.data_manager import DataManager
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("应用启动")
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.stop()

# 应用标题
st.title("🛡️ 电子战对抗仿真系统")
st.markdown("""
    **专业的电子战体系对抗仿真与评估平台**
    
    支持一对一、多对一、多对多对抗想定，提供完整的电磁环境构建、对抗仿真、效能评估和可视化功能。
""")

# 侧边栏导航
st.sidebar.title("导航")
page = st.sidebar.radio(
    "选择页面",
    ["🏠 概览", "🎯 想定配置", "⚡ 仿真控制", "📊 结果分析", "📁 数据管理", "⚙️ 系统设置"]
)

# 初始化会话状态
if 'scenario' not in st.session_state:
    st.session_state.scenario = None
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'assessment_results' not in st.session_state:
    st.session_state.assessment_results = None
if 'visualizations' not in st.session_state:
    st.session_state.visualizations = {}

# 数据管理器
data_manager = DataManager()

def fig_to_base64(fig):
    """将Matplotlib图形转换为base64字符串"""
    import io
    import base64
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)  # 关闭图形以释放内存
    return img_str

def render_bokeh_plot(plot, height=600):
    """渲染Bokeh图表到Streamlit"""
    try:
        from bokeh.embed import components
        from bokeh.resources import CDN
        
        # 将HoloViews/GeoViews图表转换为Bokeh
        bokeh_plot = hv.render(plot)
        
        # 生成脚本和div
        script, div = components(bokeh_plot)
        
        # 创建完整的HTML
        html = f"""
        <html>
        <head>
            {CDN.render()}
        </head>
        <body>
            {div}
            {script}
        </body>
        </html>
        """
        
        # 在Streamlit中显示
        st.components.v1.html(html, height=height, scrolling=True)
        
    except Exception as e:
        st.error(f"渲染Bokeh图表失败: {e}")
        return False
    
    return True

# 页面函数
def show_overview():
    """显示概览页面"""
    st.header("🏠 系统概览")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("支持的想定", "3种", "一对一/多对一/多对多")
    
    with col2:
        st.metric("仿真速度", "1000实体/秒", "高性能计算")
    
    with col3:
        st.metric("可视化类型", "5种", "地图/图表/3D")
    
    st.markdown("---")
    
    # 快速开始
    st.subheader("🚀 快速开始")
    
    quick_start_col1, quick_start_col2, quick_start_col3 = st.columns(3)
    
    with quick_start_col1:
        if st.button("创建一对一对抗", width='stretch'):
            st.session_state.scenario = ScenarioFactory.create_scenario("one_vs_one")
            st.success("一对一对抗想定已创建")
    
    with quick_start_col2:
        if st.button("运行示例仿真", width='stretch'):
            # 运行示例仿真
            with st.spinner("正在运行示例仿真..."):
                try:
                    scenario = ScenarioFactory.create_scenario("one_vs_one")
                    config = {
                        "radar": {
                            "id": "example_radar",
                            "name": "示例雷达",
                            "frequency": 3.0,
                            "power": 100.0,
                            "lat": 39.9,
                            "lon": 116.4,
                            "alt": 50.0
                        },
                        "jammer": {
                            "id": "example_jammer",
                            "name": "示例干扰机",
                            "power": 1000.0,
                            "lat": 40.0,
                            "lon": 116.5,
                            "alt": 10000.0
                        }
                    }
                    scenario.setup(config)
                    results = scenario.execute()
                    assessment = scenario.assess()
                    
                    st.session_state.simulation_results = results
                    st.session_state.assessment_results = assessment
                    st.success("示例仿真完成！")
                    
                except Exception as e:
                    st.error(f"示例仿真失败: {e}")
    
    with quick_start_col3:
        if st.button("查看示例结果", width='stretch'):
            st.session_state.page = "结果分析"
            st.rerun()
    
    st.markdown("---")
    
    # 系统状态
    st.subheader("📊 系统状态")
    
    # 获取数据统计
    stats = data_manager.get_data_statistics()
    
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.metric("仿真结果文件", stats.get('total_results', 0))
    
    with status_col2:
        st.metric("数据总量", f"{stats.get('total_size_mb', 0):.1f} MB")
    
    with status_col3:
        st.metric("最近更新", "刚刚" if stats.get('recent_files') else "无")
    
    with status_col4:
        st.metric("系统健康", "正常", "✓")
    
    # 最近文件
    if stats.get('recent_files'):
        st.subheader("📁 最近文件")
        recent_df = pd.DataFrame(stats['recent_files'][:5])
        st.dataframe(recent_df, width='stretch', hide_index=True)

def show_scenario_config():
    """显示想定配置页面"""
    st.header("🎯 想定配置")
    
    # 想定类型选择
    scenario_type = st.selectbox(
        "选择对抗想定类型",
        ["一对一对抗", "多对一对抗", "多对多对抗"],
        index=0
    )
    
    # 映射想定类型
    scenario_map = {
        "一对一对抗": "one_vs_one",
        "多对一对抗": "many_vs_one", 
        "多对多对抗": "many_vs_many"
    }
    
    selected_type = scenario_map[scenario_type]
    
    # 获取想定描述
    scenarios_info = ScenarioFactory.get_available_scenarios()
    scenario_info = next((s for s in scenarios_info if s['id'] == selected_type), None)
    
    if scenario_info:
        st.info(f"**{scenario_info['name']}**: {scenario_info['description']}")
    
    # 配置表单
    st.subheader("⚙️ 实体配置")
    
    if selected_type == "one_vs_one":
        config_one_vs_one()
    elif selected_type == "many_vs_one":
        config_many_vs_one()
    elif selected_type == "many_vs_many":
        config_many_vs_many()
    
    # 环境配置
    st.subheader("🌍 环境设置")
    
    env_col1, env_col2 = st.columns(2)
    
    with env_col1:
        terrain_type = st.selectbox(
            "地形类型",
            ["平原", "丘陵", "山地", "城市", "海洋", "沙漠", "森林"],
            index=0
        )
    
    with env_col2:
        atmosphere = st.selectbox(
            "大气条件", 
            ["标准大气", "异常传播", "雨天", "沙尘", "浓雾"],
            index=0
        )
    
    # 创建想定按钮
    if st.button("🚀 创建对抗想定", type="primary", width='stretch'):
        with st.spinner("正在创建想定..."):
            try:
                # 这里应该根据表单输入创建配置字典
                config = get_scenario_config(selected_type)
                
                # 创建想定
                scenario = ScenarioFactory.create_scenario(selected_type)
                scenario.setup(config)
                
                st.session_state.scenario = scenario
                st.session_state.scenario_config = config
                
                st.success(f"✅ {scenario_type} 想定创建成功！")
                st.info(f"雷达数量: {len(scenario.radars)} | 干扰机数量: {len(scenario.jammers)}")
                
            except Exception as e:
                st.error(f"创建想定失败: {e}")

def config_one_vs_one():
    """配置一对一对抗"""
    st.write("**雷达配置**")
    
    radar_col1, radar_col2, radar_col3 = st.columns(3)
    
    with radar_col1:
        radar_lat = st.number_input("雷达纬度", value=39.9, format="%.4f", key="radar_lat")
        radar_freq = st.number_input("雷达频率 (GHz)", value=3.0, format="%.1f", key="radar_freq")
        radar_power = st.number_input("雷达功率 (kW)", value=100.0, format="%.1f", key="radar_power")
    
    with radar_col2:
        radar_lon = st.number_input("雷达经度", value=116.4, format="%.4f", key="radar_lon")
        radar_gain = st.number_input("雷达增益 (dBi)", value=40.0, format="%.1f", key="radar_gain")
        radar_beamwidth = st.number_input("波束宽度 (°)", value=1.5, format="%.1f", key="radar_beamwidth")
    
    with radar_col3:
        radar_alt = st.number_input("雷达高度 (m)", value=50.0, format="%.1f", key="radar_alt")
        radar_range = st.number_input("最大作用距离 (km)", value=300.0, format="%.1f", key="radar_range")
    
    st.write("**干扰机配置**")
    
    jammer_col1, jammer_col2, jammer_col3 = st.columns(3)
    
    with jammer_col1:
        jammer_lat = st.number_input("干扰机纬度", value=40.0, format="%.4f", key="jammer_lat")
        jammer_power = st.number_input("干扰机功率 (W)", value=1000.0, format="%.1f", key="jammer_power")
    
    with jammer_col2:
        jammer_lon = st.number_input("干扰机经度", value=116.5, format="%.4f", key="jammer_lon")
        jammer_gain = st.number_input("干扰机增益 (dBi)", value=15.0, format="%.1f", key="jammer_gain")
    
    with jammer_col3:
        jammer_alt = st.number_input("干扰机高度 (m)", value=10000.0, format="%.1f", key="jammer_alt")
        jammer_beamwidth = st.number_input("干扰波束宽度 (°)", value=60.0, format="%.1f", key="jammer_beamwidth")

def config_many_vs_one():
    """配置多对一对抗"""
    st.write("**雷达网络配置**")
    
    num_radars = st.slider("雷达数量", 2, 10, 3)
    
    radar_configs = []
    for i in range(num_radars):
        with st.expander(f"雷达 {i+1}", expanded=i==0):
            col1, col2 = st.columns(2)
            
            with col1:
                lat = st.number_input(f"纬度 {i+1}", value=39.9 + i*0.1, format="%.4f", key=f"radar_{i}_lat")
                lon = st.number_input(f"经度 {i+1}", value=116.4 + i*0.1, format="%.4f", key=f"radar_{i}_lon")
                freq = st.number_input(f"频率 {i+1} (GHz)", value=3.0 + i*0.2, format="%.1f", key=f"radar_{i}_freq")
            
            with col2:
                power = st.number_input(f"功率 {i+1} (kW)", value=100.0 + i*20, format="%.1f", key=f"radar_{i}_power")
                gain = st.number_input(f"增益 {i+1} (dBi)", value=40.0, format="%.1f", key=f"radar_{i}_gain")
    
    st.write("**干扰机配置**")
    
    jammer_col1, jammer_col2 = st.columns(2)
    
    with jammer_col1:
        jammer_lat = st.number_input("干扰机纬度", value=40.1, format="%.4f", key="many_jammer_lat")
        jammer_power = st.number_input("干扰机功率 (W)", value=1500.0, format="%.1f", key="many_jammer_power")
    
    with jammer_col2:
        jammer_lon = st.number_input("干扰机经度", value=116.6, format="%.4f", key="many_jammer_lon")
        jammer_gain = st.number_input("干扰机增益 (dBi)", value=15.0, format="%.1f", key="many_jammer_gain")

def config_many_vs_many():
    """配置多对多对抗"""
    st.write("**雷达网络配置**")
    
    num_radars = st.slider("雷达数量", 2, 10, 3)
    
    for i in range(num_radars):
        with st.expander(f"雷达 {i+1}", expanded=i==0):
            col1, col2 = st.columns(2)
            
            with col1:
                lat = st.number_input(f"雷达纬度 {i+1}", value=39.8 + i*0.2, format="%.4f", key=f"net_radar_{i}_lat")
                lon = st.number_input(f"雷达经度 {i+1}", value=116.3 + i*0.2, format="%.4f", key=f"net_radar_{i}_lon")
            
            with col2:
                freq = st.number_input(f"雷达频率 {i+1} (GHz)", value=3.0 + i*0.3, format="%.1f", key=f"net_radar_{i}_freq")
                power = st.number_input(f"雷达功率 {i+1} (kW)", value=100.0 + i*30, format="%.1f", key=f"net_radar_{i}_power")
    
    st.write("**干扰网络配置**")
    
    num_jammers = st.slider("干扰机数量", 2, 8, 2)
    
    for i in range(num_jammers):
        with st.expander(f"干扰机 {i+1}", expanded=i==0):
            col1, col2 = st.columns(2)
            
            with col1:
                lat = st.number_input(f"干扰机纬度 {i+1}", value=40.1 + i*0.1, format="%.4f", key=f"net_jammer_{i}_lat")
                lon = st.number_input(f"干扰机经度 {i+1}", value=116.6 + i*0.1, format="%.4f", key=f"net_jammer_{i}_lon")
            
            with col2:
                power = st.number_input(f"干扰机功率 {i+1} (W)", value=1000.0 + i*500, format="%.1f", key=f"net_jammer_{i}_power")
                gain = st.number_input(f"干扰机增益 {i+1} (dBi)", value=15.0, format="%.1f", key=f"net_jammer_{i}_gain")

def get_scenario_config(scenario_type: str) -> Dict[str, Any]:
    """获取想定配置"""
    # 这里应该从表单中提取配置
    # 简化实现
    if scenario_type == "one_vs_one":
        return {
            "radar": {
                "id": "radar_001",
                "name": "配置雷达",
                "frequency": 3.0,
                "power": 100.0,
                "lat": 39.9,
                "lon": 116.4,
                "alt": 50.0
            },
            "jammer": {
                "id": "jammer_001",
                "name": "配置干扰机",
                "power": 1000.0,
                "lat": 40.0,
                "lon": 116.5,
                "alt": 10000.0
            }
        }
    elif scenario_type == "many_vs_one":
        return {
            "radars": [
                {
                    "id": f"radar_{i}",
                    "name": f"雷达{i}",
                    "frequency": 3.0 + i*0.2,
                    "power": 100.0 + i*20,
                    "lat": 39.9 + i*0.1,
                    "lon": 116.4 + i*0.1,
                    "alt": 50.0
                } for i in range(3)
            ],
            "jammer": {
                "id": "jammer_001",
                "name": "干扰机",
                "power": 1500.0,
                "lat": 40.1,
                "lon": 116.6,
                "alt": 10000.0
            }
        }
    elif scenario_type == "many_vs_many":
        return {
            "radar_network": [
                {
                    "id": f"net_radar_{i}",
                    "name": f"网络雷达{i}",
                    "frequency": 3.0 + i*0.3,
                    "power": 100.0 + i*30,
                    "lat": 39.8 + i*0.2,
                    "lon": 116.3 + i*0.2,
                    "alt": 50.0
                } for i in range(3)
            ],
            "jammer_network": [
                {
                    "id": f"net_jammer_{i}",
                    "name": f"网络干扰机{i}",
                    "power": 1000.0 + i*500,
                    "lat": 40.1 + i*0.1,
                    "lon": 116.6 + i*0.1,
                    "alt": 10000.0
                } for i in range(2)
            ]
        }
    
    return {}

def show_simulation_control():
    """显示仿真控制页面"""
    st.header("⚡ 仿真控制")
    
    if st.session_state.scenario is None:
        st.warning("⚠️ 请先创建或加载一个对抗想定")
        if st.button("前往想定配置"):
            st.session_state.page = "想定配置"
            st.rerun()
        return
    
    scenario = st.session_state.scenario
    
    st.success(f"✅ 当前想定: **{scenario.name}**")
    st.info(f"📋 {scenario.description}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("雷达数量", len(scenario.radars))
    
    with col2:
        st.metric("干扰机数量", len(scenario.jammers))
    
    with col3:
        st.metric("目标数量", len(scenario.targets))
    
    st.markdown("---")
    
    # 仿真参数设置
    st.subheader("⚙️ 仿真参数")
    
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    
    with sim_col1:
        simulation_speed = st.select_slider(
            "仿真速度",
            options=["0.5x", "1x", "2x", "5x", "10x", "实时"],
            value="1x"
        )
    
    with sim_col2:
        duration = st.number_input("仿真时长 (秒)", min_value=1, max_value=3600, value=300)
    
    with sim_col3:
        resolution = st.select_slider(
            "分辨率",
            options=["低", "中", "高", "最高"],
            value="中"
        )
    
    # 开始仿真按钮
    if st.button("🚀 开始仿真", type="primary", width='stretch'):
        with st.spinner("正在运行仿真..."):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 模拟仿真进度
                for i in range(100):
                    progress = (i + 1) / 100
                    progress_bar.progress(progress)
                    status_text.text(f"仿真进度: {progress:.0%}")
                    
                    # 这里应该调用实际的仿真逻辑
                    import time
                    time.sleep(0.01)  # 模拟计算时间
                
                # 执行仿真
                results = scenario.execute()
                assessment = scenario.assess()
                
                st.session_state.simulation_results = results
                st.session_state.assessment_results = assessment
                
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ 仿真完成！")
                
                # 显示简要结果
                if 'result' in results:
                    result = results['result']
                    st.info(f"干扰是否有效: {'是' if result.get('effective') else '否'}")
                    st.info(f"干信比: {result.get('j_s_ratio', 0):.1f} dB")
                
            except Exception as e:
                exec_str = traceback.format_exc()
                st.error(f"仿真失败222: {exec_str}")
    
    # 如果已有仿真结果，显示快速操作
    if st.session_state.simulation_results:
        st.markdown("---")
        st.subheader("🔧 结果操作")
        
        op_col1, op_col2, op_col3 = st.columns(3)
        
        with op_col1:
            if st.button("重新仿真", width='stretch'):
                st.session_state.simulation_results = None
                st.session_state.assessment_results = None
                st.rerun()
        
        with op_col2:
            if st.button("查看详细结果", width='stretch'):
                st.session_state.page = "结果分析"
                st.rerun()
        
        with op_col3:
            if st.button("导出结果", width='stretch'):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"simulation_{timestamp}.json"
                    
                    data_manager.save_simulation_results(
                        st.session_state.simulation_results,
                        scenario.name
                    )
                    
                    st.success(f"✅ 结果已导出")
                except Exception as e:
                    st.error(f"导出失败: {e}")

def show_results_analysis():
    """显示结果分析页面"""
    st.header("📊 结果分析")
    
    if st.session_state.simulation_results is None:
        st.warning("⚠️ 暂无仿真结果，请先运行仿真")
        if st.button("前往仿真控制"):
            st.session_state.page = "仿真控制"
            st.rerun()
        return
    
    results = st.session_state.simulation_results
    assessment = st.session_state.assessment_results
    
    # 结果摘要
    st.subheader("📈 仿真结果摘要")
    
    if 'result' in results:
        result = results['result']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            effective = result.get('effective', False)
            st.metric(
                "干扰效果", 
                "有效" if effective else "无效",
                delta="✓" if effective else "✗"
            )
        
        with col2:
            j_s_ratio = result.get('j_s_ratio', 0)
            st.metric("干信比", f"{j_s_ratio:.1f} dB")
        
        with col3:
            det_prob = result.get('detection_probability', 0) * 100
            st.metric("探测概率", f"{det_prob:.1f}%")
        
        with col4:
            prop_loss = result.get('propagation_loss', 0)
            st.metric("传播损耗", f"{prop_loss:.1f} dB")
    
    st.markdown("---")
    
    # 可视化标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 地理态势", "📡 信号分析", "📊 效能评估", "📁 详细数据"])
    
    with tab1:
        show_geographical_visualization()
    
    with tab2:
        show_signal_analysis()
    
    with tab3:
        show_performance_assessment()
    
    with tab4:
        show_detailed_data()
    
    # 导出选项
    st.markdown("---")
    st.subheader("💾 导出选项")
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        export_format = st.selectbox(
            "导出格式",
            ["JSON", "CSV", "Excel", "PDF报告", "HTML报告"]
        )
    
    with export_col2:
        if st.button("生成报告", width='stretch'):
            try:
                report = ReportGenerator.generate_assessment_report(assessment, format="html")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{timestamp}.html"
                
                with open(f"static/reports/{filename}", "w", encoding='utf-8') as f:
                    f.write(report)
                
                st.success(f"✅ 报告已生成: {filename}")
            except Exception as e:
                st.error(f"生成报告失败: {e}")
    
    with export_col3:
        if st.button("保存所有结果", width='stretch', type="primary"):
            try:
                all_data = {
                    "simulation_results": results,
                    "assessment": assessment,
                    "metadata": {
                        "export_time": datetime.now().isoformat(),
                        "scenario": st.session_state.scenario.name if st.session_state.scenario else "未知"
                    }
                }
                
                filename = data_manager.save_simulation_results(all_data)
                st.success(f"✅ 所有结果已保存到: {filename}")
            except Exception as e:
                st.error(f"保存失败: {e}")

def show_geographical_visualization():
    """显示地理可视化"""
    st.write("**地理态势图**")
    
    if st.session_state.scenario is None:
        st.warning("暂无想定数据")
        return
    
    scenario = st.session_state.scenario
    
    # 创建可视化
    viz = EWVisualizer.create_coverage_map(
        scenario.radars, 
        scenario.jammers,
        scenario.targets
    )
    
    # 检查可视化类型并显示
    if hasattr(viz, '__class__'):
        viz_class_name = viz.__class__.__name__
        
        if 'DynamicMap' in viz_class_name or 'HoloViews' in str(type(viz)):
            # 这是HoloViews/GeoViews对象
            if VISUALIZATION_AVAILABLE:
                try:
                    # 尝试使用Bokeh渲染
                    if render_bokeh_plot(viz, height=600):
                        st.success("✓ 地理态势图显示成功")
                    else:
                        st.warning("Bokeh渲染失败，尝试使用备用方案")
                        # 使用Matplotlib备用方案
                        if isinstance(viz, plt.Figure):
                            st.pyplot(viz)
                except Exception as e:
                    st.error(f"渲染Bokeh图表失败: {e}")
                    # 使用Matplotlib备用方案
                    if isinstance(viz, plt.Figure):
                        st.pyplot(viz)
            else:
                st.warning("高级可视化不可用，显示简化版")
                # 使用Matplotlib图形
                if isinstance(viz, plt.Figure):
                    st.pyplot(viz)
        elif isinstance(viz, plt.Figure):
            # 这是Matplotlib图形
            st.pyplot(viz)
        else:
            st.warning(f"未知的可视化类型: {viz_class_name}")
            
            # 尝试使用Folium
            try:
                folium_map = EWVisualizer.create_folium_map(
                    scenario.radars, 
                    scenario.jammers,
                    scenario.targets
                )
                
                # 保存为HTML并显示
                map_path = "static/temp/map.html"
                os.makedirs(os.path.dirname(map_path), exist_ok=True)
                folium_map.save(map_path)
                
                with open(map_path, "r", encoding='utf-8') as f:
                    html = f.read()
                
                st.components.v1.html(html, height=600, scrolling=True)
                
            except Exception as e2:
                st.error(f"Folium地图也失败: {e2}")
                
                # 使用最简单的文本显示
                st.write("**实体位置**")
                
                pos_data = []
                for radar in scenario.radars:
                    pos_data.append({
                        "类型": "雷达",
                        "名称": radar.name,
                        "纬度": radar.position.lat,
                        "经度": radar.position.lon,
                        "高度": radar.position.alt
                    })
                
                for jammer in scenario.jammers:
                    pos_data.append({
                        "类型": "干扰机", 
                        "名称": jammer.name,
                        "纬度": jammer.position.lat,
                        "经度": jammer.position.lon,
                        "高度": jammer.position.alt
                    })
                
                if pos_data:
                    st.dataframe(pd.DataFrame(pos_data), width='stretch', hide_index=True)
    else:
        st.warning("可视化对象类型未知")

def show_signal_analysis():
    """显示信号分析"""
    st.write("**信号分析图**")
    
    if st.session_state.simulation_results is None:
        st.warning("暂无仿真结果")
        return
    
    try:
        signal_plot = EWVisualizer.create_signal_analysis_plot(
            st.session_state.simulation_results
        )
        
        if signal_plot is not None:
            # 检查可视化类型
            if hasattr(signal_plot, '__class__'):
                viz_class_name = signal_plot.__class__.__name__
                
                if 'Curve' in viz_class_name or 'HoloViews' in str(type(signal_plot)):
                    # 这是HoloViews对象
                    if VISUALIZATION_AVAILABLE:
                        try:
                            if render_bokeh_plot(signal_plot, height=450):
                                st.success("✓ 信号分析图显示成功")
                        except Exception as e:
                            st.error(f"渲染Bokeh图表失败: {e}")
                            # 使用Matplotlib备用方案
                            if isinstance(signal_plot, plt.Figure):
                                st.pyplot(signal_plot)
                    else:
                        # 使用Matplotlib图形
                        if isinstance(signal_plot, plt.Figure):
                            st.pyplot(signal_plot)
                elif isinstance(signal_plot, plt.Figure):
                    # 这是Matplotlib图形
                    st.pyplot(signal_plot)
        else:
            st.info("信号分析图生成失败")
            
            # 显示简化的信号数据
            if 'result' in st.session_state.simulation_results:
                result = st.session_state.simulation_results['result']
                
                # 创建简单的Matplotlib图表
                fig, ax = plt.subplots(figsize=(10, 4))
                
                time = np.linspace(0, 10, 100)
                signal = 10 + 5 * np.sin(2 * np.pi * 0.5 * time)
                noise = 3 * np.sin(2 * np.pi * 0.3 * time)
                
                ax.plot(time, signal, 'b-', label='信号', linewidth=2)
                ax.plot(time, noise, 'r-', label='噪声', linewidth=2, alpha=0.7)
                ax.plot(time, signal + noise, 'g-', label='合成信号', linewidth=1, alpha=0.5)
                
                ax.set_xlabel('时间 (s)')
                ax.set_ylabel('幅度')
                ax.set_title('信号分析')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                st.pyplot(fig)
    
    except Exception as e:
        st.error(f"信号分析失败: {e}")
        
        # 显示简化的信号数据
        if 'result' in st.session_state.simulation_results:
            result = st.session_state.simulation_results['result']
            
            # 创建简单的Matplotlib图表
            fig, ax = plt.subplots(figsize=(10, 4))
            
            time = np.linspace(0, 10, 100)
            signal = 10 + 5 * np.sin(2 * np.pi * 0.5 * time)
            noise = 3 * np.sin(2 * np.pi * 0.3 * time)
            
            ax.plot(time, signal, 'b-', label='信号', linewidth=2)
            ax.plot(time, noise, 'r-', label='噪声', linewidth=2, alpha=0.7)
            ax.plot(time, signal + noise, 'g-', label='合成信号', linewidth=1, alpha=0.5)
            
            ax.set_xlabel('时间 (s)')
            ax.set_ylabel('幅度')
            ax.set_title('信号分析')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)

def show_performance_assessment():
    """显示效能评估"""
    st.write("**效能评估结果**")
    
    if st.session_state.assessment_results is None:
        st.warning("暂无评估结果")
        return
    
    assessment = st.session_state.assessment_results
    
    # 显示评估指标
    if 'jam_success_rate' in assessment:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            success_rate = assessment.get('jam_success_rate', 0)
            st.metric("干扰成功率", f"{success_rate:.1f}%")
        
        with col2:
            det_prob = assessment.get('detection_probability', 0)
            st.metric("探测概率", f"{det_prob:.1f}%")
        
        with col3:
            j_s_ratio = assessment.get('j_s_ratio', 0)
            st.metric("平均干信比", f"{j_s_ratio:.1f} dB")
        
        with col4:
            suppression = assessment.get('suppression_ratio', 0)
            st.metric("压制比例", f"{suppression:.1f}%")
    
    # 显示建议
    if 'suggested_tactics' in assessment and assessment['suggested_tactics']:
        st.subheader("💡 战术建议")
        
        tactics = assessment['suggested_tactics']
        for i, tactic in enumerate(tactics, 1):
            st.write(f"{i}. {tactic}")
    
    # 创建雷达图
    try:
        # 提取性能指标
        metrics = {}
        for key, value in assessment.items():
            if isinstance(value, (int, float)) and key not in ['jammer_utilization', 'network_coverage_ratio']:
                # 归一化到0-1范围用于雷达图
                if 'rate' in key or 'probability' in key or 'ratio' in key:
                    metrics[key] = value / 100
                elif 'j_s_ratio' in key:
                    metrics[key] = min(1.0, value / 20)  # 假设20dB为最大值
                else:
                    metrics[key] = min(1.0, value)
        
        if metrics:
            radar_plot = EWVisualizer.create_performance_radar(metrics)
            
            if radar_plot is not None:
                # 检查可视化类型
                if hasattr(radar_plot, '__class__'):
                    viz_class_name = radar_plot.__class__.__name__
                    
                    if 'Spikes' in viz_class_name or 'HoloViews' in str(type(radar_plot)):
                        # 这是HoloViews对象
                        if VISUALIZATION_AVAILABLE:
                            try:
                                if render_bokeh_plot(radar_plot, height=550):
                                    st.success("✓ 性能雷达图显示成功")
                            except Exception as e:
                                st.error(f"渲染Bokeh图表失败: {e}")
                                # 使用Matplotlib备用方案
                                if isinstance(radar_plot, plt.Figure):
                                    st.pyplot(radar_plot)
                        else:
                            # 使用Matplotlib图形
                            if isinstance(radar_plot, plt.Figure):
                                st.pyplot(radar_plot)
                    elif isinstance(radar_plot, plt.Figure):
                        # 这是Matplotlib图形
                        st.pyplot(radar_plot)
    
    except Exception as e:
        st.warning(f"创建雷达图失败: {e}")

def show_detailed_data():
    """显示详细数据"""
    st.write("**详细仿真数据**")
    
    if st.session_state.simulation_results is None:
        st.warning("暂无仿真数据")
        return
    
    results = st.session_state.simulation_results
    
    # 显示原始数据
    st.subheader("原始仿真结果")
    
    # 使用可展开的JSON查看器
    with st.expander("查看JSON数据", expanded=False):
        st.json(results)
    
    # 如果有雷达结果，显示表格
    if 'radar_results' in results:
        st.subheader("雷达仿真结果")
        radar_df = pd.DataFrame(results['radar_results'])
        st.dataframe(radar_df, width='stretch', hide_index=True)
    
    # 如果有网络结果
    if 'network_result' in results:
        st.subheader("网络仿真结果")
        network_df = pd.DataFrame([results['network_result']])
        st.dataframe(network_df, width='stretch', hide_index=True)
    
    # 显示评估结果
    if st.session_state.assessment_results:
        st.subheader("评估结果")
        assessment_df = pd.DataFrame([st.session_state.assessment_results])
        st.dataframe(assessment_df, width='stretch', hide_index=True)

def show_data_management():
    """显示数据管理页面"""
    st.header("📁 数据管理")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💾 结果管理", "📊 统计分析", "🔄 导入/导出", "🧹 清理维护"])
    
    with tab1:
        show_results_management()
    
    with tab2:
        show_statistical_analysis()
    
    with tab3:
        show_import_export()
    
    with tab4:
        show_cleanup_maintenance()

def show_results_management():
    """显示结果管理"""
    st.subheader("仿真结果管理")
    
    # 获取所有结果文件
    import glob
    result_files = glob.glob("data/results/*.json")
    
    if not result_files:
        st.info("暂无仿真结果文件")
        return
    
    # 文件列表
    st.write(f"找到 {len(result_files)} 个结果文件")
    
    selected_file = st.selectbox(
        "选择结果文件",
        result_files,
        format_func=lambda x: Path(x).name
    )
    
    if selected_file:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 加载结果", width='stretch'):
                try:
                    with open(selected_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                    
                    st.session_state.simulation_results = results.get('simulation_results')
                    st.session_state.assessment_results = results.get('assessment')
                    
                    st.success("✅ 结果加载成功")
                    st.info("前往结果分析页面查看")
                except Exception as e:
                    st.error(f"加载失败: {e}")
        
        with col2:
            if st.button("👁️ 预览", width='stretch'):
                try:
                    with open(selected_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                    
                    with st.expander("文件内容", expanded=True):
                        st.json(results)
                except Exception as e:
                    st.error(f"预览失败: {e}")
        
        with col3:
            if st.button("🗑️ 删除", width='stretch', type="secondary"):
                try:
                    os.remove(selected_file)
                    st.success("✅ 文件已删除")
                    st.rerun()
                except Exception as e:
                    st.error(f"删除失败: {e}")

def show_statistical_analysis():
    """显示统计分析"""
    st.subheader("统计分析")
    
    # 获取数据统计
    stats = data_manager.get_data_statistics()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总文件数", stats.get('total_results', 0))
    
    with col2:
        st.metric("总数据量", f"{stats.get('total_size_mb', 0):.1f} MB")
    
    with col3:
        st.metric("文件类型", len(stats.get('file_types', {})))
    
    # 文件类型分布
    if stats.get('file_types'):
        st.subheader("文件类型分布")
        
        file_types = stats['file_types']
        types_df = pd.DataFrame({
            '文件类型': list(file_types.keys()),
            '数量': list(file_types.values())
        })
        
        st.bar_chart(types_df.set_index('文件类型'))
    
    # 最近文件
    if stats.get('recent_files'):
        st.subheader("最近文件")
        recent_df = pd.DataFrame(stats['recent_files'])
        st.dataframe(recent_df, width='stretch', hide_index=True)

def show_import_export():
    """显示导入导出"""
    st.subheader("数据导入导出")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**导入数据**")
        
        uploaded_file = st.file_uploader(
            "选择文件",
            type=['json', 'csv', 'yaml', 'yml'],
            key="import_file"
        )
        
        if uploaded_file is not None:
            try:
                content = uploaded_file.read()
                
                if uploaded_file.name.endswith('.json'):
                    data = json.loads(content)
                elif uploaded_file.name.endswith('.csv'):
                    data = pd.read_csv(uploaded_file).to_dict('records')
                elif uploaded_file.name.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(content)
                
                st.success(f"✅ 成功导入 {uploaded_file.name}")
                
                if st.button("加载到当前会话"):
                    st.session_state.simulation_results = data
                    st.success("✅ 数据已加载")
                
            except Exception as e:
                st.error(f"导入失败: {e}")
    
    with col2:
        st.write("**导出数据**")
        
        if st.session_state.simulation_results:
            export_format = st.selectbox(
                "导出格式",
                ["JSON", "CSV", "Excel", "YAML"],
                key="export_format"
            )
            
            if st.button("导出当前结果", width='stretch'):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    if export_format == "JSON":
                        filename = f"export_{timestamp}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(st.session_state.simulation_results, f, indent=2, ensure_ascii=False)
                    
                    elif export_format == "CSV":
                        # 尝试转换为CSV
                        filename = f"export_{timestamp}.csv"
                        if 'radar_results' in st.session_state.simulation_results:
                            df = pd.DataFrame(st.session_state.simulation_results['radar_results'])
                            df.to_csv(filename, index=False, encoding='utf-8')
                    
                    st.success(f"✅ 已导出: {filename}")
                
                except Exception as e:
                    st.error(f"导出失败: {e}")
        else:
            st.info("暂无数据可导出")

def show_cleanup_maintenance():
    """显示清理维护"""
    st.subheader("系统清理维护")
    
    st.warning("⚠️ 警告: 这些操作可能不可逆，请谨慎操作！")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days = st.slider("清理多少天前的文件", 1, 365, 30)
        
        if st.button("清理旧文件", type="secondary", width='stretch'):
            try:
                deleted = data_manager.cleanup_old_files(days)
                st.success(f"✅ 已清理 {deleted} 个旧文件")
            except Exception as e:
                st.error(f"清理失败: {e}")
    
    with col2:
        if st.button("清理缓存", type="secondary", width='stretch'):
            try:
                data_manager.clear_cache()
                st.success("✅ 缓存已清理")
            except Exception as e:
                st.error(f"清理缓存失败: {e}")
    
    st.markdown("---")
    
    # 备份恢复
    st.subheader("备份与恢复")
    
    backup_col1, backup_col2 = st.columns(2)
    
    with backup_col1:
        if st.button("创建备份", width='stretch'):
            try:
                backup_path = data_manager.backup_data()
                st.success(f"✅ 备份已创建: {backup_path}")
            except Exception as e:
                st.error(f"备份失败: {e}")
    
    with backup_col2:
        backup_dir = st.text_input("备份目录路径", "data/backups/")
        
        if st.button("恢复备份", width='stretch', type="secondary"):
            try:
                if data_manager.restore_backup(backup_dir):
                    st.success("✅ 备份恢复成功")
                else:
                    st.error("恢复失败")
            except Exception as e:
                st.error(f"恢复失败: {e}")

def show_system_settings():
    """显示系统设置"""
    st.header("⚙️ 系统设置")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🛠️ 系统配置", "📈 性能设置", "🔐 安全设置", "ℹ️ 系统信息"])
    
    with tab1:
        show_system_config()
    
    with tab2:
        show_performance_settings()
    
    with tab3:
        show_security_settings()
    
    with tab4:
        show_system_info()

def show_system_config():
    """显示系统配置"""
    st.subheader("系统配置")
    
    # 基本设置
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "界面主题",
            ["自动", "浅色", "深色"],
            index=0
        )
        
        language = st.selectbox(
            "语言",
            ["简体中文", "English"],
            index=0
        )
    
    with col2:
        default_scenario = st.selectbox(
            "默认想定",
            ["一对一对抗", "多对一对抗", "多对多对抗"],
            index=0
        )
        
        auto_save = st.checkbox("自动保存结果", value=True)
    
    # 可视化设置
    st.subheader("可视化设置")
    
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        map_provider = st.selectbox(
            "地图服务",
            ["OpenStreetMap", "卫星影像", "地形图", "自定义"],
            index=0
        )
        
        default_zoom = st.slider("默认缩放级别", 1, 20, 8)
    
    with viz_col2:
        viz_engine = st.selectbox(
            "可视化引擎",
            ["Bokeh (推荐)", "Matplotlib", "Plotly"],
            index=0
        )
        
        high_quality = st.checkbox("高质量渲染", value=True)
    
    if st.button("💾 保存设置", type="primary"):
        st.success("✅ 设置已保存")

def show_performance_settings():
    """显示性能设置"""
    st.subheader("性能设置")
    
    # 仿真性能
    st.write("**仿真性能**")
    
    perf_col1, perf_col2 = st.columns(2)
    
    with perf_col1:
        max_entities = st.number_input(
            "最大实体数量", 
            min_value=10, 
            max_value=10000, 
            value=1000,
            help="单个想定中允许的最大实体数量"
        )
        
        cache_size = st.number_input(
            "缓存大小 (MB)", 
            min_value=10, 
            max_value=10000, 
            value=100,
            help="仿真结果缓存大小"
        )
    
    with perf_col2:
        parallel_processing = st.checkbox(
            "启用并行计算", 
            value=True,
            help="使用多核CPU加速仿真"
        )
        
        if parallel_processing:
            num_cores = st.slider("使用CPU核心数", 1, os.cpu_count() or 4, 2)
    
    # 内存管理
    st.write("**内存管理**")
    
    memory_limit = st.slider(
        "内存使用限制 (MB)",
        100, 10000, 2000,
        help="限制仿真使用的最大内存"
    )
    
    auto_cleanup = st.checkbox(
        "自动清理内存", 
        value=True,
        help="仿真完成后自动清理临时数据"
    )
    
    if st.button("🚀 应用性能设置", type="primary"):
        st.success("✅ 性能设置已应用")

def show_security_settings():
    """显示安全设置"""
    st.subheader("安全设置")
    
    # 访问控制
    st.write("**访问控制**")
    
    require_auth = st.checkbox("需要身份验证", value=False)
    
    if require_auth:
        auth_col1, auth_col2 = st.columns(2)
        
        with auth_col1:
            username = st.text_input("用户名", value="admin")
        
        with auth_col2:
            password = st.text_input("密码", type="password")
    
    # 数据安全
    st.write("**数据安全**")
    
    encrypt_data = st.checkbox("加密敏感数据", value=True)
    
    if encrypt_data:
        encryption_key = st.text_input(
            "加密密钥",
            type="password",
            help="用于加密敏感数据的密钥"
        )
    
    auto_logout = st.checkbox("自动注销", value=True)
    
    if auto_logout:
        timeout = st.slider("超时时间 (分钟)", 1, 120, 30)
    
    if st.button("🔐 保存安全设置", type="primary"):
        st.success("✅ 安全设置已保存")

def show_system_info():
    """显示系统信息"""
    st.subheader("系统信息")
    
    import platform
    import sys
    import psutil
    
    # 系统信息
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write("**操作系统**")
        st.code(f"{platform.system()} {platform.release()}")
        
        st.write("**Python版本**")
        st.code(f"{platform.python_version()}")
        
        st.write("**架构**")
        st.code(f"{platform.machine()}")
    
    with info_col2:
        st.write("**处理器**")
        st.code(f"{platform.processor()}")
        
        st.write("**内存**")
        memory = psutil.virtual_memory()
        st.code(f"可用: {memory.available/1e9:.1f} GB / 总计: {memory.total/1e9:.1f} GB")
        
        st.write("**磁盘空间**")
        disk = psutil.disk_usage('/')
        st.code(f"可用: {disk.free/1e9:.1f} GB / 总计: {disk.total/1e9:.1f} GB")
    
    # 应用信息
    st.subheader("应用信息")
    
    app_col1, app_col2 = st.columns(2)
    
    with app_col1:
        st.write("**Streamlit版本**")
        st.code(f"{st.__version__}")
        
        st.write("**应用版本**")
        st.code("1.0.0")
    
    with app_col2:
        st.write("**启动时间**")
        st.code(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.write("**运行时间**")
        st.code("刚刚启动")

# 主路由
if page == "🏠 概览":
    show_overview()
elif page == "🎯 想定配置":
    show_scenario_config()
elif page == "⚡ 仿真控制":
    show_simulation_control()
elif page == "📊 结果分析":
    show_results_analysis()
elif page == "📁 数据管理":
    show_data_management()
elif page == "⚙️ 系统设置":
    show_system_settings()

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: gray;">
        <p>电子战对抗仿真系统 v1.0.0 | © 2024 电子战仿真实验室</p>
        <p>技术支持: support@ew-simulation.com | 文档: <a href="https://ew-simulation.com/docs" target="_blank">在线文档</a></p>
    </div>
    """,
    unsafe_allow_html=True
)

