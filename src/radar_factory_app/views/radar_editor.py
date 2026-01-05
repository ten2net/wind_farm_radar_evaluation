"""
雷达编辑器视图模块
提供雷达参数编辑和创建界面
使用Streamlit构建交互式编辑表单
"""

import streamlit as st
import numpy as np
from typing import Dict, Any, Optional, List
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.radar_models import RadarModel, RadarBand, PlatformType, MissionType
from controllers.radar_controller import RadarController, RadarDataValidator
from utils.helpers import format_frequency, format_power, format_distance


class RadarEditorView:
    """雷达编辑器视图类"""
    
    def __init__(self):
        self.controller = RadarController()
        self.validator = RadarDataValidator()
        self.setup_page_config()
    
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="雷达编辑器 - 雷达工厂",
            page_icon="⚙️",
            layout="wide"
        )
        
        # 自定义CSS样式
        st.markdown("""
        <style>
        .editor-header {
            font-size: 2rem;
            color: #2E86AB;
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .param-section {
            background-color: #080408;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border-left: 4px solid #2E86AB;
        }
        .preview-card {
            background-color: #383438;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #2E86AB;
            border-left: 4px solid #2E86AB;
        }
        .warning-box {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """渲染页面头部"""
        st.markdown('<div class="editor-header">⚙️ 雷达参数编辑器</div>', 
                   unsafe_allow_html=True)
        
        # 显示当前编辑状态
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
                st.info(f"正在编辑雷达: {st.session_state.editing_radar_id}")
            else:
                st.success("创建新雷达")
        
        with col2:
            if st.button("📋 返回主界面", key="editor_btn_back"):
                st.session_state.current_view = "dashboard"
                st.rerun()
        
        with col3:
            if st.button("💾 保存模板", key="editor_btn_save_template"):
                self._save_as_template()
    
    def render_editor(self):
        """渲染雷达编辑器"""
        # 确保编辑数据已初始化
        if 'radar_edit_data' not in st.session_state or st.session_state.radar_edit_data is None:
            if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
                # 编辑现有雷达
                self._load_existing_radar(st.session_state.editing_radar_id)
            else:
                # 创建新雷达
                self._initialize_new_radar()
        
        # 检查编辑数据是否有效
        if st.session_state.radar_edit_data is None:
            st.error("无法初始化雷达编辑数据")
            if st.button("重新初始化", key="editor_btn_reinit"):
                self._initialize_new_radar()
                st.rerun()
            return
        
        # 创建选项卡布局
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 基本参数", 
            "📡 发射机参数", 
            "📊 天线参数", 
            "🔧 信号处理"
        ])
        
        with tab1:
            self._render_basic_parameters()
        
        with tab2:
            self._render_transmitter_parameters()
        
        with tab3:
            self._render_antenna_parameters()
        
        with tab4:
            self._render_signal_processing_parameters()
        
        # 预览和操作区域
        st.markdown("---")
        self._render_preview_and_actions()
    
    def _load_existing_radar(self, radar_id: str):
        """加载现有雷达数据"""
        try:
            radar = self.controller.get_radar_by_id(radar_id)
            if radar:
                # 转换为编辑数据格式
                st.session_state.radar_edit_data = {
                    'radar_id': radar_id,
                    'name': radar.name,
                    'type': self._get_radar_type_string(radar),
                    'platform': radar.platform.value,
                    'mission_types': [mission.value for mission in radar.mission_types],
                    'deployment_method': getattr(radar, 'deployment_method', ''),
                    'theoretical_range_km': getattr(radar, 'theoretical_range_km', 0),
                    'transmitter': {
                        'frequency_hz': radar.transmitter.frequency_hz if radar.transmitter else 1e9,
                        'power_w': radar.transmitter.power_w if radar.transmitter else 100000,
                        'pulse_width_s': radar.transmitter.pulse_width_s if radar.transmitter else 100e-6,
                        'prf_hz': getattr(radar.transmitter, 'prf_hz', 1000) if radar.transmitter else 1000
                    } if radar.transmitter else {},
                    'antenna': {
                        'gain_dbi': radar.antenna.gain_dbi if radar.antenna else 30.0,
                        'azimuth_beamwidth': radar.antenna.azimuth_beamwidth if radar.antenna else 5.0,
                        'elevation_beamwidth': radar.antenna.elevation_beamwidth if radar.antenna else 10.0
                    } if radar.antenna else {},
                    'signal_processing': {
                        'mti_filter': getattr(radar.signal_processing, 'mti_filter', '') if radar.signal_processing else '',
                        'doppler_channels': getattr(radar.signal_processing, 'doppler_channels', 256) if radar.signal_processing else 256,
                        'max_tracking_targets': getattr(radar.signal_processing, 'max_tracking_targets', 100) if radar.signal_processing else 100
                    } if radar.signal_processing else {}
                }
            else:
                st.error(f"雷达 {radar_id} 不存在")
                self._initialize_new_radar()
        except Exception as e:
            st.error(f"加载雷达数据时发生错误: {str(e)}")
            self._initialize_new_radar()
    
    def _initialize_new_radar(self):
        """初始化新雷达数据"""
        try:
            # 获取雷达数量
            radar_count = len(self.controller.get_all_radars()) if hasattr(self.controller, 'get_all_radars') else 0
            
            st.session_state.radar_edit_data = {
                'radar_id': f"RAD_{radar_count + 1:04d}",
                'name': '新建雷达',
                'type': 'early_warning',
                'platform': '地面机动',
                'mission_types': ['远程预警'],
                'deployment_method': '固定部署',
                'theoretical_range_km': 200,
                'transmitter': {
                    'frequency_hz': 1e9,
                    'power_w': 100000,
                    'pulse_width_s': 100e-6,
                    'prf_hz': 1000
                },
                'antenna': {
                    'gain_dbi': 30.0,
                    'azimuth_beamwidth': 5.0,
                    'elevation_beamwidth': 10.0
                },
                'signal_processing': {
                    'mti_filter': '3脉冲对消器',
                    'doppler_channels': 256,
                    'max_tracking_targets': 100
                }
            }
        except Exception as e:
            st.error(f"初始化新雷达时发生错误: {str(e)}")
            # 提供默认值
            st.session_state.radar_edit_data = {
                'radar_id': 'RAD_0001',
                'name': '新建雷达',
                'type': 'early_warning',
                'platform': '地面机动',
                'mission_types': ['远程预警'],
                'deployment_method': '固定部署',
                'theoretical_range_km': 200,
                'transmitter': {'frequency_hz': 1e9, 'power_w': 100000, 'pulse_width_s': 100e-6, 'prf_hz': 1000},
                'antenna': {'gain_dbi': 30.0, 'azimuth_beamwidth': 5.0, 'elevation_beamwidth': 10.0},
                'signal_processing': {'mti_filter': '3脉冲对消器', 'doppler_channels': 256, 'max_tracking_targets': 100}
            }
    
    def _get_radar_type_string(self, radar) -> str:
        """获取雷达类型字符串"""
        class_name = radar.__class__.__name__
        type_map = {
            'EarlyWarningRadar': 'early_warning',
            'AirborneRadar': 'airborne', 
            'FireControlRadar': 'fire_control',
            'MaritimeRadar': 'maritime'
        }
        return type_map.get(class_name, 'early_warning')
    
    def _render_basic_parameters(self):
        """渲染基本参数部分"""
        st.markdown('<div class="param-section">📝 基本参数</div>', 
                   unsafe_allow_html=True)
        
        # 确保编辑数据存在
        if st.session_state.radar_edit_data is None:
            st.error("编辑数据不存在")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 雷达名称和ID
            st.session_state.radar_edit_data['name'] = st.text_input(
                "雷达名称",
                value=st.session_state.radar_edit_data.get('name', '新建雷达'),
                help="输入雷达的完整名称",
                key="radar_name_input"
            )
            
            st.session_state.radar_edit_data['radar_id'] = st.text_input(
                "雷达ID",
                value=st.session_state.radar_edit_data.get('radar_id', 'RAD_0001'),
                help="雷达的唯一标识符",
                key="radar_id_input"
            )
            
            # 雷达类型
            radar_type = st.selectbox(
                "雷达类型",
                options=['early_warning', 'airborne', 'fire_control', 'maritime'],
                format_func=lambda x: {
                    'early_warning': '预警雷达',
                    'airborne': '机载雷达', 
                    'fire_control': '火控雷达',
                    'maritime': '海事雷达'
                }[x],
                index=['early_warning', 'airborne', 'fire_control', 'maritime'].index(
                    st.session_state.radar_edit_data.get('type', 'early_warning')
                ),
                key="radar_type_select"
            )
            st.session_state.radar_edit_data['type'] = radar_type
        
        with col2:
            # 平台类型
            platform = st.selectbox(
                "平台类型",
                options=['地面机动', '机载', '舰载', '固定阵地'],
                index=['地面机动', '机载', '舰载', '固定阵地'].index(
                    st.session_state.radar_edit_data.get('platform', '地面机动')
                ),
                key="platform_select"
            )
            st.session_state.radar_edit_data['platform'] = platform
            
            # 部署方式
            st.session_state.radar_edit_data['deployment_method'] = st.text_input(
                "部署方式",
                value=st.session_state.radar_edit_data.get('deployment_method', '固定部署'),
                help="例如：固定部署、机动部署等",
                key="deployment_input"
            )
            
            # 理论探测距离
            st.session_state.radar_edit_data['theoretical_range_km'] = st.number_input(
                "理论探测距离 (km)",
                min_value=1.0,
                max_value=1000.0,
                value=float(st.session_state.radar_edit_data.get('theoretical_range_km', 200)),
                step=10.0,
                key="theoretical_range_input"
            )
        
        # 任务类型（多选）
        # st.subheader("任务类型")
        st.markdown('<div class="param-section">📝 任务类型</div>', 
                   unsafe_allow_html=True)        
        mission_options = ['远程预警', '反隐身', '空中预警', '指挥控制', 
                          '区域防空', '火控', '海事监视']
        
        selected_missions = st.multiselect(
            "选择雷达任务类型",
            options=mission_options,
            default=st.session_state.radar_edit_data.get('mission_types', ['远程预警']),
            help="可多选雷达的主要任务类型",
            key="mission_multiselect"
        )
        st.session_state.radar_edit_data['mission_types'] = selected_missions
        
        # 根据雷达类型显示提示信息
        self._show_radar_type_tips(radar_type)
    
    def _show_radar_type_tips(self, radar_type: str):
        """显示雷达类型提示信息"""
        tips = {
            'early_warning': {
                'title': '预警雷达特点',
                'content': '• 工作频段通常为UHF/L波段\n• 大功率、大天线孔径\n• 重点考虑反隐身能力\n• 适合远程预警任务'
            },
            'airborne': {
                'title': '机载雷达特点', 
                'content': '• 工作频段通常为L/S波段\n• 平台高度优势明显\n• 需要考虑平台运动影响\n• 适合空中预警和指挥控制'
            },
            'fire_control': {
                'title': '火控雷达特点',
                'content': '• 工作频段通常为C/X波段\n• 高精度、高数据率\n• 强调跟踪和制导能力\n• 适合末端防御和导弹引导'
            },
            'maritime': {
                'title': '海事雷达特点',
                'content': '• 工作频段广泛(S/X/Ku波段)\n• 需要良好的杂波抑制\n• 考虑海面多路径效应\n• 适合海上监视和目标检测'
            }
        }
        
        tip = tips.get(radar_type, tips['early_warning'])
        st.info(f"**{tip['title']}**\n\n{tip['content']}")
    
    def _render_transmitter_parameters(self):
        """渲染发射机参数部分"""
        st.markdown('<div class="param-section">📡 发射机参数</div>', 
                   unsafe_allow_html=True)
        
        # 确保编辑数据存在
        if st.session_state.radar_edit_data is None:
            st.error("编辑数据不存在")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 工作频率
            freq_hz = st.number_input(
                "工作频率 (Hz)",
                min_value=1e6,
                max_value=100e9,
                value=float(st.session_state.radar_edit_data.get('transmitter', {}).get('frequency_hz', 1e9)),
                step=1e6,
                format="%.0f",
                key="freq_input"
            )
            st.session_state.radar_edit_data['transmitter']['frequency_hz'] = freq_hz
            st.write(f"**频率显示:** {format_frequency(freq_hz)}")
            
            # 发射功率
            power_w = st.number_input(
                "发射功率 (W)",
                min_value=1.0,
                max_value=10e6,
                value=float(st.session_state.radar_edit_data.get('transmitter', {}).get('power_w', 100000)),
                step=1000.0,
                format="%.0f",
                key="power_input"
            )
            st.session_state.radar_edit_data['transmitter']['power_w'] = power_w
            st.write(f"**功率显示:** {format_power(power_w)}")
        
        with col2:
            # 脉冲宽度
            pulse_width_s = st.number_input(
                "脉冲宽度 (秒)",
                min_value=1e-9,
                max_value=1.0,
                value=float(st.session_state.radar_edit_data.get('transmitter', {}).get('pulse_width_s', 100e-6)),
                step=1e-6,
                format="%.6f",
                key="pulse_width_input"
            )
            st.session_state.radar_edit_data['transmitter']['pulse_width_s'] = pulse_width_s
            st.write(f"**脉冲宽度:** {pulse_width_s * 1e6:.2f} μs")
            
            # 脉冲重复频率
            prf_hz = st.number_input(
                "脉冲重复频率 (Hz)",
                min_value=1.0,
                max_value=100000.0,
                value=float(st.session_state.radar_edit_data.get('transmitter', {}).get('prf_hz', 1000)),
                step=100.0,
                key="prf_input"
            )
            st.session_state.radar_edit_data['transmitter']['prf_hz'] = prf_hz
        
        # 频率建议
        self._show_frequency_recommendations(freq_hz)
        
        # 参数验证
        self._validate_transmitter_parameters()
    
    def _show_frequency_recommendations(self, frequency_hz: float):
        """显示频率建议"""
        freq_ghz = frequency_hz / 1e9
        
        if freq_ghz < 0.3:
            band = "UHF波段"
            tips = "• 反隐身能力强\n• 大气衰减小\n• 适合远程预警\n• 天线尺寸较大"
        elif freq_ghz < 1:
            band = "L波段" 
            tips = "• 平衡性较好\n• 适合预警机\n• 中等分辨率\n• 通用性强"
        elif freq_ghz < 2:
            band = "S波段"
            tips = "• 多功能性\n• 适合区域防空\n• 分辨率适中\n• 应用广泛"
        elif freq_ghz < 4:
            band = "C波段"
            tips = "• 跟踪精度高\n• 适合火控雷达\n• 抗干扰能力强\n• 大气衰减增加"
        elif freq_ghz < 8:
            band = "X波段"
            tips = "• 分辨率高\n• 适合精密跟踪\n• 天线尺寸小\n• 大气衰减明显"
        else:
            band = "Ku波段及以上"
            tips = "• 极高分辨率\n• 适合近程应用\n• 衰减严重\n• 雨衰影响大"
        
        st.success(f"**{band}雷达**\n\n{tips}")
    
    def _validate_transmitter_parameters(self):
        """验证发射机参数"""
        tx_params = st.session_state.radar_edit_data.get('transmitter', {})
        is_valid, errors = self.validator.validate_transmitter_parameters(tx_params)
        
        if not is_valid:
            for error in errors:
                st.markdown(f'<div class="warning-box">⚠️ {error}</div>', 
                           unsafe_allow_html=True)
    
    def _render_antenna_parameters(self):
        """渲染天线参数部分"""
        st.markdown('<div class="param-section">📊 天线参数</div>', 
                   unsafe_allow_html=True)
        
        # 确保编辑数据存在
        if st.session_state.radar_edit_data is None:
            st.error("编辑数据不存在")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 天线增益
            gain_dbi = st.slider(
                "天线增益 (dBi)",
                min_value=0.0,
                max_value=50.0,
                value=float(st.session_state.radar_edit_data.get('antenna', {}).get('gain_dbi', 30.0)),
                step=0.1,
                key="gain_slider"
            )
            st.session_state.radar_edit_data['antenna']['gain_dbi'] = gain_dbi
            
            # 方位波束宽度
            azimuth_bw = st.slider(
                "方位波束宽度 (度)",
                min_value=0.1,
                max_value=90.0,
                value=float(st.session_state.radar_edit_data.get('antenna', {}).get('azimuth_beamwidth', 5.0)),
                step=0.1,
                key="azimuth_slider"
            )
            st.session_state.radar_edit_data['antenna']['azimuth_beamwidth'] = azimuth_bw
        
        with col2:
            # 俯仰波束宽度
            elevation_bw = st.slider(
                "俯仰波束宽度 (度)",
                min_value=0.1,
                max_value=90.0,
                value=float(st.session_state.radar_edit_data.get('antenna', {}).get('elevation_beamwidth', 10.0)),
                step=0.1,
                key="elevation_slider"
            )
            st.session_state.radar_edit_data['antenna']['elevation_beamwidth'] = elevation_bw
            
            # 计算天线尺寸估计
            try:
                freq_hz = st.session_state.radar_edit_data.get('transmitter', {}).get('frequency_hz', 1e9)
                wavelength = 3e8 / freq_hz
                aperture_az = 70 * wavelength / azimuth_bw if azimuth_bw > 0 else 0
                aperture_el = 70 * wavelength / elevation_bw if elevation_bw > 0 else 0
                
                st.write(f"**天线尺寸估计:**")
                st.write(f"- 方位孔径: {aperture_az:.2f} m")
                st.write(f"- 俯仰孔径: {aperture_el:.2f} m")
            except Exception as e:
                st.warning("无法计算天线尺寸")
        
        # 天线类型建议
        self._show_antenna_recommendations(gain_dbi, azimuth_bw, elevation_bw)
    
    def _show_antenna_recommendations(self, gain: float, az_bw: float, el_bw: float):
        """显示天线建议"""
        if gain > 40:
            antenna_type = "高增益抛物面天线"
            tips = "• 适合远程预警\n• 波束窄、增益高\n• 机械扫描\n• 尺寸较大"
        elif gain > 30:
            antenna_type = "相控阵天线"
            tips = "• 电子扫描\n• 多波束能力\n• 适合多功能雷达\n• 成本较高"
        elif gain > 20:
            antenna_type = "平板裂缝天线"
            tips = "• 中等增益\n• 波束控制灵活\n• 适合机载平台\n• 重量较轻"
        else:
            antenna_type = "简单阵列天线"
            tips = "• 成本低\n• 适合近程应用\n• 波束较宽\n• 安装简便"
        
        st.info(f"**{antenna_type}**\n\n{tips}")
        
        # 波束宽度建议
        if az_bw < 1.0 or el_bw < 1.0:
            st.warning("波束宽度过窄，可能需要精密机械结构或相控阵技术")
        elif az_bw > 30.0 or el_bw > 30.0:
            st.warning("波束宽度较宽，可能影响角度分辨率和跟踪精度")
    
    def _render_signal_processing_parameters(self):
        """渲染信号处理参数部分"""
        st.markdown('<div class="param-section">🔧 信号处理参数</div>', 
                   unsafe_allow_html=True)
        
        # 确保编辑数据存在
        if st.session_state.radar_edit_data is None:
            st.error("编辑数据不存在")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # MTI滤波器类型
            mti_filter = st.selectbox(
                "MTI滤波器类型",
                options=['无', '3脉冲对消器', '自适应MTI', '自适应MTD', '高速目标MTD'],
                index=['无', '3脉冲对消器', '自适应MTI', '自适应MTD', '高速目标MTD'].index(
                    st.session_state.radar_edit_data.get('signal_processing', {}).get('mti_filter', '3脉冲对消器')
                ) if st.session_state.radar_edit_data.get('signal_processing', {}).get('mti_filter', '3脉冲对消器') in 
                ['无', '3脉冲对消器', '自适应MTI', '自适应MTD', '高速目标MTD'] else 1,  # 默认3脉冲对消器
                key="mti_filter_select"
            )
            st.session_state.radar_edit_data['signal_processing']['mti_filter'] = mti_filter
            
            # 多普勒通道数
            doppler_channels = st.selectbox(
                "多普勒通道数",
                options=[64, 128, 256, 512, 1024, 2048],
                index=[64, 128, 256, 512, 1024, 2048].index(
                    st.session_state.radar_edit_data.get('signal_processing', {}).get('doppler_channels', 256)
                ) if st.session_state.radar_edit_data.get('signal_processing', {}).get('doppler_channels', 256) in 
                [64, 128, 256, 512, 1024, 2048] else 2,  # 默认256
                key="doppler_channels_select"
            )
            st.session_state.radar_edit_data['signal_processing']['doppler_channels'] = doppler_channels
        
        with col2:
            # 最大跟踪目标数
            max_targets = st.number_input(
                "最大跟踪目标数",
                min_value=1,
                max_value=10000,
                value=int(st.session_state.radar_edit_data.get('signal_processing', {}).get('max_tracking_targets', 100)),
                step=10,
                key="max_targets_input"
            )
            st.session_state.radar_edit_data['signal_processing']['max_tracking_targets'] = max_targets
            
            # 处理增益估算
            processing_gain = doppler_channels * 10  # 简化估算
            st.write(f"**处理增益估算:** {processing_gain:.1f} dB")
        
        # 信号处理建议
        self._show_processing_recommendations(mti_filter, doppler_channels)
    
    def _show_processing_recommendations(self, mti_filter: str, doppler_channels: int):
        """显示信号处理建议"""
        if mti_filter == '无':
            tips = "• 适合简单应用\n• 处理复杂度低\n• 杂波抑制能力弱"
        elif '自适应' in mti_filter:
            tips = "• 杂波抑制能力强\n• 适合复杂环境\n• 处理复杂度高"
        else:
            tips = "• 平衡性能\n• 适合一般应用\n• 处理复杂度中等"
        
        st.info(f"**{mti_filter}**\n\n{tips}")
        
        if doppler_channels >= 1024:
            st.success("多普勒通道数充足，速度分辨率高")
        elif doppler_channels <= 128:
            st.warning("多普勒通道数较少，速度分辨率受限")
    
    def _render_preview_and_actions(self):
        """渲染预览和操作区域"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="preview-card">📊 雷达参数预览</div>', 
                       unsafe_allow_html=True)
            self._render_radar_preview()
        
        with col2:
            st.markdown("##### 操作")
            self._render_action_buttons()
    
    def _render_radar_preview(self):
        """渲染雷达参数预览"""
        # 确保编辑数据存在
        if st.session_state.radar_edit_data is None:
            st.error("无雷达参数可预览")
            return
        
        data = st.session_state.radar_edit_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**基本信息**")
            st.write(f"- 名称: {data.get('name', '未知')}")
            st.write(f"- ID: {data.get('radar_id', '未知')}")
            st.write(f"- 类型: {self._get_radar_type_display(data.get('type', 'early_warning'))}")
            st.write(f"- 平台: {data.get('platform', '未知')}")
            st.write(f"- 任务: {', '.join(data.get('mission_types', []))}")
        
        with col2:
            st.write("**技术参数**")
            st.write(f"- 频率: {format_frequency(data.get('transmitter', {}).get('frequency_hz', 0))}")
            st.write(f"- 功率: {format_power(data.get('transmitter', {}).get('power_w', 0))}")
            st.write(f"- 天线增益: {data.get('antenna', {}).get('gain_dbi', 0):.1f} dBi")
            st.write(f"- 波束宽度: {data.get('antenna', {}).get('azimuth_beamwidth', 0):.1f}° × {data.get('antenna', {}).get('elevation_beamwidth', 0):.1f}°")
        
        # 性能估算
        self._render_performance_estimate()
    
    def _get_radar_type_display(self, radar_type: str) -> str:
        """获取雷达类型显示名称"""
        type_map = {
            'early_warning': '预警雷达',
            'airborne': '机载雷达',
            'fire_control': '火控雷达', 
            'maritime': '海事雷达'
        }
        return type_map.get(radar_type, '未知类型')
    
    def _render_performance_estimate(self):
        """渲染性能估算"""
        try:
            # 确保编辑数据存在
            if st.session_state.radar_edit_data is None:
                st.warning("无数据用于性能估算")
                return
                
            # 使用控制器创建临时雷达进行性能估算
            success, message, temp_radar = self.controller.create_radar(
                st.session_state.radar_edit_data
            )
            
            if success and temp_radar:
                performance = self.controller.get_radar_performance(temp_radar.radar_id, use_cache=False)
                
                if performance:
                    st.write("**性能估算**")
                    st.write(f"- 最大探测距离: {performance.get('max_detection_range_km', 0):.1f} km")
                    st.write(f"- 距离分辨率: {performance.get('range_resolution_m', 0):.2f} m")
                    st.write(f"- 角分辨率: {performance.get('angular_resolution_deg', 0):.1f}°")
        except Exception as e:
            st.warning("性能估算暂时不可用")
    
    def _render_action_buttons(self):
        """渲染操作按钮"""
        # 验证数据
        is_valid, errors = self.validator.validate_radar_data(st.session_state.radar_edit_data)
        
        if not is_valid:
            st.error("参数验证失败:")
            for error in errors:
                st.write(f"• {error}")
        
        # 保存按钮
        if st.button("💾 保存雷达", type="primary", disabled=not is_valid, 
                    key="save_radar_btn"):
            self._save_radar()
        
        # 重置按钮
        if st.button("🔄 重置参数", key="reset_params_btn"):
            self._reset_parameters()
        
        # 取消按钮
        if st.button("❌ 取消编辑", key="cancel_edit_btn"):
            self._cancel_editing()
        
        # 从模板加载按钮
        if st.button("📁 从模板加载", key="load_template_btn"):
            self._load_from_template()
    
    def _save_radar(self):
        """保存雷达数据"""
        try:
            data = st.session_state.radar_edit_data
            
            # 检查是新建还是更新
            if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
                # 更新现有雷达
                success, message = self.controller.update_radar(
                    st.session_state.editing_radar_id, data
                )
            else:
                # 创建新雷达
                success, message, radar = self.controller.create_radar(data)
            
            if success:
                st.success(message)
                # 延迟返回主界面
                st.session_state.current_view = "dashboard"
                st.rerun()
            else:
                st.error(message)
        except Exception as e:
            st.error(f"保存雷达时发生错误: {str(e)}")
    
    def _reset_parameters(self):
        """重置参数为默认值"""
        if st.checkbox("确认重置所有参数？", key="confirm_reset_checkbox"):
            if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
                # 重新加载原始雷达数据
                self._load_existing_radar(st.session_state.editing_radar_id)
            else:
                # 重置为新雷达默认值
                self._initialize_new_radar()
            st.rerun()
    
    def _cancel_editing(self):
        """取消编辑"""
        if st.checkbox("确认取消编辑？未保存的更改将丢失", key="confirm_cancel_checkbox"):
            # 清除编辑状态
            if 'editing_radar_id' in st.session_state:
                del st.session_state.editing_radar_id
            if 'radar_edit_data' in st.session_state:
                del st.session_state.radar_edit_data
            
            st.session_state.current_view = "dashboard"
            st.rerun()
    
    def _load_from_template(self):
        """从模板加载雷达参数"""
        templates = {
            "预警雷达模板": {
                'type': 'early_warning',
                'platform': '地面机动',
                'mission_types': ['远程预警', '反隐身'],
                'transmitter': {'frequency_hz': 300e6, 'power_w': 500000, 'pulse_width_s': 200e-6},
                'antenna': {'gain_dbi': 35.0, 'azimuth_beamwidth': 3.5, 'elevation_beamwidth': 8.0},
                'signal_processing': {'mti_filter': '3脉冲对消器', 'doppler_channels': 256, 'max_tracking_targets': 512}
            },
            "机载雷达模板": {
                'type': 'airborne',
                'platform': '机载',
                'mission_types': ['空中预警', '指挥控制'],
                'transmitter': {'frequency_hz': 1.4e9, 'power_w': 10000, 'pulse_width_s': 50e-6},
                'antenna': {'gain_dbi': 38.0, 'azimuth_beamwidth': 1.2, 'elevation_beamwidth': 4.5},
                'signal_processing': {'mti_filter': '自适应MTI', 'doppler_channels': 512, 'max_tracking_targets': 1024}
            },
            "火控雷达模板": {
                'type': 'fire_control',
                'platform': '地面机动',
                'mission_types': ['火控'],
                'transmitter': {'frequency_hz': 4.2e9, 'power_w': 100000, 'pulse_width_s': 10e-6},
                'antenna': {'gain_dbi': 45.0, 'azimuth_beamwidth': 0.8, 'elevation_beamwidth': 0.8},
                'signal_processing': {'mti_filter': '高速目标MTD', 'doppler_channels': 2048, 'max_tracking_targets': 16}
            }
        }
        
        selected_template = st.selectbox("选择模板", list(templates.keys()), key="template_select")
        
        if st.button("加载模板", key="load_template_confirm_btn"):
            template = templates[selected_template]
            
            # 确保编辑数据存在
            if st.session_state.radar_edit_data is None:
                self._initialize_new_radar()
            
            # 更新当前编辑数据
            for key, value in template.items():
                if key in st.session_state.radar_edit_data:
                    if isinstance(value, dict):
                        st.session_state.radar_edit_data[key].update(value)
                    else:
                        st.session_state.radar_edit_data[key] = value
            
            st.success(f"已加载 {selected_template}")
            st.rerun()
    
    def _save_as_template(self):
        """保存当前设置为模板"""
        template_name = st.text_input("模板名称", value="自定义模板", key="template_name_input")
        
        if st.button("保存模板", key="save_template_btn"):
            # 这里可以实现模板保存逻辑（保存到文件或数据库）
            st.success(f"模板 '{template_name}' 保存成功")
    
    def render(self):
        """渲染完整编辑器"""
        self.render_header()
        self.render_editor()


def main():
    """主函数"""
    # 初始化编辑器视图
    editor = RadarEditorView()
    
    # 渲染编辑器
    editor.render()


if __name__ == "__main__":
    main()                



# """
# 雷达编辑器视图模块
# 提供雷达参数编辑和创建界面
# 使用Streamlit构建交互式编辑表单
# """

# import streamlit as st
# import numpy as np
# from typing import Dict, Any, Optional, List
# import sys
# import os

# # 添加项目根目录到路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# from models.radar_models import RadarModel, RadarBand, PlatformType, MissionType
# from controllers.radar_controller import RadarController, RadarDataValidator
# from utils.helpers import format_frequency, format_power, format_distance
# from utils.constants import DEFAULT_RADAR_PARAMS


# class RadarEditorView:
#     """雷达编辑器视图类"""
    
#     def __init__(self):
#         self.controller = RadarController()
#         self.validator = RadarDataValidator()
#         self.setup_page_config()
    
#     def setup_page_config(self):
#         """设置页面配置"""
#         st.set_page_config(
#             page_title="雷达编辑器 - 雷达工厂工厂",
#             page_icon="⚙️",
#             layout="wide"
#         )
        
#         # 自定义CSS样式
#         st.markdown("""
#         <style>
#         .editor-header {
#             font-size: 2rem;
#             color: #2E86AB;
#             border-bottom: 2px solid #2E86AB;
#             padding-bottom: 0.5rem;
#             margin-bottom: 1.5rem;
#         }
#         .param-section {
#             background-color: #f8f9fa;
#             padding: 1rem;
#             border-radius: 10px;
#             margin-bottom: 1rem;
#             border-left: 4px solid #2E86AB;
#         }
#         .preview-card {
#             background-color: #e8f4f8;
#             padding: 1rem;
#             border-radius: 10px;
#             border: 1px solid #2E86AB;
#         }
#         .warning-box {
#             background-color: #fff3cd;
#             border: 1px solid #ffc107;
#             border-radius: 5px;
#             padding: 0.75rem;
#             margin: 0.5rem 0;
#         }
#         </style>
#         """, unsafe_allow_html=True)
    
#     def render_header(self):
#         """渲染页面头部"""
#         st.markdown('<div class="editor-header">⚙️ 雷达参数编辑器</div>', 
#                    unsafe_allow_html=True)
        
#         # 显示当前编辑状态
#         col1, col2, col3 = st.columns([2, 1, 1])
        
#         with col1:
#             if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
#                 st.info(f"正在编辑雷达: {st.session_state.editing_radar_id}")
#             else:
#                 st.success("创建新雷达")
        
#         with col2:
#             if st.button("📋 返回主界面", width='stretch'):
#                 st.session_state.current_view = "dashboard"
#                 st.rerun()
        
#         with col3:
#             if st.button("💾 保存模板", width='stretch'):
#                 self._save_as_template()
    
#     def render_editor(self):
#         """渲染雷达编辑器"""
#         # 初始化编辑数据
#         if 'radar_edit_data' not in st.session_state:
#             if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
#                 # 编辑现有雷达
#                 self._load_existing_radar(st.session_state.editing_radar_id)
#             else:
#                 # 创建新雷达
#                 self._initialize_new_radar()
        
#         # 创建选项卡布局
#         tab1, tab2, tab3, tab4 = st.tabs([
#             "📝 基本参数", 
#             "📡 发射机参数", 
#             "📊 天线参数", 
#             "🔧 信号处理"
#         ])
        
#         with tab1:
#             self._render_basic_parameters()
        
#         with tab2:
#             self._render_transmitter_parameters()
        
#         with tab3:
#             self._render_antenna_parameters()
        
#         with tab4:
#             self._render_signal_processing_parameters()
        
#         # 预览和操作区域
#         st.markdown("---")
#         self._render_preview_and_actions()
    
#     def _load_existing_radar(self, radar_id: str):
#         """加载现有雷达数据"""
#         radar = self.controller.get_radar_by_id(radar_id)
#         if radar:
#             # 转换为编辑数据格式
#             st.session_state.radar_edit_data = {
#                 'radar_id': radar_id,
#                 'name': radar.name,
#                 'type': self._get_radar_type_string(radar),
#                 'platform': radar.platform.value,
#                 'mission_types': [mission.value for mission in radar.mission_types],
#                 'deployment_method': radar.deployment_method,
#                 'theoretical_range_km': radar.theoretical_range_km,
#                 'transmitter': {
#                     'frequency_hz': radar.transmitter.frequency_hz if radar.transmitter else 1e9,
#                     'power_w': radar.transmitter.power_w if radar.transmitter else 100000,
#                     'pulse_width_s': radar.transmitter.pulse_width_s if radar.transmitter else 100e-6,
#                     'prf_hz': radar.transmitter.prf_hz if radar.transmitter else 1000
#                 } if radar.transmitter else {},
#                 'antenna': {
#                     'gain_dbi': radar.antenna.gain_dbi if radar.antenna else 30.0,
#                     'azimuth_beamwidth': radar.antenna.azimuth_beamwidth if radar.antenna else 5.0,
#                     'elevation_beamwidth': radar.antenna.elevation_beamwidth if radar.antenna else 10.0
#                 } if radar.antenna else {},
#                 'signal_processing': {
#                     'mti_filter': radar.signal_processing.mti_filter if radar.signal_processing else '',
#                     'doppler_channels': radar.signal_processing.doppler_channels if radar.signal_processing else 256,
#                     'max_tracking_targets': radar.signal_processing.max_tracking_targets if radar.signal_processing else 100
#                 } if radar.signal_processing else {}
#             }
    
#     def _initialize_new_radar(self):
#         """初始化新雷达数据"""
#         st.session_state.radar_edit_data = {
#             'radar_id': f"RAD_{len(self.controller.get_all_radars()) + 1:04d}",
#             'name': '新建雷达',
#             'type': 'early_warning',
#             'platform': '地面机动',
#             'mission_types': ['远程预警'],
#             'deployment_method': '固定部署',
#             'theoretical_range_km': 200,
#             'transmitter': DEFAULT_RADAR_PARAMS['transmitter'].copy(),
#             'antenna': DEFAULT_RADAR_PARAMS['antenna'].copy(),
#             'signal_processing': DEFAULT_RADAR_PARAMS['signal_processing'].copy()
#         }
    
#     def _get_radar_type_string(self, radar) -> str:
#         """获取雷达类型字符串"""
#         class_name = radar.__class__.__name__
#         type_map = {
#             'EarlyWarningRadar': 'early_warning',
#             'AirborneRadar': 'airborne', 
#             'FireControlRadar': 'fire_control',
#             'MaritimeRadar': 'maritime'
#         }
#         return type_map.get(class_name, 'early_warning')
    
#     def _render_basic_parameters(self):
#         """渲染基本参数部分"""
#         st.markdown('<div class="param-section">📝 基本参数</div>', 
#                    unsafe_allow_html=True)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             # 雷达名称和ID
#             st.session_state.radar_edit_data['name'] = st.text_input(
#                 "雷达名称",
#                 value=st.session_state.radar_edit_data['name'],
#                 help="输入雷达的完整名称"
#             )
            
#             st.session_state.radar_edit_data['radar_id'] = st.text_input(
#                 "雷达ID",
#                 value=st.session_state.radar_edit_data['radar_id'],
#                 help="雷达的唯一标识符"
#             )
            
#             # 雷达类型
#             radar_type = st.selectbox(
#                 "雷达类型",
#                 options=['early_warning', 'airborne', 'fire_control', 'maritime'],
#                 format_func=lambda x: {
#                     'early_warning': '预警雷达',
#                     'airborne': '机载雷达', 
#                     'fire_control': '火控雷达',
#                     'maritime': '海事雷达'
#                 }[x],
#                 index=['early_warning', 'airborne', 'fire_control', 'maritime'].index(
#                     st.session_state.radar_edit_data['type']
#                 )
#             )
#             st.session_state.radar_edit_data['type'] = radar_type
        
#         with col2:
#             # 平台类型
#             platform = st.selectbox(
#                 "平台类型",
#                 options=['地面机动', '机载', '舰载', '固定阵地'],
#                 index=['地面机动', '机载', '舰载', '固定阵地'].index(
#                     st.session_state.radar_edit_data['platform']
#                 )
#             )
#             st.session_state.radar_edit_data['platform'] = platform
            
#             # 部署方式
#             st.session_state.radar_edit_data['deployment_method'] = st.text_input(
#                 "部署方式",
#                 value=st.session_state.radar_edit_data['deployment_method'],
#                 help="例如：固定部署、机动部署等"
#             )
            
#             # 理论探测距离
#             st.session_state.radar_edit_data['theoretical_range_km'] = st.number_input(
#                 "理论探测距离 (km)",
#                 min_value=1.0,
#                 max_value=1000.0,
#                 value=float(st.session_state.radar_edit_data['theoretical_range_km']),
#                 step=10.0
#             )
        
#         # 任务类型（多选）
#         st.subheader("任务类型")
#         mission_options = ['远程预警', '反隐身', '空中预警', '指挥控制', 
#                           '区域防空', '火控', '海事监视']
        
#         selected_missions = st.multiselect(
#             "选择雷达任务类型",
#             options=mission_options,
#             default=st.session_state.radar_edit_data['mission_types'],
#             help="可多选雷达的主要任务类型"
#         )
#         st.session_state.radar_edit_data['mission_types'] = selected_missions
        
#         # 根据雷达类型显示提示信息
#         self._show_radar_type_tips(radar_type)
    
#     def _show_radar_type_tips(self, radar_type: str):
#         """显示雷达类型提示信息"""
#         tips = {
#             'early_warning': {
#                 'title': '预警雷达特点',
#                 'content': '• 工作频段通常为UHF/L波段\n• 大功率、大天线孔径\n• 重点考虑反隐身能力\n• 适合远程预警任务'
#             },
#             'airborne': {
#                 'title': '机载雷达特点', 
#                 'content': '• 工作频段通常为L/S波段\n• 平台高度优势明显\n• 需要考虑平台运动影响\n• 适合空中预警和指挥控制'
#             },
#             'fire_control': {
#                 'title': '火控雷达特点',
#                 'content': '• 工作频段通常为C/X波段\n• 高精度、高数据率\n• 强调跟踪和制导能力\n• 适合末端防御和导弹引导'
#             },
#             'maritime': {
#                 'title': '海事雷达特点',
#                 'content': '• 工作频段广泛(S/X/Ku波段)\n• 需要良好的杂波抑制\n• 考虑海面多路径效应\n• 适合海上监视和目标检测'
#             }
#         }
        
#         tip = tips.get(radar_type, tips['early_warning'])
#         st.info(f"**{tip['title']}**\n\n{tip['content']}")
    
#     def _render_transmitter_parameters(self):
#         """渲染发射机参数部分"""
#         st.markdown('<div class="param-section">📡 发射机参数</div>', 
#                    unsafe_allow_html=True)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             # 工作频率
#             freq_hz = st.number_input(
#                 "工作频率 (Hz)",
#                 min_value=1e6,
#                 max_value=100e9,
#                 value=float(st.session_state.radar_edit_data['transmitter']['frequency_hz']),
#                 step=1e6,
#                 format="%.0f"
#             )
#             st.session_state.radar_edit_data['transmitter']['frequency_hz'] = freq_hz
#             st.write(f"**频率显示:** {format_frequency(freq_hz)}")
            
#             # 发射功率
#             power_w = st.number_input(
#                 "发射功率 (W)",
#                 min_value=1.0,
#                 max_value=10e6,
#                 value=float(st.session_state.radar_edit_data['transmitter']['power_w']),
#                 step=1000.0,
#                 format="%.0f"
#             )
#             st.session_state.radar_edit_data['transmitter']['power_w'] = power_w
#             st.write(f"**功率显示:** {format_power(power_w)}")
        
#         with col2:
#             # 脉冲宽度
#             pulse_width_s = st.number_input(
#                 "脉冲宽度 (秒)",
#                 min_value=1e-9,
#                 max_value=1.0,
#                 value=float(st.session_state.radar_edit_data['transmitter']['pulse_width_s']),
#                 step=1e-6,
#                 format="%.6f"
#             )
#             st.session_state.radar_edit_data['transmitter']['pulse_width_s'] = pulse_width_s
#             st.write(f"**脉冲宽度:** {pulse_width_s * 1e6:.2f} μs")
            
#             # 脉冲重复频率
#             prf_hz = st.number_input(
#                 "脉冲重复频率 (Hz)",
#                 min_value=1.0,
#                 max_value=100000.0,
#                 value=float(st.session_state.radar_edit_data['transmitter']['prf_hz']),
#                 step=100.0
#             )
#             st.session_state.radar_edit_data['transmitter']['prf_hz'] = prf_hz
        
#         # 频率建议
#         self._show_frequency_recommendations(freq_hz)
        
#         # 参数验证
#         self._validate_transmitter_parameters()
    
#     def _show_frequency_recommendations(self, frequency_hz: float):
#         """显示频率建议"""
#         freq_ghz = frequency_hz / 1e9
        
#         if freq_ghz < 0.3:
#             band = "UHF波段"
#             tips = "• 反隐身能力强\n• 大气衰减小\n• 适合远程预警\n• 天线尺寸较大"
#         elif freq_ghz < 1:
#             band = "L波段" 
#             tips = "• 平衡性较好\n• 适合预警机\n• 中等分辨率\n• 通用性强"
#         elif freq_ghz < 2:
#             band = "S波段"
#             tips = "• 多功能性\n• 适合区域防空\n• 分辨率适中\n• 应用广泛"
#         elif freq_ghz < 4:
#             band = "C波段"
#             tips = "• 跟踪精度高\n• 适合火控雷达\n• 抗干扰能力强\n• 大气衰减增加"
#         elif freq_ghz < 8:
#             band = "X波段"
#             tips = "• 分辨率高\n• 适合精密跟踪\n• 天线尺寸小\n• 大气衰减明显"
#         else:
#             band = "Ku波段及以上"
#             tips = "• 极高分辨率\n• 适合近程应用\n• 衰减严重\n• 雨衰影响大"
        
#         st.success(f"**{band}雷达**\n\n{tips}")
    
#     def _validate_transmitter_parameters(self):
#         """验证发射机参数"""
#         tx_params = st.session_state.radar_edit_data['transmitter']
#         is_valid, errors = self.validator.validate_transmitter_parameters(tx_params)
        
#         if not is_valid:
#             for error in errors:
#                 st.markdown(f'<div class="warning-box">⚠️ {error}</div>', 
#                            unsafe_allow_html=True)
    
#     def _render_antenna_parameters(self):
#         """渲染天线参数部分"""
#         st.markdown('<div class="param-section">📊 天线参数</div>', 
#                    unsafe_allow_html=True)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             # 天线增益
#             gain_dbi = st.slider(
#                 "天线增益 (dBi)",
#                 min_value=0.0,
#                 max_value=50.0,
#                 value=float(st.session_state.radar_edit_data['antenna']['gain_dbi']),
#                 step=0.1
#             )
#             st.session_state.radar_edit_data['antenna']['gain_dbi'] = gain_dbi
            
#             # 方位波束宽度
#             azimuth_bw = st.slider(
#                 "方位波束宽度 (度)",
#                 min_value=0.1,
#                 max_value=90.0,
#                 value=float(st.session_state.radar_edit_data['antenna']['azimuth_beamwidth']),
#                 step=0.1
#             )
#             st.session_state.radar_edit_data['antenna']['azimuth_beamwidth'] = azimuth_bw
        
#         with col2:
#             # 俯仰波束宽度
#             elevation_bw = st.slider(
#                 "俯仰波束宽度 (度)",
#                 min_value=0.1,
#                 max_value=90.0,
#                 value=float(st.session_state.radar_edit_data['antenna']['elevation_beamwidth']),
#                 step=0.1
#             )
#             st.session_state.radar_edit_data['antenna']['elevation_beamwidth'] = elevation_bw
            
#             # 计算天线尺寸估计
#             wavelength = 3e8 / st.session_state.radar_edit_data['transmitter']['frequency_hz']
#             aperture_az = 70 * wavelength / azimuth_bw if azimuth_bw > 0 else 0
#             aperture_el = 70 * wavelength / elevation_bw if elevation_bw > 0 else 0
            
#             st.write(f"**天线尺寸估计:**")
#             st.write(f"- 方位孔径: {aperture_az:.2f} m")
#             st.write(f"- 俯仰孔径: {aperture_el:.2f} m")
        
#         # 天线类型建议
#         self._show_antenna_recommendations(gain_dbi, azimuth_bw, elevation_bw)
    
#     def _show_antenna_recommendations(self, gain: float, az_bw: float, el_bw: float):
#         """显示天线建议"""
#         if gain > 40:
#             antenna_type = "高增益抛物面天线"
#             tips = "• 适合远程预警\n• 波束窄、增益高\n• 机械扫描\n• 尺寸较大"
#         elif gain > 30:
#             antenna_type = "相控阵天线"
#             tips = "• 电子扫描\n• 多波束能力\n• 适合多功能雷达\n• 成本较高"
#         elif gain > 20:
#             antenna_type = "平板裂缝天线"
#             tips = "• 中等增益\n• 波束控制灵活\n• 适合机载平台\n• 重量较轻"
#         else:
#             antenna_type = "简单阵列天线"
#             tips = "• 成本低\n• 适合近程应用\n• 波束较宽\n• 安装简便"
        
#         st.info(f"**{antenna_type}**\n\n{tips}")
        
#         # 波束宽度建议
#         if az_bw < 1.0 or el_bw < 1.0:
#             st.warning("波束宽度过窄，可能需要精密机械结构或相控阵技术")
#         elif az_bw > 30.0 or el_bw > 30.0:
#             st.warning("波束宽度较宽，可能影响角度分辨率和跟踪精度")
    
#     def _render_signal_processing_parameters(self):
#         """渲染信号处理参数部分"""
#         st.markdown('<div class="param-section">🔧 信号处理参数</div>', 
#                    unsafe_allow_html=True)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             # MTI滤波器类型
#             mti_filter = st.selectbox(
#                 "MTI滤波器类型",
#                 options=['无', '3脉冲对消器', '自适应MTI', '自适应MTD', '高速目标MTD'],
#                 index=['无', '3脉冲对消器', '自适应MTI', '自适应MTD', '高速目标MTD'].index(
#                     st.session_state.radar_edit_data['signal_processing']['mti_filter']
#                 ) if st.session_state.radar_edit_data['signal_processing']['mti_filter'] in 
#                 ['无', '3脉冲对消器', '自适应MTI', '自适应MTD', '高速目标MTD'] else 0
#             )
#             st.session_state.radar_edit_data['signal_processing']['mti_filter'] = mti_filter
            
#             # 多普勒通道数
#             doppler_channels = st.selectbox(
#                 "多普勒通道数",
#                 options=[64, 128, 256, 512, 1024, 2048],
#                 index=[64, 128, 256, 512, 1024, 2048].index(
#                     st.session_state.radar_edit_data['signal_processing']['doppler_channels']
#                 ) if st.session_state.radar_edit_data['signal_processing']['doppler_channels'] in 
#                 [64, 128, 256, 512, 1024, 2048] else 2  # 默认256
#             )
#             st.session_state.radar_edit_data['signal_processing']['doppler_channels'] = doppler_channels
        
#         with col2:
#             # 最大跟踪目标数
#             max_targets = st.number_input(
#                 "最大跟踪目标数",
#                 min_value=1,
#                 max_value=10000,
#                 value=int(st.session_state.radar_edit_data['signal_processing']['max_tracking_targets']),
#                 step=10
#             )
#             st.session_state.radar_edit_data['signal_processing']['max_tracking_targets'] = max_targets
            
#             # 处理增益估算
#             processing_gain = doppler_channels * 10  # 简化估算
#             st.write(f"**处理增益估算:** {processing_gain:.1f} dB")
        
#         # 信号处理建议
#         self._show_processing_recommendations(mti_filter, doppler_channels)
    
#     def _show_processing_recommendations(self, mti_filter: str, doppler_channels: int):
#         """显示信号处理建议"""
#         if mti_filter == '无':
#             tips = "• 适合简单应用\n• 处理复杂度低\n• 杂波抑制能力弱"
#         elif '自适应' in mti_filter:
#             tips = "• 杂波抑制能力强\n• 适合复杂环境\n• 处理复杂度高"
#         else:
#             tips = "• 平衡性能\n• 适合一般应用\n• 处理复杂度中等"
        
#         st.info(f"**{mti_filter}**\n\n{tips}")
        
#         if doppler_channels >= 1024:
#             st.success("多普勒通道数充足，速度分辨率高")
#         elif doppler_channels <= 128:
#             st.warning("多普勒通道数较少，速度分辨率受限")
    
#     def _render_preview_and_actions(self):
#         """渲染预览和操作区域"""
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             st.markdown('<div class="preview-card">📊 雷达参数预览</div>', 
#                        unsafe_allow_html=True)
#             self._render_radar_preview()
        
#         with col2:
#             st.markdown("### 操作")
#             self._render_action_buttons()
    
#     def _render_radar_preview(self):
#         """渲染雷达参数预览"""
#         data = st.session_state.radar_edit_data
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.write("**基本信息**")
#             st.write(f"- 名称: {data['name']}")
#             st.write(f"- ID: {data['radar_id']}")
#             st.write(f"- 类型: {self._get_radar_type_display(data['type'])}")
#             st.write(f"- 平台: {data['platform']}")
#             st.write(f"- 任务: {', '.join(data['mission_types'])}")
        
#         with col2:
#             st.write("**技术参数**")
#             st.write(f"- 频率: {format_frequency(data['transmitter']['frequency_hz'])}")
#             st.write(f"- 功率: {format_power(data['transmitter']['power_w'])}")
#             st.write(f"- 天线增益: {data['antenna']['gain_dbi']:.1f} dBi")
#             st.write(f"- 波束宽度: {data['antenna']['azimuth_beamwidth']:.1f}° × {data['antenna']['elevation_beamwidth']:.1f}°")
        
#         # 性能估算
#         self._render_performance_estimate()
    
#     def _get_radar_type_display(self, radar_type: str) -> str:
#         """获取雷达类型显示名称"""
#         type_map = {
#             'early_warning': '预警雷达',
#             'airborne': '机载雷达',
#             'fire_control': '火控雷达', 
#             'maritime': '海事雷达'
#         }
#         return type_map.get(radar_type, '未知类型')
    
#     def _render_performance_estimate(self):
#         """渲染性能估算"""
#         try:
#             # 使用控制器创建临时雷达进行性能估算
#             success, message, temp_radar = self.controller.create_radar(
#                 st.session_state.radar_edit_data
#             )
            
#             if success and temp_radar:
#                 performance = self.controller.get_radar_performance(temp_radar.radar_id, use_cache=False)
                
#                 if performance:
#                     st.write("**性能估算**")
#                     st.write(f"- 最大探测距离: {performance.get('max_detection_range_km', 0):.1f} km")
#                     st.write(f"- 距离分辨率: {performance.get('range_resolution_m', 0):.2f} m")
#                     st.write(f"- 角分辨率: {performance.get('angular_resolution_deg', 0):.1f}°")
#         except Exception as e:
#             st.warning("性能估算暂时不可用")
    
#     def _render_action_buttons(self):
#         """渲染操作按钮"""
#         # 验证数据
#         is_valid, errors = self.validator.validate_radar_data(st.session_state.radar_edit_data)
        
#         if not is_valid:
#             st.error("参数验证失败:")
#             for error in errors:
#                 st.write(f"• {error}")
        
#         # 保存按钮
#         if st.button("💾 保存雷达", type="primary", disabled=not is_valid, 
#                     width='stretch'):
#             self._save_radar()
        
#         # 重置按钮
#         if st.button("🔄 重置参数", width='stretch'):
#             self._reset_parameters()
        
#         # 取消按钮
#         if st.button("❌ 取消编辑", width='stretch'):
#             self._cancel_editing()
        
#         # 从模板加载按钮
#         if st.button("📁 从模板加载", width='stretch'):
#             self._load_from_template()
    
#     def _save_radar(self):
#         """保存雷达数据"""
#         try:
#             data = st.session_state.radar_edit_data
            
#             # 检查是新建还是更新
#             if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
#                 # 更新现有雷达
#                 success, message = self.controller.update_radar(
#                     st.session_state.editing_radar_id, data
#                 )
#             else:
#                 # 创建新雷达
#                 success, message, radar = self.controller.create_radar(data)
            
#             if success:
#                 st.success(message)
#                 # 延迟返回主界面
#                 st.session_state.current_view = "dashboard"
#                 st.rerun()
#             else:
#                 st.error(message)
#         except Exception as e:
#             st.error(f"保存雷达时发生错误: {str(e)}")
    
#     def _reset_parameters(self):
#         """重置参数为默认值"""
#         if st.checkbox("确认重置所有参数？"):
#             if 'editing_radar_id' in st.session_state and st.session_state.editing_radar_id:
#                 # 重新加载原始雷达数据
#                 self._load_existing_radar(st.session_state.editing_radar_id)
#             else:
#                 # 重置为新雷达默认值
#                 self._initialize_new_radar()
#             st.rerun()
    
#     def _cancel_editing(self):
#         """取消编辑"""
#         if st.checkbox("确认取消编辑？未保存的更改将丢失"):
#             # 清除编辑状态
#             if 'editing_radar_id' in st.session_state:
#                 del st.session_state.editing_radar_id
#             if 'radar_edit_data' in st.session_state:
#                 del st.session_state.radar_edit_data
            
#             st.session_state.current_view = "dashboard"
#             st.rerun()
    
#     def _load_from_template(self):
#         """从模板加载雷达参数"""
#         templates = {
#             "预警雷达模板": {
#                 'type': 'early_warning',
#                 'platform': '地面机动',
#                 'mission_types': ['远程预警', '反隐身'],
#                 'transmitter': {'frequency_hz': 300e6, 'power_w': 500000, 'pulse_width_s': 200e-6},
#                 'antenna': {'gain_dbi': 35.0, 'azimuth_beamwidth': 3.5, 'elevation_beamwidth': 8.0},
#                 'signal_processing': {'mti_filter': '3脉冲对消器', 'doppler_channels': 256, 'max_tracking_targets': 512}
#             },
#             "机载雷达模板": {
#                 'type': 'airborne',
#                 'platform': '机载',
#                 'mission_types': ['空中预警', '指挥控制'],
#                 'transmitter': {'frequency_hz': 1.4e9, 'power_w': 10000, 'pulse_width_s': 50e-6},
#                 'antenna': {'gain_dbi': 38.0, 'azimuth_beamwidth': 1.2, 'elevation_beamwidth': 4.5},
#                 'signal_processing': {'mti_filter': '自适应MTI', 'doppler_channels': 512, 'max_tracking_targets': 1024}
#             },
#             "火控雷达模板": {
#                 'type': 'fire_control',
#                 'platform': '地面机动',
#                 'mission_types': ['火控'],
#                 'transmitter': {'frequency_hz': 4.2e9, 'power_w': 100000, 'pulse_width_s': 10e-6},
#                 'antenna': {'gain_dbi': 45.0, 'azimuth_beamwidth': 0.8, 'elevation_beamwidth': 0.8},
#                 'signal_processing': {'mti_filter': '高速目标MTD', 'doppler_channels': 2048, 'max_tracking_targets': 16}
#             }
#         }
        
#         selected_template = st.selectbox("选择模板", list(templates.keys()))
        
#         if st.button("加载模板", width='stretch'):
#             template = templates[selected_template]
            
#             # 更新当前编辑数据
#             for key, value in template.items():
#                 if key in st.session_state.radar_edit_data:
#                     if isinstance(value, dict):
#                         st.session_state.radar_edit_data[key].update(value)
#                     else:
#                         st.session_state.radar_edit_data[key] = value
            
#             st.success(f"已加载 {selected_template}")
#             st.rerun()
    
#     def _save_as_template(self):
#         """保存当前设置为模板"""
#         template_name = st.text_input("模板名称", value="自定义模板")
        
#         if st.button("保存模板", width='stretch'):
#             # 这里可以实现模板保存逻辑（保存到文件或数据库）
#             st.success(f"模板 '{template_name}' 保存成功")
    
#     def render(self):
#         """渲染完整编辑器"""
#         self.render_header()
#         self.render_editor()


# # 常量定义
# DEFAULT_RADAR_PARAMS = {
#     'transmitter': {
#         'frequency_hz': 1e9,
#         'power_w': 100000,
#         'pulse_width_s': 100e-6,
#         'prf_hz': 1000
#     },
#     'antenna': {
#         'gain_dbi': 30.0,
#         'azimuth_beamwidth': 5.0,
#         'elevation_beamwidth': 10.0
#     },
#     'signal_processing': {
#         'mti_filter': '3脉冲对消器',
#         'doppler_channels': 256,
#         'max_tracking_targets': 100
#     }
# }


# def main():
#     """主函数"""
#     # 初始化编辑器视图
#     editor = RadarEditorView()
    
#     # 渲染编辑器
#     editor.render()


# if __name__ == "__main__":
#     main()        