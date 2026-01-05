"""
天线分析平台 - 主应用程序
Streamlit多页面应用的主入口
整合所有视图模块，提供完整的用户体验
"""

import streamlit as st
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from views.sidebar_view import render_sidebar
from views.dashboard_view import render_dashboard
from views.analysis_view import render_analysis
from views.education_view import render_education
from views.settings_view import render_settings
from views.export_view import render_export
from utils.config import AppConfig
from utils.helpers import setup_logging, check_dependencies

def init_session_state():
    """初始化会话状态"""
    # 应用状态
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    
    if 'previous_page' not in st.session_state:
        st.session_state.previous_page = None
    
    # 数据状态
    if 'current_antenna' not in st.session_state:
        st.session_state.current_antenna = None
    
    if 'pattern_data' not in st.session_state:
        st.session_state.pattern_data = None
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    if 'comparative_analysis_results' not in st.session_state:
        st.session_state.comparative_analysis_results = None
    
    # 配置状态
    if 'sidebar_config' not in st.session_state:
        st.session_state.sidebar_config = {
            'page': 'dashboard',
            'antenna_config': {},
            'simulation_settings': {},
            'analysis_settings': {},
            'visualization_settings': {},
            'actions': {}
        }
    
    # 系统状态
    if 'simulation_status' not in st.session_state:
        st.session_state.simulation_status = {
            'type': 'idle',
            'message': '等待仿真',
            'progress': 0.0
        }
    
    if 'export_status' not in st.session_state:
        st.session_state.export_status = {
            'last_export': None,
            'export_count': 0
        }
    
    # UI状态
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    if 'language' not in st.session_state:
        st.session_state.language = 'zh-CN'
    
    st.session_state.app_initialized = True

def check_system_requirements():
    """检查系统要求"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            st.error("需要Python 3.8或更高版本")
            return False
        
        # 检查必要的依赖
        dependencies = [
            'streamlit', 'numpy', 'pandas', 'plotly',
            'scipy', 'pyyaml', 'psutil'
        ]
        
        # missing_deps = check_dependencies(dependencies)
        # if missing_deps:
        #     st.error(f"缺少依赖: {', '.join(missing_deps)}")
        #     return False
        
        return True
        
    except Exception as e:
        st.error(f"系统检查失败: {e}")
        return False

def setup_page_config():
    """设置页面配置"""
    st.set_page_config(
        page_title="长城数字天线分析平台",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/antenna-analysis',
            'Report a bug': 'https://github.com/antenna-analysis/issues',
            'About': """
            ## 天线分析平台 v1.0.0
            
            一个强大的天线性能分析和可视化平台。
            
            **功能特点:**
            - 📡 多种天线模型支持
            - 📊 高级方向图分析
            - 🔍 性能参数计算
            - 📈 交互式可视化
            - 📚 教学和设计指导
            - 💾 数据导出和分享
            
            © 2026 天线分析实验室
            """
        }
    )

def apply_theme():
    """应用主题"""
    # 从设置加载主题
    try:
        from views.settings_view import SettingsView
        config = AppConfig()
        settings_view = SettingsView(config)
        theme = settings_view.settings.get('application', {}).get('theme', 'light')
        
        if theme == 'dark':
            st.markdown("""
            <style>
            .main { background-color: #0E1117; }
            </style>
            """, unsafe_allow_html=True)
        
    except:
        pass

def render_header():
    """渲染页眉"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #1E3A8A; margin: 0;">📡 长城数字天线分析平台</h1>
            <p style="color: #666; margin: 5px 0 20px 0;">专业的天线性能分析与可视化工具</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 快速导航
    with col3:
        st.markdown("""
        <div style="text-align: right; padding-top: 10px;">
            <small>版本 1.0.0 | Python {}.{}.{}</small>
        </div>
        """.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro), 
        unsafe_allow_html=True)

def render_current_page(sidebar_config: Dict[str, Any], config: AppConfig):
    """渲染当前页面"""
    page = sidebar_config.get('page', 'dashboard')
    
    # 保存上一页
    if st.session_state.current_page != page:
        st.session_state.previous_page = st.session_state.current_page
        st.session_state.current_page = page
    
    try:
        if page == 'dashboard':
            render_dashboard(config, sidebar_config)
        
        elif page == 'analysis':
            render_analysis(config, sidebar_config)
        
        elif page == 'education':
            render_education(config, sidebar_config)
        
        elif page == 'settings':
            render_settings(config, sidebar_config)
        
        elif page == 'export':
            render_export(config, sidebar_config)
        
        else:
            st.error(f"未知页面: {page}")
            render_dashboard(config, sidebar_config)
            
    except Exception as e:
        st.error(f"页面渲染错误: {e}")
        st.exception(e)
        
        # 显示错误恢复选项
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 重新加载页面", width='stretch'):
                st.rerun()
        with col2:
            if st.button("🏠 返回仪表板", width='stretch'):
                st.session_state.sidebar_config['page'] = 'dashboard'
                st.rerun()

def render_footer():
    """渲染页脚"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: left;">
            <small>📡 天线分析平台</small><br>
            <small>版本 1.0.0</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <small>© 2026 天线分析实验室</small><br>
            <small>仅供学习和研究使用</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: right;">
            <small>🕐 最后更新: 2026-01-03</small><br>
            <small>🐍 Python {}.{}.{}</small>
        </div>
        """.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro), 
        unsafe_allow_html=True)

def handle_sidebar_actions(sidebar_config: Dict[str, Any]):
    """处理侧边栏操作"""
    actions = sidebar_config.get('actions', {})
    
    for action, triggered in actions.items():
        if triggered:
            if action == 'simulate':
                handle_simulation_action(sidebar_config)
            
            elif action == 'analyze':
                handle_analysis_action(sidebar_config)
            
            elif action == 'reset':
                handle_reset_action()
            
            elif action == 'clear_cache':
                handle_clear_cache_action()
            
            elif action == 'generate_report':
                handle_generate_report_action()
            
            # 清除操作标记
            actions[action] = False
            break  # 一次只处理一个操作

def handle_simulation_action(sidebar_config: Dict[str, Any]):
    """处理仿真操作"""
    try:
        from services.pattern_generator import get_pattern_generator_service
        
        antenna_config = sidebar_config.get('antenna_config', {})
        sim_settings = sidebar_config.get('simulation_settings', {})
        
        if not antenna_config or not antenna_config.get('data'):
            st.error("请先配置天线参数")
            return
        
        # 创建天线对象
        from views.sidebar_view import create_antenna_from_config
        antenna = create_antenna_from_config(antenna_config)
        
        if not antenna:
            st.error("无法创建天线对象")
            return
        
        # 更新进度状态
        st.session_state.simulation_status = {
            'type': 'running',
            'message': '正在运行仿真...',
            'progress': 0.1
        }
        
        # 获取仿真参数
        generator_type = sim_settings.get('generator_type', 'analytical')
        theta_res = sim_settings.get('theta_resolution', 5)
        phi_res = sim_settings.get('phi_resolution', 5)
        add_noise = sim_settings.get('add_noise', False)
        noise_level = sim_settings.get('noise_level', -30)
        
        # 生成方向图
        with st.spinner("正在生成方向图..."):
            pattern_service = get_pattern_generator_service()
            
            # 更新进度
            st.session_state.simulation_status['progress'] = 0.3
            
            pattern = pattern_service.generate_pattern(
                antenna=antenna,
                generator_type=generator_type,
                theta_resolution=theta_res,
                phi_resolution=phi_res
            )
            
            # 添加噪声（如果需要）
            if add_noise and noise_level < 0:
                pattern = pattern_service.add_noise(pattern, noise_level)
            
            # 保存结果
            st.session_state.current_antenna = antenna
            st.session_state.pattern_data = pattern
            
            # 更新进度
            st.session_state.simulation_status = {
                'type': 'completed',
                'message': '仿真完成！',
                'progress': 1.0
            }
            
            st.success("仿真完成！")
    
    except Exception as e:
        st.error(f"仿真失败: {e}")
        st.session_state.simulation_status = {
            'type': 'error',
            'message': f'仿真失败: {str(e)}',
            'progress': 0.0
        }

def handle_analysis_action(sidebar_config: Dict[str, Any]):
    """处理分析操作"""
    try:
        from services.analysis_service import get_analysis_service
        
        if not st.session_state.pattern_data:
            st.error("没有可用的方向图数据，请先运行仿真")
            return
        
        analysis_settings = sidebar_config.get('analysis_settings', {})
        pattern = st.session_state.pattern_data
        antenna = st.session_state.current_antenna
        
        # 更新进度状态
        st.session_state.simulation_status = {
            'type': 'running',
            'message': '正在进行分析...',
            'progress': 0.1
        }
        
        # 运行分析
        with st.spinner("正在分析天线性能..."):
            analysis_service = get_analysis_service()
            
            # 更新进度
            st.session_state.simulation_status['progress'] = 0.3
            
            # 获取分析类型
            analysis_types = analysis_settings.get('analysis_types', [
                'beam_analysis', 'polarization_analysis', 
                'efficiency_analysis', 'frequency_analysis'
            ])
            
            # 运行综合分析
            results = analysis_service.comprehensive_analysis(
                pattern=pattern,
                antenna=antenna,
                analysis_types=analysis_types
            )
            
            # 保存结果
            st.session_state.analysis_results = results
            
            # 更新进度
            st.session_state.simulation_status = {
                'type': 'completed',
                'message': '分析完成！',
                'progress': 1.0
            }
            
            st.success("分析完成！")
    
    except Exception as e:
        st.error(f"分析失败: {e}")
        st.session_state.simulation_status = {
            'type': 'error',
            'message': f'分析失败: {str(e)}',
            'progress': 0.0
        }

def handle_reset_action():
    """处理重置操作"""
    # 确认重置
    st.warning("这将清除所有仿真和分析数据，但会保留配置。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 确认重置", width='stretch', type="primary"):
            # 清除数据状态
            st.session_state.current_antenna = None
            st.session_state.pattern_data = None
            st.session_state.analysis_results = None
            st.session_state.comparative_analysis_results = None
            
            # 重置仿真状态
            st.session_state.simulation_status = {
                'type': 'idle',
                'message': '等待仿真',
                'progress': 0.0
            }
            
            st.success("已重置所有数据")
            st.rerun()
    
    with col2:
        if st.button("🚫 取消", width='stretch'):
            st.info("操作已取消")

def handle_clear_cache_action():
    """处理清理缓存操作"""
    try:
        import shutil
        from pathlib import Path
        
        cache_dir = Path(__file__).parent / "cache"
        
        if cache_dir.exists():
            # 获取缓存大小
            total_size = 0
            for file in cache_dir.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
            
            # 删除缓存目录
            shutil.rmtree(cache_dir)
            
            # 重新创建空目录
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            st.success(f"已清理缓存: {total_size / (1024 * 1024):.1f} MB")
        else:
            st.info("缓存目录不存在")
            
    except Exception as e:
        st.error(f"清理缓存失败: {e}")

def handle_generate_report_action():
    """处理生成报告操作"""
    st.info("报告生成功能")
    
    # 这里可以调用报告生成功能
    # 由于实现较复杂，这里只显示提示
    st.markdown("""
    **报告生成选项:**
    
    1. **技术分析报告** - 详细的技术分析结果
    2. **设计总结报告** - 设计参数和性能总结
    3. **性能评估报告** - 性能评估和建议
    4. **完整详细报告** - 包含所有数据和图表
    
    请在**导出视图**中使用完整的报告生成功能。
    """)

def check_for_updates():
    """检查更新"""
    try:
        # 这里可以实现检查更新逻辑
        # 暂时返回False表示没有更新
        return False
        
    except:
        return False

def main():
    """主函数"""
    # 设置页面配置
    setup_page_config()
    
    # 应用主题
    apply_theme()
    
    # 检查系统要求
    if not check_system_requirements():
        st.stop()
    
    # 初始化会话状态
    init_session_state()
    
    # 设置日志
    setup_logging()
    
    # 检查更新
    if check_for_updates():
        st.info("🔄 有可用更新，请在设置中查看")
    
    # 渲染页眉
    render_header()
    
    # 渲染侧边栏并获取配置
    with st.sidebar:
        sidebar_config = render_sidebar()
        st.session_state.sidebar_config = sidebar_config
    
    # 处理侧边栏操作
    handle_sidebar_actions(sidebar_config)
    
    # 主内容区域
    config = AppConfig()
    
    # 渲染当前页面
    render_current_page(sidebar_config, config)
    
    # 渲染页脚
    render_footer()
    
    # 调试信息（仅在开发模式下显示）
    if config.debug:
        with st.expander("🔧 调试信息", expanded=False):
            st.write("**会话状态:**")
            for key, value in st.session_state.items():
                if not key.startswith('_'):
                    st.write(f"- {key}: {type(value).__name__}")
            
            st.write("**侧边栏配置:**")
            st.json(sidebar_config)

if __name__ == "__main__":
    main()