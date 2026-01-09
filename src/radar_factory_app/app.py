"""
雷达工厂 - 主应用入口
基于Streamlit的交互式雷达系统设计与仿真平台
集成MVC架构，使用工厂模式创建和管理雷达系统
"""

import traceback
import streamlit as st
import sys
import os
from typing import Dict, Any, Optional
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入视图模块
from views.dashboard import DashboardView
from views.radar_editor import RadarEditorView
from views.simulation_view import SimulationView
from views.comparison_view import ComparisonView

# 导入控制器和服务
from controllers.radar_controller import RadarController
from services.radar_simulator import RadarSimulator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RadarFactoryApp:
    """雷达工厂主应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.setup_page_config()
        self.initialize_session_state()
        self.initialize_controllers()
        
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="雷达工厂",
            page_icon="🛰️",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/your-repo/radar-factory',
                'Report a bug': 'https://github.com/your-repo/radar-factory/issues',
                'About': """
                # 雷达工厂 🛰️
                
                一个基于MVC架构的雷达系统设计与仿真平台。
                
                ## 功能特性
                - 🎯 雷达系统设计与建模
                - 📡 多雷达性能对比分析
                - 🎯 空中小目标检测仿真
                - 📊 交互式数据可视化
                - 🔧 基于radarsimpy的雷达仿真
                
                ## 技术栈
                - Streamlit (前端框架)
                - radarsimpy (雷达仿真)
                - Plotly/Matplotlib (数据可视化)
                - NumPy/SciPy (科学计算)
                
                ## 架构设计
                - MVC设计模式
                - 工厂模式创建雷达实例
                - 模块化、可扩展架构
                """
            }
        )
        
        # 自定义CSS样式
        st.markdown("""
        <style>
        /* 主容器样式 */
        .main-container {
            max-width: 100%;
            padding: 0 1rem;
        }
        
        /* 侧边栏样式 */
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        
        /* 卡片样式 */
        .stCard {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        /* 按钮样式 */
        .stButton > button {
            width: 100%;
            border-radius: 5px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* 进度条样式 */
        .stProgress > div > div > div {
            background-color: #2E86AB;
        }
        
        /* 数据框样式 */
        .stDataFrame {
            border-radius: 5px;
            overflow: hidden;
        }
        
        /* 标签页样式 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0px 0px;
            gap: 1rem;
            padding: 10px 20px;
        }
        
        /* 警告框样式 */
        .stAlert {
            border-radius: 8px;
        }
        
        /* 工具提示样式 */
        .stTooltip {
            max-width: 300px;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .main-container {
                padding: 0 0.5rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """初始化session state变量"""
        # 当前视图
        if 'current_view' not in st.session_state:
            st.session_state.current_view = "dashboard"
        
        # 雷达编辑状态
        if 'editing_radar_id' not in st.session_state:
            st.session_state.editing_radar_id = None
        
        # 仿真结果
        if 'simulation_results' not in st.session_state:
            st.session_state.simulation_results = None
        
        # 选择的雷达
        if 'selected_radars' not in st.session_state:
            st.session_state.selected_radars = []
        
        # 仿真参数
        if 'simulation_params' not in st.session_state:
            st.session_state.simulation_params = {}
        
        # 用户偏好
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {
                'theme': 'light',
                'chart_style': 'plotly',
                'auto_save': True
            }
        
        # 应用状态
        if 'app_state' not in st.session_state:
            st.session_state.app_state = {
                'initialized': True,
                'last_operation': None,
                'data_loaded': False
            }
        
        # 雷达数据
        if 'radar_edit_data' not in st.session_state:
            st.session_state.radar_edit_data = None
        
        # 比较结果
        if 'comparison_results' not in st.session_state:
            st.session_state.comparison_results = None
    
    def initialize_controllers(self):
        """初始化控制器和服务"""
        # 使用单例模式，确保只初始化一次
        if 'radar_controller' not in st.session_state:
            st.session_state.radar_controller = RadarController()
        
        if 'radar_simulator' not in st.session_state:
            st.session_state.radar_simulator = RadarSimulator()
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.title("🛰️ 雷达工厂")
            st.markdown("---")
            
            # 快速导航
            st.subheader("🔍 快速导航")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 仪表板", key="sidebar_btn_dashboard", width='stretch'):
                    st.session_state.current_view = "dashboard"
                    st.rerun()
            
            with col2:
                if st.button("⚙️ 雷达设计", key="sidebar_btn_editor", width='stretch'):
                    st.session_state.current_view = "radar_editor"
                    st.rerun()
            
            col3, col4 = st.columns(2)
            with col3:
                if st.button("🎯 仿真分析", key="sidebar_btn_simulation", width='stretch'):
                    st.session_state.current_view = "simulation"
                    st.rerun()
            
            with col4:
                if st.button("📈 性能对比", key="sidebar_btn_comparison", width='stretch'):
                    st.session_state.current_view = "comparison"
                    st.rerun()
            
            st.markdown("---")
            
            # 雷达系统状态 - 优化布局
            st.subheader("📡 系统状态")
            
            controller = st.session_state.radar_controller
            stats = controller.get_statistics()
            
            # 使用紧凑的水平布局
            self._render_compact_metrics(stats)
            
            st.markdown("---")
            
            # 快速操作
            st.subheader("🚀 快速操作")
            
            if st.button("🆕 新建雷达", key="sidebar_btn_new_radar", width='stretch'):
                st.session_state.editing_radar_id = None
                st.session_state.current_view = "radar_editor"
                st.rerun()
            
            if st.button("🔄 运行仿真", key="sidebar_btn_run_sim", width='stretch'):
                st.session_state.current_view = "simulation"
                st.rerun()
            
            if st.button("📤 导出数据", key="sidebar_btn_export", width='stretch'):
                self._export_all_data()
            
            st.markdown("---")
            
            # 系统设置
            st.subheader("⚙️ 设置")
            
            # 主题选择
            theme = st.selectbox(
                "界面主题",
                ["浅色", "深色", "自动"],
                index=0,
                key="sidebar_theme_select"
            )
            
            # 数据管理
            if st.button("清空缓存", key="sidebar_btn_clear_cache", width='stretch'):
                controller.clear_cache()
                st.success("缓存已清空")
                st.rerun()
            
            # 应用信息
            st.markdown("---")
            st.caption("版本: 1.0.0")
            st.caption("最后更新: 2026-01-05")

    def _render_compact_metrics(self, stats: Dict[str, Any]):
        """使用Streamlit columns渲染紧凑指标"""
        # 使用三列布局
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="雷达总数", 
                value=stats.get('total_radars', 0),
                label_visibility="visible"
            )
        
        with col2:
            st.metric(
                label="频段数量", 
                value=stats.get('bands_represented', 0),
                label_visibility="visible"
            )
        
        with col3:
            st.metric(
                label="平台类型", 
                value=stats.get('platforms_represented', 0),
                label_visibility="visible"
            )
        
        # 添加分隔线
        st.markdown("---")
        
        # 如果有更多指标，可以继续添加
        if 'total_power' in stats:
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric(
                    label="总功率", 
                    value=f"{stats['total_power']/1000:.1f}kW",
                    label_visibility="visible"
                )
    def _export_all_data(self):
        """导出所有数据"""
        st.info("数据导出功能开发中...")
        # 这里可以实现完整的数据导出逻辑
    
    def render_current_view(self):
        """渲染当前视图"""
        current_view = st.session_state.current_view
        
        # 根据当前视图渲染对应的组件
        if current_view == "dashboard":
            self._render_dashboard_view()
        
        elif current_view == "radar_editor":
            self._render_radar_editor_view()
        
        elif current_view == "simulation":
            self._render_simulation_view()
        
        elif current_view == "comparison":
            self._render_comparison_view()
        
        elif current_view == "simulation_results":
            self._render_simulation_results_view()
        
        else:
            # 默认显示仪表板
            st.session_state.current_view = "dashboard"
            st.rerun()
    
    def _render_dashboard_view(self):
        """渲染仪表板视图"""
        try:
            controller = st.session_state.radar_controller
            radar_system = controller.radar_system
            
            # 创建仪表板视图实例
            dashboard = DashboardView(radar_system)
            dashboard.render()
            
        except Exception as e:
            logger.error(f"渲染仪表板时发生错误: {str(e)}")
            st.error(f"加载仪表板时发生错误: {str(e)}")
            st.button("返回首页", on_click=lambda: setattr(st.session_state, 'current_view', 'dashboard'))
    
    def _render_radar_editor_view(self):
        """渲染雷达编辑器视图"""
        try:
            # 创建雷达编辑器实例
            editor = RadarEditorView()
            editor.render()
            
        except Exception as e:
            exec_str = traceback.format_exc()
            logger.error(f"渲染雷达编辑器时发生错误: {exec_str}")
            st.error(f"加载雷达编辑器时发生错误: {str(e)}")
            st.button("返回首页", on_click=lambda: setattr(st.session_state, 'current_view', 'dashboard'))
    
    def _render_simulation_view(self):
        """渲染仿真视图"""
        try:
            # 创建仿真视图实例
            simulation_view = SimulationView()
            
            # 如果有仿真结果，显示结果，否则显示设置界面
            if st.session_state.simulation_results:
                simulation_view.render(st.session_state.simulation_results)
            else:
                simulation_view.render()
                
        except Exception as e:
            logger.error(f"渲染仿真视图时发生错误: {str(e)}")
            st.error(f"加载仿真界面时发生错误: {str(e)}")
            st.button("返回首页", on_click=lambda: setattr(st.session_state, 'current_view', 'dashboard'))
    
    def _render_comparison_view(self):
        """渲染对比分析视图"""
        try:
            # 创建对比分析视图实例
            comparison_view = ComparisonView()
            comparison_view.render()
            
        except Exception as e:
            logger.error(f"渲染对比视图时发生错误: {str(e)}")
            st.error(f"加载对比分析界面时发生错误: {str(e)}")
            st.button("返回首页", on_click=lambda: setattr(st.session_state, 'current_view', 'dashboard'))
    
    def _render_simulation_results_view(self):
        """渲染仿真结果视图"""
        try:
            # 如果有仿真结果，显示结果
            if st.session_state.simulation_results:
                simulation_view = SimulationView()
                simulation_view.render(st.session_state.simulation_results)
            else:
                st.warning("没有可用的仿真结果")
                st.session_state.current_view = "simulation"
                st.rerun()
                
        except Exception as e:
            logger.error(f"渲染仿真结果时发生错误: {str(e)}")
            st.error(f"加载仿真结果时发生错误: {str(e)}")
            st.button("返回仿真设置", on_click=lambda: setattr(st.session_state, 'current_view', 'simulation'))
    
    def render_header(self):
        """渲染应用头部"""
        col1, col2, col3 = st.columns([8, 1, 2])
        
        with col1:
            st.title("🛰️ 长城数字雷达工厂")
            st.caption("面向全数字仿真电子战需求的雷达系统设计与仿真平台")
        
        with col2:
            pass
        
        with col3:
            # 显示当前视图
            view_names = {
                "dashboard": "仪表板",
                "radar_editor": "雷达设计",
                "simulation": "仿真分析",
                "comparison": "性能对比",
                "simulation_results": "仿真结果"
            }
            
            current_view_name = view_names.get(
                st.session_state.current_view, 
                st.session_state.current_view
            )
            st.caption(f"当前视图: **{current_view_name}**")            
            # 用户操作状态
            if st.session_state.get('simulation_results'):
                st.success("✅ 仿真完成")
            elif st.session_state.get('editing_radar_id'):
                st.info("📝 编辑中")
            else:
                st.info("⚡ 就绪")
        
        st.markdown("---")
    
    def run_simulation(self, params: Dict[str, Any]):
        """运行仿真"""
        with st.spinner("正在运行仿真..."):
            try:
                # 获取雷达
                controller = st.session_state.radar_controller
                simulator = st.session_state.radar_simulator
                
                # 从参数获取雷达
                radar_ids = params.get('radars', [])
                radars = []
                for radar_id in radar_ids:
                    radar = controller.get_radar_by_id(radar_id)
                    if radar:
                        radars.append(radar)
                
                if not radars:
                    st.error("没有有效的雷达进行仿真")
                    return
                
                # 创建场景（简化，实际应从params创建完整场景）
                from models.simulation_models import (
                    SimulationScenario, TargetParameters, TargetType, RCSModel
                )
                import numpy as np
                
                # 创建示例场景
                scenario = SimulationScenario(
                    scenario_id="user_scenario_001",
                    name="用户仿真场景",
                    description="基于用户设置的仿真场景",
                    duration=params.get('duration', 60.0),
                    time_step=params.get('time_step', 0.1),
                    radar_positions={r.radar_id: np.array([0, 0, 0]) for r in radars},
                    targets=[
                        TargetParameters(
                            target_id="user_target_001",
                            target_type=TargetType.AIRCRAFT,
                            position=np.array([100e3, 0, 10e3]),
                            velocity=np.array([-300, 0, 0]),
                            rcs_sqm=5.0,
                            rcs_model=RCSModel.SWERLING1
                        )
                    ]
                )
                
                # 运行仿真
                results = simulator.run_simulation(scenario, radars)
                
                # 保存结果
                st.session_state.simulation_results = results
                
                # 切换到结果视图
                st.session_state.current_view = "simulation_results"
                
                st.success("仿真完成！")
                
            except Exception as e:
                logger.error(f"仿真运行时发生错误: {str(e)}")
                st.error(f"仿真失败: {str(e)}")
    
    def run(self):
        """运行主应用"""
        try:
            # 渲染侧边栏
            self.render_sidebar()
            
            # 渲染头部
            self.render_header()
            
            # 渲染当前视图
            self.render_current_view()
            
            # 底部信息
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.caption("© 2026 雷达工厂")
            
            with col2:
                st.caption("技术支持: radar.factory@example.com")
            
            with col3:
                st.caption(f"雷达数量: {len(st.session_state.radar_controller.get_all_radars())}")
        
        except Exception as e:
            logger.error(f"运行应用时发生错误: {str(e)}")
            st.error("应用程序发生错误，请刷新页面重试")
            
            # 错误恢复
            if st.button("重新加载应用"):
                st.session_state.clear()
                st.rerun()


def main():
    """主函数"""
    # 创建应用实例
    app = RadarFactoryApp()
    
    # 运行应用
    app.run()


if __name__ == "__main__":
    main()