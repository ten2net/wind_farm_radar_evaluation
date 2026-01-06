import numpy as np
from scipy.signal import convolve
from typing import Union, List, Optional, Tuple
from numpy.typing import NDArray
from radarsimpy.tools import roc_pd, roc_snr, threshold

class CFARProcessor:
    """
    CFAR处理器类，集成tools.py中的检测概率函数
    """
    
    def __init__(self, detector_type: str = "squarelaw"):
        """
        初始化CFAR处理器
        
        :param detector_type: 检测器类型，"linear"或"squarelaw"
        """
        self.detector_type = detector_type
        self.valid_detectors = ["linear", "squarelaw"]
        
        if detector_type not in self.valid_detectors:
            raise ValueError(f"检测器类型必须是 {self.valid_detectors} 之一")
    
    def calculate_threshold_factor(self, n: int, pfa: float) -> float:
        """
        使用tools.py中的threshold函数计算CFAR门限因子
        
        :param n: 参考单元数量
        :param pfa: 虚警概率
        :return: 门限乘子
        """
        if self.detector_type == "squarelaw":
            # 对于平方律检测器，直接使用threshold函数
            thresh = threshold(pfa, n) # type: ignore
            return thresh
        else:
            # 对于线性检测器，需要转换
            thresh = threshold(pfa, n) # type: ignore
            return np.sqrt(thresh)
    
    def cfar_ca_1d(
        self,
        data: NDArray,
        guard: int,
        trailing: int,
        pfa: float = 1e-5,
        axis: int = 0,
        offset: Optional[float] = None
    ) -> NDArray:
        """
        重构的1-D Cell Averaging CFAR (CA-CFAR)
        
        :param data: 幅度/功率数据
        :param guard: 一侧保护单元数
        :param trailing: 一侧参考单元数
        :param pfa: 虚警概率
        :param axis: 计算轴
        :param offset: 手动指定的门限偏移
        :return: CFAR门限
        """
        if np.iscomplexobj(data):
            raise ValueError("输入数据不应为复数")
        
        data_shape = np.shape(data)
        cfar_threshold = np.zeros_like(data)
        
        # 计算门限因子
        if offset is None:
            n_trailing = trailing * 2  # 总参考单元数
            alpha = self.calculate_threshold_factor(n_trailing, pfa)
        else:
            alpha = offset
        
        # 创建CFAR窗口
        cfar_win = np.ones((guard + trailing) * 2 + 1)
        cfar_win[trailing:(trailing + guard * 2 + 1)] = 0
        cfar_win = cfar_win / np.sum(cfar_win)
        
        if axis == 0:
            if data.ndim == 1:
                cfar_threshold = alpha * convolve(data, cfar_win, mode="same")
            elif data.ndim == 2:
                for idx in range(data_shape[1]):
                    cfar_threshold[:, idx] = alpha * convolve(data[:, idx], cfar_win, mode="same")
        elif axis == 1:
            for idx in range(data_shape[0]):
                cfar_threshold[idx, :] = alpha * convolve(data[idx, :], cfar_win, mode="same")
        
        return cfar_threshold
    
    def cfar_ca_2d(
        self,
        data: NDArray,
        guard: Union[int, List[int]],
        trailing: Union[int, List[int]],
        pfa: float = 1e-5,
        offset: Optional[float] = None
    ) -> NDArray:
        """
        重构的2-D Cell Averaging CFAR (CA-CFAR)
        
        :param data: 幅度/功率数据
        :param guard: 保护单元数（可分别指定两个维度）
        :param trailing: 参考单元数（可分别指定两个维度）
        :param pfa: 虚警概率
        :param offset: 手动指定的门限偏移
        :return: CFAR门限
        """
        if np.iscomplexobj(data):
            raise ValueError("输入数据不应为复数")
        
        guard = np.array(guard) # type: ignore
        if guard.size == 1: # type: ignore
            guard = np.tile(guard, 2) # type: ignore
        trailing = np.array(trailing) # type: ignore
        if trailing.size == 1: # type: ignore
            trailing = np.tile(trailing, 2) # type: ignore
        
        # 计算总参考单元数
        tg_sum = trailing + guard # type: ignore
        t_num = (2 * tg_sum[0] + 1) * (2 * tg_sum[1] + 1) # type: ignore
        g_num = (2 * guard[0] + 1) * (2 * guard[1] + 1) # type: ignore
        
        if t_num == g_num:
            raise ValueError("没有参考单元！")
        
        # 计算门限因子
        if offset is None:
            n_effective = t_num - g_num
            alpha = self.calculate_threshold_factor(n_effective, pfa)
        else:
            alpha = offset
        
        # 创建2D CFAR窗口
        cfar_win = np.ones(((guard + trailing) * 2 + 1)) # type: ignore
        cfar_win[
            trailing[0]:(trailing[0] + guard[0] * 2 + 1), # type: ignore
            trailing[1]:(trailing[1] + guard[1] * 2 + 1), # type: ignore
        ] = 0
        cfar_win = cfar_win / np.sum(cfar_win)
        
        return alpha * convolve(data, cfar_win, mode="same")
    
    def calculate_detection_performance(
        self,
        snr_db: float,
        pfa: float,
        npulses: int = 1,
        target_type: str = "Swerling 0"
    ) -> float:
        """
        使用tools.py计算检测性能
        
        :param snr_db: 信噪比(dB)
        :param pfa: 虚警概率
        :param npulses: 脉冲积累数
        :param target_type: 目标类型
        :return: 检测概率
        """
        valid_target_types = [
            "Coherent", "Real", "Swerling 0", "Swerling 1", 
            "Swerling 2", "Swerling 3", "Swerling 4", "Swerling 5"
        ]
        
        if target_type not in valid_target_types:
            raise ValueError(f"目标类型必须是 {valid_target_types} 之一")
        
        return roc_pd(pfa, snr_db, npulses, target_type) # type: ignore
    
    def calculate_required_snr(
        self,
        pd: float,
        pfa: float,
        npulses: int = 1,
        target_type: str = "Swerling 0"
    ) -> float:
        """
        使用tools.py计算所需的最小信噪比
        
        :param pd: 检测概率
        :param pfa: 虚警概率
        :param npulses: 脉冲积累数
        :param target_type: 目标类型
        :return: 所需最小信噪比(dB)
        """
        valid_target_types = [
            "Coherent", "Real", "Swerling 0", "Swerling 1",
            "Swerling 2", "Swerling 3", "Swerling 4", "Swerling 5"
        ]
        
        if target_type not in valid_target_types:
            raise ValueError(f"目标类型必须是 {valid_target_types} 之一")
        
        return roc_snr(pfa, pd, npulses, target_type) # type: ignore
    
    def adaptive_cfar_detection(
        self,
        data: NDArray,
        guard: int,
        trailing: int,
        pfa: float = 1e-5,
        min_snr: float = 10.0,
        target_type: str = "Swerling 0"
    ) -> Tuple[NDArray, NDArray, dict]:
        """
        自适应CFAR检测，结合检测性能分析
        
        :param data: 输入数据
        :param guard: 保护单元数
        :param trailing: 参考单元数
        :param pfa: 虚警概率
        :param min_snr: 最小可检测信噪比(dB)
        :param target_type: 目标类型
        :return: (检测结果, CFAR门限, 性能统计)
        """
        # 计算CFAR门限
        cfar_threshold = self.cfar_ca_1d(data, guard, trailing, pfa)
        
        # 执行检测
        detections = data > cfar_threshold
        
        # 性能分析
        performance_stats = self.analyze_detection_performance(
            data, cfar_threshold, detections, min_snr, pfa, target_type
        )
        
        return detections, cfar_threshold, performance_stats
    
    def analyze_detection_performance(
        self,
        data: NDArray,
        threshold: NDArray,
        detections: NDArray,
        min_snr: float,
        pfa: float,
        target_type: str
    ) -> dict:
        """
        分析检测性能
        
        :param data: 原始数据
        :param threshold: CFAR门限
        :param detections: 检测结果
        :param min_snr: 最小可检测信噪比
        :param pfa: 虚警概率
        :param target_type: 目标类型
        :return: 性能统计字典
        """
        # 计算检测点的信噪比
        detection_indices = np.where(detections)
        snr_estimates = []
        
        for idx in zip(*detection_indices):
            signal_power = data[idx]
            # 估计噪声功率（使用周围参考单元）
            noise_estimate = self.estimate_local_noise(data, idx, 5)  # 5x5窗口
            if noise_estimate > 0:
                snr_db = 10 * np.log10(signal_power / noise_estimate)
                snr_estimates.append(snr_db)
        
        stats = {
            'num_detections': np.sum(detections),
            'max_snr': np.max(snr_estimates) if snr_estimates else 0,
            'min_snr': np.min(snr_estimates) if snr_estimates else 0,
            'mean_snr': np.mean(snr_estimates) if snr_estimates else 0,
            'snr_estimates': np.array(snr_estimates)
        }
        
        # 计算预期检测概率
        if snr_estimates:
            avg_snr = stats['mean_snr']
            expected_pd = self.calculate_detection_performance(
                avg_snr, pfa, 1, target_type
            )
            stats['expected_pd'] = expected_pd
        else:
            stats['expected_pd'] = 0
        
        return stats
    
    def estimate_local_noise(
        self,
        data: NDArray,
        center_index: tuple,
        window_size: int
    ) -> float:
        """
        估计局部噪声功率
        
        :param data: 输入数据
        :param center_index: 中心点索引
        :param window_size: 估计窗口大小
        :return: 噪声功率估计
        """
        half_window = window_size // 2
        rows, cols = data.shape
        
        # 计算窗口边界
        row_start = max(0, center_index[0] - half_window)
        row_end = min(rows, center_index[0] + half_window + 1)
        col_start = max(0, center_index[1] - half_window)
        col_end = min(cols, center_index[1] + half_window + 1)
        
        # 排除中心点附近的区域
        noise_region = data[row_start:row_end, col_start:col_end]
        
        # 排除中心3x3区域
        center_row_start = max(0, center_index[0] - 1)
        center_row_end = min(rows, center_index[0] + 2)
        center_col_start = max(0, center_index[1] - 1)
        center_col_end = min(cols, center_index[1] + 2)
        
        # 创建掩码排除中心区域
        mask = np.ones(noise_region.shape, dtype=bool)
        local_center_row_start = center_row_start - row_start
        local_center_row_end = center_row_end - row_start
        local_center_col_start = center_col_start - col_start
        local_center_col_end = center_col_end - col_start
        
        mask[local_center_row_start:local_center_row_end, 
             local_center_col_start:local_center_col_end] = False
        
        noise_samples = noise_region[mask]
        
        if len(noise_samples) > 0:
            return np.mean(noise_samples) # type: ignore
        else:
            return np.mean(data)  # type: ignore # 回退到全局平均


# 兼容原有函数接口的包装函数
def cfar_ca_1d(
    data: NDArray,
    guard: int,
    trailing: int,
    pfa: float = 1e-5,
    axis: int = 0,
    detector: str = "squarelaw",
    offset: Optional[float] = None
) -> NDArray:
    """
    兼容原有接口的1D CA-CFAR函数
    """
    processor = CFARProcessor(detector)
    return processor.cfar_ca_1d(data, guard, trailing, pfa, axis, offset)


def cfar_ca_2d(
    data: NDArray,
    guard: Union[int, List[int]],
    trailing: Union[int, List[int]],
    pfa: float = 1e-5,
    detector: str = "squarelaw",
    offset: Optional[float] = None
) -> NDArray:
    """
    兼容原有接口的2D CA-CFAR函数
    """
    processor = CFARProcessor(detector)
    return processor.cfar_ca_2d(data, guard, trailing, pfa, offset)


# 示例使用代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    data = np.random.rand(100, 50)  # 模拟雷达数据
    
    # 使用重构的CFAR处理器
    cfar_processor = CFARProcessor("squarelaw")
    
    # 执行CFAR检测
    detections, threshold, stats = cfar_processor.adaptive_cfar_detection(
        data, guard=2, trailing=10, pfa=1e-6, min_snr=10.0
    )
    
    print(f"检测到目标数量: {stats['num_detections']}")
    print(f"平均信噪比: {stats['mean_snr']:.2f} dB")
    print(f"预期检测概率: {stats['expected_pd']:.4f}")
    
    # 计算特定场景下的检测性能
    pd = cfar_processor.calculate_detection_performance(
        snr_db=15.0, pfa=1e-6, npulses=10, target_type="Swerling 1"
    )
    print(f"SNR=15dB, Pfa=1e-6, 10个脉冲积累的检测概率: {pd:.4f}")
    
    # 计算所需信噪比
    required_snr = cfar_processor.calculate_required_snr(
        pd=0.9, pfa=1e-6, npulses=10, target_type="Swerling 1"
    )
    print(f"达到Pd=0.9, Pfa=1e-6所需的最小信噪比: {required_snr:.2f} dB")