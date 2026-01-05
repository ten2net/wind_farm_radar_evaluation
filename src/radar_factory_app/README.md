# 雷达工厂 🛰️

基于MVC架构的雷达系统设计与仿真平台，支持多雷达系统设计、性能对比和仿真分析。

## 🌟 功能特性

### 核心功能
- **雷达系统设计**：创建、编辑和管理多种类型的雷达系统
- **性能仿真**：基于radarsimpy的雷达信号处理和目标检测仿真
- **对比分析**：多雷达系统性能对比和优化建议
- **数据可视化**：交互式图表展示雷达性能指标

### 雷达类型支持
- 🚨 远程预警雷达 (Early Warning)
- ✈️ 机载预警雷达 (Airborne AWACS)
- 🎯 火控雷达 (Fire Control)
- 🚢 海事监视雷达 (Maritime Surveillance)

### 仿真功能
- 多目标运动仿真
- 信号处理链仿真
- 目标检测与跟踪
- 性能指标计算

## 📁 项目结构

```
radar_factory_app/
├── app.py                          # 主应用入口
├── requirements.txt               # 依赖包列表
├── README.md                      # 项目说明文档
├── models/                        # 数据模型层
│   ├── __init__.py
│   ├── radar_models.py           # 雷达基础模型
│   └── simulation_models.py      # 仿真数据模型
├── views/                         # 视图层
│   ├── __init__.py
│   ├── dashboard.py              # 主仪表板视图
│   ├── radar_editor.py           # 雷达编辑器视图
│   ├── comparison_view.py        # 对比分析视图
│   └── simulation_view.py        # 仿真结果视图
├── controllers/                   # 控制层
│   ├── __init__.py
│   ├── radar_controller.py       # 雷达数据控制器
│   └── simulation_controller.py   # 仿真控制器
├── services/                      # 业务逻辑层
│   ├── __init__.py
│   ├── radar_simulator.py        # 雷达仿真服务
│   ├── performance_calculator.py # 性能计算服务
│   └── data_processor.py         # 数据处理服务
├── utils/                         # 工具函数
│   ├── __init__.py
│   ├── config.py                 # 配置文件
│   ├── constants.py              # 常量定义
│   └── helpers.py                # 辅助函数
└── assets/                        # 静态资源
    ├── styles/
    │   └── custom.css            # 自定义样式
    └── images/
        └── radar_icon.png        # 应用图标
```

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
streamlit run app.py
```

### 访问应用
打开浏览器访问：http://localhost:8501

## 📦 依赖项

### 主要依赖
- streamlit >= 1.28.0
- radarsimpy >= 0.5.0
- numpy >= 1.24.0
- pandas >= 2.0.0
- plotly >= 5.15.0
- matplotlib >= 3.7.0
- scipy >= 1.10.0

### 可选依赖
- openpyxl (用于Excel导出)
- seaborn (用于高级图表)

## 🔧 配置说明

### 环境变量
```bash
# 应用配置
RADAR_FACTORY_DEBUG=True
RADAR_FACTORY_PORT=8501
RADAR_FACTORY_HOST=0.0.0.0

# 仿真配置
SIMULATION_MAX_DURATION=600
SIMULATION_MAX_TARGETS=100
```

### 配置文件
创建 `config/settings.yaml` 文件进行自定义配置：

```yaml
application:
  name: "雷达工厂工厂"
  version: "1.0.0"
  debug: false
  
simulation:
  default_duration: 60.0
  time_step: 0.1
  max_targets: 50
  
visualization:
  theme: "light"
  chart_style: "plotly"
  animation_enabled: true
  
data:
  auto_save: true
  save_interval: 300
  export_formats: ["json", "csv", "excel"]
```

## 🎯 使用指南

### 1. 雷达设计
1. 点击"雷达设计"进入编辑器
2. 选择雷达类型（预警、机载、火控、海事）
3. 配置发射机、天线、信号处理参数
4. 保存雷达配置

### 2. 仿真分析
1. 选择要仿真的雷达
2. 配置仿真场景（目标、环境）
3. 设置仿真参数
4. 运行仿真并查看结果

### 3. 性能对比
1. 选择要对比的雷达
2. 查看各项性能指标对比
3. 分析雷达优势和不足
4. 获取优化建议

### 4. 数据导出
支持多种格式导出：
- JSON：完整数据导出
- CSV：表格数据导出
- Excel：结构化数据导出
- PDF：报告导出

## 📊 性能指标

平台计算的主要性能指标包括：

### 探测性能
- 最大探测距离
- 距离分辨率
- 角度分辨率
- 速度分辨率
- 检测概率
- 虚警概率

### 系统性能
- 功率孔径积
- 搜索性能
- 跟踪性能
- 抗干扰能力
- 多目标处理能力

### 环境适应性
- 大气衰减
- 雨衰影响
- 杂波抑制
- 多路径效应

## 🔄 更新日志

### v1.0.0 (2025-01-20)
- 初始版本发布
- 支持雷达系统设计与建模
- 集成radarsimpy仿真引擎
- 实现MVC架构设计
- 提供完整的数据可视化

### 计划功能
- [ ] 多用户协作
- [ ] 云端仿真计算
- [ ] 实时数据流处理
- [ ] 机器学习优化
- [ ] API接口服务

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范
- 遵循PEP 8代码规范
- 添加适当的注释和文档
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情

## 📞 支持与反馈

- 问题反馈：https://github.com/your-repo/radar-factory/issues
- 功能建议：https://github.com/your-repo/radar-factory/discussions
- 邮件支持：radar.factory@example.com
- 文档网站：https://your-docs-site.com

## 🙏 致谢

感谢以下开源项目的支持：

- https://github.com/radarsimpy/radarsimpy - 雷达仿真引擎
- https://streamlit.io - Web应用框架
- https://plotly.com - 数据可视化库
- https://numpy.org - 科学计算库

---

**雷达工厂** - 让雷达系统设计更简单、更智能！ 🚀

