"""
地图组件 - 军事风格地图
"""

import folium
from folium import plugins
import streamlit as st
from typing import List, Tuple, Dict, Any
import numpy as np

def create_military_map(center: List[float] = None,  # type: ignore
                       zoom_start: int = 5,
                       style: str = "military") -> folium.Map:
    """创建军事风格地图"""
    if center is None:
        center = [39.9042, 116.4074]  # 北京
    
    # 选择地图样式
    if style == "military":
        # 军事地形图
        tiles = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
        attr = "OpenTopoMap"
    elif style == "satellite":
        # 卫星影像
        tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attr = "Esri"
    elif style == "dark":
        # 暗色模式
        tiles = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attr = "CartoDB"
    else:
        # 标准街道图
        tiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attr = "OpenStreetMap"
    
    # 创建地图
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles=tiles,
        attr=attr,
        control_scale=True,
        prefer_canvas=True
    )
    
    # 添加军事网格
    # add_military_grid(m)
    
    # 添加比例尺
    plugins.MeasureControl(position='bottomleft').add_to(m)
    
    # 添加全屏控件
    plugins.Fullscreen(position='topright').add_to(m)
    
    # 添加图层控制
    folium.LayerControl().add_to(m)
    
    return m

def add_military_grid(map_obj: folium.Map, grid_size: float = 1.0):
    """添加军事网格"""
    bounds = map_obj.get_bounds()
    print(">>>>>>>>>>>",bounds)
    if bounds and len(bounds) == 2:
        south, west = bounds[0]
        north, east = bounds[1]
        
        # 计算网格线
        lats = np.arange(south, north, grid_size)
        lngs = np.arange(west, east, grid_size)
        
        # 添加纬度线
        for lat in lats:
            folium.PolyLine(
                locations=[[lat, west], [lat, east]],
                color='#666666',
                weight=1,
                opacity=0.5,
                dash_array='5, 5'
            ).add_to(map_obj)
        
        # 添加经度线
        for lng in lngs:
            folium.PolyLine(
                locations=[[south, lng], [north, lng]],
                color='#666666',
                weight=1,
                opacity=0.5,
                dash_array='5, 5'
            ).add_to(map_obj)
        
        # 添加网格标签
        for lat in lats:
            for lng in lngs:
                if lat % 5 == 0 and lng % 5 == 0:  # 每5度添加标签
                    folium.Marker(
                        location=[lat + 0.1, lng + 0.1],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 10px; color: #666;">{lat:.1f}°, {lng:.1f}°</div>'
                        )
                    ).add_to(map_obj)

def add_radar_to_map(map_obj: folium.Map, 
                    position: List[float],
                    radar_type: str = "phased_array",
                    name: str = "雷达",
                    range_km: float = 100,
                    **kwargs):
    """添加雷达到地图"""
    
    # 根据雷达类型选择图标颜色
    color_map = {
        "phased_array": "blue",
        "mechanical": "green", 
        "mimo": "purple",
        "passive": "orange"
    }
    
    color = color_map.get(radar_type, "red")
    
    # 创建雷达图标
    radar_icon = folium.DivIcon(
        html=f"""
        <div style="
            background-color: {color};
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 5px {color};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        ">R</div>
        """,
        icon_size=(20, 20),
        icon_anchor=(10, 10)
    )
    
    # 添加雷达标记
    marker = folium.Marker(
        location=position,
        popup=folium.Popup(f"<b>{name}</b><br>类型: {radar_type}<br>探测距离: {range_km}km", max_width=200),
        tooltip=name,
        icon=radar_icon
    )
    
    marker.add_to(map_obj)
    
    # 添加探测范围圆
    folium.Circle(
        location=position,
        radius=range_km * 1000,  # 转换为米
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.1,
        weight=1
    ).add_to(map_obj)
    
    # 添加波束方向
    if "beam_direction" in kwargs:
        direction = kwargs["beam_direction"]
        beam_length = range_km * 0.8  # 波束长度
        
        end_lat = position[0] + beam_length * np.cos(np.radians(direction)) / 111
        end_lng = position[1] + beam_length * np.sin(np.radians(direction)) / (111 * np.cos(np.radians(position[0])))
        
        folium.PolyLine(
            locations=[position, [end_lat, end_lng]],
            color=color,
            weight=2,
            opacity=0.7
        ).add_to(map_obj)
    
    return marker

def add_target_to_map(map_obj: folium.Map,
                     position: List[float],
                     target_type: str = "fighter",
                     name: str = "目标",
                     speed_kts: float = 300,
                     altitude_m: float = 10000,
                     **kwargs):
    """添加目标到地图"""
    
    # 根据目标类型选择图标
    icon_map = {
        "fighter": "fighter-jet",
        "bomber": "plane",
        "uav": "drone",
        "missile": "rocket",
        "ship": "ship",
        "vehicle": "truck"
    }
    
    icon_name = icon_map.get(target_type, "target")
    color = kwargs.get("color", "red")
    
    # 创建目标图标
    target_icon = folium.DivIcon(
        html=f"""
        <div style="
            position: relative;
            width: 30px;
            height: 30px;
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                width: 30px;
                height: 30px;
                background-color: {color};
                border-radius: 50%;
                opacity: 0.7;
                animation: pulse 2s infinite;
            "></div>
            <div style="
                position: absolute;
                top: 5px;
                left: 5px;
                width: 20px;
                height: 20px;
                background-color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
                color: {color};
            ">T</div>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ transform: scale(1); opacity: 0.7; }}
                50% {{ transform: scale(1.1); opacity: 0.3; }}
                100% {{ transform: scale(1); opacity: 0.7; }}
            }}
        </style>
        """,
        icon_size=(30, 30),
        icon_anchor=(15, 15)
    )
    
    # 添加目标标记
    popup_content = f"""
    <b>{name}</b><br>
    类型: {target_type}<br>
    速度: {speed_kts}节<br>
    高度: {altitude_m:,}m
    """
    
    if "heading" in kwargs:
        popup_content += f"<br>航向: {kwargs['heading']}°"
    
    marker = folium.Marker(
        location=position,
        popup=folium.Popup(popup_content, max_width=200),
        tooltip=name,
        icon=target_icon
    )
    
    marker.add_to(map_obj)
    
    # 添加目标轨迹
    if "trajectory" in kwargs and kwargs["trajectory"]:
        trajectory = kwargs["trajectory"]
        folium.PolyLine(
            locations=trajectory,
            color=color,
            weight=2,
            opacity=0.5,
            dash_array="5, 5"
        ).add_to(map_obj)
    
    return marker

def add_engagement_zone(map_obj: folium.Map,
                       center: List[float],
                       radius_km: float = 50,
                       zone_type: str = "engagement",
                       **kwargs):
    """添加交战区域"""
    
    color_map = {
        "engagement": "red",
        "defense": "blue", 
        "no_fly": "orange",
        "warning": "yellow"
    }
    
    color = color_map.get(zone_type, "gray")
    
    # 添加圆形区域
    folium.Circle(
        location=center,
        radius=radius_km * 1000,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.2,
        weight=2
    ).add_to(map_obj)
    
    # 添加区域标签
    folium.Marker(
        location=[center[0] + 0.05, center[1] - 0.05],
        icon=folium.DivIcon(
            html=f'<div style="font-size: 12px; font-weight: bold; color: {color};">{zone_type.upper()}</div>'
        )
    ).add_to(map_obj)