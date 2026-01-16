"""
启动脚本 - 用于启动数字射频战场仿真系统Web应用
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("检查依赖...")
    
    required_packages = [
        'streamlit',
        'streamlit-folium',
        'folium',
        'plotly',
        'pandas',
        'numpy',
        'requests',
        'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        print("正在安装依赖...")
        
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        
        print("依赖安装完成")
    
    return True

def setup_directories():
    """设置目录结构"""
    print("设置目录结构...")
    
    directories = [
        'data/configs',
        'data/scenarios',
        'data/results',
        'data/cache',
        'assets/css',
        'assets/images',
        'assets/fonts',
        'components',
        'utils',
        'config',
        'backend'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # 创建默认配置文件
    config_dir = Path('config')
    
    default_config = {
        "system_name": "数字射频战场仿真系统",
        "system_mode": "single_radar",
        "simulation_duration": 300.0,
        "time_step": 0.1,
        "real_time_factor": 1.0,
        "num_radars": 1,
        "num_targets": 3,
        "output_dir": "./output",
        "enable_visualization": True,
        "enable_evaluation": True
    }
    
    config_file = config_dir / 'default_config.json'
    if not config_file.exists():
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print("目录结构设置完成")

def start_streamlit():
    """启动Streamlit应用"""
    print("启动数字射频战场仿真系统Web应用...")
    
    # 检查主应用文件
    app_file = Path('app.py')
    if not app_file.exists():
        print("错误: 未找到app.py文件")
        return False
    
    # 启动Streamlit
    cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.port=8501']
    
    print(f"启动命令: {' '.join(cmd)}")
    print("应用将在浏览器中打开...")
    
    # 延迟打开浏览器
    time.sleep(2)
    webbrowser.open('http://localhost:8501')
    
    # 运行Streamlit
    subprocess.run(cmd)
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("数字射频战场仿真系统 - Web应用启动器")
    print("=" * 60)
    
    try:
        # 检查依赖
        if not check_dependencies():
            return
        
        # 设置目录
        setup_directories()
        
        # 启动应用
        start_streamlit()
        
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()