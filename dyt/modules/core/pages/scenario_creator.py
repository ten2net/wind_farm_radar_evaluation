import streamlit as st
from datetime import datetime
import sys
import os
import json

# 添加父目录到路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("=======================")

st.set_page_config(
    page_title="场景创建器",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 场景创建器")

# 初始化会话状态
if 'scenario_created' not in st.session_state:
    st.session_state.scenario_created = False
if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = None

# 返回按钮
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("← 返回主页面", width='stretch'):
        # 注意：需要确保main_application_module.py存在
        st.switch_page("main_application_module.py")

st.markdown("""
使用此工具创建自定义的作战场景。设置导弹位置、目标参数和干扰条件。
""")

# 场景创建表单
with st.form("scenario_creation_form", clear_on_submit=False):
    st.subheader("场景基本信息")
    
    scenario_name = st.text_input("场景名称", "新场景_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    scenario_desc = st.text_area("场景描述", "描述此场景的作战环境和目标")
    
    st.subheader("导引头配置")
    guidance_type = st.selectbox(
        "导引头类型",
        ["被动雷达", "主动雷达", "复合制导"]
    )
    
    st.info(f"**{guidance_type}特点:** " + {
        "被动雷达": "隐蔽性好，依赖目标辐射信号",
        "主动雷达": "自主探测，但容易暴露",
        "复合制导": "结合被动和主动优势，适应性更强"
    }[guidance_type])
    
    st.subheader("战场配置")
    
    tab1, tab2, tab3 = st.tabs(["导弹位置", "目标设置", "干扰设置"])
    
    with tab1:
        st.markdown("### 🚀 导弹初始位置")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            missile_lat = st.number_input("导弹纬度", 30.0, 40.0, 35.0, 0.1)
        with col2:
            missile_lon = st.number_input("导弹经度", 110.0, 120.0, 115.0, 0.1)
        with col3:
            missile_alt = st.number_input("导弹海拔(m)", 0, 20000, 5000, 100)
        
        weather = st.selectbox("天气条件", ['clear', 'cloudy', 'rain', 'fog', 'storm'])
        
        st.markdown(f"""
        **位置信息:**
        - 纬度: {missile_lat}°
        - 经度: {missile_lon}°
        - 海拔: {missile_alt} 米
        - 天气: {weather}
        """)
    
    with tab2:
        st.markdown("### 🎯 目标配置")
        target_type = st.selectbox(
            "目标类型",
            ["fighter", "bomber", "awacs", "warship", "radar_station"],
            format_func=lambda x: {
                "fighter": "战斗机",
                "bomber": "轰炸机", 
                "awacs": "预警机",
                "warship": "军舰",
                "radar_station": "雷达站"
            }[x]
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            target_lat = st.number_input("目标纬度", 30.0, 40.0, 36.0, 0.1)
            target_lon = st.number_input("目标经度", 110.0, 120.0, 117.0, 0.1)
            
        with col2:
            target_alt = st.number_input("目标海拔(m)", 0, 20000, 8000, 100)
            emission_power = st.slider("辐射功率", 0.0, 1.0, 0.8, 0.1)
            
        with col3:
            rcs = st.number_input("RCS (雷达截面积)", 1.0, 1000.0, 50.0, 10.0)
            velocity = st.number_input("目标速度(m/s)", 0, 1000, 250, 10)
        
        st.info(f"**目标类型:** {target_type} | **RCS:** {rcs}m² | **辐射功率:** {emission_power}")
    
    with tab3:
        st.markdown("### ⚡ 干扰配置")
        jamming_type = st.selectbox(
            "干扰类型",
            ["none", "noise", "deception", "smart_noise"],
            format_func=lambda x: {
                "none": "无干扰",
                "noise": "噪声压制干扰",
                "deception": "欺骗式干扰", 
                "smart_noise": "灵巧噪声干扰"
            }[x]
        )
        
        if jamming_type != "none":
            col1, col2 = st.columns(2)
            with col1:
                jammer_lat = st.number_input("干扰源纬度", 30.0, 40.0, 36.5, 0.1)
                jammer_lon = st.number_input("干扰源经度", 110.0, 120.0, 116.5, 0.1)
                
            with col2:
                jammer_power = st.slider("干扰功率", 0.0, 1.0, 0.5, 0.1)
                jammer_range = st.number_input("干扰范围(km)", 10, 200, 100, 10)
        else:
            st.info("当前场景无电子干扰")
    
    # 场景预览
    st.subheader("👁️ 场景预览")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        **导弹配置:**
        - 类型: {guidance_type}
        - 位置: ({missile_lat}, {missile_lon})
        - 海拔: {missile_alt}米
        - 天气: {weather}
        """)
    
    with col2:
        st.markdown(f"""
        **目标配置:**
        - 类型: {target_type}
        - 位置: ({target_lat}, {target_lon})
        - 海拔: {target_alt}米
        - RCS: {rcs}m²
        - 干扰: {jamming_type}
        """)
    
    # 提交按钮 - 使用form_submit_button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_button = st.form_submit_button(
            "🚀 创建场景并开始仿真", 
            width='stretch',
            type="primary"
        )

# 表单提交后的处理逻辑（放在表单外部）
if submit_button:
    # 创建场景配置
    scenario_config = {
        'name': scenario_name,
        'description': scenario_desc,
        'battlefield': {
            'missile_position': {
                'lat': missile_lat,
                'lon': missile_lon,
                'alt': missile_alt
            },
            'targets': [{
                'target_id': 'main_target',
                'type': target_type,
                'position': {
                    'lat': target_lat,
                    'lon': target_lon,
                    'alt': target_alt
                },
                'emission_power': emission_power,
                'rcs': rcs,
                'velocity': velocity
            }],
            'jammers': [] if jamming_type == 'none' else [{
                'jammer_id': 'main_jammer',
                'position': {
                    'lat': jammer_lat if jamming_type != 'none' else 0,
                    'lon': jammer_lon if jamming_type != 'none' else 0,
                    'alt': 0
                },
                'type': jamming_type,
                'power': jammer_power if jamming_type != 'none' else 0,
                'range': jammer_range if jamming_type != 'none' else 0
            }],
            'weather': weather
        },
        'guidance_system': guidance_type
    }
    
    # 保存到会话状态
    st.session_state.current_scenario = scenario_config
    st.session_state.scenario_created = True
    
    st.success(f"✅ 场景 '{scenario_name}' 创建成功！")
    st.balloons()

# 显示下一步操作（放在表单外部）
if st.session_state.scenario_created and st.session_state.current_scenario:
    st.markdown("---")
    st.subheader("🎯 下一步操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ 立即开始仿真", width='stretch'):
            # 切换到主应用程序页面
            st.switch_page("main_application_module.py")
    
    with col2:
        if st.button("💾 保存场景配置", width='stretch'):
            # 保存场景到文件
            try:
                filename = f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.current_scenario, f, indent=2, ensure_ascii=False)
                st.success(f"场景已保存到: {filename}")
            except Exception as e:
                st.error(f"保存失败: {e}")
    
    with col3:
        if st.button("🔄 创建新场景", width='stretch'):
            # 重置状态，允许创建新场景
            st.session_state.scenario_created = False
            st.session_state.current_scenario = None
            st.rerun()
    
    # 显示当前场景详情
    st.markdown("---")
    st.subheader("📋 当前场景详情")
    st.json(st.session_state.current_scenario)

# 如果没有创建场景，显示使用说明
if not st.session_state.scenario_created:
    st.markdown("---")
    st.info("""
    **使用说明:**
    1. 填写场景基本信息
    2. 配置导引头类型
    3. 设置战场参数（导弹位置、目标设置、干扰配置）
    4. 点击"创建场景并开始仿真"按钮
    5. 选择下一步操作
    """)