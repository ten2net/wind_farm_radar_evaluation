"""
导出视图
数据导出和结果分享功能
支持多种格式导出，包括数据、图表、报告等
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import yaml
import csv
import pickle
from datetime import datetime
from pathlib import Path
import base64
import zipfile
from io import BytesIO, StringIO
from typing import Dict, Any, List, Optional, Tuple, Union
import sys
import os
import tempfile

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.antenna_models import AntennaParameters
from models.pattern_models import RadiationPattern, PatternStatistics
from services.visualization_service import get_visualization_service
from utils.config import AppConfig
from utils.helpers import format_frequency, format_gain, format_percentage

class ExportView:
    """导出视图类"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.viz_service = get_visualization_service()
        
    def render(self, sidebar_config: Dict[str, Any]):
        """渲染导出视图"""
        st.title("📤 数据导出与分享")
        
        # 检查是否有可导出的数据
        if not self._check_export_data():
            return
        
        # 创建导出标签页
        tab1, tab2, tab3, tab4 = st.tabs([
            "📁 数据导出", 
            "📈 图表导出", 
            "📄 报告生成",
            "🌐 在线分享"
        ])
        
        with tab1:
            self._render_data_export()
        
        with tab2:
            self._render_chart_export()
        
        with tab3:
            self._render_report_generation()
        
        with tab4:
            self._render_online_sharing()
    
    def _check_export_data(self) -> bool:
        """检查是否有可导出的数据"""
        has_data = False
        data_sources = []
        
        if 'current_antenna' in st.session_state and st.session_state.current_antenna:
            has_data = True
            data_sources.append("天线参数")
        
        if 'pattern_data' in st.session_state and st.session_state.pattern_data:
            has_data = True
            data_sources.append("方向图数据")
        
        if 'analysis_results' in st.session_state and st.session_state.analysis_results:
            has_data = True
            data_sources.append("分析结果")
        
        if 'comparative_analysis_results' in st.session_state and st.session_state.comparative_analysis_results:
            has_data = True
            data_sources.append("比较分析结果")
        
        if not has_data:
            st.warning("⚠️ 没有可导出的数据")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("""
                请先进行仿真和分析以生成导出数据：
                1. 在侧边栏配置天线参数
                2. 运行仿真生成方向图
                3. 运行分析获取结果
                4. 返回此页面导出数据
                """)
            
            with col2:
                if st.button("🚀 运行示例仿真", width='stretch', type="primary"):
                    self._run_example_simulation()
            
            return False
        
        # 显示可用数据源
        st.info(f"✅ 检测到可导出数据: {', '.join(data_sources)}")
        return True
    
    def _run_example_simulation(self):
        """运行示例仿真"""
        with st.spinner("正在运行示例仿真..."):
            # 使用示例天线
            from models.antenna_models import create_patch_antenna
            example_antenna = create_patch_antenna()
            
            # 生成方向图
            from services.pattern_generator import get_pattern_generator_service
            pattern_service = get_pattern_generator_service()
            pattern = pattern_service.generate_pattern(
                example_antenna,
                generator_type='analytical',
                theta_resolution=5,
                phi_resolution=5
            )
            
            # 运行分析
            from services.analysis_service import get_analysis_service
            analysis_service = get_analysis_service()
            results = analysis_service.comprehensive_analysis(pattern, example_antenna)
            
            # 保存到session
            st.session_state.current_antenna = example_antenna
            st.session_state.pattern_data = pattern
            st.session_state.analysis_results = results
            
            st.success("示例仿真完成！数据已准备好导出。")
            st.rerun()
    
    def _render_data_export(self):
        """渲染数据导出"""
        st.markdown("## 📁 数据导出")
        
        # 数据选择
        st.markdown("### 1. 选择导出数据")
        
        export_options = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_options['antenna_params'] = st.checkbox("天线参数", value=True)
            export_options['pattern_data'] = st.checkbox("方向图数据", value=True)
            export_options['pattern_stats'] = st.checkbox("方向图统计", value=True)
        
        with col2:
            export_options['analysis_results'] = st.checkbox("分析结果", value=True)
            export_options['comparison_results'] = st.checkbox("比较结果", value=True)
            export_options['config_data'] = st.checkbox("配置信息", value=True)
        
        # 导出格式
        st.markdown("### 2. 选择导出格式")
        
        format_col1, format_col2, format_col3 = st.columns(3)
        
        with format_col1:
            export_formats = st.multiselect(
                "数据格式",
                ["CSV", "JSON", "YAML", "Excel", "MATLAB (.mat)", "Python (.pkl)"],
                default=["CSV", "JSON"]
            )
        
        with format_col2:
            compression = st.checkbox("启用压缩", value=True)
            if compression:
                compress_level = st.slider("压缩级别", 1, 9, 6)
        
        with format_col3:
            include_metadata = st.checkbox("包含元数据", value=True)
            timestamp_format = st.selectbox(
                "时间戳格式",
                ["自动生成", "自定义"],
                index=0
            )
            
            if timestamp_format == "自定义":
                custom_timestamp = st.text_input("时间戳", datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        # 数据预览
        st.markdown("### 3. 数据预览")
        
        if st.button("👁️ 预览数据", width='stretch'):
            self._preview_export_data(export_options)
        
        # 导出控制
        st.markdown("### 4. 执行导出")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_name = st.text_input("导出文件名", "antenna_analysis_export")
        
        with col2:
            if st.button("📥 导出数据", type="primary", width='stretch'):
                with st.spinner("正在导出数据..."):
                    self._export_data(export_options, export_formats, export_name, 
                                     compression if 'compression' in locals() else True,
                                     compress_level if 'compress_level' in locals() else 6,
                                     include_metadata)
        
        with col3:
            if st.button("🧹 清除所有导出", width='stretch'):
                self._clear_export_files()
    
    def _preview_export_data(self, export_options: Dict[str, bool]):
        """预览导出数据"""
        preview_data = {}
        
        if export_options.get('antenna_params') and 'current_antenna' in st.session_state:
            antenna = st.session_state.current_antenna
            preview_data['antenna_parameters'] = antenna.to_dict()
        
        if export_options.get('pattern_data') and 'pattern_data' in st.session_state:
            pattern = st.session_state.pattern_data
            # 只预览部分数据
            preview_data['pattern_summary'] = {
                'frequency_ghz': pattern.frequency,
                'theta_resolution': pattern.theta_resolution,
                'phi_resolution': pattern.phi_resolution,
                'max_gain': np.max(pattern.gain_data)
            }
        
        if export_options.get('analysis_results') and 'analysis_results' in st.session_state:
            results = st.session_state.analysis_results
            # 提取关键结果
            preview_data['key_results'] = self._extract_key_results(results)
        
        if preview_data:
            st.json(preview_data, expanded=False)
        else:
            st.info("没有选择要导出的数据")
    
    def _extract_key_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """从分析结果中提取关键结果"""
        key_results = {}
        
        if 'beam' in results and 'beam_parameters' in results['beam']:
            beam_params = results['beam']['beam_parameters']
            key_results['peak_gain'] = beam_params.get('peak_gain', 0)
            key_results['beamwidth_3db'] = beam_params.get('main_lobe_width_3db_e', 0)
        
        if 'efficiency' in results and 'efficiency_parameters' in results['efficiency']:
            eff_params = results['efficiency']['efficiency_parameters']
            key_results['total_efficiency'] = eff_params.get('total_efficiency', 0)
        
        if 'overall_assessment' in results:
            assessment = results['overall_assessment']
            key_results['performance_score'] = assessment.get('performance_score', 0)
        
        return key_results
    
    def _export_data(self, export_options: Dict[str, bool], export_formats: List[str], 
                    export_name: str, compression: bool, compress_level: int,
                    include_metadata: bool):
        """执行数据导出"""
        try:
            # 准备导出数据
            export_data = self._prepare_export_data(export_options, include_metadata)
            
            if not export_data:
                st.error("没有可导出的数据")
                return
            
            # 为每种格式创建导出
            export_files = {}
            
            for fmt in export_formats:
                if fmt == "CSV":
                    csv_data = self._convert_to_csv(export_data)
                    export_files[f"{export_name}.csv"] = csv_data
                
                elif fmt == "JSON":
                    json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
                    export_files[f"{export_name}.json"] = json_data
                
                elif fmt == "YAML":
                    yaml_data = yaml.dump(export_data, default_flow_style=False, allow_unicode=True)
                    export_files[f"{export_name}.yaml"] = yaml_data
                
                elif fmt == "Excel":
                    excel_data = self._convert_to_excel(export_data)
                    export_files[f"{export_name}.xlsx"] = excel_data
                
                elif fmt == "MATLAB (.mat)":
                    mat_data = self._convert_to_matlab(export_data)
                    export_files[f"{export_name}.mat"] = mat_data
                
                elif fmt == "Python (.pkl)":
                    pkl_data = pickle.dumps(export_data)
                    export_files[f"{export_name}.pkl"] = pkl_data
            
            # 创建压缩包或单独文件
            if len(export_files) > 1 and compression:
                zip_buffer = self._create_zip_file(export_files, compress_level)
                self._download_file(zip_buffer, f"{export_name}.zip", "application/zip")
                st.success(f"已导出 {len(export_files)} 个文件到 {export_name}.zip")
            else:
                # 下载单个文件
                for filename, data in export_files.items():
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    self._download_file(data, filename, self._get_mime_type(filename))
                st.success(f"已导出 {len(export_files)} 个文件")
            
        except Exception as e:
            st.error(f"导出失败: {e}")
            st.exception(e)
    
    def _prepare_export_data(self, export_options: Dict[str, bool], 
                           include_metadata: bool) -> Dict[str, Any]:
        """准备导出数据"""
        export_data = {}
        
        # 添加元数据
        if include_metadata:
            export_data['metadata'] = {
                'export_timestamp': datetime.now().isoformat(),
                'export_version': '1.0',
                'software': 'Antenna Analysis Platform',
                'export_options': export_options
            }
        
        # 天线参数
        if export_options.get('antenna_params') and 'current_antenna' in st.session_state:
            antenna = st.session_state.current_antenna
            export_data['antenna_parameters'] = antenna.to_dict()
        
        # 方向图数据
        if export_options.get('pattern_data') and 'pattern_data' in st.session_state:
            pattern = st.session_state.pattern_data
            export_data['radiation_pattern'] = pattern.to_dict()
        
        # 方向图统计
        if export_options.get('pattern_stats') and 'pattern_data' in st.session_state:
            pattern = st.session_state.pattern_data
            stats = self._calculate_pattern_statistics(pattern)
            export_data['pattern_statistics'] = stats
        
        # 分析结果
        if export_options.get('analysis_results') and 'analysis_results' in st.session_state:
            results = st.session_state.analysis_results
            export_data['analysis_results'] = results
        
        # 比较结果
        if export_options.get('comparison_results') and 'comparative_analysis_results' in st.session_state:
            comp_results = st.session_state.comparative_analysis_results
            export_data['comparative_analysis'] = comp_results
        
        # 配置信息
        if export_options.get('config_data'):
            export_data['configuration'] = self._collect_config_data()
        
        return export_data
    
    def _calculate_pattern_statistics(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """计算方向图统计"""
        gain_data = pattern.gain_data
        
        return {
            'max_gain': float(np.max(gain_data)),
            'min_gain': float(np.min(gain_data)),
            'mean_gain': float(np.mean(gain_data)),
            'std_gain': float(np.std(gain_data)),
            'frequency_ghz': pattern.frequency,
            'theta_range': [float(pattern.theta_grid[0]), float(pattern.theta_grid[-1])],
            'phi_range': [float(pattern.phi_grid[0]), float(pattern.phi_grid[-1])],
            'theta_resolution': pattern.theta_resolution,
            'phi_resolution': pattern.phi_resolution
        }
    
    def _collect_config_data(self) -> Dict[str, Any]:
        """收集配置数据"""
        config_data = {}
        
        # 收集当前配置
        if 'current_antenna' in st.session_state:
            config_data['antenna_name'] = st.session_state.current_antenna.name
        
        # 添加系统配置
        config_data['system'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'export_timestamp': datetime.now().isoformat()
        }
        
        return config_data
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """转换为CSV格式"""
        output = StringIO()
        writer = csv.writer(output)
        
        # 扁平化数据结构
        flattened = self._flatten_dict(data)
        
        # 写入CSV
        writer.writerow(['Key', 'Value'])
        for key, value in flattened.items():
            writer.writerow([key, str(value)])
        
        return output.getvalue()
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', 
                     sep: str = '.') -> Dict[str, Any]:
        """扁平化嵌套字典"""
        items = {}
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key, sep))
            elif isinstance(v, list):
                # 处理列表
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.update(self._flatten_dict(item, f"{new_key}[{i}]", sep))
                    else:
                        items[f"{new_key}[{i}]"] = item
            else:
                items[new_key] = v
        
        return items
    
    def _convert_to_excel(self, data: Dict[str, Any]) -> bytes:
        """转换为Excel格式"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 创建不同的工作表
            if 'antenna_parameters' in data:
                df_antenna = pd.DataFrame([data['antenna_parameters']])
                df_antenna.to_excel(writer, sheet_name='天线参数', index=False)
            
            if 'pattern_statistics' in data:
                df_stats = pd.DataFrame([data['pattern_statistics']])
                df_stats.to_excel(writer, sheet_name='方向图统计', index=False)
            
            if 'analysis_results' in data:
                # 简化分析结果
                flat_results = self._flatten_dict(data['analysis_results'])
                df_results = pd.DataFrame(list(flat_results.items()), columns=['参数', '值'])
                df_results.to_excel(writer, sheet_name='分析结果', index=False)
            
            # 添加汇总表
            summary_data = self._create_summary_data(data)
            df_summary = pd.DataFrame(list(summary_data.items()), columns=['项目', '值'])
            df_summary.to_excel(writer, sheet_name='汇总', index=False)
        
        return output.getvalue()
    
    def _create_summary_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建汇总数据"""
        summary = {}
        
        if 'metadata' in data:
            summary['导出时间'] = data['metadata'].get('export_timestamp', '未知')
        
        if 'antenna_parameters' in data:
            antenna = data['antenna_parameters']
            summary['天线名称'] = antenna.get('name', '未知')
            summary['天线类型'] = antenna.get('antenna_type', '未知')
            summary['中心频率'] = f"{antenna.get('center_frequency', 0)} GHz"
        
        if 'pattern_statistics' in data:
            stats = data['pattern_statistics']
            summary['最大增益'] = f"{stats.get('max_gain', 0):.1f} dB"
            summary['平均增益'] = f"{stats.get('mean_gain', 0):.1f} dB"
        
        if 'analysis_results' in data and 'overall_assessment' in data['analysis_results']:
            assessment = data['analysis_results']['overall_assessment']
            score = assessment.get('performance_score', 0) * 100
            summary['性能评分'] = f"{score:.1f}%"
        
        return summary
    
    def _convert_to_matlab(self, data: Dict[str, Any]) -> bytes:
        """转换为MATLAB格式"""
        try:
            import scipy.io as sio
            import tempfile
            
            # 准备MATLAB兼容的数据
            mat_data = {}
            
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    # 对于复杂结构，保存为JSON字符串
                    mat_data[key] = json.dumps(value, ensure_ascii=False)
                else:
                    mat_data[key] = value
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix='.mat', delete=False) as tmp:
                sio.savemat(tmp.name, mat_data)
                with open(tmp.name, 'rb') as f:
                    matlab_data = f.read()
                
                # 清理临时文件
                os.unlink(tmp.name)
            
            return matlab_data
            
        except ImportError:
            st.warning("scipy库未安装，无法导出MATLAB格式")
            return b""
    
    def _create_zip_file(self, files: Dict[str, Union[str, bytes]], 
                        compress_level: int = 6) -> bytes:
        """创建ZIP文件"""
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED, 
                           compresslevel=compress_level) as zip_file:
            for filename, data in files.items():
                if isinstance(data, str):
                    data = data.encode('utf-8')
                zip_file.writestr(filename, data)
        
        return zip_buffer.getvalue()
    
    def _download_file(self, data: bytes, filename: str, mime_type: str):
        """提供文件下载"""
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">点击下载 {filename}</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    def _get_mime_type(self, filename: str) -> str:
        """获取MIME类型"""
        ext = filename.split('.')[-1].lower()
        
        mime_types = {
            'csv': 'text/csv',
            'json': 'application/json',
            'yaml': 'text/yaml',
            'yml': 'text/yaml',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'mat': 'application/octet-stream',
            'pkl': 'application/octet-stream',
            'zip': 'application/zip',
            'png': 'image/png',
            'pdf': 'application/pdf',
            'svg': 'image/svg+xml',
            'html': 'text/html'
        }
        
        return mime_types.get(ext, 'application/octet-stream')
    
    def _clear_export_files(self):
        """清除导出文件"""
        # 这里可以添加清理临时文件的逻辑
        st.info("导出文件清理功能")
    
    def _render_chart_export(self):
        """渲染图表导出"""
        st.markdown("## 📈 图表导出")
        
        # 图表选择
        st.markdown("### 1. 选择要导出的图表")
        
        available_charts = self._get_available_charts()
        
        selected_charts = []
        
        for chart_type, charts in available_charts.items():
            with st.expander(f"📊 {chart_type}图表", expanded=True):
                for chart in charts:
                    if st.checkbox(chart['name'], value=chart.get('default', False)):
                        selected_charts.append(chart)
        
        if not selected_charts:
            st.warning("请至少选择一个图表")
            return
        
        # 导出设置
        st.markdown("### 2. 导出设置")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            chart_formats = st.multiselect(
                "导出格式",
                ["PNG", "PDF", "SVG", "HTML", "JPEG"],
                default=["PNG", "PDF"]
            )
            
            dpi = st.slider("分辨率 (DPI)", 72, 600, 150, 72)
        
        with col2:
            fig_width = st.number_input("图宽 (像素)", 400, 4000, 1200, 100)
            fig_height = st.number_input("图高 (像素)", 300, 3000, 800, 100)
            
            theme = st.selectbox("主题", ["浅色", "深色", "系统默认"], index=0)
        
        with col3:
            include_title = st.checkbox("包含标题", value=True)
            include_legend = st.checkbox("包含图例", value=True)
            transparent_bg = st.checkbox("透明背景", value=False)
            
            batch_export = st.checkbox("批量导出", value=True)
        
        # 预览
        st.markdown("### 3. 图表预览")
        
        preview_chart = st.selectbox(
            "选择预览图表",
            [chart['name'] for chart in selected_charts],
            index=0
        )
        
        if st.button("👁️ 预览图表", width='stretch'):
            chart_to_preview = next((c for c in selected_charts if c['name'] == preview_chart), None)
            if chart_to_preview:
                self._preview_chart(chart_to_preview, fig_width, fig_height, theme)
        
        # 导出控制
        st.markdown("### 4. 执行导出")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_prefix = st.text_input("导出文件名前缀", "antenna_chart")
            
            if batch_export:
                zip_export = st.checkbox("打包为ZIP", value=True)
        
        with col2:
            if st.button("📤 导出图表", type="primary", width='stretch'):
                with st.spinner("正在生成和导出图表..."):
                    self._export_charts(selected_charts, chart_formats, export_prefix,
                                       fig_width, fig_height, dpi, theme,
                                       include_title, include_legend, transparent_bg,
                                       batch_export, zip_export if 'zip_export' in locals() else True)
    
    def _get_available_charts(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取可用的图表列表"""
        available_charts = {
            "方向图": [
                {"id": "pattern_2d_e", "name": "2D方向图 (E面)", "type": "2d", "default": True},
                {"id": "pattern_2d_h", "name": "2D方向图 (H面)", "type": "2d", "default": True},
                {"id": "pattern_3d", "name": "3D方向图", "type": "3d", "default": True},
                {"id": "pattern_polar", "name": "极坐标方向图", "type": "polar", "default": False}
            ],
            "分析": [
                {"id": "beam_analysis", "name": "波束分析图", "type": "analysis", "default": True},
                {"id": "polarization_analysis", "name": "极化分析图", "type": "analysis", "default": False},
                {"id": "efficiency_analysis", "name": "效率分析图", "type": "analysis", "default": False}
            ],
            "比较": [
                {"id": "comparison_chart", "name": "性能比较图", "type": "comparison", "default": True},
                {"id": "radar_chart", "name": "雷达比较图", "type": "comparison", "default": False}
            ],
            "统计": [
                {"id": "statistics_summary", "name": "统计摘要图", "type": "statistics", "default": True},
                {"id": "performance_gauge", "name": "性能仪表盘", "type": "statistics", "default": False}
            ]
        }
        
        return available_charts
    
    def _preview_chart(self, chart_info: Dict[str, Any], 
                      width: int, height: int, theme: str):
        """预览图表"""
        try:
            # 生成图表
            fig = self._generate_chart(chart_info, width, height, theme)
            
            if fig:
                st.plotly_chart(fig, width='stretch')
            else:
                st.warning("无法生成图表预览")
                
        except Exception as e:
            st.error(f"生成图表预览失败: {e}")
    
    def _generate_chart(self, chart_info: Dict[str, Any], 
                       width: int, height: int, theme: str) -> Optional[go.Figure]:
        """生成图表"""
        chart_id = chart_info['id']
        
        try:
            if chart_id == "pattern_2d_e":
                return self._create_2d_pattern_chart('elevation', width, height, theme)
            
            elif chart_id == "pattern_2d_h":
                return self._create_2d_pattern_chart('azimuth', width, height, theme)
            
            elif chart_id == "pattern_3d":
                return self._create_3d_pattern_chart(width, height, theme)
            
            elif chart_id == "beam_analysis":
                return self._create_beam_analysis_chart(width, height, theme)
            
            elif chart_id == "comparison_chart":
                return self._create_comparison_chart(width, height, theme)
            
            elif chart_id == "statistics_summary":
                return self._create_statistics_chart(width, height, theme)
            
            else:
                # 生成默认图表
                return self._create_default_chart(chart_info['name'], width, height, theme)
                
        except Exception as e:
            st.error(f"生成图表 {chart_info['name']} 失败: {e}")
            return None
    
    def _create_2d_pattern_chart(self, plane: str, width: int, 
                                height: int, theme: str) -> Optional[go.Figure]:
        """创建2D方向图"""
        if 'pattern_data' not in st.session_state:
            return None
        
        pattern = st.session_state.pattern_data
        
        # 获取切面
        if plane == 'elevation':
            fixed_angle = 0
            slice_data = pattern.get_slice(fixed_phi=fixed_angle)
            plane_name = "E面"
        else:
            fixed_angle = 90
            slice_data = pattern.get_slice(fixed_theta=fixed_angle)
            plane_name = "H面"
        
        # 创建图表
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=slice_data.angles,
            y=slice_data.values,
            mode='lines',
            name=f'{plane_name}方向图',
            line=dict(color='blue', width=3)
        ))
        
        # 标记峰值
        peak_idx = np.argmax(slice_data.values)
        peak_angle = slice_data.angles[peak_idx]
        peak_value = slice_data.values[peak_idx]
        
        fig.add_trace(go.Scatter(
            x=[peak_angle],
            y=[peak_value],
            mode='markers+text',
            name='峰值',
            marker=dict(color='red', size=10),
            text=[f'{peak_value:.1f} dB'],
            textposition='top center'
        ))
        
        # 更新布局
        fig.update_layout(
            title=f'{plane_name}方向图 (固定角度: {fixed_angle}°)',
            xaxis_title='角度 (°)',
            yaxis_title='增益 (dB)',
            width=width,
            height=height,
            template=self._get_plotly_theme(theme),
            showlegend=True
        )
        
        return fig
    
    def _create_3d_pattern_chart(self, width: int, height: int, 
                                theme: str) -> Optional[go.Figure]:
        """创建3D方向图"""
        if 'pattern_data' not in st.session_state:
            return None
        
        pattern = st.session_state.pattern_data
        
        theta = pattern.theta_grid
        phi = pattern.phi_grid
        gain_data = pattern.gain_data
        
        # 转换为直角坐标
        theta_rad = np.deg2rad(theta)
        phi_rad = np.deg2rad(phi)
        
        x = np.outer(np.sin(theta_rad), np.cos(phi_rad))
        y = np.outer(np.sin(theta_rad), np.sin(phi_rad))
        z = np.outer(np.cos(theta_rad), np.ones_like(phi_rad))
        
        # 缩放以显示增益
        scale_factor = 10**(gain_data/20)  # 转换为线性
        x_scaled = x * scale_factor
        y_scaled = y * scale_factor
        z_scaled = z * scale_factor
        
        # 创建3D表面图
        fig = go.Figure(data=[
            go.Surface(
                x=x_scaled,
                y=y_scaled,
                z=z_scaled,
                surfacecolor=gain_data,
                colorscale='Viridis',
                opacity=0.8,
                showscale=True,
                colorbar=dict(title='增益 (dB)')
            )
        ])
        
        fig.update_layout(
            title='3D方向图',
            width=width,
            height=height,
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                aspectmode='data'
            ),
            template=self._get_plotly_theme(theme)
        )
        
        return fig
    
    def _create_beam_analysis_chart(self, width: int, height: int, 
                                   theme: str) -> Optional[go.Figure]:
        """创建波束分析图"""
        if 'analysis_results' not in st.session_state:
            return None
        
        results = st.session_state.analysis_results
        
        if 'beam' not in results:
            return None
        
        beam_results = results['beam']
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('波束宽度', '副瓣电平', '波束形状', '对称性'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'scatter'}, {'type': 'indicator'}]]
        )
        
        # 1. 波束宽度
        if 'beamwidths' in beam_results:
            beamwidths = beam_results['beamwidths']
            levels = []
            widths = []
            
            for key, value in beamwidths.items():
                if 'beamwidth' in key and 'db' in key:
                    # 提取电平
                    level = key.replace('beamwidth_', '').replace('db_e', '').replace('db_h', '')
                    if level.isdigit():
                        levels.append(f'{level}dB')
                        widths.append(value)
            
            if levels and widths:
                fig.add_trace(
                    go.Bar(x=levels, y=widths, name='波束宽度', marker_color='blue'),
                    row=1, col=1
                )
        
        # 2. 副瓣电平
        if 'sidelobes' in beam_results:
            sidelobes = beam_results['sidelobes']
            
            sidelobe_data = [
                sidelobes.get('max_sidelobe_level_e', 0),
                sidelobes.get('max_sidelobe_level_h', 0),
                sidelobes.get('first_sidelobe_level_e', 0),
                sidelobes.get('first_sidelobe_level_h', 0)
            ]
            
            sidelobe_labels = ['最大副瓣E', '最大副瓣H', '第一副瓣E', '第一副瓣H']
            
            fig.add_trace(
                go.Bar(x=sidelobe_labels, y=sidelobe_data, name='副瓣电平', marker_color='red'),
                row=1, col=2
            )
        
        # 3. 波束形状
        if 'pattern_data' in st.session_state:
            pattern = st.session_state.pattern_data
            e_slice = pattern.get_slice(fixed_phi=0)
            h_slice = pattern.get_slice(fixed_theta=90)
            
            fig.add_trace(
                go.Scatter(x=e_slice.angles, y=e_slice.values, name='E面', mode='lines'),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=h_slice.angles, y=h_slice.values, name='H面', mode='lines'),
                row=2, col=1
            )
        
        # 4. 对称性指示器
        if 'beam_parameters' in beam_results:
            beam_params = beam_results['beam_parameters']
            if 'symmetry_e' in beam_params and 'symmetry_error' in beam_params['symmetry_e']:
                symmetry_error = beam_params['symmetry_e']['symmetry_error']
                # 转换为0-100的对称性分数
                symmetry_score = max(0, 100 - symmetry_error * 10)
                
                fig.add_trace(
                    go.Indicator(
                        mode="gauge+number",
                        value=symmetry_score,
                        title={'text': "对称性"},
                        domain={'row': 2, 'col': 2},
                        gauge={'axis': {'range': [0, 100]}}
                    ),
                    row=2, col=2
                )
        
        # 更新布局
        fig.update_layout(
            title='波束分析',
            width=width,
            height=height,
            template=self._get_plotly_theme(theme),
            showlegend=True
        )
        
        return fig
    
    def _create_comparison_chart(self, width: int, height: int, 
                                theme: str) -> Optional[go.Figure]:
        """创建比较图"""
        if 'comparative_analysis_results' not in st.session_state:
            return None
        
        comp_results = st.session_state.comparative_analysis_results
        
        if 'analysis_results' not in comp_results:
            return None
        
        analysis_results = comp_results['analysis_results']
        
        # 提取关键指标
        metrics_data = {}
        for name, data in analysis_results.items():
            if 'metrics' in data:
                metrics_data[name] = data['metrics']
        
        if not metrics_data:
            return None
        
        # 创建条形图
        fig = go.Figure()
        
        metrics = list(next(iter(metrics_data.values())).keys())
        
        for metric in metrics:
            values = [data.get(metric, 0) for data in metrics_data.values()]
            names = list(metrics_data.keys())
            
            fig.add_trace(go.Bar(
                x=names,
                y=values,
                name=metric
            ))
        
        fig.update_layout(
            title='性能比较',
            xaxis_title='天线/配置',
            yaxis_title='数值',
            width=width,
            height=height,
            template=self._get_plotly_theme(theme),
            barmode='group'
        )
        
        return fig
    
    def _create_statistics_chart(self, width: int, height: int, 
                                theme: str) -> Optional[go.Figure]:
        """创建统计图"""
        if 'analysis_results' not in st.session_state:
            return None
        
        results = st.session_state.analysis_results
        
        # 提取关键统计数据
        stats_data = {}
        
        if 'beam' in results and 'beam_parameters' in results['beam']:
            beam_params = results['beam']['beam_parameters']
            stats_data['峰值增益'] = beam_params.get('peak_gain', 0)
            stats_data['3dB波束宽度'] = beam_params.get('main_lobe_width_3db_e', 0)
        
        if 'beam' in results and 'sidelobes' in results['beam']:
            sidelobes = results['beam']['sidelobes']
            stats_data['最大副瓣电平'] = sidelobes.get('max_sidelobe_level_e', 0)
        
        if 'efficiency' in results and 'efficiency_parameters' in results['efficiency']:
            eff_params = results['efficiency']['efficiency_parameters']
            stats_data['总效率'] = eff_params.get('total_efficiency', 0) * 100
        
        if 'overall_assessment' in results:
            assessment = results['overall_assessment']
            stats_data['性能评分'] = assessment.get('performance_score', 0) * 100
        
        if not stats_data:
            return None
        
        # 创建水平条形图
        fig = go.Figure(data=[
            go.Bar(
                x=list(stats_data.values()),
                y=list(stats_data.keys()),
                orientation='h',
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            title='性能统计摘要',
            xaxis_title='数值',
            yaxis_title='参数',
            width=width,
            height=height,
            template=self._get_plotly_theme(theme)
        )
        
        return fig
    
    def _create_default_chart(self, title: str, width: int, 
                             height: int, theme: str) -> go.Figure:
        """创建默认图表"""
        # 生成示例数据
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        fig = go.Figure(data=[
            go.Scatter(x=x, y=y, mode='lines', name='示例数据')
        ])
        
        fig.update_layout(
            title=title,
            width=width,
            height=height,
            template=self._get_plotly_theme(theme)
        )
        
        return fig
    
    def _get_plotly_theme(self, theme: str) -> str:
        """获取Plotly主题"""
        themes = {
            "浅色": "plotly_white",
            "深色": "plotly_dark",
            "系统默认": "plotly"
        }
        return themes.get(theme, "plotly")
    
    def _export_charts(self, charts: List[Dict[str, Any]], formats: List[str], 
                      prefix: str, width: int, height: int, dpi: int, theme: str,
                      include_title: bool, include_legend: bool, transparent_bg: bool,
                      batch_export: bool, zip_export: bool):
        """导出图表"""
        try:
            export_files = {}
            
            for chart_info in charts:
                # 生成图表
                fig = self._generate_chart(chart_info, width, height, theme)
                
                if not fig:
                    st.warning(f"无法生成图表: {chart_info['name']}")
                    continue
                
                # 调整图表
                if not include_title:
                    fig.update_layout(title=None)
                if not include_legend:
                    fig.update_layout(showlegend=False)
                
                # 为每种格式导出
                chart_name = chart_info['name'].replace(' ', '_').lower()
                
                for fmt in formats:
                    if fmt == "PNG":
                        img_data = fig.to_image(format="png", width=width, 
                                               height=height, scale=dpi/72)
                        export_files[f"{prefix}_{chart_name}.png"] = img_data
                    
                    elif fmt == "PDF":
                        img_data = fig.to_image(format="pdf", width=width, 
                                               height=height)
                        export_files[f"{prefix}_{chart_name}.pdf"] = img_data
                    
                    elif fmt == "SVG":
                        img_data = fig.to_image(format="svg", width=width, 
                                               height=height)
                        export_files[f"{prefix}_{chart_name}.svg"] = img_data
                    
                    elif fmt == "HTML":
                        html_data = fig.to_html(include_plotlyjs='cdn', full_html=True)
                        export_files[f"{prefix}_{chart_name}.html"] = html_data
                    
                    elif fmt == "JPEG":
                        img_data = fig.to_image(format="jpeg", width=width, 
                                               height=height, scale=dpi/72)
                        export_files[f"{prefix}_{chart_name}.jpg"] = img_data
            
            if not export_files:
                st.error("没有生成任何导出文件")
                return
            
            # 提供下载
            if len(export_files) > 1 and (batch_export or zip_export):
                zip_buffer = self._create_zip_file(export_files)
                self._download_file(zip_buffer, f"{prefix}_charts.zip", "application/zip")
                st.success(f"已导出 {len(export_files)} 个图表文件到 {prefix}_charts.zip")
            else:
                # 下载单个文件
                for filename, data in export_files.items():
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    self._download_file(data, filename, self._get_mime_type(filename))
                st.success(f"已导出 {len(export_files)} 个图表文件")
            
        except Exception as e:
            st.error(f"导出图表失败: {e}")
            st.exception(e)
    
    def _render_report_generation(self):
            """渲染报告生成"""
            st.markdown("## 📄 报告生成")
            
            # 报告类型选择
            st.markdown("### 1. 选择报告类型")
            
            col1, col2 = st.columns(2)
            
            with col1:
                report_type = st.selectbox(
                    "报告类型",
                    ["技术分析报告", "设计总结报告", "性能评估报告", "完整详细报告", "自定义报告"],
                    index=0,
                    key="report_type_selectbox"
                )
                
                report_language = st.selectbox(
                    "报告语言",
                    ["中文", "英文", "中英双语"],
                    index=0,
                    key="report_language_selectbox"
                )
            
            with col2:
                report_template = st.selectbox(
                    "报告模板",
                    ["标准模板", "学术模板", "企业模板", "简洁模板", "自定义模板"],
                    index=0,
                    key="report_template_selectbox"
                )
                
                include_appendix = st.checkbox("包含附录", value=True, key="include_appendix_checkbox")
            
            # 报告内容
            st.markdown("### 2. 配置报告内容")
            
            content_options = {}
            
            with st.expander("📋 报告章节", expanded=True):
                # 为每个checkbox添加唯一的key
                content_options['executive_summary'] = st.checkbox(
                    "执行摘要", value=True, key="executive_summary_checkbox"
                )
                content_options['introduction'] = st.checkbox(
                    "引言", value=True, key="introduction_checkbox"
                )
                content_options['methodology'] = st.checkbox(
                    "分析方法", value=True, key="methodology_checkbox"
                )
                content_options['results'] = st.checkbox(
                    "结果分析", value=True, key="results_checkbox"
                )
                content_options['discussion'] = st.checkbox(
                    "讨论", value=False, key="discussion_checkbox"
                )
                content_options['conclusion'] = st.checkbox(
                    "结论", value=True, key="conclusion_checkbox"
                )
                content_options['recommendations'] = st.checkbox(
                    "建议", value=True, key="recommendations_checkbox"
                )
            
            with st.expander("📊 数据内容", expanded=True):
                # 为每个checkbox添加唯一的key
                content_options['antenna_specs'] = st.checkbox(
                    "天线规格", value=True, key="antenna_specs_checkbox"
                )
                content_options['pattern_data'] = st.checkbox(
                    "方向图数据", value=True, key="pattern_data_checkbox"
                )
                content_options['analysis_results'] = st.checkbox(
                    "分析结果", value=True, key="analysis_results_checkbox"
                )
                content_options['comparisons'] = st.checkbox(
                    "比较分析", value=False, key="comparisons_checkbox"
                )
                content_options['charts'] = st.checkbox(
                    "图表", value=True, key="charts_checkbox"
                )
            
            with st.expander("📈 图表设置", expanded=False):
                chart_quality = st.selectbox(
                    "图表质量", ["标准", "高清", "印刷质量"], 
                    index=0, key="chart_quality_selectbox"
                )
                chart_style = st.selectbox(
                    "图表风格", ["专业", "学术", "简洁", "彩色"], 
                    index=0, key="chart_style_selectbox"
                )
                max_charts = st.slider(
                    "最大图表数量", 1, 20, 10, key="max_charts_slider"
                )
            
            # 报告格式
            st.markdown("### 3. 选择报告格式")
            
            format_col1, format_col2 = st.columns(2)
            
            with format_col1:
                report_formats = st.multiselect(
                    "输出格式",
                    ["PDF", "Word (.docx)", "HTML", "Markdown", "LaTeX"],
                    default=["PDF", "Word (.docx)"],
                    key="report_formats_multiselect"
                )
            
            with format_col2:
                page_size = st.selectbox(
                    "页面尺寸", ["A4", "Letter", "A3"], 
                    index=0, key="page_size_selectbox"
                )
                orientation = st.radio(
                    "页面方向", ["纵向", "横向"], 
                    horizontal=True, key="orientation_radio"
                )
                
                include_toc = st.checkbox(
                    "包含目录", value=True, key="include_toc_checkbox"
                )
                page_numbers = st.checkbox(
                    "包含页码", value=True, key="page_numbers_checkbox"
                )
            
            # 报告预览
            st.markdown("### 4. 报告预览")
            
            if st.button("👁️ 预览报告大纲", width='stretch', key="preview_report_button"):
                self._preview_report_outline(report_type, content_options)
            
            # 生成报告
            st.markdown("### 5. 生成报告")
            
            col1, col2 = st.columns(2)
            
            with col1:
                report_title = st.text_input(
                    "报告标题", "天线分析报告", key="report_title_input"
                )
                report_author = st.text_input(
                    "作者", "天线分析平台", key="report_author_input"
                )
                from datetime import datetime
                report_date = st.date_input(
                    "报告日期", datetime.now().date(), key="report_date_input"
                )
            
            with col2:
                if st.button("📄 生成报告", type="primary", width='stretch', key="generate_report_button"):
                    with st.spinner("正在生成报告..."):
                        self._generate_report(
                            report_type, report_formats, report_title,
                            report_author, report_date, content_options,
                            page_size, orientation, include_toc, page_numbers
                        )
    
    def _preview_report_outline(self, report_type: str, 
                               content_options: Dict[str, bool]):
        """预览报告大纲"""
        st.markdown("### 📋 报告大纲预览")
        
        outline = ["# 天线分析报告"]
        
        if content_options.get('executive_summary'):
            outline.append("## 执行摘要")
        
        if content_options.get('introduction'):
            outline.append("## 1. 引言")
            outline.append("### 1.1 研究背景")
            outline.append("### 1.2 研究目的")
        
        if content_options.get('methodology'):
            outline.append("## 2. 分析方法")
            outline.append("### 2.1 天线模型")
            outline.append("### 2.2 仿真设置")
            outline.append("### 2.3 分析指标")
        
        if content_options.get('results'):
            outline.append("## 3. 结果分析")
            
            if content_options.get('antenna_specs'):
                outline.append("### 3.1 天线规格")
            
            if content_options.get('pattern_data'):
                outline.append("### 3.2 方向图特性")
            
            if content_options.get('analysis_results'):
                outline.append("### 3.3 性能分析")
                outline.append("#### 3.3.1 波束特性")
                outline.append("#### 3.3.2 极化特性")
                outline.append("#### 3.3.3 效率分析")
            
            if content_options.get('comparisons'):
                outline.append("### 3.4 比较分析")
        
        if content_options.get('discussion'):
            outline.append("## 4. 讨论")
            outline.append("### 4.1 结果解释")
            outline.append("### 4.2 影响因素")
            outline.append("### 4.3 局限性")
        
        if content_options.get('conclusion'):
            outline.append("## 5. 结论")
        
        if content_options.get('recommendations'):
            outline.append("## 6. 建议")
            outline.append("### 6.1 设计优化建议")
            outline.append("### 6.2 应用建议")
        
        if content_options.get('charts'):
            outline.append("## 附录")
            outline.append("### 附录A: 图表汇总")
        
        # 显示大纲
        for item in outline:
            if item.startswith("# "):
                st.markdown(f"**{item}**")
            elif item.startswith("## "):
                st.markdown(f"  {item}")
            elif item.startswith("### "):
                st.markdown(f"    {item}")
            elif item.startswith("#### "):
                st.markdown(f"      {item}")
            else:
                st.markdown(item)
    
    def _generate_report(self, report_type: str, report_formats: List[str],
                        title: str, author: str, date: datetime.date,
                        content_options: Dict[str, bool], page_size: str,
                        orientation: str, include_toc: bool, page_numbers: bool):
        """生成报告"""
        try:
            # 这里应该实现具体的报告生成逻辑
            # 由于报告生成比较复杂，这里只提供一个示例
            
            st.info("报告生成功能开发中...")
            
            # 示例：生成Markdown报告
            if "Markdown" in report_formats:
                md_report = self._generate_markdown_report(title, author, date, content_options)
                
                # 提供下载
                self._download_file(
                    md_report.encode('utf-8'),
                    f"{title.replace(' ', '_')}.md",
                    "text/markdown"
                )
            
            # 示例：生成HTML报告
            if "HTML" in report_formats:
                html_report = self._generate_html_report(title, author, date, content_options)
                
                self._download_file(
                    html_report.encode('utf-8'),
                    f"{title.replace(' ', '_')}.html",
                    "text/html"
                )
            
            st.success("报告生成完成！")
            
        except Exception as e:
            st.error(f"生成报告失败: {e}")
    
    def _generate_markdown_report(self, title: str, author: str, 
                                 date: datetime.date, 
                                 content_options: Dict[str, bool]) -> str:
        """生成Markdown报告"""
        report_lines = []
        
        # 标题页
        report_lines.append(f"# {title}")
        report_lines.append("")
        report_lines.append(f"**作者**: {author}")
        report_lines.append(f"**日期**: {date.strftime('%Y年%m月%d日')}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # 执行摘要
        if content_options.get('executive_summary'):
            report_lines.append("## 执行摘要")
            report_lines.append("")
            report_lines.append("本报告对天线的辐射特性进行了全面分析，包括方向图、增益、波束宽度、极化特性、效率等关键参数。")
            report_lines.append("")
            
            # 添加关键结果
            if 'analysis_results' in st.session_state:
                results = st.session_state.analysis_results
                if 'overall_assessment' in results:
                    assessment = results['overall_assessment']
                    score = assessment.get('performance_score', 0) * 100
                    report_lines.append(f"**性能评分**: {score:.1f}%")
                    report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        # 引言
        if content_options.get('introduction'):
            report_lines.append("## 1. 引言")
            report_lines.append("")
            report_lines.append("### 1.1 研究背景")
            report_lines.append("天线是无线通信系统的关键组成部分，其性能直接影响通信质量。")
            report_lines.append("")
            report_lines.append("### 1.2 研究目的")
            report_lines.append("本报告旨在分析天线的辐射特性，评估其性能，为设计和优化提供依据。")
            report_lines.append("")
        
        # 分析方法
        if content_options.get('methodology'):
            report_lines.append("## 2. 分析方法")
            report_lines.append("")
            
            if 'current_antenna' in st.session_state:
                antenna = st.session_state.current_antenna
                report_lines.append(f"### 2.1 天线模型")
                report_lines.append(f"- **天线类型**: {antenna.antenna_type.value}")
                report_lines.append(f"- **中心频率**: {antenna.center_frequency} GHz")
                report_lines.append(f"- **增益**: {antenna.gain} dBi")
                report_lines.append("")
            
            report_lines.append("### 2.2 仿真设置")
            if 'pattern_data' in st.session_state:
                pattern = st.session_state.pattern_data
                report_lines.append(f"- **Theta分辨率**: {pattern.theta_resolution}°")
                report_lines.append(f"- **Phi分辨率**: {pattern.phi_resolution}°")
            report_lines.append("")
            
            report_lines.append("### 2.3 分析指标")
            report_lines.append("- 增益和方向性")
            report_lines.append("- 波束宽度")
            report_lines.append("- 副瓣电平")
            report_lines.append("- 极化特性")
            report_lines.append("- 效率分析")
            report_lines.append("")
        
        # 结果分析
        if content_options.get('results'):
            report_lines.append("## 3. 结果分析")
            report_lines.append("")
            
            # 天线规格
            if content_options.get('antenna_specs') and 'current_antenna' in st.session_state:
                antenna = st.session_state.current_antenna
                report_lines.append("### 3.1 天线规格")
                report_lines.append("| 参数 | 值 |")
                report_lines.append("|------|-----|")
                report_lines.append(f"| 天线名称 | {antenna.name} |")
                report_lines.append(f"| 天线类型 | {antenna.antenna_type.value} |")
                report_lines.append(f"| 中心频率 | {antenna.center_frequency} GHz |")
                report_lines.append(f"| 增益 | {antenna.gain} dBi |")
                report_lines.append(f"| 带宽 | {antenna.bandwidth}% |")
                report_lines.append(f"| 极化 | {antenna.polarization.value} |")
                report_lines.append("")
            
            # 方向图特性
            if content_options.get('pattern_data') and 'pattern_data' in st.session_state:
                pattern = st.session_state.pattern_data
                report_lines.append("### 3.2 方向图特性")
                report_lines.append(f"- 最大增益: {np.max(pattern.gain_data):.1f} dB")
                report_lines.append(f"- 频率: {pattern.frequency} GHz")
                report_lines.append("")
            
            # 性能分析
            if content_options.get('analysis_results') and 'analysis_results' in st.session_state:
                results = st.session_state.analysis_results
                report_lines.append("### 3.3 性能分析")
                report_lines.append("")
                
                if 'beam' in results and 'beam_parameters' in results['beam']:
                    beam_params = results['beam']['beam_parameters']
                    report_lines.append("#### 3.3.1 波束特性")
                    report_lines.append(f"- 峰值增益: {beam_params.get('peak_gain', 0):.1f} dBi")
                    report_lines.append(f"- 3dB波束宽度: {beam_params.get('main_lobe_width_3db_e', 0):.1f}°")
                    report_lines.append("")
                
                if 'efficiency' in results and 'efficiency_parameters' in results['efficiency']:
                    eff_params = results['efficiency']['efficiency_parameters']
                    report_lines.append("#### 3.3.2 效率分析")
                    report_lines.append(f"- 总效率: {eff_params.get('total_efficiency', 0)*100:.1f}%")
                    report_lines.append("")
        
        # 结论
        if content_options.get('conclusion'):
            report_lines.append("## 4. 结论")
            report_lines.append("")
            report_lines.append("通过对天线的全面分析，得出以下结论：")
            report_lines.append("")
            
            if 'analysis_results' in st.session_state:
                results = st.session_state.analysis_results
                if 'overall_assessment' in results:
                    assessment = results['overall_assessment']
                    
                    report_lines.append("### 主要发现")
                    for strength in assessment.get('strengths', []):
                        report_lines.append(f"- ✅ {strength}")
                    
                    for weakness in assessment.get('weaknesses', []):
                        report_lines.append(f"- ⚠️ {weakness}")
            
            report_lines.append("")
        
        # 建议
        if content_options.get('recommendations'):
            report_lines.append("## 5. 建议")
            report_lines.append("")
            report_lines.append("### 5.1 设计优化建议")
            report_lines.append("")
            
            if 'analysis_results' in st.session_state:
                results = st.session_state.analysis_results
                if 'overall_assessment' in results:
                    assessment = results['overall_assessment']
                    for rec in assessment.get('recommendations', []):
                        report_lines.append(f"- {rec}")
            
            report_lines.append("")
            report_lines.append("### 5.2 应用建议")
            report_lines.append("- 根据分析结果选择合适应用场景")
            report_lines.append("- 注意天线的安装和使用环境")
            report_lines.append("- 定期进行性能监测和维护")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _generate_html_report(self, title: str, author: str, 
                             date: datetime.date, 
                             content_options: Dict[str, bool]) -> str:
        """生成HTML报告"""
        # 这里简化实现，实际应用中应该使用模板引擎
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; color: #333; }}
        .header .meta {{ color: #666; margin-top: 10px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .chart-placeholder {{ background-color: #f9f9f9; border: 1px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; }}
        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                <p>作者: {author} | 日期: {date.strftime('%Y年%m月%d日')}</p>
            </div>
        </div>
        
        <div class="section">
            <h2>执行摘要</h2>
            <p>本报告对天线的辐射特性进行了全面分析，包括方向图、增益、波束宽度、极化特性、效率等关键参数。</p>
        </div>
        
        <div class="section">
            <h2>关键结果</h2>
            <table>
                <tr><th>参数</th><th>值</th><th>单位</th></tr>
        """
        
        # 添加关键结果
        if 'analysis_results' in st.session_state:
            results = st.session_state.analysis_results
            
            if 'beam' in results and 'beam_parameters' in results['beam']:
                beam_params = results['beam']['beam_parameters']
                html += f"""
                <tr><td>峰值增益</td><td>{beam_params.get('peak_gain', 0):.1f}</td><td>dB</td></tr>
                <tr><td>3dB波束宽度</td><td>{beam_params.get('main_lobe_width_3db_e', 0):.1f}</td><td>度</td></tr>
                """
            
            if 'efficiency' in results and 'efficiency_parameters' in results['efficiency']:
                eff_params = results['efficiency']['efficiency_parameters']
                html += f"""
                <tr><td>总效率</td><td>{eff_params.get('total_efficiency', 0)*100:.1f}</td><td>%</td></tr>
                """
        
        html += """
            </table>
        </div>
        
        <div class="section">
            <h2>图表</h2>
            <div class="chart-placeholder">
                <p>[此处为方向图图表]</p>
            </div>
        </div>
        
        <div class="footer">
            <p>报告生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            <p>生成工具: 天线分析平台</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _render_online_sharing(self):
        """渲染在线分享"""
        st.markdown("## 🌐 在线分享")
        
        # 分享选项
        st.markdown("### 1. 分享设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            share_type = st.selectbox(
                "分享类型",
                ["公开分享", "私有分享", "团队分享", "临时分享"],
                index=1
            )
            
            if share_type == "公开分享":
                st.info("所有人都可以访问")
            elif share_type == "私有分享":
                st.info("需要密码访问")
            elif share_type == "团队分享":
                st.info("团队成员可以访问")
            else:  # 临时分享
                st.info("链接将在指定时间后失效")
        
        with col2:
            expiration = st.selectbox(
                "有效期",
                ["1天", "7天", "30天", "永久", "自定义"],
                index=1
            )
            
            if expiration == "自定义":
                custom_days = st.number_input("天数", 1, 365, 7)
            
            if share_type == "私有分享":
                share_password = st.text_input("访问密码", type="password")
            elif share_type == "团队分享":
                team_members = st.text_area("团队成员邮箱", 
                                          placeholder="用逗号分隔的邮箱地址")
        
        # 分享内容
        st.markdown("### 2. 分享内容")
        
        share_content = {}
        
        with st.expander("📁 数据内容", expanded=True):
            share_content['data'] = st.checkbox("分析数据", value=True)
            share_content['charts'] = st.checkbox("图表", value=True)
            share_content['report'] = st.checkbox("报告", value=False)
        
        with st.expander("🔐 访问权限", expanded=False):
            can_view = st.checkbox("允许查看", value=True)
            can_download = st.checkbox("允许下载", value=True)
            can_comment = st.checkbox("允许评论", value=False)
            
            if can_comment:
                require_login = st.checkbox("评论需登录", value=True)
        
        # 预览
        st.markdown("### 3. 预览分享")
        
        if st.button("👁️ 预览分享页面", width='stretch'):
            self._preview_share_page(share_content)
        
        # 生成分享
        st.markdown("### 4. 生成分享")
        
        col1, col2 = st.columns(2)
        
        with col1:
            share_title = st.text_input("分享标题", "天线分析结果分享")
            share_description = st.text_area("分享描述", 
                                           "这是我使用天线分析平台得到的结果")
        
        with col2:
            if st.button("🌐 生成分享链接", type="primary", width='stretch'):
                with st.spinner("正在生成分享..."):
                    share_url = self._create_share_link(share_type, share_content, 
                                                       expiration, share_title, 
                                                       share_description)
                    
                    if share_url:
                        st.success("分享链接生成成功！")
                        st.code(share_url, language=None)
                        
                        # 复制到剪贴板按钮
                        st.button("📋 复制链接", width='stretch')
    
    def _preview_share_page(self, share_content: Dict[str, bool]):
        """预览分享页面"""
        st.markdown("### 📱 分享页面预览")
        
        # 创建预览
        preview_html = """
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px; background-color: #f9f9f9;">
            <h2 style="color: #333;">天线分析结果分享</h2>
            <p style="color: #666;">这是我使用天线分析平台得到的结果</p>
            <hr>
        """
        
        if share_content.get('data'):
            preview_html += """
            <div style="margin: 10px 0;">
                <h4 style="color: #2c3e50;">📊 分析数据</h4>
                <p>包含天线参数、方向图数据、分析结果等</p>
            </div>
            """
        
        if share_content.get('charts'):
            preview_html += """
            <div style="margin: 10px 0;">
                <h4 style="color: #2c3e50;">📈 图表</h4>
                <p>包含各种分析图表和可视化结果</p>
            </div>
            """
        
        if share_content.get('report'):
            preview_html += """
            <div style="margin: 10px 0;">
                <h4 style="color: #2c3e50;">📄 报告</h4>
                <p>详细的分析报告和总结</p>
            </div>
            """
        
        preview_html += """
            <hr>
            <p style="color: #999; font-size: 0.9em;">
                <strong>访问权限:</strong> 可查看、可下载<br>
                <strong>有效期:</strong> 7天<br>
                <strong>生成时间:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """
            </p>
        </div>
        """
        
        st.markdown(preview_html, unsafe_allow_html=True)
    
    def _create_share_link(self, share_type: str, share_content: Dict[str, bool],
                          expiration: str, title: str, description: str) -> Optional[str]:
        """创建分享链接"""
        # 这里应该实现实际的分享功能
        # 由于这需要后端服务支持，这里只返回示例链接
        
        st.info("在线分享功能需要后端服务支持")
        
        # 生成示例链接
        import secrets
        share_id = secrets.token_urlsafe(8)
        
        base_url = "https://share.antenna-analysis.com"
        
        if share_type == "公开分享":
            return f"{base_url}/public/{share_id}"
        elif share_type == "私有分享":
            return f"{base_url}/private/{share_id}"
        elif share_type == "团队分享":
            return f"{base_url}/team/{share_id}"
        else:  # 临时分享
            return f"{base_url}/temp/{share_id}"
        
        return None

def render_export(config: AppConfig, sidebar_config: Dict[str, Any]):
    """
    渲染导出视图的主函数
    """
    try:
        export_view = ExportView(config)
        export_view.render(sidebar_config)
    except Exception as e:
        st.error(f"导出视图渲染错误: {e}")
        st.exception(e)

if __name__ == "__main__":
    # 测试代码
    config = AppConfig()
    sidebar_config = {
        'page': 'export',
        'antenna_config': {},
        'simulation_settings': {},
        'analysis_settings': {},
        'visualization_settings': {},
        'actions': {}
    }
    
    st.set_page_config(layout="wide")
    render_export(config, sidebar_config)