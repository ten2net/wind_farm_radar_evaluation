"""
天线分析平台 - 集成测试
测试各模块之间的集成
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.antenna_models import AntennaParameters, AntennaType, PolarizationType
from services.pattern_generator import get_pattern_generator_service
from services.analysis_service import get_analysis_service
from services.visualization_service import get_visualization_service


class TestSystemIntegration:
    """系统集成测试类"""
    
    def setup_method(self):
        """测试设置"""
        # 创建示例天线
        self.antenna = AntennaParameters(
            name="集成测试天线",
            antenna_type=AntennaType.DIPOLE,
            frequency_range=(1.0, 2.0),
            center_frequency=1.5,
            gain=2.15,
            bandwidth=10.0,
            vswr=1.5,
            polarization=PolarizationType.VERTICAL,
            beamwidth_e=78.0,
            beamwidth_h=360.0,
            sidelobe_level=-12.0
        )
        
        # 获取服务实例
        self.pattern_service = get_pattern_generator_service()
        self.analysis_service = get_analysis_service()
        self.viz_service = get_visualization_service()
    
    def test_end_to_end_simulation(self):
        """测试端到端仿真流程"""
        # 1. 生成方向图
        pattern = self.pattern_service.generate_pattern(
            antenna=self.antenna,
            generator_type='analytical',
            theta_resolution=5,
            phi_resolution=5
        )
        
        assert pattern is not None
        assert pattern.frequency == self.antenna.center_frequency
        assert pattern.gain_data.shape == (37, 73)  # 180/5+1, 360/5+1
        
        # 2. 分析方向图
        analysis_results = self.analysis_service.comprehensive_analysis(
            pattern=pattern,
            antenna=self.antenna
        )
        
        assert analysis_results is not None
        assert 'beam' in analysis_results
        assert 'polarization' in analysis_results
        assert 'efficiency' in analysis_results
        assert 'overall_assessment' in analysis_results
        
        # 3. 可视化
        fig_2d = self.viz_service.create_2d_pattern(
            pattern=pattern,
            plane='elevation',
            fixed_angle=0
        )
        
        fig_3d = self.viz_service.create_3d_pattern(
            pattern=pattern,
            show_surface=True
        )
        
        assert fig_2d is not None
        assert fig_3d is not None
    
    def test_parameter_variation_study(self):
        """测试参数变化研究"""
        # 测试不同频率下的方向图变化
        frequencies = [1.0, 1.5, 2.0]
        patterns = []
        
        for freq in frequencies:
            antenna = AntennaParameters(
                name=f"频率测试天线 {freq}GHz",
                antenna_type=AntennaType.DIPOLE,
                center_frequency=freq
            )
            
            pattern = self.pattern_service.generate_pattern(
                antenna=antenna,
                generator_type='analytical'
            )
            patterns.append(pattern)
        
        assert len(patterns) == 3
        
        # 检查频率变化对方向图的影响
        max_gains = [np.max(p.gain_data) for p in patterns]
        
        # 增益应该随频率变化
        assert not all(abs(g - max_gains[0]) < 0.1 for g in max_gains)
    
    def test_export_import_workflow(self, tmp_path):
        """测试导出导入工作流"""
        # 生成方向图
        pattern = self.pattern_service.generate_pattern(
            antenna=self.antenna,
            generator_type='analytical'
        )
        
        # 导出到文件
        export_dir = tmp_path / "exports"
        export_dir.mkdir()
        
        # 测试不同格式导出
        formats = ['npy', 'csv', 'json']
        
        for fmt in formats:
            export_path = export_dir / f"pattern.{fmt}"
            
            if fmt == 'npy':
                pattern.save(export_path)
            elif fmt == 'csv':
                pattern.export_to_csv(export_path)
            elif fmt == 'json':
                pattern.export_to_json(export_path)
            
            # 检查文件是否创建
            assert export_path.exists()
            assert export_path.stat().st_size > 0
    
    def test_comparative_analysis(self):
        """测试比较分析"""
        # 创建两个不同的天线
        antenna1 = AntennaParameters(
            name="偶极子天线",
            antenna_type=AntennaType.DIPOLE,
            center_frequency=1.0
        )
        
        antenna2 = AntennaParameters(
            name="微带贴片",
            antenna_type=AntennaType.PATCH,
            center_frequency=2.4
        )
        
        # 生成方向图
        pattern1 = self.pattern_service.generate_pattern(antenna1)
        pattern2 = self.pattern_service.generate_pattern(antenna2)
        
        # 运行比较分析
        comparison_results = self.analysis_service.compare_patterns(
            patterns=[pattern1, pattern2],
            pattern_names=["偶极子", "微带贴片"]
        )
        
        assert comparison_results is not None
        assert 'patterns' in comparison_results
        assert 'metrics_comparison' in comparison_results
        assert 'summary' in comparison_results
        
        # 检查比较结果
        assert len(comparison_results['patterns']) == 2
        assert len(comparison_results['metrics_comparison']) > 0
    
    def test_performance_benchmark(self):
        """测试性能基准"""
        import time
        
        # 测试方向图生成性能
        start_time = time.time()
        
        pattern = self.pattern_service.generate_pattern(
            antenna=self.antenna,
            generator_type='analytical',
            theta_resolution=1,  # 高分辨率
            phi_resolution=1
        )
        
        generation_time = time.time() - start_time
        
        # 检查生成时间（应该小于2秒）
        assert generation_time < 2.0
        
        # 测试分析性能
        start_time = time.time()
        
        analysis_results = self.analysis_service.comprehensive_analysis(
            pattern=pattern,
            antenna=self.antenna
        )
        
        analysis_time = time.time() - start_time
        
        # 检查分析时间（应该小于5秒）
        assert analysis_time < 5.0
        
        print(f"性能基准:")
        print(f"  方向图生成: {generation_time:.3f}秒")
        print(f"  综合分析: {analysis_time:.3f}秒")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效天线参数
        invalid_antenna = AntennaParameters(
            name="无效天线",
            antenna_type=AntennaType.DIPOLE,
            center_frequency=-1.0  # 无效频率
        )
        
        # 应该抛出异常
        with pytest.raises(ValueError):
            self.pattern_service.generate_pattern(invalid_antenna)
        
        # 测试无效分辨率
        with pytest.raises(ValueError):
            self.pattern_service.generate_pattern(
                antenna=self.antenna,
                theta_resolution=0  # 无效分辨率
            )
        
        # 测试无效分析参数
        pattern = self.pattern_service.generate_pattern(self.antenna)
        
        with pytest.raises(ValueError):
            self.analysis_service.analyze_beam(
                pattern=pattern,
                invalid_param=True
            )
    
    def test_data_persistence(self, tmp_path):
        """测试数据持久化"""
        # 创建临时数据库
        db_path = tmp_path / "test_database.db"
        
        # 这里应该测试数据库操作
        # 由于数据库实现不在当前范围，这里只是占位
        print(f"数据库路径: {db_path}")
        
        # 测试配置文件持久化
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        config_data = {
            'test_setting': 'value',
            'nested': {
                'setting': 123
            }
        }
        
        import yaml
        config_file = config_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 读取配置文件
        with open(config_file, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        assert loaded_config == config_data


class TestServiceIntegration:
    """服务集成测试类"""
    
    def test_pattern_generator_services(self):
        """测试方向图生成器服务"""
        service = get_pattern_generator_service()
        
        # 测试不同生成器
        antenna = AntennaParameters(
            name="测试天线",
            antenna_type=AntennaType.DIPOLE,
            center_frequency=1.0
        )
        
        generators = ['analytical', 'numerical']
        
        for generator_type in generators:
            pattern = service.generate_pattern(
                antenna=antenna,
                generator_type=generator_type
            )
            
            assert pattern is not None
            assert pattern.frequency == antenna.center_frequency
            
            # 检查数据有效性
            assert not np.any(np.isnan(pattern.gain_data))
            assert not np.any(np.isinf(pattern.gain_data))
    
    def test_analysis_service_integration(self):
        """测试分析服务集成"""
        service = get_analysis_service()
        
        # 创建测试方向图
        antenna = AntennaParameters(
            name="分析测试天线",
            antenna_type=AntennaType.DIPOLE,
            center_frequency=1.0
        )
        
        pattern_service = get_pattern_generator_service()
        pattern = pattern_service.generate_pattern(antenna)
        
        # 测试各种分析
        analysis_types = [
            'beam_analysis',
            'polarization_analysis',
            'efficiency_analysis',
            'frequency_analysis'
        ]
        
        for analysis_type in analysis_types:
            result = service.analyze_pattern(
                pattern=pattern,
                antenna=antenna,
                analysis_type=analysis_type
            )
            
            assert result is not None
            assert 'analysis_type' in result
            assert result['analysis_type'] == analysis_type
    
    def test_visualization_service_integration(self):
        """测试可视化服务集成"""
        service = get_visualization_service()
        
        # 创建测试方向图
        antenna = AntennaParameters(
            name="可视化测试天线",
            antenna_type=AntennaType.DIPOLE,
            center_frequency=1.0
        )
        
        pattern_service = get_pattern_generator_service()
        pattern = pattern_service.generate_pattern(antenna)
        
        # 测试2D可视化
        fig_2d = service.create_2d_pattern(
            pattern=pattern,
            plane='elevation',
            fixed_angle=0,
            title="测试2D方向图"
        )
        
        assert fig_2d is not None
        assert hasattr(fig_2d, 'update_layout')
        
        # 测试3D可视化
        fig_3d = service.create_3d_pattern(
            pattern=pattern,
            title="测试3D方向图"
        )
        
        assert fig_3d is not None
        assert hasattr(fig_3d, 'update_layout')
        
        # 测试统计图表
        analysis_service = get_analysis_service()
        analysis_results = analysis_service.comprehensive_analysis(pattern, antenna)
        
        fig_stats = service.create_analysis_summary(
            analysis_results=analysis_results,
            title="测试分析摘要"
        )
        
        assert fig_stats is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])