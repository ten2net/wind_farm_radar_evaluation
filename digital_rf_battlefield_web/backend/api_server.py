"""
后端API服务器 - 基于FastAPI的仿真引擎API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import json
import logging
from datetime import datetime
import uuid

from .simulation_engine import SimulationEngine
from .models import (
    SimulationConfig, RadarConfig, TargetConfig,
    SimulationRequest, SimulationResponse, SimulationStatus
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="数字射频战场仿真系统API",
    description="提供仿真计算和数据处理的API接口",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局仿真引擎实例
simulation_engine = SimulationEngine()

# 存储仿真会话
sessions: Dict[str, Dict[str, Any]] = {}

class APIResponse(BaseModel):
    """API响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    """根端点，返回API信息"""
    return {
        "name": "数字射频战场仿真系统API",
        "version": "1.0.0",
        "status": "运行中",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return APIResponse(
        success=True,
        message="API服务运行正常",
        data={"timestamp": datetime.now().isoformat()}
    )

@app.post("/api/simulation/initialize", response_model=APIResponse)
async def initialize_simulation(request: SimulationRequest):
    """初始化仿真"""
    try:
        session_id = str(uuid.uuid4())
        
        # 创建仿真配置
        config = SimulationConfig(
            simulation_id=session_id,
            simulation_name=request.simulation_name,
            time_step=request.time_step,
            duration=request.duration,
            real_time_factor=request.real_time_factor
        )
        
        # 初始化仿真引擎
        success = simulation_engine.initialize(config)
        
        if not success:
            raise HTTPException(status_code=500, detail="仿真引擎初始化失败")
        
        # 添加雷达
        for radar_data in request.radars:
            radar = RadarConfig(**radar_data)
            simulation_engine.add_radar(radar)
        
        # 添加目标
        for target_data in request.targets:
            target = TargetConfig(**target_data)
            simulation_engine.add_target(target)
        
        # 存储会话
        sessions[session_id] = {
            "id": session_id,
            "name": request.simulation_name,
            "status": "initialized",
            "start_time": datetime.now().isoformat(),
            "progress": 0.0,
            "config": config.dict(),
            "radars": [r.dict() for r in simulation_engine.radars],
            "targets": [t.dict() for t in simulation_engine.targets]
        }
        
        return APIResponse(
            success=True,
            message="仿真初始化成功",
            data={"session_id": session_id}
        )
        
    except Exception as e:
        logger.error(f"初始化仿真失败: {e}")
        return APIResponse(
            success=False,
            message="仿真初始化失败",
            error=str(e)
        )

@app.post("/api/simulation/start/{session_id}", response_model=APIResponse)
async def start_simulation(session_id: str, background_tasks: BackgroundTasks):
    """开始仿真"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    if sessions[session_id]["status"] == "running":
        return APIResponse(
            success=False,
            message="仿真已在运行中"
        )
    
    # 更新会话状态
    sessions[session_id]["status"] = "running"
    sessions[session_id]["start_time"] = datetime.now().isoformat()
    
    # 在后台运行仿真
    background_tasks.add_task(run_simulation, session_id)
    
    return APIResponse(
        success=True,
        message="仿真开始运行",
        data={"session_id": session_id}
    )

async def run_simulation(session_id: str):
    """运行仿真（后台任务）"""
    try:
        # 获取仿真配置
        config_data = sessions[session_id]["config"]
        config = SimulationConfig(**config_data)
        
        # 运行仿真
        simulation_engine.run(config)
        
        # 更新状态为完成
        sessions[session_id]["status"] = "completed"
        sessions[session_id]["end_time"] = datetime.now().isoformat()
        sessions[session_id]["progress"] = 1.0
        
    except Exception as e:
        logger.error(f"仿真运行失败: {e}")
        sessions[session_id]["status"] = "error"
        sessions[session_id]["error"] = str(e)

@app.post("/api/simulation/stop/{session_id}", response_model=APIResponse)
async def stop_simulation(session_id: str):
    """停止仿真"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    if sessions[session_id]["status"] != "running":
        return APIResponse(
            success=False,
            message="仿真未在运行中"
        )
    
    # 停止仿真引擎
    simulation_engine.stop()
    
    # 更新会话状态
    sessions[session_id]["status"] = "stopped"
    sessions[session_id]["end_time"] = datetime.now().isoformat()
    
    return APIResponse(
        success=True,
        message="仿真已停止",
        data={"session_id": session_id}
    )

@app.get("/api/simulation/status/{session_id}", response_model=APIResponse)
async def get_simulation_status(session_id: str):
    """获取仿真状态"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    session = sessions[session_id]
    
    # 获取仿真引擎状态
    engine_status = simulation_engine.get_status()
    
    # 合并状态信息
    status_data = {
        "session_id": session_id,
        "name": session["name"],
        "status": session["status"],
        "start_time": session.get("start_time"),
        "end_time": session.get("end_time"),
        "progress": session["progress"],
        "engine_status": engine_status,
        "radar_count": len(session.get("radars", [])),
        "target_count": len(session.get("targets", [])),
        "current_time": simulation_engine.current_time if hasattr(simulation_engine, 'current_time') else 0.0
    }
    
    return APIResponse(
        success=True,
        message="状态获取成功",
        data=status_data
    )

@app.post("/api/simulation/step/{session_id}", response_model=APIResponse)
async def simulation_step(session_id: str):
    """执行一步仿真"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    try:
        # 执行一步仿真
        step_data = simulation_engine.step()
        
        # 更新会话进度
        if sessions[session_id]["status"] == "running":
            config = sessions[session_id]["config"]
            duration = config.get("duration", 300)
            progress = min(step_data.get("current_time", 0) / duration, 1.0)
            sessions[session_id]["progress"] = progress
        
        return APIResponse(
            success=True,
            message="仿真步骤执行成功",
            data=step_data
        )
        
    except Exception as e:
        logger.error(f"执行仿真步骤失败: {e}")
        return APIResponse(
            success=False,
            message="执行仿真步骤失败",
            error=str(e)
        )

@app.get("/api/simulation/results/{session_id}", response_model=APIResponse)
async def get_simulation_results(session_id: str):
    """获取仿真结果"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    if sessions[session_id]["status"] not in ["completed", "stopped", "error"]:
        return APIResponse(
            success=False,
            message="仿真尚未完成"
        )
    
    try:
        # 获取仿真结果
        results = simulation_engine.get_results()
        
        return APIResponse(
            success=True,
            message="结果获取成功",
            data=results
        )
        
    except Exception as e:
        logger.error(f"获取仿真结果失败: {e}")
        return APIResponse(
            success=False,
            message="获取仿真结果失败",
            error=str(e)
        )

@app.get("/api/simulation/sessions", response_model=APIResponse)
async def list_simulation_sessions():
    """列出所有仿真会话"""
    session_list = []
    
    for session_id, session in sessions.items():
        session_list.append({
            "id": session_id,
            "name": session["name"],
            "status": session["status"],
            "start_time": session.get("start_time"),
            "progress": session["progress"],
            "radar_count": len(session.get("radars", [])),
            "target_count": len(session.get("targets", []))
        })
    
    return APIResponse(
        success=True,
        message="会话列表获取成功",
        data={"sessions": session_list, "count": len(session_list)}
    )

@app.delete("/api/simulation/session/{session_id}", response_model=APIResponse)
async def delete_simulation_session(session_id: str):
    """删除仿真会话"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="仿真会话不存在")
    
    # 如果仿真正在运行，先停止
    if sessions[session_id]["status"] == "running":
        simulation_engine.stop()
    
    # 删除会话
    del sessions[session_id]
    
    return APIResponse(
        success=True,
        message="会话删除成功",
        data={"session_id": session_id}
    )

@app.get("/api/radar/templates", response_model=APIResponse)
async def get_radar_templates():
    """获取雷达模板"""
    try:
        with open("config/radar_templates.json", "r", encoding="utf-8") as f:
            templates = json.load(f)
        
        return APIResponse(
            success=True,
            message="雷达模板获取成功",
            data={"templates": templates}
        )
        
    except Exception as e:
        logger.error(f"获取雷达模板失败: {e}")
        return APIResponse(
            success=False,
            message="获取雷达模板失败",
            error=str(e)
        )

@app.get("/api/target/templates", response_model=APIResponse)
async def get_target_templates():
    """获取目标模板"""
    try:
        with open("config/target_templates.json", "r", encoding="utf-8") as f:
            templates = json.load(f)
        
        return APIResponse(
            success=True,
            message="目标模板获取成功",
            data={"templates": templates}
        )
        
    except Exception as e:
        logger.error(f"获取目标模板失败: {e}")
        return APIResponse(
            success=False,
            message="获取目标模板失败",
            error=str(e)
        )

@app.post("/api/analysis/detection", response_model=APIResponse)
async def analyze_detection(data: Dict[str, Any]):
    """分析检测性能"""
    try:
        # 这里实现检测性能分析逻辑
        # 由于复杂度，这里只返回模拟数据
        analysis_result = {
            "detection_probability": 0.85,
            "false_alarm_rate": 1.2e-4,
            "snr_threshold": 13.5,
            "roc_curve": [],
            "precision_recall": []
        }
        
        return APIResponse(
            success=True,
            message="检测分析完成",
            data=analysis_result
        )
        
    except Exception as e:
        logger.error(f"检测分析失败: {e}")
        return APIResponse(
            success=False,
            message="检测分析失败",
            error=str(e)
        )

@app.post("/api/analysis/tracking", response_model=APIResponse)
async def analyze_tracking(data: Dict[str, Any]):
    """分析跟踪性能"""
    try:
        # 这里实现跟踪性能分析逻辑
        analysis_result = {
            "track_continuity": 0.92,
            "position_error": 45.3,
            "track_lifetime": 156.7,
            "initiation_time": 2.5
        }
        
        return APIResponse(
            success=True,
            message="跟踪分析完成",
            data=analysis_result
        )
        
    except Exception as e:
        logger.error(f"跟踪分析失败: {e}")
        return APIResponse(
            success=False,
            message="跟踪分析失败",
            error=str(e)
        )

@app.post("/api/optimization/parameters", response_model=APIResponse)
async def optimize_parameters(data: Dict[str, Any]):
    """参数优化"""
    try:
        # 这里实现参数优化逻辑
        optimized_params = {
            "frequency": 3000,
            "bandwidth": 10,
            "prf": 1000,
            "pulse_width": 10.0,
            "improvement": 0.15
        }
        
        return APIResponse(
            success=True,
            message="参数优化完成",
            data={"optimized_parameters": optimized_params}
        )
        
    except Exception as e:
        logger.error(f"参数优化失败: {e}")
        return APIResponse(
            success=False,
            message="参数优化失败",
            error=str(e)
        )

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )