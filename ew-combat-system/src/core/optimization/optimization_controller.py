# 文件: src/core/optimization/optimization_controller.py
"""
优化控制器
集成ePDE算法和对抗分析，提供完整的优化解决方案
"""

import time
import numpy as np
from typing import Dict, Any, Tuple
from .epde_algorithm import EPDEOptimizer
from .result_analyzer import OptimizationResultAnalyzer
from ..analysis.combat_analyzer import CombatAnalyzer

class OptimizationController:
    """优化控制器"""
    
    def __init__(self, consider_illumination: bool = True, time_limit: float = 1.0):
        """
        初始化优化控制器
        
        参数:
            consider_illumination: 是否考虑平台照明
            time_limit: 优化时间限制
        """
        self.combat_analyzer = CombatAnalyzer(consider_illumination)
        self.optimizer = EPDEOptimizer(time_limit=time_limit)
        self.result_analyzer = OptimizationResultAnalyzer()
        self.optimization_history = []
    
    def run_optimization(self, scenario) -> Dict[str, Any]:
        """
        运行完整优化流程
        
        参数:
            scenario: 仿真场景
            
        返回:
            优化结果
        """
        start_time = time.time()
        
        print("开始COTEJA优化流程...")
        print(f"场景: {len(scenario['radars'])}部雷达 vs {len(scenario['jammers'])}个干扰机")
        
        # 1. 运行ePDE优化
        best_solution, best_fitness, convergence_data = self.optimizer.optimize( # type: ignore
            scenario, self.combat_analyzer
        )
        
        # 2. 分析优化结果
        convergence_analysis = self.result_analyzer.analyze_convergence(convergence_data)
        assignment_report = self.result_analyzer.generate_assignment_report(
            best_solution, scenario, self.combat_analyzer
        )
        
        # 3. 记录优化历史
        optimization_record = {
            'timestamp': time.time(),
            'best_solution': best_solution,
            'best_fitness': best_fitness,
            'convergence_data': convergence_data,
            'convergence_analysis': convergence_analysis,
            'assignment_report': assignment_report,
            'scenario_info': {
                'n_radars': len(scenario['radars']),
                'n_jammers': len(scenario['jammers'])
            }
        }
        
        self.optimization_history.append(optimization_record)
        
        total_time = time.time() - start_time
        
        # 4. 生成最终结果
        result = {
            'success': True,
            'optimization_time': total_time,
            'best_solution': best_solution,
            'best_fitness': best_fitness,
            'convergence_analysis': convergence_analysis,
            'assignment_report': assignment_report,
            'convergence_data': convergence_data,
            'resource_utilization': assignment_report['summary']['resource_utilization']
        }
        
        print(f"优化完成! 总时间: {total_time:.3f}s")
        print(f"最优适应度: {best_fitness:.3f}")
        print(f"资源利用率: {result['resource_utilization']:.1%}")
        
        return result
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        if not self.optimization_history:
            return {}
        
        recent_runs = self.optimization_history[-10:]  # 最近10次运行
        
        fitness_values = [run['best_fitness'] for run in recent_runs]
        times = [run['optimization_time'] for run in recent_runs if 'optimization_time' in run]
        
        stats = {
            'total_runs': len(self.optimization_history),
            'avg_fitness': np.mean(fitness_values) if fitness_values else 0.0,
            'std_fitness': np.std(fitness_values) if fitness_values else 0.0,
            'max_fitness': max(fitness_values) if fitness_values else 0.0,
            'avg_time': np.mean(times) if times else 0.0,
            'success_rate': len([r for r in recent_runs if r.get('success', False)]) / len(recent_runs) 
                           if recent_runs else 0.0
        }
        
        return stats