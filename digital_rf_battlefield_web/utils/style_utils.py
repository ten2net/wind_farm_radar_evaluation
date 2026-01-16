"""
样式工具 - 现代化军事科技风格样式
"""

import streamlit as st
from pathlib import Path

def set_page_config(page_title: str = None, page_icon: str = None, 
                   layout: str = "wide", initial_sidebar_state: str = "expanded"):
    """设置页面配置"""
    st.set_page_config(
        page_title=page_title or "数字射频战场仿真系统",
        page_icon=page_icon or "🛰️",
        layout=layout,
        initial_sidebar_state=initial_sidebar_state
    )

def load_custom_css():
    """加载自定义CSS样式"""
    css_file = Path(__file__).parent.parent / "assets" / "css" / "custom.css"
    
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # 内联CSS样式
        st.markdown("""
        <style>
        /* 主容器样式 */
        .main {
            padding: 0 1rem;
        }
        
        /* 军事科技风格主题 */
        :root {
            --primary-color: #1a73e8;
            --secondary-color: #0d47a1;
            --accent-color: #00e676;
            --warning-color: #ff9800;
            --danger-color: #f44336;
            --dark-bg: #121212;
            --card-bg: #1e1e1e;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
        }
        
        /* 页眉样式 */
        .header-container {
            background: linear-gradient(135deg, #0d47a1 0%, #1a237e 100%);
            padding: 1rem 2rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header-logo {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .header-logo h1 {
            color: white;
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
        }
        
        .header-status {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .status-active {
            background: rgba(0, 230, 118, 0.2);
            color: #00e676;
            border: 1px solid rgba(0, 230, 118, 0.3);
        }
        
        .status-ready {
            background: rgba(26, 115, 232, 0.2);
            color: #1a73e8;
            border: 1px solid rgba(26, 115, 232, 0.3);
        }
        
        /* 通知栏样式 */
        .notification-item, .time-display {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }
        
        .notification-icon, .time-icon {
            font-size: 1.2rem;
        }
        
        .notification-text, .time-text {
            font-weight: 500;
        }
        
        .status-ticker {
            background: rgba(0, 0, 0, 0.3);
            padding: 0.5rem;
            border-radius: 4px;
            border-left: 3px solid #1a73e8;
        }
        
        /* 侧边栏样式 */
        .sidebar-header {
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1rem;
        }
        
        .sidebar-header h3 {
            color: var(--text-primary);
            margin: 0;
        }
        
        .sidebar-section {
            margin: 1.5rem 0;
        }
        
        .sidebar-section h4 {
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .system-info {
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 4px;
            border-left: 3px solid #00e676;
        }
        
        /* 卡片样式 */
        .military-card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .military-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .card-title {
            color: var(--text-primary);
            margin: 0;
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .card-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        /* 数据仪表样式 */
        .data-meter {
            margin: 1rem 0;
        }
        
        .meter-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.25rem;
        }
        
        .meter-bar {
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
        }
        
        .meter-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.3s ease;
        }
        
        .meter-value {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        /* 按钮样式 */
        .stButton > button {
            background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
            border: none;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(26, 115, 232, 0.3);
        }
        
        /* 表格样式 */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        
        .data-table th {
            background: rgba(255, 255, 255, 0.05);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .data-table td {
            padding: 0.75rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .data-table tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }
        
        /* 选项卡样式 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background: rgba(255, 255, 255, 0.05);
            padding: 2px;
            border-radius: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 2px;
            padding: 0.5rem 1rem;
        }
        
        .stTabs [aria-selected="true"] {
            background: #1a73e8;
        }
        
        /* 进度条样式 */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #1a73e8 0%, #00e676 100%);
        }
        
        /* 滚动条样式 */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)

def get_military_style(element_type: str) -> str:
    """获取军事科技风格样式"""
    styles = {
        "header": """
            background: linear-gradient(135deg, #0d47a1 0%, #1a237e 100%);
            padding: 1rem 2rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        """,
        "card": """
            background: #1e1e1e;
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        """,
        "button_primary": """
            background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
            border: none;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 600;
        """,
        "button_secondary": """
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 600;
        """,
        "metric": """
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 4px;
            border-left: 3px solid #1a73e8;
        """
    }
    
    return styles.get(element_type, "")

def create_data_card(title: str, value: any, unit: str = "", 
                    trend: float = None, icon: str = "📊"):
    """创建数据卡片组件"""
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown(f"<div style='font-size: 2rem;'>{icon}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<h3 style='margin: 0;'>{title}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='margin: 0; color: #1a73e8;'>{value} {unit}</h1>", unsafe_allow_html=True)
        
        if trend is not None:
            trend_icon = "↗️" if trend > 0 else "↘️" if trend < 0 else "➡️"
            trend_color = "#00e676" if trend > 0 else "#f44336" if trend < 0 else "#ff9800"
            st.markdown(
                f"<small style='color: {trend_color};'>"
                f"{trend_icon} {abs(trend):.1f}% 变化</small>",
                unsafe_allow_html=True
            )

def create_gauge_chart(value: float, max_value: float = 100, 
                      label: str = "", color: str = "#1a73e8"):
    """创建仪表盘图表"""
    percentage = (value / max_value) * 100
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
            <span style="font-size: 0.9rem; color: #b0b0b0;">{label}</span>
            <span style="font-weight: 600; color: {color};">{value:.1f}</span>
        </div>
        <div style="height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 3px; overflow: hidden;">
            <div style="width: {percentage}%; height: 100%; background: {color}; border-radius: 3px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)