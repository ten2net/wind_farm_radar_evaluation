# run_app.py
#!/usr/bin/env python3
"""
导引头电子战仿真系统 - 主启动脚本
作者: 电子战仿真团队
版本: 2.0.0
"""

import os
import sys
import argparse
import logging
import webbrowser
import subprocess
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def setup_logging(log_level="INFO", log_file=None):
    """设置日志系统"""
    log_formats = {
        'DEBUG': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'INFO': '%(asctime)s - %(levelname)s - %(message)s',
        'WARNING': '%(asctime)s - %(levelname)s - %(message)s',
        'ERROR': '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    }
    
    log_format = log_formats.get(log_level, log_formats['INFO'])
    
    handlers = [
        logging.StreamHandler(sys.stdout)
    ]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成 - 级别: {log_level}")
    
    return logger

def check_dependencies():
    """检查依赖包"""
    logger = logging.getLogger(__name__)
    
    required_packages = [
        ('streamlit', '1.28.0'),
        ('plotly', '5.17.0'),
        ('pandas', '2.0.3'),
        ('numpy', '1.24.3'),
        ('folium', '0.14.0'),
        ('streamlit-folium', '0.15.2'),
        ('psutil', '5.9.5'),
        ('sqlalchemy', '2.0.20'),
    ]
    
    optional_packages = [
        ('openpyxl', None),  # Excel导出
        ('requests', None),  # HTTP请求
        ('aiohttp', None),  # 异步HTTP
    ]
    
    missing_required = []
    missing_optional = []
    
    for package, version in required_packages:
        try:
            mod = __import__(package)
            if version and hasattr(mod, '__version__'):
                installed_version = mod.__version__
                logger.debug(f"{package} 版本: {installed_version}")
        except ImportError:
            missing_required.append(f"{package}>={version}" if version else package)
    
    for package, version in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(f"{package}>={version}" if version else package)
    
    if missing_required:
        logger.error(f"缺少必要的依赖包: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        logger.warning(f"缺少可选依赖包: {', '.join(missing_optional)}")
        logger.warning("某些功能可能不可用")
    
    return True

def create_directory_structure():
    """创建必要的目录结构"""
    directories = [
        'data',          # 数据存储
        'exports',       # 导出文件
        'logs',          # 日志文件
        'temp',          # 临时文件
        'config',        # 配置文件
        'scenarios',     # 场景文件
        'reports',       # 报告文件
    ]
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(exist_ok=True)
            (dir_path / '.gitkeep').touch(exist_ok=True)  # 确保目录被Git跟踪
        except Exception as e:
            print(f"创建目录 {dir_path} 失败: {e}")
    
    return True

def setup_configuration():
    """设置配置文件"""
    config_dir = project_root / 'config'
    default_config = {
        'application': {
            'name': '导引头电子战仿真系统',
            'version': '2.0.0',
            'debug': False,
            'log_level': 'INFO',
            'data_dir': str(project_root / 'data'),
            'export_dir': str(project_root / 'exports'),
        },
        'database': {
            'type': 'sqlite',
            'path': str(project_root / 'data' / 'simulation.db'),
            'pool_size': 10,
            'max_overflow': 20,
        },
        'simulation': {
            'default_time_step': 0.1,
            'max_simulation_time': 300,
            'auto_save_interval': 60,
            'default_speed': 1.0,
        },
        'visualization': {
            'map_center': [35.0, 115.0],
            'default_zoom': 8,
            'show_terrain': True,
            'show_weather': True,
            'show_trajectory': True,
        },
        'security': {
            'allowed_ips': ['127.0.0.1', 'localhost'],
            'max_login_attempts': 5,
            'lockout_time': 300,
            'require_authentication': False,
        }
    }
    
    # 创建默认配置文件
    config_file = config_dir / 'config.yaml'
    if not config_file.exists():
        try:
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
            print(f"配置文件已创建: {config_file}")
        except ImportError:
            print("警告: 未安装PyYAML，使用默认配置")
    
    return True

def check_environment():
    """检查运行环境"""
    logger = logging.getLogger(__name__)
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        logger.error(f"需要Python 3.8或更高版本，当前版本: {python_version.major}.{python_version.minor}")
        return False
    
    # 检查操作系统
    import platform
    system = platform.system()
    logger.info(f"操作系统: {system} {platform.release()}")
    
    # 检查内存
    try:
        import psutil
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        available_gb = memory.available / (1024**3)
        
        logger.info(f"系统内存: 总共 {total_gb:.1f} GB, 可用 {available_gb:.1f} GB")
        
        if available_gb < 2:
            logger.warning("可用内存较少，可能影响性能")
    except:
        logger.warning("无法获取内存信息")
    
    # 检查磁盘空间
    try:
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)
        logger.info(f"磁盘空间: 可用 {free_gb:.1f} GB")
        
        if free_gb < 1:
            logger.warning("磁盘空间不足，建议清理")
    except:
        logger.warning("无法获取磁盘空间信息")
    
    return True

def start_application(mode="web", port=8501, host="localhost", open_browser=True, debug=False):
    """启动应用程序"""
    logger = logging.getLogger(__name__)
    
    if mode == "web":
        # 启动Streamlit应用
        app_file = project_root / "main_application_module.py"
        
        if not app_file.exists():
            logger.error(f"主应用程序文件不存在: {app_file}")
            return False
        
        # 构建Streamlit启动命令
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(app_file),
            "--server.port", str(port),
            "--server.address", host,
            "--server.headless", "false" if open_browser else "true",
            "--browser.gatherUsageStats", "false",
        ]
        
        if debug:
            cmd.extend(["--logger.level", "debug"])
        
        logger.info(f"启动应用程序: {' '.join(cmd)}")
        logger.info(f"服务器地址: http://{host}:{port}")
        
        try:
            # 自动打开浏览器
            if open_browser:
                webbrowser.open(f"http://{host}:{port}")
            
            # 启动子进程
            process = subprocess.Popen(cmd, cwd=project_root)
            
            # 等待进程结束
            process.wait()
            
            return process.returncode == 0
            
        except KeyboardInterrupt:
            logger.info("接收到中断信号，正在关闭应用程序...")
            if process:
                process.terminate()
            return True
        except Exception as e:
            logger.error(f"启动应用程序失败: {e}")
            return False
    
    elif mode == "cli":
        # 命令行模式
        logger.info("启动命令行模式")
        try:
            from main_application_module import main
            main()
            return True
        except Exception as e:
            logger.error(f"命令行模式启动失败: {e}")
            return False
    
    else:
        logger.error(f"不支持的启动模式: {mode}")
        return False

def backup_database():
    """备份数据库"""
    logger = logging.getLogger(__name__)
    
    db_path = project_root / 'data' / 'simulation.db'
    if not db_path.exists():
        logger.info("数据库文件不存在，无需备份")
        return True
    
    backup_dir = project_root / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"simulation_backup_{timestamp}.db"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_file)
        logger.info(f"数据库已备份到: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        return False

def clear_temp_files():
    """清理临时文件"""
    logger = logging.getLogger(__name__)
    
    temp_dirs = [
        project_root / 'temp',
        project_root / '__pycache__',
    ]
    
    for temp_dir in temp_dirs:
        if temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"已清理临时目录: {temp_dir}")
            except Exception as e:
                logger.error(f"清理临时目录失败 {temp_dir}: {e}")
    
    return True

def install_dependencies():
    """安装依赖包"""
    logger = logging.getLogger(__name__)
    
    requirements_file = project_root / 'requirements.txt'
    if not requirements_file.exists():
        logger.error(f"依赖文件不存在: {requirements_file}")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        logger.info("依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"依赖包安装失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="导引头电子战仿真系统 - 启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                          # 默认启动Web应用
  %(prog)s --mode cli              # 启动命令行模式
  %(prog)s --port 8080             # 指定端口
  %(prog)s --no-browser            # 不自动打开浏览器
  %(prog)s --debug                 # 调试模式
  %(prog)s --install-deps          # 安装依赖
  %(prog)s --backup                # 备份数据库
  %(prog)s --clear-cache           # 清理缓存
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["web", "cli"], 
        default="web",
        help="启动模式: web(网页应用, 默认) 或 cli(命令行)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8501,
        help="服务器端口 (默认: 8501)"
    )
    parser.add_argument(
        "--host", 
        default="localhost",
        help="服务器地址 (默认: localhost)"
    )
    parser.add_argument(
        "--no-browser", 
        action="store_true",
        help="不自动打开浏览器"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="启用调试模式"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    parser.add_argument(
        "--log-file", 
        help="日志文件路径"
    )
    parser.add_argument(
        "--install-deps", 
        action="store_true",
        help="安装依赖包"
    )
    parser.add_argument(
        "--backup", 
        action="store_true",
        help="备份数据库"
    )
    parser.add_argument(
        "--clear-cache", 
        action="store_true",
        help="清理缓存和临时文件"
    )
    parser.add_argument(
        "--version", 
        action="store_true",
        help="显示版本信息"
    )
    
    args = parser.parse_args()
    
    # 显示版本信息
    if args.version:
        print("导引头电子战仿真系统 v2.0.0")
        print("版权所有 © 2024 电子战仿真实验室")
        return 0
    
    # 安装依赖
    if args.install_deps:
        if install_dependencies():
            print("✅ 依赖包安装成功")
        else:
            print("❌ 依赖包安装失败")
            return 1
    
    # 备份数据库
    if args.backup:
        logger = setup_logging(args.log_level, args.log_file)
        if backup_database():
            print("✅ 数据库备份成功")
        else:
            print("❌ 数据库备份失败")
        return 0
    
    # 清理缓存
    if args.clear_cache:
        logger = setup_logging(args.log_level, args.log_file)
        if clear_temp_files():
            print("✅ 缓存清理完成")
        else:
            print("❌ 缓存清理失败")
        return 0
    
    # 设置日志
    logger = setup_logging(args.log_level, args.log_file)
    
    # 显示启动信息
    logger.info("=" * 60)
    logger.info("导引头电子战仿真系统 v2.0.0")
    logger.info("=" * 60)
    
    # 检查环境
    if not check_environment():
        logger.error("环境检查失败")
        return 1
    
    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败")
        return 1
    
    # 创建目录结构
    if not create_directory_structure():
        logger.error("目录结构创建失败")
        return 1
    
    # 设置配置文件
    setup_configuration()
    
    # 启动应用
    logger.info(f"启动模式: {args.mode}")
    logger.info(f"服务器: {args.host}:{args.port}")
    logger.info(f"调试模式: {args.debug}")
    
    try:
        success = start_application(
            mode=args.mode,
            port=args.port,
            host=args.host,
            open_browser=not args.no_browser,
            debug=args.debug
        )
        
        if success:
            logger.info("应用程序正常退出")
            return 0
        else:
            logger.error("应用程序启动失败")
            return 1
            
    except KeyboardInterrupt:
        logger.info("应用程序被用户中断")
        return 0
    except Exception as e:
        logger.error(f"应用程序运行出错: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())