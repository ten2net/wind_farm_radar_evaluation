"""
可视化工具模块
负责地图、图表和3D可视化
"""

import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
import math
import json
from pathlib import Path
from dataclasses import dataclass
import base64
from io import BytesIO

from config.config import (
    COLOR_SCHEME, MAP_CONFIG, CHART_CONFIG, 
    RADAR_FREQUENCY_BANDS, TURBINE_MODELS,
    ANTENNA_TYPES, COMMUNICATION_SYSTEMS
)
from utils.radar_calculations import RadarCalculator

@dataclass
class MapMarker:
    """地图标记类"""
    id: str
    name: str
    position: Dict[str, float]  # {lat, lon, alt}
    type: str  # wind_turbine, radar_station, comm_station, target
    icon: str
    color: str
    popup_content: str
    tooltip: str
    data: Optional[Dict[str, Any]] = None

@dataclass
class MapLayer:
    """地图图层类"""
    name: str
    feature_group: folium.FeatureGroup
    visible: bool = True
    z_index: int = 0

class VisualizationTools:
    """可视化工具类"""
    
    def __init__(self):
        """初始化可视化工具"""
        self.calculator = RadarCalculator()
        self.color_scheme = COLOR_SCHEME
        self.map_config = MAP_CONFIG
        self.chart_config = CHART_CONFIG
        
    def create_base_map(
        self, 
        center: Optional[List[float]] = None,
        zoom: Optional[int] = None,
        tile_provider: Optional[str] = None
    ) -> folium.Map:
        """
        创建基础地图
        
        参数:
            center: 地图中心坐标 [lat, lon]
            zoom: 缩放级别
            tile_provider: 底图提供者
            
        返回:
            folium地图对象
        """
        if center is None:
            center = self.map_config['default_center']
        if zoom is None:
            zoom = self.map_config['default_zoom']
        if tile_provider is None:
            tile_provider = self.map_config['tile_provider_default']
        
        # 创建地图
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            control_scale=True,
            tiles=tile_provider
        )
        
        # 添加全屏控制
        folium.plugins.Fullscreen().add_to(m)
        
        # 添加测量工具
        folium.plugins.MeasureControl(
            position='topleft',
            primary_length_unit='kilometers',
            secondary_length_unit='miles',
            primary_area_unit='sqkilometers',
            secondary_area_unit='acres'
        ).add_to(m)
        
        # 添加图层控制
        folium.LayerControl().add_to(m)
        
        return m
    
    def create_wind_turbine_marker(
        self, 
        turbine_data: Dict[str, Any]
    ) -> MapMarker:
        """
        创建风机标记
        
        参数:
            turbine_data: 风机数据
            
        返回:
            风机标记对象
        """
        # 获取风机信息
        turbine_id = turbine_data.get('id', 'unknown')
        model = turbine_data.get('model', 'unknown')
        position = turbine_data.get('position', {})
        
        # 获取风机型号信息
        model_info = TURBINE_MODELS.get(model, {})
        manufacturer = model_info.get('manufacturer', '未知')
        
        # 创建弹出窗口内容
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 300px;">
            <h4 style="color: {self.color_scheme['wind_turbine']}; margin: 0 0 10px 0;">
                🌀 风机 #{turbine_id}
            </h4>
            <p style="margin: 5px 0;"><strong>型号:</strong> {model}</p>
            <p style="margin: 5px 0;"><strong>制造商:</strong> {manufacturer}</p>
            <p style="margin: 5px 0;"><strong>位置:</strong> {position.get('lat', 0):.6f}, {position.get('lon', 0):.6f}</p>
            <p style="margin: 5px 0;"><strong>高度:</strong> {turbine_data.get('height', 0)} m</p>
            <p style="margin: 5px 0;"><strong>转子直径:</strong> {turbine_data.get('rotor_diameter', 0)} m</p>
            <p style="margin: 5px 0;"><strong>方位角:</strong> {turbine_data.get('orientation', 0)}°</p>
        </div>
        """
        
        return MapMarker(
            id=turbine_id,
            name=f"风机 {turbine_id}",
            position=position,
            type="wind_turbine",
            icon="wind",
            color=self.color_scheme['wind_turbine'],
            popup_content=popup_content,
            tooltip=f"风机 {turbine_id} ({model})",
            data=turbine_data
        )
    
    def create_radar_station_marker(
        self,
        radar_data: Dict[str, Any]
    ) -> MapMarker:
        """
        创建雷达站标记
        
        参数:
            radar_data: 雷达站数据
            
        返回:
            雷达站标记对象
        """
        radar_id = radar_data.get('id', 'unknown')
        radar_type = radar_data.get('type', '未知')
        frequency_band = radar_data.get('frequency_band', 'S')
        position = radar_data.get('position', {})
        
        # 获取频段信息
        band_info = RADAR_FREQUENCY_BANDS.get(frequency_band.upper(), {})
        band_description = band_info.get('description', '未知频段')
        
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 300px;">
            <h4 style="color: {self.color_scheme['radar_station']}; margin: 0 0 10px 0;">
                📡 雷达站 #{radar_id}
            </h4>
            <p style="margin: 5px 0;"><strong>类型:</strong> {radar_type}</p>
            <p style="margin: 5px 0;"><strong>频段:</strong> {frequency_band} ({band_description})</p>
            <p style="margin: 5px 0;"><strong>位置:</strong> {position.get('lat', 0):.6f}, {position.get('lon', 0):.6f}</p>
            <p style="margin: 5px 0;"><strong>高度:</strong> {position.get('alt', 0)} m</p>
            <p style="margin: 5px 0;"><strong>峰值功率:</strong> {radar_data.get('peak_power', 0):,.0f} W</p>
            <p style="margin: 5px 0;"><strong>天线增益:</strong> {radar_data.get('antenna_gain', 0)} dBi</p>
            <p style="margin: 5px 0;"><strong>波束宽度:</strong> {radar_data.get('beam_width', 0)}°</p>
        </div>
        """
        
        return MapMarker(
            id=radar_id,
            name=f"雷达站 {radar_id}",
            position=position,
            type="radar_station",
            icon="satellite",
            color=self.color_scheme['radar_station'],
            popup_content=popup_content,
            tooltip=f"雷达站 {radar_id} ({radar_type})",
            data=radar_data
        )
    
    def create_communication_station_marker(
        self,
        comm_data: Dict[str, Any]
    ) -> MapMarker:
        """
        创建通信站标记
        
        参数:
            comm_data: 通信站数据
            
        返回:
            通信站标记对象
        """
        comm_id = comm_data.get('id', 'unknown')
        service_type = comm_data.get('service_type', '移动通信')
        antenna_type = comm_data.get('antenna_type', '全向天线')
        position = comm_data.get('position', {})
        
        # 获取天线信息
        antenna_info = ANTENNA_TYPES.get(antenna_type, {})
        antenna_name = antenna_info.get('name', '未知天线')
        
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 300px;">
            <h4 style="color: {self.color_scheme['comm_station']}; margin: 0 0 10px 0;">
                📶 通信站 #{comm_id}
            </h4>
            <p style="margin: 5px 0;"><strong>服务类型:</strong> {service_type}</p>
            <p style="margin: 5px 0;"><strong>天线类型:</strong> {antenna_name}</p>
            <p style="margin: 5px 0;"><strong>位置:</strong> {position.get('lat', 0):.6f}, {position.get('lon', 0):.6f}</p>
            <p style="margin: 5px 0;"><strong>高度:</strong> {position.get('alt', 0)} m</p>
            <p style="margin: 5px 0;"><strong>频率:</strong> {comm_data.get('frequency', 0)} MHz</p>
            <p style="margin: 5px 0;"><strong>EIRP:</strong> {comm_data.get('eirp', 0)} dBm</p>
            <p style="margin: 5px 0;"><strong>天线增益:</strong> {comm_data.get('antenna_gain', 0)} dBi</p>
        </div>
        """
        
        return MapMarker(
            id=comm_id,
            name=f"通信站 {comm_id}",
            position=position,
            type="comm_station",
            icon="broadcast-tower",
            color=self.color_scheme['comm_station'],
            popup_content=popup_content,
            tooltip=f"通信站 {comm_id} ({service_type})",
            data=comm_data
        )
    
    def create_target_marker(
        self,
        target_data: Dict[str, Any]
    ) -> MapMarker:
        """
        创建目标标记
        
        参数:
            target_data: 目标数据
            
        返回:
            目标标记对象
        """
        target_id = target_data.get('id', 'unknown')
        target_type = target_data.get('type', '未知目标')
        rcs = target_data.get('rcs', 0)
        position = target_data.get('position', {})
        
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 300px;">
            <h4 style="color: {self.color_scheme['target']}; margin: 0 0 10px 0;">
                🎯 目标 #{target_id}
            </h4>
            <p style="margin: 5px 0;"><strong>类型:</strong> {target_type}</p>
            <p style="margin: 5px 0;"><strong>位置:</strong> {position.get('lat', 0):.6f}, {position.get('lon', 0):.6f}</p>
            <p style="margin: 5px 0;"><strong>高度:</strong> {position.get('alt', 0)} m</p>
            <p style="margin: 5px 0;"><strong>RCS:</strong> {rcs} m²</p>
            <p style="margin: 5px 0;"><strong>速度:</strong> {target_data.get('speed', 0)} m/s</p>
            <p style="margin: 5px 0;"><strong>航向:</strong> {target_data.get('heading', 0)}°</p>
        </div>
        """
        
        return MapMarker(
            id=target_id,
            name=f"目标 {target_id}",
            position=position,
            type="target",
            icon="crosshairs",
            color=self.color_scheme['target'],
            popup_content=popup_content,
            tooltip=f"目标 {target_id} ({target_type})",
            data=target_data
        )
    
    def add_marker_to_map(
        self,
        map_obj: folium.Map,
        marker: MapMarker
    ) -> folium.Marker:
        """
        添加标记到地图
        
        参数:
            map_obj: folium地图对象
            marker: 标记对象
            
        返回:
            创建的folium标记
        """
        # 创建自定义图标
        if marker.type == "wind_turbine":
            icon_color = "green"
            icon_name = "wind"
        elif marker.type == "radar_station":
            icon_color = "red"
            icon_name = "satellite"
        elif marker.type == "comm_station":
            icon_color = "blue"
            icon_name = "broadcast-tower"
        elif marker.type == "target":
            icon_color = "orange"
            icon_name = "crosshairs"
        else:
            icon_color = "gray"
            icon_name = "circle"
        
        # 创建图标
        icon = folium.Icon(
            color=icon_color,
            icon=icon_name,
            prefix='fa'
        )
        
        # 创建标记
        folium_marker = folium.Marker(
            location=[marker.position.get('lat', 0), marker.position.get('lon', 0)],
            popup=folium.Popup(marker.popup_content, max_width=300),
            tooltip=marker.tooltip,
            icon=icon
        )
        
        # 添加到地图
        folium_marker.add_to(map_obj)
        
        return folium_marker
    
    def add_radar_coverage_layer(
        self,
        map_obj: folium.Map,
        radar_position: Dict[str, float],
        radar_data: Dict[str, Any],
        max_range_km: float = 100
    ) -> folium.FeatureGroup:
        """
        添加雷达覆盖图层
        
        参数:
            map_obj: folium地图对象
            radar_position: 雷达位置
            radar_data: 雷达数据
            max_range_km: 最大覆盖范围（km）
            
        返回:
            特征组对象
        """
        # 创建特征组
        feature_group = folium.FeatureGroup(name=f"雷达覆盖范围")
        
        # 雷达位置
        radar_lat = radar_position.get('lat', 0)
        radar_lon = radar_position.get('lon', 0)
        
        # 添加雷达位置标记
        folium.CircleMarker(
            location=[radar_lat, radar_lon],
            radius=8,
            popup=f"雷达站<br>覆盖半径: {max_range_km}km",
            color=self.color_scheme['radar_station'],
            fill=True,
            fill_color=self.color_scheme['radar_station'],
            fill_opacity=0.8
        ).add_to(feature_group)
        
        # 添加覆盖范围
        folium.Circle(
            location=[radar_lat, radar_lon],
            radius=max_range_km * 1000,  # 转换为米
            popup=f'雷达覆盖范围<br>半径: {max_range_km}km',
            color=self.color_scheme['primary'],
            fill=True,
            fill_color=self.color_scheme['coverage_area'],
            fill_opacity=0.3,
            weight=2
        ).add_to(feature_group)
        
        # 如果有波束宽度信息，添加扇形覆盖
        beam_width = radar_data.get('beam_width', 360)
        if beam_width < 360:
            # 添加波束指向线
            bearing = radar_data.get('bearing', 0)
            end_lat, end_lon = self._calculate_destination(
                radar_lat, radar_lon, bearing, max_range_km
            )
            
            folium.PolyLine(
                locations=[
                    [radar_lat, radar_lon],
                    [end_lat, end_lon]
                ],
                color=self.color_scheme['primary'],
                weight=2,
                dash_array='5, 5',
                popup=f'波束指向: {bearing}°'
            ).add_to(feature_group)
        
        # 添加到地图
        feature_group.add_to(map_obj)
        
        return feature_group
    
    def add_wind_farm_layer(
        self,
        map_obj: folium.Map,
        turbines: List[Dict[str, Any]]
    ) -> folium.FeatureGroup:
        """
        添加风电场图层
        
        参数:
            map_obj: folium地图对象
            turbines: 风机列表
            
        返回:
            特征组对象
        """
        feature_group = folium.FeatureGroup(name="风电场")
        
        for turbine in turbines:
            position = turbine.get('position', {})
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            turbine_id = turbine.get('id', 'unknown')
            height = turbine.get('height', 0)
            diameter = turbine.get('rotor_diameter', 0)
            
            # 添加风机标记
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                popup=f'''风机 #{turbine_id}<br>
                         高度: {height}m<br>
                         转子直径: {diameter}m''',
                color=self.color_scheme['wind_turbine'],
                fill=True,
                fill_color=self.color_scheme['wind_turbine'],
                fill_opacity=0.6,
                weight=2
            ).add_to(feature_group)
            
            # 添加转子扫掠区域
            rotor_radius = diameter / 2
            folium.Circle(
                location=[lat, lon],
                radius=rotor_radius,
                popup=f'转子扫掠区域<br>半径: {rotor_radius}m',
                color=self.color_scheme['wind_turbine'],
                fill=True,
                fill_color=self.color_scheme['wind_turbine'],
                fill_opacity=0.1,
                weight=1
            ).add_to(feature_group)
        
        # 添加到地图
        feature_group.add_to(map_obj)
        
        return feature_group
    
    def add_interference_heatmap(
        self,
        map_obj: folium.Map,
        interference_data: List[Dict[str, Any]],
        max_interference_db: float = -50
    ) -> folium.FeatureGroup:
        """
        添加干扰热力图
        
        参数:
            map_obj: folium地图对象
            interference_data: 干扰数据
            max_interference_db: 最大干扰电平
            
        返回:
            特征组对象
        """
        feature_group = folium.FeatureGroup(name="干扰热力图")
        
        # 准备热力图数据
        heat_data = []
        for data in interference_data:
            position = data.get('position', {})
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            interference_level = data.get('interference_level_db', -100)
            
            # 归一化到[0,1]
            normalized_level = max(0, min(1, 
                (interference_level - (-100)) / (max_interference_db - (-100))
            ))
            
            heat_data.append([lat, lon, normalized_level])
        
        # 添加热力图
        from folium.plugins import HeatMap
        
        if heat_data:
            HeatMap(
                heat_data,
                radius=15,
                blur=10,
                max_zoom=1,
                gradient={
                    0.0: 'blue',
                    0.5: 'lime',
                    1.0: 'red'
                }
            ).add_to(feature_group)
        
        # 添加到地图
        feature_group.add_to(map_obj)
        
        return feature_group
    
    def create_scenario_map(
        self,
        scenario_data: Dict[str, Any],
        show_coverage: bool = True,
        show_interference: bool = False
    ) -> folium.Map:
        """
        创建场景地图
        
        参数:
            scenario_data: 场景数据
            show_coverage: 是否显示雷达覆盖
            show_interference: 是否显示干扰热力图
            
        返回:
            包含场景的folium地图
        """
        # 获取中心位置
        center_lat = scenario_data.get('center_lat', 39.0)
        center_lon = scenario_data.get('center_lon', 119.0)
        
        # 创建基础地图
        m = self.create_base_map(center=[center_lat, center_lon])
        
        # 添加风机
        turbines = scenario_data.get('wind_turbines', [])
        if turbines:
            self.add_wind_farm_layer(m, turbines)
        
        # 添加雷达站
        radar_stations = scenario_data.get('radar_stations', [])
        for radar in radar_stations:
            marker = self.create_radar_station_marker(radar)
            self.add_marker_to_map(m, marker)
            
            # 添加雷达覆盖
            if show_coverage:
                position = radar.get('position', {})
                max_range = radar.get('max_range', 100000) / 1000  # 转换为km
                self.add_radar_coverage_layer(m, position, radar, max_range)
        
        # 添加通信站
        comm_stations = scenario_data.get('communication_stations', [])
        for comm in comm_stations:
            marker = self.create_communication_station_marker(comm)
            self.add_marker_to_map(m, marker)
        
        # 添加目标
        targets = scenario_data.get('targets', [])
        for target in targets:
            marker = self.create_target_marker(target)
            self.add_marker_to_map(m, marker)
        
        # 添加干扰热力图
        if show_interference and 'interference_data' in scenario_data:
            self.add_interference_heatmap(m, scenario_data['interference_data'])
        
        # 添加图例
        self._add_map_legend(m)
        
        return m
    
    def create_snr_comparison_chart(
        self,
        snr_without_turbines: List[float],
        snr_with_turbines: List[float],
        distances: List[float],
        title: str = "有/无风机条件下信噪比对比"
    ) -> go.Figure:
        """
        创建信噪比对比图表
        
        参数:
            snr_without_turbines: 无风机条件下的SNR
            snr_with_turbines: 有风机条件下的SNR
            distances: 距离数据
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        fig = go.Figure()
        
        # 添加无风机曲线
        fig.add_trace(go.Scatter(
            x=distances,
            y=snr_without_turbines,
            mode='lines',
            name='无风机',
            line=dict(color=self.color_scheme['success'], width=3),
            hovertemplate='距离: %{x:.0f}m<br>SNR: %{y:.1f}dB<extra></extra>'
        ))
        
        # 添加有风机曲线
        fig.add_trace(go.Scatter(
            x=distances,
            y=snr_with_turbines,
            mode='lines',
            name='有风机',
            line=dict(color=self.color_scheme['warning'], width=3, dash='dash'),
            hovertemplate='距离: %{x:.0f}m<br>SNR: %{y:.1f}dB<extra></extra>'
        ))
        
        # 添加检测门限线
        threshold = 13  # 典型检测门限
        fig.add_hline(
            y=threshold,
            line_dash="dot",
            line_color="red",
            annotation_text=f"检测门限 ({threshold}dB)",
            annotation_position="bottom right"
        )
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=16, color=self.color_scheme['primary']),
                x=0.5
            ),
            xaxis_title=dict(
                text="距离 (m)",
                font=dict(color=self.color_scheme['light'])
            ),
            yaxis_title=dict(
                text="信噪比 (dB)",
                font=dict(color=self.color_scheme['light'])
            ),
            plot_bgcolor='rgba(20, 25, 50, 0.1)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.color_scheme['light']),
            hovermode='x unified',
            height=400,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(30, 30, 50, 0.7)',
                bordercolor=self.color_scheme['primary'],
                borderwidth=1
            )
        )
        
        return fig
    
    def create_power_comparison_chart(
        self,
        power_data: Dict[str, List[float]],
        distances: List[float],
        title: str = "接收功率对比"
    ) -> go.Figure:
        """
        创建功率对比图表
        
        参数:
            power_data: 功率数据字典
            distances: 距离数据
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        fig = go.Figure()
        
        colors = ['#00ccff', '#00ff99', '#ff3366', '#ff9900', '#9966ff']
        
        for i, (label, power_values) in enumerate(power_data.items()):
            fig.add_trace(go.Scatter(
                x=distances,
                y=power_values,
                mode='lines',
                name=label,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f'{label}<br>距离: %{{x:.0f}}m<br>功率: %{{y:.1f}}dB<extra></extra>'
            ))
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=16, color=self.color_scheme['primary']),
                x=0.5
            ),
            xaxis_title=dict(
                text="距离 (m)",
                font=dict(color=self.color_scheme['light'])
            ),
            yaxis_title=dict(
                text="接收功率 (dB)",
                font=dict(color=self.color_scheme['light'])
            ),
            plot_bgcolor='rgba(20, 25, 50, 0.1)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.color_scheme['light']),
            hovermode='x unified',
            height=400,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(30, 30, 50, 0.7)',
                bordercolor=self.color_scheme['primary'],
                borderwidth=1
            )
        )
        
        return fig
    
    def create_doppler_spectrum_chart(
        self,
        doppler_frequencies: List[float],
        spectrum_values: List[float],
        target_velocity: float = 0,
        title: str = "多普勒频谱"
    ) -> go.Figure:
        """
        创建多普勒频谱图表
        
        参数:
            doppler_frequencies: 多普勒频率数组
            spectrum_values: 频谱值数组
            target_velocity: 目标速度
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        fig = go.Figure()
        
        # 添加频谱曲线
        fig.add_trace(go.Scatter(
            x=doppler_frequencies,
            y=spectrum_values,
            mode='lines',
            name='频谱',
            line=dict(color=self.color_scheme['primary'], width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 204, 255, 0.2)',
            hovertemplate='频率: %{x:.0f}Hz<br>幅度: %{y:.1f}<extra></extra>'
        ))
        
        # 如果有目标速度，标记目标位置
        if target_velocity != 0:
            # 计算目标多普勒频率
            target_frequency = 2 * target_velocity / 0.1  # 假设波长为0.1m
            
            fig.add_vline(
                x=target_frequency,
                line_dash="dash",
                line_color=self.color_scheme['warning'],
                annotation_text=f"目标: {target_velocity}m/s",
                annotation_position="top right"
            )
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=16, color=self.color_scheme['primary']),
                x=0.5
            ),
            xaxis_title=dict(
                text="多普勒频率 (Hz)",
                font=dict(color=self.color_scheme['light'])
            ),
            yaxis_title=dict(
                text="幅度",
                font=dict(color=self.color_scheme['light'])
            ),
            plot_bgcolor='rgba(20, 25, 50, 0.1)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.color_scheme['light']),
            height=400
        )
        
        return fig
    
    def create_multipath_analysis_chart(
        self,
        multipath_data: Dict[str, List[float]],
        distances: List[float],
        title: str = "多径效应分析"
    ) -> go.Figure:
        """
        创建多径效应分析图表
        
        参数:
            multipath_data: 多径数据字典
            distances: 距离数据
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        fig = go.Figure()
        
        # 添加多径损耗曲线
        if 'multipath_loss' in multipath_data:
            fig.add_trace(go.Scatter(
                x=distances,
                y=multipath_data['multipath_loss'],
                mode='lines',
                name='多径损耗',
                line=dict(color=self.color_scheme['warning'], width=2),
                hovertemplate='距离: %{x:.0f}m<br>损耗: %{y:.1f}dB<extra></extra>'
            ))
        
        # 添加路径差曲线
        if 'path_difference' in multipath_data:
            fig.add_trace(go.Scatter(
                x=distances,
                y=multipath_data['path_difference'],
                mode='lines',
                name='路径差',
                line=dict(color=self.color_scheme['info'], width=2, dash='dash'),
                yaxis='y2',
                hovertemplate='距离: %{x:.0f}m<br>路径差: %{y:.1f}m<extra></extra>'
            ))
        
        # 更新布局
        layout = dict(
            title=dict(
                text=title,
                font=dict(size=16, color=self.color_scheme['primary']),
                x=0.5
            ),
            xaxis=dict(
                title=dict(text="距离 (m)", font=dict(color=self.color_scheme['light'])),
                gridcolor='rgba(100, 100, 100, 0.2)'
            ),
            yaxis=dict(
                title=dict(text="多径损耗 (dB)", font=dict(color=self.color_scheme['warning'])),
                gridcolor='rgba(100, 100, 100, 0.2)'
            ),
            yaxis2=dict(
                title=dict(text="路径差 (m)", font=dict(color=self.color_scheme['info'])),
                overlaying='y',
                side='right',
                gridcolor='rgba(100, 100, 100, 0.1)'
            ),
            plot_bgcolor='rgba(20, 25, 50, 0.1)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.color_scheme['light']),
            hovermode='x unified',
            height=400,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(30, 30, 50, 0.7)',
                bordercolor=self.color_scheme['primary'],
                borderwidth=1
            )
        )
        
        fig.update_layout(layout)
        
        return fig
    
    def create_interference_analysis_chart(
        self,
        interference_data: Dict[str, Any],
        title: str = "干扰分析"
    ) -> go.Figure:
        """
        创建干扰分析图表
        
        参数:
            interference_data: 干扰数据
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "载干比分布", 
                "干扰电平分布",
                "频率重叠分析",
                "干扰余量分析"
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )
        
        # 1. 载干比分布
        if 'cir_values' in interference_data:
            fig.add_trace(
                go.Histogram(
                    x=interference_data['cir_values'],
                    name='CIR分布',
                    marker_color=self.color_scheme['primary'],
                    nbinsx=20
                ),
                row=1, col=1
            )
            
            # 添加门限线
            fig.add_vline(
                x=20,  # 典型CIR门限
                line_dash="dash",
                line_color="red",
                row=1, col=1
            )
        
        # 2. 干扰电平分布
        if 'interference_levels' in interference_data:
            fig.add_trace(
                go.Box(
                    y=interference_data['interference_levels'],
                    name='干扰电平',
                    marker_color=self.color_scheme['warning'],
                    boxmean='sd'
                ),
                row=1, col=2
            )
        
        # 3. 频率重叠分析
        if 'frequency_overlap' in interference_data:
            frequencies = interference_data['frequency_overlap'].get('frequencies', [])
            desired_power = interference_data['frequency_overlap'].get('desired_power', [])
            interference_power = interference_data['frequency_overlap'].get('interference_power', [])
            
            fig.add_trace(
                go.Scatter(
                    x=frequencies,
                    y=desired_power,
                    mode='lines',
                    name='期望信号',
                    line=dict(color=self.color_scheme['success'], width=2)
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=frequencies,
                    y=interference_power,
                    mode='lines',
                    name='干扰信号',
                    line=dict(color=self.color_scheme['danger'], width=2, dash='dash'),
                    fill='tozeroy',
                    fillcolor='rgba(255, 51, 102, 0.2)'
                ),
                row=2, col=1
            )
        
        # 4. 干扰余量分析
        if 'interference_margin' in interference_data:
            margin_data = interference_data['interference_margin']
            
            categories = list(margin_data.keys())
            values = list(margin_data.values())
            
            # 创建颜色数组
            colors = []
            for val in values:
                if val >= 10:
                    colors.append(self.color_scheme['success'])
                elif val >= 0:
                    colors.append(self.color_scheme['warning'])
                else:
                    colors.append(self.color_scheme['danger'])
            
            fig.add_trace(
                go.Bar(
                    x=categories,
                    y=values,
                    name='干扰余量',
                    marker_color=colors,
                    text=[f'{v:.1f}dB' for v in values],
                    textposition='auto'
                ),
                row=2, col=2
            )
            
            # 添加0dB线
            fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=2)
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, color=self.color_scheme['primary']),
                x=0.5
            ),
            plot_bgcolor='rgba(20, 25, 50, 0.1)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.color_scheme['light']),
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(30, 30, 50, 0.7)',
                bordercolor=self.color_scheme['primary'],
                borderwidth=1
            )
        )
        
        # 更新子图样式
        for i in range(1, 5):
            row = (i-1)//2 + 1
            col = (i-1)%2 + 1
            
            fig.update_xaxes(
                gridcolor='rgba(100, 100, 100, 0.2)',
                linecolor='rgba(200, 200, 200, 0.3)',
                row=row, col=col
            )
            fig.update_yaxes(
                gridcolor='rgba(100, 100, 100, 0.2)',
                linecolor='rgba(200, 200, 200, 0.3)',
                row=row, col=col
            )
        
        return fig
    
    def create_performance_summary_chart(
        self,
        performance_metrics: Dict[str, Any],
        title: str = "性能指标总结"
    ) -> go.Figure:
        """
        创建性能指标总结图表
        
        参数:
            performance_metrics: 性能指标数据
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        # 提取关键指标
        categories = [
            '检测性能', '跟踪能力', '距离分辨率',
            '速度分辨率', '干扰影响', '杂波影响'
        ]
        
        values = [
            1.0 if performance_metrics.get('detection_performance') == '可检测' else 0.5,
            1.0 if performance_metrics.get('tracking_capability') == '可跟踪' else 0.5,
            1.0 if performance_metrics.get('range_resolution_quality') == '高' else 0.5,
            1.0 if performance_metrics.get('velocity_resolution_quality') == '高' else 0.5,
            1.0 if performance_metrics.get('interference_impact') == '轻微' else 0.5,
            1.0 if performance_metrics.get('clutter_impact') == '轻微' else 0.5
        ]
        
        # 创建雷达图
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='性能指标',
            line_color=self.color_scheme['primary'],
            fillcolor='rgba(0, 204, 255, 0.3)'
        ))
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=16, color=self.color_scheme['primary']),
                x=0.5
            ),
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    gridcolor='rgba(100, 100, 100, 0.3)',
                    linecolor='rgba(200, 200, 200, 0.5)',
                    tickfont=dict(color=self.color_scheme['light'])
                ),
                angularaxis=dict(
                    gridcolor='rgba(100, 100, 100, 0.3)',
                    linecolor='rgba(200, 200, 200, 0.5)',
                    rotation=90,
                    direction='clockwise',
                    tickfont=dict(color=self.color_scheme['light'])
                ),
                bgcolor='rgba(20, 25, 50, 0.1)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.color_scheme['light']),
            height=500,
            showlegend=False
        )
        
        return fig
    
    def create_comprehensive_dashboard(
        self,
        analysis_results: Dict[str, Any],
        scenario_name: str = "评估场景"
    ) -> List[go.Figure]:
        """
        创建综合仪表板
        
        参数:
            analysis_results: 分析结果
            scenario_name: 场景名称
            
        返回:
            图表列表
        """
        charts = []
        
        # 1. 信噪比对比图
        if 'snr_comparison' in analysis_results:
            snr_data = analysis_results['snr_comparison']
            fig1 = self.create_snr_comparison_chart(
                snr_data.get('without_turbines', []),
                snr_data.get('with_turbines', []),
                snr_data.get('distances', []),
                title=f"{scenario_name} - 信噪比对比"
            )
            charts.append(fig1)
        
        # 2. 接收功率对比图
        if 'power_comparison' in analysis_results:
            power_data = analysis_results['power_comparison']
            fig2 = self.create_power_comparison_chart(
                power_data.get('power_values', {}),
                power_data.get('distances', []),
                title=f"{scenario_name} - 接收功率对比"
            )
            charts.append(fig2)
        
        # 3. 多普勒频谱图
        if 'doppler_analysis' in analysis_results:
            doppler_data = analysis_results['doppler_analysis']
            fig3 = self.create_doppler_spectrum_chart(
                doppler_data.get('frequencies', []),
                doppler_data.get('spectrum', []),
                doppler_data.get('target_velocity', 0),
                title=f"{scenario_name} - 多普勒频谱"
            )
            charts.append(fig3)
        
        # 4. 多径效应分析图
        if 'multipath_analysis' in analysis_results:
            multipath_data = analysis_results['multipath_analysis']
            fig4 = self.create_multipath_analysis_chart(
                multipath_data.get('data', {}),
                multipath_data.get('distances', []),
                title=f"{scenario_name} - 多径效应分析"
            )
            charts.append(fig4)
        
        # 5. 干扰分析图
        if 'interference_analysis' in analysis_results:
            interference_data = analysis_results['interference_analysis']
            fig5 = self.create_interference_analysis_chart(
                interference_data,
                title=f"{scenario_name} - 干扰分析"
            )
            charts.append(fig5)
        
        # 6. 性能总结图
        if 'performance_metrics' in analysis_results:
            performance_data = analysis_results['performance_metrics']
            fig6 = self.create_performance_summary_chart(
                performance_data,
                title=f"{scenario_name} - 性能指标总结"
            )
            charts.append(fig6)
        
        return charts
    
    def save_chart_as_image(
        self,
        fig: go.Figure,
        filename: str,
        output_dir: Path,
        width: int = 1200,
        height: int = 800,
        format: str = 'png'
    ) -> str:
        """
        保存图表为图片
        
        参数:
            fig: Plotly图表对象
            filename: 文件名
            output_dir: 输出目录
            width: 图片宽度
            height: 图片高度
            format: 图片格式
            
        返回:
            保存的文件路径
        """
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加扩展名
        if not filename.endswith(f'.{format}'):
            filename = f"{filename}.{format}"
        
        # 完整文件路径
        filepath = output_dir / filename
        
        # 保存图表
        fig.write_image(
            str(filepath),
            width=width,
            height=height,
            scale=2  # 提高分辨率
        )
        
        return str(filepath)
    
    def _add_map_legend(self, map_obj: folium.Map) -> None:
        """添加地图图例"""
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
            <h4 style="margin-top:0; color: {self.color_scheme['primary']}">图例</h4>
            <p style="margin: 5px 0;"><span style="color: {self.color_scheme['wind_turbine']}; font-weight: bold;">●</span> 风机</p>
            <p style="margin: 5px 0;"><span style="color: {self.color_scheme['radar_station']}; font-weight: bold;">●</span> 雷达站</p>
            <p style="margin: 5px 0;"><span style="color: {self.color_scheme['comm_station']}; font-weight: bold;">●</span> 通信站</p>
            <p style="margin: 5px 0;"><span style="color: {self.color_scheme['target']}; font-weight: bold;">●</span> 目标</p>
            <p style="margin: 5px 0;"><span style="color: {self.color_scheme['coverage_area']}; font-weight: bold;">◯</span> 雷达覆盖</p>
            <p style="margin: 5px 0;"><span style="color: {self.color_scheme['interference_area']}; font-weight: bold;">◯</span> 干扰区域</p>
        </div>
        '''
        
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def _calculate_destination(
        self,
        lat: float,
        lon: float,
        bearing: float,
        distance_km: float
    ) -> Tuple[float, float]:
        """计算目标点坐标"""
        R = 6371.0  # 地球半径，km
        
        # 转换为弧度
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        bearing_rad = math.radians(bearing)
        
        # 角距离
        angular_distance = distance_km / R
        
        # 计算目标点
        dest_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(angular_distance) +
            math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
        )
        
        dest_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
            math.cos(angular_distance) - math.sin(lat_rad) * math.sin(dest_lat_rad)
        )
        
        return math.degrees(dest_lat_rad), math.degrees(dest_lon_rad)

# 创建全局可视化工具实例
viz_tools = VisualizationTools()