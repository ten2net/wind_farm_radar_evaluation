"""
雷达图绘制模块
提供雷达仿真结果的可视化功能
包括距离多普勒图、距离剖面图、多普勒剖面图和天线方向图
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.colors as colors
from typing import Dict, List, Any, Optional, Tuple, Union
import os
from datetime import datetime

# 导入相关模型
from radar_factory_app.models.radar_models import RadarModel, WindowType
from radar_factory_app.models.simulation_models import SimulationResults, RadarDetection


class RadarPlotter:
    """
    雷达图绘制器
    提供多种雷达数据可视化功能
    """
    
    def __init__(self, style: str = "seaborn-v0_8"):
        """
        初始化雷达图绘制器
        
        Args:
            style: matplotlib样式
        """
        self.style = style
        self.figures = {}  # 存储生成的图形
        self._setup_plotting_style()
    
    def _setup_plotting_style(self):
        """设置绘图样式"""
        plt.style.use(self.style)
        
        # 设置雷达图专用颜色映射
        self.cmap_radar = plt.cm.jet # type: ignore
        self.cmap_doppler = plt.cm.bwr  # type: ignore # 蓝白红，适合多普勒显示
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题      
        
    def plot_range_doppler_map(self, rd_map: np.ndarray, 
                             radar_model: RadarModel,
                             timestamp: float = 0.0,
                             title: str = None, # type: ignore
                             figsize: Tuple[float, float] = (12, 8),
                             save_path: str = None, # type: ignore
                             show: bool = True) -> Figure:
        """
        绘制距离-多普勒图
        
        Args:
            rd_map: 距离-多普勒矩阵 [多普勒单元, 距离单元]
            radar_model: 雷达模型（用于获取参数）
            timestamp: 时间戳（用于标题）
            title: 图标题
            figsize: 图形尺寸
            save_path: 保存路径
            show: 是否显示图形
            
        Returns:
            matplotlib图形对象
        """
        if rd_map is None or rd_map.size == 0:
            raise ValueError("距离-多普勒图为空")
        
        # 创建图形
        fig, ax = plt.subplots(figsize=figsize)
        
        # 计算坐标轴
        range_axis, doppler_axis = self._calculate_rd_axes(rd_map, radar_model)
        
        # 创建网格
        R, D = np.meshgrid(range_axis, doppler_axis)
        
        # 绘制热图
        im = ax.pcolormesh(R, D, rd_map, 
                          cmap=self.cmap_radar, 
                          shading='auto')
        
        # 设置坐标轴标签
        ax.set_xlabel('距离 (km)')
        ax.set_ylabel('速度 (m/s)')
        
        # 设置标题
        if title is None:
            title = f"距离-多普勒图 (t={timestamp:.2f}s)"
        ax.set_title(title)
        
        # 添加颜色条
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('功率 (dB)')
        
        # 设置坐标轴范围
        ax.set_xlim(range_axis[0], range_axis[-1])
        ax.set_ylim(doppler_axis[0], doppler_axis[-1])
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 保存图形
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图形已保存: {save_path}")
        
        # 显示图形
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        # 存储图形引用
        fig_id = f"rd_map_{datetime.now().strftime('%H%M%S')}"
        self.figures[fig_id] = fig
        
        return fig
    
    def _calculate_rd_axes(self, rd_map: np.ndarray, 
                          radar_model: RadarModel) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算距离-多普勒图的坐标轴
        
        Args:
            rd_map: 距离-多普勒矩阵
            radar_model: 雷达模型
            
        Returns:
            (距离轴, 多普勒轴)
        """
        # 获取雷达参数
        tx = radar_model.transmitter
        if not tx:
            # 使用默认参数
            bandwidth = 1e6  # 1MHz
            prf = 1000      # 1kHz
            fc = 1e9        # 1GHz
        else:
            bandwidth = getattr(tx, 'bandwidth_hz', 1e6)
            prf = getattr(tx, 'prf_hz', 1000)
            fc = getattr(tx, 'frequency_hz', 1e9)
        
        # 计算距离参数
        range_res = 3e8 / (2 * bandwidth)  # 距离分辨率
        max_range = (rd_map.shape[1] * range_res) / 1000  # 最大距离(km)
        range_axis = np.linspace(0, max_range, rd_map.shape[1])
        
        # 计算多普勒参数
        wavelength = 3e8 / fc
        doppler_res = prf / rd_map.shape[0]  # 多普勒分辨率
        max_doppler = (rd_map.shape[0] // 2) * doppler_res
        doppler_axis = np.linspace(-max_doppler, max_doppler, rd_map.shape[0])
        
        # 将多普勒频率转换为速度
        velocity_axis = doppler_axis * wavelength / 2  # 速度(m/s)
        
        return range_axis, velocity_axis
    
    def plot_range_profile(self, range_profile: np.ndarray,
                          radar_model: RadarModel,
                          detections: List[RadarDetection] = None, # type: ignore
                          cfar_threshold: np.ndarray = None, # type: ignore
                          timestamp: float = 0.0,
                          title: str = None, # type: ignore
                          figsize: Tuple[float, float] = (10, 6),
                          save_path: str = None,
                          show: bool = True) -> Figure:
        """
        绘制距离剖面图
        
        Args:
            range_profile: 距离剖面数据
            radar_model: 雷达模型
            detections: 检测点列表
            cfar_threshold: CFAR门限
            timestamp: 时间戳
            title: 图标题
            figsize: 图形尺寸
            save_path: 保存路径
            show: 是否显示图形
            
        Returns:
            matplotlib图形对象
        """
        if range_profile is None or range_profile.size == 0:
            raise ValueError("距离剖面数据为空")
        
        # 创建图形
        fig, ax = plt.subplots(figsize=figsize)
        
        # 计算距离轴
        range_axis = self._calculate_range_axis(range_profile, radar_model)
        
        # 绘制距离剖面
        ax.plot(range_axis, range_profile, 'b-', linewidth=1.5, label='距离剖面')
        
        # 绘制CFAR门限
        if cfar_threshold is not None:
            ax.plot(range_axis, cfar_threshold, 'r--', linewidth=1.5, 
                   label='CFAR门限', alpha=0.7)
        
        # 标记检测点
        if detections:
            detection_ranges = [d.range for d in detections if d.range > 0]
            if detection_ranges:
                # 找到检测点对应的索引
                detection_indices = []
                for range_val in detection_ranges:
                    idx = np.argmin(np.abs(range_axis - range_val/1000))  # 转换为km
                    if idx < len(range_profile):
                        detection_indices.append(idx)
                
                # 绘制检测点
                ax.plot(range_axis[detection_indices], 
                       range_profile[detection_indices], 
                       'ro', markersize=6, label='检测点')
        
        # 设置坐标轴标签
        ax.set_xlabel('距离 (km)')
        ax.set_ylabel('功率 (dB)')
        
        # 设置标题
        if title is None:
            title = f"距离剖面图 (t={timestamp:.2f}s)"
        ax.set_title(title)
        
        # 添加图例
        ax.legend()
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 设置Y轴范围（动态调整）
        y_min = np.min(range_profile) - 5
        y_max = np.max(range_profile) + 5
        ax.set_ylim(y_min, y_max)
        
        # 保存图形
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图形已保存: {save_path}")
        
        # 显示图形
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        # 存储图形引用
        fig_id = f"range_profile_{datetime.now().strftime('%H%M%S')}"
        self.figures[fig_id] = fig
        
        return fig
    
    def _calculate_range_axis(self, range_profile: np.ndarray,
                             radar_model: RadarModel) -> np.ndarray:
        """
        计算距离轴
        
        Args:
            range_profile: 距离剖面数据
            radar_model: 雷达模型
            
        Returns:
            距离轴(km)
        """
        # 获取雷达参数
        tx = radar_model.transmitter
        if not tx:
            bandwidth = 1e6  # 默认1MHz
        else:
            bandwidth = getattr(tx, 'bandwidth_hz', 1e6)
        
        # 计算距离参数
        range_res = 3e8 / (2 * bandwidth)  # 距离分辨率(m)
        max_range = len(range_profile) * range_res / 1000  # 最大距离(km)
        
        return np.linspace(0, max_range, len(range_profile))
    
    def plot_doppler_profile(self, doppler_profile: np.ndarray,
                           radar_model: RadarModel,
                           detections: List[RadarDetection] = None, # type: ignore
                           cfar_threshold: np.ndarray = None, # type: ignore
                           timestamp: float = 0.0,
                           title: str = None, # type: ignore
                           figsize: Tuple[float, float] = (10, 6),
                           save_path: str = None, # type: ignore
                           show: bool = True) -> Figure:
        """
        绘制多普勒剖面图
        
        Args:
            doppler_profile: 多普勒剖面数据
            radar_model: 雷达模型
            detections: 检测点列表
            cfar_threshold: CFAR门限
            timestamp: 时间戳
            title: 图标题
            figsize: 图形尺寸
            save_path: 保存路径
            show: 是否显示图形
            
        Returns:
            matplotlib图形对象
        """
        if doppler_profile is None or doppler_profile.size == 0:
            raise ValueError("多普勒剖面数据为空")
        
        # 创建图形
        fig, ax = plt.subplots(figsize=figsize)
        
        # 计算多普勒轴
        doppler_axis = self._calculate_doppler_axis(doppler_profile, radar_model)
        
        # 绘制多普勒剖面
        ax.plot(doppler_axis, doppler_profile, 'g-', linewidth=1.5, label='多普勒剖面')
        
        # 绘制CFAR门限
        if cfar_threshold is not None:
            ax.plot(doppler_axis, cfar_threshold, 'r--', linewidth=1.5, 
                   label='CFAR门限', alpha=0.7)
        
        # 标记检测点
        if detections:
            detection_dopplers = [d.doppler for d in detections if d.doppler != 0]
            if detection_dopplers:
                # 找到检测点对应的索引
                detection_indices = []
                for doppler_val in detection_dopplers:
                    idx = np.argmin(np.abs(doppler_axis - doppler_val))
                    if idx < len(doppler_profile):
                        detection_indices.append(idx)
                
                # 绘制检测点
                ax.plot(doppler_axis[detection_indices], 
                       doppler_profile[detection_indices], 
                       'ro', markersize=6, label='检测点')
        
        # 设置坐标轴标签
        ax.set_xlabel('速度 (m/s)')
        ax.set_ylabel('功率 (dB)')
        
        # 设置标题
        if title is None:
            title = f"多普勒剖面图 (t={timestamp:.2f}s)"
        ax.set_title(title)
        
        # 添加图例
        ax.legend()
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 设置Y轴范围（动态调整）
        y_min = np.min(doppler_profile) - 5
        y_max = np.max(doppler_profile) + 5
        ax.set_ylim(y_min, y_max)
        
        # 保存图形
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图形已保存: {save_path}")
        
        # 显示图形
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        # 存储图形引用
        fig_id = f"doppler_profile_{datetime.now().strftime('%H%M%S')}"
        self.figures[fig_id] = fig
        
        return fig
    
    def _calculate_doppler_axis(self, doppler_profile: np.ndarray,
                            radar_model: RadarModel) -> np.ndarray:
        """
        计算多普勒轴
        
        Args:
            doppler_profile: 多普勒剖面数据
            radar_model: 雷达模型
            
        Returns:
            多普勒轴(速度, m/s)
        """
        # 获取雷达参数
        tx = radar_model.transmitter
        if not tx:
            prf = 1000      # 默认1kHz
            fc = 1e9        # 默认1GHz
        else:
            prf = getattr(tx, 'prf_hz', 1000)
            fc = getattr(tx, 'frequency_hz', 1e9)
        
        # 计算多普勒参数
        wavelength = 3e8 / fc
        doppler_res = prf / len(doppler_profile)  # 多普勒分辨率
        max_doppler = prf / 2  # 最大不模糊多普勒频率
        
        # 转换为速度
        max_velocity = max_doppler * wavelength / 2  # 最大速度(m/s)
        
        return np.linspace(-max_velocity, max_velocity, len(doppler_profile))
    
    def plot_antenna_pattern(self, radar_model: RadarModel,
                            pattern_type: str = "both",  # "azimuth", "elevation", "both"
                            title: str = None, # type: ignore
                            figsize: Tuple[float, float] = (12, 8),
                            save_path: str = None, # type: ignore
                            show: bool = True) -> Figure:
        """
        绘制天线方向图
        
        Args:
            radar_model: 雷达模型
            pattern_type: 方向图类型 ("azimuth", "elevation", "both")
            title: 图标题
            figsize: 图形尺寸
            save_path: 保存路径
            show: 是否显示图形
            
        Returns:
            matplotlib图形对象
        """
        if not radar_model.antenna:
            raise ValueError("雷达模型缺少天线参数")
        
        ant = radar_model.antenna
        
        # 根据类型创建图形
        if pattern_type == "both":
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
            axs = [ax1, ax2]
        else:
            fig, ax = plt.subplots(figsize=figsize)
            axs = [ax]
        
        # 生成方向图数据
        if pattern_type in ["azimuth", "both"]:
            # 方位角方向图
            az_angles = np.linspace(-180, 180, 361)
            az_pattern = self._calculate_antenna_pattern(
                az_angles, ant.azimuth_beamwidth, ant.gain_dbi
            )
            
            if pattern_type == "both":
                self._plot_single_antenna_pattern(
                    axs[0], az_angles, az_pattern, 
                    "方位角 (度)", "方位角方向图"
                )
            else:
                self._plot_single_antenna_pattern(
                    axs[0], az_angles, az_pattern, 
                    "方位角 (度)", "方位角方向图"
                )
        
        if pattern_type in ["elevation", "both"]:
            # 俯仰角方向图
            el_angles = np.linspace(-90, 90, 181)
            el_pattern = self._calculate_antenna_pattern(
                el_angles, ant.elevation_beamwidth, ant.gain_dbi
            )
            
            if pattern_type == "both":
                self._plot_single_antenna_pattern(
                    axs[1], el_angles, el_pattern, 
                    "俯仰角 (度)", "俯仰角方向图"
                )
            else:
                self._plot_single_antenna_pattern(
                    axs[0], el_angles, el_pattern, 
                    "俯仰角 (度)", "俯仰角方向图"
                )
        
        # 设置总标题
        if title is None:
            title = f"天线方向图 - {radar_model.name}"
        fig.suptitle(title, fontsize=14)
        
        plt.tight_layout()
        
        # 保存图形
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图形已保存: {save_path}")
        
        # 显示图形
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        # 存储图形引用
        fig_id = f"antenna_pattern_{datetime.now().strftime('%H%M%S')}"
        self.figures[fig_id] = fig
        
        return fig
    
    def _calculate_antenna_pattern(self, angles: np.ndarray,
                                 beamwidth: float, gain: float) -> np.ndarray:
        """
        计算天线方向图（简化模型）
        
        Args:
            angles: 角度数组(度)
            beamwidth: 波束宽度(度)
            gain: 天线增益(dBi)
            
        Returns:
            方向图(dB)
        """
        # 使用sinc函数近似方向图
        beamwidth_rad = np.radians(beamwidth)
        angles_rad = np.radians(angles)
        
        # 计算方向图
        pattern_linear = np.sinc(angles_rad / beamwidth_rad)**2
        pattern_db = gain + 10 * np.log10(pattern_linear + 1e-12)
        
        return pattern_db
    
    def _plot_single_antenna_pattern(self, ax: Axes, angles: np.ndarray,
                                   pattern: np.ndarray, xlabel: str, title: str):
        """
        绘制单个方向图
        
        Args:
            ax: 坐标轴对象
            angles: 角度数组
            pattern: 方向图数据
            xlabel: X轴标签
            title: 子图标题
        """
        # 绘制方向图
        ax.plot(angles, pattern, 'b-', linewidth=2)
        
        # 标记-3dB点
        peak_gain = np.max(pattern)
        half_power_level = peak_gain - 3
        
        # 找到-3dB点
        above_half_power = pattern >= half_power_level
        if np.any(above_half_power):
            half_power_indices = np.where(above_half_power)[0]
            if len(half_power_indices) > 0:
                beamwidth_angle = angles[half_power_indices[-1]] - angles[half_power_indices[0]]
                
                # 标记-3dB点
                ax.axhline(y=half_power_level, color='r', linestyle='--', alpha=0.7, 
                          label=f'-3dB点 (波束宽度: {beamwidth_angle:.1f}°)')
        
        # 设置坐标轴
        ax.set_xlabel(xlabel)
        ax.set_ylabel('增益 (dBi)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 设置Y轴范围
        y_min = np.min(pattern) - 10
        y_max = np.max(pattern) + 3
        ax.set_ylim(y_min, y_max)
    
    def plot_detection_results(self, results: SimulationResults,
                             radar_id: str = None, # type: ignore
                             time_range: Tuple[float, float] = None, # type: ignore
                             plot_type: str = "all",  # "range", "doppler", "snr", "all"
                             figsize: Tuple[float, float] = (15, 10),
                             save_path: str = None, # type: ignore
                             show: bool = True) -> Figure:
        """
        绘制检测结果统计图
        
        Args:
            results: 仿真结果
            radar_id: 雷达ID（None表示所有雷达）
            time_range: 时间范围 (开始, 结束)
            plot_type: 绘图类型
            figsize: 图形尺寸
            save_path: 保存路径
            show: 是否显示图形
            
        Returns:
            matplotlib图形对象
        """
        if not results.detections:
            raise ValueError("没有检测数据")
        
        # 过滤检测数据
        detections = self._filter_detections(results.detections, radar_id, time_range)
        
        if not detections:
            raise ValueError("过滤后没有检测数据")
        
        # 根据绘图类型创建子图
        if plot_type == "all":
            fig, axes = plt.subplots(2, 2, figsize=figsize)
            axs = axes.flatten()
        else:
            fig, ax = plt.subplots(figsize=figsize)
            axs = [ax]
        
        # 提取数据
        timestamps = [d.timestamp for d in detections]
        ranges = [d.range for d in detections]
        dopplers = [d.doppler for d in detections]
        snrs = [d.snr for d in detections]
        confidences = [d.detection_confidence for d in detections]
        
        # 绘制不同的图
        if plot_type in ["all", "range"]:
            idx = 0 if plot_type == "all" else 0
            self._plot_detection_range(axs[idx], timestamps, ranges, "距离随时间变化")
        
        if plot_type in ["all", "doppler"]:
            idx = 1 if plot_type == "all" else 0
            self._plot_detection_doppler(axs[idx], timestamps, dopplers, "速度随时间变化")
        
        if plot_type in ["all", "snr"]:
            idx = 2 if plot_type == "all" else 0
            self._plot_detection_snr(axs[idx], timestamps, snrs, "信噪比随时间变化")
        
        if plot_type == "all":
            self._plot_detection_confidence(axs[3], timestamps, confidences, "置信度随时间变化")
        
        # 设置总标题
        radar_info = f" - 雷达: {radar_id}" if radar_id else ""
        time_info = f" - 时间: {time_range[0]:.1f}-{time_range[1]:.1f}s" if time_range else ""
        fig.suptitle(f"检测结果统计{radar_info}{time_info}", fontsize=14)
        
        plt.tight_layout()
        
        # 保存图形
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图形已保存: {save_path}")
        
        # 显示图形
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        # 存储图形引用
        fig_id = f"detection_results_{datetime.now().strftime('%H%M%S')}"
        self.figures[fig_id] = fig
        
        return fig
    
    def _filter_detections(self, detections: List[RadarDetection],
                         radar_id: str = None, # type: ignore
                         time_range: Tuple[float, float] = None) -> List[RadarDetection]: # type: ignore
        """
        过滤检测数据
        
        Args:
            detections: 检测列表
            radar_id: 雷达ID过滤
            time_range: 时间范围过滤
            
        Returns:
            过滤后的检测列表
        """
        filtered = detections
        
        # 按雷达ID过滤
        if radar_id is not None:
            filtered = [d for d in filtered if d.radar_id == radar_id]
        
        # 按时间范围过滤
        if time_range is not None:
            t_start, t_end = time_range
            filtered = [d for d in filtered if t_start <= d.timestamp <= t_end]
        
        return filtered
    
    def _plot_detection_range(self, ax: Axes, timestamps: List[float],
                            ranges: List[float], title: str):
        """绘制距离随时间变化图"""
        ax.scatter(timestamps, ranges, c='blue', alpha=0.6, s=20)
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('距离 (m)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
    
    def _plot_detection_doppler(self, ax: Axes, timestamps: List[float],
                                  dopplers: List[float], title: str):
            """绘制速度随时间变化图"""
            ax.scatter(timestamps, dopplers, c='red', alpha=0.6, s=20)
            ax.set_xlabel('时间 (s)')
            ax.set_ylabel('速度 (m/s)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
    
    def _plot_detection_snr(self, ax: Axes, timestamps: List[float],
                          snrs: List[float], title: str):
        """绘制信噪比随时间变化图"""
        ax.scatter(timestamps, snrs, c='green', alpha=0.6, s=20)
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('信噪比 (dB)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        # 添加平均SNR线
        if len(snrs) > 0:
            avg_snr = np.mean(snrs)
            ax.axhline(y=avg_snr, color='red', linestyle='--',  # type: ignore
                      label=f'平均SNR: {avg_snr:.1f} dB')
            ax.legend()
    
    def _plot_detection_confidence(self, ax: Axes, timestamps: List[float],
                                 confidences: List[float], title: str):
        """绘制置信度随时间变化图"""
        ax.scatter(timestamps, confidences, c='purple', alpha=0.6, s=20)
        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('检测置信度')
        ax.set_title(title)
        ax.set_ylim(0, 1.0)
        ax.grid(True, alpha=0.3)
        
        # 添加平均置信度线
        if len(confidences) > 0:
            avg_confidence = np.mean(confidences)
            ax.axhline(y=avg_confidence, color='red', linestyle='--', # type: ignore
                      label=f'平均置信度: {avg_confidence:.2f}')
            ax.legend()
    
    def plot_comprehensive_analysis(self, results: SimulationResults,
                                  radar_id: str = None, # type: ignore
                                  save_dir: str = None, # type: ignore
                                  show: bool = True) -> Dict[str, str]:
        """
        绘制综合分析图集（包含所有类型的图）
        
        Args:
            results: 仿真结果
            radar_id: 雷达ID
            save_dir: 保存目录
            show: 是否显示图形
            
        Returns:
            保存的文件路径字典
        """
        if not results.raw_data:
            raise ValueError("没有原始数据可供分析")
        
        # 创建保存目录
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        saved_files = {}
        
        # 获取第一个时间步的数据作为示例
        first_timestamp = next(iter(results.raw_data[list(results.raw_data.keys())[0]]))
        radar_data = results.raw_data[list(results.raw_data.keys())[0]][first_timestamp]
        processed_data = radar_data['processed']
        
        # 1. 绘制距离-多普勒图
        if processed_data.get('rd_map') is not None:
            rd_save_path = os.path.join(save_dir, 'range_doppler_map.png') if save_dir else None
            self.plot_range_doppler_map(
                processed_data['rd_map'],
                results.parameters.radars[0],  # 使用第一个雷达
                timestamp=first_timestamp,
                save_path=rd_save_path, # type: ignore
                show=show
            )
            if rd_save_path:
                saved_files['range_doppler_map'] = rd_save_path
        
        # 2. 绘制距离剖面图
        if processed_data.get('range_profile') is not None:
            range_save_path = os.path.join(save_dir, 'range_profile.png') if save_dir else None
            detections = [RadarDetection.from_dict(d) for d in radar_data['detections']] # type: ignore
            self.plot_range_profile(
                processed_data['range_profile'],
                results.parameters.radars[0],
                detections=detections,
                cfar_threshold=processed_data.get('cfar_threshold'),
                timestamp=first_timestamp,
                save_path=range_save_path, # type: ignore
                show=show
            )
            if range_save_path:
                saved_files['range_profile'] = range_save_path
        
        # 3. 绘制多普勒剖面图
        if processed_data.get('doppler_profile') is not None:
            doppler_save_path = os.path.join(save_dir, 'doppler_profile.png') if save_dir else None
            self.plot_doppler_profile(
                processed_data['doppler_profile'],
                results.parameters.radars[0],
                detections=detections, # type: ignore
                cfar_threshold=processed_data.get('cfar_threshold'),
                timestamp=first_timestamp,
                save_path=doppler_save_path, # type: ignore
                show=show
            )
            if doppler_save_path:
                saved_files['doppler_profile'] = doppler_save_path
        
        # 4. 绘制天线方向图
        if results.parameters.radars and results.parameters.radars[0].antenna:
            antenna_save_path = os.path.join(save_dir, 'antenna_pattern.png') if save_dir else None
            self.plot_antenna_pattern(
                results.parameters.radars[0],
                pattern_type="both",
                save_path=antenna_save_path, # type: ignore
                show=show
            )
            if antenna_save_path:
                saved_files['antenna_pattern'] = antenna_save_path
        
        # 5. 绘制检测结果统计图
        if results.detections:
            detection_save_path = os.path.join(save_dir, 'detection_results.png') if save_dir else None
            self.plot_detection_results(
                results,
                radar_id=radar_id,
                plot_type="all",
                save_path=detection_save_path, # type: ignore
                show=show
            )
            if detection_save_path:
                saved_files['detection_results'] = detection_save_path
        
        return saved_files
    
    def create_animation(self, results: SimulationResults,
                       radar_id: str,
                       animation_type: str = "range_doppler",  # "range_doppler", "range", "doppler"
                       fps: int = 5,
                       save_path: str = None, # type: ignore
                       show: bool = True) -> str:
        """
        创建雷达数据动画（需要安装ffmpeg）
        
        Args:
            results: 仿真结果
            radar_id: 雷达ID
            animation_type: 动画类型
            fps: 帧率
            save_path: 保存路径
            show: 是否显示动画
            
        Returns:
            动画文件路径
        """
        try:
            from matplotlib.animation import FuncAnimation
            import matplotlib.animation as animation
        except ImportError:
            raise ImportError("创建动画需要matplotlib.animation模块")
        
        if radar_id not in results.raw_data:
            raise ValueError(f"雷达 {radar_id} 没有数据")
        
        radar_data = results.raw_data[radar_id]
        timestamps = sorted(radar_data.keys())
        
        if not timestamps:
            raise ValueError("没有时间步数据")
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(10, 6))
        
        def update(frame):
            """更新动画帧"""
            ax.clear()
            timestamp = timestamps[frame]
            data = radar_data[timestamp]['processed']
            
            if animation_type == "range_doppler" and data.get('rd_map') is not None:
                # 距离-多普勒图动画
                rd_map = data['rd_map']
                range_axis, doppler_axis = self._calculate_rd_axes(
                    rd_map, results.parameters.get_radar_by_id(radar_id) # type: ignore
                )
                R, D = np.meshgrid(range_axis, doppler_axis)
                
                im = ax.pcolormesh(R, D, rd_map, cmap=self.cmap_radar, shading='auto')
                ax.set_xlabel('距离 (km)')
                ax.set_ylabel('速度 (m/s)')
                ax.set_title(f'距离-多普勒图 (t={timestamp:.2f}s)')
                
            elif animation_type == "range" and data.get('range_profile') is not None:
                # 距离剖面动画
                range_profile = data['range_profile']
                range_axis = self._calculate_range_axis(
                    range_profile, results.parameters.get_radar_by_id(radar_id) # type: ignore
                )
                
                ax.plot(range_axis, range_profile, 'b-', linewidth=1.5)
                ax.set_xlabel('距离 (km)')
                ax.set_ylabel('功率 (dB)')
                ax.set_title(f'距离剖面 (t={timestamp:.2f}s)')
                ax.grid(True, alpha=0.3)
                
            elif animation_type == "doppler" and data.get('doppler_profile') is not None:
                # 多普勒剖面动画
                doppler_profile = data['doppler_profile']
                doppler_axis = self._calculate_doppler_axis(
                    doppler_profile, results.parameters.get_radar_by_id(radar_id) # type: ignore
                )
                
                ax.plot(doppler_axis, doppler_profile, 'g-', linewidth=1.5)
                ax.set_xlabel('速度 (m/s)')
                ax.set_ylabel('功率 (dB)')
                ax.set_title(f'多普勒剖面 (t={timestamp:.2f}s)')
                ax.grid(True, alpha=0.3)
            
            return ax
        
        # 创建动画
        anim = FuncAnimation(fig, update, frames=len(timestamps),  # type: ignore
                           interval=1000/fps, blit=False)
        
        # 保存动画
        if save_path:
            # 确保文件扩展名正确
            if not save_path.endswith('.gif') and not save_path.endswith('.mp4'):
                save_path += '.gif'
            
            # 保存为GIF
            anim.save(save_path, writer='pillow', fps=fps)
            print(f"动画已保存: {save_path}")
        
        # 显示动画
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        return save_path
    
    def save_all_figures(self, save_dir: str = "radar_plots"):
        """
        保存所有生成的图形
        
        Args:
            save_dir: 保存目录
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        saved_files = []
        for fig_id, fig in self.figures.items():
            save_path = os.path.join(save_dir, f"{fig_id}.png")
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            saved_files.append(save_path)
            print(f"图形已保存: {save_path}")
        
        return saved_files
    
    def clear_figures(self):
        """清除所有存储的图形"""
        for fig in self.figures.values():
            plt.close(fig)
        self.figures.clear()
        print("所有图形已清除")
    
    def __del__(self):
        """析构函数，确保清理图形"""
        self.clear_figures()


# 集成到RadarSimulator类中的辅助方法
def integrate_plotting_with_simulator():
    """
    演示如何将绘图模块集成到RadarSimulator中
    """
    # 在RadarSimulator类中添加以下方法
    
    class RadarSimulatorWithPlots:
        def __init__(self):
            # ... 其他初始化代码 ...
            self.plotter = RadarPlotter()
        
        def plot_simulation_results(self, results: SimulationResults,
                                 plot_types: List[str] = None, # type: ignore
                                 save_dir: str = None, # type: ignore
                                 show: bool = True) -> Dict[str, str]:
            """
            绘制仿真结果图
            
            Args:
                results: 仿真结果
                plot_types: 绘图类型列表 ["range_doppler", "range", "doppler", "antenna", "detections", "all"]
                save_dir: 保存目录
                show: 是否显示图形
                
            Returns:
                保存的文件路径字典
            """
            if plot_types is None:
                plot_types = ["all"]
            
            if "all" in plot_types:
                # 绘制所有图形
                return self.plotter.plot_comprehensive_analysis(
                    results, save_dir=save_dir, show=show
                )
            else:
                saved_files = {}
                
                # 根据类型绘制特定图形
                if "range_doppler" in plot_types and results.raw_data:
                    # 绘制距离-多普勒图
                    pass
                
                if "range" in plot_types and results.raw_data:
                    # 绘制距离剖面图
                    pass
                
                if "doppler" in plot_types and results.raw_data:
                    # 绘制多普勒剖面图
                    pass
                
                if "antenna" in plot_types and results.parameters.radars:
                    # 绘制天线方向图
                    pass
                
                if "detections" in plot_types and results.detections:
                    # 绘制检测结果统计图
                    pass
                
                return saved_files
        
        def create_simulation_animation(self, results: SimulationResults,
                                      radar_id: str,
                                      animation_type: str = "range_doppler",
                                      save_path: str = None) -> str: # type: ignore
            """
            创建仿真动画
            
            Args:
                results: 仿真结果
                radar_id: 雷达ID
                animation_type: 动画类型
                save_path: 保存路径
                
            Returns:
                动画文件路径
            """
            return self.plotter.create_animation(
                results, radar_id, animation_type, save_path=save_path
            )


# 使用示例
if __name__ == "__main__":
    # 创建绘图器实例
    plotter = RadarPlotter()
    
    # 示例1: 生成模拟数据并绘图
    print("=== 雷达图绘制模块演示 ===")
    
    # 创建模拟雷达数据
    # 距离-多普勒图 (64x128)
    rd_map = np.random.randn(64, 128) * 10 + 50
    rd_map[30:35, 60:70] += 30  # 添加目标
    
    # 距离剖面
    range_profile = np.random.randn(128) * 5 + 20
    range_profile[60:70] += 15  # 添加目标
    
    # 多普勒剖面
    doppler_profile = np.random.randn(64) * 5 + 15
    doppler_profile[30:35] += 10  # 添加目标
    
    # 创建模拟雷达模型
    class MockRadarModel:
        def __init__(self):
            self.name = "模拟雷达"
            self.transmitter = MockTransmitter()
            self.antenna = MockAntenna()
    
    class MockTransmitter:
        def __init__(self):
            self.bandwidth_hz = 1e6
            self.prf_hz = 1000
            self.frequency_hz = 1e9
    
    class MockAntenna:
        def __init__(self):
            self.azimuth_beamwidth = 10.0
            self.elevation_beamwidth = 20.0
            self.gain_dbi = 30.0
    
    mock_radar = MockRadarModel()
    
    # 绘制各种图形
    try:
        # 1. 绘制距离-多普勒图
        print("1. 绘制距离-多普勒图...")
        plotter.plot_range_doppler_map(rd_map, mock_radar, title="模拟距离-多普勒图") # type: ignore
        
        # 2. 绘制距离剖面图
        print("2. 绘制距离剖面图...")
        plotter.plot_range_profile(range_profile, mock_radar, title="模拟距离剖面图") # type: ignore
        
        # 3. 绘制多普勒剖面图
        print("3. 绘制多普勒剖面图...")
        plotter.plot_doppler_profile(doppler_profile, mock_radar, title="模拟多普勒剖面图") # type: ignore
        
        # 4. 绘制天线方向图
        print("4. 绘制天线方向图...")
        plotter.plot_antenna_pattern(mock_radar, title="模拟天线方向图") # type: ignore
        
        print("所有图形绘制完成！")
        
        # 保存所有图形
        saved_files = plotter.save_all_figures("demo_plots")
        print(f"保存了 {len(saved_files)} 个图形文件")
        
    except Exception as e:
        print(f"绘图演示失败: {str(e)}")
    
    finally:
        # 清理资源
        plotter.clear_figures()