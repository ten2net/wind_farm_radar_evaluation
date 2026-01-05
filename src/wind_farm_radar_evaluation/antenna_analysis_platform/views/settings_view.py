"""
设置视图
系统设置和配置管理
包括应用设置、用户偏好、系统信息、数据管理等
"""

import streamlit as st
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import sys
import os
import psutil
import platform
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import shutil
import tempfile
from io import StringIO, BytesIO
import zipfile
import base64

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import AppConfig
from utils.helpers import format_file_size, format_percentage, format_timestamp
from services.pattern_generator import get_pattern_generator_service
from services.analysis_service import get_analysis_service
from services.visualization_service import get_visualization_service

class SettingsView:
    """设置视图类"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.pattern_service = get_pattern_generator_service()
        self.analysis_service = get_analysis_service()
        self.viz_service = get_visualization_service()
        self.load_settings()
    
    def load_settings(self):
        """加载设置"""
        try:
            config_dir = Path(__file__).parent.parent / "config"
            settings_file = config_dir / "user_settings.yaml"
            
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.settings = yaml.safe_load(f) or {}
            else:
                self.settings = self._create_default_settings()
                
                # 保存默认设置
                config_dir.mkdir(parents=True, exist_ok=True)
                with open(settings_file, 'w', encoding='utf-8') as f:
                    yaml.dump(self.settings, f, default_flow_style=False, allow_unicode=True)
                    
        except Exception as e:
            st.error(f"加载设置失败: {e}")
            self.settings = self._create_default_settings()
    
    def _create_default_settings(self) -> Dict[str, Any]:
        """创建默认设置"""
        return {
            'application': {
                'name': '天线分析平台',
                'version': '1.0.0',
                'theme': 'light',
                'language': 'zh-CN',
                'auto_save': True,
                'save_interval': 5,  # 分钟
                'max_history': 50,
                'cache_enabled': True,
                'cache_size': 100,  # MB
                'log_level': 'INFO'
            },
            'simulation': {
                'default_generator': 'analytical',
                'default_theta_res': 5,
                'default_phi_res': 5,
                'default_component': 'total',
                'auto_normalize': True,
                'add_noise': False,
                'noise_level': -30,  # dB
                'interpolation': True,
                'interpolation_factor': 2
            },
            'visualization': {
                'theme': 'plotly_white',
                'color_theme': 'viridis',
                'default_width': 800,
                'default_height': 600,
                'show_grid': True,
                'show_legend': True,
                'show_title': True,
                'annotate_peaks': True,
                'font_size': 12,
                'dpi': 150
            },
            'analysis': {
                'default_beamwidth_levels': ['3dB', '10dB'],
                'find_nulls': True,
                'find_sidelobes': True,
                'calculate_axial_ratio': True,
                'calculate_efficiency': True,
                'performance_thresholds': {
                    'good': 0.8,
                    'fair': 0.6,
                    'poor': 0.4
                }
            },
            'export': {
                'default_format': 'PNG',
                'default_dpi': 300,
                'include_metadata': True,
                'compress_exports': True,
                'auto_open_folder': False
            },
            'data_management': {
                'auto_backup': True,
                'backup_interval': 24,  # 小时
                'max_backups': 10,
                'data_retention_days': 30,
                'cleanup_old_data': True
            },
            'user': {
                'name': '用户',
                'organization': '',
                'department': '',
                'email': '',
                'notifications': True,
                'newsletter': False
            },
            'system': {
                'last_update_check': None,
                'update_channel': 'stable',
                'auto_check_updates': True,
                'send_usage_stats': False,
                'send_crash_reports': False
            }
        }
    
    def save_settings(self):
        """保存设置"""
        try:
            config_dir = Path(__file__).parent.parent / "config"
            settings_file = config_dir / "user_settings.yaml"
            
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.settings, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            st.error(f"保存设置失败: {e}")
            return False
    
    def render(self, sidebar_config: Dict[str, Any]):
        """渲染设置视图"""
        st.title("⚙️ 系统设置")
        
        # 创建设置标签页
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🏠 应用设置", 
            "📊 仿真设置", 
            "📈 可视化设置",
            "🔍 分析设置",
            "💾 数据管理",
            "👤 用户设置",
            "🖥️ 系统信息"
        ])
        
        with tab1:
            self._render_application_settings()
        
        with tab2:
            self._render_simulation_settings()
        
        with tab3:
            self._render_visualization_settings()
        
        with tab4:
            self._render_analysis_settings()
        
        with tab5:
            self._render_data_management()
        
        with tab6:
            self._render_user_settings()
        
        with tab7:
            self._render_system_info()
        
        # 底部操作栏
        self._render_settings_actions()
    
    def _render_application_settings(self):
        """渲染应用设置"""
        st.markdown("## 🏠 应用设置")
        
        with st.form("application_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 外观设置")
                
                self.settings['application']['theme'] = st.selectbox(
                    "主题",
                    ["light", "dark", "auto"],
                    index=["light", "dark", "auto"].index(
                        self.settings['application'].get('theme', 'light')
                    ),
                    help="选择应用主题风格"
                )
                
                self.settings['application']['language'] = st.selectbox(
                    "语言",
                    ["zh-CN", "en-US"],
                    index=["zh-CN", "en-US"].index(
                        self.settings['application'].get('language', 'zh-CN')
                    ),
                    help="选择界面语言"
                )
            
            with col2:
                st.markdown("### 自动保存")
                
                self.settings['application']['auto_save'] = st.checkbox(
                    "启用自动保存",
                    value=self.settings['application'].get('auto_save', True),
                    help="自动保存工作进度"
                )
                
                if self.settings['application']['auto_save']:
                    self.settings['application']['save_interval'] = st.slider(
                        "保存间隔 (分钟)",
                        min_value=1,
                        max_value=60,
                        value=self.settings['application'].get('save_interval', 5),
                        help="自动保存的时间间隔"
                    )
            
            st.markdown("### 历史记录")
            
            col1, col2 = st.columns(2)
            
            with col1:
                self.settings['application']['max_history'] = st.number_input(
                    "最大历史记录数",
                    min_value=10,
                    max_value=1000,
                    value=self.settings['application'].get('max_history', 50),
                    help="保存的历史记录最大数量"
                )
            
            with col2:
                self.settings['application']['cache_enabled'] = st.checkbox(
                    "启用缓存",
                    value=self.settings['application'].get('cache_enabled', True),
                    help="启用缓存以提高性能"
                )
                
                if self.settings['application']['cache_enabled']:
                    self.settings['application']['cache_size'] = st.slider(
                        "缓存大小 (MB)",
                        min_value=10,
                        max_value=1000,
                        value=self.settings['application'].get('cache_size', 100),
                        help="最大缓存大小"
                    )
            
            st.markdown("### 日志设置")
            
            self.settings['application']['log_level'] = st.selectbox(
                "日志级别",
                ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                    self.settings['application'].get('log_level', 'INFO')
                ),
                help="设置日志记录级别"
            )
            
            # 保存按钮
            if st.form_submit_button("💾 保存应用设置", width='stretch', type="primary"):
                if self.save_settings():
                    st.success("应用设置已保存")
                else:
                    st.error("保存失败")
    
    def _render_simulation_settings(self):
        """渲染仿真设置"""
        st.markdown("## 📊 仿真设置")
        
        with st.form("simulation_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 默认仿真参数")
                
                self.settings['simulation']['default_generator'] = st.selectbox(
                    "默认方向图生成器",
                    ["analytical", "numerical", "radarsimpy"],
                    index=["analytical", "numerical", "radarsimpy"].index(
                        self.settings['simulation'].get('default_generator', 'analytical')
                    ),
                    help="选择默认的方向图生成算法"
                )
                
                self.settings['simulation']['default_theta_res'] = st.slider(
                    "默认Theta分辨率 (°)",
                    min_value=1,
                    max_value=20,
                    value=self.settings['simulation'].get('default_theta_res', 5),
                    help="俯仰角方向采样分辨率"
                )
            
            with col2:
                st.markdown("### 默认场分量")
                
                self.settings['simulation']['default_component'] = st.selectbox(
                    "默认场分量",
                    ["total", "theta", "phi", "co_polar", "cross_polar"],
                    index=["total", "theta", "phi", "co_polar", "cross_polar"].index(
                        self.settings['simulation'].get('default_component', 'total')
                    ),
                    help="选择默认分析的场分量"
                )
                
                self.settings['simulation']['default_phi_res'] = st.slider(
                    "默认Phi分辨率 (°)",
                    min_value=1,
                    max_value=20,
                    value=self.settings['simulation'].get('default_phi_res', 5),
                    help="方位角方向采样分辨率"
                )
            
            st.markdown("### 处理选项")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                self.settings['simulation']['auto_normalize'] = st.checkbox(
                    "自动归一化",
                    value=self.settings['simulation'].get('auto_normalize', True),
                    help="自动将方向图归一化到峰值增益"
                )
            
            with col2:
                self.settings['simulation']['add_noise'] = st.checkbox(
                    "添加噪声",
                    value=self.settings['simulation'].get('add_noise', False),
                    help="在方向图中添加随机噪声模拟测量误差"
                )
                
                if self.settings['simulation']['add_noise']:
                    self.settings['simulation']['noise_level'] = st.slider(
                        "噪声水平 (dB)",
                        min_value=-50,
                        max_value=-10,
                        value=self.settings['simulation'].get('noise_level', -30)
                    )
            
            with col3:
                self.settings['simulation']['interpolation'] = st.checkbox(
                    "启用插值",
                    value=self.settings['simulation'].get('interpolation', True),
                    help="对方向图进行插值以获得平滑结果"
                )
                
                if self.settings['simulation']['interpolation']:
                    self.settings['simulation']['interpolation_factor'] = st.slider(
                        "插值因子",
                        min_value=1,
                        max_value=5,
                        value=self.settings['simulation'].get('interpolation_factor', 2)
                    )
            
            # 保存按钮
            if st.form_submit_button("💾 保存仿真设置", width='stretch', type="primary"):
                if self.save_settings():
                    st.success("仿真设置已保存")
                else:
                    st.error("保存失败")
    
    def _render_visualization_settings(self):
            """渲染可视化设置"""
            st.markdown("## 📈 可视化设置")
            
            # 将表单内的按钮移到表单外部
            # 先预览按钮
            st.markdown("### 主题预览")
            
            if st.button("👁️ 预览主题", width='stretch'):
                self._preview_visualization_theme()
            
            st.markdown("---")
            
            # 可视化设置表单
            with st.form("visualization_settings"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 图表主题")
                    
                    theme_options = {
                        "plotly_white": "浅色主题",
                        "plotly_dark": "深色主题", 
                        "ggplot2": "ggplot2风格",
                        "seaborn": "Seaborn风格",
                        "simple_white": "简洁白色"
                    }
                    
                    current_theme = self.settings['visualization'].get('theme', 'plotly_white')
                    theme_index = list(theme_options.keys()).index(current_theme) if current_theme in theme_options else 0
                    
                    selected_theme = st.selectbox(
                        "图表主题",
                        list(theme_options.keys()),
                        index=theme_index,
                        format_func=lambda x: theme_options[x]
                    )
                    self.settings['visualization']['theme'] = selected_theme
                    
                    # 颜色映射
                    color_maps = ["viridis", "plasma", "inferno", "magma", "cividis", 
                                "rainbow", "jet", "hot", "cool", "portland"]
                    
                    self.settings['visualization']['color_theme'] = st.selectbox(
                        "颜色映射",
                        color_maps,
                        index=color_maps.index(
                            self.settings['visualization'].get('color_theme', 'viridis')
                        ),
                        help="选择图表颜色映射"
                    )
                
                with col2:
                    st.markdown("### 图表尺寸")
                    
                    self.settings['visualization']['default_width'] = st.number_input(
                        "默认宽度 (像素)",
                        min_value=400,
                        max_value=2000,
                        value=self.settings['visualization'].get('default_width', 800),
                        help="图表默认宽度"
                    )
                    
                    self.settings['visualization']['default_height'] = st.number_input(
                        "默认高度 (像素)",
                        min_value=300,
                        max_value=1500,
                        value=self.settings['visualization'].get('default_height', 600),
                        help="图表默认高度"
                    )
                    
                    self.settings['visualization']['dpi'] = st.selectbox(
                        "分辨率 (DPI)",
                        [72, 96, 150, 300, 600],
                        index=[72, 96, 150, 300, 600].index(
                            self.settings['visualization'].get('dpi', 150)
                        ),
                        help="图表导出分辨率"
                    )
                
                st.markdown("### 显示选项")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    self.settings['visualization']['show_grid'] = st.checkbox(
                        "显示网格",
                        value=self.settings['visualization'].get('show_grid', True)
                    )
                    
                    self.settings['visualization']['show_legend'] = st.checkbox(
                        "显示图例",
                        value=self.settings['visualization'].get('show_legend', True)
                    )
                
                with col2:
                    self.settings['visualization']['show_title'] = st.checkbox(
                        "显示标题",
                        value=self.settings['visualization'].get('show_title', True)
                    )
                    
                    self.settings['visualization']['annotate_peaks'] = st.checkbox(
                        "标注峰值点",
                        value=self.settings['visualization'].get('annotate_peaks', True)
                    )
                
                with col3:
                    self.settings['visualization']['font_size'] = st.slider(
                        "字体大小",
                        min_value=8,
                        max_value=20,
                        value=self.settings['visualization'].get('font_size', 12)
                    )
                
                # 保存按钮
                if st.form_submit_button("💾 保存可视化设置", width='stretch', type="primary"):
                    if self.save_settings():
                        st.success("可视化设置已保存")
                    else:
                        st.error("保存失败")
    
    def _preview_visualization_theme(self):
        """预览可视化主题"""
        # 创建示例图表
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("示例方向图", "示例统计图")
        )
        
        # 示例数据
        theta = np.linspace(0, 180, 37)
        pattern = 20 * np.log10(np.abs(np.sin(np.deg2rad(theta))) + 1e-10)
        
        # 方向图
        fig.add_trace(
            go.Scatter(
                x=theta, y=pattern,
                mode='lines',
                name='方向图',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # 统计图
        categories = ['增益', '波束宽度', '副瓣电平', '效率']
        values = [12.5, 24.3, -18.5, 78.2]
        
        fig.add_trace(
            go.Bar(
                x=categories, y=values,
                name='性能指标',
                marker_color=['#636efa', '#00cc96', '#ab63fa', '#ffa15a']
            ),
            row=1, col=2
        )
        
        # 应用主题
        theme = self.settings['visualization'].get('theme', 'plotly_white')
        fig.update_layout(
            template=theme,
            title="主题预览",
            width=self.settings['visualization'].get('default_width', 800),
            height=400,
            showlegend=self.settings['visualization'].get('show_legend', True),
            font=dict(size=self.settings['visualization'].get('font_size', 12))
        )
        
        # 显示图表
        st.plotly_chart(fig, width='stretch')
    
    def _render_analysis_settings(self):
        """渲染分析设置"""
        st.markdown("## 🔍 分析设置")
        
        with st.form("analysis_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 波束分析")
                
                beamwidth_options = ["3dB", "6dB", "10dB", "20dB"]
                default_levels = self.settings['analysis'].get('default_beamwidth_levels', ['3dB', '10dB'])
                
                self.settings['analysis']['default_beamwidth_levels'] = st.multiselect(
                    "波束宽度计算电平",
                    beamwidth_options,
                    default=default_levels,
                    help="计算这些电平的波束宽度"
                )
                
                self.settings['analysis']['find_nulls'] = st.checkbox(
                    "查找零陷",
                    value=self.settings['analysis'].get('find_nulls', True),
                    help="自动查找方向图中的零陷"
                )
            
            with col2:
                st.markdown("### 极化分析")
                
                self.settings['analysis']['calculate_axial_ratio'] = st.checkbox(
                    "计算轴比",
                    value=self.settings['analysis'].get('calculate_axial_ratio', True),
                    help="计算极化轴比"
                )
                
                self.settings['analysis']['find_sidelobes'] = st.checkbox(
                    "分析副瓣",
                    value=self.settings['analysis'].get('find_sidelobes', True),
                    help="自动分析副瓣特性"
                )
            
            st.markdown("### 效率分析")
            
            self.settings['analysis']['calculate_efficiency'] = st.checkbox(
                "计算效率",
                value=self.settings['analysis'].get('calculate_efficiency', True),
                help="计算天线各种效率"
            )
            
            st.markdown("### 性能评估阈值")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                self.settings['analysis']['performance_thresholds']['good'] = st.slider(
                    "优秀阈值",
                    min_value=0.5,
                    max_value=1.0,
                    value=self.settings['analysis']['performance_thresholds'].get('good', 0.8),
                    step=0.05,
                    help="性能评分达到此值为优秀"
                )
            
            with col2:
                self.settings['analysis']['performance_thresholds']['fair'] = st.slider(
                    "良好阈值",
                    min_value=0.3,
                    max_value=0.8,
                    value=self.settings['analysis']['performance_thresholds'].get('fair', 0.6),
                    step=0.05,
                    help="性能评分达到此值为良好"
                )
            
            with col3:
                self.settings['analysis']['performance_thresholds']['poor'] = st.slider(
                    "一般阈值",
                    min_value=0.1,
                    max_value=0.6,
                    value=self.settings['analysis']['performance_thresholds'].get('poor', 0.4),
                    step=0.05,
                    help="性能评分低于此值为一般"
                )
            
            # 保存按钮
            if st.form_submit_button("💾 保存分析设置", width='stretch', type="primary"):
                if self.save_settings():
                    st.success("分析设置已保存")
                else:
                    st.error("保存失败")
    
    def _render_data_management(self):
        """渲染数据管理"""
        st.markdown("## 💾 数据管理")
        
        with st.form("data_management_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 自动备份")
                
                self.settings['data_management']['auto_backup'] = st.checkbox(
                    "启用自动备份",
                    value=self.settings['data_management'].get('auto_backup', True),
                    help="自动备份重要数据"
                )
                
                if self.settings['data_management']['auto_backup']:
                    self.settings['data_management']['backup_interval'] = st.slider(
                        "备份间隔 (小时)",
                        min_value=1,
                        max_value=168,
                        value=self.settings['data_management'].get('backup_interval', 24),
                        help="自动备份的时间间隔"
                    )
            
            with col2:
                st.markdown("### 备份管理")
                
                self.settings['data_management']['max_backups'] = st.number_input(
                    "最大备份数量",
                    min_value=1,
                    max_value=100,
                    value=self.settings['data_management'].get('max_backups', 10),
                    help="保留的最大备份文件数量"
                )
                
                self.settings['data_management']['data_retention_days'] = st.number_input(
                    "数据保留天数",
                    min_value=1,
                    max_value=365,
                    value=self.settings['data_management'].get('data_retention_days', 30),
                    help="数据保留的最大天数"
                )
            
            st.markdown("### 数据清理")
            
            self.settings['data_management']['cleanup_old_data'] = st.checkbox(
                "自动清理旧数据",
                value=self.settings['data_management'].get('cleanup_old_data', True),
                help="自动清理过期的数据文件"
            )
            
            # 保存按钮
            if st.form_submit_button("💾 保存数据设置", width='stretch', type="primary"):
                if self.save_settings():
                    st.success("数据管理设置已保存")
                else:
                    st.error("保存失败")
        
        # 数据管理操作
        st.markdown("## 🛠️ 数据操作")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🗃️ 查看数据", width='stretch'):
                self._show_data_info()
        
        with col2:
            if st.button("🧹 清理缓存", width='stretch'):
                self._clear_cache()
        
        with col3:
            if st.button("📦 备份数据", width='stretch'):
                self._backup_data()
        
        with col4:
            if st.button("⚠️ 重置数据", width='stretch'):
                self._confirm_data_reset()
    
    def _show_data_info(self):
        """显示数据信息"""
        try:
            data_dir = Path(__file__).parent.parent / "data"
            
            if not data_dir.exists():
                st.warning("数据目录不存在")
                return
            
            # 计算数据统计
            total_size = 0
            file_count = 0
            folder_sizes = {}
            
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
                    file_count += 1
                    
                    # 按文件夹统计
                    rel_path = file_path.relative_to(data_dir)
                    if rel_path.parts:  # 有子目录
                        folder = rel_path.parts[0]
                        folder_sizes[folder] = folder_sizes.get(folder, 0) + file_path.stat().st_size
            
            # 显示统计信息
            st.markdown("### 📊 数据统计")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总数据量", format_file_size(total_size))
            
            with col2:
                st.metric("文件数量", file_count)
            
            with col3:
                st.metric("数据目录", str(data_dir))
            
            with col4:
                # 计算缓存大小
                cache_size = self._get_cache_size()
                st.metric("缓存大小", format_file_size(cache_size))
            
            # 文件夹大小分布
            st.markdown("### 📁 文件夹大小分布")
            
            if folder_sizes:
                folders = list(folder_sizes.keys())
                sizes = [folder_sizes[f] for f in folders]
                sizes_mb = [s / (1024 * 1024) for s in sizes]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=folders,
                        y=sizes_mb,
                        marker_color='lightblue',
                        text=[format_file_size(s) for s in sizes],
                        textposition='auto'
                    )
                ])
                
                fig.update_layout(
                    title="各文件夹数据量分布",
                    xaxis_title="文件夹",
                    yaxis_title="大小 (MB)",
                    height=300
                )
                
                st.plotly_chart(fig, width='stretch')
            
            # 最近文件
            st.markdown("### 📄 最近修改的文件")
            
            recent_files = []
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    file_path = Path(root) / file
                    recent_files.append({
                        'path': file_path.relative_to(data_dir),
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
            
            # 按修改时间排序
            recent_files.sort(key=lambda x: x['modified'], reverse=True)
            
            # 显示前10个文件
            if recent_files[:10]:
                df_recent = pd.DataFrame(recent_files[:10])
                df_recent['size'] = df_recent['size'].apply(format_file_size)
                df_recent['modified'] = df_recent['modified'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))
                
                st.dataframe(
                    df_recent[['path', 'size', 'modified']],
                    column_config={
                        'path': '文件路径',
                        'size': '大小',
                        'modified': '修改时间'
                    },
                    width='stretch',
                    hide_index=True
                )
            
        except Exception as e:
            st.error(f"获取数据信息失败: {e}")
    
    def _get_cache_size(self) -> int:
        """获取缓存大小"""
        try:
            cache_dir = Path(__file__).parent.parent / "cache"
            if not cache_dir.exists():
                return 0
            
            total_size = 0
            for file in cache_dir.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
            
            return total_size
        except:
            return 0
    
    def _clear_cache(self):
        """清理缓存"""
        try:
            cache_dir = Path(__file__).parent.parent / "cache"
            
            if cache_dir.exists():
                # 获取缓存大小
                cache_size = self._get_cache_size()
                
                # 删除缓存目录
                shutil.rmtree(cache_dir)
                
                # 重新创建空目录
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                st.success(f"已清理缓存: {format_file_size(cache_size)}")
            else:
                st.info("缓存目录不存在")
                
        except Exception as e:
            st.error(f"清理缓存失败: {e}")
    
    def _backup_data(self):
        """备份数据"""
        try:
            data_dir = Path(__file__).parent.parent / "data"
            backup_dir = Path(__file__).parent.parent / "backups"
            
            if not data_dir.exists():
                st.warning("数据目录不存在")
                return
            
            # 创建备份目录
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.zip"
            
            # 创建ZIP备份
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(data_dir.parent)
                        zipf.write(file_path, arcname)
            
            # 清理旧备份
            self._cleanup_old_backups(backup_dir)
            
            st.success(f"数据备份完成: {backup_file.name}")
            
            # 提供下载
            with open(backup_file, 'rb') as f:
                backup_data = f.read()
            
            self._download_file(backup_data, backup_file.name, "application/zip")
            
        except Exception as e:
            st.error(f"备份数据失败: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path):
        """清理旧备份"""
        try:
            max_backups = self.settings['data_management'].get('max_backups', 10)
            
            # 获取所有备份文件
            backup_files = list(backup_dir.glob("backup_*.zip"))
            
            if len(backup_files) > max_backups:
                # 按修改时间排序
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                
                # 删除最旧的文件
                files_to_delete = backup_files[:-max_backups]
                for file in files_to_delete:
                    file.unlink()
                
                st.info(f"已清理 {len(files_to_delete)} 个旧备份")
                
        except Exception as e:
            st.error(f"清理旧备份失败: {e}")
    
    def _confirm_data_reset(self):
        """确认数据重置"""
        st.warning("⚠️ 危险操作：这将删除所有用户数据")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ 确认重置", width='stretch', type="primary"):
                self._reset_data()
        
        with col2:
            if st.button("🚫 取消", width='stretch'):
                st.info("操作已取消")
    
    def _reset_data(self):
        """重置数据"""
        try:
            data_dir = Path(__file__).parent.parent / "data"
            
            if data_dir.exists():
                # 先备份
                self._backup_data()
                
                # 删除数据目录
                shutil.rmtree(data_dir)
                
                # 重新创建空目录
                data_dir.mkdir(parents=True, exist_ok=True)
                
                st.success("数据已重置")
            else:
                st.info("数据目录不存在")
                
        except Exception as e:
            st.error(f"重置数据失败: {e}")
    
    def _download_file(self, data: bytes, filename: str, mime_type: str):
        """提供文件下载"""
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">点击下载 {filename}</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    def _render_user_settings(self):
        """渲染用户设置"""
        st.markdown("## 👤 用户设置")
        
        with st.form("user_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 基本信息")
                
                self.settings['user']['name'] = st.text_input(
                    "姓名",
                    value=self.settings['user'].get('name', '用户'),
                    help="您的姓名"
                )
                
                self.settings['user']['organization'] = st.text_input(
                    "单位/组织",
                    value=self.settings['user'].get('organization', ''),
                    help="您所在的单位或组织"
                )
            
            with col2:
                st.markdown("### 联系信息")
                
                self.settings['user']['department'] = st.text_input(
                    "部门",
                    value=self.settings['user'].get('department', ''),
                    help="您所在的部门"
                )
                
                self.settings['user']['email'] = st.text_input(
                    "邮箱",
                    value=self.settings['user'].get('email', ''),
                    help="您的联系邮箱"
                )
            
            st.markdown("### 通知设置")
            
            col1, col2 = st.columns(2)
            
            with col1:
                self.settings['user']['notifications'] = st.checkbox(
                    "接收通知",
                    value=self.settings['user'].get('notifications', True),
                    help="接收系统通知和提醒"
                )
            
            with col2:
                self.settings['user']['newsletter'] = st.checkbox(
                    "订阅新闻",
                    value=self.settings['user'].get('newsletter', False),
                    help="订阅产品新闻和更新"
                )
            
            # 保存按钮
            if st.form_submit_button("💾 保存用户设置", width='stretch', type="primary"):
                if self.save_settings():
                    st.success("用户设置已保存")
                else:
                    st.error("保存失败")
    
    def _render_system_info(self):
        """渲染系统信息"""
        st.markdown("## 🖥️ 系统信息")
        
        # 应用信息
        st.markdown("### 📱 应用信息")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("应用名称", self.settings['application']['name'])
        
        with col2:
            st.metric("版本", self.settings['application']['version'])
        
        with col3:
            st.metric("Python版本", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        
        # 系统信息
        st.markdown("### 💻 系统信息")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("操作系统", platform.system())
        
        with col2:
            st.metric("处理器", platform.processor()[:20] + "...")
        
        with col3:
            memory = psutil.virtual_memory()
            st.metric("内存使用", f"{memory.percent}%")
        
        # 磁盘使用
        st.markdown("### 💾 磁盘使用")
        
        try:
            disk_usage = psutil.disk_usage('.')
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总空间", format_file_size(disk_usage.total))
            
            with col2:
                st.metric("已用空间", format_file_size(disk_usage.used))
            
            with col3:
                st.metric("可用空间", format_file_size(disk_usage.free))
            
            with col4:
                st.metric("使用率", f"{disk_usage.percent}%")
            
            # 磁盘使用进度条
            st.progress(disk_usage.percent / 100)
            
        except Exception as e:
            st.error(f"获取磁盘信息失败: {e}")
        
        # 依赖库信息
        st.markdown("### 📦 依赖库信息")
        
        try:
            import importlib.metadata
            
            dependencies = [
                'streamlit', 'numpy', 'pandas', 'plotly',
                'scipy', 'pyyaml', 'psutil'
            ]
            
            dep_info = []
            for dep in dependencies:
                try:
                    version = importlib.metadata.version(dep)
                    dep_info.append({"库": dep, "版本": version})
                except:
                    dep_info.append({"库": dep, "版本": "未安装"})
            
            df_deps = pd.DataFrame(dep_info)
            st.dataframe(df_deps, width='stretch', hide_index=True)
            
        except Exception as e:
            st.error(f"获取依赖信息失败: {e}")
        
        # 系统检查
        st.markdown("### 🔍 系统检查")
        
        if st.button("🔧 运行系统检查", width='stretch'):
            self._run_system_check()
    
    def _run_system_check(self):
        """运行系统检查"""
        try:
            checks = []
            
            # 检查Python版本
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
                checks.append(("✅", "Python版本", f"{python_version} (符合要求)"))
            else:
                checks.append(("⚠️", "Python版本", f"{python_version} (建议3.8+)"))
            
            # 检查内存
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            if memory_gb >= 4:
                checks.append(("✅", "系统内存", f"{memory_gb:.1f} GB (充足)"))
            elif memory_gb >= 2:
                checks.append(("⚠️", "系统内存", f"{memory_gb:.1f} GB (基本够用)"))
            else:
                checks.append(("❌", "系统内存", f"{memory_gb:.1f} GB (可能不足)"))
            
            # 检查磁盘空间
            disk_usage = psutil.disk_usage('.')
            free_gb = disk_usage.free / (1024**3)
            if free_gb >= 10:
                checks.append(("✅", "磁盘空间", f"{free_gb:.1f} GB (充足)"))
            elif free_gb >= 5:
                checks.append(("⚠️", "磁盘空间", f"{free_gb:.1f} GB (基本够用)"))
            else:
                checks.append(("❌", "磁盘空间", f"{free_gb:.1f} GB (可能不足)"))
            
            # 检查依赖库
            missing_deps = []
            try:
                import numpy
                checks.append(("✅", "NumPy", f"已安装 (v{numpy.__version__})"))
            except:
                missing_deps.append("NumPy")
                checks.append(("❌", "NumPy", "未安装"))
            
            try:
                import pandas
                checks.append(("✅", "Pandas", f"已安装 (v{pandas.__version__})"))
            except:
                missing_deps.append("Pandas")
                checks.append(("❌", "Pandas", "未安装"))
            
            try:
                import plotly
                checks.append(("✅", "Plotly", f"已安装 (v{plotly.__version__})"))
            except:
                missing_deps.append("Plotly")
                checks.append(("❌", "Plotly", "未安装"))
            
            # 显示检查结果
            st.markdown("#### 检查结果")
            
            for status, item, message in checks:
                st.markdown(f"{status} **{item}:** {message}")
            
            if missing_deps:
                st.error(f"缺少依赖库: {', '.join(missing_deps)}")
            
            # 总体评估
            error_count = sum(1 for c in checks if c[0] == "❌")
            warning_count = sum(1 for c in checks if c[0] == "⚠️")
            
            if error_count == 0 and warning_count == 0:
                st.success("✅ 系统检查通过，所有条件符合要求")
            elif error_count == 0:
                st.warning(f"⚠️ 系统检查基本通过，有 {warning_count} 个警告")
            else:
                st.error(f"❌ 系统检查失败，有 {error_count} 个错误，{warning_count} 个警告")
                
        except Exception as e:
            st.error(f"运行系统检查失败: {e}")
    
    def _render_settings_actions(self):
        """渲染设置操作"""
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 保存所有设置", width='stretch', type="primary"):
                if self.save_settings():
                    st.success("所有设置已保存")
                else:
                    st.error("保存失败")
        
        with col2:
            if st.button("🔄 恢复默认", width='stretch'):
                self._confirm_reset_defaults()
        
        with col3:
            if st.button("📥 导入设置", width='stretch'):
                self._import_settings()
        
        with col4:
            if st.button("📤 导出设置", width='stretch'):
                self._export_settings()
    
    def _confirm_reset_defaults(self):
        """确认恢复默认设置"""
        st.warning("⚠️ 这将恢复所有设置为默认值")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 确认恢复", width='stretch', type="primary"):
                self._reset_to_defaults()
        
        with col2:
            if st.button("🚫 取消", width='stretch'):
                st.info("操作已取消")
    
    def _reset_to_defaults(self):
        """恢复默认设置"""
        try:
            self.settings = self._create_default_settings()
            if self.save_settings():
                st.success("已恢复默认设置")
                st.rerun()
            else:
                st.error("恢复默认设置失败")
        except Exception as e:
            st.error(f"恢复默认设置失败: {e}")
    
    def _import_settings(self):
        """导入设置"""
        st.info("导入设置功能")
        
        uploaded_file = st.file_uploader(
            "选择设置文件 (YAML格式)",
            type=['yaml', 'yml']
        )
        
        if uploaded_file is not None:
            try:
                content = uploaded_file.read().decode('utf-8')
                imported_settings = yaml.safe_load(content)
                
                if isinstance(imported_settings, dict):
                    # 合并设置
                    self.settings.update(imported_settings)
                    
                    if self.save_settings():
                        st.success("设置导入成功")
                        st.rerun()
                    else:
                        st.error("保存导入的设置失败")
                else:
                    st.error("设置文件格式不正确")
                    
            except Exception as e:
                st.error(f"导入设置失败: {e}")
    
    def _export_settings(self):
        """导出设置"""
        try:
            settings_yaml = yaml.dump(self.settings, default_flow_style=False, allow_unicode=True)
            
            # 提供下载
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"antenna_analysis_settings_{timestamp}.yaml"
            
            self._download_file(
                settings_yaml.encode('utf-8'),
                filename,
                "text/yaml"
            )
            
            st.success("设置导出成功")
            
        except Exception as e:
            st.error(f"导出设置失败: {e}")

def render_settings(config: AppConfig, sidebar_config: Dict[str, Any]):
    """
    渲染设置视图的主函数
    """
    try:
        settings_view = SettingsView(config)
        settings_view.render(sidebar_config)
    except Exception as e:
        st.error(f"设置视图渲染错误: {e}")
        st.exception(e)

if __name__ == "__main__":
    # 测试代码
    config = AppConfig()
    sidebar_config = {
        'page': 'settings',
        'antenna_config': {},
        'simulation_settings': {},
        'analysis_settings': {},
        'visualization_settings': {},
        'actions': {}
    }
    
    st.set_page_config(layout="wide")
    render_settings(config, sidebar_config)