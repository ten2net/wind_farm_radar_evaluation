"""
侧边栏视图
Streamlit应用的侧边栏控制面板
负责用户交互和参数设置
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple, List
import yaml
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.antenna_models import (
    AntennaParameters, AntennaType, PolarizationType, 
    FeedType, MaterialProperties, ANTENNA_TEMPLATES
)
from services.pattern_generator import get_pattern_generator_service
from services.analysis_service import get_analysis_service
from services.visualization_service import get_visualization_service
from utils.config import AppConfig

def load_antenna_database() -> Dict[str, Any]:
    """加载天线数据库"""
    try:
        data_dir = Path(__file__).parent.parent / "data"
        antenna_file = data_dir / "antennas.yaml"
        
        if antenna_file.exists():
            with open(antenna_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # 创建默认天线数据库
            default_antennas = {
                'antennas': [
                    {
                        'name': '半波偶极子天线',
                        'type': 'dipole',
                        'frequency': 1.0,
                        'gain': 2.15,
                        'description': '基本的半波偶极子天线'
                    },
                    {
                        'name': '微带贴片天线',
                        'type': 'patch',
                        'frequency': 2.45,
                        'gain': 7.0,
                        'description': '2.4GHz WiFi微带贴片天线'
                    },
                    {
                        'name': '喇叭天线',
                        'type': 'horn',
                        'frequency': 10.0,
                        'gain': 20.0,
                        'description': 'X波段标准增益喇叭天线'
                    }
                ]
            }
            
            # 保存默认数据库
            data_dir.mkdir(exist_ok=True)
            with open(antenna_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_antennas, f, allow_unicode=True)
            
            return default_antennas
    except Exception as e:
        st.error(f"加载天线数据库失败: {e}")
        return {'antennas': []}

def save_antenna_to_database(antenna: AntennaParameters):
    """保存天线到数据库"""
    try:
        data_dir = Path(__file__).parent.parent / "data"
        antenna_file = data_dir / "antennas.yaml"
        
        # 加载现有数据库
        if antenna_file.exists():
            with open(antenna_file, 'r', encoding='utf-8') as f:
                database = yaml.safe_load(f)
        else:
            database = {'antennas': []}
        
        # 添加新天线
        antenna_dict = antenna.to_dict()
        antenna_dict['created_at'] = datetime.now().isoformat()
        
        # 检查是否已存在
        existing_idx = None
        for i, existing_antenna in enumerate(database['antennas']):
            if existing_antenna.get('name') == antenna.name:
                existing_idx = i
                break
        
        if existing_idx is not None:
            # 更新现有天线
            database['antennas'][existing_idx] = antenna_dict
        else:
            # 添加新天线
            database['antennas'].append(antenna_dict)
        
        # 保存数据库
        with open(antenna_file, 'w', encoding='utf-8') as f:
            yaml.dump(database, f, allow_unicode=True, default_flow_style=False)
        
        return True
    except Exception as e:
        st.error(f"保存天线到数据库失败: {e}")
        return False

def get_antenna_from_database(antenna_name: str) -> Optional[Dict[str, Any]]:
    """从数据库获取天线"""
    try:
        database = load_antenna_database()
        
        for antenna in database.get('antennas', []):
            if antenna.get('name') == antenna_name:
                return antenna
        
        return None
    except Exception as e:
        st.error(f"从数据库获取天线失败: {e}")
        return None

def render_antenna_selection() -> Dict[str, Any]:
    """渲染天线选择面板"""
    st.markdown("### 📡 天线选择")
    
    # 天线源选择
    antenna_source = st.selectbox(
        "天线来源",
        ["模板", "数据库", "自定义"],
        help="选择天线定义方式"
    )
    
    selected_antenna = None
    antenna_params = {}
    
    if antenna_source == "模板":
        # 从模板选择
        template_options = list(ANTENNA_TEMPLATES.keys())
        selected_template = st.selectbox(
            "选择天线模板",
            template_options,
            format_func=lambda x: ANTENNA_TEMPLATES[x].name
        )
        
        if selected_template:
            selected_antenna = ANTENNA_TEMPLATES[selected_template]
            
            # 允许用户自定义参数
            with st.expander("自定义参数", expanded=False):
                selected_antenna.center_frequency = st.number_input(
                    "中心频率 (GHz)",
                    value=selected_antenna.center_frequency,
                    min_value=0.1,
                    max_value=100.0,
                    step=0.1
                )
                selected_antenna.gain = st.number_input(
                    "增益 (dBi)",
                    value=selected_antenna.gain,
                    min_value=-10.0,
                    max_value=50.0,
                    step=0.1
                )
    
    elif antenna_source == "数据库":
        # 从数据库选择
        database = load_antenna_database()
        antenna_names = [antenna.get('name', '未知') for antenna in database.get('antennas', [])]
        
        if antenna_names:
            selected_antenna_name = st.selectbox(
                "选择天线",
                antenna_names
            )
            
            if selected_antenna_name:
                antenna_data = get_antenna_from_database(selected_antenna_name)
                if antenna_data:
                    try:
                        selected_antenna = AntennaParameters.from_dict(antenna_data)
                    except Exception as e:
                        st.error(f"加载天线数据失败: {e}")
        else:
            st.info("数据库中暂无天线，请先创建自定义天线")
    
    elif antenna_source == "自定义":
        # 自定义天线参数
        st.markdown("#### 基本参数")
        
        col1, col2 = st.columns(2)
        with col1:
            antenna_name = st.text_input("天线名称", value="自定义天线")
            antenna_type = st.selectbox(
                "天线类型",
                [t.value for t in AntennaType],
                format_func=lambda x: x.capitalize()
            )
            center_freq = st.number_input("中心频率 (GHz)", value=2.45, min_value=0.1, max_value=100.0)
        
        with col2:
            gain = st.number_input("增益 (dBi)", value=10.0, min_value=-10.0, max_value=50.0)
            beamwidth_e = st.number_input("E面波束宽度 (°)", value=60.0, min_value=1.0, max_value=180.0)
            beamwidth_h = st.number_input("H面波束宽度 (°)", value=60.0, min_value=1.0, max_value=180.0)
        
        # 更多参数
        with st.expander("高级参数", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                bandwidth = st.number_input("带宽 (%)", value=10.0, min_value=0.1, max_value=100.0)
                vswr = st.number_input("VSWR", value=1.5, min_value=1.0, max_value=10.0)
                polarization = st.selectbox(
                    "极化类型",
                    [p.value for p in PolarizationType],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
            
            with col2:
                sidelobe_level = st.number_input("副瓣电平 (dB)", value=-20.0, max_value=0.0, min_value=-60.0)
                efficiency = st.number_input("效率", value=0.8, min_value=0.0, max_value=1.0)
                input_power = st.number_input("输入功率 (W)", value=1.0, min_value=0.1, max_value=1000.0)
        
        # 创建天线参数对象
        antenna_params = {
            'name': antenna_name,
            'antenna_type': AntennaType(antenna_type),
            'frequency_range': (center_freq * 0.9, center_freq * 1.1),
            'center_frequency': center_freq,
            'gain': gain,
            'bandwidth': bandwidth,
            'vswr': vswr,
            'polarization': PolarizationType(polarization),
            'beamwidth_e': beamwidth_e,
            'beamwidth_h': beamwidth_h,
            'sidelobe_level': sidelobe_level,
            'efficiency': efficiency,
            'input_power': input_power
        }
    
    return {
        'antenna_source': antenna_source,
        'selected_antenna': selected_antenna,
        'antenna_params': antenna_params
    }

def render_simulation_settings() -> Dict[str, Any]:
    """渲染仿真设置面板"""
    st.markdown("### ⚙️ 仿真设置")
    
    # 生成器选择
    generator_service = get_pattern_generator_service()
    available_generators = generator_service.get_available_generators()
    
    generator_type = st.selectbox(
        "方向图生成器",
        available_generators,
        format_func=lambda x: x.capitalize(),
        help="选择方向图生成算法"
    )
    
    # 分辨率设置
    col1, col2 = st.columns(2)
    with col1:
        theta_res = st.slider(
            "Theta分辨率 (°)",
            min_value=1,
            max_value=10,
            value=5,
            help="俯仰角方向采样分辨率"
        )
    
    with col2:
        phi_res = st.slider(
            "Phi分辨率 (°)",
            min_value=1,
            max_value=10,
            value=5,
            help="方位角方向采样分辨率"
        )
    
    # 方向图组件选择
    pattern_components = ['总场', 'Theta分量', 'Phi分量']
    component_map = {'总场': 'total', 'Theta分量': 'theta', 'Phi分量': 'phi'}
    selected_component = st.selectbox(
        "分析组件",
        pattern_components,
        help="选择要分析的场分量"
    )
    
    # 高级设置
    with st.expander("高级设置", expanded=False):
        use_cache = st.checkbox("使用缓存", value=True, help="启用结果缓存以提高性能")
        normalize_pattern = st.checkbox("归一化方向图", value=True, help="将方向图归一化到峰值增益")
        
        if generator_type == "analytical":
            add_sidelobes = st.checkbox("添加副瓣", value=True, help="在解析模型中添加副瓣结构")
        
        if generator_type == "numerical":
            include_coupling = st.checkbox("考虑互耦", value=False, help="在数值计算中考虑阵元间互耦")
    
    return {
        'generator_type': generator_type,
        'theta_resolution': theta_res,
        'phi_resolution': phi_res,
        'component': component_map[selected_component],
        'use_cache': use_cache,
        'normalize_pattern': normalize_pattern,
        'advanced': {
            'add_sidelobes': add_sidelobes if 'add_sidelobes' in locals() else False,
            'include_coupling': include_coupling if 'include_coupling' in locals() else False
        }
    }

def render_analysis_settings() -> Dict[str, Any]:
    """渲染分析设置面板"""
    st.markdown("### 📊 分析设置")
    
    # 分析类型选择
    analysis_types = st.multiselect(
        "选择分析类型",
        ["波束分析", "极化分析", "效率分析", "全面分析"],
        default=["波束分析", "全面分析"],
        help="选择要执行的分析类型"
    )
    
    analysis_map = {
        "波束分析": "beam",
        "极化分析": "polarization", 
        "效率分析": "efficiency",
        "全面分析": "comprehensive"
    }
    
    selected_analyses = [analysis_map[atype] for atype in analysis_types]
    
    # 波束分析设置
    if "波束分析" in analysis_types:
        with st.expander("波束分析设置", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                beamwidth_levels = st.multiselect(
                    "波束宽度计算电平",
                    ["3dB", "6dB", "10dB", "20dB"],
                    default=["3dB", "10dB"]
                )
                calculate_null_depth = st.checkbox("计算零陷深度", value=True)
            
            with col2:
                analyze_symmetry = st.checkbox("分析波束对称性", value=True)
                calculate_beamshape = st.checkbox("计算波束形状因子", value=True)
    
    # 极化分析设置
    if "极化分析" in analysis_types:
        with st.expander("极化分析设置", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                ar_threshold = st.number_input("轴比阈值 (dB)", value=3.0, min_value=0.1, max_value=20.0)
                calculate_xpd = st.checkbox("计算交叉极化鉴别度", value=True)
            
            with col2:
                analyze_polarization_purity = st.checkbox("分析极化纯度", value=True)
                calculate_ellipse_params = st.checkbox("计算极化椭圆参数", value=True)
    
    # 比较分析设置
    enable_comparison = st.checkbox("启用比较分析", value=False, help="比较多个天线或配置")
    
    comparison_settings = {}
    if enable_comparison:
        with st.expander("比较分析设置", expanded=False):
            comparison_type = st.selectbox(
                "比较类型",
                ["不同天线", "不同频率", "不同参数"],
                help="选择比较的内容"
            )
            
            if comparison_type == "不同天线":
                num_antennas = st.number_input("天线数量", value=2, min_value=2, max_value=5)
            
            elif comparison_type == "不同频率":
                start_freq = st.number_input("起始频率 (GHz)", value=1.0, min_value=0.1)
                end_freq = st.number_input("结束频率 (GHz)", value=3.0, min_value=0.1)
                num_frequencies = st.number_input("频率点数", value=3, min_value=2, max_value=10)
            
            comparison_settings = {
                'enabled': True,
                'type': comparison_type,
                'params': locals().get('num_antennas', locals().get('num_frequencies', 0))
            }
    
    return {
        'analysis_types': selected_analyses,
        'comparison': comparison_settings,
        'beam_analysis': {
            'beamwidth_levels': beamwidth_levels if 'beamwidth_levels' in locals() else [],
            'calculate_null_depth': calculate_null_depth if 'calculate_null_depth' in locals() else False,
            'analyze_symmetry': analyze_symmetry if 'analyze_symmetry' in locals() else False,
            'calculate_beamshape': calculate_beamshape if 'calculate_beamshape' in locals() else False
        } if "波束分析" in analysis_types else {},
        'polarization_analysis': {
            'ar_threshold': ar_threshold if 'ar_threshold' in locals() else 3.0,
            'calculate_xpd': calculate_xpd if 'calculate_xpd' in locals() else False,
            'analyze_polarization_purity': analyze_polarization_purity if 'analyze_polarization_purity' in locals() else False,
            'calculate_ellipse_params': calculate_ellipse_params if 'calculate_ellipse_params' in locals() else False
        } if "极化分析" in analysis_types else {}
    }

def render_visualization_settings() -> Dict[str, Any]:
    """渲染可视化设置面板"""
    st.markdown("### 📈 可视化设置")
    
    # 可视化类型选择
    viz_types = st.multiselect(
        "选择可视化类型",
        ["2D方向图", "3D方向图", "极坐标图", "轴比分析", "统计分析", "综合仪表板"],
        default=["2D方向图", "3D方向图"],
        help="选择要生成的可视化图表"
    )
    
    viz_map = {
        "2D方向图": "2d_pattern",
        "3D方向图": "3d_pattern", 
        "极坐标图": "polar_pattern",
        "轴比分析": "axial_ratio",
        "统计分析": "statistics",
        "综合仪表板": "dashboard"
    }
    
    selected_viz = [viz_map[vtype] for vtype in viz_types]
    
    # 2D方向图设置
    if "2D方向图" in viz_types:
        with st.expander("2D方向图设置", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                fixed_angle = st.number_input("固定角度 (°)", value=0.0, min_value=0.0, max_value=360.0)
                plane = st.selectbox("切面平面", ["E面 (固定Phi)", "H面 (固定Theta)"])
            
            with col2:
                show_peaks = st.checkbox("显示峰值点", value=True)
                show_beamwidth = st.checkbox("显示波束宽度", value=True)
                show_sidelobes = st.checkbox("显示副瓣", value=True)
    
    # 3D方向图设置
    if "3D方向图" in viz_types:
        with st.expander("3D方向图设置", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                elevation_angle = st.slider("视角俯仰角", 0, 90, 30)
                azimuth_angle = st.slider("视角方位角", 0, 360, 45)
            
            with col2:
                show_contours = st.checkbox("显示等高线", value=True)
                show_colorbar = st.checkbox("显示颜色条", value=True)
                opacity = st.slider("透明度", 0.1, 1.0, 0.8)
    
    # 显示设置
    st.markdown("#### 显示设置")
    
    col1, col2 = st.columns(2)
    with col1:
        theme = st.selectbox(
            "主题",
            ["浅色", "深色", "自动"],
            help="选择可视化主题"
        )
        
        fig_width = st.number_input("图表宽度 (像素)", value=800, min_value=400, max_value=2000)
    
    with col2:
        fig_height = st.number_input("图表高度 (像素)", value=600, min_value=300, max_value=1500)
        dpi = st.selectbox("分辨率 (DPI)", [72, 96, 150, 300], index=1)
    
    # 导出设置
    with st.expander("导出设置", expanded=False):
        export_formats = st.multiselect(
            "导出格式",
            ["PNG", "PDF", "HTML", "SVG"],
            default=["PNG"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            export_dpi = st.selectbox("导出DPI", [150, 300, 600], index=1)
        
        with col2:
            export_scale = st.number_input("导出缩放比例", value=2.0, min_value=1.0, max_value=5.0)
    
    return {
        'visualization_types': selected_viz,
        '2d_settings': {
            'fixed_angle': fixed_angle if 'fixed_angle' in locals() else 0.0,
            'plane': plane if 'plane' in locals() else "E面 (固定Phi)",
            'show_peaks': show_peaks if 'show_peaks' in locals() else True,
            'show_beamwidth': show_beamwidth if 'show_beamwidth' in locals() else True,
            'show_sidelobes': show_sidelobes if 'show_sidelobes' in locals() else True
        } if "2D方向图" in viz_types else {},
        '3d_settings': {
            'elevation_angle': elevation_angle if 'elevation_angle' in locals() else 30,
            'azimuth_angle': azimuth_angle if 'azimuth_angle' in locals() else 45,
            'show_contours': show_contours if 'show_contours' in locals() else True,
            'show_colorbar': show_colorbar if 'show_colorbar' in locals() else True,
            'opacity': opacity if 'opacity' in locals() else 0.8
        } if "3D方向图" in viz_types else {},
        'display_settings': {
            'theme': theme,
            'fig_width': fig_width,
            'fig_height': fig_height,
            'dpi': dpi
        },
        'export_settings': {
            'formats': export_formats,
            'dpi': export_dpi,
            'scale': export_scale
        }
    }

def render_control_buttons() -> Dict[str, Any]:
    """渲染控制按钮"""
    st.markdown("### 🎮 控制")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        run_simulation = st.button(
            "🚀 运行仿真",
            type="primary",
            width='stretch',
            help="运行天线仿真和分析"
        )
    
    with col2:
        save_results = st.button(
            "💾 保存结果",
            width='stretch',
            help="保存当前结果到文件"
        )
    
    with col3:
        reset_all = st.button(
            "🔄 重置",
            width='stretch',
            help="重置所有设置"
        )
    
    # 清空缓存按钮
    if st.button("🧹 清空缓存", width='stretch'):
        generator_service = get_pattern_generator_service()
        generator_service.clear_cache()
        st.success("缓存已清空！")
    
    return {
        'run_simulation': run_simulation,
        'save_results': save_results,
        'reset_all': reset_all
    }

def render_navigation() -> str:
    """渲染导航菜单"""
    st.markdown("### 🧭 导航")
    
    # 页面选项
    page_options = {
        "📊 仪表板": "dashboard",
        "🔍 分析": "analysis", 
        "📚 教学": "education",
        "📥 导出": "export"
    }
    
    selected_page = st.radio(
        "选择页面",
        list(page_options.keys()),
        label_visibility="collapsed"
    )
    
    return page_options[selected_page]

def render_status_panel() -> None:
    """渲染状态面板"""
    st.markdown("### 📈 状态")
    
    # 显示当前状态
    if 'simulation_status' in st.session_state:
        status = st.session_state.simulation_status
        st.info(f"状态: {status}")
    
    # 显示天线信息
    if 'current_antenna' in st.session_state and st.session_state.current_antenna:
        antenna = st.session_state.current_antenna
        st.markdown(f"""
        **当前天线:** {antenna.name}
        **类型:** {antenna.antenna_type.value}
        **频率:** {antenna.center_frequency} GHz
        **增益:** {antenna.gain} dBi
        """)
    
    # 显示性能指标
    if 'analysis_results' in st.session_state and st.session_state.analysis_results:
        results = st.session_state.analysis_results
        if 'overall_assessment' in results:
            assessment = results['overall_assessment']
            score = assessment.get('performance_score', 0) * 100
            
            st.metric(
                label="性能评分",
                value=f"{score:.1f}%",
                delta="良好" if score > 70 else "需改进"
            )

def render_sidebar() -> Dict[str, Any]:
    """渲染侧边栏主函数"""
    
    # 初始化会话状态
    if 'sidebar_collapsed' not in st.session_state:
        st.session_state.sidebar_collapsed = False
    
    # 标题
    st.markdown("## 📡 天线分析平台")
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["天线", "仿真", "分析", "可视化"])
    
    with tab1:
        antenna_selection = render_antenna_selection()
    
    with tab2:
        simulation_settings = render_simulation_settings()
    
    with tab3:
        analysis_settings = render_analysis_settings()
    
    with tab4:
        visualization_settings = render_visualization_settings()
    
    # 分隔线
    st.markdown("---")
    
    # 控制按钮
    control_buttons = render_control_buttons()
    
    # 分隔线
    st.markdown("---")
    
    # 导航菜单
    selected_page = render_navigation()
    
    # 分隔线
    st.markdown("---")
    
    # 状态面板
    render_status_panel()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
        天线分析平台 v1.0<br>
        © 2026 雷达与天线实验室
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 返回所有设置
    return {
        'page': selected_page,
        'antenna_selection': antenna_selection,
        'simulation_settings': simulation_settings,
        'analysis_settings': analysis_settings,
        'visualization_settings': visualization_settings,
        'control_buttons': control_buttons
    }

def create_antenna_from_params(params: Dict[str, Any]) -> Optional[AntennaParameters]:
    """从参数创建天线对象"""
    try:
        # 这是一个简化版本，实际使用时需要更完整的创建逻辑
        from models.antenna_models import AntennaGeometry, FeedNetwork, Substrate, MaterialProperties
        
        # 创建基本天线参数
        antenna = AntennaParameters(
            name=params.get('name', '自定义天线'),
            antenna_type=AntennaType(params.get('antenna_type', 'dipole')),
            frequency_range=params.get('frequency_range', (1.0, 2.0)),
            center_frequency=params.get('center_frequency', 1.5),
            gain=params.get('gain', 10.0),
            bandwidth=params.get('bandwidth', 10.0),
            vswr=params.get('vswr', 1.5),
            polarization=PolarizationType(params.get('polarization', 'vertical')),
            beamwidth_e=params.get('beamwidth_e', 60.0),
            beamwidth_h=params.get('beamwidth_h', 60.0),
            sidelobe_level=params.get('sidelobe_level', -20.0),
            front_to_back_ratio=params.get('front_to_back_ratio', 20.0),
            efficiency=params.get('efficiency', 0.8),
            input_power=params.get('input_power', 1.0),
            max_power=params.get('max_power', 10.0),
            geometry=AntennaGeometry(),  # 简化
            feed_network=FeedNetwork(type=FeedType.COAXIAL_FED),
            description=params.get('description', '')
        )
        
        return antenna
    except Exception as e:
        st.error(f"创建天线对象失败: {e}")
        return None

if __name__ == "__main__":
    # 测试代码
    st.title("侧边栏测试")
    config = render_sidebar()
    st.json(config, expanded=False)