import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import plotly.graph_objects as go
import time
from datetime import datetime
import plotly.express as px

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

# 保留原有的类定义
class GuidanceSystem:
    """导引头基类"""
    def __init__(self, name, color, hex_color):
        self.name = name
        self.color = hex_color
        self.detection_range = 0
        self.jamming_resistance = 0
        self.stealth_level = 0
        
    def calculate_performance(self, target_range, jamming_power):
        pass

class PassiveRadarSeeker(GuidanceSystem):
    def __init__(self):
        super().__init__("被动雷达导引头", "passive", "#00f7ff")
        self.detection_range = 80
        self.jamming_resistance = 0.7
        self.stealth_level = 0.9
        self.description = "通过接收目标辐射的电磁波进行制导，具有出色的隐蔽性"
        
    def calculate_performance(self, target_range, jamming_power):
        base_range = self.detection_range
        jamming_effect = jamming_power * (1 - self.jamming_resistance)
        range_factor = max(0, 1 - (target_range / base_range)**2)
        performance = range_factor * (1 - jamming_effect)
        return max(0, performance)

class ActiveRadarSeeker(GuidanceSystem):
    def __init__(self):
        super().__init__("主动雷达导引头", "active", "#ff0066")
        self.detection_range = 100
        self.jamming_resistance = 0.4
        self.stealth_level = 0.2
        self.description = "主动发射雷达波探测目标，具有较高的探测精度"
        
    def calculate_performance(self, target_range, jamming_power):
        base_range = self.detection_range
        jamming_effect = jamming_power * (1 - self.jamming_resistance)
        range_factor = max(0, 1 - (target_range / base_range)**4)
        performance = range_factor * (1 - jamming_effect)
        return max(0, performance)

class CompositeSeeker(GuidanceSystem):
    def __init__(self):
        super().__init__("复合制导导引头", "composite", "#00ffaa")
        self.detection_range = 120
        self.jamming_resistance = 0.8
        self.stealth_level = 0.7
        self.description = "结合多种制导方式，具有较强的环境适应能力"
        
    def calculate_performance(self, target_range, jamming_power):
        base_range = self.detection_range
        if target_range > base_range * 0.6:
            jamming_effect = jamming_power * (1 - 0.8)
            range_factor = max(0, 1 - (target_range / base_range)**2)
        else:
            jamming_effect = jamming_power * (1 - 0.6)
            range_factor = max(0, 1 - (target_range / base_range)**3)
        performance = range_factor * (1 - jamming_effect)
        return max(0, performance)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    return 2 * atan2(sqrt(a), sqrt(1-a)) * R

def create_tech_map(missile_pos, target_pos, jammer_pos, seeker, jamming_power):
    center_lat = (missile_pos[0] + target_pos[0]) / 2
    center_lon = (missile_pos[1] + target_pos[1]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=8,
        # tiles='CartoDB dark_matter',
        # tiles='CartoDB Voyager',
        # attr='© CARTO'
    )
    
    # 计算距离
    missile_target_dist = calculate_distance(*missile_pos, *target_pos)
    missile_jammer_dist = calculate_distance(*missile_pos, *jammer_pos)
    
    # 自定义CSS样式
    html_style = """
    <style>
        .leaflet-popup-content {
            background: rgba(10, 15, 30, 0.95) !important;
            color: white !important;
            border-radius: 8px;
            padding: 10px;
            border: 1px solid rgba(0, 247, 255, 0.3);
        }
    </style>
    """
    
    # 导弹标记
    folium.Marker(
        missile_pos,
        popup=f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="color:{seeker.color}; margin:0 0 10px 0;">🚀 导弹</h4>
            <p style="margin:5px 0;"><b>导引头:</b> {seeker.name}</p>
            <p style="margin:5px 0;"><b>探测范围:</b> {seeker.detection_range}km</p>
        </div>
        """,
        tooltip="导弹",
        icon=folium.CustomIcon(
            icon_image='https://cdn-icons-png.flaticon.com/512/6062/6062646.png',
            icon_size=(40, 40)
        )
    ).add_to(m)
    
    # 目标标记
    folium.Marker(
        target_pos,
        popup=f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="color:#ff9900; margin:0 0 10px 0;">🎯 目标</h4>
            <p style="margin:5px 0;"><b>距离导弹:</b> {missile_target_dist:.1f}km</p>
        </div>
        """,
        tooltip="目标",
        icon=folium.CustomIcon(
            icon_image='https://cdn-icons-png.flaticon.com/512/2991/2991110.png',
            icon_size=(40, 40)
        )
    ).add_to(m)
    
    # 干扰源标记
    folium.Marker(
        jammer_pos,
        popup=f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="color:#cc00ff; margin:0 0 10px 0;">📡 干扰源</h4>
            <p style="margin:5px 0;"><b>干扰强度:</b> {jamming_power*100:.0f}%</p>
        </div>
        """,
        tooltip="干扰源",
        icon=folium.CustomIcon(
            icon_image='https://cdn-icons-png.flaticon.com/512/3050/3050525.png',
            icon_size=(40, 40)
        )
    ).add_to(m)
    
    # 探测范围
    folium.Circle(
        missile_pos,
        radius=seeker.detection_range * 1000,
        popup=f"{seeker.name}探测范围",
        color=seeker.color,
        fill=True,
        fill_opacity=0.1,
        weight=2,
        dash_array='5,5'
    ).add_to(m)
    
    # 连线
    folium.PolyLine(
        [missile_pos, target_pos],
        color=seeker.color,
        weight=3,
        opacity=0.7,
        dash_array='10,5',
        popup=f"攻击路径: {missile_target_dist:.1f}km"
    ).add_to(m)
    
    if missile_pos != jammer_pos:
        folium.PolyLine(
            [jammer_pos, missile_pos],
            color="#cc00ff",
            weight=2,
            opacity=0.5,
            dash_array='5,10',
            popup=f"干扰路径: {missile_jammer_dist:.1f}km"
        ).add_to(m)
    
    return m, missile_target_dist, missile_jammer_dist

def create_performance_gauge(performance_score, seeker_color):
    """创建性能仪表盘"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=performance_score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': "导引头效能评估",
            'font': {'size': 20, 'color': '#ffffff'}
        },
        number={
            'font': {'size': 40, 'color': '#ffffff'},
            'prefix': '<span style="font-size: 20px">效能</span><br>',
            'suffix': '%'
        },
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': '#ffffff',
                'tickfont': {'color': '#ffffff', 'size': 12}
            },
            'bar': {'color': seeker_color, 'thickness': 0.3},
            'bgcolor': 'rgba(0, 0, 0, 0)',
            'borderwidth': 2,
            'bordercolor': 'rgba(255, 255, 255, 0.2)',
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 0, 0, 0.3)'},
                {'range': [40, 70], 'color': 'rgba(255, 255, 0, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(0, 255, 0, 0.3)'}
            ],
            'threshold': {
                'line': {'color': seeker_color, 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#ffffff'},
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    return fig

def create_distance_performance_chart(ranges, performances, current_range, current_performance, seeker_color):
    """创建距离-性能曲线图"""
    fig = go.Figure()
    
    # 性能曲线
    fig.add_trace(go.Scatter(
        x=ranges, y=performances,
        mode='lines',
        name='性能曲线',
        line=dict(color=seeker_color, width=4),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(int(seeker_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}'
    ))
    
    # 当前状态点
    fig.add_trace(go.Scatter(
        x=[current_range], y=[current_performance],
        mode='markers+text',
        name='当前状态',
        marker=dict(color='#ffffff', size=20, line=dict(color=seeker_color, width=3)),
        text=[f"{current_performance:.1f}%"],
        textposition="top center",
        textfont=dict(color='#ffffff', size=14)
    ))
    
    fig.update_layout(
        title={
            'text': "距离-性能曲线分析",
            'font': {'color': '#ffffff', 'size': 18},
            'x': 0.5
        },
        xaxis=dict(
            title='目标距离 (km)',
            title_font=dict(color='#a0e7ff'),
            tickfont=dict(color='#a0e7ff'),
            gridcolor='rgba(255, 255, 255, 0.1)',
            zerolinecolor='rgba(255, 255, 255, 0.2)'
        ),
        yaxis=dict(
            title='导引头性能 (%)',
            title_font=dict(color='#a0e7ff'),
            tickfont=dict(color='#a0e7ff'),
            gridcolor='rgba(255, 255, 255, 0.1)',
            zerolinecolor='rgba(255, 255, 255, 0.2)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        showlegend=False,
        hoverlabel=dict(
            bgcolor='rgba(10, 15, 30, 0.9)',
            font_size=12,
            font_color='white'
        )
    )
    
    return fig

def main():
    st.set_page_config(
        page_title="导引头电子战仿真系统",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 标题区域
    st.markdown("""
    <div class="main-header">
        <h1>🎯 长城数字导引头电子战仿真系统</h1>
        <p>Advanced Guidance System EW Simulation Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'missile_lat' not in st.session_state:
        st.session_state.missile_lat = 35.0
    if 'missile_lon' not in st.session_state:
        st.session_state.missile_lon = 115.0
    if 'target_lat' not in st.session_state:
        st.session_state.target_lat = 36.0
    if 'target_lon' not in st.session_state:
        st.session_state.target_lon = 117.0
    
    # 侧边栏
    with st.sidebar:
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### ⚙️ 系统配置面板")
        
        # 导引头选择
        seeker_type = st.selectbox(
            "**导引头类型**",
            ["被动雷达导引头", "主动雷达导引头", "复合制导导引头"],
            index=0
        )
        
        seekers = {
            "被动雷达导引头": PassiveRadarSeeker(),
            "主动雷达导引头": ActiveRadarSeeker(),
            "复合制导导引头": CompositeSeeker()
        }
        
        current_seeker = seekers[seeker_type]
        
        st.markdown(f"""
        <div class="metric-display">
            <div style="color:#a0e7ff; font-size:0.9rem;">当前导引头</div>
            <div style="color:{current_seeker.color}; font-size:1.2rem; font-weight:bold;">{seeker_type}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 作战参数配置")
        
        # 目标参数
        col1, col2 = st.columns(2)
        with col1:
            target_lat = st.number_input(
                "目标纬度", 
                30.0, 40.0, 
                st.session_state.target_lat, 0.1,
                key="target_lat_input"
            )
        with col2:
            target_lon = st.number_input(
                "目标经度", 
                110.0, 120.0, 
                st.session_state.target_lon, 0.1,
                key="target_lon_input"
            )
        
        # 导弹参数
        st.markdown("##### 🚀 导弹初始位置")
        col1, col2 = st.columns(2)
        with col1:
            missile_lat = st.number_input(
                "导弹纬度", 
                30.0, 40.0, 
                st.session_state.missile_lat, 0.1,
                key="missile_lat_input"
            )
        with col2:
            missile_lon = st.number_input(
                "导弹经度", 
                110.0, 120.0, 
                st.session_state.missile_lon, 0.1,
                key="missile_lon_input"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### 📡 电子战环境配置")
        
        # 干扰设置
        jamming_type = st.radio(
            "**干扰模式**",
            ["目标自卫干扰", "远距离支援干扰"],
            index=0
        )
        
        jamming_power = st.slider(
            "**干扰强度**",
            0.0, 1.0, 0.3, 0.1,
            help="设置电子干扰强度级别"
        )
        
        if jamming_type == "远距离支援干扰":
            st.markdown("##### 📡 干扰源位置")
            col1, col2 = st.columns(2)
            with col1:
                jammer_lat = st.number_input("干扰源纬度", 30.0, 40.0, 37.0, 0.1)
            with col2:
                jammer_lon = st.number_input("干扰源经度", 110.0, 120.0, 113.0, 0.1)
        else:
            jammer_lat, jammer_lon = target_lat, target_lon
        
        st.markdown(f"""
        <div class="metric-display">
            <div style="color:#a0e7ff; font-size:0.9rem;">当前干扰强度</div>
            <div style="color:#ff0066; font-size:1.2rem; font-weight:bold;">{jamming_power*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ 仿真控制系统")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 开始仿真", width='stretch'):
                st.session_state.simulation_running = True
                st.success("仿真开始！")
        
        with col2:
            if st.button("🔄 重置系统", width='stretch'):
                for key in ['simulation_running', 'missile_lat', 'missile_lon']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        simulation_speed = st.slider("仿真速度", 1, 10, 5)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏸️ 暂停仿真", width='stretch'):
                st.session_state.simulation_running = False
                st.info("仿真已暂停")
        
        with col2:
            if st.button("📊 生成报告", width='stretch'):
                st.info("正在生成作战分析报告...")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 主界面布局
    col1, col2 = st.columns([7, 3])
    
    with col1:
        # 地图区域
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### 🗺️ 战场态势实时地图")
        
        missile_pos = [missile_lat, missile_lon]
        target_pos = [target_lat, target_lon]
        
        # 创建地图
        battle_map, missile_target_dist, missile_jammer_dist = create_tech_map(
            missile_pos, target_pos, [jammer_lat, jammer_lon], current_seeker, jamming_power
        )
        
        # 显示地图
        map_container = st.container()
        with map_container:
            st_folium(battle_map, width=800, height=450)
        
        # 战场信息指标
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">导弹-目标距离</div>
                <div style="color:#00ffaa; font-size:1.3rem; font-weight:bold;">{missile_target_dist:.1f} km</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info2:
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">导弹-干扰源距离</div>
                <div style="color:#cc00ff; font-size:1.3rem; font-weight:bold;">{missile_jammer_dist:.1f} km</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info3:
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">探测范围</div>
                <div style="color:{current_seeker.color}; font-size:1.3rem; font-weight:bold;">{current_seeker.detection_range} km</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info4:
            performance_score = current_seeker.calculate_performance(missile_target_dist, jamming_power)
            status_icon = "🟢" if performance_score > 0.7 else "🟡" if performance_score > 0.4 else "🔴"
            status_color = "#00ff00" if performance_score > 0.7 else "#ffff00" if performance_score > 0.4 else "#ff0000"
            
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">系统状态</div>
                <div style="color:{status_color}; font-size:1.3rem; font-weight:bold;">{status_icon} {performance_score*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 性能分析区域
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### 📈 导引头性能分析面板")
        
        tab1, tab2, tab3 = st.tabs(["📊 综合效能评估", "📉 距离-性能分析", "🔍 多导引头对比"])
        
        with tab1:
            # 性能仪表盘
            fig_gauge = create_performance_gauge(performance_score, current_seeker.color)
            st.plotly_chart(fig_gauge, width='stretch')
            
            # 性能参数网格
            col_params1, col_params2, col_params3 = st.columns(3)
            
            with col_params1:
                st.markdown(f"""
                <div class="metric-display" style="text-align: center;">
                    <div style="color:#a0e7ff; font-size:0.9rem;">抗干扰能力</div>
                    <div style="font-size:1.4rem; font-weight:bold; color:#00ffaa;">{current_seeker.jamming_resistance*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_params2:
                st.markdown(f"""
                <div class="metric-display" style="text-align: center;">
                    <div style="color:#a0e7ff; font-size:0.9rem;">隐蔽性</div>
                    <div style="font-size:1.4rem; font-weight:bold; color:#00ccff;">{current_seeker.stealth_level*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_params3:
                optimal_range = current_seeker.detection_range * 0.7
                st.markdown(f"""
                <div class="metric-display" style="text-align: center;">
                    <div style="color:#a0e7ff; font-size:0.9rem;">最佳攻击距离</div>
                    <div style="font-size:1.4rem; font-weight:bold; color:#ff9900;">{optimal_range:.0f} km</div>
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            # 距离-性能曲线
            ranges = np.linspace(10, 200, 50)
            performances = [current_seeker.calculate_performance(r, jamming_power)*100 for r in ranges]
            
            fig_chart = create_distance_performance_chart(
                ranges, performances, missile_target_dist, performance_score*100, current_seeker.color
            )
            st.plotly_chart(fig_chart, width='stretch')
        
        with tab3:
            # 导引头对比
            comparison_data = []
            colors = ["#00f7ff", "#ff0066", "#00ffaa"]
            
            for idx, (name, seeker) in enumerate(seekers.items()):
                score = seeker.calculate_performance(missile_target_dist, jamming_power)
                comparison_data.append({
                    '导引头类型': name,
                    '性能评分': score*100,
                    '探测距离(km)': seeker.detection_range,
                    '抗干扰(%)': seeker.jamming_resistance*100,
                    '隐蔽性(%)': seeker.stealth_level*100,
                    '颜色': colors[idx]
                })
            
            # 创建雷达图
            categories = ['探测距离', '抗干扰', '隐蔽性', '适应性']
            
            fig_radar = go.Figure()
            
            for i, (name, seeker) in enumerate(seekers.items()):
                values = [
                    seeker.detection_range / 120 * 100,  # 归一化
                    seeker.jamming_resistance * 100,
                    seeker.stealth_level * 100,
                    (seeker.jamming_resistance + seeker.stealth_level) * 50
                ]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=values + [values[0]],  # 闭合图形
                    theta=categories + [categories[0]],
                    name=name,
                    fill='toself',
                    line_color=colors[i],
                    opacity=0.7
                ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(color='#a0e7ff')
                    ),
                    angularaxis=dict(
                        tickfont=dict(color='#a0e7ff')
                    ),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=True,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ffffff'),
                height=400
            )
            
            st.plotly_chart(fig_radar, width='stretch')
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # 右侧面板 - 导引头详情
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 导引头详情")
        
        # 导引头信息卡片
        st.markdown(f"""
        <div style="background: rgba(0, 20, 40, 0.6); padding: 1rem; border-radius: 8px; border-left: 4px solid {current_seeker.color}; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <div style="width: 20px; height: 20px; background: {current_seeker.color}; border-radius: 50%; margin-right: 10px;"></div>
                <h4 style="color: {current_seeker.color}; margin: 0;">{current_seeker.name}</h4>
            </div>
            <p style="color: #a0e7ff; font-size: 0.9rem; margin: 0;">{current_seeker.description}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 参数指标
        st.markdown("##### 📊 技术参数")
        
        param_col1, param_col2 = st.columns(2)
        
        with param_col1:
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">最大探测距离</div>
                <div style="font-size:1.2rem; font-weight:bold;">{current_seeker.detection_range} km</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">工作频率</div>
                <div style="font-size:1.2rem; font-weight:bold;">X波段</div>
            </div>
            """, unsafe_allow_html=True)
        
        with param_col2:
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">抗干扰能力</div>
                <div style="font-size:1.2rem; font-weight:bold;">{current_seeker.jamming_resistance*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.9rem;">制导精度</div>
                <div style="font-size:1.2rem; font-weight:bold;">&lt; 5m</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 战术建议面板
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### 💡 智能战术建议")
        
        if performance_score > 0.7:
            status_class = "status-good"
            status_text = "作战条件优良"
            st.markdown(f"""
            <div style="background: rgba(0, 100, 0, 0.2); padding: 1rem; border-radius: 8px; border-left: 4px solid #00ff00; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <div class="status-led {status_class.replace('status-', '')}"></div>
                    <h4 style="color: #00ff00; margin: 0;">✓ {status_text}</h4>
                </div>
                <ul style="color: #a0e7ff; padding-left: 1.2rem; margin: 0;">
                    <li>导引头性能达到最优</li>
                    <li>建议立即执行打击任务</li>
                    <li>可保持当前攻击航线</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif performance_score > 0.4:
            status_class = "status-warning"
            status_text = "性能受限"
            st.markdown(f"""
            <div style="background: rgba(100, 100, 0, 0.2); padding: 1rem; border-radius: 8px; border-left: 4px solid #ffff00; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <div class="status-led {status_class.replace('status-', '')}"></div>
                    <h4 style="color: #ffff00; margin: 0;">⚠️ {status_text}</h4>
                </div>
                <ul style="color: #a0e7ff; padding-left: 1.2rem; margin: 0;">
                    <li>考虑调整攻击角度</li>
                    <li>评估干扰规避路径</li>
                    <li>准备备用制导模式</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            status_class = "status-critical"
            status_text = "作战条件恶劣"
            st.markdown(f"""
            <div style="background: rgba(100, 0, 0, 0.2); padding: 1rem; border-radius: 8px; border-left: 4px solid #ff0000; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <div class="status-led {status_class.replace('status-', '')}"></div>
                    <h4 style="color: #ff0000; margin: 0;">✗ {status_text}</h4>
                </div>
                <ul style="color: #a0e7ff; padding-left: 1.2rem; margin: 0;">
                    <li>建议终止当前任务</li>
                    <li>启用电子对抗措施</li>
                    <li>请求火力支援</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # 详细建议
        with st.expander("📋 详细作战建议", expanded=True):
            if seeker_type == "被动雷达导引头":
                st.info("""
                **被动雷达导引头战术建议:**
                - 🎯 利用隐蔽性进行突袭
                - 📡 优先攻击辐射强烈的目标
                - 🚫 避免在雷达静默区域作战
                - 🗺️ 建议攻击路径: 从目标雷达盲区接近
                """)
            elif seeker_type == "主动雷达导引头":
                st.info("""
                **主动雷达导引头战术建议:**
                - 🎯 适合中近距离交战
                - 🚀 具备"发射后不管"能力
                - ⚡ 注意避免过早暴露
                - 🗺️ 建议攻击路径: 高速接近，缩短暴露时间
                """)
            else:
                st.info("""
                **复合制导导引头战术建议:**
                - 📡 远距离使用被动模式
                - 🎯 近距离切换主动模式
                - 🔄 具备强环境适应能力
                - 🗺️ 建议攻击路径: 结合地形掩护
                """)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 系统状态面板
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        st.markdown("### ⚡ 系统状态监控")
        
        # 实时数据
        st.markdown("##### 📈 实时数据")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.8rem;">仿真速度</div>
                <div style="font-size:1.1rem; font-weight:bold;">{simulation_speed}x</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-display">
                <div style="color:#a0e7ff; font-size:0.8rem;">更新时间</div>
                <div style="font-size:0.9rem; font-weight:bold;">{datetime.now().strftime("%H:%M:%S")}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 系统状态指示
        st.markdown("##### 🔧 子系统状态")
        
        systems = [
            ("地图系统", "online", "#00ff00"),
            ("导引头", "online", "#00ff00"),
            ("仿真引擎", "online", "#00ff00"),
            ("数据记录", "online", "#00ff00"),
            ("网络连接", "online", "#00ff00")
        ]
        
        for system, status, color in systems:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f'<div style="color:#a0e7ff;">{system}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div style="color:{color}; text-align:right;">● {status}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 底部状态栏
    st.markdown("""
    <div style="background: rgba(0, 0, 0, 0.5); padding: 1rem; border-radius: 8px; margin-top: 2rem; border-top: 1px solid rgba(0, 247, 255, 0.2);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color: #a0e7ff;">系统状态: </span>
                <span style="color: #00ff00;">● 运行正常</span>
                <span style="margin-left: 2rem; color: #a0e7ff;">导引头: </span>
                <span style="color: {color};">{seeker}</span>
            </div>
            <div>
                <span style="color: #a0e7ff;">最后更新: </span>
                <span style="color: #ffffff;">{time}</span>
            </div>
        </div>
    </div>
    """.format(
        color=current_seeker.color,
        seeker=seeker_type,
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ), unsafe_allow_html=True)

if __name__ == "__main__":
    main()