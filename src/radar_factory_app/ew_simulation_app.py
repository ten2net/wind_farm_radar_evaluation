# ew_simulation_app.py
import yaml
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import pandas as pd

class EWSimulation:
    """电子战仿真应用"""
    
    def __init__(self, simulation_file: str = None):
        self.simulation_file = simulation_file
        self.scenario = None
        self.radar_stations = {}
        self.results = {}
        
    def load_simulation(self, simulation_file: str) -> bool:
        """加载仿真配置文件"""
        try:
            with open(simulation_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.scenario = config.get('simulation', {})
            self.radar_stations = config.get('radar_stations', {})
            self.engagement_rules = config.get('engagement_rules', {})
            return True
        except Exception as e:
            st.error(f"加载仿真文件失败: {e}")
            return False
    
    def calculate_detection_probability(self, radar_id: str, target_rcs: float, 
                                       range_km: float, jammer_power: float = 0) -> float:
        """计算检测概率"""
        station = self.radar_stations.get(radar_id, {})
        radar_params = station.get('雷达参数', {})
        transmitter = radar_params.get('发射机', {})
        antenna = radar_params.get('天线', {})
        
        # 简化雷达方程
        freq_hz = transmitter.get('载波频率_Hz', 1e9)
        wavelength = 3e8 / freq_hz
        peak_power = transmitter.get('峰值功率_W', 1e6)
        antenna_gain = 10**(antenna.get('增益_dB', 30) / 10)
        system_loss = 10**(station.get('雷达参数', {}).get('接收机', {}).get('系统损耗_dB', 5) / 10)
        
        # 雷达方程
        range_m = range_km * 1000
        snr = (peak_power * antenna_gain**2 * wavelength**2 * target_rcs) / \
              ((4 * np.pi)**3 * range_m**4 * 1.38e-23 * 290 * 1e6 * system_loss)
        
        # 考虑干扰
        if jammer_power > 0:
            snr = snr / (10**(jammer_power / 10))
        
        # 转换为检测概率
        if snr > 20:
            return 0.95
        elif snr > 10:
            return 0.7
        elif snr > 0:
            return 0.3
        else:
            return 0.1
    
    def simulate_scenario(self):
        """执行仿真"""
        if not self.scenario:
            return None
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'scenario': self.scenario,
            'engagements': []
        }
        
        # 这里可以实现具体的对抗逻辑
        return results

def main():
    """电子战仿真主应用"""
    st.set_page_config(
        page_title="长城电子战仿真系统",
        page_icon="⚔️",
        layout="wide"
    )
    
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">长城电子战仿真系统</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #94a3b8;">雷达对抗、电子干扰、体系仿真平台</p>', unsafe_allow_html=True)
    
    # 创建仿真器
    simulator = EWSimulation()
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### ⚙️ 仿真设置")
        
        # 加载仿真文件
        uploaded_file = st.file_uploader("上传仿真配置文件", type=['yaml', 'yml'])
        if uploaded_file is not None:
            with open("temp_simulation.yaml", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if simulator.load_simulation("temp_simulation.yaml"):
                st.success("✅ 仿真文件加载成功!")
        
        # 或者从数据库加载
        st.markdown("---")
        st.markdown("### 📡 从数据库加载")
        
        # 这里可以添加数据库连接和选择想定的代码
        
        st.markdown("---")
        st.markdown("### 🎯 仿真参数")
        
        target_rcs = st.slider("目标RCS (m²)", 0.1, 100.0, 5.0)
        range_km = st.slider("目标距离 (km)", 1, 1000, 100)
        jammer_power = st.slider("干扰功率 (dB)", 0, 80, 0)
    
    # 主界面
    if simulator.scenario:
        st.markdown(f"### 📋 仿真场景: {simulator.scenario.get('scenario_name')}")
        
        col_time, col_duration, col_status = st.columns(3)
        with col_time:
            st.metric("仿真时间", simulator.scenario.get('simulation_time', '-'))
        with col_duration:
            st.metric("持续时间", f"{simulator.scenario.get('duration_min', 0)}分钟")
        with col_status:
            st.metric("状态", "就绪")
        
        # 雷达态势显示
        st.markdown("### 📡 参与雷达")
        
        radar_list = list(simulator.radar_stations.keys())
        for radar_id in radar_list:
            station = simulator.radar_stations[radar_id]
            
            with st.expander(f"📡 {station.get('基本信息', {}).get('名称', radar_id)}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("频率", f"{station.get('雷达参数', {}).get('发射机', {}).get('载波频率_Hz', 0)/1e9:.1f} GHz")
                with col2:
                    st.metric("功率", f"{station.get('雷达参数', {}).get('发射机', {}).get('峰值功率_W', 0)/1000:.0f} kW")
                with col3:
                    # 计算检测概率
                    detection_prob = simulator.calculate_detection_probability(
                        radar_id, target_rcs, range_km, jammer_power
                    )
                    st.metric("检测概率", f"{detection_prob*100:.0f}%")
        
        # 执行仿真按钮
        if st.button("🚀 开始仿真", use_container_width=True):
            with st.spinner("执行仿真中..."):
                results = simulator.simulate_scenario()
                
                if results:
                    st.success("✅ 仿真完成!")
                    
                    # 显示结果
                    st.markdown("### 📊 仿真结果")
                    
                    # 创建结果图表
                    radar_names = []
                    detection_probs = []
                    
                    for radar_id in radar_list:
                        station = simulator.radar_stations[radar_id]
                        prob = simulator.calculate_detection_probability(
                            radar_id, target_rcs, range_km, jammer_power
                        )
                        radar_names.append(station.get('基本信息', {}).get('名称', radar_id))
                        detection_probs.append(prob)
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=radar_names,
                            y=detection_probs,
                            text=[f"{p*100:.0f}%" for p in detection_probs],
                            textposition='outside',
                            marker_color=['#ef4444' if p < 0.5 else '#f59e0b' if p < 0.8 else '#10b981' for p in detection_probs]
                        )
                    ])
                    
                    fig.update_layout(
                        title="雷达检测概率对比",
                        xaxis_title="雷达名称",
                        yaxis_title="检测概率",
                        yaxis_range=[0, 1],
                        template="plotly_dark"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("👈 请从侧边栏加载仿真配置文件")

if __name__ == "__main__":
    main()