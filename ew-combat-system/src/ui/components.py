"""
Streamlit UI组件模块
"""
import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import numpy as np

def create_header():
    """创建页面标题"""
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(45deg, #00d4ff, #0088ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0 2px 10px rgba(0, 212, 255, 0.3);
    }
    .sub-title {
        font-size: 1.2rem;
        color: #a0a0ff;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">🛡️ 电子战对抗仿真系统</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">高级电子战体系对抗仿真与评估平台</p>', unsafe_allow_html=True)

def create_status_bar(radar_count, jammer_count, target_count, scenario_name="未选择"):
    """创建状态栏"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📡 当前想定", scenario_name)
    
    with col2:
        st.metric("🎯 雷达数量", radar_count)
    
    with col3:
        st.metric("⚡ 干扰机数量", jammer_count)
    
    with col4:
        st.metric("✈️ 目标数量", target_count)

def create_scenario_selector(scenarios, on_change=None):
    """创建想定选择器"""
    scenario_options = {s["id"]: f"{s['icon']} {s['name']}" for s in scenarios}
    
    selected = st.selectbox(
        "选择对抗想定",
        options=list(scenario_options.keys()),
        format_func=lambda x: scenario_options[x],
        help="选择要仿真的对抗想定类型"
    )
    
    # 显示想定描述
    selected_scenario = next((s for s in scenarios if s["id"] == selected), None)
    if selected_scenario:
        st.info(f"**{selected_scenario['name']}**: {selected_scenario['description']}")
    
    if on_change and st.button("创建想定", type="primary"):
        on_change(selected)
    
    return selected

def create_entity_configurator(entity_type, config, on_save=None):
    """创建实体配置器"""
    with st.expander(f"⚙️ 配置{entity_type}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("名称", value=config.get("name", f"新{entity_type}"))
            entity_id = st.text_input("ID", value=config.get("id", f"{entity_type}_001"))
        
        with col2:
            lat = st.number_input("纬度", value=config.get("lat", 39.9), 
                                min_value=-90.0, max_value=90.0, step=0.1)
            lon = st.number_input("经度", value=config.get("lon", 116.4), 
                                min_value=-180.0, max_value=180.0, step=0.1)
        
        # 技术参数
        st.subheader("技术参数")
        
        if entity_type == "雷达":
            freq = st.slider("频率 (GHz)", 0.1, 40.0, config.get("frequency", 3.0), 0.1)
            power = st.slider("功率 (kW)", 1.0, 1000.0, config.get("power", 100.0), 10.0)
            range_max = st.slider("最大距离 (km)", 10.0, 500.0, config.get("range_max", 300.0), 10.0)
        
        elif entity_type == "干扰机":
            power = st.slider("功率 (W)", 1.0, 5000.0, config.get("power", 1000.0), 100.0)
            beamwidth = st.slider("波束宽度 (°)", 5.0, 120.0, config.get("beamwidth", 60.0), 5.0)
            jam_type = st.selectbox("干扰类型", ["阻塞式", "瞄准式", "扫频式"], 
                                  index=["阻塞式", "瞄准式", "扫频式"].index(config.get("jam_type", "阻塞式")))
        
        # 保存按钮
        if on_save and st.button(f"💾 保存{entity_type}配置", type="secondary"):
            new_config = {
                "id": entity_id,
                "name": name,
                "lat": lat,
                "lon": lon
            }
            
            if entity_type == "雷达":
                new_config.update({
                    "frequency": freq,
                    "power": power,
                    "range_max": range_max
                })
            elif entity_type == "干扰机":
                new_config.update({
                    "power": power,
                    "beamwidth": beamwidth,
                    "jam_type": jam_type
                })
            
            on_save(new_config)
            st.success(f"{entity_type}配置已保存")

def create_simulation_controls(on_start=None, on_pause=None, on_reset=None):
    """创建仿真控制面板"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        simulation_speed = st.select_slider(
            "仿真速度",
            options=["0.5x", "1x", "2x", "5x", "10x"],
            value="1x"
        )
    
    with col2:
        duration = st.number_input("仿真时长 (秒)", 10, 3600, 300, 10)
    
    with col3:
        st.markdown("### ")
        start_col, pause_col, reset_col = st.columns(3)
        
        with start_col:
            if on_start and st.button("▶️ 开始仿真", type="primary", use_container_width=True):
                on_start(simulation_speed, duration)
        
        with pause_col:
            if on_pause and st.button("⏸️ 暂停仿真", use_container_width=True):
                on_pause()
        
        with reset_col:
            if on_reset and st.button("🔄 重置仿真", use_container_width=True):
                on_reset()
    
    return simulation_speed, duration

def create_results_display(results):
    """创建结果展示面板"""
    if not results:
        st.warning("暂无仿真结果")
        return
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["📊 概览", "📈 图表", "📄 详情"])
    
    with tab1:
        # 显示关键指标
        st.subheader("关键效能指标")
        
        cols = st.columns(4)
        metrics = [
            ("干扰成功率", "jam_success_rate", "%"),
            ("探测概率", "detection_probability", "%"),
            ("干信比", "j_s_ratio", "dB"),
            ("系统生存性", "system_survivability", "%")
        ]
        
        for idx, (label, key, unit) in enumerate(metrics):
            with cols[idx]:
                value = results.get(key, 0)
                st.metric(label, f"{value:.1f}{unit}")
    
    with tab2:
        # 显示图表
        st.subheader("对抗效果分析")
        
        if "radar_results" in results:
            radar_names = [r["radar_name"] for r in results["radar_results"]]
            jam_effectiveness = [r.get("effective", False) for r in results["radar_results"]]
            
            df = pd.DataFrame({
                "雷达": radar_names,
                "干扰有效": jam_effectiveness
            })
            
            st.bar_chart(df.set_index("雷达"))
    
    with tab3:
        # 显示详细结果
        st.subheader("详细仿真结果")
        st.json(results)

def create_environment_settings(environment_config, on_update=None):
    """创建环境设置面板"""
    with st.expander("🌍 环境设置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            terrain = st.selectbox(
                "地形类型",
                ["平原", "丘陵", "山地", "城市", "海洋"],
                index=["平原", "丘陵", "山地", "城市", "海洋"].index(
                    environment_config.get("terrain", "平原")
                )
            )
            
            atmosphere = st.selectbox(
                "大气条件",
                ["标准", "异常传播", "雨天", "沙尘"],
                index=["标准", "异常传播", "雨天", "沙尘"].index(
                    environment_config.get("atmosphere", "标准")
                )
            )
        
        with col2:
            temperature = st.slider("温度 (°C)", -20, 50, 
                                  environment_config.get("temperature", 20))
            humidity = st.slider("湿度 (%)", 0, 100, 
                               environment_config.get("humidity", 50))
            rain_rate = st.slider("降雨率 (mm/h)", 0, 100, 
                                environment_config.get("rain_rate", 0))
        
        if on_update and st.button("更新环境设置", type="secondary"):
            new_config = {
                "terrain": terrain,
                "atmosphere": atmosphere,
                "temperature": temperature,
                "humidity": humidity,
                "rain_rate": rain_rate
            }
            on_update(new_config)
            st.success("环境设置已更新")

def create_export_panel(results, file_prefix="simulation_results"):
    """创建导出面板"""
    with st.expander("💾 数据导出", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 导出JSON"):
                if results:
                    import json
                    from datetime import datetime
                    
                    filename = f"{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    json_str = json.dumps(results, indent=2, ensure_ascii=False)
                    
                    st.download_button(
                        label="下载JSON文件",
                        data=json_str,
                        file_name=filename,
                        mime="application/json"
                    )
                else:
                    st.warning("没有可导出的数据")
        
        with col2:
            if st.button("📊 导出CSV"):
                if results and "radar_results" in results:
                    import pandas as pd
                    from datetime import datetime
                    
                    df = pd.DataFrame(results["radar_results"])
                    filename = f"{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    
                    st.download_button(
                        label="下载CSV文件",
                        data=df.to_csv(index=False).encode('utf-8'),
                        file_name=filename,
                        mime="text/csv"
                    )
        
        with col3:
            if st.button("🖼️ 导出图表"):
                st.info("图表导出功能开发中...")

def create_progress_bar(progress, message="处理中..."):
    """创建进度条"""
    if progress > 0:
        st.progress(progress)
        st.caption(message)
