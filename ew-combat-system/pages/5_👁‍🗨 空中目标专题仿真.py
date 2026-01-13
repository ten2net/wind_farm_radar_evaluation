import streamlit as st
import json
import pandas as pd
from datetime import datetime

# 添加炫酷科技风格CSS
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    
    /* 主标题样式 - 霓虹效果 */
    .main-header {
        text-align: center;
        height: 20vh;
        padding: 1.5rem 0;
        background: rgba(0, 0, 0, 0.7);
        border-radius: 15px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(0, 247, 255, 0.3);
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.3),
                    inset 0 0 20px rgba(0, 247, 255, 0.1);
    }
    
    .main-header h1 {
        background: linear-gradient(90deg, #00fff7, #00ffaa, #00f7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .main-header p {
        color: #a0e7ff;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* 高科技卡片样式 */
    .tech-card {
        background: rgba(10, 15, 30, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 0.25rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0, 247, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .tech-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 247, 255, 0.4);
        box-shadow: 0 12px 40px rgba(0, 247, 255, 0.2);
    }
    
    .tech-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00fff7, #00ffaa, #00f7ff);
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1e 0%, #151b2d 100%);
    }
    
    .sidebar .sidebar-content {
        background: transparent !important;
    }
    
    /* 小标题样式 */
    .tech-card h3 {
        color: #00f7ff;
        font-size: 1.4rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0, 247, 255, 0.3);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .tech-card h3::before {
        content: '▶';
        color: #00ffaa;
        font-size: 0.8em;
    }
    
    /* 指标卡片样式 */
    .metric-display {
        background: rgba(0, 20, 40, 0.6);
        border-radius: 10px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(0, 247, 255, 0.15);
        transition: all 0.3s ease;
    }
    
    .metric-display:hover {
        background: rgba(0, 30, 60, 0.7);
        border-color: rgba(0, 247, 255, 0.3);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #0066ff 0%, #00ccff 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0055ee 0%, #00bbee 100%);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 102, 255, 0.4);
    }
    
    /* 滑块样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #0066ff, #00ccff) !important;
    }
    
    /* 输入框样式 */
    .stNumberInput input {
        background: rgba(0, 20, 40, 0.6) !important;
        color: white !important;
        border: 1px solid rgba(0, 247, 255, 0.3) !important;
        border-radius: 6px;
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div {
        background: rgba(0, 20, 40, 0.6) !important;
        color: white !important;
        border: 1px solid rgba(0, 247, 255, 0.3) !important;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid rgba(0, 247, 255, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: rgba(255, 255, 255, 0.6) !important;
        border: none !important;
        padding: 0.8rem 1.5rem;
        border-radius: 6px 6px 0 0;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 247, 255, 0.1) !important;
        color: white !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(0, 247, 255, 0.2) !important;
        color: white !important;
        border-bottom: 2px solid #00f7ff !important;
    }
    
    /* 数据框样式 */
    .dataframe {
        background: rgba(0, 20, 40, 0.6) !important;
        color: white !important;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 20, 40, 0.6);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #0066ff, #00ccff);
        border-radius: 4px;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #0066ff, #00ccff) !important;
    }
    
    /* 状态指示灯 */
    .status-led {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .status-good { background: #00ff00; box-shadow: 0 0 10px #00ff00; }
    .status-warning { background: #ffff00; box-shadow: 0 0 10px #ffff00; }
    .status-critical { background: #ff0000; box-shadow: 0 0 10px #ff0000; }
    
    /* 地图容器 */
    .folium-map {
        border-radius: 10px;
        overflow: hidden;
        border: 2px solid rgba(0, 247, 255, 0.3);
    }
    
    /* 徽章样式 */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 0.2rem;
    }
    
    .badge-primary { background: rgba(0, 102, 255, 0.3); color: #66b3ff; }
    .badge-success { background: rgba(0, 255, 0, 0.2); color: #00ff00; }
    .badge-warning { background: rgba(255, 255, 0, 0.2); color: #ffff00; }
    .badge-danger { background: rgba(255, 0, 0, 0.2); color: #ff6666; }
    
    /* 分割线 */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 247, 255, 0.3), transparent);
        margin: 1.5rem 0;
    }
    
    /* 网格线背景 */
    .grid-bg {
        background-image: 
            linear-gradient(rgba(0, 247, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 247, 255, 0.05) 1px, transparent 1px);
        background-size: 20px 20px;
    }
</style>
""", unsafe_allow_html=True)

# 页面配置
st.set_page_config(
    page_title="1_📶天线波束成形专题仿真",
    page_icon="👥",
    layout="wide"
)

# 页面标题
# st.title("👥 📶天线波束成形专题仿真")
# 标题区域
st.markdown("""
<div class="main-header">
    <h1>📶 空中目标专题仿真</h1>
    <p>Flight Target Simulation Platform</p>
</div>
    """, unsafe_allow_html=True)
st.markdown("---")
st.success("📋 26年元月15日，我们成功完成了空中目标仿真，并取得了令人满意的结果。即将发布🎉🎊\n下面为页面占位内容！！")
# 模拟部门数据


# 回到主页
st.markdown("---")
if st.button("🏠 返回首页"):
    st.switch_page("🛡️电子战对抗仿真系统.py")