import numpy as np
from typing import Tuple, List, Dict, Union, Optional
from numpy.typing import NDArray
from scipy.spatial.distance import cdist
from dataclasses import dataclass
from enum import Enum


class MatchMethod(Enum):
    """目标匹配方法枚举"""
    NEAREST_NEIGHBOR = "nearest_neighbor"  # 最近邻匹配
    HUNGARIAN = "hungarian"  # 匈牙利算法（最优匹配）
    THRESHOLD = "threshold"  # 阈值匹配


@dataclass
class MatchResult:
    """匹配结果数据结构"""
    true_positives: int  # 正确检测数
    false_positives: int  # 虚警数
    false_negatives: int  # 漏检数
    matched_pairs: List[Tuple[int, int]]  # 匹配对列表 (目标索引, 检测索引)
    match_distances: List[float]  # 匹配距离列表
    precision: float  # 精确率
    recall: float  # 召回率
    f1_score: float  # F1分数


def _match_target_to_detection_1d(
    target_positions: NDArray,
    detection_positions: NDArray,
    tolerance: Union[float, NDArray] = 1.0,
    match_method: MatchMethod = MatchMethod.NEAREST_NEIGHBOR,
    max_distance: Optional[float] = None
) -> MatchResult:
    """
    1D目标检测匹配函数（用于距离/多普勒维匹配）
    
    :param target_positions: 真实目标位置 (N_targets,)
    :param detection_positions: 检测到的目标位置 (N_detections,)
    :param tolerance: 匹配容差，可以是标量或与target_positions同长度的数组
    :param match_method: 匹配方法
    :param max_distance: 最大匹配距离，超过此距离不匹配
    :return: 匹配结果对象
    """
    # 输入验证
    target_positions = np.asarray(target_positions).flatten()
    detection_positions = np.asarray(detection_positions).flatten()
    
    if target_positions.ndim != 1 or detection_positions.ndim != 1:
        raise ValueError("输入位置数组必须为1D")
    
    n_targets = len(target_positions)
    n_detections = len(detection_positions)
    
    # 处理容差参数
    if np.isscalar(tolerance):
        tolerance = np.full(n_targets, tolerance)
    else:
        tolerance = np.asarray(tolerance).flatten()
        if len(tolerance) != n_targets:
            raise ValueError("容差数组长度必须与目标数量一致")
    
    if max_distance is None:
        max_distance = np.inf
    
    # 空情况处理
    if n_targets == 0 and n_detections == 0:
        return MatchResult(0, 0, 0, [], [], 1.0, 1.0, 1.0)
    elif n_targets == 0:
        return MatchResult(0, n_detections, 0, [], [], 0.0, 1.0, 0.0)
    elif n_detections == 0:
        return MatchResult(0, 0, n_targets, [], [], 1.0, 0.0, 0.0)
    
    if match_method == MatchMethod.NEAREST_NEIGHBOR:
        return _nearest_neighbor_match_1d(
            target_positions, detection_positions, tolerance, max_distance
        )
    elif match_method == MatchMethod.HUNGARIAN:
        return _hungarian_match_1d(
            target_positions, detection_positions, tolerance, max_distance
        )
    elif match_method == MatchMethod.THRESHOLD:
        return _threshold_match_1d(
            target_positions, detection_positions, tolerance, max_distance
        )
    else:
        raise ValueError(f"不支持的匹配方法: {match_method}")


def _match_target_to_detection_2d(
    target_positions: NDArray,
    detection_positions: NDArray,
    tolerance: Union[float, NDArray, Tuple[float, float]] = (1.0, 1.0),
    match_method: MatchMethod = MatchMethod.NEAREST_NEIGHBOR,
    max_distance: Optional[float] = None,
    weights: Optional[Tuple[float, float]] = None
) -> MatchResult:
    """
    2D目标检测匹配函数（用于距离-多普勒或方位-俯仰维匹配）
    
    :param target_positions: 真实目标位置 (N_targets, 2) - [距离, 多普勒] 或 [方位, 俯仰]
    :param detection_positions: 检测到的目标位置 (N_detections, 2)
    :param tolerance: 匹配容差，可以是标量、数组或元组 (x_tolerance, y_tolerance)
    :param match_method: 匹配方法
    :param max_distance: 最大匹配距离
    :param weights: 各维度的权重 (weight_x, weight_y)，用于距离计算
    :return: 匹配结果对象
    """
    # 输入验证
    target_positions = np.asarray(target_positions)
    detection_positions = np.asarray(detection_positions)
    
    if target_positions.ndim != 2 or target_positions.shape[1] != 2:
        raise ValueError("目标位置必须是 (N_targets, 2) 形状")
    if detection_positions.ndim != 2 or detection_positions.shape[1] != 2:
        raise ValueError("检测位置必须是 (N_detections, 2) 形状")
    
    n_targets = len(target_positions)
    n_detections = len(detection_positions)
    
    # 处理容差参数
    if np.isscalar(tolerance):
        tolerance = np.full((n_targets, 2), tolerance)
    elif isinstance(tolerance, (list, tuple)) and len(tolerance) == 2:
        tolerance = np.tile(tolerance, (n_targets, 1))
    else:
        tolerance = np.asarray(tolerance)
        if tolerance.shape != (n_targets, 2):
            raise ValueError("容差必须是标量、长度为2的元组或 (N_targets, 2) 数组")
    
    # 处理权重
    if weights is None:
        weights = (1.0, 1.0)
    
    if max_distance is None:
        max_distance = np.inf
    
    # 空情况处理
    if n_targets == 0 and n_detections == 0:
        return MatchResult(0, 0, 0, [], [], 1.0, 1.0, 1.0)
    elif n_targets == 0:
        return MatchResult(0, n_detections, 0, [], [], 0.0, 1.0, 0.0)
    elif n_detections == 0:
        return MatchResult(0, 0, n_targets, [], [], 1.0, 0.0, 0.0)
    
    if match_method == MatchMethod.NEAREST_NEIGHBOR:
        return _nearest_neighbor_match_2d(
            target_positions, detection_positions, tolerance, max_distance, weights
        )
    elif match_method == MatchMethod.HUNGARIAN:
        return _hungarian_match_2d(
            target_positions, detection_positions, tolerance, max_distance, weights
        )
    elif match_method == MatchMethod.THRESHOLD:
        return _threshold_match_2d(
            target_positions, detection_positions, tolerance, max_distance, weights
        )
    else:
        raise ValueError(f"不支持的匹配方法: {match_method}")


def _nearest_neighbor_match_1d(
    targets: NDArray,
    detections: NDArray,
    tolerance: NDArray,
    max_distance: float
) -> MatchResult:
    """1D最近邻匹配算法"""
    n_targets = len(targets)
    n_detections = len(detections)
    
    # 计算所有目标-检测对之间的距离
    distances = np.abs(targets[:, np.newaxis] - detections)
    
    # 初始化匹配状态
    target_matched = np.zeros(n_targets, dtype=bool)
    detection_matched = np.zeros(n_detections, dtype=bool)
    matched_pairs = []
    match_distances = []
    
    # 按距离升序排序所有可能的匹配
    potential_matches = []
    for i in range(n_targets):
        for j in range(n_detections):
            dist = distances[i, j]
            if dist <= tolerance[i] and dist <= max_distance:
                potential_matches.append((dist, i, j))
    
    # 按距离排序
    potential_matches.sort(key=lambda x: x[0])
    
    # 执行最近邻匹配
    for dist, i, j in potential_matches:
        if not target_matched[i] and not detection_matched[j]:
            target_matched[i] = True
            detection_matched[j] = True
            matched_pairs.append((i, j))
            match_distances.append(dist)
    
    # 统计结果
    true_positives = len(matched_pairs)
    false_positives = n_detections - true_positives
    false_negatives = n_targets - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return MatchResult(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        matched_pairs=matched_pairs,
        match_distances=match_distances,
        precision=precision,
        recall=recall,
        f1_score=f1_score
    )


def _hungarian_match_1d(
    targets: NDArray,
    detections: NDArray,
    tolerance: NDArray,
    max_distance: float
) -> MatchResult:
    """1D匈牙利算法匹配（最优分配）"""
    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        raise ImportError("匈牙利算法需要scipy.optimize.linear_sum_assignment")
    
    n_targets = len(targets)
    n_detections = len(detections)
    
    # 创建代价矩阵
    cost_matrix = np.full((n_targets, n_detections), np.inf)
    
    for i in range(n_targets):
        for j in range(n_detections):
            dist = np.abs(targets[i] - detections[j])
            if dist <= tolerance[i] and dist <= max_distance:
                cost_matrix[i, j] = dist  # 使用距离作为代价
    
    # 匈牙利算法寻找最优匹配
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # 收集匹配结果
    matched_pairs = []
    match_distances = []
    
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] < np.inf:  # 有效的匹配
            matched_pairs.append((i, j))
            match_distances.append(cost_matrix[i, j])
    
    true_positives = len(matched_pairs)
    false_positives = n_detections - true_positives
    false_negatives = n_targets - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return MatchResult(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        matched_pairs=matched_pairs,
        match_distances=match_distances,
        precision=precision,
        recall=recall,
        f1_score=f1_score
    )


def _threshold_match_1d(
    targets: NDArray,
    detections: NDArray,
    tolerance: NDArray,
    max_distance: float
) -> MatchResult:
    """1D阈值匹配算法"""
    n_targets = len(targets)
    n_detections = len(detections)
    
    target_matched = np.zeros(n_targets, dtype=bool)
    detection_matched = np.zeros(n_detections, dtype=bool)
    matched_pairs = []
    match_distances = []
    
    # 为每个目标找到在容差范围内的所有检测
    for i in range(n_targets):
        valid_detections = []
        for j in range(n_detections):
            if not detection_matched[j]:
                dist = np.abs(targets[i] - detections[j])
                if dist <= tolerance[i] and dist <= max_distance:
                    valid_detections.append((dist, j))
        
        if valid_detections:
            # 选择最近的检测
            valid_detections.sort(key=lambda x: x[0])
            dist, best_j = valid_detections[0]
            target_matched[i] = True
            detection_matched[best_j] = True
            matched_pairs.append((i, best_j))
            match_distances.append(dist)
    
    true_positives = len(matched_pairs)
    false_positives = n_detections - true_positives
    false_negatives = n_targets - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return MatchResult(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        matched_pairs=matched_pairs,
        match_distances=match_distances,
        precision=precision,
        recall=recall,
        f1_score=f1_score
    )


def _nearest_neighbor_match_2d(
    targets: NDArray,
    detections: NDArray,
    tolerance: NDArray,
    max_distance: float,
    weights: Tuple[float, float]
) -> MatchResult:
    """2D最近邻匹配算法"""
    n_targets = len(targets)
    n_detections = len(detections)
    
    # 计算加权欧氏距离
    weighted_targets = targets * np.array(weights)
    weighted_detections = detections * np.array(weights)
    
    # 计算所有对之间的距离
    distances = cdist(weighted_targets, weighted_detections)
    
    # 应用容差约束
    valid_mask = np.zeros_like(distances, dtype=bool)
    for i in range(n_targets):
        # 计算每个目标的曼哈顿距离容差
        diff = np.abs(targets[i] - detections)
        within_tolerance = (diff[:, 0] <= tolerance[i, 0]) & (diff[:, 1] <= tolerance[i, 1])
        valid_mask[i] = within_tolerance & (distances[i] <= max_distance)
    
    # 初始化匹配状态
    target_matched = np.zeros(n_targets, dtype=bool)
    detection_matched = np.zeros(n_detections, dtype=bool)
    matched_pairs = []
    match_distances = []
    
    # 收集所有有效匹配并按距离排序
    potential_matches = []
    for i in range(n_targets):
        for j in range(n_detections):
            if valid_mask[i, j]:
                potential_matches.append((distances[i, j], i, j))
    
    potential_matches.sort(key=lambda x: x[0])
    
    # 执行匹配
    for dist, i, j in potential_matches:
        if not target_matched[i] and not detection_matched[j]:
            target_matched[i] = True
            detection_matched[j] = True
            matched_pairs.append((i, j))
            match_distances.append(dist)
    
    # 统计结果
    true_positives = len(matched_pairs)
    false_positives = n_detections - true_positives
    false_negatives = n_targets - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return MatchResult(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        matched_pairs=matched_pairs,
        match_distances=match_distances,
        precision=precision,
        recall=recall,
        f1_score=f1_score
    )


def _hungarian_match_2d(
    targets: NDArray,
    detections: NDArray,
    tolerance: NDArray,
    max_distance: float,
    weights: Tuple[float, float]
) -> MatchResult:
    """2D匈牙利算法匹配"""
    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        raise ImportError("匈牙利算法需要scipy.optimize.linear_sum_assignment")
    
    n_targets = len(targets)
    n_detections = len(detections)
    
    # 计算加权距离矩阵
    weighted_targets = targets * np.array(weights)
    weighted_detections = detections * np.array(weights)
    distance_matrix = cdist(weighted_targets, weighted_detections)
    
    # 创建代价矩阵，无效匹配设为极大值
    cost_matrix = np.full_like(distance_matrix, np.inf)
    
    for i in range(n_targets):
        for j in range(n_detections):
            # 检查是否在容差范围内
            diff = np.abs(targets[i] - detections[j])
            if (diff[0] <= tolerance[i, 0] and 
                diff[1] <= tolerance[i, 1] and 
                distance_matrix[i, j] <= max_distance):
                cost_matrix[i, j] = distance_matrix[i, j]
    
    # 匈牙利算法
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    matched_pairs = []
    match_distances = []
    
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] < np.inf:
            matched_pairs.append((i, j))
            match_distances.append(cost_matrix[i, j])
    
    true_positives = len(matched_pairs)
    false_positives = n_detections - true_positives
    false_negatives = n_targets - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return MatchResult(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        matched_pairs=matched_pairs,
        match_distances=match_distances,
        precision=precision,
        recall=recall,
        f1_score=f1_score
    )


def _threshold_match_2d(
    targets: NDArray,
    detections: NDArray,
    tolerance: NDArray,
    max_distance: float,
    weights: Tuple[float, float]
) -> MatchResult:
    """2D阈值匹配算法"""
    n_targets = len(targets)
    n_detections = len(detections)
    
    target_matched = np.zeros(n_targets, dtype=bool)
    detection_matched = np.zeros(n_detections, dtype=bool)
    matched_pairs = []
    match_distances = []
    
    # 计算加权距离
    weighted_targets = targets * np.array(weights)
    weighted_detections = detections * np.array(weights)
    
    for i in range(n_targets):
        # 找到在容差范围内的所有检测
        valid_indices = []
        for j in range(n_detections):
            if not detection_matched[j]:
                # 检查各维度容差
                diff = np.abs(targets[i] - detections[j])
                if (diff[0] <= tolerance[i, 0] and 
                    diff[1] <= tolerance[i, 1]):
                    dist = np.linalg.norm(weighted_targets[i] - weighted_detections[j])
                    if dist <= max_distance:
                        valid_indices.append((dist, j))
        
        if valid_indices:
            # 选择最近的检测
            valid_indices.sort(key=lambda x: x[0])
            dist, best_j = valid_indices[0]
            target_matched[i] = True
            detection_matched[best_j] = True
            matched_pairs.append((i, best_j))
            match_distances.append(dist)
    
    true_positives = len(matched_pairs)
    false_positives = n_detections - true_positives
    false_negatives = n_targets - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return MatchResult(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        matched_pairs=matched_pairs,
        match_distances=match_distances,
        precision=precision,
        recall=recall,
        f1_score=f1_score
    )


# 雷达专用的匹配函数
def match_radar_detections(
    true_targets: Dict[str, NDArray],
    detected_targets: Dict[str, NDArray],
    range_tolerance: float = 2.0,  # 距离单元数
    doppler_tolerance: float = 2.0,  # 多普勒单元数
    match_method: MatchMethod = MatchMethod.NEAREST_NEIGHBOR
) -> MatchResult:
    """
    雷达专用目标匹配函数
    
    :param true_targets: 真实目标字典，包含'range'和'doppler'键
    :param detected_targets: 检测目标字典，包含'range'和'doppler'键  
    :param range_tolerance: 距离容差（单元数）
    :param doppler_tolerance: 多普勒容差（单元数）
    :param match_method: 匹配方法
    :return: 匹配结果
    """
    # 提取位置信息
    true_ranges = true_targets.get('range', np.array([]))
    true_dopplers = true_targets.get('doppler', np.array([]))
    det_ranges = detected_targets.get('range', np.array([]))
    det_dopplers = detected_targets.get('doppler', np.array([]))
    
    # 确保数组形状正确
    if true_ranges.size > 0 and true_dopplers.size > 0:
        true_positions = np.column_stack([true_ranges, true_dopplers])
    else:
        true_positions = np.empty((0, 2))
    
    if det_ranges.size > 0 and det_dopplers.size > 0:
        det_positions = np.column_stack([det_ranges, det_dopplers])
    else:
        det_positions = np.empty((0, 2))
    
    # 执行2D匹配
    tolerance = (range_tolerance, doppler_tolerance)
    
    return _match_target_to_detection_2d(
        true_positions, det_positions, tolerance, match_method
    )


# 使用示例
if __name__ == "__main__":
    # 示例1: 1D匹配（距离维）
    print("=== 1D匹配示例 ===")
    true_ranges = np.array([10, 25, 40, 55])  # 真实目标距离单元
    detected_ranges = np.array([9, 26, 41, 56, 70])  # 检测到的距离单元（包含一个虚警）
    
    result_1d = _match_target_to_detection_1d(
        true_ranges, detected_ranges, tolerance=2.0
    )
    
    print(f"正确检测: {result_1d.true_positives}")
    print(f"虚警: {result_1d.false_positives}")
    print(f"漏检: {result_1d.false_negatives}")
    print(f"精确率: {result_1d.precision:.3f}")
    print(f"召回率: {result_1d.recall:.3f}")
    
    print(f"F1分数: {result_1d.f1_score:.3f}")
    print("匹配对:", result_1d.matched_pairs)
    
    # 示例2: 2D匹配（距离-多普勒维）
    print("\n=== 2D匹配示例 ===")
    # 真实目标：[距离单元, 多普勒单元]
    true_targets_2d = np.array([
        [10, 5],
        [25, 8], 
        [40, 3],
        [55, 6]
    ])
    
    # 检测目标：[距离单元, 多普勒单元]（包含一个虚警）
    detected_targets_2d = np.array([
        [9, 5],
        [26, 7],
        [41, 3],
        [56, 6],
        [70, 2]  # 虚警
    ])
    
    result_2d = _match_target_to_detection_2d(
        true_targets_2d, 
        detected_targets_2d, 
        tolerance=(2.0, 2.0),  # 距离容差2单元，多普勒容差2单元
        match_method=MatchMethod.HUNGARIAN
    )
    
    print(f"正确检测: {result_2d.true_positives}")
    print(f"虚警: {result_2d.false_positives}")
    print(f"漏检: {result_2d.false_negatives}")
    print(f"精确率: {result_2d.precision:.3f}")
    print(f"召回率: {result_2d.recall:.3f}")
    print(f"F1分数: {result_2d.f1_score:.3f}")
    print("匹配对:", result_2d.matched_pairs)
    
    # 示例3: 雷达专用匹配
    print("\n=== 雷达专用匹配示例 ===")
    true_targets_dict = {
        'range': np.array([10, 25, 40, 55]),
        'doppler': np.array([5, 8, 3, 6])
    }
    
    detected_targets_dict = {
        'range': np.array([9, 26, 41, 56, 70]),
        'doppler': np.array([5, 7, 3, 6, 2])
    }
    
    radar_result = match_radar_detections(
        true_targets_dict, 
        detected_targets_dict,
        range_tolerance=2.0,
        doppler_tolerance=2.0
    )
    
    print(f"雷达匹配 - 正确检测: {radar_result.true_positives}")
    print(f"雷达匹配 - 精确率: {radar_result.precision:.3f}")
    print(f"雷达匹配 - 召回率: {radar_result.recall:.3f}")    