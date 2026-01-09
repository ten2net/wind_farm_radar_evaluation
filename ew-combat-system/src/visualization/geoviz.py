"""
电子战对抗仿真地理可视化模块
基于GeoViews的地理可视化工具
"""
import traceback
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import cartopy.crs as ccrs
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as mcm
from matplotlib.colors import Normalize

# 导入GeoViews相关库
try:
    import geoviews as gv
    import geoviews.feature as gf
    gv.extension('bokeh')
    print("✓ 成功加载GeoViews扩展")
except ImportError as e:
    print(f"✗ 加载GeoViews失败: {e}")
    raise ImportError("请先安装GeoViews: pip install geoviews")

try:
    import holoviews as hv
    hv.extension('bokeh')
except ImportError:
    hv = None

from ..core.entities import Radar, Jammer, Target, Position

class EWVisualizer:
    """基于GeoViews的电子战可视化器"""
    
    def __init__(self, projection: str = 'PlateCarree'):
        """
        初始化可视化器
        
        参数:
            projection: 地图投影方式 ('PlateCarree', 'Mercator', 'Robinson'等)
        """
        # 设置投影
        self.projection_mapping = {
            'PlateCarree': ccrs.PlateCarree(),
            'Mercator': ccrs.Mercator(),
            'Robinson': ccrs.Robinson(),
            'Orthographic': ccrs.Orthographic(central_longitude=116.4, central_latitude=39.9),
        }
        self.crs = self.projection_mapping.get(projection, ccrs.PlateCarree())
        
        # 默认样式
        self.styles = {
            'radar': {
                'color': 'blue',
                'size': 12,
                'marker': 'triangle',
                'line_color': 'darkblue',
                'line_width': 1.5
            },
            'jammer': {
                'color': 'red',
                'size': 10,
                'marker': 'square',
                'line_color': 'darkred',
                'line_width': 1.5
            },
            'target': {
                'color': 'green',
                'size': 8,
                'marker': 'circle',
                'line_color': 'darkgreen',
                'line_width': 1.5
            },
            'coverage': {
                'fill_color': 'blue',
                'fill_alpha': 0.2,
                'line_color': 'blue',
                'line_width': 1
            },
            'jamming_sector': {
                'fill_color': 'red',
                'fill_alpha': 0.3,
                'line_color': 'red',
                'line_width': 1
            }
        }
        
        # 创建输出目录
        self.output_dir = Path("static/visualizations")
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def create_basemap(self, bbox: Optional[Tuple[float, float, float, float]] = None) :
        """
        创建基础地图
        
        参数:
            bbox: 地图边界框 (min_lon, min_lat, max_lon, max_lat)，可选
            
        返回:
            GeoViews基础地图
        """
        try:
            # 创建海岸线图层
            coastline = gf.coastline.opts(
                line_color='#4682B4',
                line_width=1.2,
                alpha=0.8
            )
            
            # 创建国界线图层
            borders = gf.borders.opts(
                line_color='gray',
                line_width=0.8,
                alpha=0.6
            )
            
            # 创建海洋填充
            ocean = gf.ocean.opts(
                fill_color='#E6F3F7',
                alpha=0.6
            )
            
            # 创建陆地填充
            land = gf.land.opts(
                fill_color='#F5F5DC',
                alpha=0.5
            )
            
            # 组合基础地图
            basemap = ocean * land * coastline * borders
            
            # 如果指定了边界框，设置地图范围
            if bbox:
                min_lon, min_lat, max_lon, max_lat = bbox
                basemap = basemap.opts(xlim=(min_lon, max_lon), ylim=(min_lat, max_lat))
            
            return basemap
            
        except Exception as e:
            print(f"创建基础地图失败: {e}")
            return gf.coastline.opts(line_color='blue', line_width=1)
    
    def plot_radar_points(self, radars: List[Radar]) :
        """
        绘制雷达位置点
        
        参数:
            radars: 雷达列表
            
        返回:
            雷达点图层
        """
        try:
            # 准备雷达数据
            radar_data = []
            for radar in radars:
                radar_data.append({
                    'Lon': radar.position.lon,
                    'Lat': radar.position.lat,
                    'Name': radar.name,
                    'Frequency': radar.radar_params.frequency,
                    'Power': radar.radar_params.power,
                    'Gain': radar.radar_params.gain,
                    'Type': 'Radar'
                })
            
            df = pd.DataFrame(radar_data)
            
            # 创建点图层
            points = gv.Points(
                df, 
                kdims=['Lon', 'Lat'],
                vdims=['Name', 'Frequency', 'Power', 'Gain', 'Type']
            ).opts(
                color=self.styles['radar']['color'],
                size=self.styles['radar']['size'],
                marker=self.styles['radar']['marker'],
                line_color=self.styles['radar']['line_color'],
                line_width=self.styles['radar']['line_width'],
                tools=['hover'],
                cmap='Blues',
                title='雷达部署',
                xlabel='经度',
                ylabel='纬度',
                width=800,
                height=600
            )
            
            return points
            
        except Exception as e:
            print(f"绘制雷达点失败: {e}")
            return gv.Points([])
    
    def plot_radar_coverage(self, radars: List[Radar]):
        """
        绘制雷达覆盖范围
        
        参数:
            radars: 雷达列表
            
        返回:
            雷达覆盖范围图层
        """
        try:
            polygons = []
            for radar in radars:
                try:
                    coverage = radar.calculate_coverage()
                    if coverage is not None and len(coverage) > 0:
                        # 将覆盖范围转换为多边形
                        poly_data = pd.DataFrame({
                            'Lon': [p[0] for p in coverage],
                            'Lat': [p[1] for p in coverage],
                            'Name': radar.name
                        })
                        polygons.append(gv.Polygons([poly_data], vdims=['Name']))
                except Exception as e:
                    print(f"计算雷达{radar.name}覆盖范围失败: {e}")
                    continue
            
            if polygons:
                coverage_layer = polygons[0]
                for poly in polygons[1:]:
                    coverage_layer *= poly
                
                return coverage_layer.opts(
                    fill_color=self.styles['coverage']['fill_color'],
                    fill_alpha=self.styles['coverage']['fill_alpha'],
                    line_color=self.styles['coverage']['line_color'],
                    line_width=self.styles['coverage']['line_width']
                )
            else:
                return gv.Polygons([])
                
        except Exception as e:
            print(f"绘制雷达覆盖范围失败: {e}")
            return gv.Polygons([])
    
    def plot_jammer_points(self, jammers: List[Jammer]) :
        """
        绘制干扰机位置点
        
        参数:
            jammers: 干扰机列表
            
        返回:
            干扰机点图层
        """
        try:
            # 准备干扰机数据
            jammer_data = []
            for jammer in jammers:
                jammer_data.append({
                    'Lon': jammer.position.lon,
                    'Lat': jammer.position.lat,
                    'Name': jammer.name,
                    'Power': jammer.jammer_params.power,
                    'Gain': jammer.jammer_params.gain,
                    'Type': 'Jammer'
                })
            
            df = pd.DataFrame(jammer_data)
            
            # 创建点图层
            points = gv.Points(
                df, 
                kdims=['Lon', 'Lat'],
                vdims=['Name', 'Power', 'Gain', 'Type']
            ).opts(
                color=self.styles['jammer']['color'],
                size=self.styles['jammer']['size'],
                marker=self.styles['jammer']['marker'],
                line_color=self.styles['jammer']['line_color'],
                line_width=self.styles['jammer']['line_width'],
                tools=['hover'],
                cmap='Reds',
                title='干扰机部署'
            )
            
            return points
            
        except Exception as e:
            print(f"绘制干扰机点失败: {e}")
            return gv.Points([])
    
    def plot_jamming_sectors(self, jammers: List[Jammer]):
        """
        绘制干扰扇区
        
        参数:
            jammers: 干扰机列表
            
        返回:
            干扰扇区图层
        """
        try:
            polygons = []
            for jammer in jammers:
                try:
                    sector = jammer.calculate_jamming_sector(azimuth=45, width=60, range_km=100)
                    if sector is not None and len(sector) > 0:
                        # 将扇区转换为多边形
                        poly_data = pd.DataFrame({
                            'Lon': [p[0] for p in sector],
                            'Lat': [p[1] for p in sector],
                            'Name': jammer.name
                        })
                        polygons.append(gv.Polygons([poly_data], vdims=['Name']))
                except Exception as e:
                    print(f"计算干扰机{jammer.name}扇区失败: {e}")
                    continue
            
            if polygons:
                sector_layer = polygons[0]
                for poly in polygons[1:]:
                    sector_layer *= poly
                
                return sector_layer.opts(
                    fill_color=self.styles['jamming_sector']['fill_color'],
                    fill_alpha=self.styles['jamming_sector']['fill_alpha'],
                    line_color=self.styles['jamming_sector']['line_color'],
                    line_width=self.styles['jamming_sector']['line_width']
                )
            else:
                return gv.Polygons([])
                
        except Exception as e:
            print(f"绘制干扰扇区失败: {e}")
            return gv.Polygons([])
    
    def plot_target_points(self, targets: List[Target]) :
        """
        绘制目标位置点
        
        参数:
            targets: 目标列表
            
        返回:
            目标点图层
        """
        try:
            if not targets:
                return gv.Points([])
            
            # 准备目标数据
            target_data = []
            for target in targets:
                target_data.append({
                    'Lon': target.position.lon,
                    'Lat': target.position.lat,
                    'Name': target.name,
                    'RCS': target.rcs,
                    'Speed': target.speed,
                    'Type': 'Target'
                })
            
            df = pd.DataFrame(target_data)
            
            # 创建点图层
            points = gv.Points(
                df, 
                kdims=['Lon', 'Lat'],
                vdims=['Name', 'RCS', 'Speed', 'Type']
            ).opts(
                color=self.styles['target']['color'],
                size=self.styles['target']['size'],
                marker=self.styles['target']['marker'],
                line_color=self.styles['target']['line_color'],
                line_width=self.styles['target']['line_width'],
                tools=['hover'],
                cmap='Greens',
                title='目标分布'
            )
            
            return points
            
        except Exception as e:
            print(f"绘制目标点失败: {e}")
            return gv.Points([])
    
    def create_ew_situation_map(self, 
                              radars: List[Radar], 
                              jammers: List[Jammer], 
                              targets: Optional[List[Target]] = None,
                              bbox: Optional[Tuple[float, float, float, float]] = None) :
        """
        创建电子战态势地图
        
        参数:
            radars: 雷达列表
            jammers: 干扰机列表
            targets: 目标列表，可选
            bbox: 地图边界框，可选
            
        返回:
            电子战态势地图
        """
        try:
            # 创建基础地图
            basemap = self.create_basemap(bbox)
            
            # 创建雷达相关图层
            radar_points = self.plot_radar_points(radars)
            radar_coverage = self.plot_radar_coverage(radars)
            
            # 创建干扰机相关图层
            jammer_points = self.plot_jammer_points(jammers)
            jammer_sectors = self.plot_jamming_sectors(jammers)
            
            # 创建目标图层
            target_points = self.plot_target_points(targets or [])
            
            # 组合所有图层
            situation_map = (
                basemap * 
                radar_coverage * 
                jammer_sectors * 
                radar_points * 
                jammer_points * 
                target_points
            )
            
            # 设置地图属性
            situation_map = situation_map.opts(
                title='电子战对抗态势图',
                xlabel='经度',
                ylabel='纬度',
                width=1000,
                height=700,
                show_grid=True,
                tools=['hover', 'pan', 'wheel_zoom', 'reset'],
                legend_position='top_right'
            )
            
            return situation_map
            
        except Exception as e:
            print(f"创建电子战态势图失败: {e}")
            traceback.print_exc()
            return self.create_basemap(bbox)
    
    def create_signal_strength_heatmap(self, 
                                     radars: List[Radar],
                                     grid_resolution: float = 0.1) :
        """
        创建信号强度热力图
        
        参数:
            radars: 雷达列表
            grid_resolution: 网格分辨率（度）
            
        返回:
            信号强度热力图
        """
        try:
            if not radars:
                return self.create_basemap()
            
            # 计算网格边界
            lons = [r.position.lon for r in radars]
            lats = [r.position.lat for r in radars]
            
            min_lon, max_lon = min(lons) - 2, max(lons) + 2
            min_lat, max_lat = min(lats) - 2, max(lats) + 2
            
            # 创建网格
            lon_grid = np.arange(min_lon, max_lon, grid_resolution)
            lat_grid = np.arange(min_lat, max_lat, grid_resolution)
            
            # 计算每个网格点的信号强度
            signal_strength = np.zeros((len(lat_grid), len(lon_grid)))
            
            for i, lat in enumerate(lat_grid):
                for j, lon in enumerate(lon_grid):
                    total_signal = 0
                    for radar in radars:
                        # 简化的信号强度计算（距离衰减）
                        distance = np.sqrt((lon - radar.position.lon)**2 + (lat - radar.position.lat)**2)
                        if distance > 0:
                            signal = radar.radar_params.power / (distance**2)
                            total_signal += signal
                    signal_strength[i, j] = total_signal
            
            # 创建QuadMesh
            xx, yy = np.meshgrid(lon_grid, lat_grid)
            
            # 归一化信号强度用于颜色映射
            if signal_strength.max() > signal_strength.min():
                normalized_strength = (signal_strength - signal_strength.min()) / (signal_strength.max() - signal_strength.min())
            else:
                normalized_strength = signal_strength
            
            # 创建QuadMesh
            heatmap = gv.QuadMesh(
                (xx, yy, normalized_strength),
                kdims=['x', 'y'],
                vdims=['Signal']
            ).opts(
                cmap='viridis',
                colorbar=True,
                colorbar_position='right',
                alpha=0.6,
                title='信号强度热力图',
                xlabel='经度',
                ylabel='纬度',
                width=800,
                height=600
            )
            
            # 添加雷达点
            radar_points = self.plot_radar_points(radars)
            
            # 组合热力图和雷达点
            complete_map = (self.create_basemap() * heatmap * radar_points)
            
            return complete_map
            
        except Exception as e:
            print(f"创建信号强度热力图失败: {e}")
            traceback.print_exc()
            return self.create_basemap()
    
    def create_3d_terrain_view(self, 
                              radars: List[Radar],
                              jammers: List[Jammer],
                              elevation_data: Optional[np.ndarray] = None) :
        """
        创建3D地形视图
        
        参数:
            radars: 雷达列表
            jammers: 干扰机列表
            elevation_data: 高程数据，可选
            
        返回:
            3D地形视图
        """
        try:
            if elevation_data is None:
                # 如果没有高程数据，创建一个简单的地形
                x = np.linspace(-2, 2, 50)
                y = np.linspace(-2, 2, 50)
                X, Y = np.meshgrid(x, y)
                elevation_data = np.sin(X**2 + Y**2)
            
            # 创建3D曲面
            terrain = gv.Surface(elevation_data).opts(
                cmap='terrain',
                colorbar=True,
                title='3D地形视图',
                width=800,
                height=600
            )
            
            # 创建雷达点（转换为3D）
            radar_points_3d = []
            for radar in radars:
                # 简化的3D位置映射
                z = 0.1  # 假设雷达在海拔0.1处
                radar_points_3d.append({
                    'x': radar.position.lon,
                    'y': radar.position.lat,
                    'z': z,
                    'Name': radar.name
                })
            
            if radar_points_3d:
                df_radar = pd.DataFrame(radar_points_3d)
                radar_points = gv.Points(
                    df_radar,
                    kdims=['x', 'y', 'z'],
                    vdims=['Name']
                ).opts(
                    color='blue',
                    size=8,
                    marker='triangle'
                )
                terrain = terrain * radar_points
            
            return terrain
            
        except Exception as e:
            print(f"创建3D地形视图失败: {e}")
            traceback.print_exc()
            return gv.Image([])
    
    def create_animation(self,
                        radar_positions: List[List[Tuple[float, float]]],
                        jammer_positions: List[List[Tuple[float, float]]],
                        time_steps: int = 10) -> hv.core.spaces.HoloMap:
        """
        创建动态动画
        
        参数:
            radar_positions: 雷达位置随时间变化的列表
            jammer_positions: 干扰机位置随时间变化的列表
            time_steps: 时间步数
            
        返回:
            动画对象
        """
        try:
            if hv is None:
                raise ImportError("Holoviews不可用，无法创建动画")
            
            # 创建动画帧列表
            frames = []
            
            for t in range(min(time_steps, len(radar_positions), len(jammer_positions))):
                # 准备当前帧的数据
                radar_data = []
                for i, (lon, lat) in enumerate(radar_positions[t]):
                    radar_data.append({
                        'Lon': lon,
                        'Lat': lat,
                        'Time': t,
                        'ID': f'Radar_{i}',
                        'Type': 'Radar'
                    })
                
                jammer_data = []
                for i, (lon, lat) in enumerate(jammer_positions[t]):
                    jammer_data.append({
                        'Lon': lon,
                        'Lat': lat,
                        'Time': t,
                        'ID': f'Jammer_{i}',
                        'Type': 'Jammer'
                    })
                
                # 合并数据
                all_data = radar_data + jammer_data
                if not all_data:
                    continue
                
                df = pd.DataFrame(all_data)
                
                # 创建当前帧
                frame = gv.Points(
                    df,
                    kdims=['Lon', 'Lat'],
                    vdims=['Time', 'ID', 'Type']
                ).opts(
                    color='Type',
                    cmap={'Radar': 'blue', 'Jammer': 'red'},
                    size=10,
                    tools=['hover'],
                    title=f'时间步: {t}'
                )
                
                # 添加到帧列表
                frames.append(frame)
            
            # 创建动画
            if frames:
                animation = hv.HoloMap({i: frame for i, frame in enumerate(frames)})
                return animation.opts(width=800, height=600, show_grid=True)
            else:
                return hv.Curve([])
                
        except Exception as e:
            print(f"创建动画失败: {e}")
            traceback.print_exc()
            return hv.Curve([])
    
    def save_to_html(self, 
                    plot,
                    filename: str = "ew_visualization.html") -> str:
        """
        保存可视化结果为HTML文件
        
        参数:
            plot: 要保存的图表
            filename: 文件名
            
        返回:
            保存的文件路径
        """
        try:
            filepath = self.output_dir / filename
            
            # 使用Bokeh后端保存
            renderer = gv.renderer('bokeh')
            renderer.save(plot, filepath)
            
            print(f"✓ 可视化结果已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"保存HTML文件失败: {e}")
            traceback.print_exc()
            return ""
    
    def save_to_png(self, 
                   plot,
                   filename: str = "ew_visualization.png") -> str:
        """
        保存可视化结果为PNG图片
        
        参数:
            plot: 要保存的图表
            filename: 文件名
            
        返回:
            保存的文件路径
        """
        try:
            filepath = self.output_dir / filename
            
            # 使用Matplotlib后端保存
            try:
                renderer = gv.renderer('matplotlib')
                renderer.save(plot, filepath)
            except:
                # 如果matplotlib后端不可用，尝试使用Bokeh后端截图
                renderer = gv.renderer('bokeh')
                renderer.save(plot, filepath)
            
            print(f"✓ 可视化结果已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"保存PNG文件失败: {e}")
            traceback.print_exc()
            return ""
    
    def display(self, plot) -> None:
        """
        显示可视化结果
        
        参数:
            plot: 要显示的图表
        """
        try:
            # 在Jupyter notebook中显示
            from IPython.display import display
            display(plot)
        except ImportError:
            # 如果不是在Jupyter中，保存为HTML并提示用户
            html_path = self.save_to_html(plot, "temp_display.html")
            if html_path:
                import webbrowser
                webbrowser.open(f"file://{html_path}")
                print(f"✓ 请在浏览器中打开: {html_path}")
    
    def create_interactive_dashboard(self,
                                   radars: List[Radar],
                                   jammers: List[Jammer],
                                   targets: Optional[List[Target]] = None) :
        """
        创建交互式仪表板
        
        参数:
            radars: 雷达列表
            jammers: 干扰机列表
            targets: 目标列表，可选
            
        返回:
            交互式仪表板
        """
        try:
            # 创建态势地图
            situation_map = self.create_ew_situation_map(radars, jammers, targets)
            
            # 创建信号强度热力图
            heatmap = self.create_signal_strength_heatmap(radars)
            
            # 如果Holoviews可用，可以创建更复杂的布局
            if hv is not None:
                # 创建统计面板
                radar_count = len(radars)
                jammer_count = len(jammers)
                target_count = len(targets) if targets else 0
                
                stats_text = f"""
                ## 电子战态势统计
                - 雷达数量: {radar_count}
                - 干扰机数量: {jammer_count}
                - 目标数量: {target_count}
                - 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                stats_panel = hv.Text(0, 0, stats_text).opts(
                    width=300,
                    height=200,
                    text_align='left',
                    text_font_size='10pt'
                )
                
                # 使用Holoviews布局
                dashboard = (situation_map + heatmap + stats_panel).cols(2)
                return dashboard
            else:
                # 仅返回态势地图
                return situation_map
                
        except Exception as e:
            print(f"创建交互式仪表板失败: {e}")
            traceback.print_exc()
            return self.create_ew_situation_map(radars, jammers, targets)


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
    
    # 显示结果
    if show:
        visualizer.display(situation_map)
    
    # 保存结果
    if output_file:
        if output_file.endswith('.html'):
            filepath = visualizer.save_to_html(situation_map, output_file)
        elif output_file.endswith('.png'):
            filepath = visualizer.save_to_png(situation_map, output_file)
        else:
            # 默认保存为HTML
            filepath = visualizer.save_to_html(situation_map, f"{output_file}.html")
    else:
        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = visualizer.save_to_html(situation_map, f"ew_situation_{timestamp}.html")
    
    return filepath


# 使用示例
if __name__ == "__main__":
    # 示例数据
    from ..core.entities import Radar, Jammer, Target, Position, RadarParameters, JammerParameters
    
    # 创建测试雷达
    radar_params = RadarParameters(
        frequency=9.0,
        power=100,
        gain=30,
        beamwidth=2.0,
        pulse_width=1e-6,
        prf=1000
    )
    
    radar1 = Radar(
        name="雷达1",
        position=Position(lon=116.4, lat=39.9, alt=100),
        radar_params=radar_params
    )
    
    radar2 = Radar(
        name="雷达2",
        position=Position(lon=116.6, lat=40.0, alt=150),
        radar_params=radar_params
    )
    
    # 创建测试干扰机
    jammer_params = JammerParameters(
        power=1000,
        gain=20,
        bandwidth=100,
        frequency_range=(8.0, 10.0)
    )
    
    jammer1 = Jammer(
        name="干扰机1",
        position=Position(lon=116.5, lat=39.8, alt=200),
        jammer_params=jammer_params
    )
    
    # 创建测试目标
    target1 = Target(
        name="目标1",
        position=Position(lon=116.45, lat=39.95, alt=10000),
        rcs=5.0,
        speed=300
    )
    
    # 创建可视化
    print("正在创建电子战态势可视化...")
    
    # 使用快速创建函数
    result_file = create_visualization(
        radars=[radar1, radar2],
        jammers=[jammer1],
        targets=[target1],
        output_file="test_ew_visualization.html",
        show=True
    )
    
    print(f"可视化结果已保存到: {result_file}")