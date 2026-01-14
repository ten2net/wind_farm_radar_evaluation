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

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    .stMetric {
        padding: 8px 0;
    }
    
    .stMetric label {
        font-size: 0.9rem !important;
    }
    
    .stMetric div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    .stMetric div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }  
    
    .stSlider > div {
        padding: 0.5rem 0;
    }
    
    /* 滑块轨道 */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, rgba(0, 150, 255, 0.1), rgba(0, 150, 255, 0.3));
        height: 6px;
        border-radius: 3px;
    }
    
    /* 滑块轨道填充部分（已选择部分） */
    .stSlider > div > div > div > div > div {
        background: linear-gradient(90deg, 
            rgba(0, 200, 255, 0.7), 
            rgba(0, 150, 255, 0.9));
        height: 6px;
        border-radius: 3px 0 0 3px;
    }
    
    /* 滑块轨道未填充部分 */
    .stSlider > div > div > div > div > div > div {
        background: rgba(100, 100, 150, 0.3);
        height: 6px;
        border-radius: 0 3px 3px 0;
    }
    
    /* 滑块圆点 */
    .stSlider > div > div > div > div > div > div > div {
        background: linear-gradient(135deg, 
            rgba(0, 200, 255, 1), 
            rgba(0, 100, 200, 1));
        border: 2px solid rgba(200, 220, 255, 0.8);
        box-shadow: 0 0 10px rgba(0, 150, 255, 0.5);
        width: 20px;
        height: 20px;
        transform: translateY(-7px);
    }
    
    /* 滑块圆点悬停效果 */
    .stSlider > div > div > div > div > div > div > div:hover {
        background: linear-gradient(135deg, 
            rgba(0, 220, 255, 1), 
            rgba(0, 120, 220, 1));
        box-shadow: 0 0 15px rgba(0, 180, 255, 0.8);
        transform: translateY(-7px) scale(1.1);
        transition: all 0.2s ease;
    }
    
    /* 滑块标签样式 */
    .stSlider label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #a0c8ff;
        margin-bottom: 0.3rem;
    }
    
    /* 滑块数值显示 */
    .stSlider > div > div > div + div {
        color: #00ccff;
        font-size: 0.9rem;
        font-weight: 600;
        text-shadow: 0 0 5px rgba(0, 150, 255, 0.5);
    }
    
    /* 滑块容器的背景 */
    .stSlider {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    /* 滑块容器悬停效果 */
    .stSlider:hover {
        background: rgba(25, 30, 50, 0.4);
        border-color: rgba(0, 150, 255, 0.3);
        box-shadow: 0 0 20px rgba(0, 100, 200, 0.1);
    }
    
    /* 数字输入框样式 */
    .stNumberInput {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
    }
    
    .stNumberInput label {
        color: #a0c8ff;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .stNumberInput input {
        color: #00ccff;
        background: rgba(10, 20, 40, 0.5);
        border: 1px solid rgba(0, 100, 200, 0.3);
        border-radius: 4px;
    }
    
    /* 选择框样式 */
    .stSelectbox {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
    }
    
    .stSelectbox label {
        color: #a0c8ff;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .stSelectbox > div > div {
        background: rgba(10, 20, 40, 0.5);
        border: 1px solid rgba(0, 100, 200, 0.3);
        color: #00ccff;
    }
    
    /* 选项卡样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: rgba(20, 25, 45, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        color: #a0c8ff;
        font-weight: 500;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, 
            rgba(0, 150, 255, 0.3), 
            rgba(0, 100, 200, 0.5));
        color: #00ccff;
        box-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
    }
    
    /* 调整间距 */
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 100, 200, 0.2);
    }
    
    /* 调整整体容器间距 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #a0d8ff;
        text-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
    }
    
    /* 分隔线样式 */
    hr {
        border-color: rgba(0, 100, 200, 0.2);
        margin: 1.5rem 0;
    }      
</style>
""", unsafe_allow_html=True)

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
    
    if st.button("🔄 保存配置到会话", type="primary"):
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
            # 确保所有值都是字符串类型
            config_df1 = pd.DataFrame({
                '参数': ['风机高度', '转子直径', '风机类型', '额定功率', '塔筒材料'],
                '数值': [
                    str(turbine_height) + " 米",
                    str(rotor_diameter) + " 米",
                    str(turbine_type),
                    str(rated_power) + " MW",
                    str(material)
                ]
            })
            st.dataframe(config_df1, width='stretch', hide_index=True)
        
        with col2:
            st.subheader("布局参数")
            # 确保所有值都是字符串类型
            config_df2 = pd.DataFrame({
                '参数': ['布局类型', '风机数量', '风机间距', '行数×列数', '地形类型'],
                '数值': [
                    str(layout_type),
                    str(num_turbines),
                    str(spacing) + " 米",
                    f"{rows} × {cols}",
                    str(terrain_type)
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
        import json
        config_json = {
            'wind_farm': st.session_state.wind_farm_config
        }
        
        st.download_button(
            label="📥 下载配置 (JSON)",
            data=json.dumps(config_json, ensure_ascii=False, indent=2),
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
        st.switch_page("pages/2_📡 雷达参数配置.py")

# 页脚
st.markdown("---")
st.caption("风电场建模模块 | 用于雷达影响评估的风电场参数配置")