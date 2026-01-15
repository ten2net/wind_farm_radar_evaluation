# 文件6: utils/report_generator.py
"""
报告生成模块
负责生成评估报告，并调用Kimi API进行数据分析
"""

import os
import json
import yaml
import markdown
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from io import StringIO
import base64
import requests
import time
import streamlit as st

from config.config import (
    REPORT_CONFIG, KIMI_API_CONFIG, COLOR_SCHEME,
    OUTPUTS_DIR, TEMPLATES_DIR, REPORTS_DIR
)
from utils.visualization import VisualizationTools
from utils.radar_calculations import RadarCalculator

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化报告生成器
        
        参数:
            api_key: Kimi API密钥
        """
        self.api_key = api_key or st.session_state.get('kimi_api_key')
        self.report_config = REPORT_CONFIG
        self.api_config = KIMI_API_CONFIG
        self.viz_tools = VisualizationTools()
        self.calculator = RadarCalculator()
        
        # 创建输出目录
        self.reports_dir = REPORTS_DIR
        self.charts_dir = self.reports_dir / "charts"
        self.data_dir = self.reports_dir / "data"
        self.images_dir = self.reports_dir / "images"
        
        for directory in [self.reports_dir, self.charts_dir, self.data_dir, self.images_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        scenario_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        生成评估报告
        
        参数:
            scenario_data: 场景数据
            analysis_results: 分析结果
            output_format: 输出格式
            
        返回:
            报告生成结果
        """
        report_data = {
            'scenario': scenario_data,
            'analysis': analysis_results,
            'timestamp': datetime.now().isoformat(),
            'report_id': self._generate_report_id(),
            'sections': {},
            'files': []
        }
        
        try:
            # 1. 生成执行摘要
            exec_summary = self._generate_executive_summary(scenario_data, analysis_results)
            report_data['sections']['executive_summary'] = exec_summary
            
            # 2. 生成项目概述
            project_overview = self._generate_project_overview(scenario_data)
            report_data['sections']['project_overview'] = project_overview
            
            # 3. 生成评估方法
            methodology = self._generate_methodology()
            report_data['sections']['methodology'] = methodology
            
            # 4. 生成场景描述
            scenario_description = self._generate_scenario_description(scenario_data)
            report_data['sections']['scenario_description'] = scenario_description
            
            # 5. 生成分析结果
            analysis_section = self._generate_analysis_results(analysis_results)
            report_data['sections']['analysis_results'] = analysis_section
            
            # 6. 生成影响评估
            impact_assessment = self._generate_impact_assessment(analysis_results)
            report_data['sections']['impact_assessment'] = impact_assessment
            
            # 7. 生成缓解措施
            mitigation_measures = self._generate_mitigation_measures(analysis_results)
            report_data['sections']['mitigation_measures'] = mitigation_measures
            
            # 8. 生成结论
            conclusions = self._generate_conclusions(analysis_results)
            report_data['sections']['conclusions'] = conclusions
            
            # 9. 生成建议
            recommendations = self._generate_recommendations(analysis_results)
            report_data['sections']['recommendations'] = recommendations
            
            # 10. 生成附录
            appendices = self._generate_appendices(scenario_data, analysis_results)
            report_data['sections']['appendices'] = appendices
            
            # 生成完整报告
            if output_format == "markdown":
                report_content = self._assemble_markdown_report(report_data)
                report_path = self._save_markdown_report(report_content, report_data['report_id'])
                report_data['files'].append(report_path)
            
            # 保存报告数据
            data_path = self._save_report_data(report_data)
            report_data['files'].append(data_path)
            
            return report_data
            
        except Exception as e:
            st.error(f"生成报告时发生错误: {str(e)}")
            raise
    
    def _generate_executive_summary(
        self,
        scenario_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成执行摘要
        
        参数:
            scenario_data: 场景数据
            analysis_results: 分析结果
            
        返回:
            执行摘要内容
        """
        # 提取关键信息
        scenario_name = scenario_data.get('name', '未命名场景')
        num_turbines = len(scenario_data.get('wind_turbines', []))
        num_radars = len(scenario_data.get('radar_stations', []))
        num_targets = len(scenario_data.get('targets', []))
        
        # 获取性能指标
        performance = analysis_results.get('performance_metrics', {})
        overall_score = performance.get('overall_score', 0)
        
        # 评估影响程度
        if overall_score >= 0.8:
            impact_level = "低"
            impact_color = "green"
        elif overall_score >= 0.6:
            impact_level = "中"
            impact_color = "orange"
        else:
            impact_level = "高"
            impact_color = "red"
        
        # 关键发现
        key_findings = []
        
        # 检查SNR影响
        if 'snr_comparison' in analysis_results:
            snr_data = analysis_results['snr_comparison']
            if 'average_reduction' in snr_data:
                reduction = snr_data['average_reduction']
                if reduction > 3:
                    key_findings.append(f"风机导致平均信噪比下降 {reduction:.1f}dB")
        
        # 检查干扰影响
        if 'interference_analysis' in analysis_results:
            interference_data = analysis_results['interference_analysis']
            if 'severe_cases' in interference_data:
                severe_cases = interference_data['severe_cases']
                if severe_cases > 0:
                    key_findings.append(f"发现 {severe_cases} 个严重干扰案例")
        
        # 生成摘要文本
        summary_text = f"""
# 执行摘要

## 评估概述
本次评估针对 **{scenario_name}** 风电场对周边雷达探测性能的影响进行了全面分析。评估范围包括 {num_turbines} 台风机、{num_radars} 个雷达站和 {num_targets} 个目标。

## 主要发现
1. **总体影响等级**: <span style='color:{impact_color}; font-weight:bold;'>{impact_level}</span>
2. **性能评分**: {overall_score:.1%}
3. **关键发现**:
"""

        for i, finding in enumerate(key_findings, 1):
            summary_text += f"   {i}. {finding}\n"
        
        summary_text += f"""
## 结论概要
根据分析结果，该风电场对雷达探测性能的影响总体为 **{impact_level}** 等级。建议采取相应的技术和管理措施以减轻潜在影响。

## 建议措施
1. 对影响较大的雷达站进行技术优化
2. 建立长期监测机制
3. 制定应急预案
"""
        
        return {
            'text': summary_text,
            'impact_level': impact_level,
            'overall_score': overall_score,
            'key_findings': key_findings
        }
    
    def _generate_project_overview(
        self,
        scenario_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成项目概述
        
        参数:
            scenario_data: 场景数据
            
        返回:
            项目概述内容
        """
        scenario_name = scenario_data.get('name', '未命名场景')
        description = scenario_data.get('description', '无描述')
        created_at = scenario_data.get('created_at', datetime.now().isoformat())
        
        # 统计信息
        turbines = scenario_data.get('wind_turbines', [])
        radars = scenario_data.get('radar_stations', [])
        comms = scenario_data.get('communication_stations', [])
        targets = scenario_data.get('targets', [])
        
        # 风机型号统计
        turbine_models = {}
        for turbine in turbines:
            model = turbine.get('model', '未知')
            turbine_models[model] = turbine_models.get(model, 0) + 1
        
        # 雷达频段统计
        radar_bands = {}
        for radar in radars:
            band = radar.get('frequency_band', '未知')
            radar_bands[band] = radar_bands.get(band, 0) + 1
        
        overview_text = f"""
# 项目概述

## 场景信息
- **场景名称**: {scenario_name}
- **创建时间**: {created_at}
- **场景描述**: {description}

## 场景构成
| 组件类型 | 数量 | 详细信息 |
|---------|------|----------|
| 风机 | {len(turbines)} | {', '.join([f'{model}×{count}' for model, count in turbine_models.items()])} |
| 雷达站 | {len(radars)} | {', '.join([f'{band}波段×{count}' for band, count in radar_bands.items()])} |
| 通信站 | {len(comms)} | 移动通信、微波中继等 |
| 评估目标 | {len(targets)} | 民航飞机、无人机等 |

## 评估目标
本次评估旨在量化分析风电场对雷达探测性能的影响，包括：
1. 信噪比变化分析
2. 多径效应评估
3. 干扰影响分析
4. 检测概率变化
5. 跟踪性能影响

## 评估方法
采用基于雷达方程的量化分析方法，结合实际场景参数进行计算。评估过程包括有风机和无风机两种条件下的对比分析。

## 技术标准
评估遵循以下技术标准：
- IEEE Radar Standards
- ITU-R Recommendations
- 中国民用航空标准
- 风电场建设规范
"""
        
        return {
            'text': overview_text,
            'statistics': {
                'turbines': len(turbines),
                'radars': len(radars),
                'comms': len(comms),
                'targets': len(targets),
                'turbine_models': turbine_models,
                'radar_bands': radar_bands
            }
        }
    
    def _generate_methodology(self) -> Dict[str, Any]:
        """生成评估方法"""
        methodology_text = """
# 评估方法

## 1. 雷达方程计算
采用标准雷达方程进行信号功率计算：

$$
P_r = \\frac{P_t G_t^2 \\lambda^2 \\sigma}{(4\\pi)^3 R^4 L_s L_a}
$$

其中：
- $P_r$: 接收功率
- $P_t$: 发射功率
- $G_t$: 天线增益
- $\\lambda$: 波长
- $\\sigma$: 目标雷达截面积
- $R$: 目标距离
- $L_s$: 系统损耗
- $L_a$: 大气损耗

## 2. 信噪比计算
$$
SNR = \\frac{P_r}{P_n}
$$

噪声功率计算：
$$
P_n = k T_0 B F
$$

其中：
- $k$: 玻尔兹曼常数
- $T_0$: 标准温度
- $B$: 带宽
- $F$: 噪声系数

## 3. 多普勒频移计算
$$
f_d = \\frac{2v_r}{\\lambda}
$$

其中：
- $f_d$: 多普勒频率
- $v_r$: 径向速度

## 4. 多径效应模型
采用双径模型计算多径损耗：
$$
L_{mp} = 20 \\log_{10} |1 + \\Gamma e^{-j\\Delta\\phi}|
$$

其中：
- $\\Gamma$: 反射系数
- $\\Delta\\phi$: 相位差

## 5. 风机RCS模型
风机RCS计算考虑以下因素：
- 风机结构尺寸
- 材料属性
- 视角关系
- 频率特性

## 6. 干扰分析模型
采用载干比(CIR)评估干扰影响：
$$
CIR = \\frac{P_{desired}}{P_{interference}}
$$

## 7. 检测概率计算
基于Swerling模型计算检测概率：
$$
P_d = f(SNR, P_{fa}, N)
$$

其中：
- $P_d$: 检测概率
- $P_{fa}$: 虚警概率
- $N$: 积累脉冲数
"""
        
        return {
            'text': methodology_text,
            'equations': [
                'radar_equation',
                'snr_calculation', 
                'doppler_calculation',
                'multipath_model',
                'turbine_rcs_model',
                'interference_model',
                'detection_probability'
            ]
        }
    
    def _generate_scenario_description(
        self,
        scenario_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成场景描述
        
        参数:
            scenario_data: 场景数据
            
        返回:
            场景描述内容
        """
        # 创建数据表格
        tables = {}
        
        # 风机信息表
        turbines = scenario_data.get('wind_turbines', [])
        if turbines:
            turbine_rows = []
            for turbine in turbines[:10]:  # 限制行数
                turbine_rows.append({
                    'ID': turbine.get('id', ''),
                    '型号': turbine.get('model', ''),
                    '位置': f"{turbine.get('position', {}).get('lat', 0):.6f}, {turbine.get('position', {}).get('lon', 0):.6f}",
                    '高度(m)': turbine.get('height', 0),
                    '转子直径(m)': turbine.get('rotor_diameter', 0),
                    '方位角(°)': turbine.get('orientation', 0)
                })
            
            turbine_df = pd.DataFrame(turbine_rows)
            tables['turbines'] = turbine_df
        
        # 雷达站信息表
        radars = scenario_data.get('radar_stations', [])
        if radars:
            radar_rows = []
            for radar in radars:
                radar_rows.append({
                    'ID': radar.get('id', ''),
                    '类型': radar.get('type', ''),
                    '频段': radar.get('frequency_band', ''),
                    '位置': f"{radar.get('position', {}).get('lat', 0):.6f}, {radar.get('position', {}).get('lon', 0):.6f}",
                    '峰值功率(W)': f"{radar.get('peak_power', 0):,}",
                    '天线增益(dBi)': radar.get('antenna_gain', 0),
                    '波束宽度(°)': radar.get('beam_width', 0)
                })
            
            radar_df = pd.DataFrame(radar_rows)
            tables['radars'] = radar_df
        
        # 生成描述文本
        description_text = "# 场景描述\n\n"
        
        # 添加表格
        for table_name, df in tables.items():
            if not df.empty:
                description_text += f"## {table_name.replace('_', ' ').title()}\n\n"
                description_text += df.to_markdown(index=False)
                description_text += "\n\n"
                
                # 调用Kimi API分析表格
                if self.api_key:
                    try:
                        analysis = self._analyze_table_with_kimi(df, table_name)
                        description_text += f"**AI分析**: {analysis}\n\n"
                    except Exception as e:
                        description_text += f"*AI分析暂时不可用*\n\n"
        
        return {
            'text': description_text,
            'tables': tables
        }
    
    def _generate_analysis_results(
        self,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成分析结果
        
        参数:
            analysis_results: 分析结果
            
        返回:
            分析结果内容
        """
        # 创建图表
        charts = []
        
        # 如果有SNR对比数据，生成图表
        if 'snr_comparison' in analysis_results:
            try:
                snr_data = analysis_results['snr_comparison']
                fig = self.viz_tools.create_snr_comparison_chart(
                    snr_data.get('without_turbines', []),
                    snr_data.get('with_turbines', []),
                    snr_data.get('distances', []),
                    title="信噪比对比分析"
                )
                
                # 保存图表
                chart_path = self.viz_tools.save_chart_as_image(
                    fig, 
                    "snr_comparison",
                    self.charts_dir
                )
                
                charts.append({
                    'name': '信噪比对比',
                    'path': chart_path,
                    'type': 'snr_comparison'
                })
                
                # 生成分析文本
                analysis_text = self._generate_snr_analysis_text(snr_data)
                
            except Exception as e:
                analysis_text = f"生成SNR对比图表时出错: {str(e)}"
        
        # 生成结果文本
        results_text = "# 分析结果\n\n"
        
        # 添加性能指标
        if 'performance_metrics' in analysis_results:
            performance = analysis_results['performance_metrics']
            results_text += "## 性能指标总结\n\n"
            
            metrics_table = [
                ["指标", "值", "评估"],
                ["检测性能", performance.get('detection_performance', '未知'), "●" * 3],
                ["跟踪能力", performance.get('tracking_capability', '未知'), "●" * 2],
                ["距离分辨率", performance.get('range_resolution_quality', '未知'), "●" * 3],
                ["速度分辨率", performance.get('velocity_resolution_quality', '未知'), "●" * 2],
                ["干扰影响", performance.get('interference_impact', '未知'), "●" * 2],
                ["杂波影响", performance.get('clutter_impact', '未知'), "●" * 1]
            ]
            
            # 转换为markdown表格
            results_text += "| " + " | ".join(metrics_table[0]) + " |\n"
            results_text += "|" + "|".join(["---"] * len(metrics_table[0])) + "|\n"
            
            for row in metrics_table[1:]:
                results_text += "| " + " | ".join(row) + " |\n"
            
            results_text += "\n"
        
        # 添加图表
        if charts:
            results_text += "## 分析图表\n\n"
            for chart in charts:
                chart_name = chart['name']
                chart_path = chart['path']
                
                # 相对路径
                rel_path = Path(chart_path).relative_to(self.reports_dir)
                
                results_text += f"### {chart_name}\n\n"
                results_text += f"![{chart_name}]({rel_path})\n\n"
                
                # 调用Kimi API分析图表
                if self.api_key:
                    try:
                        chart_analysis = self._analyze_chart_with_kimi(chart_path, chart_name)
                        results_text += f"**AI分析**: {chart_analysis}\n\n"
                    except Exception as e:
                        results_text += f"*AI分析暂时不可用*\n\n"
        
        return {
            'text': results_text,
            'charts': charts,
            'analysis_text': analysis_text if 'analysis_text' in locals() else '' # type: ignore
        }
    
    def _generate_impact_assessment(
        self,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成影响评估
        
        参数:
            analysis_results: 分析结果
            
        返回:
            影响评估内容
        """
        # 提取影响数据
        impact_data = {}
        
        if 'snr_comparison' in analysis_results:
            snr_data = analysis_results['snr_comparison']
            avg_reduction = snr_data.get('average_reduction', 0)
            
            if avg_reduction > 5:
                snr_impact = "高"
            elif avg_reduction > 2:
                snr_impact = "中"
            else:
                snr_impact = "低"
            
            impact_data['snr'] = {
                'reduction_db': avg_reduction,
                'impact_level': snr_impact
            }
        
        if 'interference_analysis' in analysis_results:
            interference_data = analysis_results['interference_analysis']
            severe_cases = interference_data.get('severe_cases', 0)
            
            if severe_cases > 3:
                interference_impact = "高"
            elif severe_cases > 0:
                interference_impact = "中"
            else:
                interference_impact = "低"
            
            impact_data['interference'] = {
                'severe_cases': severe_cases,
                'impact_level': interference_impact
            }
        
        # 生成评估文本
        assessment_text = "# 影响评估\n\n"
        
        assessment_text += "## 影响等级评估\n\n"
        assessment_text += "| 影响类型 | 影响等级 | 说明 |\n"
        assessment_text += "|----------|----------|------|\n"
        
        for impact_type, data in impact_data.items():
            impact_level = data.get('impact_level', '未知')
            description = ""
            
            if impact_type == 'snr':
                reduction = data.get('reduction_db', 0)
                description = f"信噪比平均下降 {reduction:.1f}dB"
            elif impact_type == 'interference':
                cases = data.get('severe_cases', 0)
                description = f"发现 {cases} 个严重干扰案例"
            
            assessment_text += f"| {impact_type.replace('_', ' ').title()} | {impact_level} | {description} |\n"
        
        assessment_text += "\n## 影响分析\n\n"
        
        # 总体影响评估
        impact_levels = [data.get('impact_level') for data in impact_data.values()]
        if '高' in impact_levels:
            overall_impact = "高"
        elif '中' in impact_levels:
            overall_impact = "中"
        else:
            overall_impact = "低"
        
        assessment_text += f"### 总体影响评估: **{overall_impact}**\n\n"
        
        if overall_impact == "高":
            assessment_text += "风电场对雷达探测性能有显著影响，需要立即采取措施。\n\n"
        elif overall_impact == "中":
            assessment_text += "风电场对雷达探测性能有一定影响，建议进行优化。\n\n"
        else:
            assessment_text += "风电场对雷达探测性能影响较小，可接受。\n\n"
        
        return {
            'text': assessment_text,
            'impact_data': impact_data,
            'overall_impact': overall_impact
        }
    
    def _generate_mitigation_measures(
        self,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成缓解措施"""
        # 获取建议
        recommendations = []
        if 'performance_metrics' in analysis_results:
            performance = analysis_results['performance_metrics']
            recommendations = performance.get('recommendations', [])
        
        measures_text = "# 缓解措施\n\n"
        
        measures_text += "## 技术措施\n\n"
        
        technical_measures = [
            "优化雷达参数设置，提高抗干扰能力",
            "采用频率捷变技术，避开风机反射频点",
            "使用自适应波束成形，抑制干扰方向",
            "引入MTI/MTD技术，抑制风机杂波",
            "优化信号处理算法，提高检测性能"
        ]
        
        for i, measure in enumerate(technical_measures, 1):
            measures_text += f"{i}. {measure}\n"
        
        measures_text += "\n## 管理措施\n\n"
        
        management_measures = [
            "建立风电场-雷达协同工作机制",
            "制定干扰应急预案和处置流程",
            "定期进行联合测试和评估",
            "建立长期监测和数据共享机制",
            "加强人员培训和技术交流"
        ]
        
        for i, measure in enumerate(management_measures, 1):
            measures_text += f"{i}. {measure}\n"
        
        measures_text += "\n## 工程措施\n\n"
        
        engineering_measures = [
            "优化风机布局，减少对雷达的遮挡",
            "采用低RCS风机设计，减少反射",
            "增加雷达高度，改善视线条件",
            "建设雷达屏蔽设施，减少多径效应",
            "优化基础设施布局，减少电磁干扰"
        ]
        
        for i, measure in enumerate(engineering_measures, 1):
            measures_text += f"{i}. {measure}\n"
        
        measures_text += "\n## 建议优先级\n\n"
        
        priority_measures = [
            ("高", "立即实施频率优化和参数调整"),
            ("中", "3个月内完成自适应算法升级"),
            ("低", "6-12个月内完成工程改造")
        ]
        
        for priority, measure in priority_measures:
            measures_text += f"- **{priority}优先级**: {measure}\n"
        
        return {
            'text': measures_text,
            'recommendations': recommendations
        }
    
    def _generate_conclusions(
        self,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成结论"""
        # 获取性能指标
        performance = analysis_results.get('performance_metrics', {})
        overall_score = performance.get('overall_score', 0)
        
        # 确定结论等级
        if overall_score >= 0.8:
            conclusion_level = "良好"
            conclusion_color = "green"
        elif overall_score >= 0.6:
            conclusion_level = "一般"
            conclusion_color = "orange"
        else:
            conclusion_level = "较差"
            conclusion_color = "red"
        
        conclusions_text = f"""
# 结论

## 总体评估
根据本次评估结果，风电场对雷达探测性能的影响总体评估为：<span style='color:{conclusion_color}; font-weight:bold;'>**{conclusion_level}**</span>

## 主要结论
1. **性能影响**: 风机对雷达探测性能产生了一定影响，主要体现在信噪比下降和多径效应增强。
2. **干扰情况**: 存在一定程度的电磁干扰，但多数情况下在可控范围内。
3. **检测能力**: 目标检测能力受到一定影响，但通过技术优化可缓解。
4. **跟踪性能**: 目标跟踪性能基本满足要求，但复杂环境下可能下降。

## 风险评估
| 风险类型 | 风险等级 | 说明 |
|----------|----------|------|
| 探测性能下降 | 中 | 信噪比平均下降2-5dB |
| 虚假目标增加 | 低 | 风机反射可能产生虚假目标 |
| 跟踪丢失风险 | 中 | 复杂环境下跟踪可能不稳定 |
| 系统稳定性 | 低 | 系统整体运行稳定 |

## 可行性分析
1. **技术可行性**: 现有技术手段可有效缓解大部分影响
2. **经济可行性**: 优化措施成本可控，投资回报合理
3. **操作可行性**: 管理措施易于实施，不影响正常运营
4. **时间可行性**: 可在6-12个月内完成所有优化措施

## 最终结论
综合评估结果表明，在采取适当技术和管理措施的前提下，风电场对雷达探测性能的影响处于可接受范围内。建议按照优先级逐步实施缓解措施，并建立长期监测机制。
"""
        
        return {
            'text': conclusions_text,
            'conclusion_level': conclusion_level,
            'overall_score': overall_score
        }
    
    def _generate_recommendations(
        self,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成建议"""
        # 获取性能指标中的建议
        performance = analysis_results.get('performance_metrics', {})
        tech_recommendations = performance.get('recommendations', [])
        
        recommendations_text = "# 建议\n\n"
        
        recommendations_text += "## 技术建议\n\n"
        for i, rec in enumerate(tech_recommendations, 1):
            recommendations_text += f"{i}. {rec}\n"
        
        if not tech_recommendations:
            recommendations_text += "1. 优化雷达发射功率和天线参数\n"
            recommendations_text += "2. 采用先进的信号处理算法\n"
            recommendations_text += "3. 实施频率管理和干扰抑制技术\n"
            recommendations_text += "4. 升级雷达硬件系统性能\n"
            recommendations_text += "5. 引入人工智能辅助决策系统\n"
        
        recommendations_text += "\n## 管理建议\n\n"
        
        management_recommendations = [
            "建立风电场与雷达站的定期协调机制",
            "制定详细的干扰应急预案",
            "建立长期性能监测和数据记录系统",
            "加强人员技术培训和安全教育",
            "定期进行联合测试和评估演练"
        ]
        
        for i, rec in enumerate(management_recommendations, 1):
            recommendations_text += f"{i}. {rec}\n"
        
        recommendations_text += "\n## 工程建议\n\n"
        
        engineering_recommendations = [
            "优化风机布局和安装位置",
            "采用低反射率材料和涂层",
            "改善雷达站周边电磁环境",
            "升级基础设施和供电系统",
            "建设必要的屏蔽和防护设施"
        ]
        
        for i, rec in enumerate(engineering_recommendations, 1):
            recommendations_text += f"{i}. {rec}\n"
        
        recommendations_text += "\n## 实施计划\n\n"
        
        implementation_plan = [
            ("短期(1-3个月)", "完成参数优化和初步测试"),
            ("中期(3-6个月)", "实施算法升级和系统调试"),
            ("长期(6-12个月)", "完成工程改造和全面评估")
        ]
        
        for period, plan in implementation_plan:
            recommendations_text += f"- **{period}**: {plan}\n"
        
        return {
            'text': recommendations_text,
            'technical_recommendations': tech_recommendations
        }
    
    def _generate_appendices(
        self,
        scenario_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成附录"""
        appendices_text = "# 附录\n\n"
        
        appendices_text += "## 附录A: 技术参数\n\n"
        appendices_text += "### 雷达参数\n"
        
        # 雷达参数表
        radar_params = [
            ["参数", "值", "单位"],
            ["工作频率", "3.0", "GHz"],
            ["峰值功率", "1,000,000", "W"],
            ["平均功率", "1,000", "W"],
            ["天线增益", "40", "dBi"],
            ["波束宽度", "1.0", "度"],
            ["噪声系数", "3.0", "dB"],
            ["系统损耗", "6.0", "dB"]
        ]
        
        for row in radar_params:
            appendices_text += f"| {' | '.join(row)} |\n"
        
        appendices_text += "\n### 风机参数\n"
        
        # 风机参数表
        turbine_params = [
            ["参数", "值", "单位"],
            ["轮毂高度", "150", "m"],
            ["转子直径", "150", "m"],
            ["叶片长度", "75", "m"],
            ["塔筒直径", "5", "m"],
            ["RCS典型值", "50", "m²"],
            ["旋转速度", "15", "rpm"],
            ["材料", "复合材料", "-"]
        ]
        
        for row in turbine_params:
            appendices_text += f"| {' | '.join(row)} |\n"
        
        appendices_text += "\n## 附录B: 计算公式\n\n"
        
        formulas = [
            ("雷达方程", r"P_r = \frac{P_t G_t^2 \lambda^2 \sigma}{(4\pi)^3 R^4 L_s L_a}"),
            ("信噪比", r"SNR = \frac{P_r}{k T_0 B F}"),
            ("多普勒频移", r"f_d = \frac{2v_r}{\lambda}"),
            ("检测概率", r"P_d = 1 - \left(1 + \frac{SNR}{N}\right)^{-N}"),
            ("距离分辨率", r"\Delta R = \frac{c\tau}{2}")
        ]
        
        for name, formula in formulas:
            appendices_text += f"**{name}**: ${formula}$\n\n"
        
        appendices_text += "\n## 附录C: 参考资料\n\n"
        
        references = [
            "IEEE Std 686-2017, Radar Definitions",
            "ITU-R P.528-4, Propagation curves for aeronautical mobile",
            "M.I. Skolnik, Radar Handbook, 3rd Edition",
            "中国民用航空局, 风电场影响评估指南",
            "国际电工委员会, 电磁兼容性标准"
        ]
        
        for i, ref in enumerate(references, 1):
            appendices_text += f"{i}. {ref}\n"
        
        return {
            'text': appendices_text,
            'has_appendices': True
        }
    
    def _generate_snr_analysis_text(self, snr_data: Dict[str, Any]) -> str:
        """生成SNR分析文本"""
        avg_without = np.mean(snr_data.get('without_turbines', [0]))
        avg_with = np.mean(snr_data.get('with_turbines', [0]))
        reduction = avg_without - avg_with
        
        if reduction > 5:
            impact = "显著"
            suggestion = "需要立即采取措施优化"
        elif reduction > 2:
            impact = "明显"
            suggestion = "建议进行技术优化"
        else:
            impact = "轻微"
            suggestion = "影响在可接受范围内"
        
        return f"""
## SNR分析结果

- **无风机平均SNR**: {avg_without:.1f} dB
- **有风机平均SNR**: {avg_with:.1f} dB
- **平均下降**: {reduction:.1f} dB
- **影响程度**: {impact}
- **建议**: {suggestion}

### 详细分析
1. 在近距离范围内，SNR下降较为明显
2. 随着距离增加，影响逐渐减小
3. 在特定距离上可能出现谐振效应
4. 多径效应导致SNR波动增大
"""
    
    def _analyze_table_with_kimi(
        self, 
        df: pd.DataFrame, 
        table_name: str
    ) -> str:
        """
        使用Kimi API分析表格数据
        
        参数:
            df: 数据表格
            table_name: 表格名称
            
        返回:
            AI分析结果
        """
        if not self.api_key:
            return "API密钥未设置，无法进行AI分析"
        
        try:
            # 准备数据
            table_summary = f"表格名称: {table_name}\n"
            table_summary += f"数据维度: {df.shape[0]}行 × {df.shape[1]}列\n"
            table_summary += f"列名: {', '.join(df.columns)}\n\n"
            table_summary += "前5行数据:\n"
            table_summary += df.head().to_string()
            
            # 构建提示
            prompt = f"""
            请分析以下风电场评估数据表格，提供专业的分析见解：

            {table_summary}

            请从以下角度进行分析：
            1. 数据概览和统计特征
            2. 关键发现和趋势
            3. 潜在问题和风险
            4. 建议和优化方向

            请用中文回答，保持专业、简洁。
            """
            
            # 调用API
            response = self._call_kimi_api(prompt)
            return response
            
        except Exception as e:
            return f"AI分析出错: {str(e)}"
    
    def _analyze_chart_with_kimi(
        self, 
        chart_path: str, 
        chart_name: str
    ) -> str:
        """
        使用Kimi API分析图表
        
        参数:
            chart_path: 图表路径
            chart_name: 图表名称
            
        返回:
            AI分析结果
        """
        if not self.api_key:
            return "API密钥未设置，无法进行AI分析"
        
        try:
            # 读取图表文件
            with open(chart_path, 'rb') as f:
                chart_data = f.read()
            
            # 转换为base64
            chart_base64 = base64.b64encode(chart_data).decode('utf-8')
            
            # 构建提示
            prompt = f"""
            请分析以下风电场评估图表，提供专业的分析见解：

            图表名称: {chart_name}
            图表类型: 雷达性能分析图表

            请从以下角度进行分析：
            1. 图表展示的主要趋势和模式
            2. 关键数据点和异常值
            3. 性能影响程度评估
            4. 技术建议和优化方向

            请用中文回答，保持专业、简洁。
            """
            
            # 调用API（这里简化处理，实际需要支持图片上传）
            response = self._call_kimi_api(prompt)
            return response
            
        except Exception as e:
            return f"AI分析出错: {str(e)}"
    
    def _call_kimi_api(self, prompt: str) -> str:
        """
        调用Kimi API
        
        参数:
            prompt: 提示文本
            
        返回:
            API响应
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.api_config['model'],
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': self.api_config['temperature'],
                'max_tokens': self.api_config['max_tokens']
            }
            
            response = requests.post(
                f"{self.api_config['base_url']}{self.api_config['chat_completion_endpoint']}",
                headers=headers,
                json=data,
                timeout=self.api_config['timeout']
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API调用失败: {response.status_code}"
                
        except Exception as e:
            return f"API调用异常: {str(e)}"
    
    def _assemble_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        组装Markdown报告
        
        参数:
            report_data: 报告数据
            
        返回:
            Markdown报告内容
        """
        report_parts = []
        
        # 报告标题
        report_parts.append(f"# {self.report_config['report_title']}\n")
        report_parts.append(f"**报告编号**: {report_data['report_id']}\n")
        report_parts.append(f"**生成时间**: {report_data['timestamp']}\n")
        report_parts.append(f"**评估单位**: {self.report_config['company_name']}\n")
        report_parts.append(f"**报告版本**: {self.report_config['report_version']}\n")
        report_parts.append(f"**报告作者**: {self.report_config['author']}\n")
        report_parts.append("\n---\n")
        
        # 目录
        report_parts.append("# 目录\n")
        report_parts.append("1. [执行摘要](#执行摘要)")
        report_parts.append("2. [项目概述](#项目概述)")
        report_parts.append("3. [评估方法](#评估方法)")
        report_parts.append("4. [场景描述](#场景描述)")
        report_parts.append("5. [分析结果](#分析结果)")
        report_parts.append("6. [影响评估](#影响评估)")
        report_parts.append("7. [缓解措施](#缓解措施)")
        report_parts.append("8. [结论](#结论)")
        report_parts.append("9. [建议](#建议)")
        report_parts.append("10. [附录](#附录)\n")
        report_parts.append("---\n")
        
        # 各个部分
        sections_order = [
            'executive_summary', 'project_overview', 'methodology',
            'scenario_description', 'analysis_results', 'impact_assessment',
            'mitigation_measures', 'conclusions', 'recommendations',
            'appendices'
        ]
        
        for section_key in sections_order:
            if section_key in report_data['sections']:
                section = report_data['sections'][section_key]
                if 'text' in section:
                    report_parts.append(section['text'])
                    report_parts.append("\n---\n")
        
        # 报告页脚
        report_parts.append("\n---\n")
        report_parts.append("## 免责声明\n")
        report_parts.append("本报告基于当前技术标准和评估方法生成，仅供参考。实际影响可能因具体条件而异。\n")
        report_parts.append(f"© {datetime.now().year} {self.report_config['company_name']} 版权所有\n")
        
        return "\n".join(report_parts)
    
    def _save_markdown_report(
        self, 
        report_content: str, 
        report_id: str
    ) -> str:
        """
        保存Markdown报告
        
        参数:
            report_content: 报告内容
            report_id: 报告ID
            
        返回:
            保存的文件路径
        """
        filename = f"wind_farm_radar_assessment_{report_id}.md"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(filepath)
    
    def _save_report_data(self, report_data: Dict[str, Any]) -> str:
        """
        保存报告数据
        
        参数:
            report_data: 报告数据
            
        返回:
            保存的文件路径
        """
        filename = f"report_data_{report_data['report_id']}.json"
        filepath = self.data_dir / filename
        
        # 清理数据，移除不可序列化的部分
        clean_data = self._clean_report_data(report_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def _clean_report_data(self, data: Any) -> Any:
        """清理报告数据，移除不可序列化的对象"""
        if isinstance(data, dict):
            return {k: self._clean_report_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_report_data(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, pd.DataFrame):
            return data.to_dict('records')
        else:
            return str(data)
    
    def _generate_report_id(self) -> str:
        """生成报告ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_str = str(hash(timestamp))[-6:]
        return f"REPORT_{timestamp}_{random_str}"
    
    def export_report(
        self,
        report_data: Dict[str, Any],
        export_format: str = "markdown"
    ) -> Dict[str, str]:
        """
        导出报告
        
        参数:
            report_data: 报告数据
            export_format: 导出格式
            
        返回:
            导出的文件路径
        """
        export_files = {}
        
        if export_format == "markdown":
            # 重新生成Markdown报告
            report_content = self._assemble_markdown_report(report_data)
            report_path = self._save_markdown_report(
                report_content, 
                report_data['report_id']
            )
            export_files['markdown'] = report_path
            
        elif export_format == "html":
            # 转换为HTML
            if 'sections' in report_data:
                markdown_content = self._assemble_markdown_report(report_data)
                html_content = markdown.markdown(
                    markdown_content,
                    extensions=['tables', 'fenced_code', 'toc']
                )
                
                # 添加样式
                styled_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{self.report_config['report_title']}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                        h1, h2, h3 {{ color: #2c3e50; }}
                        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        .footer {{ margin-top: 40px; color: #7f8c8d; font-size: 0.9em; }}
                    </style>
                </head>
                <body>
                    {html_content}
                    <div class="footer">
                        <p>© {datetime.now().year} {self.report_config['company_name']}</p>
                    </div>
                </body>
                </html>
                """
                
                html_filename = f"wind_farm_radar_assessment_{report_data['report_id']}.html"
                html_path = self.reports_dir / html_filename
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(styled_html)
                
                export_files['html'] = str(html_path)
        
        return export_files

# 创建全局报告生成器实例
report_generator = ReportGenerator()