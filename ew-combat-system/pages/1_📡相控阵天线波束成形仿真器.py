"""
Streamlit 相控阵天线波束成形交互式仿真应用
使用现代UI设计，支持多种交互和3D可视化
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge
from matplotlib.animation import FuncAnimation
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from scipy import signal
import time
from io import BytesIO
import base64
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置页面配置
st.set_page_config(
    page_title="相控阵天线波束成形仿真器",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    /* 子标题样式 */
    .sub-header {
        font-size: 1.8rem;
        color: #2a5298;
        border-left: 5px solid #4a90e2;
        padding-left: 1rem;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* 卡片样式 */
    .card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 0.02rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #4a90e2;
    }
    
    /* 参数面板样式 */
    .param-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* 指标显示样式 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 0.05rem;
        margin: 0.5rem;
        text-align: center;
        box-shadow: 0 3px 5px rgba(0,0,0,0.2);
    }
    
    /* 按钮样式 */
    .stButton button {
        background: linear-gradient(90deg, #4a90e2, #5a9bed);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(74, 144, 226, 0.4);
    }
    
    /* 标签样式 */
    .stSlider label {
        font-weight: 600;
        color: #2a5298;
    }
    
    /* 表格样式 */
    .dataframe {
        border: none;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 3px 5px rgba(0,0,0,0.1);
    }
    
    /* 页脚样式 */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-size: 0.9rem;
        border-top: 1px solid #e0e0e0;
        margin-top: 3rem;
    }
    
    /* 动画效果 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: fadeIn 0.8s ease-out;
    }
</style>
""", unsafe_allow_html=True)

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

# 应用标题
# st.markdown('<h1 class="main-header animate-in">📡 长城数字相控阵天线波束成形仿真器</h1>', unsafe_allow_html=True)
# st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">交互式探索天线阵列理论与波束成形技术</p>', unsafe_allow_html=True)
st.markdown("""
<div class="main-header">
    <h1>📡 长城数字相控阵天线波束成形仿真器</h1>
    <p>交互式探索天线阵列理论与波束成形技术</p>
</div>
    """, unsafe_allow_html=True)
# 在侧边栏添加导航
with st.sidebar:
    st.markdown("## 🎯 导航菜单")
    page = st.radio(
        "选择页面",
        ["🏠 主页", "📊 波束成形仿真", "🎚️ 参数调优", "📈 性能分析", "📚 理论教学", "🎨 3D可视化"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("## ⚙️ 仿真设置")
    
    # 基础参数设置
    wavelength = st.slider("波长 λ (m)", 0.1, 5.0, 1.0, 0.1, help="电磁波波长，影响阵列的物理尺寸")
    frequency = 3e8 / wavelength
    st.info(f"频率: {frequency/1e6:.1f} MHz")
    
    st.markdown("---")
    st.markdown("## 🔗 快速链接")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 导出数据", use_container_width= True):
            st.session_state.export_data = True
    with col2:
        if st.button("🔄 重置", width='stretch'):
            st.rerun()
    
    st.markdown("---")
    st.markdown("## 📈 性能指标")
    
    if 'beamwidth' in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("波束宽度", f"{st.session_state.beamwidth:.1f}°")
        with col2:
            st.metric("副瓣电平", f"{st.session_state.sidelobe_level:.1f} dB")

# 初始化会话状态
if 'current_pattern' not in st.session_state:
    st.session_state.current_pattern = None
if 'array_factor' not in st.session_state:
    st.session_state.array_factor = None

# 相控阵天线类
class PhasedArray:
    def __init__(self, num_elements, spacing, wavelength=1.0):
        self.num_elements = num_elements
        self.spacing = spacing
        self.wavelength = wavelength
        self.k = 2 * np.pi / wavelength
        self.positions = self._calculate_positions()
    
    def _calculate_positions(self):
        """计算天线位置"""
        return np.linspace(
            -(self.num_elements - 1) * self.spacing / 2,
            (self.num_elements - 1) * self.spacing / 2,
            self.num_elements
        )
    
    def calculate_pattern(self, theta_deg, steering_deg=0, amplitude_weights=None, phase_weights=None):
        """计算天线方向图"""
        theta = np.radians(theta_deg)
        steering = np.radians(steering_deg)
        
        if amplitude_weights is None:
            amplitude_weights = np.ones(self.num_elements)
        if phase_weights is None:
            phase_weights = np.zeros(self.num_elements)
        
        array_factor = np.zeros_like(theta, dtype=complex)
        
        for n, (pos, amp, phase) in enumerate(zip(self.positions, amplitude_weights, phase_weights)):
            # 波程差导致的相位
            path_phase = self.k * pos * np.sin(theta)
            # 移相器引入的相位
            phase_shift = phase + self.k * pos * np.sin(steering)
            array_factor += amp * np.exp(1j * (path_phase - phase_shift))
        
        # 归一化功率方向图
        power_pattern = np.abs(array_factor) ** 2
        power_pattern = power_pattern / np.max(power_pattern)  # 归一化
        pattern_db = 10 * np.log10(power_pattern)
        
        return pattern_db, np.abs(array_factor)
    
    def calculate_beamwidth(self, pattern_db, theta_deg):
        """计算3dB波束宽度"""
        # 找到主瓣峰值
        main_lobe_idx = np.argmax(pattern_db)
        half_power_level = pattern_db[main_lobe_idx] - 3
        
        # 找到3dB点
        left_idx = main_lobe_idx
        right_idx = main_lobe_idx
        
        while left_idx > 0 and pattern_db[left_idx] > half_power_level:
            left_idx -= 1
        while right_idx < len(pattern_db) - 1 and pattern_db[right_idx] > half_power_level:
            right_idx += 1
        
        beamwidth = theta_deg[right_idx] - theta_deg[left_idx]
        return beamwidth, theta_deg[left_idx], theta_deg[right_idx]
    
    def calculate_sidelobe_level(self, pattern_db, theta_deg):
        """计算最大副瓣电平"""
        # 找到主瓣位置
        main_lobe_idx = np.argmax(pattern_db)
        
        # 在左右各30度范围内找副瓣
        search_window = 30
        main_lobe_region = (theta_deg > theta_deg[main_lobe_idx] - 10) & (theta_deg < theta_deg[main_lobe_idx] + 10)
        
        # 排除主瓣区域
        sidelobe_pattern = pattern_db.copy()
        sidelobe_pattern[main_lobe_region] = -np.inf
        
        # 找最大副瓣
        max_sidelobe = np.max(sidelobe_pattern)
        max_sidelobe_idx = np.argmax(sidelobe_pattern)
        
        return max_sidelobe, theta_deg[max_sidelobe_idx]

# 主页面
if page == "🏠 主页":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## 🌟 欢迎使用相控阵天线仿真器")
        st.markdown("""
        本应用提供了一个直观、交互式的平台，用于探索和理解**相控阵天线**的工作原理和波束成形技术。
        
        ### 主要功能：
        ✅ **实时波束成形仿真** - 动态调整参数，观察波束变化
        ✅ **3D可视化** - 三维波束方向图展示
        ✅ **参数优化** - 探索不同参数对性能的影响
        ✅ **理论教学** - 深入了解波束成形原理
        ✅ **性能分析** - 波束宽度、副瓣电平计算
        
        ### 理论基础：
        相控阵天线通过控制各个天线单元的相位，在不转动天线的情况下实现波束的**电子扫描**。
        这种方法相比机械扫描具有更快、更灵活的优势。
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## 📱 快速开始")
        st.markdown("""
        1. 从侧边栏选择**仿真页面**
        2. 调整天线参数
        3. 观察波束成形效果
        4. 导出仿真结果
        
        ### 建议步骤：
        - 从2元天线开始
        - 观察波束宽度变化
        - 尝试波束扫描
        - 优化副瓣电平
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 添加演示动画
    st.markdown('<h2 class="sub-header">🎬 演示动画</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("### 📡 天线数量")
        st.markdown("### 2-16 元")
        st.markdown("灵活可调")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("### 📏 波束宽度")
        st.markdown("### 5-50°")
        st.markdown("可优化")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("### 📶 副瓣抑制")
        st.markdown("### -20dB")
        st.markdown("高性能")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 添加一个简单的动画演示
    st.markdown('<h2 class="sub-header">🔍 波束扫描演示</h2>', unsafe_allow_html=True)
    
    # 创建演示动画
    demo_theta = np.linspace(-90, 90, 361)
    demo_angles = [0, 15, 30, 45, 60]
    
    fig_demo, axes = plt.subplots(1, 5, figsize=(20, 4))
    
    for idx, steer_angle in enumerate(demo_angles):
        array = PhasedArray(num_elements=8, spacing=0.5, wavelength=1.0)
        pattern, _ = array.calculate_pattern(demo_theta, steer_angle)
        
        ax = axes[idx]
        ax.plot(demo_theta, pattern, 'b-', linewidth=2)
        ax.fill_between(demo_theta, -40, pattern, where=(pattern > -20), alpha=0.3, color='blue')
        ax.axvline(steer_angle, color='r', linestyle='--', alpha=0.7)
        ax.set_xlim([-90, 90])
        ax.set_ylim([-40, 5])
        ax.grid(True, alpha=0.3)
        ax.set_title(f'波束指向: {steer_angle}°', fontsize=12)
        ax.set_xlabel('角度 (°)')
        if idx == 0:
            ax.set_ylabel('增益 (dB)')
    
    plt.tight_layout()
    st.pyplot(fig_demo)
    plt.close(fig_demo)

# 波束成形仿真页面
elif page == "📊 波束成形仿真":
    st.markdown('<h2 class="sub-header">📡 波束成形仿真</h2>', unsafe_allow_html=True)
    
    # 创建两列布局
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown('<div class="param-card">', unsafe_allow_html=True)
        st.markdown("### 天线阵列参数")
        
        # 天线参数设置
        num_elements = st.slider("天线单元数量", 2, 16, 8, 1, 
                               help="增加天线数量可以减小波束宽度，提高增益")
        
        spacing_lambda = st.slider("阵元间距 (λ)", 0.1, 1.0, 0.5, 0.05,
                                 help="通常设置为0.5λ以避免栅瓣，但可以根据需要调整")
        
        spacing = spacing_lambda * wavelength
        
        st.markdown("---")
        st.markdown("### 波束控制参数")
        
        steering_angle = st.slider("波束指向角度 (°)", -60, 60, 0, 1,
                                  help="控制波束的指向方向")
        
        # 幅度加权控制
        amplitude_type = st.selectbox(
            "幅度加权类型",
            ["均匀", "切比雪夫", "泰勒", "汉宁", "自定义"],
            help="不同加权函数可以控制副瓣电平和波束宽度"
        )
        
        if amplitude_type == "切比雪夫":
            sidelobe_level = st.slider("副瓣电平 (dB)", -50, -20, -30, 1)
            weights = np.ones(num_elements)
            # 简化的切比雪夫加权
            n = np.arange(num_elements)
            beta = np.cos(np.pi * (n + 0.5) / num_elements)
            weights = np.cos((num_elements - 1) * np.arccos(beta * np.cos(np.pi / 2 / (num_elements - 1))))
            weights = weights / np.max(weights)
        
        elif amplitude_type == "泰勒":
            weights = np.ones(num_elements)
            n = np.arange(num_elements)
            weights = 1 + 0.5 * np.cos(np.pi * (2*n - num_elements + 1) / (2*num_elements))
            
        elif amplitude_type == "汉宁":
            n = np.arange(num_elements)
            weights = 0.5 - 0.5 * np.cos(2 * np.pi * n / (num_elements - 1))
            
        elif amplitude_type == "自定义":
            st.write("自定义幅度加权（归一化到0-1）")
            weights = []
            for i in range(num_elements):
                weight = st.slider(f"单元 {i+1} 幅度", 0.0, 1.0, 1.0, 0.1)
                weights.append(weight)
            weights = np.array(weights)
        else:  # 均匀
            weights = np.ones(num_elements)
        
        st.markdown("---")
        st.markdown("### 仿真控制")
        
        animate = st.checkbox("启用动画演示", True)
        if animate:
            animation_speed = st.slider("动画速度", 1, 10, 5)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        # 创建仿真
        array = PhasedArray(num_elements, spacing, wavelength)
        theta_deg = np.linspace(-90, 90, 721)
        
        # 计算方向图
        pattern_db, array_factor = array.calculate_pattern(theta_deg, steering_angle, weights)
        
        # 计算性能指标
        beamwidth, left_3db, right_3db = array.calculate_beamwidth(pattern_db, theta_deg)
        sidelobe_level, sidelobe_angle = array.calculate_sidelobe_level(pattern_db, theta_deg)
        
        # 保存到会话状态
        st.session_state.current_pattern = pattern_db
        st.session_state.array_factor = array_factor
        st.session_state.beamwidth = beamwidth
        st.session_state.sidelobe_level = sidelobe_level
        
        # 创建图表区域
        tab1, tab2, tab3 = st.tabs(["📡 方向图", "📊 阵列几何", "📈 性能指标"])
        
        with tab1:
            # 使用Plotly创建交互式图表
            fig = go.Figure()
            
            # 添加方向图
            fig.add_trace(go.Scatter(
                x=theta_deg, y=pattern_db,
                mode='lines',
                name='天线方向图',
                line=dict(color='blue', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 100, 255, 0.2)'
            ))
            
            # 添加主瓣标记
            main_lobe_idx = np.argmax(pattern_db)
            fig.add_trace(go.Scatter(
                x=[theta_deg[main_lobe_idx]],
                y=[pattern_db[main_lobe_idx]],
                mode='markers',
                name='主瓣方向',
                marker=dict(color='red', size=12, symbol='circle')
            ))
            
            # 添加3dB点
            fig.add_trace(go.Scatter(
                x=[left_3db, right_3db],
                y=[pattern_db[main_lobe_idx] - 3, pattern_db[main_lobe_idx] - 3],
                mode='markers+lines',
                name='3dB波束宽度',
                line=dict(color='green', width=2, dash='dash'),
                marker=dict(color='green', size=10)
            ))
            
            # 添加副瓣标记
            fig.add_trace(go.Scatter(
                x=[sidelobe_angle],
                y=[sidelobe_level],
                mode='markers',
                name='最高副瓣',
                marker=dict(color='orange', size=10, symbol='diamond')
            ))
            
            # 更新布局
            fig.update_layout(
                title=f'相控阵天线方向图 (N={num_elements}, d={spacing_lambda}λ, θ={steering_angle}°)',
                xaxis_title='角度 (°)',
                yaxis_title='增益 (dB)',
                height=500,
                template='plotly_white',
                hovermode='x unified',
                showlegend=True
            )
            
            # 添加网格和范围
            fig.update_xaxes(range=[-90, 90], gridcolor='lightgray')
            fig.update_yaxes(range=[-40, 5], gridcolor='lightgray')
            
            st.plotly_chart(fig, width='stretch')
        
        with tab2:
            # 显示阵列几何
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            
            # 绘制天线位置
            positions = array.positions
            for i, pos in enumerate(positions):
                # 绘制天线
                circle = plt.Circle((pos, 0), 0.1, color='red', alpha=0.8) # type: ignore
                ax2.add_patch(circle)
                # 标注序号
                ax2.text(pos, 0.2, str(i+1), ha='center', va='center', fontsize=10, fontweight='bold')
                # 绘制权重
                weight_height = weights[i] if len(weights) > i else 1
                ax2.add_patch(Rectangle((pos-0.05, -weight_height*0.5), 0.1, weight_height*0.5, 
                                      alpha=0.3, color='blue'))
            
            # 设置坐标轴
            ax2.set_xlim([min(positions)-1, max(positions)+1]) # type: ignore
            ax2.set_ylim([-1, 1]) # type: ignore
            ax2.set_aspect('equal')
            ax2.grid(True, alpha=0.3)
            ax2.set_xlabel('位置 (m)')
            ax2.set_title(f'天线阵列几何 (间距={spacing:.2f}m, λ={wavelength:.2f}m)')
            ax2.axhline(y=0, color='black', linewidth=0.5)
            
            # 添加波束方向指示
            arrow_length = max(positions) + 1
            arrow_x = arrow_length * np.sin(np.radians(steering_angle))
            arrow_y = arrow_length * np.cos(np.radians(steering_angle))
            ax2.arrow(0, 0, arrow_x, arrow_y, head_width=0.2, head_length=0.3, 
                     fc='green', ec='green', alpha=0.7, linewidth=2)
            
            st.pyplot(fig2)
            plt.close(fig2)
        
        with tab3:
            # 显示性能指标
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("波束宽度", f"{beamwidth:.2f}°", delta="3dB点")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("副瓣电平", f"{sidelobe_level:.2f} dB", 
                         delta=f"角度:{sidelobe_angle:.1f}°")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("主瓣增益", f"0.00 dB", delta="归一化")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 显示详细数据
            st.markdown("### 详细数据")
            data = {
                '角度 (°)': theta_deg[::10],
                '增益 (dB)': pattern_db[::10]
            }
            df = pd.DataFrame(data)
            st.dataframe(df.head(20), width='stretch')
            
            # 下载数据按钮
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 下载CSV数据",
                data=csv,
                file_name="beam_pattern.csv",
                mime="text/csv"
            )

# 参数调优页面
elif page == "🎚️ 参数调优":
    st.markdown('<h2 class="sub-header">🔧 参数调优分析</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="param-card">', unsafe_allow_html=True)
        st.markdown("### 参数扫描设置")
        
        # 扫描参数选择
        scan_param = st.selectbox(
            "扫描参数",
            ["天线数量", "阵元间距", "波束指向"],
            help="选择要扫描的参数，观察其对方向图的影响"
        )
        
        if scan_param == "天线数量":
            param_range = st.slider("天线数量范围", 2, 16, (4, 12), 1)
            fixed_spacing = st.slider("固定间距 (λ)", 0.1, 1.0, 0.5, 0.05)
            fixed_steering = 0
            
        elif scan_param == "阵元间距":
            fixed_elements = st.slider("固定天线数量", 2, 16, 8, 1)
            param_range = st.slider("间距范围 (λ)", 0.1, 1.5, (0.3, 0.8), 0.05)
            fixed_steering = 0
            
        else:  # 波束指向
            fixed_elements = st.slider("固定天线数量", 2, 16, 8, 1)
            fixed_spacing = st.slider("固定间距 (λ)", 0.1, 1.0, 0.5, 0.05)
            param_range = st.slider("波束指向范围 (°)", -60, 60, (-30, 30), 5)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="param-card">', unsafe_allow_html=True)
        st.markdown("### 性能指标")
        
        # 显示当前设置下的性能
        if 'beamwidth' in st.session_state:
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("当前波束宽度", f"{st.session_state.beamwidth:.2f}°")
            with col_b:
                st.metric("当前副瓣电平", f"{st.session_state.sidelobe_level:.2f} dB")
        
        st.markdown("---")
        st.markdown("### 优化目标")
        
        optimization_target = st.selectbox(
            "优化目标",
            ["最小化波束宽度", "最小化副瓣电平", "平衡波束宽度和副瓣"],
            help="选择优化的主要目标"
        )
        
        if optimization_target == "最小化波束宽度":
            st.info("增加天线数量或增大间距可以减小波束宽度")
        elif optimization_target == "最小化副瓣电平":
            st.info("使用加权（如切比雪夫、泰勒）可以降低副瓣电平")
        else:
            st.info("需要权衡波束宽度和副瓣电平，通常通过优化加权实现")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 执行参数扫描
    st.markdown("## 📈 参数扫描结果")
    
    if scan_param == "天线数量":
        num_steps = param_range[1] - param_range[0] + 1
        param_values = range(param_range[0], param_range[1] + 1)
    elif scan_param == "阵元间距":
        num_steps = 6
        param_values = np.linspace(param_range[0], param_range[1], num_steps)
    else:
        num_steps = 6
        param_values = np.linspace(param_range[0], param_range[1], num_steps)
    
    # 创建扫描图表
    fig_scan, axes_scan = plt.subplots(2, 3, figsize=(15, 10))
    axes_scan = axes_scan.flatten()
    
    theta_deg = np.linspace(-90, 90, 361)
    beamwidths = []
    sidelobes = []
    
    for idx, param_value in enumerate(param_values[:6]):  # 最多显示6个子图
        ax = axes_scan[idx]
        
        if scan_param == "天线数量":
            array = PhasedArray(int(param_value), fixed_spacing * wavelength, wavelength) # type: ignore
            title = f'N={int(param_value)}'
        elif scan_param == "阵元间距":
            array = PhasedArray(fixed_elements, param_value * wavelength, wavelength) # type: ignore
            title = f'd={param_value:.2f}λ'
        else:
            array = PhasedArray(fixed_elements, fixed_spacing * wavelength, wavelength) # type: ignore
            pattern, _ = array.calculate_pattern(theta_deg, param_value)
            title = f'θ={param_value:.0f}°'
        
        if scan_param != "波束指向":
            pattern, _ = array.calculate_pattern(theta_deg, 0)
        else:
            pattern, _ = array.calculate_pattern(theta_deg, param_value)
        
        # 计算性能指标
        beamwidth, _, _ = array.calculate_beamwidth(pattern, theta_deg)
        sidelobe_level, _ = array.calculate_sidelobe_level(pattern, theta_deg)
        
        beamwidths.append(beamwidth)
        sidelobes.append(sidelobe_level)
        
        # 绘制
        ax.plot(theta_deg, pattern, 'b-', linewidth=1.5)
        ax.fill_between(theta_deg, -40, pattern, where=(pattern > -20), alpha=0.2, color='blue')
        ax.set_xlim([-90, 90])
        ax.set_ylim([-40, 5])
        ax.grid(True, alpha=0.3)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel('角度 (°)')
        if idx % 3 == 0:
            ax.set_ylabel('增益 (dB)')
    
    plt.tight_layout()
    st.pyplot(fig_scan)
    plt.close(fig_scan)
    
    # 性能趋势图
    st.markdown("## 📊 性能趋势分析")
    
    fig_trend, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # 波束宽度趋势
    ax1.plot(param_values[:len(beamwidths)], beamwidths, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel(scan_param)
    ax1.set_ylabel('波束宽度 (°)')
    ax1.set_title('波束宽度 vs ' + scan_param)
    ax1.grid(True, alpha=0.3)
    
    # 副瓣电平趋势
    ax2.plot(param_values[:len(sidelobes)], sidelobes, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel(scan_param)
    ax2.set_ylabel('副瓣电平 (dB)')
    ax2.set_title('副瓣电平 vs ' + scan_param)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig_trend)
    plt.close(fig_trend)

# 3D可视化页面
elif page == "🎨 3D可视化":
    st.markdown('<h2 class="sub-header">🎨 3D波束方向图</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="param-card">', unsafe_allow_html=True)
        st.markdown("### 3D视图设置")
        
        # 3D视图参数
        num_elements_3d = st.slider("天线数量 (3D)", 4, 12, 8, 1)
        spacing_3d = st.slider("阵元间距 (λ, 3D)", 0.3, 0.8, 0.5, 0.05)
        elevation = st.slider("俯仰角", 10, 90, 30, 5)
        azimuth = st.slider("方位角", 0, 360, 45, 5)
        
        show_array = st.checkbox("显示天线阵列", True)
        show_surface = st.checkbox("显示3D表面", True)
        show_contour = st.checkbox("显示等高线", False)
        
        st.markdown("---")
        st.markdown("### 视图控制")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("重置视图", width='stretch'):
                st.session_state.view_reset = True
        with col_b:
            if st.button("截图", width='stretch'):
                st.session_state.screenshot = True
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # 创建3D方向图
        st.info("正在生成3D波束方向图...")
        
        # 生成3D数据
        theta = np.linspace(-90, 90, 91)
        phi = np.linspace(0, 360, 181)
        
        Theta, Phi = np.meshgrid(np.radians(theta), np.radians(phi))
        
        # 计算3D方向图（简化模型）
        array = PhasedArray(num_elements_3d, spacing_3d * wavelength, wavelength)
        
        # 在3D空间中计算方向图
        R = np.zeros_like(Theta)
        for i in range(len(phi)):
            for j in range(len(theta)):
                # 简化计算：假设是xz平面
                pattern, _ = array.calculate_pattern([theta[j]], 0)
                # 转换为极坐标
                R[i, j] = 10 ** (pattern[0] / 20)  # 转换为线性值
                # 考虑方位角
                R[i, j] *= np.cos(np.radians(phi[i]) / 2) ** 2
        
        # 转换为直角坐标
        X = R * np.sin(Theta) * np.cos(Phi)
        Y = R * np.sin(Theta) * np.sin(Phi)
        Z = R * np.cos(Theta)
        
        # 创建3D图形
        fig_3d = go.Figure()
        
        if show_surface:
            fig_3d.add_trace(go.Surface(
                x=X, y=Y, z=Z,
                colorscale='Viridis',
                opacity=0.8,
                showscale=True,
                name='波束方向图'
            ))
        
        if show_contour:
            # 添加等高线
            fig_3d.add_trace(go.Surface(
                x=X, y=Y, z=Z*0.95,  # 稍微降低以便看到
                surfacecolor=Z,
                colorscale='Viridis',
                opacity=0.6,
                showscale=False,
                contours_z=dict(
                    show=True,
                    usecolormap=True,
                    project_z=True
                ),
                name='等高线'
            ))
        
        if show_array:
            # 添加天线阵列
            positions = array.positions
            for i, pos in enumerate(positions):
                fig_3d.add_trace(go.Scatter3d(
                    x=[pos, pos],
                    y=[0, 0],
                    z=[0, 1],
                    mode='lines',
                    line=dict(color='red', width=3),
                    showlegend=(i==0),
                    name='天线单元' if i==0 else None
                ))
                fig_3d.add_trace(go.Scatter3d(
                    x=[pos],
                    y=[0],
                    z=[1],
                    mode='markers',
                    marker=dict(color='red', size=5),
                    showlegend=False
                ))
        
        # 更新布局
        fig_3d.update_layout(
            title=f'3D波束方向图 (N={num_elements_3d}, d={spacing_3d}λ)',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                camera=dict(
                    eye=dict(x=2, y=2, z=2),
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=0)
                ),
                aspectmode='data'
            ),
            height=600,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig_3d, width='stretch')
    
    # 添加平面投影视图
    st.markdown("## 📐 平面投影")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        # 俯视图
        fig_top = go.Figure()
        fig_top.add_trace(go.Scatterpolar(
            r=np.max(Z, axis=0),
            theta=theta,
            mode='lines',
            fill='toself',
            fillcolor='rgba(0,100,255,0.3)',
            line=dict(color='blue', width=2)
        ))
        fig_top.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title="俯视图",
            height=300
        )
        st.plotly_chart(fig_top, width='stretch')
    
    with col_b:
        # 侧视图
        fig_side = go.Figure()
        fig_side.add_trace(go.Scatter(
            x=theta,
            y=np.max(Z, axis=1),
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(255,100,0,0.3)',
            line=dict(color='orange', width=2)
        ))
        fig_side.update_layout(
            title="侧视图",
            xaxis_title="角度 (°)",
            yaxis_title="增益",
            height=300
        )
        st.plotly_chart(fig_side, width='stretch')
    
    with col_c:
        # 3D切片
        st.markdown("### 3D切片")
        slice_angle = st.slider("切片角度", 0, 360, 0, 15)
        
        # 创建切片
        slice_idx = int(slice_angle / 2)  # phi每2度一个点
        fig_slice = go.Figure()
        fig_slice.add_trace(go.Scatter(
            x=theta,
            y=Z[slice_idx, :],
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=4)
        ))
        fig_slice.update_layout(
            title=f"切片角度: {slice_angle}°",
            xaxis_title="θ (°)",
            yaxis_title="增益",
            height=300
        )
        st.plotly_chart(fig_slice, width='stretch')

# 理论教学页面
elif page == "📚 理论教学":
    st.markdown('<h2 class="sub-header">📖 相控阵天线理论</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 基本原理", "📐 阵列因子", "🔧 波束控制", "📈 性能指标"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 什么是相控阵天线？
            
            相控阵天线是一种由多个天线单元组成的天线阵列，通过对每个单元的发射/接收信号进行**相位控制**，
            可以实现在不物理移动天线的情况下改变波束指向。
            
            ### 核心原理
            
            1. **波前干涉原理**
               - 多个天线单元辐射的电磁波在空间中相互干涉
               - 在特定方向上建设性干涉，形成主波束
               - 在其他方向上破坏性干涉，形成副瓣
            
            2. **相位控制**
               - 通过移相器控制每个单元的相位
               - 改变相位差可以改变波束指向
               - 公式：$\\Delta\\phi = \\frac{2\\pi d}{\\lambda}\\sin(\\theta_0)$
            
            3. **幅度加权**
               - 控制每个单元的幅度可以抑制副瓣
               - 常用的加权函数：均匀、切比雪夫、泰勒、汉宁等
            """)
        
        with col2:
            # 添加原理示意图
            st.markdown("### 原理示意图")
            fig_prin, ax_prin = plt.subplots(figsize=(8, 6))
            
            # 绘制天线阵列
            x_pos = np.linspace(-2, 2, 5)
            for x in x_pos:
                ax_prin.plot([x, x], [0, 0.5], 'k-', linewidth=2)
                ax_prin.plot(x, 0.5, 'ro', markersize=10)
            
            # 绘制波前
            theta = np.radians(30)
            for i, x in enumerate(x_pos):
                # 波前线
                y_line = np.linspace(0.5, 3, 100)
                x_line = x + (y_line - 0.5) * np.tan(theta)
                ax_prin.plot(x_line, y_line, 'b-', alpha=0.3)
                
                # 标注相位
                ax_prin.text(x, 0.5, f"φ{i}", ha='center', va='bottom', fontsize=10)
            
            # 标注波束方向
            ax_prin.arrow(0, 0.5, 2*np.sin(theta), 2*np.cos(theta), 
                         head_width=0.1, head_length=0.2, fc='red', ec='red')
            ax_prin.text(1.5, 2, f'θ={np.degrees(theta):.0f}°', fontsize=12, color='red')
            
            ax_prin.set_xlim([-3, 3]) # type: ignore
            ax_prin.set_ylim([0, 4]) # type: ignore
            ax_prin.set_aspect('equal')
            ax_prin.set_xlabel('位置')
            ax_prin.set_ylabel('距离')
            ax_prin.set_title('相控阵天线原理示意图')
            ax_prin.grid(True, alpha=0.3)
            
            st.pyplot(fig_prin)
            plt.close(fig_prin)
    
    with tab2:
        st.markdown("""
        ### 阵列因子理论
        
        阵列因子是相控阵天线方向性的数学描述：
        
        $$AF(\\theta) = \\sum_{n=0}^{N-1} A_n e^{j[nkd\\sin(\\theta) + \\phi_n]}$$
        
        其中：
        - $A_n$：第n个单元的幅度加权
        - $k = \\frac{2\\pi}{\\lambda}$：波数
        - $d$：阵元间距
        - $\\phi_n$：第n个单元的相位
        - $\\theta$：观测角度
        
        ### 重要特性
        
        1. **主瓣方向**
           $$\\theta_0 = \\arcsin\\left(\\frac{\\lambda\\Delta\\phi}{2\\pi d}\\right)$$
           
        2. **波束宽度**
           $$\\text{BW} \\approx \\frac{0.886\\lambda}{Nd\\cos(\\theta_0)}$$
           
        3. **栅瓣条件**
           当 $d > \\frac{\\lambda}{1+|\\sin(\\theta_0)|}$ 时出现栅瓣
        """)
        
        # 添加数学公式演示
        st.markdown("### 公式计算演示")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            N = st.number_input("天线数量 N", 2, 16, 8)
        with col2:
            d_lambda = st.number_input("间距 (λ)", 0.1, 1.0, 0.5)
        with col3:
            theta0 = st.number_input("指向角 (°)", -60, 60, 0)
        
        # 计算理论值
        lambda_val = wavelength
        d = d_lambda * lambda_val
        
        # 波束宽度
        if N > 0 and d > 0:
            beamwidth_deg = np.degrees(0.886 * lambda_val / (N * d * np.cos(np.radians(theta0))))
            
            # 栅瓣条件
            grating_lobe_condition = lambda_val / (1 + abs(np.sin(np.radians(theta0))))
            has_grating = d > grating_lobe_condition
            
            st.markdown(f"""
            #### 计算结果：
            - **理论波束宽度**: {beamwidth_deg:.2f}°
            - **最大无栅瓣间距**: {grating_lobe_condition/lambda_val:.2f}λ
            - **当前间距**: {d_lambda:.2f}λ
            - **栅瓣风险**: {'⚠️ 存在栅瓣' if has_grating else '✅ 无栅瓣'}
            """)
    
    with tab3:
        st.markdown("""
        ### 波束控制技术
        
        #### 1. 相位扫描
        通过控制每个天线单元的相位来实现波束扫描：
        
        $$\\phi_n = -nkd\\sin(\\theta_0)$$
        
        其中 $\\theta_0$ 是期望的波束指向。
        
        #### 2. 频率扫描
        通过改变工作频率来实现波束扫描：
        
        $$\\theta_0 = \\arcsin\\left(\\frac{\\Delta\\phi\\lambda}{2\\pi d}\\right)$$
        
        #### 3. 数字波束成形
        现代相控阵采用数字信号处理技术：
        - 每个通道独立数字化
        - 数字域进行相位和幅度控制
        - 支持多波束形成
        - 自适应干扰抑制
        """)
        
        # 添加波束扫描动画
        st.markdown("### 波束扫描演示")
        
        if st.button("播放扫描动画", type="primary"):
            # 创建动画
            theta_deg = np.linspace(-90, 90, 361)
            steering_angles = np.linspace(-60, 60, 13)
            
            # 创建图形
            fig_animate, ax_animate = plt.subplots(figsize=(10, 6))
            line, = ax_animate.plot([], [], 'b-', linewidth=2)
            ax_animate.set_xlim([-90, 90]) # type: ignore
            ax_animate.set_ylim([-40, 5]) # type: ignore
            ax_animate.set_xlabel('角度 (°)')
            ax_animate.set_ylabel('增益 (dB)')
            ax_animate.grid(True, alpha=0.3)
            ax_animate.set_title('波束扫描动画')
            
            # 创建数组
            array = PhasedArray(8, 0.5 * wavelength, wavelength)
            
            # 创建占位符
            plot_placeholder = st.empty()
            
            for steer_angle in steering_angles:
                pattern, _ = array.calculate_pattern(theta_deg, steer_angle)
                
                ax_animate.clear()
                ax_animate.plot(theta_deg, pattern, 'b-', linewidth=2)
                ax_animate.fill_between(theta_deg, -40, pattern, where=(pattern > -20), alpha=0.3, color='blue')
                ax_animate.axvline(steer_angle, color='r', linestyle='--', alpha=0.7, label=f'指向: {steer_angle:.0f}°')
                ax_animate.set_xlim([-90, 90]) # type: ignore
                ax_animate.set_ylim([-40, 5]) # type: ignore
                ax_animate.set_xlabel('角度 (°)')
                ax_animate.set_ylabel('增益 (dB)')
                ax_animate.grid(True, alpha=0.3)
                ax_animate.set_title(f'波束扫描动画 - 指向角度: {steer_angle:.0f}°')
                ax_animate.legend()
                
                plot_placeholder.pyplot(fig_animate)
                time.sleep(0.2)
            
            plt.close(fig_animate)
    
    with tab4:
        st.markdown("""
        ### 关键性能指标
        
        #### 1. 波束宽度
        - **定义**: 主瓣功率下降3dB时的角度范围
        - **影响因素**: 天线数量、阵元间距、工作频率
        - **计算公式**: $\\text{BW} \\approx \\frac{0.886\\lambda}{Nd\\cos(\\theta_0)}$
        
        #### 2. 副瓣电平
        - **定义**: 主瓣之外的最大副瓣电平
        - **目标**: 尽可能低（通常<-20dB）
        - **控制方法**: 幅度加权、优化阵列布局
        
        #### 3. 增益
        - **定义**: 相对于各向同性天线的功率增益
        - **理论最大值**: $G_{max} = 10\\log_{10}(N^2)$ dB
        
        #### 4. 扫描范围
        - **定义**: 波束可以扫描的角度范围
        - **典型值**: ±60°
        - **限制因素**: 栅瓣、增益下降
        
        #### 5. 波束跃度
        - **定义**: 波束指向的最小变化角度
        - **影响因素**: 相位量化精度
        - **计算公式**: $\\Delta\\theta_{min} = \\frac{\\lambda}{Nd\\cos(\\theta_0)}$
        """)
        
        # 添加性能对比表
        st.markdown("### 不同配置性能对比")
        
        data = {
            "天线数量": [4, 8, 16, 32],
            "波束宽度 (°)": [25.0, 12.5, 6.25, 3.12],
            "理论增益 (dB)": [12.0, 18.1, 24.1, 30.1],
            "副瓣电平 (dB)": [-13.2, -13.2, -13.2, -13.2],
            "栅瓣风险": ["低", "低", "中", "高"],
            "扫描范围 (°)": ["±60", "±60", "±45", "±30"]
        }
        
        df_perf = pd.DataFrame(data)
        st.dataframe(df_perf.style.highlight_max(axis=0, subset=["理论增益 (dB)"], color='lightgreen')
                             .highlight_min(axis=0, subset=["波束宽度 (°)"], color='lightcoral'), 
                    width='stretch')

# 性能分析页面
elif page == "📈 性能分析":
    st.markdown('<h2 class="sub-header">📊 性能分析与优化</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📉 波束特性", "🔍 参数优化", "📊 对比分析"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 波束特性分析
            st.markdown("### 波束形状分析")
            
            # 创建示例阵列
            array = PhasedArray(8, 0.5 * wavelength, wavelength)
            theta_deg = np.linspace(-90, 90, 721)
            pattern, _ = array.calculate_pattern(theta_deg, 0)
            
            # 找到关键点
            main_lobe_idx = np.argmax(pattern)
            half_power = pattern[main_lobe_idx] - 3
            first_null = None
            sidelobe_peaks = []
            
            # 找到第一零点和副瓣
            for i in range(main_lobe_idx + 1, len(pattern) - 1):
                if pattern[i] <= half_power and pattern[i+1] > half_power:
                    first_null = theta_deg[i]
                if pattern[i-1] < pattern[i] > pattern[i+1] and pattern[i] < -5:
                    sidelobe_peaks.append((theta_deg[i], pattern[i]))
            
            # 绘制详细分析
            fig_detail, ax_detail = plt.subplots(figsize=(10, 6))
            ax_detail.plot(theta_deg, pattern, 'b-', linewidth=2, label='方向图')
            
            # 标注关键点
            ax_detail.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.5)
            ax_detail.axhline(y=-3, color='g', linestyle='--', linewidth=1, alpha=0.7, label='-3dB')
            ax_detail.axhline(y=-20, color='r', linestyle='--', linewidth=1, alpha=0.7, label='-20dB')
            
            # 主瓣
            ax_detail.axvline(x=theta_deg[main_lobe_idx], color='k', linestyle=':', linewidth=1, alpha=0.5)
            ax_detail.plot(theta_deg[main_lobe_idx], pattern[main_lobe_idx], 'ro', markersize=8, label='主瓣峰值')
            
            # 副瓣
            for angle, level in sidelobe_peaks[:3]:  # 只标注前3个副瓣
                ax_detail.plot(angle, level, 'mo', markersize=6)
                ax_detail.annotate(f'{level:.1f}dB', 
                                 xy=(angle, level),
                                 xytext=(angle+5, level+5),
                                 arrowprops=dict(arrowstyle='->', lw=1))
            
            ax_detail.set_xlim([-90, 90]) # type: ignore
            ax_detail.set_ylim([-40, 5]) # type: ignore
            ax_detail.set_xlabel('角度 (°)')
            ax_detail.set_ylabel('增益 (dB)')
            ax_detail.set_title('波束方向图详细分析')
            ax_detail.grid(True, alpha=0.3)
            ax_detail.legend()
            
            st.pyplot(fig_detail)
            plt.close(fig_detail)
        
        with col2:
            st.markdown("### 关键参数")
            
            if 'beamwidth' in st.session_state:
                # 显示雷达图数据
                metrics_data = {
                    '指标': ['波束宽度', '副瓣抑制', '增益', '对称性', '平坦度'],
                    '值': [100 - min(st.session_state.beamwidth, 50)*2, 
                          max(-40, st.session_state.sidelobe_level) + 50,
                          30,  # 假设增益
                          90,   # 对称性
                          85]   # 平坦度
                }
                
                # 创建雷达图
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=metrics_data['值'],
                    theta=metrics_data['指标'],
                    fill='toself',
                    name='性能指标',
                    line=dict(color='blue', width=2),
                    fillcolor='rgba(0, 100, 255, 0.3)'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=True,
                    title="性能雷达图",
                    height=400
                )
                
                st.plotly_chart(fig_radar, width='stretch')
    
    with tab2:
        st.markdown("### 自动参数优化")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 优化目标")
            
            optimization_goal = st.selectbox(
                "选择优化目标",
                ["最小波束宽度", "最低副瓣", "最大增益", "平衡性能"],
                key="opt_goal"
            )
            
            constraints = st.multiselect(
                "约束条件",
                ["无栅瓣", "波束宽度<20°", "副瓣<-20dB", "扫描范围±60°"],
                default=["无栅瓣"]
            )
            
            optimize_button = st.button("开始优化", type="primary", width='stretch')
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 优化算法")
            
            algorithm = st.radio(
                "优化算法",
                ["遗传算法", "粒子群优化", "梯度下降", "网格搜索"],
                horizontal=True
            )
            
            max_iterations = st.slider("最大迭代次数", 10, 1000, 100, 10)
            population_size = st.slider("种群大小", 10, 200, 50, 10)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if optimize_button:
            st.info("正在运行优化算法...")
            
            # 模拟优化过程
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_placeholder = st.empty()
            
            # 模拟优化迭代
            best_fitness = 0
            best_params = {}
            history = []
            
            for i in range(max_iterations):
                # 模拟优化过程
                time.sleep(0.01)
                progress = (i + 1) / max_iterations
                progress_bar.progress(progress)
                
                # 模拟找到更好的解
                if i % 20 == 0:
                    current_fitness = np.random.random()
                    if current_fitness > best_fitness:
                        best_fitness = current_fitness
                        best_params = {
                            "N": np.random.randint(4, 16),
                            "d": np.round(np.random.uniform(0.3, 0.8), 2),
                            "weighting": np.random.choice(["均匀", "切比雪夫", "泰勒"])
                        }
                
                history.append(best_fitness)
                
                status_text.text(f"迭代 {i+1}/{max_iterations}, 当前最优适应度: {best_fitness:.4f}")
            
            # 显示优化结果
            st.success("优化完成！")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("最优天线数", best_params.get("N", 8))
            with col_b:
                st.metric("最优间距", f"{best_params.get('d', 0.5)}λ")
            with col_c:
                st.metric("最优加权", best_params.get("weighting", "均匀"))
            
            # 绘制优化过程
            fig_opt, ax_opt = plt.subplots(figsize=(10, 4))
            ax_opt.plot(history, 'b-', linewidth=2)
            ax_opt.set_xlabel('迭代次数')
            ax_opt.set_ylabel('适应度')
            ax_opt.set_title('优化过程收敛曲线')
            ax_opt.grid(True, alpha=0.3)
            ax_ax = ax_opt.twinx()
            ax_ax.plot(np.gradient(history), 'r--', alpha=0.5, label='梯度')
            ax_ax.set_ylabel('梯度')
            ax_opt.legend(['适应度'], loc='upper left')
            ax_ax.legend(['梯度'], loc='upper right')
            
            st.pyplot(fig_opt)
            plt.close(fig_opt)
    
    with tab3:
        st.markdown("### 不同配置对比分析")
        
        # 创建对比数据
        configs = [
            {"name": "基本配置", "N": 8, "d": 0.5, "weighting": "均匀", "steering": 0},
            {"name": "高增益", "N": 16, "d": 0.5, "weighting": "均匀", "steering": 0},
            {"name": "低副瓣", "N": 8, "d": 0.5, "weighting": "切比雪夫", "steering": 0},
            {"name": "宽波束", "N": 4, "d": 0.8, "weighting": "均匀", "steering": 0},
        ]
        
        # 计算各种配置的性能
        results = []
        theta_deg = np.linspace(-90, 90, 361)
        
        for config in configs:
            array = PhasedArray(config["N"], config["d"] * wavelength, wavelength)
            
            # 设置加权
            if config["weighting"] == "切比雪夫":
                n = np.arange(config["N"])
                beta = np.cos(np.pi * (n + 0.5) / config["N"])
                weights = np.cos((config["N"] - 1) * np.arccos(beta * np.cos(np.pi / 2 / (config["N"] - 1))))
                weights = weights / np.max(weights)
            else:
                weights = np.ones(config["N"])
            
            pattern, _ = array.calculate_pattern(theta_deg, config["steering"], weights)
            beamwidth, _, _ = array.calculate_beamwidth(pattern, theta_deg)
            sidelobe_level, _ = array.calculate_sidelobe_level(pattern, theta_deg)
            
            results.append({
                "配置": config["name"],
                "波束宽度 (°)": f"{beamwidth:.2f}",
                "副瓣电平 (dB)": f"{sidelobe_level:.2f}",
                "天线数量": config["N"],
                "间距 (λ)": config["d"],
                "加权": config["weighting"]
            })
        
        # 显示对比表格
        df_compare = pd.DataFrame(results)
        st.dataframe(df_compare.set_index("配置"), width='stretch')
        
        # 绘制对比图
        fig_compare, axes_compare = plt.subplots(1, 2, figsize=(12, 4))
        
        # 波束宽度对比
        beamwidths = [float(r["波束宽度 (°)"]) for r in results]
        axes_compare[0].bar(range(len(results)), beamwidths, color=['blue', 'green', 'red', 'orange'])
        axes_compare[0].set_xticks(range(len(results)))
        axes_compare[0].set_xticklabels([r["配置"] for r in results])
        axes_compare[0].set_ylabel('波束宽度 (°)')
        axes_compare[0].set_title('波束宽度对比')
        axes_compare[0].grid(True, alpha=0.3, axis='y')
        
        # 副瓣电平对比
        sidelobes = [float(r["副瓣电平 (dB)"]) for r in results]
        axes_compare[1].bar(range(len(results)), sidelobes, color=['blue', 'green', 'red', 'orange'])
        axes_compare[1].set_xticks(range(len(results)))
        axes_compare[1].set_xticklabels([r["配置"] for r in results])
        axes_compare[1].set_ylabel('副瓣电平 (dB)')
        axes_compare[1].set_title('副瓣电平对比')
        axes_compare[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        st.pyplot(fig_compare)
        plt.close(fig_compare)
        
        # 方向图对比
        st.markdown("### 方向图对比")
        
        fig_patterns, ax_patterns = plt.subplots(figsize=(12, 6))
        colors = ['blue', 'green', 'red', 'orange']
        
        for idx, config in enumerate(configs):
            array = PhasedArray(config["N"], config["d"] * wavelength, wavelength)
            
            if config["weighting"] == "切比雪夫":
                n = np.arange(config["N"])
                beta = np.cos(np.pi * (n + 0.5) / config["N"])
                weights = np.cos((config["N"] - 1) * np.arccos(beta * np.cos(np.pi / 2 / (config["N"] - 1))))
                weights = weights / np.max(weights)
            else:
                weights = np.ones(config["N"])
            
            pattern, _ = array.calculate_pattern(theta_deg, config["steering"], weights)
            ax_patterns.plot(theta_deg, pattern, color=colors[idx], linewidth=2, label=config["name"])
        
        ax_patterns.set_xlim([-90, 90]) # type: ignore
        ax_patterns.set_ylim([-40, 5]) # type: ignore
        ax_patterns.set_xlabel('角度 (°)')
        ax_patterns.set_ylabel('增益 (dB)')
        ax_patterns.set_title('不同配置方向图对比')
        ax_patterns.grid(True, alpha=0.3)
        ax_patterns.legend()
        
        st.pyplot(fig_patterns)
        plt.close(fig_patterns)

# 页脚
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>📡 长城数字相控阵天线波束成形仿真器 | 版本 1.0 | 基于Python和Streamlit开发</p>
    <p>🔬 本工具用于教学和科研目的，可帮助理解相控阵天线的基本原理和设计方法</p>
    <p>📧 如有问题或建议，请联系: ten2net@163.com</p>
</div>
""", unsafe_allow_html=True)

# 回到主页
st.markdown("---")
if st.button("🏠 返回首页"):
    st.switch_page("🛡️电子战对抗仿真系统.py")

# streamlit run phased_array_simulator_web.py