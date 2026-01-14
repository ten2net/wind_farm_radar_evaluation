"""
探测影响分析页面
功能：进行雷达探测影响分析，包括遮挡、衰减、探测概率等
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from math import sqrt, radians, sin, cos, atan2, pi
import random
from scipy import constants

# 页面配置
st.set_page_config(
    page_title="探测影响分析 | 雷达影响评估系统",
    layout="wide"
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

# 标题
st.title("📊 探测影响分析")
st.markdown("进行雷达探测影响分析，包括遮挡、衰减、探测概率等计算")

# 初始化会话状态
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}

# 从会话状态获取配置
def get_config():
    """从会话状态获取配置数据"""
    wind_farm = st.session_state.get('wind_farm_config', {})
    radar = st.session_state.get('radar_config', {})
    targets = st.session_state.get('targets_config', [])
    return wind_farm, radar, targets

# 创建选项卡
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "视线分析", 
    "信号分析", 
    "探测概率", 
    "盲区分析", 
    "综合报告"
])

with tab1:
    st.header("视线（Line of Sight）分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar or not targets:
        st.warning("请先完成风电场、雷达和目标配置，再进行视线分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("分析参数")
            
            # 分析精度设置
            resolution = st.slider(
                "分析精度 (m)",
                min_value=10,
                max_value=200,
                value=50,
                step=10
            )
            
            max_altitude = st.slider(
                "最大分析高度 (m)",
                min_value=100,
                max_value=20000,
                value=5000,
                step=100
            )
            
            # 大气折射模型
            refraction_model = st.selectbox(
                "大气折射模型",
                ["标准大气", "线性梯度", "指数模型", "自定义"]
            )
            
            earth_curvature = st.checkbox(
                "考虑地球曲率",
                value=True
            )
            
            if earth_curvature:
                earth_radius = 6371000  # 地球半径，米
                st.info(f"地球半径: {earth_radius/1000:.0f} km")
        
        with col2:
            st.subheader("风电场信息")
            
            # 显示风电场统计
            num_turbines = wind_farm.get('num_turbines', 0)
            turbine_height = wind_farm.get('turbine_height', 0)
            rotor_diameter = wind_farm.get('rotor_diameter', 0)
            
            st.metric("风机数量", num_turbines)
            st.metric("风机高度", f"{turbine_height} 米")
            st.metric("转子直径", f"{rotor_diameter} 米")
        
        # 开始视线分析
        if st.button("🔍 开始视线分析", type="primary"):
            with st.spinner("正在进行视线分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                total_targets = len(targets)
                visible_targets = random.randint(0, total_targets)
                occluded_targets = total_targets - visible_targets
                
                # 计算平均遮挡率
                avg_occlusion = random.uniform(0, 100)
                
                # 计算最大遮挡距离
                max_occlusion_distance = random.uniform(1000, 10000)
                
                # 保存结果
                st.session_state.analysis_results['los'] = {
                    'visible_targets': visible_targets,
                    'occluded_targets': occluded_targets,
                    'avg_occlusion': avg_occlusion,
                    'max_occlusion_distance': max_occlusion_distance
                }
                
                st.success("视线分析完成！")
        
        # 显示分析结果
        if 'los' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['los']
            
            st.subheader("视线分析结果")
            
            col3, col4, col5, col6 = st.columns(4)
            
            with col3:
                st.metric("可见目标数", results['visible_targets'])
            
            with col4:
                st.metric("被遮挡目标数", results['occluded_targets'])
            
            with col5:
                st.metric("平均遮挡率", f"{results['avg_occlusion']:.1f}%")
            
            with col6:
                st.metric("最大遮挡距离", f"{results['max_occlusion_distance']:.0f} 米")
            
            # 遮挡统计图表
            st.subheader("遮挡统计")
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=['可见目标', '被遮挡目标'],
                    values=[results['visible_targets'], results['occluded_targets']],
                    hole=0.3
                )
            ])
            
            fig.update_layout(
                title="目标视线状态分布",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 生成视线分析图
            st.subheader("视线分析图")
            
            # 创建示例数据
            x_range = np.linspace(-5000, 5000, 100)
            y_range = np.linspace(-5000, 5000, 100)
            X, Y = np.meshgrid(x_range, y_range)
            
            # 模拟遮挡区域
            Z = np.zeros_like(X)
            for i in range(3):
                center_x = random.uniform(-3000, 3000)
                center_y = random.uniform(-3000, 3000)
                radius = random.uniform(500, 2000)
                distance = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
                Z += np.exp(-distance**2 / (2*radius**2))
            
            fig = go.Figure(data=[
                go.Contour(
                    z=Z,
                    x=x_range,
                    y=y_range,
                    colorscale='RdYlBu_r',
                    contours=dict(
                        coloring='heatmap',
                        showlabels=True,
                    ),
                    colorbar=dict(title="遮挡强度")
                )
            ])
            
            # 添加雷达位置
            radar_pos = radar.get('position', [0, 0, 50])
            fig.add_trace(go.Scatter(
                x=[radar_pos[0]],
                y=[radar_pos[1]],
                mode='markers',
                marker=dict(size=15, color='red', symbol='star'),
                name='雷达'
            ))
            
            fig.update_layout(
                title="风电场遮挡区域分析（俯视图）",
                xaxis_title="X 坐标 (米)",
                yaxis_title="Y 坐标 (米)",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab2:
    st.header("信号衰减分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar or not targets:
        st.warning("请先完成风电场、雷达和目标配置，再进行信号分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("信号参数")
            
            # 信号频段
            freq = radar.get('frequency', 3e9)
            wavelength = constants.c / freq
            
            st.metric("雷达频率", f"{freq/1e9:.2f} GHz")
            st.metric("波长", f"{wavelength*100:.2f} cm")
            
            # 传播模型
            propagation_model = st.selectbox(
                "传播模型",
                ["自由空间", "双线模型", "刀锋衍射", "多径模型", "自定义"]
            )
            
            # 天气影响
            weather = st.selectbox(
                "天气条件",
                ["晴朗", "多云", "小雨", "中雨", "大雨", "雾", "雪"]
            )
            
            # 天气衰减系数
            weather_attenuation = {
                '晴朗': 0.0,
                '多云': 0.01,
                '小雨': 0.05,
                '中雨': 0.2,
                '大雨': 0.5,
                '雾': 0.1,
                '雪': 0.3
            }
            
            attenuation_factor = weather_attenuation.get(weather, 0.0)
            st.metric(f"{weather}衰减", f"{attenuation_factor*100:.1f}%")
        
        with col2:
            st.subheader("衰减计算")
            
            # 输入距离进行计算
            distance = st.slider(
                "计算距离 (km)",
                min_value=1,
                max_value=500,
                value=10,
                step=1
            )
            
            # 计算自由空间损耗
            fspl = 20 * np.log10(distance * 1000) + 20 * np.log10(freq) - 147.55
            
            # 计算天气衰减
            weather_loss = attenuation_factor * distance
            
            # 计算总衰减
            total_loss = fspl + weather_loss
            
            st.metric("自由空间损耗", f"{fspl:.1f} dB")
            st.metric("天气衰减", f"{weather_loss:.1f} dB")
            st.metric("总衰减", f"{total_loss:.1f} dB")
        
        # 开始信号分析
        if st.button("📡 开始信号分析", type="primary"):
            with st.spinner("正在进行信号分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                max_attenuation = random.uniform(10, 50)
                avg_attenuation = random.uniform(5, 30)
                signal_quality = random.uniform(0, 100)
                
                # 保存结果
                st.session_state.analysis_results['signal'] = {
                    'max_attenuation': max_attenuation,
                    'avg_attenuation': avg_attenuation,
                    'signal_quality': signal_quality
                }
                
                st.success("信号分析完成！")
        
        # 显示分析结果
        if 'signal' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['signal']
            
            st.subheader("信号分析结果")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.metric("最大衰减", f"{results['max_attenuation']:.1f} dB")
            
            with col4:
                st.metric("平均衰减", f"{results['avg_attenuation']:.1f} dB")
            
            with col5:
                st.metric("信号质量", f"{results['signal_quality']:.1f}%")
            
            # 信号衰减曲线
            st.subheader("信号衰减曲线")
            
            distances = np.linspace(1, 100, 100)  # 1-100 km
            freqs = [1e9, 3e9, 6e9, 10e9]  # 不同频率
            
            fig = go.Figure()
            
            for freq_val in freqs:
                # 计算自由空间损耗
                fspl_curve = 20 * np.log10(distances * 1000) + 20 * np.log10(freq_val) - 147.55
                
                # 添加随机波动模拟实际环境
                fspl_curve += np.random.randn(len(distances)) * 2
                
                fig.add_trace(go.Scatter(
                    x=distances,
                    y=fspl_curve,
                    mode='lines',
                    name=f'{freq_val/1e9:.1f} GHz',
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="自由空间损耗 vs 距离（不同频率）",
                xaxis_title="距离 (km)",
                yaxis_title="损耗 (dB)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 信号强度热力图
            st.subheader("信号强度分布")
            
            # 创建示例数据
            x = np.linspace(-5000, 5000, 50)
            y = np.linspace(-5000, 5000, 50)
            X, Y = np.meshgrid(x, y)
            
            # 计算距离雷达的距离
            radar_x, radar_y, _ = radar.get('position', [0, 0, 50])
            distances_grid = np.sqrt((X - radar_x)**2 + (Y - radar_y)**2)
            
            # 计算信号强度
            signal_strength = 100 - 20 * np.log10(distances_grid/1000 + 1)
            
            # 添加风机遮挡效果
            for _ in range(num_turbines):
                tx = random.uniform(-3000, 3000)
                ty = random.uniform(-3000, 3000)
                turbine_dist = np.sqrt((X - tx)**2 + (Y - ty)**2)
                signal_strength -= 20 * np.exp(-turbine_dist**2 / (500**2))
            
            fig = go.Figure(data=[
                go.Heatmap(
                    z=signal_strength,
                    x=x,
                    y=y,
                    colorscale='Viridis',
                    zmin=0,
                    zmax=100
                )
            ])
            
            fig.update_layout(
                title="信号强度分布（考虑风机遮挡）",
                xaxis_title="X 坐标 (米)",
                yaxis_title="Y 坐标 (米)",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab3:
    st.header("探测概率分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar or not targets:
        st.warning("请先完成风电场、雷达和目标配置，再进行探测概率分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("探测参数")
            
            # 雷达参数
            peak_power = radar.get('peak_power', 1e6)
            antenna_gain = radar.get('antenna_gain', 40)
            wavelength = radar.get('wavelength', 0.1)
            
            st.metric("峰值功率", f"{peak_power/1e6:.1f} MW")
            st.metric("天线增益", f"{antenna_gain} dB")
            st.metric("波长", f"{wavelength*100:.2f} cm")
            
            # 检测门限
            detection_threshold = st.slider(
                "检测门限 (dB)",
                min_value=0,
                max_value=30,
                value=13,
                step=1
            )
            
            false_alarm_prob = st.select_slider(
                "虚警概率",
                options=['1e-12', '1e-10', '1e-8', '1e-6', '1e-4', '1e-2'],
                value='1e-6'
            )
            
            integration_type = st.selectbox(
                "积累类型",
                ["相参积累", "非相参积累", "二进制积累", "累积检测"]
            )
        
        with col2:
            st.subheader("目标参数")
            
            if targets:
                # 显示目标信息
                target_df = pd.DataFrame(targets)
                # 确保列存在
                display_cols = []
                for col in ['id', 'name', 'type', 'rcs']:
                    if col in target_df.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        target_df[display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("目标数据格式异常")
            else:
                st.info("无目标配置")
            
            # 计算示例
            example_distance = st.slider(
                "示例距离 (km)",
                min_value=1,
                max_value=500,
                value=10,
                step=1
            )
            
            example_rcs = st.slider(
                "示例RCS (m²)",
                min_value=0.01,
                max_value=100.0,
                value=1.0,
                step=0.1
            )
            
            # 计算信噪比
            snr = (peak_power * antenna_gain**2 * wavelength**2 * example_rcs) / \
                  ((4*np.pi)**3 * (example_distance*1000)**4)
            snr_db = 10 * np.log10(snr) if snr > 0 else -np.inf
            
            st.metric("示例信噪比", f"{snr_db:.1f} dB")
            
            if snr_db >= detection_threshold:
                st.success("目标可探测")
            else:
                st.error("目标不可探测")
        
        # 开始探测概率分析
        if st.button("🎯 开始探测概率分析", type="primary"):
            with st.spinner("正在进行探测概率分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                avg_detection_prob = random.uniform(0, 100)
                max_detection_range = random.uniform(10, 500)
                min_detectable_rcs = random.uniform(0.01, 10)
                
                # 保存结果
                st.session_state.analysis_results['detection'] = {
                    'avg_detection_prob': avg_detection_prob,
                    'max_detection_range': max_detection_range,
                    'min_detectable_rcs': min_detectable_rcs
                }
                
                st.success("探测概率分析完成！")
        
        # 显示分析结果
        if 'detection' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['detection']
            
            st.subheader("探测概率分析结果")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.metric("平均探测概率", f"{results['avg_detection_prob']:.1f}%")
            
            with col4:
                st.metric("最大探测距离", f"{results['max_detection_range']:.0f} km")
            
            with col5:
                st.metric("最小可探测RCS", f"{results['min_detectable_rcs']:.3f} m²")
            
            # 探测概率曲线
            st.subheader("探测概率 vs 距离")
            
            ranges = np.linspace(1, 200, 100)
            
            # 计算探测概率
            rcs_values = [0.01, 0.1, 1.0, 10.0]
            
            fig = go.Figure()
            
            for rcs in rcs_values:
                # 计算信噪比
                snr_values = (peak_power * antenna_gain**2 * wavelength**2 * rcs) / \
                            ((4*np.pi)**3 * (ranges*1000)**4)
                snr_db_values = 10 * np.log10(snr_values)
                
                # 计算探测概率（简化模型）
                detection_probs = 1 / (1 + np.exp(-(snr_db_values - detection_threshold)/3))
                
                fig.add_trace(go.Scatter(
                    x=ranges,
                    y=detection_probs*100,
                    mode='lines',
                    name=f'RCS={rcs} m²',
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="探测概率 vs 距离（不同RCS）",
                xaxis_title="距离 (km)",
                yaxis_title="探测概率 (%)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 雷达威力图
            st.subheader("雷达威力图")
            
            # 创建极坐标图
            angles = np.linspace(0, 2*np.pi, 360)
            
            fig = go.Figure()
            
            # 获取遮挡率（如果已进行视线分析）
            avg_occlusion = 0
            if 'los' in st.session_state.analysis_results:
                avg_occlusion = st.session_state.analysis_results['los'].get('avg_occlusion', 0)
            
            for rcs in rcs_values:
                # 计算最大探测距离
                max_range = ((peak_power * antenna_gain**2 * wavelength**2 * rcs) / 
                           ((4*np.pi)**3 * 10**(detection_threshold/10)))**(1/4) / 1000
                
                # 添加风电场影响
                max_range *= (1 - avg_occlusion/100)
                
                fig.add_trace(go.Scatterpolar(
                    r=[max_range] * len(angles),
                    theta=np.degrees(angles),
                    mode='lines',
                    name=f'RCS={rcs} m²',
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        title=dict(text="距离 (km)"),
                        range=[0, 200]
                    )
                ),
                title="雷达威力图（考虑风电场影响）",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab4:
    st.header("盲区分析")
    
    # 获取配置
    wind_farm, radar, targets = get_config()
    
    if not wind_farm or not radar:
        st.warning("请先完成风电场和雷达配置，再进行盲区分析")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("盲区参数")
            
            # 分析参数
            altitude_levels = st.slider(
                "分析高度层 (m)",
                min_value=0,
                max_value=20000,
                value=(1000, 5000),
                step=100
            )
            
            azimuth_sectors = st.slider(
                "方位扇区数",
                min_value=4,
                max_value=36,
                value=12,
                step=4
            )
            
            # 使用多选但确保至少有一个默认值
            elevation_options = [0, 5, 10, 15, 20, 30, 45, 60, 90]
            elevation_angles = st.multiselect(
                "分析俯仰角 (°)",
                elevation_options,
                default=[0, 5, 10, 30]
            )
            
            # 如果没有选择任何俯仰角，使用默认值
            if not elevation_angles:
                elevation_angles = [0, 5, 10, 30]
        
        with col2:
            st.subheader("盲区统计")
            
            # 显示风机信息
            num_turbines = wind_farm.get('num_turbines', 0)
            turbine_height = wind_farm.get('turbine_height', 0)
            rotor_diameter = wind_farm.get('rotor_diameter', 0)
            
            st.metric("风机总数", num_turbines)
            st.metric("风机平均高度", f"{turbine_height} 米")
            st.metric("转子平均直径", f"{rotor_diameter} 米")
            
            # 预计盲区比例
            estimated_shadow = min(0.5, num_turbines * 0.05)
            st.metric("预计盲区比例", f"{estimated_shadow*100:.1f}%")
        
        # 开始盲区分析
        if st.button("🌫️ 开始盲区分析", type="primary"):
            with st.spinner("正在进行盲区分析..."):
                import time
                
                # 模拟计算过程
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # 模拟分析结果
                shadow_area = random.uniform(0, 50)
                max_shadow_angle = random.uniform(0, 180)
                avg_shadow_depth = random.uniform(10, 50)
                
                # 保存结果
                st.session_state.analysis_results['shadow'] = {
                    'shadow_area': shadow_area,
                    'max_shadow_angle': max_shadow_angle,
                    'avg_shadow_depth': avg_shadow_depth
                }
                
                st.success("盲区分析完成！")
        
        # 显示分析结果
        if 'shadow' in st.session_state.analysis_results:
            results = st.session_state.analysis_results['shadow']
            
            st.subheader("盲区分析结果")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.metric("盲区面积比例", f"{results['shadow_area']:.1f}%")
            
            with col4:
                st.metric("最大盲区角度", f"{results['max_shadow_angle']:.1f}°")
            
            with col5:
                st.metric("平均盲区深度", f"{results['avg_shadow_depth']:.1f} dB")
            
            # 盲区分布图
            st.subheader("盲区分布图")
            
            # 创建方位-俯仰图
            azimuth = np.linspace(0, 360, azimuth_sectors)
            elevation = np.array(elevation_angles)
            
            # 确保至少有数据
            if len(elevation) == 0:
                elevation = np.array([0, 5, 10, 30])
            
            Az, El = np.meshgrid(azimuth, elevation)
            
            # 模拟盲区数据
            shadow_map = np.zeros_like(Az)
            
            for i in range(len(elevation)):
                for j in range(len(azimuth)):
                    # 创建盲区模式
                    base_shadow = 0.3
                    
                    # 添加风机遮挡效应
                    for k in range(num_turbines):
                        angle_offset = 360 * k / num_turbines
                        shadow_strength = np.exp(-((azimuth[j] - angle_offset)**2) / (30**2))
                        shadow_map[i, j] += shadow_strength * 0.2
                    
                    shadow_map[i, j] = min(base_shadow + shadow_map[i, j], 1.0)
            
            fig = go.Figure(data=[
                go.Contour(
                    z=shadow_map,
                    x=azimuth,
                    y=elevation,
                    colorscale='RdYlBu_r',
                    contours=dict(
                        coloring='heatmap',
                        showlabels=True,
                    ),
                    colorbar=dict(title="盲区强度")
                )
            ])
            
            fig.update_layout(
                title="盲区分布（方位-俯仰）",
                xaxis_title="方位角 (°)",
                yaxis_title="俯仰角 (°)",
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 三维盲区可视化
            st.subheader("三维盲区可视化")
            
            # 创建球坐标
            theta = np.radians(azimuth)
            phi = np.radians(90 - np.array(elevation))  # 转换为天顶角
            
            Theta, Phi = np.meshgrid(theta, phi)
            
            # 修复：确保R_full的形状与Theta、Phi一致
            R = 1 - shadow_map.mean(axis=0)  # 半径表示盲区深度
            # 使用np.tile确保形状匹配
            R_full = np.tile(R, (len(elevation), 1))
            
            # 计算坐标
            X = R_full * np.sin(Phi) * np.cos(Theta)
            Y = R_full * np.sin(Phi) * np.sin(Theta)
            Z = R_full * np.cos(Phi)
            
            # 创建3D曲面
            fig = go.Figure(data=[
                go.Surface(
                    x=X, y=Y, z=Z,
                    surfacecolor=shadow_map,
                    colorscale='RdYlBu_r',
                    colorbar=dict(title="盲区强度"),
                    opacity=0.8
                )
            ])
            
            fig.update_layout(
                title="三维盲区可视化",
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z",
                    aspectmode="auto"
                ),
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')

with tab5:
    st.header("综合评估报告")
    
    # 获取所有分析结果
    all_results = st.session_state.analysis_results
    
    if not all_results:
        st.warning("请先完成各项分析，再生成综合报告")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("分析结果汇总")
            
            # 创建汇总表
            summary_data = []
            
            if 'los' in all_results:
                # 确保所有值都是字符串类型
                summary_data.append(['视线分析', '平均遮挡率', f"{all_results['los']['avg_occlusion']:.1f}%"])
                summary_data.append(['视线分析', '被遮挡目标数', str(all_results['los']['occluded_targets'])])
            
            if 'signal' in all_results:
                summary_data.append(['信号分析', '最大衰减', f"{all_results['signal']['max_attenuation']:.1f} dB"])
                summary_data.append(['信号分析', '信号质量', f"{all_results['signal']['signal_quality']:.1f}%"])
            
            if 'detection' in all_results:
                summary_data.append(['探测分析', '平均探测概率', f"{all_results['detection']['avg_detection_prob']:.1f}%"])
                summary_data.append(['探测分析', '最大探测距离', f"{all_results['detection']['max_detection_range']:.0f} km"])
            
            if 'shadow' in all_results:
                summary_data.append(['盲区分析', '盲区面积比例', f"{all_results['shadow']['shadow_area']:.1f}%"])
                summary_data.append(['盲区分析', '平均盲区深度', f"{all_results['shadow']['avg_shadow_depth']:.1f} dB"])
            
            # 创建DataFrame，确保所有值都是字符串
            summary_df = pd.DataFrame(summary_data, columns=['分析类型', '指标', '数值'])
            
            # 将数值列转换为字符串
            summary_df['数值'] = summary_df['数值'].astype(str)
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("风险评估")
            
            # 计算综合风险评分
            risk_factors = []
            
            if 'los' in all_results:
                occlusion_risk = min(100, all_results['los']['avg_occlusion'] * 2)
                risk_factors.append(occlusion_risk)
            
            if 'signal' in all_results:
                signal_risk = 100 - all_results['signal']['signal_quality']
                risk_factors.append(signal_risk)
            
            if 'detection' in all_results:
                detection_risk = 100 - all_results['detection']['avg_detection_prob']
                risk_factors.append(detection_risk)
            
            if 'shadow' in all_results:
                shadow_risk = all_results['shadow']['shadow_area'] * 2
                risk_factors.append(shadow_risk)
            
            if risk_factors:
                overall_risk = np.mean(risk_factors)
                
                st.metric("综合风险评分", f"{overall_risk:.1f}/100")
                
                # 风险等级
                if overall_risk < 20:
                    st.success("✅ 风险等级：低")
                    st.info("风电场对雷达探测影响较小")
                elif overall_risk < 50:
                    st.warning("⚠️ 风险等级：中")
                    st.info("风电场对雷达探测有一定影响")
                elif overall_risk < 80:
                    st.error("❌ 风险等级：高")
                    st.info("风电场对雷达探测有显著影响")
                else:
                    st.error("🚨 风险等级：严重")
                    st.info("风电场严重影响雷达探测性能")
        
        # 生成报告
        st.subheader("评估报告生成")
        
        report_type = st.selectbox(
            "报告格式",
            ["简要报告", "详细报告", "技术报告", "管理报告"]
        )
        
        if st.button("📄 生成评估报告", type="primary"):
            with st.spinner("正在生成评估报告..."):
                import time
                time.sleep(2)
                
                # 计算综合风险评分
                overall_risk = 0
                if risk_factors:
                    overall_risk = np.mean(risk_factors)
                
                # 模拟报告生成
                report_content = f"""
# 风电场对雷达探测影响评估报告

## 1. 执行摘要

本报告对风电场对雷达探测目标的影响进行了综合评估。主要发现如下：

- 视线遮挡率: {all_results.get('los', {}).get('avg_occlusion', 0):.1f}%
- 平均探测概率: {all_results.get('detection', {}).get('avg_detection_prob', 0):.1f}%
- 盲区面积比例: {all_results.get('shadow', {}).get('shadow_area', 0):.1f}%
- 综合风险评分: {overall_risk:.1f}/100

## 2. 主要结论

根据分析结果，风电场对雷达探测性能的影响程度为{"低" if overall_risk < 20 else "中" if overall_risk < 50 else "高" if overall_risk < 80 else "严重"}。

## 3. 建议措施

1. 优化风机布局，减少视线遮挡
2. 调整雷达参数，提高探测性能
3. 考虑多雷达协同探测方案
4. 定期进行影响评估和优化

报告生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
                
                st.success("评估报告生成完成！")
                
                # 显示报告
                st.text_area("报告内容", report_content, height=300)
                
                # 下载报告
                st.download_button(
                    label="📥 下载报告 (TXT)",
                    data=report_content,
                    file_name="windfarm_radar_assessment_report.txt",
                    mime="text/plain"
                )
        
        # 优化建议
        st.subheader("优化建议")
        
        # 重新计算综合风险评分
        if all_results:
            risk_factors = []
            
            if 'los' in all_results:
                occlusion_risk = min(100, all_results['los']['avg_occlusion'] * 2)
                risk_factors.append(occlusion_risk)
            
            if 'signal' in all_results:
                signal_risk = 100 - all_results['signal']['signal_quality']
                risk_factors.append(signal_risk)
            
            if 'detection' in all_results:
                detection_risk = 100 - all_results['detection']['avg_detection_prob']
                risk_factors.append(detection_risk)
            
            if 'shadow' in all_results:
                shadow_risk = all_results['shadow']['shadow_area'] * 2
                risk_factors.append(shadow_risk)
            
            if risk_factors:
                overall_risk = np.mean(risk_factors)
            
                if overall_risk < 20:
                    st.info("""
                    **优化建议：**
                    1. 当前配置良好，可保持现状
                    2. 定期监测雷达性能变化
                    3. 建立长期影响评估机制
                    """)
                elif overall_risk < 50:
                    st.warning("""
                    **优化建议：**
                    1. 考虑调整部分风机位置
                    2. 优化雷达扫描策略
                    3. 增加雷达功率或灵敏度
                    4. 定期进行性能校准
                    """)
                elif overall_risk < 80:
                    st.error("""
                    **优化建议：**
                    1. 重新设计风电场布局
                    2. 升级雷达系统性能
                    3. 考虑部署辅助雷达
                    4. 建立动态遮挡补偿机制
                    5. 制定应急预案
                    """)
                else:
                    st.error("""
                    **紧急优化建议：**
                    1. 立即重新评估风电场选址
                    2. 升级或更换雷达系统
                    3. 部署多部雷达协同工作
                    4. 建立实时监控和预警系统
                    5. 制定详细的风险缓解计划
                    """)

# 侧边栏
with st.sidebar:
    st.markdown("## 🎯 操作指南")
    st.markdown("""
    1. **视线分析**: 分析风机对目标的视线遮挡
    2. **信号分析**: 分析信号传播和衰减
    3. **探测概率**: 计算目标探测概率
    4. **盲区分析**: 分析雷达探测盲区
    5. **综合报告**: 生成评估报告和建议
    
    **分析步骤:**
    1. 在每个选项卡中设置参数
    2. 点击"开始分析"按钮
    3. 查看分析结果和图表
    4. 生成综合评估报告
    """)
    
    st.markdown("---")
    
    # 分析状态
    st.markdown("## 📈 分析状态")
    
    analysis_types = ['视线分析', '信号分析', '探测概率', '盲区分析']
    completed_analyses = [atype for atype in analysis_types 
                         if atype[:2] in [key[:2] for key in st.session_state.analysis_results.keys()]]
    
    for atype in analysis_types:
        if atype in completed_analyses:
            st.success(f"✅ {atype}")
        else:
            st.warning(f"⏳ {atype}")
    
    st.markdown("---")
    
    if st.button("🚀 进入下一步: 三维可视化", type="primary", width='stretch'):
        st.switch_page("pages/5_👁️ 三维可视化.py")

# 页脚
st.markdown("---")
st.caption("探测影响分析模块 | 风电场对雷达探测影响的综合评估")