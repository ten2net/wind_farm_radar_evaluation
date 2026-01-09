"""
效能评估模块
"""
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class AssessmentMetrics:
    """评估指标"""
    # 雷达性能指标
    detection_probability: float
    false_alarm_rate: float
    coverage_area: float
    response_time: float
    
    # 干扰效能指标
    jam_success_rate: float
    j_s_ratio: float
    suppression_depth: float
    coverage_reduction: float
    
    # 系统效能指标
    system_availability: float
    survivability: float
    information_superiority: float
    operational_efficiency: float
    
    # 网络效能指标
    network_connectivity: float
    data_fusion_quality: float
    decision_support_level: float
    situation_awareness: float

class EWAssessor:
    """电子战效能评估器"""
    
    @staticmethod
    def assess_radar_performance(radar_data: Dict, targets: List) -> Dict:
        """评估雷达性能"""
        metrics = {
            'detection_probability': 0.0,
            'false_alarm_rate': 0.001,
            'track_accuracy': 0.0,
            'reaction_time': 0.0
        }
        
        # 简化的评估模型
        if 'detection_history' in radar_data:
            detections = radar_data['detection_history']
            if detections:
                metrics['detection_probability'] = len([d for d in detections if d.get('detected', False)]) / len(detections)
        
        # 计算跟踪精度
        if 'tracking_errors' in radar_data and radar_data['tracking_errors']:
            errors = radar_data['tracking_errors']
            metrics['track_accuracy'] = 1.0 / (1.0 + np.mean(errors))
        
        return metrics
    
    @staticmethod
    def assess_jamming_effect(jamming_data: Dict, radar_performance: Dict) -> Dict:
        """评估干扰效果"""
        metrics = {
            'jam_success_rate': 0.0,
            'j_s_ratio': 0.0,
            'suppression_factor': 0.0,
            'effectiveness_level': 'low'
        }
        
        # 基于J/S比评估
        j_s_ratio = jamming_data.get('j_s_ratio', 0)
        metrics['j_s_ratio'] = j_s_ratio
        
        # 计算干扰成功率
        if j_s_ratio > 20:
            metrics['jam_success_rate'] = 1.0
            metrics['effectiveness_level'] = 'excellent'
        elif j_s_ratio > 10:
            metrics['jam_success_rate'] = 0.8
            metrics['effectiveness_level'] = 'good'
        elif j_s_ratio > 3:
            metrics['jam_success_rate'] = 0.5
            metrics['effectiveness_level'] = 'fair'
        else:
            metrics['jam_success_rate'] = 0.2
            metrics['effectiveness_level'] = 'poor'
        
        # 计算压制系数
        detection_prob = radar_performance.get('detection_probability', 0.8)
        metrics['suppression_factor'] = 1.0 - detection_prob
        
        return metrics
    
    @staticmethod
    def assess_network_performance(network_data: Dict) -> Dict:
        """评估网络性能"""
        metrics = {
            'coverage_ratio': 0.0,
            'redundancy_level': 0.0,
            'information_fusion': 0.0,
            'decision_support': 0.0
        }
        
        # 简化的网络评估
        if 'nodes' in network_data and 'connections' in network_data:
            nodes = network_data['nodes']
            connections = network_data['connections']
            
            if nodes:
                # 覆盖率
                metrics['coverage_ratio'] = len(nodes) / 10.0  # 简化
                
                # 冗余度
                if connections:
                    avg_connections = len(connections) / len(nodes)
                    metrics['redundancy_level'] = min(1.0, avg_connections / 3.0)
        
        return metrics
    
    @staticmethod
    def calculate_system_effectiveness(radar_metrics: Dict, 
                                     jamming_metrics: Dict,
                                     network_metrics: Dict) -> Dict:
        """计算系统综合效能"""
        effectiveness = {
            'overall_score': 0.0,
            'radar_contribution': 0.0,
            'jammer_contribution': 0.0,
            'network_contribution': 0.0,
            'recommendations': []
        }
        
        # 计算各分项贡献
        radar_score = radar_metrics.get('detection_probability', 0.5) * 0.4
        jammer_score = jamming_metrics.get('jam_success_rate', 0.3) * 0.4
        network_score = network_metrics.get('coverage_ratio', 0.5) * 0.2
        
        effectiveness['radar_contribution'] = radar_score
        effectiveness['jammer_contribution'] = jammer_score
        effectiveness['network_contribution'] = network_score
        
        # 计算总体效能
        overall_score = radar_score + jammer_score + network_score
        effectiveness['overall_score'] = overall_score
        
        # 生成建议
        if overall_score < 0.3:
            effectiveness['recommendations'].extend([
                "系统效能较低，建议全面优化",
                "增加雷达部署密度",
                "提升干扰功率"
            ])
        elif overall_score < 0.6:
            effectiveness['recommendations'].extend([
                "系统效能中等，有提升空间",
                "优化网络连接",
                "改进干扰策略"
            ])
        else:
            effectiveness['recommendations'].extend([
                "系统效能良好",
                "保持当前配置",
                "考虑增加冗余度"
            ])
        
        return effectiveness
    
    @staticmethod
    def assess_scenario(scenario_data: Dict) -> Dict:
        """评估对抗想定"""
        assessment = {
            'scenario_name': scenario_data.get('name', '未知想定'),
            'assessment_time': datetime.now().isoformat(),
            'entity_counts': {},
            'performance_metrics': {},
            'effectiveness_scores': {}
        }
        
        # 统计实体数量
        entities = scenario_data.get('entities', {})
        assessment['entity_counts'] = {
            'radars': len(entities.get('radars', [])),
            'jammers': len(entities.get('jammers', [])),
            'targets': len(entities.get('targets', []))
        }
        
        # 评估性能
        radar_performance = EWAssessor.assess_radar_performance(
            scenario_data.get('radar_data', {}),
            scenario_data.get('targets', [])
        )
        
        jamming_performance = EWAssessor.assess_jamming_effect(
            scenario_data.get('jamming_data', {}),
            radar_performance
        )
        
        network_performance = EWAssessor.assess_network_performance(
            scenario_data.get('network_data', {})
        )
        
        assessment['performance_metrics'] = {
            'radar': radar_performance,
            'jamming': jamming_performance,
            'network': network_performance
        }
        
        # 计算综合效能
        system_effectiveness = EWAssessor.calculate_system_effectiveness(
            radar_performance, jamming_performance, network_performance
        )
        
        assessment['effectiveness_scores'] = system_effectiveness
        
        return assessment

class TrendAnalyzer:
    """趋势分析器"""
    
    @staticmethod
    def analyze_trends(historical_data: List[Dict], window: int = 5) -> Dict:
        """分析历史数据趋势"""
        if not historical_data:
            return {}
        
        trends = {
            'overall_trend': 'stable',
            'trend_scores': {},
            'predictions': {}
        }
        
        # 提取时间序列数据
        timestamps = []
        scores = []
        
        for data in historical_data:
            if 'assessment_time' in data and 'effectiveness_scores' in data:
                timestamp = data['assessment_time']
                score = data['effectiveness_scores'].get('overall_score', 0)
                
                timestamps.append(timestamp)
                scores.append(score)
        
        if len(scores) < 2:
            return trends
        
        # 计算趋势
        recent_scores = scores[-window:] if len(scores) > window else scores
        if len(recent_scores) > 1:
            # 线性回归
            x = np.arange(len(recent_scores))
            y = np.array(recent_scores)
            
            slope, intercept = np.polyfit(x, y, 1)
            
            if slope > 0.01:
                trends['overall_trend'] = 'improving'
            elif slope < -0.01:
                trends['overall_trend'] = 'declining'
            else:
                trends['overall_trend'] = 'stable'
            
            trends['trend_scores'] = {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(np.corrcoef(x, y)[0, 1] ** 2)
            }
            
            # 简单预测
            if len(scores) > 3:
                # 使用移动平均进行预测
                future_steps = 3
                predictions = []
                
                for i in range(future_steps):
                    if i < len(scores):
                        window_scores = scores[max(0, i - window + 1):i + 1]
                        pred = np.mean(window_scores) if window_scores else scores[-1]
                    else:
                        pred = scores[-1] + slope * (i - len(scores) + 1)
                    
                    predictions.append(max(0, min(1, pred)))
                
                trends['predictions'] = {
                    'next_steps': predictions,
                    'confidence': min(0.9, len(scores) / 20.0)
                }
        
        return trends
    
    @staticmethod
    def identify_bottlenecks(assessment_data: Dict) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        metrics = assessment_data.get('performance_metrics', {})
        
        # 检查雷达性能
        radar_metrics = metrics.get('radar', {})
        if radar_metrics.get('detection_probability', 0) < 0.5:
            bottlenecks.append("雷达探测概率低")
        if radar_metrics.get('false_alarm_rate', 0) > 0.01:
            bottlenecks.append("雷达虚警率高")
        
        # 检查干扰性能
        jamming_metrics = metrics.get('jamming', {})
        if jamming_metrics.get('jam_success_rate', 0) < 0.5:
            bottlenecks.append("干扰成功率低")
        if jamming_metrics.get('j_s_ratio', 0) < 3:
            bottlenecks.append("干信比不足")
        
        # 检查网络性能
        network_metrics = metrics.get('network', {})
        if network_metrics.get('coverage_ratio', 0) < 0.5:
            bottlenecks.append("网络覆盖率不足")
        if network_metrics.get('redundancy_level', 0) < 0.3:
            bottlenecks.append("网络冗余度低")
        
        return bottlenecks

class ReportGenerator:
    """评估报告生成器"""
    
    @staticmethod
    def generate_assessment_report(assessment_data: Dict, format: str = "markdown") -> str:
        """生成评估报告"""
        if format == "markdown":
            return ReportGenerator._generate_markdown_report(assessment_data)
        elif format == "html":
            return ReportGenerator._generate_html_report(assessment_data)
        else:
            return str(assessment_data)
    
    @staticmethod
    def _generate_markdown_report(assessment_data: Dict) -> str:
        """生成Markdown格式报告"""
        report = []
        
        # 标题
        report.append(f"# 电子战对抗效能评估报告")
        report.append(f"**想定名称**: {assessment_data.get('scenario_name', '未知')}")
        report.append(f"**评估时间**: {assessment_data.get('assessment_time', '未知')}")
        report.append("")
        
        # 实体统计
        report.append("## 实体统计")
        counts = assessment_data.get('entity_counts', {})
        report.append(f"- 雷达数量: {counts.get('radars', 0)}")
        report.append(f"- 干扰机数量: {counts.get('jammers', 0)}")
        report.append(f"- 目标数量: {counts.get('targets', 0)}")
        report.append("")
        
        # 性能指标
        report.append("## 性能指标")
        metrics = assessment_data.get('performance_metrics', {})
        
        report.append("### 雷达性能")
        radar_metrics = metrics.get('radar', {})
        report.append(f"- 探测概率: {radar_metrics.get('detection_probability', 0):.1%}")
        report.append(f"- 虚警率: {radar_metrics.get('false_alarm_rate', 0):.3%}")
        
        report.append("### 干扰效能")
        jamming_metrics = metrics.get('jamming', {})
        report.append(f"- 干扰成功率: {jamming_metrics.get('jam_success_rate', 0):.1%}")
        report.append(f"- 干信比: {jamming_metrics.get('j_s_ratio', 0):.1f} dB")
        report.append(f"- 干扰等级: {jamming_metrics.get('effectiveness_level', '未知')}")
        
        report.append("### 网络效能")
        network_metrics = metrics.get('network', {})
        report.append(f"- 覆盖率: {network_metrics.get('coverage_ratio', 0):.1%}")
        report.append(f"- 冗余度: {network_metrics.get('redundancy_level', 0):.1%}")
        report.append("")
        
        # 综合效能
        report.append("## 综合效能")
        effectiveness = assessment_data.get('effectiveness_scores', {})
        
        report.append(f"**总体评分**: {effectiveness.get('overall_score', 0):.3f}")
        report.append("")
        report.append("**贡献度分析**:")
        report.append(f"- 雷达贡献: {effectiveness.get('radar_contribution', 0):.3f}")
        report.append(f"- 干扰贡献: {effectiveness.get('jammer_contribution', 0):.3f}")
        report.append(f"- 网络贡献: {effectiveness.get('network_contribution', 0):.3f}")
        report.append("")
        
        # 建议
        report.append("## 优化建议")
        recommendations = effectiveness.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                report.append(f"- {rec}")
        else:
            report.append("- 暂无建议")
        report.append("")
        
        return "\n".join(report)
    
    @staticmethod
    def _generate_html_report(assessment_data: Dict) -> str:
        """生成HTML格式报告"""
        markdown = ReportGenerator._generate_markdown_report(assessment_data)
        
        # 简单的Markdown转HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>电子战对抗效能评估报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                h3 {{ color: #7f8c8d; }}
                .metric {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #3498db; }}
                .recommendation {{ margin: 5px 0; padding: 8px; background: #e8f4fc; border-radius: 4px; }}
            </style>
        </head>
        <body>
        """
        
        # 简单的转换
        lines = markdown.split('\n')
        for line in lines:
            if line.startswith('# '):
                html += f'<h1>{line[2:]}</h1>'
            elif line.startswith('## '):
                html += f'<h2>{line[3:]}</h2>'
            elif line.startswith('### '):
                html += f'<h3>{line[4:]}</h3>'
            elif line.startswith('- '):
                if '建议' in line:
                    html += f'<div class="recommendation">{line[2:]}</div>'
                else:
                    html += f'<div class="metric">{line[2:]}</div>'
            elif line.startswith('**'):
                html += f'<p><strong>{line[2:-2]}</strong></p>'
            elif line.strip():
                html += f'<p>{line}</p>'
            else:
                html += '<br>'
        
        html += """
        </body>
        </html>
        """
        
        return html
