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
                 course=0.0, maneuver_type="直线飞行", trajectory_params=None):
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
        self.trajectory_params = trajectory_params or {}
        
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
            'timestamp': self.timestamp,
            'trajectory_params': self.trajectory_params
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
    # 起点
    fig.add_trace(go.Scatter3d(
        x=[x_traj[0]],
        y=[y_traj[0]],
        z=[z_traj[0]],
        mode='markers',
        marker=dict(size=8, color='green', symbol='circle'),
        name='起点'
    ))
    
    # 终点
    fig.add_trace(go.Scatter3d(
        x=[x_traj[-1]],
        y=[y_traj[-1]],
        z=[z_traj[-1]],
        mode='markers',
        marker=dict(size=8, color='blue', symbol='diamond'),
        name='终点'
    ))
    
    # 添加轨迹方向指示
    if len(x_traj) > 5:
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
                colorscale=[[0, 'red'], [1, 'red']],
                name='方向指示'
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
    
    # 保存当前目标配置
    st.markdown("## 💾 保存目标配置")
    
    # 创建保存配置的表单
    with st.form("save_target_config_form"):
        config_name = st.text_input("配置名称", value="目标配置")
        config_description = st.text_area("配置描述", value="当前目标参数配置")
        
        if st.form_submit_button("保存目标配置到会话", width='stretch'):
            # 收集当前所有参数
            current_config = {
                'name': config_name,
                'description': config_description,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'targets': []
            }
            
            # 获取目标数量
            num_targets = st.session_state.get('tab1_num_targets', 1)
            
            for i in range(num_targets):
                # 为每个目标创建配置
                target_config = {
                    'id': st.session_state.get(f'tab1_target_id_{i}', f'T{100+i}'),
                    'name': st.session_state.get(f'tab1_target_name_{i}', f'目标{i+1}'),
                    'type': st.session_state.get(f'tab1_target_type_{i}', '战斗机'),
                    'rcs': st.session_state.get(f'tab3_rcs_mean_{i}', 1.0),
                    'length': st.session_state.get(f'tab1_target_length_{i}', 10.0),
                    'speed': st.session_state.get(f'tab2_speed_{i}', 200.0),
                    'altitude': st.session_state.get(f'tab2_start_alt_{i}', 1000.0),
                    'position': [
                        st.session_state.get(f'tab2_start_x_{i}', 0),
                        st.session_state.get(f'tab2_start_y_{i}', 0),
                        st.session_state.get(f'tab2_start_alt_{i}', 1000.0)
                    ],
                    'course': st.session_state.get(f'tab2_course_{i}', 0.0),
                    'maneuver_type': st.session_state.get(f'tab2_maneuver_type_{i}', '直线飞行'),
                    'rcs_type': st.session_state.get(f'tab3_rcs_type_{i}', '常数')
                }
                current_config['targets'].append(target_config)
            
            # 保存到会话状态
            if 'target_configs' not in st.session_state:
                st.session_state.target_configs = []
            
            st.session_state.target_configs.append(current_config)
            
            # 更新当前目标配置
            st.session_state.targets_config = current_config['targets']
            
            st.success(f"目标配置 '{config_name}' 已保存！")
    
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
    
    # 快速保存当前单个目标
    if st.button("💾 保存当前目标", type="primary", width='stretch'):
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
        rcs_type = st.session_state.get('tab3_rcs_type', '常数')
        
        current_target = {
            "id": target_id,
            "name": target_name,
            "type": target_type,
            "rcs": float(rcs_value),
            "speed": float(speed),
            "altitude": float(start_alt),
            "position": [float(start_x), float(start_y), float(start_alt)],
            "course": float(course),
            "maneuver_type": maneuver_type,
            "rcs_type": rcs_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if not st.session_state.targets_config:
            st.session_state.targets_config = [current_target]
        else:
            st.session_state.targets_config.append(current_target)
        
        st.success(f"目标 '{target_name}' 已保存到当前配置！")
    
    st.markdown("---")
    
    if st.button("🚀 进入下一步: 探测分析", type="primary", width='stretch'):
        st.switch_page("pages/4_📊 探测影响分析.py")

# 页脚
st.markdown("---")
st.caption("目标设置模块 | 用于雷达影响评估的目标参数配置")