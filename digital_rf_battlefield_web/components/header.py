"""
页眉组件 - 现代化军事科技风格页眉
"""

import streamlit as st
from utils.style_utils import get_military_style

def show_header():
    """显示页眉"""
    st.markdown(
        f"""
        <div style="{get_military_style('header')}">
            <div class="header-container">
                <div class="header-logo">
                    <img src="https://img.icons8.com/ios-filled/50/00ff00/satellite-antenna.png" alt="雷达图标">
                    <h1>数字射频战场仿真系统</h1>
                </div>
                <div class="header-status">
                    <span class="status-badge status-active">● 在线</span>
                    <span class="status-badge status-ready">✓ 就绪</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 显示通知栏
    show_notification_bar()

def show_notification_bar():
    """显示通知栏"""
    with st.container():
        cols = st.columns([1, 3, 1])
        
        with cols[0]:
            st.markdown(
                """
                <div class="notification-item">
                    <span class="notification-icon">📡</span>
                    <span class="notification-text">系统状态</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with cols[1]:
            # 显示实时状态
            status_text = "系统运行正常 | 仿真引擎就绪 | 数据连接稳定"
            st.markdown(
                f"""
                <div class="status-ticker">
                    <marquee behavior="scroll" direction="left" scrollamount="3">
                        {status_text}
                    </marquee>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with cols[2]:
            # 显示时间
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            st.markdown(
                f"""
                <div class="time-display">
                    <span class="time-icon">🕐</span>
                    <span class="time-text">{current_time}</span>
                </div>
                """,
                unsafe_allow_html=True
            )