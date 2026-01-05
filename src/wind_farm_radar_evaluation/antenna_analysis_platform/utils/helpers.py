"""
助手函数模块
提供各种实用工具函数
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import yaml
import base64
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import logging
import sys
import importlib
from io import BytesIO, StringIO
import math

# 日志设置
logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    设置日志配置
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为None则只输出到控制台
    """
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 设置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)
    
    # 创建文件处理器（如果需要）
    if log_file:
        try:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"创建日志文件失败: {e}")
    
    logger.info(f"日志系统已初始化，级别: {level}")

def format_frequency(freq_hz: float) -> str:
    """
    格式化频率显示
    
    Args:
        freq_hz: 频率（赫兹）
    
    Returns:
        格式化后的频率字符串
    """
    if freq_hz >= 1e9:  # GHz
        return f"{freq_hz / 1e9:.3f} GHz"
    elif freq_hz >= 1e6:  # MHz
        return f"{freq_hz / 1e6:.3f} MHz"
    elif freq_hz >= 1e3:  # kHz
        return f"{freq_hz / 1e3:.3f} kHz"
    else:  # Hz
        return f"{freq_hz:.1f} Hz"

def format_gain(gain_db: float) -> str:
    """
    格式化增益显示
    
    Args:
        gain_db: 增益（分贝）
    
    Returns:
        格式化后的增益字符串
    """
    if gain_db > 0:
        return f"+{gain_db:.2f} dB"
    else:
        return f"{gain_db:.2f} dB"

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    格式化百分比显示
    
    Args:
        value: 百分比值（0-1）
        decimals: 小数位数
    
    Returns:
        格式化后的百分比字符串
    """
    return f"{value * 100:.{decimals}f}%"

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化后的大小字符串
    """
    if size_bytes >= 1024**3:  # GB
        return f"{size_bytes / 1024**3:.2f} GB"
    elif size_bytes >= 1024**2:  # MB
        return f"{size_bytes / 1024**2:.2f} MB"
    elif size_bytes >= 1024:  # KB
        return f"{size_bytes / 1024:.2f} KB"
    else:  # B
        return f"{size_bytes} B"

def format_angle(angle_deg: float, decimals: int = 2) -> str:
    """
    格式化角度显示
    
    Args:
        angle_deg: 角度（度）
        decimals: 小数位数
    
    Returns:
        格式化后的角度字符串
    """
    return f"{angle_deg:.{decimals}f}°"

def format_timestamp(timestamp: Optional[datetime] = None, 
                    format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: 时间戳，如果为None则使用当前时间
        format_str: 时间格式字符串
    
    Returns:
        格式化后的时间字符串
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime(format_str)

def calculate_snr(signal_power: float, noise_power: float) -> float:
    """
    计算信噪比
    
    Args:
        signal_power: 信号功率（线性）
        noise_power: 噪声功率（线性）
    
    Returns:
        信噪比（分贝）
    """
    if noise_power > 0:
        snr_linear = signal_power / noise_power
        return 10 * np.log10(snr_linear)
    else:
        return float('inf')

def calculate_vswr(reflection_coefficient: float) -> float:
    """
    计算电压驻波比
    
    Args:
        reflection_coefficient: 反射系数
    
    Returns:
        电压驻波比
    """
    if reflection_coefficient < 1:
        return (1 + abs(reflection_coefficient)) / (1 - abs(reflection_coefficient))
    else:
        return float('inf')

def calculate_axial_ratio(major_axis: float, minor_axis: float) -> float:
    """
    计算轴比
    
    Args:
        major_axis: 极化椭圆长轴
        minor_axis: 极化椭圆短轴
    
    Returns:
        轴比（线性）
    """
    if minor_axis > 0:
        return major_axis / minor_axis
    else:
        return float('inf')

def calculate_efficiency(radiated_power: float, input_power: float) -> float:
    """
    计算效率
    
    Args:
        radiated_power: 辐射功率
        input_power: 输入功率
    
    Returns:
        效率（0-1）
    """
    if input_power > 0:
        return radiated_power / input_power
    else:
        return 0.0

def normalize_array(arr: np.ndarray, axis: Optional[int] = None) -> np.ndarray:
    """
    归一化数组
    
    Args:
        arr: 输入数组
        axis: 归一化轴，如果为None则全局归一化
    
    Returns:
        归一化后的数组
    """
    if axis is not None:
        max_val = np.max(arr, axis=axis, keepdims=True)
        min_val = np.min(arr, axis=axis, keepdims=True)
    else:
        max_val = np.max(arr)
        min_val = np.min(arr)
    
    # 避免除零
    range_val = max_val - min_val
    if np.any(range_val == 0):
        return np.zeros_like(arr)
    
    return (arr - min_val) / range_val

def smooth_data(data: np.ndarray, window_size: int = 5, 
               window_type: str = 'hanning') -> np.ndarray:
    """
    平滑数据
    
    Args:
        data: 输入数据
        window_size: 窗口大小
        window_type: 窗口类型 ('hanning', 'hamming', 'blackman', 'bartlett', 'flat')
    
    Returns:
        平滑后的数据
    """
    if window_size < 3:
        return data
    
    if window_type == 'flat':  # 移动平均
        w = np.ones(window_size, 'd')
    else:
        window_funcs = {
            'hanning': np.hanning,
            'hamming': np.hamming,
            'blackman': np.blackman,
            'bartlett': np.bartlett
        }
        
        if window_type not in window_funcs:
            logger.warning(f"未知窗口类型: {window_type}，使用汉宁窗")
            window_type = 'hanning'
        
        w = window_funcs[window_type](window_size)
    
    # 卷积运算
    s = np.r_[data[window_size-1:0:-1], data, data[-2:-window_size-1:-1]]
    y = np.convolve(w/w.sum(), s, mode='valid')
    
    # 调整输出长度
    offset = (window_size - 1) // 2
    return y[offset:offset+len(data)]

def interpolate_data(x: np.ndarray, y: np.ndarray, 
                    num_points: int = 100, 
                    kind: str = 'cubic') -> Tuple[np.ndarray, np.ndarray]:
    """
    插值数据
    
    Args:
        x: 原始x坐标
        y: 原始y坐标
        num_points: 插值点数
        kind: 插值类型 ('linear', 'cubic', 'quadratic')
    
    Returns:
        插值后的x和y坐标
    """
    from scipy import interpolate
    
    if len(x) < 2:
        return x, y
    
    # 创建插值函数
    if kind == 'linear':
        f = interpolate.interp1d(x, y, kind='linear', bounds_error=False, fill_value='extrapolate') # type: ignore
    elif kind == 'cubic' and len(x) >= 4:
        f = interpolate.CubicSpline(x, y)
    elif kind == 'quadratic' and len(x) >= 3:
        f = interpolate.interp1d(x, y, kind='quadratic', bounds_error=False, fill_value='extrapolate') # type: ignore
    else:
        # 回退到线性插值
        f = interpolate.interp1d(x, y, kind='linear', bounds_error=False, fill_value='extrapolate') # type: ignore
    
    # 生成插值点
    x_new = np.linspace(x[0], x[-1], num_points)
    y_new = f(x_new)
    
    return x_new, y_new

def find_peaks(data: np.ndarray, height: Optional[float] = None, 
              distance: Optional[int] = None, 
              prominence: Optional[float] = None) -> np.ndarray:
    """
    查找峰值
    
    Args:
        data: 输入数据
        height: 最小高度
        distance: 峰值间最小距离
        prominence: 最小突出度
    
    Returns:
        峰值索引数组
    """
    try:
        from scipy.signal import find_peaks
        peaks, properties = find_peaks(data, height=height, distance=distance, prominence=prominence)
        return peaks
    except ImportError:
        # 简单峰值查找算法
        peaks = []
        for i in range(1, len(data)-1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                if height is None or data[i] >= height:
                    peaks.append(i)
        
        # 应用距离限制
        if distance is not None and len(peaks) > 1:
            filtered_peaks = [peaks[0]]
            for peak in peaks[1:]:
                if peak - filtered_peaks[-1] >= distance:
                    filtered_peaks.append(peak)
            peaks = filtered_peaks
        
        return np.array(peaks)

def calculate_statistics(data: np.ndarray) -> Dict[str, float]:
    """
    计算数据统计
    
    Args:
        data: 输入数据
    
    Returns:
        统计字典
    """
    if len(data) == 0:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0,
            'q1': 0.0,
            'q3': 0.0
        }
    
    return {
        'mean': float(np.mean(data)),
        'std': float(np.std(data)),
        'min': float(np.min(data)),
        'max': float(np.max(data)),
        'median': float(np.median(data)),
        'q1': float(np.percentile(data, 25)),
        'q3': float(np.percentile(data, 75))
    }

def save_data(data: Any, filepath: Union[str, Path], 
             format: str = 'json') -> bool:
    """
    保存数据到文件
    
    Args:
        data: 要保存的数据
        filepath: 文件路径
        format: 文件格式 ('json', 'yaml', 'csv', 'npy', 'txt')
    
    Returns:
        是否成功保存
    """
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format in ['yaml', 'yml']:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        
        elif format == 'csv':
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False)
            else:
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False)
        
        elif format == 'npy':
            np.save(filepath, data)
        
        elif format == 'txt':
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        else:
            logger.error(f"不支持的格式: {format}")
            return False
        
        logger.info(f"数据已保存: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"保存数据失败: {e}")
        return False

def load_data(filepath: Union[str, Path], 
             format: Optional[str] = None) -> Any:
    """
    从文件加载数据
    
    Args:
        filepath: 文件路径
        format: 文件格式，如果为None则根据扩展名推断
    
    Returns:
        加载的数据
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.error(f"文件不存在: {filepath}")
            return None
        
        # 推断格式
        if format is None:
            ext = filepath.suffix.lower()
            if ext in ['.json']:
                format = 'json'
            elif ext in ['.yaml', '.yml']:
                format = 'yaml'
            elif ext in ['.csv']:
                format = 'csv'
            elif ext in ['.npy']:
                format = 'npy'
            elif ext in ['.txt']:
                format = 'txt'
            else:
                logger.error(f"无法推断格式: {ext}")
                return None
        
        if format == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        elif format in ['yaml', 'yml']:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        elif format == 'csv':
            return pd.read_csv(filepath)
        
        elif format == 'npy':
            return np.load(filepath, allow_pickle=True)
        
        elif format == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        else:
            logger.error(f"不支持的格式: {format}")
            return None
        
    except Exception as e:
        logger.error(f"加载数据失败: {e}")
        return None

def generate_id(prefix: str = '', length: int = 8) -> str:
    """
    生成唯一ID
    
    Args:
        prefix: ID前缀
        length: ID长度
    
    Returns:
        唯一ID字符串
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    else:
        return random_part

def check_dependencies(required_packages: List[str]) -> List[str]:
    """
    检查依赖包是否安装
    
    Args:
        required_packages: 需要的包名列表
    
    Returns:
        未安装的包名列表
    """
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def bytes_to_base64(data: bytes) -> str:
    """
    将字节数据转换为Base64字符串
    
    Args:
        data: 字节数据
    
    Returns:
        Base64字符串
    """
    return base64.b64encode(data).decode('utf-8')

def base64_to_bytes(b64_string: str) -> bytes:
    """
    将Base64字符串转换为字节数据
    
    Args:
        b64_string: Base64字符串
    
    Returns:
        字节数据
    """
    return base64.b64decode(b64_string)

def dict_to_table(data: Dict[str, Any]) -> str:
    """
    将字典转换为Markdown表格
    
    Args:
        data: 字典数据
    
    Returns:
        Markdown表格字符串
    """
    if not data:
        return ""
    
    table = "| 参数 | 值 |\n|------|-----|\n"
    for key, value in data.items():
        table += f"| {key} | {value} |\n"
    
    return table

def calculate_distance(points1: np.ndarray, points2: np.ndarray) -> np.ndarray:
    """
    计算点集之间的距离
    
    Args:
        points1: 第一个点集 (N, D)
        points2: 第二个点集 (M, D)
    
    Returns:
        距离矩阵 (N, M)
    """
    return np.sqrt(((points1[:, np.newaxis, :] - points2[np.newaxis, :, :]) ** 2).sum(axis=2))

def wrap_angle(angle_deg: float) -> float:
    """
    将角度包裹到[0, 360)范围
    
    Args:
        angle_deg: 输入角度
    
    Returns:
        包裹后的角度
    """
    return angle_deg % 360

def rad_to_deg(angle_rad: float) -> float:
    """
    弧度转角度
    
    Args:
        angle_rad: 弧度
    
    Returns:
        角度
    """
    return angle_rad * 180 / np.pi

def deg_to_rad(angle_deg: float) -> float:
    """
    角度转弧度
    
    Args:
        angle_deg: 角度
    
    Returns:
        弧度
    """
    return angle_deg * np.pi / 180

def create_progress_callback():
    """
    创建进度回调函数
    
    Returns:
        进度回调函数
    """
    progress_bar = None
    status_text = None
    
    def callback(progress: float, message: str = ""):
        nonlocal progress_bar, status_text
        
        if progress_bar is None:
            progress_bar = st.progress(0.0)
            if message:
                status_text = st.empty()
        
        progress_bar.progress(progress)
        if status_text and message:
            status_text.text(message)
    
    def cleanup():
        nonlocal progress_bar, status_text
        if progress_bar:
            progress_bar.empty()
        if status_text:
            status_text.empty()
    
    return callback, cleanup

def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
    
    Returns:
        是否有效
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL地址
    
    Returns:
        是否有效
    """
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None

def get_system_info() -> Dict[str, Any]:
    """
    获取系统信息
    
    Returns:
        系统信息字典
    """
    import platform
    import psutil
    
    return {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'ram_total': psutil.virtual_memory().total,
        'ram_available': psutil.virtual_memory().available,
        'cpu_count': psutil.cpu_count(),
        'cpu_percent': psutil.cpu_percent(interval=1)
    }

def format_duration(seconds: float) -> str:
    """
    格式化持续时间
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化后的持续时间
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法，避免除零错误
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 分母为零时的默认值
    
    Returns:
        除法结果
    """
    if denominator == 0:
        return default
    return numerator / denominator