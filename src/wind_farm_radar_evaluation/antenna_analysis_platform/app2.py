"""
天线分析平台 - 主应用入口
基于radarsimpy的天线性能分析与仿真平台
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import yaml
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置页面配置
st.set_page_config(
    page_title="天线分析平台",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-header {
        color: #1E3A8A;
        padding: 1rem 0;
        border-bottom: 2px solid #E5E7EB;
        margin-bottom: 2rem;
    }
    
    /* 卡片样式 */
    .stCard {
        background-color: #F9FAFB;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid #3B82F6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* 指标卡片样式 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    
    /* 隐藏Streamlit默认样式 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 导入自定义模块
try:
    from views.sidebar_view import render_sidebar
    from views.dashboard_view import render_dashboard
    from views.analysis_view import render_analysis
    from views.education_view import render_education
    from views.export_view import render_export
    from utils.config import AppConfig
except ImportError as e:
    st.error(f"模块导入错误: {e}")
    st.info("请确保所有模块文件已正确创建")
    # 创建占位函数以便应用能继续运行
    def render_sidebar():
        return {}
    def render_dashboard(*args, **kwargs):
        st.write("仪表板模块未找到")
    def render_analysis(*args, **kwargs):
        st.write("分析模块未找到")
    def render_education(*args, **kwargs):
        st.write("教学模块未找到")
    def render_export(*args, **kwargs):
        st.write("导出模块未找到")

# 初始化应用配置
@st.cache_resource
def init_app():
    """初始化应用配置和状态"""
    try:
        config = AppConfig()
        return config
    except Exception as e:
        st.error(f"配置初始化失败: {e}")
        return None

def main():
    """主应用函数"""
    # 应用标题
    st.markdown('<h1 class="main-header">📡 天线性能分析平台</h1>', unsafe_allow_html=True)
    
    # 初始化配置
    config = init_app()
    if config is None:
        st.stop()
    
    # 初始化session state
    if 'current_antenna' not in st.session_state:
        st.session_state.current_antenna = None
    if 'pattern_data' not in st.session_state:
        st.session_state.pattern_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    # 渲染侧边栏并获取选择
    with st.sidebar:
        st.markdown("## 🎛️ 控制面板")
        selection = render_sidebar()
    
    # 根据选择渲染主界面
    try:
        if selection.get('page') == 'dashboard':
            render_dashboard(config, selection)
        
        elif selection.get('page') == 'analysis':
            render_analysis(config, selection)
        
        elif selection.get('page') == 'education':
            render_education(config, selection)
        
        elif selection.get('page') == 'export':
            render_export(config, selection)
        
        else:
            # 默认显示仪表板
            render_dashboard(config, selection)
            
    except Exception as e:
        st.error(f"页面渲染错误: {e}")
        st.exception(e)
        
        # 显示错误详情
        with st.expander("错误详情"):
            st.write(f"错误类型: {type(e).__name__}")
            st.write(f"错误信息: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    # 页面底部信息
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**版本**: 1.0.0")
    with col2:
        st.markdown("**基于**: radarsimpy")
    with col3:
        st.markdown("**作者**: 天线分析团队")

if __name__ == "__main__":
    # 设置Matplotlib参数
    rcParams['font.family'] = 'SimHei'  # 中文字体
    rcParams['axes.unicode_minus'] = False
    rcParams['figure.dpi'] = 100
    rcParams['savefig.dpi'] = 300
    
    main()