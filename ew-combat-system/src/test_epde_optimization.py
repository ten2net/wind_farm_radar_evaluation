# 文件: examples/test_epde_optimization.py
"""
ePDE优化算法测试示例
"""

def test_epde_optimization():
    """测试ePDE优化算法"""
    print("测试COTEJA ePDE优化算法...")
    
    # 创建测试场景（基于文章的4v5场景）
    from core.entities.radar_enhanced import EnhancedRadar
    from core.optimization.optimization_controller import OptimizationController
    
    # 创建4个干扰机
    class MockJammer:
        def __init__(self, jammer_id, name, position, power):
            self.id = jammer_id
            self.name = name
            self.position = position
            self.power = power
    
    jammers = [
        MockJammer("J1", "干扰机1", {"lat": 40.0, "lon": 116.5, "alt": 10000}, 1000),
        MockJammer("J2", "干扰机2", {"lat": 40.1, "lon": 116.6, "alt": 11000}, 1200),
        MockJammer("J3", "干扰机3", {"lat": 39.9, "lon": 116.4, "alt": 9500}, 900),
        MockJammer("J4", "干扰机4", {"lat": 40.2, "lon": 116.7, "alt": 10500}, 1100)
    ]
    
    # 创建5个雷达（基于文章图3）
    radars = [
        EnhancedRadar("R1", "雷达1", {"lat": 39.8, "lon": 116.3, "alt": 50}, 3.0, 100),
        EnhancedRadar("R2", "雷达2", {"lat": 39.9, "lon": 116.4, "alt": 60}, 3.2, 120),
        EnhancedRadar("R3", "雷达3", {"lat": 40.0, "lon": 116.5, "alt": 70}, 3.5, 150),
        EnhancedRadar("R4", "雷达4", {"lat": 40.1, "lon": 116.6, "alt": 80}, 3.8, 180),
        EnhancedRadar("R5", "雷达5", {"lat": 40.2, "lon": 116.7, "alt": 90}, 4.0, 200)
    ]
    
    # 创建模拟场景
    class MockScenario:
        def __init__(self, radars, jammers):
            self.radars = radars
            self.jammers = jammers
            self.name = "4v5测试场景"
    
    scenario = MockScenario(radars, jammers)
    
    # 运行优化
    controller = OptimizationController(consider_illumination=True, time_limit=1.0)
    result = controller.run_optimization(scenario)
    
    # 显示结果
    if result['success']:
        print("\n" + "="*50)
        print("优化结果摘要:")
        print(f"最优适应度: {result['best_fitness']:.3f}")
        print(f"优化时间: {result['optimization_time']:.3f}s")
        print(f"资源利用率: {result['resource_utilization']:.1%}")
        
        # 显示分配详情
        report = result['assignment_report']
        print(f"\n分配详情:")
        for assignment in report['assignments']:
            print(f"  {assignment['jammer_name']} -> {assignment['target_name']} "
                  f"({assignment['technique']}, {assignment['bw_type']}): "
                  f"效果={assignment['effectiveness']:.3f}")
    
    print("✅ ePDE优化测试完成!")

if __name__ == "__main__":
    test_epde_optimization()