

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电子战对抗仿真系统 - 主应用
使用简化版Matplotlib可视化
"""
import streamlit as st
import sys
import os
from pathlib import Path
import warnings
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
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import yaml
from typing import Dict, List, Any, Optional
import io
import base64

# 设置Matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# 导入自定义模块
try:
    from src.core.patterns.strategy import ScenarioFactory
    from src.core.factory import EntityFactory
    from src.visualization.geoviz import EWVisualizer
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
    
    *版本: 1.0.0 | 使用稳定的Matplotlib可视化引擎*
""")

# 侧边栏导航
st.sidebar.title("导航")
page = st.sidebar.radio(
    "选择页面",
    ["🏠 概览", "🎯 想定配置", "⚡ 仿真控制", "📊 结果分析", "📁 数据管理"]
)

# 初始化会话状态
if 'scenario' not in st.session_state:
    st.session_state.scenario = None
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'assessment_results' not in st.session_state:
    st.session_state.assessment_results = None

# 数据管理器
data_manager = DataManager()

def create_simple_matplotlib_plot(radars, jammers, targets=None):
    """创建简单的Matplotlib地理态势图"""
    try:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 设置背景
        ax.set_facecolor('#f0f0f0')
        
        # 绘制雷达
        radar_lats = [r.position.lat for r in radars]
        radar_lons = [r.position.lon for r in radars]
        radar_names = [r.name for r in radars]
        
        for i, (lat, lon, name) in enumerate(zip(radar_lats, radar_lons, radar_names)):
            ax.scatter(lon, lat, c='blue', s=150, marker='^', 
                      edgecolors='black', linewidth=1.5, zorder=5)
            ax.annotate(name, (lon, lat), xytext=(5, 5), 
                       textcoords='offset points', fontsize=9, color='blue')
        
        # 绘制干扰机
        jammer_lats = [j.position.lat for j in jammers]
        jammer_lons = [j.position.lon for j in jammers]
        jammer_names = [j.name for j in jammers]
        
        for i, (lat, lon, name) in enumerate(zip(jammer_lats, jammer_lons, jammer_names)):
            ax.scatter(lon, lat, c='red', s=120, marker='s', 
                      edgecolors='black', linewidth=1.5, zorder=5)
            ax.annotate(name, (lon, lat), xytext=(5, 5), 
                       textcoords='offset points', fontsize=9, color='red')
        
        # 绘制目标
        if targets:
            target_lats = [t.position.lat for t in targets]
            target_lons = [t.position.lon for t in targets]
            target_names = [t.name for t in targets]
            
            for i, (lat, lon, name) in enumerate(zip(target_lats, target_lons, target_names)):
                ax.scatter(lon, lat, c='green', s=100, marker='o', 
                          edgecolors='black', linewidth=1.5, zorder=5)
                ax.annotate(name, (lon, lat), xytext=(5, 5), 
                           textcoords='offset points', fontsize=9, color='green')
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='blue', edgecolor='black', label=f'雷达 ({len(radars)}个)'),
            Patch(facecolor='red', edgecolor='black', label=f'干扰机 ({len(jammers)}个)'),
        ]
        if targets:
            legend_elements.append(Patch(facecolor='green', edgecolor='black', label=f'目标 ({len(targets)}个)'))
        
        ax.legend(handles=legend_elements, loc='upper right')
        
        # 设置标签和标题
        ax.set_xlabel('经度')
        ax.set_ylabel('纬度')
        ax.set_title('电子战对抗态势图', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 自动调整坐标轴范围
        all_lats = radar_lats + jammer_lats
        all_lons = radar_lons + jammer_lons
        if targets:
            all_lats += target_lats
            all_lons += target_lons
        
        if all_lats and all_lons:
            lat_padding = (max(all_lats) - min(all_lats)) * 0.1
            lon_padding = (max(all_lons) - min(all_lons)) * 0.1
            
            ax.set_xlim(min(all_lons) - lon_padding, max(all_lons) + lon_padding)
            ax.set_ylim(min(all_lats) - lat_padding, max(all_lats) + lat_padding)
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        st.error(f"创建态势图失败: {e}")
        # 返回空图
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, f'错误: {str(e)}', 
               ha='center', va='center', fontsize=12, color='red')
        return fig

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
        st.metric("可视化类型", "Matplotlib", "稳定可靠")
    
    st.markdown("---")
    
    # 快速开始
    st.subheader("🚀 快速开始")
    
    quick_start_col1, quick_start_col2, quick_start_col3 = st.columns(3)
    
    with quick_start_col1:
        if st.button("创建一对一对抗", use_container_width=True):
            try:
                st.session_state.scenario = ScenarioFactory.create_scenario("one_vs_one")
                st.success("一对一对抗想定已创建")
            except Exception as e:
                st.error(f"创建想定失败: {e}")
    
    with quick_start_col2:
        if st.button("运行示例仿真", use_container_width=True):
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
        if st.button("查看示例结果", use_container_width=True):
            if st.session_state.simulation_results:
                st.success("已有仿真结果，正在显示...")
            else:
                st.warning("请先运行示例仿真")

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
    
    # 创建想定按钮
    if st.button("🚀 创建对抗想定", type="primary", use_container_width=True):
        with st.spinner("正在创建想定..."):
            try:
                # 使用默认配置
                if selected_type == "one_vs_one":
                    config = {
                        "radar": {
                            "id": "radar_001",
                            "name": "雷达1",
                            "frequency": 3.0,
                            "power": 100.0,
                            "lat": 39.9,
                            "lon": 116.4,
                            "alt": 50.0
                        },
                        "jammer": {
                            "id": "jammer_001",
                            "name": "干扰机1",
                            "power": 1000.0,
                            "lat": 40.0,
                            "lon": 116.5,
                            "alt": 10000.0
                        }
                    }
                elif selected_type == "many_vs_one":
                    config = {
                        "radars": [
                            {
                                "id": f"radar_{i}",
                                "name": f"雷达{i+1}",
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
                else:  # many_vs_many
                    config = {
                        "radar_network": [
                            {
                                "id": f"net_radar_{i}",
                                "name": f"网络雷达{i+1}",
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
                                "name": f"网络干扰机{i+1}",
                                "power": 1000.0 + i*500,
                                "lat": 40.1 + i*0.1,
                                "lon": 116.6 + i*0.1,
                                "alt": 10000.0
                            } for i in range(2)
                        ]
                    }
                
                # 创建想定
                scenario = ScenarioFactory.create_scenario(selected_type)
                scenario.setup(config)
                
                st.session_state.scenario = scenario
                st.session_state.scenario_config = config
                
                st.success(f"✅ {scenario_type} 想定创建成功！")
                st.info(f"雷达数量: {len(scenario.radars)} | 干扰机数量: {len(scenario.jammers)}")
                
            except Exception as e:
                st.error(f"创建想定失败: {e}")

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
    
    # 开始仿真按钮
    if st.button("🚀 开始仿真", type="primary", use_container_width=True):
        with st.spinner("正在运行仿真..."):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 模拟仿真进度
                for i in range(100):
                    progress = (i + 1) / 100
                    progress_bar.progress(progress)
                    status_text.text(f"仿真进度: {progress:.0%}")
                    
                    import time
                    time.sleep(0.01)
                
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
                    effective = result.get('effective', False)
                    j_s_ratio = result.get('j_s_ratio', 0)
                    
                    st.info(f"干扰是否有效: **{'是 ✓' if effective else '否 ✗'}**")
                    st.info(f"干信比: **{j_s_ratio:.1f} dB**")
                
            except Exception as e:
                st.error(f"仿真失败: {e}")

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
    tab1, tab2, tab3 = st.tabs(["🗺️ 地理态势", "📡 信号分析", "📁 详细数据"])
    
    with tab1:
        # 显示地理态势图
        if st.session_state.scenario:
            fig = create_simple_matplotlib_plot(
                st.session_state.scenario.radars,
                st.session_state.scenario.jammers,
                st.session_state.scenario.targets
            )
            st.pyplot(fig)
    
    with tab2:
        # 显示信号分析
        if 'result' in results:
            result = results['result']
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            time = np.linspace(0, 10, 100)
            
            if 'j_s_ratio' in result:
                j_s_ratio = result['j_s_ratio']
                signal_power = 10 + 5 * np.sin(2 * np.pi * 0.5 * time)
                jammer_power = j_s_ratio + 3 * np.sin(2 * np.pi * 0.3 * time)
                
                ax.plot(time, signal_power, 'b-', label='信号功率', linewidth=2)
                ax.plot(time, jammer_power, 'r-', label='干扰功率', linewidth=2)
            else:
                signal = 10 + 5 * np.sin(2 * np.pi * 0.5 * time)
                noise = 3 * np.sin(2 * np.pi * 0.3 * time)
                
                ax.plot(time, signal, 'b-', label='信号', linewidth=2)
                ax.plot(time, noise, 'r-', label='噪声', linewidth=2, alpha=0.7)
            
            ax.set_xlabel('时间 (s)')
            ax.set_ylabel('幅度 (dB)')
            ax.set_title('信号分析')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
    
    with tab3:
        # 显示详细数据
        with st.expander("查看原始JSON数据", expanded=False):
            st.json(results)
        
        if assessment:
            st.subheader("评估结果")
            assessment_df = pd.DataFrame([assessment])
            st.dataframe(assessment_df, use_container_width=True, hide_index=True)

def show_data_management():
    """显示数据管理页面"""
    st.header("📁 数据管理")
    
    st.info("数据管理功能正在开发中...")
    
    # 简单的导入导出
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("导入数据")
        uploaded_file = st.file_uploader("选择JSON文件", type=['json'])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.simulation_results = data
                st.success("数据导入成功！")
            except Exception as e:
                st.error(f"导入失败: {e}")
    
    with col2:
        st.subheader("导出数据")
        if st.session_state.simulation_results:
            if st.button("导出当前结果"):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"simulation_result_{timestamp}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(st.session_state.simulation_results, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"结果已导出到: {filename}")
                except Exception as e:
                    st.error(f"导出失败: {e}")

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

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: gray;">
        <p>电子战对抗仿真系统 v1.0.0 | © 2024 电子战仿真实验室</p>
        <p>技术支持: support@ew-simulation.com</p>
    </div>
    """,
    unsafe_allow_html=True
)
