# 天线分析平台 - API文档

本文档描述了天线分析平台的API接口和数据结构。

## 概述

天线分析平台提供RESTful API和Python SDK两种接口方式，支持天线仿真、分析、数据管理和系统监控功能。

## 基础信息

### 版本
- 当前版本: v1.0.0
- API基础路径: `/api/v1`

### 认证
所有API请求需要包含认证头：
```http
Authorization: Bearer <access_token>
```

### 响应格式
所有API响应使用JSON格式：
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

错误响应：
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "参数验证失败",
    "details": {
      "field": "frequency",
      "issue": "必须为正数"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 天线管理

### 获取天线列表
```
GET /antennas
```

查询参数：
- `page`: 页码，默认1
- `size`: 每页数量，默认20
- `type`: 天线类型过滤
- `frequency_min`: 最小频率(GHz)
- `frequency_max`: 最大频率(GHz)
- `search`: 搜索关键词

响应：
```json
{
  "antennas": [
    {
      "id": "antenna_001",
      "name": "半波偶极子",
      "type": "dipole",
      "frequency_range": [1.0, 2.0],
      "center_frequency": 1.5,
      "gain": 2.15,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 100,
    "pages": 5
  }
}
```

### 创建天线
```
POST /antennas
```

请求体：
```json
{
  "name": "自定义天线",
  "type": "custom",
  "parameters": {
    "center_frequency": 2.4,
    "gain": 5.0,
    "bandwidth": 10.0
  }
}
```

### 获取天线详情
```
GET /antennas/{antenna_id}
```

### 更新天线
```
PUT /antennas/{antenna_id}
```

### 删除天线
```
DELETE /antennas/{antenna_id}
```

## 仿真管理

### 创建仿真任务
```
POST /simulations
```

请求体：
```json
{
  "antenna_id": "antenna_001",
  "parameters": {
    "frequency": 2.4,
    "theta_resolution": 5,
    "phi_resolution": 5,
    "generator_type": "analytical"
  },
  "callback_url": "https://example.com/callback"
}
```

响应：
```json
{
  "simulation_id": "sim_001",
  "status": "pending",
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

### 获取仿真状态
```
GET /simulations/{simulation_id}
```

### 获取仿真结果
```
GET /simulations/{simulation_id}/results
```

响应：
```json
{
  "status": "completed",
  "pattern": {
    "frequency": 2.4,
    "theta_grid": [0, 5, 10, ...],
    "phi_grid": [0, 5, 10, ...],
    "gain_data": [[...], [...]],
    "statistics": {
      "max_gain": 12.5,
      "beamwidth_3db": 24.3
    }
  },
  "download_url": "https://api.antenna-analysis.com/download/sim_001.npy"
}
```

## 分析管理

### 运行分析
```
POST /analysis
```

请求体：
```json
{
  "pattern_id": "pattern_001",
  "analyses": ["beam", "polarization", "efficiency"],
  "parameters": {
    "beamwidth_levels": [-3, -10]
  }
}
```

### 获取分析结果
```
GET /analysis/{analysis_id}
```

## 数据导出

### 导出方向图数据
```
POST /export/pattern
```

请求体：
```json
{
  "pattern_id": "pattern_001",
  "format": "csv",
  "include_metadata": true
}
```

### 导出分析报告
```
POST /export/report
```

请求体：
```json
{
  "analysis_id": "analysis_001",
  "format": "pdf",
  "template": "standard",
  "sections": ["executive_summary", "results", "conclusion"]
}
```

## 系统管理

### 获取系统状态
```
GET /system/status
```

响应：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "5d 3h 20m",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "queue": "healthy"
  },
  "metrics": {
    "active_simulations": 5,
    "active_users": 42,
    "cpu_usage": 35.2,
    "memory_usage": 68.5
  }
}
```

### 获取系统指标
```
GET /system/metrics
```

响应（Prometheus格式）：
```
# HELP antenna_active_users 活跃用户数
# TYPE antenna_active_users gauge
antenna_active_users 42

# HELP antenna_simulation_duration_seconds 仿真耗时
# TYPE antenna_simulation_duration_seconds histogram
antenna_simulation_duration_seconds_bucket{le="1"} 10
antenna_simulation_duration_seconds_bucket{le="5"} 25
```

## WebSocket接口

### 实时仿真状态
```
WS /ws/simulations/{simulation_id}
```

消息格式：
```json
{
  "type": "progress",
  "data": {
    "progress": 0.65,
    "message": "正在计算方向图..."
  }
}
```

### 实时监控数据
```
WS /ws/monitoring
```

## Python SDK示例

### 安装
```bash
pip install antenna-analysis-sdk
```

### 基本使用
```python
from antenna_analysis import AntennaAnalysisClient

# 初始化客户端
client = AntennaAnalysisClient(
    api_key="your_api_key",
    base_url="https://api.antenna-analysis.com"
)

# 创建天线
antenna = client.antennas.create(
    name="测试天线",
    type="dipole",
    parameters={
        "center_frequency": 2.4,
        "gain": 2.15
    }
)

# 运行仿真
simulation = client.simulations.create(
    antenna_id=antenna.id,
    parameters={
        "frequency": 2.4,
        "resolution": 5
    }
)

# 等待仿真完成
simulation.wait_for_completion()

# 获取结果
results = simulation.get_results()

# 运行分析
analysis = client.analysis.run(
    pattern_id=results.pattern_id,
    analyses=["beam", "polarization"]
)

# 导出报告
report = client.export.report(
    analysis_id=analysis.id,
    format="pdf"
)
report.download("report.pdf")
```

### 高级功能
```python
# 批量仿真
simulations = client.simulations.batch_create([
    {"antenna_id": "antenna_1", "frequency": 2.4},
    {"antenna_id": "antenna_2", "frequency": 5.8}
])

# 比较分析
comparison = client.analysis.compare(
    pattern_ids=["pattern_1", "pattern_2"],
    metrics=["gain", "beamwidth", "efficiency"]
)

# 参数扫描
scan_results = client.analysis.parameter_scan(
    antenna_id="antenna_001",
    parameter="frequency",
    values=[2.0, 2.4, 2.8, 3.2],
    analyses=["beam", "efficiency"]
)
```

## 错误码

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| AUTH_REQUIRED | 需要认证 | 401 |
| INVALID_TOKEN | 无效的认证令牌 | 401 |
| PERMISSION_DENIED | 权限不足 | 403 |
| RESOURCE_NOT_FOUND | 资源不存在 | 404 |
| INVALID_PARAMETER | 参数验证失败 | 400 |
| SIMULATION_FAILED | 仿真失败 | 500 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 | 429 |
| SERVICE_UNAVAILABLE | 服务暂时不可用 | 503 |

## 速率限制

- 认证用户: 1000 请求/小时
- API密钥: 10000 请求/小时
- WebSocket连接: 10 连接/分钟

## 数据限制

- 最大方向图分辨率: 1000x1000 点
- 最大仿真频率: 100 GHz
- 最大导出文件大小: 1 GB
- 数据保留时间: 30 天

## 更新日志

### v1.0.0 (2026-01-15)
- 初始版本发布
- 支持基本天线仿真和分析
- 提供RESTful API和Python SDK
- 支持数据导出和报告生成
```
