"""
验证器模块
提供各种数据验证功能
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
import re
from datetime import datetime, date
from pathlib import Path

class Validator:
    """验证器基类"""
    
    def __init__(self, required: bool = False, 
                 error_message: Optional[str] = None):
        """
        初始化验证器
        
        Args:
            required: 是否必填
            error_message: 自定义错误消息
        """
        self.required = required
        self.error_message = error_message
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        验证值
        
        Args:
            value: 要验证的值
        
        Returns:
            (是否有效, 错误消息)
        """
        raise NotImplementedError("子类必须实现此方法")

class RequiredValidator(Validator):
    """必填验证器"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(required=True, error_message=error_message)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None or (isinstance(value, str) and not value.strip()):
            msg = self.error_message or "此字段为必填项"
            return False, msg
        return True, None

class RangeValidator(Validator):
    """范围验证器"""
    
    def __init__(self, min_val: Optional[float] = None, 
                 max_val: Optional[float] = None,
                 error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
        self.min_val = min_val
        self.max_val = max_val
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        try:
            num = float(value)
            
            if self.min_val is not None and num < self.min_val:
                msg = self.error_message or f"值不能小于 {self.min_val}"
                return False, msg
            
            if self.max_val is not None and num > self.max_val:
                msg = self.error_message or f"值不能大于 {self.max_val}"
                return False, msg
            
            return True, None
            
        except (ValueError, TypeError):
            msg = self.error_message or "无效的数值"
            return False, msg

class LengthValidator(Validator):
    """长度验证器"""
    
    def __init__(self, min_len: Optional[int] = None, 
                 max_len: Optional[int] = None,
                 error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
        self.min_len = min_len
        self.max_len = max_len
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None:
            value = ""
        
        str_value = str(value)
        length = len(str_value)
        
        if self.min_len is not None and length < self.min_len:
            msg = self.error_message or f"长度不能小于 {self.min_len} 个字符"
            return False, msg
        
        if self.max_len is not None and length > self.max_len:
            msg = self.error_message or f"长度不能大于 {self.max_len} 个字符"
            return False, msg
        
        return True, None

class RegexValidator(Validator):
    """正则表达式验证器"""
    
    def __init__(self, pattern: str, 
                 error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
        self.pattern = pattern
        self.regex = re.compile(pattern)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None:
            value = ""
        
        str_value = str(value)
        
        if not self.regex.match(str_value):
            msg = self.error_message or f"格式不符合要求"
            return False, msg
        
        return True, None

class EmailValidator(Validator):
    """邮箱验证器"""
    
    def __init__(self, error_message: Optional[str] = None):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        super().__init__(error_message=error_message)
        self.regex = re.compile(pattern)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None or not value:
            return True, None  # 空值视为有效（如果需要必填，应配合RequiredValidator使用）
        
        str_value = str(value).strip()
        
        if not self.regex.match(str_value):
            msg = self.error_message or "邮箱格式不正确"
            return False, msg
        
        return True, None

class URLValidator(Validator):
    """URL验证器"""
    
    def __init__(self, error_message: Optional[str] = None):
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        super().__init__(error_message=error_message)
        self.regex = re.compile(pattern)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None or not value:
            return True, None
        
        str_value = str(value).strip()
        
        if not self.regex.match(str_value):
            msg = self.error_message or "URL格式不正确"
            return False, msg
        
        return True, None

class DateValidator(Validator):
    """日期验证器"""
    
    def __init__(self, format: str = "%Y-%m-%d",
                 min_date: Optional[date] = None,
                 max_date: Optional[date] = None,
                 error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
        self.format = format
        self.min_date = min_date
        self.max_date = max_date
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None or not value:
            return True, None
        
        if isinstance(value, date):
            date_obj = value
        elif isinstance(value, datetime):
            date_obj = value.date()
        else:
            try:
                date_obj = datetime.strptime(str(value), self.format).date()
            except ValueError:
                msg = self.error_message or f"日期格式不正确，应为 {self.format}"
                return False, msg
        
        if self.min_date is not None and date_obj < self.min_date:
            msg = self.error_message or f"日期不能早于 {self.min_date}"
            return False, msg
        
        if self.max_date is not None and date_obj > self.max_date:
            msg = self.error_message or f"日期不能晚于 {self.max_date}"
            return False, msg
        
        return True, None

class FileValidator(Validator):
    """文件验证器"""
    
    def __init__(self, allowed_extensions: Optional[List[str]] = None,
                 max_size_mb: Optional[float] = None,
                 error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
        self.allowed_extensions = allowed_extensions
        self.max_size_mb = max_size_mb
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None:
            return True, None
        
        # 检查文件路径
        if isinstance(value, (str, Path)):
            filepath = Path(value)
            
            if not filepath.exists():
                msg = self.error_message or "文件不存在"
                return False, msg
            
            # 检查扩展名
            if self.allowed_extensions:
                ext = filepath.suffix.lower()
                if ext not in self.allowed_extensions:
                    msg = self.error_message or f"不支持的文件类型。支持的类型: {', '.join(self.allowed_extensions)}"
                    return False, msg
            
            # 检查文件大小
            if self.max_size_mb:
                file_size_mb = filepath.stat().st_size / (1024 * 1024)
                if file_size_mb > self.max_size_mb:
                    msg = self.error_message or f"文件大小不能超过 {self.max_size_mb} MB"
                    return False, msg
        
        return True, None

class ChoiceValidator(Validator):
    """选择验证器"""
    
    def __init__(self, choices: List[Any],
                 error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
        self.choices = choices
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None:
            return True, None
        
        if value not in self.choices:
            msg = self.error_message or f"无效的选择。有效选项: {', '.join(map(str, self.choices))}"
            return False, msg
        
        return True, None

class ArrayValidator(Validator):
    """数组验证器"""
    
    def __init__(self, min_length: Optional[int] = None,
                 max_length: Optional[int] = None,
                 element_validator: Optional[Validator] = None,
                 error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
        self.min_length = min_length
        self.max_length = max_length
        self.element_validator = element_validator
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None:
            return True, None
        
        if not isinstance(value, (list, tuple, np.ndarray)):
            msg = self.error_message or "必须是一个数组"
            return False, msg
        
        arr = list(value)
        length = len(arr)
        
        if self.min_length is not None and length < self.min_length:
            msg = self.error_message or f"数组长度不能小于 {self.min_length}"
            return False, msg
        
        if self.max_length is not None and length > self.max_length:
            msg = self.error_message or f"数组长度不能大于 {self.max_length}"
            return False, msg
        
        # 验证数组元素
        if self.element_validator:
            for i, element in enumerate(arr):
                is_valid, error_msg = self.element_validator.validate(element)
                if not is_valid:
                    msg = f"元素 {i}: {error_msg}"
                    return False, msg
        
        return True, None

class ComplexValidator(Validator):
    """复数验证器"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None:
            return True, None
        
        try:
            complex(value)
            return True, None
        except (ValueError, TypeError):
            msg = self.error_message or "无效的复数"
            return False, msg

class AntennaParameterValidator(Validator):
    """天线参数验证器"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(error_message=error_message)
    
    def validate(self, value: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not isinstance(value, dict):
            msg = self.error_message or "天线参数必须是字典"
            return False, msg
        
        # 检查必要字段
        required_fields = ['name', 'antenna_type', 'center_frequency']
        for field in required_fields:
            if field not in value:
                msg = self.error_message or f"缺少必要字段: {field}"
                return False, msg
        
        # 验证频率
        freq = value.get('center_frequency')
        if not isinstance(freq, (int, float)) or freq <= 0:
            msg = self.error_message or "中心频率必须是正数"
            return False, msg
        
        # 验证增益
        gain = value.get('gain', 0)
        if not isinstance(gain, (int, float)):
            msg = self.error_message or "增益必须是数字"
            return False, msg
        
        return True, None

def validate_form(data: Dict[str, Any], 
                 validators: Dict[str, List[Validator]]) -> Dict[str, List[str]]:
    """
    验证表单数据
    
    Args:
        data: 表单数据字典
        validators: 验证器字典，键为字段名，值为验证器列表
    
    Returns:
        错误字典，键为字段名，值为错误消息列表
    """
    errors = {}
    
    for field, field_validators in validators.items():
        field_errors = []
        value = data.get(field)
        
        for validator in field_validators:
            is_valid, error_msg = validator.validate(value)
            if not is_valid:
                field_errors.append(error_msg)
        
        if field_errors:
            errors[field] = field_errors
    
    return errors

def validate_antenna_parameters(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证天线参数
    
    Args:
        params: 天线参数字典
    
    Returns:
        (是否有效, 错误消息列表)
    """
    errors = []
    
    # 定义验证器
    validators = {
        'name': [RequiredValidator("天线名称不能为空")],
        'antenna_type': [RequiredValidator("天线类型不能为空")],
        'center_frequency': [
            RequiredValidator("中心频率不能为空"),
            RangeValidator(0.001, 100, "中心频率必须在0.001-100 GHz范围内")
        ],
        'gain': [
            RangeValidator(-10, 100, "增益必须在-10到100 dBi范围内")
        ],
        'bandwidth': [
            RangeValidator(0, 200, "带宽必须在0-200%范围内")
        ],
        'vswr': [
            RangeValidator(1.0, 10.0, "VSWR必须在1.0-10.0范围内")
        ],
        'efficiency': [
            RangeValidator(0, 1, "效率必须在0-1范围内")
        ]
    }
    
    form_errors = validate_form(params, validators)
    
    for field, field_errors in form_errors.items():
        for error in field_errors:
            errors.append(f"{field}: {error}")
    
    return len(errors) == 0, errors

def validate_pattern_data(pattern_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证方向图数据
    
    Args:
        pattern_data: 方向图数据字典
    
    Returns:
        (是否有效, 错误消息列表)
    """
    errors = []
    
    required_fields = ['theta_grid', 'phi_grid', 'gain_data']
    
    for field in required_fields:
        if field not in pattern_data:
            errors.append(f"缺少必要字段: {field}")
    
    if not errors:
        # 检查数组维度
        try:
            theta_grid = np.array(pattern_data['theta_grid'])
            phi_grid = np.array(pattern_data['phi_grid'])
            gain_data = np.array(pattern_data['gain_data'])
            
            if gain_data.ndim != 2:
                errors.append("增益数据必须是二维数组")
            elif gain_data.shape[0] != len(theta_grid) or gain_data.shape[1] != len(phi_grid):
                errors.append("增益数据维度与角度网格不匹配")
            
        except Exception as e:
            errors.append(f"数据格式错误: {e}")
    
    return len(errors) == 0, errors

def validate_file_upload(file_obj: Any, 
                        allowed_types: List[str],
                        max_size_mb: float = 10) -> Tuple[bool, Optional[str]]:
    """
    验证文件上传
    
    Args:
        file_obj: 文件对象
        allowed_types: 允许的文件类型
        max_size_mb: 最大文件大小（MB）
    
    Returns:
        (是否有效, 错误消息)
    """
    if file_obj is None:
        return False, "未选择文件"
    
    # 检查文件类型
    file_name = getattr(file_obj, 'name', '')
    if not any(file_name.endswith(ext) for ext in allowed_types):
        return False, f"不支持的文件类型。支持的类型: {', '.join(allowed_types)}"
    
    # 检查文件大小
    try:
        file_size = len(file_obj.getvalue())
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            return False, f"文件大小不能超过 {max_size_mb} MB"
    
    except AttributeError:
        # 如果无法获取大小，跳过大小检查
        pass
    
    return True, None