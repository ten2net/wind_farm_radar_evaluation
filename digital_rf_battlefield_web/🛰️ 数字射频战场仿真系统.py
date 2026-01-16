"""
数字射频战场仿真系统 - Web应用主入口
基于Streamlit、Folium和Kimi API的现代化军事仿真平台
"""

import streamlit as st
import os
import sys
from pathlib import Path
import logging
import json
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# 导入自定义组件
from components.header import show_header
from components.sidebar import show_sidebar
from utils.style_utils import load_custom_css, set_page_config

def initialize_session_state():
    """初始化会话状态"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_page = "概览"
        st.session_state.simulation_data = {}
        st.session_state.scenario_data = {}
        st.session_state.radar_configs = []
        st.session_state.target_configs = []
        st.session_state.simulation_config = {}
        st.session_state.simulation_results = {}
        st.session_state.performance_metrics = {}
        st.session_state.kimi_api_key = None
        st.session_state.map_center = [39.9042, 116.4074]  # 北京
        st.session_state.map_zoom = 5
        st.session_state.user_settings = {
            "theme": "dark",
            "units": "metric",
            "language": "zh",
            "auto_save": True
        }
        logger.info("Session state initialized")

def main():
    """主应用入口"""
    # 设置页面配置
    set_page_config(
        page_title="数字射频战场仿真系统",
        page_icon="🛰️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 加载自定义CSS
    load_custom_css()
    
    # 初始化会话状态
    initialize_session_state()
    
    # 显示页眉
    show_header()
    
    # 显示侧边栏
    show_sidebar()
    
    # 添加页脚
    show_footer()

def show_footer():
    """显示页脚"""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div style="text-align: left; color: #888;">
                <small>© 2024 数字射频战场仿真系统</small><br>
                <small>版本: 1.0.0</small>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div style="text-align: center; color: #888;">
                <small>技术支持: 军事科技实验室</small><br>
                <small>联系方式: support@military-tech.com</small>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div style="text-align: right; color: #888;">
                <small>仿真引擎: Digital RF Engine v2.0</small><br>
                <small>数据更新时间: {}</small>
            </div>
            """.format(datetime.now().strftime("%Y-%m-%d %H:%M")),
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()