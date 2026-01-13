# 文件: src/core/optimization/result_analyzer.py
"""
优化结果分析器
用于分析和可视化优化过程结果
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List
import pandas as pd

class OptimizationResultAnalyzer:
    """优化结果分析器"""
    
    def __init__(self):
        self.convergence_data = []
    
    def analyze_convergence(self, convergence_data: List[Dict]) -> Dict[str, Any]:
        """
        分析收敛性
        
        参数:
            convergence_data: 收敛数据
            
        返回:
            收敛分析结果
        """
        if not convergence_data:
            return {}
        
        generations = [data['generation'] for data in convergence_data]
        avg_fitness = [data['avg_fitness'] for data in convergence_data]
        max_fitness = [data['max_fitness'] for data in convergence_data]
        best_fitness = [data['best_fitness'] for data in convergence_data]
        
        analysis = {
            'final_best_fitness': best_fitness[-1] if best_fitness else 0.0,
            'final_avg_fitness': avg_fitness[-1] if avg_fitness else 0.0,
            'convergence_generation': self._find_convergence_generation(best_fitness),
            'improvement_ratio': (best_fitness[-1] - best_fitness[0]) / (best_fitness[0] + 1e-6) 
                               if best_fitness and best_fitness[0] > 0 else 0.0,
            'stability': self._calculate_stability(best_fitness)
        }
        
        return analysis
    
    def _find_convergence_generation(self, best_fitness: List[float]) -> int:
        """找到收敛代数"""
        if len(best_fitness) < 10:
            return len(best_fitness) - 1
        
        # 检查最后10代是否稳定
        last_10 = best_fitness[-10:]
        std_dev = np.std(last_10)
        
        if std_dev < 0.01:  # 标准差小于0.01认为收敛
            return len(best_fitness) - 10
        
        return len(best_fitness) - 1
    
    def _calculate_stability(self, best_fitness: List[float]) -> float:
        """计算收敛稳定性"""
        if len(best_fitness) < 5:
            return 1.0
        
        last_half = best_fitness[len(best_fitness)//2:]
        return 1.0 - (np.std(last_half) / (np.mean(last_half) + 1e-6)) # type: ignore
    
    def plot_convergence(self, convergence_data: List[Dict], save_path: str = None): # type: ignore
        """
        绘制收敛曲线
        
        参数:
            convergence_data: 收敛数据
            save_path: 保存路径
        """
        if not convergence_data:
            return
        
        generations = [data['generation'] for data in convergence_data]
        avg_fitness = [data['avg_fitness'] for data in convergence_data]
        max_fitness = [data['max_fitness'] for data in convergence_data]
        best_fitness = [data['best_fitness'] for data in convergence_data]
        
        plt.figure(figsize=(12, 8))
        
        plt.plot(generations, avg_fitness, 'b-', label='平均适应度', linewidth=2, alpha=0.7)
        plt.plot(generations, max_fitness, 'g-', label='当代最优', linewidth=2, alpha=0.7)
        plt.plot(generations, best_fitness, 'r-', label='全局最优', linewidth=3)
        
        plt.xlabel('代数')
        plt.ylabel('适应度')
        plt.title('ePDE算法收敛曲线')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"收敛曲线已保存: {save_path}")
        
        plt.show()
    
    def generate_assignment_report(self, best_solution: Dict, scenario, 
                                 combat_analyzer) -> Dict[str, Any]:
        """
        生成分配报告
        
        参数:
            best_solution: 最优解
            scenario: 场景
            combat_analyzer: 对抗分析器
            
        返回:
            分配报告
        """
        # 评估分配效果
        evaluation = combat_analyzer.evaluate_assignment_effectiveness(
            best_solution, scenario['radars'], scenario['jammers']
        )
        
        # 生成详细分配信息
        assignment_details = []
        for jammer_id, assignment in best_solution.items():
            if assignment['target_id']:
                jammer = next((j for j in scenario['jammers'] if j['id'] == jammer_id), None)
                target_radar = next((r for r in scenario['radars'] if r.id == assignment['target_id']), None)
                
                if jammer and target_radar:
                    # 计算单个干扰效果
                    effectiveness = combat_analyzer.calculate_jamming_effectiveness(
                        target_radar, jammer, assignment['technique'], 
                        assignment['bw_type'], 1
                    )
                    
                    assignment_details.append({
                        'jammer_id': jammer_id,
                        'jammer_name': jammer['name'],
                        'target_id': assignment['target_id'],
                        'target_name': target_radar.name,
                        'technique': assignment['technique'],
                        'bw_type': assignment['bw_type'],
                        'effectiveness': effectiveness,
                        'radar_stage': target_radar.current_stage
                    })
        
        report = {
            'summary': {
                'total_effectiveness': evaluation['total_effectiveness'],
                'resource_utilization': evaluation['resource_utilization'],
                'interruption_count': evaluation['interruption_count'],
                'assigned_jammers': len([a for a in best_solution.values() if a['target_id']]),
                'total_jammers': len(scenario['jammers'])
            },
            'assignments': assignment_details,
            'radar_effects': evaluation['radar_effects']
        }
        
        return report