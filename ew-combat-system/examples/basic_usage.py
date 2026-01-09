"""
基本使用示例
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.patterns.strategy import ScenarioFactory
from src.core.factory import EntityFactory
from src.visualization.geoviz import EWVisualizer
import holoviews as hv

def example_one_vs_one():
    """一对一对抗示例"""
    print("=== 一对一对抗示例 ===")
    
    # 1. 创建想定
    scenario = ScenarioFactory.create_scenario("one_vs_one")
    
    # 2. 配置参数
    config = {
        "radar": {
            "id": "radar_001",
            "name": "预警雷达",
            "lat": 39.9,
            "lon": 116.4,
            "alt": 50.0,
            "frequency": 3.0,
            "power": 100.0,
            "range_max": 300.0
        },
        "jammer": {
            "id": "jammer_001",
            "name": "远距干扰机",
            "lat": 40.0,
            "lon": 116.5,
            "alt": 10000.0,
            "power": 1000.0,
            "beamwidth": 60.0
        }
    }
    
    # 3. 设置想定
    scenario.setup(config)
    
    # 4. 执行仿真
    results = scenario.execute()
    
    # 5. 显示结果
    print(f"想定: {results['scenario']}")
    print(f"雷达: {results['radar']['name']}")
    print(f"干扰机: {results['jammer']['name']}")
    print(f"干扰是否有效: {results['result']['effective']}")
    print(f"干信比: {results['result']['j_s_ratio']:.1f} dB")
    
    # 6. 评估
    assessment = scenario.assess()
    print(f"\n效能评估:")
    print(f"干扰成功率: {assessment['jam_success_rate']:.1f}%")
    print(f"探测概率: {assessment['detection_probability']:.1f}%")
    print(f"建议战术: {', '.join(assessment['suggested_tactics'])}")
    
    return scenario, results

def example_many_vs_one():
    """多对一对抗示例"""
    print("\n=== 多对一对抗示例 ===")
    
    scenario = ScenarioFactory.create_scenario("many_vs_one")
    
    config = {
        "radars": [
            {
                "id": "radar_001",
                "name": "雷达1",
                "lat": 39.9,
                "lon": 116.4,
                "frequency": 3.0,
                "power": 100.0
            },
            {
                "id": "radar_002",
                "name": "雷达2",
                "lat": 40.0,
                "lon": 116.5,
                "frequency": 2.5,
                "power": 80.0
            },
            {
                "id": "radar_003",
                "name": "雷达3",
                "lat": 39.8,
                "lon": 116.3,
                "frequency": 3.2,
                "power": 120.0
            }
        ],
        "jammer": {
            "id": "jammer_001",
            "name": "干扰机",
            "lat": 40.1,
            "lon": 116.6,
            "power": 1500.0
        }
    }
    
    scenario.setup(config)
    results = scenario.execute()
    
    print(f"雷达数量: {len(scenario.radars)}")
    print(f"干扰机数量: {len(scenario.jammers)}")
    print(f"整体干扰效果: {results['overall_effectiveness']:.1f}%")
    print(f"建议: {results['recommendation']}")
    
    return scenario, results

def example_visualization():
    """可视化示例"""
    print("\n=== 可视化示例 ===")
    
    # 创建实体
    from src.core.entities import Radar, Jammer, Position, RadarParameters, JammerParameters
    
    # 创建雷达
    radar_pos = Position(39.9, 116.4, 50.0)
    radar_params = RadarParameters(
        frequency=3.0,
        power=100.0,
        gain=40.0,
        beamwidth=1.5
    )
    
    radar = Radar(
        id="vis_radar",
        name="可视化雷达",
        position=radar_pos,
        radar_params=radar_params
    )
    
    # 创建干扰机
    jammer_pos = Position(40.0, 116.5, 10000.0)
    jammer_params = JammerParameters(
        frequency_range=(0.5, 18.0),
        power=1000.0,
        gain=15.0,
        beamwidth=60.0,
        eirp=80.0,
        jam_types=["阻塞"],
        response_time=2.0
    )
    
    jammer = Jammer(
        id="vis_jammer",
        name="可视化干扰机",
        position=jammer_pos,
        jammer_params=jammer_params
    )
    
    # 创建可视化
    ew_map = EWVisualizer.create_coverage_map([radar], [jammer])
    
    # 保存为HTML文件
    import holoviews as hv
    hv.save(ew_map, 'ew_visualization.html')
    print("可视化已保存为 ew_visualization.html")
    
    return ew_map

def main():
    """主函数"""
    print("电子战对抗仿真系统 - 使用示例")
    print("=" * 50)
    
    try:
        # 运行示例
        scenario1, results1 = example_one_vs_one()
        scenario2, results2 = example_many_vs_one()
        
        # 可视化
        ew_map = example_visualization()
        
        print("\n所有示例运行完成！")
        
    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
