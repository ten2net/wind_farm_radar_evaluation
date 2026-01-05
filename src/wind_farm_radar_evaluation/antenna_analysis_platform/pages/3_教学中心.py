"""
教学中心页面
Streamlit多页面应用的一部分
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from views.sidebar_view import render_sidebar
from views.education_view import render_education
from utils.config import AppConfig

def main():
    """教学中心页面主函数"""
    # 设置页面配置
    st.set_page_config(
        page_title="教学中心 - 天线分析平台",
        page_icon="📚",
        layout="wide"
    )
    
    # 渲染侧边栏
    with st.sidebar:
        sidebar_config = render_sidebar()
    
    # 设置当前页面
    sidebar_config['page'] = 'education'
    
    # 渲染教学视图
    config = AppConfig()
    render_education(config, sidebar_config)

if __name__ == "__main__":
    main()