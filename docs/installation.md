# 安装指南

## 系统要求

- Python 3.8 或更高版本
- 推荐使用 uv 或 pip 进行包管理
- 至少 4GB 内存
- 1GB 可用磁盘空间

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd wind_farm_radar_evaluation
```

### 2. 安装依赖

**使用 uv（推荐）：**
```bash
uv sync
```

**使用 pip：**
```bash
pip install -e .
```

### 3. 验证安装

运行示例脚本验证安装：
```bash
python examples/basic_usage.py
```

## 开发环境设置

### 安装开发依赖

```bash
uv sync --group dev
```

或

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码质量检查

```bash
black --check src/ tests/
flake8 src/ tests/
mypy src/
```
