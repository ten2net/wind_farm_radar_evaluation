"""
策略模式：不同的对抗想定
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np
from ..entities import Radar, Jammer, Target

class CombatScenario(ABC):
    """对抗想定基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.radars: List[Radar] = []
        self.jammers: List[Jammer] = []
        self.targets: List[Target] = []
        
    @abstractmethod
    def setup(self, config: Dict[str, Any]):
        """设置想定"""
        pass
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """执行对抗仿真"""
        pass
    
    @abstractmethod
    def assess(self) -> Dict[str, Any]:
        """评估对抗结果"""
        pass

class OneVsOneScenario(CombatScenario):
    """一对一对抗想定"""
    
    def __init__(self):
        super().__init__("一对一对抗", "单雷达 vs 单干扰机对抗")
        
    def setup(self, config: Dict[str, Any]):
        """设置一对一对抗"""
        from ..factory import EntityFactory
        
        # 创建雷达
        radar_config = config.get("radar", {})
        self.radars = [EntityFactory.create_radar(radar_config)]
        
        # 创建干扰机
        jammer_config = config.get("jammer", {})
        self.jammers = [EntityFactory.create_jammer(jammer_config)]
        
        # 创建目标（可选）
        if "targets" in config:
            for target_config in config["targets"]:
                self.targets.append(EntityFactory.create_target(target_config))
    
    def execute(self) -> Dict[str, Any]:
        """执行一对一对抗"""
        if not self.radars or not self.jammers:
            return {"error": "未设置雷达或干扰机"}
        
        radar = self.radars[0]
        jammer = self.jammers[0]
        
        # 计算干扰效果
        from ..simulation import EWSimulator
        result = EWSimulator.calculate_jamming_effect(
            radar, jammer, self.targets
        )
        
        return {
            "scenario": self.name,
            "radar": radar.to_dict(),
            "jammer": jammer.to_dict(),
            "result": result
        }
    
    def assess(self) -> Dict[str, Any]:
        """评估一对一对抗结果"""
        execution_result = self.execute()
        
        if "error" in execution_result:
            return execution_result
        
        result = execution_result["result"]
        
        # 计算效能指标
        assessment = {
            "jam_success_rate": 100.0 if result.get("effective", False) else 0.0,
            "detection_probability": result.get("detection_probability", 0) * 100,
            "j_s_ratio": result.get("j_s_ratio", 0),
            "suggested_tactics": []
        }
        
        # 根据结果建议战术
        if result.get("effective", False):
            assessment["suggested_tactics"].append("继续维持当前干扰参数")
        else:
            assessment["suggested_tactics"].extend([
                "增加干扰功率",
                "调整干扰频率",
                "尝试灵巧干扰"
            ])
        
        return assessment

class ManyVsOneScenario(CombatScenario):
    """多对一对抗想定（多雷达 vs 单干扰机）"""
    
    def __init__(self):
        super().__init__("多对一对抗", "多部雷达 vs 单干扰机协同对抗")
        
    def setup(self, config: Dict[str, Any]):
        """设置多对一对抗"""
        from ..factory import EntityFactory
        
        # 创建多部雷达
        self.radars = []
        for radar_config in config.get("radars", []):
            self.radars.append(EntityFactory.create_radar(radar_config))
        
        # 创建干扰机
        jammer_config = config.get("jammer", {})
        self.jammers = [EntityFactory.create_jammer(jammer_config)]
        
        # 创建目标
        self.targets = []
        for target_config in config.get("targets", []):
            self.targets.append(EntityFactory.create_target(target_config))
    
    def execute(self) -> Dict[str, Any]:
        """执行多对一对抗"""
        if not self.radars or not self.jammers:
            return {"error": "未设置雷达或干扰机"}
        
        jammer = self.jammers[0]
        results = []
        
        from ..simulation import EWSimulator
        
        for radar in self.radars:
            result = EWSimulator.calculate_jamming_effect(
                radar, jammer, self.targets
            )
            results.append({
                "radar_id": radar.id,
                "radar_name": radar.name,
                **result
            })
        
        # 计算协同效果
        effective_count = sum(1 for r in results if r.get("effective", False))
        overall_effectiveness = (effective_count / len(results)) * 100 if results else 0
        
        return {
            "scenario": self.name,
            "jammer": jammer.to_dict(),
            "radar_results": results,
            "overall_effectiveness": overall_effectiveness,
            "recommendation": self._get_recommendation(overall_effectiveness)
        }
    
    def _get_recommendation(self, effectiveness: float) -> str:
        """根据效果给出建议"""
        if effectiveness > 80:
            return "干扰机可同时压制多部雷达，建议分散干扰能量"
        elif effectiveness > 50:
            return "干扰效果良好，建议重点压制关键雷达"
        else:
            return "干扰效果有限，建议采用协同干扰或改变战术"
    def assess(self) -> Dict[str, Any]:
        """评估多对一对抗结果"""
        execution_result = self.execute()
        
        if "error" in execution_result:
            return execution_result
        
        # 提取结果
        jammer = execution_result.get("jammer", {})
        radar_results = execution_result.get("radar_results", [])
        overall_effectiveness = execution_result.get("overall_effectiveness", 0)
        
        # 计算详细指标
        if radar_results:
            # 计算平均干信比
            j_s_ratios = [r.get("j_s_ratio", 0) for r in radar_results]
            avg_j_s_ratio = np.mean(j_s_ratios) if j_s_ratios else 0
            
            # 计算探测概率
            detection_probs = [r.get("detection_probability", 0) for r in radar_results]
            avg_detection_prob = np.mean(detection_probs) * 100 if detection_probs else 0
            
            # 计算压制比例
            suppressed_radars = [r for r in radar_results if not r.get("effective", False)]
            suppression_ratio = (len(suppressed_radars) / len(radar_results)) * 100 if radar_results else 0
        else:
            avg_j_s_ratio = 0
            avg_detection_prob = 0
            suppression_ratio = 0
        
        # 生成评估结果
        assessment = {
            "jam_success_rate": overall_effectiveness,
            "avg_j_s_ratio": avg_j_s_ratio,
            "avg_detection_probability": avg_detection_prob,
            "suppression_ratio": suppression_ratio,
            "radar_count": len(self.radars),
            "effective_radar_count": len([r for r in radar_results if r.get("effective", False)]),
            "jammer_utilization": min(100, len(self.radars) * 20),  # 简化的利用率计算
            "suggested_tactics": []
        }
        
        # 根据结果建议战术
        if overall_effectiveness > 80:
            assessment["suggested_tactics"].extend([
                "干扰效果优秀，可考虑扩大干扰范围",
                "尝试干扰更多频率点"
            ])
        elif overall_effectiveness > 50:
            assessment["suggested_tactics"].extend([
                "干扰效果良好，优化干扰参数可提升效果",
                "考虑集中干扰关键雷达"
            ])
        else:
            assessment["suggested_tactics"].extend([
                "干扰效果有限，建议增加干扰机数量",
                "调整干扰策略，采用分时干扰",
                "协同其他电子战资源"
            ])
        
        # 如果某些雷达特别难干扰，给出特殊建议
        difficult_radars = [r for r in radar_results if r.get("j_s_ratio", 0) < 3]
        if difficult_radars:
            radar_names = [r.get("radar_name", "未知雷达") for r in difficult_radars]
            assessment["suggested_tactics"].append(f"雷达 {', '.join(radar_names)} 抗干扰能力强，需重点关注")
        
        return assessment        

class ManyVsManyScenario(CombatScenario):
    """多对多对抗想定"""
    
    def __init__(self):
        super().__init__("多对多对抗", "雷达网 vs 干扰网体系对抗")
        
    def setup(self, config: Dict[str, Any]):
        """设置多对多对抗"""
        from ..factory import EntityFactory
        
        # 创建雷达网
        self.radars = []
        for radar_config in config.get("radar_network", []):
            self.radars.append(EntityFactory.create_radar(radar_config))
        
        # 创建干扰网
        self.jammers = []
        for jammer_config in config.get("jammer_network", []):
            self.jammers.append(EntityFactory.create_jammer(jammer_config))
        
        # 创建目标群
        self.targets = []
        for target_config in config.get("target_group", []):
            self.targets.append(EntityFactory.create_target(target_config))
    
    def execute(self) -> Dict[str, Any]:
        """执行多对多对抗"""
        from ..simulation import NetworkEWSimulator
        
        network_result = NetworkEWSimulator.simulate_network_combat(
            self.radars, self.jammers, self.targets
        )
        
        return {
            "scenario": self.name,
            "network_result": network_result,
            "radar_count": len(self.radars),
            "jammer_count": len(self.jammers),
            "target_count": len(self.targets)
        }
    
    def assess(self) -> Dict[str, Any]:
        """评估多对多对抗结果"""
        result = self.execute()
        network_result = result.get("network_result", {})
        
        assessment = {
            "network_coverage_ratio": network_result.get("coverage_ratio", 0) * 100,
            "jammer_utilization": network_result.get("jammer_utilization", 0) * 100,
            "system_survivability": network_result.get("survivability", 0) * 100,
            "information_superiority": network_result.get("info_superiority", 0) * 100,
            "recommended_strategies": self._get_strategies(network_result)
        }
        
        return assessment
    
    def _get_strategies(self, result: Dict) -> List[str]:
        """根据结果推荐策略"""
        strategies = []
        
        if result.get("coverage_ratio", 0) > 0.7:
            strategies.append("雷达网覆盖良好，可实施区域防空")
        else:
            strategies.append("雷达网存在漏洞，建议部署补盲雷达")
        
        if result.get("jammer_utilization", 0) > 0.8:
            strategies.append("干扰网过载，建议增加干扰资源或优化分配")
        
        return strategies

class ScenarioFactory:
    """想定工厂"""
    
    _scenarios = {
        "one_vs_one": OneVsOneScenario,
        "many_vs_one": ManyVsOneScenario,
        "many_vs_many": ManyVsManyScenario
    }
    
    @classmethod
    def create_scenario(cls, scenario_type: str) -> CombatScenario:
        """创建对抗想定"""
        scenario_class = cls._scenarios.get(scenario_type)
        if not scenario_class:
            raise ValueError(f"未知的想定类型: {scenario_type}")
        
        return scenario_class()
    
    @classmethod
    def get_available_scenarios(cls) -> List[Dict]:
        """获取可用的想定列表"""
        return [
            {
                "id": "one_vs_one",
                "name": "一对一对抗",
                "description": "单雷达 vs 单干扰机",
                "icon": "🎯"
            },
            {
                "id": "many_vs_one",
                "name": "多对一对抗",
                "description": "多雷达协同 vs 单干扰机",
                "icon": "🛡️"
            },
            {
                "id": "many_vs_many",
                "name": "多对多对抗",
                "description": "雷达网 vs 干扰网体系对抗",
                "icon": "⚔️"
            }
        ]
