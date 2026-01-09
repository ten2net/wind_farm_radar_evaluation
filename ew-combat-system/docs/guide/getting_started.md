# 电子战对抗仿真系统 - 入门指南

## 系统概述

电子战对抗仿真系统是一个专业的电子战体系对抗仿真平台，支持一对一、多对一、多对多等对抗想定，提供完整的电磁环境构建、对抗仿真、效能评估和可视化功能。

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository_url>
cd ew-combat-system

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行系统

```bash
# 启动Streamlit应用
streamlit run app.py
```

在浏览器中访问 `http://localhost:8501`

### 3. 基本使用流程

1. **选择想定**
   - 在"想定配置"标签页中选择对抗类型
   - 配置雷达和干扰机参数
   - 点击"创建对抗想定"

2. **运行仿真**
   - 在"仿真控制"标签页中设置参数
   - 点击"开始仿真"
   - 查看实时进度和结果

3. **分析结果**
   - 在"结果分析"标签页中查看可视化
   - 分析效能指标
   - 导出数据和图表

## 核心功能

### 1. 对抗想定

系统支持三种主要对抗想定：

- **一对一对抗**: 单雷达 vs 单干扰机
- **多对一对抗**: 多雷达协同 vs 单干扰机
- **多对多对抗**: 雷达网 vs 干扰网体系对抗

### 2. 实体配置

支持配置以下实体：

- **雷达系统**: 预警雷达、火控雷达等
- **干扰系统**: 远距支援干扰机、自卫干扰机等
- **目标系统**: 飞机、导弹、舰船等

### 3. 仿真引擎

基于物理模型的电子战仿真：

- 信号传播模型
- 干扰效果计算
- 网络对抗分析
- 效能评估指标

### 4. 可视化分析

- 地理态势图
- 信号分析图表
- 频谱分析
- 3D地形可视化

## 配置说明

### 雷达数据库

编辑 `config/radar_database.yaml` 添加或修改雷达/干扰机型号：

```yaml
radar_types:
  early_warning:
    base_params:
      name: "预警雷达"
      frequency: 3.0
      power: 200
    variants:
      - id: "EW-001"
        name: "空警-2000"
        params:
          lat: 39.9
          lon: 116.4
```

### 想定配置

编辑 `config/scenarios.yaml` 创建预设想定：

```yaml
one_vs_one:
  name: "标准对抗"
  radar:
    type: "early_warning"
    variant: "空警-2000"
  jammer:
    type: "standoff_jammer"
    variant: "EA-18G咆哮者"
```

### 环境配置

编辑 `config/environment.yaml` 配置传播环境：

```yaml
terrain_types:
  flat:
    name: "平原"
    roughness: 0.1
atmosphere_types:
  standard:
    name: "标准大气"
    refractivity: 1.0
```

## 开发指南

### 项目结构

```
ew-combat-system/
├── config/           # 配置文件
├── src/             # 源代码
│   ├── core/        # 核心模块
│   ├── visualization/ # 可视化模块
│   ├── ui/          # 用户界面
│   └── utils/       # 工具函数
├── data/            # 数据文件
├── static/          # 静态资源
├── tests/           # 测试用例
└── app.py           # 主应用
```

### 添加新功能

1. **添加新实体类型**

```python
# 在 src/core/entities/ 中添加新实体类
@dataclass
class NewEntity(Entity):
    # 实现实体逻辑
    pass
```

2. **添加新想定**

```python
# 在 src/core/patterns/strategy.py 中添加新想定类
class NewScenario(CombatScenario):
    def setup(self, config):
        # 实现想定设置
        pass
```

3. **添加新可视化**

```python
# 在 src/visualization/ 中添加新可视化类
class NewVisualizer:
    @staticmethod
    def create_new_visualization(data):
        # 创建可视化
        pass
```

## 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t ew-simulation .

# 运行容器
docker run -p 8501:8501 ew-simulation
```

### Kubernetes部署

```bash
# 部署到Kubernetes
kubectl apply -f deployment/kubernetes/
```

## 故障排除

### 常见问题

1. **应用无法启动**
   - 检查依赖安装
   - 检查端口占用
   - 查看日志文件

2. **地图不显示**
   - 检查网络连接
   - 检查API密钥
   - 尝试离线模式

3. **仿真速度慢**
   - 减少实体数量
   - 降低分辨率
   - 启用缓存

### 获取帮助

- 查看文档: `docs/` 目录
- 查看示例: `examples/` 目录
- 查看测试: `tests/` 目录
- 查看日志: `logs/` 目录

## 许可证

本项目遵循 MIT 许可证。详情请参阅 LICENSE 文件。
