#!/bin/bash
# 环境设置脚本

set -e

echo "设置风电场雷达评估系统环境..."

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python 3"
    exit 1
fi

# 创建虚拟环境（如果使用pip）
if [ "$1" = "pip" ]; then
    echo "使用pip设置环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    
    if [ "$2" = "dev" ]; then
        pip install -e ".[dev]"
    fi
else
    echo "使用uv设置环境..."
    uv sync
    
    if [ "$1" = "dev" ]; then
        uv sync --group dev
    fi
fi

echo "环境设置完成！"
echo "运行 'python examples/basic_usage.py' 测试安装"
