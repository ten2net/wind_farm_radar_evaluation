from typing import Any, Dict, List, Tuple, Union
import numpy as np
from numpy.typing import NDArray
from radar_factory_app.services.cfar_processor import CFARProcessor
from radar_factory_app.services.target_matching import MatchMethod, MatchResult, _match_target_to_detection_1d, _match_target_to_detection_2d, match_radar_detections


class RadarDetectionEvaluator:
    """
    雷达检测评估器，集成CFAR检测和目标匹配功能
    """
    
    def __init__(self, detector_type: str = "squarelaw"):
        self.cfar_processor = CFARProcessor(detector_type)
        self.match_results = {}
    
    def evaluate_detection_performance(
        self,
        radar_data: NDArray,
        true_targets: Union[NDArray, Dict[str, NDArray]],
        guard: Union[int, List[int]],
        trailing: Union[int, List[int]],
        pfa: float = 1e-5,
        tolerance: Union[float, Tuple[float, float]] = 2.0,
        match_method: MatchMethod = MatchMethod.NEAREST_NEIGHBOR,
        detection_axis: int = 0
    ) -> Dict[str, Any]:
        """
        完整的检测性能评估流程
        
        :param radar_data: 雷达数据（距离/多普勒图等）
        :param true_targets: 真实目标位置
        :param guard: 保护单元数
        :param trailing: 参考单元数  
        :param pfa: 虚警概率
        :param tolerance: 匹配容差
        :param match_method: 匹配方法
        :param detection_axis: 检测轴（0: 距离维, 1: 多普勒维）
        :return: 完整的性能评估结果
        """
        # 执行CFAR检测
        if radar_data.ndim == 1:
            # 1D数据（距离剖面）
            cfar_threshold = self.cfar_processor.cfar_ca_1d(
                radar_data, guard, trailing, pfa, detection_axis # type: ignore
            )
            detections = radar_data > cfar_threshold
            detection_positions = np.where(detections)[0]
            
        elif radar_data.ndim == 2:
            # 2D数据（距离-多普勒图）
            cfar_threshold = self.cfar_processor.cfar_ca_2d(
                radar_data, guard, trailing, pfa
            )
            detections = radar_data > cfar_threshold
            detection_positions = np.column_stack(np.where(detections))
        
        else:
            raise ValueError("只支持1D或2D雷达数据")
        
        # 执行目标匹配
        if isinstance(true_targets, dict):
            # 雷达专用匹配（距离-多普勒）
            match_result = match_radar_detections(
                true_targets, 
                self._format_detections_to_dict(detection_positions, radar_data.ndim),
                tolerance[0] if isinstance(tolerance, (list, tuple)) else tolerance,
                tolerance[1] if isinstance(tolerance, (list, tuple)) and len(tolerance) > 1 else tolerance,
                match_method
            )
        else:
            # 通用匹配
            if radar_data.ndim == 1:
                match_result = _match_target_to_detection_1d(
                    true_targets, detection_positions, tolerance, match_method # type: ignore
                )
            else:
                match_result = _match_target_to_detection_2d(
                    true_targets, detection_positions, tolerance, match_method
                )
        
        # 性能分析
        performance_stats = self._analyze_comprehensive_performance(
            radar_data, detections, cfar_threshold, match_result
        )
        
        # 存储结果
        result_id = f"eval_{len(self.match_results)}"
        self.match_results[result_id] = {
            'detections': detections,
            'threshold': cfar_threshold,
            'match_result': match_result,
            'performance_stats': performance_stats,
            'timestamp': np.datetime64('now')
        }
        
        return {
            'match_result': match_result,
            'performance_stats': performance_stats,
            'detection_map': detections,
            'cfar_threshold': cfar_threshold,
            'evaluation_id': result_id
        }
    
    def _format_detections_to_dict(
        self, 
        detection_positions: NDArray, 
        data_ndim: int
    ) -> Dict[str, NDArray]:
        """将检测位置格式化为雷达专用字典格式"""
        if data_ndim == 1:
            return {'range': detection_positions}
        else:
            if len(detection_positions) > 0:
                return {
                    'range': detection_positions[:, 0],
                    'doppler': detection_positions[:, 1]
                }
            else:
                return {'range': np.array([]), 'doppler': np.array([])}
    
    def _analyze_comprehensive_performance(
        self,
        radar_data: NDArray,
        detections: NDArray, 
        threshold: NDArray,
        match_result: MatchResult
    ) -> Dict[str, Any]:
        """综合分析检测性能"""
        # 计算检测统计
        num_detections = np.sum(detections)
        detection_power = np.sum(radar_data[detections]) if num_detections > 0 else 0
        
        # 信噪比分析
        snr_stats = self._analyze_detection_snr(radar_data, detections, threshold)
        
        return {
            'detection_statistics': {
                'total_detections': num_detections,
                'detection_power': detection_power,
                'detection_density': num_detections / radar_data.size if radar_data.size > 0 else 0
            },
            'snr_analysis': snr_stats,
            'matching_metrics': {
                'precision': match_result.precision,
                'recall': match_result.recall,
                'f1_score': match_result.f1_score,
                'true_positives': match_result.true_positives,
                'false_positives': match_result.false_positives,
                'false_negatives': match_result.false_negatives
            },
            'quality_metrics': {
                'average_match_distance': np.mean(match_result.match_distances) if match_result.match_distances else 0,
                'max_match_distance': np.max(match_result.match_distances) if match_result.match_distances else 0,
                'match_quality_score': self._calculate_match_quality(match_result)
            }
        }
    
    def _analyze_detection_snr(
        self,
        data: NDArray,
        detections: NDArray,
        threshold: NDArray
    ) -> Dict[str, float]:
        """分析检测点的信噪比"""
        detection_indices = np.where(detections)
        
        if len(detection_indices[0]) == 0:
            return {'mean_snr': 0, 'max_snr': 0, 'min_snr': 0, 'snr_std': 0}
        
        snr_values = []
        for idx in zip(*detection_indices):
            signal_power = data[idx]
            noise_estimate = self._estimate_local_noise(data, idx, 5)
            if noise_estimate > 0:
                snr_db = 10 * np.log10(signal_power / noise_estimate)
                snr_values.append(snr_db)
        
        if snr_values:
            return {
                'mean_snr': float(np.mean(snr_values)),
                'max_snr': float(np.max(snr_values)),
                'min_snr': float(np.min(snr_values)),
                'snr_std': float(np.std(snr_values))
            }
        else:
            return {'mean_snr': 0, 'max_snr': 0, 'min_snr': 0, 'snr_std': 0}
    
    def _estimate_local_noise(
        self,
        data: NDArray,
        center_index: tuple,
        window_size: int
    ) -> float:
        """估计局部噪声功率"""
        half_window = window_size // 2
        
        if data.ndim == 1:
            # 1D数据
            start_idx = max(0, center_index[0] - half_window)
            end_idx = min(data.shape[0], center_index[0] + half_window + 1)
            
            noise_region = data[start_idx:end_idx]
            # 排除中心点附近的区域
            center_start = max(0, center_index[0] - 1)
            center_end = min(data.shape[0], center_index[0] + 2)
            
            mask = np.ones_like(noise_region, dtype=bool)
            local_center_start = center_start - start_idx
            local_center_end = center_end - start_idx
            
            if local_center_start >= 0 and local_center_end <= len(noise_region):
                mask[local_center_start:local_center_end] = False
            
            noise_samples = noise_region[mask]
        else:
            # 2D数据
            rows, cols = data.shape
            row_start = max(0, center_index[0] - half_window)
            row_end = min(rows, center_index[0] + half_window + 1)
            col_start = max(0, center_index[1] - half_window)
            col_end = min(cols, center_index[1] + half_window + 1)
            
            noise_region = data[row_start:row_end, col_start:col_end]
            
            # 创建掩码排除中心区域
            mask = np.ones(noise_region.shape, dtype=bool)
            center_row_start = max(0, center_index[0] - 1) - row_start
            center_row_end = min(rows, center_index[0] + 2) - row_start
            center_col_start = max(0, center_index[1] - 1) - col_start
            center_col_end = min(cols, center_index[1] + 2) - col_start
            
            if (center_row_start >= 0 and center_row_end <= noise_region.shape[0] and
                center_col_start >= 0 and center_col_end <= noise_region.shape[1]):
                mask[center_row_start:center_row_end, 
                     center_col_start:center_col_end] = False
            
            noise_samples = noise_region[mask]
        
        return np.mean(noise_samples) if len(noise_samples) > 0 else np.mean(data) # type: ignore
    
    def _calculate_match_quality(self, match_result: MatchResult) -> float:
        """计算匹配质量分数（0-1）"""
        if not match_result.match_distances:
            return 0.0
        
        # 基于匹配距离和检测统计的质量评分
        avg_distance = np.mean(match_result.match_distances)
        max_distance = np.max(match_result.match_distances) if match_result.match_distances else 1
        
        # 距离质量（距离越小越好）
        distance_quality = 1.0 / (1.0 + avg_distance)
        
        # 检测质量（基于精确率和召回率）
        detection_quality = match_result.f1_score
        
        # 综合质量分数
        match_quality = 0.7 * detection_quality + 0.3 * distance_quality
        
        return min(1.0, max(0.0, float(match_quality)))
    
    def get_evaluation_history(self) -> Dict[str, Any]:
        """获取评估历史"""
        return self.match_results
    
    def clear_history(self):
        """清除评估历史"""
        self.match_results.clear()


# 使用示例
if __name__ == "__main__":
    # 创建评估器
    evaluator = RadarDetectionEvaluator("squarelaw")
    
    # 生成模拟雷达数据
    np.random.seed(42)
    range_doppler_map = np.random.rand(100, 50)  # 100个距离门，50个多普勒单元
    
    # 添加模拟目标
    range_doppler_map[25, 8] += 5.0  # 强目标
    range_doppler_map[40, 3] += 3.0  # 中等目标
    range_doppler_map[55, 6] += 4.0  # 强目标
    range_doppler_map[10, 5] += 2.0  # 弱目标
    
    # 真实目标位置
    true_targets = {
        'range': np.array([10, 25, 40, 55]),
        'doppler': np.array([5, 8, 3, 6])
    }
    
    # 执行性能评估
    results = evaluator.evaluate_detection_performance(
        radar_data=range_doppler_map,
        true_targets=true_targets,
        guard=2,
        trailing=10,
        pfa=1e-6,
        tolerance=(2.0, 2.0),  # 距离容差2单元，多普勒容差2单元
        match_method=MatchMethod.HUNGARIAN
    )
    
    # 输出结果
    print("=== 雷达检测性能评估结果 ===")
    match_result = results['match_result']
    performance_stats = results['performance_stats']
    
    print(f"检测统计:")
    print(f"  总检测数: {performance_stats['detection_statistics']['total_detections']}")
    print(f"  检测功率: {performance_stats['detection_statistics']['detection_power']:.2f}")
    
    print(f"\n匹配指标:")
    print(f"  精确率: {match_result.precision:.3f}")
    print(f"  召回率: {match_result.recall:.3f}") 
    print(f"  F1分数: {match_result.f1_score:.3f}")
    print(f"  正确检测: {match_result.true_positives}")
    print(f"  虚警: {match_result.false_positives}")
    print(f"  漏检: {match_result.false_negatives}")
    
    print(f"\n信噪比分析:")
    snr_stats = performance_stats['snr_analysis']
    print(f"  平均信噪比: {snr_stats['mean_snr']:.2f} dB")
    print(f"  最大信噪比: {snr_stats['max_snr']:.2f} dB")
    print(f"  最小信噪比: {snr_stats['min_snr']:.2f} dB")
    
    print(f"\n质量指标:")
    quality_stats = performance_stats['quality_metrics']
    print(f"  平均匹配距离: {quality_stats['average_match_distance']:.3f}")
    print(f"  匹配质量分数: {quality_stats['match_quality_score']:.3f}")
    
    # 显示匹配对详情
    print(f"\n匹配对详情:")
    for i, (target_idx, detection_idx) in enumerate(match_result.matched_pairs):
        print(f"  目标{target_idx} -> 检测{detection_idx} (距离: {match_result.match_distances[i]:.3f})")
        
        