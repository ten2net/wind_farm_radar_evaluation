"""
雷达覆盖分析页面
功能：使用Folium地图可视化雷达覆盖范围、风电场分布和目标探测情况
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import random
import math
import json
import time
from scipy import constants

# 页面配置
st.set_page_config(
    page_title="雷达覆盖分析 | 雷达影响评估系统",
    layout="wide"
)

# 标题
st.title("🌍 雷达覆盖分析")
st.markdown("基于Folium地图的雷达覆盖可视化系统，集成风电场建模、雷达配置和目标设置数据")

# 地理计算函数
def calculate_destination(lat, lon, bearing, distance_km):
    """计算给定起点、方位角和距离的终点坐标"""
    R = 6371.0
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing)
    angular_distance = distance_km / R
    
    dest_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance) +
        math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
    )
    
    dest_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(dest_lat_rad)
    )
    
    return math.degrees(dest_lat_rad), math.degrees(dest_lon_rad)

def calculate_distance(lat1, lon1, lat2, lon2):
    """计算两点间距离（公里）"""
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def create_sector_polygon(center_lat, center_lon, bearing, beam_width, range_km, num_points=20):
    """创建扇形覆盖区域的多边形"""
    start_bearing = bearing - beam_width / 2
    end_bearing = bearing + beam_width / 2
    
    polygon_coords = [[center_lat, center_lon]]
    
    for i in range(num_points + 1):
        current_bearing = start_bearing + (end_bearing - start_bearing) * (i / num_points)
        arc_lat, arc_lon = calculate_destination(center_lat, center_lon, current_bearing, range_km)
        polygon_coords.append([arc_lat, arc_lon])
    
    polygon_coords.append([center_lat, center_lon])
    return polygon_coords

def is_point_in_sector(point_lat, point_lon, center_lat, center_lon, bearing, beam_width, range_km):
    """判断点是否在扇形区域内"""
    distance = calculate_distance(center_lat, center_lon, point_lat, point_lon)
    if distance > range_km:
        return False
    
    dx = math.radians(point_lon) - math.radians(center_lon)
    dy = math.radians(point_lat) - math.radians(center_lat)
    point_bearing = math.degrees(math.atan2(dx, dy))
    
    if point_bearing < 0:
        point_bearing += 360
    
    start_bearing = (bearing - beam_width/2) % 360
    end_bearing = (bearing + beam_width/2) % 360
    
    if start_bearing <= end_bearing:
        return start_bearing <= point_bearing <= end_bearing
    else:
        return point_bearing >= start_bearing or point_bearing <= end_bearing

# 初始化会话状态
if 'radar_coverage_data' not in st.session_state:
    st.session_state.radar_coverage_data = {
        'radar_lat': 40.0,
        'radar_lon': 116.0,
        'radar_alt': 50.0,
        'coverage_range': 100,
        'antenna_bearing': 0,
        'antenna_elevation': 0,
        'beam_width': 30,
        'coverage_shape': 'sector',
        'targets_fixed': [],  # 固定的目标位置
        'targets_generated': False,  # 标记是否已生成目标
        'turbines_fixed': [],  # 固定的风机位置
        'turbines_generated': False  # 标记是否已生成风机
    }

# 生成固定目标位置的函数
def generate_fixed_targets(radar_lat, radar_lon, coverage_data, targets_config, num_targets=20, seed=42):
    """生成固定位置的目标"""
    # 设置随机种子，确保每次生成相同的位置
    random.seed(seed)
    
    targets = []
    bearing = coverage_data.get('antenna_bearing', 0)
    beam_width = coverage_data.get('beam_width', 30)
    range_km = coverage_data.get('coverage_range', 100)
    
    for i in range(num_targets):
        # 在扇形覆盖范围内随机生成目标
        if coverage_data.get('coverage_shape') == 'sector':
            if beam_width >= 360:
                angle = random.uniform(0, 360)
            else:
                start_angle = (bearing - beam_width/2) % 360
                end_angle = (bearing + beam_width/2) % 360
                
                if start_angle <= end_angle:
                    angle = random.uniform(start_angle, end_angle)
                else:
                    if random.random() < 0.5:
                        angle = random.uniform(start_angle, 360)
                    else:
                        angle = random.uniform(0, end_angle)
        else:
            angle = random.uniform(0, 360)
        
        # 随机距离
        distance = random.uniform(0.1, range_km)
        
        # 计算目标位置
        target_lat, target_lon = calculate_destination(radar_lat, radar_lon, angle, distance)
        target_alt = random.uniform(100, 10000)
        
        # 获取目标配置
        if i < len(targets_config):
            target_config = targets_config[i]
            target_type = target_config.get('type', '飞机')
            target_rcs = target_config.get('rcs', 1.0)
            target_speed = target_config.get('speed', 200)
        else:
            target_type = f'目标{i+1}'
            target_rcs = random.uniform(0.1, 10.0)
            target_speed = random.uniform(100, 500)
        
        # 计算是否在雷达覆盖范围内
        if coverage_data.get('coverage_shape') == 'sector':
            is_in_range = is_point_in_sector(
                target_lat, target_lon, 
                radar_lat, radar_lon,
                bearing, beam_width, range_km
            )
        else:
            is_in_range = distance <= range_km
        
        # 计算探测概率
        if is_in_range:
            distance_factor = 1 - (distance / range_km)
            if coverage_data.get('coverage_shape') == 'sector':
                angle_diff = min(
                    abs(angle - bearing) % 360,
                    360 - abs(angle - bearing) % 360
                )
                angle_factor = 1 - (angle_diff / (beam_width/2))
                detection_prob = 50 + 50 * min(distance_factor, angle_factor)
            else:
                detection_prob = 50 + 50 * distance_factor
        else:
            detection_prob = 0
        
        detection_prob = max(0, min(100, detection_prob))
        
        targets.append({
            'id': i+1,
            'type': target_type,
            'lat': target_lat,
            'lon': target_lon,
            'alt': target_alt,
            'rcs': target_rcs,
            'speed': target_speed,
            'distance_km': distance,
            'angle': angle,
            'in_range': is_in_range,
            'detection_prob': detection_prob
        })
    
    return targets

# 生成固定风机位置的函数
def generate_fixed_turbines(radar_lat, radar_lon, wind_farm_config, seed=123):
    """生成固定位置的风机"""
    random.seed(seed)
    
    num_turbines = wind_farm_config.get('num_turbines', 0)
    layout_type = wind_farm_config.get('layout_type', 'grid')
    
    turbines = []
    
    if num_turbines > 0:
        if layout_type == 'grid':
            rows = int(math.sqrt(num_turbines))
            cols = int(math.ceil(num_turbines / rows))
            spacing = wind_farm_config.get('spacing', 500)
            
            for i in range(num_turbines):
                row = i // cols
                col = i % cols
                x = (col - cols/2) * spacing
                y = (row - rows/2) * spacing
                
                turbine_lat = radar_lat + y / 111000.0
                turbine_lon = radar_lon + x / (111000.0 * math.cos(math.radians(radar_lat)))
                distance_km = calculate_distance(radar_lat, radar_lon, turbine_lat, turbine_lon)
                
                turbines.append({
                    'id': i+1,
                    'lat': turbine_lat,
                    'lon': turbine_lon,
                    'x': x,
                    'y': y,
                    'distance_km': distance_km
                })
        
        elif layout_type == 'circle':
            radius = wind_farm_config.get('radius', 2000)
            
            for i in range(num_turbines):
                angle = 2 * math.pi * i / num_turbines
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
                turbine_lat = radar_lat + y / 111000.0
                turbine_lon = radar_lon + x / (111000.0 * math.cos(math.radians(radar_lat)))
                distance_km = calculate_distance(radar_lat, radar_lon, turbine_lat, turbine_lon)
                
                turbines.append({
                    'id': i+1,
                    'lat': turbine_lat,
                    'lon': turbine_lon,
                    'x': x,
                    'y': y,
                    'distance_km': distance_km
                })
        
        elif layout_type == 'line':
            spacing = wind_farm_config.get('spacing', 500)
            
            for i in range(num_turbines):
                x = i * spacing - (num_turbines-1) * spacing / 2
                y = 0
                
                turbine_lat = radar_lat + y / 111000.0
                turbine_lon = radar_lon + x / (111000.0 * math.cos(math.radians(radar_lat)))
                distance_km = calculate_distance(radar_lat, radar_lon, turbine_lat, turbine_lon)
                
                turbines.append({
                    'id': i+1,
                    'lat': turbine_lat,
                    'lon': turbine_lon,
                    'x': x,
                    'y': y,
                    'distance_km': distance_km
                })
        else:
            rows = int(math.sqrt(num_turbines))
            cols = int(math.ceil(num_turbines / rows))
            spacing = wind_farm_config.get('spacing', 500)
            
            for i in range(num_turbines):
                row = i // cols
                col = i % cols
                x = (col - cols/2) * spacing
                y = (row - rows/2) * spacing
                
                turbine_lat = radar_lat + y / 111000.0
                turbine_lon = radar_lon + x / (111000.0 * math.cos(math.radians(radar_lat)))
                distance_km = calculate_distance(radar_lat, radar_lon, turbine_lat, turbine_lon)
                
                turbines.append({
                    'id': i+1,
                    'lat': turbine_lat,
                    'lon': turbine_lon,
                    'x': x,
                    'y': y,
                    'distance_km': distance_km
                })                
    
    return turbines

# 主布局
col_map, col_control = st.columns([3, 1])

with col_map:
    st.markdown("### 雷达覆盖地图")
    
    # 从session中获取数据
    radar_config = st.session_state.get('radar_config', {})
    wind_farm_config = st.session_state.get('wind_farm_config', {})
    targets_config = st.session_state.get('targets_config', [])
    
    # 获取雷达位置
    if radar_config and 'position' in radar_config:
        radar_x, radar_y, radar_z = radar_config['position']
        radar_lat = 40.0 + radar_y / 111000.0
        radar_lon = 116.0 + radar_x / (111000.0 * math.cos(math.radians(40.0)))
    else:
        radar_lat = 40.0
        radar_lon = 116.0
        radar_z = 50.0
    
    # 更新会话状态
    coverage_data = st.session_state.radar_coverage_data
    coverage_data['radar_lat'] = radar_lat
    coverage_data['radar_lon'] = radar_lon
    coverage_data['radar_alt'] = radar_z
    
    # 获取雷达覆盖范围
    coverage_range = radar_config.get('max_range', 100000) / 1000
    coverage_data['coverage_range'] = min(coverage_range, 500)
    
    # 获取天线参数
    antenna_bearing = radar_config.get('antenna_bearing', 0)
    beam_width = radar_config.get('beam_width', 30)
    coverage_data['antenna_bearing'] = antenna_bearing
    coverage_data['beam_width'] = beam_width
    
    # 生成或获取固定风机位置
    if wind_farm_config and not coverage_data.get('turbines_generated', False):
        turbines = generate_fixed_turbines(radar_lat, radar_lon, wind_farm_config)
        coverage_data['turbines_fixed'] = turbines
        coverage_data['turbines_generated'] = True
    else:
        turbines = coverage_data.get('turbines_fixed', [])
    
    # 生成或获取固定目标位置
    if targets_config and not coverage_data.get('targets_generated', False):
        num_targets = min(len(targets_config), 20)  # 限制目标数量
        targets = generate_fixed_targets(radar_lat, radar_lon, coverage_data, targets_config, num_targets)
        coverage_data['targets_fixed'] = targets
        coverage_data['targets_generated'] = True
    else:
        targets = coverage_data.get('targets_fixed', [])
    
    # 创建地图
    map_center = [radar_lat, radar_lon]
    m = folium.Map(
        location=map_center,
        zoom_start=10,
        control_scale=True,
        # tiles='CartoDB dark_matter'
    )
    
    # 添加雷达位置标记
    folium.Marker(
        location=[radar_lat, radar_lon],
        popup=f'''雷达站
高度: {radar_z:.1f}m
方位角: {antenna_bearing:.1f}°
波束宽度: {beam_width:.1f}°''',
        tooltip="雷达站",
        icon=folium.Icon(color='red', icon='satellite', prefix='fa')
    ).add_to(m)
    
    # 添加雷达覆盖扇形
    if coverage_data.get('coverage_shape') == 'sector':
        bearing = coverage_data.get('antenna_bearing', 0)
        beam_width = coverage_data.get('beam_width', 30)
        range_km = coverage_data.get('coverage_range', 100)
        
        # 创建扇形多边形
        sector_coords = create_sector_polygon(
            radar_lat, radar_lon,
            bearing, beam_width, range_km
        )
        
        # 添加扇形多边形
        folium.Polygon(
            locations=sector_coords,
            popup=f'''雷达覆盖扇形
半径: {range_km:.1f}km
方位: {bearing:.1f}°
宽度: {beam_width:.1f}°''',
            color='rgba(0, 150, 255, 0.8)',
            fill=True,
            fill_color='rgba(0, 150, 255, 0.2)',
            fill_opacity=0.3,
            weight=2
        ).add_to(m)
        
        # 添加天线指向线
        end_lat, end_lon = calculate_destination(
            radar_lat, radar_lon,
            bearing, range_km
        )
        
        folium.PolyLine(
            locations=[
                [radar_lat, radar_lon],
                [end_lat, end_lon]
            ],
            color='rgba(255, 255, 0, 0.8)',
            weight=2,
            dash_array='5, 5',
            popup=f'天线指向: {bearing:.1f}°'
        ).add_to(m)
    else:
        # 圆形覆盖
        range_km = coverage_data.get('coverage_range', 100)
        folium.Circle(
            location=[radar_lat, radar_lon],
            radius=range_km * 1000,
            popup=f'雷达覆盖范围<br>半径: {range_km:.1f}km',
            color='rgba(0, 150, 255, 0.8)',
            fill=True,
            fill_color='rgba(0, 150, 255, 0.2)',
            fill_opacity=0.3,
            weight=2
        ).add_to(m)
    
    # 添加风机标记
    for turbine in turbines:
        folium.CircleMarker(
            location=[turbine['lat'], turbine['lon']],
            radius=5,
            popup=f'''风机 #{turbine['id']}
距离雷达: {turbine['distance_km']:.2f}km
坐标: {turbine['lat']:.6f}, {turbine['lon']:.6f}''',
            color='rgba(0, 255, 0, 0.8)',
            fill=True,
            fill_color='rgba(0, 255, 0, 0.3)',
            fill_opacity=0.5,
            weight=1
        ).add_to(m)
    
    # 添加目标标记
    for target in targets:
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
        
        icon = folium.DivIcon(
            html=icon_html,
            icon_size=(20, 20),
            icon_anchor=(10, 10)
        )
        
        folium.Marker(
            location=[target['lat'], target['lon']],
            popup=f'''目标 #{target['id']} ({target['type']})
距离: {target['distance_km']:.2f}km
高度: {target['alt']:.0f}m
RCS: {target['rcs']:.1f}m²
探测概率: {target['detection_prob']:.1f}%''',
            tooltip=f"目标 {target['id']}",
            icon=icon
        ).add_to(m)
        
        # 从雷达到目标的连线
        if target['in_range']:
            folium.PolyLine(
                locations=[
                    [radar_lat, radar_lon],
                    [target['lat'], target['lon']]
                ],
                color='rgba(255, 255, 255, 0.5)',
                weight=1,
                dash_array='5, 5'
            ).add_to(m)
    
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
        <p style="margin: 5px 0;"><span style="color: green; font-weight: bold;">●</span> 风机</p>
        <p style="margin: 5px 0;"><span style="color: #0096ff;">▢</span> 雷达覆盖</p>
        <p style="margin: 5px 0;"><span style="color: green; font-weight: bold;">●</span> 目标(高探测率)</p>
        <p style="margin: 5px 0;"><span style="color: orange; font-weight: bold;">●</span> 目标(中探测率)</p>
        <p style="margin: 5px 0;"><span style="color: red; font-weight: bold;">●</span> 目标(低探测率)</p>
        <p style="margin: 5px 0;"><span style="color: gray; font-weight: bold;">●</span> 目标(不可探测)</p>
        <p style="margin: 5px 0;"><span style="color: yellow; font-weight: bold;">━</span> 天线指向</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html)) # type: ignore
    
    # 显示地图
    map_output = st_folium(m, width=800, height=600, key="main_map")

with col_control:
    st.markdown("### 雷达参数控制")
    
    # 从会话状态获取当前数据
    coverage_data = st.session_state.radar_coverage_data
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["雷达参数", "数据统计", "控制选项"])
    
    with tab1:
        st.markdown("#### 雷达位置")
        
        col_lat, col_lon = st.columns(2)
        
        with col_lat:
            radar_lat_input = st.number_input(
                "雷达纬度 (°)",
                min_value=-90.0,
                max_value=90.0,
                value=float(coverage_data.get('radar_lat', 40.0)),
                step=0.001,
                format="%.6f",
                key="ctrl_radar_lat"
            )
        
        with col_lon:
            radar_lon_input = st.number_input(
                "雷达经度 (°)",
                min_value=-180.0,
                max_value=180.0,
                value=float(coverage_data.get('radar_lon', 116.0)),
                step=0.001,
                format="%.6f",
                key="ctrl_radar_lon"
            )
        
        radar_alt_input = st.number_input(
            "雷达高度 (m)",
            min_value=0.0,
            max_value=10000.0,
            value=float(coverage_data.get('radar_alt', 50.0)),
            step=1.0,
            key="ctrl_radar_alt"
        )
        
        st.markdown("#### 覆盖参数")
        
        coverage_shape = st.selectbox(
            "覆盖形状",
            ["扇形", "圆形"],
            index=0 if coverage_data.get('coverage_shape') == 'sector' else 1,
            key="ctrl_coverage_shape"
        )
        
        coverage_range = st.slider(
            "覆盖半径 (km)",
            min_value=10,
            max_value=500,
            value=int(coverage_data.get('coverage_range', 100)),
            step=10,
            key="ctrl_coverage_range"
        )
        
        if coverage_shape == "扇形":
            st.markdown("#### 天线参数")
            
            antenna_bearing = st.slider(
                "天线方位角 (°)",
                min_value=0,
                max_value=360,
                value=int(coverage_data.get('antenna_bearing', 0)),
                step=1,
                key="ctrl_antenna_bearing"
            )
            
            beam_width = st.slider(
                "波束宽度 (°)",
                min_value=1,
                max_value=180,
                value=int(coverage_data.get('beam_width', 30)),
                step=1,
                key="ctrl_beam_width"
            )
        
        # 更新按钮
        if st.button("🔄 更新雷达参数", type="primary", use_container_width=True):
            # 更新会话状态
            coverage_data.update({
                'radar_lat': radar_lat_input,
                'radar_lon': radar_lon_input,
                'radar_alt': radar_alt_input,
                'coverage_range': coverage_range,
                'coverage_shape': 'sector' if coverage_shape == "扇形" else 'circle',
                'antenna_bearing': antenna_bearing if coverage_shape == "扇形" else 0,
                'beam_width': beam_width if coverage_shape == "扇形" else 360
            })
            
            # 同时更新radar_config
            if 'radar_config' not in st.session_state:
                st.session_state.radar_config = {}
            
            st.session_state.radar_config.update({
                'position': [0, 0, radar_alt_input],
                'max_range': coverage_range * 1000,
                'antenna_bearing': antenna_bearing if coverage_shape == "扇形" else 0,
                'beam_width': beam_width if coverage_shape == "扇形" else 360
            })
            
            st.success("雷达参数已更新！")
            st.rerun()
    
    with tab2:
        st.markdown("#### 数据统计")
        
        # 雷达信息
        st.markdown("**雷达信息**")
        col_radar1, col_radar2 = st.columns(2)
        
        with col_radar1:
            st.metric("经度", f"{coverage_data.get('radar_lon', 0):.4f}°")
            st.metric("纬度", f"{coverage_data.get('radar_lat', 0):.4f}°")
        
        with col_radar2:
            st.metric("高度", f"{coverage_data.get('radar_alt', 0):.0f}m")
            st.metric("覆盖半径", f"{coverage_data.get('coverage_range', 0):.0f}km")
        
        # 目标统计
        targets = coverage_data.get('targets_fixed', [])
        if targets:
            st.markdown("**目标统计**")
            
            total_targets = len(targets)
            targets_in_range = sum(1 for t in targets if t.get('in_range', False))
            avg_detection_prob = np.mean([t.get('detection_prob', 0) for t in targets if t.get('in_range', False)]) if targets_in_range > 0 else 0
            
            col_target1, col_target2 = st.columns(2)
            
            with col_target1:
                st.metric("总目标数", total_targets)
                st.metric("覆盖范围内", targets_in_range)
            
            with col_target2:
                st.metric("覆盖范围外", total_targets - targets_in_range)
                st.metric("平均探测率", f"{avg_detection_prob:.1f}%")
        
        # 风机统计
        turbines = coverage_data.get('turbines_fixed', [])
        if turbines:
            st.markdown("**风机统计**")
            
            total_turbines = len(turbines)
            
            if total_turbines > 0:
                avg_distance = np.mean([t.get('distance_km', 0) for t in turbines])
                
                col_turbine1, col_turbine2 = st.columns(2)
                
                with col_turbine1:
                    st.metric("风机总数", total_turbines)
                    st.metric("平均距离", f"{avg_distance:.2f}km")
    
    with tab3:
        st.markdown("#### 控制选项")
        
        # 重新生成目标按钮
        if st.button("🎯 重新生成目标", use_container_width=True):
            # 清除已生成标记
            coverage_data['targets_generated'] = False
            coverage_data['targets_fixed'] = []
            st.success("目标已重新生成！")
            st.rerun()
        
        # 重新生成风机按钮
        if st.button("🌀 重新生成风机", use_container_width=True):
            # 清除已生成标记
            coverage_data['turbines_generated'] = False
            coverage_data['turbines_fixed'] = []
            st.success("风机已重新生成！")
            st.rerun()
        
        # 重置所有按钮
        if st.button("🔄 重置所有", use_container_width=True):
            st.session_state.radar_coverage_data = {
                'radar_lat': 40.0,
                'radar_lon': 116.0,
                'radar_alt': 50.0,
                'coverage_range': 100,
                'antenna_bearing': 0,
                'antenna_elevation': 0,
                'beam_width': 30,
                'coverage_shape': 'sector',
                'targets_fixed': [],
                'targets_generated': False,
                'turbines_fixed': [],
                'turbines_generated': False
            }
            st.success("所有数据已重置！")
            st.rerun()
        
        st.markdown("---")
        st.markdown("#### 系统信息")
        
        # 数据源状态
        st.markdown("**数据源状态**")
        
        has_radar = 'radar_config' in st.session_state and bool(st.session_state.radar_config)
        has_wind_farm = 'wind_farm_config' in st.session_state and bool(st.session_state.wind_farm_config)
        has_targets = 'targets_config' in st.session_state and len(st.session_state.get('targets_config', [])) > 0
        
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            status = "✅" if has_radar else "❌"
            st.metric("雷达配置", status)
        
        with col_status2:
            status = "✅" if has_wind_farm else "❌"
            st.metric("风电场", status)
        
        with col_status3:
            status = "✅" if has_targets else "❌"
            st.metric("目标", status)

# 页脚
st.markdown("---")
st.caption("雷达覆盖分析模块 | 基于Folium的雷达覆盖可视化系统")

# 添加CSS样式
st.markdown("""
<style>
    .folium-map {
        border-radius: 10px;
        border: 2px solid rgba(0, 100, 200, 0.3);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }
    
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
</style>
""", unsafe_allow_html=True)