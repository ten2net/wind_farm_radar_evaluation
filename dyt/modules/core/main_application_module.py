# main_application_module.py
import streamlit as st
import sys
import os
import importlib
from pathlib import Path
import tempfile
import time
from datetime import datetime
import webbrowser

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
class ApplicationConfig:
    """应用程序配置类"""
    
    def __init__(self):
        self.app_title = "导引头电子战仿真分析系统"
        self.app_version = "2.0.0"
        self.author = "电子战仿真团队"
        self.description = "基于Streamlit的被动/主动/复合导引头电子战性能仿真分析平台"
        
        # 功能模块开关
        self.modules_enabled = {
            'core': True,
            'visualization': True,
            'simulation_control': True,
            'advanced_features': True,
            'multi_user': False,  # 默认关闭多用户功能
            'export': True
        }
        
        # 界面配置
        self.theme_config = {
            'primary_color': '#1f77b4',
            'background_color': '#f0f2f6',
            'secondary_color': '#ff7f0e'
        }
        
    def get_app_info(self):
        """获取应用程序信息"""
        return {
            'title': self.app_title,
            'version': self.app_version,
            'author': self.author,
            'description': self.description,
            'modules': self.modules_enabled
        }

class ApplicationInitializer:
    """应用程序初始化器"""
    
    def __init__(self):
        self.config = ApplicationConfig()
        self.modules_loaded = {}
        self.is_initialized = False
        
    def initialize_application(self):
        """初始化应用程序"""
        try:
            # 设置页面配置
            st.set_page_config(
                page_title=self.config.app_title,
                page_icon="🛰️",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            
            # 加载CSS样式
            self._load_custom_styles()
            
            # 初始化模块
            self._initialize_modules()
            
            # 创建数据目录
            self._create_data_directories()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            st.error(f"应用程序初始化失败: {e}")
            return False
    
    def _load_custom_styles(self):
        """加载自定义CSS样式"""
        st.markdown("""
        <style>
        /* 主标题样式 */
        .main-title {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        
        /* 模块卡片样式 */
        .module-card {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #1f77b4;
        }
        
        /* 状态指示器样式 */
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-active { background-color: #28a745; }
        .status-inactive { background-color: #dc3545; }
        .status-warning { background-color: #ffc107; }
        
        /* 按钮样式增强 */
        .stButton button {
            border-radius: 5px;
            font-weight: bold;
        }
        
        /* 指标卡片样式 */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _initialize_modules(self):
        """初始化各功能模块 - 修复版本"""
        # 修正模块映射：使用实际存在的类名
        modules_to_load = {
            'core': ('core_module', 'SimulationEngine'),  # 改为实际存在的类
            'visualization': ('map_visualization_module', 'VisualizationToolkit'),
            'simulation_control': ('simulation_control_module', 'SimulationUI'),
            'advanced_features': ('advanced_features_module', 'AdvancedIntegration'),
        }
        
        for module_name, (file_name, class_name) in modules_to_load.items():
            if self.config.modules_enabled.get(module_name, False):
                try:
                    # 动态导入模块
                    module = importlib.import_module(file_name)
                    
                    # 检查类是否存在
                    if hasattr(module, class_name):
                        module_class = getattr(module, class_name)
                        self.modules_loaded[module_name] = module_class()
                        st.success(f"✅ {module_name} 模块加载成功")
                    else:
                        st.warning(f"⚠️ {module_name} 模块中未找到类: {class_name}")
                        self.modules_loaded[module_name] = self._create_fallback_module(module_name)
                        
                except ImportError as e:
                    st.error(f"❌ {module_name} 模块导入失败: {e}")
                    self.modules_loaded[module_name] = self._create_fallback_module(module_name)
                except Exception as e:
                    st.error(f"❌ {module_name} 模块加载失败: {e}")
                    self.modules_loaded[module_name] = self._create_fallback_module(module_name)
            else:
                st.info(f"⏭️ {module_name} 模块已禁用")
                self.modules_loaded[module_name] = None
    
    def _create_fallback_module(self, module_name):
        """创建备用模块实例"""
        st.warning(f"为 {module_name} 模块创建备用实例")
        
        # 为每个模块类型提供基本的备用实现
        if module_name == 'core':
            return self._create_core_fallback()
        elif module_name == 'visualization':
            return self._create_visualization_fallback()
        else:
            return None
    
    def _create_core_fallback(self):
        """创建核心模块备用实例"""
        # 创建一个简单的核心模块备用实现
        class FallbackCoreModule:
            def __init__(self):
                self.name = "Fallback Core Module"
                self.status = "fallback"
                
            def get_status(self):
                return {"status": "fallback", "message": "使用备用核心模块"}
        
        return FallbackCoreModule()
    
    def _create_visualization_fallback(self):
        """创建可视化模块备用实例"""
        class FallbackVisualizationToolkit:
            def __init__(self):
                self.name = "Fallback Visualization Toolkit"
                
            def create_basic_map(self):
                import folium
                return folium.Map(location=[35.0, 115.0], zoom_start=6)
        
        return FallbackVisualizationToolkit()
    
    def _create_data_directories(self):
        """创建数据目录"""
        directories = ['data', 'exports', 'logs', 'temp']
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)

class MainApplication:
    """主应用程序类"""
    
    def __init__(self):
        self.initializer = ApplicationInitializer()
        self.config = self.initializer.config
        self.modules = self.initializer.modules_loaded
        self.current_page = "dashboard"
        self.user_session = {}
        
    def run(self):
        """运行主应用程序"""
        if not self.initializer.is_initialized:
            if not self.initializer.initialize_application():
                return
        
        # 显示应用程序标题
        self._display_header()
        
        # 显示侧边栏导航
        self._display_sidebar()
        
        # 显示主内容区域
        self._display_main_content()
        
        # 显示页脚
        self._display_footer()
    
    def _display_header(self):
        """显示应用程序标题"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <h1 class="main-title">🛰️ {self.config.app_title}</h1>
                <p style="color: #666; font-size: 1.1rem;">版本 {self.config.app_version} | {self.config.description}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 显示系统状态
        self._display_system_status()
    
    def _display_system_status(self):
        """显示系统状态"""
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_color = "status-active" if self.initializer.is_initialized else "status-inactive"
            st.markdown(f"""
            <div class="module-card">
                <span class="status-indicator {status_color}"></span>
                <strong>系统状态:</strong> {"运行中" if self.initializer.is_initialized else "未初始化"}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            loaded_modules = sum(1 for m in self.modules.values() if m is not None)
            total_modules = len(self.modules)
            st.markdown(f"""
            <div class="module-card">
                <span class="status-indicator status-active"></span>
                <strong>模块加载:</strong> {loaded_modules}/{total_modules}
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.markdown(f"""
            <div class="module-card">
                <span class="status-indicator status-active"></span>
                <strong>当前时间:</strong> {current_time}
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # 快速操作按钮
            if st.button("🔄 刷新系统", use_container_width=True):
                st.rerun()
    
    def _display_sidebar(self):
        """显示侧边栏导航"""
        with st.sidebar:
            st.markdown("## 🧭 导航菜单")
            
            # 页面选择
            page_options = {
                "dashboard": "📊 控制面板",
                "simulation": "🎮 仿真控制",
                "analysis": "📈 数据分析",
                "visualization": "🗺️ 战场可视化",
                "scenarios": "🌍 场景管理",
                "reports": "📋 报告生成",
                "settings": "⚙️ 系统设置"
            }
            
            selected_page = st.selectbox(
                "选择页面",
                options=list(page_options.keys()),
                format_func=lambda x: page_options[x],
                index=0
            )
            self.current_page = selected_page
            
            st.markdown("---")
            
            # 快速操作面板
            st.markdown("### ⚡ 快速操作")
            
            if st.button("🚀 新建仿真", use_container_width=True):
                self._create_new_simulation()
            
            if st.button("💾 保存进度", use_container_width=True):
                self._save_current_session()
            
            if st.button("📤 导出报告", use_container_width=True):
                self._export_reports()
            
            st.markdown("---")
            
            # 系统信息
            st.markdown("### ℹ️ 系统信息")
            st.write(f"**版本:** {self.config.app_version}")
            st.write(f"**作者:** {self.config.author}")
            st.write(f"**更新时间:** 2024-01-01")
            
            # 系统资源监控
            st.markdown("---")
            st.markdown("### 📊 资源监控")
            self._display_resource_monitor()
    
    def _display_resource_monitor(self):
        """显示资源监控"""
        # 模拟资源使用情况
        import psutil
        import time
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        st.metric("CPU使用率", f"{cpu_percent}%")
        
        # 内存使用
        memory = psutil.virtual_memory()
        st.metric("内存使用", f"{memory.percent}%")
        
        # 磁盘使用
        disk = psutil.disk_usage('/')
        st.metric("磁盘使用", f"{disk.percent}%")
        
        # 网络状态
        try:
            net_io = psutil.net_io_counters()
            st.metric("网络活动", "正常")
        except:
            st.metric("网络活动", "未知")
    
    def _display_main_content(self):
        """显示主内容区域"""
        # 根据当前页面显示相应内容
        page_handlers = {
            "dashboard": self._show_dashboard,
            "simulation": self._show_simulation_control,
            "analysis": self._show_data_analysis,
            "visualization": self._show_visualization,
            "scenarios": self._show_scenario_management,
            "reports": self._show_report_generation,
            "settings": self._show_system_settings
        }
        
        handler = page_handlers.get(self.current_page, self._show_dashboard)
        handler()
    
    def _show_dashboard(self):
        """显示控制面板"""
        st.header("📊 系统控制面板")
        
        # 欢迎信息
        st.markdown("""
        <div class="module-card">
            <h3>👋 欢迎使用导引头电子战仿真系统</h3>
            <p>这是一个专业的电子战仿真分析平台，支持被动、主动和复合导引头的性能仿真和评估。</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 关键指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🎯 仿真场景</h3>
                <p style="font-size: 2rem; margin: 0;">12</p>
                <p>已配置场景</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>📈 分析报告</h3>
                <p style="font-size: 2rem; margin: 0;">47</p>
                <p>已生成报告</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🛰️ 导引头类型</h3>
                <p style="font-size: 2rem; margin: 0;">3</p>
                <p>支持的类型</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>⚡ 仿真次数</h3>
                <p style="font-size: 2rem; margin: 0;">156</p>
                <p>累计仿真</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 快速开始区域
        st.markdown("---")
        st.header("🚀 快速开始")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("新建仿真场景", use_container_width=True, icon="🌍"):
                self._create_new_scenario()
        
        with col2:
            if st.button("导入历史数据", use_container_width=True, icon="📁"):
                self._import_historical_data()
        
        with col3:
            if st.button("查看使用教程", use_container_width=True, icon="📚"):
                self._show_tutorial()
        
        # 最近活动
        st.markdown("---")
        st.header("📅 最近活动")
        
        recent_activities = [
            {"time": "10:30", "action": "完成了空战场景仿真", "user": "管理员"},
            {"time": "09:15", "action": "导出了海上作战分析报告", "user": "分析师"},
            {"time": "昨天", "action": "创建了新的干扰对抗场景", "user": "工程师"},
            {"time": "昨天", "action": "优化了地形分析算法", "user": "开发员"}
        ]
        
        for activity in recent_activities:
            st.markdown(f"""
            <div style="padding: 10px; border-left: 3px solid #1f77b4; margin: 5px 0; background: #f8f9fa;">
                <strong>{activity['time']}</strong> - {activity['action']}
                <br><small>由 {activity['user']} 执行</small>
            </div>
            """, unsafe_allow_html=True)
    
    def _show_simulation_control(self):
        """显示仿真控制页面"""
        st.header("🎮 仿真控制中心")
        
        if 'simulation_control' not in self.modules:
            st.error("仿真控制模块未加载")
            return
        
        # 创建仿真控制界面
        simulation_ui = self.modules['simulation_control']
        
        # 创建两列布局
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 仿真可视化区域
            st.subheader("📊 实时仿真可视化")
            self._display_simulation_visualization()
        
        with col2:
            # 控制面板
            st.subheader("🎛️ 控制面板")
            simulation_ui.create_control_panel()
            
            # 导引头配置
            st.subheader("🎯 导引头配置")
            simulation_ui.create_guidance_system_panel()
            
            # 数据管理
            st.subheader("💾 数据管理")
            simulation_ui.create_data_management_panel()
    
    def _show_data_analysis(self):
        """显示数据分析页面"""
        st.header("📈 数据分析中心")
        
        if 'advanced_features' not in self.modules:
            st.error("高级功能模块未加载")
            return
        
        advanced_module = self.modules['advanced_features']
        
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 性能分析", "🎯 多目标分析", "⚡ 电子对抗分析", "🤖 AI智能分析"
        ])
        
        with tab1:
            self._show_performance_analysis(advanced_module)
        
        with tab2:
            self._show_multi_target_analysis(advanced_module)
        
        with tab3:
            self._show_ew_analysis(advanced_module)
        
        with tab4:
            self._show_ai_analysis(advanced_module)
    
    def _show_visualization(self):
        """显示可视化页面"""
        st.header("🗺️ 战场可视化中心")
        
        if 'visualization' not in self.modules:
            st.error("可视化模块未加载")
            return
        
        visualization_toolkit = self.modules['visualization']
        
        # 创建可视化布局
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("🌍 战场态势图")
            self._display_battlefield_map(visualization_toolkit)
        
        with col2:
            st.subheader("⚙️ 可视化设置")
            self._display_visualization_controls(visualization_toolkit)
            
            st.subheader("📐 测量工具")
            self._display_measurement_tools()
    
    def _show_scenario_management(self):
        """显示场景管理页面"""
        st.header("🌍 场景管理中心")
        
        if 'simulation_control' not in self.modules:
            st.error("仿真控制模块未加载")
            return
        
        simulation_ui = self.modules['simulation_control']
        
        # 场景管理界面
        simulation_ui.create_scenario_panel()
        
        # 场景预览
        st.markdown("---")
        st.subheader("👁️ 场景预览")
        self._display_scenario_preview()
    
    def _show_report_generation(self):
        """显示报告生成页面"""
        st.header("📋 报告生成中心")
        
        # 报告类型选择
        report_types = {
            "performance": "性能分析报告",
            "technical": "技术评估报告",
            "executive": "执行摘要报告",
            "comparative": "对比分析报告"
        }
        
        selected_report = st.selectbox(
            "选择报告类型",
            options=list(report_types.keys()),
            format_func=lambda x: report_types[x]
        )
        
        # 报告配置
        st.subheader("⚙️ 报告配置")
        col1, col2 = st.columns(2)
        
        with col1:
            report_title = st.text_input("报告标题", "导引头性能分析报告")
            include_charts = st.checkbox("包含图表", value=True)
            include_raw_data = st.checkbox("包含原始数据", value=False)
        
        with col2:
            report_format = st.selectbox("输出格式", ["PDF", "HTML", "Word", "Excel"])
            time_range = st.selectbox("时间范围", ["最近一次", "今天", "本周", "本月", "自定义"])
        
        # 生成报告
        if st.button("🔄 生成报告", icon="📊"):
            self._generate_report({
                'type': selected_report,
                'title': report_title,
                'format': report_format,
                'include_charts': include_charts,
                'include_raw_data': include_raw_data
            })
    
    def _show_system_settings(self):
        """显示系统设置页面"""
        st.header("⚙️ 系统设置")
        
        # 基本设置
        st.subheader("🔧 基本设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 界面设置
            st.markdown("#### 🎨 界面设置")
            theme = st.selectbox("主题", ["浅色", "深色", "自动"])
            language = st.selectbox("语言", ["中文", "English"])
            timezone = st.selectbox("时区", ["北京时间", "UTC", "自动检测"])
        
        with col2:
            # 仿真设置
            st.markdown("#### ⚡ 仿真设置")
            default_time_step = st.number_input("默认时间步长(s)", 0.01, 5.0, 0.1)
            auto_save_interval = st.number_input("自动保存间隔(min)", 1, 60, 5)
            max_simulation_time = st.number_input("最大仿真时间(min)", 1, 240, 60)
        
        # 模块管理
        st.markdown("---")
        st.subheader("📦 模块管理")
        
        for module_name, enabled in self.config.modules_enabled.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{module_name}模块**")
            with col2:
                new_status = st.checkbox("启用", value=enabled, key=f"module_{module_name}")
                if new_status != enabled:
                    self.config.modules_enabled[module_name] = new_status
                    st.success(f"{module_name}模块状态已更新")
        
        # 数据管理
        st.markdown("---")
        st.subheader("💾 数据管理")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 清空临时文件", icon="⚠️"):
                self._clear_temp_files()
            
            if st.button("📊 备份系统数据", icon="💾"):
                self._backup_system_data()
        
        with col2:
            if st.button("🔄 重置系统设置", icon="🔄"):
                self._reset_system_settings()
            
            if st.button("📋 系统诊断", icon="🔍"):
                self._run_system_diagnostic()
    
    def _display_simulation_visualization(self):
        """显示仿真可视化"""
        # 这里放置仿真可视化的具体实现
        st.info("仿真可视化区域 - 实时显示仿真进度和结果")
        
        # 模拟仿真进度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            # 更新进度条
            progress_bar.progress(i + 1)
            status_text.text(f"仿真进度: {i + 1}%")
            time.sleep(0.02)
        
        status_text.text("仿真完成!")
        
        # 显示仿真结果图表
        self._display_simulation_results()
        
    def _display_simulation_results(self):
        """显示仿真结果图表"""
        st.subheader("📈 仿真结果")
        
        # 创建示例仿真结果数据
        import pandas as pd
        import numpy as np
        
        # 生成示例时间序列数据
        time_points = np.arange(0, 100, 1)
        performance = np.sin(time_points * 0.1) * 0.4 + 0.5  # 模拟性能波动
        distance = np.linspace(200, 10, 100)  # 距离从200km减少到10km
        jamming = np.random.uniform(0.1, 0.8, 100)  # 随机干扰
        
        # 创建图表
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['性能时间线', '目标距离变化', '干扰强度', '综合态势'],
            specs=[[{"secondary_y": True}, {}],
                  [{"colspan": 2}, None]]
        )
        
        # 性能时间线
        fig.add_trace(
            go.Scatter(x=time_points, y=performance, name="性能", line=dict(color='blue')),
            row=1, col=1
        )
        
        # 目标距离
        fig.add_trace(
            go.Scatter(x=time_points, y=distance, name="目标距离", line=dict(color='red')),
            row=1, col=2
        )
        
        # 干扰强度
        fig.add_trace(
            go.Bar(x=time_points[::5], y=jamming[::5], name="干扰强度", marker_color='orange'),
            row=2, col=1
        )
        
        fig.update_layout(height=600, showlegend=True, title_text="仿真结果分析")
        st.plotly_chart(fig, use_container_width=True)
        
        # 添加关键指标
        st.subheader("📊 关键性能指标")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均性能", f"{np.mean(performance)*100:.1f}%")
        with col2:
            st.metric("最终距离", f"{distance[-1]:.1f} km")
        with col3:
            st.metric("平均干扰", f"{np.mean(jamming)*100:.1f}%")
        with col4:
            success = "成功" if performance[-1] > 0.4 else "失败"
            st.metric("任务结果", success)

    def _show_performance_analysis(self, advanced_module):
        """显示性能分析"""
        st.subheader("📊 性能分析")
        
        # 创建示例分析图表
        import plotly.graph_objects as go
        import numpy as np
        
        # 雷达图 - 性能对比
        categories = ['探测距离', '抗干扰', '精度', '隐蔽性', '可靠性']
        
        fig = go.Figure()
        
        # 添加不同导引头的性能数据
        systems = {
            '被动雷达': [0.8, 0.7, 0.6, 0.9, 0.8],
            '主动雷达': [1.0, 0.4, 0.8, 0.2, 0.85],
            '复合制导': [0.9, 0.8, 0.9, 0.7, 0.9]
        }
        
        for name, values in systems.items():
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=name
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            title="导引头性能对比"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 添加详细分析
        st.subheader("📈 详细分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **性能分析要点:**
            1. 被动雷达在隐蔽性方面表现最佳
            2. 主动雷达在探测距离和精度方面有优势
            3. 复合制导在抗干扰和可靠性方面表现均衡
            4. 系统选择应根据具体作战任务
            """)
        
        with col2:
            st.warning("""
            **优化建议:**
            1. 考虑使用复合制导提升整体性能
            2. 优化天线设计以提高探测距离
            3. 增加频率捷变能力提升抗干扰
            4. 改善信号处理算法提高精度
            """)

    def _show_multi_target_analysis(self, advanced_module):
        """显示多目标分析"""
        st.subheader("🎯 多目标分析")
        
        # 创建示例多目标分析
        import plotly.express as px
        import pandas as pd
        
        # 创建示例数据
        data = {
            'target_id': ['Target_1', 'Target_2', 'Target_3', 'Target_4'],
            'priority': [0.9, 0.7, 0.6, 0.5],
            'distance': [50, 80, 120, 150],
            'threat_level': [0.8, 0.6, 0.4, 0.3],
            'type': ['预警机', '战斗机', '军舰', '雷达站']
        }
        
        df = pd.DataFrame(data)
        
        # 创建水平条形图
        fig = px.bar(
            df.sort_values('priority'),
            y='target_id',
            x='priority',
            color='threat_level',
            hover_data=['distance', 'type'],
            title="目标攻击优先级排序",
            orientation='h'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # 添加战术建议
        st.subheader("💡 多目标攻击战术")
        
        st.info("""
        **推荐攻击序列:**
        1. Target_1 (预警机) - 最高优先级，压制敌方空中指挥
        2. Target_2 (战斗机) - 消除主要空中威胁
        3. Target_3 (军舰) - 打击海上目标
        4. Target_4 (雷达站) - 最后处理固定目标
        """)

    def _show_ew_analysis(self, advanced_module):
        """显示电子对抗分析"""
        st.subheader("⚡ 电子对抗分析")
        
        # 创建示例电子对抗分析
        import plotly.graph_objects as go
        
        # 创建干扰分析图
        jamming_types = ['噪声压制', '欺骗干扰', '灵巧噪声', 'DRM干扰']
        effectiveness = [0.8, 0.6, 0.7, 0.9]
        counter_measures = ['频率捷变', '波形捷变', '自适应滤波', '多基地雷达']
        
        fig = go.Figure(data=[
            go.Bar(name='干扰效果', x=jamming_types, y=effectiveness, marker_color='red'),
            go.Bar(name='对抗效果', x=counter_measures, y=[0.7, 0.8, 0.75, 0.9], marker_color='blue')
        ])
        
        fig.update_layout(
            title="干扰与对抗效果分析",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 添加电子对抗建议
        st.subheader("🛡️ 电子对抗建议")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("""
            **主动对抗措施:**
            1. 频率捷变技术
            2. 极化分集处理
            3. 空间滤波算法
            4. 波形自适应调整
            """)
        
        with col2:
            st.warning("""
            **被动对抗措施:**
            1. 电磁静默策略
            2. 低截获概率波形
            3. 功率管理控制
            4. 多基地协同探测
            """)

    def _show_ai_analysis(self, advanced_module):
        """显示AI智能分析"""
        st.subheader("🤖 AI智能分析")
        
        # 创建AI分析仪表盘
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("AI评估等级", "良好", delta="+5%")
        
        with col2:
            st.metric("风险指数", "中等", delta="-3%")
        
        with col3:
            st.metric("优化潜力", "高", delta="+8%")
        
        with col4:
            st.metric("可靠性", "85%", delta="+2%")
        
        # AI分析报告
        st.subheader("📋 AI分析报告")
        
        with st.expander("详细分析报告", expanded=True):
            tab1, tab2, tab3 = st.tabs(["优势分析", "问题识别", "优化建议"])
            
            with tab1:
                st.success("""
                **✅ 系统优势:**
                1. 隐蔽性能优秀，适合突袭作战
                2. 抗干扰能力较强，能在复杂电磁环境下工作
                3. 探测距离满足作战需求
                4. 系统可靠性达到作战标准
                """)
            
            with tab2:
                st.warning("""
                **⚠️ 需要改进:**
                1. 目标识别精度有待提高
                2. 在多目标场景下性能下降明显
                3. 对抗新型干扰能力不足
                4. 系统响应时间可以进一步优化
                """)
            
            with tab3:
                st.info("""
                **💡 优化建议:**
                1. 升级信号处理算法
                2. 增加多传感器融合
                3. 采用人工智能辅助决策
                4. 优化系统架构设计
                """)        
    
    def _display_battlefield_map(self, visualization_toolkit):
        """显示战场地图"""
        # 这里放置地图可视化的具体实现
        st.info("战场地图可视化区域 - 显示地理信息和战场态势")
        
        # 创建示例地图
        import folium
        from streamlit_folium import st_folium
        
        # 创建地图
        m = folium.Map(location=[35.0, 115.0], zoom_start=6)
        
        # 添加标记
        folium.Marker(
            [35.0, 115.0], 
            popup="导弹位置", 
            tooltip="导弹"
        ).add_to(m)
        
        folium.Marker(
            [36.0, 117.0], 
            popup="目标位置", 
            tooltip="目标",
            icon=folium.Icon(color='red')
        ).add_to(m)
        
        # 显示地图
        st_folium(m, width=700, height=500)
    
    # 其他辅助方法
    def _create_new_simulation(self):
        """创建新仿真"""
        st.session_state['new_simulation'] = True
        st.success("新建仿真场景已准备")
    
    def _save_current_session(self):
        """保存当前会话"""
        with st.spinner("保存会话中..."):
            time.sleep(1)
            st.success("会话已保存")
    
    def _export_reports(self):
        """导出报告"""
        st.info("报告导出功能")
    
    def _create_new_scenario(self):
        """创建新场景"""
        st.switch_page("pages/scenario_creator.py")
    
    def _import_historical_data(self):
        """导入历史数据"""
        uploaded_file = st.file_uploader("选择数据文件", type=['csv', 'json', 'xlsx'])
        if uploaded_file:
            st.success(f"文件 {uploaded_file.name} 上传成功")
    
    def _show_tutorial(self):
        """显示使用教程"""
        st.info("使用教程页面")
    
    def _display_visualization_controls(self, visualization_toolkit):
        """显示可视化控制"""
        st.checkbox("显示地形", value=True)
        st.checkbox("显示天气效果", value=True)
        st.checkbox("显示探测范围", value=True)
        st.checkbox("显示轨迹", value=True)
        
        visualization_type = st.selectbox(
            "可视化类型",
            ["2D地图", "3D场景", "卫星视图", "地形图"]
        )
    
    def _display_measurement_tools(self):
        """显示测量工具"""
        st.button("距离测量", use_container_width=True)
        st.button("面积测量", use_container_width=True)
        st.button("高程分析", use_container_width=True)
    
    def _display_scenario_preview(self):
        """显示场景预览"""
        st.info("场景预览功能")
    
    def _generate_report(self, config):
        """生成报告"""
        with st.spinner("生成报告中..."):
            time.sleep(2)
            st.success(f"{config['format']}格式报告生成完成")
    
    def _clear_temp_files(self):
        """清空临时文件"""
        st.warning("此操作将删除所有临时文件")
        if st.button("确认清空"):
            st.success("临时文件已清空")
    
    def _backup_system_data(self):
        """备份系统数据"""
        with st.spinner("备份数据中..."):
            time.sleep(2)
            st.success("系统数据备份完成")
    
    def _reset_system_settings(self):
        """重置系统设置"""
        st.warning("此操作将恢复系统默认设置")
        if st.button("确认重置"):
            st.success("系统设置已重置")
    
    def _run_system_diagnostic(self):
        """运行系统诊断"""
        with st.spinner("运行系统诊断..."):
            time.sleep(3)
            
            # 模拟诊断结果
            diagnostic_results = {
                "系统状态": "正常",
                "模块加载": "完整",
                "数据连接": "稳定",
                "性能指标": "良好"
            }
            
            for item, status in diagnostic_results.items():
                st.success(f"✅ {item}: {status}")
    def _display_footer(self):
        """显示页脚"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **技术支持**  
            📧 contact@ew-simulation.com  
            📞 400-123-4567
            """)
        
        with col2:
            st.markdown("""
            **版本信息**  
            🏢 电子战仿真实验室  
            🔄 版本 2.0.0
            """)
        
        with col3:
            st.markdown("""
            **相关链接**  
            📚 [使用文档](https://docs.example.com)  
            🐛 [问题反馈](https://github.com/example/issues)
            """)
        
        # 版权信息
        st.markdown("---")
        st.markdown(
            '<div style="text-align: center; color: #666; font-size: 0.8rem;">'
            '© 2024 电子战仿真实验室. 保留所有权利.'
            '</div>', 
            unsafe_allow_html=True
        )

class ApplicationManager:
    """应用程序管理器"""
    
    def __init__(self):
        self.main_app = MainApplication()
        self.is_running = False
        self.session_data = {}
        self.error_log = []
        
    def start_application(self):
        """启动应用程序"""
        try:
            # 初始化应用程序
            if not self.main_app.initializer.initialize_application():
                st.error("应用程序初始化失败")
                return False
            
            # 设置会话状态
            if 'app_initialized' not in st.session_state:
                st.session_state.app_initialized = True
                st.session_state.current_page = "dashboard"
                st.session_state.user_preferences = {}
                st.session_state.simulation_data = {}
            
            # 运行主应用程序
            self.main_app.run()
            self.is_running = True
            
            # 记录启动日志
            self._log_event("APPLICATION_STARTED", "应用程序启动成功")
            
            return True
            
        except Exception as e:
            error_msg = f"应用程序启动失败: {str(e)}"
            st.error(error_msg)
            self._log_event("APPLICATION_ERROR", error_msg)
            return False
    
    def stop_application(self):
        """停止应用程序"""
        try:
            # 保存当前状态
            self._save_application_state()
            
            # 清理资源
            self._cleanup_resources()
            
            self.is_running = False
            self._log_event("APPLICATION_STOPPED", "应用程序正常停止")
            
        except Exception as e:
            error_msg = f"应用程序停止过程中出错: {str(e)}"
            self._log_event("APPLICATION_ERROR", error_msg)
    
    def restart_application(self):
        """重启应用程序"""
        self.stop_application()
        time.sleep(1)  # 短暂延迟
        return self.start_application()
    
    def _save_application_state(self):
        """保存应用程序状态"""
        try:
            # 保存用户偏好设置
            if hasattr(st, 'session_state'):
                state_data = {
                    'user_preferences': st.session_state.get('user_preferences', {}),
                    'current_page': st.session_state.get('current_page', 'dashboard'),
                    'last_save_time': datetime.now().isoformat()
                }
                
                # 保存到文件（简化实现）
                state_file = "app_state.json"
                with open(state_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
                
                self._log_event("STATE_SAVED", "应用程序状态已保存")
                
        except Exception as e:
            self._log_event("STATE_SAVE_ERROR", f"状态保存失败: {str(e)}")
    
    def _load_application_state(self):
        """加载应用程序状态"""
        try:
            state_file = "app_state.json"
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                
                # 恢复状态
                if hasattr(st, 'session_state'):
                    st.session_state.user_preferences = state_data.get('user_preferences', {})
                    st.session_state.current_page = state_data.get('current_page', 'dashboard')
                
                self._log_event("STATE_LOADED", "应用程序状态已恢复")
                return True
                
        except Exception as e:
            self._log_event("STATE_LOAD_ERROR", f"状态加载失败: {str(e)}")
        
        return False
    
    def _cleanup_resources(self):
        """清理资源"""
        try:
            # 关闭数据库连接等资源
            if hasattr(self.main_app, 'data_manager'):
                # 这里可以添加数据库连接关闭逻辑
                pass
                
            # 清理临时文件
            self._cleanup_temp_files()
            
        except Exception as e:
            self._log_event("CLEANUP_ERROR", f"资源清理失败: {str(e)}")
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dirs = ['temp', 'cache']
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                        except Exception as e:
                            print(f"无法删除文件 {file_path}: {e}")
            
            self._log_event("TEMP_CLEANED", "临时文件已清理")
            
        except Exception as e:
            self._log_event("CLEANUP_ERROR", f"临时文件清理失败: {str(e)}")
    
    def _log_event(self, event_type, message):
        """记录事件日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'session_id': id(self)
        }
        
        self.error_log.append(log_entry)
        
        # 控制日志数量
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-500:]
        
        # 输出到控制台（在开发环境中）
        if os.getenv('DEBUG_MODE'):
            print(f"[{log_entry['timestamp']}] {event_type}: {message}")
    
    def get_application_status(self):
        """获取应用程序状态"""
        return {
            'is_running': self.is_running,
            'modules_loaded': len([m for m in self.main_app.modules.values() if m is not None]),
            'total_modules': len(self.main_app.modules),
            'last_error': self.error_log[-1] if self.error_log else None,
            'error_count': len([log for log in self.error_log if log['type'] == 'ERROR']),
            'uptime': self._get_uptime() if hasattr(self, 'start_time') else 0
        }
    
    def _get_uptime(self):
        """获取运行时间"""
        if hasattr(self, 'start_time'):
            return (datetime.now() - self.start_time).total_seconds()
        return 0
    
    def export_error_log(self, format_type='json'):
        """导出错误日志"""
        try:
            if format_type == 'json':
                return self._export_logs_to_json()
            elif format_type == 'csv':
                return self._export_logs_to_csv()
            else:
                return None
                
        except Exception as e:
            self._log_event("LOG_EXPORT_ERROR", f"日志导出失败: {str(e)}")
            return None
    
    def _export_logs_to_json(self):
        """导出日志为JSON"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            json.dump(self.error_log, tmp, indent=2, ensure_ascii=False)
            return tmp.name
    
    def _export_logs_to_csv(self):
        """导出日志为CSV"""
        if not self.error_log:
            return None
            
        df = pd.DataFrame(self.error_log)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            df.to_csv(tmp.name, index=False, encoding='utf-8')
            return tmp.name

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.performance_metrics = {}
        self.optimization_settings = {
            'cache_enabled': True,
            'lazy_loading': True,
            'memory_limit_mb': 1024,
            'max_threads': 4
        }
    
    def optimize_application(self, app_manager):
        """优化应用程序性能"""
        optimizations = []
        
        # 检查模块加载状态
        loaded_modules = sum(1 for m in app_manager.main_app.modules.values() if m is not None)
        if loaded_modules < len(app_manager.main_app.modules):
            optimizations.append("建议启用更多功能模块以提升性能")
        
        # 内存使用优化
        memory_usage = self._get_memory_usage()
        if memory_usage > self.optimization_settings['memory_limit_mb'] * 0.8:
            optimizations.append("内存使用较高，建议关闭不必要的标签页")
        
        # 缓存优化
        if not self.optimization_settings['cache_enabled']:
            optimizations.append("启用缓存可以显著提升性能")
        
        return {
            'optimizations': optimizations,
            'current_memory_mb': memory_usage,
            'suggested_actions': self._get_suggested_actions(memory_usage)
        }
    
    def _get_memory_usage(self):
        """获取内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # 转换为MB
        except:
            return 0
    
    def _get_suggested_actions(self, memory_usage):
        """获取建议操作"""
        actions = []
        
        if memory_usage > self.optimization_settings['memory_limit_mb'] * 0.9:
            actions.append("立即清理内存")
        elif memory_usage > self.optimization_settings['memory_limit_mb'] * 0.7:
            actions.append("建议重启应用程序")
        
        if len(self.performance_metrics) > 1000:
            actions.append("清理性能指标数据")
        
        return actions

class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.allowed_ips = ['127.0.0.1', 'localhost']
        self.login_attempts = {}
        self.max_login_attempts = 5
        self.lockout_time = 300  # 5分钟
    
    def validate_access(self, ip_address, user_token=None):
        """验证访问权限"""
        # IP地址检查
        if ip_address not in self.allowed_ips:
            return False, "IP地址不在允许列表中"
        
        # 登录尝试检查
        if self._is_ip_locked(ip_address):
            return False, "IP地址已被暂时锁定"
        
        # Token验证（简化实现）
        if user_token and not self._validate_token(user_token):
            self._record_failed_attempt(ip_address)
            return False, "无效的用户令牌"
        
        return True, "访问验证通过"
    
    def _is_ip_locked(self, ip_address):
        """检查IP是否被锁定"""
        if ip_address in self.login_attempts:
            last_attempt, attempts = self.login_attempts[ip_address]
            if attempts >= self.max_login_attempts:
                time_since_last = time.time() - last_attempt
                if time_since_last < self.lockout_time:
                    return True
                else:
                    # 锁定时间已过，重置尝试次数
                    del self.login_attempts[ip_address]
        return False
    
    def _validate_token(self, token):
        """验证用户令牌（简化实现）"""
        # 实际应用中应使用更安全的验证方式
        return len(token) > 10  # 简单长度检查
    
    def _record_failed_attempt(self, ip_address):
        """记录失败尝试"""
        current_time = time.time()
        if ip_address in self.login_attempts:
            last_attempt, attempts = self.login_attempts[ip_address]
            # 检查是否在锁定时间窗口内
            if current_time - last_attempt < self.lockout_time:
                self.login_attempts[ip_address] = (current_time, attempts + 1)
            else:
                # 重置计数
                self.login_attempts[ip_address] = (current_time, 1)
        else:
            self.login_attempts[ip_address] = (current_time, 1)

class UpdateManager:
    """更新管理器"""
    
    def __init__(self):
        self.update_server = "https://updates.ew-simulation.com"
        self.current_version = "2.0.0"
        self.update_check_interval = 3600  # 1小时检查一次
        self.last_check_time = 0
    
    def check_for_updates(self):
        """检查更新"""
        try:
            current_time = time.time()
            if current_time - self.last_check_time < self.update_check_interval:
                return {'update_available': False, 'reason': '检查间隔未到'}
            
            # 模拟检查更新（实际应用中应调用API）
            latest_version = self._get_latest_version()
            
            self.last_check_time = current_time
            
            if self._compare_versions(latest_version, self.current_version) > 0:
                return {
                    'update_available': True,
                    'latest_version': latest_version,
                    'current_version': self.current_version,
                    'release_notes': self._get_release_notes(latest_version)
                }
            else:
                return {'update_available': False, 'reason': '已是最新版本'}
                
        except Exception as e:
            return {'update_available': False, 'error': str(e)}
    
    def _get_latest_version(self):
        """获取最新版本（模拟实现）"""
        # 实际应用中应从服务器获取
        return "2.1.0"
    
    def _compare_versions(self, version1, version2):
        """比较版本号"""
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))
        
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        return 0
    
    def _get_release_notes(self, version):
        """获取版本说明（模拟实现）"""
        release_notes = {
            "2.1.0": [
                "新增多目标协同攻击功能",
                "优化3D可视化性能",
                "修复已知的内存泄漏问题",
                "增强电子对抗模拟精度"
            ],
            "2.0.1": [
                "修复界面显示问题",
                "优化数据导出功能",
                "提升系统稳定性"
            ]
        }
        return release_notes.get(version, ["版本说明暂不可用"])

# 应用程序入口点
def main():
    """主函数"""
    try:
        # 创建应用程序管理器
        app_manager = ApplicationManager()
        
        # 启动应用程序
        if app_manager.start_application():
            st.success("应用程序启动成功")
        else:
            st.error("应用程序启动失败")
            return
        
        # 显示应用程序信息
        app_info = app_manager.main_app.config.get_app_info()
        st.sidebar.markdown(f"**版本:** {app_info['version']}")
        st.sidebar.markdown(f"**状态:** {'运行中' if app_manager.is_running else '已停止'}")
        
        # 添加管理控制到侧边栏
        with st.sidebar.expander("⚙️ 系统管理", expanded=False):
            if st.button("🔄 重启应用", use_container_width=True):
                if app_manager.restart_application():
                    st.rerun()
            
            if st.button("📊 性能监控", use_container_width=True):
                show_performance_monitor(app_manager)
            
            if st.button("🛡️ 安全检查", use_container_width=True):
                show_security_status(app_manager)
            
            if st.button("🔄 检查更新", use_container_width=True):
                check_application_updates(app_manager)
            
            if st.button("🚪 退出应用", use_container_width=True):
                app_manager.stop_application()
                st.stop()
        
    except Exception as e:
        st.error(f"应用程序运行出错: {str(e)}")
        # 记录错误日志
        if 'app_manager' in locals():
            app_manager._log_event("RUNTIME_ERROR", f"主函数错误: {str(e)}")

def show_performance_monitor(app_manager):
    """显示性能监控"""
    optimizer = PerformanceOptimizer()
    performance_info = optimizer.optimize_application(app_manager)
    
    st.subheader("📊 性能监控")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("内存使用", f"{performance_info['current_memory_mb']:.1f} MB")
        st.metric("运行时间", f"{app_manager.get_application_status()['uptime']:.0f} 秒")
    
    with col2:
        loaded_modules = app_manager.get_application_status()['modules_loaded']
        total_modules = app_manager.get_application_status()['total_modules']
        st.metric("模块加载", f"{loaded_modules}/{total_modules}")
        st.metric("错误数量", app_manager.get_application_status()['error_count'])
    
    # 优化建议
    if performance_info['optimizations']:
        st.subheader("💡 优化建议")
        for suggestion in performance_info['optimizations']:
            st.info(suggestion)
    
    # 错误日志
    if app_manager.error_log:
        st.subheader("📋 最近错误")
        recent_errors = [log for log in app_manager.error_log[-5:] if log['type'] == 'ERROR']
        for error in recent_errors:
            st.error(f"{error['timestamp']}: {error['message']}")

def show_security_status(app_manager):
    """显示安全状态"""
    security_mgr = SecurityManager()
    
    st.subheader("🛡️ 安全状态")
    
    # 模拟安全检查
    access_status, message = security_mgr.validate_access('127.0.0.1')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("访问控制", "正常" if access_status else "异常")
        st.metric("IP检查", "通过")
    
    with col2:
        st.metric("会话安全", "正常")
        st.metric("数据加密", "启用")
    
    if access_status:
        st.success("✅ 系统安全状态正常")
    else:
        st.error(f"❌ 安全检查未通过: {message}")

def check_application_updates(app_manager):
    """检查应用程序更新"""
    update_mgr = UpdateManager()
    update_info = update_mgr.check_for_updates()
    
    st.subheader("🔄 更新检查")
    
    if update_info.get('update_available'):
        st.warning(f"发现新版本: {update_info['latest_version']}")
        st.info(f"当前版本: {update_info['current_version']}")
        
        st.subheader("📝 版本说明")
        for note in update_info.get('release_notes', []):
            st.write(f"• {note}")
        
        if st.button("🔄 立即更新", type="primary"):
            st.info("更新功能开发中...")
            # 实际应用中这里应实现更新逻辑
    else:
        st.success("✅ 已是最新版本")
        if 'error' in update_info:
            st.error(f"检查更新时出错: {update_info['error']}")

# 工具函数
def setup_environment():
    """设置运行环境"""
    # 检查必要的依赖
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy', 'folium']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        st.error(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        st.info("请运行: pip install " + " ".join(missing_packages))
        return False
    
    # 检查数据目录
    required_dirs = ['data', 'exports', 'logs']
    for dir_name in required_dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    return True

def create_demo_data():
    """创建演示数据"""
    demo_scenario = {
        'name': '演示场景 - 空战对抗',
        'description': '战斗机对抗预警机和干扰机的典型空战场景',
        'battlefield': {
            'missile_position': {'lat': 35.0, 'lon': 115.0, 'alt': 5000},
            'targets': [
                {
                    'target_id': 'awacs_1',
                    'type': 'awacs',
                    'position': {'lat': 36.0, 'lon': 117.0, 'alt': 8000},
                    'emission_power': 0.9,
                    'rcs': 50.0
                }
            ],
            'jammers': [
                {
                    'jammer_id': 'escort_jammer',
                    'position': {'lat': 36.2, 'lon': 116.8, 'alt': 7000},
                    'type': 'noise',
                    'power': 0.7,
                    'range': 100.0
                }
            ],
            'weather': 'clear'
        }
    }
    
    return demo_scenario

# 应用程序配置检查
if __name__ == "__main__":
    # 环境检查
    if not setup_environment():
        st.stop()
    
    # 显示启动画面
    st.title("🛰️ 导引头电子战仿真系统")
    st.markdown("---")
    
    with st.spinner("初始化应用程序..."):
        time.sleep(1)
        
        # 运行主应用程序
        main()