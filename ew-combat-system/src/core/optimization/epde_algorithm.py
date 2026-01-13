# 文件: src/core/optimization/epde_algorithm.py
"""
扩展置换差分进化算法 (ePDE)
基于文章第4节描述的优化算法实现
"""

import numpy as np
import time
from typing import List, Dict, Any, Tuple, Optional
import random
from ..analysis.combat_analyzer import CombatAnalyzer
from ..entities.radar_enhanced import EnhancedRadar

class EPDEOptimizer:
    """
    扩展置换差分进化算法
    用于解决干扰资源分配的组合优化问题
    基于文章中的ePDE算法实现
    """
    
    def __init__(self, population_size: int = 50, max_generations: int = 100, 
                 crossover_rate: float = 0.9, scaling_factor: float = 0.5,
                 time_limit: float = 1.0):
        """
        初始化ePDE优化器
        
        参数:
            population_size: 种群大小
            max_generations: 最大迭代次数
            crossover_rate: 交叉概率
            scaling_factor: 缩放因子
            time_limit: 时间限制(秒)
        """
        self.population_size = population_size
        self.max_generations = max_generations
        self.cr = crossover_rate
        self.f = scaling_factor
        self.time_limit = time_limit
        
        # 干扰技术选项
        self.jamming_techniques = ['NJ', 'CP', 'MFT', 'RGPO', 'VGPO']
        self.bandwidth_types = ['N', 'M', 'W']
        
    def optimize(self, scenario, combat_analyzer: CombatAnalyzer) -> Tuple[Dict, float]:
        """
        主优化函数 - 在1秒内找到最优干扰分配
        
        参数:
            scenario: 仿真场景
            combat_analyzer: 对抗分析器
            
        返回:
            Tuple[最优分配, 最优适应度]
        """
        start_time = time.time()
        
        # 初始化种群
        population = self._initialize_population(scenario)
        best_solution = None
        best_fitness = float('-inf')
        convergence_data = []
        
        print(f"开始ePDE优化: 种群大小={self.population_size}, 时间限制={self.time_limit}s")
        
        for generation in range(self.max_generations):
            # 检查时间限制
            if time.time() - start_time > self.time_limit:
                print(f"时间限制到达，停止优化。当前代数: {generation}")
                break
            
            new_population = []
            generation_fitness = []
            
            for i, individual in enumerate(population):
                # 1. 变异操作
                mutant = self._mutation(population, i)
                
                # 2. 交叉操作
                trial = self._crossover(individual, mutant)
                
                # 3. 修复无效解
                trial = self._repair_solution(trial, scenario)
                
                # 4. 评估适应度
                individual_fitness = self._evaluate_fitness(individual, scenario, combat_analyzer)
                trial_fitness = self._evaluate_fitness(trial, scenario, combat_analyzer)
                
                generation_fitness.append(individual_fitness)
                
                # 5. 选择操作
                if trial_fitness > individual_fitness:
                    new_population.append(trial)
                    if trial_fitness > best_fitness:
                        best_fitness = trial_fitness
                        best_solution = trial.copy()
                else:
                    new_population.append(individual)
                    if individual_fitness > best_fitness:
                        best_fitness = individual_fitness
                        best_solution = individual.copy()
            
            population = new_population
            
            # 记录收敛数据
            avg_fitness = np.mean(generation_fitness)
            max_fitness = np.max(generation_fitness)
            convergence_data.append({
                'generation': generation,
                'avg_fitness': avg_fitness,
                'max_fitness': max_fitness,
                'best_fitness': best_fitness
            })
            
            if generation % 10 == 0:
                print(f"代数 {generation}: 平均适应度={avg_fitness:.3f}, 最优适应度={best_fitness:.3f}")
        
        optimization_time = time.time() - start_time
        print(f"优化完成! 时间: {optimization_time:.3f}s, 最优适应度: {best_fitness:.3f}")
        
        return best_solution, best_fitness, convergence_data
    
    def _initialize_population(self, scenario) -> List[Dict]:
        """
        初始化种群 - 随机生成干扰分配方案
        
        参数:
            scenario: 仿真场景
            
        返回:
            种群列表
        """
        population = []
        n_jammers = len(scenario['jammers'])
        n_radars = len(scenario['radars'])

        for _ in range(self.population_size):
            individual = {}
            
            for jammer in scenario['jammers']:
                # 随机分配干扰技术和目标
                if n_radars > 0:
                    # 随机选择目标雷达
                    target_radar = random.choice(scenario['radars'])
                    
                    # 随机选择干扰技术
        
        for _ in range(self.population_size):
            individual = {}
            
            for jammer in scenario['jammers']:
                # 随机分配干扰技术和目标
                if n_radars > 0:
                    # 随机选择目标雷达
                    target_radar = random.choice(scenario['radars'])
                    
                    # 随机选择干扰技术
                    technique = random.choice(self.jamming_techniques)
                    
                    # 随机选择带宽类型
                    bw_type = random.choice(self.bandwidth_types)
                    
                    individual[jammer['id']] = {
                        'target_id': target_radar.id,
                        'technique': technique,
                        'bw_type': bw_type,
                        'jammer_power': jammer['power']
                    }
                else:
                    # 无雷达目标，设置空分配
                    individual[jammer.id] = {
                        'target_id': None,
                        'technique': None,
                        'bw_type': None,
                        'jammer_power': jammer['power']
                    }
            
            population.append(individual)
        
        return population
    
    def _mutation(self, population: List[Dict], current_idx: int) -> Dict:
        """
        变异操作 - 基于差分进化的变异策略
        
        参数:
            population: 当前种群
            current_idx: 当前个体索引
            
        返回:
            变异后的个体
        """
        # 选择三个不同的个体
        indices = [i for i in range(len(population)) if i != current_idx]
        a, b, c = random.sample(indices, 3)
        
        individual_a = population[a]
        individual_b = population[b]
        individual_c = population[c]
        
        mutant = {}
        
        # 对每个干扰机进行变异
        for jammer_id in individual_a.keys():
            if random.random() < 0.8:  # 变异概率
                # 差分变异: mutant = a + F * (b - c)
                # 这里采用离散版本的差分变异
                if random.random() < 0.5:
                    # 从个体a继承
                    mutant[jammer_id] = individual_a[jammer_id].copy()
                else:
                    # 随机扰动
                    if individual_b[jammer_id]['target_id'] and individual_c[jammer_id]['target_id']:
                        # 有意义的差分操作
                        if random.random() < self.f:
                            mutant[jammer_id] = individual_b[jammer_id].copy()
                        else:
                            mutant[jammer_id] = individual_c[jammer_id].copy()
                    else:
                        mutant[jammer_id] = individual_a[jammer_id].copy()
            else:
                # 保持原样
                mutant[jammer_id] = individual_a[jammer_id].copy()
        
        return mutant
    
    def _crossover(self, target: Dict, mutant: Dict) -> Dict:
        """
        交叉操作 - 生成试验个体
        
        参数:
            target: 目标个体
            mutant: 变异个体
            
        返回:
            交叉后的试验个体
        """
        trial = {}
        
        for jammer_id in target.keys():
            if random.random() < self.cr or jammer_id not in trial:
                # 从变异个体继承
                trial[jammer_id] = mutant.get(jammer_id, target[jammer_id]).copy()
            else:
                # 从目标个体继承
                trial[jammer_id] = target[jammer_id].copy()
        
        return trial
    
    def _repair_solution(self, individual: Dict, scenario) -> Dict:
        """
        修复无效解 - 确保分配方案满足约束条件
        
        参数:
            individual: 需要修复的个体
            scenario: 仿真场景
            
        返回:
            修复后的个体
        """
        repaired = individual.copy()
        n_radars = len(scenario['radars'])
        
        # 统计每个雷达被分配的次数
        radar_assignments = {}
        for radar in scenario['radars']:
            radar_assignments[radar.id] = 0
        
        # 修复无效目标分配
        for jammer_id, assignment in repaired.items():
            if assignment['target_id']:
                # 检查目标是否存在
                target_exists = any(radar.id == assignment['target_id'] for radar in scenario['radars'])
                if not target_exists and n_radars > 0:
                    # 分配无效，随机分配一个有效目标
                    new_target = random.choice(scenario['radars'])
                    assignment['target_id'] = new_target.id
                
                # 统计分配
                if assignment['target_id'] in radar_assignments:
                    radar_assignments[assignment['target_id']] += 1
        
        # 检查带宽约束（基于文章表3）
        for jammer_id, assignment in repaired.items():
            if assignment['target_id'] and assignment['bw_type']:
                assigned_targets = radar_assignments[assignment['target_id']]
                bw_type = assignment['bw_type']
                
                # 检查是否超过带宽支持的最大目标数
                max_targets = self._get_max_targets_by_bw(bw_type)
                if assigned_targets > max_targets:
                    # 超过限制，需要重新分配
                    if n_radars > 1:
                        # 选择分配较少的雷达
                        available_radars = [r for r in scenario['radars'] 
                                          if radar_assignments[r.id] < self._get_max_targets_by_bw(bw_type)]
                        if available_radars:
                            new_target = min(available_radars, 
                                          key=lambda r: radar_assignments[r.id])
                            assignment['target_id'] = new_target.id
                            radar_assignments[new_target.id] += 1
        
        return repaired
    
    def _get_max_targets_by_bw(self, bw_type: str) -> int:
        """
        获取带宽类型支持的最大目标数（基于文章表3）
        
        参数:
            bw_type: 带宽类型
            
        返回:
            最大目标数
        """
        max_targets = {
            'N': 1,  # 窄带支持1个目标
            'M': 3,  # 中带支持3个目标
            'W': 5   # 宽带支持5个目标
        }
        return max_targets.get(bw_type, 1)
    
    def _evaluate_fitness(self, individual: Dict, scenario, combat_analyzer: CombatAnalyzer) -> float:
        """
        评估个体适应度 - 基于干扰效果和资源利用率
        
        参数:
            individual: 干扰分配个体
            scenario: 仿真场景
            combat_analyzer: 对抗分析器
            
        返回:
            适应度值
        """
        try:
            # 转换分配格式
            assignment_matrix = individual
            
            # 使用对抗分析器评估效果
            evaluation = combat_analyzer.evaluate_assignment_effectiveness(
                assignment_matrix, scenario['radars'], scenario['jammers']
            )
            
            # 基础适应度 = 总干扰效果
            base_fitness = evaluation['total_effectiveness']
            
            # 考虑资源利用率（RUR）
            rur = evaluation['resource_utilization']
            rur_bonus = rur * 0.5  # 资源利用率奖励
            
            # 考虑中断次数奖励
            interruption_bonus = evaluation['interruption_count'] * 0.3
            
            # 总适应度
            total_fitness = base_fitness + rur_bonus + interruption_bonus
            
            # 添加约束惩罚
            penalty = self._calculate_constraint_penalty(individual, scenario)
            total_fitness -= penalty
            
            return max(0.0, total_fitness)  # 确保非负
            
        except Exception as e:
            print(f"适应度评估错误: {e}")
            return 0.0
    
    def _calculate_constraint_penalty(self, individual: Dict, scenario) -> float:
        """
        计算约束违反惩罚
        
        参数:
            individual: 干扰分配个体
            scenario: 仿真场景
            
        返回:
            惩罚值
        """
        penalty = 0.0
        
        # 检查每个干扰机的分配
        for jammer_id, assignment in individual.items():
            if assignment['target_id']:
                # 检查目标是否存在
                target_exists = any(radar.id == assignment['target_id'] for radar in scenario['radars'])
                if not target_exists:
                    penalty += 1.0
                
                # 检查带宽约束
                if assignment['bw_type']:
                    # 统计该雷达被分配的次数
                    assigned_count = sum(1 for assign in individual.values() 
                                       if assign['target_id'] == assignment['target_id'])
                    
                    max_allowed = self._get_max_targets_by_bw(assignment['bw_type'])
                    if assigned_count > max_allowed:
                        penalty += (assigned_count - max_allowed) * 0.5
        
        return penalty