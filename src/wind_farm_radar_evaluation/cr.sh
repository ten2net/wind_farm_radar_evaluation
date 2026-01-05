#!/bin/bash

# 创建主目录
echo "创建项目目录结构..."
mkdir -p radar_factory_app
cd radar_factory_app

# 创建根目录文件
touch app.py
touch requirements.txt
touch README.md

# 创建子目录
mkdir -p models views controllers services utils assets/styles assets/images

# 创建models目录文件
touch models/__init__.py
touch models/radar_models.py
touch models/radar_factory.py
touch models/simulation_models.py

# 创建views目录文件
touch views/__init__.py
touch views/dashboard.py
touch views/radar_editor.py
touch views/comparison_view.py
touch views/simulation_view.py

# 创建controllers目录文件
touch controllers/__init__.py
touch controllers/radar_controller.py
touch controllers/simulation_controller.py
touch controllers/data_controller.py

# 创建services目录文件
touch services/__init__.py
touch services/radar_simulator.py
touch services/performance_calculator.py
touch services/data_processor.py

# 创建utils目录文件
touch utils/__init__.py
touch utils/config.py
touch utils/constants.py
touch utils/helpers.py

# 创建assets目录文件
touch assets/styles/custom.css
touch assets/images/radar_icon.png

# 设置文件权限
chmod 644 app.py requirements.txt README.md
chmod 644 models/*.py views/*.py controllers/*.py services/*.py utils/*.py
chmod 644 assets/styles/custom.css
chmod 644 assets/images/radar_icon.png

echo "项目结构创建完成！"
echo "目录结构:"
find . -type d | sort | sed 's|[^/]*/|- |g' | sed 's|/|  |g'