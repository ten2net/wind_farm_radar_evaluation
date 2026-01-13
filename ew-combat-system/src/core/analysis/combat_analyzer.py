# 文件: src/core/analysis/combat_analyzer.py
import traceback
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .combat_tables import CombatAnalysisTables

class CombatAnalyzer:
    """
    核心对抗分析器
    实现文章中的干扰机-雷达对抗分析逻辑
    """
    
    def __init__(self, consider_illumination: bool = True):
        """
        初始化对抗分析器
        
        参数:
            consider_illumination: 是否考虑平台照明效应
        """
        self.tables = CombatAnalysisTables(consider_illumination)
        self.consider_illumination = consider_illumination
    
    def calculate_jamming_effectiveness(self, radar, jammer, jamming_technique: str, 
                                      bw_type: str = 'M', assigned_targets: int = 1) -> float:
        """
        计算单个干扰机对单个雷达的干扰效果
        
        参数:
            radar: 雷达对象
            jammer: 干扰机对象
            jamming_technique: 干扰技术
            bw_type: 带宽类型 (N, M, W)
            assigned_targets: 分配的目标数量
            
        返回:
            总干扰效果因子
        """
        try:
            # 1. 基础阶段有效性
            base_effectiveness = self.tables.get_stage_effectiveness(
                radar.current_stage, jamming_technique
            )
            
            # 2. 带宽调整
            bw_adjustment = self.tables.get_bw_adjustment(bw_type, assigned_targets)
            if bw_adjustment is None:
                return 0.0  # 无效分配
            
            # 3. 距离衰减因子（简化模型）
            distance_effect = self._calculate_distance_effect(radar, jammer)
            
            # 4. 功率匹配因子
            power_match = self._calculate_power_match(radar, jammer)
            
            # 计算总效果
            total_effect = (base_effectiveness + bw_adjustment) * distance_effect * power_match
            
            # 限制在合理范围
            return max(-1.0, min(1.0, total_effect))
            
        except Exception as e:
            print(f"计算干扰效果错误: {e}")
            return 0.0
    
    def calculate_cooperative_effect(self, radar, jamming_assignments: List[Dict], 
                                   jammers: List) -> float:
        """
        计算协同干扰效果（多干扰机对单雷达）
        
        参数:
            radar: 目标雷达
            jamming_assignments: 干扰分配列表
            jammers: 干扰机列表
            
        返回:
            协同干扰效果因子
        """
        try:
            total_effect = 0.0
            active_techniques = []
            
            # 收集针对该雷达的干扰技术
            for assignment in jamming_assignments:
                if assignment['target_id'] == radar.id:
                    jammer = next((j for j in jammers if j['id'] == assignment['jammer_id']), None)
                    if jammer:
                        technique = assignment['technique']
                        bw_type = assignment.get('bw_type', 'M')
                        
                        # 计算单个干扰效果
                        individual_effect = self.calculate_jamming_effectiveness(
                            radar, jammer, technique, bw_type, len(jamming_assignments)
                        )
                        
                        # 考虑技术交互
                        interaction_effect = 0.0
                        for other_tech in active_techniques:
                            interaction = self.tables.get_tech_interaction(technique, other_tech)
                            interaction_effect += interaction
                        
                        total_effect += individual_effect + interaction_effect
                        active_techniques.append(technique)
            
            return max(-1.0, min(1.0, total_effect))
            
        except Exception as e:
            exec_str = traceback.format_exc()
            print(f"计算协同干扰效果错误: {exec_str}")
            return 0.0
    
    def evaluate_assignment_effectiveness(self, assignment_matrix: Dict, 
                                        radars: List, jammers: List) -> Dict[str, Any]:
        """
        评估分配矩阵的整体效果
        
        参数:
            assignment_matrix: 分配矩阵 {jammer_id: {target_id, technique, bw_type}}
            radars: 雷达列表
            jammers: 干扰机列表
            
        返回:
            评估结果字典
        """
        results = {
            'total_effectiveness': 0.0,
            'radar_effects': {},
            'resource_utilization': 0.0,
            'interruption_count': 0
        }
        
        # 转换分配矩阵格式
        jamming_assignments = []
        for jammer_id, assignment in assignment_matrix.items():
            if assignment:  # 非空分配
                jamming_assignments.append({
                    'jammer_id': jammer_id,
                    'target_id': assignment['target_id'],
                    'technique': assignment['technique'],
                    'bw_type': assignment.get('bw_type', 'M')
                })
        
        # 计算每个雷达的效果
        for radar in radars:
            radar_effect = self.calculate_cooperative_effect(radar, jamming_assignments, jammers)
            results['radar_effects'][radar.id] = radar_effect
            results['total_effectiveness'] += radar_effect
            
            # 检查是否会发生中断
            if radar_effect > (1.0 - radar.interruption_threshold):
                results['interruption_count'] += 1
        
        # 计算资源利用率
        used_jammers = len([a for a in jamming_assignments if a['target_id']])
        results['resource_utilization'] = used_jammers / len(jammers) if jammers else 0.0
        
        return results
    
    def _calculate_distance_effect(self, radar, jammer) -> float:
        """计算距离衰减效应"""
        try:
            # 简化的距离衰减模型
            distance = self._calculate_distance(radar.position, jammer.position)
            # 假设有效干扰距离为50km
            max_effective_distance = 50000  # 50km
            if distance > max_effective_distance:
                return 0.1  # 远距离衰减
            else:
                return 1.0 - (distance / max_effective_distance) * 0.8
        except:
            return 0.5  # 默认值
    
    def _calculate_power_match(self, radar, jammer) -> float:
        """计算功率匹配效应"""
        try:
            # 简化的功率匹配模型
            power_ratio = jammer.power / (radar.power + 1e-6)  # 避免除零
            return min(1.0, power_ratio / 10.0)  # 归一化
        except:
            return 0.5  # 默认值
    
    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """计算两点间距离（简化球面距离）"""
        try:
            # 使用哈弗辛公式计算大圆距离
            from math import radians, sin, cos, sqrt, asin
            
            lat1, lon1 = radians(pos1['lat']), radians(pos1['lon'])
            lat2, lon2 = radians(pos2['lat']), radians(pos2['lon'])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            
            # 地球半径（米）
            r = 6371000
            return c * r
        except:
            return 100000  # 默认距离