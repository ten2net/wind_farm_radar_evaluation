"""
Ku波段32x32相控阵雷达波束成形及实时仿真工具
使用Streamlit和Plotly构建
优化版本
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from typing import Tuple, List, Optional

# --- 页面配置 ---
st.set_page_config(
    page_title="Ku波段相控阵雷达仿真",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 标题和描述 ---
st.title("📡 Ku波段32x32相控阵雷达波束成形仿真")
st.markdown("""
这是一个交互式相控阵雷达波束成形仿真工具。
- **阵列规模**：32×32阵元
- **工作频段**：Ku波段（12-18 GHz）
- **主要功能**：波束成形、方向图可视化、实时扫描仿真
""")

# --- 缓存装饰器以提高性能 ---
@st.cache_data
def calculate_wavelength_cached(frequency_ghz: float) -> float:
    """计算波长"""
    c = 3e8  # 光速 m/s
    return c / (frequency_ghz * 1e9)

@st.cache_data
def generate_array_positions_cached(N: int, M: int, d: float, wavelength: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """生成阵列位置"""
    x = np.arange(-(N-1)/2, (N-1)/2 + 1) * d * wavelength
    y = np.arange(-(M-1)/2, (M-1)/2 + 1) * d * wavelength
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)
    return X, Y, Z

@st.cache_data
def calculate_phase_shift_cached(theta_deg: float, phi_deg: float, X: np.ndarray, Y: np.ndarray, 
                                 Z: np.ndarray, wavelength: float) -> np.ndarray:
    """计算相位偏移"""
    theta = np.radians(theta_deg)
    phi = np.radians(phi_deg)
    
    k = 2 * np.pi / wavelength
    u = np.sin(theta) * np.cos(phi)
    v = np.sin(theta) * np.sin(phi)
    w = np.cos(theta)
    
    phase = k * (u * X + v * Y + w * Z)
    return phase

@st.cache_data
def calculate_array_factor_cached(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, phase_shift: np.ndarray,
                                 theta_scan: float, phi_scan: float, wavelength: float) -> float:
    """计算阵列因子"""
    theta = np.radians(theta_scan)
    phi = np.radians(phi_scan)
    
    k = 2 * np.pi / wavelength
    u_obs = np.sin(theta) * np.cos(phi)
    v_obs = np.sin(theta) * np.sin(phi)
    w_obs = np.cos(theta)
    
    spatial_phase = k * (u_obs * X + v_obs * Y + w_obs * Z)
    total_phase = spatial_phase - phase_shift
    array_factor = np.sum(np.exp(1j * total_phase))
    
    return np.abs(array_factor) / (X.shape[0] * X.shape[1])

@st.cache_data
def calculate_radiation_pattern_cached(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, phase_shift: np.ndarray,
                                      wavelength: float, theta_range: np.ndarray, phi_fixed: float = 0) -> np.ndarray:
    """计算辐射方向图"""
    af_values = []
    for t in theta_range:
        af = calculate_array_factor_cached(X, Y, Z, phase_shift, t, phi_fixed, wavelength)
        af_values.append(20 * np.log10(af + 1e-10))
    return np.array(af_values)

# --- 分析函数 ---
def analyze_pattern(pattern: np.ndarray, angles: np.ndarray) -> Tuple[float, float, List[Tuple[float, float]]]:
    """分析方向图特性"""
    mainlobe_idx = np.argmax(pattern)
    mainlobe_gain = pattern[mainlobe_idx]
    mainlobe_angle = angles[mainlobe_idx]
    
    # 查找副瓣
    sidelobes = []
    for i in range(1, len(pattern)-1):
        if pattern[i] > pattern[i-1] and pattern[i] > pattern[i+1] and i != mainlobe_idx:
            sidelobes.append((angles[i], pattern[i]))
    
    sidelobes.sort(key=lambda x: x[1], reverse=True)
    return mainlobe_gain, mainlobe_angle, sidelobes[:3]

def calculate_scan_loss(theta_deg: float, phi_deg: float, d: float, wavelength: float) -> float:
    """计算扫描损失"""
    theta_rad = np.radians(theta_deg)
    phi_rad = np.radians(phi_deg)
    
    # 波束扫描因子
    u = np.sin(theta_rad) * np.cos(phi_rad)
    v = np.sin(theta_rad) * np.sin(phi_rad)
    
    # 阵元间距归一化
    d_norm = d * wavelength
    
    # 扫描损失近似计算
    if np.abs(u) < 1e-10 and np.abs(v) < 1e-10:
        return 0.0
    
    # 使用余弦损失模型
    scan_angle = np.arccos(np.sqrt(1 - u**2 - v**2))
    scan_loss = 20 * np.log10(np.cos(scan_angle))
    
    return min(0, scan_loss)  # 确保损失为负值

# --- 权重函数 ---
def calculate_weighting(window_type: str, N: int, M: int, sidelobe_level: float = -30) -> np.ndarray:
    """计算加权系数"""
    if window_type == "均匀":
        return np.ones((N, M))
    
    elif window_type == "切比雪夫":
        # 切比雪夫权重近似计算
        n = np.arange(N)
        m = np.arange(M)
        Wx = np.cos(np.pi * (2*n - N + 1) / (2*N))
        Wy = np.cos(np.pi * (2*m - M + 1) / (2*M))
        Wx, Wy = np.meshgrid(Wx, Wy)
        
        # 调整副瓣电平
        R = 10**(sidelobe_level/20)
        w = R + (1 - R) * Wx * Wy
        return w / np.max(w)
    
    elif window_type == "泰勒":
        # 泰勒权重近似
        nx = np.linspace(-1, 1, N)
        ny = np.linspace(-1, 1, M)
        nx, ny = np.meshgrid(nx, ny)
        r = np.sqrt(nx**2 + ny**2)
        
        # 泰勒分布参数
        n_bar = 4
        sigma = 1.5
        w = np.zeros_like(r)
        mask = r <= 1
        w[mask] = 1 + 0.5 * np.cos(np.pi * r[mask]) - 0.5 * np.cos(3 * np.pi * r[mask])
        w[~mask] = 0
        
        return w
    
    elif window_type == "汉明":
        # 汉明窗
        nx = np.arange(N)
        my = np.arange(M)
        Wx = 0.54 - 0.46 * np.cos(2 * np.pi * nx / (N - 1))
        Wy = 0.54 - 0.46 * np.cos(2 * np.pi * my / (M - 1))
        Wx, Wy = np.meshgrid(Wx, Wy)
        return Wx * Wy
    
    return np.ones((N, M))

# --- 侧边栏控制参数 ---
st.sidebar.header("🎛️ 参数设置")

# 频率设置
frequency = st.sidebar.slider(
    "工作频率 (GHz)",
    min_value=12.0,
    max_value=18.0,
    value=14.0,
    step=0.1,
    help="Ku波段频率范围"
)

# 波束方向
theta = st.sidebar.slider(
    "俯仰角 (度)",
    min_value=-60,
    max_value=60,
    value=0,
    step=1,
    help="波束在垂直方向的指向"
)

phi = st.sidebar.slider(
    "方位角 (度)",
    min_value=-60,
    max_value=60,
    value=0,
    step=1,
    help="波束在水平方向的指向"
)

# 阵元间距
d = st.sidebar.slider(
    "阵元间距 (λ)",
    min_value=0.3,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="以波长为单位的阵元间距"
)

# 波束赋形权重
st.sidebar.subheader("波束赋形设置")
weighting_type = st.sidebar.selectbox(
    "权重函数",
    ["均匀", "切比雪夫", "泰勒", "汉明"],
    index=0,
    help="选择加权函数以控制副瓣电平"
)

if weighting_type != "均匀":
    sidelobe_level = st.sidebar.slider(
        "副瓣电平 (dB)",
        -50.0, -20.0, -30.0,
        step=1.0,
        help="目标副瓣电平（仅适用于切比雪夫加权）"
    )

# 目标设置
st.sidebar.subheader("目标模拟")
show_target = st.sidebar.checkbox("显示目标", value=False)
if show_target:
    target_theta = st.sidebar.slider("目标俯仰角", -60, 60, 20)
    target_phi = st.sidebar.slider("目标方位角", -60, 60, 30)
    target_rcs = st.sidebar.slider("目标RCS (m²)", 0.1, 10.0, 1.0, step=0.1)
    target_range = st.sidebar.slider("目标距离 (km)", 1, 100, 10)

# 仿真控制
st.sidebar.subheader("仿真控制")
animate = st.sidebar.checkbox("启用动画仿真", value=True)
if animate:
    scan_mode = st.sidebar.selectbox(
        "扫描模式",
        ["线性扫描", "圆形扫描", "螺旋扫描", "跟踪目标"],
        index=0
    )
    speed = st.sidebar.slider("动画速度", 1, 10, 5)

# 高级设置
with st.sidebar.expander("高级设置"):
    show_grating_lobes = st.checkbox("显示栅瓣", value=False)
    show_null_locations = st.checkbox("显示零点位置", value=False)
    resolution = st.slider("角度分辨率 (度)", 0.1, 1.0, 0.5, step=0.1)

# --- 主计算逻辑 ---
# 计算波长
wavelength = calculate_wavelength_cached(frequency)

# 生成阵列位置
N, M = 32, 32
X, Y, Z = generate_array_positions_cached(N, M, d, wavelength)

# 计算加权系数
weights = calculate_weighting(
    weighting_type, 
    N, M, 
    sidelobe_level if weighting_type != "均匀" else -30
)

# 计算相位偏移
phase_shift = calculate_phase_shift_cached(theta, phi, X, Y, Z, wavelength)

# 应用加权
weighted_phase_shift = phase_shift * weights

# 计算方向图
theta_range = np.linspace(-90, 90, int(180/resolution) + 1)
pattern_elevation = calculate_radiation_pattern_cached(
    X, Y, Z, weighted_phase_shift, wavelength, theta_range, phi_fixed=phi
)

# 计算方位角方向图
phi_range = np.linspace(-180, 180, int(360/resolution) + 1)
pattern_azimuth = calculate_radiation_pattern_cached(
    X, Y, Z, weighted_phase_shift, wavelength, phi_range, theta
)

# 分析方向图
mainlobe_gain, mainlobe_angle, sidelobes = analyze_pattern(pattern_elevation, theta_range)

# 计算波束宽度
half_power = np.max(pattern_elevation) - 3
mainlobe_idx = np.argmax(pattern_elevation)

left_idx = mainlobe_idx
while left_idx > 0 and pattern_elevation[left_idx] > half_power:
    left_idx -= 1

right_idx = mainlobe_idx
while right_idx < len(pattern_elevation) - 1 and pattern_elevation[right_idx] > half_power:
    right_idx += 1

beamwidth = theta_range[right_idx] - theta_range[left_idx]

# 计算扫描损失
scan_loss = calculate_scan_loss(theta, phi, d, wavelength)

# --- 可视化 ---
# 创建子图
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("阵列布局与相位分布", "俯仰角方向图", "波束加权系数", "方位角方向图"),
    specs=[
        [{"type": "scatter3d"}, {"type": "scatter"}],
        [{"type": "heatmap"}, {"type": "scatter"}]
    ],
    vertical_spacing=0.12,
    horizontal_spacing=0.1
)

# 1. 阵列布局（3D）- 添加相位颜色
fig.add_trace(
    go.Scatter3d(
        x=X.flatten(),
        y=Y.flatten(),
        z=Z.flatten(),
        mode='markers',
        marker=dict(
            size=5,
            color=phase_shift.flatten(),
            colorscale='Rainbow',
            showscale=True,
            colorbar=dict(title="相位 (rad)", x=0.45, len=0.7)
        ),
        name='阵元',
        hovertemplate='X: %{x:.3f}m<br>Y: %{y:.3f}m<br>Z: %{z:.3f}m<br>相位: %{marker.color:.2f}rad<extra></extra>'
    ),
    row=1, col=1
)

# 阵列网格
fig.add_trace(
    go.Scatter3d(
        x=X[0, :],
        y=Y[0, :],
        z=Z[0, :],
        mode='lines',
        line=dict(color='gray', width=1, dash='dash'),
        showlegend=False
    ),
    row=1, col=1
)

fig.add_trace(
    go.Scatter3d(
        x=X[:, 0],
        y=Y[:, 0],
        z=Z[:, 0],
        mode='lines',
        line=dict(color='gray', width=1, dash='dash'),
        showlegend=False
    ),
    row=1, col=1
)

fig.update_layout(
    scene=dict(
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        zaxis_title="Z (m)",
        aspectmode='data',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
    )
)

# 2. 俯仰角方向图
fig.add_trace(
    go.Scatter(
        x=theta_range,
        y=pattern_elevation,
        mode='lines',
        line=dict(color='blue', width=3),
        name='方向图',
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.1)',
        hovertemplate='角度: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
    ),
    row=1, col=2
)

# 标记主瓣方向
fig.add_trace(
    go.Scatter(
        x=[theta],
        y=[mainlobe_gain],
        mode='markers+text',
        marker=dict(size=12, color='red', symbol='star'),
        text=['主瓣'],
        textposition="top center",
        name=f'主瓣 ({theta}°)',
        hovertemplate='俯仰角: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
    ),
    row=1, col=2
)

# 标记-3dB点
fig.add_trace(
    go.Scatter(
        x=[theta_range[left_idx], theta_range[right_idx]],
        y=[half_power, half_power],
        mode='markers+lines',
        marker=dict(size=8, color='orange'),
        line=dict(color='orange', width=2, dash='dash'),
        name=f'波束宽度: {beamwidth:.1f}°',
        hovertemplate='角度: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
    ),
    row=1, col=2
)

# 标记副瓣
if sidelobes:
    for i, (angle, gain) in enumerate(sidelobes[:2]):
        fig.add_trace(
            go.Scatter(
                x=[angle],
                y=[gain],
                mode='markers+text',
                marker=dict(size=8, color='green', symbol='triangle-up'),
                text=[f'副瓣{i+1}'],
                textposition="top center",
                showlegend=False,
                hovertemplate='角度: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
            ),
            row=1, col=2
        )

# 显示目标
if show_target:
    target_gain = calculate_array_factor_cached(
        X, Y, Z, weighted_phase_shift, target_theta, phi, wavelength
    )
    target_gain_db = 20 * np.log10(target_gain + 1e-10)
    
    fig.add_trace(
        go.Scatter(
            x=[target_theta],
            y=[target_gain_db],
            mode='markers+text',
            marker=dict(size=15, color='purple', symbol='x'),
            text=['目标'],
            textposition="top center",
            name='目标',
            hovertemplate='目标角度: %{x:.1f}°<br>接收增益: %{y:.2f} dB<extra></extra>'
        ),
        row=1, col=2
    )

fig.update_xaxes(title_text="俯仰角 (度)", row=1, col=2, range=[-90, 90])
fig.update_yaxes(title_text="增益 (dB)", row=1, col=2)

# 3. 加权系数（热图）
fig.add_trace(
    go.Heatmap(
        z=weights,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="加权系数", x=1.02, len=0.7),
        hovertemplate='X: %{x}<br>Y: %{y}<br>权重: %{z:.3f}<extra></extra>',
        name='加权系数'
    ),
    row=2, col=1
)

fig.update_xaxes(title_text="X 阵元", row=2, col=1, tickmode='linear', dtick=4)
fig.update_yaxes(title_text="Y 阵元", row=2, col=1, tickmode='linear', dtick=4)

# 4. 方位角方向图
fig.add_trace(
    go.Scatter(
        x=phi_range,
        y=pattern_azimuth,
        mode='lines',
        line=dict(color='green', width=3),
        name='方位方向图',
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)',
        hovertemplate='方位角: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
    ),
    row=2, col=2
)

# 标记主瓣方向
azimuth_mainlobe_gain = calculate_array_factor_cached(
    X, Y, Z, weighted_phase_shift, theta, phi, wavelength
)
azimuth_mainlobe_gain_db = 20 * np.log10(azimuth_mainlobe_gain + 1e-10)

fig.add_trace(
    go.Scatter(
        x=[phi],
        y=[azimuth_mainlobe_gain_db],
        mode='markers+text',
        marker=dict(size=10, color='red'),
        text=['主瓣'],
        textposition="top center",
        showlegend=False,
        hovertemplate='方位角: %{x:.1f}°<br>增益: %{y:.2f} dB<extra></extra>'
    ),
    row=2, col=2
)

fig.update_xaxes(title_text="方位角 (度)", row=2, col=2, range=[-180, 180])
fig.update_yaxes(title_text="增益 (dB)", row=2, col=2)

# 更新布局
fig.update_layout(
    height=900,
    showlegend=True,
    template='plotly_dark',
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02
    ),
    margin=dict(l=50, r=50, t=50, b=50)
)

# 显示图表
st.plotly_chart(fig, width='stretch')

# --- 性能指标 ---
st.header("📊 性能指标")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="主瓣增益",
        value=f"{mainlobe_gain:.2f} dB",
        delta=f"角度: {theta}°"
    )

with col2:
    st.metric(
        label="波束宽度",
        value=f"{beamwidth:.2f}°",
        help="-3dB 波束宽度"
    )

with col3:
    st.metric(
        label="扫描损失",
        value=f"{scan_loss:.2f} dB",
        help="由于波束扫描引起的增益损失"
    )

with col4:
    st.metric(
        label="工作波长",
        value=f"{wavelength*100:.2f} cm",
        delta=f"频率: {frequency} GHz"
    )

with col5:
    st.metric(
        label="阵元总数",
        value=f"{N*M}",
        delta=f"({N}×{M})"
    )

# 副瓣信息
if sidelobes:
    st.subheader("副瓣信息")
    for i, (angle, gain) in enumerate(sidelobes):
        st.info(f"副瓣{i+1}: {gain:.2f} dB @ {angle:.1f}° (比主瓣低{mainlobe_gain-gain:.2f} dB)")

# --- 实时动画仿真 ---
if animate:
    st.header("🎬 实时波束扫描仿真")
    
    # 创建动画图表
    if scan_mode == "线性扫描":
        theta_range_anim = np.linspace(-30, 30, 60)
        
        frames = []
        for t in theta_range_anim:
            phase = calculate_phase_shift_cached(t, phi, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, theta_range, phi_fixed=phi
            )
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=theta_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='blue', width=2)
                    ),
                    go.Scatter(
                        x=[t],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=10, color='red', symbol='star')
                    )
                ],
                name=f"θ={t:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title="俯仰角线性扫描",
            xaxis_title="俯仰角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                x=0.1,
                y=1.15,
                buttons=[
                    dict(
                        label="▶️ 播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}, "fromcurrent": True}]
                    ),
                    dict(
                        label="⏸️ 暂停",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]
                    )
                ]
            )],
            sliders=[dict(
                steps=[
                    dict(
                        args=[[f.name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                        label=f"{t:.1f}°",
                        method="animate"
                    )
                    for f, t in zip(frames, theta_range_anim)
                ],
                x=0.1,
                y=0,
                len=0.9,
                xanchor="left",
                yanchor="top",
                active=0,
            )],
            template='plotly_dark'
        )
        
    elif scan_mode == "圆形扫描":
        phi_range_anim = np.linspace(0, 360, 60)
        
        frames = []
        for p in phi_range_anim:
            phase = calculate_phase_shift_cached(theta, p, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, phi_range, theta
            )
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=phi_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='green', width=2)
                    ),
                    go.Scatter(
                        x=[p],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=10, color='red', symbol='star')
                    )
                ],
                name=f"φ={p:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title="方位角圆形扫描",
            xaxis_title="方位角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="暂停", method="animate", args=[[None]])
                ]
            )],
            template='plotly_dark'
        )
        
    elif scan_mode == "螺旋扫描":
        n_frames = 60
        frames = []
        
        for i in range(n_frames):
            t = -20 + 40 * i / n_frames
            p = 360 * i / n_frames
            
            phase = calculate_phase_shift_cached(t, p, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, theta_range, phi_fixed=p
            )
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=theta_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='purple', width=2)
                    ),
                    go.Scatter(
                        x=[t],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=10, color='red', symbol='star')
                    )
                ],
                name=f"θ={t:.1f}°, φ={p:.1f}°"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title="螺旋扫描",
            xaxis_title="俯仰角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="暂停", method="animate", args=[[None]])
                ]
            )],
            template='plotly_dark'
        )
    
    elif scan_mode == "跟踪目标" and show_target:
        # 目标跟踪仿真
        scan_range = 20
        n_frames = 30
        frames = []
        
        for i in range(n_frames):
            # 在目标周围小范围扫描
            offset = scan_range * np.sin(2 * np.pi * i / n_frames)
            current_theta = target_theta + offset
            current_phi = target_phi + offset
            
            phase = calculate_phase_shift_cached(current_theta, current_phi, X, Y, Z, wavelength)
            weighted_phase = phase * weights
            pattern = calculate_radiation_pattern_cached(
                X, Y, Z, weighted_phase, wavelength, theta_range, phi_fixed=current_phi
            )
            
            # 计算目标增益
            target_current_gain = calculate_array_factor_cached(
                X, Y, Z, weighted_phase_shift, target_theta, target_phi, wavelength
            )
            target_current_gain_db = 20 * np.log10(target_current_gain + 1e-10)
            
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=theta_range,
                        y=pattern,
                        mode='lines',
                        line=dict(color='orange', width=2)
                    ),
                    go.Scatter(
                        x=[current_theta],
                        y=[np.max(pattern)],
                        mode='markers',
                        marker=dict(size=10, color='red', symbol='star'),
                        name='波束指向'
                    ),
                    go.Scatter(
                        x=[target_theta],
                        y=[target_current_gain_db],
                        mode='markers',
                        marker=dict(size=12, color='purple', symbol='x'),
                        name='目标'
                    )
                ],
                name=f"帧 {i+1}"
            ))
        
        fig_anim = go.Figure(
            data=[frames[0].data[0], frames[0].data[1], frames[0].data[2]],
            frames=frames
        )
        
        fig_anim.update_layout(
            title="目标跟踪扫描",
            xaxis_title="俯仰角 (度)",
            yaxis_title="增益 (dB)",
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="播放",
                        method="animate",
                        args=[None, {"frame": {"duration": 1000//speed, "redraw": True}}]
                    ),
                    dict(label="暂停", method="animate", args=[[None]])
                ]
            )],
            template='plotly_dark'
        )
    
    st.plotly_chart(fig_anim, width='stretch')

# --- 技术说明 ---
with st.expander("📖 技术说明"):
    st.markdown("""
### 相控阵雷达原理

相控阵雷达通过控制每个阵元的相位来改变波束方向，而不需要机械转动。

**核心公式：**

1. **相位偏移计算：**
$$
Δφ = k · (u·x + v·y + w·z)
$$
其中 k = 2π/λ 是波数，(u, v, w) 是方向向量。

2. **阵列因子：**
$$
AF(θ, φ) = Σ w_n exp[j(k·(u·x_n + v·y_n + w·z_n) - Δφ_n)]
$$
其中 w_n 是阵元加权系数。

3. **波束扫描：**
通过调整相位偏移 Δφ，可以实现波束在空间中的扫描。

4. **扫描损失：**
$$
L_scan = 20·log₁₀(cos(θ_scan))
$$
其中 θ_scan 是波束扫描角度。

**波束赋形技术：**

- **均匀加权**：所有阵元等权重，主瓣最窄但副瓣最高
- **切比雪夫加权**：在给定副瓣电平下获得最窄主瓣
- **泰勒加权**：优化副瓣包络，适用于大阵列
- **汉明加权**：降低第一副瓣，主瓣稍有展宽

**Ku波段特点：**
- 频率范围：12-18 GHz
- 波长范围：1.67-2.5 cm
- 应用：卫星通信、雷达、气象探测

**32×32阵列优势：**
- 高增益（约30 dB）
- 窄波束宽度（约3-5°）
- 快速波束扫描能力
- 多波束形成能力
""")

# --- 使用说明 ---
with st.expander("🎮 使用说明"):
    st.markdown("""
1. **基本参数设置**：
   - 调整左侧的工作频率（12-18 GHz）
   - 设置波束指向的俯仰角和方位角
   - 调整阵元间距（建议0.5λ以避免栅瓣）

2. **波束赋形设置**：
   - 选择不同的加权函数控制副瓣电平
   - 切比雪夫加权可指定目标副瓣电平
   - 观察不同加权对波束形状的影响

3. **目标模拟**：
   - 启用"显示目标"选项
   - 设置目标的位置和雷达截面积
   - 观察波束对目标的响应

4. **仿真控制**：
   - 启用动画仿真观察波束扫描
   - 选择不同的扫描模式
   - 调整动画播放速度

5. **高级设置**：
   - 显示栅瓣位置
   - 显示零点位置
   - 调整角度分辨率

**交互操作：**
- 鼠标悬停在图表上查看详细数据
- 使用滑块调整参数
- 点击动画播放按钮启动仿真
- 查看性能指标和副瓣信息
""")

# --- 雷达方程计算 ---
with st.expander("📐 雷达方程计算"):
    st.markdown("""
### 雷达方程
    
雷达方程用于估计雷达的探测性能：
""")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transmit_power = st.number_input("发射功率 (W)", 100.0, 10000.0, 1000.0, 100.0)
        antenna_gain = st.number_input("天线增益 (dB)", 20.0, 50.0, 30.0, 1.0)
        frequency_input = st.number_input("频率 (GHz)", 12.0, 18.0, 14.0, 0.1)
    
    with col2:
        target_rcs_input = st.number_input("目标RCS (m²)", 0.1, 100.0, 1.0, 0.1)
        target_range_input = st.number_input("目标距离 (km)", 1.0, 1000.0, 10.0, 1.0)
        noise_figure = st.number_input("噪声系数 (dB)", 1.0, 10.0, 3.0, 0.5)
    
    if st.button("计算雷达性能"):
        # 转换为线性值
        G_linear = 10**(antenna_gain/10)
        RCS_linear = target_rcs_input
        R = target_range_input * 1000  # 转换为米
        wavelength_calc = 3e8 / (frequency_input * 1e9)
        
        # 雷达方程
        received_power = (transmit_power * G_linear**2 * wavelength_calc**2 * RCS_linear) / ((4 * np.pi)**3 * R**4)
        received_power_dBm = 10 * np.log10(received_power * 1000)  # 转换为dBm
        
        # 热噪声
        T0 = 290  # 标准温度 (K)
        k = 1.38e-23  # 玻尔兹曼常数
        B = 10e6  # 带宽 10MHz
        
        noise_power = k * T0 * B * 10**(noise_figure/10)
        noise_power_dBm = 10 * np.log10(noise_power * 1000)
        
        SNR = received_power_dBm - noise_power_dBm
        
        col3, col4, col5 = st.columns(3)
        with col3:
            st.metric("接收功率", f"{received_power_dBm:.2f} dBm")
        with col4:
            st.metric("噪声功率", f"{noise_power_dBm:.2f} dBm")
        with col5:
            st.metric("信噪比", f"{SNR:.2f} dB", 
                     delta="良好" if SNR > 10 else "临界" if SNR > 0 else "不足",
                     delta_color="normal" if SNR > 10 else "off" if SNR > 0 else "inverse")

st.markdown("---")
st.markdown("💡 **提示**：调整左侧参数后，图表会实时更新。启用动画可以观察波束扫描过程。")
