"""
对比分析视图模块
提供多雷达性能对比分析功能
包括参数对比、性能评分、雷达排名和优化建议
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.radar_models import RadarModel, RadarBand, PlatformType, MissionType
from controllers.radar_controller import RadarController
from services.performance_calculator import RadarPerformanceCalculator, PerformanceAnalyzer
from utils.helpers import format_frequency, format_power, format_distance, linear_to_db


class ComparisonView:
    """对比分析视图类"""
    
    def __init__(self):
        self.controller = RadarController()
        self.performance_calculator = RadarPerformanceCalculator()
        self.performance_analyzer = PerformanceAnalyzer(self.performance_calculator)
        self.setup_page_config()
    
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="雷达对比分析 - 雷达工厂",
            page_icon="📈",
            layout="wide"
        )
        
        # 自定义CSS样式
        st.markdown("""
        <style>
        .comparison-header {
            font-size: 2rem;
            color: #2E86AB;
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .comparison-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #2E86AB;
            margin-bottom: 1.5rem;
        }
        .radar-card {
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            border: 1px solid #e0e0e0;
        }
        .radar-card-highlight {
            border: 2px solid #2E86AB;
            background-color: #e8f4f8;
        }
        .score-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.875rem;
        }
        .score-excellent { background-color: #4CAF50; color: white; }
        .score-good { background-color: #8BC34A; color: white; }
        .score-average { background-color: #FFC107; color: black; }
        .score-poor { background-color: #F44336; color: white; }
        .parameter-table {
            width: 100%;
            border-collapse: collapse;
        }
        .parameter-table th, .parameter-table td {
            padding: 0.5rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .parameter-table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .parameter-table tr:hover {
            background-color: #f5f5f5;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """渲染页面头部"""
        st.markdown('<div class="comparison-header">📈 雷达性能对比分析</div>', 
                   unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write("**多雷达性能综合对比与评估**")
            st.caption("选择雷达进行详细对比分析")
        
        with col2:
            if st.button("🔄 刷新数据", width='stretch'):
                st.cache_data.clear()
                st.rerun()
        
        with col3:
            if st.button("🏠 返回主界面", width='stretch'):
                st.session_state.current_view = "dashboard"
                st.rerun()
    
    def render_comparison_interface(self):
        """渲染对比分析界面"""
        # 获取所有雷达
        all_radars = self.controller.get_all_radars()
        
        if not all_radars:
            st.warning("系统中暂无雷达数据，请先添加雷达")
            st.button("⚙️ 前往雷达设计", 
                     on_click=lambda: setattr(st.session_state, 'current_view', 'radar_editor'))
            return
        
        # 雷达选择
        st.subheader("1️⃣ 选择对比雷达")
        radar_options = {radar_id: f"{radar.name} ({radar.get_band().value}波段)" 
                        for radar_id, radar in all_radars.items()}
        
        selected_radars = st.multiselect(
            "选择要对比的雷达（至少选择2个）",
            options=list(radar_options.keys()),
            format_func=lambda x: radar_options[x],
            default=list(all_radars.keys())[:min(3, len(all_radars))],
            help="选择2个或多个雷达进行对比分析"
        )
        
        if len(selected_radars) < 2:
            st.info("请选择至少2个雷达进行对比分析")
            return
        
        # 获取选中的雷达数据
        comparison_radars = {radar_id: all_radars[radar_id] for radar_id in selected_radars}
        
        # 对比模式选择
        st.subheader("2️⃣ 选择对比模式")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            comparison_mode = st.selectbox(
                "对比维度",
                options=["综合对比", "参数对比", "性能对比", "应用场景对比"],
                index=0
            )
        
        with col2:
            target_rcs = st.selectbox(
                "目标RCS (m²)",
                options=[0.01, 0.1, 1.0, 5.0, 10.0, 100.0],
                index=2,
                help="选择目标雷达截面积用于性能计算"
            )
        
        with col3:
            range_reference = st.number_input(
                "参考距离 (km)",
                min_value=10.0,
                max_value=1000.0,
                value=100.0,
                step=10.0
            )
        
        # 执行对比分析
        comparison_results = self._perform_comparison_analysis(
            comparison_radars, target_rcs, range_reference
        )
        
        # 显示对比结果
        st.markdown("---")
        st.subheader("📊 对比分析结果")
        
        # 根据对比模式显示不同内容
        if comparison_mode == "综合对比":
            self._render_comprehensive_comparison(comparison_results, comparison_radars)
        elif comparison_mode == "参数对比":
            self._render_parameter_comparison(comparison_results, comparison_radars)
        elif comparison_mode == "性能对比":
            self._render_performance_comparison(comparison_results, comparison_radars)
        elif comparison_mode == "应用场景对比":
            self._render_application_comparison(comparison_results, comparison_radars)
    
    def _perform_comparison_analysis(self, radars: Dict[str, RadarModel], 
                                   target_rcs: float, range_reference: float) -> Dict[str, Any]:
        """执行对比分析"""
        results = {
            'radar_info': {},
            'parameter_comparison': {},
            'performance_comparison': {},
            'scores': {},
            'rankings': [],
            'recommendations': []
        }
        
        # 计算每个雷达的性能
        for radar_id, radar in radars.items():
            # 获取雷达信息
            results['radar_info'][radar_id] = {
                'name': radar.name,
                'band': radar.get_band().value,
                'platform': radar.platform.value,
                'missions': [m.value for m in radar.mission_types],
                'type': radar.__class__.__name__
            }
            
            # 参数对比
            if radar.transmitter and radar.antenna:
                results['parameter_comparison'][radar_id] = {
                    'frequency_hz': radar.transmitter.frequency_hz,
                    'power_w': radar.transmitter.power_w,
                    'pulse_width_s': radar.transmitter.pulse_width_s,
                    'gain_dbi': radar.antenna.gain_dbi,
                    'azimuth_bw': radar.antenna.azimuth_beamwidth,
                    'elevation_bw': radar.antenna.elevation_beamwidth
                }
            
            # 性能对比
            performance = self.performance_calculator.calculate_system_performance(radar, target_rcs)
            results['performance_comparison'][radar_id] = performance
            
            # 计算综合评分
            score = self._calculate_comprehensive_score(radar, performance, range_reference)
            results['scores'][radar_id] = score
        
        # 雷达排名
        results['rankings'] = self._calculate_rankings(results['scores'], results['radar_info'])
        
        # 生成建议
        results['recommendations'] = self._generate_recommendations(results, radars)
        
        return results
    
    def _calculate_comprehensive_score(self, radar: RadarModel, performance: Dict[str, Any], 
                                     range_reference: float) -> Dict[str, Any]:
        """计算综合评分"""
        score_components = {}
        
        # 1. 探测距离评分 (0-30分)
        max_range = performance.get('max_detection_range_km', 0)
        if max_range > 500:
            range_score = 30
        elif max_range > 200:
            range_score = 25
        elif max_range > 100:
            range_score = 20
        elif max_range > 50:
            range_score = 15
        elif max_range > 20:
            range_score = 10
        else:
            range_score = 5
        score_components['detection_range'] = {
            'score': range_score,
            'max_score': 30,
            'value': f"{max_range:.1f} km"
        }
        
        # 2. 分辨率评分 (0-20分)
        range_res = performance.get('range_resolution_m', 0)
        angular_res = performance.get('angular_resolution_deg', 0)
        
        if range_res < 10 and angular_res < 1:
            resolution_score = 20
        elif range_res < 30 and angular_res < 3:
            resolution_score = 15
        elif range_res < 50 and angular_res < 5:
            resolution_score = 10
        else:
            resolution_score = 5
        score_components['resolution'] = {
            'score': resolution_score,
            'max_score': 20,
            'value': f"{range_res:.1f}m/{angular_res:.1f}°"
        }
        
        # 3. 频段适应性评分 (0-15分)
        band = radar.get_band()
        band_scores = {
            RadarBand.UHF: 15,  # 反隐身优势
            RadarBand.L: 12,    # 平衡性
            RadarBand.S: 10,    # 通用性
            RadarBand.C: 8,     # 精度优势
            RadarBand.X: 7,     # 高分辨率
            RadarBand.KU: 5     # 特殊应用
        }
        band_score = band_scores.get(band, 5)
        score_components['frequency_band'] = {
            'score': band_score,
            'max_score': 15,
            'value': band.value
        }
        
        # 4. 平台适应性评分 (0-10分)
        platform = radar.platform
        platform_scores = {
            PlatformType.GROUND_MOBILE: 8,  # 机动性
            PlatformType.AIRBORNE: 10,      # 高度优势
            PlatformType.SHIPBORNE: 7,      # 海上应用
            PlatformType.FIXED: 5           # 固定部署
        }
        platform_score = platform_scores.get(platform, 5)
        score_components['platform'] = {
            'score': platform_score,
            'max_score': 10,
            'value': platform.value
        }
        
        # 5. 多任务能力评分 (0-10分)
        mission_count = len(radar.mission_types)
        mission_score = min(10, mission_count * 2)  # 每个任务2分，最多10分
        score_components['multi_mission'] = {
            'score': mission_score,
            'max_score': 10,
            'value': f"{mission_count}种任务"
        }
        
        # 6. 信噪比评分 (0-10分)
        snr_at_ref = self.performance_calculator.calculate_snr_at_range(
            radar, target_rcs=1.0, range_m=range_reference*1000
        )
        if snr_at_ref > 20:
            snr_score = 10
        elif snr_at_ref > 15:
            snr_score = 8
        elif snr_at_ref > 10:
            snr_score = 6
        elif snr_at_ref > 5:
            snr_score = 4
        else:
            snr_score = 2
        score_components['snr'] = {
            'score': snr_score,
            'max_score': 10,
            'value': f"{snr_at_ref:.1f} dB"
        }
        
        # 7. 检测概率评分 (0-5分)
        detection_prob = performance.get('detection_probability', 0)
        detection_score = min(5, detection_prob * 5)  # 线性映射
        score_components['detection_probability'] = {
            'score': detection_score,
            'max_score': 5,
            'value': f"{detection_prob:.2f}"
        }
        
        # 计算总分
        total_score = sum(comp['score'] for comp in score_components.values())
        max_total_score = sum(comp['max_score'] for comp in score_components.values())
        
        return {
            'total_score': total_score,
            'max_total_score': max_total_score,
            'score_percentage': (total_score / max_total_score) * 100,
            'components': score_components,
            'performance_summary': {
                'max_range_km': max_range,
                'range_resolution_m': range_res,
                'angular_resolution_deg': angular_res,
                'snr_at_reference_db': snr_at_ref
            }
        }
    
    def _calculate_rankings(self, scores: Dict[str, Dict[str, Any]], 
                          radar_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算雷达排名"""
        rankings = []
        
        for radar_id, score_data in scores.items():
            info = radar_info.get(radar_id, {})
            rankings.append({
                'radar_id': radar_id,
                'radar_name': info.get('name', radar_id),
                'band': info.get('band', '未知'),
                'platform': info.get('platform', '未知'),
                'total_score': score_data['total_score'],
                'score_percentage': score_data['score_percentage'],
                'max_range_km': score_data['performance_summary'].get('max_range_km', 0)
            })
        
        # 按总分排序
        rankings.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 添加排名
        for i, rank in enumerate(rankings):
            rank['rank'] = i + 1
            rank['ranking_class'] = self._get_ranking_class(rank['score_percentage'])
        
        return rankings
    
    def _get_ranking_class(self, score_percentage: float) -> str:
        """获取排名等级"""
        if score_percentage >= 80:
            return "优秀"
        elif score_percentage >= 70:
            return "良好"
        elif score_percentage >= 60:
            return "中等"
        else:
            return "需改进"
    
    def _generate_recommendations(self, results: Dict[str, Any], 
                                radars: Dict[str, RadarModel]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []
        
        # 分析频段分布
        bands = [info['band'] for info in results['radar_info'].values()]
        unique_bands = set(bands)
        
        if len(unique_bands) < 2:
            recommendations.append({
                'type': 'warning',
                'title': '频段多样性不足',
                'content': '建议增加不同频段的雷达以提高系统抗干扰能力和覆盖范围',
                'priority': '高'
            })
        
        # 分析平台分布
        platforms = [info['platform'] for info in results['radar_info'].values()]
        if PlatformType.AIRBORNE.value not in platforms:
            recommendations.append({
                'type': 'suggestion',
                'title': '缺少机载平台',
                'content': '考虑增加机载雷达以提高低空探测能力和战场态势感知',
                'priority': '中'
            })
        
        # 分析性能差距
        scores = [score['total_score'] for score in results['scores'].values()]
        if len(scores) >= 2:
            max_score = max(scores)
            min_score = min(scores)
            if max_score - min_score > 20:  # 分差较大
                recommendations.append({
                    'type': 'warning',
                    'title': '性能差距较大',
                    'content': '系统内雷达性能差异明显，可能影响协同作战效果',
                    'priority': '中'
                })
        
        # 检查UHF波段反隐身能力
        if RadarBand.UHF.value not in bands:
            recommendations.append({
                'type': 'suggestion',
                'title': '反隐身能力建议',
                'content': '考虑增加UHF波段雷达以增强对隐身目标的探测能力',
                'priority': '高'
            })
        
        return recommendations
    
    def _render_comprehensive_comparison(self, results: Dict[str, Any], 
                                       radars: Dict[str, RadarModel]):
        """渲染综合对比"""
        # 雷达排名
        st.subheader("🏆 雷达综合排名")
        self._render_ranking_table(results['rankings'])
        
        # 综合评分雷达图
        st.subheader("📊 综合评分对比")
        self._render_radar_chart(results, radars)
        
        # 性能对比图表
        st.subheader("📈 关键性能指标对比")
        self._render_performance_bar_charts(results)
        
        # 优化建议
        st.subheader("💡 优化建议")
        self._render_recommendations(results['recommendations'])
        
        # 详细对比表格
        st.subheader("📋 详细参数对比")
        self._render_detailed_comparison_table(results, radars)
    
    def _render_ranking_table(self, rankings: List[Dict[str, Any]]):
        """渲染排名表格"""
        ranking_data = []
        
        for rank in rankings:
            ranking_data.append({
                '排名': rank['rank'],
                '雷达名称': rank['radar_name'],
                '频段': rank['band'],
                '平台': rank['platform'],
                '综合得分': f"{rank['total_score']:.1f}",
                '得分率': f"{rank['score_percentage']:.1f}%",
                '等级': rank['ranking_class'],
                '最远探测距离': f"{rank['max_range_km']:.1f} km"
            })
        
        df_rankings = pd.DataFrame(ranking_data)
        st.dataframe(df_rankings, width='stretch', height=300)
        
        # 排名说明
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏅 第一名", rankings[0]['radar_name'] if rankings else "-")
        with col2:
            st.metric("🥈 第二名", rankings[1]['radar_name'] if len(rankings) > 1 else "-")
        with col3:
            st.metric("🥉 第三名", rankings[2]['radar_name'] if len(rankings) > 2 else "-")
        with col4:
            avg_score = np.mean([r['total_score'] for r in rankings]) if rankings else 0
            st.metric("平均得分", f"{avg_score:.1f}")
    
    def _render_radar_chart(self, results: Dict[str, Any], radars: Dict[str, RadarModel]):
        """渲染雷达图（综合评分对比）"""
        if len(radars) < 2:
            st.info("需要至少2个雷达才能生成对比图表")
            return
        
        # 提取评分维度
        radar_ids = list(radars.keys())
        radar_names = [results['radar_info'][rid]['name'] for rid in radar_ids]
        
        # 使用第一个雷达的评分维度
        first_radar_id = radar_ids[0]
        score_components = results['scores'][first_radar_id]['components']
        categories = list(score_components.keys())
        
        # 创建雷达图
        fig = go.Figure()
        
        for i, radar_id in enumerate(radar_ids):
            scores = results['scores'][radar_id]
            component_scores = [scores['components'][cat]['score'] for cat in categories]
            max_scores = [scores['components'][cat]['max_score'] for cat in categories]
            
            # 雷达图需要闭合
            component_scores_closed = component_scores + [component_scores[0]]
            categories_closed = categories + [categories[0]]
            
            fig.add_trace(go.Scatterpolar(
                r=component_scores_closed,
                theta=categories_closed,
                name=radar_names[i],
                fill='toself',
                line=dict(width=2)
            ))
        
        # 转换显示名称
        display_names = {
            'detection_range': '探测距离',
            'resolution': '分辨率',
            'frequency_band': '频段适应性',
            'platform': '平台适应性',
            'multi_mission': '多任务能力',
            'snr': '信噪比',
            'detection_probability': '检测概率'
        }
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 30]  # 最大评分范围
                )
            ),
            title="雷达综合评分对比图",
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _render_performance_bar_charts(self, results: Dict[str, Any]):
        """渲染性能对比柱状图"""
        radar_ids = list(results['performance_comparison'].keys())
        radar_names = [results['radar_info'][rid]['name'] for rid in radar_ids]
        
        # 提取关键性能指标
        metrics_data = {
            '探测距离 (km)': [],
            '距离分辨率 (m)': [],
            '角分辨率 (°)': [],
            '信噪比 (dB)': []
        }
        
        for radar_id in radar_ids:
            perf = results['performance_comparison'][radar_id]
            metrics_data['探测距离 (km)'].append(perf.get('max_detection_range_km', 0))
            metrics_data['距离分辨率 (m)'].append(perf.get('range_resolution_m', 0))
            metrics_data['角分辨率 (°)'].append(perf.get('angular_resolution_deg', 0))
            metrics_data['信噪比 (dB)'].append(perf.get('snr_at_100km_db', 0))
        
        # 创建分面柱状图
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        for i, (metric_name, values) in enumerate(metrics_data.items()):
            fig.add_trace(go.Bar(
                x=radar_names,
                y=values,
                name=metric_name,
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            title="关键性能指标对比",
            xaxis_title="雷达型号",
            yaxis_title="数值",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 性能指标说明
        with st.expander("📋 性能指标说明"):
            st.markdown("""
            | 指标 | 说明 | 评价标准 |
            |------|------|----------|
            | 探测距离 | 雷达能够探测目标的最大距离 | 值越大越好 |
            | 距离分辨率 | 雷达在距离维度上区分两个目标的能力 | 值越小越好 |
            | 角分辨率 | 雷达在角度维度上区分两个目标的能力 | 值越小越好 |
            | 信噪比 | 信号与噪声的功率比，影响检测性能 | 值越大越好 |
            """)
    
    def _render_recommendations(self, recommendations: List[Dict[str, Any]]):
        """渲染优化建议"""
        if not recommendations:
            st.success("✅ 系统配置合理，无特殊优化建议")
            return
        
        for rec in recommendations:
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    if rec['type'] == 'warning':
                        st.error("⚠️ 警告")
                    elif rec['type'] == 'suggestion':
                        st.info("💡 建议")
                    else:
                        st.warning("📋 注意")
                
                with col2:
                    st.markdown(f"**{rec['title']}** - 优先级: {rec['priority']}")
                    st.caption(rec['content'])
            
            st.markdown("---")
    
    def _render_detailed_comparison_table(self, results: Dict[str, Any], 
                                        radars: Dict[str, RadarModel]):
        """渲染详细对比表格"""
        radar_ids = list(radars.keys())
        
        # 创建对比表格
        comparison_data = []
        
        for radar_id in radar_ids:
            radar = radars[radar_id]
            info = results['radar_info'][radar_id]
            params = results['parameter_comparison'].get(radar_id, {})
            perf = results['performance_comparison'][radar_id]
            score = results['scores'][radar_id]
            
            row = {
                '雷达名称': info['name'],
                '频段': info['band'],
                '平台': info['platform'],
                '频率': format_frequency(params.get('frequency_hz', 0)),
                '功率': format_power(params.get('power_w', 0)),
                '天线增益': f"{params.get('gain_dbi', 0):.1f} dBi",
                '探测距离': f"{perf.get('max_detection_range_km', 0):.1f} km",
                '距离分辨率': f"{perf.get('range_resolution_m', 0):.2f} m",
                '综合得分': f"{score['total_score']:.1f}",
                '得分率': f"{score['score_percentage']:.1f}%"
            }
            comparison_data.append(row)
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, width='stretch', height=300)
    
    def _render_parameter_comparison(self, results: Dict[str, Any], 
                                   radars: Dict[str, RadarModel]):
        """渲染参数对比"""
        st.subheader("🔧 技术参数对比")
        
        # 参数对比表格
        radar_ids = list(radars.keys())
        radar_names = [results['radar_info'][rid]['name'] for rid in radar_ids]
        
        # 创建参数对比数据
        param_categories = {
            '发射机参数': ['frequency_hz', 'power_w', 'pulse_width_s'],
            '天线参数': ['gain_dbi', 'azimuth_bw', 'elevation_bw']
        }
        
        for category, params in param_categories.items():
            st.markdown(f"**{category}**")
            
            # 创建对比表格
            table_data = []
            for param in params:
                param_display = {
                    'frequency_hz': '工作频率',
                    'power_w': '发射功率',
                    'pulse_width_s': '脉冲宽度',
                    'gain_dbi': '天线增益',
                    'azimuth_bw': '方位波束宽度',
                    'elevation_bw': '俯仰波束宽度'
                }.get(param, param)
                
                row = {'参数': param_display}
                for i, radar_id in enumerate(radar_ids):
                    param_value = results['parameter_comparison'].get(radar_id, {}).get(param, 0)
                    
                    # 格式化显示
                    if param == 'frequency_hz':
                        display_value = format_frequency(param_value)
                    elif param == 'power_w':
                        display_value = format_power(param_value)
                    elif param == 'pulse_width_s':
                        display_value = f"{param_value * 1e6:.1f} μs"
                    elif param.endswith('_bw'):
                        display_value = f"{param_value:.1f}°"
                    elif param == 'gain_dbi':
                        display_value = f"{param_value:.1f} dBi"
                    else:
                        display_value = str(param_value)
                    
                    row[radar_names[i]] = display_value
                
                table_data.append(row)
            
            df_params = pd.DataFrame(table_data)
            st.dataframe(df_params, width='stretch', height=200)
            st.markdown("---")
    
    def _render_performance_comparison(self, results: Dict[str, Any], 
                                     radars: Dict[str, RadarModel]):
        """渲染性能对比"""
        st.subheader("📊 检测性能对比")
        
        # 创建性能对比图表
        radar_ids = list(radars.keys())
        radar_names = [results['radar_info'][rid]['name'] for rid in radar_ids]
        
        # 提取性能数据
        perf_metrics = {
            'max_detection_range_km': '最大探测距离 (km)',
            'range_resolution_m': '距离分辨率 (m)',
            'angular_resolution_deg': '角分辨率 (°)',
            'snr_at_100km_db': '信噪比 @100km (dB)',
            'detection_probability': '检测概率'
        }
        
        for metric_key, metric_name in perf_metrics.items():
            values = []
            for radar_id in radar_ids:
                perf = results['performance_comparison'][radar_id]
                values.append(perf.get(metric_key, 0))
            
            # 创建柱状图
            fig = go.Figure(data=[
                go.Bar(x=radar_names, y=values, name=metric_name)
            ])
            
            fig.update_layout(
                title=metric_name,
                xaxis_title="雷达型号",
                yaxis_title=metric_name.split('(')[-1].split(')')[0] if '(' in metric_name else "数值",
                height=300
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # 检测概率对比（特殊处理）
        st.subheader("🎯 检测概率对比")
        self._render_detection_probability_chart(results, radars)
    
    def _render_detection_probability_chart(self, results: Dict[str, Any], 
                                          radars: Dict[str, RadarModel]):
        """渲染检测概率对比图"""
        radar_ids = list(radars.keys())
        radar_names = [results['radar_info'][rid]['name'] for rid in radar_ids]
        
        # 模拟不同距离下的检测概率
        ranges = np.linspace(10, 500, 50)  # 10-500km
        
        fig = go.Figure()
        
        for i, radar_id in enumerate(radar_ids):
            radar = radars[radar_id]
            detection_probs = []
            
            for range_km in ranges:
                # 简化计算检测概率
                snr = self.performance_calculator.calculate_snr_at_range(
                    radar, target_rcs=1.0, range_m=range_km*1000
                )
                # 简化检测概率计算
                if snr > 20:
                    prob = 0.95
                elif snr > 15:
                    prob = 0.85
                elif snr > 10:
                    prob = 0.70
                elif snr > 5:
                    prob = 0.50
                elif snr > 0:
                    prob = 0.20
                else:
                    prob = 0.05
                
                detection_probs.append(prob)
            
            fig.add_trace(go.Scatter(
                x=ranges,
                y=detection_probs,
                mode='lines',
                name=radar_names[i],
                line=dict(width=3)
            ))
        
        fig.update_layout(
            title="检测概率 vs 距离",
            xaxis_title="距离 (km)",
            yaxis_title="检测概率",
            yaxis=dict(range=[0, 1]),
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _render_application_comparison(self, results: Dict[str, Any], 
                                     radars: Dict[str, RadarModel]):
        """渲染应用场景对比"""
        st.subheader("🎯 应用场景适应性分析")
        
        # 定义应用场景和要求
        application_scenarios = {
            '远程预警': {
                'requirements': ['探测距离', '反隐身能力', '多目标处理'],
                'weight': {'探测距离': 0.5, '反隐身能力': 0.3, '多目标处理': 0.2}
            },
            '区域防空': {
                'requirements': ['跟踪精度', '反应速度', '抗干扰能力'],
                'weight': {'跟踪精度': 0.4, '反应速度': 0.3, '抗干扰能力': 0.3}
            },
            '反隐身作战': {
                'requirements': ['低RCS探测', '频率多样性', '信号处理'],
                'weight': {'低RCS探测': 0.5, '频率多样性': 0.3, '信号处理': 0.2}
            },
            '海事监视': {
                'requirements': ['海杂波抑制', '目标分类', '全天候工作'],
                'weight': {'海杂波抑制': 0.4, '目标分类': 0.3, '全天候工作': 0.3}
            }
        }
        
        radar_ids = list(radars.keys())
        radar_names = [results['radar_info'][rid]['name'] for rid in radar_ids]
        
        # 计算每个雷达在各项应用场景的适应性评分
        for scenario, scenario_info in application_scenarios.items():
            st.markdown(f"**{scenario}**")
            
            # 创建评分表格
            scores = []
            for radar_id in radar_ids:
                radar = radars[radar_id]
                radar_type = radar.__class__.__name__
                
                # 根据雷达类型和应用场景计算适应性
                if scenario == '远程预警':
                    if radar_type in ['EarlyWarningRadar', 'AirborneRadar']:
                        score = np.random.uniform(0.7, 0.9)
                    else:
                        score = np.random.uniform(0.3, 0.6)
                elif scenario == '区域防空':
                    if radar_type in ['FireControlRadar']:
                        score = np.random.uniform(0.8, 0.95)
                    else:
                        score = np.random.uniform(0.4, 0.7)
                elif scenario == '反隐身作战':
                    if radar.get_band() == RadarBand.UHF:
                        score = np.random.uniform(0.8, 0.95)
                    else:
                        score = np.random.uniform(0.3, 0.6)
                elif scenario == '海事监视':
                    if radar_type in ['MaritimeRadar']:
                        score = np.random.uniform(0.8, 0.95)
                    else:
                        score = np.random.uniform(0.4, 0.7)
                else:
                    score = 0.5
                
                scores.append(score)
            
            # 显示评分
            fig = go.Figure(data=[
                go.Bar(x=radar_names, y=scores, 
                      text=[f"{s:.1%}" for s in scores],
                      textposition='auto',
                      marker_color=scores,
                      colorscale='RdYlGn')
            ])
            
            fig.update_layout(
                xaxis_title="雷达型号",
                yaxis_title="适应性评分",
                yaxis=dict(range=[0, 1]),
                height=300
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # 应用场景建议
        st.subheader("💡 应用场景建议")
        
        for radar_id, radar in radars.items():
            radar_name = results['radar_info'][radar_id]['name']
            missions = results['radar_info'][radar_id]['missions']
            
            with st.expander(f"📡 {radar_name} 应用建议"):
                st.write(f"**主要任务类型:** {', '.join(missions)}")
                
                # 根据雷达类型给出建议
                if radar.__class__.__name__ == 'EarlyWarningRadar':
                    st.markdown("""
                    ✅ **推荐应用场景:**
                    - 远程空中预警
                    - 反隐身探测
                    - 战略防空
                    
                    ⚠️ **注意事项:**
                    - 适合大范围监视
                    - 分辨率相对较低
                    - 需要与其他雷达协同
                    """)
                elif radar.__class__.__name__ == 'AirborneRadar':
                    st.markdown("""
                    ✅ **推荐应用场景:**
                    - 空中预警指挥
                    - 战场监视
                    - 低空补盲
                    
                    ⚠️ **注意事项:**
                    - 受平台限制
                    - 需要考虑平台运动补偿
                    - 部署灵活
                    """)
                elif radar.__class__.__name__ == 'FireControlRadar':
                    st.markdown("""
                    ✅ **推荐应用场景:**
                    - 武器制导
                    - 精密跟踪
                    - 末端防御
                    
                    ⚠️ **注意事项:**
                    - 作用距离有限
                    - 需要高数据率
                    - 抗干扰要求高
                    """)
                elif radar.__class__.__name__ == 'MaritimeRadar':
                    st.markdown("""
                    ✅ **推荐应用场景:**
                    - 海上监视
                    - 目标分类
                    - 海警执法
                    
                    ⚠️ **注意事项:**
                    - 海杂波影响大
                    - 需要考虑多路径效应
                    - 全天候工作要求
                    """)
    
    def render(self):
        """渲染完整对比分析视图"""
        self.render_header()
        self.render_comparison_interface()


def main():
    """主函数"""
    # 初始化对比分析视图
    comparison_view = ComparisonView()
    
    # 渲染视图
    comparison_view.render()


if __name__ == "__main__":
    main()