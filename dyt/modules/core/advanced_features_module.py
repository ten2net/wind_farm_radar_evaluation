# advanced_features_module.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import threading
import time
import socket
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

class MultiTargetCoordination:
    """多目标协同攻击模块"""
    
    def __init__(self):
        self.target_priority_weights = {
            'awacs': 0.9,      # 预警机最高优先级
            'radar_station': 0.8,  # 雷达站
            'bomber': 0.7,     # 轰炸机
            'warship': 0.6,    # 军舰
            'fighter': 0.5      # 战斗机
        }
        self.coordination_mode = "sequential"  # sequential, simultaneous, adaptive
        
    def calculate_target_priority(self, target, missile_position, battlefield):
        """计算目标攻击优先级"""
        # 基础优先级
        base_priority = self.target_priority_weights.get(target.target_type.value, 0.5)
        
        # 距离因素（越近优先级越高）
        distance = self.calculate_distance(missile_position, target.position)
        distance_factor = max(0.1, 1 - distance / 200)  # 200km最大影响距离
        
        # 威胁因素（辐射功率越大威胁越大）
        threat_factor = target.emission_power
        
        # 干扰因素（有干扰保护的目标优先级调整）
        jamming_protection = self._get_jamming_protection(target, battlefield)
        jamming_factor = 1.0 if jamming_protection else 1.2  # 无保护目标优先级稍高
        
        # 综合优先级
        priority = base_priority * distance_factor * threat_factor * jamming_factor
        
        return {
            'target_id': target.target_id,
            'priority': priority,
            'distance': distance,
            'threat_level': threat_factor,
            'jamming_protected': jamming_protection
        }
    
    def _get_jamming_protection(self, target, battlefield):
        """检查目标是否有干扰保护"""
        for jammer in battlefield.jammers.values():
            if jammer.target_id == target.target_id:
                return True
        return False
    
    def plan_attack_sequence(self, battlefield, guidance_system):
        """规划攻击序列"""
        missile_pos = battlefield.missile_position
        targets_priority = []
        
        for target in battlefield.targets.values():
            priority_info = self.calculate_target_priority(target, missile_pos, battlefield)
            targets_priority.append(priority_info)
        
        # 按优先级排序
        targets_priority.sort(key=lambda x: x['priority'], reverse=True)
        
        return targets_priority
    
    def create_attack_plan_chart(self, attack_plan):
        """创建攻击计划图表"""
        if not attack_plan:
            return go.Figure()
        
        df = pd.DataFrame(attack_plan)
        df['color'] = df['priority'].apply(
            lambda x: 'green' if x > 0.7 else 'orange' if x > 0.5 else 'red'
        )
        
        fig = go.Figure(data=[
            go.Bar(
                x=df['target_id'],
                y=df['priority'],
                marker_color=df['color'],
                text=df['priority'].round(3),
                textposition='auto',
                hovertemplate=(
                    "目标: %{x}<br>" +
                    "优先级: %{y:.3f}<br>" +
                    "距离: %{customdata:.1f}km<br>" +
                    "威胁等级: %{customdata2:.2f}"
                ),
                customdata=df['distance'],
                customdata2=df['threat_level']
            )
        ])
        
        fig.update_layout(
            title="多目标攻击优先级规划",
            xaxis_title="目标ID",
            yaxis_title="攻击优先级",
            yaxis_range=[0, 1],
            height=400
        )
        
        return fig

class AdvancedElectronicWarfare:
    """高级电子对抗模块"""
    
    def __init__(self):
        self.jamming_techniques = {
            'noise': {
                'name': '噪声压制',
                'effectiveness': 0.8,
                'counter_measures': ['frequency_hopping', 'power_management']
            },
            'deception': {
                'name': '欺骗干扰',
                'effectiveness': 0.6,
                'counter_measures': ['waveform_agility', 'polarization_diversity']
            },
            'smart_noise': {
                'name': '灵巧噪声',
                'effectiveness': 0.7,
                'counter_measures': ['adaptive_filtering', 'time_diversity']
            },
            'drm': {
                'name': 'DRM干扰',
                'effectiveness': 0.9,
                'counter_measures': ['spatial_filtering', 'multi_static']
            }
        }
        
        self.ecm_techniques = {
            'frequency_hopping': {'effectiveness': 0.7, 'description': '频率捷变'},
            'power_management': {'effectiveness': 0.5, 'description': '功率管理'},
            'waveform_agility': {'effectiveness': 0.8, 'description': '波形捷变'},
            'polarization_diversity': {'effectiveness': 0.6, 'description': '极化分集'},
            'adaptive_filtering': {'effectiveness': 0.75, 'description': '自适应滤波'},
            'time_diversity': {'effectiveness': 0.65, 'description': '时间分集'},
            'spatial_filtering': {'effectiveness': 0.85, 'description': '空间滤波'},
            'multi_static': {'effectiveness': 0.9, 'description': '多基地雷达'}
        }
    
    def simulate_jamming_effect(self, jamming_type, distance, guidance_system):
        """模拟干扰效果"""
        technique = self.jamming_techniques.get(jamming_type, {})
        base_effectiveness = technique.get('effectiveness', 0.5)
        
        # 距离衰减
        distance_factor = max(0.1, 1 - distance / 100)
        
        # 导引头抗干扰能力
        system_resistance = getattr(guidance_system, 'jamming_resistance', 0.5)
        
        # 综合干扰效果
        jamming_effect = base_effectiveness * distance_factor * (1 - system_resistance)
        
        return min(1.0, jamming_effect)
    
    def apply_ecm_countermeasures(self, guidance_system, jamming_type):
        """应用电子对抗措施"""
        technique = self.jamming_techniques.get(jamming_type, {})
        counter_measures = technique.get('counter_measures', [])
        
        total_improvement = 0.0
        applied_measures = []
        
        for measure in counter_measures:
            if measure in self.ecm_techniques:
                effectiveness = self.ecm_techniques[measure]['effectiveness']
                total_improvement += effectiveness * 0.2  # 每个措施改善20%
                applied_measures.append({
                    'technique': measure,
                    'description': self.ecm_techniques[measure]['description'],
                    'improvement': effectiveness * 0.2
                })
        
        return {
            'total_improvement': min(0.5, total_improvement),  # 最大改善50%
            'applied_measures': applied_measures,
            'new_performance': guidance_system.current_performance + total_improvement
        }
    
    def create_ew_analysis_dashboard(self, battlefield, guidance_system):
        """创建电子战分析面板"""
        # 分析当前干扰环境
        jamming_analysis = self.analyze_jamming_environment(battlefield, guidance_system)
        
        # 创建图表
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['干扰源分析', '抗干扰措施效果', '频率对抗', '空间对抗'],
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "heatmap"}, {"type": "scatter"}]]
        )
        
        # 干扰源分析
        jammer_data = []
        for jammer in battlefield.jammers.values():
            effect = self.simulate_jamming_effect(
                jammer.jamming_type.value, 
                50,  # 假设距离
                guidance_system
            )
            jammer_data.append({
                'name': f"干扰源{jammer.jammer_id}",
                'effect': effect * 100,
                'type': jammer.jamming_type.value
            })
        
        if jammer_data:
            df = pd.DataFrame(jammer_data)
            fig.add_trace(
                go.Bar(
                    x=df['name'],
                    y=df['effect'],
                    name="干扰效果",
                    marker_color='red'
                ), row=1, col=1
            )
        
        # 抗干扰措施
        ecm_results = []
        for jamming_type in self.jamming_techniques.keys():
            result = self.apply_ecm_countermeasures(guidance_system, jamming_type)
            ecm_results.append({
                'jamming_type': jamming_type,
                'improvement': result['total_improvement'] * 100
            })
        
        if ecm_results:
            df_ecm = pd.DataFrame(ecm_results)
            fig.add_trace(
                go.Pie(
                    labels=df_ecm['jamming_type'],
                    values=df_ecm['improvement'],
                    name="抗干扰改善"
                ), row=1, col=2
            )
        
        fig.update_layout(height=600, showlegend=False)
        return fig
    
    def analyze_jamming_environment(self, battlefield, guidance_system):
        """分析干扰环境"""
        analysis = {
            'total_jammers': len(battlefield.jammers),
            'jamming_power': 0.0,
            'recommended_ecm': [],
            'threat_level': '低'
        }
        
        total_power = 0.0
        for jammer in battlefield.jammers.values():
            effect = self.simulate_jamming_effect(
                jammer.jamming_type.value, 50, guidance_system
            )
            total_power += effect * jammer.power
            
            # 推荐对抗措施
            technique = self.jamming_techniques.get(jammer.jamming_type.value, {})
            analysis['recommended_ecm'].extend(technique.get('counter_measures', []))
        
        analysis['jamming_power'] = total_power
        analysis['threat_level'] = self._assess_threat_level(total_power)
        
        return analysis
    
    def _assess_threat_level(self, jamming_power):
        """评估威胁等级"""
        if jamming_power > 0.7:
            return "极高"
        elif jamming_power > 0.5:
            return "高"
        elif jamming_power > 0.3:
            return "中"
        else:
            return "低"

class SystemEffectivenessEvaluator:
    """系统效能评估模块"""
    
    def __init__(self):
        self.metrics_weights = {
            'detection_range': 0.2,
            'jamming_resistance': 0.25,
            'stealth': 0.15,
            'accuracy': 0.2,
            'reliability': 0.1,
            'cost': 0.1
        }
    
    def calculate_system_effectiveness(self, guidance_system, battlefield, mission_type="air_superiority"):
        """计算系统效能"""
        # 根据任务类型调整权重
        weights = self._adjust_weights_for_mission(mission_type)
        
        # 计算各项指标
        metrics = self._calculate_all_metrics(guidance_system, battlefield)
        
        # 综合效能得分
        effectiveness = 0.0
        for metric, value in metrics.items():
            effectiveness += value * weights.get(metric, 0)
        
        return {
            'overall_effectiveness': effectiveness * 100,
            'metrics': metrics,
            'weights': weights,
            'mission_type': mission_type
        }
    
    def _adjust_weights_for_mission(self, mission_type):
        """根据任务类型调整权重"""
        base_weights = self.metrics_weights.copy()
        
        mission_adjustments = {
            'air_superiority': {'jamming_resistance': 0.3, 'stealth': 0.2},
            'sead': {'detection_range': 0.3, 'jamming_resistance': 0.3},
            'naval': {'accuracy': 0.3, 'reliability': 0.15},
            'recon': {'stealth': 0.3, 'detection_range': 0.25}
        }
        
        adjustment = mission_adjustments.get(mission_type, {})
        for metric, weight in adjustment.items():
            if metric in base_weights:
                # 调整权重，保持总和为1
                base_weights[metric] = weight
        
        return self._normalize_weights(base_weights)
    
    def _calculate_all_metrics(self, guidance_system, battlefield):
        """计算所有效能指标"""
        return {
            'detection_range': self._normalize_metric(
                guidance_system.detection_range, 0, 200
            ),
            'jamming_resistance': guidance_system.jamming_resistance,
            'stealth': guidance_system.stealth_level,
            'accuracy': getattr(guidance_system, 'accuracy', 0.7),
            'reliability': self._estimate_reliability(guidance_system),
            'cost': self._estimate_cost(guidance_system)
        }
    
    def _normalize_metric(self, value, min_val, max_val):
        """归一化指标"""
        return (value - min_val) / (max_val - min_val)
    
    def _estimate_reliability(self, guidance_system):
        """估计可靠性"""
        # 简化模型：复合制导最可靠，主动次之，被动最低
        reliability_map = {
            'PassiveRadarSeeker': 0.8,
            'ActiveRadarSeeker': 0.85,
            'CompositeSeeker': 0.9
        }
        return reliability_map.get(guidance_system.__class__.__name__, 0.8)
    
    def _estimate_cost(self, guidance_system):
        """估计成本（反向指标，成本越低越好）"""
        cost_map = {
            'PassiveRadarSeeker': 0.8,  # 成本较低
            'ActiveRadarSeeker': 0.4,   # 成本较高
            'CompositeSeeker': 0.2     # 成本最高
        }
        return cost_map.get(guidance_system.__class__.__name__, 0.5)
    
    def _normalize_weights(self, weights):
        """归一化权重使其和为1"""
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
    
    def create_effectiveness_radar(self, effectiveness_results):
        """创建效能雷达图"""
        metrics = effectiveness_results['metrics']
        weights = effectiveness_results['weights']
        
        categories = list(metrics.keys())
        values = [metrics[cat] * 100 for cat in categories]  # 转换为百分比
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # 闭合图形
            theta=categories + [categories[0]],
            fill='toself',
            name='系统效能',
            line=dict(color='blue', width=3)
        ))
        
        # 添加权重指示
        weight_values = [weights[cat] * 100 for cat in categories] + [weights[categories[0]] * 100]
        fig.add_trace(go.Scatterpolar(
            r=weight_values,
            theta=categories + [categories[0]],
            name='权重分配',
            line=dict(color='red', width=2, dash='dot')
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            title=f"系统效能评估 - {effectiveness_results['mission_type']}",
            height=500
        )
        
        return fig

class DistributedSimulation:
    """分布式仿真支持模块"""
    
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.connected_clients = []
        self.simulation_state = {}
        self.is_master = False
        
    async def start_master_node(self):
        """启动主节点"""
        self.is_master = True
        # 这里实现主节点逻辑
        pass
    
    async def connect_to_master(self, master_host, master_port):
        """连接到主节点"""
        try:
            # 实现连接逻辑
            pass
        except Exception as e:
            print(f"连接主节点失败: {e}")
    
    def synchronize_simulation_state(self, state_data):
        """同步仿真状态"""
        self.simulation_state.update(state_data)
        
    def distribute_calculation(self, calculation_type, data):
        """分布式计算"""
        if calculation_type == "terrain_analysis":
            return self._distribute_terrain_calculation(data)
        elif calculation_type == "ew_analysis":
            return self._distribute_ew_calculation(data)
        else:
            return self._local_calculation(data)
    
    def _distribute_terrain_analysis(self, terrain_data):
        """分布式地形分析"""
        # 实现地形分析的分布式计算
        pass
    
    def _distribute_ew_analysis(self, ew_data):
        """分布式电子战分析"""
        # 实现电子战分析的分布式计算
        pass

class RealTimeCollaboration:
    """实时协作模块"""
    
    def __init__(self):
        self.collaborators = {}
        self.shared_workspace = {}
        self.chat_messages = []
        
    def add_collaborator(self, user_id, user_name, role="viewer"):
        """添加协作者"""
        self.collaborators[user_id] = {
            'name': user_name,
            'role': role,
            'join_time': datetime.now(),
            'last_active': datetime.now()
        }
    
    def share_simulation_state(self, state_data, user_id=None):
        """共享仿真状态"""
        self.shared_workspace['simulation_state'] = state_data
        self.shared_workspace['last_update'] = datetime.now()
        self.shared_workspace['updated_by'] = user_id
        
    def add_chat_message(self, user_id, message, message_type="text"):
        """添加聊天消息"""
        chat_msg = {
            'user_id': user_id,
            'user_name': self.collaborators[user_id]['name'],
            'message': message,
            'type': message_type,
            'timestamp': datetime.now()
        }
        self.chat_messages.append(chat_msg)
        
        # 保持消息数量合理
        if len(self.chat_messages) > 100:
            self.chat_messages = self.chat_messages[-50:]
    
    def get_collaboration_dashboard(self):
        """获取协作面板数据"""
        return {
            'collaborators': list(self.collaborators.values()),
            'active_users': len([c for c in self.collaborators.values() 
                               if (datetime.now() - c['last_active']).seconds < 300]),
            'chat_messages': self.chat_messages[-20:],  # 最近20条消息
            'workspace_status': self.shared_workspace
        }

class AdvancedVisualization:
    """高级可视化模块"""
    
    def create_3d_battlefield(self, battlefield, guidance_system):
        """创建3D战场可视化"""
        fig = go.Figure()
        
        # 添加导弹位置
        missile_pos = battlefield.missile_position
        fig.add_trace(go.Scatter3d(
            x=[missile_pos.lon],
            y=[missile_pos.lat], 
            z=[missile_pos.alt],
            mode='markers',
            marker=dict(size=10, color='red'),
            name='导弹'
        ))
        
        # 添加目标
        for target in battlefield.targets.values():
            fig.add_trace(go.Scatter3d(
                x=[target.position.lon],
                y=[target.position.lat],
                z=[target.position.alt],
                mode='markers',
                marker=dict(size=8, color='blue'),
                name=f'目标{target.target_id}'
            ))
        
        # 添加干扰源
        for jammer in battlefield.jammers.values():
            fig.add_trace(go.Scatter3d(
                x=[jammer.position.lon],
                y=[jammer.position.lat],
                z=[jammer.position.alt],
                mode='markers',
                marker=dict(size=6, color='purple'),
                name=f'干扰源{jammer.jammer_id}'
            ))
        
        # 添加导弹轨迹
        if guidance_system.trajectory:
            lons = [point.position.lon for point in guidance_system.trajectory]
            lats = [point.position.lat for point in guidance_system.trajectory]
            alts = [point.position.alt for point in guidance_system.trajectory]
            
            fig.add_trace(go.Scatter3d(
                x=lons, y=lats, z=alts,
                mode='lines',
                line=dict(color='green', width=4),
                name='导弹轨迹'
            ))
        
        fig.update_layout(
            title="3D战场态势",
            scene=dict(
                xaxis_title='经度',
                yaxis_title='纬度', 
                zaxis_title='海拔 (m)'
            ),
            height=600
        )
        
        return fig
    
    def create_time_slider_visualization(self, simulation_history):
        """创建带时间滑块的动态可视化"""
        if not simulation_history:
            return go.Figure()
        
        # 创建时间序列数据
        times = [point['timestamp'] for point in simulation_history]
        performances = [point['performance'] * 100 for point in simulation_history]
        distances = [point.get('target_distance', 0) for point in simulation_history]
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 性能曲线
        fig.add_trace(
            go.Scatter(x=times, y=performances, name="性能", line=dict(color='blue')),
            secondary_y=False
        )
        
        # 距离曲线
        fig.add_trace(
            go.Scatter(x=times, y=distances, name="目标距离", line=dict(color='red')),
            secondary_y=True
        )
        
        # 添加时间滑块
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1min", step="minute", stepmode="backward"),
                        dict(count=5, label="5min", step="minute", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            ),
            title="仿真时间线（可交互）",
            height=400
        )
        
        return fig

class AIAssistant:
    """AI智能分析助手模块"""
    
    def __init__(self):
        self.analysis_history = []
        
    def analyze_simulation_results(self, simulation_data):
        """分析仿真结果并提供建议"""
        analysis = {
            'summary': self._generate_summary(simulation_data),
            'strengths': self._identify_strengths(simulation_data),
            'weaknesses': self._identify_weaknesses(simulation_data),
            'recommendations': self._generate_recommendations(simulation_data),
            'risk_assessment': self._assess_risks(simulation_data)
        }
        
        self.analysis_history.append({
            'timestamp': datetime.now(),
            'analysis': analysis
        })
        
        return analysis
    
    def _generate_summary(self, data):
        """生成仿真摘要"""
        performance = data.get('performance', 0) * 100
        if performance > 80:
            return "仿真表现优秀，系统在复杂电磁环境下仍保持高效性能"
        elif performance > 60:
            return "仿真表现良好，系统在多数情况下能够有效工作"
        elif performance > 40:
            return "仿真表现一般，系统性能受到明显影响"
        else:
            return "仿真表现较差，需要优化系统配置或战术"
    
    def _identify_strengths(self, data):
        """识别优势"""
        strengths = []
        if data.get('jamming_resistance', 0) > 0.7:
            strengths.append("强大的抗干扰能力")
        if data.get('stealth', 0) > 0.7:
            strengths.append("良好的隐蔽性能")
        if data.get('detection_range', 0) > 80:
            strengths.append("优秀的探测距离")
        
        return strengths if strengths else ["无明显优势"]
    
    def _identify_weaknesses(self, data):
        """识别弱点"""
        weaknesses = []
        if data.get('performance', 0) < 0.5:
            weaknesses.append("整体性能不足")
        if data.get('reliability', 0) < 0.6:
            weaknesses.append("系统可靠性有待提高")
        if data.get('cost', 0) < 0.3:  # 成本指标是反向的
            weaknesses.append("系统成本较高")
        
        return weaknesses if weaknesses else ["无明显弱点"]
    
    def _generate_recommendations(self, data):
        """生成改进建议"""
        recommendations = []
        
        if data.get('jamming_resistance', 0) < 0.6:
            recommendations.append("考虑增加频率捷变功能提升抗干扰能力")
        if data.get('detection_range', 0) < 60:
            recommendations.append("优化天线设计以提高探测距离")
        if data.get('performance', 0) < 0.6:
            recommendations.append("建议采用复合制导方案提升整体性能")
        
        return recommendations if recommendations else ["当前配置较为合理"]
    
    def _assess_risks(self, data):
        """评估风险"""
        risk_level = "低"
        risks = []
        
        performance = data.get('performance', 0) * 100
        if performance < 30:
            risk_level = "极高"
            risks.append("系统在复杂电磁环境下可能完全失效")
        elif performance < 50:
            risk_level = "高"
            risks.append("系统性能不稳定，存在任务失败风险")
        elif performance < 70:
            risk_level = "中"
            risks.append("系统在特定条件下可能表现不佳")
        else:
            risk_level = "低"
            risks.append("系统风险可控")
        
        return {
            'level': risk_level,
            'details': risks
        }
    
    def create_ai_analysis_dashboard(self, analysis_results):
        """创建AI分析仪表盘"""
        # 创建卡片式布局
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 总体评价
            st.metric("AI评估", analysis_results['summary'].split('，')[0])
            
        with col2:
            # 风险等级
            risk_level = analysis_results['risk_assessment']['level']
            risk_color = {
                '极高': 'red', '高': 'orange', '中': 'yellow', '低': 'green'
            }.get(risk_level, 'gray')
            st.metric("风险等级", risk_level)
            
        with col3:
            # 优势数量
            strengths_count = len(analysis_results['strengths'])
            st.metric("优势点", strengths_count)
            
        with col4:
            # 建议数量
            rec_count = len(analysis_results['recommendations'])
            st.metric("改进建议", rec_count)
        
        # 详细分析
        with st.expander("📊 详细分析报告", expanded=True):
            tab1, tab2, tab3, tab4 = st.tabs(["优势分析", "弱点识别", "改进建议", "风险评估"])
            
            with tab1:
                st.subheader("✅ 系统优势")
                for strength in analysis_results['strengths']:
                    st.success(f"• {strength}")
                    
            with tab2:
                st.subheader("⚠️ 需要改进")
                for weakness in analysis_results['weaknesses']:
                    st.warning(f"• {weakness}")
                    
            with tab3:
                st.subheader("💡 优化建议")
                for recommendation in analysis_results['recommendations']:
                    st.info(f"• {recommendation}")
                    
            with tab4:
                st.subheader("🔴 风险评估")
                risk = analysis_results['risk_assessment']
                st.error(f"风险等级: {risk['level']}")
                for detail in risk['details']:
                    st.write(f"• {detail}")

class AdvancedIntegration:
    """高级集成模块"""
    
    def __init__(self):
        self.multi_target_coordinator = MultiTargetCoordination()
        self.electronic_warfare = AdvancedElectronicWarfare()
        self.effectiveness_evaluator = SystemEffectivenessEvaluator()
        self.distributed_sim = DistributedSimulation()
        self.collaboration_tool = RealTimeCollaboration()
        self.visualization_engine = AdvancedVisualization()
        self.ai_assistant = AIAssistant()
        self.integrated_systems = {}
        
    def initialize_integrated_system(self, battlefield, guidance_system):
        """初始化集成系统"""
        self.integrated_systems = {
            'battlefield': battlefield,
            'guidance_system': guidance_system,
            'multi_target': self.multi_target_coordinator,
            'ew_system': self.electronic_warfare,
            'evaluator': self.effectiveness_evaluator,
            'last_update': datetime.now()
        }
        
        return True
    
    def run_comprehensive_analysis(self, simulation_data):
        """运行综合分析"""
        analyses = {}
        
        # 多目标分析
        if hasattr(self.integrated_systems.get('battlefield'), 'targets'):
            analyses['multi_target'] = self.multi_target_coordinator.plan_attack_sequence(
                self.integrated_systems['battlefield'],
                self.integrated_systems['guidance_system']
            )
        
        # 电子战分析
        analyses['electronic_warfare'] = self.electronic_warfare.analyze_jamming_environment(
            self.integrated_systems['battlefield'],
            self.integrated_systems['guidance_system']
        )
        
        # 系统效能评估
        analyses['effectiveness'] = self.effectiveness_evaluator.calculate_system_effectiveness(
            self.integrated_systems['guidance_system'],
            self.integrated_systems['battlefield']
        )
        
        # AI分析
        analyses['ai_analysis'] = self.ai_assistant.analyze_simulation_results(
            simulation_data
        )
        
        return analyses
    
    def create_comprehensive_dashboard(self, simulation_data, analyses):
        """创建综合仪表盘"""
        # 创建标签页布局
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 综合概览", "🎯 多目标分析", "⚡ 电子对抗", 
            "📊 效能评估", "🤖 AI分析"
        ])
        
        with tab1:
            self._create_overview_tab(simulation_data, analyses)
            
        with tab2:
            self._create_multi_target_tab(analyses.get('multi_target', []))
            
        with tab3:
            self._create_ew_analysis_tab(analyses.get('electronic_warfare', {}))
            
        with tab4:
            self._create_effectiveness_tab(analyses.get('effectiveness', {}))
            
        with tab5:
            self._create_ai_analysis_tab(analyses.get('ai_analysis', {}))
    
    def _create_overview_tab(self, simulation_data, analyses):
        """创建概览标签页"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 性能趋势图
            if hasattr(self.integrated_systems.get('guidance_system'), 'trajectory'):
                fig = self.visualization_engine.create_time_slider_visualization(
                    self.integrated_systems['guidance_system'].trajectory
                )
                st.plotly_chart(fig, width='stretch')
            
            # 3D战场可视化
            fig_3d = self.visualization_engine.create_3d_battlefield(
                self.integrated_systems['battlefield'],
                self.integrated_systems['guidance_system']
            )
            st.plotly_chart(fig_3d, width='stretch')
        
        with col2:
            # 关键指标
            st.subheader("📊 关键性能指标")
            
            performance = simulation_data.get('performance', 0) * 100
            st.metric("当前性能", f"{performance:.1f}%")
            
            distance = simulation_data.get('target_distance', 0)
            st.metric("目标距离", f"{distance:.1f} km")
            
            jamming = simulation_data.get('jamming_power', 0) * 100
            st.metric("干扰强度", f"{jamming:.1f}%")
            
            # 系统状态
            st.subheader("🛡️ 系统状态")
            system = self.integrated_systems['guidance_system']
            st.metric("探测距离", f"{system.detection_range} km")
            st.metric("抗干扰能力", f"{system.jamming_resistance * 100:.1f}%")
            st.metric("隐蔽性", f"{system.stealth_level * 100:.1f}%")
    
    def _create_multi_target_tab(self, attack_plan):
        """创建多目标分析标签页"""
        if attack_plan:
            # 攻击优先级图表
            fig = self.multi_target_coordinator.create_attack_plan_chart(attack_plan)
            st.plotly_chart(fig, width='stretch')
            
            # 攻击序列表格
            st.subheader("🎯 攻击序列规划")
            df = pd.DataFrame(attack_plan)
            st.dataframe(df, width='stretch')
            
            # 战术建议
            st.subheader("💡 多目标攻击战术建议")
            if len(attack_plan) > 1:
                st.info("""
                **多目标攻击策略建议:**
                - 优先攻击高优先级目标（预警机、雷达站）
                - 采用时间差攻击策略，避免同时暴露
                - 利用地形掩护接近次要目标
                - 考虑使用诱饵吸引敌方防御火力
                """)
        else:
            st.info("暂无多目标分析数据")
    
    def _create_ew_analysis_tab(self, ew_analysis):
        """创建电子对抗分析标签页"""
        if ew_analysis:
            # 威胁等级显示
            col1, col2, col3 = st.columns(3)
            
            with col1:
                threat_level = ew_analysis.get('threat_level', '低')
                threat_color = {
                    '极高': 'red', '高': 'orange', '中': 'yellow', '低': 'green'
                }.get(threat_level, 'gray')
                
                st.metric("电磁威胁等级", threat_level)
                
            with col2:
                jamming_power = ew_analysis.get('jamming_power', 0) * 100
                st.metric("综合干扰强度", f"{jamming_power:.1f}%")
                
            with col3:
                jammer_count = ew_analysis.get('total_jammers', 0)
                st.metric("干扰源数量", jammer_count)
            
            # 电子战分析图表
            fig = self.electronic_warfare.create_ew_analysis_dashboard(
                self.integrated_systems['battlefield'],
                self.integrated_systems['guidance_system']
            )
            st.plotly_chart(fig, width='stretch')
            
            # 对抗措施建议
            st.subheader("🛡️ 电子对抗措施建议")
            recommended_measures = ew_analysis.get('recommended_ecm', [])
            if recommended_measures:
                for measure in set(recommended_measures):  # 去重
                    measure_info = self.electronic_warfare.ecm_techniques.get(measure, {})
                    st.success(f"• {measure_info.get('description', measure)}")
            else:
                st.info("当前电磁环境较为简单，无需特殊对抗措施")
        else:
            st.info("暂无电子对抗分析数据")
    
    def _create_effectiveness_tab(self, effectiveness_data):
        """创建效能评估标签页"""
        if effectiveness_data:
            # 雷达图
            fig = self.effectiveness_evaluator.create_effectiveness_radar(effectiveness_data)
            st.plotly_chart(fig, width='stretch')
            
            # 详细指标
            st.subheader("📈 详细效能指标")
            metrics = effectiveness_data.get('metrics', {})
            weights = effectiveness_data.get('weights', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                for metric, value in list(metrics.items())[:3]:
                    weight = weights.get(metric, 0) * 100
                    score = value * 100
                    st.metric(
                        f"{metric} (权重:{weight:.1f}%)",
                        f"{score:.1f}%"
                    )
                    
            with col2:
                for metric, value in list(metrics.items())[3:]:
                    weight = weights.get(metric, 0) * 100
                    score = value * 100
                    st.metric(
                        f"{metric} (权重:{weight:.1f}%)",
                        f"{score:.1f}%"
                    )
            
            # 总体效能
            overall = effectiveness_data.get('overall_effectiveness', 0)
            mission_type = effectiveness_data.get('mission_type', '通用')
            
            st.subheader("🎯 总体效能评估")
            st.metric(
                f"{mission_type}任务效能",
                f"{overall:.1f}%"
            )
        else:
            st.info("暂无效能评估数据")
    
    def _create_ai_analysis_tab(self, ai_analysis):
        """创建AI分析标签页"""
        if ai_analysis:
            self.ai_assistant.create_ai_analysis_dashboard(ai_analysis)
        else:
            st.info("暂无AI分析数据")

class ExportManager:
    """导出管理器"""
    
    def __init__(self):
        self.export_formats = ['excel', 'json', 'csv', 'html', 'pdf']
        self.export_templates = {}
        
    def export_comprehensive_report(self, simulation_data, analyses, file_format='excel'):
        """导出综合报告"""
        if file_format == 'excel':
            return self._export_to_excel(simulation_data, analyses)
        elif file_format == 'json':
            return self._export_to_json(simulation_data, analyses)
        elif file_format == 'html':
            return self._export_to_html(simulation_data, analyses)
        elif file_format == 'pdf':
            return self._export_to_pdf(simulation_data, analyses)
        else:
            return self._export_to_csv(simulation_data, analyses)
    
    def _export_to_excel(self, simulation_data, analyses):
        """导出到Excel"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
                    # 仿真数据表
                    sim_df = self._prepare_simulation_data(simulation_data)
                    sim_df.to_excel(writer, sheet_name='仿真数据', index=False)
                    
                    # 多目标分析表
                    if 'multi_target' in analyses:
                        mt_df = pd.DataFrame(analyses['multi_target'])
                        mt_df.to_excel(writer, sheet_name='多目标分析', index=False)
                    
                    # 效能评估表
                    if 'effectiveness' in analyses:
                        eff_data = analyses['effectiveness']
                        eff_df = pd.DataFrame([{
                            '指标': key,
                            '得分': value * 100,
                            '权重': eff_data['weights'].get(key, 0) * 100
                        } for key, value in eff_data['metrics'].items()])
                        eff_df.to_excel(writer, sheet_name='效能评估', index=False)
                    
                    # AI分析表
                    if 'ai_analysis' in analyses:
                        ai_data = analyses['ai_analysis']
                        ai_rows = []
                        for category, items in ai_data.items():
                            if isinstance(items, list):
                                for item in items:
                                    ai_rows.append({'类别': category, '内容': item})
                            elif isinstance(items, dict):
                                for key, value in items.items():
                                    ai_rows.append({'类别': f"{category}_{key}", '内容': str(value)})
                            else:
                                ai_rows.append({'类别': category, '内容': str(items)})
                        
                        ai_df = pd.DataFrame(ai_rows)
                        ai_df.to_excel(writer, sheet_name='AI分析', index=False)
                
                return tmp.name
                
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return None
    
    def _export_to_json(self, simulation_data, analyses):
        """导出到JSON"""
        try:
            export_data = {
                'simulation_data': simulation_data,
                'analyses': analyses,
                'export_time': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
                json.dump(export_data, tmp, indent=2, ensure_ascii=False)
                return tmp.name
                
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return None
    
    def _export_to_html(self, simulation_data, analyses):
        """导出到HTML报告"""
        try:
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>导引头仿真分析报告</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }
                    .section { margin: 30px 0; }
                    .metric { display: inline-block; margin: 10px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
                    .positive { color: green; }
                    .warning { color: orange; }
                    .danger { color: red; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>导引头电子战仿真分析报告</h1>
                    <p>生成时间: {timestamp}</p>
                </div>
                
                {content}
            </body>
            </html>
            """
            
            # 生成报告内容
            content_sections = []
            
            # 总体性能
            performance = simulation_data.get('performance', 0) * 100
            performance_class = "positive" if performance > 70 else "warning" if performance > 50 else "danger"
            
            content_sections.append(f"""
            <div class="section">
                <h2>总体性能</h2>
                <div class="metric {performance_class}">
                    <h3>综合性能评分</h3>
                    <p style="font-size: 24px; font-weight: bold;">{performance:.1f}%</p>
                </div>
            </div>
            """)
            
            # AI分析摘要
            if 'ai_analysis' in analyses:
                ai_data = analyses['ai_analysis']
                content_sections.append(f"""
                <div class="section">
                    <h2>AI分析摘要</h2>
                    <p><strong>总体评价:</strong> {ai_data.get('summary', '无')}</p>
                    <p><strong>风险等级:</strong> {ai_data.get('risk_assessment', {}).get('level', '未知')}</p>
                </div>
                """)
            
            # 组合完整HTML
            html_content = html_template.format(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                content='\n'.join(content_sections)
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
                tmp.write(html_content.encode('utf-8'))
                return tmp.name
                
        except Exception as e:
            print(f"导出HTML失败: {e}")
            return None
    
    def _export_to_pdf(self, simulation_data, analyses):
        """导出到PDF（简化实现）"""
        # 实际应用中可以使用reportlab等库生成PDF
        # 这里简化为返回HTML文件路径
        return self._export_to_html(simulation_data, analyses)
    
    def _export_to_csv(self, simulation_data, analyses):
        """导出到CSV"""
        try:
            # 主要导出仿真数据
            df = self._prepare_simulation_data(simulation_data)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                df.to_csv(tmp.name, index=False, encoding='utf-8')
                return tmp.name
                
        except Exception as e:
            print(f"导出CSV失败: {e}")
            return None
    
    def _prepare_simulation_data(self, simulation_data):
        """准备仿真数据"""
        data_dict = {
            'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'performance': [simulation_data.get('performance', 0) * 100],
            'target_distance': [simulation_data.get('target_distance', 0)],
            'jamming_power': [simulation_data.get('jamming_power', 0) * 100],
            'terrain_factor': [simulation_data.get('terrain_factor', 0) * 100],
            'weather_factor': [simulation_data.get('weather_factor', 0) * 100]
        }
        
        return pd.DataFrame(data_dict)

# 测试函数
def test_advanced_features():
    """测试高级功能模块"""
    print("测试高级功能模块...")
    
    # 测试多目标协同
    mt_coordinator = MultiTargetCoordination()
    print("多目标协同模块初始化成功")
    
    # 测试电子对抗
    ew_system = AdvancedElectronicWarfare()
    print("电子对抗模块初始化成功")
    
    # 测试效能评估
    evaluator = SystemEffectivenessEvaluator()
    print("效能评估模块初始化成功")
    
    # 测试AI助手
    ai_assistant = AIAssistant()
    print("AI分析模块初始化成功")
    
    # 测试集成系统
    integration = AdvancedIntegration()
    print("高级集成模块初始化成功")
    
    print("所有高级功能模块测试完成")

if __name__ == "__main__":
    test_advanced_features()