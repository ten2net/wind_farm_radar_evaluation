@echo off
REM 电子战对抗仿真系统启动脚本
REM 适用于Windows系统

setlocal enabledelayedexpansion

REM 颜色定义
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "RED=%ESC%[31m"
set "BLUE=%ESC%[34m"
set "NC=%ESC%[0m"

REM 打印带颜色的消息
:log_info
    echo %GREEN%[INFO]%NC% %*
    goto :eof

:log_warn
    echo %YELLOW%[WARN]%NC% %*
    goto :eof

:log_error
    echo %RED%[ERROR]%NC% %*
    goto :eof

REM 检查Python版本
:check_python_version
    where python >nul 2>nul
    if errorlevel 1 (
        call :log_error "未找到Python，请安装Python 3.8或更高版本"
        exit /b 1
    )
    
    for /f "tokens=2 delims= " %%i in ('python -c "import sys; print(sys.version)"') do set "version=%%i"
    for /f "tokens=1,2 delims=." %%i in ("%version%") do (
        set "major=%%i"
        set "minor=%%j"
    )
    
    if %major% LSS 3 (
        call :log_error "需要Python 3.8或更高版本，当前版本: %version%"
        exit /b 1
    )
    
    if %major% EQU 3 if %minor% LSS 8 (
        call :log_error "需要Python 3.8或更高版本，当前版本: %version%"
        exit /b 1
    )
    
    call :log_info "Python版本: %version%"
    goto :eof

REM 检查依赖
:check_dependencies
    call :log_info "检查系统依赖..."
    
    REM 检查Git
    where git >nul 2>nul
    if errorlevel 1 (
        call :log_warn "Git未安装"
    )
    
    REM 检查Docker
    where docker >nul 2>nul
    if errorlevel 1 (
        call :log_warn "Docker未安装，将使用本地模式运行"
    )
    goto :eof

REM 设置虚拟环境
:setup_venv
    call :log_info "设置Python虚拟环境..."
    
    if not exist venv (
        python -m venv venv
        call :log_info "虚拟环境创建完成"
    ) else (
        call :log_info "虚拟环境已存在"
    )
    
    REM 激活虚拟环境
    call venv\Scripts\activate.bat
    
    REM 升级pip
    python -m pip install --upgrade pip
    
    REM 安装依赖
    call :log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    if exist requirements-dev.txt (
        call :log_info "安装开发依赖..."
        pip install -r requirements-dev.txt
    )
    goto :eof

REM 检查配置文件
:check_config_files
    call :log_info "检查配置文件..."
    
    if not exist config\radar_database.yaml (
        call :log_warn "配置文件不存在: config\radar_database.yaml"
        mkdir config 2>nul
        copy config\radar_database.yaml.example config\radar_database.yaml 2>nul
    )
    
    if not exist config\scenarios.yaml (
        call :log_warn "配置文件不存在: config\scenarios.yaml"
        copy config\scenarios.yaml.example config\scenarios.yaml 2>nul
    )
    
    if not exist config\environment.yaml (
        call :log_warn "配置文件不存在: config\environment.yaml"
        copy config\environment.yaml.example config\environment.yaml 2>nul
    )
    goto :eof

REM 启动应用
:start_application
    if "%1"=="docker" (
        call :start_docker
    ) else (
        call :start_local
    )
    goto :eof

REM 本地启动
:start_local
    call :log_info "启动Streamlit应用..."
    
    REM 检查Streamlit是否安装
    python -c "import streamlit" 2>nul
    if errorlevel 1 (
        call :log_error "Streamlit未安装，请先安装依赖"
        exit /b 1
    )
    
    REM 启动应用
    start /b streamlit run app.py ^
        --server.port=8501 ^
        --server.address=0.0.0.0 ^
        --theme.base="dark" ^
        --browser.serverAddress="localhost" ^
        --server.fileWatcherType="none" ^
        --server.headless=false
    
    timeout /t 2 /nobreak >nul
    call :log_info "应用启动完成，访问: http://localhost:8501"
    goto :eof

REM Docker启动
:start_docker
    call :log_info "使用Docker启动..."
    
    where docker >nul 2>nul
    if errorlevel 1 (
        call :log_error "Docker未安装，无法使用Docker模式"
        exit /b 1
    )
    
    REM 构建镜像
    call :log_info "构建Docker镜像..."
    docker build -t ew-simulation .
    
    REM 运行容器
    call :log_info "启动Docker容器..."
    docker run -d ^
        -p 8501:8501 ^
        -v "%cd%\data:/app/data" ^
        -v "%cd%\config:/app/config" ^
        -v "%cd%\logs:/app/logs" ^
        --name ew-simulation ^
        ew-simulation
    
    call :log_info "Docker容器已启动，应用运行在: http://localhost:8501"
    goto :eof

REM 停止应用
:stop_application
    if "%1"=="docker" (
        call :stop_docker
    ) else (
        call :stop_local
    )
    goto :eof

REM 停止本地应用
:stop_local
    call :log_info "停止本地应用..."
    
    REM 查找并终止进程
    for /f "tokens=2" %%i in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do (
        taskkill /PID %%i /F >nul 2>nul
    )
    goto :eof

REM 停止Docker应用
:stop_docker
    call :log_info "停止Docker容器..."
    docker stop ew-simulation 2>nul
    docker rm ew-simulation 2>nul
    goto :eof

REM 显示状态
:show_status
    call :log_info "系统状态检查..."
    
    REM 检查端口占用
    netstat -ano | findstr :8501 >nul
    if errorlevel 0 (
        call :log_info "端口8501已被占用"
        netstat -ano | findstr :8501
    ) else (
        call :log_info "端口8501空闲"
    )
    
    REM 检查虚拟环境
    if exist venv (
        call :log_info "虚拟环境: 已存在"
    ) else (
        call :log_warn "虚拟环境: 不存在"
    )
    
    REM 检查配置文件
    if exist config\radar_database.yaml (
        call :log_info "配置文件 radar_database.yaml: 存在"
    ) else (
        call :log_warn "配置文件 radar_database.yaml: 不存在"
    )
    
    if exist config\scenarios.yaml (
        call :log_info "配置文件 scenarios.yaml: 存在"
    ) else (
        call :log_warn "配置文件 scenarios.yaml: 不存在"
    )
    
    if exist config\environment.yaml (
        call :log_info "配置文件 environment.yaml: 存在"
    ) else (
        call :log_warn "配置文件 environment.yaml: 不存在"
    )
    goto :eof

REM 更新依赖
:update_dependencies
    call :log_info "更新Python依赖..."
    
    call venv\Scripts\activate.bat
    pip install --upgrade -r requirements.txt
    
    if exist requirements-dev.txt (
        pip install --upgrade -r requirements-dev.txt
    )
    
    call :log_info "依赖更新完成"
    goto :eof

REM 运行测试
:run_tests
    call :log_info "运行测试..."
    
    call venv\Scripts\activate.bat
    
    if exist tests\unit (
        call :log_info "运行单元测试..."
        python -m pytest tests\unit\ -v
    )
    
    if exist tests\integration (
        call :log_info "运行集成测试..."
        python -m pytest tests\integration\ -v
    )
    
    if exist tests\performance (
        call :log_info "运行性能测试..."
        python -m pytest tests\performance\ -v
    )
    
    call :log_info "运行所有测试..."
    python -m pytest tests\ -v
    goto :eof

REM 清理临时文件
:cleanup
    call :log_info "清理临时文件..."
    
    REM 清理Python缓存
    for /r %%i in (__pycache__) do if exist %%i rmdir /s /q "%%i"
    del /s /q *.pyc
    del /s /q *.pyo
    del /s /q .coverage
    
    REM 清理构建文件
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    if exist *.egg-info rmdir /s /q *.egg-info
    
    REM 清理日志文件
    if exist logs (
        forfiles /p logs /s /m *.log /d -7 /c "cmd /c del /q @path"
    )
    
    REM 清理数据文件
    if exist data\temp (
        rmdir /s /q data\temp
        mkdir data\temp
    )
    
    call :log_info "清理完成"
    goto :eof

REM 显示帮助
:show_help
    echo %BLUE%电子战对抗仿真系统启动脚本%NC%
    echo.
    echo 用法: start.bat [选项]
    echo.
    echo 选项:
    echo   start          启动应用 (默认)
    echo   stop           停止应用
    echo   restart        重启应用
    echo   status         显示状态
    echo   docker         使用Docker模式
    echo   local          使用本地模式 (默认)
    echo   update         更新依赖
    echo   test           运行测试
    echo   clean          清理临时文件
    echo   help           显示此帮助
    echo.
    echo 示例:
    echo   start.bat              # 本地启动
    echo   start.bat docker       # Docker启动
    echo   start.bat status       # 查看状态
    echo   start.bat stop         # 停止应用
    goto :eof

REM 主函数
:main
    set "action=start"
    set "mode=local"
    
    REM 解析参数
    if "%1"=="" goto :default_action
    
    :parse_args
    if "%1"=="" goto :execute_action
    
    if "%1"=="start" set "action=start"
    if "%1"=="stop" set "action=stop"
    if "%1"=="restart" set "action=restart"
    if "%1"=="status" set "action=status"
    if "%1"=="update" set "action=update"
    if "%1"=="test" set "action=test"
    if "%1"=="clean" set "action=clean"
    if "%1"=="help" set "action=help"
    if "%1"=="docker" set "mode=docker"
    if "%1"=="local" set "mode=local"
    
    shift
    goto :parse_args
    
    :default_action
    set "action=start"
    
    :execute_action
    if "%action%"=="start" (
        call :check_python_version
        call :check_dependencies
        call :setup_venv
        call :check_config_files
        call :start_application %mode%
    )
    
    if "%action%"=="stop" (
        call :stop_application %mode%
    )
    
    if "%action%"=="restart" (
        call :stop_application %mode%
        timeout /t 2 /nobreak >nul
        call :check_python_version
        call :start_application %mode%
    )
    
    if "%action%"=="status" (
        call :show_status
    )
    
    if "%action%"=="update" (
        call :update_dependencies
    )
    
    if "%action%"=="test" (
        call :check_python_version
        call :setup_venv
        call :run_tests
    )
    
    if "%action%"=="clean" (
        call :cleanup
    )
    
    if "%action%"=="help" (
        call :show_help
    )
    goto :eof

REM 运行主函数
call :main %*
if errorlevel 1 (
    pause
    exit /b 1
)
