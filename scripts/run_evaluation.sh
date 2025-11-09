#!/bin/bash
# 运行评估脚本

set -e

# 进入项目目录
cd "$(dirname "$0")/.."

# 激活虚拟环境（如果存在）
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 运行评估
python -m wind_farm_radar_evaluation.main

echo "评估完成！结果保存在 results/ 目录中"
