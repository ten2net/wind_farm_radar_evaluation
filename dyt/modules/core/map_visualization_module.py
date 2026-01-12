# map_visualization_module.py
import folium
from folium import plugins
from streamlit_folium import st_folium
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from core_module import *

class AdvancedMapVisualizer:
    """高级地图可视化类"""
    def __init__(self):
        self.map = None
        self.trajectory_layer = None
        self.range_rings_layer = None
        
    def create_battlefield_map(self, battlefield, guidance_system, 
                             show_trajectory=True, show_range_rings=True,
                             show_terrain=True, show_weather=True):
        """创建战场态势地图"""
        # 计算地图中心点
        center_lat = battlefield.missile_position.lat
        center_lon = battlefield.missile_position.lon
        
        # 如果有目标，以导弹和目标中心为地图中心
        if battlefield.targets:
            target_pos = list(battlefield.targets.values())[0].position
            center_lat = (battlefield.missile_position.lat + target_pos.lat) / 2
            center_lon = (battlefield.missile_position.lon + target_pos.lon) / 2
        
        # 创建地图
        self.map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=9,
            tiles='OpenStreetMap'
        )
        
        # 添加地形图层（如果可用）
        if show_terrain:
            self._add_terrain_layers()
        
        # 添加导弹位置
        self._add_missile_marker(battlefield.missile_position, guidance_system)
        
        # 添加目标和干扰机
        self._add_targets_and_jammers(battlefield)
        
        # 添加探测范围环
        if show_range_rings:
            self._add_range_rings(battlefield.missile_position, guidance_system)
        
        # 添加轨迹
        if show_trajectory and guidance_system.trajectory:
            self._add_trajectory(guidance_system.trajectory, guidance_system.color)
        
        # 添加天气效果
        if show_weather:
            self._add_weather_effects(battlefield.weather_condition, battlefield.missile_position)
        
        # 添加测量工具
        self._add_map_controls()
        
        return self.map
    
    def _add_terrain_layers(self):
        """添加地形图层"""
        # 地形图图层
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='地形图',
            overlay=False
        ).add_to(self.map)
        
        # 卫星图图层
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='卫星图',
            overlay=False
        ).add_to(self.map)
    
    def _add_missile_marker(self, position, guidance_system):
        """添加导弹标记"""
        # 性能颜色映射
        performance = guidance_system.current_performance
        if performance > 0.7:
            color = 'green'
        elif performance > 0.4:
            color = 'orange'
        else:
            color = 'red'
        
        # 自定义图标
        icon_html = f'''
            <div style="font-size: 12px; color: {color};">
                <i class="fa fa-fighter-jet" style="font-size: 24px;"></i><br>
                {guidance_system.name}<br>
                性能: {performance*100:.1f}%
            </div>
        '''
        
        icon = folium.DivIcon(
            html=icon_html,
            icon_size=(100, 40),
            icon_anchor=(50, 20),
        )
        
        folium.Marker(
            [position.lat, position.lon],
            popup=folium.Popup(f"""
                <b>导弹状态</b><br>
                导引头: {guidance_system.name}<br>
                性能: {performance*100:.1f}%<br>
                模式: {getattr(guidance_system, 'current_mode', 'N/A')}<br>
                位置: {position.lat:.4f}, {position.lon:.4f}<br>
                海拔: {position.alt:.0f}米
            """, max_width=300),
            tooltip=f"导弹 - {guidance_system.name}",
            icon=icon
        ).add_to(self.map)
    
    def _add_targets_and_jammers(self, battlefield):
        """添加目标和干扰机标记"""
        # 添加目标
        for target_id, target in battlefield.targets.items():
            folium.Marker(
                [target.position.lat, target.position.lon],
                popup=folium.Popup(f"""
                    <b>目标信息</b><br>
                    类型: {target.target_type.value}<br>
                    辐射功率: {target.emission_power}<br>
                    RCS: {target.rcs}<br>
                    速度: {target.velocity} m/s<br>
                    航向: {target.heading}°
                """, max_width=300),
                tooltip=f"目标 - {target.target_type.value}",
                icon=folium.Icon(color='red', icon='bullseye', prefix='fa')
            ).add_to(self.map)
        
        # 添加干扰机
        for jammer_id, jammer in battlefield.jammers.items():
            folium.Marker(
                [jammer.position.lat, jammer.position.lon],
                popup=folium.Popup(f"""
                    <b>干扰机信息</b><br>
                    类型: {jammer.jamming_type.value}<br>
                    功率: {jammer.power}<br>
                    范围: {jammer.range} km<br>
                    保护目标: {jammer.target_id or '无'}
                """, max_width=300),
                tooltip=f"干扰机 - {jammer.jamming_type.value}",
                icon=folium.Icon(color='purple', icon='signal', prefix='fa')
            ).add_to(self.map)
            
            # 添加干扰范围
            folium.Circle(
                [jammer.position.lat, jammer.position.lon],
                radius=jammer.range * 1000,  # 转换为米
                popup=f"干扰有效范围: {jammer.range}km",
                color='purple',
                fill=True,
                fillOpacity=0.1,
                weight=2
            ).add_to(self.map)
    
    def _add_range_rings(self, position, guidance_system):
        """添加探测范围环"""
        ranges = [guidance_system.detection_range * 0.25, 
                 guidance_system.detection_range * 0.5, 
                 guidance_system.detection_range * 0.75,
                 guidance_system.detection_range]
        
        colors = ['green', 'blue', 'orange', 'red']
        
        for i, (range_km, color) in enumerate(zip(ranges, colors)):
            folium.Circle(
                [position.lat, position.lon],
                radius=range_km * 1000,
                popup=f"探测范围: {range_km:.1f}km",
                color=color,
                fill=False,
                weight=2,
                opacity=0.7
            ).add_to(self.map)
            
            # 添加范围标签
            folium.Marker(
                [position.lat, position.lon],
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 10px; color: {color};">{range_km:.0f}km</div>',
                    icon_size=(50, 20),
                    icon_anchor=(25, 10),
                )
            ).add_to(self.map)
    
    def _add_trajectory(self, trajectory, color):
        """添加导弹轨迹"""
        if len(trajectory) < 2:
            return
            
        points = [[point.position.lat, point.position.lon] for point in trajectory]
        
        # 创建颜色渐变基于性能
        performance_values = [point.performance for point in trajectory]
        
        # 添加轨迹线
        folium.PolyLine(
            points,
            popup="导弹飞行轨迹",
            color=color,
            weight=4,
            opacity=0.7
        ).add_to(self.map)
        
        # 添加轨迹点标记
        for i, point in enumerate(trajectory):
            if i % 5 == 0:  # 每5个点标记一个
                # 根据性能设置点颜色
                if point.performance > 0.7:
                    point_color = 'green'
                elif point.performance > 0.4:
                    point_color = 'orange'
                else:
                    point_color = 'red'
                    
                folium.CircleMarker(
                    [point.position.lat, point.position.lon],
                    radius=3,
                    popup=f"时间: {point.timestamp.strftime('%H:%M:%S')}<br>性能: {point.performance*100:.1f}%",
                    color=point_color,
                    fill=True,
                    fillOpacity=0.7
                ).add_to(self.map)
    
    def _add_weather_effects(self, weather_condition, center_position):
        """添加天气效果"""
        if weather_condition == 'rain':
            # 模拟降雨区域
            folium.Rectangle(
                bounds=[[center_position.lat-0.5, center_position.lon-0.5],
                       [center_position.lat+0.5, center_position.lon+0.5]],
                popup='降雨区域',
                fill=True,
                fillColor='blue',
                fillOpacity=0.1,
                color='blue',
                weight=1
            ).add_to(self.map)
        elif weather_condition == 'fog':
            folium.Rectangle(
                bounds=[[center_position.lat-0.5, center_position.lon-0.5],
                       [center_position.lat+0.5, center_position.lon+0.5]],
                popup='雾区',
                fill=True,
                fillColor='gray',
                fillOpacity=0.1,
                color='gray',
                weight=1
            ).add_to(self.map)
        elif weather_condition == 'storm':
            folium.Rectangle(
                bounds=[[center_position.lat-1, center_position.lon-1],
                       [center_position.lat+1, center_position.lon+1]],
                popup='风暴区域',
                fill=True,
                fillColor='darkred',
                fillOpacity=0.1,
                color='darkred',
                weight=2
            ).add_to(self.map)
    
    def _add_map_controls(self):
        """添加地图控件"""
        # 全屏控件
        plugins.Fullscreen().add_to(self.map)
        
        # 测量工具
        plugins.MeasureControl(
            position='topleft',
            primary_length_unit='kilometers',
            secondary_length_unit='miles'
        ).add_to(self.map)
        
        # 图层控制
        folium.LayerControl().add_to(self.map)

class PerformanceVisualizer:
    """性能可视化类"""
    
    @staticmethod
    def create_performance_gauge(performance, guidance_system):
        """创建性能仪表盘"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=performance * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"{guidance_system.name}<br>综合性能评分"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': guidance_system.color},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': performance * 100
                }
            }
        ))
        fig.update_layout(height=300)
        return fig
    
    @staticmethod
    def create_performance_timeline(trajectory):
        """创建性能时间线图"""
        if not trajectory:
            return go.Figure()
            
        times = [point.timestamp for point in trajectory]
        performances = [point.performance * 100 for point in trajectory]
        distances = [point.distance_to_target for point in trajectory]
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 性能曲线
        fig.add_trace(
            go.Scatter(x=times, y=performances, name="性能评分", line=dict(color='blue', width=3)),
            secondary_y=False,
        )
        
        # 距离曲线
        fig.add_trace(
            go.Scatter(x=times, y=distances, name="目标距离", line=dict(color='red', width=2)),
            secondary_y=True,
        )
        
        fig.update_layout(
            title="性能时间线",
            xaxis_title="时间",
            height=300
        )
        
        fig.update_yaxes(title_text="性能评分 (%)", secondary_y=False)
        fig.update_yaxes(title_text="目标距离 (km)", secondary_y=True)
        
        return fig
    
    @staticmethod
    def create_parameter_radar(guidance_systems, current_system_name):
        """创建参数雷达图"""
        categories = ['探测距离', '抗干扰', '隐蔽性', '精度']
        
        fig = go.Figure()
        
        for system in guidance_systems.values():
            # 归一化参数值 (0-100)
            values = [
                system.detection_range / 120 * 100,  # 最大探测距离120km
                system.jamming_resistance * 100,
                system.stealth_level * 100,
                getattr(system, 'accuracy', 0.5) * 100
            ]
            
            # 当前系统高亮显示
            line_width = 3 if system.name == current_system_name else 1
            opacity = 1.0 if system.name == current_system_name else 0.6
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # 闭合图形
                theta=categories + [categories[0]],
                fill='toself',
                name=system.name,
                line=dict(color=system.color, width=line_width),
                opacity=opacity
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=True,
            title="导引头性能对比雷达图",
            height=400
        )
        
        return fig

class RealTimeDashboard:
    """实时仪表盘类"""
    
    def __init__(self):
        self.metrics = {}
        
    def update_metrics(self, battlefield, guidance_system, simulation_result):
        """更新实时指标"""
        target, distance = battlefield.get_closest_target(battlefield.missile_position)
        
        self.metrics = {
            'performance': simulation_result['performance'] * 100,
            'target_distance': distance,
            'jamming_power': simulation_result['jamming_power'] * 100,
            'terrain_factor': simulation_result['terrain_factor'] * 100,
            'weather_factor': simulation_result['weather_factor'] * 100,
            'target_type': target.target_type.value if target else '无目标',
            'guidance_mode': getattr(guidance_system, 'current_mode', 'N/A'),
            'simulation_time': simulation_result.get('simulation_time', 0)
        }
    
    def display_metrics(self, guidance_system):
        """显示实时指标面板"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("导引头性能", f"{self.metrics['performance']:.1f}%")
            st.metric("目标距离", f"{self.metrics['target_distance']:.1f} km")
            
        with col2:
            st.metric("干扰强度", f"{self.metrics['jamming_power']:.1f}%")
            st.metric("地形影响", f"{self.metrics['terrain_factor']:.1f}%")
            
        with col3:
            st.metric("天气影响", f"{self.metrics['weather_factor']:.1f}%")
            st.metric("目标类型", self.metrics['target_type'])
            
        with col4:
            st.metric("工作模式", self.metrics['guidance_mode'])
            st.metric("仿真时间", f"{self.metrics['simulation_time']:.1f}s")

class MultiTargetVisualizer:
    """多目标可视化类"""
    
    def __init__(self):
        self.target_colors = ['red', 'blue', 'green', 'orange', 'purple']
        
    def create_multi_target_map(self, battlefield, guidance_system):
        """创建多目标战场地图"""
        # 创建基础地图
        map_visualizer = AdvancedMapVisualizer()
        base_map = map_visualizer.create_battlefield_map(
            battlefield, guidance_system, show_trajectory=True
        )
        
        # 添加多目标连线
        missile_pos = battlefield.missile_position
        for i, (target_id, target) in enumerate(battlefield.targets.items()):
            color = self.target_colors[i % len(self.target_colors)]
            
            # 计算距离和性能
            distance = TerrainModel.calculate_distance(missile_pos, target.position)
            jamming_power = battlefield.get_jamming_power(missile_pos)
            performance = guidance_system.calculate_performance(distance, jamming_power)
            
            # 添加目标连线
            folium.PolyLine(
                [[missile_pos.lat, missile_pos.lon], [target.position.lat, target.position.lon]],
                color=color,
                weight=3,
                opacity=0.7,
                popup=f"目标 {target_id}<br>距离: {distance:.1f}km<br>性能: {performance*100:.1f}%"
            ).add_to(base_map)
            
            # 添加距离标签
            mid_lat = (missile_pos.lat + target.position.lat) / 2
            mid_lon = (missile_pos.lon + target.position.lon) / 2
            
            folium.Marker(
                [mid_lat, mid_lon],
                icon=folium.DivIcon(
                    html=f'<div style="color: {color}; font-weight: bold;">{distance:.1f}km</div>',
                    icon_size=(60, 20),
                    icon_anchor=(30, 10),
                )
            ).add_to(base_map)
        
        return base_map
    
    def create_target_priority_chart(self, battlefield, guidance_system):
        """创建目标优先级图表"""
        missile_pos = battlefield.missile_position
        target_data = []
        
        for target_id, target in battlefield.targets.items():
            distance = TerrainModel.calculate_distance(missile_pos, target.position)
            jamming_power = battlefield.get_jamming_power(missile_pos)
            performance = guidance_system.calculate_performance(distance, jamming_power)
            
            # 计算优先级得分（简化模型）
            priority_score = (target.emission_power * 0.4 + 
                            (1 - distance/200) * 0.3 + 
                            performance * 0.3)
            
            target_data.append({
                'target_id': target_id,
                'target_type': target.target_type.value,
                'distance': distance,
                'performance': performance * 100,
                'priority_score': priority_score * 100,
                'emission_power': target.emission_power * 100
            })
        
        df = pd.DataFrame(target_data)
        if df.empty:
            return go.Figure()
            
        # 按优先级排序
        df = df.sort_values('priority_score', ascending=False)
        
        # 创建水平条形图
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df['target_id'],
            x=df['priority_score'],
            orientation='h',
            marker_color='skyblue',
            text=df['priority_score'].round(1),
            textposition='auto',
            hovertemplate=(
                "目标: %{y}<br>" +
                "优先级: %{x:.1f}%<br>" +
                "距离: %{customdata[0]:.1f}km<br>" +
                "性能: %{customdata[1]:.1f}%<br>" +
                "辐射功率: %{customdata[2]:.1f}%"
            ),
            customdata=np.stack((df['distance'], df['performance'], df['emission_power']), axis=-1)
        ))
        
        fig.update_layout(
            title="目标攻击优先级",
            xaxis_title="优先级得分 (%)",
            yaxis_title="目标ID",
            height=400
        )
        
        return fig

class TerrainAnalysisVisualizer:
    """地形分析可视化类"""
    
    def create_terrain_analysis_map(self, battlefield):
        """创建地形分析地图"""
        # 创建高程地图
        center_lat = battlefield.missile_position.lat
        center_lon = battlefield.missile_position.lon
        
        # 生成网格点
        lats = np.linspace(center_lat - 0.5, center_lat + 0.5, 20)
        lons = np.linspace(center_lon - 0.5, center_lon + 0.5, 20)
        
        # 计算高程数据
        elevation_data = []
        for lat in lats:
            row = []
            for lon in lons:
                alt = battlefield.terrain_model.get_elevation(lat, lon)
                row.append(alt)
            elevation_data.append(row)
        
        # 创建等高线地图
        fig = go.Figure(data=
            go.Contour(
                z=elevation_data,
                x=lons,
                y=lats,
                colorscale='Viridis',
                contours=dict(
                    coloring='lines',
                ),
                line=dict(width=2),
            )
        )
        
        # 添加导弹位置标记
        fig.add_trace(go.Scatter(
            x=[battlefield.missile_position.lon],
            y=[battlefield.missile_position.lat],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='导弹位置'
        ))
        
        # 添加目标位置标记
        for target in battlefield.targets.values():
            fig.add_trace(go.Scatter(
                x=[target.position.lon],
                y=[target.position.lat],
                mode='markers',
                marker=dict(size=12, color='blue'),
                name=f'目标 ({target.target_type.value})'
            ))
        
        fig.update_layout(
            title="战场地形分析",
            xaxis_title="经度",
            yaxis_title="纬度",
            height=500
        )
        
        return fig
    
    def create_line_of_sight_analysis(self, battlefield, guidance_system):
        """创建视线分析图表"""
        missile_pos = battlefield.missile_position
        target_data = []
        
        for target_id, target in battlefield.targets.items():
            distance = TerrainModel.calculate_distance(missile_pos, target.position)
            terrain_factor = battlefield.get_terrain_factor(missile_pos, target.position)
            
            # 视线分析（简化模型）
            elevation_diff = abs(missile_pos.alt - target.position.alt)
            los_obstruction = max(0, 1 - terrain_factor)  # 视线受阻程度
            
            target_data.append({
                'target_id': target_id,
                'distance': distance,
                'elevation_diff': elevation_diff,
                'terrain_factor': terrain_factor * 100,
                'los_quality': (1 - los_obstruction) * 100,  # 视线质量
                'effective_range': guidance_system.detection_range * terrain_factor
            })
        
        df = pd.DataFrame(target_data)
        if df.empty:
            return go.Figure()
        
        # 创建散点图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['distance'],
            y=df['los_quality'],
            mode='markers+text',
            text=df['target_id'],
            textposition='top center',
            marker=dict(
                size=df['terrain_factor'] / 10,
                color=df['los_quality'],
                colorscale='Viridis',
                showscale=True
            ),
            hovertemplate=(
                "目标: %{text}<br>" +
                "距离: %{x:.1f}km<br>" +
                "视线质量: %{y:.1f}%<br>" +
                "地形影响: %{marker.size:.1f}%"
            )
        ))
        
        fig.update_layout(
            title="目标视线质量分析",
            xaxis_title="距离 (km)",
            yaxis_title="视线质量 (%)",
            height=400
        )
        
        return fig

class WeatherImpactVisualizer:
    """天气影响可视化类"""
    
    def create_weather_impact_chart(self, battlefield, guidance_system):
        """创建天气影响分析图表"""
        weather_conditions = ['clear', 'cloudy', 'rain', 'fog', 'storm']
        distances = np.linspace(10, 200, 20)
        
        data = []
        
        for weather in weather_conditions:
            for distance in distances:
                weather_factor = battlefield.weather_model.get_weather_factor(weather, distance)
                performance = guidance_system.calculate_performance(
                    distance, 0.3, 1.0, weather_factor  # 固定干扰和地形
                )
                
                data.append({
                    'weather': weather,
                    'distance': distance,
                    'weather_factor': weather_factor * 100,
                    'performance': performance * 100
                })
        
        df = pd.DataFrame(data)
        
        # 创建多线图
        fig = go.Figure()
        
        for weather in weather_conditions:
            weather_df = df[df['weather'] == weather]
            fig.add_trace(go.Scatter(
                x=weather_df['distance'],
                y=weather_df['performance'],
                name=weather,
                mode='lines',
                hovertemplate=(
                    "天气: %{customdata}<br>" +
                    "距离: %{x:.1f}km<br>" +
                    "性能: %{y:.1f}%<br>" +
                    "天气影响: %{text:.1f}%"
                ),
                text=weather_df['weather_factor'],
                customdata=[weather] * len(weather_df)
            ))
        
        fig.update_layout(
            title="不同天气条件下的性能影响",
            xaxis_title="目标距离 (km)",
            yaxis_title="导引头性能 (%)",
            height=400
        )
        
        return fig

# 导出可视化工具集
class VisualizationToolkit:
    """可视化工具集"""
    
    def __init__(self):
        self.map_visualizer = AdvancedMapVisualizer()
        self.performance_visualizer = PerformanceVisualizer()
        self.realtime_dashboard = RealTimeDashboard()
        self.multitarget_visualizer = MultiTargetVisualizer()
        self.terrain_analyzer = TerrainAnalysisVisualizer()
        self.weather_visualizer = WeatherImpactVisualizer()
    
    def get_all_visualizations(self, battlefield, guidance_system, simulation_result):
        """获取所有可视化组件"""
        visualizations = {}
        
        # 基础地图
        visualizations['battlefield_map'] = self.map_visualizer.create_battlefield_map(
            battlefield, guidance_system
        )
        
        # 性能图表
        visualizations['performance_gauge'] = self.performance_visualizer.create_performance_gauge(
            simulation_result['performance'], guidance_system
        )
        
        # 时间线图表
        visualizations['performance_timeline'] = self.performance_visualizer.create_performance_timeline(
            guidance_system.trajectory
        )
        
        # 多目标分析（如果有多目标）
        if len(battlefield.targets) > 1:
            visualizations['multitarget_map'] = self.multitarget_visualizer.create_multi_target_map(
                battlefield, guidance_system
            )
            visualizations['target_priority'] = self.multitarget_visualizer.create_target_priority_chart(
                battlefield, guidance_system
            )
        
        # 地形分析
        visualizations['terrain_analysis'] = self.terrain_analyzer.create_terrain_analysis_map(
            battlefield
        )
        visualizations['los_analysis'] = self.terrain_analyzer.create_line_of_sight_analysis(
            battlefield, guidance_system
        )
        
        # 天气影响
        visualizations['weather_impact'] = self.weather_visualizer.create_weather_impact_chart(
            battlefield, guidance_system
        )
        
        return visualizations

# 工具函数
def create_interactive_legend():
    """创建交互式图例"""
    legend_html = """
    <div style="
        position: fixed; 
        top: 10px; 
        right: 10px; 
        background: white; 
        border: 2px solid grey; 
        z-index: 9999; 
        padding: 10px;
        border-radius: 5px;
    ">
        <h4>图例</h4>
        <p>🛩️ 导弹位置</p>
        <p>🎯 目标位置</p>
        <p>📡 干扰源</p>
        <p>📈 性能良好 (>70%)</p>
        <p>⚠️ 性能中等 (40-70%)</p>
        <p>❌ 性能差 (<40%)</p>
    </div>
    """
    return legend_html

def add_custom_css():
    """添加自定义CSS样式"""
    st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin: 5px;
    }
    .performance-good {
        color: green;
        font-weight: bold;
    }
    .performance-warning {
        color: orange;
        font-weight: bold;
    }
    .performance-danger {
        color: red;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 测试函数
def test_visualization_module():
    """测试可视化模块"""
    # 创建测试战场
    battlefield = Battlefield()
    
    # 添加测试目标
    target = Target(
        target_id="test_target",
        target_type=TargetType.AWACS,
        position=Position(36.0, 117.0, 8000),
        emission_power=0.9,
        rcs=50.0
    )
    battlefield.add_target(target)
    
    # 创建导引头
    guidance_system = CompositeSeeker()
    
    # 测试可视化工具
    toolkit = VisualizationToolkit()
    visualizations = toolkit.get_all_visualizations(
        battlefield, guidance_system, {'performance': 0.8}
    )
    
    print("可视化模块测试完成")

if __name__ == "__main__":
    test_visualization_module()