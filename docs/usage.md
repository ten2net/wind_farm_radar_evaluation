# 使用指南

## 基本用法

### 1. 配置系统

编辑 `conf/config.yaml` 文件来配置雷达、风电场和评估参数。

### 2. 运行评估

```python
from wind_farm_radar_evaluation import main

# 运行完整评估
main()
```

### 3. 查看结果

评估结果将保存在 `results/` 目录中，包括：
- 图表文件（PNG/PDF格式）
- 评估报告
- 数据导出文件

## 高级用法

### 自定义配置

```python
from wind_farm_radar_evaluation.config.configuration import get_config_manager

# 加载自定义配置
config_manager = get_config_manager("my_config.yaml")

# 动态修改配置
config_manager.update_config('radar', 'frequency', 10e9)
```

### 批量处理

系统支持批量处理多个风电场场景，具体用法参考示例代码。
