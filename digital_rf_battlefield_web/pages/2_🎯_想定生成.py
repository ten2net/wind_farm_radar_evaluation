"""
想定生成页面 - 基于Kimi API的智能想定生成
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from datetime import datetime
import requests
from utils.kimi_api import generate_scenario_with_kimi
from components.maps import create_military_map, add_radar_to_map, add_target_to_map

def main():
    """想定生成页面主函数"""
    st.title("🎯 AI想定生成")
    st.markdown("使用Kimi大模型智能生成战场想定")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📝 想定描述", "🗺️ 地图配置", "⚙️ 参数设置"])
    
    with tab1:
        show_scenario_description()
    
    with tab2:
        show_map_configuration()
    
    with tab3:
        show_parameter_settings()

def show_scenario_description():
    """显示想定描述界面"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 想定描述输入
        st.subheader("想定描述")
        scenario_description = st.text_area(
            "描述您的想定场景:",
            value="红方3架战斗机从西沙群岛起飞，拦截向中国领空飞来的2架蓝方轰炸机，确保领空安全。",
            height=200,
            placeholder="例如：在南海区域，红方3架战斗机从西沙群岛起飞，拦截向中国领空飞来的2架蓝方轰炸机，确保领空安全...",
            help="详细描述战场环境、双方兵力、任务目标等信息"
        )
        
        # 想定类型
        scenario_type = st.selectbox(
            "想定类型",
            ["空中监视", "防空作战", "电子对抗", "多目标跟踪", "联合演习", "自定义"],
            index=0
        )
        
        # 复杂度设置
        complexity = st.slider("想定复杂度", 1, 10, 5, 
                             help="复杂度越高，生成的想定越详细")
    
    with col2:
        # Kimi API配置
        st.subheader("AI配置")
        
        api_key = st.text_input(
            "Kimi API密钥",
            type="password",
            help="输入您的Kimi API密钥"
        )
        
        if api_key:
            st.session_state.kimi_api_key = api_key
            st.success("✅ API密钥已设置")
        
        # 生成选项
        st.subheader("生成选项")
        
        generate_option = st.radio(
            "生成方式",
            ["快速生成", "详细生成", "定制生成"],
            index=0
        )
        
        temperature = st.slider("创意度", 0.0, 1.0, 0.7, 0.1,
                              help="控制生成的创造性，值越高创意性越强")
        
        # 生成按钮
        if st.button("🚀 生成想定", type="primary", use_container_width=True):
            if scenario_description and api_key:
                with st.spinner("AI正在生成想定..."):
                    scenario = generate_scenario_with_kimi(
                        api_key=api_key,
                        description=scenario_description,
                        scenario_type=scenario_type,
                        complexity=complexity,
                        temperature=temperature
                    )
                    
                    if scenario:
                        st.session_state.scenario_data = scenario
                        st.success("✅ 想定生成成功！")
                        show_scenario_preview(scenario)
                    else:
                        st.error("❌ 想定生成失败，请检查API密钥和网络连接")
            else:
                st.warning("⚠️ 请输入想定描述和API密钥")

def show_scenario_preview(scenario):
    """显示想定预览"""
    with st.expander("📋 生成的想定详情", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 想定概述")
            st.markdown(f"**名称:** {scenario.get('name', '未命名')}")
            st.markdown(f"**类型:** {scenario.get('type', '未知')}")
            st.markdown(f"**地区:** {scenario.get('region', '未知')}")
            st.markdown(f"**时间:** {scenario.get('time', '未知')}")
            
            st.markdown("### 红方力量")
            print(">>>>>>>>>",scenario)
            red_forces = scenario.get('red_forces', {})
            print("红方力量:", red_forces)
            st.markdown(f"**雷达数量:** {len(scenario.get('radar_configs', []))}")
            st.markdown(f"**目标数量:** {len(scenario.get('target_configs', []))}")
            # st.markdown(f"**雷达数量:** {red_forces.get('radar_count', 0)}")
            # st.markdown(f"**目标数量:** {red_forces.get('target_count', 0)}")
        
        with col2:
            st.markdown("### 蓝方力量")
            blue_forces = scenario.get('blue_forces', {})
            st.markdown(f"**雷达数量:** {blue_forces.get('radar_count', 0)}")
            st.markdown(f"**目标数量:** {blue_forces.get('target_count', 0)}")
            
            st.markdown("### 环境条件")
            environment = scenario.get('environment', {})
            st.markdown(f"**天气:** {environment.get('weather', '未知')}")
            st.markdown(f"**能见度:** {environment.get('visibility', '未知')}")
        
        # 任务描述
        st.markdown("### 任务描述")
        st.markdown(scenario.get('mission_description', '无描述'))

def show_map_configuration():
    """显示地图配置界面"""
    st.subheader("🗺️ 战场地图配置")
    
    # 创建地图
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 初始化地图
        if 'map_center' not in st.session_state:
            st.session_state.map_center = [39.9042, 119.4074]
        
        m = create_military_map(
            center=st.session_state.map_center,
            zoom_start=st.session_state.get('map_zoom', 5),
            style="OpenStreetMap"
        )
        
        # 添加地图交互控件
        folium.LatLngPopup().add_to(m)
        # folium.MeasureControl(position='topleft').add_to(m)
        
        # 显示地图
        map_data = st_folium(m, width=700, height=500)
        
        # 更新地图状态
        if map_data.get("last_clicked"):
            st.session_state.map_center = [
                map_data["last_clicked"]["lat"],
                map_data["last_clicked"]["lng"]
            ]
        
        if map_data.get("zoom"):
            st.session_state.map_zoom = map_data["zoom"]
    
    with col2:
        # 地图控制
        st.markdown("### 地图控制")
        
        # 中心点设置
        lat = st.number_input("纬度", -90.0, 90.0, st.session_state.map_center[0], 0.1)
        lng = st.number_input("经度", -180.0, 180.0, st.session_state.map_center[1], 0.1)
        
        if st.button("定位到坐标", use_container_width=True):
            st.session_state.map_center = [lat, lng]
            st.rerun()
        
        # 预设区域
        preset_areas = {
            "南海地区": [15.0, 115.0],
            "台海地区": [25.0, 121.0],
            "东海地区": [30.0, 123.0],
            "华北平原": [39.0, 116.0],
            "青藏高原": [32.0, 91.0]
        }
        
        selected_area = st.selectbox("预设区域", list(preset_areas.keys()))
        
        if st.button("跳转到区域", use_container_width=True):
            st.session_state.map_center = preset_areas[selected_area]
            st.session_state.map_zoom = 6
            st.rerun()
        
        # 地图样式
        map_style = st.selectbox(
            "地图样式",
            ["军事地形图", "卫星影像", "街道图", "暗色模式"],
            index=0
        )

def show_parameter_settings():
    """显示参数设置界面"""
    st.subheader("⚙️ 想定参数设置")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 兵力参数")
        
        # 雷达数量
        radar_count = st.number_input("雷达数量", 1, 20, 3, 1,
                                    help="部署的雷达系统数量")
        
        # 雷达类型分布
        st.markdown("**雷达类型分布**")
        phased_ratio = st.slider("相控阵雷达", 0.0, 1.0, 0.6, 0.1)
        mechanical_ratio = st.slider("机械扫描雷达", 0.0, 1.0, 0.3, 0.1)
        passive_ratio = 1.0 - phased_ratio - mechanical_ratio
        st.metric("无源雷达", f"{passive_ratio:.1%}")
    
    with col2:
        st.markdown("### 目标参数")
        
        # 目标数量
        target_count = st.number_input("目标数量", 1, 100, 10, 1,
                                     help="模拟的目标数量")
        
        # 目标类型分布
        st.markdown("**目标类型分布**")
        fighter_ratio = st.slider("战斗机", 0.0, 1.0, 0.4, 0.1)
        uav_ratio = st.slider("无人机", 0.0, 1.0, 0.3, 0.1)
        missile_ratio = st.slider("巡航导弹", 0.0, 1.0, 0.2, 0.1)
        other_ratio = 1.0 - fighter_ratio - uav_ratio - missile_ratio
        st.metric("其他目标", f"{other_ratio:.1%}")
    
    with col3:
        st.markdown("### 环境参数")
        
        # 天气条件
        weather = st.selectbox(
            "天气条件",
            ["晴朗", "多云", "小雨", "大雨", "雾", "雪"],
            index=0
        )
        
        # 能见度
        visibility = st.slider("能见度 (km)", 1, 50, 20, 1)
        
        # 电子环境
        ecm_intensity = st.slider("电子对抗强度", 0, 10, 3, 1,
                                help="0=无干扰，10=强干扰")
        
        # 保存参数
        if st.button("💾 保存参数配置", use_container_width=True):
            params = {
                "radar_count": radar_count,
                "radar_distribution": {
                    "phased_array": phased_ratio,
                    "mechanical": mechanical_ratio,
                    "passive": passive_ratio
                },
                "target_count": target_count,
                "target_distribution": {
                    "fighter": fighter_ratio,
                    "uav": uav_ratio,
                    "missile": missile_ratio,
                    "other": other_ratio
                },
                "weather": weather,
                "visibility": visibility,
                "ecm_intensity": ecm_intensity,
                "save_time": datetime.now().isoformat()
            }
            
            st.session_state.scenario_params = params
            st.success("✅ 参数配置已保存")

if __name__ == "__main__":
    main()