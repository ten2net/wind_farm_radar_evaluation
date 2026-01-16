# 数字射频战场仿真系统 - 部署说明

## 系统要求

### 硬件要求
- CPU: 4核或更高
- 内存: 8GB 或更高
- 磁盘空间: 10GB 可用空间
- GPU: 可选（用于加速计算）

### 软件要求
- 操作系统: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- Python: 3.8 或更高版本
- 浏览器: Chrome 90+, Firefox 88+, Edge 90+

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd digital_rf_battlefield_web
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动应用
```bash
python start_app.py
```

或者直接运行：
```bash
streamlit run app.py
```

### 4. 访问应用
打开浏览器访问：http://localhost:8501

## 配置说明

### 环境变量
创建 `.env` 文件：
```env
# Kimi API配置
KIMI_API_KEY=your_kimi_api_key_here

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rf_simulation
DB_USER=username
DB_PASSWORD=password

# 仿真引擎配置
SIMULATION_ENGINE_URL=http://localhost:8000
SIMULATION_TIMEOUT=30
```

### Streamlit配置
修改 `.streamlit/config.toml`：
```toml
[theme]
primaryColor = "#1a73e8"
backgroundColor = "#121212"
secondaryBackgroundColor = "#1e1e1e"
textColor = "#ffffff"
font = "sans serif"

[server]
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

## 生产环境部署

### 使用Docker部署

1. 构建Docker镜像：
```bash
docker build -t rf-simulation-web .
```

2. 运行容器：
```bash
docker run -d -p 8501:8501 --name rf-simulation-web rf-simulation-web
```

### 使用Nginx反向代理

Nginx配置示例：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 使用PM2管理（Linux/Mac）

1. 安装PM2：
```bash
npm install -g pm2
```

2. 启动应用：
```bash
pm2 start "streamlit run app.py --server.port=8501" --name rf-simulation
```

3. 设置开机自启：
```bash
pm2 startup
pm2 save
```

## 安全配置

### HTTPS配置
1. 获取SSL证书（推荐使用Let's Encrypt）：
```bash
sudo certbot --nginx -d your-domain.com
```

2. 更新Nginx配置启用HTTPS

### 访问控制
1. 在Streamlit中启用身份验证：
```python
# 在app.py中添加
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials,
    "rf_simulation",
    "auth",
    cookie_expiry_days=30
)
```

2. 配置防火墙：
```bash
# 只允许特定IP访问
sudo ufw allow from 192.168.1.0/24 to any port 8501
```

## 监控和维护

### 日志管理
应用日志位置：
- 访问日志: `logs/access.log`
- 错误日志: `logs/error.log`
- 应用日志: `app.log`

### 性能监控
1. 使用Streamlit内置监控：
```bash
streamlit run app.py --server.enableCORS=false --server.enableXsrfProtection=true
```

2. 使用第三方监控工具（如Prometheus + Grafana）

### 备份策略
1. 定期备份配置文件：
```bash
# 备份配置
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
# 备份数据
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

2. 使用自动化备份脚本

## 故障排除

### 常见问题

1. **应用无法启动**
   - 检查端口是否被占用：`netstat -tuln | grep 8501`
   - 检查依赖是否安装：`pip list | grep streamlit`

2. **地图无法显示**
   - 检查网络连接
   - 检查Folium和streamlit-folium版本兼容性

3. **Kimi API调用失败**
   - 检查API密钥是否正确
   - 检查网络连接
   - 检查API配额

4. **内存占用过高**
   - 减少同时仿真的目标数量
   - 增加数据清理频率
   - 调整仿真参数

### 调试模式
启用调试模式：
```bash
streamlit run app.py --logger.level=debug
```

查看详细日志：
```bash
tail -f app.log
```

## 性能优化建议

1. **前端优化**
   - 减少页面元素数量
   - 使用分页加载数据
   - 优化图表渲染

2. **后端优化**
   - 使用缓存（Redis/Memcached）
   - 异步处理耗时操作
   - 数据库索引优化

3. **仿真优化**
   - 调整时间步长
   - 减少目标数量
   - 使用简化模型

## 扩展开发

### 添加新页面
1. 在 `pages/` 目录下创建新的Python文件
2. 文件名格式：`序号_图标_页面名.py`
3. 实现页面功能

### 添加新组件
1. 在 `components/` 目录下创建新组件
2. 导入到需要的页面中
3. 确保组件风格一致

### 集成新算法
1. 在 `backend/` 目录下实现算法
2. 通过API接口暴露功能
3. 在前端页面中调用

## 技术支持

如有问题，请联系：
- 邮箱: support@military-tech.com
- 文档: https://docs.rf-simulation.com
- GitHub: https://github.com/your-org/rf-simulation

## 许可证

本项目采用 MIT 许可证。详情见 LICENSE 文件。

