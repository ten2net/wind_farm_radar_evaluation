# simulation_control_module.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from pathlib import Path
import pickle
import tempfile
from typing import Dict, List, Optional, Any

class SimulationController:
    """仿真控制器"""
    
    def __init__(self):
        self.simulation_engine = None
        self.is_running = False
        self.is_paused = False
        self.simulation_speed = 1.0
        self.current_time = 0.0
        self.max_simulation_time = 300.0  # 最大仿真时间5分钟
        self.time_step = 0.1  # 仿真步长
        self.simulation_history = []
        self.callbacks = {}
        
    def initialize_simulation(self, battlefield, guidance_system):
        """初始化仿真"""
        from core_module import SimulationEngine
        
        self.simulation_engine = SimulationEngine()
        self.simulation_engine.battlefield = battlefield
        self.simulation_engine.set_guidance_system(
            self._get_system_key(guidance_system)
        )
        self.current_time = 0.0
        self.simulation_history = []
        self.is_running = False
        self.is_paused = False
        
        # 记录初始状态
        self._record_snapshot("初始化")
        
    def start_simulation(self):
        """开始仿真"""
        if self.simulation_engine:
            self.is_running = True
            self.is_paused = False
            self._notify_callbacks('simulation_started')
            
    def pause_simulation(self):
        """暂停仿真"""
        self.is_paused = True
        self._notify_callbacks('simulation_paused')
        
    def resume_simulation(self):
        """恢复仿真"""
        self.is_paused = False
        self._notify_callbacks('simulation_resumed')
        
    def stop_simulation(self):
        """停止仿真"""
        self.is_running = False
        self.is_paused = False
        self._notify_callbacks('simulation_stopped')
        
    def step_simulation(self):
        """单步仿真"""
        if self.simulation_engine and not self.is_running:
            result = self.simulation_engine.run_simulation_step(self.time_step)
            self.current_time += self.time_step
            self._record_snapshot("单步执行")
            self._notify_callbacks('simulation_stepped', result)
            return result
        return None
        
    def run_real_time_simulation(self):
        """实时运行仿真"""
        if not self.simulation_engine or not self.is_running or self.is_paused:
            return None
            
        # 计算实际时间步长（考虑仿真速度）
        actual_time_step = self.time_step * self.simulation_speed
        
        # 运行仿真步
        result = self.simulation_engine.run_simulation_step(actual_time_step)
        self.current_time += actual_time_step
        
        # 记录历史
        self._record_snapshot("实时仿真")
        
        # 检查仿真结束条件
        if (self.current_time >= self.max_simulation_time or 
            result.get('performance', 0) <= 0.01):
            self.stop_simulation()
            
        self._notify_callbacks('simulation_updated', result)
        return result
        
    def set_simulation_speed(self, speed: float):
        """设置仿真速度"""
        self.simulation_speed = max(0.1, min(10.0, speed))
        
    def rewind_simulation(self, target_time: float):
        """回退仿真到指定时间"""
        # 查找最近的历史快照
        for i, snapshot in enumerate(reversed(self.simulation_history)):
            if snapshot['timestamp'] <= target_time:
                # 恢复到该快照状态
                self._restore_from_snapshot(snapshot)
                self.current_time = target_time
                # 截断后续历史
                self.simulation_history = self.simulation_history[:len(self.simulation_history)-i]
                break
                
        self._notify_callbacks('simulation_rewound')
        
    def register_callback(self, event: str, callback: callable):
        """注册回调函数"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        
    def _notify_callbacks(self, event: str, data: Any = None):
        """通知回调函数"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data) if data else callback()
                except Exception as e:
                    print(f"Callback error: {e}")
                    
    def _record_snapshot(self, action: str):
        """记录仿真快照"""
        if not self.simulation_engine:
            return
            
        snapshot = {
            'timestamp': self.current_time,
            'action': action,
            'battlefield_state': self._serialize_battlefield(),
            'guidance_system_state': self._serialize_guidance_system(),
            'performance': getattr(
                self.simulation_engine.current_guidance_system, 
                'current_performance', 
                0.0
            )
        }
        self.simulation_history.append(snapshot)
        
    def _restore_from_snapshot(self, snapshot: Dict):
        """从快照恢复状态"""
        # 这里需要实现状态恢复逻辑
        # 由于对象序列化复杂，这里使用简化实现
        pass
        
    def _serialize_battlefield(self) -> Dict:
        """序列化战场状态"""
        if not self.simulation_engine:
            return {}
        return {
            'missile_position': {
                'lat': self.simulation_engine.battlefield.missile_position.lat,
                'lon': self.simulation_engine.battlefield.missile_position.lon,
                'alt': self.simulation_engine.battlefield.missile_position.alt
            },
            'weather_condition': self.simulation_engine.battlefield.weather_condition
        }
        
    def _serialize_guidance_system(self) -> Dict:
        """序列化导引头状态"""
        if not self.simulation_engine or not self.simulation_engine.current_guidance_system:
            return {}
            
        system = self.simulation_engine.current_guidance_system
        return {
            'name': system.name,
            'performance': system.current_performance,
            'trajectory_length': len(system.trajectory)
        }
        
    def _get_system_key(self, guidance_system) -> str:
        """获取导引头类型键"""
        system_map = {
            'PassiveRadarSeeker': 'passive',
            'ActiveRadarSeeker': 'active', 
            'CompositeSeeker': 'composite'
        }
        return system_map.get(guidance_system.__class__.__name__, 'composite')

class DataManager:
    """数据管理器"""
    
    def __init__(self, db_path: str = "simulation_data.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建仿真会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                created_time DATETIME,
                duration REAL,
                parameters TEXT
            )
        ''')
        
        # 创建仿真数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_data (
                data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp REAL,
                performance REAL,
                target_distance REAL,
                jamming_power REAL,
                terrain_factor REAL,
                weather_factor REAL,
                missile_lat REAL,
                missile_lon REAL,
                missile_alt REAL,
                FOREIGN KEY (session_id) REFERENCES simulation_sessions (session_id)
            )
        ''')
        
        # 创建场景配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenarios (
                scenario_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                battlefield_config TEXT,
                guidance_system_config TEXT,
                created_time DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def save_simulation_session(self, session_id: str, name: str, description: str,
                              controller: SimulationController) -> bool:
        """保存仿真会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 保存会话元数据
            cursor.execute('''
                INSERT OR REPLACE INTO simulation_sessions 
                (session_id, name, description, created_time, duration, parameters)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                name,
                description,
                datetime.now(),
                controller.current_time,
                json.dumps(self._serialize_controller(controller))
            ))
            
            # 保存仿真数据
            for snapshot in controller.simulation_history:
                cursor.execute('''
                    INSERT INTO simulation_data 
                    (session_id, timestamp, performance, target_distance, jamming_power,
                     terrain_factor, weather_factor, missile_lat, missile_lon, missile_alt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    snapshot['timestamp'],
                    snapshot.get('performance', 0),
                    self._extract_distance(snapshot),
                    self._extract_jamming_power(snapshot),
                    self._extract_terrain_factor(snapshot),
                    self._extract_weather_factor(snapshot),
                    *self._extract_missile_position(snapshot)
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"保存仿真会话错误: {e}")
            return False
            
    def load_simulation_session(self, session_id: str) -> Optional[Dict]:
        """加载仿真会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 加载会话元数据
            cursor.execute(
                'SELECT * FROM simulation_sessions WHERE session_id = ?',
                (session_id,)
            )
            session_data = cursor.fetchone()
            
            if not session_data:
                return None
                
            # 加载仿真数据
            cursor.execute(
                'SELECT * FROM simulation_data WHERE session_id = ? ORDER BY timestamp',
                (session_id,)
            )
            simulation_data = cursor.fetchall()
            
            conn.close()
            
            return {
                'session_id': session_data[0],
                'name': session_data[1],
                'description': session_data[2],
                'created_time': session_data[3],
                'duration': session_data[4],
                'parameters': json.loads(session_data[5]),
                'data': simulation_data
            }
            
        except Exception as e:
            print(f"加载仿真会话错误: {e}")
            return None
            
    def list_simulation_sessions(self) -> List[Dict]:
        """列出所有仿真会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id, name, description, created_time, duration 
            FROM simulation_sessions 
            ORDER BY created_time DESC
        ''')
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0],
                'name': row[1],
                'description': row[2],
                'created_time': row[3],
                'duration': row[4]
            })
            
        conn.close()
        return sessions
        
    def save_scenario(self, scenario_id: str, name: str, description: str,
                     battlefield_config: Dict, guidance_system_config: Dict) -> bool:
        """保存场景配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO scenarios 
                (scenario_id, name, description, battlefield_config, guidance_system_config, created_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                scenario_id,
                name,
                description,
                json.dumps(battlefield_config),
                json.dumps(guidance_system_config),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"保存场景错误: {e}")
            return False
            
    def load_scenario(self, scenario_id: str) -> Optional[Dict]:
        """加载场景配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM scenarios WHERE scenario_id = ?',
                (scenario_id,)
            )
            scenario_data = cursor.fetchone()
            
            conn.close()
            
            if scenario_data:
                return {
                    'scenario_id': scenario_data[0],
                    'name': scenario_data[1],
                    'description': scenario_data[2],
                    'battlefield_config': json.loads(scenario_data[3]),
                    'guidance_system_config': json.loads(scenario_data[4]),
                    'created_time': scenario_data[5]
                }
            return None
            
        except Exception as e:
            print(f"加载场景错误: {e}")
            return None
            
    def list_scenarios(self) -> List[Dict]:
        """列出所有场景"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT scenario_id, name, description, created_time 
            FROM scenarios 
            ORDER BY created_time DESC
        ''')
        
        scenarios = []
        for row in cursor.fetchall():
            scenarios.append({
                'scenario_id': row[0],
                'name': row[1],
                'description': row[2],
                'created_time': row[3]
            })
            
        conn.close()
        return scenarios
        
    def _serialize_controller(self, controller: SimulationController) -> Dict:
        """序列化控制器状态"""
        return {
            'simulation_speed': controller.simulation_speed,
            'current_time': controller.current_time,
            'max_simulation_time': controller.max_simulation_time,
            'time_step': controller.time_step
        }
        
    def _extract_distance(self, snapshot: Dict) -> float:
        """从快照提取距离数据"""
        # 简化实现，实际应根据快照结构解析
        return snapshot.get('performance', 0) * 100  # 示例逻辑
        
    def _extract_jamming_power(self, snapshot: Dict) -> float:
        """从快照提取干扰功率"""
        return 0.0  # 简化实现
        
    def _extract_terrain_factor(self, snapshot: Dict) -> float:
        """从快照提取地形因子"""
        return 1.0  # 简化实现
        
    def _extract_weather_factor(self, snapshot: Dict) -> float:
        """从快照提取天气因子"""
        return 1.0  # 简化实现
        
    def _extract_missile_position(self, snapshot: Dict) -> tuple:
        """从快照提取导弹位置"""
        battlefield_state = snapshot.get('battlefield_state', {})
        missile_pos = battlefield_state.get('missile_position', {})
        return (
            missile_pos.get('lat', 0),
            missile_pos.get('lon', 0),
            missile_pos.get('alt', 0)
        )

class AnalysisTools:
    """分析工具类"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        
    def create_performance_comparison_chart(self, session_ids: List[str]) -> go.Figure:
        """创建性能对比图表"""
        fig = go.Figure()
        
        for session_id in session_ids:
            session_data = self.data_manager.load_simulation_session(session_id)
            if not session_data:
                continue
                
            # 提取性能数据
            timestamps = []
            performances = []
            
            for data_point in session_data['data']:
                timestamps.append(data_point[2])  # timestamp
                performances.append(data_point[3] * 100)  # performance
                
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=performances,
                name=session_data['name'],
                mode='lines'
            ))
            
        fig.update_layout(
            title="多会话性能对比",
            xaxis_title="仿真时间 (s)",
            yaxis_title="性能评分 (%)",
            height=400
        )
        
        return fig
        
    def create_statistical_summary(self, session_id: str) -> Dict:
        """创建统计摘要"""
        session_data = self.data_manager.load_simulation_session(session_id)
        if not session_data:
            return {}
            
        performances = [data[3] for data in session_data['data']]
        distances = [data[4] for data in session_data['data']]
        
        return {
            'session_name': session_data['name'],
            'duration': session_data['duration'],
            'max_performance': max(performances) * 100,
            'min_performance': min(performances) * 100,
            'avg_performance': np.mean(performances) * 100,
            'final_performance': performances[-1] * 100 if performances else 0,
            'min_distance': min(distances) if distances else 0,
            'success_rate': self._calculate_success_rate(performances)
        }
        
    def _calculate_success_rate(self, performances: List[float]) -> float:
        """计算成功率"""
        if not performances:
            return 0.0
        successful_steps = sum(1 for p in performances if p > 0.7)
        return (successful_steps / len(performances)) * 100
        
    def export_to_excel(self, session_id: str, file_path: str) -> bool:
        """导出数据到Excel"""
        try:
            session_data = self.data_manager.load_simulation_session(session_id)
            if not session_data:
                return False
                
            # 创建DataFrame
            df_data = []
            for data_point in session_data['data']:
                df_data.append({
                    '时间': data_point[2],
                    '性能评分': data_point[3] * 100,
                    '目标距离': data_point[4],
                    '干扰强度': data_point[5] * 100,
                    '地形影响': data_point[6] * 100,
                    '天气影响': data_point[7] * 100,
                    '导弹纬度': data_point[8],
                    '导弹经度': data_point[9],
                    '导弹海拔': data_point[10]
                })
                
            df = pd.DataFrame(df_data)
            
            # 创建Excel写入器
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='仿真数据', index=False)
                
                # 添加统计摘要
                stats = self.create_statistical_summary(session_id)
                stats_df = pd.DataFrame([stats])
                stats_df.to_excel(writer, sheet_name='统计摘要', index=False)
                
            return True
            
        except Exception as e:
            print(f"导出Excel错误: {e}")
            return False

class RealTimeMonitor:
    """实时监控器"""
    
    def __init__(self):
        self.metrics_history = {}
        self.update_interval = 1.0  # 秒
        self.last_update = time.time()
        
    def update_metrics(self, metrics: Dict):
        """更新监控指标"""
        current_time = time.time()
        
        # 限制更新频率
        if current_time - self.last_update < self.update_interval:
            return
            
        timestamp = current_time
        
        for key, value in metrics.items():
            if key not in self.metrics_history:
                self.metrics_history[key] = []
                
            self.metrics_history[key].append({
                'timestamp': timestamp,
                'value': value
            })
                
        self.last_update = current_time
        
    def get_metric_trend(self, metric_name: str, time_window: float = 60.0) -> List:
        """获取指标趋势"""
        if metric_name not in self.metrics_history:
            return []
            
        current_time = time.time()
        window_start = current_time - time_window
        
        return [
            point for point in self.metrics_history[metric_name]
            if point['timestamp'] >= window_start
        ]
        
    def create_realtime_dashboard(self) -> go.Figure:
        """创建实时监控仪表盘"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['性能趋势', '干扰强度', '目标距离', '系统状态'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "indicator"}]]
        )
        
        # 性能趋势
        performance_data = self.get_metric_trend('performance')
        if performance_data:
            times = [p['timestamp'] for p in performance_data]
            values = [p['value'] for p in performance_data]
            
            fig.add_trace(
                go.Scatter(x=times, y=values, name="性能", line=dict(color='blue')),
                row=1, col=1
            )
            
        # 干扰强度
        jamming_data = self.get_metric_trend('jamming_power')
        if jamming_data:
            times = [j['timestamp'] for j in jamming_data]
            values = [j['value'] for j in jamming_data]
            
            fig.add_trace(
                go.Scatter(x=times, y=values, name="干扰强度", line=dict(color='red')),
                row=1, col=2
            )
            
        # 目标距离
        distance_data = self.get_metric_trend('target_distance')
        if distance_data:
            times = [d['timestamp'] for d in distance_data]
            values = [d['value'] for d in distance_data]
            
            fig.add_trace(
                go.Scatter(x=times, y=values, name="目标距离", line=dict(color='green')),
                row=2, col=1
            )
            
        # 系统状态指示器
        current_perf = performance_data[-1]['value'] if performance_data else 0
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_perf,
                title={"text": "当前性能"},
                gauge={'axis': {'range': [0, 100]}},
                domain={'row': 1, 'column': 1}
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        return fig

class ScenarioManager:
    """场景管理器"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.preset_scenarios = self._create_preset_scenarios()
        
    def _create_preset_scenarios(self) -> Dict[str, Dict]:
        """创建预设场景"""
        return {
            'air_superiority': {
                'name': '空战优势场景',
                'description': '战斗机对抗预警机和干扰机的空战场景',
                'battlefield': {
                    'missile_position': {'lat': 35.0, 'lon': 115.0, 'alt': 5000},
                    'targets': [
                        {
                            'target_id': 'awacs_1',
                            'type': 'awacs',
                            'position': {'lat': 36.0, 'lon': 117.0, 'alt': 8000},
                            'emission_power': 0.9,
                            'rcs': 50
                        }
                    ],
                    'jammers': [
                        {
                            'jammer_id': 'escort_jammer',
                            'position': {'lat': 36.2, 'lon': 116.8, 'alt': 7000},
                            'type': 'noise',
                            'power': 0.6,
                            'range': 80
                        }
                    ],
                    'weather': 'clear'
                },
                'recommended_systems': ['composite', 'passive']
            },
            'naval_warfare': {
                'name': '海上作战场景',
                'description': '反舰导弹对抗军舰自卫干扰的场景',
                'battlefield': {
                    'missile_position': {'lat': 35.5, 'lon': 116.0, 'alt': 100},
                    'targets': [
                        {
                            'target_id': 'warship_1',
                            'type': 'warship',
                            'position': {'lat': 35.8, 'lon': 116.5, 'alt': 0},
                            'emission_power': 0.7,
                            'rcs': 1000
                        }
                    ],
                    'jammers': [
                        {
                            'jammer_id': 'ship_jammer',
                            'position': {'lat': 35.8, 'lon': 116.5, 'alt': 0},
                            'type': 'deception',
                            'power': 0.8,
                            'range': 50
                        }
                    ],
                    'weather': 'rain'
                },
                'recommended_systems': ['active', 'composite']
            },
            'sead_mission': {
                'name': '防空压制任务',
                'description': '反辐射导弹攻击雷达站的典型场景',
                'battlefield': {
                    'missile_position': {'lat': 34.8, 'lon': 115.5, 'alt': 3000},
                    'targets': [
                        {
                            'target_id': 'radar_station',
                            'type': 'radar_station',
                            'position': {'lat': 35.2, 'lon': 116.2, 'alt': 0},
                            'emission_power': 1.0,
                            'rcs': 100
                        }
                    ],
                    'jammers': [],
                    'weather': 'cloudy'
                },
                'recommended_systems': ['passive']
            }
        }
        
    def get_preset_scenario(self, scenario_key: str) -> Optional[Dict]:
        """获取预设场景"""
        return self.preset_scenarios.get(scenario_key)
        
    def list_preset_scenarios(self) -> List[Dict]:
        """列出所有预设场景"""
        return [
            {'key': key, **value} 
            for key, value in self.preset_scenarios.items()
        ]
        
    def create_custom_scenario(self, scenario_config: Dict) -> str:
        """创建自定义场景"""
        scenario_id = f"custom_{int(time.time())}"
        success = self.data_manager.save_scenario(
            scenario_id,
            scenario_config.get('name', '自定义场景'),
            scenario_config.get('description', ''),
            scenario_config.get('battlefield', {}),
            scenario_config.get('guidance_system', {})
        )
        return scenario_id if success else ""

class SimulationUI:
    """仿真界面组件"""
    
    def __init__(self):
        self.controller = SimulationController()
        self.data_manager = DataManager()
        self.analysis_tools = AnalysisTools(self.data_manager)
        self.monitor = RealTimeMonitor()
        self.scenario_manager = ScenarioManager(self.data_manager)
        self.current_scenario = None
        self.current_guidance_system = None
        
    def create_control_panel(self):
        """创建控制面板"""
        st.sidebar.header("🎮 仿真控制")
        
        col1, col2, col3 = st.sidebar.columns(3)
        
        with col1:
            if st.button("▶️ 开始", use_container_width=True, key="start_btn"):
                self.controller.start_simulation()
                st.rerun()
                
        with col2:
            if st.button("⏸️ 暂停", use_container_width=True, key="pause_btn"):
                self.controller.pause_simulation()
                st.rerun()
                
        with col3:
            if st.button("⏹️ 停止", use_container_width=True, key="stop_btn"):
                self.controller.stop_simulation()
                st.rerun()
        
        # 单步控制
        st.sidebar.markdown("---")
        if st.sidebar.button("🔹 单步仿真", use_container_width=True):
            result = self.controller.step_simulation()
            if result:
                self.monitor.update_metrics({
                    'performance': result['performance'] * 100,
                    'target_distance': result['target_distance'],
                    'jamming_power': result['jamming_power'] * 100
                })
            st.rerun()
        
        # 仿真速度控制
        st.sidebar.markdown("---")
        simulation_speed = st.sidebar.slider(
            "仿真速度", 0.1, 10.0, 1.0, 0.1,
            help="控制仿真运行速度"
        )
        self.controller.set_simulation_speed(simulation_speed)
        
        # 时间控制
        col1, col2 = st.sidebar.columns(2)
        with col1:
            time_step = st.number_input("步长(s)", 0.01, 5.0, 0.1, 0.01)
            self.controller.time_step = time_step
            
        with col2:
            max_time = st.number_input("最大时间(s)", 10, 600, 300, 10)
            self.controller.max_simulation_time = max_time
        
        # 回退控制
        st.sidebar.markdown("---")
        if self.controller.simulation_history:
            current_time = self.controller.current_time
            rewind_time = st.sidebar.slider(
                "回退到", 0.0, current_time, 0.0, 1.0
            )
            
            if st.sidebar.button("↩️ 回退仿真", use_container_width=True):
                self.controller.rewind_simulation(rewind_time)
                st.rerun()
        
        # 状态显示
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 仿真状态")
        
        status_color = "🔴" if not self.controller.is_running else "🟢"
        status_text = "运行中" if self.controller.is_running else "已停止"
        if self.controller.is_paused:
            status_color = "🟡"
            status_text = "已暂停"
            
        st.sidebar.metric("状态", f"{status_color} {status_text}")
        st.sidebar.metric("当前时间", f"{self.controller.current_time:.1f}s")
        st.sidebar.metric("历史步数", len(self.controller.simulation_history))
    
    def create_scenario_panel(self):
        """创建场景管理面板"""
        st.sidebar.header("🌍 场景管理")
        
        # 场景选择
        tab1, tab2, tab3 = st.sidebar.tabs(["预设场景", "自定义场景", "历史场景"])
        
        with tab1:
            self._create_preset_scenarios_tab()
            
        with tab2:
            self._create_custom_scenario_tab()
            
        with tab3:
            self._create_history_scenarios_tab()
    
    def _create_preset_scenarios_tab(self):
        """创建预设场景选项卡"""
        preset_scenarios = self.scenario_manager.list_preset_scenarios()
        
        for scenario in preset_scenarios:
            with st.expander(f"{scenario['name']}"):
                st.write(scenario['description'])
                
                if st.button(f"加载场景", key=f"load_{scenario['key']}"):
                    self._load_preset_scenario(scenario['key'])
                    st.rerun()
                
                st.caption(f"推荐导引头: {', '.join(scenario['recommended_systems'])}")
    
    def _create_custom_scenario_tab(self):
        """创建自定义场景选项卡"""
        with st.form("custom_scenario_form"):
            st.subheader("自定义场景")
            
            scenario_name = st.text_input("场景名称", "自定义作战场景")
            scenario_desc = st.text_area("场景描述", "自定义作战场景描述")
            
            # 战场配置
            st.subheader("战场配置")
            col1, col2 = st.columns(2)
            
            with col1:
                missile_lat = st.number_input("导弹纬度", 30.0, 40.0, 35.0, 0.1)
                missile_lon = st.number_input("导弹经度", 110.0, 120.0, 115.0, 0.1)
                missile_alt = st.number_input("导弹海拔(m)", 0, 20000, 5000, 100)
                
            with col2:
                weather_condition = st.selectbox(
                    "天气条件",
                    ['clear', 'cloudy', 'rain', 'fog', 'storm']
                )
            
            # 目标配置
            st.subheader("目标配置")
            target_type = st.selectbox(
                "目标类型",
                ['fighter', 'bomber', 'awacs', 'warship', 'radar_station']
            )
            
            col1, col2 = st.columns(2)
            with col1:
                target_lat = st.number_input("目标纬度", 30.0, 40.0, 36.0, 0.1)
                target_lon = st.number_input("目标经度", 110.0, 120.0, 117.0, 0.1)
                target_alt = st.number_input("目标海拔(m)", 0, 20000, 8000, 100)
                
            with col2:
                emission_power = st.slider("辐射功率", 0.0, 1.0, 0.8, 0.1)
                rcs = st.number_input("RCS", 1.0, 1000.0, 50.0, 10.0)
            
            # 干扰配置
            st.subheader("干扰配置")
            jamming_type = st.selectbox(
                "干扰类型",
                ['none', 'noise', 'deception', 'smart_noise']
            )
            
            if jamming_type != 'none':
                col1, col2 = st.columns(2)
                with col1:
                    jammer_lat = st.number_input("干扰源纬度", 30.0, 40.0, 36.5, 0.1)
                    jammer_lon = st.number_input("干扰源经度", 110.0, 120.0, 116.5, 0.1)
                    
                with col2:
                    jammer_power = st.slider("干扰功率", 0.0, 1.0, 0.5, 0.1)
                    jammer_range = st.number_input("干扰范围(km)", 10, 200, 100, 10)
            
            # 提交按钮
            if st.form_submit_button("创建并加载场景", use_container_width=True):
                scenario_config = {
                    'name': scenario_name,
                    'description': scenario_desc,
                    'battlefield': {
                        'missile_position': {
                            'lat': missile_lat,
                            'lon': missile_lon,
                            'alt': missile_alt
                        },
                        'targets': [{
                            'target_id': 'custom_target',
                            'type': target_type,
                            'position': {
                                'lat': target_lat,
                                'lon': target_lon,
                                'alt': target_alt
                            },
                            'emission_power': emission_power,
                            'rcs': rcs
                        }],
                        'jammers': [] if jamming_type == 'none' else [{
                            'jammer_id': 'custom_jammer',
                            'position': {
                                'lat': jammer_lat,
                                'lon': jammer_lon,
                                'alt': 0
                            },
                            'type': jamming_type,
                            'power': jammer_power,
                            'range': jammer_range
                        }],
                        'weather': weather_condition
                    }
                }
                
                scenario_id = self.scenario_manager.create_custom_scenario(scenario_config)
                if scenario_id:
                    st.success(f"场景创建成功: {scenario_id}")
                    self._load_custom_scenario(scenario_id)
    
    def _create_history_scenarios_tab(self):
        """创建历史场景选项卡"""
        scenarios = self.data_manager.list_scenarios()
        
        if not scenarios:
            st.info("暂无历史场景")
            return
            
        for scenario in scenarios:
            with st.expander(f"{scenario['name']}"):
                st.write(f"描述: {scenario['description']}")
                st.write(f"创建时间: {scenario['created_time']}")
                
                if st.button(f"加载", key=f"load_hist_{scenario['scenario_id']}"):
                    loaded = self._load_scenario(scenario['scenario_id'])
                    if loaded:
                        st.rerun()
                
                if st.button(f"删除", key=f"delete_{scenario['scenario_id']}"):
                    # 这里需要实现删除功能
                    pass
    
    def _load_preset_scenario(self, scenario_key: str):
        """加载预设场景"""
        scenario = self.scenario_manager.get_preset_scenario(scenario_key)
        if scenario:
            self.current_scenario = scenario
            st.success(f"已加载预设场景: {scenario['name']}")
            
            # 创建战场对象
            from core_module import Battlefield, Target, Jammer, Position
            from core_module import TargetType, JammingType
            
            battlefield = Battlefield()
            
            # 设置导弹位置
            missile_pos = scenario['battlefield']['missile_position']
            battlefield.missile_position = Position(
                missile_pos['lat'], missile_pos['lon'], missile_pos['alt']
            )
            
            # 添加目标
            for target_config in scenario['battlefield']['targets']:
                target = Target(
                    target_id=target_config['target_id'],
                    target_type=TargetType(target_config['type']),
                    position=Position(
                        target_config['position']['lat'],
                        target_config['position']['lon'],
                        target_config['position']['alt']
                    ),
                    emission_power=target_config['emission_power'],
                    rcs=target_config['rcs']
                )
                battlefield.add_target(target)
            
            # 添加干扰机
            for jammer_config in scenario['battlefield']['jammers']:
                jammer = Jammer(
                    jammer_id=jammer_config['jammer_id'],
                    position=Position(
                        jammer_config['position']['lat'],
                        jammer_config['position']['lon'],
                        jammer_config['position']['alt']
                    ),
                    jamming_type=JammingType(jammer_config['type']),
                    power=jammer_config['power'],
                    range=jammer_config['range']
                )
                battlefield.add_jammer(jammer)
            
            # 设置天气
            battlefield.weather_condition = scenario['battlefield']['weather']
            
            return battlefield
        return None
    
    def _load_custom_scenario(self, scenario_id: str):
        """加载自定义场景"""
        return self._load_scenario(scenario_id)
    
    def _load_scenario(self, scenario_id: str):
        """加载场景"""
        scenario = self.data_manager.load_scenario(scenario_id)
        if scenario:
            self.current_scenario = scenario
            st.success(f"已加载场景: {scenario['name']}")
            return True
        return False
    
    def create_guidance_system_panel(self):
        """创建导引头选择面板"""
        st.sidebar.header("🎯 导引头配置")
        
        system_type = st.sidebar.selectbox(
            "选择导引头类型",
            ["被动雷达导引头", "主动雷达导引头", "复合制导导引头"],
            index=0
        )
        
        # 根据选择创建导引头对象
        from core_module import PassiveRadarSeeker, ActiveRadarSeeker, CompositeSeeker
        
        if system_type == "被动雷达导引头":
            self.current_guidance_system = PassiveRadarSeeker()
        elif system_type == "主动雷达导引头":
            self.current_guidance_system = ActiveRadarSeeker()
        else:
            self.current_guidance_system = CompositeSeeker()
        
        # 显示当前导引头参数
        with st.sidebar.expander("导引头参数", expanded=True):
            st.metric("探测距离", f"{self.current_guidance_system.detection_range} km")
            st.metric("抗干扰能力", f"{self.current_guidance_system.jamming_resistance * 100:.1f}%")
            st.metric("隐蔽性", f"{self.current_guidance_system.stealth_level * 100:.1f}%")
            st.metric("精度", f"{getattr(self.current_guidance_system, 'accuracy', 0.5) * 100:.1f}%")
    
    def create_data_management_panel(self):
        """创建数据管理面板"""
        st.sidebar.header("💾 数据管理")
        
        tab1, tab2, tab3 = st.sidebar.tabs(["保存会话", "加载会话", "数据分析"])
        
        with tab1:
            self._create_save_session_tab()
            
        with tab2:
            self._create_load_session_tab()
            
        with tab3:
            self._create_data_analysis_tab()
    
    def _create_save_session_tab(self):
        """创建保存会话选项卡"""
        session_name = st.text_input("会话名称", "仿真会话_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        session_desc = st.text_area("会话描述", "仿真会话描述")
        
        if st.button("💾 保存当前会话", use_container_width=True):
            if self.controller.simulation_engine and self.controller.simulation_history:
                session_id = f"session_{int(time.time())}"
                success = self.data_manager.save_simulation_session(
                    session_id, session_name, session_desc, self.controller
                )
                if success:
                    st.success(f"会话保存成功: {session_id}")
                else:
                    st.error("会话保存失败")
            else:
                st.warning("没有仿真数据可保存")
    
    def _create_load_session_tab(self):
        """创建加载会话选项卡"""
        sessions = self.data_manager.list_simulation_sessions()
        
        if not sessions:
            st.info("暂无历史会话")
            return
            
        for session in sessions:
            with st.expander(f"{session['name']}"):
                st.write(f"描述: {session['description']}")
                st.write(f"创建时间: {session['created_time']}")
                st.write(f"持续时间: {session['duration']:.1f}s")
                
                if st.button("加载", key=f"load_session_{session['session_id']}"):
                    loaded_session = self.data_manager.load_simulation_session(session['session_id'])
                    if loaded_session:
                        st.success(f"已加载会话: {session['name']}")
                        # 这里需要实现会话恢复逻辑
                        pass
                
                if st.button("删除", key=f"delete_session_{session['session_id']}"):
                    # 这里需要实现删除功能
                    pass
    
    def _create_data_analysis_tab(self):
        """创建数据分析选项卡"""
        sessions = self.data_manager.list_simulation_sessions()
        
        if len(sessions) >= 2:
            session_options = {s['name']: s['session_id'] for s in sessions}
            selected_sessions = st.multiselect(
                "选择要对比的会话",
                options=list(session_options.keys()),
                default=list(session_options.keys())[:2]
            )
            
            if selected_sessions and len(selected_sessions) >= 2:
                session_ids = [session_options[name] for name in selected_sessions]
                
                if st.button("📈 生成对比图表", use_container_width=True):
                    fig = self.analysis_tools.create_performance_comparison_chart(session_ids)
                    st.plotly_chart(fig, use_container_width=True)
        
        # 导出功能
        st.markdown("---")
        st.subheader("数据导出")
        
        if sessions:
            export_session = st.selectbox(
                "选择要导出的会话",
                options=[s['name'] for s in sessions]
            )
            
            if st.button("📥 导出为Excel", use_container_width=True):
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    session_id = session_options[export_session]
                    success = self.analysis_tools.export_to_excel(session_id, tmp.name)
                    
                    if success:
                        with open(tmp.name, 'rb') as f:
                            st.download_button(
                                label="下载Excel文件",
                                data=f,
                                file_name=f"{export_session}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
        
        # 统计分析
        st.markdown("---")
        st.subheader("统计分析")
        
        if sessions:
            stat_session = st.selectbox(
                "选择要分析的会话",
                options=[s['name'] for s in sessions],
                key="stat_select"
            )
            
            if st.button("📊 生成统计摘要", use_container_width=True):
                session_id = session_options[stat_session]
                stats = self.analysis_tools.create_statistical_summary(session_id)
                
                if stats:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("会话名称", stats['session_name'])
                        st.metric("最大性能", f"{stats['max_performance']:.1f}%")
                        st.metric("平均性能", f"{stats['avg_performance']:.1f}%")
                        st.metric("最终性能", f"{stats['final_performance']:.1f}%")
                    
                    with col2:
                        st.metric("持续时间", f"{stats['duration']:.1f}s")
                        st.metric("最小距离", f"{stats['min_distance']:.1f}km")
                        st.metric("成功率", f"{stats['success_rate']:.1f}%")
                        st.metric("最小性能", f"{stats['min_performance']:.1f}%")
    
    def create_realtime_monitor(self):
        """创建实时监控面板"""
        st.header("📊 实时监控")
        
        # 显示实时数据
        if hasattr(self, 'current_metrics'):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "导引头性能",
                    f"{self.current_metrics.get('performance', 0):.1f}%",
                    delta="+1.2%" if hasattr(self, 'last_performance') else None
                )
                
            with col2:
                st.metric(
                    "目标距离", 
                    f"{self.current_metrics.get('target_distance', 0):.1f} km"
                )
                
            with col3:
                st.metric(
                    "干扰强度",
                    f"{self.current_metrics.get('jamming_power', 0):.1f}%"
                )
                
            with col4:
                st.metric(
                    "仿真时间",
                    f"{self.controller.current_time:.1f}s"
                )
        
        # 显示监控图表
        if self.controller.is_running and not self.controller.is_paused:
            fig = self.monitor.create_realtime_dashboard()
            st.plotly_chart(fig, use_container_width=True)
    
    def run_simulation_loop(self):
        """运行仿真循环"""
        if self.controller.is_running and not self.controller.is_paused:
            result = self.controller.run_real_time_simulation()
            
            if result:
                # 更新监控指标
                self.current_metrics = {
                    'performance': result['performance'] * 100,
                    'target_distance': result['target_distance'],
                    'jamming_power': result['jamming_power'] * 100,
                    'terrain_factor': result['terrain_factor'] * 100,
                    'weather_factor': result['weather_factor'] * 100
                }
                
                self.monitor.update_metrics(self.current_metrics)
                
                # 更新界面
                st.rerun()
    
    def initialize_simulation(self):
        """初始化仿真"""
        if self.current_scenario and self.current_guidance_system:
            from core_module import Battlefield, Position, Target, Jammer, TargetType, JammingType
            
            # 创建战场对象
            battlefield = Battlefield()
            scenario_config = self.current_scenario
            
            # 设置导弹位置
            missile_pos = scenario_config['battlefield']['missile_position']
            battlefield.missile_position = Position(
                missile_pos['lat'], missile_pos['lon'], missile_pos['alt']
            )
            
            # 添加目标
            for target_config in scenario_config['battlefield']['targets']:
                target = Target(
                    target_id=target_config['target_id'],
                    target_type=TargetType(target_config['type']),
                    position=Position(
                        target_config['position']['lat'],
                        target_config['position']['lon'],
                        target_config['position']['alt']
                    ),
                    emission_power=target_config['emission_power'],
                    rcs=target_config['rcs']
                )
                battlefield.add_target(target)
            
            # 添加干扰机
            for jammer_config in scenario_config['battlefield']['jammers']:
                jammer = Jammer(
                    jammer_id=jammer_config['jammer_id'],
                    position=Position(
                        jammer_config['position']['lat'],
                        jammer_config['position']['lon'],
                        jammer_config['position']['alt']
                    ),
                    jamming_type=JammingType(jammer_config['type']),
                    power=jammer_config['power'],
                    range=jammer_config['range']
                )
                battlefield.add_jammer(jammer)
            
            # 设置天气
            battlefield.weather_condition = scenario_config['battlefield']['weather']
            
            # 初始化仿真
            self.controller.initialize_simulation(battlefield, self.current_guidance_system)
            
            return True
        
        return False

# 辅助函数
def create_session_id() -> str:
    """创建会话ID"""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def validate_scenario_config(config: Dict) -> bool:
    """验证场景配置"""
    required_fields = ['name', 'battlefield']
    for field in required_fields:
        if field not in config:
            return False
    
    battlefield_fields = ['missile_position', 'targets']
    for field in battlefield_fields:
        if field not in config['battlefield']:
            return False
    
    return True

# 测试函数
def test_simulation_control():
    """测试仿真控制模块"""
    # 创建UI实例
    ui = SimulationUI()
    
    # 测试控制面板创建
    print("测试控制面板创建...")
    
    # 测试数据管理
    data_manager = DataManager()
    sessions = data_manager.list_simulation_sessions()
    print(f"发现 {len(sessions)} 个历史会话")
    
    # 测试场景管理
    scenario_manager = ScenarioManager(data_manager)
    scenarios = scenario_manager.list_preset_scenarios()
    print(f"发现 {len(scenarios)} 个预设场景")
    
    print("仿真控制模块测试完成")

if __name__ == "__main__":
    test_simulation_control()