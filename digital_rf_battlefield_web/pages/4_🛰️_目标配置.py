"""
目标配置页面 - 目标参数配置界面
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from utils.style_utils import create_data_card, get_military_style
from components.maps import create_military_map, add_target_to_map
from streamlit_folium import st_folium

def main():
    """目标配置页面主函数"""
    st.title("🛰️ 目标系统配置")
    st.markdown("配置目标参数、运动轨迹和电磁特性")
    
    # 初始化目标配置
    if 'target_configs' not in st.session_state:
        st.session_state.target_configs = []
    
    if 'target_catalog' not in st.session_state:
        load_target_catalog()
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📍 目标部署", "🛩️ 运动参数", "📡 电磁特性", "🗂️ 配置管理"])
    
    with tab1:
        show_target_deployment()
    
    with tab2:
        show_motion_parameters()
    
    with tab3:
        show_electromagnetic_properties()
    
    with tab4:
        show_target_management()

def load_target_catalog():
    """加载目标目录"""
    target_catalog = [
        {
            "id": "j-20",
            "name": "歼-20战斗机",
            "type": "fighter",
            "rcs_m2": 0.001,
            "max_speed_mach": 2.0,
            "cruise_speed_mach": 1.2,
            "max_altitude_m": 20000,
            "description": "第五代隐形战斗机"
        },
        {
            "id": "h-6k",
            "name": "轰-6K轰炸机",
            "type": "bomber",
            "rcs_m2": 10.0,
            "max_speed_mach": 0.8,
            "cruise_speed_mach": 0.7,
            "max_altitude_m": 15000,
            "description": "战略轰炸机"
        },
        {
            "id": "ch-5",
            "name": "彩虹-5无人机",
            "type": "uav",
            "rcs_m2": 0.1,
            "max_speed_mach": 0.3,
            "cruise_speed_mach": 0.2,
            "max_altitude_m": 9000,
            "description": "中高空长航时无人机"
        },
        {
            "id": "cj-10",
            "name": "CJ-10巡航导弹",
            "type": "missile",
            "rcs_m2": 0.01,
            "max_speed_mach": 0.8,
            "cruise_speed_mach": 0.7,
            "max_altitude_m": 50,
            "description": "远程巡航导弹"
        },
        {
            "id": "y-20",
            "name": "运-20运输机",
            "type": "transport",
            "rcs_m2": 50.0,
            "max_speed_mach": 0.75,
            "cruise_speed_mach": 0.7,
            "max_altitude_m": 13000,
            "description": "大型军用运输机"
        }
    ]
    st.session_state.target_catalog = target_catalog

def show_target_deployment():
    """显示目标部署界面"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 创建部署地图
        st.subheader("🗺️ 目标部署地图")
        
        # 获取或设置地图中心
        if 'target_map_center' not in st.session_state:
            st.session_state.target_map_center = [39.9042, 116.4074]
        
        # 创建地图
        m = create_military_map(
            center=st.session_state.target_map_center,
            zoom_start=6
        )
        
        # 添加现有目标
        for target in st.session_state.get('target_configs', []):
            if 'position' in target and target['position']:
                add_target_to_map(
                    m,
                    position=target['position'],
                    target_type=target.get('type', 'fighter'),
                    name=target.get('name', '未知目标'),
                    speed_kts=target.get('speed_kts', 300),
                    altitude_m=target.get('altitude_m', 10000)
                )
        
        # 交互式地图
        map_data = st_folium(m, width=600, height=500)
        
        # 处理地图交互
        if map_data.get("last_clicked"):
            handle_target_map_click(map_data["last_clicked"])
    
    with col2:
        # 目标部署控制
        st.subheader("📍 部署控制")
        
        # 添加新目标
        st.markdown("### 添加新目标")
        
        target_type = st.selectbox(
            "目标类型",
            ["fighter", "bomber", "uav", "missile", "transport", "ship", "vehicle"],
            format_func=lambda x: {
                "fighter": "战斗机",
                "bomber": "轰炸机",
                "uav": "无人机",
                "missile": "导弹",
                "transport": "运输机",
                "ship": "舰船",
                "vehicle": "车辆"
            }.get(x, x)
        )
        
        # 从目录选择
        target_catalog = st.session_state.get('target_catalog', [])
        target_templates = {t['name']: t for t in target_catalog if t['type'] == target_type}
        
        if target_templates:
            selected_template = st.selectbox(
                "选择目标型号",
                list(target_templates.keys())
            )
            
            if st.button("📋 加载模板", use_container_width=True):
                template = target_templates[selected_template]
                st.session_state.selected_target_template = template
                st.success(f"已加载 {selected_template} 模板")
        
        # 手动输入目标名称
        target_name = st.text_input("目标名称", value="目标")
        
        # 位置选择方式
        location_method = st.radio(
            "位置选择方式",
            ["地图点击", "手动输入", "随机生成"],
            horizontal=True
        )
        
        if location_method == "手动输入":
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input("纬度", -90.0, 90.0, 39.9042, 0.001)
            with col_lng:
                longitude = st.number_input("经度", -180.0, 180.0, 116.4074, 0.001)
            position = [latitude, longitude]
        elif location_method == "随机生成":
            if st.button("🎲 生成随机位置", use_container_width=True):
                position = generate_random_position()
                st.session_state.selected_target_position = position
                st.success(f"已生成位置: {position[0]:.4f}, {position[1]:.4f}")
            position = st.session_state.get('selected_target_position', [39.9042, 116.4074])
        else:
            position = st.session_state.get('selected_target_position')
            if position:
                st.info(f"已选择位置: {position[0]:.4f}, {position[1]:.4f}")
            else:
                st.warning("请在地图上点击选择位置")
                position = [39.9042, 116.4074]
        
        # 初始高度
        altitude = st.slider(
            "初始高度 (m)",
            0, 30000, 10000, 100,
            help="目标飞行高度"
        )
        
        # 初始速度
        speed = st.slider(
            "初始速度 (节)",
            0, 2000, 300, 10,
            help="目标飞行速度"
        )
        
        # 添加目标按钮
        if st.button("➕ 添加目标", type="primary", use_container_width=True):
            add_new_target(target_name, target_type, position, altitude, speed)
        
        st.markdown("---")
        
        # 目标列表
        st.subheader("📋 已部署目标")
        show_target_list()

def handle_target_map_click(click_data):
    """处理目标地图点击事件"""
    lat = click_data["lat"]
    lng = click_data["lng"]
    st.session_state.selected_target_position = [lat, lng]
    
    # 显示位置信息
    st.sidebar.info(f"已选择目标位置: {lat:.4f}, {lng:.4f}")

def generate_random_position():
    """生成随机位置"""
    # 在设定范围内随机生成位置
    lat = np.random.uniform(30.0, 45.0)
    lng = np.random.uniform(110.0, 125.0)
    return [lat, lng]

def add_new_target(name, target_type, position, altitude, speed):
    """添加新目标"""
    new_target = {
        "id": f"target_{len(st.session_state.target_configs) + 1:03d}",
        "name": name,
        "type": target_type,
        "position": position,
        "altitude_m": altitude,
        "speed_kts": speed,
        "heading_deg": 0,  # 默认航向
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    # 如果选择了模板，应用模板参数
    if 'selected_target_template' in st.session_state:
        template = st.session_state.selected_target_template
        new_target.update({
            "rcs_m2": template.get('rcs_m2'),
            "max_speed_mach": template.get('max_speed_mach'),
            "cruise_speed_mach": template.get('cruise_speed_mach'),
            "max_altitude_m": template.get('max_altitude_m'),
            "description": template.get('description')
        })
    
    st.session_state.target_configs.append(new_target)
    st.success(f"已添加目标: {name}")
    st.rerun()

def show_target_list():
    """显示目标列表"""
    targets = st.session_state.get('target_configs', [])
    
    if not targets:
        st.info("暂无部署目标")
        return
    
    for i, target in enumerate(targets):
        with st.expander(f"{target['name']} ({target.get('type', '未知')})", expanded=False):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**ID:** {target['id']}")
                st.markdown(f"**位置:** {target.get('position', ['N/A', 'N/A'])[0]:.4f}, {target.get('position', ['N/A', 'N/A'])[1]:.4f}")
                st.markdown(f"**高度:** {target.get('altitude_m', 0):,} m")
            
            with col2:
                speed = target.get('speed_kts', 0)
                mach = speed / 661.5  # 简化转换
                st.markdown(f"**速度:** {speed} 节 ({mach:.2f}马赫)")
                
                if 'rcs_m2' in target:
                    st.markdown(f"**RCS:** {target['rcs_m2']} m²")
            
            with col3:
                if st.button("🗑️", key=f"delete_target_{i}"):
                    st.session_state.target_configs.pop(i)
                    st.rerun()
                
                if st.button("✏️", key=f"edit_target_{i}"):
                    st.session_state.editing_target_index = i
                    st.switch_page("pages/4_🛰️_目标配置.py")

def show_motion_parameters():
    """显示运动参数配置界面"""
    st.subheader("🛩️ 目标运动参数")
    
    # 选择要配置的目标
    targets = st.session_state.get('target_configs', [])
    
    if not targets:
        st.warning("请先部署目标")
        return
    
    target_names = [t['name'] for t in targets]
    selected_target = st.selectbox("选择目标", target_names)
    
    # 找到选中的目标
    target_index = next(i for i, t in enumerate(targets) if t['name'] == selected_target)
    target = targets[target_index]
    
    # 创建运动参数表单
    with st.form(f"motion_form_{target_index}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 当前位置")
            
            # 当前位置编辑
            current_lat = st.number_input(
                "纬度",
                -90.0, 90.0, target.get('position', [0, 0])[0], 0.001,
                key=f"lat_{target_index}"
            )
            
            current_lng = st.number_input(
                "经度",
                -180.0, 180.0, target.get('position', [0, 0])[1], 0.001,
                key=f"lng_{target_index}"
            )
            
            current_alt = st.number_input(
                "高度 (m)",
                0, 30000, target.get('altitude_m', 10000), 100,
                key=f"alt_{target_index}"
            )
        
        with col2:
            st.markdown("### 运动参数")
            
            speed = st.number_input(
                "速度 (节)",
                0, 2000, target.get('speed_kts', 300), 10,
                key=f"speed_{target_index}"
            )
            
            heading = st.slider(
                "航向 (°)",
                0, 360, target.get('heading_deg', 0), 1,
                key=f"heading_{target_index}"
            )
            
            vertical_rate = st.number_input(
                "爬升率 (m/s)",
                -100, 100, 0, 1,
                key=f"vrate_{target_index}"
            )
        
        st.markdown("### 运动模式")
        motion_mode = st.radio(
            "选择运动模式",
            ["直线飞行", "盘旋", "随机机动", "预设航线"],
            horizontal=True,
            key=f"mode_{target_index}"
        )
        
        if motion_mode == "盘旋":
            col_circle1, col_circle2 = st.columns(2)
            with col_circle1:
                circle_radius = st.number_input(
                    "盘旋半径 (km)",
                    1, 100, 10, 1,
                    key=f"radius_{target_index}"
                )
            with col_circle2:
                circle_direction = st.radio(
                    "盘旋方向",
                    ["顺时针", "逆时针"],
                    horizontal=True,
                    key=f"cdir_{target_index}"
                )
        
        elif motion_mode == "预设航线":
            st.text_area(
                "航线坐标 (每行格式: 纬度,经度,高度)",
                "",
                height=100,
                key=f"route_{target_index}",
                help="例如:\n39.9,116.4,10000\n40.0,116.5,11000\n40.1,116.6,10500"
            )
        
        # 运动参数
        st.markdown("### 运动特性")
        col_motion1, col_motion2 = st.columns(2)
        
        with col_motion1:
            acceleration = st.number_input(
                "最大加速度 (m/s²)",
                0.1, 50.0, 5.0, 0.1,
                key=f"accel_{target_index}"
            )
            
            turn_rate = st.number_input(
                "最大转弯率 (°/s)",
                0.1, 30.0, 3.0, 0.1,
                key=f"turn_{target_index}"
            )
        
        with col_motion2:
            speed_variance = st.slider(
                "速度变化幅度 (%)",
                0, 50, 10, 1,
                key=f"speed_var_{target_index}"
            )
            
            alt_variance = st.slider(
                "高度变化幅度 (m)",
                0, 5000, 500, 100,
                key=f"alt_var_{target_index}"
            )
        
        # 提交按钮
        if st.form_submit_button("💾 保存运动参数", use_container_width=True):
            # 更新目标配置
            st.session_state.target_configs[target_index].update({
                "position": [current_lat, current_lng],
                "altitude_m": current_alt,
                "speed_kts": speed,
                "heading_deg": heading,
                "vertical_rate": vertical_rate,
                "motion_mode": motion_mode,
                "acceleration": acceleration,
                "turn_rate": turn_rate,
                "speed_variance": speed_variance,
                "alt_variance": alt_variance,
                "last_modified": datetime.now().isoformat()
            })
            
            if motion_mode == "盘旋":
                st.session_state.target_configs[target_index].update({
                    "circle_radius_km": circle_radius,
                    "circle_direction": circle_direction
                })
            
            st.success(f"已保存 {selected_target} 的运动参数")

def show_electromagnetic_properties():
    """显示电磁特性配置界面"""
    st.subheader("📡 目标电磁特性")
    
    # 选择要配置的目标
    targets = st.session_state.get('target_configs', [])
    
    if not targets:
        st.warning("请先部署目标")
        return
    
    target_names = [t['name'] for t in targets]
    selected_target = st.selectbox("选择目标配置", target_names)
    
    # 找到选中的目标
    target_index = next(i for i, t in enumerate(targets) if t['name'] == selected_target)
    target = targets[target_index]
    
    # 创建电磁特性表单
    with st.form(f"em_form_{target_index}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 雷达散射截面")
            
            rcs = st.number_input(
                "RCS (m²)",
                0.0001, 1000.0, target.get('rcs_m2', 1.0), 0.1,
                format="%.4f",
                key=f"rcs_{target_index}"
            )
            
            # RCS频率特性
            st.markdown("**RCS频率特性**")
            rcs_freq_dependency = st.selectbox(
                "频率相关性",
                ["常数", "线性", "平方", "复杂"],
                key=f"rcs_freq_{target_index}"
            )
            
            if rcs_freq_dependency != "常数":
                rcs_freq_min = st.number_input(
                    "最低频率RCS (m²)",
                    0.0001, 1000.0, rcs * 0.5, 0.1,
                    key=f"rcs_min_{target_index}"
                )
                rcs_freq_max = st.number_input(
                    "最高频率RCS (m²)",
                    0.0001, 1000.0, rcs * 2.0, 0.1,
                    key=f"rcs_max_{target_index}"
                )
            
            # RCS方位特性
            st.markdown("**RCS方位特性**")
            rcs_azimuth_variation = st.slider(
                "方位变化 (dB)",
                0, 40, 10, 1,
                key=f"rcs_azi_{target_index}"
            )
        
        with col2:
            st.markdown("### 辐射特性")
            
            # 辐射源
            st.markdown("**辐射源类型**")
            emitter_types = st.multiselect(
                "选择辐射源",
                ["雷达", "通信", "导航", "IFF", "ESM", "ECM"],
                default=["雷达", "IFF"],
                key=f"emitters_{target_index}"
            )
            
            if "雷达" in emitter_types:
                col_radar1, col_radar2 = st.columns(2)
                with col_radar1:
                    radar_freq_min = st.number_input(
                        "雷达频率范围 (MHz)",
                        100, 20000, 3000, 100,
                        key=f"radar_freq_min_{target_index}"
                    )
                with col_radar2:
                    radar_freq_max = st.number_input(
                        "",
                        100, 20000, 10000, 100,
                        key=f"radar_freq_max_{target_index}"
                    )
                
                radar_prf = st.number_input(
                    "雷达PRF (Hz)",
                    100, 10000, 1000, 100,
                    key=f"radar_prf_{target_index}"
                )
            
            if "ECM" in emitter_types:
                st.markdown("**电子对抗参数**")
                ecm_type = st.selectbox(
                    "ECM类型",
                    ["噪声干扰", "欺骗干扰", "复合干扰"],
                    key=f"ecm_type_{target_index}"
                )
                
                ecm_power = st.number_input(
                    "干扰功率 (kW)",
                    1, 1000, 100, 10,
                    key=f"ecm_power_{target_index}"
                )
        
        st.markdown("### 信号特性")
        
        # 信号参数
        col_sig1, col_sig2, col_sig3 = st.columns(3)
        
        with col_sig1:
            signal_power = st.number_input(
                "信号功率 (dBm)",
                -100, 100, 10, 1,
                key=f"sig_power_{target_index}"
            )
        
        with col_sig2:
            bandwidth = st.number_input(
                "带宽 (MHz)",
                0.1, 100.0, 10.0, 0.1,
                key=f"bandwidth_{target_index}"
            )
        
        with col_sig3:
            duty_cycle = st.slider(
                "占空比 (%)",
                0, 100, 10, 1,
                key=f"duty_{target_index}"
            )
        
        # 提交按钮
        if st.form_submit_button("💾 保存电磁参数", use_container_width=True):
            # 更新目标配置
            em_config = {
                "rcs_m2": rcs,
                "rcs_freq_dependency": rcs_freq_dependency,
                "rcs_azimuth_variation": rcs_azimuth_variation,
                "emitter_types": emitter_types,
                "signal_power_db": signal_power,
                "bandwidth_mhz": bandwidth,
                "duty_cycle": duty_cycle,
                "last_modified": datetime.now().isoformat()
            }
            
            if "雷达" in emitter_types:
                em_config.update({
                    "radar_freq_min_mhz": radar_freq_min,
                    "radar_freq_max_mhz": radar_freq_max,
                    "radar_prf_hz": radar_prf
                })
            
            if "ECM" in emitter_types:
                em_config.update({
                    "ecm_type": ecm_type,
                    "ecm_power_kw": ecm_power
                })
            
            st.session_state.target_configs[target_index].update(em_config)
            st.success(f"已保存 {selected_target} 的电磁参数")

def show_target_management():
    """显示目标管理界面"""
    st.subheader("🗂️ 目标配置管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 批量操作")
        
        # 批量添加目标
        st.markdown("**批量添加目标**")
        batch_count = st.number_input("目标数量", 1, 100, 10, 1)
        
        if st.button("🎲 批量随机生成", use_container_width=True):
            generate_batch_targets(batch_count)
    
    with col2:
        st.markdown("### 📊 目标统计")
        
        targets = st.session_state.get('target_configs', [])
        
        if targets:
            # 统计信息
            type_count = {}
            for target in targets:
                ttype = target.get('type', 'unknown')
                type_count[ttype] = type_count.get(ttype, 0) + 1
            
            st.markdown("**类型分布:**")
            for ttype, count in type_count.items():
                st.markdown(f"- {ttype}: {count}个")
            
            # 总统计
            st.markdown(f"**总数:** {len(targets)}个目标")
            
            # 平均速度
            avg_speed = np.mean([t.get('speed_kts', 0) for t in targets])
            st.markdown(f"**平均速度:** {avg_speed:.0f}节")
        else:
            st.info("暂无部署目标")
    
    st.markdown("---")
    
    # 目标分组
    st.markdown("### 👥 目标分组")
    
    # 创建分组
    col_group1, col_group2 = st.columns(2)
    
    with col_group1:
        group_name = st.text_input("分组名称", value="目标组")
        
        if st.button("创建新分组", use_container_width=True):
            create_target_group(group_name)
    
    with col_group2:
        # 显示现有分组
        if 'target_groups' in st.session_state:
            groups = st.session_state.target_groups
            group_names = list(groups.keys())
            
            if group_names:
                selected_group = st.selectbox("选择分组", group_names)
                st.info(f"分组 '{selected_group}' 包含 {len(groups[selected_group])} 个目标")
    
    st.markdown("---")
    
    # 数据导出
    st.markdown("### 📤 数据导出")
    
    export_format = st.radio(
        "导出格式",
        ["JSON", "CSV", "KML"],
        horizontal=True
    )
    
    if st.button("导出目标数据", use_container_width=True):
        export_target_data(export_format)

def generate_batch_targets(count):
    """批量生成目标"""
    for i in range(count):
        # 随机生成目标
        target_types = ["fighter", "bomber", "uav", "missile", "transport"]
        target_type = np.random.choice(target_types)
        
        # 随机位置
        lat = np.random.uniform(30.0, 45.0)
        lng = np.random.uniform(110.0, 125.0)
        position = [lat, lng]
        
        # 随机参数
        altitude = np.random.randint(1000, 20000, 1000)
        speed = np.random.randint(200, 800)
        
        # 添加目标
        new_target = {
            "id": f"target_batch_{len(st.session_state.target_configs) + 1:03d}",
            "name": f"批量目标{i+1}",
            "type": target_type,
            "position": position,
            "altitude_m": altitude,
            "speed_kts": speed,
            "heading_deg": np.random.randint(0, 360),
            "rcs_m2": np.random.uniform(0.001, 10.0),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        st.session_state.target_configs.append(new_target)
    
    st.success(f"已批量生成 {count} 个目标")
    st.rerun()

def create_target_group(group_name):
    """创建目标分组"""
    if 'target_groups' not in st.session_state:
        st.session_state.target_groups = {}
    
    st.session_state.target_groups[group_name] = []
    st.success(f"已创建分组: {group_name}")

def export_target_data(format):
    """导出目标数据"""
    targets = st.session_state.get('target_configs', [])
    
    if not targets:
        st.warning("没有目标数据可导出")
        return
    
    if format == "JSON":
        export_data = {
            "targets": targets,
            "export_time": datetime.now().isoformat(),
            "count": len(targets)
        }
        
        st.download_button(
            label="📥 下载JSON文件",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"targets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    elif format == "CSV":
        # 转换为DataFrame
        df = pd.DataFrame(targets)
        
        # 清理数据用于CSV
        for col in df.columns:
            if isinstance(df[col].iloc[0] if not df.empty else None, list):
                df[col] = df[col].apply(lambda x: str(x))
        
        csv_data = df.to_csv(index=False)
        
        st.download_button(
            label="📥 下载CSV文件",
            data=csv_data,
            file_name=f"targets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()