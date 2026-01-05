"""
仪表板视图
显示天线分析平台的综合信息、实时数据和关键指标
采用多列卡片式布局，支持数据可视化
"""

from enum import Enum
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional, Tuple
import datetime
import json
import yaml
from pathlib import Path
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.antenna_models import AntennaParameters, AntennaType
    from models.pattern_models import RadiationPattern, PatternStatistics
    from services.pattern_generator import get_pattern_generator_service
    from services.analysis_service import get_analysis_service
    from services.visualization_service import get_visualization_service
    from utils.config import AppConfig
    from utils.helpers import format_frequency, format_gain, format_percentage
except ImportError as e:
    st.warning(f"部分模块导入失败: {e}")

class DashboardView:
    """仪表板视图类"""
    
    def __init__(self, config=None):
        self.config = config
        self.pattern_service = None
        self.analysis_service = None
        self.viz_service = None
        
        # 尝试初始化服务
        try:
            from services.pattern_generator import get_pattern_generator_service
            from services.analysis_service import get_analysis_service
            from services.visualization_service import get_visualization_service
            self.pattern_service = get_pattern_generator_service()
            self.analysis_service = get_analysis_service()
            self.viz_service = get_visualization_service()
        except ImportError:
            pass
        
    def render(self, sidebar_config: Dict[str, Any]):
        """
        渲染仪表板
        """
        st.title("📊 天线分析仪表板")
        
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs(["概览", "实时监控", "性能分析", "数据管理"])
        
        with tab1:
            self._render_overview(sidebar_config)
        
        with tab2:
            self._render_monitoring(sidebar_config)
        
        with tab3:
            self._render_performance_analysis(sidebar_config)
        
        with tab4:
            self._render_data_management(sidebar_config)
        
        # 底部状态栏
        self._render_status_bar()
    
    def _render_overview(self, sidebar_config: Dict[str, Any]):
        """
        渲染概览页面
        """
        # 第一行：关键指标卡片
        st.markdown("### 📈 关键性能指标")
        self._render_kpi_cards()
        
        st.markdown("---")
        
        # 第二行：图表和配置
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📡 天线方向图概览")
            self._render_pattern_overview()
        
        with col2:
            st.markdown("### ⚙️ 当前配置")
            self._render_current_config(sidebar_config)
        
        # 第三行：分析结果
        st.markdown("### 🔍 分析结果摘要")
        self._render_analysis_summary()
    
    def _render_kpi_cards(self):
        """渲染关键性能指标卡片"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._create_kpi_card(
                title="峰值增益",
                value="12.5 dBi",
                delta="+1.2 dBi",
                delta_type="normal",
                icon="📶"
            )
        
        with col2:
            self._create_kpi_card(
                title="波束宽度",
                value="24.3°",
                delta="-2.1°",
                delta_type="inverse",
                icon="🎯"
            )
        
        with col3:
            self._create_kpi_card(
                title="副瓣电平",
                value="-18.5 dB",
                delta="-1.3 dB",
                delta_type="normal",
                icon="📉"
            )
        
        with col4:
            self._create_kpi_card(
                title="效率",
                value="78.2%",
                delta="+3.2%",
                delta_type="normal",
                icon="⚡"
            )
    
    def _create_kpi_card(self, title: str, value: str, delta: str = None, 
                        delta_type: str = "normal", icon: str = ""):
        """创建单个KPI卡片"""
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            {f'<div class="kpi-delta {delta_type}">{delta}</div>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # 添加CSS样式
        st.markdown("""
        <style>
        .kpi-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 20px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .kpi-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .kpi-title {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        .kpi-value {
            font-size: 1.8em;
            font-weight: bold;
            margin: 10px 0;
        }
        .kpi-delta {
            font-size: 0.9em;
            padding: 3px 8px;
            border-radius: 12px;
            display: inline-block;
        }
        .kpi-delta.normal {
            background-color: rgba(255, 255, 255, 0.2);
        }
        .kpi-delta.inverse {
            background-color: rgba(255, 255, 255, 0.2);
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_pattern_overview(self):
        """渲染方向图概览"""
        # 检查是否有方向图数据
        if 'pattern_data' in st.session_state and st.session_state.pattern_data:
            pattern = st.session_state.pattern_data
            self._render_pattern_charts(pattern)
        else:
            # 显示示例图表
            self._render_example_charts()
            
            st.info("💡 没有仿真数据，请先运行仿真")
            if st.button("🚀 运行示例仿真", type="primary"):
                self._run_example_simulation()
    
    def _render_pattern_charts(self, pattern):
        """渲染方向图图表"""
        try:
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("E面方向图", "H面方向图", "3D方向图", "轴比分布"),
                specs=[[{"type": "scatter"}, {"type": "scatter"}],
                       [{"type": "surface"}, {"type": "scatter"}]],
                vertical_spacing=0.15,
                horizontal_spacing=0.1
            )
            
            # 1. E面方向图
            if hasattr(pattern, 'get_slice'):
                e_plane_slice = pattern.get_slice(fixed_phi=0)
                fig.add_trace(
                    go.Scatter(
                        x=e_plane_slice.angles if hasattr(e_plane_slice, 'angles') else np.arange(len(e_plane_slice.values)),
                        y=e_plane_slice.values,
                        mode='lines',
                        name='E面',
                        line=dict(color='#636efa', width=2)
                    ),
                    row=1, col=1
                )
            
            # 2. H面方向图
            if hasattr(pattern, 'get_slice'):
                h_plane_slice = pattern.get_slice(fixed_theta=90)
                fig.add_trace(
                    go.Scatter(
                        x=h_plane_slice.angles if hasattr(h_plane_slice, 'angles') else np.arange(len(h_plane_slice.values)),
                        y=h_plane_slice.values,
                        mode='lines',
                        name='H面',
                        line=dict(color='#ef553b', width=2)
                    ),
                    row=1, col=2
                )
            
            # 3. 3D方向图
            if hasattr(pattern, 'theta_grid') and hasattr(pattern, 'phi_grid') and hasattr(pattern, 'gain_data'):
                theta = pattern.theta_grid
                phi = pattern.phi_grid
                gain_data = pattern.gain_data
                
                # 转换为直角坐标用于3D绘图
                theta_rad = np.deg2rad(theta)
                phi_rad = np.deg2rad(phi)
                
                x = np.outer(np.sin(theta_rad), np.cos(phi_rad)) * gain_data
                y = np.outer(np.sin(theta_rad), np.sin(phi_rad)) * gain_data
                z = np.outer(np.cos(theta_rad), np.ones_like(phi_rad)) * gain_data
                
                fig.add_trace(
                    go.Surface(
                        x=x, y=y, z=z,
                        surfacecolor=gain_data,
                        colorscale='Viridis',
                        opacity=0.8,
                        showscale=False
                    ),
                    row=2, col=1
                )
            
            # 4. 轴比分布
            if hasattr(pattern, 'axial_ratio_data'):
                ar_data = pattern.axial_ratio_data
                avg_ar = np.mean(ar_data, axis=1)
                fig.add_trace(
                    go.Scatter(
                        x=theta if 'theta' in locals() else np.arange(len(avg_ar)),
                        y=avg_ar,
                        mode='lines+markers',
                        name='轴比',
                        line=dict(color='#00cc96', width=2)
                    ),
                    row=2, col=2
                )
            
            # 更新布局
            fig.update_layout(
                height=600,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            # 更新子图布局
            fig.update_xaxes(title_text="角度 (°)", row=1, col=1)
            fig.update_xaxes(title_text="角度 (°)", row=1, col=2)
            fig.update_xaxes(title_text="Theta (°)", row=2, col=2)
            
            fig.update_yaxes(title_text="增益 (dB)", row=1, col=1)
            fig.update_yaxes(title_text="增益 (dB)", row=1, col=2)
            fig.update_yaxes(title_text="轴比 (dB)", row=2, col=2)
            
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"渲染方向图时出错: {e}")
            self._render_example_charts()
    
    def _render_example_charts(self):
        """渲染示例图表"""
        # 创建示例数据
        theta = np.linspace(0, 180, 37)
        phi = np.linspace(0, 360, 73)
        
        # 示例方向图（高斯波束）
        theta_mesh, phi_mesh = np.meshgrid(theta, phi, indexing='ij')
        
        # 主瓣
        beam_pattern = np.exp(-((theta_mesh - 90)**2 + (phi_mesh - 180)**2) / (2 * 30**2))
        
        # 添加副瓣
        sidelobes = 0.1 * np.exp(-((theta_mesh - 90)**2 + (phi_mesh - 100)**2) / (2 * 20**2))
        sidelobes += 0.1 * np.exp(-((theta_mesh - 90)**2 + (phi_mesh - 260)**2) / (2 * 20**2))
        
        pattern_total = beam_pattern + sidelobes
        pattern_db = 20 * np.log10(pattern_total + 1e-10)
        
        # 创建图表
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("E面方向图 (示例)", "3D方向图 (示例)"),
            specs=[[{"type": "scatter"}, {"type": "surface"}]]
        )
        
        # E面方向图
        e_plane = pattern_db[:, 0]
        fig.add_trace(
            go.Scatter(
                x=theta,
                y=e_plane,
                mode='lines',
                name='E面',
                line=dict(color='#636efa', width=2)
            ),
            row=1, col=1
        )
        
        # 3D方向图
        fig.add_trace(
            go.Surface(
                z=pattern_db,
                colorscale='Viridis',
                opacity=0.8,
                showscale=True
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            height=400,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _run_example_simulation(self):
        """运行示例仿真"""
        with st.spinner("正在运行示例仿真..."):
            try:
                # 使用示例天线
                from models.antenna_models import create_patch_antenna
                example_antenna = create_patch_antenna()
                
                # 生成方向图
                if self.pattern_service:
                    pattern = self.pattern_service.generate_pattern(
                        example_antenna,
                        generator_type='analytical',
                        theta_resolution=5,
                        phi_resolution=5
                    )
                else:
                    # 创建示例方向图
                    pattern = self._create_example_pattern()
                
                # 保存到session
                st.session_state.current_antenna = example_antenna
                st.session_state.pattern_data = pattern
                
                # 运行分析
                if self.analysis_service:
                    results = self.analysis_service.comprehensive_analysis(pattern, example_antenna)
                    st.session_state.analysis_results = results
                else:
                    st.session_state.analysis_results = self._create_example_analysis()
                
                st.success("示例仿真完成！")
                st.rerun()
            except Exception as e:
                st.error(f"示例仿真失败: {e}")
                # 创建模拟数据
                st.session_state.current_antenna = self._create_mock_antenna()
                st.session_state.pattern_data = self._create_example_pattern()
                st.session_state.analysis_results = self._create_example_analysis()
                st.success("使用模拟数据完成仿真！")
                st.rerun()
    
    def _create_mock_antenna(self):
        """创建模拟天线数据"""
        from dataclasses import replace
        from models.antenna_models import create_patch_antenna
        
        return create_patch_antenna("模拟天线")
    
    def _create_example_pattern(self):
        """创建示例方向图"""
        class MockPattern:
            def __init__(self):
                self.theta_grid = np.linspace(0, 180, 37)
                self.phi_grid = np.linspace(0, 360, 73)
                self.gain_data = np.random.randn(37, 73) + 10
                
            def get_slice(self, fixed_phi=None, fixed_theta=None):
                class Slice:
                    def __init__(self, angles, values):
                        self.angles = angles
                        self.values = values
                
                if fixed_phi is not None:
                    return Slice(self.theta_grid, self.gain_data[:, fixed_phi % 73])
                elif fixed_theta is not None:
                    return Slice(self.phi_grid, self.gain_data[fixed_theta % 37, :])
                return Slice([], [])
        
        return MockPattern()
    
    def _create_example_analysis(self):
        """创建示例分析结果"""
        return {
            'beam': {
                'beam_parameters': {
                    'peak_gain': 12.5,
                    'main_lobe_width_3db_e': 24.3,
                    'main_lobe_width_3db_h': 28.1
                },
                'sidelobes': {
                    'max_sidelobe_level_e': -18.5,
                    'max_sidelobe_level_h': -20.2
                }
            },
            'efficiency': {
                'efficiency_parameters': {
                    'total_efficiency': 0.782
                }
            },
            'overall_assessment': {
                'performance_score': 0.85,
                'strengths': ['增益较高', '波束对称性好'],
                'recommendations': ['优化副瓣电平', '提高效率']
            }
        }
    
    def _render_current_config(self, sidebar_config: Dict[str, Any]):
        """渲染当前配置"""
        config_data = {}
        
        # 从session state获取当前配置，添加空值检查
        if 'current_antenna' in st.session_state and st.session_state.current_antenna is not None:
            antenna = st.session_state.current_antenna
            try:
                config_data['天线名称'] = antenna.name
                config_data['天线类型'] = getattr(antenna, 'antenna_type', '未知')
                if isinstance(config_data['天线类型'], Enum):
                    config_data['天线类型'] = config_data['天线类型'].value
                config_data['中心频率'] = f"{getattr(antenna, 'center_frequency', 0)} GHz"
                config_data['增益'] = f"{getattr(antenna, 'gain', 0)} dBi"
            except AttributeError as e:
                st.warning(f"获取天线属性时出错: {e}")
        
        # 从侧边栏配置获取
        if 'simulation_settings' in sidebar_config:
            sim_settings = sidebar_config['simulation_settings']
            config_data['仿真算法'] = sim_settings.get('generator_type', 'analytical')
            config_data['Theta分辨率'] = f"{sim_settings.get('theta_resolution', 5)}°"
            config_data['Phi分辨率'] = f"{sim_settings.get('phi_resolution', 5)}°"
        
        # 显示配置
        if config_data:
            for key, value in config_data.items():
                st.markdown(f"**{key}:** {value}")
        else:
            st.info("📄 暂无配置信息")
        
        st.markdown("---")
        
        # 快速操作
        st.markdown("#### ⚡ 快速操作")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 重新仿真", width='stretch'):
                st.session_state.force_rerun = True
                st.rerun()
        
        with col2:
            if st.button("📊 详细分析", width='stretch'):
                st.switch_page("pages/2_分析工具.py")
        
        # 配置管理
        st.markdown("---")
        st.markdown("#### ⚙️ 配置管理")
        
        config_col1, config_col2 = st.columns(2)
        with config_col1:
            if st.button("💾 保存配置", width='stretch'):
                self._save_current_config(sidebar_config)
        
        with config_col2:
            if st.button("📥 加载配置", width='stretch'):
                self._load_config()
    
    def _save_current_config(self, sidebar_config: Dict[str, Any]):
        """保存当前配置"""
        try:
            # 创建配置目录
            current_dir = Path(__file__).parent
            config_dir = current_dir.parent / "config" / "saved"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            config_file = config_dir / f"config_{timestamp}.yaml"
            
            # 准备配置数据
            config_data = {
                'timestamp': timestamp,
                'sidebar_config': sidebar_config
            }
            
            # 如果存在天线数据，保存
            if 'current_antenna' in st.session_state and st.session_state.current_antenna is not None:
                try:
                    config_data['antenna_data'] = st.session_state.current_antenna.to_dict()
                except Exception as e:
                    st.warning(f"无法保存天线数据: {e}")
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
            
            st.success(f"配置已保存: {config_file.name}")
        except Exception as e:
            st.error(f"保存配置失败: {e}")
    
    def _load_config(self):
        """加载配置"""
        try:
            # 查找配置目录
            current_dir = Path(__file__).parent
            config_dir = current_dir.parent / "config" / "saved"
            
            if not config_dir.exists():
                st.warning("没有找到保存的配置")
                return
            
            config_files = list(config_dir.glob("config_*.yaml"))
            
            if not config_files:
                st.warning("没有找到保存的配置")
                return
            
            # 让用户选择配置文件
            file_names = [f.name for f in config_files]
            selected_file = st.selectbox("选择配置文件", file_names)
            
            if selected_file:
                config_file = config_dir / selected_file
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                st.success(f"已加载配置: {selected_file}")
                
                # 应用配置到session state
                if 'sidebar_config' in config_data:
                    st.session_state.sidebar_config = config_data['sidebar_config']
                
                if 'antenna_data' in config_data:
                    try:
                        from models.antenna_models import AntennaParameters
                        antenna = AntennaParameters.from_dict(config_data['antenna_data'])
                        st.session_state.current_antenna = antenna
                    except Exception as e:
                        st.warning(f"加载天线数据失败: {e}")
                
                st.rerun()
                
        except Exception as e:
            st.error(f"加载配置失败: {e}")
    
    def _render_analysis_summary(self):
        """渲染分析结果摘要"""
        if 'analysis_results' not in st.session_state or not st.session_state.analysis_results:
            st.info("暂无分析结果，请先运行仿真和分析")
            return
        
        results = st.session_state.analysis_results
        
        # 创建摘要卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'beam' in results and 'beam_parameters' in results['beam']:
                params = results['beam']['beam_parameters']
                gain = params.get('peak_gain', 0)
                self._create_summary_card("峰值增益", f"{gain:.1f} dBi", "📶")
            else:
                self._create_summary_card("峰值增益", "N/A", "📶")
        
        with col2:
            if 'beam' in results and 'beam_parameters' in results['beam']:
                params = results['beam']['beam_parameters']
                beamwidth = params.get('main_lobe_width_3db_e', 0)
                self._create_summary_card("3dB波束宽度", f"{beamwidth:.1f}°", "🎯")
            else:
                self._create_summary_card("3dB波束宽度", "N/A", "🎯")
        
        with col3:
            if 'beam' in results and 'sidelobes' in results['beam']:
                sidelobes = results['beam']['sidelobes']
                sll = sidelobes.get('max_sidelobe_level_e', 0)
                self._create_summary_card("副瓣电平", f"{sll:.1f} dB", "📉")
            else:
                self._create_summary_card("副瓣电平", "N/A", "📉")
        
        with col4:
            if 'efficiency' in results and 'efficiency_parameters' in results['efficiency']:
                eff_params = results['efficiency']['efficiency_parameters']
                efficiency = eff_params.get('total_efficiency', 0) * 100
                self._create_summary_card("总效率", f"{efficiency:.1f}%", "⚡")
            else:
                self._create_summary_card("总效率", "N/A", "⚡")
        
        # 详细结果
        st.markdown("---")
        st.markdown("#### 📋 详细分析结果")
        
        if 'overall_assessment' in results:
            assessment = results['overall_assessment']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 🎯 性能评估")
                score = assessment.get('performance_score', 0) * 100
                
                # 进度条显示分数
                st.progress(score/100)
                st.markdown(f"**综合评分:** {score:.1f}%")
                
                # 优点
                if 'strengths' in assessment and assessment['strengths']:
                    st.markdown("**✅ 优点:**")
                    for strength in assessment['strengths'][:3]:  # 显示前3个
                        st.markdown(f"- {strength}")
                else:
                    st.markdown("**✅ 优点:** 无数据")
            
            with col2:
                st.markdown("##### 💡 建议")
                if 'recommendations' in assessment and assessment['recommendations']:
                    for rec in assessment['recommendations'][:3]:  # 显示前3个
                        st.markdown(f"- {rec}")
                else:
                    st.markdown("无特殊建议")
        else:
            st.info("暂无详细评估信息")
    
    def _create_summary_card(self, title: str, value: str, icon: str = ""):
        """创建摘要卡片"""
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 15px;
            color: white;
            text-align: center;
            margin: 5px 0;
        '>
            <div style='font-size: 1.5em; margin-bottom: 5px;'>{icon}</div>
            <div style='font-size: 0.9em; opacity: 0.9;'>{title}</div>
            <div style='font-size: 1.2em; font-weight: bold; margin: 5px 0;'>{value}</div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_monitoring(self, sidebar_config: Dict[str, Any]):
        """
        渲染实时监控页面
        """
        st.markdown("### 📡 实时监控")
        
        # 监控控制面板
        col1, col2, col3 = st.columns(3)
        
        with col1:
            monitor_enabled = st.toggle("启用实时监控", value=False)
        
        with col2:
            update_interval = st.slider("更新间隔 (秒)", 1, 60, 5, disabled=not monitor_enabled)
        
        with col3:
            if st.button("🔄 手动刷新", disabled=not monitor_enabled):
                st.rerun()
        
        if monitor_enabled:
            # 实时图表
            self._render_realtime_charts()
            
            # 监控数据
            st.markdown("---")
            self._render_monitoring_data()
        else:
            st.info("💡 启用实时监控以查看实时数据和图表")
    
    def _render_realtime_charts(self):
        """渲染实时图表"""
        # 创建示例实时数据
        time_points = 20
        time_series = list(range(time_points))
        
        # 生成随机数据（模拟实时数据）
        np.random.seed(42)
        gain_data = 10 + np.random.randn(time_points).cumsum() * 0.5
        efficiency_data = 0.7 + np.random.randn(time_points).cumsum() * 0.02
        vswr_data = 1.5 + np.random.randn(time_points).cumsum() * 0.1
        
        # 创建图表
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("增益监控", "效率监控", "VSWR监控", "频谱监控"),
            vertical_spacing=0.15
        )
        
        # 增益监控
        fig.add_trace(
            go.Scatter(
                x=time_series,
                y=gain_data,
                mode='lines+markers',
                name='增益',
                line=dict(color='#636efa', width=2)
            ),
            row=1, col=1
        )
        
        # 效率监控
        fig.add_trace(
            go.Scatter(
                x=time_series,
                y=efficiency_data * 100,
                mode='lines+markers',
                name='效率',
                line=dict(color='#00cc96', width=2)
            ),
            row=1, col=2
        )
        
        # VSWR监控
        fig.add_trace(
            go.Scatter(
                x=time_series,
                y=vswr_data,
                mode='lines+markers',
                name='VSWR',
                line=dict(color='#ef553b', width=2)
            ),
            row=2, col=1
        )
        
        # 频谱监控（示例）
        freq = np.linspace(2.4, 2.5, 100)
        spectrum = np.random.randn(100) + np.sin(freq * 20) * 0.5
        
        fig.add_trace(
            go.Scatter(
                x=freq,
                y=spectrum,
                mode='lines',
                name='频谱',
                line=dict(color='#ab63fa', width=2)
            ),
            row=2, col=2
        )
        
        # 更新布局
        fig.update_layout(
            height=600,
            showlegend=True,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # 更新坐标轴标签
        fig.update_xaxes(title_text="时间", row=1, col=1)
        fig.update_xaxes(title_text="时间", row=1, col=2)
        fig.update_xaxes(title_text="时间", row=2, col=1)
        fig.update_xaxes(title_text="频率 (GHz)", row=2, col=2)
        
        fig.update_yaxes(title_text="增益 (dBi)", row=1, col=1)
        fig.update_yaxes(title_text="效率 (%)", row=1, col=2)
        fig.update_yaxes(title_text="VSWR", row=2, col=1)
        fig.update_yaxes(title_text="幅度 (dB)", row=2, col=2)
        
        st.plotly_chart(fig, width='stretch')
    
    def _render_monitoring_data(self):
        """渲染监控数据"""
        st.markdown("#### 📊 实时数据")
        
        # 创建数据表
        data = {
            '时间': [f"T-{i}" for i in range(10, 0, -1)],
            '增益 (dBi)': np.random.uniform(10, 12, 10).round(1),
            '效率 (%)': np.random.uniform(70, 80, 10).round(1),
            'VSWR': np.random.uniform(1.2, 2.0, 10).round(2),
            '温度 (°C)': np.random.uniform(20, 35, 10).round(1)
        }
        
        df = pd.DataFrame(data)
        
        # 高亮异常值
        def highlight_anomalies(val, column):
            if column == 'VSWR' and val > 1.5:
                return 'background-color: rgba(255, 0, 0, 0.3)'
            elif column == '温度 (°C)' and val > 30:
                return 'background-color: rgba(255, 165, 0, 0.3)'
            return ''
        
        styled_df = df.style.apply(
            lambda row: [highlight_anomalies(row[col], col) for col in df.columns], 
            axis=1
        )
        
        st.dataframe(styled_df, width='stretch', height=300)
        
        # 告警信息
        st.markdown("#### ⚠️ 告警信息")
        
        alerts = [
            {"时间": "10:30", "级别": "警告", "描述": "VSWR超过1.8", "状态": "已确认"},
            {"时间": "10:25", "级别": "注意", "描述": "温度超过30°C", "状态": "未确认"},
            {"时间": "10:20", "级别": "信息", "描述": "效率波动较大", "状态": "已确认"}
        ]
        
        for alert in alerts:
            level_color = {
                "警告": "🔴",
                "注意": "🟡", 
                "信息": "🔵"
            }[alert["级别"]]
            
            st.markdown(f"{level_color} **{alert['时间']}** - {alert['描述']} ({alert['状态']})")
    
    def _render_performance_analysis(self, sidebar_config: Dict[str, Any]):
        """
        渲染性能分析页面
        """
        st.markdown("### 📊 性能深度分析")
        
        if 'analysis_results' not in st.session_state or not st.session_state.analysis_results:
            st.info("请先运行仿真和分析以查看性能数据")
            if st.button("🚀 运行分析", type="primary"):
                self._run_analysis()
            return
        
        results = st.session_state.analysis_results
        
        # 创建分析标签页
        perf_tab1, perf_tab2, perf_tab3, perf_tab4 = st.tabs([
            "波束特性", "极化特性", "效率分析", "比较分析"
        ])
        
        with perf_tab1:
            self._render_beam_analysis(results)
        
        with perf_tab2:
            self._render_polarization_analysis(results)
        
        with perf_tab3:
            self._render_efficiency_analysis(results)
        
        with perf_tab4:
            self._render_comparative_analysis(results)
    
    def _run_analysis(self):
        """运行分析"""
        if 'pattern_data' in st.session_state and st.session_state.pattern_data:
            pattern = st.session_state.pattern_data
            antenna = st.session_state.get('current_antenna')
            
            with st.spinner("正在分析..."):
                if self.analysis_service:
                    results = self.analysis_service.comprehensive_analysis(pattern, antenna)
                else:
                    results = self._create_example_analysis()
                st.session_state.analysis_results = results
            
            st.success("分析完成！")
            st.rerun()
        else:
            st.warning("请先运行仿真生成方向图数据")
    
    def _render_beam_analysis(self, results: Dict[str, Any]):
        """渲染波束特性分析"""
        if 'beam' not in results:
            st.info("暂无波束分析数据")
            return
        
        beam_results = results['beam']
        
        # 波束参数
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🎯 波束参数")
            if 'beam_parameters' in beam_results:
                params = beam_results['beam_parameters']
                
                params_data = {
                    "峰值增益": f"{params.get('peak_gain', 0):.1f} dBi",
                    "3dB波束宽度 (E)": f"{params.get('main_lobe_width_3db_e', 0):.1f}°",
                    "3dB波束宽度 (H)": f"{params.get('main_lobe_width_3db_h', 0):.1f}°",
                    "对称性误差": f"{params.get('symmetry_e', {}).get('symmetry_error', 0):.2f}" if isinstance(params.get('symmetry_e'), dict) else "N/A"
                }
                
                for key, value in params_data.items():
                    st.markdown(f"**{key}:** {value}")
            else:
                st.markdown("暂无波束参数数据")
        
        with col2:
            st.markdown("##### 📉 副瓣分析")
            if 'sidelobes' in beam_results:
                sidelobes = beam_results['sidelobes']
                
                sidelobe_data = {
                    "最大副瓣电平 (E)": f"{sidelobes.get('max_sidelobe_level_e', 0):.1f} dB",
                    "最大副瓣电平 (H)": f"{sidelobes.get('max_sidelobe_level_h', 0):.1f} dB",
                    "第一副瓣电平 (E)": f"{sidelobes.get('first_sidelobe_level_e', 0):.1f} dB",
                    "副瓣数量 (E)": f"{sidelobes.get('sidelobe_count_e', 0)}"
                }
                
                for key, value in sidelobe_data.items():
                    st.markdown(f"**{key}:** {value}")
            else:
                st.markdown("暂无副瓣分析数据")
        
        # 波束宽度分析
        st.markdown("---")
        st.markdown("##### 📏 波束宽度分析")
        
        if 'beamwidths' in beam_results:
            beamwidths = beam_results['beamwidths']
            
            # 创建数据框
            bw_data = []
            for level in [3, 6, 10, 20]:
                key_e = f'beamwidth_{level}db_e'
                key_h = f'beamwidth_{level}db_h'
                if key_e in beamwidths and key_h in beamwidths:
                    bw_data.append({
                        '电平': f'{level}dB',
                        'E面': beamwidths[key_e],
                        'H面': beamwidths[key_h]
                    })
            
            if bw_data:
                df_bw = pd.DataFrame(bw_data)
                st.dataframe(df_bw, width='stretch')
            else:
                st.info("无波束宽度数据")
        else:
            st.info("无波束宽度分析数据")
        
        # 零陷分析
        st.markdown("---")
        st.markdown("##### 🕳️ 零陷分析")
        
        if 'nulls' in beam_results:
            nulls = beam_results['nulls']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("零陷数量 (E)", nulls.get('null_count_e', 0))
                st.metric("最大零陷深度 (E)", f"{nulls.get('max_null_depth_e', 0):.1f} dB")
            
            with col2:
                st.metric("零陷数量 (H)", nulls.get('null_count_h', 0))
                st.metric("最大零陷深度 (H)", f"{nulls.get('max_null_depth_h', 0):.1f} dB")
        else:
            st.info("无零陷分析数据")
    
    def _render_polarization_analysis(self, results: Dict[str, Any]):
        """渲染极化特性分析"""
        if 'polarization' not in results:
            st.info("暂无极化分析数据")
            return
        
        pol_results = results['polarization']
        
        # 轴比分析
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🔄 轴比分析")
            if 'axial_ratio' in pol_results:
                ar = pol_results['axial_ratio']
                
                ar_data = {
                    "最小轴比": f"{ar.get('axial_ratio_min', 0):.1f} dB",
                    "最大轴比": f"{ar.get('axial_ratio_max', 0):.1f} dB",
                    "平均轴比": f"{ar.get('axial_ratio_mean', 0):.1f} dB",
                    "主瓣平均轴比": f"{ar.get('mainlobe_axial_ratio_mean', 0):.1f} dB"
                }
                
                for key, value in ar_data.items():
                    st.markdown(f"**{key}:** {value}")
            else:
                st.markdown("暂无轴比数据")
        
        with col2:
            st.markdown("##### 📊 极化纯度")
            if 'polarization_purity' in pol_results:
                purity = pol_results['polarization_purity']
                
                purity_data = {
                    "极化纯度均值": f"{purity.get('polarization_purity_mean', 0):.3f}",
                    "极化纯度标准差": f"{purity.get('polarization_purity_std', 0):.3f}",
                    "交叉极化鉴别度": f"{results.get('polarization_parameters', {}).get('xpd_mean', 0):.1f} dB"
                }
                
                for key, value in purity_data.items():
                    st.markdown(f"**{key}:** {value}")
            else:
                st.markdown("暂无极化纯度数据")
        
        # 极化椭圆参数
        st.markdown("---")
        st.markdown("##### 🌀 极化椭圆参数")
        
        if 'polarization_ellipse' in pol_results:
            ellipse = pol_results['polarization_ellipse']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("长轴均值", f"{ellipse.get('major_axis_mean', 0):.3f}")
            with col2:
                st.metric("短轴均值", f"{ellipse.get('minor_axis_mean', 0):.3f}")
            with col3:
                st.metric("椭圆率", f"{ellipse.get('ellipticity', 0):.3f}")
        else:
            st.info("无极化椭圆参数数据")
    
    def _render_efficiency_analysis(self, results: Dict[str, Any]):
        """渲染效率分析"""
        if 'efficiency' not in results:
            st.info("暂无效率分析数据")
            return
        
        eff_results = results['efficiency']
        
        # 效率参数
        st.markdown("##### ⚡ 效率参数")
        
        if 'efficiency_parameters' in eff_results:
            eff_params = eff_results['efficiency_parameters']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                efficiency = eff_params.get('radiation_efficiency', 0) * 100
                st.metric("辐射效率", f"{efficiency:.1f}%")
            
            with col2:
                efficiency = eff_params.get('aperture_efficiency', 0) * 100
                st.metric("孔径效率", f"{efficiency:.1f}%")
            
            with col3:
                efficiency = eff_params.get('beam_efficiency', 0) * 100
                st.metric("波束效率", f"{efficiency:.1f}%")
            
            with col4:
                efficiency = eff_params.get('total_efficiency', 0) * 100
                st.metric("总效率", f"{efficiency:.1f}%")
        else:
            st.info("无效率参数数据")
        
        # 效率分析
        st.markdown("---")
        st.markdown("##### 📈 效率分析")
        
        # 创建示例效率图表
        efficiency_types = ['辐射效率', '孔径效率', '波束效率', '总效率']
        
        if 'efficiency_parameters' in eff_results:
            eff_params = eff_results['efficiency_parameters']
            efficiency_values = [
                eff_params.get('radiation_efficiency', 0.85),
                eff_params.get('aperture_efficiency', 0.75),
                eff_params.get('beam_efficiency', 0.80),
                eff_params.get('total_efficiency', 0.65)
            ]
        else:
            efficiency_values = [0.85, 0.75, 0.80, 0.65]  # 示例值
        
        fig = go.Figure(data=[
            go.Bar(
                x=efficiency_types,
                y=efficiency_values,
                marker_color=['#636efa', '#ef553b', '#00cc96', '#ab63fa']
            )
        ])
        
        fig.update_layout(
            title="效率分析",
            yaxis_title="效率",
            yaxis_tickformat=".0%",
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _render_comparative_analysis(self, results: Dict[str, Any]):
        """渲染比较分析"""
        st.markdown("##### ⚖️ 比较分析")
        
        # 示例比较数据
        antenna_names = ['天线A', '天线B', '天线C', '当前天线']
        
        # 尝试从结果中获取当前天线的值
        current_gain = results.get('beam', {}).get('beam_parameters', {}).get('peak_gain', 11.3)
        current_beamwidth = results.get('beam', {}).get('beam_parameters', {}).get('main_lobe_width_3db_e', 24.3)
        current_sidelobe = results.get('beam', {}).get('sidelobes', {}).get('max_sidelobe_level_e', -19.1)
        current_efficiency = results.get('efficiency', {}).get('efficiency_parameters', {}).get('total_efficiency', 0.753) * 100
        
        comparison_data = {
            '增益 (dBi)': [10.2, 12.5, 9.8, current_gain],
            '波束宽度 (°)': [25.3, 22.1, 28.5, current_beamwidth],
            '副瓣电平 (dB)': [-18.2, -20.5, -16.8, current_sidelobe],
            '效率 (%)': [72.5, 78.2, 68.9, current_efficiency]
        }
        
        df_comparison = pd.DataFrame(comparison_data, index=antenna_names)
        
        # 显示比较表格
        st.dataframe(df_comparison, width='stretch')
        
        # 比较图表
        st.markdown("---")
        st.markdown("##### 📊 性能比较")
        
        metrics = st.multiselect(
            "选择比较指标",
            list(comparison_data.keys()),
            default=['增益 (dBi)', '效率 (%)']
        )
        
        if metrics:
            fig = go.Figure()
            
            for metric in metrics:
                fig.add_trace(go.Bar(
                    x=antenna_names,
                    y=df_comparison[metric],
                    name=metric
                ))
            
            fig.update_layout(
                title="天线性能比较",
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
    
    def _render_data_management(self, sidebar_config: Dict[str, Any]):
        """
        渲染数据管理页面
        """
        st.markdown("### 💾 数据管理")
        
        # 数据管理标签页
        data_tab1, data_tab2, data_tab3 = st.tabs([
            "数据存储", "导入/导出", "历史记录"
        ])
        
        with data_tab1:
            self._render_data_storage()
        
        with data_tab2:
            self._render_data_import_export()
        
        with data_tab3:
            self._render_history_records()
    
    def _render_data_storage(self):
        """渲染数据存储"""
        st.markdown("#### 💿 数据存储配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            storage_type = st.selectbox(
                "存储类型",
                ["本地文件", "数据库", "云存储"],
                help="选择数据存储方式"
            )
            
            if storage_type == "本地文件":
                data_dir = st.text_input(
                    "数据目录",
                    value=str(Path.home() / "antenna_data"),
                    help="数据存储目录"
                )
                
                auto_save = st.checkbox("自动保存", value=True)
                if auto_save:
                    save_interval = st.slider("保存间隔 (分钟)", 1, 60, 5)
            
            elif storage_type == "数据库":
                db_type = st.selectbox("数据库类型", ["SQLite", "MySQL", "PostgreSQL"])
                db_host = st.text_input("主机地址", value="localhost")
                db_name = st.text_input("数据库名", value="antenna_db")
            
            else:  # 云存储
                cloud_provider = st.selectbox("云提供商", ["AWS S3", "Google Cloud", "Azure"])
                bucket_name = st.text_input("存储桶名称", value="antenna-storage")
        
        with col2:
            st.markdown("##### 📁 存储统计")
            
            # 示例统计
            stats = {
                "总数据量": "1.2 GB",
                "天线数量": "24",
                "仿真次数": "156",
                "配置文件": "12"
            }
            
            for key, value in stats.items():
                st.markdown(f"**{key}:** {value}")
        
        # 存储操作
        st.markdown("---")
        st.markdown("#### ⚡ 存储操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 立即备份", width='stretch'):
                st.success("数据备份完成")
        
        with col2:
            if st.button("🧹 清理缓存", width='stretch'):
                st.success("缓存已清理")
        
        with col3:
            if st.button("📊 存储分析", width='stretch'):
                st.info("存储分析完成")
    
    def _render_data_import_export(self):
        """渲染数据导入导出"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📥 数据导入")
            
            import_format = st.selectbox(
                "导入格式",
                ["CSV", "JSON", "YAML", "MAT文件", "NEC文件"],
                key="import_format"
            )
            
            uploaded_file = st.file_uploader(
                f"选择{import_format}文件",
                type=[import_format.lower()],
                key="import_uploader"
            )
            
            if uploaded_file is not None:
                st.info(f"已选择文件: {uploaded_file.name}")
                
                if st.button("导入数据", type="primary"):
                    with st.spinner("正在导入..."):
                        # 这里应该实现具体的导入逻辑
                        st.success(f"成功导入 {uploaded_file.name}")
            
            # 从数据库导入
            st.markdown("---")
            st.markdown("##### 🗃️ 从数据库导入")
            
            if st.button("浏览数据库", width='stretch'):
                st.info("数据库浏览器功能开发中...")
        
        with col2:
            st.markdown("#### 📤 数据导出")
            
            export_format = st.selectbox(
                "导出格式",
                ["CSV", "JSON", "YAML", "Excel", "PNG", "PDF"],
                key="export_format"
            )
            
            export_options = st.multiselect(
                "导出内容",
                ["天线参数", "方向图数据", "分析结果", "可视化图表", "配置信息"],
                default=["天线参数", "分析结果"]
            )
            
            if st.button("导出数据", type="primary", width='stretch'):
                with st.spinner("正在导出..."):
                    # 这里应该实现具体的导出逻辑
                    st.success(f"数据已导出为 {export_format} 格式")
            
            # 批量导出
            st.markdown("---")
            st.markdown("##### 📦 批量导出")
            
            batch_range = st.slider("选择导出范围", 1, 100, (1, 10))
            if st.button("批量导出选中项", width='stretch'):
                st.info(f"将导出 {batch_range[0]}-{batch_range[1]} 项数据")
    
    def _render_history_records(self):
        """渲染历史记录"""
        st.markdown("#### 📜 历史记录")
        
        # 搜索和筛选
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_query = st.text_input("🔍 搜索", placeholder="输入关键词...")
        
        with col2:
            date_range = st.date_input(
                "📅 日期范围",
                value=(datetime.date.today() - datetime.timedelta(days=7), datetime.date.today())
            )
        
        with col3:
            # 确保record_type是有效的列表
            record_types_options = ["仿真", "分析", "配置", "导出", "错误"]
            record_type = st.multiselect(
                "📁 记录类型",
                record_types_options,
                default=["仿真", "分析"]
            )
        
        # 历史记录表格
        st.markdown("---")
        
        # 生成示例历史数据
        history_data = []
        for i in range(20):
            record_types = ["仿真", "分析", "配置", "导出", "错误"]
            r_type = np.random.choice(record_types, p=[0.4, 0.3, 0.1, 0.1, 0.1])
            
            status_types = ["成功", "失败", "进行中"]
            status = np.random.choice(status_types, p=[0.8, 0.15, 0.05])
            
            history_data.append({
                "ID": f"REC{i+1:04d}",
                "时间": (datetime.datetime.now() - datetime.timedelta(hours=i*2)).strftime("%Y-%m-%d %H:%M"),
                "类型": r_type,
                "描述": f"{r_type}操作 - 天线仿真 #{i+1}",
                "状态": status,
                "大小": f"{np.random.randint(1, 1000)} KB"
            })
        
        df_history = pd.DataFrame(history_data)
        
        # 应用筛选 - 修复isin错误
        if search_query and search_query.strip():
            # 确保搜索查询是字符串
            search_query_str = str(search_query).strip()
            df_history = df_history[df_history['描述'].str.contains(search_query_str, case=False, na=False)]
        
        if record_type and len(record_type) > 0:
            try:
                # 确保record_type是字符串列表
                record_type_str = [str(r) for r in record_type if r is not None]
                
                # 确保DataFrame列是字符串类型
                if df_history['类型'].dtype != 'object':
                    df_history['类型'] = df_history['类型'].astype(str)
                
                # 使用isin进行筛选
                mask = df_history['类型'].isin(record_type_str)
                df_history = df_history[mask]
            except Exception as e:
                st.warning(f"筛选记录类型时出错: {e}")
                # 出错时显示所有记录
        
        # 显示表格
        st.dataframe(
            df_history,
            width='stretch',
            height=400,
            column_config={
                "ID": st.column_config.Column(width="small"),
                "时间": st.column_config.Column(width="medium"),
                "类型": st.column_config.Column(width="small"),
                "描述": st.column_config.Column(width="large"),
                "状态": st.column_config.Column(width="small"),
                "大小": st.column_config.Column(width="small")
            }
        )
        
        # 历史操作
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_ids = st.multiselect("选择记录", df_history['ID'].tolist())
        
        with col2:
            action = st.selectbox("操作", ["查看详情", "重新运行", "导出", "删除"])
        
        with col3:
            if st.button("执行操作", disabled=len(selected_ids) == 0):
                st.success(f"对 {len(selected_ids)} 条记录执行了 {action} 操作")
    
    def _render_status_bar(self):
        """渲染底部状态栏"""
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.caption(f"🕐 最后更新: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        with col2:
            st.caption("💾 内存使用: 45%")
        
        with col3:
            st.caption("⚡ 响应时间: 120ms")
        
        with col4:
            st.caption("✅ 系统状态: 正常")

def render_dashboard(config=None, sidebar_config: Dict[str, Any] = None):
    """
    渲染仪表板的主函数
    """
    try:
        if sidebar_config is None:
            sidebar_config = {}
            
        dashboard = DashboardView(config)
        dashboard.render(sidebar_config)
    except Exception as e:
        st.error(f"仪表板渲染错误: {e}")
        st.exception(e)

if __name__ == "__main__":
    # 测试代码
    sidebar_config = {
        'page': 'dashboard',
        'antenna_config': {},
        'simulation_settings': {},
        'analysis_settings': {},
        'visualization_settings': {},
        'actions': {}
    }
    
    st.set_page_config(layout="wide")
    render_dashboard(sidebar_config=sidebar_config)