"""
性能测试
"""
import pytest
import time
import numpy as np
from src.core.simulation import EWSimulator
from src.core.entities import Radar, Jammer, Position, RadarParameters, JammerParameters
from src.core.entities.target import Aircraft

class TestPerformance:
    """性能测试"""
    
    def setup_entities(self, count=10):
        """设置测试实体"""
        radars = []
        jammers = []
        targets = []
        
        # 创建多个实体
        for i in range(count):
            # 创建雷达
            radar_pos = Position(39.9 + i*0.01, 116.4 + i*0.01, 50.0)
            radar_params = RadarParameters(
                frequency=3.0 + i*0.1,
                power=100.0 + i*10,
                gain=40.0,
                beamwidth=1.5
            )
            
            radar = Radar(
                id=f"radar_{i}",
                name=f"雷达{i}",
                position=radar_pos,
                radar_params=radar_params
            )
            radars.append(radar)
            
            # 创建干扰机
            jammer_pos = Position(40.0 + i*0.01, 116.5 + i*0.01, 10000.0)
            jammer_params = JammerParameters(
                frequency_range=(0.5, 18.0),
                power=1000.0 + i*100,
                gain=15.0,
                beamwidth=60.0,
                eirp=80.0,
                jam_types=["阻塞"],
                response_time=2.0
            )
            
            jammer = Jammer(
                id=f"jammer_{i}",
                name=f"干扰机{i}",
                position=jammer_pos,
                jammer_params=jammer_params
            )
            jammers.append(jammer)
            
            # 创建目标
            target = Aircraft(
                id=f"target_{i}",
                name=f"目标{i}",
                position=Position(40.0 + i*0.005, 116.5 + i*0.005, 10000.0),
                rcs=5.0 + i*0.5,
                speed=300.0
            )
            targets.append(target)
        
        return radars, jammers, targets
    
    def test_jamming_effect_performance(self):
        """测试干扰效果计算性能"""
        radars, jammers, targets = self.setup_entities(count=5)
        
        # 测量计算时间
        start_time = time.time()
        
        for radar in radars:
            for jammer in jammers:
                result = EWSimulator.calculate_jamming_effect(
                    radar, jammer, targets[:1]
                )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n干扰效果计算时间: {execution_time:.3f}秒")
        print(f"计算次数: {len(radars) * len(jammers)}")
        
        # 验证性能要求（应该小于1秒）
        assert execution_time < 1.0, f"计算时间过长: {execution_time:.3f}秒"
    
    def test_coverage_simulation_performance(self):
        """测试覆盖模拟性能"""
        radars, _, _ = self.setup_entities(count=3)
        
        start_time = time.time()
        
        for radar in radars:
            coverage = EWSimulator.simulate_radar_coverage(
                radar, resolution_km=10.0
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n覆盖模拟计算时间: {execution_time:.3f}秒")
        print(f"雷达数量: {len(radars)}")
        
        # 验证性能要求
        assert execution_time < 2.0, f"覆盖模拟时间过长: {execution_time:.3f}秒"
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量实体
        radars, jammers, targets = self.setup_entities(count=50)
        
        # 记录创建后内存
        after_creation_memory = process.memory_info().rss / 1024 / 1024
        
        memory_increase = after_creation_memory - initial_memory
        
        print(f"\n内存使用情况:")
        print(f"初始内存: {initial_memory:.1f} MB")
        print(f"创建后内存: {after_creation_memory:.1f} MB")
        print(f"内存增加: {memory_increase:.1f} MB")
        
        # 验证内存使用
        assert memory_increase < 100.0, f"内存使用过多: {memory_increase:.1f} MB"
    
    def test_large_scale_simulation(self):
        """测试大规模仿真性能"""
        # 创建大量实体
        entity_counts = [10, 20, 50]
        
        for count in entity_counts:
            radars, jammers, targets = self.setup_entities(count=count)
            
            start_time = time.time()
            
            # 执行仿真计算
            calculations = 0
            for radar in radars:
                for jammer in jammers:
                    result = EWSimulator.calculate_jamming_effect(radar, jammer)
                    calculations += 1
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"\n实体数量: {count}")
            print(f"计算次数: {calculations}")
            print(f"执行时间: {execution_time:.3f}秒")
            print(f"平均每次计算时间: {execution_time/calculations*1000:.1f}毫秒")
            
            # 验证性能
            assert execution_time < 5.0, f"大规模仿真时间过长: {execution_time:.3f}秒"
    
    def test_concurrent_calculations(self):
        """测试并发计算性能"""
        import concurrent.futures
        
        radars, jammers, targets = self.setup_entities(count=20)
        
        # 串行计算
        start_time = time.time()
        
        serial_results = []
        for radar in radars:
            for jammer in jammers:
                result = EWSimulator.calculate_jamming_effect(radar, jammer)
                serial_results.append(result)
        
        serial_time = time.time() - start_time
        
        # 并行计算
        start_time = time.time()
        
        parallel_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for radar in radars:
                for jammer in jammers:
                    future = executor.submit(
                        EWSimulator.calculate_jamming_effect, radar, jammer
                    )
                    futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                parallel_results.append(future.result())
        
        parallel_time = time.time() - start_time
        
        print(f"\n计算性能对比:")
        print(f"串行计算时间: {serial_time:.3f}秒")
        print(f"并行计算时间: {parallel_time:.3f}秒")
        print(f"加速比: {serial_time/parallel_time:.2f}x")
        
        # 验证结果数量
        assert len(serial_results) == len(parallel_results)
        
        # 验证并行计算加速
        if len(radars) * len(jammers) > 10:
            assert parallel_time < serial_time, "并行计算没有加速"
