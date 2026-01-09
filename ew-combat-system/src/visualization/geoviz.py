"""
GeoViews可视化模块
"""
import geoviews as gv
import geoviews.feature as gf
import holoviews as hv
from holoviews.operation.datashader import rasterize, shade
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColorBar, LinearColorMapper
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import xarray as xr

class EWVisualizer:
    """电子战可视化器"""
    
    @staticmethod
    def create_coverage_map(radars, jammers, targets=None, bbox=None):
        """创建覆盖态势图"""
        if bbox is None:
            bbox = [115, 38, 118, 41]  # 默认范围
        
        # 创建基础地图
        base_map = (
            gf.coastline.opts(line_color='blue', line_width=1, alpha=0.5) * 
            gf.borders.opts(line_color='gray', line_width=0.5) * 
            gf.land.opts(fill_color='lightgray', alpha=0.3) * 
            gf.ocean.opts(fill_color='aliceblue', alpha=0.3)
        )
        
        # 添加WMTS底图
        tile_layer = gv.WMTS('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{Y}/{X}.jpg')
        
        # 创建雷达可视化
        radar_elements = EWVisualizer._create_radar_visualization(radars)
        
        # 创建干扰机可视化
        jammer_elements = EWVisualizer._create_jammer_visualization(jammers)
        
        # 创建目标可视化
        target_elements = EWVisualizer._create_target_visualization(targets) if targets else gv.Overlay([])
        
        # 组合所有图层
        ew_map = (
            tile_layer * 
            base_map * 
            radar_elements * 
            jammer_elements * 
            target_elements
        ).opts(
            gv.opts.Overlay(
                width=800,
                height=600,
                title="电子战对抗态势图",
                xlim=(bbox[0], bbox[2]),
                ylim=(bbox[1], bbox[3]),
                toolbar='above',
                tools=['pan', 'wheel_zoom', 'reset', 'save', 'hover']
            )
        )
        
        return ew_map
    
    @staticmethod
    def _create_radar_visualization(radars):
        """创建雷达可视化"""
        elements = []
        
        for radar in radars:
            # 雷达位置点
            radar_point = gv.Points(
                [(radar.position.lon, radar.position.lat)], 
                ['lon', 'lat'], 
                ['name', 'state']
            ).opts(
                size=12,
                color='red',
                line_color='darkred',
                line_width=2,
                tools=['hover'],
                marker='triangle_dot',
                hover_fill_color='red',
                hover_line_color='darkred'
            )
            elements.append(radar_point)
            
            # 雷达覆盖范围
            if hasattr(radar, 'calculate_coverage'):
                try:
                    coverage_points = radar.calculate_coverage()
                    if coverage_points is not None and len(coverage_points) > 2:
                        # 创建多边形
                        poly_points = list(zip(coverage_points[:, 1], coverage_points[:, 0]))
                        coverage_poly = gv.Polygons([poly_points])
                        coverage_viz = coverage_poly.opts(
                            fill_color='red',
                            fill_alpha=0.1,
                            line_color='red',
                            line_width=1.5,
                            line_dash='dashed',
                            hover_fill_alpha=0.3
                        )
                        elements.append(coverage_viz)
                except Exception as e:
                    print(f"计算雷达覆盖失败: {e}")
        
        return gv.Overlay(elements)
    
    @staticmethod
    def _create_jammer_visualization(jammers):
        """创建干扰机可视化"""
        elements = []
        
        for jammer in jammers:
            # 干扰机位置点
            jammer_point = gv.Points(
                [(jammer.position.lon, jammer.position.lat)], 
                ['lon', 'lat'], 
                ['name', 'state']
            ).opts(
                size=12,
                color='blue',
                line_color='darkblue',
                line_width=2,
                tools=['hover'],
                marker='square_x',
                hover_fill_color='blue',
                hover_line_color='darkblue'
            )
            elements.append(jammer_point)
            
            # 干扰扇区
            if hasattr(jammer, 'calculate_jamming_sector'):
                try:
                    # 获取参数
                    azimuth = jammer.parameters.get('azimuth', 0)
                    width = jammer.parameters.get('beamwidth', 60)
                    range_km = jammer.parameters.get('range_effective', 200)
                    
                    sector_points = jammer.calculate_jamming_sector(azimuth, width, range_km)
                    if sector_points is not None and len(sector_points) > 2:
                        sector_poly = gv.Polygons([sector_points])
                        sector_viz = sector_poly.opts(
                            fill_color='blue',
                            fill_alpha=0.2,
                            line_color='blue',
                            line_width=1.5,
                            line_dash='solid',
                            hover_fill_alpha=0.4
                        )
                        elements.append(sector_viz)
                except Exception as e:
                    print(f"计算干扰扇区失败: {e}")
        
        return gv.Overlay(elements)
    
    @staticmethod
    def _create_target_visualization(targets):
        """创建目标可视化"""
        elements = []
        
        for target in targets:
            if hasattr(target, 'trajectory') and target.trajectory:
                # 轨迹线
                traj_points = [(p[1], p[0]) for p in target.trajectory]  # (lon, lat)
                traj_line = gv.Curve(traj_points, vdims=['time'])
                traj_viz = traj_line.opts(
                    color='green',
                    line_width=2,
                    line_dash='dotted',
                    alpha=0.7
                )
                elements.append(traj_viz)
                
                # 当前位置点
                last_point = traj_points[-1]
                target_point = gv.Points([last_point], ['lon', 'lat'], ['name'])
                point_viz = target_point.opts(
                    size=8,
                    color='green',
                    line_color='darkgreen',
                    marker='circle',
                    hover_fill_color='green'
                )
                elements.append(point_viz)
        
        return gv.Overlay(elements)
    
    @staticmethod
    def create_signal_analysis_plot(simulation_results):
        """创建信号分析图"""
        if not simulation_results:
            return None
        
        # 创建子图布局
        plots = []
        
        # 1. 干信比随时间变化
        if 'j_s_ratio_history' in simulation_results:
            time_steps = len(simulation_results['j_s_ratio_history'])
            time = np.arange(time_steps)
            js_ratio = simulation_results['j_s_ratio_history']
            
            df_js = pd.DataFrame({
                '时间': time,
                '干信比(dB)': js_ratio
            })
            
            js_plot = gv.Curve(df_js, '时间', '干信比(dB)').opts(
                width=400,
                height=300,
                title="干信比随时间变化",
                color='red',
                ylim=(-20, 40)
            )
            plots.append(js_plot)
        
        # 2. 探测概率分布
        if 'detection_probability' in simulation_results:
            det_probs = simulation_results['detection_probability']
            if isinstance(det_probs, dict):
                radar_names = list(det_probs.keys())
                prob_values = list(det_probs.values())
                
                df_det = pd.DataFrame({
                    '雷达': radar_names,
                    '探测概率': prob_values
                })
                
                det_plot = gv.Bars(df_det, '雷达', '探测概率').opts(
                    width=400,
                    height=300,
                    title="各雷达探测概率",
                    color='blue',
                    ylim=(0, 1)
                )
                plots.append(det_plot)
        
        # 3. 传播损耗分析
        if 'propagation_loss' in simulation_results:
            distances = np.linspace(10, 300, 100)
            losses = []
            
            for d in distances:
                # 简化的传播损耗模型
                loss = 20 * np.log10(d) + 20 * np.log10(3) + 32.44
                losses.append(loss)
            
            df_loss = pd.DataFrame({
                '距离(km)': distances,
                '传播损耗(dB)': losses
            })
            
            loss_plot = gv.Curve(df_loss, '距离(km)', '传播损耗(dB)').opts(
                width=400,
                height=300,
                title="传播损耗 vs 距离",
                color='purple',
                ylim=(80, 180)
            )
            plots.append(loss_plot)
        
        # 组合所有子图
        if plots:
            layout = gv.Layout(plots).cols(2)
            return layout.opts(
                hv.opts.Layout(
                    title="信号分析图表",
                    toolbar='above'
                )
            )
        
        return None
    
    @staticmethod
    def create_3d_terrain_visualization(terrain_data, radar_positions=None, jammer_positions=None):
        """创建3D地形可视化"""
        try:
            import xarray as xr
            from holoviews.operation import contours
            
            if isinstance(terrain_data, (str, xr.DataArray)):
                if isinstance(terrain_data, str):
                    # 从文件加载
                    dem = xr.open_rasterio(terrain_data)
                else:
                    dem = terrain_data
                
                # 创建3D表面
                terrain_surface = gv.Surface(
                    (dem.x, dem.y, dem.values[0]),
                    ['x', 'y'], '高程'
                ).opts(
                    cmap='terrain',
                    colorbar=True,
                    width=600,
                    height=500,
                    title="地形高程图"
                )
                
                # 添加等高线
                contour = contours(terrain_surface, levels=20)
                
                # 组合
                visualization = terrain_surface * contour.opts(
                    line_color='black',
                    line_width=0.5,
                    alpha=0.5
                )
                
                return visualization
                
        except ImportError as e:
            print(f"3D可视化需要额外依赖: {e}")
            return None
    
    @staticmethod
    def create_spectrum_analysis(frequencies, powers, radar_freqs=None, jammer_freqs=None):
        """创建频谱分析图"""
        # 创建频谱数据
        df_spectrum = pd.DataFrame({
            '频率(MHz)': frequencies,
            '功率(dBm)': powers
        })
        
        spectrum_plot = gv.Curve(df_spectrum, '频率(MHz)', '功率(dBm)').opts(
            width=600,
            height=400,
            title="电磁频谱分析",
            color='blue',
            line_width=2
        )
        
        # 添加雷达频率标记
        if radar_freqs:
            for freq in radar_freqs:
                vline = gv.VLine(freq).opts(
                    color='red',
                    line_width=1.5,
                    line_dash='dashed'
                )
                spectrum_plot *= vline
        
        # 添加干扰频率标记
        if jammer_freqs:
            for freq in jammer_freqs:
                vline = gv.VLine(freq).opts(
                    color='orange',
                    line_width=1.5,
                    line_dash='dotted'
                )
                spectrum_plot *= vline
        
        return spectrum_plot
