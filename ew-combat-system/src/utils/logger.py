"""
日志模块
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json
from datetime import datetime
import sys


class EWLogger:
    """电子战仿真系统日志器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EWLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.loggers = {}
        self.config = {}
        self._initialized = True
        
        # 创建日志目录
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self._load_config()
        
        # 配置根日志器
        self._configure_root_logger()
    
    def _load_config(self):
        """加载日志配置"""
        config_path = Path("config/logging.yaml")
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                print(f"加载日志配置失败: {e}")
                self.config = self._get_default_config()
        else:
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': 'logs/ew_simulation.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                },
                'error_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                    'filename': 'logs/error.log',
                    'maxBytes': 5242880,  # 5MB
                    'backupCount': 3
                }
            },
            'loggers': {
                'src': {
                    'level': 'INFO',
                    'handlers': ['console', 'file'],
                    'propagate': False
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console', 'file', 'error_file']
            }
        }
    
    def _configure_root_logger(self):
        """配置根日志器"""
        # 清除现有处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 应用配置
        # logging.config.dictConfig(self.config)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        
        return self.loggers[name]
    
    def set_level(self, name: str, level: str):
        """设置日志级别"""
        logger = self.get_logger(name)
        level_num = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level_num)
    
    def add_file_handler(self, name: str, filename: str, 
                        level: str = 'INFO', 
                        formatter: str = 'detailed'):
        """添加文件处理器"""
        logger = self.get_logger(name)
        
        # 创建文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(self.log_dir / filename),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        
        # 设置级别
        level_num = getattr(logging, level.upper(), logging.INFO)
        file_handler.setLevel(level_num)
        
        # 设置格式
        formatter_config = self.config['formatters'].get(formatter, {})
        fmt = logging.Formatter(formatter_config.get('format', '%(message)s'))
        file_handler.setFormatter(fmt)
        
        # 添加到日志器
        logger.addHandler(file_handler)
    
    def log_simulation_start(self, scenario_name: str, config: Dict = None):
        """记录仿真开始"""
        logger = self.get_logger('simulation')
        logger.info("=" * 60)
        logger.info(f"仿真开始: {scenario_name}")
        logger.info(f"开始时间: {datetime.now().isoformat()}")
        
        if config:
            logger.debug(f"仿真配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
    
    def log_simulation_progress(self, progress: float, message: str = ""):
        """记录仿真进度"""
        logger = self.get_logger('simulation')
        logger.info(f"仿真进度: {progress:.1%} - {message}")
    
    def log_simulation_result(self, result: Dict):
        """记录仿真结果"""
        logger = self.get_logger('simulation')
        
        if 'error' in result:
            logger.error(f"仿真失败: {result['error']}")
        else:
            logger.info(f"仿真完成: {result.get('scenario', '未知')}")
            
            # 记录关键结果
            if 'result' in result:
                res = result['result']
                logger.info(f"干扰效果: {res.get('effective', False)}")
                logger.info(f"干信比: {res.get('j_s_ratio', 0):.1f} dB")
                logger.info(f"探测概率: {res.get('detection_probability', 0)*100:.1f}%")
    
    def log_entity_created(self, entity_type: str, entity_info: Dict):
        """记录实体创建"""
        logger = self.get_logger('entity')
        logger.info(f"创建{entity_type}: {entity_info.get('name', '未知')} "
                   f"({entity_info.get('id', '未知')})")
    
    def log_entity_updated(self, entity_type: str, entity_id: str, changes: Dict):
        """记录实体更新"""
        logger = self.get_logger('entity')
        logger.debug(f"更新{entity_type} {entity_id}: {changes}")
    
    def log_entity_deleted(self, entity_type: str, entity_id: str):
        """记录实体删除"""
        logger = self.get_logger('entity')
        logger.info(f"删除{entity_type}: {entity_id}")
    
    def log_assessment_result(self, assessment: Dict):
        """记录评估结果"""
        logger = self.get_logger('assessment')
        
        if 'effectiveness_scores' in assessment:
            scores = assessment['effectiveness_scores']
            logger.info(f"效能评估 - 总体评分: {scores.get('overall_score', 0):.3f}")
            
            # 记录详细评分
            for key, value in scores.items():
                if key != 'recommendations':
                    logger.debug(f"{key}: {value}")
    
    def log_visualization_created(self, viz_type: str, details: str = ""):
        """记录可视化创建"""
        logger = self.get_logger('visualization')
        logger.info(f"创建可视化: {viz_type} {details}")
    
    def log_data_exported(self, export_type: str, filename: str):
        """记录数据导出"""
        logger = self.get_logger('data')
        logger.info(f"数据导出: {export_type} -> {filename}")
    
    def log_data_imported(self, import_type: str, filename: str):
        """记录数据导入"""
        logger = self.get_logger('data')
        logger.info(f"数据导入: {import_type} <- {filename}")
    
    def log_error(self, context: str, error: Exception, extra: Dict = None):
        """记录错误"""
        logger = self.get_logger('error')
        
        error_msg = f"{context}: {str(error)}"
        if extra:
            error_msg += f" | 额外信息: {extra}"
        
        logger.error(error_msg, exc_info=True)
    
    def log_warning(self, context: str, warning: str, extra: Dict = None):
        """记录警告"""
        logger = self.get_logger('warning')
        
        warning_msg = f"{context}: {warning}"
        if extra:
            warning_msg += f" | 额外信息: {extra}"
        
        logger.warning(warning_msg)
    
    def log_performance(self, operation: str, duration: float, 
                       details: Dict = None):
        """记录性能信息"""
        logger = self.get_logger('performance')
        
        perf_msg = f"{operation}: {duration:.3f}秒"
        if details:
            perf_msg += f" | 详情: {details}"
        
        logger.info(perf_msg)
    
    def get_log_stats(self, log_name: str = 'ew_simulation.log') -> Dict[str, Any]:
        """获取日志统计信息"""
        log_file = self.log_dir / log_name
        
        if not log_file.exists():
            return {}
        
        stats = {
            'total_lines': 0,
            'level_counts': {},
            'last_modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
            'file_size_mb': log_file.stat().st_size / (1024 * 1024)
        }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                stats['total_lines'] = len(lines)
                
                # 统计级别
                for line in lines:
                    for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                        if f' - {level} - ' in line:
                            stats['level_counts'][level] = stats['level_counts'].get(level, 0) + 1
                            break
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def clear_logs(self, days_old: int = 30) -> int:
        """清理旧日志"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        deleted_count = 0
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.log_error("清理日志失败", e, {'file': str(log_file)})
        
        return deleted_count
    
    def export_log_summary(self, output_file: str = None) -> str:
        """导出日志摘要"""
        stats = self.get_log_stats()
        
        if output_file:
            output_path = self.log_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            return str(output_path)
        else:
            return json.dumps(stats, indent=2, ensure_ascii=False)

# 全局日志器实例
logger = EWLogger()

# 便利函数
def get_logger(name: str) -> logging.Logger:
    """获取日志器（便利函数）"""
    return logger.get_logger(name)

def log_simulation_start(scenario_name: str, config: Dict = None):
    """记录仿真开始（便利函数）"""
    logger.log_simulation_start(scenario_name, config)

def log_simulation_progress(progress: float, message: str = ""):
    """记录仿真进度（便利函数）"""
    logger.log_simulation_progress(progress, message)

def log_simulation_result(result: Dict):
    """记录仿真结果（便利函数）"""
    logger.log_simulation_result(result)

def log_error(context: str, error: Exception, extra: Dict = None):
    """记录错误（便利函数）"""
    logger.log_error(context, error, extra)
