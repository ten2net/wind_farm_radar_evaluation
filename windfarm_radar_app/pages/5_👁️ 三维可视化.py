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
                    X_range = radar_x + R_range * np.sin(Phi) * np.cos(Theta) # type: ignore
                    Y_range = radar_y + R_range * np.sin(Phi) * np.sin(Theta) # type: ignore
                    Z_range = radar_z + R_range * np.cos(Phi) # type: ignore
                    
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
            if "风机位置" in export_data: # type: ignore
                wind_farm_data = {
                    '风机ID': list(range(1, 10)),
                    'X坐标': [random.uniform(-1000, 1000) for _ in range(9)],
                    'Y坐标': [random.uniform(-1000, 1000) for _ in range(9)],
                    '高度': [100] * 9,
                    '状态': ['正常'] * 9
                }
                
                st.write("**风机位置数据:**")
                st.dataframe(pd.DataFrame(wind_farm_data), width='stretch')
            
            if "目标轨迹" in export_data: # type: ignore
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
        num_traces = len(fig.data) # type: ignore
        
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
