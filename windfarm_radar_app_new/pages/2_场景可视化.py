"""
场景可视化页面
功能：展示风电场、雷达、通信站和目标的地理分布
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path
import math

# 添加utils路径
sys.path.append(str(Path(__file__).parent.parent / "config"))
sys.path.append(str(Path(__file__).parent.parent / "utils"))

# 导入配置 - 添加默认配置以防导入失败
try:
    from config.config import (
        COLOR_SCHEME, MAP_CONFIG, TURBINE_MODELS, 
        RADAR_FREQUENCY_BANDS, ANTENNA_TYPES
    )
except ImportError:
    # 提供默认配置
    COLOR_SCHEME = {
        'wind_turbine': 'green',
        'radar_station': 'red', 
        'comm_station': 'blue',
        'target': 'orange',
        'primary': 'purple',
        'coverage_area': 'lightblue'
    }
    
    MAP_CONFIG = {
        'default_center': [40.0, 116.0],
        'tile_providers': {
            'OpenStreetMap': 'OpenStreetMap',
            '卫星影像': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        }
    }

# 初始化可视化工具
class SimpleVisualizationTools:
    """简化版可视化工具"""
    
    def create_base_map(self, center, zoom=10, tile_provider='OpenStreetMap'):
        """创建基础地图"""
        if tile_provider == 'OpenStreetMap':
            m = folium.Map(location=center, zoom_start=zoom)
        else:
            m = folium.Map(
                location=center, 
                zoom_start=zoom,
                tiles=tile_provider,
                attr='ESRI World Imagery'
            )
        return m

# 页面配置
st.set_page_config(
    page_title="场景可视化 | 风电雷达影响评估系统",
    page_icon="🗺️",
    layout="wide"
)

# 页面标题
st.title("🗺️ 场景可视化")
st.markdown("交互式地图展示风电场、雷达、通信站和目标的地理分布")

# 初始化会话状态
if 'viz_tools' not in st.session_state:
    st.session_state.viz_tools = SimpleVisualizationTools()

# 检查场景是否加载
if 'scenario_data' not in st.session_state or not st.session_state.get('scenario_loaded', False):
    st.warning("⚠️ 请先加载场景配置文件")
    
    # 提供跳转到场景配置页面的按钮
    if st.button("📁 前往场景配置页面", width='stretch'):
        st.switch_page("pages/1_场景配置.py")
    
    st.stop()

# 获取场景数据
scenario_data = st.session_state.scenario_data
scenario_name = st.session_state.scenario_name

# 创建选项卡
tab1, tab2, tab3 = st.tabs([
    "🗺️ 主地图", 
    "📊 数据概览", 
    "⚙️ 地图设置"
])

with tab1:
    st.header("地理分布图")
    st.markdown(f"**场景名称**: {scenario_name}")
    
    # 地图控制面板
    col_controls1, col_controls2, col_controls3 = st.columns(3)
    
    with col_controls1:
        # 地图中心选择
        map_center_option = st.selectbox(
            "地图中心",
            ["自动中心", "风电场中心", "雷达站中心", "自定义中心"],
            help="选择地图的显示中心位置"
        )
        
        if map_center_option == "自定义中心":
            col_custom_lat, col_custom_lon = st.columns(2)
            with col_custom_lat:
                custom_lat = st.number_input("纬度", value=40.0, min_value=-90.0, max_value=90.0, step=0.1)
            with col_custom_lon:
                custom_lon = st.number_input("经度", value=116.0, min_value=-180.0, max_value=180.0, step=0.1)
    
    with col_controls2:
        # 缩放级别
        zoom_level = st.slider(
            "缩放级别",
            min_value=8,
            max_value=18,
            value=10,
            help="调整地图的缩放级别"
        )
        
        # 底图选择
        tile_provider_options = list(MAP_CONFIG['tile_providers'].values())
        tile_provider = st.selectbox(
            "地图样式",
            options=tile_provider_options,
            index=0,
            help="选择地图的显示样式"
        )
    
    with col_controls3:
        # 显示选项
        show_labels = st.checkbox("显示标签", value=True, help="显示元素的名称标签")
        show_grid = st.checkbox("显示网格", value=False, help="显示经纬度网格")
        show_coverage = st.checkbox("显示雷达覆盖", value=True, help="显示雷达的覆盖范围")
    
    # 计算地图中心
    center_lat, center_lon = MAP_CONFIG['default_center']
    
    if map_center_option == "自动中心":
        # 计算所有元素的平均中心
        all_lats = []
        all_lons = []
        
        # 收集所有位置
        for element_type in ['wind_turbines', 'radar_stations', 'communication_stations', 'targets']:
            elements = scenario_data.get(element_type, [])
            for element in elements:
                pos = element.get('position', {})
                if 'lat' in pos and 'lon' in pos:
                    all_lats.append(pos.get('lat', 0))
                    all_lons.append(pos.get('lon', 0))
        
        if all_lats and all_lons:
            center_lat = sum(all_lats) / len(all_lats)
            center_lon = sum(all_lons) / len(all_lons)
    
    elif map_center_option == "风电场中心":
        # 计算风电场中心
        turbine_lats = []
        turbine_lons = []
        
        for turbine in scenario_data.get('wind_turbines', []):
            pos = turbine.get('position', {})
            if 'lat' in pos and 'lon' in pos:
                turbine_lats.append(pos.get('lat', 0))
                turbine_lons.append(pos.get('lon', 0))
        
        if turbine_lats and turbine_lons:
            center_lat = sum(turbine_lats) / len(turbine_lats)
            center_lon = sum(turbine_lons) / len(turbine_lons)
    
    elif map_center_option == "雷达站中心":
        # 计算雷达站中心
        radar_lats = []
        radar_lons = []
        
        for radar in scenario_data.get('radar_stations', []):
            pos = radar.get('position', {})
            if 'lat' in pos and 'lon' in pos:
                radar_lats.append(pos.get('lat', 0))
                radar_lons.append(pos.get('lon', 0))
        
        if radar_lats and radar_lons:
            center_lat = sum(radar_lats) / len(radar_lats)
            center_lon = sum(radar_lons) / len(radar_lons)
    
    elif map_center_option == "自定义中心" and 'custom_lat' in locals() and 'custom_lon' in locals():
        center_lat, center_lon = custom_lat, custom_lon
    
    # 创建地图
    try:
        m = st.session_state.viz_tools.create_base_map(
            center=[center_lat, center_lon],
            zoom=zoom_level,
            tile_provider=tile_provider
        )
        
        # 添加网格
        if show_grid:
            folium.plugins.MousePosition().add_to(m)
        
        # 添加风机
        turbines = scenario_data.get('wind_turbines', [])
        if turbines:
            turbine_group = folium.FeatureGroup(name="风电场", show=True)
            
            for turbine in turbines:
                turbine_id = turbine.get('id', '未知')
                model = turbine.get('model', '未知')
                position = turbine.get('position', {})
                lat = position.get('lat', 0)
                lon = position.get('lon', 0)
                height = turbine.get('height', 0)
                diameter = turbine.get('rotor_diameter', 0)
                
                # 创建弹出窗口
                popup_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 300px;">
                    <h4 style="color: {COLOR_SCHEME['wind_turbine']}; margin: 0 0 10px 0;">
                        🌀 风机 #{turbine_id}
                    </h4>
                    <p style="margin: 5px 0;"><strong>型号:</strong> {model}</p>
                    <p style="margin: 5px 0;"><strong>位置:</strong> {lat:.6f}, {lon:.6f}</p>
                    <p style="margin: 5px 0;"><strong>高度:</strong> {height} m</p>
                    <p style="margin: 5px 0;"><strong>转子直径:</strong> {diameter} m</p>
                </div>
                """
                
                # 添加风机标记
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"风机 {turbine_id}",
                    color=COLOR_SCHEME['wind_turbine'],
                    fill=True,
                    fill_color=COLOR_SCHEME['wind_turbine'],
                    fill_opacity=0.7,
                    weight=2
                ).add_to(turbine_group)
                
                # 添加标签
                if show_labels:
                    folium.Marker(
                        location=[lat, lon],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 10px; color: {COLOR_SCHEME["wind_turbine"]};">风机{turbine_id}</div>'
                        )
                    ).add_to(turbine_group)
            
            turbine_group.add_to(m)
        
        # 添加雷达站
        radars = scenario_data.get('radar_stations', [])
        if radars:
            radar_group = folium.FeatureGroup(name="雷达站", show=True)
            
            for radar in radars:
                radar_id = radar.get('id', '未知')
                radar_type = radar.get('type', '未知')
                frequency_band = radar.get('frequency_band', '未知')
                position = radar.get('position', {})
                lat = position.get('lat', 0)
                lon = position.get('lon', 0)
                peak_power = radar.get('peak_power', 0)
                
                # 创建弹出窗口
                popup_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 300px;">
                    <h4 style="color: {COLOR_SCHEME['radar_station']}; margin: 0 0 10px 0;">
                        📡 雷达站 #{radar_id}
                    </h4>
                    <p style="margin: 5px 0;"><strong>类型:</strong> {radar_type}</p>
                    <p style="margin: 5px 0;"><strong>频段:</strong> {frequency_band}</p>
                    <p style="margin: 5px 0;"><strong>位置:</strong> {lat:.6f}, {lon:.6f}</p>
                    <p style="margin: 5px 0;"><strong>峰值功率:</strong> {peak_power:,} W</p>
                </div>
                """
                
                # 添加雷达标记
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"雷达站 {radar_id}",
                    color=COLOR_SCHEME['radar_station'],
                    fill=True,
                    fill_color=COLOR_SCHEME['radar_station'],
                    fill_opacity=0.8,
                    weight=2
                ).add_to(radar_group)
                
                # 添加雷达覆盖范围
                if show_coverage:
                    # 简化覆盖范围计算
                    coverage_radius = 50  # 默认50km
                    folium.Circle(
                        location=[lat, lon],
                        radius=coverage_radius * 1000,
                        popup=f'雷达覆盖范围<br>半径: {coverage_radius}km',
                        color=COLOR_SCHEME['primary'],
                        fill=True,
                        fill_color=COLOR_SCHEME['coverage_area'],
                        fill_opacity=0.2,
                        weight=1
                    ).add_to(radar_group)
            
            radar_group.add_to(m)
        
        # 添加目标
        targets = scenario_data.get('targets', [])
        if targets:
            target_group = folium.FeatureGroup(name="评估目标", show=True)
            
            for target in targets:
                target_id = target.get('id', '未知')
                target_type = target.get('type', '未知')
                rcs = target.get('rcs', 0)
                position = target.get('position', {})
                lat = position.get('lat', 0)
                lon = position.get('lon', 0)
                speed = target.get('speed', 0)
                heading = target.get('heading', 0)
                
                # 创建弹出窗口
                popup_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 300px;">
                    <h4 style="color: {COLOR_SCHEME['target']}; margin: 0 0 10px 0;">
                        🎯 目标 #{target_id}
                    </h4>
                    <p style="margin: 5px 0;"><strong>类型:</strong> {target_type}</p>
                    <p style="margin: 5px 0;"><strong>位置:</strong> {lat:.6f}, {lon:.6f}</p>
                    <p style="margin: 5px 0;"><strong>RCS:</strong> {rcs} m²</p>
                    <p style="margin: 5px 0;"><strong>速度:</strong> {speed} m/s</p>
                </div>
                """
                
                # 添加目标标记
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"目标 {target_id}",
                    color=COLOR_SCHEME['target'],
                    fill=True,
                    fill_color=COLOR_SCHEME['target'],
                    fill_opacity=0.7,
                    weight=2
                ).add_to(target_group)
            
            target_group.add_to(m)
        
        # 添加图层控制
        folium.LayerControl().add_to(m)
        
        # 添加图例
        legend_html = f'''
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
            <h4 style="margin-top:0; color: {COLOR_SCHEME['primary']}">图例</h4>
            <p style="margin: 5px 0;"><span style="color: {COLOR_SCHEME['wind_turbine']}; font-weight: bold;">●</span> 风机</p>
            <p style="margin: 5px 0;"><span style="color: {COLOR_SCHEME['radar_station']}; font-weight: bold;">●</span> 雷达站</p>
            <p style="margin: 5px 0;"><span style="color: {COLOR_SCHEME['target']}; font-weight: bold;">●</span> 目标</p>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 显示地图
        st_folium(m, width=1200, height=700, key="main_visualization_map")
        
    except Exception as e:
        st.error(f"地图创建失败: {str(e)}")
        st.info("请检查Folium和Streamlit-Folium的安装情况")

# 其余标签页代码保持不变...
with tab2:
    st.header("数据概览")
    
    # 数据统计和表格显示代码...
    # 这里可以添加原有的数据统计代码

with tab3:
    st.header("地图设置")
    
    # 地图设置代码...
    # 这里可以添加原有的地图设置代码

# 侧边栏代码...
with st.sidebar:
    st.markdown("## 🎯 快速操作")
    
    if st.button("🔄 刷新地图", width='stretch'):
        st.rerun()

# 页脚
st.markdown("---")
st.caption("风电雷达影响评估系统 | 场景可视化模块")