import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
from math import sqrt, sin, cos, radians



# 设置页面配置
st.set_page_config(
    page_title="风电场对雷达探测影响模拟系统",
    page_icon="🌬️",
    layout="wide"
)

# 初始化会话状态
if 'turbines' not in st.session_state:
    st.session_state.turbines = []
if 'targets' not in st.session_state:
    st.session_state.targets = []
if 'radar' not in st.session_state:
    st.session_state.radar = {'position': [0, 0, 50], 'range': 10000}
if 'simulation_time' not in st.session_state:
    st.session_state.simulation_time = 0

class WindTurbine:
    """风机类"""
    def __init__(self, position, height=100, rotor_diameter=80):
        self.position = position
        self.height = height
        self.rotor_diameter = rotor_diameter
        self.hub_height = height
        self.blade_length = rotor_diameter / 2
        self.id = len(st.session_state.turbines)
    
    def get_3d_points(self):
        """获取风机3D模型的点"""
        x, y, z_base = self.position
        
        # 塔筒（圆柱体，用多个点表示）
        theta = np.linspace(0, 2*np.pi, 8)
        tower_radius = 2
        
        # 塔筒底部
        tower_bottom_x = x + tower_radius * np.cos(theta)
        tower_bottom_y = y + tower_radius * np.sin(theta)
        tower_bottom_z = np.full_like(theta, 0)
        
        # 塔筒顶部
        tower_top_x = x + tower_radius * np.cos(theta)
        tower_top_y = y + tower_radius * np.sin(theta)
        tower_top_z = np.full_like(theta, self.height)
        
        # 机舱（球体）
        nacelle_center = [x, y, self.height]
        nacelle_radius = 3
        
        # 叶片（圆锥体简化）
        blades = []
        for i in range(3):
            angle = i * 120
            blade_length = self.blade_length
            blade_tip_x = x + blade_length * np.cos(radians(angle))
            blade_tip_y = y + blade_length * np.sin(radians(angle))
            blade_tip_z = self.height
            
            blades.append({
                'base': [x, y, self.height],
                'tip': [blade_tip_x, blade_tip_y, blade_tip_z]
            })
        
        return {
            'tower': {
                'x': np.concatenate([tower_bottom_x, tower_top_x]),
                'y': np.concatenate([tower_bottom_y, tower_top_y]),
                'z': np.concatenate([tower_bottom_z, tower_top_z])
            },
            'nacelle': nacelle_center,
            'blades': blades
        }

class Target:
    """目标类"""
    def __init__(self, position, velocity, rcs=1.0, target_type='无人机'):
        self.position = position
        self.velocity = velocity
        self.rcs = rcs
        self.type = target_type
        self.id = len(st.session_state.targets)
        self.trajectory = [position.copy()]
    
    def move(self, dt):
        """目标移动"""
        new_pos = [
            self.position[0] + self.velocity[0] * dt,
            self.position[1] + self.velocity[1] * dt,
            self.position[2] + self.velocity[2] * dt
        ]
        self.position = new_pos
        self.trajectory.append(new_pos.copy())
        return new_pos

def create_wind_farm(num_turbines, spacing, turbine_params):
    """创建风电场"""
    turbines = []
    rows = int(sqrt(num_turbines))
    cols = int(sqrt(num_turbines))
    
    for i in range(rows):
        for j in range(cols):
            if len(turbines) >= num_turbines:
                break
            x = (i - rows/2) * spacing * 10 + 5000
            y = (j - cols/2) * spacing * 10 + 5000
            turbines.append(WindTurbine(
                [x, y, 0],
                turbine_params['height'],
                turbine_params['diameter']
            ))
    
    return turbines

def create_targets(num_targets, area_size, target_types):
    """创建目标"""
    targets = []
    for i in range(num_targets):
        target_type = random.choice(target_types)
        rcs_map = {'无人机': 0.1, '战斗机': 5.0, '客机': 10.0, '直升机': 2.0}
        
        x = random.uniform(-area_size, area_size)
        y = random.uniform(-area_size, area_size)
        z = random.uniform(100, 2000)
        
        vx = random.uniform(-100, 100)
        vy = random.uniform(-100, 100)
        vz = random.uniform(-5, 5)
        
        targets.append(Target(
            [x, y, z],
            [vx, vy, vz],
            rcs=rcs_map[target_type],
            target_type=target_type
        ))
    
    return targets

def calculate_line_of_sight(radar_pos, target_pos, turbines):
    """计算雷达与目标之间的视线"""
    radar_x, radar_y, radar_z = radar_pos
    target_x, target_y, target_z = target_pos
    
    line_of_sight_clear = True
    blocking_turbine = None
    occlusion_factor = 0.0
    
    for turbine in turbines:
        tx, ty, tz_base = turbine.position
        turbine_height = turbine.height + turbine.blade_length
        
        # 计算视线与风机圆柱体的交点
        # 简化模型：检查目标是否在风机后面且被遮挡
        dx = target_x - radar_x
        dy = target_y - radar_y
        dz = target_z - radar_z
        
        # 计算参数t，表示在视线上的位置
        t = ((tx - radar_x) * dx + (ty - radar_y) * dy) / (dx**2 + dy**2) if (dx**2 + dy**2) != 0 else 0
        
        if 0 <= t <= 1:  # 风机在雷达和目标之间
            # 计算最近点
            closest_x = radar_x + t * dx
            closest_y = radar_y + t * dy
            
            # 计算距离
            distance = sqrt((closest_x - tx)**2 + (closest_y - ty)**2)
            
            # 如果距离小于风机半径，且高度在范围内
            if distance <= turbine.rotor_diameter/2:
                # 计算视线高度
                line_z = radar_z + t * dz
                
                if 0 <= line_z <= turbine_height:
                    line_of_sight_clear = False
                    blocking_turbine = turbine.id
                    occlusion_factor = 0.7  # 70%信号衰减
                    break
    
    return line_of_sight_clear, blocking_turbine, occlusion_factor

def calculate_snr(radar_power, radar_freq, target_rcs, distance, occlusion_factor):
    """计算信噪比"""
    wavelength = 3e8 / radar_freq
    
    # 简化的雷达方程
    snr_base = (radar_power * target_rcs * wavelength**2) / \
               ((4*np.pi)**3 * (distance**4))
    
    # 应用遮挡衰减
    snr = snr_base * (1 - occlusion_factor)
    
    return snr

def create_3d_plot(turbines, targets, radar_pos, detection_status):
    """创建3D可视化图"""
    fig = go.Figure()
    
    # 添加风机
    for turbine in turbines:
        points = turbine.get_3d_points()
        
        # 塔筒
        fig.add_trace(go.Mesh3d(
            x=points['tower']['x'],
            y=points['tower']['y'],
            z=points['tower']['z'],
            color='gray',
            opacity=0.7,
            name=f'风机 {turbine.id}',
            showlegend=False
        ))
        
        # 机舱
        fig.add_trace(go.Scatter3d(
            x=[points['nacelle'][0]],
            y=[points['nacelle'][1]],
            z=[points['nacelle'][2]],
            mode='markers',
            marker=dict(size=5, color='blue'),
            name='机舱',
            showlegend=False
        ))
        
        # 叶片
        for blade in points['blades']:
            fig.add_trace(go.Scatter3d(
                x=[blade['base'][0], blade['tip'][0]],
                y=[blade['base'][1], blade['tip'][1]],
                z=[blade['base'][2], blade['tip'][2]],
                mode='lines',
                line=dict(color='lightblue', width=3),
                showlegend=False
            ))
    
    # 添加雷达
    fig.add_trace(go.Scatter3d(
        x=[radar_pos[0]],
        y=[radar_pos[1]],
        z=[radar_pos[2]],
        mode='markers+lines',
        marker=dict(size=10, color='red', symbol='diamond'),
        line=dict(color='red', width=2),
        name='雷达'
    ))
    
    # 添加目标
    colors = {'可探测': 'green', '被遮挡': 'orange', '信号弱': 'gray'}
    for i, target in enumerate(targets):
        status = detection_status[i]['状态']
        
        # 目标点
        fig.add_trace(go.Scatter3d(
            x=[target.position[0]],
            y=[target.position[1]],
            z=[target.position[2]],
            mode='markers+text',
            marker=dict(size=8, color=colors[status]),
            text=[f'目标{i+1}'],
            textposition="top center",
            name=f'目标{i+1} ({status})'
        ))
        
        # 轨迹
        if len(target.trajectory) > 1:
            traj_x = [p[0] for p in target.trajectory]
            traj_y = [p[1] for p in target.trajectory]
            traj_z = [p[2] for p in target.trajectory]
            
            fig.add_trace(go.Scatter3d(
                x=traj_x,
                y=traj_y,
                z=traj_z,
                mode='lines',
                line=dict(color=colors[status], width=1, dash='dot'),
                showlegend=False
            ))
        
        # 雷达-目标连线
        if detection_status[i]['visible']:
            line_color = 'limegreen' if status == '可探测' else 'orange'
            fig.add_trace(go.Scatter3d(
                x=[radar_pos[0], target.position[0]],
                y=[radar_pos[1], target.position[1]],
                z=[radar_pos[2], target.position[2]],
                mode='lines',
                line=dict(color=line_color, width=2),
                showlegend=False
            ))
    
    # 设置3D场景
    fig.update_layout(
        scene=dict(
            xaxis_title='X (米)',
            yaxis_title='Y (米)',
            zaxis_title='Z (米)',
            aspectmode='manual',
            aspectratio=dict(x=2, y=2, z=1),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1)
            )
        ),
        title='风电场对雷达探测影响三维可视化',
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def main():

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
    
    # st.title("🌬️ 风电场对雷达探测目标影响模拟系统")
    st.markdown("""
    <div class="main-header">
        <h1>🌬️ 风电场对雷达探测目标影响模拟系统</h1>
    </div>
        """, unsafe_allow_html=True)
    # 侧边栏控制面板
    with st.sidebar:
        st.header("控制面板")
        
        # 风电场设置
        st.subheader("风电场设置")
        num_turbines = st.slider("风机数量", 1, 36, 9)
        turbine_spacing = st.slider("风机间距(米)", 100, 500, 200)
        turbine_height = st.slider("风机高度(米)", 50, 200, 100)
        rotor_diameter = st.slider("转子直径(米)", 50, 150, 80)
        
        # 目标设置
        st.subheader("目标设置")
        num_targets = st.slider("目标数量", 1, 20, 5)
        target_types = st.multiselect(
            "目标类型",
            ['无人机', '战斗机', '客机', '直升机'],
            default=['无人机', '战斗机']
        )
        
        # 雷达设置
        st.subheader("雷达设置")
        col1, col2, col3 = st.columns(3)
        with col1:
            radar_x = st.number_input("雷达X(米)", -5000, 5000, 0)
        with col2:
            radar_y = st.number_input("雷达Y(米)", -5000, 5000, 0)
        with col3:
            radar_z = st.number_input("雷达高度(米)", 0, 200, 50)
        
        radar_range = st.slider("探测范围(米)", 1000, 20000, 10000)
        radar_power = st.select_slider(
            "雷达功率(kW)",
            options=[10, 50, 100, 500, 1000, 5000],
            value=1000
        )
        
        freq_options = {
            'L波段(1-2GHz)': 1.5e9,
            'S波段(2-4GHz)': 3e9,
            'C波段(4-8GHz)': 6e9,
            'X波段(8-12GHz)': 10e9
        }
        radar_freq_label = st.selectbox(
            "雷达频段",
            list(freq_options.keys())
        )
        radar_freq = freq_options[radar_freq_label]
        
        # 环境设置
        st.subheader("环境设置")
        weather = st.selectbox(
            "天气条件",
            ['晴朗', '多云', '小雨', '中雨', '大雨', '雾']
        )
        
        weather_attenuation = {
            '晴朗': 0.0,
            '多云': 0.1,
            '小雨': 0.3,
            '中雨': 0.5,
            '大雨': 0.7,
            '雾': 0.4
        }
        
        # 模拟控制
        st.subheader("模拟控制")
        col1, col2 = st.columns(2)
        with col1:
            simulate_btn = st.button("开始模拟", type="primary", width='stretch')
        with col2:
            if st.button("重置场景", width='stretch'):
                st.session_state.turbines = []
                st.session_state.targets = []
                st.session_state.simulation_time = 0
                st.rerun()
        
        if simulate_btn:
            turbine_params = {
                'height': turbine_height,
                'diameter': rotor_diameter
            }
            st.session_state.turbines = create_wind_farm(
                num_turbines, turbine_spacing, turbine_params
            )
            target_area= st.session_state.turbines[0].position[0] + np.random.randint(500, 5000)
            # target_y_area= st.session_state.turbines[0].position[1] + np.random.randint(-1000, 1000)
            st.session_state.targets = create_targets(
                num_targets, target_area, target_types
            )
            st.session_state.radar = {
                'position': [radar_x, radar_y, radar_z],
                'range': radar_range,
                'power': radar_power * 1000,  # 转换为瓦特
                'frequency': radar_freq
            }
            st.session_state.weather = weather
    
    # 主显示区域
    if st.session_state.turbines and st.session_state.targets:
        turbines = st.session_state.turbines
        targets = st.session_state.targets
        radar = st.session_state.radar
        
        # 模拟时间步进
        if 'simulation_time' in st.session_state:
            dt = 1  # 1秒时间步长
            for target in targets:
                target.move(dt)
            st.session_state.simulation_time += dt
        
        # 计算探测状态
        detection_data = []
        weather_atten = weather_attenuation.get(st.session_state.get('weather', '晴朗'), 0.0)
        
        for i, target in enumerate(targets):
            # 计算距离
            distance = np.sqrt(
                (target.position[0] - radar['position'][0])**2 +
                (target.position[1] - radar['position'][1])**2 +
                (target.position[2] - radar['position'][2])**2
            )
            
            # 检查视线
            los_clear, blocking_turbine, occlusion_factor = calculate_line_of_sight(
                radar['position'], target.position, turbines
            )
            
            # 计算信噪比
            total_attenuation = occlusion_factor + weather_atten
            snr = calculate_snr(
                radar['power'], radar['frequency'],
                target.rcs, distance, total_attenuation
            )
            
            # 确定探测状态
            if not los_clear:
                status = "被遮挡"
                visible = False
            elif snr > 1e-12:  # 可探测阈值
                status = "可探测"
                visible = True
            elif distance > radar['range']:
                status = "超出范围"
                visible = False
            else:
                status = "信号弱"
                visible = False
            
            detection_data.append({
                '目标ID': i + 1,
                '目标类型': target.type,
                '位置X': f"{target.position[0]:.0f}",
                '位置Y': f"{target.position[1]:.0f}",
                '高度': f"{target.position[2]:.0f}",
                '距离': f"{distance:.0f}",
                'RCS': f"{target.rcs:.1f} m²",
                '状态': status,
                '遮挡风机': f"#{blocking_turbine + 1}" if blocking_turbine is not None else "无",
                '信噪比(dB)': f"{10 * np.log10(snr) if snr > 0 else -np.inf:.1f}",
                'visible': visible
            })
        
        # 创建布局
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 3D可视化
            fig = create_3d_plot(turbines, targets, radar['position'], detection_data)
            st.plotly_chart(fig, width='stretch', theme=None)
            
            # 雷达覆盖图
            st.subheader("雷达覆盖范围")
            fig2d = go.Figure()
            
            # 添加风机位置
            turbine_x = [t.position[0] for t in turbines]
            turbine_y = [t.position[1] for t in turbines]
            fig2d.add_trace(go.Scatter(
                x=turbine_x, y=turbine_y,
                mode='markers',
                marker=dict(size=10, color='blue', symbol='square'),
                name='风机'
            ))
            
            # 添加目标位置
            for i, target in enumerate(targets):
                color = 'green' if detection_data[i]['状态'] == '可探测' else \
                       'orange' if detection_data[i]['状态'] == '被遮挡' else 'gray'
                fig2d.add_trace(go.Scatter(
                    x=[target.position[0]],
                    y=[target.position[1]],
                    mode='markers+text',
                    marker=dict(size=8, color=color),
                    text=[f"目标{i+1}"],
                    textposition="top center",
                    name=f'目标{i+1}'
                ))
            
            # 添加雷达位置
            fig2d.add_trace(go.Scatter(
                x=[radar['position'][0]],
                y=[radar['position'][1]],
                mode='markers',
                marker=dict(size=12, color='red', symbol='star'),
                name='雷达'
            ))
            
            # 雷达覆盖范围圆
            theta = np.linspace(0, 2*np.pi, 100)
            circle_x = radar['position'][0] + radar['range'] * np.cos(theta)
            circle_y = radar['position'][1] + radar['range'] * np.sin(theta)
            fig2d.add_trace(go.Scatter(
                x=circle_x, y=circle_y,
                mode='lines',
                line=dict(color='red', width=1, dash='dash'),
                fill='none',
                name='探测范围'
            ))
            
            fig2d.update_layout(
                title='雷达覆盖范围（俯视图）',
                xaxis_title='X (米)',
                yaxis_title='Y (米)',
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig2d, width='stretch', theme=None)
        
        with col2:
            # 数据显示
            st.subheader("目标探测状态")
            df = pd.DataFrame(detection_data)
            st.dataframe(df[['目标ID', '目标类型', '状态', '距离', '信噪比(dB)', '遮挡风机']], 
                        width='stretch')
            
            # 统计信息
            st.subheader("统计信息")
            detected = sum(1 for d in detection_data if d['状态'] == '可探测')
            occluded = sum(1 for d in detection_data if d['状态'] == '被遮挡')
            weak = sum(1 for d in detection_data if d['状态'] == '信号弱')
            out_of_range = sum(1 for d in detection_data if d['状态'] == '超出范围')
            
            cols_stats = st.columns(2)
            cols_stats[0].metric("可探测目标", detected)
            cols_stats[1].metric("被遮挡目标", occluded)
            cols_stats[0].metric("信号弱目标", weak)
            cols_stats[1].metric("超出范围", out_of_range)
            
            # 探测率
            detection_rate = detected / len(detection_data) * 100
            st.metric("探测率", f"{detection_rate:.1f}%")
            
            # 时间显示
            st.info(f"模拟时间: {st.session_state.simulation_time}秒")
            
            # 状态分布饼图
            st.subheader("探测状态分布")
            status_counts = {
                '可探测': detected,
                '被遮挡': occluded,
                '信号弱': weak,
                '超出范围': out_of_range
            }
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                hole=0.3
            )])
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, width='stretch', theme=None)
            
            # 信噪比分布
            st.subheader("信噪比分布")
            snr_values = []
            for d in detection_data:
                try:
                    snr_db = float(d['信噪比(dB)'].replace(' dB', ''))
                    if snr_db != -np.inf:
                        snr_values.append(snr_db)
                except:
                    continue
            
            if snr_values:
                fig_hist = go.Figure(data=[go.Histogram(x=snr_values, nbinsx=20)])
                fig_hist.update_layout(
                    xaxis_title='信噪比 (dB)',
                    yaxis_title='数量',
                    height=300
                )
                st.plotly_chart(fig_hist, width='stretch', theme=None)
            
            # 下载数据按钮
            csv = df.to_csv(index=False)
            st.download_button(
                label="下载探测数据 (CSV)",
                data=csv,
                file_name="radar_detection_data.csv",
                mime="text/csv"
            )
    else:
        # 初始状态显示
        st.info("👈 请在左侧面板配置参数并点击'开始模拟'按钮")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("系统功能介绍")
            st.markdown("""
            1. **风电场建模**
               - 可配置风机数量、高度、间距
               - 3D可视化展示风机布局
            
            2. **雷达探测模拟**
               - 支持多频段雷达配置
               - 计算雷达方程和信噪比
            
            3. **目标探测分析**
               - 视线遮挡计算
               - 天气影响模拟
               - 实时状态监控
            
            4. **数据分析**
               - 探测率统计
               - 信号质量分析
               - 数据导出功能
            """)
        
        with col2:
            st.subheader("目标类型参数")
            target_params = pd.DataFrame({
                '目标类型': ['无人机', '战斗机', '客机', '直升机'],
                'RCS范围(m²)': ['0.01-0.5', '1-10', '10-100', '1-5'],
                '典型速度(m/s)': ['10-50', '200-600', '200-300', '0-50'],
                '飞行高度(m)': ['50-1000', '100-15000', '500-12000', '0-3000']
            })
            st.dataframe(target_params, width='stretch')
            
            st.subheader("雷达频段特性")
            radar_bands = pd.DataFrame({
                '频段': ['L波段', 'S波段', 'C波段', 'X波段'],
                '频率范围(GHz)': ['1-2', '2-4', '4-8', '8-12'],
                '典型用途': ['远程预警', '中程搜索', '火控雷达', '精确制导'],
                '抗雨衰能力': ['强', '中', '较弱', '弱']
            })
            st.dataframe(radar_bands, width='stretch')

if __name__ == "__main__":
    main()