# 文件: examples/test_combat_analysis.py
"""
对抗分析模块测试示例
"""

def test_combat_analysis():
    """测试对抗分析功能"""
    print("测试COTEJA对抗分析模块...")
    
    # 创建测试雷达
    from core.entities.radar_enhanced import EnhancedRadar
    from core.analysis.combat_analyzer import CombatAnalyzer
    
    # 创建雷达
    radar1 = EnhancedRadar(
        radar_id="radar_001",
        name="预警雷达",
        position={"lat": 39.9, "lon": 116.4, "alt": 50.0},
        frequency=3.0,
        power=100.0
    )
    
    # 创建模拟干扰机
    class MockJammer:
        def __init__(self, jammer_id, name, position, power):
            self.id = jammer_id
            self.name = name
            self.position = position
            self.power = power
    
    jammer1 = MockJammer(
        jammer_id="jammer_001",
        name="干扰机1",
        position={"lat": 40.0, "lon": 116.5, "alt": 10000.0},
        power=1000.0
    )
    
    # 创建对抗分析器
    analyzer = CombatAnalyzer(consider_illumination=True)
    
    # 测试单个干扰效果
    effectiveness = analyzer.calculate_jamming_effectiveness(
        radar1, jammer1, "NJ", "M", 1
    )
    
    print(f"单个干扰效果: {effectiveness:.3f}")
    
    # 测试雷达阶段更新
    radar1.update_stage(5.0, effectiveness)  # 5秒时间步长
    print(f"雷达阶段: {radar1.current_stage}, 性能水平: {radar1.performance_level:.3f}")
    
    # 测试协同干扰
    jamming_assignments = [{
        'jammer_id': 'jammer_001',
        'target_id': 'radar_001', 
        'technique': 'NJ',
        'bw_type': 'M'
    }]
    
    cooperative_effect = analyzer.calculate_cooperative_effect(
        radar1, jamming_assignments, [jammer1]
    )
    
    print(f"协同干扰效果: {cooperative_effect:.3f}")
    
    print("✅ 对抗分析测试完成!")

if __name__ == "__main__":
    test_combat_analysis()