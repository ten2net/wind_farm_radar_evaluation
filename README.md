# 风电场雷达影响评估系统

一个用于评估风电场对海岸监视雷达影响的专业仿真分析工具。

## 功能特性

- **雷达系统建模**：完整的雷达参数配置和信号建模
- **风电场场景**：支持批量风机坐标导入和转换
- **多径效应分析**：考虑海面反射和风机旋转影响
- **目标检测评估**：空中和海面目标的检测性能分析
- **专业可视化**：距离-多普勒图、PPI显示、影响分析图
- **自动报告生成**：生成完整的评估报告

## 快速开始

### 安装依赖

使用 uv（推荐）：
```bash
uv sync
```

或使用 pip：
```bash
pip install -e .
```

### 基本使用

```python
from wind_farm_radar_evaluation import main

# 运行评估
main()
```

### 配置系统

编辑 `conf/config.yaml` 文件来配置系统参数：

```yaml
radar:
  name: "海岸雷达"
  frequency: 9.4e9
  # ... 其他参数

wind_farm:
  turbine_coordinates:
    - [36.600, 120.600, 0]  # 风机坐标
    # ... 更多风机
```

## 项目结构

```
wind_farm_radar_evaluation/
├── conf/                 # 配置文件
├── src/                  # 源代码
├── data/                 # 数据文件
├── results/              # 结果输出
├── tests/                # 测试代码
├── docs/                 # 文档
└── examples/             # 使用示例
```

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black src/ tests/
```

### 类型检查

```bash
mypy src/
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
