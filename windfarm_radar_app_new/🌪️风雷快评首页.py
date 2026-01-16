## 文件1: main.py

"""
风电场对雷达探测性能影响评估系统
主应用程序入口
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加utils路径到系统路径
sys.path.append(str(Path(__file__).parent / "config"))
sys.path.append(str(Path(__file__).parent / "utils"))

# 页面配置
st.set_page_config(
    page_title="风电雷达影响评估系统",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    .stMetric {
        padding: 8px 0;
    }
    
    .stMetric label {
        font-size: 0.9rem !important;
    }
    
    .stMetric div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    .stMetric div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }  
    
    .stSlider > div {
        padding: 0.5rem 0;
    }
    
    /* 滑块轨道 */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, rgba(0, 150, 255, 0.1), rgba(0, 150, 255, 0.3));
        height: 6px;
        border-radius: 3px;
    }
    
    /* 滑块轨道填充部分（已选择部分） */
    .stSlider > div > div > div > div > div {
        background: linear-gradient(90deg, 
            rgba(0, 200, 255, 0.7), 
            rgba(0, 150, 255, 0.9));
        height: 6px;
        border-radius: 3px 0 0 3px;
    }
    
    /* 滑块轨道未填充部分 */
    .stSlider > div > div > div > div > div > div {
        background: rgba(100, 100, 150, 0.3);
        height: 6px;
        border-radius: 0 3px 3px 0;
    }
    
    /* 滑块圆点 */
    .stSlider > div > div > div > div > div > div > div {
        background: linear-gradient(135deg, 
            rgba(0, 200, 255, 1), 
            rgba(0, 100, 200, 1));
        border: 2px solid rgba(200, 220, 255, 0.8);
        box-shadow: 0 0 10px rgba(0, 150, 255, 0.5);
        width: 20px;
        height: 20px;
        transform: translateY(-7px);
    }
    
    /* 滑块圆点悬停效果 */
    .stSlider > div > div > div > div > div > div > div:hover {
        background: linear-gradient(135deg, 
            rgba(0, 220, 255, 1), 
            rgba(0, 120, 220, 1));
        box-shadow: 0 0 15px rgba(0, 180, 255, 0.8);
        transform: translateY(-7px) scale(1.1);
        transition: all 0.2s ease;
    }
    
    /* 滑块标签样式 */
    .stSlider label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #a0c8ff;
        margin-bottom: 0.3rem;
    }
    
    /* 滑块数值显示 */
    .stSlider > div > div > div + div {
        color: #00ccff;
        font-size: 0.9rem;
        font-weight: 600;
        text-shadow: 0 0 5px rgba(0, 150, 255, 0.5);
    }
    
    /* 滑块容器的背景 */
    .stSlider {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    /* 滑块容器悬停效果 */
    .stSlider:hover {
        background: rgba(25, 30, 50, 0.4);
        border-color: rgba(0, 150, 255, 0.3);
        box-shadow: 0 0 20px rgba(0, 100, 200, 0.1);
    }
    
    /* 数字输入框样式 */
    .stNumberInput {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
    }
    
    .stNumberInput label {
        color: #a0c8ff;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .stNumberInput input {
        color: #00ccff;
        background: rgba(10, 20, 40, 0.5);
        border: 1px solid rgba(0, 100, 200, 0.3);
        border-radius: 4px;
    }
    
    /* 选择框样式 */
    .stSelectbox {
        background: rgba(20, 25, 45, 0.3);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
        margin: 0.5rem 0;
    }
    
    .stSelectbox label {
        color: #a0c8ff;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .stSelectbox > div > div {
        background: rgba(10, 20, 40, 0.5);
        border: 1px solid rgba(0, 100, 200, 0.3);
        color: #00ccff;
    }
    
    /* 选项卡样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: rgba(20, 25, 45, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: 1px solid rgba(0, 100, 200, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        color: #a0c8ff;
        font-weight: 500;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, 
            rgba(0, 150, 255, 0.3), 
            rgba(0, 100, 200, 0.5));
        color: #00ccff;
        box-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
    }
    
    /* 调整间距 */
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 100, 200, 0.2);
    }
    
    /* 调整整体容器间距 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #a0d8ff;
        text-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
    }
    
    /* 分隔线样式 */
    hr {
        border-color: rgba(0, 100, 200, 0.2);
        margin: 1.5rem 0;
    }      
</style>
""", unsafe_allow_html=True)

# 导入自定义模块
try:
    from utils.radar_calculations import RadarCalculator
    from utils.visualization import VisualizationTools
    from utils.report_generator import ReportGenerator
    from config.config import (
        APP_TITLE, APP_DESCRIPTION, 
        RADAR_FREQUENCY_BANDS, TURBINE_MODELS
    )
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.info("请确保已安装所有依赖包: pip install -r requirements.txt")

# 应用CSS样式
def load_css():
    """加载自定义CSS样式"""
    css = """
    <style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    
    /* 标题样式 */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, 
            rgba(0, 100, 200, 0.2), 
            rgba(0, 150, 255, 0.3), 
            rgba(0, 100, 200, 0.2));
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 150, 255, 0.3);
    }
    
    .main-header h1 {
        color: #00ccff;
        text-shadow: 0 0 10px rgba(0, 150, 255, 0.5);
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: #a0d8ff;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* 卡片样式 */
    .feature-card {
        background: rgba(20, 25, 50, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(0, 150, 255, 0.2);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 150, 255, 0.2);
        border-color: rgba(0, 200, 255, 0.4);
    }
    
    .feature-card h3 {
        color: #00ccff;
        margin-top: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .feature-card p {
        color: #a0c8ff;
        line-height: 1.6;
    }
    
    /* 导航按钮 */
    .nav-button {
        display: block;
        width: 100%;
        padding: 1rem;
        margin: 0.5rem 0;
        background: linear-gradient(135deg, 
            rgba(0, 100, 200, 0.8), 
            rgba(0, 50, 100, 0.9));
        border: none;
        border-radius: 8px;
        color: white;
        font-size: 1.1rem;
        font-weight: 500;
        text-align: left;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
    }
    
    .nav-button:hover {
        background: linear-gradient(135deg, 
            rgba(0, 120, 220, 0.9), 
            rgba(0, 70, 120, 1));
        box-shadow: 0 5px 15px rgba(0, 150, 255, 0.3);
        transform: translateY(-2px);
    }
    
    /* 侧边栏样式 */
    .sidebar .sidebar-content {
        background: rgba(15, 20, 40, 0.8);
    }
    
    /* 指标卡片 */
    .metric-card {
        background: rgba(30, 40, 70, 0.5);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid rgba(0, 150, 255, 0.2);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00ccff;
        text-shadow: 0 0 5px rgba(0, 150, 255, 0.3);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #a0c8ff;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 状态指示器 */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active {
        background-color: #00ff00;
        box-shadow: 0 0 10px #00ff00;
    }
    
    .status-inactive {
        background-color: #ff0000;
        box-shadow: 0 0 10px #ff0000;
    }
    
    .status-warning {
        background-color: #ff9900;
        box-shadow: 0 0 10px #ff9900;
    }
    
    /* 进度条样式 */
    .stProgress > div > div {
        background: linear-gradient(90deg, 
            rgba(0, 150, 255, 0.8), 
            rgba(0, 200, 255, 0.9));
    }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 响应式调整 */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        .feature-card {
            padding: 1rem;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# 初始化会话状态
def init_session_state():
    """初始化会话状态"""
    default_states = {
        'scenario_loaded': False,
        'scenario_data': None,
        'analysis_results': None,
        'current_page': 'home',
        'report_data': {},
        'output_dir': Path("outputs"),
        'charts_dir': Path("outputs/charts"),
        'data_dir': Path("outputs/data"),
        'reports_dir': Path("outputs/reports"),
        'kimi_api_key': None,
        'calculation_complete': False
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # 创建输出目录
    for dir_path in [
        st.session_state.output_dir,
        st.session_state.charts_dir,
        st.session_state.data_dir,
        st.session_state.reports_dir
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

# 主页内容
def show_home_page():
    """显示主页"""
    # 主标题
    st.markdown(f"""
    <div class="main-header">
        <h1>{APP_TITLE}</h1>
        <p>{APP_DESCRIPTION}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 系统状态
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "status-active" if st.session_state.scenario_loaded else "status-inactive"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">场景配置</div>
            <div class="metric-value">
                <span class="status-indicator {status}"></span>
                {len(st.session_state.scenario_data['wind_turbines']) if st.session_state.scenario_loaded else 0}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        radar_count = len(st.session_state.scenario_data['radar_stations']) if st.session_state.scenario_loaded else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">雷达台站</div>
            <div class="metric-value">{radar_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        comm_count = len(st.session_state.scenario_data['communication_stations']) if st.session_state.scenario_loaded else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">通信台站</div>
            <div class="metric-value">{comm_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        target_count = len(st.session_state.scenario_data['targets']) if st.session_state.scenario_loaded else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">评估目标</div>
            <div class="metric-value">{target_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 功能特性展示
    st.subheader("🔧 系统功能模块")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📁 1. 场景配置</h3>
            <p>加载YAML格式的场景配置文件，定义风电场、雷达、通信台站和目标参数。支持多种天线类型和雷达频段配置。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>📡 3. 雷达性能分析</h3>
            <p>基于雷达方程计算有/无风机条件下的信噪比、功率、多普勒频移、多径效应等关键性能指标。</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🗺️ 2. 场景可视化</h3>
            <p>交互式地图显示风机、雷达、通信台站和目标位置，支持3D模型和天线方向图可视化。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>📊 4. 报告生成</h3>
            <p>自动生成专业评估报告，包含数据表格、分析图表和AI解读，支持Markdown格式导出。</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 快速开始
    st.markdown("---")
    st.subheader("🚀 快速开始")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 1. 准备场景文件
        创建YAML格式的场景配置文件，定义：
        - 风机位置和型号
        - 雷达台站参数
        - 通信台站参数
        - 评估目标参数
        
        示例文件：`examples/wind_farm_scenario.yaml`
        """)
        
        # 示例YAML内容预览
        with st.expander("查看YAML文件结构"):
            st.code("""
# 风电场评估场景配置文件示例
wind_turbines:
  - id: wt001
    model: "Vestas_V150"
    position: {lat: 40.123, lon: 116.456, alt: 50}
    height: 150
    rotor_diameter: 150
    
radar_stations:
  - id: radar1
    type: "气象雷达"
    frequency_band: "S"
    position: {lat: 40.1, lon: 116.4, alt: 100}
    peak_power: 1000000
    antenna_gain: 40
    beam_width: 1.0
            
communication_stations:
  - id: comm1
    frequency: 1800
    position: {lat: 40.2, lon: 116.5, alt: 30}
    antenna_type: "全向天线"
    eirp: 50
            
targets:
  - id: target1
    type: "民航飞机"
    rcs: 10
    speed: 250
    flight_path: [...]
            """, language="yaml")
    
    with col2:
        st.markdown("""
        ### 2. 使用步骤
        1. **场景配置**：加载YAML配置文件
        2. **场景可视化**：查看地理分布
        3. **性能分析**：进行雷达影响评估
        4. **报告生成**：导出评估报告
        
        ### 3. 技术要求
        - Python 3.8+
        - Streamlit
        - Folium (地图可视化)
        - Plotly (图表生成)
        - PyYAML (配置文件解析)
        
        安装依赖：
        ```bash
        pip install -r requirements.txt
        ```
        """)
    
    # 技术支持信息
    st.markdown("---")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("""
        ### 📞 技术支持
        **联系方式**：
        - 邮箱：support@radar-assessment.com
        - 电话：+86 10 1234 5678
        
        **办公时间**：
        工作日 9:00-18:00
        """)
    
    with col_info2:
        st.markdown("""
        ### 📚 文档资源
        **用户指南**：
        - 快速入门
        - 配置手册
        - API文档
        
        **案例研究**：
        - 风电场评估案例
        - 最佳实践
        """)
    
    with col_info3:
        st.markdown("""
        ### 🔄 版本信息
        **当前版本**：v1.0.0
        
        **更新日志**：
        - 初始版本发布
        - 支持YAML配置
        - 集成AI分析
        
        **计划功能**：
        - 实时数据接口
        - 批量分析模式
        """)

# 侧边栏导航
def create_sidebar():
    """创建侧边栏导航"""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/wind-turbine.png", width=80)
        st.markdown("## 🌪️ 风电雷达影响评估")
        
        st.markdown("---")
        
        # 场景状态
        if st.session_state.scenario_loaded:
            scenario_name = st.session_state.scenario_data.get('name', '未命名场景')
            st.success(f"✅ 场景已加载: {scenario_name}")
        else:
            st.warning("⚠️ 未加载场景文件")
        
        st.markdown("---")
        
        # 导航菜单
        st.markdown("### 🧭 导航")
        
        # 主页按钮
        if st.button("🏠 系统首页", width='stretch'):
            st.session_state.current_page = "home"
            st.rerun()
        
        # 页面导航按钮
        pages = [
            ("📁 场景配置", "1_📁 场景配置"),
            ("🗺️ 场景可视化", "2_🗺️ 场景可视化"),
            ("📡 雷达性能分析", "3_📡 雷达性能分析"),
            ("📊 报告生成", "4_📊 报告生成")
        ]
        
        for page_name, page_file in pages:
            if st.button(page_name, width='stretch', key=f"nav_{page_file}"):
                st.switch_page(f"pages/{page_file}.py")
        
        st.markdown("---")
        
        # 快速操作
        st.markdown("### ⚡ 快速操作")
        
        if st.button("🔄 重新加载场景", width='stretch'):
            st.session_state.scenario_loaded = False
            st.session_state.scenario_data = None
            st.rerun()
        
        if st.button("🗑️ 清除所有数据", width='stretch', type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # API设置
        st.markdown("### 🔑 Kimi API设置")
        api_key = st.text_input(
            "Kimi API密钥",
            value=st.session_state.get('kimi_api_key', ''),
            type="password",
            help="输入Kimi API密钥以启用AI分析功能"
        )
        if api_key:
            st.session_state.kimi_api_key = api_key
            st.success("✅ API密钥已设置")
        
        st.markdown("---")
        
        # 系统信息
        st.markdown("### ℹ️ 系统信息")
        st.markdown(f"""
        **版本**: 1.0.0
        **状态**: {"就绪" if st.session_state.scenario_loaded else "等待配置"}
        **分析完成**: {"✅" if st.session_state.calculation_complete else "❌"}
        """)

# 主函数
def main():
    """主函数"""
    # 加载CSS样式
    load_css()
    
    # 初始化会话状态
    init_session_state()
    
    # 创建侧边栏
    create_sidebar()
    
    # 显示主页
    show_home_page()

if __name__ == "__main__":
    main()
