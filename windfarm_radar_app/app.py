"""
风电场对雷达目标探测影响评估系统
多页面Streamlit应用 - 主入口文件
"""

import streamlit as st

# 设置页面配置
st.set_page_config(
    page_title="风电场雷达影响评估系统",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.8rem;
        color: #1E40AF;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 0.5rem;
    }
    .info-card {

        border-left: 4px solid #3B82F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-card {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-card {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<h1 class="main-header">🌬️ 风电场对雷达目标探测影响评估系统</h1>', unsafe_allow_html=True)

# 应用介绍
st.markdown("""
<div class="info-card">
    <h3>📊 系统概述</h3>
    <p>本系统提供了一套完整的风电场对雷达探测目标影响的评估工具，涵盖了从风电场建模、雷达参数配置、目标设置、探测分析到三维可视化的全流程分析。</p>
</div>
""", unsafe_allow_html=True)

# 页面导航说明
st.markdown('<h2 class="section-header">🚀 快速开始</h2>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-card"><h3>1️⃣</h3><p>风电场建模</p></div>', unsafe_allow_html=True)
    st.markdown("配置风机参数、布局和地形条件")
    
with col2:
    st.markdown('<div class="metric-card"><h3>2️⃣</h3><p>雷达配置</p></div>', unsafe_allow_html=True)
    st.markdown("设置雷达参数、频段和探测模式")

with col3:
    st.markdown('<div class="metric-card"><h3>3️⃣</h3><p>分析评估</p></div>', unsafe_allow_html=True)
    st.markdown("进行影响评估和可视化分析")

# 功能模块介绍
st.markdown('<h2 class="section-header">🔧 功能模块</h2>', unsafe_allow_html=True)

# 创建功能模块的选项卡
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📐 风电场建模", 
    "📡 雷达参数", 
    "🎯 目标设置", 
    "📊 探测分析", 
    "👁️ 三维可视化"
])

with tab1:
    st.markdown("""
    ### 风电场建模模块
    
    **主要功能：**
    - 风机参数配置（高度、直径、间距）
    - 风电场布局设计（规则排列、自定义排列）
    - 地形高程建模
    - 风机类型选择（陆上/海上风机）
    
    **关键技术：**
    - 风机三维模型生成
    - 布局优化算法
    - 地形遮挡分析
    """)

with tab2:
    st.markdown("""
    ### 雷达参数配置模块
    
    **主要功能：**
    - 雷达类型选择（预警雷达、火控雷达、气象雷达）
    - 频段配置（S/C/X波段）
    - 功率和灵敏度设置
    - 扫描模式配置
    
    **关键技术：**
    - 雷达方程计算
    - 波束形成模拟
    - 信号处理模拟
    """)

with tab3:
    st.markdown("""
    ### 目标设置模块
    
    **主要功能：**
    - 目标类型选择（无人机、战斗机、客机）
    - 目标轨迹设置
    - 雷达截面积配置
    - 飞行参数设置
    
    **关键技术：**
    - 目标运动学模型
    - 雷达散射截面计算
    - 轨迹规划算法
    """)

with tab4:
    st.markdown("""
    ### 探测影响分析模块
    
    **主要功能：**
    - 视线遮挡分析
    - 信号衰减计算
    - 探测概率评估
    - 盲区分析
    
    **关键技术：**
    - 射线追踪算法
    - 传播损耗模型
    - 统计分析方法
    """)

with tab5:
    st.markdown("""
    ### 三维可视化模块
    
    **主要功能：**
    - 三维场景渲染
    - 实时动画显示
    - 交互式分析
    - 结果对比显示
    
    **关键技术：**
    - Plotly 3D可视化
    - 实时数据更新
    - 多视角切换
    """)

# 技术规格
st.markdown('<h2 class="section-header">📈 技术规格</h2>', unsafe_allow_html=True)

spec_col1, spec_col2 = st.columns(2)

with spec_col1:
    st.markdown("""
    **计算能力：**
    - 支持最多100个风机模拟
    - 同时追踪50个目标
    - 实时射线追踪计算
    
    **可视化能力：**
    - 交互式3D场景
    - 实时数据更新
    - 多视图对比
    
    **输出能力：**
    - 数据导出（CSV, JSON）
    - 报告生成（PDF）
    - 图表导出（PNG, SVG）
    """)

with spec_col2:
    st.markdown("""
    **支持的雷达频段：**
    - L波段 (1-2 GHz)
    - S波段 (2-4 GHz)
    - C波段 (4-8 GHz)
    - X波段 (8-12 GHz)
    
    **支持的目标类型：**
    - 无人机 (RCS: 0.01-0.5 m²)
    - 战斗机 (RCS: 1-10 m²)
    - 客机 (RCS: 10-100 m²)
    - 直升机 (RCS: 1-5 m²)
    """)

# 使用说明
st.markdown('<h2 class="section-header">📋 使用说明</h2>', unsafe_allow_html=True)

st.markdown("""
1. **从左边的侧边栏导航**到不同的功能页面
2. **按照页面顺序**依次配置参数：
   - 首先配置风电场参数
   - 然后配置雷达参数
   - 接着设置目标参数
   - 最后进行分析和可视化
3. **查看结果**：
   - 在分析页面查看数值结果
   - 在可视化页面查看3D效果
4. **导出数据**用于进一步分析
""")

# 侧边栏信息
with st.sidebar:
    st.markdown("## 🧭 导航")
    st.markdown("""
    ### 页面列表：
    1. **风电场建模** - 配置风机参数
    2. **雷达参数配置** - 设置雷达特性
    3. **目标设置** - 定义探测目标
    4. **探测影响分析** - 计算结果
    5. **三维可视化** - 3D可视化展示
    
    ### 快速操作：
    - 点击右上角的"×"可关闭侧边栏
    - 使用浏览器的刷新按钮重置应用
    - 按F11键可进入全屏模式
    """)
    
    st.markdown("---")
    
    st.markdown("## ℹ️ 系统信息")
    st.markdown("""
    **版本:** 1.0.0
    **更新日期:** 2026年1月
    **开发者:** 雷达影响评估团队
    
    **技术支持:**
    - 邮箱: support@radar-windfarm.com
    - 电话: 400-123-4567
    """)
    
    st.markdown("---")
    
    # 系统状态
    st.markdown("## 🖥️ 系统状态")
    st.progress(100, text="系统就绪")
    
    if st.button("🔄 重置所有设置", type="secondary"):
        st.success("设置已重置！")
        st.rerun()

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 0.9rem;">
    <p>风电场对雷达目标探测影响评估系统 © 2026 | 版本 1.0.0</p>
    <p>本系统用于长城数字科研和工程评估目的，结果仅供参考</p>
</div>
""", unsafe_allow_html=True)
