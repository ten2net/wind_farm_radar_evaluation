"""
场景配置页面
功能：加载和管理YAML格式的风电场评估场景文件
"""

import streamlit as st
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import pandas as pd
from datetime import datetime
import sys
import os

# 添加utils路径
sys.path.append(str(Path(__file__).parent.parent / "config"))
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from config.config import (
    TURBINE_MODELS, RADAR_FREQUENCY_BANDS, ANTENNA_TYPES,
    COMMUNICATION_SYSTEMS, TARGET_RCS_DB, RADAR_TYPES,
    VALIDATION_RULES, SYSTEM_MESSAGES
)
from utils.yaml_loader import YAMLConfigValidator, YAMLLoader

# 页面标题
st.set_page_config(
    page_title="场景配置 | 风电雷达影响评估系统",
    page_icon="📁"
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

# 页面标题
st.title("📁 场景配置")
st.markdown("加载和管理YAML格式的风电场评估场景配置文件")

# 初始化会话状态
if 'scenario_data' not in st.session_state:
    st.session_state.scenario_data = None
    st.session_state.scenario_loaded = False
    st.session_state.scenario_name = ""
    st.session_state.scenario_file_path = ""
    st.session_state.validation_errors = []
    st.session_state.validation_warnings = []

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 加载场景", 
    "✏️ 编辑场景", 
    "👁️ 预览场景", 
    "💾 保存场景"
])

with tab1:
    st.header("加载场景配置文件")
    
    col_load1, col_load2 = st.columns([2, 1])
    
    with col_load1:
        # 文件上传
        uploaded_file = st.file_uploader(
            "选择YAML配置文件",
            type=["yaml", "yml"],
            help="上传符合规范的风电场评估场景YAML文件"
        )
        
        if uploaded_file is not None:
            try:
                # 读取文件内容
                file_content = uploaded_file.getvalue().decode("utf-8")
                
                # 验证YAML格式
                scenario_data = yaml.safe_load(file_content)
                
                if scenario_data:
                    # 使用新的验证器验证场景数据
                    validator = YAMLConfigValidator()
                    is_valid, errors = validator.validate_scenario(scenario_data)
                    warnings = validator.get_warnings()
                    
                    if errors:
                        st.error("❌ 场景文件验证失败")
                        for error in errors:
                            st.error(f"❌ {error}")
                        st.session_state.validation_errors = errors
                        st.session_state.validation_warnings = warnings
                    else:
                        # 保存到会话状态
                        st.session_state.scenario_data = scenario_data
                        st.session_state.scenario_loaded = True
                        st.session_state.scenario_name = scenario_data.get('name', '未命名场景')
                        st.session_state.scenario_file_path = uploaded_file.name
                        st.session_state.validation_errors = []
                        st.session_state.validation_warnings = warnings
                        
                        st.success(f"✅ 场景文件加载成功: {st.session_state.scenario_name}")
                        
                        # 显示警告信息（如果有）
                        if warnings:
                            st.warning("⚠️ 验证警告（不影响使用）:")
                            for warning in warnings:
                                st.warning(f"⚠️ {warning}")
                        
                        # 显示场景概览
                        st.subheader("场景概览")
                        
                        col_overview1, col_overview2, col_overview3, col_overview4 = st.columns(4)
                        
                        with col_overview1:
                            turbines_count = len(scenario_data.get('wind_turbines', []))
                            st.metric("风机数量", turbines_count)
                        
                        with col_overview2:
                            radars_count = len(scenario_data.get('radar_stations', []))
                            st.metric("雷达台站", radars_count)
                        
                        with col_overview3:
                            comms_count = len(scenario_data.get('communication_stations', []))
                            st.metric("通信台站", comms_count)
                        
                        with col_overview4:
                            targets_count = len(scenario_data.get('targets', []))
                            st.metric("评估目标", targets_count)
                        
                        # 显示场景描述
                        description = scenario_data.get('description', '无描述')
                        st.info(f"场景描述: {description}")
                
            except yaml.YAMLError as e:
                st.error(f"❌ YAML解析错误: {e}")
            except Exception as e:
                st.error(f"❌ 文件加载错误: {e}")
    
    with col_load2:
        st.markdown("### 示例文件")
        
        # 显示示例文件结构
        with st.expander("查看示例结构"):
            st.code("""# 风电场评估场景配置示例
name: "华北风电场评估场景"
description: "华北地区典型风电场对周边雷达影响评估"

metadata:
  created_at: "2024-01-01"
  updated_at: "2024-01-01"
  author: "系统生成"
  version: "1.0"

# 风机配置
wind_turbines:
  - id: "WT001"
    model: "Vestas_V150"
    position: {lat: 40.123456, lon: 116.234567, alt: 50}
    height: 150
    rotor_diameter: 150
    orientation: 0
    operational: true

# 雷达台站配置
radar_stations:
  - id: "RADAR001"
    type: "气象雷达"
    frequency_band: "S"
    position: {lat: 40.1, lon: 116.2, alt: 100}
    peak_power: 1000000
    antenna_gain: 40
    beam_width: 1.0
    pulse_width: 2.0
    prf: 300
    noise_figure: 3.0
    system_losses: 6.0
    antenna_height: 30

# 通信台站配置
communication_stations:
  - id: "COMM001"
    service_type: "基站"
    frequency: 1800
    position: {lat: 40.15, lon: 116.25, alt: 30}
    antenna_type: "sector"
    eirp: 50
    antenna_gain: 18
    antenna_height: 30

# 评估目标配置
targets:
  - id: "TARGET001"
    type: "民航飞机"
    rcs: 10.0
    position: {lat: 40.2, lon: 116.3, alt: 10000}
    speed: 250
    heading: 90
    altitude: 10000""", language="yaml")
        
        # 下载示例文件
        example_yaml = """# 风电场评估场景配置示例
name: "示例风电场场景"
description: "示例场景用于演示系统功能"

metadata:
  created_at: "2024-01-01"
  updated_at: "2024-01-01"
  author: "系统生成"
  version: "1.0"

wind_turbines:
  - id: "WT001"
    model: "Vestas_V150"
    position: {lat: 40.123, lon: 116.234, alt: 50}
    height: 150
    rotor_diameter: 150
    orientation: 0
    operational: true
    metadata: {rcs_profile: "medium", blade_material: "复合材料"}

radar_stations:
  - id: "RADAR001"
    type: "气象雷达"
    frequency_band: "S"
    position: {lat: 40.1, lon: 116.2, alt: 100}
    peak_power: 1000000
    antenna_gain: 40
    beam_width: 1.0
    pulse_width: 2.0
    prf: 300
    noise_figure: 3.0
    system_losses: 6.0
    antenna_height: 30
    metadata: {polarization: "horizontal", scanning_mode: "mechanical"}

communication_stations:
  - id: "COMM001"
    service_type: "基站"
    frequency: 1800
    position: {lat: 40.15, lon: 116.25, alt: 30}
    antenna_type: "sector"
    eirp: 50
    antenna_gain: 18
    antenna_height: 30
    metadata: {bandwidth: 20}

targets:
  - id: "TARGET001"
    type: "民航飞机"
    rcs: 10.0
    position: {lat: 40.2, lon: 116.3, alt: 10000}
    speed: 250
    heading: 90
    altitude: 10000
    metadata: {category: "航空器", description: "商业客机"}
"""
        
        st.download_button(
            label="📥 下载示例文件",
            data=example_yaml,
            file_name="wind_farm_scenario_example.yaml",
            mime="text/yaml",
            help="下载示例YAML配置文件"
        )

with tab2:
    st.header("编辑场景配置")
    
    if not st.session_state.scenario_loaded:
        st.warning("⚠️ 请先加载场景文件")
    else:
        scenario_data = st.session_state.scenario_data
        
        # 创建编辑表单
        st.subheader("基本信息")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            scenario_name = st.text_input(
                "场景名称",
                value=scenario_data.get('name', ''),
                help="输入场景名称"
            )
        
        with col_info2:
            scenario_version = st.text_input(
                "场景版本",
                value=scenario_data.get('metadata', {}).get('version', '1.0'),
                help="输入场景版本号"
            )
        
        scenario_description = st.text_area(
            "场景描述",
            value=scenario_data.get('description', ''),
            height=100,
            help="详细描述评估场景"
        )
        
        st.markdown("---")
        
        # 风机配置编辑
        st.subheader("风机配置")
        
        if 'wind_turbines' not in scenario_data:
            scenario_data['wind_turbines'] = []
        
        turbines = scenario_data['wind_turbines']
        
        # 添加新风机按钮
        if st.button("➕ 添加风机", key="add_turbine"):
            new_turbine = {
                'id': f"WT{len(turbines)+1:03d}",
                'model': "Vestas_V150",
                'position': {'lat': 40.0, 'lon': 116.0, 'alt': 50},
                'height': 150,
                'rotor_diameter': 150,
                'orientation': 0,
                'operational': True
            }
            turbines.append(new_turbine)
            st.rerun()
        
        # 显示和编辑风机列表
        for i, turbine in enumerate(turbines):
            with st.expander(f"风机 {turbine.get('id', f'WT{i+1:03d}')}", expanded=False):
                col_t1, col_t2 = st.columns(2)
                
                with col_t1:
                    turbine_id = st.text_input(
                        "风机ID",
                        value=turbine.get('id', f'WT{i+1:03d}'),
                        key=f"turbine_id_{i}"
                    )
                    
                    # 选择风机型号
                    model_options = list(TURBINE_MODELS.keys())
                    current_model = turbine.get('model', 'Vestas_V150')
                    selected_model = st.selectbox(
                        "风机型号",
                        options=model_options,
                        index=model_options.index(current_model) if current_model in model_options else 0,
                        key=f"turbine_model_{i}"
                    )
                    
                    # 显示选中型号的详细信息
                    if selected_model in TURBINE_MODELS:
                        model_info = TURBINE_MODELS[selected_model]
                        st.caption(f"制造商: {model_info.get('manufacturer', '未知')}")
                        st.caption(f"额定功率: {model_info.get('rated_power', 0)} kW")
                        st.caption(f"轮毂高度: {model_info.get('hub_height', 0)} m")
                
                with col_t2:
                    col_lat, col_lon, col_alt = st.columns(3)
                    
                    with col_lat:
                        lat = st.number_input(
                            "纬度",
                            min_value=-90.0,
                            max_value=90.0,
                            value=turbine.get('position', {}).get('lat', 40.0),
                            format="%.6f",
                            key=f"turbine_lat_{i}"
                        )
                    
                    with col_lon:
                        lon = st.number_input(
                            "经度",
                            min_value=-180.0,
                            max_value=180.0,
                            value=turbine.get('position', {}).get('lon', 116.0),
                            format="%.6f",
                            key=f"turbine_lon_{i}"
                        )
                    
                    with col_alt:
                        alt = st.number_input(
                            "海拔(m)",
                            min_value=0.0,
                            max_value=10000.0,
                            value=float(turbine.get('position', {}).get('alt', 50.0)),
                            key=f"turbine_alt_{i}"
                        )
                
                col_t3, col_t4 = st.columns(2)
                
                with col_t3:
                    height = st.number_input(
                        "风机高度(m)",
                        min_value=10.0,
                        max_value=300.0,
                        value=float(turbine.get('height', 150.0)),
                        key=f"turbine_height_{i}"
                    )
                    
                    diameter = st.number_input(
                        "转子直径(m)",
                        min_value=10.0,
                        max_value=200.0,
                        value=float(turbine.get('rotor_diameter', 150.0)),
                        key=f"turbine_diameter_{i}"
                    )
                
                with col_t4:
                    orientation = st.number_input(
                        "方位角(°)",
                        min_value=0.0,
                        max_value=360.0,
                        value=float(turbine.get('orientation', 0.0)),
                        key=f"turbine_orientation_{i}"
                    )
                    
                    operational = st.checkbox(
                        "运行状态",
                        value=turbine.get('operational', True),
                        key=f"turbine_operational_{i}"
                    )
                
                # 删除按钮
                if st.button("🗑️ 删除此风机", key=f"delete_turbine_{i}"):
                    turbines.pop(i)
                    st.rerun()
        
        st.markdown("---")
        
        # 雷达配置编辑
        st.subheader("雷达台站配置")
        
        if 'radar_stations' not in scenario_data:
            scenario_data['radar_stations'] = []
        
        radars = scenario_data['radar_stations']
        
        # 添加新雷达按钮
        if st.button("➕ 添加雷达", key="add_radar"):
            new_radar = {
                'id': f"RADAR{len(radars)+1:03d}",
                'type': "气象雷达",
                'frequency_band': "S",
                'position': {'lat': 40.0, 'lon': 116.0, 'alt': 100},
                'peak_power': 1000000,
                'antenna_gain': 40,
                'beam_width': 1.0,
                'pulse_width': 2.0,
                'prf': 300,
                'noise_figure': 3.0,
                'system_losses': 6.0,
                'antenna_height': 30
            }
            radars.append(new_radar)
            st.rerun()
        
        # 显示和编辑雷达列表
        for i, radar in enumerate(radars):
            with st.expander(f"雷达 {radar.get('id', f'RADAR{i+1:03d}')}", expanded=False):
                col_r1, col_r2 = st.columns(2)
                
                with col_r1:
                    radar_id = st.text_input(
                        "雷达ID",
                        value=radar.get('id', f'RADAR{i+1:03d}'),
                        key=f"radar_id_{i}"
                    )
                    
                    # 雷达类型选择
                    radar_type_options = list(RADAR_TYPES.keys())
                    current_type = radar.get('type', '气象雷达')
                    selected_type = st.selectbox(
                        "雷达类型",
                        options=radar_type_options,
                        index=radar_type_options.index(current_type) if current_type in radar_type_options else 0,
                        key=f"radar_type_{i}"
                    )
                    
                    # 频段选择
                    band_options = list(RADAR_FREQUENCY_BANDS.keys())
                    current_band = radar.get('frequency_band', 'S')
                    selected_band = st.selectbox(
                        "工作频段",
                        options=band_options,
                        index=band_options.index(current_band) if current_band in band_options else 0,
                        key=f"radar_band_{i}"
                    )
                
                with col_r2:
                    col_r_lat, col_r_lon, col_r_alt = st.columns(3)
                    
                    with col_r_lat:
                        lat = st.number_input(
                            "纬度",
                            min_value=-90.0,
                            max_value=90.0,
                            value=radar.get('position', {}).get('lat', 40.0),
                            format="%.6f",
                            key=f"radar_lat_{i}"
                        )
                    
                    with col_r_lon:
                        lon = st.number_input(
                            "经度",
                            min_value=-180.0,
                            max_value=180.0,
                            value=radar.get('position', {}).get('lon', 116.0),
                            format="%.6f",
                            key=f"radar_lon_{i}"
                        )
                    
                    with col_r_alt:
                        alt = st.number_input(
                            "海拔(m)",
                            min_value=0.0,
                            max_value=10000.0,
                            value=float(radar.get('position', {}).get('alt', 100.0)),
                            key=f"radar_alt_{i}"
                        )
                
                col_r3, col_r4 = st.columns(2)
                
                with col_r3:
                    peak_power = st.number_input(
                        "峰值功率(W)",
                        min_value=1000.0,
                        max_value=10000000.0,
                        value=float(radar.get('peak_power', 1000000)),
                        key=f"radar_power_{i}"
                    )
                    
                    antenna_gain = st.number_input(
                        "天线增益(dBi)",
                        min_value=0.0,
                        max_value=60.0,
                        value=float(radar.get('antenna_gain', 40)),
                        key=f"radar_gain_{i}"
                    )
                
                with col_r4:
                    beam_width = st.number_input(
                        "波束宽度(°)",
                        min_value=0.1,
                        max_value=180.0,
                        value=float(radar.get('beam_width', 1.0)),
                        key=f"radar_beamwidth_{i}"
                    )
                    
                    pulse_width = st.number_input(
                        "脉冲宽度(μs)",
                        min_value=0.01,
                        max_value=100.0,
                        value=float(radar.get('pulse_width', 2.0)),
                        key=f"radar_pulsewidth_{i}"
                    )
                
                col_r5, col_r6 = st.columns(2)
                
                with col_r5:
                    prf = st.number_input(
                        "脉冲重复频率(Hz)",
                        min_value=10.0,
                        max_value=10000.0,
                        value=float(radar.get('prf', 300)),
                        key=f"radar_prf_{i}"
                    )
                    
                    noise_figure = st.number_input(
                        "噪声系数(dB)",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(radar.get('noise_figure', 3.0)),
                        key=f"radar_noise_{i}"
                    )
                
                with col_r6:
                    system_losses = st.number_input(
                        "系统损耗(dB)",
                        min_value=0.0,
                        max_value=20.0,
                        value=float(radar.get('system_losses', 6.0)),
                        key=f"radar_losses_{i}"
                    )
                    
                    antenna_height = st.number_input(
                        "天线高度(m)",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(radar.get('antenna_height', 30)),
                        key=f"radar_antenna_height_{i}"
                    )
                
                # 删除按钮
                if st.button("🗑️ 删除此雷达", key=f"delete_radar_{i}"):
                    radars.pop(i)
                    st.rerun()
        
        st.markdown("---")
        
        # 目标配置编辑
        st.subheader("评估目标配置")
        
        if 'targets' not in scenario_data:
            scenario_data['targets'] = []
        
        targets = scenario_data['targets']
        
        # 添加新目标按钮
        if st.button("➕ 添加目标", key="add_target"):
            new_target = {
                'id': f"TARGET{len(targets)+1:03d}",
                'type': "民航飞机",
                'rcs': 10.0,
                'position': {'lat': 40.2, 'lon': 116.3, 'alt': 10000},
                'speed': 250,
                'heading': 90,
                'altitude': 10000
            }
            targets.append(new_target)
            st.rerun()
        
        # 显示和编辑目标列表
        for i, target in enumerate(targets):
            with st.expander(f"目标 {target.get('id', f'TARGET{i+1:03d}')}", expanded=False):
                col_tg1, col_tg2 = st.columns(2)
                
                with col_tg1:
                    target_id = st.text_input(
                        "目标ID",
                        value=target.get('id', f'TARGET{i+1:03d}'),
                        key=f"target_id_{i}"
                    )
                    
                    # 目标类型选择
                    target_type_options = list(TARGET_RCS_DB.keys())
                    current_type = target.get('type', '民航飞机')
                    selected_type = st.selectbox(
                        "目标类型",
                        options=target_type_options,
                        index=target_type_options.index(current_type) if current_type in target_type_options else 0,
                        key=f"target_type_{i}"
                    )
                    
                    # 显示选中类型的信息
                    if selected_type in TARGET_RCS_DB:
                        type_info = TARGET_RCS_DB[selected_type]
                        st.caption(f"类别: {type_info.get('category', '未知')}")
                        st.caption(f"典型RCS: {type_info.get('rcs_typical', 0)} m²")
                        st.caption(f"典型速度: {type_info.get('speed_typical', 0)} m/s")
                
                with col_tg2:
                    col_tg_lat, col_tg_lon, col_tg_alt = st.columns(3)
                    
                    with col_tg_lat:
                        lat = st.number_input(
                            "纬度",
                            min_value=-90.0,
                            max_value=90.0,
                            value=target.get('position', {}).get('lat', 40.0),
                            format="%.6f",
                            key=f"target_lat_{i}"
                        )
                    
                    with col_tg_lon:
                        lon = st.number_input(
                            "经度",
                            min_value=-180.0,
                            max_value=180.0,
                            value=target.get('position', {}).get('lon', 116.0),
                            format="%.6f",
                            key=f"target_lon_{i}"
                        )
                    
                    with col_tg_alt:
                        alt = st.number_input(
                            "海拔(m)",
                            min_value=0.0,
                            max_value=20000.0,
                            value=float(target.get('position', {}).get('alt', 10000.0)),
                            key=f"target_alt_{i}"
                        )
                
                col_tg3, col_tg4 = st.columns(2)
                
                with col_tg3:
                    rcs = st.number_input(
                        "RCS (m²)",
                        min_value=0.001,
                        max_value=10000.0,
                        value=float(target.get('rcs', 10.0)),
                        key=f"target_rcs_{i}"
                    )
                    
                    speed = st.number_input(
                        "速度 (m/s)",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(target.get('speed', 250)),
                        key=f"target_speed_{i}"
                    )
                
                with col_tg4:
                    heading = st.number_input(
                        "航向 (°)",
                        min_value=0.0,
                        max_value=360.0,
                        value=float(target.get('heading', 90)),
                        key=f"target_heading_{i}"
                    )
                    
                    altitude = st.number_input(
                        "高度 (m)",
                        min_value=0.0,
                        max_value=20000.0,
                        value=float(target.get('altitude', 10000)),
                        key=f"target_altitude_{i}"
                    )
                
                # 删除按钮
                if st.button("🗑️ 删除此目标", key=f"delete_target_{i}"):
                    targets.pop(i)
                    st.rerun()
        
        # 更新会话状态
        if st.button("💾 保存编辑", type="primary", width='stretch'):
            # 更新基本数据
            scenario_data['name'] = scenario_name
            scenario_data['description'] = scenario_description
            
            # 更新元数据
            if 'metadata' not in scenario_data:
                scenario_data['metadata'] = {}
            scenario_data['metadata']['version'] = scenario_version
            scenario_data['metadata']['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if 'created_at' not in scenario_data['metadata']:
                scenario_data['metadata']['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 验证编辑后的数据
            validator = YAMLConfigValidator()
            is_valid, errors = validator.validate_scenario(scenario_data)
            warnings = validator.get_warnings()
            
            if errors:
                st.error("❌ 保存失败，存在验证错误:")
                for error in errors:
                    st.error(f"❌ {error}")
                st.session_state.validation_errors = errors
                st.session_state.validation_warnings = warnings
            else:
                st.session_state.scenario_data = scenario_data
                st.session_state.scenario_name = scenario_name
                st.session_state.validation_errors = []
                st.session_state.validation_warnings = warnings
                
                st.success("✅ 场景编辑已保存")
                
                # 显示警告信息（如果有）
                if warnings:
                    st.warning("⚠️ 验证警告（不影响使用）:")
                    for warning in warnings:
                        st.warning(f"⚠️ {warning}")
                
                st.rerun()

with tab3:
    st.header("预览场景配置")
    
    if not st.session_state.scenario_loaded:
        st.warning("⚠️ 请先加载场景文件")
    else:
        scenario_data = st.session_state.scenario_data
        
        # 显示JSON预览
        st.subheader("JSON数据预览")
        
        with st.expander("查看完整JSON", expanded=False):
            st.json(scenario_data)
        
        # 显示数据统计
        st.subheader("数据统计")
        
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            turbines_count = len(scenario_data.get('wind_turbines', []))
            st.metric("风机数量", turbines_count)
        
        with col_stats2:
            radars_count = len(scenario_data.get('radar_stations', []))
            st.metric("雷达台站", radars_count)
        
        with col_stats3:
            comms_count = len(scenario_data.get('communication_stations', []))
            st.metric("通信台站", comms_count)
        
        with col_stats4:
            targets_count = len(scenario_data.get('targets', []))
            st.metric("评估目标", targets_count)
        
        st.markdown("---")
        
        # 显示详细数据表格
        st.subheader("风机列表")
        
        if turbines_count > 0:
            turbines_df_data = []
            for turbine in scenario_data['wind_turbines']:
                pos = turbine.get('position', {})
                turbines_df_data.append({
                    'ID': turbine.get('id', ''),
                    '型号': turbine.get('model', ''),
                    '纬度': pos.get('lat', 0),
                    '经度': pos.get('lon', 0),
                    '海拔(m)': pos.get('alt', 0),
                    '高度(m)': turbine.get('height', 0),
                    '转子直径(m)': turbine.get('rotor_diameter', 0),
                    '方位角(°)': turbine.get('orientation', 0),
                    '运行状态': '是' if turbine.get('operational', True) else '否'
                })
            
            turbines_df = pd.DataFrame(turbines_df_data)
            st.dataframe(turbines_df, width='stretch', hide_index=True)
        else:
            st.info("暂无风机数据")
        
        st.subheader("雷达台站列表")
        
        if radars_count > 0:
            radars_df_data = []
            for radar in scenario_data['radar_stations']:
                pos = radar.get('position', {})
                radars_df_data.append({
                    'ID': radar.get('id', ''),
                    '类型': radar.get('type', ''),
                    '频段': radar.get('frequency_band', ''),
                    '纬度': pos.get('lat', 0),
                    '经度': pos.get('lon', 0),
                    '海拔(m)': pos.get('alt', 0),
                    '峰值功率(kW)': radar.get('peak_power', 0) / 1000,
                    '天线增益(dBi)': radar.get('antenna_gain', 0),
                    '波束宽度(°)': radar.get('beam_width', 0)
                })
            
            radars_df = pd.DataFrame(radars_df_data)
            st.dataframe(radars_df, width='stretch', hide_index=True)
        else:
            st.info("暂无雷达数据")
        
        st.subheader("评估目标列表")
        
        if targets_count > 0:
            targets_df_data = []
            for target in scenario_data['targets']:
                pos = target.get('position', {})
                targets_df_data.append({
                    'ID': target.get('id', ''),
                    '类型': target.get('type', ''),
                    'RCS(m²)': target.get('rcs', 0),
                    '纬度': pos.get('lat', 0),
                    '经度': pos.get('lon', 0),
                    '海拔(m)': pos.get('alt', 0),
                    '速度(m/s)': target.get('speed', 0),
                    '航向(°)': target.get('heading', 0),
                    '高度(m)': target.get('altitude', 0)
                })
            
            targets_df = pd.DataFrame(targets_df_data)
            st.dataframe(targets_df, width='stretch', hide_index=True)
        else:
            st.info("暂无目标数据")
        
        # 显示位置信息
        st.subheader("地理位置概览")
        
        col_loc1, col_loc2 = st.columns(2)
        
        with col_loc1:
            if turbines_count > 0:
                turbines_positions = []
                for turbine in scenario_data['wind_turbines']:
                    pos = turbine.get('position', {})
                    turbines_positions.append({
                        'ID': turbine.get('id', ''),
                        '纬度': pos.get('lat', 0),
                        '经度': pos.get('lon', 0),
                        '高度': pos.get('alt', 0)
                    })
                
                if turbines_positions:
                    st.write("风机位置:")
                    st.dataframe(pd.DataFrame(turbines_positions), hide_index=True)
        
        with col_loc2:
            if radars_count > 0:
                radars_positions = []
                for radar in scenario_data['radar_stations']:
                    pos = radar.get('position', {})
                    radars_positions.append({
                        'ID': radar.get('id', ''),
                        '纬度': pos.get('lat', 0),
                        '经度': pos.get('lon', 0),
                        '高度': pos.get('alt', 0)
                    })
                
                if radars_positions:
                    st.write("雷达位置:")
                    st.dataframe(pd.DataFrame(radars_positions), hide_index=True)

with tab4:
    st.header("保存场景配置")
    
    if not st.session_state.scenario_loaded:
        st.warning("⚠️ 请先加载场景文件")
    else:
        scenario_data = st.session_state.scenario_data
        
        col_save1, col_save2 = st.columns(2)
        
        with col_save1:
            # 保存选项
            save_format = st.radio(
                "保存格式",
                ["YAML", "JSON"],
                horizontal=True
            )
            
            # 文件名输入
            default_filename = f"wind_farm_scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            filename = st.text_input(
                "文件名",
                value=default_filename,
                help="输入保存的文件名（不含扩展名）"
            )
        
        with col_save2:
            # 保存位置
            save_location = st.radio(
                "保存位置",
                ["本地下载", "服务器保存"],
                horizontal=True
            )
        
        # 保存按钮
        if st.button("💾 保存文件", type="primary", width='stretch'):
            try:
                if save_format == "YAML":
                    file_content = yaml.dump(scenario_data, default_flow_style=False, allow_unicode=True, indent=2)
                    file_extension = ".yaml"
                    mime_type = "text/yaml"
                else:  # JSON
                    file_content = json.dumps(scenario_data, ensure_ascii=False, indent=2)
                    file_extension = ".json"
                    mime_type = "application/json"
                
                full_filename = f"{filename}{file_extension}"
                
                if save_location == "本地下载":
                    # 提供下载
                    st.download_button(
                        label="📥 下载文件",
                        data=file_content,
                        file_name=full_filename,
                        mime=mime_type,
                        key="download_scenario"
                    )
                else:
                    # 保存到服务器
                    save_dir = Path("outputs/scenarios")
                    save_dir.mkdir(parents=True, exist_ok=True)
                    
                    save_path = save_dir / full_filename
                    
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    
                    st.success(f"✅ 文件已保存到: {save_path}")
                    
                    # 显示保存信息
                    st.info(f"文件大小: {len(file_content)} 字节")
                    st.info(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
            except Exception as e:
                st.error(f"❌ 保存失败: {e}")

# 侧边栏信息
with st.sidebar:
    st.markdown("## ℹ️ 场景状态")
    
    if st.session_state.scenario_loaded:
        st.success(f"✅ 已加载: {st.session_state.scenario_name}")
        
        # 显示验证状态
        if st.session_state.validation_errors:
            st.error(f"⚠️ 验证错误: {len(st.session_state.validation_errors)} 个")
        else:
            st.success("✅ 验证通过")
        
        if st.session_state.validation_warnings:
            st.warning(f"⚠️ 验证警告: {len(st.session_state.validation_warnings)} 个")
        
        # 快速统计
        st.markdown("### 📊 快速统计")
        
        if st.session_state.scenario_data:
            scenario = st.session_state.scenario_data
            
            turbines_count = len(scenario.get('wind_turbines', []))
            radars_count = len(scenario.get('radar_stations', []))
            targets_count = len(scenario.get('targets', []))
            
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                st.metric("风机", turbines_count)
                st.metric("目标", targets_count)
            
            with col_stat2:
                st.metric("雷达", radars_count)
        
        # 快速操作
        st.markdown("### ⚡ 快速操作")
        
        if st.button("🔄 重新验证", width='stretch'):
            if st.session_state.scenario_data:
                validator = YAMLConfigValidator()
                is_valid, errors = validator.validate_scenario(st.session_state.scenario_data)
                warnings = validator.get_warnings()
                
                if errors:
                    st.session_state.validation_errors = errors
                    st.session_state.validation_warnings = warnings
                    st.error(f"❌ 验证发现 {len(errors)} 个错误")
                else:
                    st.session_state.validation_errors = []
                    st.session_state.validation_warnings = warnings
                    st.success("✅ 验证通过")
                
                if warnings:
                    st.warning(f"⚠️ 发现 {len(warnings)} 个警告")
                
                st.rerun()
        
        if st.button("🗑️ 清除场景", width='stretch', type="secondary"):
            st.session_state.scenario_data = None
            st.session_state.scenario_loaded = False
            st.session_state.scenario_name = ""
            st.session_state.scenario_file_path = ""
            st.session_state.validation_errors = []
            st.session_state.validation_warnings = []
            st.rerun()
    
    else:
        st.warning("⚠️ 未加载场景")
    
    st.markdown("---")
    
    # 使用说明
    st.markdown("## 📖 使用说明")
    
    with st.expander("查看说明"):
        st.markdown("""
        1. **加载场景**: 上传YAML格式的场景配置文件
        2. **编辑场景**: 修改风机、雷达、目标等参数
        3. **预览场景**: 查看JSON数据和统计信息
        4. **保存场景**: 将编辑后的场景保存为文件
        
        **文件格式要求**:
        - 必须包含风机、雷达、目标配置
        - 坐标必须在有效范围内
        - 参数必须符合类型和范围要求
        """)
    
    # 技术支持
    st.markdown("---")
    st.markdown("### 🆘 技术支持")
    st.caption("如有问题，请联系技术支持")
    st.caption("邮箱: support@wind-radar-assessment.com")
    st.caption("电话: 010-12345678")

# 页脚
st.markdown("---")
st.caption("风电雷达影响评估系统 | 场景配置模块")