"""
观察者模式：实时状态更新
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class Observer(ABC):
    """观察者接口"""
    
    @abstractmethod
    def update(self, subject: 'Subject', event: Dict[str, Any]):
        """接收更新通知"""
        pass

class Subject(ABC):
    """主题（被观察者）接口"""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer):
        """附加观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer):
        """分离观察者"""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass
    
    def notify(self, event: Dict[str, Any]):
        """通知所有观察者"""
        for observer in self._observers:
            observer.update(self, event)

class SimulationSubject(Subject):
    """仿真主题"""
    
    def __init__(self):
        super().__init__()
        self.state = "idle"
        self.progress = 0.0
        self.results = {}
    
    def start_simulation(self):
        """开始仿真"""
        self.state = "running"
        self.notify({
            "event": "simulation_started",
            "time": datetime.now().isoformat(),
            "state": self.state
        })
    
    def update_progress(self, progress: float):
        """更新仿真进度"""
        self.progress = progress
        self.notify({
            "event": "progress_updated",
            "time": datetime.now().isoformat(),
            "progress": self.progress
        })
    
    def complete_simulation(self, results: Dict[str, Any]):
        """完成仿真"""
        self.state = "completed"
        self.results = results
        self.notify({
            "event": "simulation_completed",
            "time": datetime.now().isoformat(),
            "state": self.state,
            "results": self.results
        })
    
    def error_occurred(self, error: str):
        """发生错误"""
        self.state = "error"
        self.notify({
            "event": "error_occurred",
            "time": datetime.now().isoformat(),
            "state": self.state,
            "error": error
        })

class StatusObserver(Observer):
    """状态观察者"""
    
    def __init__(self, name: str = "StatusObserver"):
        self.name = name
        self.status_history = []
    
    def update(self, subject: Subject, event: Dict[str, Any]):
        """更新状态"""
        self.status_history.append({
            "time": datetime.now(),
            "event": event.get("event"),
            "data": event
        })
        
        # 根据事件类型处理
        event_type = event.get("event")
        if event_type == "simulation_started":
            print(f"[{self.name}] 仿真开始")
        elif event_type == "progress_updated":
            progress = event.get("progress", 0) * 100
            print(f"[{self.name}] 仿真进度: {progress:.1f}%")
        elif event_type == "simulation_completed":
            print(f"[{self.name}] 仿真完成")
        elif event_type == "error_occurred":
            error = event.get("error", "未知错误")
            print(f"[{self.name}] 错误: {error}")

class ResultsObserver(Observer):
    """结果观察者"""
    
    def __init__(self, output_file: str = None):
        self.output_file = output_file
        self.results = []
    
    def update(self, subject: Subject, event: Dict[str, Any]):
        """更新结果"""
        if event.get("event") == "simulation_completed":
            results = event.get("results", {})
            self.results.append({
                "timestamp": datetime.now(),
                "results": results
            })
            
            if self.output_file:
                import json
                with open(self.output_file, 'a') as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "results": results
                    }, f, ensure_ascii=False, indent=2)
                    f.write("\n")
    
    def get_latest_results(self) -> Dict:
        """获取最新结果"""
        if self.results:
            return self.results[-1]
        return {}
