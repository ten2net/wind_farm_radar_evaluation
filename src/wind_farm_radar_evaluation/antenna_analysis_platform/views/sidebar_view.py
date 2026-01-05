"""
侧边栏视图 - 重新设计
Streamlit应用的侧边栏控制面板
采用模块化设计，功能更完善
"""

from enum import Enum
import streamlit as st
from typing import Dict, Any, Optional, List, Tuple, Callable
import yaml
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.antenna_models import (
    AntennaParameters, AntennaType, PolarizationType, 
    FeedType, MaterialProperties, Substrate, Element,
    AntennaGeometry, FeedNetwork, ANTENNA_TEMPLATES,
    PREDEFINED_MATERIALS, create_dipole_antenna, create_patch_antenna
)
from models.pattern_models import PatternComponent
from services.pattern_generator import get_pattern_generator_service
from services.analysis_service import get_analysis_service
from services.visualization_service import get_visualization_service
from utils.config import AppConfig
# from utils.helpers import validate_frequency_range, format_frequency

# ============================================================================
# 工具函数
# ============================================================================

def load_antenna_database() -> Dict[str, Any]:
    """加载天线数据库"""
    try:
        config = AppConfig()
        data_file = config.get_data_path("antennas.yaml")
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {'antennas': []}
        
        # 创建默认数据库
        default_data = {
            'antennas': [
                {
                    'name': '半波偶极子天线',
                    'type': 'dipole',
                    'frequency': 1.0,
                    'gain': 2.15,
                    'description': '基本的半波偶极子天线，用于教学演示'
                },
                {
                    'name': '2.4GHz微带贴片天线',
                    'type': 'patch',
                    'frequency': 2.45,
                    'gain': 7.0,
                    'description': 'WiFi频段微带贴片天线'
                },
                {
                    'name': 'X波段喇叭天线',
                    'type': 'horn',
                    'frequency': 10.0,
                    'gain': 20.0,
                    'description': 'X波段标准增益喇叭天线'
                }
            ],
            'materials': [
                {'name': 'FR4', 'er': 4.4, 'loss_tangent': 0.02},
                {'name': 'Rogers RO4350B', 'er': 3.48, 'loss_tangent': 0.0037},
                {'name': 'PTFE', 'er': 2.1, 'loss_tangent': 0.0004}
            ]
        }
        
        data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_data, f, allow_unicode=True, default_flow_style=False)
        
        return default_data
        
    except Exception as e:
        st.error(f"加载天线数据库失败: {e}")
        return {'antennas': [], 'materials': []}

def save_antenna_to_database(antenna_params: Dict[str, Any]) -> bool:
    """保存天线到数据库"""
    try:
        config = AppConfig()
        data_file = config.get_data_path("antennas.yaml")
        
        database = load_antenna_database()
        
        # 添加或更新天线
        existing_idx = -1
        for i, antenna in enumerate(database['antennas']):
            if antenna.get('name') == antenna_params['name']:
                existing_idx = i
                break
        
        if existing_idx >= 0:
            database['antennas'][existing_idx] = antenna_params
        else:
            database['antennas'].append(antenna_params)
        
        # 保存数据库
        with open(data_file, 'w', encoding='utf-8') as f:
            yaml.dump(database, f, allow_unicode=True, default_flow_style=False)
        
        return True
    except Exception as e:
        st.error(f"保存天线失败: {e}")
        return False

# ============================================================================
# 天线选择模块
# ============================================================================

class AntennaSelector:
    """天线选择器"""
    
    @staticmethod
    def render() -> Dict[str, Any]:
        """渲染天线选择界面"""
        st.markdown("### 📡 天线配置")
        
        # 选择天线来源
        source = st.radio(
            "天线来源",
            ["🏗️ 模板天线", "🗃️ 数据库天线", "⚙️ 自定义天线"],
            horizontal=True,
            help="选择天线定义方式"
        )
        
        antenna_data = {}
        
        if "模板天线" in source:
            antenna_data = AntennaSelector._render_template_selection()
        elif "数据库天线" in source:
            antenna_data = AntennaSelector._render_database_selection()
        else:
            antenna_data = AntennaSelector._render_custom_antenna()
        
        return {
            'source': source,
            'data': antenna_data
        }
    
    @staticmethod
    def _render_template_selection() -> Dict[str, Any]:
        """渲染模板天线选择"""
        templates = {
            "半波偶极子": create_dipole_antenna(),
            "微带贴片天线": create_patch_antenna(),
            "喇叭天线 (模拟)": AntennaSelector._create_horn_template(),
            "抛物面天线 (模拟)": AntennaSelector._create_parabolic_template()
        }
        
        selected = st.selectbox(
            "选择天线模板",
            list(templates.keys()),
            format_func=lambda x: f"{x} - {templates[x].description[:30]}..."
        )
        
        antenna = templates[selected]

        # 允许参数调整
        with st.expander("🔧 调整参数", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                antenna.center_frequency = st.number_input(
                    "中心频率 (GHz)",
                    value=antenna.center_frequency,
                    min_value=0.1,
                    max_value=100.0,
                    step=0.1,
                    format="%.2f"
                )
                antenna.gain = st.number_input(
                    "增益 (dBi)",
                    value=antenna.gain,
                    min_value=-10.0,
                    max_value=50.0,
                    step=0.1
                )
            
            with col2:
                antenna.beamwidth_e = st.number_input(
                    "E面波束宽度 (°)",
                    value=antenna.beamwidth_e,
                    min_value=1.0,
                    max_value=180.0,
                    step=1.0
                )
                antenna.beamwidth_h = st.number_input(
                    "H面波束宽度 (°)",
                    value=antenna.beamwidth_h,
                    min_value=1.0,
                    max_value=180.0,
                    step=1.0
                )
        
        return antenna.to_dict()
    
    @staticmethod
    def _render_database_selection() -> Dict[str, Any]:
        """渲染数据库天线选择"""
        database = load_antenna_database()
        antennas = database.get('antennas', [])
        
        if not antennas:
            st.info("数据库为空，请先创建自定义天线")
            return {}
        
        antenna_names = [f"{a.get('name', '未命名')} - {a.get('type', '未知')}" 
                        for a in antennas]
        
        selected = st.selectbox("选择天线", antenna_names)
        
        # 找到选中的天线
        selected_idx = antenna_names.index(selected)
        antenna_data = antennas[selected_idx]
        
        # 显示天线信息
        with st.expander("📋 天线详情", expanded=False):
            st.json(antenna_data, expanded=False)
        
        return antenna_data
    
    @staticmethod
    def _render_custom_antenna() -> Dict[str, Any]:
        """渲染自定义天线配置"""
        tab1, tab2, tab3 = st.tabs(["基本参数", "几何结构", "材料与馈电"])
        
        antenna_params = {}
        
        with tab1:
            antenna_params.update(AntennaSelector._render_basic_parameters())
        
        with tab2:
            antenna_params.update(AntennaSelector._render_geometry_parameters())
        
        with tab3:
            antenna_params.update(AntennaSelector._render_material_feed_parameters())
        
        return antenna_params
    
    @staticmethod
    def _render_basic_parameters() -> Dict[str, Any]:
        """渲染基本参数"""
        st.markdown("#### 基本参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("天线名称", value="自定义天线")
            antenna_type = st.selectbox(
                "天线类型",
                [t.value for t in AntennaType],
                format_func=lambda x: x.replace('_', ' ').title(),
                index=1
            )
            center_freq = st.number_input(
                "中心频率 (GHz)",
                value=2.45,
                min_value=0.1,
                max_value=100.0,
                step=0.1
            )
        
        with col2:
            gain = st.number_input("增益 (dBi)", value=10.0, min_value=-10.0, max_value=50.0)
            bandwidth = st.number_input("带宽 (%)", value=10.0, min_value=0.1, max_value=200.0)
            vswr = st.number_input("VSWR", value=1.5, min_value=1.0, max_value=10.0, step=0.1)
        
        # 频率范围
        freq_low = st.number_input("最低频率 (GHz)", value=center_freq * 0.9, min_value=0.1)
        freq_high = st.number_input("最高频率 (GHz)", value=center_freq * 1.1, min_value=0.1)
        
        # 极化类型
        polarization = st.selectbox(
            "极化类型",
            [p.value for p in PolarizationType],
            format_func=lambda x: x.replace('_', ' ').title(),
            index=0
        )
        
        return {
            'name': name,
            'antenna_type': antenna_type,
            'center_frequency': center_freq,
            'frequency_range': [float(freq_low), float(freq_high)],
            'gain': float(gain),
            'bandwidth': float(bandwidth),
            'vswr': float(vswr),
            'polarization': polarization
        }
    
    @staticmethod
    def _render_geometry_parameters() -> Dict[str, Any]:
        """渲染几何参数"""
        st.markdown("#### 几何参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            beamwidth_e = st.number_input("E面波束宽度 (°)", value=60.0, min_value=1.0, max_value=180.0)
            sidelobe_level = st.number_input("副瓣电平 (dB)", value=-20.0, max_value=0.0, min_value=-60.0)
        
        with col2:
            beamwidth_h = st.number_input("H面波束宽度 (°)", value=60.0, min_value=1.0, max_value=180.0)
            front_to_back = st.number_input("前后比 (dB)", value=20.0, min_value=0.0, max_value=60.0)
        
        # 阵列参数
        is_array = st.checkbox("启用阵列配置", value=False)
        array_params = {}
        
        if is_array:
            st.markdown("##### 阵列参数")
            col1, col2, col3 = st.columns(3)
            with col1:
                rows = st.number_input("行数", value=2, min_value=1, max_value=16)
            with col2:
                cols = st.number_input("列数", value=2, min_value=1, max_value=16)
            with col3:
                spacing = st.number_input("间距 (mm)", value=150.0, min_value=10.0, max_value=1000.0)
            
            array_params = {
                'is_array': True,
                'rows': int(rows),
                'columns': int(cols),
                'spacing': float(spacing)
            }
        
        geometry_params = {
            'beamwidth_e': float(beamwidth_e),
            'beamwidth_h': float(beamwidth_h),
            'sidelobe_level': float(sidelobe_level),
            'front_to_back_ratio': float(front_to_back)
        }
        
        if array_params:
            geometry_params.update(array_params)
        
        return geometry_params
    
    @staticmethod
    def _render_material_feed_parameters() -> Dict[str, Any]:
        """渲染材料和馈电参数"""
        st.markdown("#### 材料与馈电")
        
        # 基板材料
        st.markdown("##### 基板材料")
        material_options = list(PREDEFINED_MATERIALS.keys())
        selected_material = st.selectbox("选择材料", material_options)
        
        material = PREDEFINED_MATERIALS[selected_material]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            substrate_height = st.number_input("基板厚度 (mm)", value=material.thickness, 
                                              min_value=0.1, max_value=10.0)
        with col2:
            substrate_width = st.number_input("基板宽度 (mm)", value=50.0, min_value=1.0, max_value=500.0)
        with col3:
            substrate_length = st.number_input("基板长度 (mm)", value=50.0, min_value=1.0, max_value=500.0)
        
        # 馈电参数
        st.markdown("##### 馈电网络")
        feed_type = st.selectbox(
            "馈电类型",
            [f.value for f in FeedType],
            format_func=lambda x: x.replace('_', ' ').title(),
            index=0
        )
        
        feed_impedance = st.number_input("特性阻抗 (Ω)", value=50.0, min_value=1.0, max_value=300.0)
        
        # 效率参数
        st.markdown("##### 效率参数")
        col1, col2 = st.columns(2)
        with col1:
            efficiency = st.slider("辐射效率", 0.0, 1.0, 0.8, 0.01)
        with col2:
            input_power = st.number_input("输入功率 (W)", value=1.0, min_value=0.1, max_value=1000.0)
        
        return {
            'material': {
                'name': material.name,
                'dielectric_constant': material.dielectric_constant,
                'loss_tangent': material.loss_tangent,
                'thickness': float(substrate_height)
            },
            'substrate_dimensions': {
                'width': float(substrate_width),
                'length': float(substrate_length),
                'height': float(substrate_height)
            },
            'feed_network': {
                'type': feed_type,
                'impedance': float(feed_impedance)
            },
            'efficiency': float(efficiency),
            'input_power': float(input_power)
        }
    
    @staticmethod
    def _create_horn_template() -> AntennaParameters:
        """创建喇叭天线模板"""
        geometry = AntennaGeometry()
        feed_network = FeedNetwork(type=FeedType.WAVEGUIDE, impedance=50.0)
        
        return AntennaParameters(
            name="标准喇叭天线",
            antenna_type=AntennaType.HORN,
            frequency_range=(8.0, 12.0),
            center_frequency=10.0,
            gain=20.0,
            bandwidth=20.0,
            vswr=1.2,
            polarization=PolarizationType.LINEAR_VERTICAL,
            geometry=geometry,
            feed_network=feed_network,
            beamwidth_e=15.0,
            beamwidth_h=15.0,
            sidelobe_level=-25.0,
            front_to_back_ratio=40.0,
            efficiency=0.9,
            description="X波段标准增益喇叭天线，10GHz工作频率"
        )
    
    @staticmethod
    def _create_parabolic_template() -> AntennaParameters:
        """创建抛物面天线模板"""
        geometry = AntennaGeometry()
        feed_network = FeedNetwork(type=FeedType.WAVEGUIDE, impedance=50.0)
        
        return AntennaParameters(
            name="抛物面天线",
            antenna_type=AntennaType.PARABOLIC,
            frequency_range=(4.0, 6.0),
            center_frequency=5.0,
            gain=30.0,
            bandwidth=10.0,
            vswr=1.3,
            polarization=PolarizationType.LINEAR_HORIZONTAL,
            geometry=geometry,
            feed_network=feed_network,
            beamwidth_e=5.0,
            beamwidth_h=5.0,
            sidelobe_level=-20.0,
            front_to_back_ratio=60.0,
            efficiency=0.7,
            description="C波段抛物面天线，直径1.2米"
        )

# ============================================================================
# 仿真设置模块
# ============================================================================

class SimulationSettings:
    """仿真设置"""
    
    @staticmethod
    def render() -> Dict[str, Any]:
        """渲染仿真设置界面"""
        st.markdown("### ⚙️ 仿真设置")
        
        tab1, tab2 = st.tabs(["基本设置", "高级设置"])
        
        settings = {}
        
        with tab1:
            settings.update(SimulationSettings._render_basic_settings())
        
        with tab2:
            settings.update(SimulationSettings._render_advanced_settings())
        
        return settings
    
    @staticmethod
    def _render_basic_settings() -> Dict[str, Any]:
        """渲染基本设置"""
        col1, col2 = st.columns(2)
        
        with col1:
            # 方向图生成器
            generator_service = get_pattern_generator_service()
            generators = generator_service.get_available_generators()
            
            generator_map = {
                'analytical': '📊 解析法',
                'numerical': '🧮 数值法', 
                'radarsimpy': '🛰️ Radarsimpy'
            }
            
            generator_options = [generator_map.get(g, g) for g in generators]
            generator_selected = st.selectbox(
                "方向图生成器",
                generator_options,
                help="选择方向图生成算法"
            )
            
            generator_type = [k for k, v in generator_map.items() if v == generator_selected][0]
            
            # 分辨率设置
            theta_res = st.slider(
                "Theta分辨率 (°)",
                min_value=1,
                max_value=20,
                value=5,
                help="俯仰角方向采样分辨率"
            )
        
        with col2:
            # 角度范围
            phi_res = st.slider(
                "Phi分辨率 (°)",
                min_value=1,
                max_value=20,
                value=5,
                help="方位角方向采样分辨率"
            )
            
            # 方向图组件
            component_options = {
                '总场': 'total',
                'Theta分量': 'theta', 
                'Phi分量': 'phi',
                '同极化': 'co_polar',
                '交叉极化': 'cross_polar'
            }
            
            component_selected = st.selectbox(
                "场分量",
                list(component_options.keys()),
                index=0
            )
            component = component_options[component_selected]
        
        return {
            'generator_type': generator_type,
            'theta_resolution': theta_res,
            'phi_resolution': phi_res,
            'component': component
        }
    
    @staticmethod
    def _render_advanced_settings() -> Dict[str, Any]:
        """渲染高级设置"""
        st.markdown("##### 高级仿真参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_cache = st.checkbox("启用缓存", value=True, 
                                   help="缓存仿真结果以提高性能")
            normalize = st.checkbox("归一化方向图", value=True,
                                   help="将方向图归一化到峰值增益")
            add_noise = st.checkbox("添加噪声", value=False,
                                   help="在方向图中添加随机噪声模拟测量误差")
        
        with col2:
            interpolation = st.checkbox("启用插值", value=True,
                                       help="对方向图进行插值以获得平滑结果")
            interpolation_factor = st.slider("插值因子", 1, 5, 2,
                                           disabled=not interpolation)
            save_raw_data = st.checkbox("保存原始数据", value=False,
                                       help="保存仿真的原始场数据")
        
        # 噪声参数
        noise_params = {}
        if add_noise:
            with st.expander("噪声参数", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    noise_level = st.slider("噪声水平 (dB)", -50, -10, -30)
                with col2:
                    noise_type = st.selectbox("噪声类型", ["高斯", "均匀", "相位噪声"])
        
        return {
            'advanced': {
                'use_cache': use_cache,
                'normalize': normalize,
                'add_noise': add_noise,
                'noise_level': noise_level if add_noise else -30,
                'noise_type': noise_type if add_noise else '高斯',
                'interpolation': interpolation,
                'interpolation_factor': interpolation_factor if interpolation else 1,
                'save_raw_data': save_raw_data
            }
        }

# ============================================================================
# 分析设置模块
# ============================================================================

class AnalysisSettings:
    """分析设置"""
    
    @staticmethod
    def render() -> Dict[str, Any]:
        """渲染分析设置界面"""
        st.markdown("### 📊 分析设置")
        
        # 分析类型选择
        analysis_types = st.multiselect(
            "选择分析类型",
            ["波束特性", "极化特性", "效率分析", "频域分析", "比较分析"],
            default=["波束特性", "极化特性"],
            help="选择要执行的分析类型"
        )
        
        settings = {
            'analysis_types': analysis_types,
            'beam_analysis': {},
            'polarization_analysis': {},
            'efficiency_analysis': {},
            'frequency_analysis': {},
            'comparison_analysis': {}
        }
        
        # 波束特性分析设置
        if "波束特性" in analysis_types:
            with st.expander("⚡ 波束分析设置", expanded=True):
                settings['beam_analysis'] = AnalysisSettings._render_beam_analysis()
        
        # 极化特性分析设置
        if "极化特性" in analysis_types:
            with st.expander("🔄 极化分析设置", expanded=True):
                settings['polarization_analysis'] = AnalysisSettings._render_polarization_analysis()
        
        # 效率分析设置
        if "效率分析" in analysis_types:
            with st.expander("📈 效率分析设置", expanded=True):
                settings['efficiency_analysis'] = AnalysisSettings._render_efficiency_analysis()
        
        # 频域分析设置
        if "频域分析" in analysis_types:
            with st.expander("📡 频域分析设置", expanded=True):
                settings['frequency_analysis'] = AnalysisSettings._render_frequency_analysis()
        
        # 比较分析设置
        if "比较分析" in analysis_types:
            with st.expander("⚖️ 比较分析设置", expanded=True):
                settings['comparison_analysis'] = AnalysisSettings._render_comparison_analysis()
        
        return settings
    
    @staticmethod
    def _render_beam_analysis() -> Dict[str, Any]:
        """渲染波束分析设置"""
        col1, col2 = st.columns(2)
        
        with col1:
            beamwidth_levels = st.multiselect(
                "波束宽度计算",
                ["3dB", "6dB", "10dB", "20dB"],
                default=["3dB", "10dB"]
            )
            
            find_nulls = st.checkbox("查找零陷", value=True)
            analyze_symmetry = st.checkbox("分析对称性", value=True)
        
        with col2:
            calculate_beamshape = st.checkbox("计算波束形状", value=True)
            sidelobe_analysis = st.checkbox("副瓣分析", value=True)
            if sidelobe_analysis:
                num_sidelobes = st.number_input("分析副瓣数量", 1, 10, 3)
        
        return {
            'beamwidth_levels': [int(level.replace('dB', '')) for level in beamwidth_levels],
            'find_nulls': find_nulls,
            'analyze_symmetry': analyze_symmetry,
            'calculate_beamshape': calculate_beamshape,
            'sidelobe_analysis': sidelobe_analysis,
            'num_sidelobes': num_sidelobes if sidelobe_analysis else 3
        }
    
    @staticmethod
    def _render_polarization_analysis() -> Dict[str, Any]:
        """渲染极化分析设置"""
        col1, col2 = st.columns(2)
        
        with col1:
            calculate_axial_ratio = st.checkbox("计算轴比", value=True)
            if calculate_axial_ratio:
                ar_threshold = st.number_input("轴比阈值 (dB)", 0.1, 20.0, 3.0)
            
            calculate_xpd = st.checkbox("交叉极化鉴别度", value=True)
        
        with col2:
            polarization_purity = st.checkbox("极化纯度", value=True)
            ellipse_analysis = st.checkbox("极化椭圆分析", value=True)
            tilt_angle_analysis = st.checkbox("倾角分析", value=True)
        
        return {
            'calculate_axial_ratio': calculate_axial_ratio,
            'ar_threshold': ar_threshold if calculate_axial_ratio else 3.0,
            'calculate_xpd': calculate_xpd,
            'polarization_purity': polarization_purity,
            'ellipse_analysis': ellipse_analysis,
            'tilt_angle_analysis': tilt_angle_analysis
        }
    
    @staticmethod
    def _render_efficiency_analysis() -> Dict[str, Any]:
        """渲染效率分析设置"""
        col1, col2 = st.columns(2)
        
        with col1:
            radiation_efficiency = st.checkbox("辐射效率", value=True)
            aperture_efficiency = st.checkbox("孔径效率", value=True)
            beam_efficiency = st.checkbox("波束效率", value=True)
        
        with col2:
            total_efficiency = st.checkbox("总效率", value=True)
            if total_efficiency:
                include_losses = st.checkbox("包含损耗", value=True)
            
            matching_efficiency = st.checkbox("匹配效率", value=False)
        
        return {
            'radiation_efficiency': radiation_efficiency,
            'aperture_efficiency': aperture_efficiency,
            'beam_efficiency': beam_efficiency,
            'total_efficiency': total_efficiency,
            'include_losses': include_losses if total_efficiency else False,
            'matching_efficiency': matching_efficiency
        }
    
    @staticmethod
    def _render_frequency_analysis() -> Dict[str, Any]:
        """渲染频域分析设置"""
        col1, col2 = st.columns(2)
        
        with col1:
            freq_start = st.number_input("起始频率 (GHz)", 0.1, 100.0, 2.0)
            freq_steps = st.number_input("频率点数", 2, 20, 5)
        
        with col2:
            freq_end = st.number_input("结束频率 (GHz)", 0.1, 100.0, 3.0)
            sweep_type = st.selectbox("扫频类型", ["线性", "对数"])
        
        bandwidth_analysis = st.checkbox("带宽分析", value=True)
        if bandwidth_analysis:
            bw_level = st.selectbox("带宽计算电平", ["-3dB", "-6dB", "-10dB"])
        
        return {
            'freq_start': freq_start,
            'freq_end': freq_end,
            'freq_steps': freq_steps,
            'sweep_type': sweep_type,
            'bandwidth_analysis': bandwidth_analysis,
            'bw_level': bw_level if bandwidth_analysis else "-3dB"
        }
    
    @staticmethod
    def _render_comparison_analysis() -> Dict[str, Any]:
        """渲染比较分析设置"""
        comparison_type = st.radio(
            "比较类型",
            ["不同天线", "不同参数", "不同频率", "与理论值"],
            horizontal=True
        )
        
        comparison_params = {'type': comparison_type}
        
        if comparison_type == "不同天线":
            num_antennas = st.number_input("天线数量", 2, 5, 2)
            comparison_params['num_antennas'] = num_antennas
            
        elif comparison_type == "不同参数":
            param_options = ["增益", "波束宽度", "副瓣电平", "效率"]
            selected_params = st.multiselect("比较参数", param_options, default=["增益"])
            comparison_params['parameters'] = selected_params
        
        elif comparison_type == "不同频率":
            freq_points = st.number_input("频率点数", 2, 10, 3)
            comparison_params['freq_points'] = freq_points
        
        else:  # 与理论值
            theory_model = st.selectbox("理论模型", ["各向同性", "偶极子", "抛物面"])
            comparison_params['theory_model'] = theory_model
        
        metrics = st.multiselect(
            "比较指标",
            ["增益", "波束宽度", "副瓣电平", "效率", "轴比"],
            default=["增益", "波束宽度"]
        )
        
        comparison_params['metrics'] = metrics
        
        return comparison_params

# ============================================================================
# 可视化设置模块
# ============================================================================

class VisualizationSettings:
    """可视化设置"""
    
    @staticmethod
    def render() -> Dict[str, Any]:
        """渲染可视化设置界面"""
        st.markdown("### 📈 可视化设置")
        
        tab1, tab2, tab3 = st.tabs(["图表类型", "显示设置", "导出设置"])
        
        settings = {}
        
        with tab1:
            settings.update(VisualizationSettings._render_chart_types())
        
        with tab2:
            settings.update(VisualizationSettings._render_display_settings())
        
        with tab3:
            settings.update(VisualizationSettings._render_export_settings())
        
        return settings
    
    @staticmethod
    def _render_chart_types() -> Dict[str, Any]:
        """渲染图表类型选择"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            chart_types = st.multiselect(
                "选择图表类型",
                [
                    "2D方向图 (直角坐标)",
                    "2D方向图 (极坐标)", 
                    "3D方向图",
                    "轴比分布图",
                    "极化椭圆图",
                    "参数统计图",
                    "频响曲线",
                    "波束轮廓图"
                ],
                default=["2D方向图 (直角坐标)", "3D方向图", "参数统计图"]
            )
        
        with col2:
            st.markdown("##### 平面选择")
            plane = st.radio(
                "2D方向图平面",
                ["E面 (Phi=0°)", "H面 (Theta=90°)", "自定义"],
                index=0
            )
            
            if plane == "自定义":
                fixed_angle = st.number_input("固定角度 (°)", 0.0, 360.0, 0.0)
            else:
                fixed_angle = 0.0 if "E面" in plane else 90.0
        
        # 3D设置
        three_d_settings = {}
        if "3D方向图" in chart_types:
            with st.expander("🎮 3D图设置", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    elevation = st.slider("视角俯仰", 0, 90, 30)
                    show_contour = st.checkbox("显示等高线", True)
                with col2:
                    azimuth = st.slider("视角方位", 0, 360, 45)
                    opacity = st.slider("透明度", 0.1, 1.0, 0.8)
                
                three_d_settings = {
                    'elevation': elevation,
                    'azimuth': azimuth,
                    'show_contour': show_contour,
                    'opacity': opacity
                }
        
        return {
            'chart_types': chart_types,
            'plane': plane,
            'fixed_angle': fixed_angle,
            'three_d_settings': three_d_settings
        }
    
    @staticmethod
    def _render_display_settings() -> Dict[str, Any]:
        """渲染显示设置"""
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox("主题风格", ["浅色", "深色", "科技蓝", "专业灰"])
            fig_width = st.number_input("图表宽度", 400, 2000, 800, 50)
            show_grid = st.checkbox("显示网格", True)
            show_legend = st.checkbox("显示图例", True)
        
        with col2:
            color_map = st.selectbox("颜色映射", 
                ["viridis", "plasma", "inferno", "coolwarm", "rainbow"])
            fig_height = st.number_input("图表高度", 300, 1500, 600, 50)
            show_title = st.checkbox("显示标题", True)
            show_colorbar = st.checkbox("显示颜色条", True)
        
        # 标注设置
        with st.expander("📝 标注设置", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                annotate_peaks = st.checkbox("标注峰值点", True)
                annotate_beamwidth = st.checkbox("标注波束宽度", True)
            with col2:
                annotate_sidelobes = st.checkbox("标注副瓣", True)
                font_size = st.slider("字体大小", 8, 20, 12)
        
        return {
            'display': {
                'theme': theme,
                'fig_width': fig_width,
                'fig_height': fig_height,
                'color_map': color_map,
                'show_grid': show_grid,
                'show_legend': show_legend,
                'show_title': show_title,
                'show_colorbar': show_colorbar,
                'annotate_peaks': annotate_peaks,
                'annotate_beamwidth': annotate_beamwidth,
                'annotate_sidelobes': annotate_sidelobes,
                'font_size': font_size
            }
        }
    
    @staticmethod
    def _render_export_settings() -> Dict[str, Any]:
        """渲染导出设置"""
        col1, col2 = st.columns(2)
        
        with col1:
            export_formats = st.multiselect(
                "导出格式",
                ["PNG", "PDF", "SVG", "HTML", "JSON", "CSV"],
                default=["PNG", "PDF"]
            )
            
            dpi = st.selectbox("导出DPI", [72, 150, 300, 600], index=1)
        
        with col2:
            export_scale = st.slider("导出缩放", 1.0, 5.0, 2.0, 0.5)
            transparent_bg = st.checkbox("透明背景", False)
            include_metadata = st.checkbox("包含元数据", True)
        
        # 导出选项
        export_options = {}
        if "PNG" in export_formats:
            export_options['png'] = {'dpi': dpi, 'transparent': transparent_bg}
        if "PDF" in export_formats:
            export_options['pdf'] = {'dpi': dpi}
        if "SVG" in export_formats:
            export_options['svg'] = {}
        if "HTML" in export_formats:
            export_options['html'] = {'include_plotlyjs': True}
        if "JSON" in export_formats:
            export_options['json'] = {'indent': 2}
        if "CSV" in export_formats:
            export_options['csv'] = {'index': False}
        
        return {
            'export': {
                'formats': export_formats,
                'options': export_options,
                'scale': export_scale,
                'include_metadata': include_metadata
            }
        }

# ============================================================================
# 控制面板模块
# ============================================================================

class ControlPanel:
    """控制面板"""
    
    @staticmethod
    def render() -> Dict[str, Any]:
        """渲染控制面板"""
        st.markdown("### 🎮 控制面板")
        
        col1, col2, col3 = st.columns(3)
        
        actions = {}
        
        with col1:
            if st.button("🚀 运行仿真", width='stretch', type="primary"):
                actions['run_simulation'] = True
                st.session_state.last_action = "run_simulation"
        
        with col2:
            if st.button("💾 保存配置", width='stretch'):
                actions['save_config'] = True
                st.session_state.last_action = "save_config"
        
        with col3:
            if st.button("📥 加载配置", width='stretch'):
                actions['load_config'] = True
                st.session_state.last_action = "load_config"
        
        # 第二行按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 重置", width='stretch'):
                actions['reset'] = True
                st.session_state.last_action = "reset"
        
        with col2:
            if st.button("🧹 清空缓存", width='stretch'):
                actions['clear_cache'] = True
                st.session_state.last_action = "clear_cache"
        
        with col3:
            if st.button("📋 生成报告", width='stretch'):
                actions['generate_report'] = True
                st.session_state.last_action = "generate_report"
        
        # 操作状态
        if 'last_action' in st.session_state:
            st.info(f"上次操作: {st.session_state.last_action}")
        
        return actions

# ============================================================================
# 状态面板模块
# ============================================================================

class StatusPanel:
    """状态面板"""
    
    @staticmethod
    def render():
        """渲染状态面板"""
        st.markdown("### 📈 状态信息")
        
        # 天线信息
        if 'current_antenna' in st.session_state and st.session_state.current_antenna:
            antenna = st.session_state.current_antenna
            StatusPanel._render_antenna_status(antenna)
        
        # 仿真状态
        if 'simulation_status' in st.session_state:
            StatusPanel._render_simulation_status()
        
        # 分析结果
        if 'analysis_results' in st.session_state and st.session_state.analysis_results:
            StatusPanel._render_analysis_status()
        
        # 系统信息
        StatusPanel._render_system_status()
    
    @staticmethod
    def _render_antenna_status(antenna):
            """渲染天线状态"""
            st.markdown("#### 📡 当前天线")
            
            col1, col2 = st.columns(2)
            with col1:
                # 使用getattr安全访问属性
                name = getattr(antenna, 'name', '未命名')
                antenna_type = getattr(antenna, 'antenna_type', '未知')
                
                # 如果是枚举类型，获取其值
                if isinstance(antenna_type, Enum):
                    antenna_type = antenna_type.value
                
                st.metric("名称", name)
                st.metric("类型", antenna_type)
            
            with col2:
                freq = getattr(antenna, 'center_frequency', 0)
                st.metric("频率", f"{freq:.2f} GHz")
                
                gain = getattr(antenna, 'gain', 0)
                st.metric("增益", f"{gain:.1f} dBi")
            
            # 添加更多信息
            st.markdown("#### 🔧 天线参数")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 频率范围
                freq_range = getattr(antenna, 'frequency_range', (0, 0))
                st.text(f"频率范围: {freq_range[0]:.2f}-{freq_range[1]:.2f} GHz")
                
                # 带宽
                bandwidth = getattr(antenna, 'bandwidth', 0)
                st.text(f"带宽: {bandwidth:.1f}%")
                
                # 极化
                polarization = getattr(antenna, 'polarization', '未知')
                if isinstance(polarization, Enum):
                    polarization = polarization.value
                st.text(f"极化: {polarization}")
            
            with col2:
                # 波束宽度
                beamwidth_e = getattr(antenna, 'beamwidth_e', 0)
                beamwidth_h = getattr(antenna, 'beamwidth_h', 0)
                st.text(f"E面波束宽度: {beamwidth_e:.1f}°")
                st.text(f"H面波束宽度: {beamwidth_h:.1f}°")
                
                # 副瓣电平
                sidelobe_level = getattr(antenna, 'sidelobe_level', 0)
                st.text(f"副瓣电平: {sidelobe_level:.1f} dB")
                
                # 效率
                efficiency = getattr(antenna, 'efficiency', 0)
                st.text(f"效率: {efficiency*100:.1f}%")
    
    @staticmethod
    def _render_simulation_status():
        """渲染仿真状态"""
        st.markdown("#### ⚙️ 仿真状态")
        
        status = st.session_state.simulation_status
        status_type = status.get('type', 'idle')
        message = status.get('message', '')
        
        if status_type == 'running':
            st.warning(f"🔄 {message}")
        elif status_type == 'completed':
            st.success(f"✅ {message}")
        elif status_type == 'error':
            st.error(f"❌ {message}")
        else:
            st.info("💤 等待仿真")
        
        # 进度条
        if 'progress' in status:
            progress = status['progress']
            st.progress(progress)
            st.caption(f"进度: {progress*100:.1f}%")
    
    @staticmethod
    def _render_analysis_status():
        """渲染分析状态"""
        st.markdown("#### 📊 分析结果")
        
        results = st.session_state.analysis_results
        
        if 'overall_assessment' in results:
            assessment = results['overall_assessment']
            score = assessment.get('performance_score', 0) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("性能评分", f"{score:.1f}%")
            with col2:
                if score >= 80:
                    st.success("优秀")
                elif score >= 60:
                    st.warning("良好")
                else:
                    st.error("需改进")
        
        # 关键指标
        if 'beam' in results and 'beam_parameters' in results['beam']:
            beam_params = results['beam']['beam_parameters']
            
            col1, col2 = st.columns(2)
            with col1:
                if 'peak_gain' in beam_params:
                    st.metric("峰值增益", f"{beam_params['peak_gain']:.1f} dBi")
            with col2:
                if 'main_lobe_width_3db_e' in beam_params:
                    st.metric("3dB波束宽度", f"{beam_params['main_lobe_width_3db_e']:.1f}°")
    
    @staticmethod
    def _render_system_status():
        """渲染系统状态"""
        st.markdown("#### 🖥️ 系统信息")
        
        # 内存使用（简化）
        import psutil
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("内存使用", f"{memory_percent:.1f}%")
        with col2:
            st.metric("Python版本", f"{sys.version_info.major}.{sys.version_info.minor}")
        
        # 服务状态
        st.caption("✅ 所有服务正常运行")

# ============================================================================
# 主侧边栏函数
# ============================================================================

def render_sidebar() -> Dict[str, Any]:
    """
    渲染侧边栏主函数
    返回包含所有用户设置的字典
    """
    
    # 初始化会话状态
    if 'sidebar_initialized' not in st.session_state:
        st.session_state.sidebar_initialized = True
        st.session_state.simulation_status = {
            'type': 'idle',
            'message': '等待仿真',
            'progress': 0.0
        }
    
    # 侧边栏标题
    st.sidebar.markdown(
        """
        <div style='text-align: center; margin-bottom: 20px;'>
            <h1 style='color: #1E3A8A;'>📡</h1>
            <h3 style='color: #1E3A8A;'>天线分析平台</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 页面导航
    page = st.sidebar.radio(
        "导航菜单",
        ["📊 仪表板", "🔍 分析工具", "📚 教学中心", "⚙️ 系统设置", "📥 数据导出"],
        label_visibility="collapsed"
    )
    
    page_map = {
        "📊 仪表板": "dashboard",
        "🔍 分析工具": "analysis",
        "📚 教学中心": "education", 
        "⚙️ 系统设置": "settings",
        "📥 数据导出": "export"
    }
    
    selected_page = page_map[page]
    
    # 主配置区域
    with st.sidebar.expander("🎯 天线配置", expanded=True):
        antenna_config = AntennaSelector.render()
    
    with st.sidebar.expander("⚙️ 仿真设置", expanded=False):
        sim_settings = SimulationSettings.render()
    
    with st.sidebar.expander("📊 分析设置", expanded=False):
        analysis_settings = AnalysisSettings.render()
    
    with st.sidebar.expander("📈 可视化设置", expanded=False):
        viz_settings = VisualizationSettings.render()
    
    # 控制面板
    st.sidebar.markdown("---")
    actions = ControlPanel.render()
    
    # 状态面板
    st.sidebar.markdown("---")
    StatusPanel.render()
    
    # 页脚
    st.sidebar.markdown("---")
    st.sidebar.caption(
        """
        <div style='text-align: center; color: #666;'>
        天线分析平台 v1.0.0<br>
        © 2026 雷达与天线实验室
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 返回所有配置
    return {
        'page': selected_page,
        'antenna_config': antenna_config,
        'simulation_settings': sim_settings,
        'analysis_settings': analysis_settings,
        'visualization_settings': viz_settings,
        'actions': actions
    }

# ============================================================================
# 辅助函数
# ============================================================================

def create_antenna_from_config(config: Dict[str, Any]) -> Optional[AntennaParameters]:
    """从配置创建天线对象"""
    try:
        antenna_data = config.get('data', {})
        
        if not antenna_data:
            return None
        
        # 从模板或数据库加载的天线已经有完整结构
        if 'antenna_type' in antenna_data and isinstance(antenna_data['antenna_type'], str):
            # 已经是序列化数据，尝试直接创建
            try:
                return AntennaParameters.from_dict(antenna_data)
            except:
                pass
        
        # 否则从自定义配置构建
        from models.antenna_models import AntennaGeometry, FeedNetwork
        
        # 创建几何结构
        geometry = AntennaGeometry()
        
        # 创建馈电网络
        feed_data = antenna_data.get('feed_network', {})
        feed_network = FeedNetwork(
            type=FeedType(feed_data.get('type', 'coaxial_fed')),
            impedance=feed_data.get('impedance', 50.0)
        )
        
        # 创建天线参数
        antenna = AntennaParameters(
            name=antenna_data.get('name', '自定义天线'),
            antenna_type=AntennaType(antenna_data.get('antenna_type', 'dipole')),
            frequency_range=tuple(antenna_data.get('frequency_range', [1.0, 2.0])),
            center_frequency=antenna_data.get('center_frequency', 1.5),
            gain=antenna_data.get('gain', 10.0),
            bandwidth=antenna_data.get('bandwidth', 10.0),
            vswr=antenna_data.get('vswr', 1.5),
            polarization=PolarizationType(antenna_data.get('polarization', 'vertical')),
            beamwidth_e=antenna_data.get('beamwidth_e', 60.0),
            beamwidth_h=antenna_data.get('beamwidth_h', 60.0),
            sidelobe_level=antenna_data.get('sidelobe_level', -20.0),
            front_to_back_ratio=antenna_data.get('front_to_back_ratio', 20.0),
            geometry=geometry,
            feed_network=feed_network,
            efficiency=antenna_data.get('efficiency', 0.8),
            input_power=antenna_data.get('input_power', 1.0),
            description=antenna_data.get('description', '自定义天线')
        )
        
        return antenna
        
    except Exception as e:
        st.error(f"创建天线对象失败: {e}")
        return None

def save_current_config(config: Dict[str, Any]) -> bool:
    """保存当前配置到文件"""
    try:
        config_dir = Path(__file__).parent.parent / "config" / "saved"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_file = config_dir / f"config_{timestamp}.yaml"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        return True
    except Exception as e:
        st.error(f"保存配置失败: {e}")
        return False

def load_config_from_file() -> Optional[Dict[str, Any]]:
    """从文件加载配置"""
    try:
        config_dir = Path(__file__).parent.parent / "config" / "saved"
        
        if not config_dir.exists():
            return None
        
        config_files = list(config_dir.glob("config_*.yaml"))
        
        if not config_files:
            return None
        
        # 选择最新的配置文件
        latest_file = max(config_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
        
    except Exception as e:
        st.error(f"加载配置失败: {e}")
        return None

if __name__ == "__main__":
    # 测试代码
    st.title("侧边栏测试")
    config = render_sidebar()
    st.json(config, expanded=False)