"""
仿真配置页面 - 仿真参数和时间配置界面
"""

import streamlit as st
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.style_utils import create_data_card, create_gauge_chart, get_military_style

def main():
    """仿真配置页面主函数"""
    st.title("⚙️ 仿真参数配置")
    st.markdown("配置仿真参数、时间设置和环境条件")
    
    # 初始化仿真配置
    if 'simulation_config' not in st.session_state:
        st.session_state.simulation_config = get_default_config()
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["⏱️ 时间设置", "🌍 环境条件", "📈 性能参数", "💾 配置管理"])
    
    with tab1:
        show_time_settings()
    
    with tab2:
        show_environment_settings()
    
    with tab3:
        show_performance_settings()
    
    with tab4:
        show_configuration_settings()

def get_default_config():
    """获取默认配置"""
    return {
        "time_settings": {
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": 300,
            "time_step": 0.1,
            "real_time_factor": 1.0
        },
        "environment": {
            "weather": "clear",
            "visibility_km": 20,
            "temperature_c": 15,
            "humidity_percent": 60,
            "wind_speed_kts": 10,
            "wind_direction_deg": 0,
            "sea_state": 1,
            "terrain_type": "flat"
        },
        "performance": {
            "simulation_speed": "normal",
            "data_logging": True,
            "log_interval": 1.0,
            "max_memory_mb": 4096,
            "parallel_processing": True,
            "num_threads": 4
        },
        "advanced": {
            "random_seed": 42,
            "enable_interference": True,
            "enable_multipath": False,
            "signal_attenuation_model": "free_space",
            "atmospheric_model": "standard"
        }
    }

def show_time_settings():
    """显示时间设置界面"""
    st.subheader("⏱️ 仿真时间设置")
    
    config = st.session_state.simulation_config.get('time_settings', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 时间参数")
        
        # 开始时间
        print(">>>>>>>>>>>>>>>>", config.get('start_time'))
        start_time = st.datetime_input(
            "仿真开始时间",
            # datetime.strptime(config.get('start_time', datetime.now().isoformat()), "%Y-%m-%d %H:%M:%S"),
            key="sim_start_time"
        )
        
        # 仿真时长
        duration_options = {
            "30秒 (快速测试)": 30,
            "1分钟": 60,
            "5分钟": 300,
            "10分钟": 600,
            "30分钟": 1800,
            "1小时": 3600,
            "自定义": None
        }
        
        duration_preset = st.selectbox(
            "仿真时长预设",
            list(duration_options.keys())
        )
        
        if duration_options[duration_preset] is None:
            duration = st.number_input(
                "仿真时长 (秒)",
                1, 86400, config.get('duration_seconds', 300), 1
            )
        else:
            duration = duration_options[duration_preset]
            st.info(f"时长: {duration} 秒 ({duration/60:.1f} 分钟)")
    
    with col2:
        st.markdown("### 时间控制")
        
        # 时间步长
        time_step_options = {
            "0.01秒 (高精度)": 0.01,
            "0.1秒 (标准)": 0.1,
            "1秒 (快速)": 1.0,
            "自定义": None
        }
        
        time_step_preset = st.selectbox(
            "时间步长预设",
            list(time_step_options.keys())
        )
        
        if time_step_preset == "自定义":
            time_step = st.number_input(
                "时间步长 (秒)",
                0.001, 10.0, config.get('time_step', 0.1), 0.001,
                format="%.3f"
            )
        else:
            time_step = time_step_options[time_step_preset]
            st.info(f"时间步长: {time_step} 秒")
        
        # 实时因子
        real_time_factor = st.slider(
            "实时因子",
            0.1, 10.0, config.get('real_time_factor', 1.0), 0.1,
            help="1.0=实时，<1.0=慢于实时，>1.0=快于实时"
        )
        
        # 计算仿真时间
        estimated_real_time = duration / real_time_factor
        st.info(f"预计实际运行时间: {estimated_real_time:.1f} 秒")
    
    st.markdown("---")
    
    # 时间轴预览
    st.markdown("### 📅 时间轴预览")
    
    time_data = {
        "时间点": ["开始", "1/4", "中点", "3/4", "结束"],
        "仿真时间 (秒)": [0, duration/4, duration/2, duration*3/4, duration],
        "实际时间 (秒)": [0, estimated_real_time/4, estimated_real_time/2, estimated_real_time*3/4, estimated_real_time]
    }
    
    df_time = pd.DataFrame(time_data)
    st.dataframe(df_time, use_container_width=True, hide_index=True)
    
    # 保存按钮
    if st.button("💾 保存时间设置", type="primary", use_container_width=True):
        st.session_state.simulation_config['time_settings'] = {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": duration,
            "time_step": time_step,
            "real_time_factor": real_time_factor
        }
        st.success("时间设置已保存")

def show_environment_settings():
    """显示环境设置界面"""
    st.subheader("🌍 环境条件设置")
    
    config = st.session_state.simulation_config.get('environment', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 天气条件")
        
        weather = st.selectbox(
            "天气状况",
            ["晴朗", "多云", "小雨", "大雨", "雾", "雪", "风暴"],
            index=["晴朗", "多云", "小雨", "大雨", "雾", "雪", "风暴"].index(
                config.get('weather', '晴朗')
            ) if config.get('weather', '晴朗') in ["晴朗", "多云", "小雨", "大雨", "雾", "雪", "风暴"] else 0
        )
        
        visibility = st.slider(
            "能见度 (km)",
            0.1, 50.0, config.get('visibility_km', 20.0), 0.1
        )
        
        temperature = st.slider(
            "温度 (°C)",
            -50, 50, config.get('temperature_c', 15), 1
        )
        
        humidity = st.slider(
            "湿度 (%)",
            0, 100, config.get('humidity_percent', 60), 1
        )
    
    with col2:
        st.markdown("### 大气条件")
        
        wind_speed = st.slider(
            "风速 (节)",
            0, 100, config.get('wind_speed_kts', 10), 1
        )
        
        wind_direction = st.slider(
            "风向 (°)",
            0, 360, config.get('wind_direction_deg', 0), 1
        )
        
        sea_state = st.selectbox(
            "海况",
            ["平静", "轻浪", "中浪", "大浪", "巨浪", "狂浪"],
            index=config.get('sea_state', 1) - 1
        )
        
        terrain_type = st.selectbox(
            "地形类型",
            ["平坦", "丘陵", "山地", "城市", "海洋", "混合"],
            index=["平坦", "丘陵", "山地", "城市", "海洋", "混合"].index(
                config.get('terrain_type', '平坦')
            ) if config.get('terrain_type', '平坦') in ["平坦", "丘陵", "山地", "城市", "海洋", "混合"] else 0
        )
    
    st.markdown("---")
    
    # 环境对雷达性能的影响
    st.markdown("### 📡 环境影响分析")
    
    col_env1, col_env2, col_env3 = st.columns(3)
    
    with col_env1:
        # 计算能见度对探测距离的影响
        if visibility < 5:
            vis_impact = 0.7
            vis_color = "red"
        elif visibility < 10:
            vis_impact = 0.85
            vis_color = "orange"
        else:
            vis_impact = 1.0
            vis_color = "green"
        
        create_gauge_chart(
            vis_impact * 100,
            label="能见度影响",
            color=vis_color
        )
    
    with col_env2:
        # 计算降水对信号的影响
        if weather in ["大雨", "雪", "风暴"]:
            precip_impact = 0.6
            precip_color = "red"
        elif weather in ["小雨"]:
            precip_impact = 0.85
            precip_color = "orange"
        else:
            precip_impact = 1.0
            precip_color = "green"
        
        create_gauge_chart(
            precip_impact * 100,
            label="降水影响",
            color=precip_color
        )
    
    with col_env3:
        # 大气衰减
        if humidity > 80:
            atm_impact = 0.8
            atm_color = "orange"
        else:
            atm_impact = 1.0
            atm_color = "green"
        
        create_gauge_chart(
            atm_impact * 100,
            label="大气衰减",
            color=atm_color
        )
    
    # 保存按钮
    if st.button("💾 保存环境设置", type="primary", use_container_width=True):
        st.session_state.simulation_config['environment'] = {
            "weather": weather,
            "visibility_km": visibility,
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "wind_speed_kts": wind_speed,
            "wind_direction_deg": wind_direction,
            "sea_state": ["平静", "轻浪", "中浪", "大浪", "巨浪", "狂浪"].index(sea_state) + 1,
            "terrain_type": terrain_type
        }
        st.success("环境设置已保存")

def show_performance_settings():
    """显示性能设置界面"""
    st.subheader("📈 仿真性能设置")
    
    config = st.session_state.simulation_config.get('performance', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 仿真速度")
        
        sim_speed = st.selectbox(
            "仿真速度模式",
            ["慢速 (高精度)", "标准", "快速", "极速"],
            index={"慢速 (高精度)": 0, "标准": 1, "快速": 2, "极速": 3}.get(
                config.get('simulation_speed', '标准'), 1
            )
        )
        
        # 数据记录
        data_logging = st.checkbox(
            "启用数据记录",
            value=config.get('data_logging', True)
        )
        
        if data_logging:
            log_interval = st.number_input(
                "记录间隔 (秒)",
                0.1, 60.0, config.get('log_interval', 1.0), 0.1
            )
        else:
            log_interval = 1.0
    
    with col2:
        st.markdown("### 资源设置")
        
        max_memory = st.number_input(
            "最大内存使用 (MB)",
            256, 32768, config.get('max_memory_mb', 4096), 256
        )
        
        parallel_processing = st.checkbox(
            "启用并行处理",
            value=config.get('parallel_processing', True)
        )
        
        if parallel_processing:
            import multiprocessing
            max_threads = multiprocessing.cpu_count()
            num_threads = st.slider(
                "并行线程数",
                1, max_threads, min(config.get('num_threads', 4), max_threads), 1
            )
        else:
            num_threads = 1
    
    st.markdown("---")
    
    # 性能预估
    st.markdown("### 📊 性能预估")
    
    # 根据设置估算性能
    performance_factors = {
        "慢速 (高精度)": {"speed": 0.5, "accuracy": 1.0},
        "标准": {"speed": 1.0, "accuracy": 0.9},
        "快速": {"speed": 2.0, "accuracy": 0.7},
        "极速": {"speed": 5.0, "accuracy": 0.5}
    }
    
    perf_factor = performance_factors.get(sim_speed, performance_factors["标准"])
    
    col_perf1, col_perf2, col_perf3 = st.columns(3)
    
    with col_perf1:
        speed_factor = perf_factor["speed"] * (num_threads if parallel_processing else 1)
        create_gauge_chart(
            min(speed_factor * 20, 100),
            label="处理速度",
            color="#1a73e8"
        )
    
    with col_perf2:
        create_gauge_chart(
            perf_factor["accuracy"] * 100,
            label="仿真精度",
            color="#00e676"
        )
    
    with col_perf3:
        memory_efficiency = min(100, max_memory / 8192 * 100)
        create_gauge_chart(
            memory_efficiency,
            label="内存效率",
            color="#ff9800"
        )
    
    # 保存按钮
    if st.button("💾 保存性能设置", type="primary", use_container_width=True):
        st.session_state.simulation_config['performance'] = {
            "simulation_speed": sim_speed,
            "data_logging": data_logging,
            "log_interval": log_interval,
            "max_memory_mb": max_memory,
            "parallel_processing": parallel_processing,
                    "num_threads": num_threads
                }
        st.success("性能设置已保存")

def show_configuration_settings():
    """显示配置设置界面"""
    st.subheader("💾 配置管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📤 配置导出")
        
        # 导出当前配置
        config_name = st.text_input("配置名称", value="仿真配置")
        
        if st.button("💾 保存当前配置", use_container_width=True):
            save_simulation_config(config_name)
        
        # 导出为文件
        if st.button("📥 导出JSON配置", use_container_width=True):
            export_simulation_config()
    
    with col2:
        st.markdown("### 📥 配置导入")
        
        # 导入配置
        uploaded_file = st.file_uploader("上传配置文件", type=['json'])
        
        if uploaded_file is not None:
            if st.button("📤 导入配置", use_container_width=True):
                import_simulation_config(uploaded_file)
    
    st.markdown("---")
    
    # 配置模板
    st.markdown("### 🧩 配置模板")
    
    col_tmpl1, col_tmpl2, col_tmpl3 = st.columns(3)
    
    with col_tmpl1:
        if st.button("快速测试模板", use_container_width=True):
            load_template("quick_test")
    
    with col_tmpl2:
        if st.button("标准仿真模板", use_container_width=True):
            load_template("standard")
    
    with col_tmpl3:
        if st.button("高精度仿真模板", use_container_width=True):
            load_template("high_accuracy")
    
    st.markdown("---")
    
    # 当前配置预览
    st.markdown("### 👁️ 当前配置预览")
    
    with st.expander("查看配置详情", expanded=False):
        st.json(st.session_state.simulation_config)

def save_simulation_config(config_name):
    """保存仿真配置"""
    import json
    from pathlib import Path
    
    config_data = {
        "name": config_name,
        "configuration": st.session_state.simulation_config,
        "save_time": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    config_dir = Path("data/simulation_configs")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    config_file = config_dir / filename
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    st.success(f"配置已保存: {filename}")

def export_simulation_config():
    """导出仿真配置"""
    config_data = {
        "simulation_config": st.session_state.simulation_config,
        "export_time": datetime.now().isoformat()
    }
    
    st.download_button(
        label="📥 下载JSON文件",
        data=json.dumps(config_data, indent=2, ensure_ascii=False),
        file_name=f"sim_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def import_simulation_config(uploaded_file):
    """导入仿真配置"""
    try:
        config_data = json.load(uploaded_file)
        st.session_state.simulation_config = config_data.get('simulation_config', {})
        st.success("配置导入成功")
        st.rerun()
    except Exception as e:
        st.error(f"导入失败: {e}")

def load_template(template_name):
    """加载配置模板"""
    templates = {
        "quick_test": {
            "time_settings": {
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": 30,
                "time_step": 0.1,
                "real_time_factor": 5.0
            },
            "environment": {
                "weather": "晴朗",
                "visibility_km": 20,
                "temperature_c": 15,
                "humidity_percent": 60,
                "wind_speed_kts": 5,
                "wind_direction_deg": 0,
                "sea_state": 1,
                "terrain_type": "平坦"
            },
            "performance": {
                "simulation_speed": "快速",
                "data_logging": True,
                "log_interval": 0.5,
                "max_memory_mb": 1024,
                "parallel_processing": True,
                "num_threads": 2
            }
        },
        "standard": {
            "time_settings": {
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": 300,
                "time_step": 0.1,
                "real_time_factor": 1.0
            },
            "environment": {
                "weather": "晴朗",
                "visibility_km": 20,
                "temperature_c": 15,
                "humidity_percent": 60,
                "wind_speed_kts": 10,
                "wind_direction_deg": 0,
                "sea_state": 1,
                "terrain_type": "平坦"
            },
            "performance": {
                "simulation_speed": "标准",
                "data_logging": True,
                "log_interval": 1.0,
                "max_memory_mb": 4096,
                "parallel_processing": True,
                "num_threads": 4
            }
        },
        "high_accuracy": {
            "time_settings": {
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": 600,
                "time_step": 0.01,
                "real_time_factor": 0.5
            },
            "environment": {
                "weather": "晴朗",
                "visibility_km": 20,
                "temperature_c": 15,
                "humidity_percent": 60,
                "wind_speed_kts": 5,
                "wind_direction_deg": 0,
                "sea_state": 1,
                "terrain_type": "平坦"
            },
            "performance": {
                "simulation_speed": "慢速 (高精度)",
                "data_logging": True,
                "log_interval": 0.1,
                "max_memory_mb": 8192,
                "parallel_processing": True,
                "num_threads": 8
            }
        }
    }
    
    if template_name in templates:
        st.session_state.simulation_config.update(templates[template_name])
        st.success(f"已加载 {template_name} 模板")
        st.rerun()
    else:
        st.error(f"模板 {template_name} 不存在")

if __name__ == "__main__":
    main()