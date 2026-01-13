# 文件: tests/test_coteja_integration.py
"""
COTEJA系统集成测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestCOTEJAIntegration:
    """COTEJA系统集成测试类"""
    
    def test_optimization_flow(self):
        """测试优化流程"""
        from src.core.optimization.optimization_controller import OptimizationController
        from src.core.analysis.combat_analyzer import CombatAnalyzer
        
        # 创建测试场景
        scenario = self.create_test_scenario()
        
        # 创建优化控制器
        controller = OptimizationController(time_limit=1.0)
        
        # 运行优化
        result = controller.run_optimization(scenario)
        
        # 验证结果
        assert result['success'] == True
        assert result['optimization_time'] <= 2.0  # 包含额外缓冲
        assert result['best_fitness'] >= 0.0
        assert 'best_solution' in result
        
        print("✅ 优化流程测试通过")
    
    def test_combat_analysis(self):
        """测试对抗分析"""
        from src.core.analysis.combat_analyzer import CombatAnalyzer
        
        analyzer = CombatAnalyzer(consider_illumination=True)
        scenario = self.create_test_scenario()
        
        # 测试基础分析功能
        effectiveness = analyzer.calculate_jamming_effectiveness(
            scenario['radars'][0], scenario['jammers'][0], 'NJ', 'M', 1
        )
        
        assert -1.0 <= effectiveness <= 1.0
        print("✅ 对抗分析测试通过")
    
    def create_test_scenario(self):
        """创建测试场景"""
        from src.core.entities.radar_enhanced import EnhancedRadar
        
        # 创建测试雷达
        radars = [
            EnhancedRadar("R1", "测试雷达1", {"lat": 39.9, "lon": 116.4, "alt": 50}, 3.0, 100),
            EnhancedRadar("R2", "测试雷达2", {"lat": 40.0, "lon": 116.5, "alt": 60}, 3.5, 120)
        ]
        
        # 创建测试干扰机
        jammers = [
            {
                'id': 'J1', 
                'name': '测试干扰机1',
                'position': {'lat': 40.1, 'lon': 116.6, 'alt': 10000},
                'power': 1000,
                'type': 'standoff_jammer'
            }
        ]
        
        return {
            'name': '集成测试场景',
            'radars': radars,
            'jammers': jammers
        }

if __name__ == "__main__":
    # 运行测试
    test = TestCOTEJAIntegration()
    test.test_optimization_flow()
    test.test_combat_analysis()
    print("🎉 所有集成测试通过！")