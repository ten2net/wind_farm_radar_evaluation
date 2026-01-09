#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电子战对抗仿真系统 - 安装配置文件
"""

from setuptools import setup, find_packages
import os
import re

# 读取版本号
with open('src/__init__.py', 'r') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        version = '1.0.0'

# 读取README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# 读取requirements
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

setup(
    name="ew-combat-system",
    version=version,
    author="电子战仿真实验室",
    author_email="support@ew-simulation.com",
    description="专业的电子战体系对抗仿真与评估平台",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ew-combat-system",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/ew-combat-system/issues",
        "Documentation": "https://ew-simulation.com/docs",
        "Source Code": "https://github.com/yourusername/ew-combat-system",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: Streamlit",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pre-commit>=3.5.0",
            "sphinx>=7.2.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
        "full": [
            "geoviews[recommended]>=1.9.1",
            "holoviews>=1.16.0",
            "bokeh>=3.3.0",
            "plotly>=5.18.0",
            "cartopy>=0.21.0",
            "pydeck>=0.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ew-sim=ew_combat_system.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ew_combat_system": [
            "config/*.yaml",
            "config/*.yml",
            "static/*",
            "static/**/*",
        ],
    },
    data_files=[
        ("share/ew-combat-system/config", ["config/radar_database.yaml"]),
        ("share/ew-combat-system/config", ["config/scenarios.yaml"]),
        ("share/ew-combat-system/config", ["config/environment.yaml"]),
        ("share/ew-combat-system/config", ["config/logging.yaml"]),
    ],
    keywords=[
        "electronic warfare",
        "radar simulation",
        "jammer simulation",
        "combat simulation",
        "military simulation",
        "signal propagation",
        "ew simulation",
    ],
    platforms=["any"],
    license="MIT",
    zip_safe=False,
)