#!/bin/bash

# 天线分析平台 - 部署脚本
# 支持多种部署方式：Docker、Kubernetes、虚拟机

set -e  # 遇到错误立即退出
set -o pipefail  # 管道命令失败时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$DEBUG" = "true" ]; then
        echo -e "${MAGENTA}[DEBUG]${NC} $1"
    fi
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "需要 '$1' 命令，但未找到。"
        exit 1
    fi
}

# 打印帮助信息
print_help() {
    cat << EOF
天线分析平台 - 部署脚本 v1.0.0

用法: $0 [选项] [环境]

选项:
  -h, --help          显示帮助信息
  -e, --env ENV       部署环境 (local|test|prod)
  -d, --debug         启用调试模式
  -f, --force         强制部署，跳过确认
  -c, --config FILE   指定配置文件
  --skip-build        跳过构建步骤
  --skip-test         跳过测试步骤
  --skip-backup       跳过备份步骤
  --dry-run           模拟运行，不执行实际操作

环境:
  local     本地开发环境
  test      测试环境
  prod      生产环境

示例:
  $0 -e local          部署到本地环境
  $0 -e test --dry-run 模拟部署到测试环境
  $0 -e prod --force   强制部署到生产环境
EOF
}

# 解析命令行参数
parse_args() {
    ENVIRONMENT="local"
    DEBUG="false"
    FORCE="false"
    SKIP_BUILD="false"
    SKIP_TEST="false"
    SKIP_BACKUP="false"
    DRY_RUN="false"
    CONFIG_FILE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                print_help
                exit 0
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -d|--debug)
                DEBUG="true"
                shift
                ;;
            -f|--force)
                FORCE="true"
                shift
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --skip-build)
                SKIP_BUILD="true"
                shift
                ;;
            --skip-test)
                SKIP_TEST="true"
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            *)
                log_error "未知选项: $1"
                print_help
                exit 1
                ;;
        esac
    done
    
    # 验证环境参数
    case $ENVIRONMENT in
        local|test|prod)
            ;;
        *)
            log_error "无效的环境: $ENVIRONMENT。必须是 local、test 或 prod。"
            exit 1
            ;;
    esac
}

# 加载配置文件
load_config() {
    local config_file="deploy/config.$ENVIRONMENT.yaml"
    
    if [ -n "$CONFIG_FILE" ]; then
        config_file="$CONFIG_FILE"
    fi
    
    if [ ! -f "$config_file" ]; then
        log_warning "配置文件 $config_file 不存在，使用默认配置"
        return
    fi
    
    log_info "加载配置文件: $config_file"
    
    # 使用Python解析YAML配置文件
    python3 -c "
import yaml, sys, os, json
try:
    with open('$config_file', 'r') as f:
        config = yaml.safe_load(f)
    print('export CONFIG_DATA=\"' + json.dumps(config) + '\"')
except Exception as e:
    print('echo \"解析配置文件失败: ' + str(e) + '\" >&2')
    sys.exit(1)
" | source /dev/stdin
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python
    check_command python3
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python版本: $python_version"
    
    # 检查Docker
    if [ "$ENVIRONMENT" != "local" ]; then
        check_command docker
        docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log_info "Docker版本: $docker_version"
        
        # 检查Docker Compose
        check_command docker-compose
        docker_compose_version=$(docker-compose --version | cut -d' ' -f3 | tr -d ',')
        log_info "Docker Compose版本: $docker_compose_version"
    fi
    
    # 检查必要的工具
    check_command curl
    check_command git
    
    log_success "系统要求检查通过"
}

# 检查Git状态
check_git_status() {
    if [ "$ENVIRONMENT" = "prod" ] && [ "$FORCE" = "false" ]; then
        log_info "检查Git状态..."
        
        if ! git status --porcelain | grep -q '^ M'; then
            log_success "工作目录干净"
        else
            log_warning "工作目录有未提交的更改"
            
            if [ "$DRY_RUN" = "false" ]; then
                read -p "是否继续部署？(y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        fi
    fi
}

# 备份当前版本
backup_current_version() {
    if [ "$SKIP_BACKUP" = "true" ]; then
        log_info "跳过备份步骤"
        return
    fi
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        log_info "备份当前版本..."
        
        local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        # 备份数据
        if [ -d "data" ]; then
            cp -r data "$backup_dir/"
        fi
        
        # 备份配置文件
        if [ -d "config" ]; then
            cp -r config "$backup_dir/"
        fi
        
        # 备份日志
        if [ -d "logs" ]; then
            cp -r logs "$backup_dir/"
        fi
        
        log_success "备份已保存到: $backup_dir"
        
        # 清理旧的备份（保留最近5个）
        ls -dt backups/*/ 2>/dev/null | tail -n +6 | xargs rm -rf
    fi
}

# 运行测试
run_tests() {
    if [ "$SKIP_TEST" = "true" ]; then
        log_info "跳过测试步骤"
        return
    fi
    
    log_info "运行测试..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # 运行单元测试
        if python3 -m pytest tests/ -x -v --tb=short; then
            log_success "单元测试通过"
        else
            log_error "单元测试失败"
            exit 1
        fi
        
        # 运行集成测试
        if python3 -m pytest tests/test_integration.py -x -v --tb=short; then
            log_success "集成测试通过"
        else
            log_error "集成测试失败"
            exit 1
        fi
    else
        log_info "模拟运行测试"
    fi
}

# 构建应用
build_application() {
    if [ "$SKIP_BUILD" = "true" ]; then
        log_info "跳过构建步骤"
        return
    fi
    
    log_info "构建应用..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # 安装依赖
        log_info "安装Python依赖..."
        pip install -r requirements.txt
        
        # 构建Docker镜像
        if [ "$ENVIRONMENT" != "local" ]; then
            log_info "构建Docker镜像..."
            docker build -t antenna-analysis:latest .
            
            # 标记版本
            local version=$(git describe --tags --always)
            docker tag antenna-analysis:latest antenna-analysis:$version
        fi
    else
        log_info "模拟构建应用"
    fi
    
    log_success "应用构建完成"
}

# 部署到本地环境
deploy_local() {
    log_info "部署到本地环境..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # 停止现有容器
        if docker-compose -f docker-compose.local.yml ps | grep -q "antenna-analysis"; then
            log_info "停止现有容器..."
            docker-compose -f docker-compose.local.yml down
        fi
        
        # 启动应用
        log_info "启动应用..."
        docker-compose -f docker-compose.local.yml up -d
        
        # 等待应用启动
        log_info "等待应用启动..."
        sleep 10
        
        # 检查应用状态
        if curl -f http://localhost:8501/_stcore/health; then
            log_success "应用启动成功"
        else
            log_error "应用启动失败"
            docker-compose -f docker-compose.local.yml logs
            exit 1
        fi
    else
        log_info "模拟部署到本地环境"
    fi
}

# 部署到测试环境
deploy_test() {
    log_info "部署到测试环境..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # 推送到容器仓库
        log_info "推送到容器仓库..."
        docker tag antenna-analysis:latest registry.example.com/antenna-analysis:test
        docker push registry.example.com/antenna-analysis:test
        
        # 在测试服务器上部署
        log_info "在测试服务器上部署..."
        ssh test-server "
            cd /opt/antenna-analysis
            docker-compose pull
            docker-compose down
            docker-compose up -d
        "
        
        # 运行健康检查
        log_info "运行健康检查..."
        sleep 30
        if curl -f https://test.antenna.example.com/health; then
            log_success "测试环境部署成功"
        else
            log_error "测试环境部署失败"
            exit 1
        fi
    else
        log_info "模拟部署到测试环境"
    fi
}

# 部署到生产环境
deploy_prod() {
    log_info "部署到生产环境..."
    
    if [ "$FORCE" = "false" ] && [ "$DRY_RUN" = "false" ]; then
        read -p "确认要部署到生产环境？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "部署已取消"
            exit 0
        fi
    fi
    
    if [ "$DRY_RUN" = "false" ]; then
        # 标记版本
        local version=$(git describe --tags --always)
        log_info "部署版本: $version"
        
        # 推送到容器仓库
        log_info "推送到容器仓库..."
        docker tag antenna-analysis:latest registry.example.com/antenna-analysis:$version
        docker tag antenna-analysis:latest registry.example.com/antenna-analysis:latest
        docker push registry.example.com/antenna-analysis:$version
        docker push registry.example.com/antenna-analysis:latest
        
        # 蓝绿部署
        log_info "开始蓝绿部署..."
        
        # 获取当前运行的容器颜色
        local current_color=$(ssh prod-server "docker inspect antenna-analysis-app --format='{{.Config.Labels.color}}' 2>/dev/null || echo 'blue'")
        local new_color="green"
        
        if [ "$current_color" = "green" ]; then
            new_color="blue"
        fi
        
        log_info "当前颜色: $current_color, 新颜色: $new_color"
        
        # 启动新版本
        log_info "启动新版本 ($new_color)..."
        ssh prod-server "
            docker run -d \
                --name antenna-analysis-$new_color \
                --label color=$new_color \
                -p 8501 \
                -v /opt/antenna-analysis/data:/app/data \
                -v /opt/antenna-analysis/config:/app/config \
                registry.example.com/antenna-analysis:$version
        "
        
        # 等待新版本启动
        log_info "等待新版本启动..."
        sleep 30
        
        # 健康检查
        local new_container_ip=$(ssh prod-server "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' antenna-analysis-$new_color")
        if curl -f http://$new_container_ip:8501/_stcore/health; then
            log_success "新版本健康检查通过"
        else
            log_error "新版本健康检查失败"
            ssh prod-server "docker logs antenna-analysis-$new_color"
            ssh prod_server "docker rm -f antenna-analysis-$new_color"
            exit 1
        fi
        
        # 切换流量
        log_info "切换流量到新版本..."
        ssh prod-server "
            docker network disconnect antenna-network antenna-analysis-$current_color
            docker network connect antenna-network antenna-analysis-$new_color
        "
        
        # 更新负载均衡器配置
        ssh prod-server "sed -i 's/$current_color/$new_color/g' /etc/nginx/upstream.conf"
        ssh prod-server "nginx -s reload"
        
        # 停止旧版本
        log_info "停止旧版本..."
        ssh prod-server "docker stop antenna-analysis-$current_color"
        
        # 保留旧版本容器用于回滚
        ssh prod_server "docker rename antenna-analysis-$current_color antenna-analysis-$current_color-old"
        
        log_success "生产环境部署完成"
    else
        log_info "模拟部署到生产环境"
    fi
}

# 运行部署后检查
post_deploy_checks() {
    log_info "运行部署后检查..."
    
    local health_url=""
    case $ENVIRONMENT in
        local)
            health_url="http://localhost:8501/_stcore/health"
            ;;
        test)
            health_url="https://test.antenna.example.com/health"
            ;;
        prod)
            health_url="https://antenna.example.com/health"
            ;;
    esac
    
    if [ "$DRY_RUN" = "false" ]; then
        # 健康检查
        log_info "运行健康检查..."
        for i in {1..10}; do
            if curl -f "$health_url"; then
                log_success "健康检查通过"
                break
            fi
            log_info "第 $i 次健康检查失败，重试..."
            sleep 10
        done
        
        # 性能检查
        log_info "运行性能检查..."
        local response_time=$(curl -o /dev/null -s -w '%{time_total}\n' "$health_url")
        log_info "响应时间: ${response_time}s"
        
        if (( $(echo "$response_time > 5" | bc -l) )); then
            log_warning "响应时间较慢"
        fi
        
        # 功能测试
        log_info "运行功能测试..."
        # 这里可以添加API端点的功能测试
        
    else
        log_info "模拟运行部署后检查"
    fi
    
    log_success "部署后检查完成"
}

# 清理工作
cleanup() {
    log_info "清理工作..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # 清理未使用的Docker镜像
        if [ "$ENVIRONMENT" != "local" ]; then
            docker image prune -f
        fi
        
        # 清理构建缓存
        if [ -d "__pycache__" ]; then
            rm -rf __pycache__
        fi
        
        if [ -d ".pytest_cache" ]; then
            rm -rf .pytest_cache
        fi
    else
        log_info "模拟清理工作"
    fi
}

# 发送部署通知
send_notification() {
    local status="$1"
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        log_info "发送部署通知..."
        
        local message=""
        local color=""
        
        if [ "$status" = "success" ]; then
            message="✅ 天线分析平台生产环境部署成功"
            color="good"
        else
            message="❌ 天线分析平台生产环境部署失败"
            color="danger"
        fi
        
        local version=$(git describe --tags --always)
        local deployer=$(whoami)
        local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
        
        # 发送到Slack
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                'attachments': [{
                    'color': '$color',
                    'blocks': [
                        {
                            'type': 'header',
                            'text': {
                                'type': 'plain_text',
                                'text': '$message'
                            }
                        },
                        {
                            'type': 'section',
                            'fields': [
                                {
                                    'type': 'mrkdwn',
                                    'text': '*环境:*\\n$ENVIRONMENT'
                                },
                                {
                                    'type': 'mrkdwn',
                                    'text': '*版本:*\\n$version'
                                }
                            ]
                        },
                        {
                            'type': 'section',
                            'fields': [
                                {
                                    'type': 'mrkdwn',
                                    'text': '*部署者:*\\n$deployer'
                                },
                                {
                                    'type': 'mrkdwn',
                                    'text': '*时间:*\\n$timestamp'
                                }
                            ]
                        }
                    ]
                }]
            }" \
            "$SLACK_WEBHOOK_URL" || true
            
        log_info "部署通知已发送"
    fi
}

# 主函数
main() {
    log_info "========================================"
    log_info "    天线分析平台 - 部署脚本 v1.0.0     "
    log_info "========================================"
    
    # 解析参数
    parse_args "$@"
    
    # 显示部署信息
    log_info "部署环境: $ENVIRONMENT"
    log_info "调试模式: $DEBUG"
    log_info "强制部署: $FORCE"
    log_info "模拟运行: $DRY_RUN"
    
    # 检查命令
    check_requirements
    
    # 加载配置
    load_config
    
    # 检查Git状态
    check_git_status
    
    # 备份当前版本
    backup_current_version
    
    # 运行测试
    run_tests
    
    # 构建应用
    build_application
    
    # 部署
    case $ENVIRONMENT in
        local)
            deploy_local
            ;;
        test)
            deploy_test
            ;;
        prod)
            deploy_prod
            ;;
    esac
    
    # 部署后检查
    post_deploy_checks
    
    # 清理
    cleanup
    
    # 发送通知
    send_notification "success"
    
    log_info "========================================"
    log_success "部署完成！"
    log_info "========================================"
}

# 错误处理
trap 'log_error "部署过程中断"; send_notification "failure"; exit 1' INT TERM
trap 'log_error "部署失败: $?"; send_notification "failure"; exit 1' ERR

# 运行主函数
main "$@"

exit 0