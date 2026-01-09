"""
配置管理模块
负责加载和管理系统的所有配置文件
"""
import yaml
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
import copy

# 配置类型枚举
class ConfigType(Enum):
    """配置类型枚举"""
    RADAR_DB = "radar_database"
    SCENARIO = "scenarios"
    ENVIRONMENT = "environment"
    LOGGING = "logging"
    SYSTEM = "system"
    VISUALIZATION = "visualization"
    SIMULATION = "simulation"

@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    name: str = "ew_simulation"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 20
    max_overflow: int = 30
    echo: bool = False
    
    def connection_string(self) -> str:
        """获取数据库连接字符串"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    decode_responses: bool = True
    socket_timeout: int = 5
    
    def connection_string(self) -> str:
        """获取Redis连接字符串"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    type: str = "redis"  # redis, memory, file
    ttl: int = 3600  # 缓存时间（秒）
    max_size: int = 1000  # 最大缓存项数
    cleanup_interval: int = 300  # 清理间隔（秒）

@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # 文件日志
    file_enabled: bool = True
    file_path: str = "logs/ew_simulation.log"
    file_max_size: int = 10485760  # 10MB
    file_backup_count: int = 5
    
    # 控制台日志
    console_enabled: bool = True
    
    # 数据库日志
    database_enabled: bool = False
    database_table: str = "system_logs"
    
    def get_log_level(self) -> int:
        """获取日志级别"""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(self.level.upper(), logging.INFO)

@dataclass
class VisualizationConfig:
    """可视化配置"""
    engine: str = "matplotlib"  # matplotlib, bokeh, plotly, folium
    theme: str = "default"
    resolution: Dict[str, int] = field(default_factory=lambda: {"width": 1200, "height": 800})
    
    # 地图配置
    map_provider: str = "openstreetmap"  # openstreetmap, satellite, terrain
    map_center: List[float] = field(default_factory=lambda: [39.9, 116.4])
    map_zoom: int = 8
    map_tile_url: str = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    
    # 颜色配置
    colors: Dict[str, str] = field(default_factory=lambda: {
        "radar": "#1f77b4",
        "jammer": "#d62728",
        "target": "#2ca02c",
        "coverage": "#9467bd",
        "jamming": "#ff7f0e"
    })
    
    # 性能配置
    cache_plots: bool = True
    max_plot_cache: int = 50
    auto_refresh: bool = True
    refresh_interval: int = 1  # 秒

@dataclass
class SimulationConfig:
    """仿真配置"""
    # 性能配置
    max_entities: int = 1000
    parallel_processing: bool = True
    num_processes: int = 4
    memory_limit_mb: int = 2048
    
    # 仿真参数
    time_step: float = 0.1  # 时间步长（秒）
    default_duration: int = 300  # 默认仿真时长（秒）
    real_time_factor: float = 1.0  # 实时因子
    
    # 精度配置
    propagation_precision: int = 3  # 传播模型计算精度
    interpolation_method: str = "linear"  # 插值方法
    
    # 数据记录
    save_intermediate_results: bool = True
    result_precision: int = 4
    auto_save: bool = True
    save_interval: int = 60  # 自动保存间隔（秒）

@dataclass
class SystemConfig:
    """系统配置"""
    # 应用配置
    name: str = "电子战对抗仿真系统"
    version: str = "1.0.0"
    description: str = "专业的电子战体系对抗仿真与评估平台"
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8501
    debug: bool = False
    reload: bool = False
    
    # 安全配置
    secret_key: str = "ew-simulation-secret-key-2024"
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    # 文件上传
    max_upload_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = field(default_factory=lambda: [".json", ".yaml", ".yml", ".csv"])
    
    # 会话配置
    session_timeout: int = 1800  # 会话超时时间（秒）
    max_sessions: int = 100  # 最大并发会话数

@dataclass
class RadarDatabaseConfig:
    """雷达数据库配置"""
    # 雷达类型定义
    radar_types: Dict[str, Any] = field(default_factory=lambda: {
        "early_warning": {
            "name": "预警雷达",
            "description": "远程预警雷达，用于早期发现目标",
            "base_params": {
                "frequency": 3.0,
                "power": 200.0,
                "gain": 40.0,
                "beamwidth": 1.5,
                "range_max": 400.0,
                "altitude_max": 30000.0
            },
            "variants": [
                {
                    "id": "ew_001",
                    "name": "远程预警雷达A型",
                    "params": {
                        "frequency": 3.2,
                        "power": 250.0,
                        "range_max": 500.0
                    }
                }
            ]
        },
        "fire_control": {
            "name": "火控雷达",
            "description": "火控雷达，用于精确跟踪和制导",
            "base_params": {
                "frequency": 10.0,
                "power": 50.0,
                "gain": 45.0,
                "beamwidth": 0.5,
                "range_max": 150.0,
                "altitude_max": 20000.0
            }
        }
    })
    
    # 干扰机类型定义
    jammer_types: Dict[str, Any] = field(default_factory=lambda: {
        "standoff_jammer": {
            "name": "远距支援干扰机",
            "description": "在防区外对雷达实施干扰",
            "base_params": {
                "frequency_range": [0.5, 18.0],
                "power": 1000.0,
                "gain": 15.0,
                "beamwidth": 60.0,
                "eirp": 80.0
            }
        },
        "self_protection_jammer": {
            "name": "自卫干扰机",
            "description": "安装在平台上，用于自我保护",
            "base_params": {
                "frequency_range": [2.0, 18.0],
                "power": 200.0,
                "gain": 10.0,
                "beamwidth": 120.0,
                "eirp": 50.0
            }
        }
    })
    
    # 目标类型定义
    target_types: Dict[str, Any] = field(default_factory=lambda: {
        "aircraft": {
            "name": "飞机",
            "description": "空中目标",
            "base_params": {
                "rcs": 5.0,
                "speed": 300.0,
                "maneuverability": 5.0
            }
        },
        "missile": {
            "name": "导弹",
            "description": "导弹目标",
            "base_params": {
                "rcs": 0.1,
                "speed": 800.0,
                "maneuverability": 20.0
            }
        },
        "ship": {
            "name": "舰船",
            "description": "海上目标",
            "base_params": {
                "rcs": 5000.0,
                "speed": 15.0,
                "maneuverability": 1.0
            }
        }
    })

@dataclass
class EnvironmentConfig:
    """环境配置"""
    # 地形类型
    terrain_types: Dict[str, Any] = field(default_factory=lambda: {
        "plain": {
            "name": "平原",
            "description": "平坦地形",
            "roughness": 0.1,
            "dielectric_constant": 15.0,
            "conductivity": 0.005
        },
        "hilly": {
            "name": "丘陵",
            "description": "丘陵地形",
            "roughness": 0.3,
            "dielectric_constant": 12.0,
            "conductivity": 0.01
        },
        "mountainous": {
            "name": "山地",
            "description": "山地地形",
            "roughness": 0.8,
            "dielectric_constant": 8.0,
            "conductivity": 0.02
        },
        "urban": {
            "name": "城市",
            "description": "城市地形",
            "roughness": 0.9,
            "dielectric_constant": 5.0,
            "conductivity": 0.001
        },
        "marine": {
            "name": "海洋",
            "description": "海洋环境",
            "roughness": 0.2,
            "dielectric_constant": 80.0,
            "conductivity": 5.0
        }
    })
    
    # 大气条件
    atmosphere_conditions: Dict[str, Any] = field(default_factory=lambda: {
        "standard": {
            "name": "标准大气",
            "description": "标准大气条件",
            "temperature": 15.0,
            "pressure": 1013.25,
            "humidity": 50.0,
            "refraction_index": 1.0003
        },
        "rainy": {
            "name": "雨天",
            "description": "雨天大气条件",
            "temperature": 10.0,
            "pressure": 1010.0,
            "humidity": 95.0,
            "rain_rate": 10.0,  # mm/h
            "refraction_index": 1.0004
        },
        "foggy": {
            "name": "雾天",
            "description": "雾天大气条件",
            "temperature": 5.0,
            "pressure": 1015.0,
            "humidity": 100.0,
            "visibility": 1000.0,  # 米
            "refraction_index": 1.0005
        },
        "dusty": {
            "name": "沙尘",
            "description": "沙尘天气",
            "temperature": 25.0,
            "pressure": 1005.0,
            "humidity": 20.0,
            "dust_concentration": 0.1,  # g/m³
            "refraction_index": 1.0006
        }
    })
    
    # 传播模型参数
    propagation_models: Dict[str, Any] = field(default_factory=lambda: {
        "free_space": {
            "name": "自由空间传播",
            "description": "自由空间传播模型"
        },
        "two_ray": {
            "name": "双径传播",
            "description": "考虑地面反射的双径传播模型"
        },
        "itu_r": {
            "name": "ITU-R传播",
            "description": "ITU-R推荐的传播模型"
        }
    })

@dataclass
class ScenarioConfig:
    """想定配置"""
    # 想定类型
    scenario_types: Dict[str, Any] = field(default_factory=lambda: {
        "one_vs_one": {
            "name": "一对一对抗",
            "description": "单雷达 vs 单干扰机对抗",
            "icon": "🎯",
            "max_radars": 1,
            "max_jammers": 1,
            "max_targets": 10
        },
        "many_vs_one": {
            "name": "多对一对抗",
            "description": "多雷达协同 vs 单干扰机",
            "icon": "🛡️",
            "max_radars": 10,
            "max_jammers": 1,
            "max_targets": 20
        },
        "many_vs_many": {
            "name": "多对多对抗",
            "description": "雷达网 vs 干扰网体系对抗",
            "icon": "⚔️",
            "max_radars": 20,
            "max_jammers": 10,
            "max_targets": 50
        }
    })
    
    # 默认想定配置
    default_scenarios: Dict[str, Any] = field(default_factory=lambda: {
        "one_vs_one": {
            "radar": {
                "type": "early_warning",
                "name": "预警雷达",
                "position": {"lat": 39.9, "lon": 116.4, "alt": 50.0},
                "frequency": 3.0,
                "power": 100.0
            },
            "jammer": {
                "type": "standoff_jammer",
                "name": "远距支援干扰机",
                "position": {"lat": 40.0, "lon": 116.5, "alt": 10000.0},
                "power": 1000.0
            },
            "targets": [
                {
                    "type": "aircraft",
                    "name": "目标飞机",
                    "position": {"lat": 40.1, "lon": 116.6, "alt": 8000.0},
                    "rcs": 5.0,
                    "speed": 300.0
                }
            ]
        }
    })
    
    # 仿真参数
    simulation_params: Dict[str, Any] = field(default_factory=lambda: {
        "time_steps": 100,
        "time_step_size": 0.1,
        "output_frequency": 10,
        "random_seed": 42
    })

class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _configs = {}
    _config_paths = {
        ConfigType.RADAR_DB: "config/radar_database.yaml",
        ConfigType.SCENARIO: "config/scenarios.yaml",
        ConfigType.ENVIRONMENT: "config/environment.yaml",
        ConfigType.LOGGING: "config/logging.yaml",
        ConfigType.SYSTEM: "config/system.yaml",
        ConfigType.VISUALIZATION: "config/visualization.yaml",
        ConfigType.SIMULATION: "config/simulation.yaml"
    }
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.logger = logging.getLogger(__name__)
            self._default_configs = self._create_default_configs()
            
            # 确保配置目录存在
            self._ensure_config_dirs()
    
    def _ensure_config_dirs(self):
        """确保配置目录存在"""
        for config_path in self._config_paths.values():
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # 确保其他必要目录存在
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("static").mkdir(exist_ok=True)
        Path("static/visualizations").mkdir(exist_ok=True)
        Path("static/reports").mkdir(exist_ok=True)
        Path("static/css").mkdir(exist_ok=True)
        Path("static/js").mkdir(exist_ok=True)
    
    def _create_default_configs(self) -> Dict[ConfigType, Any]:
        """创建默认配置"""
        return {
            ConfigType.SYSTEM: SystemConfig(),
            ConfigType.LOGGING: LoggingConfig(),
            ConfigType.VISUALIZATION: VisualizationConfig(),
            ConfigType.SIMULATION: SimulationConfig(),
            ConfigType.RADAR_DB: RadarDatabaseConfig(),
            ConfigType.ENVIRONMENT: EnvironmentConfig(),
            ConfigType.SCENARIO: ScenarioConfig()
        }
    
    def load_config(self, config_type: ConfigType, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置
        
        参数:
            config_type: 配置类型
            force_reload: 是否强制重新加载
            
        返回:
            配置字典
        """
        if config_type in self._configs and not force_reload:
            return self._configs[config_type]
        
        config_path = self._config_paths.get(config_type)
        
        if not config_path or not Path(config_path).exists():
            # 使用默认配置
            default_config = self._default_configs.get(config_type)
            if default_config:
                config_dict = asdict(default_config) if hasattr(default_config, '__dataclass_fields__') else default_config
                self._configs[config_type] = config_dict
                self.logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
                return config_dict
            else:
                self.logger.error(f"没有找到配置类型: {config_type}")
                return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                elif config_path.endswith('.json'):
                    config_data = json.load(f)
                else:
                    # 尝试YAML，然后JSON
                    try:
                        f.seek(0)
                        config_data = yaml.safe_load(f)
                    except:
                        f.seek(0)
                        config_data = json.load(f)
            
            # 合并默认配置
            default_config = self._default_configs.get(config_type)
            if default_config:
                if hasattr(default_config, '__dataclass_fields__'):
                    default_dict = asdict(default_config)
                else:
                    default_dict = default_config
                
                # 深度合并配置
                merged_config = self._deep_merge(default_dict, config_data)
                self._configs[config_type] = merged_config
                return merged_config
            else:
                self._configs[config_type] = config_data
                return config_data
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {config_path}, 错误: {e}")
            
            # 返回默认配置
            default_config = self._default_configs.get(config_type)
            if default_config:
                config_dict = asdict(default_config) if hasattr(default_config, '__dataclass_fields__') else default_config
                self._configs[config_type] = config_dict
                return config_dict
            
            return {}
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并字典"""
        result = copy.deepcopy(base)
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_config(self, config_type: ConfigType, config_data: Dict[str, Any], 
                   format: str = "yaml") -> bool:
        """
        保存配置
        
        参数:
            config_type: 配置类型
            config_data: 配置数据
            format: 保存格式 (yaml/json)
            
        返回:
            是否成功
        """
        config_path = self._config_paths.get(config_type)
        if not config_path:
            self.logger.error(f"未知的配置类型: {config_type}")
            return False
        
        try:
            # 确保目录存在
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if format.lower() == "json":
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
            
            # 更新缓存
            self._configs[config_type] = config_data
            self.logger.info(f"配置保存成功: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {config_path}, 错误: {e}")
            return False
    
    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        config_dict = self.load_config(ConfigType.SYSTEM)
        return SystemConfig(**config_dict)
    
    def get_logging_config(self) -> LoggingConfig:
        """获取日志配置"""
        config_dict = self.load_config(ConfigType.LOGGING)
        return LoggingConfig(**config_dict)
    
    def get_visualization_config(self) -> VisualizationConfig:
        """获取可视化配置"""
        config_dict = self.load_config(ConfigType.VISUALIZATION)
        return VisualizationConfig(**config_dict)
    
    def get_simulation_config(self) -> SimulationConfig:
        """获取仿真配置"""
        config_dict = self.load_config(ConfigType.SIMULATION)
        return SimulationConfig(**config_dict)
    
    def get_radar_database_config(self) -> Dict[str, Any]:
        """获取雷达数据库配置"""
        return self.load_config(ConfigType.RADAR_DB)
    
    def get_environment_config(self) -> Dict[str, Any]:
        """获取环境配置"""
        return self.load_config(ConfigType.ENVIRONMENT)
    
    def get_scenario_config(self) -> Dict[str, Any]:
        """获取想定配置"""
        return self.load_config(ConfigType.SCENARIO)
    
    def get_all_configs(self) -> Dict[ConfigType, Dict[str, Any]]:
        """获取所有配置"""
        all_configs = {}
        for config_type in ConfigType:
            all_configs[config_type] = self.load_config(config_type)
        return all_configs
    
    def update_config(self, config_type: ConfigType, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        参数:
            config_type: 配置类型
            updates: 更新内容
            
        返回:
            是否成功
        """
        current_config = self.load_config(config_type)
        updated_config = self._deep_merge(current_config, updates)
        return self.save_config(config_type, updated_config)
    
    def create_default_config_files(self) -> bool:
        """创建默认配置文件"""
        try:
            for config_type, default_config in self._default_configs.items():
                config_path = self._config_paths.get(config_type)
                if config_path:
                    config_dict = asdict(default_config) if hasattr(default_config, '__dataclass_fields__') else default_config
                    self.save_config(config_type, config_dict)
            
            self.logger.info("默认配置文件创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")
            return False
    
    def validate_config(self, config_type: ConfigType) -> Dict[str, Any]:
        """
        验证配置
        
        参数:
            config_type: 配置类型
            
        返回:
            验证结果
        """
        config = self.load_config(config_type)
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 基本的配置验证
        if not config:
            validation_result["valid"] = False
            validation_result["errors"].append("配置为空")
            return validation_result
        
        # 根据配置类型进行特定验证
        if config_type == ConfigType.SYSTEM:
            if "secret_key" in config and config["secret_key"] == "ew-simulation-secret-key-2024":
                validation_result["warnings"].append("使用默认的密钥，建议在生产环境中修改")
        
        elif config_type == ConfigType.LOGGING:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config.get("level") not in valid_levels:
                validation_result["errors"].append(f"无效的日志级别: {config.get('level')}")
        
        elif config_type == ConfigType.VISUALIZATION:
            valid_engines = ["matplotlib", "bokeh", "plotly", "folium"]
            if config.get("engine") not in valid_engines:
                validation_result["errors"].append(f"无效的可视化引擎: {config.get('engine')}")
        
        elif config_type == ConfigType.SIMULATION:
            if config.get("max_entities", 0) <= 0:
                validation_result["errors"].append("max_entities 必须大于0")
            if config.get("memory_limit_mb", 0) < 100:
                validation_result["warnings"].append("内存限制过低，可能影响性能")
        
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        return validation_result

# 全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config(config_type: Union[ConfigType, str]) -> Dict[str, Any]:
    """获取配置"""
    if isinstance(config_type, str):
        try:
            config_type = ConfigType(config_type)
        except ValueError:
            raise ValueError(f"无效的配置类型: {config_type}")
    
    return config_manager.load_config(config_type)

def get_system_config() -> SystemConfig:
    """获取系统配置"""
    return config_manager.get_system_config()

def get_logging_config() -> LoggingConfig:
    """获取日志配置"""
    return config_manager.get_logging_config()

def get_visualization_config() -> VisualizationConfig:
    """获取可视化配置"""
    return config_manager.get_visualization_config()

def get_simulation_config() -> SimulationConfig:
    """获取仿真配置"""
    return config_manager.get_simulation_config()

def update_config(config_type: Union[ConfigType, str], updates: Dict[str, Any]) -> bool:
    """更新配置"""
    if isinstance(config_type, str):
        try:
            config_type = ConfigType(config_type)
        except ValueError:
            raise ValueError(f"无效的配置类型: {config_type}")
    
    return config_manager.update_config(config_type, updates)

# 测试函数
if __name__ == "__main__":
    # 测试配置管理器
    print("测试配置管理器...")
    
    # 创建配置管理器实例
    cm = ConfigManager()
    
    # 测试加载配置
    print("\n1. 加载系统配置:")
    sys_config = cm.get_system_config()
    print(f"   系统名称: {sys_config.name}")
    print(f"   版本: {sys_config.version}")
    print(f"   服务器端口: {sys_config.port}")
    
    print("\n2. 加载日志配置:")
    log_config = cm.get_logging_config()
    print(f"   日志级别: {log_config.level}")
    print(f"   文件日志: {'启用' if log_config.file_enabled else '禁用'}")
    
    print("\n3. 加载可视化配置:")
    viz_config = cm.get_visualization_config()
    print(f"   可视化引擎: {viz_config.engine}")
    print(f"   地图提供商: {viz_config.map_provider}")
    
    print("\n4. 加载仿真配置:")
    sim_config = cm.get_simulation_config()
    print(f"   最大实体数: {sim_config.max_entities}")
    print(f"   并行处理: {'启用' if sim_config.parallel_processing else '禁用'}")
    
    print("\n5. 验证配置:")
    validation = cm.validate_config(ConfigType.SYSTEM)
    print(f"   系统配置有效: {validation['valid']}")
    if validation['warnings']:
        print(f"   警告: {validation['warnings']}")
    
    print("\n✅ 配置管理器测试完成！")
