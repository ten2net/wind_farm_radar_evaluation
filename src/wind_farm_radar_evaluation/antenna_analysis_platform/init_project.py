# 22. 初始化脚本 (init_project.py

"""
项目初始化脚本
创建必要的目录结构和配置文件
"""

import sys
import os
from pathlib import Path
import json
import yaml
import shutil
import subprocess
from typing import Dict, Any, List, Optional
import platform

def print_header():
    """打印项目初始化头部信息"""
    header = """
    ========================================
        天线分析平台 - 项目初始化脚本
    ========================================
    """
    print(header)

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    
    if sys.version_info < (3, 8):
        print(f"❌ 需要Python 3.8或更高版本，当前版本: {sys.version_info.major}.{sys.version_info.minor}")
        return False
    else:
        print(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")
    
    required_packages = [
        ('streamlit', 'streamlit'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('plotly', 'plotly'),
        ('scipy', 'scipy'),
        ('pyyaml', 'yaml'),
        ('psutil', 'psutil'),
        ('pillow', 'PIL')
    ]
    
    missing_packages = []
    installed_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            installed_packages.append(package_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"  ❌ {package_name}")
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        install_missing = input("是否自动安装缺失的依赖包？(y/n): ").lower() == 'y'
        if install_missing:
            install_dependencies(missing_packages)
            return True
        else:
            print("请手动安装缺失的依赖包:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    else:
        print("✅ 所有依赖包已安装")
        return True

def install_dependencies(packages: List[str]):
    """安装缺失的依赖包"""
    print(f"\n📦 安装依赖包: {', '.join(packages)}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("✅ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装依赖包失败: {e}")
        return False

def create_directory_structure():
    """创建目录结构"""
    print("\n📁 创建目录结构...")
    
    directories = [
        # 主目录
        "data",
        "data/antennas",
        "data/patterns", 
        "data/exports",
        "data/backups",
        "data/education",
        "data/uploads",
        "cache",
        "logs",
        "logs/app",
        "logs/errors",
        "config",
        "pages",
        
        # 代码目录
        "models",
        "services", 
        "views",
        "utils"
    ]
    
    created_dirs = []
    existing_dirs = []
    
    for directory in directories:
        dir_path = Path(directory)
        if dir_path.exists():
            existing_dirs.append(directory)
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(directory)
    
    for directory in created_dirs:
        print(f"  📁 创建: {directory}")
    
    for directory in existing_dirs:
        print(f"  ℹ️  已存在: {directory}")
    
    return len(created_dirs) > 0

def create_config_files():
    """创建配置文件"""
    print("\n⚙️ 创建配置文件...")
    
    config_dir = Path("config")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # 应用配置
    app_config = {
        'application': {
            'name': '天线分析平台',
            'version': '1.0.0',
            'debug': False,
            'log_level': 'INFO',
            'max_file_size': 100,
            'allowed_extensions': ['.json', '.yaml', '.yml', '.csv', '.txt', '.xlsx', '.mat']
        },
        'paths': {
            'data_dir': 'data',
            'cache_dir': 'cache', 
            'log_dir': 'logs',
            'export_dir': 'data/exports',
            'backup_dir': 'data/backups',
            'upload_dir': 'data/uploads'
        },
        'simulation': {
            'default_frequency': 2.4,
            'max_points': 10000,
            'default_resolution': 5,
            'interpolation_enabled': True,
            'auto_normalize': True
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
            'session_timeout': 3600
        }
    }
    
    # 用户设置
    user_settings = {
        'application': {
            'name': '天线分析平台',
            'version': '1.0.0',
            'theme': 'light',
            'language': 'zh-CN',
            'auto_save': True,
            'save_interval': 5,
            'max_history': 50,
            'cache_enabled': True,
            'cache_size': 100,
            'log_level': 'INFO'
        },
        'simulation': {
            'default_generator': 'analytical',
            'default_theta_res': 5,
            'default_phi_res': 5,
            'default_component': 'total',
            'auto_normalize': True,
            'add_noise': False,
            'noise_level': -30,
            'interpolation': True,
            'interpolation_factor': 2
        },
        'visualization': {
            'theme': 'plotly_white',
            'color_theme': 'viridis',
            'default_width': 800,
            'default_height': 600,
            'show_grid': True,
            'show_legend': True,
            'show_title': True,
            'annotate_peaks': True,
            'font_size': 12,
            'dpi': 150
        },
        'analysis': {
            'default_beamwidth_levels': ['3dB', '10dB'],
            'find_nulls': True,
            'find_sidelobes': True,
            'calculate_axial_ratio': True,
            'calculate_efficiency': True,
            'performance_thresholds': {
                'good': 0.8,
                'fair': 0.6,
                'poor': 0.4
            }
        },
        'export': {
            'default_format': 'PNG',
            'default_dpi': 300,
            'include_metadata': True,
            'compress_exports': True,
            'auto_open_folder': False
        },
        'data_management': {
            'auto_backup': True,
            'backup_interval': 24,
            'max_backups': 10,
            'data_retention_days': 30,
            'cleanup_old_data': True
        },
        'user': {
            'name': '用户',
            'organization': '',
            'department': '',
            'email': '',
            'notifications': True,
            'newsletter': False
        },
        'system': {
            'last_update_check': None,
            'update_channel': 'stable',
            'auto_check_updates': True,
            'send_usage_stats': False,
            'send_crash_reports': False
        }
    }
    
    # 天线数据库
    antenna_database = {
        'version': '1.0.0',
        'last_updated': '2026-01-01',
        'antennas': [
            {
                'id': 'dipole_example',
                'name': '半波偶极子示例',
                'antenna_type': 'dipole',
                'description': '标准半波偶极子天线',
                'frequency_range': [0.1, 3.0],
                'center_frequency': 1.0,
                'gain': 2.15,
                'bandwidth': 15.0,
                'vswr': 1.2,
                'polarization': 'vertical',
                'beamwidth_e': 78.0,
                'beamwidth_h': 360.0,
                'sidelobe_level': -12.0,
                'front_to_back_ratio': 0.0,
                'efficiency': 0.95,
                'tags': ['基础天线', '全向天线', '线天线']
            },
            {
                'id': 'patch_example',
                'name': '微带贴片天线示例',
                'antenna_type': 'patch',
                'description': '2.4GHz WiFi微带贴片天线',
                'frequency_range': [2.4, 2.5],
                'center_frequency': 2.45,
                'gain': 7.0,
                'bandwidth': 3.0,
                'vswr': 1.5,
                'polarization': 'linear',
                'beamwidth_e': 75.0,
                'beamwidth_h': 75.0,
                'sidelobe_level': -15.0,
                'front_to_back_ratio': 20.0,
                'efficiency': 0.85,
                'tags': ['微带天线', '平面天线', 'WiFi']
            },
            {
                'id': 'horn_example',
                'name': '标准增益喇叭天线示例',
                'antenna_type': 'horn',
                'description': 'X波段标准增益喇叭天线',
                'frequency_range': [8.0, 12.0],
                'center_frequency': 10.0,
                'gain': 20.0,
                'bandwidth': 40.0,
                'vswr': 1.3,
                'polarization': 'horizontal',
                'beamwidth_e': 15.0,
                'beamwidth_h': 15.0,
                'sidelobe_level': -20.0,
                'front_to_back_ratio': 35.0,
                'efficiency': 0.9,
                'tags': ['喇叭天线', '标准增益', '微波']
            }
        ],
        'categories': [
            {
                'id': 'wire_antennas',
                'name': '线天线',
                'description': '由金属导线构成的天线',
                'antennas': ['dipole_example']
            },
            {
                'id': 'aperture_antennas',
                'name': '口径天线',
                'description': '由金属口径构成的天线',
                'antennas': ['horn_example']
            },
            {
                'id': 'planar_antennas',
                'name': '平面天线',
                'description': '印刷在基板上的平面天线',
                'antennas': ['patch_example']
            }
        ]
    }
    
    # 创建配置文件
    config_files = [
        ('app_config.yaml', app_config),
        ('user_settings.yaml', user_settings),
        ('antenna_database.yaml', antenna_database)
    ]
    
    created_files = []
    existing_files = []
    
    for filename, config_data in config_files:
        filepath = config_dir / filename
        
        if filepath.exists():
            existing_files.append(filename)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            created_files.append(filename)
    
    for filename in created_files:
        print(f"  📄 创建: config/{filename}")
    
    for filename in existing_files:
        print(f"  ℹ️  已存在: config/{filename}")
    
    return len(created_files) > 0

def create_data_files():
    """创建数据文件"""
    print("\n💾 创建数据文件...")
    
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建README文件
    readme_content = """# 天线分析平台 - 数据目录

## 目录结构

- `antennas/` - 天线配置文件
- `patterns/` - 方向图数据
- `exports/` - 导出文件
- `backups/` - 备份文件
- `education/` - 教学资料
- `uploads/` - 上传文件

## 文件格式

### 天线配置文件 (.json, .yaml)
```yaml
name: 天线名称
antenna_type: 天线类型
center_frequency: 中心频率 (GHz)
gain: 增益 (dBi)
bandwidth: 带宽 (%)
polarization: 极化方式
# ... 其他参数
```

### 方向图数据 (.npy, .json)
- theta_grid: 俯仰角网格
- phi_grid: 方位角网格
- gain_data: 增益数据
- phase_data: 相位数据 (可选)
- axial_ratio_data: 轴比数据 (可选)
"""
    
    readme_path = data_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  📄 创建: data/README.md")
    
    return True

def create_education_content():
    """创建教学内容"""
    print("\n📚 创建教学内容...")
    
    education_dir = Path("data") / "education"
    education_dir.mkdir(parents=True, exist_ok=True)
    
    # 基础理论知识
    fundamentals = {
        'fundamentals': [
            {
                'id': 'fundamentals_1',
                'title': '天线基本原理',
                'sections': [
                    {
                        'title': '天线定义',
                        'content': """**天线** 是将导行波与自由空间波相互转换的装置，是无线通信系统的关键组成部分。

## 主要功能
1. **发射天线**: 将高频电流转换为电磁波辐射
2. **接收天线**: 将电磁波转换为高频电流

## 基本参数
- **频率范围**: 天线能够有效工作的频率范围
- **阻抗**: 天线的输入阻抗，通常为50Ω或75Ω
- **极化**: 电磁波的电场方向
- **增益**: 天线在特定方向上的辐射能力
"""
                    },
                    {
                        'title': '辐射原理',
                        'content': """## 电流辐射理论
根据麦克斯韦方程组，变化的电场产生磁场，变化的磁场产生电场。

### 偶极子辐射
最简单的天线是偶极子天线，其辐射场为：

$$
E_θ = \\frac{jI_0l}{2λr} \\sqrt{\\frac{μ_0}{ε_0}} \\sin θ e^{-jkr}
$$

其中：
- $I_0$: 电流幅度
- $l$: 偶极子长度
- $λ$: 波长
- $r$: 观察点到天线的距离
- $θ$: 观察方向与天线轴的夹角
"""
                    }
                ]
            }
        ],
        'design_guidelines': [
            {
                'id': 'design_1',
                'title': '天线设计流程',
                'steps': [
                    {
                        'step': 1,
                        'title': '需求分析',
                        'content': '明确应用场景、频率、增益、波束宽度、极化等要求'
                    },
                    {
                        'step': 2,
                        'title': '选型',
                        'content': '根据需求选择合适的天线类型'
                    }
                ]
            }
        ]
    }
    
    # 保存教学内容
    content_file = education_dir / "content.yaml"
    with open(content_file, 'w', encoding='utf-8') as f:
        yaml.dump(fundamentals, f, default_flow_style=False, allow_unicode=True)
    
    print(f"  📄 创建: data/education/content.yaml")
    
    return True

def create_example_files():
    """创建示例文件"""
    print("\n📁 创建示例文件...")
    
    # 创建示例天线配置文件
    examples_dir = Path("data") / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    
    # 示例天线配置
    example_antennas = [
        {
            'name': '2.4GHz WiFi天线',
            'description': '用于无线路由器的微带贴片天线',
            'antenna_type': 'patch',
            'frequency_range': [2.4, 2.5],
            'center_frequency': 2.45,
            'gain': 7.0,
            'bandwidth': 4.0,
            'vswr': 1.8,
            'polarization': 'linear',
            'beamwidth_e': 75.0,
            'beamwidth_h': 75.0
        },
        {
            'name': 'UHF电视天线',
            'description': 'UHF频段电视接收天线',
            'antenna_type': 'yagi',
            'frequency_range': [470, 862],
            'center_frequency': 600,
            'gain': 12.0,
            'bandwidth': 20.0,
            'vswr': 1.5,
            'polarization': 'horizontal',
            'beamwidth_e': 45.0,
            'beamwidth_h': 60.0
        }
    ]
    
    for i, antenna in enumerate(example_antennas, 1):
        filename = examples_dir / f"example_antenna_{i}.yaml"
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(antenna, f, default_flow_style=False, allow_unicode=True)
        print(f"  📄 创建: data/examples/{filename.name}")
    
    return True

def create_readme():
    """创建项目README文件"""
    print("\n📋 创建项目README文件...")
    
    readme_content = """# 天线分析平台

一个基于Python的专业天线性能分析与可视化平台。

## 功能特性

### 📡 天线仿真
- 多种天线类型支持
- 方向图生成和计算
- 参数化天线建模
- 实时仿真结果展示

### 📊 性能分析
- 波束特性分析
- 极化特性分析
- 效率计算
- 频域分析
- 比较分析

### 📈 数据可视化
- 2D/3D方向图展示
- 交互式图表
- 多维度数据对比
- 自定义可视化主题

### 📚 教学中心
- 天线理论基础
- 设计指南
- 案例分析
- 学习资源

### ⚙️ 系统功能
- 用户设置管理
- 数据导入导出
- 多格式报告生成
- 系统监控

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 初始化项目
```bash
python init_project.py
```

### 运行应用
```bash
streamlit run app.py
```

## 项目结构
```
antenna-analysis-platform/
├── app.py                    # 主应用程序
├── pages/                    # 多页面应用
├── models/                   # 数据模型
├── services/                 # 业务服务
├── views/                    # 视图组件
├── utils/                    # 工具函数
├── config/                   # 配置文件
├── data/                     # 数据文件
├── cache/                    # 缓存文件
├── logs/                     # 日志文件
└── requirements.txt          # 依赖列表
```

## 配置说明

### 应用配置
- `config/app_config.yaml`: 应用全局配置
- `config/user_settings.yaml`: 用户设置
- `config/antenna_database.yaml`: 天线数据库

### 数据目录
- `data/antennas/`: 天线配置文件
- `data/patterns/`: 方向图数据
- `data/exports/`: 导出文件
- `data/backups/`: 备份文件
- `data/education/`: 教学资料

## 开发指南

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 编写文档字符串
- 单元测试覆盖

### 添加新功能
1. 在对应模块中添加代码
2. 更新配置文件
3. 添加测试用例
4. 更新文档

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 贡献指南

欢迎提交Issue和Pull Request！

## 支持

如有问题，请：
1. 查看文档
2. 搜索Issue
3. 提交新Issue
"""

    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("  📄 创建: README.md")
    
    return True

def create_requirements_file():
    """创建requirements.txt文件"""
    print("\n📦 创建依赖文件...")
    
    requirements = """# 天线分析平台依赖包

# 核心框架
streamlit>=1.28.0
numpy>=1.24.0
pandas>=2.0.0
plotly>=5.17.0

# 科学计算
scipy>=1.11.0
sympy>=1.12.0

# 数据处理
pyyaml>=6.0
openpyxl>=3.1.0
python-docx>=1.1.0

# 系统工具
psutil>=5.9.0
pillow>=10.0.0
tqdm>=4.66.0

# 开发工具
black>=23.0.0
pylint>=3.0.0
pytest>=7.4.0
"""
    
    with open("requirements.txt", 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print("  📄 创建: requirements.txt")
    
    return True

def create_gitignore():
    """创建.gitignore文件"""
    print("\n🔒 创建.gitignore文件...")
    
    gitignore = """# 开发环境
.env
.venv
venv/
env/
ENV/

# 编辑器
.vscode/
.idea/
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# 项目特定
.DS_Store
Thumbs.db

# 数据文件
data/exports/*
data/backups/*
data/uploads/*
cache/*
logs/*
!data/README.md
!data/examples/

# 大型文件
*.npy
*.mat
*.pkl
*.h5
*.hdf5

# 临时文件
*.tmp
*.temp
temp/

# 测试文件
.coverage
htmlcov/
.pytest_cache/
.tox/
"""
    
    with open(".gitignore", 'w', encoding='utf-8') as f:
        f.write(gitignore)
    
    print("  📄 创建: .gitignore")
    
    return True

def create_license():
    """创建许可证文件"""
    print("\n⚖️ 创建许可证文件...")
    
    license_text = """MIT License

Copyright (c) 2026 天线分析平台

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    with open("LICENSE", 'w', encoding='utf-8') as f:
        f.write(license_text)
    
    print("  📄 创建: LICENSE")
    
    return True

def create_main_app():
    """创建主应用文件"""
    print("\n🚀 创建主应用文件...")
    
    # 检查是否已存在
    if Path("app.py").exists():
        print("  ℹ️  已存在: app.py")
        return True
    
    # 从模板复制（这里简化处理）
    app_content = '''"""
天线分析平台 - 主应用程序
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    st.set_page_config(
        page_title="天线分析平台",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📡 天线分析平台")
    st.markdown("### 专业的天线性能分析与可视化工具")
    
    st.markdown("""
    ## 🎉 欢迎使用天线分析平台！
    
    这是一个基于Python开发的专业天线性能分析工具，提供完整的仿真、分析、可视化功能。
    
    ### 🚀 快速开始
    
    1. **配置天线参数** - 在侧边栏设置天线类型和参数
    2. **运行仿真** - 生成天线方向图
    3. **分析结果** - 查看性能指标和可视化结果
    4. **导出报告** - 生成分析报告和图表
    
    ### 📁 项目已成功初始化！
    
    请查看左侧导航栏开始使用：
    - **📊 仪表板**: 查看系统概览和快速操作
    - **🔍 分析工具**: 运行仿真和分析
    - **📚 教学中心**: 学习天线理论和设计
    - **⚙️ 系统设置**: 配置应用参数
    - **📤 数据导出**: 导出结果和报告
    """)
    
    st.info("💡 提示: 首次使用建议先查看教学中心了解基本概念和操作方法。")

if __name__ == "__main__":
    main()
'''
    
    with open("app.py", 'w', encoding='utf-8') as f:
        f.write(app_content)
    
    print("  📄 创建: app.py")
    
    return True

def create_pages():
    """创建页面文件"""
    print("\n📄 创建页面文件...")
    
    pages_dir = Path("pages")
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    # 页面配置
    pages_config = [
        {
            'filename': '1_📊_仪表板.py',
            'content': '''"""
仪表板页面
"""
import streamlit as st

st.set_page_config(page_title="仪表板", page_icon="📊")

st.title("📊 仪表板")
st.markdown("### 系统概览和快速操作")

st.info("页面内容将在运行初始化后自动生成。")
'''
        },
        {
            'filename': '2_🔍_分析工具.py',
            'content': '''"""
分析工具页面
"""
import streamlit as st

st.set_page_config(page_title="分析工具", page_icon="🔍")

st.title("🔍 分析工具")
st.markdown("### 天线仿真和性能分析")

st.info("页面内容将在运行初始化后自动生成。")
'''
        },
        {
            'filename': '3_📚_教学中心.py',
            'content': '''"""
教学中心页面
"""
import streamlit as st

st.set_page_config(page_title="教学中心", page_icon="📚")

st.title("📚 教学中心")
st.markdown("### 天线理论和设计指南")

st.info("页面内容将在运行初始化后自动生成。")
'''
        },
        {
            'filename': '4_⚙️_系统设置.py',
            'content': '''"""
系统设置页面
"""
import streamlit as st

st.set_page_config(page_title="系统设置", page_icon="⚙️")

st.title("⚙️ 系统设置")
st.markdown("### 应用配置和管理")

st.info("页面内容将在运行初始化后自动生成。")
'''
        },
        {
            'filename': '5_📤_数据导出.py',
            'content': '''"""
数据导出页面
"""
import streamlit as st

st.set_page_config(page_title="数据导出", page_icon="📤")

st.title("📤 数据导出")
st.markdown("### 结果导出和报告生成")

st.info("页面内容将在运行初始化后自动生成。")
'''
        }
    ]
    
    created_pages = []
    
    for page in pages_config:
        filepath = pages_dir / page['filename']
        if not filepath.exists():
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page['content'])
            created_pages.append(page['filename'])
    
    for page in created_pages:
        print(f"  📄 创建: pages/{page}")
    
    if not created_pages:
        print("  ℹ️  所有页面文件已存在")
    
    return len(created_pages) > 0

def setup_complete():
    """完成设置"""
    print("\n" + "="*50)
    print("🎉 项目初始化完成！")
    print("="*50)
    
    print("""
## 下一步操作：

1. 安装依赖包：
   pip install -r requirements.txt

2. 运行应用：
   streamlit run app.py

3. 打开浏览器访问：
   http://localhost:8501

## 项目结构已创建：

📁 config/         - 配置文件
📁 data/           - 数据文件
📁 cache/          - 缓存文件
📁 logs/           - 日志文件
📁 pages/          - 页面文件
📁 models/         - 数据模型
📁 services/       - 业务服务
📁 views/          - 视图组件
📁 utils/          - 工具函数
📄 app.py          - 主应用程序
📄 README.md       - 项目说明
📄 requirements.txt - 依赖列表
📄 LICENSE         - 许可证
📄 .gitignore      - Git忽略文件

## 快速测试：

运行以下命令检查系统：
   python -c "import streamlit; import numpy; import pandas; print('✅ 所有依赖包已安装')"

祝您使用愉快！🎯
""")

def main():
    """主函数"""
    print_header()
    
    # 检查Python版本
    if not check_python_version():
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 创建目录结构
    create_directory_structure()
    
    # 创建配置文件
    create_config_files()
    
    # 创建数据文件
    create_data_files()
    
    # 创建教学内容
    create_education_content()
    
    # 创建示例文件
    create_example_files()
    
    # 创建README
    create_readme()
    
    # 创建依赖文件
    create_requirements_file()
    
    # 创建.gitignore
    create_gitignore()
    
    # 创建许可证
    create_license()
    
    # 创建主应用
    create_main_app()
    
    # 创建页面文件
    create_pages()
    
    # 完成设置
    setup_complete()

if __name__ == "__main__":
    main()


# ## 初始化脚本功能总结

# ### 1. **系统检查**
# - Python版本验证
# - 依赖包检查
# - 自动安装缺失依赖

# ### 2. **目录结构创建**
# - 完整的项目目录树
# - 数据存储目录
# - 缓存和日志目录
# - 配置和页面目录

# ### 3. **配置文件生成**
# - 应用全局配置
# - 用户设置配置
# - 天线数据库
# - 教学资源文件

# ### 4. **示例文件创建**
# - 示例天线配置
# - 教学材料
# - 数据README

# ### 5. **项目文档**
# - README.md说明文档
# - requirements.txt依赖列表
# - .gitignore文件
# - LICENSE许可证

# ### 6. **应用框架**
# - 主应用文件
# - 多页面结构
# - 基础页面模板

# ### 7. **使用说明**
# - 详细的后续步骤
# - 运行指南
# - 测试方法

