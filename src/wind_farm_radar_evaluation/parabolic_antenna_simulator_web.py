

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import plotly.graph_objects as go
import plotly.express as px
from scipy.special import j1, jv
import pandas as pd
from dataclasses import dataclass
from typing import Tuple, List, Dict, Callable
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 页面配置
st.set_page_config(
    page_title="长城数字抛物面天线方向图对比实验系统",
    page_icon="📡",
    layout="wide"
)

# 应用标题
st.title("📡 长城数字抛物面天线方向图对比实验系统")
st.markdown("""
本实验系统用于对比不同数学函数在抛物面天线方向图建模中的效果，包括高斯函数、sinc函数、泰勒加权等。
通过交互式参数调整，您可以直观地观察各种函数对天线性能指标的影响。
""")

# 侧边栏 - 参数控制
st.sidebar.header("🔧 天线参数配置")

# 基本天线参数
st.sidebar.subheader("基本参数")
frequency = st.sidebar.slider(
    "工作频率 (GHz)",
    min_value=0.5,
    max_value=20.0,
    value=3.0,
    step=0.1,
    help="天线的工作频率，单位GHz"
)

antenna_diameter = st.sidebar.slider(
    "天线口径直径 (m)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.1,
    help="抛物面天线的物理口径直径"
)

efficiency = st.sidebar.slider(
    "天线效率 (%)",
    min_value=30,
    max_value=90,
    value=60,
    step=5,
    help="天线的孔径效率，考虑各种损耗"
)

# 波束参数
st.sidebar.subheader("波束参数")
beamwidth_az = st.sidebar.slider(
    "方位波束宽度 (°)",
    min_value=0.1,
    max_value=10.0,
    value=3.5,
    step=0.1,
    help="方位面上的3dB波束宽度"
)

beamwidth_el = st.sidebar.slider(
    "俯仰波束宽度 (°)",
    min_value=0.1,
    max_value=15.0,
    value=8.0,
    step=0.1,
    help="俯仰面上的3dB波束宽度"
)

# 方向图函数选择
st.sidebar.subheader("方向图函数选择")

selected_functions = st.sidebar.multiselect(
    "选择要对比的函数模型",
    ["高斯函数", "sinc函数", "泰勒加权", "切比雪夫加权", "余弦平方加权", "实际抛物面模型"],
    default=["高斯函数", "sinc函数", "实际抛物面模型"],
    help="选择用于生成方向图的函数模型"
)

# 高级参数
with st.sidebar.expander("🔬 高级参数配置"):
    # 高斯函数参数
    st.markdown("**高斯函数参数**")
    gauss_sigma_factor = st.slider(
        "高斯Sigma系数",
        min_value=0.1,
        max_value=1.0,
        value=0.4247,
        step=0.01,
        help="控制高斯函数宽度的参数，通常为0.4247时-3dB宽度对应1个标准差"
    )
    
    # 泰勒加权参数
    st.markdown("**泰勒加权参数**")
    taylor_nbar = st.slider(
        "泰勒n̄参数",
        min_value=2,
        max_value=10,
        value=4,
        step=1,
        help="泰勒加权中的n̄参数，控制过渡区"
    )
    
    taylor_sll_db = st.slider(
        "泰勒设计旁瓣电平 (dB)",
        min_value=-50,
        max_value=-20,
        value=-30,
        step=5,
        help="泰勒加权设计旁瓣电平"
    )
    
    # 切比雪夫参数
    st.markdown("**切比雪夫参数**")
    chebyshev_sll_db = st.slider(
        "切比雪夫旁瓣电平 (dB)",
        min_value=-50,
        max_value=-20,
        value=-25,
        step=5,
        help="切比雪夫加权设计旁瓣电平"
    )

st.sidebar.subheader("[天线分析平台](http://192.168.15.131:8502/)")
st.sidebar.subheader("[相控阵天线波束成形仿真器](http://192.168.15.131:8503/)")

# 初始化数据类
@dataclass
class AntennaPatternResult:
    """天线方向图结果数据类"""
    name: str
    azimuth_pattern: np.ndarray
    elevation_pattern: np.ndarray
    full_pattern: np.ndarray
    azimuth_angles: np.ndarray
    elevation_angles: np.ndarray
    parameters: Dict
    metrics: Dict

class ParabolicAntennaPatternGenerator:
    """抛物面天线方向图生成器"""
    
    def __init__(self, frequency: float, diameter: float, efficiency: float):
        """
        初始化天线参数
        
        参数:
            frequency: 频率 (GHz)
            diameter: 口径直径 (m)
            efficiency: 天线效率 (%)
        """
        self.frequency = frequency
        self.diameter = diameter
        self.efficiency = efficiency / 100.0
        
        # 计算波长
        self.wavelength = 0.3 / frequency  # 光速/frequency (m)
        
        # 计算有效面积
        self.area = np.pi * (diameter / 2)**2
        
        # 计算理论增益
        self.theoretical_gain = 10 * np.log10(
            self.efficiency * (4 * np.pi * self.area / self.wavelength**2)
        )
        
    def calculate_ideal_beamwidth(self) -> float:
        """计算理想波束宽度"""
        # 抛物面天线的理想波束宽度公式: θ ≈ 70 * λ/D (度)
        ideal_bw = 70 * self.wavelength / self.diameter
        return ideal_bw
    
    def generate_gaussian_pattern(self, beamwidth_az: float, beamwidth_el: float, 
                                 sigma_factor: float = 0.4247) -> AntennaPatternResult:
        """生成高斯函数方向图"""
        # 创建角度网格
        az_angles = np.linspace(-3*beamwidth_az, 3*beamwidth_az, 361)
        el_angles = np.linspace(-3*beamwidth_el, 3*beamwidth_el, 361)
        
        # 计算标准差
        sigma_az = beamwidth_az / (2 * np.sqrt(2 * np.log(2)))  # 转换为标准差
        sigma_el = beamwidth_el / (2 * np.sqrt(2 * np.log(2)))
        
        # 生成高斯方向图
        az_pattern = np.exp(-0.5 * (az_angles / (sigma_az * sigma_factor))**2)
        el_pattern = np.exp(-0.5 * (el_angles / (sigma_el * sigma_factor))**2)
        
        # 生成完整2D方向图
        AZ, EL = np.meshgrid(az_angles, el_angles)
        full_pattern = np.exp(-0.5 * ((AZ/(sigma_az*sigma_factor))**2 + (EL/(sigma_el*sigma_factor))**2))
        
        # 转换为dB
        az_pattern_db = 20 * np.log10(az_pattern + 1e-10)
        el_pattern_db = 20 * np.log10(el_pattern + 1e-10)
        full_pattern_db = 20 * np.log10(full_pattern + 1e-10)
        
        # 计算性能指标
        metrics = self._calculate_pattern_metrics(az_pattern_db, el_pattern_db, full_pattern_db)
        
        return AntennaPatternResult(
            name="高斯函数",
            azimuth_pattern=az_pattern_db,
            elevation_pattern=el_pattern_db,
            full_pattern=full_pattern_db,
            azimuth_angles=az_angles,
            elevation_angles=el_angles,
            parameters={
                "sigma_factor": sigma_factor,
                "beamwidth_az": beamwidth_az,
                "beamwidth_el": beamwidth_el
            },
            metrics=metrics
        )
    
    def generate_sinc_pattern(self, beamwidth_az: float, beamwidth_el: float) -> AntennaPatternResult:
        """生成sinc函数方向图（均匀照射）"""
        # 创建角度网格
        az_angles = np.linspace(-3*beamwidth_az, 3*beamwidth_az, 361)
        el_angles = np.linspace(-3*beamwidth_el, 3*beamwidth_el, 361)
        
        # 归一化因子
        k_az = np.pi * 1.39 / np.radians(beamwidth_az)  # sinc函数第一个零点位置
        k_el = np.pi * 1.39 / np.radians(beamwidth_el)
        
        # 生成sinc方向图
        az_rad = np.radians(az_angles)
        el_rad = np.radians(el_angles)
        
        az_pattern = np.abs(np.sinc(k_az * az_rad / np.pi))
        el_pattern = np.abs(np.sinc(k_el * el_rad / np.pi))
        
        # 生成完整2D方向图
        AZ, EL = np.meshgrid(az_rad, el_rad)
        full_pattern = np.abs(np.sinc(k_az * AZ / np.pi)) * np.abs(np.sinc(k_el * EL / np.pi))
        
        # 转换为dB
        az_pattern_db = 20 * np.log10(az_pattern + 1e-10)
        el_pattern_db = 20 * np.log10(el_pattern + 1e-10)
        full_pattern_db = 20 * np.log10(full_pattern + 1e-10)
        
        # 计算性能指标
        metrics = self._calculate_pattern_metrics(az_pattern_db, el_pattern_db, full_pattern_db)
        
        return AntennaPatternResult(
            name="sinc函数（均匀照射）",
            azimuth_pattern=az_pattern_db,
            elevation_pattern=el_pattern_db,
            full_pattern=full_pattern_db,
            azimuth_angles=az_angles,
            elevation_angles=el_angles,
            parameters={
                "k_az": k_az,
                "k_el": k_el
            },
            metrics=metrics
        )
    
    def generate_taylor_pattern(self, beamwidth_az: float, beamwidth_el: float,
                               nbar: int = 4, sll_db: float = -30) -> AntennaPatternResult:
        """生成泰勒加权方向图"""
        # 创建角度网格
        az_angles = np.linspace(-3*beamwidth_az, 3*beamwidth_az, 361)
        el_angles = np.linspace(-3*beamwidth_el, 3*beamwidth_el, 361)
        
        # 泰勒加权参数
        sll_linear = 10**(sll_db/20)
        
        # 计算泰勒加权的sigma参数
        A = (1/np.pi) * np.arccosh(1/sll_linear)
        sigma = nbar / np.sqrt(A**2 + (nbar - 0.5)**2)
        
        # 生成泰勒方向图
        az_pattern = self._taylor_weighting(az_angles, beamwidth_az, nbar, sll_db, sigma)
        el_pattern = self._taylor_weighting(el_angles, beamwidth_el, nbar, sll_db, sigma)
        
        # 生成完整2D方向图
        AZ, EL = np.meshgrid(az_angles, el_angles)
        az_part = self._taylor_weighting(AZ.flatten(), beamwidth_az, nbar, sll_db, sigma)
        el_part = self._taylor_weighting(EL.flatten(), beamwidth_el, nbar, sll_db, sigma)
        full_pattern = (az_part * el_part).reshape(AZ.shape)
        
        # 转换为dB
        az_pattern_db = 20 * np.log10(az_pattern + 1e-10)
        el_pattern_db = 20 * np.log10(el_pattern + 1e-10)
        full_pattern_db = 20 * np.log10(full_pattern + 1e-10)
        
        # 计算性能指标
        metrics = self._calculate_pattern_metrics(az_pattern_db, el_pattern_db, full_pattern_db)
        
        return AntennaPatternResult(
            name=f"泰勒加权 (n̄={nbar}, SLL={sll_db}dB)",
            azimuth_pattern=az_pattern_db,
            elevation_pattern=el_pattern_db,
            full_pattern=full_pattern_db,
            azimuth_angles=az_angles,
            elevation_angles=el_angles,
            parameters={
                "nbar": nbar,
                "sll_db": sll_db,
                "sigma": sigma
            },
            metrics=metrics
        )
    
    def _taylor_weighting(self, angles: np.ndarray, beamwidth: float, 
                          nbar: int, sll_db: float, sigma: float) -> np.ndarray:
        """泰勒加权函数
        
        参数:
            angles: 角度数组（度）
            beamwidth: 波束宽度（度）
            nbar: 泰勒窗的阶数
            sll_db: 期望的副瓣电平（dB）
            sigma: 泰勒窗参数
        
        返回:
            加权系数数组
        """
        # 转换为弧度
        theta = np.radians(angles)
        bw_rad = np.radians(beamwidth)
        
        # 计算A参数（基于副瓣电平）
        # 泰勒加权公式中的A
        A = (1.0 / np.pi) * np.arccosh(10**(-sll_db / 20.0))
        
        # 计算u参数
        u = (np.pi * 1.39 / bw_rad) * np.sin(theta)  # 使用1.39确保第一个零点对应波束宽度
        
        # 泰勒方向图函数
        pattern = np.ones_like(u)
        
        for n in range(1, nbar):
            pattern *= (1 - (u**2) / (np.pi**2 * sigma**2 * (A**2 + (n-0.5)**2))) / \
                      (1 - (u**2) / (np.pi**2 * n**2))
        
        # 归一化
        pattern = np.abs(pattern)
        pattern[pattern > 1] = 1
        
        return pattern
    
    def generate_chebyshev_pattern(self, beamwidth_az: float, beamwidth_el: float,
                                  sll_db: float = -25) -> AntennaPatternResult:
        """生成切比雪夫加权方向图"""
        # 创建角度网格
        az_angles = np.linspace(-3*beamwidth_az, 3*beamwidth_az, 361)
        el_angles = np.linspace(-3*beamwidth_el, 3*beamwidth_el, 361)
        
        # 切比雪夫参数
        R = 10**(-sll_db/20)
        x0 = np.cosh(np.arccosh(R) / 10)  # 假设10个元素
        
        # 生成切比雪夫方向图
        az_pattern = self._chebyshev_weighting(az_angles, beamwidth_az, x0)
        el_pattern = self._chebyshev_weighting(el_angles, beamwidth_el, x0)
        
        # 生成完整2D方向图
        AZ, EL = np.meshgrid(az_angles, el_angles)
        az_part = self._chebyshev_weighting(AZ.flatten(), beamwidth_az, x0)
        el_part = self._chebyshev_weighting(EL.flatten(), beamwidth_el, x0)
        full_pattern = (az_part * el_part).reshape(AZ.shape)
        
        # 转换为dB
        az_pattern_db = 20 * np.log10(az_pattern + 1e-10)
        el_pattern_db = 20 * np.log10(el_pattern + 1e-10)
        full_pattern_db = 20 * np.log10(full_pattern + 1e-10)
        
        # 计算性能指标
        metrics = self._calculate_pattern_metrics(az_pattern_db, el_pattern_db, full_pattern_db)
        
        return AntennaPatternResult(
            name=f"切比雪夫加权 (SLL={sll_db}dB)",
            azimuth_pattern=az_pattern_db,
            elevation_pattern=el_pattern_db,
            full_pattern=full_pattern_db,
            azimuth_angles=az_angles,
            elevation_angles=el_angles,
            parameters={
                "sll_db": sll_db,
                "R": R,
                "x0": x0
            },
            metrics=metrics
        )
    
    def _chebyshev_weighting(self, angles: np.ndarray, beamwidth: float, x0: float) -> np.ndarray:
        """切比雪夫加权函数"""
        # 转换为弧度
        theta = np.radians(angles)
        bw_rad = np.radians(beamwidth)
        
        # 计算u参数
        u = (np.pi * 1.39 / bw_rad) * np.sin(theta)
        
        # 切比雪夫多项式
        pattern = np.abs(np.cos(10 * np.arccos(np.cos(u) / x0)))
        
        # 归一化
        pattern = pattern / np.max(pattern)
        
        return pattern
    
    def generate_cosine_squared_pattern(self, beamwidth_az: float, beamwidth_el: float) -> AntennaPatternResult:
        """生成余弦平方加权方向图"""
        # 创建角度网格
        az_angles = np.linspace(-3*beamwidth_az, 3*beamwidth_az, 361)
        el_angles = np.linspace(-3*beamwidth_el, 3*beamwidth_el, 361)
        
        # 生成余弦平方方向图
        az_pattern = np.cos(np.radians(az_angles) * (90/beamwidth_az))**2
        el_pattern = np.cos(np.radians(el_angles) * (90/beamwidth_el))**2
        
        # 处理边界
        az_pattern[np.abs(az_angles) > 90] = 0
        el_pattern[np.abs(el_angles) > 90] = 0
        
        # 生成完整2D方向图
        AZ, EL = np.meshgrid(az_angles, el_angles)
        full_pattern = np.cos(np.radians(AZ) * (90/beamwidth_az))**2 * np.cos(np.radians(EL) * (90/beamwidth_el))**2
        
        # 转换为dB
        az_pattern_db = 20 * np.log10(az_pattern + 1e-10)
        el_pattern_db = 20 * np.log10(el_pattern + 1e-10)
        full_pattern_db = 20 * np.log10(full_pattern + 1e-10)
        
        # 计算性能指标
        metrics = self._calculate_pattern_metrics(az_pattern_db, el_pattern_db, full_pattern_db)
        
        return AntennaPatternResult(
            name="余弦平方加权",
            azimuth_pattern=az_pattern_db,
            elevation_pattern=el_pattern_db,
            full_pattern=full_pattern_db,
            azimuth_angles=az_angles,
            elevation_angles=el_angles,
            parameters={},
            metrics=metrics
        )
    
    def generate_real_parabolic_pattern(self, beamwidth_az: float, beamwidth_el: float) -> AntennaPatternResult:
        """生成实际抛物面天线方向图（基于Bessel函数）"""
        # 创建角度网格
        az_angles = np.linspace(-3*beamwidth_az, 3*beamwidth_az, 361)
        el_angles = np.linspace(-3*beamwidth_el, 3*beamwidth_el, 361)
        
        # 计算抛物面天线方向图（圆口径均匀照射）
        D_lambda = self.diameter / self.wavelength
        
        # 方位方向图
        az_rad = np.radians(az_angles)
        az_u = np.pi * D_lambda * np.sin(az_rad)
        az_pattern = np.ones_like(az_u)
        mask_az = az_u != 0
        az_pattern[mask_az] = np.abs(2 * j1(az_u[mask_az]) / az_u[mask_az])
        
        # 俯仰方向图
        el_rad = np.radians(el_angles)
        el_u = np.pi * D_lambda * np.sin(el_rad)
        el_pattern = np.ones_like(el_u)
        mask_el = el_u != 0
        el_pattern[mask_el] = np.abs(2 * j1(el_u[mask_el]) / el_u[mask_el])
        
        # 生成完整2D方向图
        AZ, EL = np.meshgrid(az_rad, el_rad)
        U = np.pi * D_lambda * np.sqrt(np.sin(AZ)**2 + np.sin(EL)**2)
        full_pattern = np.ones_like(U)
        mask = U != 0
        full_pattern[mask] = np.abs(2 * j1(U[mask]) / U[mask])
        
        # 转换为dB
        az_pattern_db = 20 * np.log10(az_pattern + 1e-10)
        el_pattern_db = 20 * np.log10(el_pattern + 1e-10)
        full_pattern_db = 20 * np.log10(full_pattern + 1e-10)
        
        # 计算性能指标
        metrics = self._calculate_pattern_metrics(az_pattern_db, el_pattern_db, full_pattern_db)
        
        return AntennaPatternResult(
            name="实际抛物面模型",
            azimuth_pattern=az_pattern_db,
            elevation_pattern=el_pattern_db,
            full_pattern=full_pattern_db,
            azimuth_angles=az_angles,
            elevation_angles=el_angles,
            parameters={
                "D/λ": D_lambda
            },
            metrics=metrics
        )
    
    def _calculate_pattern_metrics(self, az_pattern_db: np.ndarray, el_pattern_db: np.ndarray, 
                                   full_pattern_db: np.ndarray) -> Dict:
        """计算方向图性能指标"""
        # 计算波束宽度
        az_3db_bw = self._calculate_3db_beamwidth(az_pattern_db)
        el_3db_bw = self._calculate_3db_beamwidth(el_pattern_db)
        
        # 计算旁瓣电平
        az_sll = self._calculate_sidelobe_level(az_pattern_db)
        el_sll = self._calculate_sidelobe_level(el_pattern_db)
        
        # 计算第一零点位置
        az_first_null = self._calculate_first_null(az_pattern_db)
        el_first_null = self._calculate_first_null(el_pattern_db)
        
        return {
            "beamwidth_3db_az": az_3db_bw,
            "beamwidth_3db_el": el_3db_bw,
            "sidelobe_level_az": az_sll,
            "sidelobe_level_el": el_sll,
            "first_null_az": az_first_null,
            "first_null_el": el_first_null,
            "directivity": self._estimate_directivity(az_3db_bw, el_3db_bw)
        }
    
    def _calculate_3db_beamwidth(self, pattern_db: np.ndarray) -> float:
        """计算3dB波束宽度"""
        peak_idx = np.argmax(pattern_db)
        half_power = pattern_db[peak_idx] - 3
        
        # 查找-3dB点
        left_idx = np.where(pattern_db[:peak_idx] <= half_power)[0]
        right_idx = np.where(pattern_db[peak_idx:] <= half_power)[0]
        
        if len(left_idx) > 0 and len(right_idx) > 0:
            beamwidth = 2 * min(abs(left_idx[-1] - peak_idx), abs(right_idx[0]))
        else:
            beamwidth = 0
        
        return beamwidth
    
    def _calculate_sidelobe_level(self, pattern_db: np.ndarray) -> float:
        """计算旁瓣电平"""
        peak_idx = np.argmax(pattern_db)
        
        # 找到主瓣范围（假设主瓣宽度为5个采样点）
        mainlobe_width = 5
        mainlobe_indices = range(max(0, peak_idx - mainlobe_width),  # type: ignore
                                 min(len(pattern_db), peak_idx + mainlobe_width + 1)) # type: ignore
        
        # 在主瓣之外寻找最高旁瓣
        sidelobe_indices = [i for i in range(len(pattern_db)) if i not in mainlobe_indices]
        
        if len(sidelobe_indices) > 0:
            max_sidelobe = np.max(pattern_db[sidelobe_indices])
            sll = pattern_db[peak_idx] - max_sidelobe
        else:
            sll = 0
        
        return sll
    
    def _calculate_first_null(self, pattern_db: np.ndarray) -> float:
        """计算第一零点位置"""
        peak_idx = np.argmax(pattern_db)
        
        # 从峰值点向右查找第一个最小值
        for i in range(peak_idx + 1, len(pattern_db) - 1):
            if pattern_db[i] < pattern_db[i-1] and pattern_db[i] < pattern_db[i+1]:
                return i - peak_idx # type: ignore
        
        return 0
    
    def _estimate_directivity(self, bw_az: float, bw_el: float) -> float:
        """估算方向性系数"""
        # 简单估算公式: D ≈ 41253 / (θ_az * θ_el)
        if bw_az > 0 and bw_el > 0:
            D = 41253 / (bw_az * bw_el)
            return 10 * np.log10(D)
        return 0

# 主应用
def main():
    # 初始化天线生成器
    antenna_gen = ParabolicAntennaPatternGenerator(frequency, antenna_diameter, efficiency)
    
    # 计算理想波束宽度
    ideal_bw = antenna_gen.calculate_ideal_beamwidth()
    
    # 显示天线参数
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("工作频率", f"{frequency:.1f} GHz")
    with col2:
        st.metric("天线口径", f"{antenna_diameter:.1f} m")
    with col3:
        st.metric("天线效率", f"{efficiency}%")
    with col4:
        st.metric("理想波束宽度", f"{ideal_bw:.2f}°")
    
    st.markdown("---")
    
    # 生成方向图
    results = []
    
    if "高斯函数" in selected_functions:
        gauss_result = antenna_gen.generate_gaussian_pattern(
            beamwidth_az, beamwidth_el, gauss_sigma_factor
        )
        results.append(gauss_result)
    
    if "sinc函数" in selected_functions:
        sinc_result = antenna_gen.generate_sinc_pattern(beamwidth_az, beamwidth_el)
        results.append(sinc_result)
    
    if "泰勒加权" in selected_functions:
        taylor_result = antenna_gen.generate_taylor_pattern(
            beamwidth_az, beamwidth_el, taylor_nbar, taylor_sll_db
        )
        results.append(taylor_result)
    
    if "切比雪夫加权" in selected_functions:
        chebyshev_result = antenna_gen.generate_chebyshev_pattern(
            beamwidth_az, beamwidth_el, chebyshev_sll_db
        )
        results.append(chebyshev_result)
    
    if "余弦平方加权" in selected_functions:
        cosine_result = antenna_gen.generate_cosine_squared_pattern(beamwidth_az, beamwidth_el)
        results.append(cosine_result)
    
    if "实际抛物面模型" in selected_functions:
        real_result = antenna_gen.generate_real_parabolic_pattern(beamwidth_az, beamwidth_el)
        results.append(real_result)
    
    # 创建选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["📈 方向图对比", "🌐 3D可视化", "📊 性能指标", "📚 理论分析"])
    
    with tab1:
        st.header("方向图对比分析")
        
        # 选择视图类型
        view_type = st.radio(
            "选择视图类型",
            ["方位方向图", "俯仰方向图", "二维方向图"],
            horizontal=True
        )
        
        if view_type in ["方位方向图", "俯仰方向图"]:
            # 创建方向图对比图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for i, result in enumerate(results):
                if view_type == "方位方向图":
                    angles = result.azimuth_angles
                    pattern = result.azimuth_pattern
                    label = f"{result.name} (BW={result.metrics['beamwidth_3db_az']:.1f}°, SLL={result.metrics['sidelobe_level_az']:.1f}dB)"
                else:  # 俯仰方向图
                    angles = result.elevation_angles
                    pattern = result.elevation_pattern
                    label = f"{result.name} (BW={result.metrics['beamwidth_3db_el']:.1f}°, SLL={result.metrics['sidelobe_level_el']:.1f}dB)"
                
                ax.plot(angles, pattern, linewidth=2, color=colors[i % len(colors)], label=label)
            
            ax.set_xlabel("角度 (°)", fontsize=12)
            ax.set_ylabel("增益 (dB)", fontsize=12)
            ax.set_title(f"{view_type}对比", fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=10)
            ax.set_ylim([-50, 5]) # type: ignore
            
            # 添加参考线
            ax.axhline(y=-3, color='gray', linestyle='--', alpha=0.5, label='-3dB')
            ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
            
            st.pyplot(fig)
            
        else:  # 二维方向图
            # 选择要显示的函数
            selected_result = st.selectbox(
                "选择要显示的函数",
                [r.name for r in results],
                index=0
            )
            
            result = next(r for r in results if r.name == selected_result)
            
            # 创建2D方向图
            fig, ax = plt.subplots(figsize=(8, 6))
            
            im = ax.imshow(result.full_pattern, 
                          extent=[result.azimuth_angles[0], result.azimuth_angles[-1],
                                  result.elevation_angles[0], result.elevation_angles[-1]], # type: ignore
                          cmap='jet', aspect='auto', origin='lower',
                          vmin=-30, vmax=0)
            
            ax.set_xlabel("方位角 (°)", fontsize=12)
            ax.set_ylabel("俯仰角 (°)", fontsize=12)
            ax.set_title(f"{result.name} - 二维方向图", fontsize=14, fontweight='bold')
            
            plt.colorbar(im, ax=ax, label='增益 (dB)')
            
            st.pyplot(fig)
    
    with tab2:
        st.header("三维方向图可视化")
        
        # 选择要显示的函数
        selected_result_3d = st.selectbox(
            "选择要3D可视化的函数",
            [r.name for r in results],
            index=0,
            key="3d_select"
        )
        
        result_3d = next(r for r in results if r.name == selected_result_3d)
        
        # 创建3D图
        X, Y = np.meshgrid(result_3d.azimuth_angles, result_3d.elevation_angles)
        Z = result_3d.full_pattern
        
        # 创建Plotly 3D图
        fig = go.Figure(data=[
            go.Surface(
                z=Z, x=X, y=Y,
                colorscale='jet',
                contours={
                    "z": {"show": True, "usecolormap": True, "highlightcolor": "limegreen", "project": {"z": True}}
                },
                showscale=True,
                colorbar=dict(title="增益 (dB)")
                # colorbar=dict(title="增益 (dB)", titleside="right")
            )
        ])
        
        fig.update_layout(
            title=f"{result_3d.name} - 三维方向图",
            scene=dict(
                xaxis_title='方位角 (°)',
                yaxis_title='俯仰角 (°)',
                zaxis_title='增益 (dB)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=600,
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
    
    with tab3:
        st.header("性能指标对比")
        
        # 创建性能指标表格
        metrics_data = []
        for result in results:
            metrics_data.append({
                "函数模型": result.name,
                "方位3dB波束宽度 (°)": f"{result.metrics['beamwidth_3db_az']:.2f}",
                "俯仰3dB波束宽度 (°)": f"{result.metrics['beamwidth_3db_el']:.2f}",
                "方位旁瓣电平 (dB)": f"{result.metrics['sidelobe_level_az']:.1f}",
                "俯仰旁瓣电平 (dB)": f"{result.metrics['sidelobe_level_el']:.1f}",
                "方位第一零点 (°)": f"{result.metrics['first_null_az']:.1f}",
                "俯仰第一零点 (°)": f"{result.metrics['first_null_el']:.1f}",
                "估算方向性 (dBi)": f"{result.metrics['directivity']:.1f}"
            })
        
        df_metrics = pd.DataFrame(metrics_data)
        st.dataframe(df_metrics, width='stretch')
        
        # 创建性能对比图
        st.subheader("关键性能指标对比")
        
        metric_to_compare = st.selectbox(
            "选择要对比的指标",
            ["方位3dB波束宽度 (°)", "方位旁瓣电平 (dB)", "估算方向性 (dBi)"]
        )
        
        # 提取数据
        model_names = [result.name for result in results]
        if metric_to_compare == "方位3dB波束宽度 (°)":
            metric_values = [result.metrics['beamwidth_3db_az'] for result in results]
            ylabel = "波束宽度 (°)"
        elif metric_to_compare == "方位旁瓣电平 (dB)":
            metric_values = [result.metrics['sidelobe_level_az'] for result in results]
            ylabel = "旁瓣电平 (dB)"
        else:
            metric_values = [result.metrics['directivity'] for result in results]
            ylabel = "方向性 (dBi)"
        
        # 创建柱状图
        fig_bar, ax_bar = plt.subplots(figsize=(10, 6))
        bars = ax_bar.bar(range(len(model_names)), metric_values, 
                         color=plt.cm.Set3(np.linspace(0, 1, len(model_names)))) # type: ignore
        
        ax_bar.set_xlabel("函数模型", fontsize=12)
        ax_bar.set_ylabel(ylabel, fontsize=12)
        ax_bar.set_title(f"各函数模型{metric_to_compare}对比", fontsize=14, fontweight='bold')
        ax_bar.set_xticks(range(len(model_names)))
        ax_bar.set_xticklabels(model_names, rotation=45, ha='right')
        ax_bar.grid(True, axis='y', alpha=0.3)
        
        # 在柱子上添加数值
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            ax_bar.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{value:.1f}', ha='center', va='bottom', fontsize=10)
        
        st.pyplot(fig_bar)
    
    with tab4:
        st.header("理论分析与说明")
        
        st.markdown("""
        ### 各函数模型的数学原理
        
        #### 1. 高斯函数
        **数学表达式**: 
        $$
        F(θ) = \\exp\\left(-\\frac{θ^2}{2σ^2}\\right)
        $$
        
        **特点**:
        - 旁瓣电平较低，自然衰减
        - 无限可导，数学性质优良
        - 傅里叶变换仍是高斯函数
        - 广泛应用于系统级仿真
        
        #### 2. sinc函数（均匀照射）
        **数学表达式**:
        $$
        F(θ) = \\left|\\frac{\\sin(πD\\sinθ/λ)}{πD\\sinθ/λ}\\right|
        $$
        
        **特点**:
        - 描述均匀照射圆孔径的理想方向图
        - 第一旁瓣电平为-13.2dB
        - 存在明显的旁瓣结构
        
        #### 3. 泰勒加权
        **数学原理**:
        - 通过调整孔径照射函数控制旁瓣
        - 设计旁瓣电平可调
        - 在主瓣附近近似等旁瓣电平
        
        #### 4. 切比雪夫加权
        **特点**:
        - 等旁瓣设计
        - 给定旁瓣电平时波束最窄
        - 工程实现复杂
        
        #### 5. 余弦平方加权
        **数学表达式**:
        $$
        F(θ) = \\cos^2\\left(\\frac{πθ}{2θ_0}\\right)
        $$
        
        **特点**:
        - 简单加权函数
        - 旁瓣衰减较快
        - 实现简单
        
        ### 应用建议
        
        1. **快速系统仿真**：推荐使用高斯函数，计算简单，旁瓣特性合理
        2. **精确天线设计**：推荐使用实际抛物面模型或泰勒加权
        3. **教学演示**：使用sinc函数展示理想情况
        4. **旁瓣抑制设计**：使用泰勒加权或切比雪夫加权
        """)
        
        # 添加公式说明
        st.subheader("关键公式")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **抛物面天线增益公式**:
            $$
            G = η\\left(\\frac{πD}{λ}\\right)^2
            $$
            
            **3dB波束宽度近似**:
            $$
            θ_{3dB} ≈ \\frac{70λ}{D} \\quad [度]
            $$
            """)
        
        with col2:
            st.markdown("""
            **方向性估算公式**:
            $$
            D ≈ \\frac{41253}{θ_{az}θ_{el}} \\quad [dBi]
            $$
            
            **第一零点位置**:
            $$
            θ_{null} ≈ \\frac{1.22λ}{D} \\quad [弧度]
            $$
            """)
    
    # 添加结论部分
    st.markdown("---")
    st.header("🎯 实验结论与建议")
    
    if len(results) >= 2:
        # 找出最佳模型
        best_sll = min(results, key=lambda x: x.metrics['sidelobe_level_az'])
        best_bw = min(results, key=lambda x: x.metrics['beamwidth_3db_az'])
        best_directivity = max(results, key=lambda x: x.metrics['directivity'])
        
        st.info(f"""
        ### 实验结果总结
        
        基于当前参数配置：
        
        1. **旁瓣抑制最佳**: **{best_sll.name}**，旁瓣电平 = {best_sll.metrics['sidelobe_level_az']:.1f}dB
        2. **波束最窄**: **{best_bw.name}**，波束宽度 = {best_bw.metrics['beamwidth_3db_az']:.2f}°
        3. **方向性最高**: **{best_directivity.name}**，方向性 = {best_directivity.metrics['directivity']:.1f}dBi
        
        ### 雷达应用建议
        
        | 应用场景 | 推荐函数 | 理由 |
        |---------|---------|------|
        | 空中小目标检测 | 高斯函数 | 旁瓣低，减少多径干扰 |
        | 高精度跟踪 | 实际抛物面模型 | 最接近真实天线特性 |
        | 快速仿真 | sinc函数 | 计算简单，物理意义明确 |
        | 低旁瓣系统 | 泰勒加权 | 可设计旁瓣电平 |
        
        ### 调整建议
        
        1. 降低工作频率或增大口径可减小波束宽度
        2. 提高天线效率可增加方向性
        3. 高斯函数的sigma系数影响波束形状和旁瓣
        4. 泰勒加权的n̄参数控制旁瓣过渡
        """)
    
    # 添加下载功能
    st.markdown("---")
    st.subheader("📥 数据导出")
    
    if st.button("导出实验数据"):
        # 创建数据表格
        export_data = []
        for result in results:
            export_data.append({
                "模型名称": result.name,
                "方位波束宽度_deg": result.metrics['beamwidth_3db_az'],
                "俯仰波束宽度_deg": result.metrics['beamwidth_3db_el'],
                "方位旁瓣电平_dB": result.metrics['sidelobe_level_az'],
                "俯仰旁瓣电平_dB": result.metrics['sidelobe_level_el'],
                "方位第一零点_deg": result.metrics['first_null_az'],
                "俯仰第一零点_deg": result.metrics['first_null_el'],
                "估算方向性_dBi": result.metrics['directivity']
            })
        
        df_export = pd.DataFrame(export_data)
        csv = df_export.to_csv(index=False)
        
        st.download_button(
            label="下载CSV文件",
            data=csv,
            file_name=f"antenna_pattern_comparison_f{frequency}GHz_D{antenna_diameter}m.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()