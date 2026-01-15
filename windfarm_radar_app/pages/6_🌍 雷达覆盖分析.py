"""
雷达覆盖分析页面
功能：使用Folium地图可视化雷达覆盖范围、风电场分布和目标探测情况
"""

import streamlit as st
import folium
from streamlit_folium import st_folium, folium_static
import numpy as np
import pandas as pd
from scipy import constants
import random
from math import radians, sin, cos, sqrt, atan2, degrees, pi
import json
import geopandas as gpd
from shapely.geometry import Point, Polygon
from branca.colormap import linear
import branca.colormap as cm
import math

# 页面配置
st.set_page_config(
    page_title="雷达覆盖分析 | 雷达影响评估系统",
    layout="wide"
)

# 标题
st.title("🌍 雷达覆盖分析")
st.markdown("使用交互式地图可视化雷达覆盖范围、风电场分布和目标探测情况")

# 初始化会话状态
if 'map_data' not in st.session_state:
    st.session_state.map_data = {
        'radar_lat': 39.0,
        'radar_lon': 120.5,
        'radar_alt': 50.0,
        'coverage_range': 100,
        'wind_farm_polygon': [],
        'targets': [],
        'antenna_bearing': 0,  # 天线方位角
        'antenna_elevation': 0,  # 天线俯仰角
        'beam_width': 30,  # 波束宽度
        'coverage_shape': 'sector'  # 覆盖形状：sector(扇形)或circle(圆形)
    }

# 地理计算函数
def calculate_destination(lat, lon, bearing, distance_km):
    """
    计算给定起点、方位角和距离的终点坐标
    
    参数:
    lat, lon: 起点经纬度（度）
    bearing: 方位角（度，0=北，90=东）
    distance_km: 距离（公里）
    
    返回:
    (dest_lat, dest_lon): 终点经纬度
    """
    # 地球半径（公里）
    R = 6371.0
    
    # 转换为弧度
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing)
    
    # 角距离
    angular_distance = distance_km / R
    
    # 计算终点纬度
    dest_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance) +
        math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
    )
    
    # 计算终点经度
    dest_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(dest_lat_rad)
    )
    
    # 转换为度
    dest_lat = math.degrees(dest_lat_rad)
    dest_lon = math.degrees(dest_lon_rad)
    
    return dest_lat, dest_lon

def create_sector_polygon(center_lat, center_lon, bearing, beam_width, range_km, num_points=20):
    """
    创建扇形覆盖区域的多边形
    
    参数:
    center_lat, center_lon: 中心点经纬度
    bearing: 中心方位角（度）
    beam_width: 波束宽度（度）
    range_km: 覆盖距离（公里）
    num_points: 弧线上的点数
    
    返回:
    polygon_coords: 多边形坐标列表 [[lat, lon], ...]
    """
    # 计算起始和终止方位角
    start_bearing = bearing - beam_width / 2
    end_bearing = bearing + beam_width / 2
    
    # 起始点列表，从中心点开始
    polygon_coords = [[center_lat, center_lon]]
    
    # 添加弧线上的点
    for i in range(num_points + 1):
        # 计算当前方位角
        current_bearing = start_bearing + (end_bearing - start_bearing) * (i / num_points)
        
        # 计算弧线上的点
        arc_lat, arc_lon = calculate_destination(center_lat, center_lon, current_bearing, range_km)
        polygon_coords.append([arc_lat, arc_lon])
    
    # 闭合多边形
    polygon_coords.append([center_lat, center_lon])
    
    return polygon_coords

def calculate_distance(lat1, lon1, lat2, lon2):
    """计算两点间距离（公里）"""
    R = 6371.0  # 地球半径（公里）
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def is_point_in_sector(point_lat, point_lon, center_lat, center_lon, bearing, beam_width, range_km):
    """
    判断点是否在扇形区域内
    
    参数:
    point_lat, point_lon: 测试点坐标
    center_lat, center_lon: 扇形中心坐标
    bearing: 扇形中心方位角
    beam_width: 扇形宽度
    range_km: 扇形半径
    
    返回:
    bool: 是否在扇形内
    """
    # 计算点到中心的距离
    distance = calculate_distance(center_lat, center_lon, point_lat, point_lon)
    
    # 如果距离超出范围，直接返回False
    if distance > range_km:
        return False
    
    # 计算点到中心的方位角
    dx = math.radians(point_lon) - math.radians(center_lon)
    dy = math.radians(point_lat) - math.radians(center_lat)
    
    # 计算方位角
    point_bearing = math.degrees(math.atan2(dx, dy))
    
    # 归一化到0-360度
    if point_bearing < 0:
        point_bearing += 360
    
    # 归一化扇形起始和结束方位角
    start_bearing = (bearing - beam_width/2) % 360
    end_bearing = (bearing + beam_width/2) % 360
    
    # 检查点方位角是否在扇形范围内
    if start_bearing <= end_bearing:
        return start_bearing <= point_bearing <= end_bearing
    else:
        # 处理跨越0度的情况
        return point_bearing >= start_bearing or point_bearing <= end_bearing

# 从会话状态获取配置
def get_config():
    """从会话状态获取配置数据"""
    wind_farm = st.session_state.get('wind_farm_config', {})
    radar = st.session_state.get('radar_config', {})
    targets = st.session_state.get('targets_config', [])
    return wind_farm, radar, targets

# 创建选项卡
tab1, tab2, tab3 = st.tabs([
    "地图配置", 
    "覆盖分析", 
    "高级分析"
])

with tab1:
    st.header("地图和场景配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("雷达位置和参数")
        
        # 雷达位置输入
        col_lat, col_lon = st.columns(2)
        
        with col_lat:
            radar_lat = st.number_input(
                "雷达纬度 (°)",
                min_value=-90.0,
                max_value=90.0,
                value=39.5,
                step=0.1,
                format="%.6f",
                key="radar_lat"
            )
        
        with col_lon:
            radar_lon = st.number_input(
                "雷达经度 (°)",
                min_value=-180.0,
                max_value=180.0,
                value=120.5,
                step=0.1,
                format="%.6f",
                key="radar_lon"
            )
        
        radar_alt = st.number_input(
            "雷达高度 (m)",
            min_value=0.0,
            max_value=1000.0,
            value=50.0,
            step=1.0,
            key="radar_alt"
        )
        
        # 覆盖参数
        coverage_range = st.slider(
            "雷达覆盖半径 (km)",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="coverage_range"
        )
        
        # 获取雷达配置
        radar_config = st.session_state.get('radar_config', {})
        if radar_config:
            radar_type = radar_config.get('type', '未知')
            radar_freq = radar_config.get('frequency', 3e9) / 1e9
            st.info(f"当前雷达配置: {radar_type}, {radar_freq:.1f} GHz")
    
    with col2:
        st.subheader("天线朝向参数")
        
        # 覆盖形状选择
        coverage_shape = st.selectbox(
            "覆盖形状",
            ["扇形", "圆形"],
            key="coverage_shape",
            help="选择雷达覆盖区域的形状：扇形（考虑天线朝向）或圆形（不考虑朝向）"
        )
        
        if coverage_shape == "扇形":
            # 天线朝向参数
            col_bearing, col_beamwidth = st.columns(2)
            
            with col_bearing:
                antenna_bearing = st.slider(
                    "天线方位角 (°)",
                    min_value=0,
                    max_value=360,
                    value=0,
                    step=1,
                    key="antenna_bearing",
                    help="0°=北，90°=东，180°=南，270°=西"
                )
            
            with col_beamwidth:
                beam_width = st.slider(
                    "波束宽度 (°)",
                    min_value=1,
                    max_value=180,
                    value=30,
                    step=1,
                    key="beam_width"
                )
            
            # 方位角可视化
            st.markdown("**方位角可视化**")
            
            # 创建罗盘图
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            # 添加罗盘圆
            theta = np.linspace(0, 2*np.pi, 100)
            fig.add_trace(go.Scatterpolar(
                r=[1]*100,
                theta=np.degrees(theta),
                mode='lines',
                line=dict(color='gray', width=1),
                fill='toself',
                fillcolor='rgba(200, 200, 200, 0.1)',
                showlegend=False
            ))
            
            # 添加方向标记
            directions = ['N', 'E', 'S', 'W']
            angles = [0, 90, 180, 270]
            
            for direction, angle in zip(directions, angles):
                fig.add_annotation(
                    x=0.5 + 0.5 * math.sin(math.radians(angle)),
                    y=0.5 + 0.5 * math.cos(math.radians(angle)),
                    text=direction,
                    showarrow=False,
                    font=dict(size=12, color="white")
                )
            
            # 添加天线波束
            beam_start = antenna_bearing - beam_width/2
            beam_end = antenna_bearing + beam_width/2
            
            theta_beam = np.linspace(math.radians(beam_start), math.radians(beam_end), 50)
            r_beam = [1] * 50
            
            fig.add_trace(go.Scatterpolar(
                r=r_beam,
                theta=np.degrees(theta_beam),
                mode='lines',
                line=dict(color='red', width=3),
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.3)',
                name='天线波束'
            ))
            
            # 添加天线指向线
            fig.add_trace(go.Scatterpolar(
                r=[0, 1],
                theta=[antenna_bearing, antenna_bearing],
                mode='lines',
                line=dict(color='yellow', width=2, dash='dash'),
                name='天线指向'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=False, range=[0, 1]),
                    angularaxis=dict(rotation=90, direction="clockwise")
                ),
                showlegend=True,
                title=dict(text=f"天线指向: {antenna_bearing}°", font=dict(size=12)),
                height=200,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, width='stretch')
        
        st.subheader("目标配置")
        
        targets_config = st.session_state.get('targets_config', [])
        num_targets = st.slider(
            "目标数量",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            key="num_targets"
        )
        
        if st.button("生成随机目标", width='stretch'):
            # 在雷达覆盖范围内生成随机目标
            targets = []
            for i in range(num_targets):
                # 如果使用扇形，在扇形内生成目标
                if coverage_shape == "扇形":
                    # 在扇形范围内随机生成方位角
                    if beam_width >= 360: # type: ignore
                        angle = random.uniform(0, 360)
                    else:
                        start_angle = (antenna_bearing - beam_width/2) % 360 # type: ignore
                        end_angle = (antenna_bearing + beam_width/2) % 360 # type: ignore
                        
                        if start_angle <= end_angle:
                            angle = random.uniform(start_angle, end_angle)
                        else:
                            # 处理跨越0度的情况
                            if random.random() < 0.5:
                                angle = random.uniform(start_angle, 360)
                            else:
                                angle = random.uniform(0, end_angle)
                else:
                    # 圆形覆盖，随机生成方位角
                    angle = random.uniform(0, 360)
                
                # 随机距离
                distance = random.uniform(0.1, coverage_range)
                
                # 计算目标位置
                target_lat, target_lon = calculate_destination(radar_lat, radar_lon, angle, distance)
                target_alt = random.uniform(100, 10000)  # 目标高度
                target_rcs = random.uniform(0.1, 10.0)  # 目标RCS
                
                # 计算是否在雷达覆盖范围内
                if coverage_shape == "扇形":
                    is_in_range = is_point_in_sector(
                        target_lat, target_lon, 
                        radar_lat, radar_lon,
                        antenna_bearing, beam_width, coverage_range # type: ignore
                    )
                else:
                    # 圆形覆盖
                    is_in_range = distance <= coverage_range
                
                # 计算探测概率（简化模型）
                if is_in_range:
                    # 距离越近，探测概率越高
                    distance_factor = 1 - (distance / coverage_range)
                    # 如果扇形覆盖，考虑方位角偏离中心的程度
                    if coverage_shape == "扇形":
                        angle_diff = min(
                            abs(angle - antenna_bearing) % 360, # type: ignore
                            360 - abs(angle - antenna_bearing) % 360 # type: ignore
                        )
                        angle_factor = 1 - (angle_diff / (beam_width/2)) # type: ignore
                        detection_prob = 80 + 20 * min(distance_factor, angle_factor)
                    else:
                        detection_prob = 80 + 20 * distance_factor
                else:
                    detection_prob = 0
                
                detection_prob = max(0, min(100, detection_prob))
                
                targets.append({
                    'id': i+1,
                    'name': f'目标{i+1}',
                    'lat': target_lat,
                    'lon': target_lon,
                    'alt': target_alt,
                    'rcs': target_rcs,
                    'distance_km': distance,
                    'in_range': is_in_range,
                    'detection_prob': detection_prob,
                    'bearing_to_radar': (angle + 180) % 360  # 目标到雷达的方位角
                })
            
            st.session_state.map_data['targets'] = targets
            st.success(f"已生成{num_targets}个目标")
    
    # 保存地图数据
    if st.button("💾 保存地图配置", type="primary", width='stretch'):
        st.session_state.map_data.update({
            'radar_lat': radar_lat,
            'radar_lon': radar_lon,
            'radar_alt': radar_alt,
            'coverage_range': coverage_range,
            'coverage_shape': 'sector' if coverage_shape == "扇形" else 'circle',
            'antenna_bearing': antenna_bearing if coverage_shape == "扇形" else 0, # type: ignore
            'beam_width': beam_width if coverage_shape == "扇形" else 360 # type: ignore
        })
        st.success("地图配置已保存！")

with tab2:
    st.header("雷达覆盖分析地图")
    
    # 获取地图数据
    map_data = st.session_state.map_data
    
    col_map1, col_map2 = st.columns([3, 1])
    
    with col_map1:
        # 创建地图
        map_center = [map_data['radar_lat'], map_data['radar_lon']]
        print(map_center)
        print(map_data)
        m = folium.Map(
            location=map_center,
            zoom_start=10,
            control_scale=True,
            # tiles='CartoDB dark_matter'  # 使用深色底图
        )
        
        # 添加雷达位置标记
        folium.Marker(
            location=[map_data['radar_lat'], map_data['radar_lon']],
            popup=f"雷达站<br>高度: {map_data['radar_alt']}m<br>朝向: {map_data.get('antenna_bearing', 0)}°",
            tooltip="雷达站",
            icon=folium.Icon(color='red', icon='satellite', prefix='fa')
        ).add_to(m)
        
        # 添加雷达覆盖范围
        if map_data.get('coverage_shape') == 'sector':
            # 扇形覆盖
            bearing = map_data.get('antenna_bearing', 0)
            beam_width = map_data.get('beam_width', 30)
            
            # 创建扇形多边形
            sector_coords = create_sector_polygon(
                map_data['radar_lat'], map_data['radar_lon'],
                bearing, beam_width, map_data['coverage_range']
            )
            
            # 添加扇形多边形
            folium.Polygon(
                locations=sector_coords,
                popup=f'雷达覆盖扇形<br>半径: {map_data["coverage_range"]}km<br>方位: {bearing}°<br>宽度: {beam_width}°',
                color='rgba(0, 150, 255, 0.8)',
                fill=True,
                fill_color='rgba(0, 150, 255, 0.2)',
                fill_opacity=0.3,
                weight=2
            ).add_to(m)
            
            # 添加天线指向线
            end_lat, end_lon = calculate_destination(
                map_data['radar_lat'], map_data['radar_lon'],
                bearing, map_data['coverage_range']
            )
            
            folium.PolyLine(
                locations=[
                    [map_data['radar_lat'], map_data['radar_lon']],
                    [end_lat, end_lon]
                ],
                color='rgba(255, 255, 0, 0.8)',
                weight=2,
                dash_array='5, 5',
                popup=f'天线指向: {bearing}°'
            ).add_to(m)
            
            # 添加波束边界线
            for angle_offset in [-beam_width/2, beam_width/2]:
                boundary_angle = (bearing + angle_offset) % 360
                end_lat_b, end_lon_b = calculate_destination(
                    map_data['radar_lat'], map_data['radar_lon'],
                    boundary_angle, map_data['coverage_range']
                )
                
                folium.PolyLine(
                    locations=[
                        [map_data['radar_lat'], map_data['radar_lon']],
                        [end_lat_b, end_lon_b]
                    ],
                    color='rgba(0, 200, 255, 0.6)',
                    weight=1,
                    dash_array='3, 3'
                ).add_to(m)
                
        else:
            # 圆形覆盖
            folium.Circle(
                location=[map_data['radar_lat'], map_data['radar_lon']],
                radius=map_data['coverage_range'] * 1000,  # 转换为米
                popup=f'雷达覆盖范围<br>半径: {map_data["coverage_range"]}km',
                color='rgba(0, 150, 255, 0.8)',
                fill=True,
                fill_color='rgba(0, 150, 255, 0.2)',
                fill_opacity=0.3,
                weight=2
            ).add_to(m)
        
        # 添加风电场边界
        if map_data.get('wind_farm_polygon'):
            folium.Polygon(
                locations=map_data['wind_farm_polygon'],
                popup='风电场区域',
                color='rgba(0, 255, 150, 0.8)',
                fill=True,
                fill_color='rgba(0, 255, 150, 0.3)',
                fill_opacity=0.3,
                weight=2
            ).add_to(m)
            
            # 在风电场中心添加标记
            center_lat = sum(p[0] for p in map_data['wind_farm_polygon']) / len(map_data['wind_farm_polygon'])
            center_lon = sum(p[1] for p in map_data['wind_farm_polygon']) / len(map_data['wind_farm_polygon'])
            
            folium.Marker(
                location=[center_lat, center_lon],
                popup='风电场中心',
                tooltip="风电场中心",
                icon=folium.Icon(color='green', icon='wind', prefix='fa')
            ).add_to(m)
        
        # 添加目标标记
        for target in map_data.get('targets', []):
            # 根据探测概率选择颜色
            if target['detection_prob'] > 80:
                color = 'green'
            elif target['detection_prob'] > 50:
                color = 'orange'
            elif target['detection_prob'] > 0:
                color = 'red'
            else:
                color = 'gray'
            
            # 创建自定义图标
            icon_html = f'''
                <div style="
                    width: 20px;
                    height: 20px;
                    background-color: {color};
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 0 5px rgba(0,0,0,0.5);
                "></div>
            '''
            
            # 创建自定义图标
            icon = folium.DivIcon(
                html=icon_html,
                icon_size=(20, 20),
                icon_anchor=(10, 10)
            )
            
            # 添加标记
            folium.Marker(
                location=[target['lat'], target['lon']],
                popup=f'''目标: {target['name']}<br>
                         距离: {target['distance_km']:.1f}km<br>
                         高度: {target['alt']:.0f}m<br>
                         RCS: {target['rcs']:.1f}m²<br>
                         探测概率: {target['detection_prob']:.1f}%<br>
                         到雷达方位: {target.get('bearing_to_radar', 0):.1f}°''',
                tooltip=target['name'],
                icon=icon
            ).add_to(m)
            
            # 从雷达到目标的连线（只对在范围内的目标）
            if target['in_range']:
                folium.PolyLine(
                    locations=[
                        [map_data['radar_lat'], map_data['radar_lon']],
                        [target['lat'], target['lon']]
                    ],
                    color='rgba(255, 255, 255, 0.5)',
                    weight=1,
                    dash_array='5, 5'
                ).add_to(m)
        
        # 添加罗盘
        from folium.features import DivIcon
        
        # 创建罗盘
        compass_html = '''
        <div style="
            position: absolute;
            top: 10px;
            right: 10px;
            width: 100px;
            height: 100px;
            background: rgba(30, 30, 50, 0.8);
            border-radius: 50%;
            border: 2px solid rgba(100, 150, 200, 0.5);
        ">
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate({bearing}deg);
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 40px solid rgba(255, 50, 50, 0.8);
            "></div>
            <div style="
                position: absolute;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);
                color: white;
                font-size: 12px;
                font-weight: bold;
            ">N</div>
            <div style="
                position: absolute;
                bottom: 10px;
                left: 50%;
                transform: translateX(-50%);
                color: white;
                font-size: 12px;
                font-weight: bold;
            ">S</div>
            <div style="
                position: absolute;
                top: 50%;
                right: 10px;
                transform: translateY(-50%);
                color: white;
                font-size: 12px;
                font-weight: bold;
            ">E</div>
            <div style="
                position: absolute;
                top: 50%;
                left: 10px;
                transform: translateY(-50%);
                color: white;
                font-size: 12px;
                font-weight: bold;
            ">W</div>
        </div>
        '''.format(bearing=map_data.get('antenna_bearing', 0))
        
        m.get_root().html.add_child(folium.Element(compass_html)) # type: ignore
        
        # 添加图例
        legend_html = '''
        <div style="
            position: fixed; 
            bottom: 50px; 
            right: 50px; 
            width: 200px; 
            height: auto; 
            background-color: rgba(30, 30, 50, 0.8);
            border: 2px solid rgba(100, 100, 200, 0.5);
            border-radius: 5px;
            padding: 10px;
            font-size: 12px;
            color: white;
            z-index: 9999;
        ">
            <h4 style="margin-top:0; color: #a0d8ff">图例</h4>
            <p style="margin: 5px 0;"><span style="color: red; font-weight: bold;">●</span> 雷达站</p>
            <p style="margin: 5px 0;"><span style="color: green; font-weight: bold;">●</span> 风电场</p>
            <p style="margin: 5px 0;"><span style="color: #0096ff;">▢</span> 雷达覆盖范围</p>
            <p style="margin: 5px 0;"><span style="color: #00ff96;">▢</span> 风电场区域</p>
            <p style="margin: 5px 0;"><span style="color: green; font-weight: bold;">●</span> 目标(高探测率)</p>
            <p style="margin: 5px 0;"><span style="color: orange; font-weight: bold;">●</span> 目标(中探测率)</p>
            <p style="margin: 5px 0;"><span style="color: red; font-weight: bold;">●</span> 目标(低探测率)</p>
            <p style="margin: 5px 0;"><span style="color: gray; font-weight: bold;">●</span> 目标(不可探测)</p>
            <p style="margin: 5px 0;"><span style="color: yellow; font-weight: bold;">━</span> 天线指向</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html)) # type: ignore
        
        # 显示地图
        st_folium(m, width=800, height=600)
    
    with col_map2:
        st.subheader("覆盖统计")
        
        targets = map_data.get('targets', [])
        if targets:
            # 计算统计信息
            total_targets = len(targets)
            targets_in_range = sum(1 for t in targets if t['in_range'])
            avg_detection_prob = np.mean([t['detection_prob'] for t in targets if t['in_range']]) if targets_in_range > 0 else 0
            
            col_stats1, col_stats2 = st.columns(2)
            
            with col_stats1:
                st.metric("总目标数", total_targets)
                st.metric("覆盖范围内", f"{targets_in_range}")
            
            with col_stats2:
                st.metric("覆盖范围外", f"{total_targets - targets_in_range}")
                st.metric("平均探测率", f"{avg_detection_prob:.1f}%" if targets_in_range > 0 else "N/A")
            
            # 天线朝向信息
            if map_data.get('coverage_shape') == 'sector':
                st.markdown("---")
                st.subheader("天线信息")
                
                bearing = map_data.get('antenna_bearing', 0)
                beam_width = map_data.get('beam_width', 30)
                
                col_ant1, col_ant2 = st.columns(2)
                
                with col_ant1:
                    st.metric("方位角", f"{bearing}°")
                
                with col_ant2:
                    st.metric("波束宽度", f"{beam_width}°")
                
                # 计算目标方位分布
                bearings = [t.get('bearing_to_radar', 0) for t in targets if t['in_range']]
                if bearings:
                    avg_bearing = np.mean(bearings) % 360
                    bearing_std = np.std([(b - avg_bearing + 180) % 360 - 180 for b in bearings])
                    st.metric("平均目标方位", f"{avg_bearing:.1f}°")
            
            st.markdown("---")
            st.subheader("目标列表")
            
            # 创建目标数据表
            target_data = []
            for target in targets[:10]:  # 只显示前10个
                target_data.append({
                    'ID': target['id'],
                    '距离(km)': f"{target['distance_km']:.1f}",
                    '方位角': f"{target.get('bearing_to_radar', 0):.1f}°",
                    '探测率': f"{target['detection_prob']:.1f}%",
                    '状态': '✅' if target['in_range'] else '❌'
                })
            
            if target_data:
                st.dataframe(
                    pd.DataFrame(target_data),
                    width='stretch',
                    hide_index=True
                )
            
            if len(targets) > 10:
                st.caption(f"... 还有 {len(targets)-10} 个目标未显示")
            
            st.markdown("---")
            
            # 导出选项
            if st.button("📥 导出地图为HTML", width='stretch'):
                # 保存地图为HTML文件
                m.save("radar_coverage_map.html")
                st.success("地图已保存为 radar_coverage_map.html")
        else:
            st.info("暂无目标数据，请在左侧生成目标")

with tab3:
    st.header("高级分析功能")
    
    col_adv1, col_adv2 = st.columns(2)
    
    with col_adv1:
        st.subheader("覆盖分析")
        
        # 扇形覆盖分析
        if map_data.get('coverage_shape') == 'sector':
            st.markdown("**扇形覆盖分析**")
            
            bearing = map_data.get('antenna_bearing', 0)
            beam_width = map_data.get('beam_width', 30)
            range_km = map_data.get('coverage_range', 100)
            
            # 计算扇形面积
            sector_area = (beam_width / 360) * math.pi * (range_km ** 2)
            circle_area = math.pi * (range_km ** 2)
            coverage_ratio = sector_area / circle_area
            
            col_area1, col_area2 = st.columns(2)
            
            with col_area1:
                st.metric("扇形面积", f"{sector_area:.0f} km²")
            
            with col_area2:
                st.metric("覆盖率比例", f"{coverage_ratio*100:.1f}%")
            
            # 方位角分析
            st.markdown("**方位角覆盖分析**")
            
            # 创建方位角分布图
            import plotly.graph_objects as go
            
            if map_data.get('targets'):
                targets_in_range = [t for t in map_data['targets'] if t['in_range']]
                if targets_in_range:
                    bearings = [t.get('bearing_to_radar', 0) for t in targets_in_range]
                    
                    fig_polar = go.Figure()
                    
                    # 添加扇形区域
                    theta_sector = np.linspace(
                        math.radians(bearing - beam_width/2),
                        math.radians(bearing + beam_width/2),
                        50
                    )
                    
                    fig_polar.add_trace(go.Scatterpolar(
                        r=[range_km]*50,
                        theta=np.degrees(theta_sector),
                        mode='lines',
                        line=dict(color='blue', width=2),
                        fill='toself',
                        fillcolor='rgba(0, 0, 255, 0.2)',
                        name='覆盖扇形'
                    ))
                    
                    # 添加目标点
                    fig_polar.add_trace(go.Scatterpolar(
                        r=[t['distance_km'] for t in targets_in_range],
                        theta=[t.get('bearing_to_radar', 0) for t in targets_in_range],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color=[t['detection_prob'] for t in targets_in_range],
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(title="探测概率")
                        ),
                        name='目标',
                        text=[f"目标{t['id']}: {t['detection_prob']:.1f}%" for t in targets_in_range]
                    ))
                    
                    fig_polar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                title=dict(text="距离 (km)", font=dict(size=10)),
                                range=[0, range_km],
                                tickfont=dict(size=8)
                            ),
                            angularaxis=dict(
                                rotation=90,
                                direction="clockwise",
                                tickfont=dict(size=8)
                            )
                        ),
                        showlegend=True,
                        title=dict(text="目标方位分布", font=dict(size=12)),
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig_polar, width='stretch')
        
        # 盲区分析
        st.markdown("---")
        st.subheader("盲区分析")
        
        if st.button("🔍 分析盲区", width='stretch'):
            with st.spinner("正在分析盲区..."):
                import time
                
                # 模拟盲区分析
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)
                
                # 模拟结果
                if map_data.get('coverage_shape') == 'sector':
                    blind_zone_percent = 100 - (beam_width / 360) * 100 # type: ignore
                else:
                    blind_zone_percent = 0
                
                st.metric("盲区面积比例", f"{blind_zone_percent:.1f}%")
                
                st.success("盲区分析完成！")
    
    with col_adv2:
        st.subheader("雷达参数优化")
        
        # 参数优化建议
        st.markdown("**优化建议**")
        
        targets = map_data.get('targets', [])
        if targets and map_data.get('coverage_shape') == 'sector':
            targets_in_range = [t for t in targets if t['in_range']]
            
            if targets_in_range:
                # 计算目标方位角
                bearings = [t.get('bearing_to_radar', 0) for t in targets_in_range]
                
                # 计算目标方位角范围
                min_bearing = min(bearings)
                max_bearing = max(bearings)
                bearing_range = (max_bearing - min_bearing) % 360
                
                # 计算建议方位角（目标方位的中心）
                if bearing_range < 180:
                    optimal_bearing = (min_bearing + bearing_range/2) % 360
                else:
                    # 处理跨越0度的情况
                    optimal_bearing = (max_bearing + (360 - bearing_range)/2) % 360
                
                col_opt1, col_opt2 = st.columns(2)
                
                with col_opt1:
                    st.metric("目标方位范围", f"{bearing_range:.1f}°")
                
                with col_opt2:
                    st.metric("建议方位角", f"{optimal_bearing:.1f}°")
                
                # 计算当前方位角与建议方位角的偏差
                current_bearing = map_data.get('antenna_bearing', 0)
                bearing_diff = min(
                    abs(optimal_bearing - current_bearing) % 360,
                    360 - abs(optimal_bearing - current_bearing) % 360
                )
                
                if bearing_diff < 10:
                    st.success("✅ 当前方位角接近最优")
                elif bearing_diff < 30:
                    st.warning("⚠️ 建议调整方位角以优化覆盖")
                else:
                    st.error("❌ 建议重新调整天线方位角")
        
        st.markdown("---")
        st.subheader("数据导出")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            if st.button("📊 导出统计数据", width='stretch'):
                st.success("统计数据已生成")
                
                # 生成示例数据
                export_data = {
                    '雷达位置': f"{map_data['radar_lat']:.6f}, {map_data['radar_lon']:.6f}",
                    '覆盖形状': map_data.get('coverage_shape', 'circle'),
                    '覆盖半径_km': map_data['coverage_range'],
                    '天线方位角': map_data.get('antenna_bearing', 0),
                    '波束宽度': map_data.get('beam_width', 360),
                    '目标总数': len(map_data.get('targets', [])),
                    '覆盖范围内目标数': sum(1 for t in map_data.get('targets', []) if t['in_range']),
                    '平均探测率': np.mean([t['detection_prob'] for t in map_data.get('targets', []) if t['in_range']]) 
                    if map_data.get('targets') else 0
                }
                
                st.json(export_data)
        
        with col_exp2:
            if st.button("🗺️ 导出地理数据", width='stretch'):
                st.success("地理数据已生成")
                
                # 生成KML格式数据
                kml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>雷达覆盖分析</name>
    <description>雷达覆盖范围和目标分布</description>
    
    <Placemark>
        <name>雷达站</name>
        <description>方位角: {map_data.get('antenna_bearing', 0)}°, 波束宽度: {map_data.get('beam_width', 360)}°</description>
        <Point>
            <coordinates>{map_data['radar_lon']},{map_data['radar_lat']},{map_data['radar_alt']}</coordinates>
        </Point>
    </Placemark>
</Document>
</kml>"""
                
                st.code(kml_data, language='xml')

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **地图配置**: 设置雷达和风电场位置
    2. **覆盖分析**: 查看雷达覆盖范围和目标分布
    3. **高级分析**: 进行盲区、视线和干扰分析
    
    **使用步骤:**
    1. 在地图配置中设置参数
    2. 生成目标并查看覆盖
    3. 进行高级分析
    4. 导出分析结果
    """)
    
    st.markdown("---")
    
    # 快速操作
    st.markdown("## ⚡ 快速操作")
    
    if st.button("📍 定位到雷达", width='stretch'):
        st.session_state.map_data['radar_lat'] = 39.5
        st.session_state.map_data['radar_lon'] = 120.5
        st.rerun()
    
    if st.button("🔄 重置地图", width='stretch'):
        st.session_state.map_data = {
            'radar_lat': 39.5,
            'radar_lon': 120.0,
            'radar_alt': 50.0,
            'coverage_range': 100,
            'wind_farm_polygon': [],
            'targets': [],
            'antenna_bearing': 0,
            'beam_width': 30,
            'coverage_shape': 'sector'
        }
        st.rerun()
    
    st.markdown("---")
    
    # 天线控制
    st.markdown("## 🎯 天线控制")
    
    if map_data.get('coverage_shape') == 'sector':
        col_ant1, col_ant2 = st.columns(2)
        
        with col_ant1:
            if st.button("⬅️ 左转", width='stretch'):
                st.session_state.map_data['antenna_bearing'] = (map_data.get('antenna_bearing', 0) - 10) % 360
                st.rerun()
        
        with col_ant2:
            if st.button("➡️ 右转", width='stretch'):
                st.session_state.map_data['antenna_bearing'] = (map_data.get('antenna_bearing', 0) + 10) % 360
                st.rerun()
        
        # 预设方位
        st.markdown("**预设方位**")
        col_dir1, col_dir2, col_dir3, col_dir4 = st.columns(4)
        
        with col_dir1:
            if st.button("N", width='stretch'):
                st.session_state.map_data['antenna_bearing'] = 0
                st.rerun()
        
        with col_dir2:
            if st.button("E", width='stretch'):
                st.session_state.map_data['antenna_bearing'] = 90
                st.rerun()
        
        with col_dir3:
            if st.button("S", width='stretch'):
                st.session_state.map_data['antenna_bearing'] = 180
                st.rerun()
        
        with col_dir4:
            if st.button("W", width='stretch'):
                st.session_state.map_data['antenna_bearing'] = 270
                st.rerun()
    
    st.markdown("---")
    
    # 系统信息
    st.markdown("## ℹ️ 系统信息")
    
    total_targets = len(st.session_state.map_data.get('targets', []))
    st.metric("当前目标数", total_targets)
    
    coverage_percent = 0
    if total_targets > 0:
        targets_in_range = sum(1 for t in st.session_state.map_data.get('targets', []) if t['in_range'])
        coverage_percent = (targets_in_range / total_targets) * 100
    
    st.metric("目标覆盖率", f"{coverage_percent:.1f}%")

# 页脚
st.markdown("---")
st.caption("雷达覆盖分析模块 | 基于Folium的雷达覆盖可视化系统")

# 添加CSS样式
st.markdown("""
<style>
    /* 优化地图容器样式 */
    .folium-map {
        border-radius: 10px;
        border: 2px solid rgba(0, 100, 200, 0.3);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }
    
    /* 优化卡片样式 */
    .metric-card {
        background: rgba(20, 25, 50, 0.3);
        border: 1px solid rgba(0, 150, 255, 0.2);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* 优化按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 100, 200, 0.8), rgba(0, 50, 100, 0.9));
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 120, 220, 0.9), rgba(0, 70, 120, 1));
        box-shadow: 0 5px 15px rgba(0, 150, 255, 0.3);
    }
    
    /* 优化标签样式 */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(20, 25, 50, 0.3);
        border-radius: 8px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #a0c8ff;
        border-radius: 5px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(0, 100, 200, 0.3);
        color: #00ccff;
    }
</style>
""", unsafe_allow_html=True)