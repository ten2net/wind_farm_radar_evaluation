#!/bin/bash

# 电子战对抗仿真系统启动脚本
# 适用于Linux和Mac系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python_version() {
    local python_cmd="python3"
    if command -v python3 &> /dev/null; then
        python_cmd="python3"
    elif command -v python &> /dev/null; then
        python_cmd="python"
    else
        log_error "未找到Python，请安装Python 3.8或更高版本"
        exit 1
    fi
    
    local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local major=$($python_cmd -c "import sys; print(sys.version_info.major)")
    local minor=$($python_cmd -c "import sys; print(sys.version_info.minor)")
    
    if [ $major -lt 3 ] || { [ $major -eq 3 ] && [ $minor -lt 8 ]; }; then
        log_error "需要Python 3.8或更高版本，当前版本: $version"
        exit 1
    fi
    
    log_info "Python版本: $version"
    echo "$python_cmd"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查必要的系统包
    local missing_packages=()
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        missing_packages+=("git")
    fi
    
    # 检查Docker（可选）
    if ! command -v docker &> /dev/null; then
        log_warn "Docker未安装，将使用本地模式运行"
    fi
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        log_warn "缺少系统包: ${missing_packages[*]}"
        log_info "请手动安装缺少的包"
    fi
}

# 设置虚拟环境
setup_venv() {
    local python_cmd=$1
    
    log_info "设置Python虚拟环境..."
    
    if [ ! -d "venv" ]; then
        $python_cmd -m venv venv
        log_info "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    if [ -f "requirements-dev.txt" ]; then
        log_info "安装开发依赖..."
        pip install -r requirements-dev.txt
    fi
}

# 检查配置文件
check_config_files() {
    log_info "检查配置文件..."
    
    # 创建必要的配置文件
    if [ ! -f "config/radar_database.yaml" ]; then
        log_warn "配置文件不存在: config/radar_database.yaml"
        log_info "将创建默认配置文件"
        mkdir -p config
        cp config/radar_database.yaml.example config/radar_database.yaml 2>/dev/null || true
    fi
    
    if [ ! -f "config/scenarios.yaml" ]; then
        log_warn "配置文件不存在: config/scenarios.yaml"
        cp config/scenarios.yaml.example config/scenarios.yaml 2>/dev/null || true
    fi
    
    if [ ! -f "config/environment.yaml" ]; then
        log_warn "配置文件不存在: config/environment.yaml"
        cp config/environment.yaml.example config/environment.yaml 2>/dev/null || true
    fi
}

# 启动应用
start_application() {
    local mode=$1
    
    log_info "启动电子战对抗仿真系统..."
    
    if [ "$mode" = "docker" ]; then
        start_docker
    else
        start_local
    fi
}

# 本地启动
start_local() {
    log_info "启动Streamlit应用..."
    
    # 检查Streamlit是否安装
    if ! python -c "import streamlit" &> /dev/null; then
        log_error "Streamlit未安装，请先安装依赖"
        exit 1
    fi
    
    # 启动应用
    streamlit run app.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --theme.base="dark" \
        --browser.serverAddress="localhost" \
        --server.fileWatcherType="none" \
        --server.headless=false
}

# Docker启动
start_docker() {
    log_info "使用Docker启动..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，无法使用Docker模式"
        exit 1
    fi
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker build -t ew-simulation .
    
    # 运行容器
    log_info "启动Docker容器..."
    docker run -d \
        -p 8501:8501 \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/config:/app/config \
        -v $(pwd)/logs:/app/logs \
        --name ew-simulation \
        ew-simulation
    
    log_info "Docker容器已启动，应用运行在: http://localhost:8501"
}

# 停止应用
stop_application() {
    local mode=$1
    
    if [ "$mode" = "docker" ]; then
        log_info "停止Docker容器..."
        docker stop ew-simulation 2>/dev/null || true
        docker rm ew-simulation 2>/dev/null || true
    else
        log_info "停止本地应用..."
        pkill -f "streamlit run app.py" 2>/dev/null || true
    fi
}

# 显示状态
show_status() {
    log_info "系统状态检查..."
    
    # 检查端口占用
    if lsof -i:8501 &> /dev/null; then
        log_info "端口8501已被占用"
        lsof -i:8501
    else
        log_info "端口8501空闲"
    fi
    
    # 检查虚拟环境
    if [ -d "venv" ]; then
        log_info "虚拟环境: 已存在"
    else
        log_warn "虚拟环境: 不存在"
    fi
    
    # 检查配置文件
    config_files=("radar_database.yaml" "scenarios.yaml" "environment.yaml")
    for config in "${config_files[@]}"; do
        if [ -f "config/$config" ]; then
            log_info "配置文件 $config: 存在"
        else
            log_warn "配置文件 $config: 不存在"
        fi
    done
}

# 显示帮助
show_help() {
    echo -e "${BLUE}电子战对抗仿真系统启动脚本${NC}"
    echo ""
    echo "用法: ./start.sh [选项]"
    echo ""
    echo "选项:"
    echo "  start          启动应用 (默认)"
    echo "  stop           停止应用"
    echo "  restart        重启应用"
    echo "  status         显示状态"
    echo "  docker         使用Docker模式"
    echo "  local          使用本地模式 (默认)"
    echo "  update         更新依赖"
    echo "  test           运行测试"
    echo "  clean          清理临时文件"
    echo "  help           显示此帮助"
    echo ""
    echo "示例:"
    echo "  ./start.sh              # 本地启动"
    echo "  ./start.sh docker       # Docker启动"
    echo "  ./start.sh status       # 查看状态"
    echo "  ./start.sh stop         # 停止应用"
}

# 更新依赖
update_dependencies() {
    log_info "更新Python依赖..."
    
    source venv/bin/activate
    pip install --upgrade -r requirements.txt
    
    if [ -f "requirements-dev.txt" ]; then
        pip install --upgrade -r requirements-dev.txt
    fi
    
    log_info "依赖更新完成"
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    source venv/bin/activate
    
    # 运行单元测试
    if [ -d "tests/unit" ]; then
        log_info "运行单元测试..."
        python -m pytest tests/unit/ -v
    fi
    
    # 运行集成测试
    if [ -d "tests/integration" ]; then
        log_info "运行集成测试..."
        python -m pytest tests/integration/ -v
    fi
    
    # 运行性能测试
    if [ -d "tests/performance" ]; then
        log_info "运行性能测试..."
        python -m pytest tests/performance/ -v
    fi
    
    # 运行所有测试
    log_info "运行所有测试..."
    python -m pytest tests/ -v
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    
    # 清理Python缓存
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name ".coverage" -delete
    
    # 清理构建文件
    rm -rf build/ dist/ *.egg-info/
    
    # 清理日志文件
    if [ -d "logs" ]; then
        find logs -type f -name "*.log" -mtime +7 -delete
    fi
    
    # 清理数据文件
    if [ -d "data/temp" ]; then
        rm -rf data/temp/*
    fi
    
    log_info "清理完成"
}

# 主函数
main() {
    local action="start"
    local mode="local"
    
    # 解析参数
    while [ $# -gt 0 ]; do
        case $1 in
            start|stop|restart|status|update|test|clean|help)
                action=$1
                shift
                ;;
            docker)
                mode="docker"
                shift
                ;;
            local)
                mode="local"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行操作
    case $action in
        start)
            python_cmd=$(check_python_version)
            check_dependencies
            setup_venv $python_cmd
            check_config_files
            start_application $mode
            ;;
        stop)
            stop_application $mode
            ;;
        restart)
            stop_application $mode
            sleep 2
            python_cmd=$(check_python_version)
            start_application $mode
            ;;
        status)
            show_status
            ;;
        update)
            update_dependencies
            ;;
        test)
            python_cmd=$(check_python_version)
            setup_venv $python_cmd
            run_tests
            ;;
        clean)
            cleanup
            ;;
        help)
            show_help
            ;;
    esac
}

# 运行主函数
main "$@"
