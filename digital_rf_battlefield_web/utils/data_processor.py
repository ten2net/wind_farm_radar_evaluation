"""
数据处理工具 - 数据转换和处理
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理工具类"""
    
    @staticmethod
    def convert_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
        """将数据列表转换为DataFrame"""
        if not data:
            return pd.DataFrame()
        
        try:
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"转换数据到DataFrame失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_statistics(data: List[Dict[str, Any]], column: str) -> Dict[str, Any]:
        """计算统计信息"""
        if not data:
            return {}
        
        try:
            values = [item.get(column) for item in data if column in item]
            values = [v for v in values if v is not None]
            
            if not values:
                return {}
            
            return {
                'count': len(values),
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values)
            }
        except Exception as e:
            logger.error(f"计算统计信息失败: {e}")
            return {}
    
    @staticmethod
    def filter_data(data: List[Dict[str, Any]], 
                   filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤数据"""
        if not data or not filters:
            return data
        
        filtered_data = []
        
        for item in data:
            include = True
            
            for key, value in filters.items():
                if key in item:
                    if isinstance(value, (list, tuple)):
                        if item[key] not in value:
                            include = False
                            break
                    else:
                        if item[key] != value:
                            include = False
                            break
                else:
                    include = False
                    break
            
            if include:
                filtered_data.append(item)
        
        return filtered_data
    
    @staticmethod
    def sort_data(data: List[Dict[str, Any]], 
                 sort_by: str, 
                 descending: bool = False) -> List[Dict[str, Any]]:
        """排序数据"""
        if not data or not sort_by:
            return data
        
        try:
            return sorted(data, 
                         key=lambda x: x.get(sort_by, 0), 
                         reverse=descending)
        except Exception as e:
            logger.error(f"排序数据失败: {e}")
            return data
    
    @staticmethod
    def group_data(data: List[Dict[str, Any]], 
                  group_by: str) -> Dict[str, List[Dict[str, Any]]]:
        """按字段分组数据"""
        if not data or not group_by:
            return {}
        
        grouped = {}
        
        for item in data:
            if group_by in item:
                key = item[group_by]
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(item)
        
        return grouped
    
    @staticmethod
    def calculate_correlation(data: List[Dict[str, Any]], 
                            x_col: str, 
                            y_col: str) -> Optional[float]:
        """计算相关性"""
        if not data:
            return None
        
        try:
            x_values = []
            y_values = []
            
            for item in data:
                if x_col in item and y_col in item:
                    x_val = item[x_col]
                    y_val = item[y_col]
                    
                    if x_val is not None and y_val is not None:
                        x_values.append(float(x_val))
                        y_values.append(float(y_val))
            
            if len(x_values) < 2:
                return None
            
            correlation = np.corrcoef(x_values, y_values)[0, 1]
            return correlation
            
        except Exception as e:
            logger.error(f"计算相关性失败: {e}")
            return None
    
    @staticmethod
    def normalize_data(data: List[float], 
                      method: str = 'minmax') -> List[float]:
        """归一化数据"""
        if not data or len(data) < 2:
            return data
        
        try:
            data_array = np.array(data)
            
            if method == 'minmax':
                min_val = np.min(data_array)
                max_val = np.max(data_array)
                
                if max_val - min_val == 0:
                    return [0.0] * len(data)
                
                normalized = (data_array - min_val) / (max_val - min_val)
                return normalized.tolist()
            
            elif method == 'zscore':
                mean_val = np.mean(data_array)
                std_val = np.std(data_array)
                
                if std_val == 0:
                    return [0.0] * len(data)
                
                normalized = (data_array - mean_val) / std_val
                return normalized.tolist()
            
            else:
                return data.tolist()
                
        except Exception as e:
            logger.error(f"归一化数据失败: {e}")
            return data
    
    @staticmethod
    def calculate_percentiles(data: List[float], 
                            percentiles: List[float] = None) -> Dict[str, float]:
        """计算百分位数"""
        if not data:
            return {}
        
        if percentiles is None:
            percentiles = [25, 50, 75, 90, 95, 99]
        
        try:
            data_array = np.array(data)
            results = {}
            
            for p in percentiles:
                results[f'p{p}'] = np.percentile(data_array, p)
            
            return results
            
        except Exception as e:
            logger.error(f"计算百分位数失败: {e}")
            return {}
    
    @staticmethod
    def detect_outliers(data: List[float], 
                       method: str = 'iqr',
                       threshold: float = 1.5) -> List[int]:
        """检测异常值"""
        if not data or len(data) < 3:
            return []
        
        try:
            data_array = np.array(data)
            outliers = []
            
            if method == 'iqr':
                q1 = np.percentile(data_array, 25)
                q3 = np.percentile(data_array, 75)
                iqr = q3 - q1
                
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr
                
                for i, val in enumerate(data_array):
                    if val < lower_bound or val > upper_bound:
                        outliers.append(i)
            
            elif method == 'zscore':
                mean_val = np.mean(data_array)
                std_val = np.std(data_array)
                
                if std_val > 0:
                    for i, val in enumerate(data_array):
                        zscore = abs((val - mean_val) / std_val)
                        if zscore > threshold:
                            outliers.append(i)
            
            return outliers
            
        except Exception as e:
            logger.error(f"检测异常值失败: {e}")
            return []
    
    @staticmethod
    def aggregate_data(data: List[Dict[str, Any]], 
                      group_by: str, 
                      aggregate_col: str, 
                      operation: str = 'sum') -> Dict[str, Any]:
        """聚合数据"""
        if not data or not group_by or not aggregate_col:
            return {}
        
        try:
            grouped = DataProcessor.group_data(data, group_by)
            results = {}
            
            for key, group in grouped.items():
                values = [item.get(aggregate_col) for item in group 
                         if aggregate_col in item and item[aggregate_col] is not None]
                
                if not values:
                    continue
                
                if operation == 'sum':
                    results[key] = sum(values)
                elif operation == 'mean':
                    results[key] = np.mean(values)
                elif operation == 'median':
                    results[key] = np.median(values)
                elif operation == 'max':
                    results[key] = max(values)
                elif operation == 'min':
                    results[key] = min(values)
                elif operation == 'count':
                    results[key] = len(values)
            
            return results
            
        except Exception as e:
            logger.error(f"聚合数据失败: {e}")
            return {}
    
    @staticmethod
    def merge_data(data1: List[Dict[str, Any]], 
                  data2: List[Dict[str, Any]], 
                  on: str, 
                  how: str = 'inner') -> List[Dict[str, Any]]:
        """合并数据"""
        if not data1 or not data2 or not on:
            return []
        
        try:
            # 转换为DataFrame进行合并
            df1 = pd.DataFrame(data1)
            df2 = pd.DataFrame(data2)
            
            if on not in df1.columns or on not in df2.columns:
                return []
            
            merged_df = pd.merge(df1, df2, on=on, how=how)
            return merged_df.to_dict('records')
            
        except Exception as e:
            logger.error(f"合并数据失败: {e}")
            return []
    
    @staticmethod
    def calculate_trend(data: List[float], 
                       method: str = 'linear') -> Dict[str, Any]:
        """计算趋势"""
        if not data or len(data) < 2:
            return {}
        
        try:
            x = np.arange(len(data))
            y = np.array(data)
            
            if method == 'linear':
                coeffs = np.polyfit(x, y, 1)
                slope = coeffs[0]
                intercept = coeffs[1]
                
                return {
                    'slope': slope,
                    'intercept': intercept,
                    'trend': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                    'magnitude': abs(slope)
                }
            
            elif method == 'exponential':
                # 对数变换后线性拟合
                mask = y > 0
                if np.sum(mask) < 2:
                    return {}
                
                x_fit = x[mask]
                y_fit = np.log(y[mask])
                
                coeffs = np.polyfit(x_fit, y_fit, 1)
                slope = coeffs[0]
                
                return {
                    'growth_rate': slope,
                    'trend': 'growing' if slope > 0 else 'declining' if slope < 0 else 'stable'
                }
            
            else:
                return {}
                
        except Exception as e:
            logger.error(f"计算趋势失败: {e}")
            return {}
    
    @staticmethod
    def export_to_file(data: Any, 
                      filepath: str, 
                      format: str = 'json') -> bool:
        """导出数据到文件"""
        try:
            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format == 'csv':
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    df.to_csv(filepath, index=False, encoding='utf-8')
                elif isinstance(data, pd.DataFrame):
                    data.to_csv(filepath, index=False, encoding='utf-8')
                else:
                    logger.error("不支持的CSV数据格式")
                    return False
            
            elif format == 'excel':
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    df.to_excel(filepath, index=False)
                elif isinstance(data, pd.DataFrame):
                    data.to_excel(filepath, index=False)
                else:
                    logger.error("不支持的Excel数据格式")
                    return False
            
            else:
                logger.error(f"不支持的导出格式: {format}")
                return False
            
            logger.info(f"数据已导出到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return False
    
    @staticmethod
    def import_from_file(filepath: str, 
                        format: str = 'json') -> Any:
        """从文件导入数据"""
        try:
            if format == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif format == 'csv':
                return pd.read_csv(filepath).to_dict('records')
            
            elif format == 'excel':
                return pd.read_excel(filepath).to_dict('records')
            
            else:
                logger.error(f"不支持的导入格式: {format}")
                return None
                
        except Exception as e:
            logger.error(f"导入数据失败: {e}")
            return None
    
    @staticmethod
    def calculate_rolling_statistics(data: List[float], 
                                   window: int = 5, 
                                   statistic: str = 'mean') -> List[float]:
        """计算滚动统计量"""
        if not data or len(data) < window:
            return []
        
        try:
            data_array = np.array(data)
            results = []
            
            for i in range(len(data_array) - window + 1):
                window_data = data_array[i:i+window]
                
                if statistic == 'mean':
                    results.append(np.mean(window_data))
                elif statistic == 'median':
                    results.append(np.median(window_data))
                elif statistic == 'std':
                    results.append(np.std(window_data))
                elif statistic == 'min':
                    results.append(np.min(window_data))
                elif statistic == 'max':
                    results.append(np.max(window_data))
                else:
                    results.append(np.mean(window_data))
            
            return results
            
        except Exception as e:
            logger.error(f"计算滚动统计量失败: {e}")
            return []