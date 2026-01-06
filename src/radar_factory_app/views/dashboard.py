"""
主仪表板视图模块
展示雷达系统概览、性能指标和快速操作界面
使用Streamlit构建交互式仪表板
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.radar_models import RadarSystem, RadarBand, PlatformType, MissionType
from models.simulation_models import PRESET_SCENARIOS
from services.performance_calculator import RadarPerformanceCalculator
from utils.helpers import format_frequency, format_distance, format_power


class DashboardView:
    """主仪表板视图类"""
    
    def __init__(self, radar_system: RadarSystem):
        self.radar_system = radar_system
        self.performance_calc = RadarPerformanceCalculator()
        self.setup_page_config()
    
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="雷达工厂",
            page_icon="🛰️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 自定义CSS样式
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #1f77b4;
        }       
        .radar-card {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }

        .stTabs button[role="tab"] > div > p {
            font-size: 1.3em !important;
        }
    

        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """渲染页面头部"""        
      
        # st.markdown('<h1 class="main-header">🛰️ 雷达工厂</h1>', 
        #            unsafe_allow_html=True)
        
        # 创建选项卡
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 系统概览", 
            "📡 雷达管理", 
            "🎯 仿真分析", 
            "⚙️ 系统设置"
        ])
        
        return tab1, tab2, tab3, tab4
    
    def render_system_overview(self, tab):
        """渲染系统概览选项卡"""
        with tab:
            # 在容器中应用自定义样式
            with st.container():
                st.markdown("""
                <style>
                /* 为metric组件应用自定义样式 */
                [data-testid="stMetric"] [data-testid="stMetricValue"] {
                    font-size: 1.2rem !important;
                    font-weight: 600 !important;
                }
                [data-testid="stMetric"] [data-testid="stMetricLabel"] {
                    font-size: 0.85rem !important;
                }
                </style>
                """, unsafe_allow_html=True)            
            # 系统概览指标
            col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
            
            # 获取系统摘要
            summary = self._get_system_summary()
            
            with col1:
                st.metric(
                    label="雷达总数",
                    value=summary["total_radars"],
                    delta=None
                )
            
            with col2:
                total_power_mw = summary["total_power_w"] / 1000
                st.metric(
                    label="总发射功率",
                    value=f"{total_power_mw:.1f} MW",
                    delta=None
                )
            
            with col3:
                freq_range = summary["frequency_coverage_hz"]
                min_freq = format_frequency(freq_range["min"])
                max_freq = format_frequency(freq_range["max"])
                st.metric(
                    label="频率覆盖范围",
                    value=f"{min_freq} - {max_freq}",
                    delta=None
                )
            
            with col4:
                band_count = len(summary["band_distribution"])
                st.metric(
                    label="频段数量",
                    value=band_count,
                    delta=None
                )
            
            # 频段分布图表
            st.markdown("##### 📈 频段分布分析")
            self._render_band_distribution(summary["band_distribution"])
            
            # 雷达性能对比
            st.markdown("##### ⚡ 雷达性能对比")
            self._render_performance_comparison()
            
            # 快速操作面板
            st.markdown("##### 🚀 快速操作")
            self._render_quick_actions()
    
    def _get_system_summary(self):
        """获取系统摘要"""
        # 简化实现，实际应从雷达系统获取
        if not hasattr(self.radar_system, 'radars') or not self.radar_system.radars:
            return {
                "total_radars": 0,
                "total_power_w": 0,
                "frequency_coverage_hz": {"min": 0, "max": 0},
                "band_distribution": {}
            }
        
        # 计算实际值
        total_radars = len(self.radar_system.radars)
        total_power_w = 0
        frequencies = []
        band_distribution = {}
        
        for radar_id, radar in self.radar_system.radars.items():
            if hasattr(radar, 'transmitter') and radar.transmitter:
                total_power_w += radar.transmitter.power_w
                frequencies.append(radar.transmitter.frequency_hz)
            
            band = radar.get_band().value if hasattr(radar, 'get_band') else "未知"
            band_distribution[band] = band_distribution.get(band, 0) + 1
        
        return {
            "total_radars": total_radars,
            "total_power_w": total_power_w,
            "frequency_coverage_hz": {
                "min": min(frequencies) if frequencies else 0,
                "max": max(frequencies) if frequencies else 0
            },
            "band_distribution": band_distribution
        }
    
    def _render_band_distribution(self, band_distribution: Dict[str, int]):
        """渲染频段分布图表"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 饼图展示频段分布
            if band_distribution:
                bands = list(band_distribution.keys())
                counts = list(band_distribution.values())
                
                fig = px.pie(
                    values=counts,
                    names=bands,
                    title="雷达频段分布图",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, width='stretch')
        
        with col2:
            # 频段统计表格
            st.write("**频段统计:**")
            for band, count in band_distribution.items():
                st.write(f"- {band}波段: {count}部")
    
    def _render_performance_comparison(self):
        """渲染雷达性能对比图表"""
        if not hasattr(self.radar_system, 'radars') or not self.radar_system.radars:
            st.info("暂无雷达数据，请先添加雷达系统")
            return
        
        # 准备对比数据
        radar_names = []
        ranges = []
        powers = []
        frequencies = []
        
        for radar_id, radar in self.radar_system.radars.items():
            radar_names.append(radar.name)
            
            # 获取性能数据
            try:
                performance = radar.calculate_performance() if hasattr(radar, 'calculate_performance') else {}
                ranges.append(performance.get("max_range_km", 0))
            except:
                ranges.append(0)
            
            if hasattr(radar, 'transmitter') and radar.transmitter:
                powers.append(radar.transmitter.power_w / 1000)  # 转换为kW
                frequencies.append(radar.transmitter.frequency_hz / 1e9)  # 转换为GHz
            else:
                powers.append(0)
                frequencies.append(0)
        
        # 创建对比图表
        fig = go.Figure()
        
        # 添加探测距离柱状图
        fig.add_trace(go.Bar(
            x=radar_names,
            y=ranges,
            name='最大探测距离 (km)',
            marker_color='#1f77b4'
        ))
        
        # 添加发射功率散点图（次坐标轴）
        fig.add_trace(go.Scatter(
            x=radar_names,
            y=powers,
            name='发射功率 (kW)',
            marker=dict(color='#ff7f0e', size=10),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="雷达性能对比图",
            xaxis_title="雷达型号",
            yaxis=dict(
                title="探测距离 (km)",
                # titlefont=dict(color="#1f77b4"),
                tickfont=dict(color="#1f77b4")
            ),
            yaxis2=dict(
                title="发射功率 (kW)",
                # titlefont=dict(color="#ff7f0e"),
                tickfont=dict(color="#ff7f0e"),
                overlaying="y",
                side="right"
            ),
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _render_quick_actions(self):
        """渲染快速操作面板"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🆕 新建雷达", key="dashboard_btn_new_radar"):
                st.session_state.current_view = "radar_editor"
                st.rerun()
        
        with col2:
            if st.button("🎯 开始仿真", key="dashboard_btn_simulation"):
                # st.session_state.current_view = "simulation"
                # st.rerun()
                # 设置默认仿真参数
                controller = st.session_state.radar_controller
                all_radars = controller.get_all_radars()
                radar_ids = list(all_radars.keys())[:3] if len(all_radars) > 0 else []
                
                # 创建仿真参数
                simulation_params = {
                    "radars": radar_ids,
                    "duration": 1.0,
                    "time_step": 0.1,
                    "target_rcs": 5.0,
                    "scenario_type": "single_target"
                }
                
                # 保存参数到session state
                st.session_state.simulation_params = simulation_params
                
                # 切换到仿真视图
                st.session_state.current_view = "simulation"
                st.rerun()                
        
        with col3:
            if st.button("📊 性能分析", key="dashboard_btn_analysis"):
                st.session_state.current_view = "comparison"
                st.rerun()
        
        with col4:
            if st.button("💾 导出数据", key="dashboard_btn_export"):
                self._export_system_data()
    
    def _export_system_data(self):
        """导出系统数据"""
        # 实现数据导出逻辑
        st.success("系统数据导出功能开发中...")
    
    def render_radar_management(self, tab):
        """渲染雷达管理选项卡"""
        with tab:
            # st.header("📡 雷达管理系统")
            
            # 搜索和过滤
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_term = st.text_input("🔍 搜索雷达", placeholder="输入雷达名称或ID")
            
            with col2:
                band_filter = st.selectbox("频段过滤", ["全部"] + [band.value for band in RadarBand])
            
            with col3:
                platform_filter = st.selectbox("平台过滤", ["全部"] + [platform.value for platform in PlatformType])
            
            # 雷达列表
            filtered_radars = self._filter_radars(search_term, band_filter, platform_filter)
            self._render_radar_list(filtered_radars)
    
    def _filter_radars(self, search_term: str, band_filter: str, platform_filter: str) -> List:
        """过滤雷达列表"""
        filtered = []
        
        if not hasattr(self.radar_system, 'radars'):
            return filtered
            
        for radar_id, radar in self.radar_system.radars.items():
            # 搜索条件
            if search_term and search_term.lower() not in radar.name.lower() and search_term not in radar_id:
                continue
            
            # 频段过滤
            if band_filter != "全部" and hasattr(radar, 'get_band') and radar.get_band().value != band_filter:
                continue
            
            # 平台过滤
            if platform_filter != "全部" and hasattr(radar, 'platform') and radar.platform.value != platform_filter:
                continue
            
            filtered.append((radar_id, radar))
        
        return filtered
    
    def _render_radar_list(self, radars: List):
        """渲染雷达列表"""
        if not radars:
            st.info("没有找到匹配的雷达")
            return
        
        for idx, (radar_id, radar) in enumerate(radars):
            with st.expander(f"📡 {radar.name} ({radar_id})", expanded=False):
                self._render_radar_detail(radar, idx)
    
    def _render_radar_detail(self, radar, idx: int):
        """渲染雷达详细信息"""
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 基本参数
            st.write(f"**雷达ID:** {radar.radar_id}")
            st.write(f"**平台类型:** {radar.platform.value}")
            st.write(f"**工作频段:** {radar.get_band().value}")
            st.write(f"**部署方式:** {getattr(radar, 'deployment_method', '未知')}")
            
            # 任务类型
            mission_str = ", ".join([mission.value for mission in radar.mission_types])
            st.write(f"**任务类型:** {mission_str}")
        
        with col2:
            # 性能参数
            if hasattr(radar, 'transmitter') and radar.transmitter:
                st.write(f"**工作频率:** {format_frequency(radar.transmitter.frequency_hz)}")
                st.write(f"**发射功率:** {format_power(radar.transmitter.power_w)}")
                st.write(f"**脉冲宽度:** {radar.transmitter.pulse_width_s * 1e6:.1f} μs")
            
            if hasattr(radar, 'antenna') and radar.antenna:
                st.write(f"**天线增益:** {radar.antenna.gain_dbi:.1f} dBi")
                st.write(f"**波束宽度:** {radar.antenna.azimuth_beamwidth:.1f}° × {radar.antenna.elevation_beamwidth:.1f}°")
            
            st.write(f"**理论探测距离:** {getattr(radar, 'theoretical_range_km', 0):.1f} km")
            
            # 操作按钮
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 6])
            with col_btn1:
                if st.button("编辑", key=f"radar_edit_{idx}_{radar.radar_id}"):
                    st.session_state.editing_radar_id = radar.radar_id
                    st.session_state.current_view = "radar_editor"
                    st.rerun()
            
            with col_btn2:
                if st.button("仿真", key=f"radar_sim_{idx}_{radar.radar_id}"):
                    st.session_state.selected_radar_id = radar.radar_id
                    st.session_state.current_view = "simulation"
                    st.rerun()
            
            with col_btn3:
                if st.button("删除", key=f"radar_del_{idx}_{radar.radar_id}"):
                    self._delete_radar(radar.radar_id)
                    
            with col_btn4:
                if st.button("添加到电子战模型数据库", key=f"radar_to_model_database_{idx}_{radar.radar_id}"):
                    st.success(f"雷达 {radar.radar_id} 已添加到电子战模型数据库")
                    # st.rerun()
                    # self._delete_radar(radar.radar_id)
    
    def _delete_radar(self, radar_id: str):
        """删除雷达"""
        if hasattr(self.radar_system, 'radars') and radar_id in self.radar_system.radars:
            del self.radar_system.radars[radar_id]
            st.success(f"雷达 {radar_id} 已删除")
            st.rerun()
    
    def render_simulation_analysis(self, tab):
        """渲染仿真分析选项卡"""
        with tab:
            # st.header("🎯 仿真分析")
            
            # 仿真场景选择
            col1, col2 = st.columns(2)
            
            with col1:
                scenario_option = st.selectbox(
                    "选择仿真场景",
                    ["自定义场景"] + list(PRESET_SCENARIOS.keys())
                )
                
                if scenario_option != "自定义场景":
                    scenario = PRESET_SCENARIOS[scenario_option]
                    st.write(f"**场景描述:** {scenario.description}")
                    st.write(f"**仿真时长:** {scenario.duration}秒")
                    st.write(f"**目标数量:** {len(scenario.targets)}")
            
            with col2:
                radar_list = list(self.radar_system.radars.keys()) if hasattr(self.radar_system, 'radars') else []
                selected_radars = st.multiselect(
                    "选择参与仿真的雷达",
                    radar_list,
                    default=radar_list[:3] if radar_list else []
                )
                
                # 仿真参数设置
                sim_duration = st.slider("仿真时长 (秒)", 10, 600, 60)
                time_step = st.selectbox("时间步长 (秒)", [0.01, 0.1, 0.5, 1.0], index=1)
            
            # 开始仿真按钮
            if st.button("🚀 开始仿真", type="primary", key="sim_start_btn"):
                if not selected_radars:
                    st.warning("请选择至少一个雷达进行仿真")
                else:
                    st.session_state.simulation_params = {
                        "scenario": scenario_option,
                        "radars": selected_radars,
                        "duration": sim_duration,
                        "time_step": time_step
                    }
                    st.session_state.current_view = "simulation_results"
                    st.rerun()
            
            # 历史仿真结果
            st.subheader("📋 历史仿真记录")
            self._render_simulation_history()
    
    def _render_simulation_history(self):
        """渲染仿真历史记录"""
        # 这里可以连接数据库或文件存储来获取历史记录
        st.info("仿真历史记录功能开发中...")
    
    def render_system_settings(self, tab):
        """渲染系统设置选项卡"""
        with tab:
            # st.header("⚙️ 系统设置")
            
            # 数据管理
            st.markdown("###### 💾 数据管理")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("导出系统配置", key="btn_export_config"):
                    self._export_system_config()
                
                if st.button("导入雷达数据", key="btn_import_radar"):
                    self._import_radar_data()
            
            with col2:
                if st.button("清空所有数据", key="btn_clear_all"):
                    if st.checkbox("确认清空所有数据？此操作不可恢复"):
                        self._clear_all_data()
            
            # 显示设置
            st.markdown("###### 🎨 显示设置")
            theme = st.selectbox("界面主题", ["浅色", "深色", "自动"])
            chart_style = st.selectbox("图表样式", ["Plotly", "Matplotlib", "Altair"])
            
            # 性能设置
            st.markdown("###### ⚡ 性能设置")
            cache_enabled = st.checkbox("启用缓存", value=True)
            parallel_processing = st.checkbox("启用并行处理", value=False)
            
            if st.button("保存设置", key="btn_save_settings"):
                st.success("系统设置已保存")
    
    def _export_system_config(self):
        """导出系统配置"""
        st.success("系统配置导出功能开发中...")
    
    def _import_radar_data(self):
        """导入雷达数据"""
        uploaded_file = st.file_uploader("选择雷达数据文件", type=['json', 'csv', 'xml'])
        if uploaded_file is not None:
            st.success(f"文件 {uploaded_file.name} 上传成功，解析功能开发中...")
    
    def _clear_all_data(self):
        """清空所有数据"""
        if hasattr(self.radar_system, 'radars'):
            self.radar_system.radars.clear()
        st.success("所有数据已清空")
        st.rerun()
    
    def _render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.title("🛰️ 雷达工厂")
            st.markdown("---")
            
            # 显示系统状态
            st.subheader("📊 系统状态")
            radar_count = len(self.radar_system.radars) if hasattr(self.radar_system, 'radars') else 0
            st.metric("雷达总数", radar_count)
            st.metric("仿真次数", 0)
            st.metric("最近活动", "刚刚")
            
            st.markdown("---")
            
            # 快速导航
            st.subheader("🔍 快速导航")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 仪表板", key="sidebar_btn_dashboard"):
                    st.session_state.current_view = "dashboard"
                    st.rerun()
            
            with col2:
                if st.button("⚙️ 雷达设计", key="sidebar_btn_editor"):
                    st.session_state.current_view = "radar_editor"
                    st.rerun()
            
            col3, col4 = st.columns(2)
            with col3:
                if st.button("🎯 仿真分析", key="sidebar_btn_simulation"):
                    st.session_state.current_view = "simulation"
                    st.rerun()
            
            with col4:
                if st.button("📈 性能对比", key="sidebar_btn_comparison"):
                    st.session_state.current_view = "comparison"
                    st.rerun()
    
    def render(self):
        """渲染完整仪表板"""
        # 初始化session state
        if 'current_view' not in st.session_state:
            st.session_state.current_view = "dashboard"
        
        # 渲染侧边栏
        # self._render_sidebar()
        
        # 渲染头部和选项卡
        tab1, tab2, tab3, tab4 = self.render_header()
        
        # 根据当前视图渲染不同内容
        if st.session_state.current_view == "dashboard":
            self.render_system_overview(tab1)
            self.render_radar_management(tab2)
            self.render_simulation_analysis(tab3)
            self.render_system_settings(tab4)
        else:
            # 如果当前视图不是仪表板，显示提示信息
            st.warning(f"当前视图: {st.session_state.current_view}")
            if st.button("返回仪表板", key="btn_back_to_dashboard"):
                st.session_state.current_view = "dashboard"
                st.rerun()


def main():
    """主函数"""
    # 初始化雷达系统
    radar_system = RadarSystem()
    
    # 创建仪表板视图
    dashboard = DashboardView(radar_system)
    
    # 渲染仪表板
    dashboard.render()


if __name__ == "__main__":
    main()


