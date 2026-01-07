"""
雷达图绘制模块 - 增强版
添加雷达模型关键参数到图中
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.patches as patches
from matplotlib.offsetbox import AnchoredText
import matplotlib.colors as colors
from typing import Dict, List, Any, Optional, Tuple, Union
import os
from datetime import datetime

# 导入相关模型
from radar_factory_app.models.radar_models import RadarModel, WindowType, RadarBand
from radar_factory_app.models.simulation_models import SimulationResults, RadarDetection


class EnhancedRadarPlotter:
    """
    增强版雷达图绘制器
    在图中添加雷达模型关键参数
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
        self.cmap_radar = plt.cm.jet
        self.cmap_doppler = plt.cm.bwr  # 蓝白红，适合多普勒显示
        
        # 设置字体
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题  
    
    def _extract_radar_parameters(self, radar_model: RadarModel) -> Dict[str, Any]:
        """
        提取雷达模型的关键参数
        
        Args:
            radar_model: 雷达模型
            
        Returns:
            参数字典
        """
        params = {
            '基本信息': {},
            '发射机参数': {},
            '接收机参数': {},
            '天线参数': {},
            '信号处理参数': {}
        }
        
        # 基本信息
        params['基本信息'] = {
            '雷达名称': getattr(radar_model, 'name', '未知'),
            '雷达型号': getattr(radar_model, 'model', '未知'),
            '工作频段': getattr(radar_model, 'band', RadarBand.S.value) if hasattr(radar_model, 'band') else '未知',
            '雷达ID': getattr(radar_model, 'radar_id', '未知')
        }
        
        # 发射机参数
        if radar_model.transmitter:
            tx = radar_model.transmitter
            params['发射机参数'] = {
                '频率': f"{getattr(tx, 'frequency_hz', 0)/1e9:.2f} GHz",
                '带宽': f"{getattr(tx, 'bandwidth_hz', 0)/1e6:.1f} MHz",
                '峰值功率': f"{getattr(tx, 'power_w', 0)/1e3:.1f} kW",
                '脉冲宽度': f"{getattr(tx, 'pulse_width_s', 0)*1e6:.1f} μs",
                'PRF': f"{getattr(tx, 'prf_hz', 0)/1e3:.1f} kHz",
                '脉冲数': getattr(tx, 'pulses', 1)
            }
        
        # 接收机参数
        if radar_model.receiver:
            rx = radar_model.receiver
            params['接收机参数'] = {
                '采样率': f"{getattr(rx, 'sampling_rate_hz', 0)/1e6:.1f} MHz",
                '噪声系数': f"{getattr(rx, 'noise_figure_db', 0):.1f} dB",
                '动态范围': f"{getattr(rx, 'dynamic_range_db', 0):.1f} dB",
                'RF增益': f"{getattr(rx, 'rf_gain_dbi', 0):.1f} dB"
            }
        
        # 天线参数
        if radar_model.antenna:
            ant = radar_model.antenna
            params['天线参数'] = {
                '增益': f"{getattr(ant, 'gain_dbi', 0):.1f} dBi",
                '方位波束宽度': f"{getattr(ant, 'azimuth_beamwidth', 0):.1f}°",
                '俯仰波束宽度': f"{getattr(ant, 'elevation_beamwidth', 0):.1f}°",
                '极化方式': getattr(ant, 'polarization', '未知')
            }

        # 信号处理参数
        if radar_model.signal_processing:
            sp = radar_model.signal_processing
            params['信号处理参数'] = {
                '距离单元数': getattr(sp, 'range_cells', 0),
                '多普勒单元数': getattr(sp, 'doppler_cells', 0),
                'CFAR类型': getattr(sp, 'cfar_method', 'CA'),
                'CFAR虚警概率': f"{getattr(sp, 'cfar_pfa', 1e-6):.1e}"
            }
        
        return params
    
    def _add_parameter_textbox(self, ax: Axes, params: Dict[str, Any], 
                             position: str = 'right') -> AnchoredText:
        """
        添加参数文本框到图中
        
        Args:
            ax: 坐标轴对象
            params: 参数字典
            position: 文本框位置 ('right', 'left', 'top', 'bottom')
            
        Returns:
            锚定文本对象
        """
        # 生成参数字符串
        param_text = "雷达参数:\n"
        param_text += "=" * 20 + "\n"
        
        for category, category_params in params.items():
            if category_params:  # 只添加非空类别
                param_text += f"\n{category}:\n"
                for key, value in category_params.items():
                    param_text += f"{key}: {value}\n"
        
        # 创建锚定文本
        anchored_text = AnchoredText(param_text, loc='upper right', 
                                   frameon=True, prop=dict(size=8))
        anchored_text.patch.set_boxstyle("round,pad=0.2")
        anchored_text.patch.set_facecolor('lightgray')
        anchored_text.patch.set_alpha(0.8)
        
        ax.add_artist(anchored_text)
        return anchored_text
    
    def _add_mini_parameter_table(self, fig: Figure, params: Dict[str, Any],
                                position: Tuple[float, float] = (0.02, 0.02)) -> Any:
        """
        添加迷你参数表格到图形底部
        
        Args:
            fig: 图形对象
            params: 参数字典
            position: 表格位置 (x, y)
            
        Returns:
            文本对象
        """
        # 选择最重要的参数
        key_params = {}
        
        # 基本信息
        if '基本信息' in params:
            key_params.update(params['基本信息'])
        
        # 发射机关键参数
        if '发射机参数' in params:
            tx_keys = ['频率', '带宽', '峰值功率']
            for key in tx_keys:
                if key in params['发射机参数']:
                    key_params[f"Tx {key}"] = params['发射机参数'][key]
        
        # 接收机关键参数
        if '接收机参数' in params:
            rx_keys = ['采样率', '噪声系数']
            for key in rx_keys:
                if key in params['接收机参数']:
                    key_params[f"Rx {key}"] = params['接收机参数'][key]
        
        # 天线关键参数
        if '天线参数' in params:
            ant_keys = ['增益', '方位波束宽度']
            for key in ant_keys:
                if key in params['天线参数']:
                    key_params[f"Ant {key}"] = params['天线参数'][key]
        
        # 生成参数文本
        param_lines = []
        for i, (key, value) in enumerate(key_params.items()):
            if i % 2 == 0:
                line = f"{key}: {value}"
            else:
                line += f" | {key}: {value}"
                param_lines.append(line)
        
        # 如果参数个数为奇数，添加最后一个
        if len(key_params) % 2 != 0:
            param_lines.append(f"{list(key_params.keys())[-1]}: {list(key_params.values())[-1]}")
        
        param_text = "\n".join(param_lines)
        
        # 添加文本到图形
        text_obj = fig.text(position[0], position[1], param_text, 
                          fontsize=8, bbox=dict(boxstyle="round,pad=0.3", 
                                              facecolor="lightgray", alpha=0.7),
                          transform=fig.transFigure)
        
        return text_obj
    
    def plot_range_doppler_map(self, rd_map: np.ndarray, 
                             radar_model: RadarModel,
                             timestamp: float = 0.0,
                             title: str = None,
                             figsize: Tuple[float, float] = (14, 9),
                             show_parameters: bool = True,
                             parameter_position: str = 'right',
                             save_path: str = None,
                             show: bool = True) -> Figure:
        """
        绘制距离-多普勒图（增强版）
        
        Args:
            rd_map: 距离-多普勒矩阵 [多普勒单元, 距离单元]
            radar_model: 雷达模型（用于获取参数）
            timestamp: 时间戳（用于标题）
            title: 图标题
            figsize: 图形尺寸
            show_parameters: 是否显示参数
            parameter_position: 参数显示位置 ('right', 'bottom', 'both')
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
        ax.set_xlabel('距离 (km)', fontsize=12)
        ax.set_ylabel('速度 (m/s)', fontsize=12)
        
        # 设置标题
        if title is None:
            title = f"距离-多普勒图\n雷达: {getattr(radar_model, 'name', '未知')} | 时间: {timestamp:.2f}s"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # 添加颜色条
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('功率 (dB)', fontsize=12)
        
        # 设置坐标轴范围
        ax.set_xlim(range_axis[0], range_axis[-1])
        ax.set_ylim(doppler_axis[0], doppler_axis[-1])
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 添加雷达参数
        if show_parameters:
            # 提取参数
            params = self._extract_radar_parameters(radar_model)
            
            if parameter_position in ['right', 'both']:
                # 在右侧添加详细参数文本框
                self._add_parameter_textbox(ax, params, 'upper right')
            
            if parameter_position in ['bottom', 'both']:
                # 在底部添加迷你参数表
                self._add_mini_parameter_table(fig, params, (0.02, 0.02))
        
        # 添加性能指标
        self._add_performance_indicators(ax, rd_map)
        
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
    
    def _add_performance_indicators(self, ax: Axes, rd_map: np.ndarray):
        """添加性能指标到图中"""
        # 计算动态范围
        dynamic_range = np.max(rd_map) - np.min(rd_map)
        
        # 计算信噪比估计
        noise_floor = np.percentile(rd_map, 10)  # 使用10%分位数作为噪声基底
        signal_peak = np.max(rd_map)
        snr_estimate = signal_peak - noise_floor
        
        # 添加性能文本
        perf_text = f"动态范围: {dynamic_range:.1f} dB\n峰值SNR: {snr_estimate:.1f} dB"
        
        # 在左上角添加性能指标
        ax.text(0.02, 0.98, perf_text, transform=ax.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    def plot_range_profile(self, range_profile: np.ndarray,
                          radar_model: RadarModel,
                          detections: List[RadarDetection] = None,
                          cfar_threshold: np.ndarray = None,
                          timestamp: float = 0.0,
                          title: str = None,
                          figsize: Tuple[float, float] = (12, 8),
                          show_parameters: bool = True,
                          save_path: str = None,
                          show: bool = True) -> Figure:
        """
        绘制距离剖面图（增强版）
        
        Args:
            range_profile: 距离剖面数据
            radar_model: 雷达模型
            detections: 检测点列表
            cfar_threshold: CFAR门限
            timestamp: 时间戳
            title: 图标题
            figsize: 图形尺寸
            show_parameters: 是否显示参数
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
        ax.set_xlabel('距离 (km)', fontsize=12)
        ax.set_ylabel('功率 (dB)', fontsize=12)
        
        # 设置标题
        if title is None:
            title = f"距离剖面图\n雷达: {getattr(radar_model, 'name', '未知')} | 时间: {timestamp:.2f}s"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # 添加图例
        ax.legend(fontsize=10)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 设置Y轴范围（动态调整）
        y_min = np.min(range_profile) - 5
        y_max = np.max(range_profile) + 5
        ax.set_ylim(y_min, y_max)
        
        # 添加雷达参数
        if show_parameters:
            params = self._extract_radar_parameters(radar_model)
            self._add_parameter_textbox(ax, params, 'upper right')
            
            # 添加距离分辨率信息
            range_res = self._calculate_range_resolution(radar_model)
            ax.text(0.02, 0.98, f"距离分辨率: {range_res:.1f} m", 
                   transform=ax.transAxes, fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
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
    
    def _calculate_range_resolution(self, radar_model: RadarModel) -> float:
        """计算距离分辨率"""
        if not radar_model.transmitter:
            return 150.0  # 默认值
        
        bandwidth = getattr(radar_model.transmitter, 'bandwidth_hz', 1e6)
        return 3e8 / (2 * bandwidth)  # 距离分辨率(m)
    
    def plot_doppler_profile(self, doppler_profile: np.ndarray,
                           radar_model: RadarModel,
                           detections: List[RadarDetection] = None, # type: ignore
                           cfar_threshold: np.ndarray = None, # type: ignore
                           timestamp: float = 0.0,
                           title: str = None, # type: ignore
                           figsize: Tuple[float, float] = (12, 8),
                           show_parameters: bool = True,
                           save_path: str = None, # type: ignore
                           show: bool = True) -> Figure:
        """
        绘制多普勒剖面图（增强版）
        
        Args:
            doppler_profile: 多普勒剖面数据
            radar_model: 雷达模型
            detections: 检测点列表
            cfar_threshold: CFAR门限
            timestamp: 时间戳
            title: 图标题
            figsize: 图形尺寸
            show_parameters: 是否显示参数
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
        ax.set_xlabel('速度 (m/s)', fontsize=12)
        ax.set_ylabel('功率 (dB)', fontsize=12)
        
        # 设置标题
        if title is None:
            title = f"多普勒剖面图\n雷达: {getattr(radar_model, 'name', '未知')} | 时间: {timestamp:.2f}s"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # 添加图例
        ax.legend(fontsize=10)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 设置Y轴范围（动态调整）
        y_min = np.min(doppler_profile) - 5
        y_max = np.max(doppler_profile) + 5
        ax.set_ylim(y_min, y_max)
        
        # 添加雷达参数
        if show_parameters:
            params = self._extract_radar_parameters(radar_model)
            self._add_parameter_textbox(ax, params, 'upper right')
            
            # 添加速度分辨率信息
            vel_res = self._calculate_velocity_resolution(radar_model)
            ax.text(0.02, 0.98, f"速度分辨率: {vel_res:.1f} m/s", 
                   transform=ax.transAxes, fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
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
    
    def _calculate_velocity_resolution(self, radar_model: RadarModel) -> float:
        """计算速度分辨率"""
        if not radar_model.transmitter:
            return 1.0  # 默认值
        
        fc = getattr(radar_model.transmitter, 'frequency_hz', 1e9)
        prf = getattr(radar_model.transmitter, 'prf_hz', 1000)
        n_pulses = getattr(radar_model.transmitter, 'pulses', 64)
        
        wavelength = 3e8 / fc
        doppler_res = prf / n_pulses
        return doppler_res * wavelength / 2  # 速度分辨率(m/s)
    
    def plot_antenna_pattern(self, radar_model: RadarModel,
                            pattern_type: str = "both",  # "azimuth", "elevation", "both"
                            title: str = None, # type: ignore
                            figsize: Tuple[float, float] = (14, 8),
                            show_parameters: bool = True,
                            save_path: str = None, # type: ignore
                            show: bool = True) -> Figure:
        """
        绘制天线方向图（修正版）
        
        Args:
            radar_model: 雷达模型
            pattern_type: 方向图类型 ("azimuth", "elevation", "both")
            title: 图标题
            figsize: 图形尺寸
            show_parameters: 是否显示参数
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
            # 方位角方向图 - 修正角度单位
            extension_factor = 8
            # 统一使用度数
            az_range = max(ant.azimuth_beamwidth * extension_factor, 10.0)  # 至少±10度
            az_angles = np.linspace(-az_range, az_range, 361)  # 角度数组（度）
            
            # 计算方向图，包含实际增益
            az_pattern = self._calculate_antenna_pattern(
                az_angles, ant.azimuth_beamwidth, ant.gain_dbi, include_gain=True
            )
            
            if pattern_type == "both":
                self._plot_single_antenna_pattern(
                    axs[0], az_angles, az_pattern, 
                    "方位角 (度)", f"方位角方向图\n波束宽度: {ant.azimuth_beamwidth}°",
                    peak_gain=ant.gain_dbi
                )
            else:
                self._plot_single_antenna_pattern(
                    axs[0], az_angles, az_pattern, 
                    "方位角 (度)", f"方位角方向图\n波束宽度: {ant.azimuth_beamwidth}°",
                    peak_gain=ant.gain_dbi
                )
        
        if pattern_type in ["elevation", "both"]:
            # 俯仰角方向图 - 修正角度单位
            extension_factor = 4
            el_range = max(ant.elevation_beamwidth * extension_factor, 10.0)  # 至少±10度
            el_angles = np.linspace(-el_range, el_range, 181)  # 角度数组（度）
            
            # 计算方向图，包含实际增益
            el_pattern = self._calculate_antenna_pattern(
                el_angles, ant.elevation_beamwidth, ant.gain_dbi, include_gain=True
            )
            
            if pattern_type == "both":
                self._plot_single_antenna_pattern(
                    axs[1], el_angles, el_pattern, 
                    "俯仰角 (度)", f"俯仰角方向图\n波束宽度: {ant.elevation_beamwidth}°",
                    peak_gain=ant.gain_dbi
                )
            else:
                self._plot_single_antenna_pattern(
                    axs[0], el_angles, el_pattern, 
                    "俯仰角 (度)", f"俯仰角方向图\n波束宽度: {ant.elevation_beamwidth}°",
                    peak_gain=ant.gain_dbi
                )
        
        # 设置总标题
        if title is None:
            title = f"天线方向图 - {radar_model.name}\n增益: {ant.gain_dbi:.1f} dBi"
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.95)
        
        # 添加雷达参数
        if show_parameters:
            params = self._extract_radar_parameters(radar_model)
            self._add_mini_parameter_table(fig, params, (0.02, 0.02))
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
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
                                beamwidth: float, gain: float, 
                                include_gain: bool = True) -> np.ndarray:
        """
        计算天线方向图（修正版）
        
        Args:
            angles: 角度数组（度）
            beamwidth: 波束宽度（度）
            gain: 天线峰值增益（dBi）
            include_gain: 是否包含天线增益
            
        Returns:
            方向图数据（dB）
        """
        # 转换为弧度进行计算
        angles_rad = np.radians(angles)
        beamwidth_rad = np.radians(beamwidth)
        
        # 使用改进的sinc函数模型
        pattern_linear = np.sinc(angles_rad / beamwidth_rad)**2
        
        if include_gain:
            # 包含天线实际增益
            pattern_db = gain + 10 * np.log10(pattern_linear + 1e-12)
        else:
            # 归一化方向图（峰值0dB）
            pattern_db = 10 * np.log10(pattern_linear + 1e-12)
        
        return pattern_db

    def _plot_single_antenna_pattern(self, ax: Axes, angles: np.ndarray,
                                pattern: np.ndarray, xlabel: str, 
                                title: str, peak_gain: float):
        """
        绘制单个方向图（修正版）
        
        Args:
            ax: 坐标轴对象
            angles: 角度数组（度）
            pattern: 方向图数据（dB）
            xlabel: X轴标签
            title: 子图标题
            peak_gain: 峰值增益（dBi）
        """
        # 绘制方向图
        ax.plot(angles, pattern, 'b-', linewidth=2, label='方向图')
        
        # 精确计算-3dB点
        half_power_level = peak_gain - 3
        
        # 找到所有-3dB点
        above_half_power = pattern >= half_power_level
        half_power_indices = np.where(above_half_power)[0]
        
        if len(half_power_indices) > 0:
            # 找到第一个和最后一个-3dB点
            first_index = half_power_indices[0]
            last_index = half_power_indices[-1]
            beamwidth_angle = angles[last_index] - angles[first_index]
            
            # 标记-3dB点水平线
            ax.axhline(y=half_power_level, color='r', linestyle='--', alpha=0.7, 
                    label=f'-3dB点')
            
            # 标记波束宽度垂直线
            ax.axvline(x=angles[first_index], color='g', linestyle=':', alpha=0.5, 
                    label=f'波束宽度: {beamwidth_angle:.1f}°')
            ax.axvline(x=angles[last_index], color='g', linestyle=':', alpha=0.5)
            
            # 在图中添加波束宽度文本
            ax.text(0.05, 0.95, f'波束宽度: {beamwidth_angle:.1f}°', 
                    transform=ax.transAxes, fontsize=10, 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # 标记峰值增益
        ax.axhline(y=peak_gain, color='orange', linestyle='--', alpha=0.5, 
                label=f'峰值增益: {peak_gain:.1f} dBi')
        
        # 设置坐标轴
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel('增益 (dBi)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 智能设置Y轴范围
        y_min = max(np.min(pattern) - 5, peak_gain - 50)  # 确保显示足够的动态范围
        y_max = peak_gain + 3
        ax.set_ylim(y_min, y_max)
        
        # 添加图例（限制图例项数量）
        ax.legend(loc='lower center', fontsize=9, ncol=2)
        
        # 添加0度参考线（天线指向方向）
        ax.axvline(x=0, color='k', linestyle='-', alpha=0.3, linewidth=0.5)
    
    def plot_detection_results(self, results: SimulationResults,
                             radar_id: str = None,
                             time_range: Tuple[float, float] = None,
                             plot_type: str = "all",  # "range", "doppler", "snr", "all"
                             figsize: Tuple[float, float] = (16, 12),
                             show_parameters: bool = True,
                             save_path: str = None,
                             show: bool = True) -> Figure:
        """
        绘制检测结果统计图（增强版）
        
        Args:
            results: 仿真结果
            radar_id: 雷达ID（None表示所有雷达）
            time_range: 时间范围 (开始, 结束)
            plot_type: 绘图类型
            figsize: 图形尺寸
            show_parameters: 是否显示参数
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
        fig.suptitle(f"检测结果统计{radar_info}{time_info}", fontsize=16, fontweight='bold')
        
        # 添加雷达参数
        if show_parameters and results.parameters.radars:
            # 获取第一个雷达的参数
            first_radar = results.parameters.radars[0]
            params = self._extract_radar_parameters(first_radar)
            
            # 添加检测统计
            stats_text = f"总检测数: {len(detections)}\n平均SNR: {np.mean(snrs):.1f} dB"
            fig.text(0.02, 0.02, stats_text, fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8),
                    transform=fig.transFigure)
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
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
    
    def _plot_detection_range(self, ax: Axes, timestamps: List[float],
                            ranges: List[float], title: str):
        """绘制距离随时间变化图"""
        ax.scatter(timestamps, ranges, c='blue', alpha=0.6, s=20)
        ax.set_xlabel('时间 (s)', fontsize=12)
        ax.set_ylabel('距离 (m)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 添加统计信息
        if ranges:
            avg_range = np.mean(ranges)
            ax.axhline(y=avg_range, color='red', linestyle='--', 
                      label=f'平均距离: {avg_range:.0f} m')
            ax.legend()
    
    def _plot_detection_doppler(self, ax: Axes, timestamps: List[float],
                              dopplers: List[float], title: str):
        """绘制速度随时间变化图"""
        ax.scatter(timestamps, dopplers, c='red', alpha=0.6, s=20)
        ax.set_xlabel('时间 (s)', fontsize=12)
        ax.set_ylabel('速度 (m/s)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 添加统计信息
        if dopplers:
            avg_doppler = np.mean(dopplers)
            ax.axhline(y=avg_doppler, color='blue', linestyle='--', 
                      label=f'平均速度: {avg_doppler:.1f} m/s')
            ax.legend()
    
    def _plot_detection_snr(self, ax: Axes, timestamps: List[float],
                          snrs: List[float], title: str):
        """绘制信噪比随时间变化图"""
        ax.scatter(timestamps, snrs, c='green', alpha=0.6, s=20)
        ax.set_xlabel('时间 (s)', fontsize=12)
        ax.set_ylabel('信噪比 (dB)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 添加统计信息
        if snrs:
            avg_snr = np.mean(snrs)
            ax.axhline(y=avg_snr, color='red', linestyle='--', 
                      label=f'平均SNR: {avg_snr:.1f} dB')
            ax.legend()
    
    def _plot_detection_confidence(self, ax: Axes, timestamps: List[float],
                                 confidences: List[float], title: str):
        """绘制置信度随时间变化图"""
        ax.scatter(timestamps, confidences, c='purple', alpha=0.6, s=20)
        ax.set_xlabel('时间 (s)', fontsize=12)
        ax.set_ylabel('检测置信度', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1.0)
        ax.grid(True, alpha=0.3)
        
        # 添加统计信息
        if confidences:
            avg_confidence = np.mean(confidences)
            ax.axhline(y=avg_confidence, color='red', linestyle='--',
                      label=f'平均置信度: {avg_confidence:.2f}')
            ax.legend()

    def _extract_radar_parameters(self, radar_model: RadarModel) -> Dict[str, Any]:
        """
        提取雷达模型的关键参数（增强版）
        
        Args:
            radar_model: 雷达模型
            
        Returns:
            参数字典
        """
        params = {
            '基本信息': {},
            '发射机参数': {},
            '接收机参数': {},
            '天线参数': {},
            '信号处理参数': {},
            '性能指标': {}
        }
        
        # 基本信息
        params['基本信息'] = {
            '雷达名称': getattr(radar_model, 'name', '未知'),
            '雷达型号': getattr(radar_model, 'model', '未知'),
            '工作频段': getattr(radar_model, 'band', RadarBand.S.value) if hasattr(radar_model, 'band') else '未知',
            '雷达ID': getattr(radar_model, 'radar_id', '未知')
        }
        
        # 发射机参数
        if radar_model.transmitter:
            tx = radar_model.transmitter
            params['发射机参数'] = {
                '频率': f"{getattr(tx, 'frequency_hz', 0)/1e9:.2f} GHz",
                '带宽': f"{getattr(tx, 'bandwidth_hz', 0)/1e6:.1f} MHz",
                '峰值功率': f"{getattr(tx, 'power_w', 0)/1e3:.1f} kW",
                '脉冲宽度': f"{getattr(tx, 'pulse_width_s', 0)*1e6:.1f} μs",
                'PRF': f"{getattr(tx, 'prf_hz', 0)/1e3:.1f} kHz",
                '脉冲数': getattr(tx, 'pulses', 1)
            }
        
        # 接收机参数
        if radar_model.receiver:
            rx = radar_model.receiver
            params['接收机参数'] = {
                '采样率': f"{getattr(rx, 'sampling_rate_hz', 0)/1e6:.1f} MHz",
                '噪声系数': f"{getattr(rx, 'noise_figure_db', 0):.1f} dB",
                '动态范围': f"{getattr(rx, 'dynamic_range_db', 0):.1f} dB",
                'RF增益': f"{getattr(rx, 'rf_gain_dbi', 0):.1f} dB"
            }
        
        # 天线参数
        if radar_model.antenna:
            ant = radar_model.antenna
            params['天线参数'] = {
                '增益': f"{getattr(ant, 'gain_dbi', 0):.1f} dBi",
                '方位波束宽度': f"{getattr(ant, 'azimuth_beamwidth', 0):.1f}°",
                '俯仰波束宽度': f"{getattr(ant, 'elevation_beamwidth', 0):.1f}°",
                '极化方式': getattr(ant, 'polarization', '未知')
            }
        
        # 信号处理参数
        if radar_model.signal_processing:
            sp = radar_model.signal_processing
            params['信号处理参数'] = {
                '距离单元数': getattr(sp, 'range_cells', 0),
                '多普勒单元数': getattr(sp, 'doppler_cells', 0),
                'CFAR类型': getattr(sp, 'cfar_method', 'CA'),
                'CFAR虚警概率': f"{getattr(sp, 'cfar_pfa', 1e-6):.1e}"
            }
        
        # 性能指标
        params['性能指标'] = self._calculate_performance_metrics(radar_model)
        
        return params
    
    def _calculate_performance_metrics(self, radar_model: RadarModel) -> Dict[str, str]:
        """计算雷达性能指标"""
        metrics = {}
        
        # 距离分辨率
        if radar_model.transmitter:
            bandwidth = getattr(radar_model.transmitter, 'bandwidth_hz', 1e6)
            range_res = 3e8 / (2 * bandwidth)
            metrics['距离分辨率'] = f"{range_res:.1f} m"
        
        # 最大不模糊距离
        if radar_model.transmitter:
            prf = getattr(radar_model.transmitter, 'prf_hz', 1000)
            max_unambiguous_range = 3e8 / (2 * prf)
            metrics['最大不模糊距离'] = f"{max_unambiguous_range/1000:.1f} km"
        
        # 速度分辨率
        if radar_model.transmitter and radar_model.antenna:
            fc = getattr(radar_model.transmitter, 'frequency_hz', 1e9)
            prf = getattr(radar_model.transmitter, 'prf_hz', 1000)
            n_pulses = getattr(radar_model.transmitter, 'pulses', 64)
            wavelength = 3e8 / fc
            doppler_res = prf / n_pulses
            vel_res = doppler_res * wavelength / 2
            metrics['速度分辨率'] = f"{vel_res:.2f} m/s"
        
        # 最大不模糊速度
        if radar_model.transmitter and radar_model.antenna:
            fc = getattr(radar_model.transmitter, 'frequency_hz', 1e9)
            prf = getattr(radar_model.transmitter, 'prf_hz', 1000)
            wavelength = 3e8 / fc
            max_unambiguous_vel = prf * wavelength / 4
            metrics['最大不模糊速度'] = f"{max_unambiguous_vel:.1f} m/s"
        
        return metrics

    def plot_comprehensive_analysis(self, results: SimulationResults,
                                  radar_id: str = None,
                                  save_dir: str = None,
                                  show: bool = True) -> Dict[str, str]:
        """
        绘制综合分析图集（增强版）
        
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
        
        # 获取雷达模型
        if not results.parameters.radars:
            raise ValueError("没有雷达模型数据")
        
        radar_model = results.parameters.radars[0]  # 使用第一个雷达
        
        # 获取第一个时间步的数据作为示例
        first_radar_id = list(results.raw_data.keys())[0]
        first_timestamp = next(iter(results.raw_data[first_radar_id]))
        radar_data = results.raw_data[first_radar_id][first_timestamp]
        processed_data = radar_data['processed']
        
        # 1. 绘制距离-多普勒图
        if processed_data.get('rd_map') is not None:
            rd_save_path = os.path.join(save_dir, 'range_doppler_map.png') if save_dir else None
            self.plot_range_doppler_map(
                processed_data['rd_map'],
                radar_model,
                timestamp=first_timestamp,
                save_path=rd_save_path,
                show=show
            )
            if rd_save_path:
                saved_files['range_doppler_map'] = rd_save_path
        
        # 2. 绘制距离剖面图
        if processed_data.get('range_profile') is not None:
            range_save_path = os.path.join(save_dir, 'range_profile.png') if save_dir else None
            detections = [RadarDetection.from_dict(d) for d in radar_data['detections']]
            self.plot_range_profile(
                processed_data['range_profile'],
                radar_model,
                detections=detections,
                cfar_threshold=processed_data.get('cfar_threshold'),
                timestamp=first_timestamp,
                save_path=range_save_path,
                show=show
            )
            if range_save_path:
                saved_files['range_profile'] = range_save_path
        
        # 3. 绘制多普勒剖面图
        if processed_data.get('doppler_profile') is not None:
            doppler_save_path = os.path.join(save_dir, 'doppler_profile.png') if save_dir else None
            self.plot_doppler_profile(
                processed_data['doppler_profile'],
                radar_model,
                detections=detections,
                cfar_threshold=processed_data.get('cfar_threshold'),
                timestamp=first_timestamp,
                save_path=doppler_save_path,
                show=show
            )
            if doppler_save_path:
                saved_files['doppler_profile'] = doppler_save_path
        
        # 4. 绘制天线方向图
        if radar_model.antenna:
            antenna_save_path = os.path.join(save_dir, 'antenna_pattern.png') if save_dir else None
            self.plot_antenna_pattern(
                radar_model,
                pattern_type="both",
                save_path=antenna_save_path,
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
                save_path=detection_save_path,
                show=show
            )
            if detection_save_path:
                saved_files['detection_results'] = detection_save_path
        
        # 6. 绘制雷达参数汇总图
        param_save_path = os.path.join(save_dir, 'radar_parameters.png') if save_dir else None
        self.plot_radar_parameters_summary(
            radar_model,
            save_path=param_save_path,
            show=show
        )
        if param_save_path:
            saved_files['radar_parameters'] = param_save_path
        
        return saved_files

    def plot_radar_parameters_summary(self, radar_model: RadarModel,
                                    title: str = None,
                                    figsize: Tuple[float, float] = (12, 8),
                                    save_path: str = None,
                                    show: bool = True) -> Figure:
        """
        绘制雷达参数汇总图
        
        Args:
            radar_model: 雷达模型
            title: 图标题
            figsize: 图形尺寸
            save_path: 保存路径
            show: 是否显示图形
            
        Returns:
            matplotlib图形对象
        """
        # 创建图形
        fig, ax = plt.subplots(figsize=figsize)
        
        # 提取参数
        params = self._extract_radar_parameters(radar_model)
        
        # 生成参数文本
        param_text = "雷达参数汇总\n"
        param_text += "=" * 30 + "\n\n"
        
        for category, category_params in params.items():
            if category_params:  # 只添加非空类别
                param_text += f"【{category}】\n"
                for key, value in category_params.items():
                    param_text += f"  {key}: {value}\n"
                param_text += "\n"
        
        # 隐藏坐标轴
        ax.axis('off')
        
        # 添加参数文本
        ax.text(0.05, 0.95, param_text, transform=ax.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
        # 设置标题
        if title is None:
            title = f"雷达参数汇总 - {getattr(radar_model, 'name', '未知雷达')}"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
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
        fig_id = f"radar_parameters_{datetime.now().strftime('%H%M%S')}"
        self.figures[fig_id] = fig
        
        return fig

    def _calculate_rd_axes(self, rd_map: np.ndarray, radar_model: RadarModel) -> Tuple[np.ndarray, np.ndarray]:
        """计算距离-多普勒图的坐标轴"""
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

    def _calculate_range_axis(self, range_profile: np.ndarray,
                            radar_model: RadarModel) -> np.ndarray:
        """计算距离轴"""
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

    def _calculate_doppler_axis(self, doppler_profile: np.ndarray,
                              radar_model: RadarModel) -> np.ndarray:
        """计算多普勒轴"""
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
    def _filter_detections(self, detections: List[RadarDetection],
                         radar_id: str = None,
                         time_range: Tuple[float, float] = None) -> List[RadarDetection]:
        """过滤检测数据"""
        filtered = detections
        
        # 按雷达ID过滤
        if radar_id is not None:
            filtered = [d for d in filtered if d.radar_id == radar_id]
        
        # 按时间范围过滤
        if time_range is not None:
            t_start, t_end = time_range
            filtered = [d for d in filtered if t_start <= d.timestamp <= t_end]
        
        return filtered

    def save_all_figures(self, save_dir: str = "radar_plots"):
        """保存所有生成的图形"""
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


# 使用示例
if __name__ == "__main__":
    # 创建增强版绘图器实例
    plotter = EnhancedRadarPlotter()
    
    # 创建模拟雷达模型
    class MockRadarModel:
        def __init__(self):
            self.name = "JY-27B UHF雷达"
            self.model = "JY-27B"
            self.radar_id = "JY-27B_UHF001"
            self.band = RadarBand.UHF
            self.transmitter = MockTransmitter()
            self.receiver = MockReceiver()
            self.antenna = MockAntenna()
            self.signal_processing = MockSignalProcessing()
    
    class MockTransmitter:
        def __init__(self):
            self.frequency_hz = 450e6  # 450MHz
            self.bandwidth_hz = 10e6   # 10MHz
            self.power_w = 100e3       # 100kW
            self.pulse_width_s = 100e-6  # 100μs
            self.prf_hz = 1000         # 1kHz
            self.pulses = 64
    
    class MockReceiver:
        def __init__(self):
            self.sampling_rate_hz = 20e6  # 20MHz
            self.noise_figure_db = 3.0    # 3dB
            self.dynamic_range_db = 80.0  # 80dB
            self.rf_gain_dbi = 30.0       # 30dB
    
    class MockAntenna:
        def __init__(self):
            self.gain_dbi = 25.0           # 25dBi
            self.azimuth_beamwidth = 10.0  # 10°
            self.elevation_beamwidth = 20.0  # 20°
            self.polarization = "水平极化"
    
    class MockSignalProcessing:
        def __init__(self):
            self.range_cells = 256
            self.doppler_cells = 64
            self.cfar_method = "CA"
            self.cfar_pfa = 1e-6
    
    mock_radar = MockRadarModel()
    
    # 生成模拟数据
    # 距离-多普勒图 (64x256)
    rd_map = np.random.randn(64, 256) * 8 + 50
    rd_map[30:35, 120:130] += 30  # 添加目标
    
    # 距离剖面
    range_profile = np.random.randn(256) * 5 + 20
    range_profile[120:130] += 15  # 添加目标
    
    # 多普勒剖面
    doppler_profile = np.random.randn(64) * 5 + 15
    doppler_profile[30:35] += 10  # 添加目标
    
    # 绘制各种图形
    try:
        print("=== 增强版雷达图绘制模块演示 ===")
        
        # 1. 绘制距离-多普勒图
        print("1. 绘制距离-多普勒图...")
        plotter.plot_range_doppler_map(rd_map, mock_radar, title="JY-27B雷达距离-多普勒图")
        
        # 2. 绘制距离剖面图
        print("2. 绘制距离剖面图...")
        plotter.plot_range_profile(range_profile, mock_radar, title="JY-27B雷达距离剖面图")
        
        # 3. 绘制多普勒剖面图
        print("3. 绘制多普勒剖面图...")
        plotter.plot_doppler_profile(doppler_profile, mock_radar, title="JY-27B雷达多普勒剖面图")
        
        # 4. 绘制天线方向图
        print("4. 绘制天线方向图...")
        plotter.plot_antenna_pattern(mock_radar, title="JY-27B雷达天线方向图")
        
        # 5. 绘制雷达参数汇总图
        print("5. 绘制雷达参数汇总图...")
        plotter.plot_radar_parameters_summary(mock_radar, title="JY-27B雷达参数汇总")
        
        print("所有图形绘制完成！")
        
        # 保存所有图形
        saved_files = plotter.save_all_figures("enhanced_demo_plots")
        print(f"保存了 {len(saved_files)} 个图形文件")
        
    except Exception as e:
        print(f"绘图演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        plotter.clear_figures()