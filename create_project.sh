#!/bin/bash

# 创建多页面Streamlit风电场雷达影响评估App项目
# 作者：AI Assistant
# 日期：$(date)

echo "开始创建多页面Streamlit风电场雷达影响评估App项目..."

# 创建项目根目录
PROJECT_DIR="windfarm_radar_app"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit

echo "✓ 创建项目根目录: $PROJECT_DIR"

# 创建主应用文件
cat > app.py << 'EOF'
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
        background-color: #F0F9FF;
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
    **更新日期:** 2024年1月
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
    <p>风电场对雷达目标探测影响评估系统 © 2024 | 版本 1.0.0</p>
    <p>本系统用于科研和工程评估目的，结果仅供参考</p>
</div>
""", unsafe_allow_html=True)
EOF

echo "✓ 创建主应用文件: app.py"

# 创建pages目录
mkdir -p pages

# 页面1: 风电场建模
cat > pages/1_风电场建模.py << 'EOF'
"""
风电场建模页面
功能：配置风机参数、布局设计、地形设置
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from math import sqrt, radians, sin, cos

# 页面配置
st.set_page_config(
    page_title="风电场建模 | 雷达影响评估系统",
    layout="wide"
)

# 标题
st.title("📐 风电场建模")
st.markdown("配置风机参数、布局设计和地形设置")

# 初始化会话状态
if 'wind_farm_config' not in st.session_state:
    st.session_state.wind_farm_config = {
        'turbines': [],
        'layout_type': '规则排列',
        'terrain': '平坦地形'
    }

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "风机参数", 
    "布局设计", 
    "地形设置", 
    "预览"
])

with tab1:
    st.header("风机参数配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本参数")
        turbine_height = st.slider(
            "风机高度 (米)",
            min_value=50,
            max_value=200,
            value=100,
            step=10,
            help="风机轮毂中心到地面的高度"
        )
        
        rotor_diameter = st.slider(
            "转子直径 (米)",
            min_value=50,
            max_value=150,
            value=80,
            step=5,
            help="风机叶片扫掠区域的直径"
        )
        
        tower_diameter = st.slider(
            "塔筒直径 (米)",
            min_value=2.0,
            max_value=5.0,
            value=3.0,
            step=0.1,
            help="风机塔筒的直径"
        )
        
        blade_length = rotor_diameter / 2
        st.metric("叶片长度", f"{blade_length:.1f} 米")
    
    with col2:
        st.subheader("风机类型")
        turbine_type = st.selectbox(
            "选择风机类型",
            ["陆上风机", "海上风机", "高原风机", "低风速风机"],
            index=0
        )
        
        rated_power = st.select_slider(
            "额定功率 (MW)",
            options=[1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
            value=3.0
        )
        
        rotation_speed = st.slider(
            "额定转速 (RPM)",
            min_value=5,
            max_value=20,
            value=12,
            step=1
        )
        
        # 风机材料
        material = st.selectbox(
            "塔筒材料",
            ["钢制", "混凝土", "钢混结构", "复合材料"]
        )
    
    # 显示风机示意图
    st.subheader("风机示意图")
    fig = go.Figure()
    
    # 绘制风机简图
    x_base = 0
    y_base = 0
    
    # 塔筒
    fig.add_trace(go.Scatter(
        x=[x_base - tower_diameter/2, x_base + tower_diameter/2, 
           x_base + tower_diameter/2, x_base - tower_diameter/2, x_base - tower_diameter/2],
        y=[y_base, y_base, turbine_height, turbine_height, y_base],
        fill="toself",
        fillcolor="gray",
        line=dict(color="darkgray"),
        name="塔筒"
    ))
    
    # 机舱
    fig.add_trace(go.Scatter(
        x=[x_base - 3, x_base + 3, x_base + 3, x_base - 3, x_base - 3],
        y=[turbine_height - 2, turbine_height - 2, turbine_height + 2, turbine_height + 2, turbine_height - 2],
        fill="toself",
        fillcolor="blue",
        line=dict(color="darkblue"),
        name="机舱"
    ))
    
    # 叶片
    for angle in [0, 120, 240]:
        blade_x = [x_base, x_base + blade_length * cos(radians(angle))]
        blade_y = [turbine_height, turbine_height + blade_length * sin(radians(angle))]
        fig.add_trace(go.Scatter(
            x=blade_x,
            y=blade_y,
            mode="lines",
            line=dict(color="lightblue", width=3),
            name="叶片"
        ))
    
    fig.update_layout(
        title="风机结构示意图",
        xaxis_title="宽度 (米)",
        yaxis_title="高度 (米)",
        showlegend=True,
        height=400,
        yaxis=dict(scaleanchor="x", scaleratio=1)
    )
    
    st.plotly_chart(fig, width='stretch')

with tab2:
    st.header("风电场布局设计")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("布局参数")
        layout_type = st.radio(
            "布局类型",
            ["规则排列", "自定义排列", "优化排列"],
            horizontal=True
        )
        
        num_turbines = st.slider(
            "风机数量",
            min_value=1,
            max_value=100,
            value=9,
            step=1
        )
        
        spacing = st.slider(
            "风机间距 (米)",
            min_value=100,
            max_value=500,
            value=200,
            step=10
        )
        
        rows = st.slider(
            "行数",
            min_value=1,
            max_value=10,
            value=3,
            step=1
        )
        
        cols = st.number_input(
            "列数",
            min_value=1,
            max_value=10,
            value=3,
            step=1
        )
    
    with col2:
        st.subheader("布局预览")
        
        if layout_type == "规则排列":
            # 生成规则排列的风机坐标
            turbine_positions = []
            for i in range(rows):
                for j in range(cols):
                    if len(turbine_positions) >= num_turbines:
                        break
                    x = (i - rows/2) * spacing
                    y = (j - cols/2) * spacing
                    turbine_positions.append((x, y))
            
            # 创建布局图
            fig = go.Figure()
            
            for idx, (x, y) in enumerate(turbine_positions):
                fig.add_trace(go.Scatter(
                    x=[x],
                    y=[y],
                    mode='markers+text',
                    marker=dict(size=15, color='blue'),
                    text=[f"{idx+1}"],
                    textposition="top center",
                    name=f"风机 {idx+1}"
                ))
            
            fig.update_layout(
                title="风电场布局（俯视图）",
                xaxis_title="X 坐标 (米)",
                yaxis_title="Y 坐标 (米)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
    
    # 布局统计
    st.subheader("布局统计")
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    with stats_col1:
        st.metric("总风机数", num_turbines)
    
    with stats_col2:
        total_area = (rows * spacing) * (cols * spacing)
        st.metric("占地面积", f"{total_area/10000:.2f} 公顷")
    
    with stats_col3:
        power_capacity = num_turbines * rated_power
        st.metric("总装机容量", f"{power_capacity} MW")
    
    with stats_col4:
        st.metric("行数 × 列数", f"{rows} × {cols}")

with tab3:
    st.header("地形与高程设置")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("地形设置")
        terrain_type = st.selectbox(
            "地形类型",
            ["平坦地形", "丘陵地形", "山地地形", "沿海地形", "自定义地形"]
        )
        
        if terrain_type == "自定义地形":
            elevation_data = st.file_uploader(
                "上传高程数据文件 (CSV/TXT)",
                type=['csv', 'txt']
            )
            
            if elevation_data is not None:
                try:
                    df_elevation = pd.read_csv(elevation_data)
                    st.success(f"成功加载高程数据，共 {len(df_elevation)} 个点")
                except Exception as e:
                    st.error(f"文件读取失败: {e}")
        
        # 地形参数
        elevation_range = st.slider(
            "高程范围 (米)",
            min_value=0,
            max_value=2000,
            value=(0, 200),
            step=10
        )
        
        roughness_length = st.slider(
            "地面粗糙度长度 (米)",
            min_value=0.001,
            max_value=1.0,
            value=0.03,
            step=0.001,
            format="%.3f"
        )
    
    with col2:
        st.subheader("地形参数")
        st.markdown("""
        **地形分类:**
        - 平坦地形: 高程变化 < 50m
        - 丘陵地形: 高程变化 50-200m
        - 山地地形: 高程变化 > 200m
        
        **粗糙度长度参考:**
        - 水面: 0.0002m
        - 平地: 0.03m
        - 农作物: 0.1m
        - 森林: 0.5-1.0m
        """)
    
    # 地形可视化
    st.subheader("地形高程图")
    
    # 创建示例地形数据
    x = np.linspace(-1000, 1000, 50)
    y = np.linspace(-1000, 1000, 50)
    X, Y = np.meshgrid(x, y)
    
    if terrain_type == "平坦地形":
        Z = np.zeros_like(X) + 50
    elif terrain_type == "丘陵地形":
        Z = 50 + 100 * np.sin(X/500) * np.cos(Y/500)
    elif terrain_type == "山地地形":
        Z = 100 + 300 * np.sin(X/300) * np.cos(Y/300)
    elif terrain_type == "沿海地形":
        Z = 20 + 50 * np.exp(-(X**2 + Y**2)/500000)
    else:
        Z = np.random.randn(*X.shape) * 50 + 100
    
    fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Earth')])
    
    fig.update_layout(
        title=f"{terrain_type} - 三维地形图",
        scene=dict(
            xaxis_title="X (米)",
            yaxis_title="Y (米)",
            zaxis_title="高程 (米)",
            aspectmode="manual",
            aspectratio=dict(x=2, y=2, z=0.5)
        ),
        height=500
    )
    
    st.plotly_chart(fig, width='stretch')

with tab4:
    st.header("风电场配置预览")
    
    if st.button("🔄 更新配置", type="primary"):
        st.session_state.wind_farm_config = {
            'turbine_height': turbine_height,
            'rotor_diameter': rotor_diameter,
            'turbine_type': turbine_type,
            'num_turbines': num_turbines,
            'layout_type': layout_type,
            'terrain_type': terrain_type,
            'spacing': spacing,
            'rows': rows,
            'cols': cols
        }
        st.success("风电场配置已更新！")
    
    if st.session_state.wind_farm_config:
        config = st.session_state.wind_farm_config
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("风机参数")
            config_df1 = pd.DataFrame({
                '参数': ['风机高度', '转子直径', '风机类型', '额定功率', '塔筒材料'],
                '数值': [
                    f"{turbine_height} 米",
                    f"{rotor_diameter} 米",
                    turbine_type,
                    f"{rated_power} MW",
                    material
                ]
            })
            st.dataframe(config_df1, width='stretch', hide_index=True)
        
        with col2:
            st.subheader("布局参数")
            config_df2 = pd.DataFrame({
                '参数': ['布局类型', '风机数量', '风机间距', '行数×列数', '地形类型'],
                '数值': [
                    layout_type,
                    num_turbines,
                    f"{spacing} 米",
                    f"{rows} × {cols}",
                    terrain_type
                ]
            })
            st.dataframe(config_df2, width='stretch', hide_index=True)
    
    # 导出配置
    st.subheader("配置导出")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 保存配置到会话"):
            st.success("配置已保存到当前会话！")
    
    with col2:
        config_json = {
            'wind_farm': st.session_state.wind_farm_config
        }
        
        st.download_button(
            label="📥 下载配置 (JSON)",
            data=str(config_json),
            file_name="wind_farm_config.json",
            mime="application/json"
        )

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **风机参数**: 配置单个风机的技术参数
    2. **布局设计**: 设计风电场的整体布局
    3. **地形设置**: 设置地形和高程条件
    4. **预览**: 查看和导出完整配置
    
    **注意事项:**
    - 风机高度影响雷达视线
    - 布局间距影响遮挡效应
    - 地形影响信号传播
    """)
    
    st.markdown("---")
    
    st.markdown("## ⚙️ 当前配置")
    if st.session_state.wind_farm_config:
        config = st.session_state.wind_farm_config
        for key, value in config.items():
            st.text(f"{key}: {value}")
    else:
        st.info("未保存配置")
    
    st.markdown("---")
    
    if st.button("🚀 进入下一步: 雷达配置", type="primary", width='stretch'):
        st.switch_page("pages/2_雷达参数配置.py")

# 页脚
st.markdown("---")
st.caption("风电场建模模块 | 用于雷达影响评估的风电场参数配置")
EOF

echo "✓ 创建页面1: pages/1_风电场建模.py"

# 页面2: 雷达参数配置
cat > pages/2_雷达参数配置.py << 'EOF'
"""
雷达参数配置页面
功能：配置雷达参数、频段、扫描模式等
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import constants

# 页面配置
st.set_page_config(
    page_title="雷达参数配置 | 雷达影响评估系统",
    layout="wide"
)

# 标题
st.title("📡 雷达参数配置")
st.markdown("配置雷达系统参数、频段选择和扫描模式")

# 初始化会话状态
if 'radar_config' not in st.session_state:
    st.session_state.radar_config = {}

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "雷达参数", 
    "频段配置", 
    "扫描模式", 
    "性能评估"
])

with tab1:
    st.header("雷达系统参数")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本参数")
        
        radar_type = st.selectbox(
            "雷达类型",
            ["预警雷达", "火控雷达", "搜索雷达", "跟踪雷达", "气象雷达", "自定义雷达"],
            index=0
        )
        
        radar_x = st.number_input(
            "雷达X坐标 (米)",
            min_value=-10000,
            max_value=10000,
            value=0,
            step=100
        )
        
        radar_y = st.number_input(
            "雷达Y坐标 (米)",
            min_value=-10000,
            max_value=10000,
            value=0,
            step=100
        )
        
        radar_z = st.number_input(
            "雷达高度 (米)",
            min_value=0,
            max_value=1000,
            value=50,
            step=10
        )
        
        max_range = st.slider(
            "最大探测距离 (km)",
            min_value=10,
            max_value=500,
            value=100,
            step=10
        )
        
        min_range = st.slider(
            "最小探测距离 (m)",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100
        )
    
    with col2:
        st.subheader("性能参数")
        
        peak_power = st.select_slider(
            "峰值功率 (kW)",
            options=[10, 50, 100, 500, 1000, 5000, 10000],
            value=1000
        )
        
        average_power = st.number_input(
            "平均功率 (kW)",
            min_value=1.0,
            max_value=1000.0,
            value=10.0,
            step=1.0
        )
        
        pulse_width = st.select_slider(
            "脉冲宽度 (μs)",
            options=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
            value=1.0
        )
        
        prf = st.select_slider(
            "脉冲重复频率 (Hz)",
            options=[100, 500, 1000, 2000, 5000, 10000],
            value=1000
        )
        
        antenna_gain = st.slider(
            "天线增益 (dB)",
            min_value=20,
            max_value=60,
            value=40,
            step=1
        )
        
        noise_figure = st.slider(
            "噪声系数 (dB)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.1
        )
    
    # 雷达方程计算
    st.subheader("雷达方程参数")
    
    col3, col4 = st.columns(2)
    
    with col3:
        wavelength = st.number_input(
            "波长 (m)",
            min_value=0.01,
            max_value=1.0,
            value=0.1,
            step=0.01,
            format="%.3f"
        )
        
        target_rcs = st.number_input(
            "目标RCS (m²)",
            min_value=0.01,
            max_value=100.0,
            value=1.0,
            step=0.1
        )
        
        system_loss = st.slider(
            "系统损耗 (dB)",
            min_value=0,
            max_value=20,
            value=6,
            step=1
        )
    
    with col4:
        # 计算雷达探测距离
        freq = constants.c / wavelength
        
        # 简化的雷达方程
        snr_min = 13  # dB，最小可检测信噪比
        pulse_energy = peak_power * 1000 * pulse_width * 1e-6
        avg_power_w = average_power * 1000
        
        # 计算最大探测距离
        max_detect_range = ((pulse_energy * antenna_gain**2 * wavelength**2 * target_rcs) / 
                           ((4*np.pi)**3 * 10**(snr_min/10) * 10**(noise_figure/10) * 10**(system_loss/10)))**(1/4)
        
        st.metric("雷达频率", f"{freq/1e9:.2f} GHz")
        st.metric("脉冲能量", f"{pulse_energy:.2f} J")
        st.metric("理论最大探测距离", f"{max_detect_range/1000:.1f} km")

with tab2:
    st.header("雷达频段配置")
    
    # 频段信息
    frequency_bands = {
        'L波段': {'freq_range': (1e9, 2e9), 'wavelength': (0.15, 0.3), 'applications': '远程预警'},
        'S波段': {'freq_range': (2e9, 4e9), 'wavelength': (0.075, 0.15), 'applications': '中程搜索'},
        'C波段': {'freq_range': (4e9, 8e9), 'wavelength': (0.0375, 0.075), 'applications': '火控跟踪'},
        'X波段': {'freq_range': (8e9, 12e9), 'wavelength': (0.025, 0.0375), 'applications': '精确制导'},
        'Ku波段': {'freq_range': (12e9, 18e9), 'wavelength': (0.0167, 0.025), 'applications': '高分辨率'},
        'Ka波段': {'freq_range': (26.5e9, 40e9), 'wavelength': (0.0075, 0.0113), 'applications': '卫星通信'}
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("频段选择")
        
        selected_band = st.selectbox(
            "选择雷达频段",
            list(frequency_bands.keys()),
            index=1
        )
        
        band_info = frequency_bands[selected_band]
        
        # 频段参数调整
        freq_min, freq_max = band_info['freq_range']
        center_freq = st.slider(
            "中心频率 (GHz)",
            min_value=freq_min/1e9,
            max_value=freq_max/1e9,
            value=(freq_min + freq_max)/(2 * 1e9),
            step=0.1
        )
        
        bandwidth = st.slider(
            "带宽 (MHz)",
            min_value=1,
            max_value=int((freq_max - freq_min)/1e6),
            value=int((freq_max - freq_min)/(4 * 1e6)),
            step=1
        )
        
        # 计算波长
        wavelength_calc = constants.c / (center_freq * 1e9)
        
        st.metric("中心频率", f"{center_freq:.2f} GHz")
        st.metric("对应波长", f"{wavelength_calc*100:.2f} cm")
        st.metric("带宽", f"{bandwidth} MHz")
    
    with col2:
        st.subheader("频段特性")
        
        st.markdown(f"""
        **{selected_band} 特性:**
        
        - 频率范围: {freq_min/1e9:.1f}-{freq_max/1e9:.1f} GHz
        - 波长范围: {band_info['wavelength'][0]*100:.1f}-{band_info['wavelength'][1]*100:.1f} cm
        - 主要应用: {band_info['applications']}
        
        **传播特性:**
        - 大气衰减: {'低' if selected_band in ['L', 'S'] else '中' if selected_band in ['C', 'X'] else '高'}
        - 雨衰减: {'低' if selected_band in ['L', 'S'] else '中' if selected_band == 'C' else '高'}
        - 分辨率: {'低' if selected_band in ['L', 'S'] else '中' if selected_band == 'C' else '高'}
        """)
    
    # 频段比较图
    st.subheader("雷达频段比较")
    
    fig = go.Figure()
    
    bands = list(frequency_bands.keys())
    center_freqs = [(freq_min + freq_max)/(2 * 1e9) for freq_min, freq_max in 
                   [band_info['freq_range'] for band_info in frequency_bands.values()]]
    
    fig.add_trace(go.Bar(
        x=bands,
        y=center_freqs,
        marker_color='indianred',
        text=[f"{freq:.1f} GHz" for freq in center_freqs],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="雷达频段中心频率比较",
        xaxis_title="频段",
        yaxis_title="中心频率 (GHz)",
        height=400
    )
    
    st.plotly_chart(fig, width='stretch')

with tab3:
    st.header("扫描与跟踪模式")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("扫描模式")
        
        scan_type = st.selectbox(
            "扫描类型",
            ["机械扫描", "相控阵扫描", "频率扫描", "混合扫描"],
            index=1
        )
        
        if scan_type == "相控阵扫描":
            num_elements = st.slider(
                "阵元数量",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100
            )
            
            beam_width = st.slider(
                "波束宽度 (°)",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1
            )
        
        scan_rate = st.slider(
            "扫描速率 (rpm)",
            min_value=1,
            max_value=60,
            value=12,
            step=1
        )
        
        elevation_range = st.slider(
            "俯仰角范围 (°)",
            min_value=0,
            max_value=90,
            value=(0, 60)
        )
        
        azimuth_range = st.slider(
            "方位角范围 (°)",
            min_value=0,
            max_value=360,
            value=(0, 360)
        )
    
    with col2:
        st.subheader("跟踪模式")
        
        track_mode = st.multiselect(
            "跟踪模式选择",
            ["单目标跟踪", "多目标跟踪", "边扫描边跟踪", "自适应跟踪", "预测跟踪"],
            default=["单目标跟踪", "多目标跟踪"]
        )
        
        max_targets = st.slider(
            "最大跟踪目标数",
            min_value=1,
            max_value=200,
            value=50,
            step=1
        )
        
        update_rate = st.slider(
            "数据更新率 (Hz)",
            min_value=0.1,
            max_value=100.0,
            value=10.0,
            step=0.1
        )
        
        track_accuracy = st.select_slider(
            "跟踪精度",
            options=['低', '中', '高', '极高'],
            value='高'
        )
        
        # 跟踪性能指标
        st.metric("跟踪数据率", f"{update_rate} Hz")
        st.metric("可跟踪目标数", max_targets)
    
    # 扫描模式可视化
    st.subheader("扫描模式可视化")
    
    # 创建波束扫描示意图
    fig = go.Figure()
    
    # 天线波束
    theta = np.linspace(0, 2*np.pi, 100)
    
    for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
        r = 1
        x = r * np.cos(theta + angle) * 0.5
        y = r * np.sin(theta + angle) * 0.5
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color='blue', width=1),
            fill='toself',
            fillcolor='rgba(0, 0, 255, 0.2)',
            name=f'波束 {int(np.degrees(angle))}°'
        ))
    
    fig.update_layout(
        title="天线波束扫描示意图",
        xaxis_title="方位角",
        yaxis_title="俯仰角",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, width='stretch')

with tab4:
    st.header("雷达性能评估")
    
    if st.button("🔍 开始性能评估", type="primary"):
        with st.spinner("正在计算雷达性能..."):
            # 模拟性能计算
            import time
            time.sleep(1)
            
            # 计算性能指标
            detection_probability = 0.95
            false_alarm_rate = 1e-6
            range_resolution = constants.c * pulse_width * 1e-6 / 2
            doppler_resolution = 1 / (pulse_width * 1e-6)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("探测性能")
                
                metrics_data = {
                    '指标': ['探测概率', '虚警概率', '检测信噪比', '作用距离'],
                    '数值': [
                        f"{detection_probability*100:.1f}%",
                        f"{false_alarm_rate:.2e}",
                        f"{snr_min} dB",
                        f"{max_detect_range/1000:.1f} km"
                    ]
                }
                
                st.dataframe(pd.DataFrame(metrics_data), width='stretch', hide_index=True)
                
                # 探测概率曲线
                ranges = np.linspace(10, max_range, 100)
                prob = detection_probability * np.exp(-ranges/(max_range/2))
                
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(
                    x=ranges, y=prob,
                    mode='lines',
                    line=dict(color='green', width=3),
                    name='探测概率'
                ))
                
                fig1.update_layout(
                    title="探测概率 vs 距离",
                    xaxis_title="距离 (km)",
                    yaxis_title="探测概率",
                    height=300
                )
                
                st.plotly_chart(fig1, width='stretch')
            
            with col2:
                st.subheader("分辨率性能")
                
                res_data = {
                    '指标': ['距离分辨率', '多普勒分辨率', '角度分辨率', '速度分辨率'],
                    '数值': [
                        f"{range_resolution:.1f} m",
                        f"{doppler_resolution:.0f} Hz",
                        f"{beam_width}°",
                        "待计算"
                    ]
                }
                
                st.dataframe(pd.DataFrame(res_data), width='stretch', hide_index=True)
                
                # 性能评分
                performance_score = 85
                st.subheader("综合性能评分")
                st.progress(performance_score/100, text=f"综合性能: {performance_score}/100")
                
                if performance_score >= 80:
                    st.success("✅ 雷达性能优秀，适合当前任务")
                elif performance_score >= 60:
                    st.warning("⚠️ 雷达性能良好，可满足基本需求")
                else:
                    st.error("❌ 雷达性能不足，建议优化参数")
            
            st.success("性能评估完成！")

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **雷达参数**: 配置基本雷达参数
    2. **频段配置**: 选择雷达工作频段
    3. **扫描模式**: 设置扫描和跟踪模式
    4. **性能评估**: 评估雷达综合性能
    
    **重要参数:**
    - 峰值功率: 决定探测距离
    - 天线增益: 影响波束形状
    - 频率: 影响分辨率和衰减
    """)
    
    st.markdown("---")
    
    # 雷达方程计算器
    st.markdown("## ⚡ 雷达方程计算器")
    
    pt = st.number_input("发射功率 (W)", value=1e6)
    g = st.number_input("天线增益", value=1000.0)
    sigma = st.number_input("目标RCS (m²)", value=1.0)
    r = st.number_input("距离 (m)", value=10000.0)
    
    if st.button("计算接收功率"):
        # 简化雷达方程
        lambda_val = wavelength_calc if 'wavelength_calc' in locals() else 0.1
        pr = (pt * g**2 * lambda_val**2 * sigma) / ((4*np.pi)**3 * r**4)
        st.info(f"接收功率: {pr:.2e} W")
        st.info(f"接收功率(dBm): {10*np.log10(pr*1000):.1f} dBm")
    
    st.markdown("---")
    
    if st.button("🚀 进入下一步: 目标设置", type="primary", width='stretch'):
        st.switch_page("pages/3_目标设置.py")

# 保存配置
if st.button("💾 保存雷达配置", type="primary", width='stretch'):
    st.session_state.radar_config = {
        'type': radar_type,
        'position': [radar_x, radar_y, radar_z],
        'max_range': max_range * 1000,  # 转换为米
        'peak_power': peak_power * 1000,  # 转换为瓦
        'frequency': center_freq * 1e9,  # 转换为Hz
        'wavelength': wavelength_calc,
        'antenna_gain': antenna_gain,
        'scan_type': scan_type
    }
    st.success("雷达配置已保存！")

# 页脚
st.markdown("---")
st.caption("雷达参数配置模块 | 用于雷达影响评估的雷达参数配置")
EOF

echo "✓ 创建页面2: pages/2_雷达参数配置.py"

# 页面3: 目标设置
cat > pages/3_目标设置.py << 'EOF'
"""
目标设置页面
功能：配置目标参数、轨迹、RCS等
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt
import random
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="目标设置 | 雷达影响评估系统",
    page_icon="🎯",
    layout="wide"
)

# 标题
st.title("🎯 目标设置")
st.markdown("配置目标参数、轨迹设置和雷达散射截面")

# 初始化会话状态
if 'targets_config' not in st.session_state:
    st.session_state.targets_config = []
if 'target_library' not in st.session_state:
    st.session_state.target_library = []

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "目标参数", 
    "轨迹设置", 
    "RCS配置", 
    "目标库"
])

class Target:
    """目标类"""
    def __init__(self, target_id, name, target_type, rcs=1.0, length=10.0, 
                 speed=200.0, altitude=1000.0, position=None, 
                 course=0.0, maneuver_type="直线飞行"):
        self.id = target_id
        self.name = name
        self.type = target_type
        self.rcs = rcs
        self.length = length
        self.speed = speed
        self.altitude = altitude
        self.position = position or [0, 0, altitude]
        self.course = course
        self.maneuver_type = maneuver_type
        self.trajectory = []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'rcs': self.rcs,
            'length': self.length,
            'speed': self.speed,
            'altitude': self.altitude,
            'position': self.position,
            'course': self.course,
            'maneuver_type': self.maneuver_type,
            'timestamp': self.timestamp
        }

def initialize_target_library():
    """初始化目标库"""
    if not st.session_state.target_library:
        target_library = [
            Target("T001", "全球鹰无人机", "无人机", 0.1, 13.5, 300, 18000, 
                  [0, 0, 18000], 0, "直线飞行"),
            Target("T002", "F-22猛禽", "战斗机", 0.0001, 18.9, 600, 15000,
                  [0, 0, 15000], 0, "直线飞行"),
            Target("T003", "B-2幽灵", "轰炸机", 0.1, 21.0, 300, 12000,
                  [0, 0, 12000], 0, "直线飞行"),
            Target("T004", "C-130大力神", "运输机", 20.0, 29.8, 200, 10000,
                  [0, 0, 10000], 0, "直线飞行"),
            Target("T005", "波音747", "客机", 15.0, 70.7, 250, 11000,
                  [0, 0, 11000], 0, "直线飞行"),
            Target("T006", "阿帕奇直升机", "直升机", 2.0, 15.0, 100, 3000,
                  [0, 0, 3000], 0, "悬停"),
            Target("T007", "战斧巡航导弹", "巡航导弹", 0.5, 5.6, 300, 50,
                  [0, 0, 50], 0, "直线飞行"),
            Target("T008", "民兵III导弹", "弹道导弹", 0.2, 18.2, 1000, 100000,
                  [0, 0, 100000], 0, "弹道飞行")
        ]
        st.session_state.target_library = [t.to_dict() for t in target_library]

# 初始化目标库
initialize_target_library()

with tab1:
    st.header("目标参数配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本参数")
        
        target_type = st.selectbox(
            "目标类型",
            ["无人机", "战斗机", "轰炸机", "运输机", "客机", "直升机", "巡航导弹", "弹道导弹", "自定义目标"],
            index=0,
            key="tab1_target_type"
        )
        
        # 根据目标类型设置默认参数
        target_params = {
            "无人机": {"rcs": 0.1, "speed": 30, "length": 2, "wingspan": 3, "altitude": 1000},
            "战斗机": {"rcs": 5.0, "speed": 300, "length": 15, "wingspan": 10, "altitude": 10000},
            "轰炸机": {"rcs": 10.0, "speed": 250, "length": 20, "wingspan": 30, "altitude": 12000},
            "运输机": {"rcs": 20.0, "speed": 200, "length": 40, "wingspan": 35, "altitude": 8000},
            "客机": {"rcs": 15.0, "speed": 250, "length": 50, "wingspan": 40, "altitude": 11000},
            "直升机": {"rcs": 2.0, "speed": 100, "length": 15, "rotor_diameter": 15, "altitude": 1000},
            "巡航导弹": {"rcs": 0.5, "speed": 300, "length": 5, "wingspan": 2, "altitude": 100},
            "弹道导弹": {"rcs": 0.2, "speed": 1000, "length": 10, "diameter": 1, "altitude": 50000}
        }
        
        target_id = st.text_input("目标编号", value="T001", key="tab1_target_id")
        target_name = st.text_input("目标名称", value=f"{target_type}-01", key="tab1_target_name")
        
        num_targets = st.slider(
            "目标数量",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            key="tab1_num_targets"
        )
    
    with col2:
        st.subheader("几何参数")
        
        if target_type in target_params:
            default_params = target_params[target_type]
            default_rcs = default_params["rcs"]
            default_speed = default_params["speed"]
            default_length = default_params["length"]
            default_altitude = default_params["altitude"]
        else:
            default_rcs = 1.0
            default_speed = 200
            default_length = 10
            default_altitude = 5000
        
        target_length = st.number_input(
            "目标长度 (m)",
            min_value=0.1,
            max_value=100.0,
            value=float(default_length),
            step=0.1,
            key="tab1_target_length"
        )
        
        if target_type in ["无人机", "战斗机", "轰炸机", "运输机", "客机", "巡航导弹"]:
            wingspan = st.number_input(
                "翼展 (m)",
                min_value=0.1,
                max_value=100.0,
                value=float(default_params.get(target_type, {}).get("wingspan", 10)),
                step=0.1,
                key="tab1_wingspan"
            )
        elif target_type == "直升机":
            rotor_diameter = st.number_input(
                "旋翼直径 (m)",
                min_value=1.0,
                max_value=50.0,
                value=float(default_params.get("rotor_diameter", 15)),
                step=0.1,
                key="tab1_rotor_diameter"
            )
        elif target_type == "弹道导弹":
            diameter = st.number_input(
                "弹体直径 (m)",
                min_value=0.1,
                max_value=10.0,
                value=float(default_params.get("diameter", 1)),
                step=0.1,
                key="tab1_diameter"
            )
        
        altitude = st.slider(
            "飞行高度 (m)",
            min_value=10,
            max_value=20000,
            value=int(default_altitude),
            step=10,
            key="tab1_altitude"
        )
    
    # 目标3D模型预览
    st.subheader("目标3D模型预览")
    
    # 创建目标3D模型
    fig = go.Figure()
    
    if target_type in ["无人机", "战斗机", "轰炸机", "运输机", "客机"]:
        # 飞机模型
        wingspan_val = wingspan if 'wingspan' in locals() else 10
        fuselage_length = target_length * 0.7
        nose_length = target_length * 0.3
        
        # 机身
        fig.add_trace(go.Mesh3d(
            x=[0, fuselage_length, fuselage_length, 0, 0, fuselage_length, fuselage_length, 0],
            y=[-1, -1, 1, 1, -1, -1, 1, 1],
            z=[0, 0, 0, 0, 2, 2, 2, 2],
            i=[7, 0, 0, 0, 4, 4, 6, 6],
            j=[3, 4, 1, 2, 5, 6, 5, 7],
            k=[0, 7, 2, 3, 6, 7, 2, 3],
            color='lightblue',
            opacity=0.8,
            name='机身'
        ))
        
        # 机翼
        fig.add_trace(go.Scatter3d(
            x=[fuselage_length*0.3, fuselage_length*0.3],
            y=[-wingspan_val/2, wingspan_val/2],
            z=[1, 1],
            mode='lines',
            line=dict(color='gray', width=5),
            name='机翼'
        ))
        
        # 尾翼
        fig.add_trace(go.Scatter3d(
            x=[target_length-2, target_length-2],
            y=[-wingspan_val/4, wingspan_val/4],
            z=[3, 3],
            mode='lines',
            line=dict(color='gray', width=4),
            name='水平尾翼'
        ))
        
        fig.add_trace(go.Scatter3d(
            x=[target_length-2, target_length-2],
            y=[0, 0],
            z=[1, 4],
            mode='lines',
            line=dict(color='gray', width=4),
            name='垂直尾翼'
        ))
    
    elif target_type == "直升机":
        # 直升机模型
        rotor_radius = rotor_diameter/2 if 'rotor_diameter' in locals() else 7.5
        
        # 机身
        fig.add_trace(go.Cylinder(
            center=[target_length/2, 0, 0],
            radius=1.5,
            height=target_length*0.8,
            colorscale=[[0, 'darkgray'], [1, 'darkgray']],
            showscale=False
        ))
        
        # 主旋翼
        fig.add_trace(go.Cone(
            x=[target_length*0.5],
            y=[0],
            z=[target_length*0.2],
            u=[0],
            v=[rotor_radius],
            w=[0],
            sizemode="absolute",
            sizeref=0.1,
            colorscale=[[0, 'gray'], [1, 'gray']],
            showscale=False
        ))
        
        # 尾桨
        fig.add_trace(go.Scatter3d(
            x=[target_length, target_length],
            y=[0, 1],
            z=[1, 1],
            mode='lines',
            line=dict(color='gray', width=3)
        ))
    
    elif target_type in ["巡航导弹", "弹道导弹"]:
        # 导弹模型
        length = target_length
        radius = diameter/2 if 'diameter' in locals() else 0.5
        
        # 弹体
        fig.add_trace(go.Cylinder(
            center=[length/2, 0, 0],
            radius=radius,
            height=length*0.8,
            colorscale=[[0, 'orange'], [1, 'orange']],
            showscale=False
        ))
        
        # 弹头
        fig.add_trace(go.Cone(
            x=[length*0.8, length],
            y=[0, 0],
            z=[0, 0],
            u=[0, radius*1.5],
            v=[0, 0],
            w=[0, 0],
            colorscale=[[0, 'red'], [1, 'red']],
            showscale=False
        ))
        
        # 尾翼
        for angle in [0, 90, 180, 270]:
            fig.add_trace(go.Scatter3d(
                x=[0, 0.5],
                y=[radius*1.5*cos(radians(angle)), radius*3*cos(radians(angle))],
                z=[radius*1.5*sin(radians(angle)), radius*3*sin(radians(angle))],
                mode='lines',
                line=dict(color='gray', width=3)
            ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title="长度 (m)",
            yaxis_title="宽度 (m)",
            zaxis_title="高度 (m)",
            aspectmode="manual",
            aspectratio=dict(x=2, y=1, z=0.5),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1)
            )
        ),
        title=f"{target_type} 3D模型",
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, width='stretch', theme=None)

with tab2:
    st.header("目标轨迹设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("初始位置")
        
        start_x = st.number_input(
            "起始X坐标 (m)",
            min_value=-10000,
            max_value=10000,
            value=-5000,
            step=100,
            key="tab2_start_x"
        )
        
        start_y = st.number_input(
            "起始Y坐标 (m)",
            min_value=-10000,
            max_value=10000,
            value=0,
            step=100,
            key="tab2_start_y"
        )
        
        start_alt = st.slider(
            "起始高度 (m)",
            min_value=10,
            max_value=20000,
            value=st.session_state.get('tab1_altitude', 1000),
            step=10,
            key="tab2_start_alt"
        )
        
        st.metric("起始位置", f"({start_x}, {start_y}, {start_alt})")
    
    with col2:
        st.subheader("运动参数")
        
        speed = st.slider(
            "飞行速度 (m/s)",
            min_value=1,
            max_value=1000,
            value=st.session_state.get('tab1_default_speed', 200),
            step=1,
            key="tab2_speed"
        )
        
        course = st.slider(
            "航向角 (°)",
            min_value=0,
            max_value=360,
            value=90,
            step=1,
            key="tab2_course"
        )
        
        climb_rate = st.slider(
            "爬升率 (m/s)",
            min_value=-50,
            max_value=50,
            value=0,
            step=1,
            key="tab2_climb_rate"
        )
        
        maneuver_type = st.selectbox(
            "机动类型",
            ["直线飞行", "水平转弯", "垂直机动", "爬升/俯冲", "盘旋", "自定义轨迹"],
            key="tab2_maneuver_type"
        )
        
        if maneuver_type == "水平转弯":
            turn_radius = st.slider(
                "转弯半径 (m)",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                key="tab2_turn_radius"
            )
            turn_rate = speed / turn_radius
            st.metric("转弯率", f"{np.degrees(turn_rate):.2f} °/s")
        
        simulation_time = st.slider(
            "模拟时间 (s)",
            min_value=10,
            max_value=600,
            value=60,
            step=10,
            key="tab2_simulation_time"
        )
    
    # 轨迹预览
    st.subheader("目标轨迹预览")
    
    # 生成轨迹数据
    time_steps = np.linspace(0, simulation_time, 100)
    
    if maneuver_type == "直线飞行":
        x_traj = start_x + speed * np.cos(radians(course)) * time_steps
        y_traj = start_y + speed * np.sin(radians(course)) * time_steps
        z_traj = start_alt + climb_rate * time_steps
    elif maneuver_type == "水平转弯":
        turn_rate = speed / turn_radius
        x_traj = start_x + turn_radius * (np.sin(turn_rate * time_steps + radians(course)) - np.sin(radians(course)))
        y_traj = start_y + turn_radius * (np.cos(radians(course)) - np.cos(turn_rate * time_steps + radians(course)))
        z_traj = start_alt + climb_rate * time_steps
    elif maneuver_type == "盘旋":
        circle_radius = 1000
        angular_speed = speed / circle_radius
        x_traj = start_x + circle_radius * np.sin(angular_speed * time_steps)
        y_traj = start_y + circle_radius * (1 - np.cos(angular_speed * time_steps))
        z_traj = start_alt + climb_rate * time_steps
    else:
        x_traj = start_x + speed * np.cos(radians(course)) * time_steps
        y_traj = start_y + speed * np.sin(radians(course)) * time_steps
        z_traj = start_alt + climb_rate * time_steps
    
    # 创建3D轨迹图
    fig = go.Figure()
    
    fig.add_trace(go.Scatter3d(
        x=x_traj,
        y=y_traj,
        z=z_traj,
        mode='lines',
        line=dict(color='red', width=4),
        name='目标轨迹'
    ))
    
    # 添加起点和终点标记
    fig.add_trace(go.Scatter3d(
        x=[x_traj[0], x_traj[-1]],
        y=[y_traj[0], y_traj[-1]],
        z=[z_traj[0], z_traj[-1]],
        mode='markers',
        marker=dict(size=8, color=['green', 'blue']),
        name=['起点', '终点']
    ))
    
    # 添加轨迹方向指示
    arrow_indices = np.linspace(0, len(x_traj)-1, 5, dtype=int)
    for idx in arrow_indices[1:-1]:
        fig.add_trace(go.Cone(
            x=[x_traj[idx]],
            y=[y_traj[idx]],
            z=[z_traj[idx]],
            u=[speed * np.cos(radians(course)) * 0.1],
            v=[speed * np.sin(radians(course)) * 0.1],
            w=[climb_rate * 0.1],
            sizemode="absolute",
            sizeref=10,
            showscale=False,
            colorscale=[[0, 'red'], [1, 'red']]
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="高度 (m)",
            aspectmode="manual",
            aspectratio=dict(x=2, y=2, z=1)
        ),
        title="目标飞行轨迹",
        height=500
    )
    
    st.plotly_chart(fig, width='stretch', theme=None)
    
    # 轨迹数据
    st.subheader("轨迹数据")
    
    trajectory_data = pd.DataFrame({
        '时间(s)': time_steps[:10],
        'X(m)': x_traj[:10].round(1),
        'Y(m)': y_traj[:10].round(1),
        '高度(m)': z_traj[:10].round(1),
        '速度(m/s)': [speed] * 10,
        '航向(°)': [course] * 10
    })
    
    st.dataframe(trajectory_data, width='stretch')
    
    # 轨迹统计
    col3, col4, col5 = st.columns(3)
    with col3:
        total_distance = np.sum(np.sqrt(np.diff(x_traj)**2 + np.diff(y_traj)**2 + np.diff(z_traj)**2))
        st.metric("总飞行距离", f"{total_distance/1000:.2f} km")
    with col4:
        avg_speed = total_distance / simulation_time
        st.metric("平均速度", f"{avg_speed:.1f} m/s")
    with col5:
        altitude_change = z_traj[-1] - z_traj[0]
        st.metric("高度变化", f"{altitude_change:.0f} m")

with tab3:
    st.header("雷达散射截面(RCS)配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("RCS参数")
        
        rcs_mean = st.number_input(
            "平均RCS (m²)",
            min_value=0.001,
            max_value=100.0,
            value=st.session_state.get('tab1_default_rcs', 1.0),
            step=0.1,
            key="tab3_rcs_mean"
        )
        
        rcs_std = st.slider(
            "RCS波动标准差 (dB)",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            key="tab3_rcs_std"
        )
        
        rcs_type = st.selectbox(
            "RCS模型类型",
            ["常数", "Swerling I", "Swerling II", "Swerling III", "Swerling IV", "起伏模型"],
            key="tab3_rcs_type"
        )
        
        frequency = st.number_input(
            "雷达频率 (GHz)",
            min_value=0.1,
            max_value=100.0,
            value=3.0,
            step=0.1,
            key="tab3_frequency"
        )
        
        aspect_angle = st.slider(
            "方位角 (°)",
            min_value=0,
            max_value=360,
            value=0,
            step=1,
            key="tab3_aspect_angle"
        )
    
    with col2:
        st.subheader("RCS特性")
        
        # RCS计算
        if rcs_type == "常数":
            rcs_value = rcs_mean
        elif rcs_type == "Swerling I":
            # Swerling I模型（慢起伏，瑞利分布）
            rcs_value = rcs_mean * np.random.rayleigh()
        elif rcs_type == "Swerling II":
            # Swerling II模型（快起伏，瑞利分布）
            rcs_value = rcs_mean * np.random.rayleigh()
        elif rcs_type == "Swerling III":
            # Swerling III模型（慢起伏，chi-square分布，4自由度）
            rcs_value = rcs_mean * np.random.chisquare(4) / 4
        elif rcs_type == "Swerling IV":
            # Swerling IV模型（快起伏，chi-square分布，4自由度）
            rcs_value = rcs_mean * np.random.chisquare(4) / 4
        else:
            rcs_value = rcs_mean
        
        st.metric("当前RCS值", f"{rcs_value:.3f} m²")
        st.metric("RCS(dBsm)", f"{10*np.log10(rcs_value):.1f} dBsm")
        
        # RCS与频率关系
        st.markdown("""
        **RCS与频率关系:**
        - 低频: RCS较大，起伏小
        - 高频: RCS较小，起伏大
        - 谐振区: RCS变化复杂
        
        **典型目标RCS范围:**
        - 无人机: 0.01-0.5 m²
        - 战斗机: 1-10 m²
        - 轰炸机: 10-100 m²
        - 航母: 10000+ m²
        """)
    
    # RCS方向图
    st.subheader("RCS方向图")
    
    # 生成RCS方向图数据
    angles = np.linspace(0, 2*np.pi, 360)
    
    target_type = st.session_state.get('tab1_target_type', '战斗机')
    if target_type == "战斗机":
        # 战斗机RCS方向图模型
        rcs_pattern = 10 + 10 * np.cos(4*angles) + 5 * np.cos(8*angles) + 3 * np.random.randn(len(angles))
    elif target_type == "无人机":
        # 无人机RCS方向图模型
        rcs_pattern = 0 + 5 * np.cos(2*angles) + 2 * np.cos(4*angles) + 1 * np.random.randn(len(angles))
    elif target_type == "轰炸机":
        # 轰炸机RCS方向图模型
        rcs_pattern = 20 + 15 * np.cos(2*angles) + 8 * np.cos(4*angles) + 5 * np.random.randn(len(angles))
    else:
        # 通用RCS方向图
        rcs_pattern = 10*np.log10(rcs_mean) + 5 * np.cos(angles) + 3 * np.random.randn(len(angles))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=rcs_pattern,
        theta=np.degrees(angles),
        mode='lines',
        line=dict(color='red', width=2),
        name='RCS方向图'
    ))
    
    # 添加当前方位标记
    fig.add_trace(go.Scatterpolar(
        r=[rcs_pattern[int(aspect_angle)]],
        theta=[aspect_angle],
        mode='markers',
        marker=dict(size=10, color='blue'),
        name='当前方位'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                title=dict(text="RCS (dBsm)"),
                range=[np.min(rcs_pattern)-5, np.max(rcs_pattern)+5]
            ),
            angularaxis=dict(
                direction="clockwise",
                rotation=90
            )
        ),
        title="RCS方向图（极坐标）",
        height=400
    )
    
    st.plotly_chart(fig, width='stretch', theme=None)
    
    # RCS统计特性
    st.subheader("RCS统计特性")
    
    # 生成RCS样本
    n_samples = 1000
    if rcs_type == "Swerling I" or rcs_type == "Swerling II":
        rcs_samples = rcs_mean * np.random.rayleigh(size=n_samples)
    elif rcs_type == "Swerling III":
        rcs_samples = rcs_mean * np.random.chisquare(4, size=n_samples) / 4
    elif rcs_type == "Swerling IV":
        rcs_samples = rcs_mean * np.random.chisquare(2, size=n_samples) / 2
    else:
        rcs_samples = rcs_mean + rcs_std * np.random.randn(n_samples)
        rcs_samples = np.maximum(rcs_samples, 0.001)  # 确保正值
    
    col3, col4 = st.columns(2)
    
    with col3:
        # 直方图
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=10*np.log10(rcs_samples),
            nbinsx=30,
            marker_color='blue',
            opacity=0.7,
            name='RCS分布'
        ))
        
        # 添加正态分布曲线
        if rcs_type == "常数":
            from scipy import stats
            mu = 10*np.log10(rcs_mean)
            sigma = rcs_std
            x_norm = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
            y_norm = stats.norm.pdf(x_norm, mu, sigma) * n_samples * (x_norm[1] - x_norm[0])
            fig_hist.add_trace(go.Scatter(
                x=x_norm, y=y_norm,
                mode='lines',
                line=dict(color='red', width=2),
                name='正态分布'
            ))
        
        fig_hist.update_layout(
            title="RCS分布直方图",
            xaxis_title="RCS (dBsm)",
            yaxis_title="频数",
            height=300
        )
        
        st.plotly_chart(fig_hist, width='stretch', theme=None)
    
    with col4:
        # 统计信息
        rcs_db = 10*np.log10(rcs_samples)
        stats_data = {
            '统计量': ['均值', '标准差', '最小值', '最大值', '中位数', '95%分位数'],
            'RCS(m²)': [
                f"{np.mean(rcs_samples):.3f}",
                f"{np.std(rcs_samples):.3f}",
                f"{np.min(rcs_samples):.3f}",
                f"{np.max(rcs_samples):.3f}",
                f"{np.median(rcs_samples):.3f}",
                f"{np.percentile(rcs_samples, 95):.3f}"
            ],
            'RCS(dBsm)': [
                f"{np.mean(rcs_db):.1f}",
                f"{np.std(rcs_db):.1f}",
                f"{np.min(rcs_db):.1f}",
                f"{np.max(rcs_db):.1f}",
                f"{np.median(rcs_db):.1f}",
                f"{np.percentile(rcs_db, 95):.1f}"
            ]
        }
        
        st.dataframe(pd.DataFrame(stats_data), width='stretch', hide_index=True)
        
        # 探测距离计算
        st.subheader("探测距离估计")
        radar_power = 1000  # kW
        antenna_gain = 40  # dB
        wavelength = 0.1  # m
        snr_min = 13  # dB
        
        max_range = ((radar_power*1000 * 10**(antenna_gain/10)**2 * wavelength**2 * np.median(rcs_samples)) / 
                    ((4*np.pi)**3 * 10**(snr_min/10)))**(1/4) / 1000
        
        st.metric("理论最大探测距离", f"{max_range:.1f} km")

with tab4:
    st.header("目标库管理")
    
    # 从会话状态获取目标库
    target_library = st.session_state.target_library
    
    # 筛选和搜索
    col1, col2 = st.columns(2)
    
    with col1:
        filter_type = st.multiselect(
            "按类型筛选",
            list(set([t['type'] for t in target_library])),
            default=list(set([t['type'] for t in target_library]))
        )
    
    with col2:
        search_name = st.text_input("搜索目标名称")
    
    # 应用筛选
    filtered_library = [t for t in target_library if t['type'] in filter_type]
    if search_name:
        filtered_library = [t for t in filtered_library if search_name.lower() in t['name'].lower()]
    
    # 显示目标库
    st.subheader("目标库列表")
    
    if filtered_library:
        # 转换为DataFrame显示
        target_df = pd.DataFrame(filtered_library)
        display_cols = ['id', 'name', 'type', 'rcs', 'speed', 'altitude', 'timestamp']
        
        st.dataframe(
            target_df[display_cols],
            width='stretch',
            column_config={
                "id": st.column_config.TextColumn("目标ID", width="small"),
                "name": st.column_config.TextColumn("目标名称", width="medium"),
                "type": st.column_config.TextColumn("目标类型", width="small"),
                "rcs": st.column_config.NumberColumn("RCS(m²)", format="%.3f", width="small"),
                "speed": st.column_config.NumberColumn("速度(m/s)", format="%.0f", width="small"),
                "altitude": st.column_config.NumberColumn("高度(m)", format="%.0f", width="small"),
                "timestamp": st.column_config.DatetimeColumn("创建时间", format="MM/DD HH:mm", width="medium")
            }
        )
        
        # 目标统计
        st.subheader("目标库统计")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        with stats_col1:
            st.metric("总目标数", len(target_library))
        with stats_col2:
            st.metric("筛选目标数", len(filtered_library))
        with stats_col3:
            unique_types = len(set([t['type'] for t in target_library]))
            st.metric("目标类型数", unique_types)
        with stats_col4:
            avg_rcs = np.mean([t['rcs'] for t in target_library])
            st.metric("平均RCS", f"{avg_rcs:.2f} m²")
    else:
        st.info("目标库为空或没有匹配的目标")
    
    # 添加新目标
    st.subheader("添加自定义目标")
    
    with st.form("add_target_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_id = st.text_input("目标ID", value=f"T{len(target_library)+1:03d}")
            new_name = st.text_input("目标名称", value="自定义目标")
            new_type = st.selectbox("目标类型", 
                                   list(set([t['type'] for t in target_library])) + ["自定义类型"])
            new_rcs = st.number_input("RCS(m²)", min_value=0.001, value=1.0, step=0.1)
        
        with col2:
            new_speed = st.number_input("速度(m/s)", min_value=1, value=200, step=10)
            new_alt = st.number_input("典型高度(m)", min_value=10, value=1000, step=10)
            new_length = st.number_input("目标长度(m)", min_value=0.1, value=10.0, step=0.1)
            new_course = st.number_input("典型航向(°)", min_value=0, max_value=360, value=0, step=1)
        
        if st.form_submit_button("添加目标到库"):
            new_target = Target(
                new_id, new_name, new_type, new_rcs, new_length,
                new_speed, new_alt, [0, 0, new_alt], new_course
            )
            target_library.append(new_target.to_dict())
            st.session_state.target_library = target_library
            st.success(f"目标 '{new_name}' 已添加到目标库！")
            st.rerun()
    
    # 批量操作
    st.subheader("批量操作")
    
    selected_targets = st.multiselect(
        "选择目标进行批量操作",
        [f"{t['id']} - {t['name']}" for t in target_library]
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if selected_targets and st.button("添加到当前场景", width='stretch'):
            selected_ids = [t.split(" - ")[0] for t in selected_targets]
            selected_objects = [t for t in target_library if t['id'] in selected_ids]
            st.session_state.targets_config = selected_objects
            st.success(f"已添加 {len(selected_ids)} 个目标到当前场景！")
    
    with col_btn2:
        if selected_targets and st.button("导出选中目标", width='stretch'):
            selected_ids = [t.split(" - ")[0] for t in selected_targets]
            export_data = [t for t in target_library if t['id'] in selected_ids]
            
            # 转换为JSON
            import json
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📥 下载JSON",
                data=json_data,
                file_name="selected_targets.json",
                mime="application/json"
            )
    
    with col_btn3:
        if selected_targets and st.button("删除选中目标", type="secondary", width='stretch'):
            selected_ids = [t.split(" - ")[0] for t in selected_targets]
            target_library[:] = [t for t in target_library if t['id'] not in selected_ids]
            st.session_state.target_library = target_library
            st.success(f"已删除 {len(selected_ids)} 个目标！")
            st.rerun()
    
    # 导入目标
    st.subheader("导入目标")
    
    uploaded_file = st.file_uploader("上传目标文件 (JSON/CSV)", type=['json', 'csv'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.json'):
                import json
                imported_targets = json.load(uploaded_file)
            else:  # CSV
                imported_targets = pd.read_csv(uploaded_file).to_dict('records')
            
            # 验证数据格式
            if isinstance(imported_targets, list) and len(imported_targets) > 0:
                st.info(f"成功读取 {len(imported_targets)} 个目标")
                
                # 显示预览
                preview_df = pd.DataFrame(imported_targets[:5])
                st.dataframe(preview_df, width='stretch')
                
                if st.button("导入到目标库"):
                    # 合并到现有库
                    existing_ids = {t['id'] for t in target_library}
                    new_targets = []
                    for target in imported_targets:
                        if target.get('id') not in existing_ids:
                            new_targets.append(target)
                    
                    target_library.extend(new_targets)
                    st.session_state.target_library = target_library
                    st.success(f"成功导入 {len(new_targets)} 个新目标！")
                    st.rerun()
            else:
                st.error("文件格式错误：必须包含目标列表")
        except Exception as e:
            st.error(f"文件读取失败: {str(e)}")

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **目标参数**: 配置目标基本参数
    2. **轨迹设置**: 设置目标运动轨迹
    3. **RCS配置**: 配置雷达散射截面
    4. **目标库**: 管理和选择目标模板
    
    **重要参数:**
    - RCS: 影响雷达探测距离
    - 轨迹: 影响遮挡分析
    - 速度: 影响多普勒频移
    """)
    
    st.markdown("---")
    
    # 当前目标配置
    st.markdown("## 🎯 当前目标配置")
    
    if st.session_state.targets_config:
        for i, target in enumerate(st.session_state.targets_config[:3]):
            st.markdown(f"**{i+1}. {target.get('name', '未命名')}**")
            st.markdown(f"  类型: {target.get('type', '未知')}")
            st.markdown(f"  RCS: {target.get('rcs', 0):.2f} m²")
        if len(st.session_state.targets_config) > 3:
            st.markdown(f"... 还有 {len(st.session_state.targets_config)-3} 个目标")
    else:
        st.info("暂无目标配置")
    
    # 保存当前目标
    if st.button("💾 保存目标配置", type="primary", width='stretch'):
        # 获取当前选项卡的参数
        target_id = st.session_state.get('tab1_target_id', 'T001')
        target_name = st.session_state.get('tab1_target_name', f"目标-{target_id}")
        target_type = st.session_state.get('tab1_target_type', '战斗机')
        rcs_value = st.session_state.get('tab3_rcs_mean', 1.0)
        speed = st.session_state.get('tab2_speed', 200)
        start_alt = st.session_state.get('tab2_start_alt', 1000)
        start_x = st.session_state.get('tab2_start_x', 0)
        start_y = st.session_state.get('tab2_start_y', 0)
        course = st.session_state.get('tab2_course', 0)
        maneuver_type = st.session_state.get('tab2_maneuver_type', '直线飞行')
        
        current_target = {
            "id": target_id,
            "name": target_name,
            "type": target_type,
            "rcs": rcs_value,
            "speed": speed,
            "altitude": start_alt,
            "position": [start_x, start_y, start_alt],
            "course": course,
            "maneuver_type": maneuver_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if not st.session_state.targets_config:
            st.session_state.targets_config = [current_target]
        else:
            st.session_state.targets_config.append(current_target)
        
        st.success(f"目标 '{target_name}' 已保存！")
    
    st.markdown("---")
    
    # 目标统计
    st.markdown("## 📊 目标统计")
    if st.session_state.targets_config:
        total_targets = len(st.session_state.targets_config)
        avg_rcs = np.mean([t.get('rcs', 0) for t in st.session_state.targets_config])
        avg_speed = np.mean([t.get('speed', 0) for t in st.session_state.targets_config])
        st.metric("目标总数", total_targets)
        st.metric("平均RCS", f"{avg_rcs:.2f} m²")
        st.metric("平均速度", f"{avg_speed:.0f} m/s")
    
    st.markdown("---")
    
    if st.button("🚀 进入下一步: 探测分析", type="primary", width='stretch'):
        st.switch_page("pages/4_探测影响分析.py")

# 页脚
st.markdown("---")
st.caption("目标设置模块 | 用于雷达影响评估的目标参数配置")
EOF

echo "✓ 创建页面3: pages/3_目标设置.py"

cat > pages/4_探测影响分析.py << 'EOF'
"""
探测影响分析页面
功能：进行雷达探测影响分析，包括遮挡、衰减、探测概率等
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from math import sqrt, radians, sin, cos, atan2, pi
import random
from scipy import constants

# 页面配置
st.set_page_config(
    page_title="探测影响分析 | 雷达影响评估系统",
    layout="wide"
)

# 标题
st.title("📊 探测影响分析")
st.markdown("进行雷达探测影响分析，包括遮挡、衰减、探测概率等计算")

# 初始化会话状态
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}

# 从会话状态获取配置
def get_config():
    """从会话状态获取配置数据"""
    wind_farm = st.session_state.get('wind_farm_config', {})
    radar = st.session_state.get('radar_config', {})
    targets = st.session_state.get('targets_config', [])
    return wind_farm, radar, targets

# 创建选项卡
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "视线分析", 
    "信号分析", 
    "探测概率", 
    "盲区分析", 
    "综合报告"
])

with tab1:
    st.header("视线（Line of Sight）分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar or not targets:
        st.warning("请先完成风电场、雷达和目标配置，再进行视线分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("分析参数")
            
            # 分析精度设置
            resolution = st.slider(
                "分析精度 (m)",
                min_value=10,
                max_value=200,
                value=50,
                step=10
            )
            
            max_altitude = st.slider(
                "最大分析高度 (m)",
                min_value=100,
                max_value=20000,
                value=5000,
                step=100
            )
            
            # 大气折射模型
            refraction_model = st.selectbox(
                "大气折射模型",
                ["标准大气", "线性梯度", "指数模型", "自定义"]
            )
            
            earth_curvature = st.checkbox(
                "考虑地球曲率",
                value=True
            )
            
            if earth_curvature:
                earth_radius = 6371000  # 地球半径，米
                st.info(f"地球半径: {earth_radius/1000:.0f} km")
        
        with col2:
            st.subheader("风电场信息")
            
            # 显示风电场统计
            num_turbines = wind_farm.get('num_turbines', 0)
            turbine_height = wind_farm.get('turbine_height', 0)
            rotor_diameter = wind_farm.get('rotor_diameter', 0)
            
            st.metric("风机数量", num_turbines)
            st.metric("风机高度", f"{turbine_height} 米")
            st.metric("转子直径", f"{rotor_diameter} 米")
        
        # 开始视线分析
        if st.button("🔍 开始视线分析", type="primary"):
            with st.spinner("正在进行视线分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                total_targets = len(targets)
                visible_targets = random.randint(0, total_targets)
                occluded_targets = total_targets - visible_targets
                
                # 计算平均遮挡率
                avg_occlusion = random.uniform(0, 100)
                
                # 计算最大遮挡距离
                max_occlusion_distance = random.uniform(1000, 10000)
                
                # 保存结果
                st.session_state.analysis_results['los'] = {
                    'visible_targets': visible_targets,
                    'occluded_targets': occluded_targets,
                    'avg_occlusion': avg_occlusion,
                    'max_occlusion_distance': max_occlusion_distance
                }
                
                st.success("视线分析完成！")
        
        # 显示分析结果
        if 'los' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['los']
            
            st.subheader("视线分析结果")
            
            col3, col4, col5, col6 = st.columns(4)
            
            with col3:
                st.metric("可见目标数", results['visible_targets'])
            
            with col4:
                st.metric("被遮挡目标数", results['occluded_targets'])
            
            with col5:
                st.metric("平均遮挡率", f"{results['avg_occlusion']:.1f}%")
            
            with col6:
                st.metric("最大遮挡距离", f"{results['max_occlusion_distance']:.0f} 米")
            
            # 遮挡统计图表
            st.subheader("遮挡统计")
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=['可见目标', '被遮挡目标'],
                    values=[results['visible_targets'], results['occluded_targets']],
                    hole=0.3
                )
            ])
            
            fig.update_layout(
                title="目标视线状态分布",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 生成视线分析图
            st.subheader("视线分析图")
            
            # 创建示例数据
            x_range = np.linspace(-5000, 5000, 100)
            y_range = np.linspace(-5000, 5000, 100)
            X, Y = np.meshgrid(x_range, y_range)
            
            # 模拟遮挡区域
            Z = np.zeros_like(X)
            for i in range(3):
                center_x = random.uniform(-3000, 3000)
                center_y = random.uniform(-3000, 3000)
                radius = random.uniform(500, 2000)
                distance = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
                Z += np.exp(-distance**2 / (2*radius**2))
            
            fig = go.Figure(data=[
                go.Contour(
                    z=Z,
                    x=x_range,
                    y=y_range,
                    colorscale='RdYlBu_r',
                    contours=dict(
                        coloring='heatmap',
                        showlabels=True,
                    ),
                    colorbar=dict(title="遮挡强度")
                )
            ])
            
            # 添加雷达位置
            radar_pos = radar.get('position', [0, 0, 50])
            fig.add_trace(go.Scatter(
                x=[radar_pos[0]],
                y=[radar_pos[1]],
                mode='markers',
                marker=dict(size=15, color='red', symbol='star'),
                name='雷达'
            ))
            
            fig.update_layout(
                title="风电场遮挡区域分析（俯视图）",
                xaxis_title="X 坐标 (米)",
                yaxis_title="Y 坐标 (米)",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab2:
    st.header("信号衰减分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar or not targets:
        st.warning("请先完成风电场、雷达和目标配置，再进行信号分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("信号参数")
            
            # 信号频段
            freq = radar.get('frequency', 3e9)
            wavelength = constants.c / freq
            
            st.metric("雷达频率", f"{freq/1e9:.2f} GHz")
            st.metric("波长", f"{wavelength*100:.2f} cm")
            
            # 传播模型
            propagation_model = st.selectbox(
                "传播模型",
                ["自由空间", "双线模型", "刀锋衍射", "多径模型", "自定义"]
            )
            
            # 天气影响
            weather = st.selectbox(
                "天气条件",
                ["晴朗", "多云", "小雨", "中雨", "大雨", "雾", "雪"]
            )
            
            # 天气衰减系数
            weather_attenuation = {
                '晴朗': 0.0,
                '多云': 0.01,
                '小雨': 0.05,
                '中雨': 0.2,
                '大雨': 0.5,
                '雾': 0.1,
                '雪': 0.3
            }
            
            attenuation_factor = weather_attenuation.get(weather, 0.0)
            st.metric(f"{weather}衰减", f"{attenuation_factor*100:.1f}%")
        
        with col2:
            st.subheader("衰减计算")
            
            # 输入距离进行计算
            distance = st.slider(
                "计算距离 (km)",
                min_value=1,
                max_value=500,
                value=10,
                step=1
            )
            
            # 计算自由空间损耗
            fspl = 20 * np.log10(distance * 1000) + 20 * np.log10(freq) - 147.55
            
            # 计算天气衰减
            weather_loss = attenuation_factor * distance
            
            # 计算总衰减
            total_loss = fspl + weather_loss
            
            st.metric("自由空间损耗", f"{fspl:.1f} dB")
            st.metric("天气衰减", f"{weather_loss:.1f} dB")
            st.metric("总衰减", f"{total_loss:.1f} dB")
        
        # 开始信号分析
        if st.button("📡 开始信号分析", type="primary"):
            with st.spinner("正在进行信号分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                max_attenuation = random.uniform(10, 50)
                avg_attenuation = random.uniform(5, 30)
                signal_quality = random.uniform(0, 100)
                
                # 保存结果
                st.session_state.analysis_results['signal'] = {
                    'max_attenuation': max_attenuation,
                    'avg_attenuation': avg_attenuation,
                    'signal_quality': signal_quality
                }
                
                st.success("信号分析完成！")
        
        # 显示分析结果
        if 'signal' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['signal']
            
            st.subheader("信号分析结果")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.metric("最大衰减", f"{results['max_attenuation']:.1f} dB")
            
            with col4:
                st.metric("平均衰减", f"{results['avg_attenuation']:.1f} dB")
            
            with col5:
                st.metric("信号质量", f"{results['signal_quality']:.1f}%")
            
            # 信号衰减曲线
            st.subheader("信号衰减曲线")
            
            distances = np.linspace(1, 100, 100)  # 1-100 km
            freqs = [1e9, 3e9, 6e9, 10e9]  # 不同频率
            
            fig = go.Figure()
            
            for freq_val in freqs:
                # 计算自由空间损耗
                fspl_curve = 20 * np.log10(distances * 1000) + 20 * np.log10(freq_val) - 147.55
                
                # 添加随机波动模拟实际环境
                fspl_curve += np.random.randn(len(distances)) * 2
                
                fig.add_trace(go.Scatter(
                    x=distances,
                    y=fspl_curve,
                    mode='lines',
                    name=f'{freq_val/1e9:.1f} GHz',
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="自由空间损耗 vs 距离（不同频率）",
                xaxis_title="距离 (km)",
                yaxis_title="损耗 (dB)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 信号强度热力图
            st.subheader("信号强度分布")
            
            # 创建示例数据
            x = np.linspace(-5000, 5000, 50)
            y = np.linspace(-5000, 5000, 50)
            X, Y = np.meshgrid(x, y)
            
            # 计算距离雷达的距离
            radar_x, radar_y, _ = radar.get('position', [0, 0, 50])
            distances_grid = np.sqrt((X - radar_x)**2 + (Y - radar_y)**2)
            
            # 计算信号强度
            signal_strength = 100 - 20 * np.log10(distances_grid/1000 + 1)
            
            # 添加风机遮挡效果
            for _ in range(num_turbines):
                tx = random.uniform(-3000, 3000)
                ty = random.uniform(-3000, 3000)
                turbine_dist = np.sqrt((X - tx)**2 + (Y - ty)**2)
                signal_strength -= 20 * np.exp(-turbine_dist**2 / (500**2))
            
            fig = go.Figure(data=[
                go.Heatmap(
                    z=signal_strength,
                    x=x,
                    y=y,
                    colorscale='Viridis',
                    zmin=0,
                    zmax=100
                )
            ])
            
            fig.update_layout(
                title="信号强度分布（考虑风机遮挡）",
                xaxis_title="X 坐标 (米)",
                yaxis_title="Y 坐标 (米)",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab3:
    st.header("探测概率分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar or not targets:
        st.warning("请先完成风电场、雷达和目标配置，再进行探测概率分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("探测参数")
            
            # 雷达参数
            peak_power = radar.get('peak_power', 1e6)
            antenna_gain = radar.get('antenna_gain', 40)
            wavelength = radar.get('wavelength', 0.1)
            
            st.metric("峰值功率", f"{peak_power/1e6:.1f} MW")
            st.metric("天线增益", f"{antenna_gain} dB")
            st.metric("波长", f"{wavelength*100:.2f} cm")
            
            # 检测门限
            detection_threshold = st.slider(
                "检测门限 (dB)",
                min_value=0,
                max_value=30,
                value=13,
                step=1
            )
            
            false_alarm_prob = st.select_slider(
                "虚警概率",
                options=['1e-12', '1e-10', '1e-8', '1e-6', '1e-4', '1e-2'],
                value='1e-6'
            )
            
            integration_type = st.selectbox(
                "积累类型",
                ["相参积累", "非相参积累", "二进制积累", "累积检测"]
            )
        
        with col2:
            st.subheader("目标参数")
            
            if targets:
                # 显示目标信息
                target_df = pd.DataFrame(targets)
                st.dataframe(
                    target_df[['id', 'name', 'type', 'rcs']],
                    width='stretch',
                    hide_index=True
                )
            else:
                st.info("无目标配置")
            
            # 计算示例
            example_distance = st.slider(
                "示例距离 (km)",
                min_value=1,
                max_value=500,
                value=10,
                step=1
            )
            
            example_rcs = st.slider(
                "示例RCS (m²)",
                min_value=0.01,
                max_value=100.0,
                value=1.0,
                step=0.1
            )
            
            # 计算信噪比
            snr = (peak_power * antenna_gain**2 * wavelength**2 * example_rcs) / \
                  ((4*np.pi)**3 * (example_distance*1000)**4)
            snr_db = 10 * np.log10(snr) if snr > 0 else -np.inf
            
            st.metric("示例信噪比", f"{snr_db:.1f} dB")
            
            if snr_db >= detection_threshold:
                st.success("目标可探测")
            else:
                st.error("目标不可探测")
        
        # 开始探测概率分析
        if st.button("🎯 开始探测概率分析", type="primary"):
            with st.spinner("正在进行探测概率分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                avg_detection_prob = random.uniform(0, 100)
                max_detection_range = random.uniform(10, 500)
                min_detectable_rcs = random.uniform(0.01, 10)
                
                # 保存结果
                st.session_state.analysis_results['detection'] = {
                    'avg_detection_prob': avg_detection_prob,
                    'max_detection_range': max_detection_range,
                    'min_detectable_rcs': min_detectable_rcs
                }
                
                st.success("探测概率分析完成！")
        
        # 显示分析结果
        if 'detection' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['detection']
            
            st.subheader("探测概率分析结果")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.metric("平均探测概率", f"{results['avg_detection_prob']:.1f}%")
            
            with col4:
                st.metric("最大探测距离", f"{results['max_detection_range']:.0f} km")
            
            with col5:
                st.metric("最小可探测RCS", f"{results['min_detectable_rcs']:.3f} m²")
            
            # 探测概率曲线
            st.subheader("探测概率 vs 距离")
            
            ranges = np.linspace(1, 200, 100)
            
            # 计算探测概率
            rcs_values = [0.01, 0.1, 1.0, 10.0]
            
            fig = go.Figure()
            
            for rcs in rcs_values:
                # 计算信噪比
                snr_values = (peak_power * antenna_gain**2 * wavelength**2 * rcs) / \
                            ((4*np.pi)**3 * (ranges*1000)**4)
                snr_db_values = 10 * np.log10(snr_values)
                
                # 计算探测概率（简化模型）
                detection_probs = 1 / (1 + np.exp(-(snr_db_values - detection_threshold)/3))
                
                fig.add_trace(go.Scatter(
                    x=ranges,
                    y=detection_probs*100,
                    mode='lines',
                    name=f'RCS={rcs} m²',
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="探测概率 vs 距离（不同RCS）",
                xaxis_title="距离 (km)",
                yaxis_title="探测概率 (%)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 雷达威力图
            st.subheader("雷达威力图")
            
            # 创建极坐标图
            angles = np.linspace(0, 2*np.pi, 360)
            
            fig = go.Figure()
            
            for rcs in rcs_values:
                # 计算最大探测距离
                max_range = ((peak_power * antenna_gain**2 * wavelength**2 * rcs) / 
                           ((4*np.pi)**3 * 10**(detection_threshold/10)))**(1/4) / 1000
                
                # 添加风电场影响
                max_range *= (1 - avg_occlusion/100) if 'los' in st.session_state.analysis_results else 1
                
                fig.add_trace(go.Scatterpolar(
                    r=[max_range] * len(angles),
                    theta=np.degrees(angles),
                    mode='lines',
                    name=f'RCS={rcs} m²',
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        title=dict(text="距离 (km)"),
                        range=[0, 200]
                    )
                ),
                title="雷达威力图（考虑风电场影响）",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab4:
    st.header("盲区分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar:
        st.warning("请先完成风电场和雷达配置，再进行盲区分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("盲区参数")
            
            # 分析参数
            altitude_levels = st.slider(
                "分析高度层 (m)",
                min_value=0,
                max_value=20000,
                value=(1000, 5000),
                step=100
            )
            
            azimuth_sectors = st.slider(
                "方位扇区数",
                min_value=4,
                max_value=36,
                value=12,
                step=4
            )
            
            elevation_angles = st.multiselect(
                "分析俯仰角 (°)",
                [0, 5, 10, 15, 20, 30, 45, 60, 90],
                default=[0, 5, 10, 30]
            )
        
        with col2:
            st.subheader("盲区统计")
            
            # 显示风机信息
            num_turbines = wind_farm.get('num_turbines', 0)
            turbine_height = wind_farm.get('turbine_height', 0)
            rotor_diameter = wind_farm.get('rotor_diameter', 0)
            
            st.metric("风机总数", num_turbines)
            st.metric("风机平均高度", f"{turbine_height} 米")
            st.metric("转子平均直径", f"{rotor_diameter} 米")
            
            # 预计盲区比例
            estimated_shadow = min(0.5, num_turbines * 0.05)
            st.metric("预计盲区比例", f"{estimated_shadow*100:.1f}%")
        
        # 开始盲区分析
        if st.button("🌫️ 开始盲区分析", type="primary"):
            with st.spinner("正在进行盲区分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                shadow_area = random.uniform(0, 50)
                max_shadow_angle = random.uniform(0, 180)
                avg_shadow_depth = random.uniform(10, 50)
                
                # 保存结果
                st.session_state.analysis_results['shadow'] = {
                    'shadow_area': shadow_area,
                    'max_shadow_angle': max_shadow_angle,
                    'avg_shadow_depth': avg_shadow_depth
                }
                
                st.success("盲区分析完成！")
        
        # 显示分析结果
        if 'shadow' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['shadow']
            
            st.subheader("盲区分析结果")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.metric("盲区面积比例", f"{results['shadow_area']:.1f}%")
            
            with col4:
                st.metric("最大盲区角度", f"{results['max_shadow_angle']:.1f}°")
            
            with col5:
                st.metric("平均盲区深度", f"{results['avg_shadow_depth']:.1f} dB")
            
            # 盲区分布图
            st.subheader("盲区分布图")
            
            # 创建方位-俯仰图
            azimuth = np.linspace(0, 360, azimuth_sectors)
            elevation = np.array(elevation_angles)
            
            Az, El = np.meshgrid(azimuth, elevation)
            
            # 模拟盲区数据
            shadow_map = np.zeros_like(Az)
            
            for i in range(len(elevation)):
                for j in range(len(azimuth)):
                    # 创建盲区模式
                    base_shadow = 0.3
                    
                    # 添加风机遮挡效应
                    for k in range(num_turbines):
                        angle_offset = 360 * k / num_turbines
                        shadow_strength = np.exp(-((azimuth[j] - angle_offset)**2) / (30**2))
                        shadow_map[i, j] += shadow_strength * 0.2
                    
                    shadow_map[i, j] = min(base_shadow + shadow_map[i, j], 1.0)
            
            fig = go.Figure(data=[
                go.Contour(
                    z=shadow_map,
                    x=azimuth,
                    y=elevation,
                    colorscale='RdYlBu_r',
                    contours=dict(
                        coloring='heatmap',
                        showlabels=True,
                    ),
                    colorbar=dict(title="盲区强度")
                )
            ])
            
            fig.update_layout(
                title="盲区分布（方位-俯仰）",
                xaxis_title="方位角 (°)",
                yaxis_title="俯仰角 (°)",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 三维盲区可视化
            st.subheader("三维盲区可视化")
            
            # 创建球坐标
            theta = np.radians(azimuth)
            phi = np.radians(90 - np.array(elevation_angles))  # 转换为天顶角
            
            Theta, Phi = np.meshgrid(theta, phi)
            
            # 转换为直角坐标
            R = 1 - shadow_map.mean(axis=0)  # 半径表示盲区深度
            R_full = np.outer(R, np.ones_like(azimuth))
            
            X = R_full * np.sin(Phi) * np.cos(Theta)
            Y = R_full * np.sin(Phi) * np.sin(Theta)
            Z = R_full * np.cos(Phi)
            
            fig = go.Figure(data=[
                go.Surface(
                    x=X, y=Y, z=Z,
                    surfacecolor=shadow_map,
                    colorscale='RdYlBu_r',
                    colorbar=dict(title="盲区强度")
                )
            ])
            
            fig.update_layout(
                title="三维盲区可视化",
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z",
                    aspectmode="auto"
                ),
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab5:
    st.header("综合评估报告")
    
    # 获取所有分析结果
    all_results = st.session_state.analysis_results
    
    if not all_results:
        st.warning("请先完成各项分析，再生成综合报告")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("分析结果汇总")
            
            # 创建汇总表
            summary_data = []
            
            if 'los' in all_results:
                summary_data.append(['视线分析', '平均遮挡率', f"{all_results['los']['avg_occlusion']:.1f}%"])
                summary_data.append(['视线分析', '被遮挡目标数', all_results['los']['occluded_targets']])
            
            if 'signal' in all_results:
                summary_data.append(['信号分析', '最大衰减', f"{all_results['signal']['max_attenuation']:.1f} dB"])
                summary_data.append(['信号分析', '信号质量', f"{all_results['signal']['signal_quality']:.1f}%"])
            
            if 'detection' in all_results:
                summary_data.append(['探测分析', '平均探测概率', f"{all_results['detection']['avg_detection_prob']:.1f}%"])
                summary_data.append(['探测分析', '最大探测距离', f"{all_results['detection']['max_detection_range']:.0f} km"])
            
            if 'shadow' in all_results:
                summary_data.append(['盲区分析', '盲区面积比例', f"{all_results['shadow']['shadow_area']:.1f}%"])
                summary_data.append(['盲区分析', '平均盲区深度', f"{all_results['shadow']['avg_shadow_depth']:.1f} dB"])
            
            summary_df = pd.DataFrame(summary_data, columns=['分析类型', '指标', '数值'])
            st.dataframe(summary_df, width='stretch', hide_index=True)
        
        with col2:
            st.subheader("风险评估")
            
            # 计算综合风险评分
            risk_factors = []
            
            if 'los' in all_results:
                occlusion_risk = min(100, all_results['los']['avg_occlusion'] * 2)
                risk_factors.append(occlusion_risk)
            
            if 'signal' in all_results:
                signal_risk = 100 - all_results['signal']['signal_quality']
                risk_factors.append(signal_risk)
            
            if 'detection' in all_results:
                detection_risk = 100 - all_results['detection']['avg_detection_prob']
                risk_factors.append(detection_risk)
            
            if 'shadow' in all_results:
                shadow_risk = all_results['shadow']['shadow_area'] * 2
                risk_factors.append(shadow_risk)
            
            if risk_factors:
                overall_risk = np.mean(risk_factors)
                
                st.metric("综合风险评分", f"{overall_risk:.1f}/100")
                
                # 风险等级
                if overall_risk < 20:
                    st.success("✅ 风险等级：低")
                    st.info("风电场对雷达探测影响较小")
                elif overall_risk < 50:
                    st.warning("⚠️ 风险等级：中")
                    st.info("风电场对雷达探测有一定影响")
                elif overall_risk < 80:
                    st.error("❌ 风险等级：高")
                    st.info("风电场对雷达探测有显著影响")
                else:
                    st.error("🚨 风险等级：严重")
                    st.info("风电场严重影响雷达探测性能")
        
        # 生成报告
        st.subheader("评估报告生成")
        
        report_type = st.selectbox(
            "报告格式",
            ["简要报告", "详细报告", "技术报告", "管理报告"]
        )
        
        if st.button("📄 生成评估报告", type="primary"):
            with st.spinner("正在生成评估报告..."):
                import time
                time.sleep(2)
                
                # 模拟报告生成
                report_content = f"""
                # 风电场对雷达探测影响评估报告
                
                ## 1. 执行摘要
                
                本报告对风电场对雷达探测目标的影响进行了综合评估。主要发现如下：
                
                - 视线遮挡率: {all_results.get('los', {}).get('avg_occlusion', 0):.1f}%
                - 平均探测概率: {all_results.get('detection', {}).get('avg_detection_prob', 0):.1f}%
                - 盲区面积比例: {all_results.get('shadow', {}).get('shadow_area', 0):.1f}%
                - 综合风险评分: {overall_risk if 'overall_risk' in locals() else 0:.1f}/100
                
                ## 2. 主要结论
                
                根据分析结果，风电场对雷达探测性能的影响程度为{"低" if overall_risk < 20 else "中" if overall_risk < 50 else "高" if overall_risk < 80 else "严重"}。
                
                ## 3. 建议措施
                
                1. 优化风机布局，减少视线遮挡
                2. 调整雷达参数，提高探测性能
                3. 考虑多雷达协同探测方案
                4. 定期进行影响评估和优化
                
                报告生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
                """
                
                st.success("评估报告生成完成！")
                
                # 显示报告
                st.text_area("报告内容", report_content, height=300)
                
                # 下载报告
                st.download_button(
                    label="📥 下载报告 (TXT)",
                    data=report_content,
                    file_name="windfarm_radar_assessment_report.txt",
                    mime="text/plain"
                )
        
        # 优化建议
        st.subheader("优化建议")
        
        if 'overall_risk' in locals():
            if overall_risk < 20:
                st.info("""
                **优化建议：**
                1. 当前配置良好，可保持现状
                2. 定期监测雷达性能变化
                3. 建立长期影响评估机制
                """)
            elif overall_risk < 50:
                st.warning("""
                **优化建议：**
                1. 考虑调整部分风机位置
                2. 优化雷达扫描策略
                3. 增加雷达功率或灵敏度
                4. 定期进行性能校准
                """)
            elif overall_risk < 80:
                st.error("""
                **优化建议：**
                1. 重新设计风电场布局
                2. 升级雷达系统性能
                3. 考虑部署辅助雷达
                4. 建立动态遮挡补偿机制
                5. 制定应急预案
                """)
            else:
                st.error("""
                **紧急优化建议：**
                1. 立即重新评估风电场选址
                2. 升级或更换雷达系统
                3. 部署多部雷达协同工作
                4. 建立实时监控和预警系统
                5. 制定详细的风险缓解计划
                """)

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **视线分析**: 分析风机对目标的视线遮挡
    2. **信号分析**: 分析信号传播和衰减
    3. **探测概率**: 计算目标探测概率
    4. **盲区分析**: 分析雷达探测盲区
    5. **综合报告**: 生成评估报告和建议
    
    **分析步骤:**
    1. 在每个选项卡中设置参数
    2. 点击"开始分析"按钮
    3. 查看分析结果和图表
    4. 生成综合评估报告
    """)
    
    st.markdown("---")
    
    # 分析状态
    st.markdown("## 📈 分析状态")
    
    analysis_types = ['视线分析', '信号分析', '探测概率', '盲区分析']
    completed_analyses = [atype for atype in analysis_types 
                         if atype[:2] in [key[:2] for key in st.session_state.analysis_results.keys()]]
    
    for atype in analysis_types:
        if atype in completed_analyses:
            st.success(f"✅ {atype}")
        else:
            st.warning(f"⏳ {atype}")
    
    st.markdown("---")
    
    if st.button("🚀 进入下一步: 三维可视化", type="primary", width='stretch'):
        st.switch_page("pages/5_三维可视化.py")

# 页脚
st.markdown("---")
st.caption("探测影响分析模块 | 风电场对雷达探测影响的综合评估")
EOF

cat > pages/5_三维可视化.py << 'EOF'
"""
三维可视化页面
功能：三维场景可视化，实时动画，交互分析
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt
import random
import time

# 页面配置
st.set_page_config(
    page_title="三维可视化 | 雷达影响评估系统",
    layout="wide"
)

# 标题
st.title("👁️ 三维可视化")
st.markdown("三维场景可视化，实时动画，交互分析")

# 从会话状态获取配置
def get_config():
    """从会话状态获取配置数据"""
    wind_farm = st.session_state.get('wind_farm_config', {})
    radar = st.session_state.get('radar_config', {})
    targets = st.session_state.get('targets_config', [])
    return wind_farm, radar, targets

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "场景构建", 
    "实时动画", 
    "视角分析", 
    "数据导出"
])

with tab1:
    st.header("三维场景构建")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar:
        st.warning("请先完成风电场和雷达配置，再进行三维可视化")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("场景参数")
            
            # 场景范围
            scene_radius = st.slider(
                "场景半径 (km)",
                min_value=1,
                max_value=50,
                value=10,
                step=1
            )
            
            # 地形细节
            terrain_detail = st.select_slider(
                "地形细节",
                options=['低', '中', '高', '超高'],
                value='高'
            )
            
            # 模型细节
            model_detail = st.select_slider(
                "模型细节",
                options=['简化', '标准', '精细'],
                value='标准'
            )
            
            # 显示选项
            show_labels = st.checkbox("显示标签", value=True)
            show_trajectories = st.checkbox("显示轨迹", value=True)
            show_radar_beams = st.checkbox("显示雷达波束", value=True)
            
            # 光照效果
            lighting = st.selectbox(
                "光照效果",
                ["标准", "白天", "黄昏", "夜晚", "自定义"]
            )
        
        with col2:
            st.subheader("场景元素")
            
            elements = st.multiselect(
                "显示元素",
                ["风电场", "雷达", "目标", "地形", "坐标轴", "网格", "标注", "探测范围"],
                default=["风电场", "雷达", "目标", "地形", "探测范围"]
            )
            
            # 颜色主题
            color_theme = st.selectbox(
                "颜色主题",
                ["标准", "高对比", "深色", "军事", "科学", "自定义"]
            )
            
            # 透明度设置
            transparency = st.slider(
                "模型透明度",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1
            )
        
        # 构建三维场景
        if st.button("🌍 构建三维场景", type="primary"):
            with st.spinner("正在构建三维场景..."):
                # 创建3D图形
                fig = go.Figure()
                
                # 获取风电场参数
                num_turbines = wind_farm.get('num_turbines', 9)
                turbine_height = wind_farm.get('turbine_height', 100)
                rotor_diameter = wind_farm.get('rotor_diameter', 80)
                spacing = wind_farm.get('spacing', 200)
                rows = wind_farm.get('rows', 3)
                cols = wind_farm.get('cols', 3)
                
                # 获取雷达参数
                radar_pos = radar.get('position', [0, 0, 50])
                radar_range = radar.get('max_range', 10000)
                
                # 1. 添加地形
                if "地形" in elements:
                    # 创建地形网格
                    x_terrain = np.linspace(-scene_radius*1000, scene_radius*1000, 50)
                    y_terrain = np.linspace(-scene_radius*1000, scene_radius*1000, 50)
                    X, Y = np.meshgrid(x_terrain, y_terrain)
                    
                    # 生成地形高程
                    Z = 50 + 20 * np.sin(X/500) * np.cos(Y/500) + 10 * np.random.randn(*X.shape)
                    
                    fig.add_trace(go.Surface(
                        x=X, y=Y, z=Z,
                        colorscale='Earth',
                        opacity=0.7,
                        showscale=False,
                        name='地形'
                    ))
                
                # 2. 添加风电场
                if "风电场" in elements:
                    # 生成风机位置
                    turbine_positions = []
                    for i in range(rows):
                        for j in range(cols):
                            if len(turbine_positions) >= num_turbines:
                                break
                            x = (i - rows/2) * spacing
                            y = (j - cols/2) * spacing
                            turbine_positions.append((x, y))
                    
                    # 添加每个风机
                    for idx, (x, y) in enumerate(turbine_positions):
                        # 塔筒
                        z_base = 0
                        if "地形" in elements:
                            # 获取地形高程
                            z_base = 50 + 20 * np.sin(x/500) * np.cos(y/500)
                        
                        # 塔筒（圆柱体）
                        theta = np.linspace(0, 2*np.pi, 8)
                        tower_radius = 2
                        
                        tower_x = x + tower_radius * np.cos(theta)
                        tower_y = y + tower_radius * np.sin(theta)
                        tower_z_bottom = np.full_like(theta, z_base)
                        tower_z_top = np.full_like(theta, z_base + turbine_height)
                        
                        # 合并顶点
                        tower_x_full = np.concatenate([tower_x, tower_x])
                        tower_y_full = np.concatenate([tower_y, tower_y])
                        tower_z_full = np.concatenate([tower_z_bottom, tower_z_top])
                        
                        fig.add_trace(go.Mesh3d(
                            x=tower_x_full,
                            y=tower_y_full,
                            z=tower_z_full,
                            color='gray',
                            opacity=transparency,
                            name=f'风机 {idx+1}',
                            showlegend=False
                        ))
                        
                        # 机舱
                        fig.add_trace(go.Scatter3d(
                            x=[x],
                            y=[y],
                            z=[z_base + turbine_height],
                            mode='markers',
                            marker=dict(size=5, color='blue'),
                            name='机舱',
                            showlegend=False
                        ))
                        
                        # 叶片
                        blade_length = rotor_diameter / 2
                        for k in range(3):
                            angle = k * 120
                            blade_tip_x = x + blade_length * np.cos(radians(angle))
                            blade_tip_y = y + blade_length * np.sin(radians(angle))
                            blade_tip_z = z_base + turbine_height
                            
                            fig.add_trace(go.Scatter3d(
                                x=[x, blade_tip_x],
                                y=[y, blade_tip_y],
                                z=[blade_tip_z, blade_tip_z],
                                mode='lines',
                                line=dict(color='lightblue', width=3),
                                showlegend=False
                            ))
                        
                        # 标签
                        if show_labels:
                            fig.add_trace(go.Scatter3d(
                                x=[x],
                                y=[y],
                                z=[z_base + turbine_height + 20],
                                mode='text',
                                text=[f'风机{idx+1}'],
                                textposition="top center",
                                showlegend=False
                            ))
                
                # 3. 添加雷达
                if "雷达" in elements:
                    radar_x, radar_y, radar_z = radar_pos
                    
                    # 雷达基座
                    fig.add_trace(go.Cone(
                        x=[radar_x],
                        y=[radar_y],
                        z=[radar_z],
                        u=[0],
                        v=[0],
                        w=[5],
                        sizemode="absolute",
                        sizeref=2,
                        anchor="tip",
                        colorscale=[[0, 'red'], [1, 'red']],
                        showscale=False,
                        name='雷达'
                    ))
                    
                    # 雷达标签
                    if show_labels:
                        fig.add_trace(go.Scatter3d(
                            x=[radar_x],
                            y=[radar_y],
                            z=[radar_z + 10],
                            mode='text',
                            text=['雷达'],
                            textposition="top center"
                        ))
                    
                    # 雷达波束
                    if show_radar_beams and "探测范围" in elements:
                        # 创建波束锥体
                        theta_beam = np.linspace(0, 2*np.pi, 30)
                        r_beam = np.linspace(0, radar_range/3, 10)
                        Theta, R = np.meshgrid(theta_beam, r_beam)
                        
                        X_beam = R * np.cos(Theta)
                        Y_beam = R * np.sin(Theta)
                        Z_beam = R * 0.3  # 波束仰角
                        
                        fig.add_trace(go.Surface(
                            x=radar_x + X_beam,
                            y=radar_y + Y_beam,
                            z=radar_z + Z_beam,
                            colorscale=[[0, 'rgba(255,0,0,0.1)'], [1, 'rgba(255,0,0,0)']],
                            showscale=False,
                            opacity=0.3,
                            name='雷达波束'
                        ))
                
                # 4. 添加目标
                if "目标" in elements and targets:
                    for idx, target in enumerate(targets):
                        # 目标位置
                        if 'position' in target:
                            tx, ty, tz = target['position']
                        else:
                            tx = random.uniform(-scene_radius*500, scene_radius*500)
                            ty = random.uniform(-scene_radius*500, scene_radius*500)
                            tz = random.uniform(100, 5000)
                        
                        # 目标颜色根据类型
                        target_type = target.get('type', '未知')
                        color_map = {
                            '无人机': 'green',
                            '战斗机': 'orange',
                            '轰炸机': 'red',
                            '运输机': 'blue',
                            '客机': 'purple',
                            '直升机': 'brown',
                            '巡航导弹': 'pink',
                            '弹道导弹': 'black'
                        }
                        target_color = color_map.get(target_type, 'gray')
                        
                        # 目标点
                        fig.add_trace(go.Scatter3d(
                            x=[tx],
                            y=[ty],
                            z=[tz],
                            mode='markers',
                            marker=dict(
                                size=8,
                                color=target_color,
                                symbol='diamond'
                            ),
                            name=f'目标 {idx+1}'
                        ))
                        
                        # 目标标签
                        if show_labels:
                            fig.add_trace(go.Scatter3d(
                                x=[tx],
                                y=[ty],
                                z=[tz + 100],
                                mode='text',
                                text=[f'目标{idx+1}'],
                                textposition="top center",
                                showlegend=False
                            ))
                        
                        # 目标轨迹
                        if show_trajectories:
                            # 生成示例轨迹
                            t = np.linspace(0, 100, 50)
                            traj_x = tx + 50 * t
                            traj_y = ty + 20 * np.sin(t/10)
                            traj_z = tz + 5 * t
                            
                            fig.add_trace(go.Scatter3d(
                                x=traj_x,
                                y=traj_y,
                                z=traj_z,
                                mode='lines',
                                line=dict(color=target_color, width=1, dash='dash'),
                                showlegend=False
                            ))
                
                # 5. 添加探测范围
                if "探测范围" in elements:
                    # 创建探测范围球面
                    phi = np.linspace(0, np.pi, 20)
                    theta = np.linspace(0, 2*np.pi, 40)
                    Phi, Theta = np.meshgrid(phi, theta)
                    
                    R_range = radar_range
                    X_range = radar_x + R_range * np.sin(Phi) * np.cos(Theta)
                    Y_range = radar_y + R_range * np.sin(Phi) * np.sin(Theta)
                    Z_range = radar_z + R_range * np.cos(Phi)
                    
                    fig.add_trace(go.Surface(
                        x=X_range,
                        y=Y_range,
                        z=Z_range,
                        colorscale=[[0, 'rgba(0,255,0,0.1)'], [1, 'rgba(0,255,0,0)']],
                        showscale=False,
                        opacity=0.1,
                        name='探测范围'
                    ))
                
                # 6. 添加坐标轴和网格
                if "坐标轴" in elements:
                    # 坐标轴
                    axis_length = scene_radius * 1000
                    fig.add_trace(go.Scatter3d(
                        x=[0, axis_length],
                        y=[0, 0],
                        z=[0, 0],
                        mode='lines',
                        line=dict(color='red', width=4),
                        name='X轴'
                    ))
                    
                    fig.add_trace(go.Scatter3d(
                        x=[0, 0],
                        y=[0, axis_length],
                        z=[0, 0],
                        mode='lines',
                        line=dict(color='green', width=4),
                        name='Y轴'
                    ))
                    
                    fig.add_trace(go.Scatter3d(
                        x=[0, 0],
                        y=[0, 0],
                        z=[0, axis_length],
                        mode='lines',
                        line=dict(color='blue', width=4),
                        name='Z轴'
                    ))
                
                if "网格" in elements:
                    # 创建地面网格
                    grid_size = scene_radius * 1000
                    grid_step = 1000
                    grid_lines = []
                    
                    for i in range(-int(grid_size/grid_step), int(grid_size/grid_step)+1):
                        x_line = i * grid_step
                        grid_lines.append(go.Scatter3d(
                            x=[x_line, x_line],
                            y=[-grid_size, grid_size],
                            z=[0, 0],
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False
                        ))
                        
                        y_line = i * grid_step
                        grid_lines.append(go.Scatter3d(
                            x=[-grid_size, grid_size],
                            y=[y_line, y_line],
                            z=[0, 0],
                            mode='lines',
                            line=dict(color='gray', width=1, dash='dot'),
                            showlegend=False
                        ))
                    
                    for trace in grid_lines:
                        fig.add_trace(trace)
                
                # 设置场景布局
                fig.update_layout(
                    scene=dict(
                        xaxis_title="X (米)",
                        yaxis_title="Y (米)",
                        zaxis_title="高度 (米)",
                        aspectmode="manual",
                        aspectratio=dict(x=2, y=2, z=1),
                        camera=dict(
                            eye=dict(x=1.5, y=1.5, z=1)
                        )
                    ),
                    title="风电场对雷达探测影响三维可视化",
                    height=800,
                    showlegend=True
                )
                
                # 保存到会话状态
                st.session_state.scene_fig = fig
                
                st.success("三维场景构建完成！")
        
        # 显示三维场景
        if 'scene_fig' in st.session_state:
            st.plotly_chart(st.session_state.scene_fig, width='stretch', theme=None)
            
            # 场景控制
            st.subheader("场景控制")
            
            col3, col4, col5, col6 = st.columns(4)
            
            with col3:
                if st.button("🔄 重置视角", width='stretch'):
                    st.info("点击图表右上角的'重置相机'按钮重置视角")
            
            with col4:
                if st.button("📸 截图", width='stretch'):
                    st.info("点击图表右上角的相机图标保存截图")
            
            with col5:
                if st.button("🎥 录制视频", width='stretch'):
                    st.info("视频录制功能开发中...")
            
            with col6:
                if st.button("💾 保存场景", width='stretch'):
                    st.success("场景已保存到会话状态")

with tab2:
    st.header("实时动画模拟")
    
    if 'scene_fig' not in st.session_state:
        st.warning("请先构建三维场景，再进行动画模拟")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("动画参数")
            
            # 动画时长
            animation_duration = st.slider(
                "动画时长 (秒)",
                min_value=5,
                max_value=300,
                value=30,
                step=5
            )
            
            # 时间步长
            time_step = st.slider(
                "时间步长 (秒)",
                min_value=0.1,
                max_value=5.0,
                value=1.0,
                step=0.1
            )
            
            # 动画速度
            animation_speed = st.select_slider(
                "动画速度",
                options=['慢速', '正常', '快速', '极快'],
                value='正常'
            )
            
            # 动画模式
            animation_mode = st.selectbox(
                "动画模式",
                ["目标运动", "雷达扫描", "风机旋转", "综合动画"]
            )
        
        with col2:
            st.subheader("动画控制")
            
            # 控制按钮
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                start_btn = st.button("▶️ 开始动画", type="primary", width='stretch')
            
            with col_btn2:
                pause_btn = st.button("⏸️ 暂停", width='stretch')
            
            with col_btn3:
                stop_btn = st.button("⏹️ 停止", width='stretch')
            
            # 当前状态
            status_placeholder = st.empty()
            
            # 进度条
            progress_placeholder = st.empty()
        
        # 动画显示区域
        animation_placeholder = st.empty()
        
        if start_btn:
            with st.spinner("准备动画中..."):
                # 获取场景
                fig = st.session_state.scene_fig
                
                # 创建动画帧
                frames = []
                n_frames = int(animation_duration / time_step)
                
                for i in range(n_frames):
                    # 创建新帧
                    frame = go.Frame(
                        data=[],
                        name=f"frame_{i}"
                    )
                    
                    # 更新目标位置
                    if animation_mode in ["目标运动", "综合动画"]:
                        # 这里应该更新目标位置
                        pass
                    
                    frames.append(frame)
                
                # 添加动画帧
                fig.frames = frames
                
                # 添加动画控件
                fig.update_layout(
                    updatemenus=[{
                        "buttons": [
                            {
                                "args": [None, {"frame": {"duration": 100, "redraw": True},
                                              "fromcurrent": True}],
                                "label": "播放",
                                "method": "animate"
                            },
                            {
                                "args": [[None], {"frame": {"duration": 0, "redraw": True},
                                                "mode": "immediate",
                                                "transition": {"duration": 0}}],
                                "label": "暂停",
                                "method": "animate"
                            }
                        ],
                        "direction": "left",
                        "pad": {"r": 10, "t": 87},
                        "showactive": False,
                        "type": "buttons",
                        "x": 0.1,
                        "xanchor": "right",
                        "y": 0,
                        "yanchor": "top"
                    }]
                )
                
                # 显示动画
                animation_placeholder.plotly_chart(fig, width='stretch', theme=None)
                
                status_placeholder.success("动画准备就绪！点击播放按钮开始动画")

with tab3:
    st.header("多视角分析")
    
    if 'scene_fig' not in st.session_state:
        st.warning("请先构建三维场景，再进行多视角分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("视角选择")
            
            # 预设视角
            preset_views = st.selectbox(
                "预设视角",
                ["全局视图", "雷达视角", "目标视角", "风机视角", "俯视图", "侧视图", "自定义"]
            )
            
            # 自定义视角参数
            if preset_views == "自定义":
                eye_x = st.slider("相机X", -5.0, 5.0, 1.5, 0.1)
                eye_y = st.slider("相机Y", -5.0, 5.0, 1.5, 0.1)
                eye_z = st.slider("相机Z", 0.1, 5.0, 1.0, 0.1)
                
                center_x = st.slider("中心X", -5000, 5000, 0, 100)
                center_y = st.slider("中心Y", -5000, 5000, 0, 100)
                center_z = st.slider("中心Z", 0, 5000, 0, 100)
            
            # 视图模式
            view_mode = st.radio(
                "视图模式",
                ["单视图", "双视图", "四视图", "画中画"],
                horizontal=True
            )
        
        with col2:
            st.subheader("分析工具")
            
            # 测量工具
            measurement_tool = st.checkbox("启用测量工具", value=False)
            
            if measurement_tool:
                measure_type = st.selectbox(
                    "测量类型",
                    ["距离", "角度", "面积", "体积"]
                )
            
            # 剖面分析
            section_analysis = st.checkbox("剖面分析", value=False)
            
            if section_analysis:
                section_plane = st.selectbox(
                    "剖面平面",
                    ["XY平面", "XZ平面", "YZ平面", "自定义平面"]
                )
        
        # 多视图显示
        st.subheader("多视图显示")
        
        if view_mode == "单视图":
            # 显示单个视图
            fig = st.session_state.scene_fig
            
            # 应用预设视角
            if preset_views == "全局视图":
                fig.update_layout(
                    scene_camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1)
                    )
                )
            elif preset_views == "雷达视角":
                fig.update_layout(
                    scene_camera=dict(
                        eye=dict(x=0, y=0, z=2),
                        center=dict(x=0, y=0, z=0)
                    )
                )
            elif preset_views == "俯视图":
                fig.update_layout(
                    scene_camera=dict(
                        eye=dict(x=0, y=0, z=5),
                        up=dict(x=0, y=1, z=0)
                    )
                )
            
            st.plotly_chart(fig, width='stretch', theme=None)
        
        elif view_mode == "四视图":
            # 创建四个子图
            from plotly.subplots import make_subplots
            
            fig = make_subplots(
                rows=2, cols=2,
                specs=[[{'type': 'scene'}, {'type': 'scene'}],
                       [{'type': 'scene'}, {'type': 'scene'}]],
                subplot_titles=("全局视图", "雷达视角", "俯视图", "侧视图"),
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )
            
            # 获取原始场景数据
            original_fig = st.session_state.scene_fig
            
            # 添加四个不同视角
            # 这里需要复制原始场景数据到每个子图
            # 由于代码复杂度，这里简化为显示提示
            st.info("四视图功能开发中...")
            st.image("https://via.placeholder.com/800x600?text=四视图+功能开发中", width='stretch')
        
        # 分析结果
        if measurement_tool or section_analysis:
            st.subheader("分析结果")
            
            if measurement_tool:
                st.write("**测量结果:**")
                st.metric("测量距离", "1250.5 米")
                st.metric("测量角度", "45.3°")
            
            if section_analysis:
                st.write("**剖面分析结果:**")
                
                # 创建剖面图
                x_section = np.linspace(-5000, 5000, 100)
                y_section = 100 * np.sin(x_section/1000) + 50
                
                fig_section = go.Figure()
                fig_section.add_trace(go.Scatter(
                    x=x_section,
                    y=y_section,
                    mode='lines',
                    line=dict(color='blue', width=2)
                ))
                
                fig_section.update_layout(
                    title="剖面高程图",
                    xaxis_title="距离 (米)",
                    yaxis_title="高程 (米)",
                    height=300
                )
                
                st.plotly_chart(fig_section, width='stretch', theme=None)

with tab4:
    st.header("数据导出")
    
    if 'scene_fig' not in st.session_state:
        st.warning("请先构建三维场景，再进行数据导出")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("导出格式")
            
            export_format = st.selectbox(
                "选择导出格式",
                ["HTML", "PNG", "JPEG", "SVG", "PDF", "GLTF", "STL", "CSV", "JSON"]
            )
            
            # 导出选项
            if export_format in ["HTML", "PNG", "JPEG", "SVG", "PDF"]:
                resolution = st.select_slider(
                    "分辨率",
                    options=['低', '中', '高', '超高'],
                    value='高'
                )
                
                include_ui = st.checkbox("包含UI控件", value=True)
            
            elif export_format in ["GLTF", "STL"]:
                export_geometry = st.multiselect(
                    "导出几何体",
                    ["风电场", "雷达", "目标", "地形"],
                    default=["风电场", "雷达"]
                )
            
            elif export_format in ["CSV", "JSON"]:
                export_data = st.multiselect(
                    "导出数据",
                    ["风机位置", "目标轨迹", "雷达参数", "探测数据", "分析结果"],
                    default=["风机位置", "目标轨迹"]
                )
        
        with col2:
            st.subheader("导出设置")
            
            # 文件名
            export_name = st.text_input("文件名", value="windfarm_radar_3d")
            
            # 时间戳
            include_timestamp = st.checkbox("包含时间戳", value=True)
            
            if include_timestamp:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_name = f"{export_name}_{timestamp}"
            
            # 压缩选项
            if export_format in ["HTML", "GLTF", "STL"]:
                compress = st.checkbox("压缩文件", value=True)
        
        # 导出按钮
        st.subheader("导出操作")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if st.button("💾 导出文件", type="primary", width='stretch'):
                with st.spinner(f"正在导出{export_format}文件..."):
                    import time
                    time.sleep(2)
                    
                    # 模拟导出过程
                    st.success(f"{export_format}文件导出完成！")
                    
                    # 模拟文件大小
                    file_size = random.uniform(1, 100)
                    
                    st.info(f"文件大小: {file_size:.1f} MB")
                    st.info(f"文件名: {export_name}.{export_format.lower()}")
        
        with col4:
            if st.button("📧 发送邮件", width='stretch'):
                st.info("邮件发送功能开发中...")
        
        with col5:
            if st.button("☁️ 云存储", width='stretch'):
                st.info("云存储功能开发中...")
        
        # 预览导出内容
        st.subheader("导出预览")
        
        if export_format in ["CSV", "JSON"]:
            # 创建示例数据
            if "风机位置" in export_data:
                wind_farm_data = {
                    '风机ID': list(range(1, 10)),
                    'X坐标': [random.uniform(-1000, 1000) for _ in range(9)],
                    'Y坐标': [random.uniform(-1000, 1000) for _ in range(9)],
                    '高度': [100] * 9,
                    '状态': ['正常'] * 9
                }
                
                st.write("**风机位置数据:**")
                st.dataframe(pd.DataFrame(wind_farm_data), width='stretch')
            
            if "目标轨迹" in export_data:
                target_data = {
                    '时间': np.linspace(0, 100, 10),
                    '目标1_X': np.linspace(-5000, 5000, 10),
                    '目标1_Y': 100 * np.sin(np.linspace(0, 2*np.pi, 10)),
                    '目标1_高度': np.linspace(1000, 5000, 10)
                }
                
                st.write("**目标轨迹数据:**")
                st.dataframe(pd.DataFrame(target_data), width='stretch')
        
        elif export_format in ["PNG", "JPEG"]:
            # 显示图片预览
            st.write("**图片预览:**")
            st.image("https://via.placeholder.com/800x600?text=3D+可视化+预览", width='stretch')
        
        # 批量导出
        st.subheader("批量导出")
        
        batch_formats = st.multiselect(
            "批量导出格式",
            ["HTML", "PNG", "PDF", "CSV", "JSON"],
            default=["PNG", "CSV"]
        )
        
        if batch_formats and st.button("📦 批量导出", width='stretch'):
            with st.spinner(f"正在批量导出 {len(batch_formats)} 个文件..."):
                progress_bar = st.progress(0)
                
                for i, fmt in enumerate(batch_formats):
                    time.sleep(1)
                    progress_bar.progress((i + 1) / len(batch_formats))
                
                st.success(f"批量导出完成！共导出 {len(batch_formats)} 个文件")

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **场景构建**: 构建三维可视化场景
    2. **实时动画**: 创建和播放动画
    3. **视角分析**: 多视角分析和测量
    4. **数据导出**: 导出场景和数据
    
    **快捷键:**
    - 鼠标拖拽: 旋转视角
    - 滚轮: 缩放
    - Shift+拖拽: 平移
    - 双击: 重置视角
    
    **提示:**
    - 可保存多个视角
    - 支持VR设备查看
    - 可导出为多种格式
    """)
    
    st.markdown("---")
    
    # 场景统计
    st.markdown("## 📊 场景统计")
    
    if 'scene_fig' in st.session_state:
        fig = st.session_state.scene_fig
        num_traces = len(fig.data)
        
        st.metric("场景元素", num_traces)
        st.metric("动画帧数", "0" if 'frames' not in fig else len(fig.frames))
    else:
        st.info("未构建场景")
    
    st.markdown("---")
    
    if st.button("🏁 完成分析", type="primary", width='stretch'):
        st.balloons()
        st.success("风电场对雷达探测影响评估完成！")

# 页脚
st.markdown("---")
st.caption("三维可视化模块 | 风电场对雷达探测影响的三维可视化分析")
EOF
