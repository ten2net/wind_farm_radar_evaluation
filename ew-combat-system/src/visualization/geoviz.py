"""
电子战对抗仿真地理可视化模块
基于Folium的地理可视化工具
"""
import traceback
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import folium
from folium import plugins
import branca.colormap as cm
import matplotlib.pyplot as plt
import matplotlib.cm as mcm
from matplotlib.colors import Normalize
from datetime import datetime
import math

from ..core.entities import Radar, Jammer, Target, Position


class EWVisualizer:
    """基于Folium的电子战可视化器"""
    
    def __init__(self, center_lat: float = 39.9, center_lon: float = 116.4, zoom_start: int = 6):
        """
        初始化可视化器
        
        参数:
            center_lat: 地图中心纬度
            center_lon: 地图中心经度
            zoom_start: 初始缩放级别
        """
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.zoom_start = zoom_start
        
        # 地图样式选项
        self.tiles_options = {
            "标准地图": "OpenStreetMap",
            "卫星影像": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "地形图": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            "深色主题": "CartoDB dark_matter"
        }
        
        # 颜色映射
        self.colormaps = {
            'radar': 'Blues',
            'jammer': 'Reds',
            'target': 'Greens',
            'signal': 'viridis'
        }
        
        # 创建输出目录
        self.output_dir = Path("static/visualizations")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 缓存已创建的地图
        self.current_map = None
        
    @staticmethod
    def create_matplotlib_plot(radars: List, jammers: List, targets: Optional[List] = None) -> plt.Figure:
        """
        创建Matplotlib可视化图表
        这是修复后添加的方法
        
        参数:
            radars: 雷达列表
            jammers: 干扰机列表
            targets: 目标列表，可选
            
        返回:
            Matplotlib图形对象
        """
        try:
            return EWVisualizer._create_simple_visualization(radars, jammers, targets)
        except Exception as e:
            print(f"创建Matplotlib图表失败: {e}")
            return EWVisualizer._create_basic_matplotlib_plot(radars, jammers, targets)        
    
    @staticmethod
    def _create_simple_visualization(radars: List, jammers: List, 
                                   targets: Optional[List] = None,
                                   bbox: Optional[Tuple[float, float, float, float]] = None) -> Any:
        """创建简单的可视化（备用方案）"""
        try:
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            
            # 获取所有位置计算边界
            all_positions = []
            for radar in radars:
                all_positions.append([radar.position['lon'], radar.position['lat']])
            for jammer in jammers:
                all_positions.append([jammer.position['lon'], jammer.position['lat']])
            if targets:
                for target in targets:
                    all_positions.append([target.position['lon'], target.position['lat']])
            
            if all_positions:
                lons = [p[0] for p in all_positions]
                lats = [p[1] for p in all_positions]
                
                if bbox is None:
                    padding = 0.5
                    bbox = (
                        min(lons) - padding,
                        min(lats) - padding,
                        max(lons) + padding,
                        max(lats) + padding
                    )
            else:
                bbox = (115.9, 39.4, 116.9, 40.4)
            
            min_lon, min_lat, max_lon, max_lat = bbox
            
            # 创建图形和坐标轴
            fig = plt.figure(figsize=(12, 10))
            
            # 使用PlateCarree投影
            ax = plt.axes(projection=ccrs.PlateCarree())
            
            # 设置地图范围
            ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree()) # type: ignore
            
            # 添加地理特征
            ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3) # type: ignore
            ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3) # type: ignore
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5, alpha=0.5) # type: ignore
            ax.add_feature(cfeature.BORDERS, linewidth=0.5, alpha=0.5, linestyle=':') # type: ignore
            
            # 添加经纬度网格
            gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, linestyle='--') # type: ignore
            gl.top_labels = False
            gl.right_labels = False
            
            # 绘制雷达
            radar_scatter = None
            if radars:
                radar_lons = [r.position['lon'] for r in radars]
                radar_lats = [r.position['lat'] for r in radars]
                radar_names = [r.name for r in radars]
                
                radar_scatter = ax.scatter(
                    radar_lons, radar_lats, 
                    c='blue', s=150, marker='^', 
                    edgecolors='black', linewidth=1.5, 
                    transform=ccrs.PlateCarree(),
                    label=f'雷达 ({len(radars)}个)',
                    zorder=5
                )
                
                # 添加雷达标签
                for i, (lon, lat, name) in enumerate(zip(radar_lons, radar_lats, radar_names)):
                    ax.text(lon + 0.01, lat + 0.01, name, 
                           transform=ccrs.PlateCarree(),
                           fontsize=8, color='blue',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
            
            # 绘制干扰机
            jammer_scatter = None
            if jammers:
                jammer_lons = [j.position['lon'] for j in jammers]
                jammer_lats = [j.position['lat'] for j in jammers]
                jammer_names = [j.name for j in jammers]
                
                jammer_scatter = ax.scatter(
                    jammer_lons, jammer_lats, 
                    c='red', s=120, marker='s', 
                    edgecolors='black', linewidth=1.5,
                    transform=ccrs.PlateCarree(),
                    label=f'干扰机 ({len(jammers)}个)',
                    zorder=5
                )
                
                # 添加干扰机标签
                for i, (lon, lat, name) in enumerate(zip(jammer_lons, jammer_lats, jammer_names)):
                    ax.text(lon + 0.01, lat + 0.01, name, 
                           transform=ccrs.PlateCarree(),
                           fontsize=8, color='red',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
            
            # 绘制目标
            target_scatter = None
            if targets:
                target_lons = [t.position['lon'] for t in targets]
                target_lats = [t.position['lat'] for t in targets]
                target_names = [t.name for t in targets]
                
                target_scatter = ax.scatter(
                    target_lons, target_lats, 
                    c='green', s=100, marker='o', 
                    edgecolors='black', linewidth=1.5,
                    transform=ccrs.PlateCarree(),
                    label=f'目标 ({len(targets)}个)',
                    zorder=5
                )
                
                # 添加目标标签
                for i, (lon, lat, name) in enumerate(zip(target_lons, target_lats, target_names)):
                    ax.text(lon + 0.01, lat + 0.01, name, 
                           transform=ccrs.PlateCarree(),
                           fontsize=8, color='green',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
            
            # 添加图例
            handles = []
            if radar_scatter:
                handles.append(radar_scatter)
            if jammer_scatter:
                handles.append(jammer_scatter)
            if target_scatter:
                handles.append(target_scatter)
            
            if handles:
                ax.legend(handles=handles, loc='upper right', fontsize=10)
            
            # 设置标题
            ax.set_title('电子战对抗态势图', fontsize=16, fontweight='bold', pad=20)
            
            # 添加比例尺
            scale_lon = max_lon - 0.3
            scale_lat = min_lat + 0.1
            scale_length_deg = 0.9  # 大约100km在纬度40度
            
            # 添加比例尺文本
            ax.text(scale_lon + scale_length_deg/2, scale_lat - 0.02, '~100 km',
                   transform=ccrs.PlateCarree(),
                   ha='center', fontsize=9)
            
            # 添加比例尺线
            ax.plot([scale_lon, scale_lon + scale_length_deg], 
                   [scale_lat, scale_lat], 
                   'k-', linewidth=3, transform=ccrs.PlateCarree())
            ax.plot([scale_lon, scale_lon], 
                   [scale_lat - 0.01, scale_lat + 0.01], 
                   'k-', linewidth=2, transform=ccrs.PlateCarree())
            ax.plot([scale_lon + scale_length_deg, scale_lon + scale_length_deg], 
                   [scale_lat - 0.01, scale_lat + 0.01], 
                   'k-', linewidth=2, transform=ccrs.PlateCarree())
            
            # 调整布局
            plt.tight_layout()
            
            return fig
            
        except Exception as e:
            print(f"创建Cartopy图表失败: {e}")
            # 使用简单的Matplotlib图表
            return EWVisualizer._create_basic_matplotlib_plot(radars, jammers, targets, bbox)
    @staticmethod
    def _create_basic_matplotlib_plot(radars: List, jammers: List, 
                                    targets: Optional[List] = None,
                                    bbox: Optional[Tuple[float, float, float, float]] = None) -> Any:
        """创建基础的Matplotlib图表"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 设置背景
            ax.set_facecolor('#f0f0f0')
            
            # 绘制雷达
            if radars:
                radar_lons = [r.position['lon'] for r in radars]
                radar_lats = [r.position['lat'] for r in radars]
                radar_names = [r.name for r in radars]
                
                radar_scatter = ax.scatter(radar_lons, radar_lats, c='blue', s=150, marker='^', 
                                         label=f'雷达 ({len(radars)}个)', edgecolors='black', linewidth=1.5)
                
                # 添加雷达标签
                for i, (lon, lat, name) in enumerate(zip(radar_lons, radar_lats, radar_names)):
                    ax.text(lon + 0.01, lat + 0.01, name, fontsize=9, color='blue',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
            
            # 绘制干扰机
            if jammers:
                jammer_lons = [j.position['lon'] for j in jammers]
                jammer_lats = [j.position['lat'] for j in jammers]
                jammer_names = [j.name for j in jammers]
                
                jammer_scatter = ax.scatter(jammer_lons, jammer_lats, c='red', s=120, marker='s', 
                                          label=f'干扰机 ({len(jammers)}个)', edgecolors='black', linewidth=1.5)
                
                # 添加干扰机标签
                for i, (lon, lat, name) in enumerate(zip(jammer_lons, jammer_lats, jammer_names)):
                    ax.text(lon + 0.01, lat + 0.01, name, fontsize=9, color='red',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
            
            # 绘制目标
            if targets:
                target_lons = [t.position['lon'] for t in targets]
                target_lats = [t.position['lat'] for t in targets]
                target_names = [t.name for t in targets]
                
                target_scatter = ax.scatter(target_lons, target_lats, c='green', s=100, marker='o', 
                                          label=f'目标 ({len(targets)}个)', edgecolors='black', linewidth=1.5)
                
                # 添加目标标签
                for i, (lon, lat, name) in enumerate(zip(target_lons, target_lats, target_names)):
                    ax.text(lon + 0.01, lat + 0.01, name, fontsize=9, color='green',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
            
            # 设置标签和标题
            ax.set_xlabel('经度')
            ax.set_ylabel('纬度')
            ax.set_title('电子战对抗态势图', fontsize=16, fontweight='bold')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # 设置坐标轴范围
            if bbox:
                min_lon, min_lat, max_lon, max_lat = bbox
                ax.set_xlim(min_lon, max_lon)
                ax.set_ylim(min_lat, max_lat)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"创建基础Matplotlib图表失败: {e}")
            # 返回错误提示图
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, f'可视化错误: {str(e)}', 
                   ha='center', va='center', fontsize=12, color='red')
            return fig            
    
    @staticmethod
    def create_folium_map(radars: List, jammers: List, targets: Optional[List] = None) -> folium.Map:
        """
        使用Folium创建交互式地图
        
        参数:
            radars: 雷达列表
            jammers: 干扰机列表
            targets: 目标列表，可选
            
        返回:
            Folium地图对象
        """
        try:
            # 计算中心点
            all_positions = []
            for radar in radars:
                if hasattr(radar, 'position'):
                    if isinstance(radar.position, dict):
                        lat = radar.position.get('lat', 39.9)
                        lon = radar.position.get('lon', 116.4)
                    else:
                        lat = getattr(radar.position, 'lat', 39.9)
                        lon = getattr(radar.position, 'lon', 116.4)
                else:
                    lat = getattr(radar, 'lat', 39.9)
                    lon = getattr(radar, 'lon', 116.4)
                all_positions.append([lat, lon])
            
            for jammer in jammers:
                if hasattr(jammer, 'position'):
                    if isinstance(jammer.position, dict):
                        lat = jammer.position.get('lat', 40.0)
                        lon = jammer.position.get('lon', 116.5)
                    else:
                        lat = getattr(jammer.position, 'lat', 40.0)
                        lon = getattr(jammer.position, 'lon', 116.5)
                else:
                    lat = getattr(jammer, 'lat', 40.0)
                    lon = getattr(jammer, 'lon', 116.5)
                all_positions.append([lat, lon])
            
            if all_positions:
                center_lat = np.mean([p[0] for p in all_positions])
                center_lon = np.mean([p[1] for p in all_positions])
            else:
                center_lat, center_lon = 39.9, 116.4
            
            # 创建地图
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=8
            )
            
            # 添加雷达标记
            for radar in radars:
                if hasattr(radar, 'position'):
                    if isinstance(radar.position, dict):
                        lat = radar.position.get('lat', 39.9)
                        lon = radar.position.get('lon', 116.4)
                    else:
                        lat = getattr(radar.position, 'lat', 39.9)
                        lon = getattr(radar.position, 'lon', 116.4)
                else:
                    lat = getattr(radar, 'lat', 39.9)
                    lon = getattr(radar, 'lon', 116.4)
                
                folium.Marker(
                    location=[lat, lon],
                    popup=f"雷达: {getattr(radar, 'name', '未知')}",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
            
            # 添加干扰机标记
            for jammer in jammers:
                if hasattr(jammer, 'position'):
                    if isinstance(jammer.position, dict):
                        lat = jammer.position.get('lat', 40.0)
                        lon = jammer.position.get('lon', 116.5)
                    else:
                        lat = getattr(jammer.position, 'lat', 40.0)
                        lon = getattr(jammer.position, 'lon', 116.5)
                else:
                    lat = getattr(jammer, 'lat', 40.0)
                    lon = getattr(jammer, 'lon', 116.5)
                
                folium.Marker(
                    location=[lat, lon],
                    popup=f"干扰机: {getattr(jammer, 'name', '未知')}",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
            
            return m
            
        except Exception as e:
            print(f"创建Folium地图失败: {e}")
            return folium.Map(location=[39.9, 116.4], zoom_start=8)    
    def create_base_map(self, tile_style: str = "标准地图") -> folium.Map:
        """
        创建基础地图
        
        参数:
            tile_style: 地图瓦片样式
            
        返回:
            Folium地图对象
        """
        # 获取瓦片URL
        tiles = self.tiles_options.get(tile_style, "OpenStreetMap")
        
        # 创建地图
        m = folium.Map(
            location=[self.center_lat, self.center_lon],
            zoom_start=self.zoom_start,
            tiles=tiles,
            attr='Map data © OpenStreetMap contributors'
        )
        
        # 添加全屏控件
        plugins.Fullscreen().add_to(m)
        
        # 添加比例尺
        # plugins.ScaleBar(position='bottomleft').add_to(m) # type: ignore
        
        # 添加绘制工具
        draw = plugins.Draw(
            export=True,
            position='topleft',
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': True,
                'marker': True,
                'circlemarker': False
            }
        )
        draw.add_to(m)
        
        return m
    
    def calculate_circle_coordinates(self, center_lat: float, center_lon: float, 
                                    radius_km: float, num_points: int = 36) -> List[Tuple[float, float]]:
        """
        计算圆形覆盖范围的坐标点
        
        参数:
            center_lat: 中心纬度
            center_lon: 中心经度
            radius_km: 半径（公里）
            num_points: 点数
            
        返回:
            坐标点列表
        """
        coordinates = []
        
        for i in range(num_points + 1):
            angle = 2 * math.pi * i / num_points
            
            # 计算偏移（以度为单位）
            lat_offset = (radius_km / 111.32) * math.cos(angle)  # 1度纬度约111.32公里
            lon_offset = (radius_km / (111.32 * math.cos(math.radians(center_lat)))) * math.sin(angle)
            
            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            
            coordinates.append((lat, lon))
        
        return coordinates
    
    def calculate_sector_coordinates(self, center_lat: float, center_lon: float,
                                    azimuth: float, width: float, 
                                    radius_km: float, num_points: int = 20) -> List[Tuple[float, float]]:
        """
        计算扇形区域的坐标点
        
        参数:
            center_lat: 中心纬度
            center_lon: 中心经度
            azimuth: 中心方位角（度）
            width: 扇区宽度（度）
            radius_km: 半径（公里）
            num_points: 点数
            
        返回:
            坐标点列表
        """
        coordinates = []
        
        # 起始点
        coordinates.append((center_lat, center_lon))
        
        # 转换角度为弧度
        az_rad = math.radians(azimuth)
        width_rad = math.radians(width)
        
        # 计算扇形边缘
        for i in range(num_points + 1):
            angle = az_rad - width_rad/2 + width_rad * i / num_points
            
            lat_offset = (radius_km / 111.32) * math.cos(angle)
            lon_offset = (radius_km / (111.32 * math.cos(math.radians(center_lat)))) * math.sin(angle)
            
            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            
            coordinates.append((lat, lon))
        
        return coordinates
    
    def add_radar_to_map(self, radar: Radar, m: folium.Map, show_coverage: bool = True) -> None:
        """
        添加雷达到地图
        
        参数:
            radar: 雷达对象
            m: Folium地图
            show_coverage: 是否显示覆盖范围
        """
        # 雷达位置
        lat, lon = radar.position.lat, radar.position.lon
        
        # 创建雷达标记
        radar_icon = folium.Icon(
            color='blue',
            icon='radar',
            prefix='fa',
            icon_color='white'
        )
        
        # 雷达弹窗信息
        popup_html = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: blue; margin-bottom: 5px;">{radar.name}</h4>
            <hr style="margin: 5px 0;">
            <p><b>位置:</b> {lat:.4f}, {lon:.4f}</p>
            <p><b>高度:</b> {radar.position.alt} 米</p>
            <p><b>频率:</b> {radar.radar_params.frequency} GHz</p>
            <p><b>功率:</b> {radar.radar_params.power} kW</p>
            <p><b>增益:</b> {radar.radar_params.gain} dBi</p>
            <p><b>波束宽度:</b> {radar.radar_params.beamwidth} 度</p>
        </div>
        """
        
        # 添加雷达标记

        radar_icon = folium.Icon(
            color='red',
            icon='rss',
            prefix='fa',
            icon_color='white'
        )        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"雷达: {radar.name}",
            icon=radar_icon
        ).add_to(m)
        
        # 添加雷达覆盖范围
        if show_coverage:
            # 计算覆盖范围半径（简化模型）
            # 这里可以根据雷达参数计算实际覆盖范围
            coverage_radius = 100  # 公里
            
            # 计算圆形坐标
            coverage_coords = self.calculate_circle_coordinates(lat, lon, coverage_radius)
            
            # 添加覆盖范围多边形
            folium.Polygon(
                locations=coverage_coords,
                color='blue',
                weight=1,
                fill=True,
                fill_color='blue',
                fill_opacity=0.2,
                popup=f'{radar.name} 覆盖范围 ({coverage_radius}km)',
                tooltip=f'雷达覆盖范围'
            ).add_to(m)
    
    def add_jammer_to_map(self, jammer: Jammer, m: folium.Map, show_sector: bool = True) -> None:
        """
        添加干扰机到地图
        
        参数:
            jammer: 干扰机对象
            m: Folium地图
            show_sector: 是否显示干扰扇区
        """
        # 干扰机位置
        lat, lon = jammer.position.lat, jammer.position.lon
        
        # 创建干扰机标记
        jammer_icon = folium.Icon(
            color='red',
            icon='signal',
            prefix='fa',
            icon_color='white'
        )
        
        # 干扰机弹窗信息
        popup_html = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: red; margin-bottom: 5px;">{jammer.name}</h4>
            <hr style="margin: 5px 0;">
            <p><b>位置:</b> {lat:.4f}, {lon:.4f}</p>
            <p><b>高度:</b> {jammer.position.alt} 米</p>
            <p><b>功率:</b> {jammer.jammer_params.power} W</p>
            <p><b>增益:</b> {jammer.jammer_params.gain} dBi</p>
            <p><b>带宽:</b> {jammer.jammer_params.bandwidth} MHz</p>
            <p><b>频率范围:</b> {jammer.jammer_params.frequency_range[0]}-{jammer.jammer_params.frequency_range[1]} GHz</p>
        </div>
        """
        
        # 添加干扰机标记
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"干扰机: {jammer.name}",
            icon=jammer_icon
        ).add_to(m)
        
        # 添加干扰扇区
        if show_sector:
            # 扇区参数
            azimuth = 45  # 方位角
            width = 60    # 扇区宽度
            range_km = 100  # 作用距离
            
            # 计算扇区坐标
            sector_coords = self.calculate_sector_coordinates(lat, lon, azimuth, width, range_km)
            
            # 添加扇区多边形
            folium.Polygon(
                locations=sector_coords,
                color='red',
                weight=1,
                fill=True,
                fill_color='red',
                fill_opacity=0.3,
                popup=f'{jammer.name} 干扰扇区',
                tooltip=f'干扰扇区'
            ).add_to(m)
    
    def add_target_to_map(self, target: Target, m: folium.Map) -> None:
        """
        添加目标到地图
        
        参数:
            target: 目标对象
            m: Folium地图
        """
        # 目标位置
        lat, lon = target.position.lat, target.position.lon
        
        # 创建目标标记
        target_icon = folium.Icon(
            color='green',
            icon='fighter-jet',
            prefix='fa',
            icon_color='white'
        )
        
        # 目标弹窗信息
        popup_html = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: green; margin-bottom: 5px;">{target.name}</h4>
            <hr style="margin: 5px 0;">
            <p><b>位置:</b> {lat:.4f}, {lon:.4f}</p>
            <p><b>高度:</b> {target.position.alt} 米</p>
            <p><b>RCS:</b> {target.rcs} m²</p>
            <p><b>速度:</b> {target.speed} m/s</p>
        </div>
        """
        
        # 添加目标标记
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"目标: {target.name}",
            icon=target_icon
        ).add_to(m)
    
    def add_signal_heatmap(self, radars: List[Radar], m: folium.Map, resolution: float = 0.1) -> None:
        """
        添加信号强度热力图
        
        参数:
            radars: 雷达列表
            m: Folium地图
            resolution: 网格分辨率（度）
        """
        if not radars:
            return
        
        # 计算所有雷达的边界
        lats = [r.position.lat for r in radars]
        lons = [r.position.lon for r in radars]
        
        if not lats or not lons:
            return
        
        # 扩展边界
        lat_min, lat_max = min(lats) - 1, max(lats) + 1
        lon_min, lon_max = min(lons) - 1, max(lons) + 1
        
        # 创建网格
        lat_grid = np.arange(lat_min, lat_max, resolution)
        lon_grid = np.arange(lon_min, lon_max, resolution)
        
        # 计算每个网格点的信号强度
        heat_data = []
        
        for lat in lat_grid:
            for lon in lon_grid:
                total_signal = 0
                for radar in radars:
                    # 简化的信号强度计算（距离衰减）
                    distance = math.sqrt((lon - radar.position.lon)**2 + (lat - radar.position.lat)**2)
                    if distance > 0:
                        # 转换为度数距离
                        distance_km = distance * 111.32  # 近似转换
                        signal = radar.radar_params.power / (distance_km**2)
                        total_signal += signal
                
                # 归一化信号强度
                if total_signal > 0:
                    heat_data.append([lat, lon, min(total_signal, 100)])  # 限制最大值
        
        if heat_data:
            # 创建热力图
            plugins.HeatMap(
                heat_data,
                min_opacity=0.3,
                max_val=100,
                radius=20,
                blur=15,
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 1: 'red'}
            ).add_to(m)
    
    def create_ew_situation_map(self, 
                               radars: List[Radar], 
                               jammers: List[Jammer], 
                               targets: Optional[List[Target]] = None,
                               show_coverage: bool = True,
                               show_sectors: bool = True,
                               show_heatmap: bool = False,
                               tile_style: str = "标准地图") -> folium.Map:
        """
        创建电子战态势地图
        
        参数:
            radars: 雷达列表
            jammers: 干扰机列表
            targets: 目标列表，可选
            show_coverage: 是否显示雷达覆盖范围
            show_sectors: 是否显示干扰扇区
            show_heatmap: 是否显示信号热力图
            tile_style: 地图瓦片样式
            
        返回:
            Folium地图对象
        """
        try:
            # 计算地图中心点
            all_lats = []
            all_lons = []
            
            for radar in radars:
                all_lats.append(radar.position.lat)
                all_lons.append(radar.position.lon)
            
            for jammer in jammers:
                all_lats.append(jammer.position.lat)
                all_lons.append(jammer.position.lon)
            
            if targets:
                for target in targets:
                    all_lats.append(target.position.lat)
                    all_lons.append(target.position.lon)
            
            if all_lats and all_lons:
                center_lat = np.mean(all_lats)
                center_lon = np.mean(all_lons)
            else:
                center_lat, center_lon = self.center_lat, self.center_lon
            
            # 创建基础地图
            m = folium.Map(
                location=[center_lat, center_lon], # type: ignore
                zoom_start=8,
                tiles=self.tiles_options.get(tile_style, "OpenStreetMap"),
                attr='Map data © OpenStreetMap contributors',
                control_scale=True
            )
            
            # 添加全屏控件
            plugins.Fullscreen().add_to(m)
            
            # 添加雷达
            for radar in radars:
                self.add_radar_to_map(radar, m, show_coverage)
            
            # 添加干扰机
            for jammer in jammers:
                self.add_jammer_to_map(jammer, m, show_sectors)
            
            # 添加目标
            if targets:
                for target in targets:
                    self.add_target_to_map(target, m)
            
            # 添加信号热力图
            if show_heatmap and radars:
                self.add_signal_heatmap(radars, m)
            
            # 添加图例
            self.add_legend(m)
            
            # 缓存地图
            self.current_map = m
            
            return m
            
        except Exception as e:
            print(f"创建电子战态势图失败: {e}")
            traceback.print_exc()
            # 返回简单的地图
            return self.create_base_map(tile_style)
    
    def add_legend(self, m: folium.Map) -> None:
        """
        添加图例
        
        参数:
            m: Folium地图
        """
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 150px; height: 150px; 
                    border:2px solid grey; z-index:9999; font-size:14px;
                    background-color:white; opacity:0.9; padding: 10px;
                    border-radius: 5px;">
        <b style="color: black;">图例</b><br>
        <i class="fa fa-rss fa-lg" style="color:blue"></i> <span style="color: black;">雷达</span><br>
        <i class="fa fa-signal fa-lg" style="color:red"></i> <span style="color: black;">干扰机</span><br>
        <i class="fa fa-fighter-jet fa-lg" style="color:green"></i> <span style="color: black;">目标</span><br>
        <div style="width:20px; height:20px; background-color:blue; opacity:0.2; display:inline-block;"></div> <span style="color: black;">雷达覆盖</span><br>
        <div style="width:20px; height:20px; background-color:red; opacity:0.3; display:inline-block;"></div> <span style="color: black;">干扰扇区</span><br>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(legend_html)) # type: ignore
    
    def save_to_html(self, m: folium.Map, filename: str = "ew_visualization.html") -> str:
        """
        保存地图为HTML文件
        
        参数:
            m: Folium地图对象
            filename: 文件名
            
        返回:
            保存的文件路径
        """
        try:
            filepath = self.output_dir / filename
            
            # 保存地图
            m.save(str(filepath))
            
            print(f"✓ 可视化结果已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"保存HTML文件失败: {e}")
            return ""
    
    def get_map_html(self, m: folium.Map) -> str:
        """
        获取地图的HTML内容
        
        参数:
            m: Folium地图对象
            
        返回:
            HTML内容字符串
        """
        if m is None:
            return ""
        
        return m._repr_html_()
    
    def create_alignment_analysis(self, radar: Radar, jammer: Jammer) -> Tuple[folium.Map, str]:
        """
        创建干扰机对准分析
        
        参数:
            radar: 雷达对象
            jammer: 干扰机对象
            
        返回:
            (地图对象, 分析信息)
        """
        try:
            # 创建地图
            center_lat = (radar.position.lat + jammer.position.lat) / 2
            center_lon = (radar.position.lon + jammer.position.lon) / 2
            
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=9,
                tiles=self.tiles_options["标准地图"]
            )
            
            # 添加雷达
            self.add_radar_to_map(radar, m, show_coverage=True)
            
            # 添加干扰机
            self.add_jammer_to_map(jammer, m, show_sector=True)
            
            # 添加连线
            line_points = [
                [jammer.position.lat, jammer.position.lon],
                [radar.position.lat, radar.position.lon]
            ]
            
            folium.PolyLine(
                line_points,
                color='red',
                weight=2,
                opacity=0.7,
                dash_array='5, 5',
                popup='干扰机-雷达连线'
            ).add_to(m)
            
            # 计算分析信息
            distance = self._calculate_distance(
                jammer.position.lat, jammer.position.lon,
                radar.position.lat, radar.position.lon
            )
            
            # 计算方位角
            bearing = self._calculate_bearing(
                jammer.position.lat, jammer.position.lon,
                radar.position.lat, radar.position.lon
            )
            
            analysis_info = f"""
            **干扰机对准分析:**
            > 距离: {distance:.1f} 公里
            > 方位角: {bearing:.1f} 度
            > 雷达频率: {radar.radar_params.frequency} GHz
            > 干扰机功率: {jammer.jammer_params.power} W
            """
            
            # 添加分析信息弹窗
            info_html = f"""
            <div style="font-family: Arial; min-width: 250px;">
                <h4>对准分析结果</h4>
                {analysis_info}
            </div>
            """
            
            folium.Marker(
                location=[center_lat, center_lon],
                icon=folium.DivIcon(html='<div style="color: black; font-weight: bold;">分析点</div>'),
                popup=folium.Popup(info_html, max_width=300)
            ).add_to(m)
            
            return m, analysis_info
            
        except Exception as e:
            print(f"创建对准分析失败: {e}")
            traceback.print_exc()
            return self.create_base_map(), "分析失败"
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（公里）"""
        # 使用Haversine公式
        R = 6371  # 地球半径，公里
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算方位角（度）"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.degrees(math.atan2(x, y))
        bearing = (bearing + 360) % 360  # 归一化到0-360度
        
        return bearing


# 工具函数
def create_visualization(radars: List[Radar],
                         jammers: List[Jammer],
                         targets: Optional[List[Target]] = None,
                         output_file: Optional[str] = None,
                         show: bool = True) -> str:
    """
    快速创建电子战可视化
    
    参数:
        radars: 雷达列表
        jammers: 干扰机列表
        targets: 目标列表，可选
        output_file: 输出文件名，可选
        show: 是否显示可视化结果
        
    返回:
        保存的文件路径
    """
    # 创建可视化器
    visualizer = EWVisualizer()
    
    # 创建态势地图
    situation_map = visualizer.create_ew_situation_map(radars, jammers, targets)
    
    # 保存结果
    if output_file:
        if output_file.endswith('.html'):
            filepath = visualizer.save_to_html(situation_map, output_file)
        else:
            # 默认保存为HTML
            filepath = visualizer.save_to_html(situation_map, f"{output_file}.html")
    else:
        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = visualizer.save_to_html(situation_map, f"ew_situation_{timestamp}.html")
    
    return filepath