"""
配置管理模块
加载和管理应用程序配置
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os
import sys

class AppConfig:
    """应用程序配置类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self.load_config()
        
    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        # 首先尝试项目根目录下的config目录
        project_root = Path(__file__).parent.parent
        config_file = project_root / "config" / "app_config.yaml"
        
        if config_file.exists():
            return config_file
        
        # 如果不存在，创建默认配置
        config_file.parent.mkdir(parents=True, exist_ok=True)
        self._create_default_config(config_file)
        
        return config_file
    
    def _create_default_config(self, config_file: Path):
        """创建默认配置文件"""
        default_config = {
            'application': {
                'name': '天线分析平台',
                'version': '1.0.0',
                'debug': False,
                'log_level': 'INFO',
                'max_file_size': 100,  # MB
                'allowed_extensions': ['.json', '.yaml', '.yml', '.csv', '.txt']
            },
            'paths': {
                'data_dir': 'data',
                'cache_dir': 'cache',
                'log_dir': 'logs',
                'export_dir': 'exports',
                'backup_dir': 'backups'
            },
            'simulation': {
                'default_frequency': 2.4,  # GHz
                'max_points': 10000,
                'default_resolution': 5,  # degrees
                'interpolation_enabled': True
            },
            'visualization': {
                'default_theme': 'plotly_white',
                'default_width': 800,
                'default_height': 600,
                'animation_enabled': True,
                'interactive_mode': True
            },
            'export': {
                'default_format': 'PNG',
                'default_dpi': 300,
                'default_quality': 90,
                'auto_open': False
            },
            'security': {
                'max_file_uploads': 10,
                'max_file_size_mb': 100,
                'enable_cors': True,
                'session_timeout': 3600  # seconds
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 确保所有必要的部分都存在
            config = self._ensure_config_structure(config)
            
            return config
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self._create_minimal_config()
    
    def _ensure_config_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """确保配置结构完整"""
        # 定义默认结构
        default_structure = {
            'application': {},
            'paths': {},
            'simulation': {},
            'visualization': {},
            'export': {},
            'security': {}
        }
        
        # 合并配置
        for section, defaults in default_structure.items():
            if section not in config:
                config[section] = defaults
        
        return config
    
    def _create_minimal_config(self) -> Dict[str, Any]:
        """创建最小化配置"""
        return {
            'application': {
                'name': '天线分析平台',
                'version': '1.0.0',
                'debug': False
            },
            'paths': {
                'data_dir': 'data',
                'cache_dir': 'cache'
            }
        }
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔键"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值，支持点分隔键"""
        keys = key.split('.')
        config = self.config
        
        # 遍历到倒数第二个键
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最后一个键的值
        config[keys[-1]] = value
    
    def update(self, updates: Dict[str, Any]):
        """批量更新配置"""
        for key, value in updates.items():
            self.set(key, value)
        
        self.save_config()
    
    @property
    def debug(self) -> bool:
        """获取调试模式状态"""
        return self.get('application.debug', False)
    
    @property
    def data_dir(self) -> Path:
        """获取数据目录路径"""
        data_dir = self.get('paths.data_dir', 'data')
        return Path(data_dir)
    
    @property
    def cache_dir(self) -> Path:
        """获取缓存目录路径"""
        cache_dir = self.get('paths.cache_dir', 'cache')
        return Path(cache_dir)
    
    @property
    def log_dir(self) -> Path:
        """获取日志目录路径"""
        log_dir = self.get('paths.log_dir', 'logs')
        return Path(log_dir)
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.data_dir,
            self.cache_dir,
            self.log_dir,
            self.data_dir / 'antennas',
            self.data_dir / 'patterns',
            self.data_dir / 'exports',
            self.data_dir / 'backups',
            self.data_dir / 'education'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> tuple[bool, list[str]]:
        """验证配置"""
        errors = []
        
        # 检查必要配置
        required_configs = [
            'application.name',
            'application.version',
            'paths.data_dir'
        ]
        
        for config_key in required_configs:
            if self.get(config_key) is None:
                errors.append(f"缺少必要配置: {config_key}")
        
        # 检查路径权限
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # 测试写入权限
            test_file = self.data_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
            
        except PermissionError:
            errors.append(f"没有写入权限: {self.data_dir}")
        
        return len(errors) == 0, errors

# 全局配置实例
_config_instance: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance

def init_config(config_path: Optional[str] = None) -> AppConfig:
    """初始化配置"""
    global _config_instance
    _config_instance = AppConfig(config_path)
    
    # 验证配置
    is_valid, errors = _config_instance.validate()
    if not is_valid:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
    
    # 创建目录
    _config_instance.create_directories()
    
    return _config_instance