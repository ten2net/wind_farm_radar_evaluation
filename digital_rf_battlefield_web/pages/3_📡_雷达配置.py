"""
雷达配置页面 - 现代化雷达参数配置界面
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from utils.style_utils import create_data_card, create_gauge_chart, get_military_style
from components.maps import create_military_map, add_radar_to_map
from streamlit_folium import st_folium

def main():
    """雷达配置页面主函数"""
    st.title("📡 雷达系统配置")
    st.markdown("配置雷达参数、部署位置和操作模式")
    
    # 初始化雷达配置
    if 'radar_configs' not in st.session_state:
        st.session_state.radar_configs = []
    
    if 'radar_catalog' not in st.session_state:
        load_radar_catalog()
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📍 雷达部署", "⚙️ 参数配置", "📊 性能分析", "🗂️ 配置管理"])
    
    with tab1:
        show_radar_deployment()
    
    with tab2:
        show_parameter_configuration()
    
    with tab3:
        show_performance_analysis()
    
    with tab4:
        show_configuration_management()

def load_radar_catalog():
    """加载雷达目录"""
    radar_catalog = [
        {
            "id": "jyl-1",
            "name": "JYL-1远程预警雷达",
            "type": "phased_array",
            "frequency_band": "UHF",
            "range_km": 500,
            "power_kw": 1000,
            "beamwidth_deg": 2.5,
            "scan_rate_rpm": 6,
            "description": "远程空中预警雷达，具备多目标跟踪能力"
        },
        {
            "id": "yj-26",
            "name": "YJ-26相控阵雷达",
            "type": "phased_array",
            "frequency_band": "L",
            "range_km": 400,
            "power_kw": 800,
            "beamwidth_deg": 3.0,
            "scan_rate_rpm": 10,
            "description": "多功能相控阵雷达，支持电子对抗"
        },
        {
            "id": "hq-9",
            "name": "HQ-9防空雷达",
            "type": "mechanical",
            "frequency_band": "S",
            "range_km": 300,
            "power_kw": 600,
            "beamwidth_deg": 1.5,
            "scan_rate_rpm": 12,
            "description": "防空导弹系统配套雷达"
        },
        {
            "id": "cl-1010",
            "name": "CL-1010无源雷达",
            "type": "passive",
            "frequency_band": "VHF",
            "range_km": 350,
            "power_kw": 50,
            "beamwidth_deg": 5.0,
            "scan_rate_rpm": 0,
            "description": "无源探测系统，高隐蔽性"
        },
        {
            "id": "sj-212",
            "name": "SJ-212 MIMO雷达",
            "type": "mimo",
            "frequency_band": "X",
            "range_km": 250,
            "power_kw": 200,
            "beamwidth_deg": 2.0,
            "scan_rate_rpm": 20,
            "description": "MIMO实验雷达，高分辨率"
        }
    ]
    st.session_state.radar_catalog = radar_catalog

def show_radar_deployment():
    """显示雷达部署界面"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 创建部署地图
        st.subheader("🗺️ 雷达部署地图")
        
        # 获取或设置地图中心
        if 'deployment_map_center' not in st.session_state:
            st.session_state.deployment_map_center = [39.9042, 116.4074]
        
        # 创建地图
        m = create_military_map(
            center=st.session_state.deployment_map_center,
            zoom_start=6
        )
        
        # 添加现有雷达
        for radar in st.session_state.get('radar_configs', []):
            if 'position' in radar and radar['position']:
                add_radar_to_map(
                    m,
                    position=radar['position'],
                    radar_type=radar.get('type', 'phased_array'),
                    name=radar.get('name', '未知雷达'),
                    range_km=radar.get('range_km', 100)
                )
        
        # 交互式地图
        map_data = st_folium(m, width=600, height=500)
        
        # 处理地图交互
        if map_data.get("last_clicked"):
            handle_map_click(map_data["last_clicked"])
    
    with col2:
        # 雷达部署控制
        st.subheader("📍 部署控制")
        
        # 添加新雷达
        st.markdown("### 添加新雷达")
        
        radar_type = st.selectbox(
            "雷达类型",
            ["phased_array", "mechanical", "mimo", "passive"],
            format_func=lambda x: {
                "phased_array": "相控阵雷达",
                "mechanical": "机械扫描雷达",
                "mimo": "MIMO雷达",
                "passive": "无源雷达"
            }.get(x, x)
        )
        
        # 从目录选择
        radar_catalog = st.session_state.get('radar_catalog', [])
        radar_templates = {r['name']: r for r in radar_catalog if r['type'] == radar_type}
        
        if radar_templates:
            selected_template = st.selectbox(
                "选择雷达型号",
                list(radar_templates.keys())
            )
            
            if st.button("📋 加载模板", use_container_width=True):
                template = radar_templates[selected_template]
                st.session_state.selected_radar_template = template
                st.success(f"已加载 {selected_template} 模板")
        
        # 手动输入雷达名称
        radar_name = st.text_input("雷达名称", value="雷达站")
        
        # 位置选择方式
        location_method = st.radio(
            "位置选择方式",
            ["地图点击", "手动输入"],
            horizontal=True
        )
        
        if location_method == "手动输入":
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input("纬度", -90.0, 90.0, 39.9042, 0.001)
            with col_lng:
                longitude = st.number_input("经度", -180.0, 180.0, 116.4074, 0.001)
            position = [latitude, longitude]
        else:
            position = st.session_state.get('selected_position')
            if position:
                st.info(f"已选择位置: {position[0]:.4f}, {position[1]:.4f}")
            else:
                st.warning("请在地图上点击选择位置")
                position = [39.9042, 116.4074]
        
        # 探测范围
        detection_range = st.slider(
            "探测范围 (km)",
            10, 1000, 200, 10,
            help="雷达最大探测距离"
        )
        
        # 添加雷达按钮
        if st.button("➕ 添加雷达", type="primary", use_container_width=True):
            add_new_radar(radar_name, radar_type, position, detection_range)
        
        st.markdown("---")
        
        # 雷达列表
        st.subheader("📋 已部署雷达")
        show_radar_list()

def handle_map_click(click_data):
    """处理地图点击事件"""
    lat = click_data["lat"]
    lng = click_data["lng"]
    st.session_state.selected_position = [lat, lng]
    
    # 显示位置信息
    st.sidebar.info(f"已选择位置: {lat:.4f}, {lng:.4f}")

def add_new_radar(name, radar_type, position, detection_range):
    """添加新雷达"""
    new_radar = {
        "id": f"radar_{len(st.session_state.radar_configs) + 1:03d}",
        "name": name,
        "type": radar_type,
        "position": position,
        "range_km": detection_range,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    # 如果选择了模板，应用模板参数
    if 'selected_radar_template' in st.session_state:
        template = st.session_state.selected_radar_template
        new_radar.update({
            "frequency_band": template.get('frequency_band'),
            "power_kw": template.get('power_kw'),
            "beamwidth_deg": template.get('beamwidth_deg'),
            "scan_rate_rpm": template.get('scan_rate_rpm'),
            "description": template.get('description')
        })
    
    st.session_state.radar_configs.append(new_radar)
    st.success(f"已添加雷达: {name}")
    st.rerun()

def show_radar_list():
    """显示雷达列表"""
    radars = st.session_state.get('radar_configs', [])
    
    if not radars:
        st.info("暂无部署雷达")
        return
    
    for i, radar in enumerate(radars):
        with st.expander(f"{radar['name']} ({radar.get('type', '未知')})", expanded=False):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**ID:** {radar['id']}")
                st.markdown(f"**位置:** {radar.get('position', ['N/A', 'N/A'])[0]:.4f}, {radar.get('position', ['N/A', 'N/A'])[1]:.4f}")
                st.markdown(f"**探测范围:** {radar.get('range_km', 0)} km")
            
            with col2:
                status = radar.get('status', 'active')
                status_color = "green" if status == 'active' else "red"
                st.markdown(f"**状态:** <span style='color:{status_color};'>{status}</span>", unsafe_allow_html=True)
                
                if 'frequency_band' in radar:
                    st.markdown(f"**频段:** {radar['frequency_band']}")
            
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.radar_configs.pop(i)
                    st.rerun()
                
                if st.button("✏️", key=f"edit_{i}"):
                    st.session_state.editing_radar_index = i
                    st.switch_page("pages/3_📡_雷达配置.py")

def show_parameter_configuration():
    """显示参数配置界面"""
    st.subheader("⚙️ 雷达参数配置")
    
    # 选择要配置的雷达
    radars = st.session_state.get('radar_configs', [])
    
    if not radars:
        st.warning("请先部署雷达")
        return
    
    radar_names = [r['name'] for r in radars]
    selected_radar = st.selectbox("选择雷达", radar_names)
    
    # 找到选中的雷达
    radar_index = next(i for i, r in enumerate(radars) if r['name'] == selected_radar)
    radar = radars[radar_index]
    
    # 创建配置表单
    with st.form(f"radar_config_form_{radar_index}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 基本参数")
            
            # 发射机参数
            st.markdown("**发射机参数**")
            frequency_mhz = st.number_input(
                "中心频率 (MHz)",
                100, 10000, 3000, 100,
                key=f"freq_{radar_index}"
            )
            
            bandwidth_mhz = st.number_input(
                "带宽 (MHz)",
                1, 1000, 10, 1,
                key=f"bw_{radar_index}"
            )
            
            peak_power_kw = st.number_input(
                "峰值功率 (kW)",
                1, 10000, 500, 10,
                key=f"power_{radar_index}"
            )
            
            prf_hz = st.number_input(
                "脉冲重复频率 (Hz)",
                100, 10000, 1000, 100,
                key=f"prf_{radar_index}"
            )
        
        with col2:
            st.markdown("### 天线参数")
            
            antenna_gain_db = st.number_input(
                "天线增益 (dB)",
                10, 60, 30, 1,
                key=f"gain_{radar_index}"
            )
            
            beamwidth_az = st.number_input(
                "方位波束宽度 (°)",
                0.1, 10.0, 2.5, 0.1,
                key=f"bw_az_{radar_index}"
            )
            
            beamwidth_el = st.number_input(
                "俯仰波束宽度 (°)",
                0.1, 10.0, 2.5, 0.1,
                key=f"bw_el_{radar_index}"
            )
            
            scan_sector = st.slider(
                "扫描扇区 (°)",
                0, 360, (0, 360),
                key=f"sector_{radar_index}"
            )
        
        st.markdown("### 处理参数")
        col_proc1, col_proc2 = st.columns(2)
        
        with col_proc1:
            pulse_width_us = st.number_input(
                "脉冲宽度 (μs)",
                0.1, 100.0, 10.0, 0.1,
                key=f"pw_{radar_index}"
            )
            
            integration_pulses = st.number_input(
                "累积脉冲数",
                1, 1000, 10, 1,
                key=f"integ_{radar_index}"
            )
        
        with col_proc2:
            cfar_type = st.selectbox(
                "CFAR类型",
                ["CA-CFAR", "SO-CFAR", "GO-CFAR", "OS-CFAR"],
                key=f"cfar_{radar_index}"
            )
            
            false_alarm_rate = st.number_input(
                "虚警概率",
                1e-9, 1e-3, 1e-6, format="%e",
                key=f"pfa_{radar_index}"
            )
        
        # 提交按钮
        if st.form_submit_button("💾 保存配置", use_container_width=True):
            # 更新雷达配置
            st.session_state.radar_configs[radar_index].update({
                "frequency_mhz": frequency_mhz,
                "bandwidth_mhz": bandwidth_mhz,
                "peak_power_kw": peak_power_kw,
                "prf_hz": prf_hz,
                "antenna_gain_db": antenna_gain_db,
                "beamwidth_az": beamwidth_az,
                "beamwidth_el": beamwidth_el,
                "scan_sector": scan_sector,
                "pulse_width_us": pulse_width_us,
                "integration_pulses": integration_pulses,
                "cfar_type": cfar_type,
                "false_alarm_rate": false_alarm_rate,
                "last_modified": datetime.now().isoformat()
            })
            st.success(f"已保存 {selected_radar} 的配置")

def show_performance_analysis():
    """显示性能分析界面"""
    st.subheader("📊 雷达性能分析")
    
    radars = st.session_state.get('radar_configs', [])
    
    if not radars:
        st.warning("请先配置雷达")
        return
    
    # 选择雷达进行分析
    radar_names = [r['name'] for r in radars]
    selected_radar_name = st.selectbox("选择雷达进行分析", radar_names)
    
    radar = next(r for r in radars if r['name'] == selected_radar_name)
    
    # 性能指标计算
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 探测范围估计
        if all(k in radar for k in ['frequency_mhz', 'peak_power_kw', 'antenna_gain_db']):
            max_range = calculate_max_range(radar)
            create_data_card(
                "最大探测距离",
                f"{max_range:.0f}",
                "km",
                icon="📡"
            )
    
    with col2:
        # 分辨率
        if 'bandwidth_mhz' in radar:
            range_res = calculate_range_resolution(radar)
            create_data_card(
                "距离分辨率",
                f"{range_res:.1f}",
                "m",
                icon="📏"
            )
    
    with col3:
        # 更新率
        if all(k in radar for k in ['scan_sector', 'beamwidth_az', 'prf_hz']):
            update_rate = calculate_update_rate(radar)
            create_data_card(
                "数据更新率",
                f"{update_rate:.1f}",
                "Hz",
                icon="🔄"
            )
    
    st.markdown("---")
    
    # 性能图表
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 📶 探测性能曲线")
        
        # 生成探测概率曲线
        if all(k in radar for k in ['frequency_mhz', 'peak_power_kw', 'antenna_gain_db']):
            snr_values, detection_prob = generate_detection_curve(radar)
            
            chart_data = pd.DataFrame({
                'SNR (dB)': snr_values,
                'Detection Probability': detection_prob
            })
            
            st.line_chart(chart_data, x='SNR (dB)', y='Detection Probability')
    
    with col_chart2:
        st.markdown("#### 🎯 覆盖范围")
        
        # 生成覆盖范围图
        if 'position' in radar and 'range_km' in radar:
            # 这里可以添加更复杂的覆盖范围计算
            coverage_area = np.pi * radar['range_km'] ** 2
            st.metric("覆盖面积", f"{coverage_area:,.0f} km²")
            
            # 简单显示覆盖范围
            st.info(f"以雷达为中心，半径 {radar['range_km']}km 的圆形区域")

def calculate_max_range(radar_config):
    """计算最大探测距离（简化雷达方程）"""
    # 雷达方程: R^4 = (Pt * G^2 * λ^2 * σ) / ((4π)^3 * k * T * B * SNR * L)
    # 这里使用简化计算
    frequency = radar_config.get('frequency_mhz', 3000)  # MHz
    wavelength = 300 / frequency  # 波长 (m)
    power = radar_config.get('peak_power_kw', 500) * 1000  # W
    gain = 10 ** (radar_config.get('antenna_gain_db', 30) / 10)  # 线性
    
    # 假设目标RCS为1 m²，SNR=13dB，损失=10dB
    target_rcs = 1  # m²
    snr_linear = 10 ** (13 / 10)  # 13dB
    losses = 10 ** (10 / 10)  # 10dB损失
    
    # 计算最大距离
    numerator = power * (gain ** 2) * (wavelength ** 2) * target_rcs
    denominator = (4 * np.pi) ** 3 * snr_linear * losses
    max_range = (numerator / denominator) ** 0.25
    
    return max_range / 1000  # 转换为km

def calculate_range_resolution(radar_config):
    """计算距离分辨率"""
    bandwidth = radar_config.get('bandwidth_mhz', 10) * 1e6  # Hz
    c = 3e8  # 光速 (m/s)
    range_res = c / (2 * bandwidth)  # 距离分辨率
    return range_res

def calculate_update_rate(radar_config):
    """计算数据更新率"""
    scan_sector = radar_config.get('scan_sector', (0, 360))
    sector_width = scan_sector[1] - scan_sector[0]
    beamwidth = radar_config.get('beamwidth_az', 2.5)
    prf = radar_config.get('prf_hz', 1000)
    
    # 简化计算：扫描整个扇区所需时间
    scan_time = (sector_width / beamwidth) * (1 / prf)
    update_rate = 1 / scan_time if scan_time > 0 else 0
    
    return update_rate

def generate_detection_curve(radar_config):
    """生成探测概率曲线"""
    snr_values = np.linspace(0, 20, 50)
    
    # 使用Swerling I模型计算探测概率
    pfa = radar_config.get('false_alarm_rate', 1e-6)
    detection_prob = []
    
    for snr in snr_values:
        # 简化计算
        threshold = -np.log(pfa)
        prob = 1 - (1 + snr/10) ** (-threshold)
        detection_prob.append(min(prob, 1.0))
    
    return snr_values, detection_prob

def show_configuration_management():
    """显示配置管理界面"""
    st.subheader("🗂️ 雷达配置管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 保存配置")
        
        config_name = st.text_input("配置名称", value="雷达配置")
        
        if st.button("保存当前配置", use_container_width=True):
            save_radar_configuration(config_name)
    
    with col2:
        st.markdown("### 📂 加载配置")
        
        # 加载已有配置
        config_files = list_configuration_files()
        
        if config_files:
            selected_config = st.selectbox(
                "选择配置文件",
                config_files
            )
            
            if st.button("加载选中配置", use_container_width=True):
                load_radar_configuration(selected_config)
        else:
            st.info("暂无保存的配置")
    
    st.markdown("---")
    
    # 配置导出/导入
    st.markdown("### 🔄 数据交换")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        if st.button("📤 导出JSON配置", use_container_width=True):
            export_configuration()
    
    with col_exp2:
        uploaded_file = st.file_uploader("导入JSON文件", type=['json'])
        if uploaded_file is not None:
            if st.button("📥 导入配置", use_container_width=True):
                import_configuration(uploaded_file)
    
    st.markdown("---")
    
    # 批量操作
    st.markdown("### ⚡ 批量操作")
    
    if st.button("🔄 重置所有雷达", type="secondary", use_container_width=True):
        st.session_state.radar_configs = []
        st.success("已重置所有雷达配置")
        st.rerun()
    
    if st.button("🧹 清除无效配置", type="secondary", use_container_width=True):
        clear_invalid_configurations()

def save_radar_configuration(config_name):
    """保存雷达配置"""
    import json
    from pathlib import Path
    
    config_data = {
        "name": config_name,
        "radar_configs": st.session_state.get('radar_configs', []),
        "save_time": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    config_dir = Path("data/radar_configs")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    config_file = config_dir / filename
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    st.success(f"配置已保存: {filename}")

def list_configuration_files():
    """列出配置文件"""
    from pathlib import Path
    
    config_dir = Path("data/radar_configs")
    if not config_dir.exists():
        return []
    
    config_files = []
    for file in config_dir.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                config_files.append({
                    "name": config_data.get('name', file.stem),
                    "file": file.name,
                    "time": config_data.get('save_time', ''),
                    "radar_count": len(config_data.get('radar_configs', []))
                })
        except:
            continue
    
    # 按时间排序
    config_files.sort(key=lambda x: x.get('time', ''), reverse=True)
    
    return [f"{f['name']} ({f['radar_count']}个雷达)" for f in config_files]

def load_radar_configuration(config_name):
    """加载雷达配置"""
    from pathlib import Path
    
    # 提取文件名
    file_match = config_name.split(' (')[0]
    
    config_dir = Path("data/radar_configs")
    config_file = None
    
    for file in config_dir.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            if config_data.get('name') == file_match:
                config_file = file
                break
    
    if config_file:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            st.session_state.radar_configs = config_data.get('radar_configs', [])
            st.success(f"已加载配置: {config_data.get('name')}")
            st.rerun()
    else:
        st.error("配置文件未找到")

def export_configuration():
    """导出配置为JSON"""
    config_data = {
        "radar_configs": st.session_state.get('radar_configs', []),
        "export_time": datetime.now().isoformat()
    }
    
    st.download_button(
        label="📥 下载JSON文件",
        data=json.dumps(config_data, indent=2, ensure_ascii=False),
        file_name=f"radar_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def import_configuration(uploaded_file):
    """导入配置"""
    try:
        config_data = json.load(uploaded_file)
        st.session_state.radar_configs = config_data.get('radar_configs', [])
        st.success("配置导入成功")
        st.rerun()
    except Exception as e:
        st.error(f"导入失败: {e}")

def clear_invalid_configurations():
    """清除无效配置"""
    radars = st.session_state.get('radar_configs', [])
    valid_radars = []
    
    for radar in radars:
        # 检查必要字段
        if all(k in radar for k in ['name', 'position', 'range_km']):
            valid_radars.append(radar)
    
    removed_count = len(radars) - len(valid_radars)
    st.session_state.radar_configs = valid_radars
    
    if removed_count > 0:
        st.success(f"已清除 {removed_count} 个无效配置")
    else:
        st.info("未发现无效配置")

if __name__ == "__main__":
    main()