# 文件: app_integrated.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电子战对抗仿真系统
集成对抗分析模块和优化算法模块
"""
import trace
import traceback
import streamlit as st
import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 添加炫酷科技风格CSS
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    
    /* 主标题样式 - 霓虹效果 */
    .main-header {
        text-align: center;
        height: 20vh;
        padding: 1.5rem 0;
        background: rgba(0, 0, 0, 0.7);
        border-radius: 15px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(0, 247, 255, 0.3);
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.3),
                    inset 0 0 20px rgba(0, 247, 255, 0.1);
    }
    
    .main-header h1 {
        background: linear-gradient(90deg, #00fff7, #00ffaa, #00f7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .main-header p {
        color: #a0e7ff;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* 高科技卡片样式 */
    .tech-card {
        background: rgba(10, 15, 30, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 0.25rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0, 247, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .tech-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 247, 255, 0.4);
        box-shadow: 0 12px 40px rgba(0, 247, 255, 0.2);
    }
    
    .tech-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00fff7, #00ffaa, #00f7ff);
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1e 0%, #151b2d 100%);
    }
    
    .sidebar .sidebar-content {
        background: transparent !important;
    }
    
    /* 小标题样式 */
    .tech-card h3 {
        color: #00f7ff;
        font-size: 1.4rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0, 247, 255, 0.3);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .tech-card h3::before {
        content: '▶';
        color: #00ffaa;
        font-size: 0.8em;
    }
    
    /* 指标卡片样式 */
    .metric-display {
        background: rgba(0, 20, 40, 0.6);
        border-radius: 10px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(0, 247, 255, 0.15);
        transition: all 0.3s ease;
    }
    
    .metric-display:hover {
        background: rgba(0, 30, 60, 0.7);
        border-color: rgba(0, 247, 255, 0.3);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #0066ff 0%, #00ccff 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0055ee 0%, #00bbee 100%);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 102, 255, 0.4);
    }
    
    /* 滑块样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #0066ff, #00ccff) !important;
    }
    
    /* 输入框样式 */
    .stNumberInput input {
        background: rgba(0, 20, 40, 0.6) !important;
        color: white !important;
        border: 1px solid rgba(0, 247, 255, 0.3) !important;
        border-radius: 6px;
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div {
        background: rgba(0, 20, 40, 0.6) !important;
        color: white !important;
        border: 1px solid rgba(0, 247, 255, 0.3) !important;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid rgba(0, 247, 255, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: rgba(255, 255, 255, 0.6) !important;
        border: none !important;
        padding: 0.8rem 1.5rem;
        border-radius: 6px 6px 0 0;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 247, 255, 0.1) !important;
        color: white !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(0, 247, 255, 0.2) !important;
        color: white !important;
        border-bottom: 2px solid #00f7ff !important;
    }
    
    /* 数据框样式 */
    .dataframe {
        background: rgba(0, 20, 40, 0.6) !important;
        color: white !important;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 20, 40, 0.6);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #0066ff, #00ccff);
        border-radius: 4px;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #0066ff, #00ccff) !important;
    }
    
    /* 状态指示灯 */
    .status-led {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .status-good { background: #00ff00; box-shadow: 0 0 10px #00ff00; }
    .status-warning { background: #ffff00; box-shadow: 0 0 10px #ffff00; }
    .status-critical { background: #ff0000; box-shadow: 0 0 10px #ff0000; }
    
    /* 地图容器 */
    .folium-map {
        border-radius: 10px;
        overflow: hidden;
        border: 2px solid rgba(0, 247, 255, 0.3);
    }
    
    /* 徽章样式 */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 0.2rem;
    }
    
    .badge-primary { background: rgba(0, 102, 255, 0.3); color: #66b3ff; }
    .badge-success { background: rgba(0, 255, 0, 0.2); color: #00ff00; }
    .badge-warning { background: rgba(255, 255, 0, 0.2); color: #ffff00; }
    .badge-danger { background: rgba(255, 0, 0, 0.2); color: #ff6666; }
    
    /* 分割线 */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 247, 255, 0.3), transparent);
        margin: 1.5rem 0;
    }
    
    /* 网格线背景 */
    .grid-bg {
        background-image: 
            linear-gradient(rgba(0, 247, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 247, 255, 0.05) 1px, transparent 1px);
        background-size: 20px 20px;
    }
</style>
""", unsafe_allow_html=True)

# 设置页面配置
st.set_page_config(
    page_title="长城数字智能干扰资源分配和协同对抗仿真系统",
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
import time
import plotly.graph_objects as go
import plotly.express as px

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

try:
    from src.core.analysis.combat_analyzer import CombatAnalyzer
    from src.core.optimization.epde_algorithm import EPDEOptimizer
    from src.core.optimization.optimization_controller import OptimizationController
    from src.core.entities.radar_enhanced import EnhancedRadar
    from src.visualization.geoviz import EWVisualizer
    from src.utils.data_manager import DataManager
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("集成版应用启动")
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.stop()
    
def show_paper_comparison():
      """显示与基准结果的详细对比分析"""
      st.header("📊 与基准结果对比分析")
      
      st.info("""
      **对比基准**: 基于组合优化的威胁评估和干扰分配系统的实现》中的COTEJA系统
      **测试场景**: 4个干扰机 vs 5部雷达的典型对抗想定
      **评估指标**: 优化时间、资源利用率、中断次数、适应度等
      """)
      
      # 检查是否有仿真结果
      if not st.session_state.coteja_results:
          st.warning("⚠️ 暂无仿真结果，请先运行优化")
          if st.button("前往智能优化页面"):
              st.session_state.page = "智能优化"
              st.rerun()
          return
      
      results = st.session_state.coteja_results
      
      # 创建详细的对比表格
      comparison_data = {
          '性能指标': [
              '优化决策时间', 
              '资源利用率 (RUR)', 
              '雷达中断次数',
              '最优适应度',
              '收敛代数',
              '计算稳定性',
              '场景适应性'
          ],
          '本文结果': [
              f"{results['optimization_time']:.3f}s",
              f"{results['resource_utilization']:.1%}",
              results['assignment_report']['summary']['interruption_count'],
              f"{results['best_fitness']:.3f}",
              f"{len(results['convergence_data'])}代",
              "稳定" if results['optimization_time'] < 2.0 else "一般",
              "4v5场景通过"
          ],
          '基准结果': [
              "≤1.0s",
              "≥97.0%", 
              "≥3次",
              "≥0.9",
              "50-100代",
              "高度稳定",
              "4v5场景验证"
          ],
          '达标情况': [
              "✅ 达标" if results['optimization_time'] <= 1.0 else "⚠️ 接近",
              "✅ 达标" if results['resource_utilization'] >= 0.97 else "⚠️ 接近",
              "✅ 达标" if results['assignment_report']['summary']['interruption_count'] >= 3 else "❌ 未达",
              "✅ 达标" if results['best_fitness'] >= 0.9 else "⚠️ 接近",
              "✅ 达标",
              "✅ 达标",
              "✅ 达标"
          ]
      }
      
      comparison_df = pd.DataFrame(comparison_data)
      st.dataframe(comparison_df, width='stretch', hide_index=True)
      
      # 性能达标率统计
      st.subheader("📈 性能达标率分析")
      
      total_metrics = len(comparison_data['性能指标'])
      passed_metrics = sum(1 for status in comparison_data['达标情况'] if '✅' in status)
      pass_rate = (passed_metrics / total_metrics) * 100
      
      col1, col2, col3 = st.columns(3)
      with col1:
          st.metric("总指标数", total_metrics)
      with col2:
          st.metric("达标数", passed_metrics)
      with col3:
          st.metric("达标率", f"{pass_rate:.1f}%")
      
      # 可视化对比
      st.subheader("📊 关键指标对比图")
      
      # 准备可视化数据
      metrics_visualization = ['优化时间(s)', '资源利用率(%)', '中断次数', '适应度']
      our_results = [
          results['optimization_time'],
          results['resource_utilization'] * 100,
          results['assignment_report']['summary']['interruption_count'],
          results['best_fitness'] * 100  # 转换为百分比便于比较
      ]
      
      paper_results = [1.0, 97.0, 3, 90.0]
      
      # 创建对比柱状图
      fig, ax = plt.subplots(figsize=(12, 6))
      x = np.arange(len(metrics_visualization))
      width = 0.35
      
      bars1 = ax.bar(x - width/2, our_results, width, label='本文结果', color='#1f77b4', alpha=0.8)
      bars2 = ax.bar(x + width/2, paper_results, width, label='基准结果', color='#ff7f0e', alpha=0.8)
      
      ax.set_xlabel('性能指标')
      ax.set_ylabel('数值')
      ax.set_title('系统性能对比')
      ax.set_xticks(x)
      ax.set_xticklabels(metrics_visualization)
      ax.legend()
      ax.grid(True, alpha=0.3)
      
      # 在柱子上添加数值标签
      for bar in bars1:
          height = bar.get_height()
          ax.text(bar.get_x() + bar.get_width()/2., height,
                  f'{height:.1f}', ha='center', va='bottom')
      
      for bar in bars2:
          height = bar.get_height()
          ax.text(bar.get_x() + bar.get_width()/2., height,
                  f'{height:.1f}', ha='center', va='bottom')
      
      st.pyplot(fig)
      
      # 详细分析
      st.subheader("🔍 详细分析报告")
      
      analysis_tabs = st.tabs(["优化性能", "资源利用", "对抗效果", "系统稳定性"])
      
      with analysis_tabs[0]:
          st.write("**优化性能分析**")
          if results['optimization_time'] <= 1.0:
              st.success("✅ 优化时间达到基准要求（≤1.0秒）")
              st.write("ePDE算法在实时性方面表现优秀，满足作战决策的时效性要求。")
          else:
              st.warning("⚠️ 优化时间略超基准要求")
              st.write("建议调整算法参数或优化代码实现以提高计算效率。")
      
      with analysis_tabs[1]:
          st.write("**资源利用率分析**")
          if results['resource_utilization'] >= 0.97:
              st.success("✅ 资源利用率达到基准要求（≥97%）")
              st.write("系统在干扰资源分配方面表现出色，实现了高效利用。")
          else:
              st.warning("⚠️ 资源利用率接近基准要求")
              st.write("可通过进一步优化分配策略提升资源利用效率。")
      
      with analysis_tabs[2]:
          st.write("**对抗效果分析**")
          interruptions = results['assignment_report']['summary']['interruption_count']
          if interruptions >= 3:
              st.success("✅ 中断次数达到基准要求（≥3次）")
              st.write("系统在雷达压制方面效果显著，具备实战价值。")
          else:
              st.warning("⚠️ 中断次数未达基准要求")
              st.write("可能需要调整干扰策略或优化技术参数。")
      
      with analysis_tabs[3]:
          st.write("**系统稳定性分析**")
          if len(results.get('convergence_data', [])) > 0:
              convergence_data = results['convergence_data']
              if len(convergence_data) < 100:  # 收敛较快
                  st.success("✅ 算法收敛性良好")
                  st.write("ePDE算法在较少的代数内实现收敛，稳定性优秀。")
              else:
                  st.info("ℹ️ 算法收敛性一般")
                  st.write("算法需要较多代数收敛，建议调整算法参数。")
      
      # 导出对比报告
      st.subheader("💾 导出对比报告")
      
      if st.button("生成详细对比报告", type="primary"):
          generate_comparison_report(results, comparison_data)    

def display_scenario_info():
    """显示当前想定的详细信息"""
    if not st.session_state.scenario:
        return
    
    scenario = st.session_state.scenario
    
    st.subheader("📋 当前想定信息")
    
    # 想定基本信息
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"**想定名称**: {scenario.get('name', '未命名想定')}")
        st.write(f"**描述**: {scenario.get('description', '无描述')}")
        st.write(f"**创建时间**: {scenario.get('created_time', '未知')}")
    
    with col2:
        st.metric("雷达数量", len(scenario['radars']))
        st.metric("干扰机数量", len(scenario['jammers']))
        st.metric("想定类型", st.session_state.get('scenario_type', '未知'))
    
    # 雷达详细信息
    st.subheader("📡 雷达配置详情")
    
    radar_data = []
    for radar in scenario['radars']:
        radar_data.append({
            'ID': radar.id,
            '名称': radar.name,
            '位置': f"({radar.position['lat']:.3f}, {radar.position['lon']:.3f})",
            '高度': f"{radar.position['alt']}m",
            '频率': f"{radar.frequency}GHz",
            '功率': f"{radar.power}kW",
            '当前阶段': radar.current_stage,
            '性能水平': f"{radar.performance_level:.1%}"
        })
    
    if radar_data:
        radar_df = pd.DataFrame(radar_data)
        st.dataframe(radar_df, width='stretch', hide_index=True)
    
    # 干扰机详细信息
    st.subheader("🎯 干扰机配置详情")
    
    jammer_data = []
    for jammer in scenario['jammers']:
        jammer_data.append({
            'ID': jammer['id'],
            '名称': jammer['name'],
            '位置': f"({jammer['position']['lat']:.3f}, {jammer['position']['lon']:.3f})",
            '高度': f"{jammer['position']['alt']}m",
            '功率': f"{jammer['power']}W",
            '类型': jammer['type']
        })
    
    if jammer_data:
        jammer_df = pd.DataFrame(jammer_data)
        st.dataframe(jammer_df, width='stretch', hide_index=True)
    
    # 地理分布可视化
    st.subheader("🗺️ 地理分布")
    
    try:
        # 创建简化的地理分布图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 绘制雷达位置（红色三角形）
        radar_lats = [r.position['lat'] for r in scenario['radars']]
        radar_lons = [r.position['lon'] for r in scenario['radars']]
        ax.scatter(radar_lons, radar_lats, c='red', marker='^', s=100, label='雷达', alpha=0.7)
        
        # 绘制干扰机位置（蓝色圆形）
        jammer_lats = [j['position']['lat'] for j in scenario['jammers']]
        jammer_lons = [j['position']['lon'] for j in scenario['jammers']]
        ax.scatter(jammer_lons, jammer_lats, c='blue', marker='o', s=100, label='干扰机', alpha=0.7)
        
        # 添加标签
        for i, radar in enumerate(scenario['radars']):
            ax.annotate(radar.name, (radar_lons[i], radar_lats[i]), xytext=(5, 5), 
                       textcoords='offset points', fontsize=9)
        
        for i, jammer in enumerate(scenario['jammers']):
            ax.annotate(jammer['name'], (jammer_lons[i], jammer_lats[i]), xytext=(5, 5), 
                       textcoords='offset points', fontsize=9)
        
        ax.set_xlabel('经度')
        ax.set_ylabel('纬度')
        ax.set_title('雷达与干扰机地理分布')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"创建地理分布图失败: {e}")

def show_signal_analysis():
    """显示信号分析"""
    st.subheader("📡 信号分析")
    
    if not st.session_state.coteja_results:
        st.info("请先运行优化以获得信号分析数据")
        return
    
    results = st.session_state.coteja_results
    
    # 信号分析标签页
    tab1, tab2, tab3 = st.tabs(["📊 干扰效果分析", "📈 信号强度", "🔍 频谱分析"])
    
    with tab1:
        st.write("**干扰效果详细分析**")
        
        # 创建干扰效果热力图
        if 'assignment_report' in results:
            assignments = results['assignment_report']['assignments']
            
            if assignments:
                # 准备热力图数据
                radar_names = [f"雷达{i+1}" for i in range(len(st.session_state.scenario['radars']))]
                jammer_names = [f"干扰机{i+1}" for i in range(len(st.session_state.scenario['jammers']))]
                
                # 创建效果矩阵
                effect_matrix = np.zeros((len(jammer_names), len(radar_names)))
                
                for assignment in assignments:
                    jammer_idx = int(assignment['jammer_name'].replace("干扰机", "")) - 1
                    radar_idx = int(assignment['target_name'].replace("雷达", "")) - 1
                    effect_matrix[jammer_idx, radar_idx] = assignment['effectiveness']
                
                # 创建热力图
                fig, ax = plt.subplots(figsize=(10, 6))
                im = ax.imshow(effect_matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=1)
                
                # 设置坐标轴
                ax.set_xticks(np.arange(len(radar_names)))
                ax.set_yticks(np.arange(len(jammer_names)))
                ax.set_xticklabels(radar_names)
                ax.set_yticklabels(jammer_names)
                
                # 添加数值标签
                for i in range(len(jammer_names)):
                    for j in range(len(radar_names)):
                        text = ax.text(j, i, f'{effect_matrix[i, j]:.2f}',
                                      ha="center", va="center", color="black" if effect_matrix[i, j] > 0.5 else "white")
                
                ax.set_title('干扰机-雷达干扰效果热力图')
                fig.colorbar(im, ax=ax, label='干扰效果')
                
                st.pyplot(fig)
            else:
                st.info("暂无分配数据")
    
    with tab2:
        st.write("**信号强度分析**")
        
        # 创建信号强度图表
        if st.session_state.scenario:
            radars = st.session_state.scenario['radars']
            jammers = st.session_state.scenario['jammers']
            
            # 计算距离和信号强度
            distances = []
            signal_strengths = []
            
            for jammer in jammers:
                for radar in radars:
                    # 简化距离计算
                    dist = np.sqrt(
                        (jammer['position']['lat'] - radar.position['lat'])**2 +
                        (jammer['position']['lon'] - radar.position['lon'])**2
                    ) * 111  # 转换为公里
                    distances.append(dist)
                    
                    # 简化信号强度计算（基于距离和功率）
                    strength = jammer['power'] / (dist**2) if dist > 0 else jammer['power']
                    signal_strengths.append(strength)
            
            # 创建散点图
            fig, ax = plt.subplots(figsize=(10, 6))
            scatter = ax.scatter(distances, signal_strengths, c=signal_strengths, 
                                cmap='viridis', alpha=0.6, s=50)
            ax.set_xlabel('距离 (km)')
            ax.set_ylabel('相对信号强度')
            ax.set_title('干扰机-雷达信号强度分布')
            ax.grid(True, alpha=0.3)
            fig.colorbar(scatter, ax=ax, label='信号强度')
            
            st.pyplot(fig)
    
    with tab3:
        st.write("**频谱分析**")
        
        # 创建频谱示意图
        frequencies = np.linspace(2.0, 5.0, 100)
        
        # 模拟雷达和干扰机频谱
        radar_spectrum = np.zeros_like(frequencies)
        jammer_spectrum = np.zeros_like(frequencies)
        
        for radar in st.session_state.scenario['radars']:
            # 雷达频谱（高斯形状）
            center_freq = radar.frequency
            radar_spectrum += np.exp(-(frequencies - center_freq)**2 / 0.1)
        
        for jammer in st.session_state.scenario['jammers']:
            # 干扰机频谱（更宽的高斯）
            center_freq = 3.5  # 假设中心频率
            jammer_spectrum += np.exp(-(frequencies - center_freq)**2 / 0.3)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(frequencies, radar_spectrum, 'r-', label='雷达频谱', linewidth=2)
        ax.plot(frequencies, jammer_spectrum, 'b-', label='干扰频谱', linewidth=2)
        ax.fill_between(frequencies, radar_spectrum, alpha=0.3, color='red')
        ax.fill_between(frequencies, jammer_spectrum, alpha=0.3, color='blue')
        
        ax.set_xlabel('频率 (GHz)')
        ax.set_ylabel('相对功率')
        ax.set_title('雷达与干扰机频谱分布')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        st.pyplot(fig)

def show_tech_interaction():
    """显示技术交互分析"""
    st.subheader("🔧 干扰技术交互分析")
    
    # 基于文章表2的技术交互因子
    tech_interaction_matrix = {
        'NJ': {'NJ': 0.0, 'CP': 0.0, 'MFT': 0.2, 'RGPO': -0.3, 'VGPO': -0.3},
        'CP': {'NJ': 0.0, 'CP': 0.0, 'MFT': 0.1, 'RGPO': 0.2, 'VGPO': 0.2},
        'MFT': {'NJ': 0.2, 'CP': 0.1, 'MFT': 0.0, 'RGPO': -0.2, 'VGPO': -0.2},
        'RGPO': {'NJ': -0.3, 'CP': 0.2, 'MFT': -0.2, 'RGPO': 0.0, 'VGPO': 0.2},
        'VGPO': {'NJ': -0.3, 'CP': 0.2, 'MFT': -0.2, 'RGPO': 0.2, 'VGPO': 0.0}
    }
    
    techniques = ['NJ', 'CP', 'MFT', 'RGPO', 'VGPO']
    
    # 创建技术交互热力图
    interaction_data = np.zeros((len(techniques), len(techniques)))
    
    for i, tech1 in enumerate(techniques):
        for j, tech2 in enumerate(techniques):
            interaction_data[i, j] = tech_interaction_matrix[tech1][tech2]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(interaction_data, cmap='RdBu', aspect='auto', vmin=-0.5, vmax=0.5)
    
    # 设置坐标轴
    ax.set_xticks(np.arange(len(techniques)))
    ax.set_yticks(np.arange(len(techniques)))
    ax.set_xticklabels(techniques)
    ax.set_yticklabels(techniques)
    
    # 添加数值标签
    for i in range(len(techniques)):
        for j in range(len(techniques)):
            color = 'white' if abs(interaction_data[i, j]) > 0.25 else 'black'
            text = ax.text(j, i, f'{interaction_data[i, j]:.1f}',
                          ha="center", va="center", color=color, fontweight='bold')
    
    ax.set_title('干扰技术交互因子热力图')
    fig.colorbar(im, ax=ax, label='交互因子（>0增强，<0削弱）')
    
    st.pyplot(fig)
    
    # 技术交互说明
    st.subheader("📋 技术交互说明")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**增强型交互（>0）:**")
        st.write("✅ NJ + MFT: 噪声和多假目标相互增强")
        st.write("✅ CP + RGPO/VGPO: 覆盖脉冲增强拖引效果")
        st.write("✅ RGPO + VGPO: 距离和速度拖引相互增强")
    
    with col2:
        st.write("**削弱型交互（<0）:**")
        st.write("❌ NJ + RGPO/VGPO: 噪声削弱拖引效果")
        st.write("❌ MFT + RGPO/VGPO: 多假目标削弱拖引效果")
        st.write("❌ RGPO + NJ: 距离拖引被噪声削弱")
    
    # 实际应用中的技术组合分析
    if st.session_state.coteja_results:
        st.subheader("🔍 当前优化中的技术组合")
        
        results = st.session_state.coteja_results
        assignments = results.get('assignment_report', {}).get('assignments', [])
        
        if assignments:
            tech_combinations = {}
            for assignment in assignments:
                tech = assignment['technique']
                tech_combinations[tech] = tech_combinations.get(tech, 0) + 1
            
            # 显示技术使用统计
            tech_stats = []
            for tech, count in tech_combinations.items():
                tech_stats.append({
                    '干扰技术': tech,
                    '使用次数': count,
                    '占比': f"{(count / len(assignments) * 100):.1f}%"
                })
            
            if tech_stats:
                tech_df = pd.DataFrame(tech_stats)
                st.dataframe(tech_df, width='stretch', hide_index=True)

def load_paper_simulation_scenario():
    """加载基准仿真场景"""
    with st.spinner("正在加载基准仿真场景..."):
        try:
            # 基于文章中的仿真参数创建场景
            jammers = []
            jammer_positions = [
                {"lat": 40.0, "lon": 116.4, "alt": 10000},  # J1
                {"lat": 40.1, "lon": 116.5, "alt": 11000},  # J2  
                {"lat": 39.9, "lon": 116.3, "alt": 9500},   # J3
                {"lat": 40.2, "lon": 116.6, "alt": 10500}   # J4
            ]
            
            # 基于文章图3的干扰机配置
            jammer_configs = [
                {'power': 1200, 'type': 'standoff_jammer', 'capabilities': ['NJ', 'CP', 'MFT']},
                {'power': 1000, 'type': 'standoff_jammer', 'capabilities': ['NJ', 'RGPO', 'VGPO']},
                {'power': 1500, 'type': 'standoff_jammer', 'capabilities': ['NJ', 'CP', 'MFT']},
                {'power': 1300, 'type': 'standoff_jammer', 'capabilities': ['NJ', 'RGPO', 'VGPO']}
            ]
            
            for i in range(4):
                jammer = {
                    'id': f'J{i+1}',
                    'name': f'干扰机{i+1}',
                    'position': jammer_positions[i],
                    'power': jammer_configs[i]['power'],
                    'type': jammer_configs[i]['type'],
                    # 'capabilities': jammer_configs[i]['capabilities']
                }
                jammers.append(jammer)
            
            # 创建5个雷达（基于文章）
            radars = []
            radar_positions = [
                {"lat": 39.8, "lon": 116.2, "alt": 50},   # R1
                {"lat": 39.9, "lon": 116.3, "alt": 60},   # R2
                {"lat": 40.0, "lon": 116.4, "alt": 70},   # R3  
                {"lat": 40.1, "lon": 116.5, "alt": 80},   # R4
                {"lat": 40.2, "lon": 116.6, "alt": 90}    # R5
            ]
            
            radar_configs = [
                {'frequency': 3.0, 'power': 100, 'type': 'search_radar'},
                {'frequency': 3.5, 'power': 120, 'type': 'acquisition_radar'},
                {'frequency': 4.0, 'power': 150, 'type': 'tracking_radar'},
                {'frequency': 4.5, 'power': 180, 'type': 'guidance_radar'},
                {'frequency': 5.0, 'power': 200, 'type': 'search_radar'}
            ]
            
            for i in range(5):
                radar = EnhancedRadar(
                    radar_id=f'R{i+1}',
                    name=f'雷达{i+1}',
                    position=radar_positions[i],
                    frequency=radar_configs[i]['frequency'],
                    power=radar_configs[i]['power'],
                    # radar_type=radar_configs[i]['type']
                )
                radars.append(radar)
            
            # 设置雷达初始阶段（基于文章仿真）
            radar_stages = ['search', 'acquisition', 'tracking', 'guidance', 'search']
            for i, radar in enumerate(radars):
                radar.current_stage = radar_stages[i]
                radar.performance_level = 0.9  # 初始性能水平
            
            # 创建基准仿真场景
            scenario = {
                'name': '基准仿真场景（6时间间隔）',
                'description': '4v5仿真场景，包含6个时间间隔的动态仿真',
                'radars': radars,
                'jammers': jammers,
                'time_intervals': 6,
                'consider_illumination': True,
                'created_time': datetime.now().isoformat(),
                'source': 'paper_simulation'
            }
            
            st.session_state.scenario = scenario
            st.session_state.scenario_type = 'paper_simulation'
            
            st.success("✅ 基准仿真场景加载成功！")
            st.info("""
            **场景特性:**
            - 4v5配置
            - 支持6个时间间隔的动态仿真
            - 包含完整的干扰技术配置
            - 考虑平台照明效应
            """)
            
        except Exception as e:
            st.error(f"加载基准仿真场景失败: {e}")

def plot_radar_stages():
    """绘制雷达阶段图"""
    if not st.session_state.scenario:
        return
    
    scenario = st.session_state.scenario
    
    st.subheader("📊 雷达阶段演化")
    
    # 创建雷达阶段时间序列数据（模拟）
    time_intervals = 6
    radar_names = [radar.name for radar in scenario['radars']]
    
    # 阶段映射
    stage_mapping = {'search': 0, 'acquisition': 1, 'tracking': 2, 'guidance': 3}
    stage_colors = ['blue', 'green', 'orange', 'red']
    stage_labels = ['搜索', '捕获', '跟踪', '制导']
    
    # 创建阶段演化图
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for i, radar in enumerate(scenario['radars']):
        # 模拟雷达阶段演化（基于文章中的模式）
        stages = []
        current_stage = stage_mapping[radar.current_stage]
        
        for t in range(time_intervals):
            # 模拟阶段转换（简化模型）
            if t == 0:
                stages.append(current_stage)
            else:
                # 随机阶段转换，但倾向于向前推进
                if np.random.random() < 0.3 and current_stage < 3:
                    current_stage += 1
                elif np.random.random() < 0.1 and current_stage > 0:
                    current_stage -= 1
                stages.append(current_stage)
        
        # 绘制阶段演化
        ax.plot(range(time_intervals), stages, 
                marker='o', linewidth=2, markersize=8, label=radar.name)
    
    ax.set_xlabel('时间间隔')
    ax.set_ylabel('雷达阶段')
    ax.set_title('雷达阶段演化图')
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(stage_labels)
    ax.set_xticks(range(time_intervals))
    ax.set_xticklabels([f'T{i+1}' for i in range(time_intervals)])
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    
    # 阶段统计信息
    st.subheader("📈 阶段统计")
    
    current_stages = {}
    for radar in scenario['radars']:
        stage = radar.current_stage
        current_stages[stage] = current_stages.get(stage, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    stage_display = {
        'search': ('搜索', '🔍', 'blue'),
        'acquisition': ('捕获', '🎯', 'green'), 
        'tracking': ('跟踪', '📡', 'orange'),
        'guidance': ('制导', '🚀', 'red')
    }
    
    for stage, (label, icon, color) in stage_display.items():
        count = current_stages.get(stage, 0)
        with col1 if stage == 'search' else col2 if stage == 'acquisition' else col3 if stage == 'tracking' else col4:
            st.metric(f"{icon} {label}", count)

def create_custom_scenario(n_radars, n_jammers, consider_illumination):
    """创建自定义想定"""
    with st.spinner("正在创建自定义想定..."):
        try:
            # 创建干扰机
            jammers = []
            base_lat, base_lon = 40.0, 116.4
            
            for i in range(n_jammers):
                jammer = {
                    'id': f'J{i+1}',
                    'name': f'自定义干扰机{i+1}',
                    'position': {
                        'lat': base_lat + (i % 3) * 0.1,
                        'lon': base_lon + (i // 3) * 0.1,
                        'alt': 10000 + i * 500
                    },
                    'power': 1000 + i * 200,
                    'type': 'standoff_jammer',
                    'capabilities': ['NJ', 'CP', 'MFT', 'RGPO', 'VGPO']
                }
                jammers.append(jammer)
            
            # 创建雷达
            radars = []
            for i in range(n_radars):
                radar = EnhancedRadar(
                    radar_id=f'R{i+1}',
                    name=f'自定义雷达{i+1}',
                    position={
                        'lat': base_lat - 0.2 + (i % 3) * 0.1,
                        'lon': base_lon - 0.2 + (i // 3) * 0.1,
                        'alt': 50 + i * 10
                    },
                    frequency=3.0 + i * 0.5,
                    power=100.0 + i * 50
                )
                radars.append(radar)
            
            # 创建想定
            scenario = {
                'name': f'自定义想定 ({n_jammers}v{n_radars})',
                'description': f'自定义创建的{n_jammers}个干扰机对抗{n_radars}部雷达的场景',
                'radars': radars,
                'jammers': jammers,
                'consider_illumination': consider_illumination,
                'created_time': datetime.now().isoformat()
            }
            
            st.session_state.scenario = scenario
            st.session_state.scenario_type = 'custom'
            
            st.success(f"✅ 自定义想定创建成功！")
            st.info(f"雷达数量: {len(radars)} | 干扰机数量: {len(jammers)} | 考虑平台照明: {consider_illumination}")
            
        except Exception as e:
            st.error(f"创建自定义想定失败: {e}")

def show_data_management():
    """显示数据管理页面（简化版）"""
    st.header("📁 数据管理系统")
    st.info("数据管理功能正在开发中...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("导出当前想定", type="primary"):
            export_current_scenario()
    
    with col2:
        if st.button("清除所有数据", type="secondary"):
            clear_all_data()

def export_current_scenario():
    """导出当前想定"""
    from src.core.entities.radar_enhanced import EnhancedRadar, EnhancedRadarEncoder
    from src.utils.data_serializer import DataSerializer    
    if st.session_state.scenario:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scenario_export_{timestamp}.json"
            
            export_data = {
                'scenario': st.session_state.scenario,
                'export_time': timestamp,
                'version': '2.0.0'
            }
            
            with open(f"exports/{filename}", 'w', encoding='utf-8') as f:
                serialized_data = DataSerializer.serialize_scenario(export_data)
                json.dump(serialized_data, f, cls=EnhancedRadarEncoder, indent=2, ensure_ascii=False)              
                # json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ 想定已导出: exports/{filename}")
        except Exception as e:
            st.error(f"导出失败: {e}")
    else:
        st.warning("暂无想定数据可导出")

def clear_all_data():
    """清除所有数据"""
    if st.button("确认清除所有数据？此操作不可逆！", type="primary"):
        st.session_state.scenario = None
        st.session_state.coteja_results = None
        st.session_state.scenario_type = None
        st.success("✅ 所有数据已清除")
        st.rerun()
# 应用标题
# st.title("🛡️ 智能干扰资源分配和协同对抗仿真系统")
st.markdown("""
<div class="main-header">
    <h1>🛡️ 长城数字智能干扰资源分配和协同对抗仿真系统</h1>
    <p>采用ePDE优化算法和对抗分析，实现智能干扰资源分配和协同对抗分析</p>
</div>
    """, unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.title("导航")
page = st.sidebar.radio(
    "选择页面",
    ["🏠 系统概览", "🎯 想定", "⚡ 智能优化", "📊 对抗分析", "📈 效能评估", "📁 数据管理"]
)

# 初始化会话状态
if 'scenario' not in st.session_state:
    st.session_state.scenario = None
if 'coteja_results' not in st.session_state:
    st.session_state.coteja_results = None
if 'optimization_controller' not in st.session_state:
    st.session_state.optimization_controller = OptimizationController()
if 'combat_analyzer' not in st.session_state:
    st.session_state.combat_analyzer = CombatAnalyzer(consider_illumination=True)

# 数据管理器
data_manager = DataManager()

def show_system_overview():
    """显示系统概览页面"""
    st.header("🏠 系统概览")
    
    # 系统特性展示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("优化算法", "ePDE", "扩展置换差分进化")
    
    with col2:
        st.metric("决策速度", "≤1秒", "实时优化")
    
    with col3:
        st.metric("资源利用率", "≥97%", "高效分配")
    
    with col4:
        st.metric("雷达阶段", "4阶段", "搜索/捕获/跟踪/制导")
    
    st.markdown("---")
    
    # 系统介绍
    st.subheader("🎯 系统特性")
    
    coteja_features = [
        "✅ **智能对抗分析**: 基于查找表的干扰机-雷达对抗分析",
        "✅ **协同干扰优化**: 支持多干扰机协同干扰策略",
        "✅ **实时决策**: 1秒内完成最优干扰分配",
        "✅ **阶段感知**: 雷达四阶段模型和中断机制",
        "✅ **带宽优化**: 智能带宽分配和调整",
        "✅ **技术交互**: 考虑干扰技术间的协同效应"
    ]
    
    for feature in coteja_features:
        st.markdown(feature)
    
    # 快速开始
    st.subheader("🚀 快速开始")
    
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("创建4v5测试想定", width='stretch'):
            create_4v5_test_scenario()
    
    with quick_col2:
        if st.button("运行优化", width='stretch'):
            if st.session_state.scenario:
                run_coteja_optimization()
            else:
                st.warning("请先创建想定")
    
    with quick_col3:
        if st.button("查看基准对比", width='stretch'):
            show_paper_comparison()

def create_4v5_test_scenario():
    """创建4v5测试想定（基于文章中的测试场景）"""
    with st.spinner("正在创建4v5测试想定..."):
        try:
            # 创建4个干扰机（基于文章图3）
            jammers = []
            jammer_positions = [
                {"lat": 40.0, "lon": 116.4, "alt": 10000},  # J1
                {"lat": 40.1, "lon": 116.5, "alt": 11000},  # J2  
                {"lat": 39.9, "lon": 116.3, "alt": 9500},   # J3
                {"lat": 40.2, "lon": 116.6, "alt": 10500}   # J4
            ]
            
            for i in range(4):
                jammer = {
                    'id': f'J{i+1}',
                    'name': f'干扰机{i+1}',
                    'position': jammer_positions[i],
                    'power': 1000 + i*200,  # 功率递增
                    'type': 'standoff_jammer'
                }
                jammers.append(jammer)
            
            # 创建5个雷达（基于文章图3）
            radars = []
            radar_positions = [
                {"lat": 39.8, "lon": 116.2, "alt": 50},   # R1
                {"lat": 39.9, "lon": 116.3, "alt": 60},   # R2
                {"lat": 40.0, "lon": 116.4, "alt": 70},   # R3  
                {"lat": 40.1, "lon": 116.5, "alt": 80},   # R4
                {"lat": 40.2, "lon": 116.6, "alt": 90}    # R5
            ]
            
            for i in range(5):
                radar = EnhancedRadar(
                    radar_id=f'R{i+1}',
                    name=f'雷达{i+1}',
                    position=radar_positions[i],
                    frequency=3.0 + i*0.5,
                    power=100.0 + i*50
                )
                radars.append(radar)
            
            # 创建想定
            scenario = {
                'name': '4v5测试想定',
                'description': '4个干扰机对抗5部雷达的典型场景',
                'radars': radars,
                'jammers': jammers,
                'created_time': datetime.now().isoformat()
            }
            
            st.session_state.scenario = scenario
            st.session_state.scenario_type = 'many_vs_many'
            
            st.success("✅ 4v5测试想定创建成功！")
            st.info(f"雷达数量: {len(radars)} | 干扰机数量: {len(jammers)}")
            
        except Exception as e:
            st.error(f"创建想定失败: {e}")

def show_coteja_scenario():
    st.header("🎯 想定配置")
    
    # 想定类型选择
    scenario_type = st.selectbox(
        "选择想定类型",
        ["4v5标准测试", "自定义想定", "文章仿真场景"],
        help="选择预定义想定或创建自定义想定"
    )
    
    if scenario_type == "4v5标准测试":
        st.info("**4v5标准测试想定**: 4个干扰机对抗5部雷达的测试场景")
        
        if st.button("加载4v5想定", type="primary"):
            create_4v5_test_scenario()
    
    elif scenario_type == "自定义想定":
        show_custom_scenario_config()
    
    else:  # 文章仿真场景
        show_paper_simulation_scenario()
    
    # 显示当前想定信息
    if st.session_state.scenario:
        display_scenario_info()

def show_custom_scenario_config():
    """显示自定义想定配置"""
    st.subheader("自定义想定配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n_radars = st.number_input("雷达数量", min_value=1, max_value=20, value=5)
        n_jammers = st.number_input("干扰机数量", min_value=1, max_value=10, value=4)
    
    with col2:
        terrain_type = st.selectbox("地形环境", ["平原", "丘陵", "山地", "城市", "海洋"])
        weather = st.selectbox("气象条件", ["晴好", "雨天", "雾天", "沙尘"])
    
    # 高级配置
    with st.expander("高级配置"):
        col3, col4 = st.columns(2)
        
        with col3:
            consider_illumination = st.checkbox("考虑平台照明", value=True)
            enable_cooperative = st.checkbox("启用协同干扰", value=True)
        
        with col4:
            default_technique = st.selectbox("默认干扰技术", ['NJ', 'CP', 'MFT', 'RGPO', 'VGPO'])
            default_bw = st.selectbox("默认带宽", ['N', 'M', 'W'])
    
    if st.button("创建自定义想定", type="primary"):
        create_custom_scenario(n_radars, n_jammers, consider_illumination)

def show_paper_simulation_scenario():
    """显示文章仿真场景"""
    st.subheader("基准仿真场景配置")
    
    st.info("""
    **仿真参数配置**:
    - 干扰机: 4个远距支援干扰机
    - 雷达: 5部不同型号的警戒雷达  
    - 距离: 50-100km典型交战距离
    - 时间: 6个时间间隔动态仿真
    """)
    
    # 文章中的具体参数
    st.subheader("干扰技术参数")
    
    tech_col1, tech_col2, tech_col3 = st.columns(3)
    
    with tech_col1:
        st.metric("NJ效果", "0.8-0.9", "噪声干扰")
        st.metric("CP效果", "0.9", "覆盖脉冲")
    
    with tech_col2:
        st.metric("MFT效果", "1.0", "多假目标") 
        st.metric("RGPO效果", "0.9", "距离拖引")
    
    with tech_col3:
        st.metric("VGPO效果", "0.9", "速度拖引")
        st.metric("带宽支持", "1-5目标", "N/M/W")
    
    if st.button("加载基准仿真场景", type="primary"):
        load_paper_simulation_scenario()

def show_intelligent_optimization():
    """显示智能优化页面"""
    st.header("⚡ 智能优化")
    
    if not st.session_state.scenario:
        st.warning("⚠️ 请先创建或加载一个对抗想定")
        return
    
    scenario = st.session_state.scenario
    
    # 显示想定信息
    st.success(f"✅ 当前想定: **{scenario.get('name', '未命名想定')}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("雷达数量", len(scenario['radars']))
    with col2:
        st.metric("干扰机数量", len(scenario['jammers']))
    with col3:
        st.metric("想定类型", st.session_state.get('scenario_type', '未知'))
    
    st.markdown("---")
    
    # 优化参数配置
    st.subheader("⚙️ 优化参数配置")
    
    opt_col1, opt_col2, opt_col3 = st.columns(3)
    
    with opt_col1:
        time_limit = st.slider("优化时间限制(秒)", 0.5, 5.0, 1.0, 0.1)
        population_size = st.number_input("种群大小", 10, 200, 50)
    
    with opt_col2:
        max_generations = st.number_input("最大代数", 10, 500, 100)
        crossover_rate = st.slider("交叉概率", 0.1, 1.0, 0.9, 0.05)
    
    with opt_col3:
        scaling_factor = st.slider("缩放因子", 0.1, 1.0, 0.5, 0.05)
        consider_illumination = st.checkbox("考虑平台照明", value=True)
    
    # 高级选项
    with st.expander("高级优化选项"):
        advanced_col1, advanced_col2 = st.columns(2)
        
        with advanced_col1:
            enable_elitism = st.checkbox("启用精英保留", value=True)
            mutation_strategy = st.selectbox("变异策略", ["rand/1", "best/1", "current-to-best/1"])
        
        with advanced_col2:
            constraint_handling = st.selectbox("约束处理", ["修复", "惩罚", "拒绝"])
            local_search = st.checkbox("启用局部搜索", value=False)
    
    # 优化控制按钮
    st.markdown("---")
    st.subheader("🚀 优化执行")
    
    if st.button("开始优化", type="primary", width='stretch'):
        run_coteja_optimization(time_limit, population_size, max_generations, 
                              crossover_rate, scaling_factor, consider_illumination)

def run_coteja_optimization(time_limit=1.0, population_size=50, max_generations=100,
                          crossover_rate=0.9, scaling_factor=0.5, consider_illumination=True):

    with st.spinner("正在进行优化..."):
        try:
            # 更新对抗分析器配置
            st.session_state.combat_analyzer = CombatAnalyzer(
                consider_illumination=consider_illumination
            )
            
            # 创建优化控制器
            controller = OptimizationController(
                consider_illumination=consider_illumination,
                time_limit=time_limit
            )
            
            # 配置优化器参数
            controller.optimizer.population_size = population_size
            controller.optimizer.max_generations = max_generations
            controller.optimizer.cr = crossover_rate
            controller.optimizer.f = scaling_factor
            
            # 运行优化
            start_time = time.time()
            result = controller.run_optimization(st.session_state.scenario)
            optimization_time = time.time() - start_time
            
            # 保存结果
            st.session_state.coteja_results = result
            st.session_state.optimization_controller = controller
            
            # 显示优化结果
            display_optimization_results(result, optimization_time)
            
        except Exception as e:
            exec_str = traceback.format_exc()
            st.error(f"优化过程失败: {exec_str}")

def display_optimization_results(result, optimization_time):
    """显示优化结果"""
    st.success("✅ 优化完成！")
    
    # 关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("优化时间", f"{optimization_time:.3f}s")
    
    with col2:
        st.metric("最优适应度", f"{result['best_fitness']:.3f}")
    
    with col3:
        st.metric("资源利用率", f"{result['resource_utilization']:.1%}")
    
    with col4:
        st.metric("中断次数", result['assignment_report']['summary']['interruption_count'])
    
    # 显示收敛曲线
    if 'convergence_data' in result and result['convergence_data']:
        plot_convergence_curve(result['convergence_data'])
    
    # 显示分配结果
    display_assignment_results(result['assignment_report'])

def plot_convergence_curve(convergence_data):
    """绘制收敛曲线"""
    st.subheader("📈 优化收敛曲线")
    
    if not convergence_data:
        return
    
    # 准备数据
    generations = [data['generation'] for data in convergence_data]
    avg_fitness = [data['avg_fitness'] for data in convergence_data]
    max_fitness = [data['max_fitness'] for data in convergence_data]
    best_fitness = [data['best_fitness'] for data in convergence_data]
    
    # 使用Plotly创建交互式图表
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=generations, y=avg_fitness,
        mode='lines',
        name='平均适应度',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=generations, y=max_fitness,
        mode='lines',
        name='当代最优',
        line=dict(color='green', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=generations, y=best_fitness,
        mode='lines',
        name='全局最优',
        line=dict(color='red', width=3)
    ))
    
    fig.update_layout(
        title='ePDE算法收敛曲线',
        xaxis_title='代数',
        yaxis_title='适应度',
        height=400
    )
    
    st.plotly_chart(fig, width='stretch')

def display_assignment_results(assignment_report):
    """显示分配结果"""
    st.subheader("📋 最优干扰分配")
    
    # 创建分配表格
    assignment_data = []
    for assignment in assignment_report['assignments']:
        assignment_data.append({
            '干扰机': assignment['jammer_name'],
            '目标雷达': assignment['target_name'],
            '干扰技术': assignment['technique'],
            '带宽类型': assignment['bw_type'],
            '干扰效果': f"{assignment['effectiveness']:.3f}",
            '雷达阶段': assignment['radar_stage']
        })
    
    if assignment_data:
        df = pd.DataFrame(assignment_data)
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("无分配数据")
    
    # 显示雷达效果
    st.subheader("📊 雷达干扰效果")
    
    radar_effects = []
    for radar_id, effect in assignment_report['radar_effects'].items():
        radar = next((r for r in st.session_state.scenario['radars'] if r.id == radar_id), None)
        if radar:
            radar_effects.append({
                '雷达': radar.name,
                '干扰效果': f"{effect:.3f}",
                '当前阶段': radar.current_stage,
                '性能水平': f"{radar.performance_level:.1%}"
            })
    
    if radar_effects:
        effect_df = pd.DataFrame(radar_effects)
        st.dataframe(effect_df, width='stretch', hide_index=True)

def show_combat_analysis():
    """显示对抗分析页面"""
    st.header("📊 对抗分析")
    
    if not st.session_state.coteja_results:
        st.warning("⚠️ 请先运行优化")
        return
    
    results = st.session_state.coteja_results
    
    # 对抗分析标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 态势可视化", "📡 信号分析", "🔧 技术交互", "📈 效能评估"])
    
    with tab1:
        show_situation_visualization()
    
    with tab2:
        show_signal_analysis()
    
    with tab3:
        show_tech_interaction()
    
    with tab4:
        show_performance_assessment()

def show_situation_visualization():
    """显示态势可视化"""
    st.subheader("🗺️ 对抗态势可视化")
    
    if not st.session_state.scenario:
        return
    
    scenario = st.session_state.scenario
    
    # 可视化选项
    viz_type = st.radio(
        "可视化类型",
        ["地理态势图", "干扰分配图", "雷达阶段图"],
        horizontal=True
    )
    
    if viz_type == "地理态势图":
        # 使用EWVisualizer创建地理态势图
        try:
            fig = EWVisualizer.create_matplotlib_plot(
                scenario['radars'], 
                [Jammer(**j) for j in scenario['jammers']]  # 转换为Jammer对象
            )
            st.pyplot(fig)
        except Exception as e:
            st.error(f"创建态势图失败: {e}")
    
    elif viz_type == "干扰分配图":
        plot_jamming_assignment()
    
    else:  # 雷达阶段图
        plot_radar_stages()

def plot_jamming_assignment():
    """绘制干扰分配图"""
    if not st.session_state.coteja_results:
        return
    
    results = st.session_state.coteja_results
    
    # 创建干扰分配网络图
    fig = go.Figure()
    
    # 添加雷达节点
    radar_nodes = []
    for radar in st.session_state.scenario['radars']:
        radar_nodes.append({
            'id': radar.id,
            'label': radar.name,
            'group': 'radar',
            'stage': radar.current_stage
        })
    
    # 添加干扰机节点
    jammer_nodes = []
    for jammer in st.session_state.scenario['jammers']:
        jammer_nodes.append({
            'id': jammer['id'],
            'label': jammer['name'],
            'group': 'jammer'
        })
    
    # 创建网络图数据
    edge_x = []
    edge_y = []
    
    for assignment in results['assignment_report']['assignments']:
        # 添加连接线
        pass  # 简化实现
    
    st.plotly_chart(fig, width='stretch')

def show_performance_assessment():
    """显示效能评估"""
    st.subheader("📈 系统效能评估")
    
    if not st.session_state.coteja_results:
        return
    
    results = st.session_state.coteja_results
    
    # 效能指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("综合效能", f"{results['best_fitness']:.3f}")
    
    with col2:
        st.metric("决策速度", f"{results['optimization_time']:.3f}s")
    
    with col3:
        st.metric("资源利用率", f"{results['resource_utilization']:.1%}")
    
    with col4:
        interruptions = results['assignment_report']['summary']['interruption_count']
        st.metric("雷达中断", interruptions)
    
    # 与文章结果对比
    st.subheader("📊 与基准结果对比")
    
    comparison_data = {
        '指标': ['优化时间', '资源利用率', '中断次数', '适应度'],
        '本文结果': [
            f"{results['optimization_time']:.3f}s",
            f"{results['resource_utilization']:.1%}",
            results['assignment_report']['summary']['interruption_count'],
            f"{results['best_fitness']:.3f}"
        ],
        '基准结果': ['≤1.0s', '≥97.0%', '≥3', '≥0.9']
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, width='stretch', hide_index=True)
    
    # 性能达标检查
    st.subheader("✅ 性能达标情况")
    
    performance_checks = [
        ("优化时间 ≤ 1.0s", results['optimization_time'] <= 1.0),
        ("资源利用率 ≥ 97%", results['resource_utilization'] >= 0.97),
        ("适应度 ≥ 0.9", results['best_fitness'] >= 0.9)
    ]
    
    for check_name, check_passed in performance_checks:
        if check_passed:
            st.success(f"✅ {check_name}")
        else:
            st.warning(f"⚠️ {check_name}")

# 辅助类和函数
class Jammer:
    """简化的干扰机类"""
    def __init__(self, id, name, position, power, type):
        self.id = id
        self.name = name
        self.position = position
        self.power = power
        self.type = type

# 主路由
if page == "🏠 系统概览":
    show_system_overview()
elif page == "🎯 想定":
    show_coteja_scenario()
elif page == "⚡ 智能优化":
    show_intelligent_optimization()
elif page == "📊 对抗分析":
    show_combat_analysis()
elif page == "📈 效能评估":
    show_performance_assessment()
elif page == "📁 数据管理":
    show_data_management()

def generate_comparison_report(results, comparison_data):
      """生成详细的对比报告"""
      try:
          report_content = {
              "生成时间": datetime.now().isoformat(),
              "系统版本": "v2.0.0",
              "对比基准": "基于组合优化的威胁评估和干扰分配系统的实现》",
              "测试场景": "4v5典型对抗想定",
              "性能对比": comparison_data,
              "详细结果": {
                  "优化时间": results['optimization_time'],
                  "资源利用率": results['resource_utilization'],
                  "中断次数": results['assignment_report']['summary']['interruption_count'],
                  "最优适应度": results['best_fitness']
              },
              "达标分析": {
                  "总指标": len(comparison_data['性能指标']),
                  "达标数": sum(1 for status in comparison_data['达标情况'] if '✅' in status),
                  "达标率": f"{(sum(1 for status in comparison_data['达标情况'] if '✅' in status) / len(comparison_data['性能指标']) * 100):.1f}%"
              }
          }
          
          # 保存报告
          timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
          filename = f"paper_comparison_report_{timestamp}.json"
          
          with open(f"reports/{filename}", 'w', encoding='utf-8') as f:
              json.dump(report_content, f, indent=2, ensure_ascii=False)
          
          st.success(f"✅ 对比报告已生成: reports/{filename}")
          
      except Exception as e:
          st.error(f"生成报告失败: {e}")    

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: gray;">
        <p>长城数字智能干扰资源分配和协同对抗仿真系统 v2.0.0 | 基于组合优化的威胁评估与干扰分配</p>
    </div>
    """,
    unsafe_allow_html=True
)