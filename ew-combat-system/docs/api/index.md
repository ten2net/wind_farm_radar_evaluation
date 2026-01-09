# 电子战对抗仿真系统 API 文档

## 核心模块

### 1. 实体模块 (`src.core.entities`)

#### Position
三维位置类，包含纬度、经度和高度。

```python
class Position:
    lat: float  # 纬度
    lon: float  # 经度
    alt: float  # 海拔高度 (米)
    
    def distance_to(other: Position) -> float
    def to_array() -> np.ndarray
```

#### RadarParameters
雷达参数类，包含雷达的所有技术参数。

```python
class RadarParameters:
    frequency: float    # 频率 (GHz)
    power: float        # 功率 (kW)
    gain: float         # 增益 (dBi)
    beamwidth: float    # 波束宽度 (度)
    range_max: float    # 最大作用距离 (km)
    
    def wavelength() -> float
    def effective_range(target_rcs: float = 1.0) -> float
```

#### JammerParameters
干扰机参数类。

```python
class JammerParameters:
    frequency_range: Tuple[float, float]  # 频率范围 (GHz)
    power: float        # 功率 (W)
    gain: float         # 增益 (dBi)
    beamwidth: float    # 波束宽度 (度)
    jam_types: List[str]  # 干扰类型
    
    def effective_radiated_power() -> float
```

#### Entity
实体基类，所有实体的父类。

```python
class Entity(ABC):
    id: str
    name: str
    entity_type: EntityType
    position: Position
    state: EntityState
    
    @abstractmethod
    def update(dt: float)
    @abstractmethod
    def to_dict() -> Dict
```

#### Radar
雷达实体类。

```python
class Radar(Entity):
    radar_params: RadarParameters
    
    def calculate_coverage(n_points: int = 72) -> np.ndarray
```

#### Jammer
干扰机实体类。

```python
class Jammer(Entity):
    jammer_params: JammerParameters
    
    def calculate_jamming_sector(azimuth: float, width: float, range_km: float) -> np.ndarray
```

### 2. 仿真模块 (`src.core.simulation`)

#### PropagationModel
传播模型类，计算信号传播损耗。

```python
class PropagationModel:
    def free_space_loss() -> float
    def two_ray_loss(ht: float, hr: float) -> float
    def total_loss(ht: float = 50, hr: float = 10000) -> float
```

#### EWSimulator
电子战仿真器，计算干扰效果。

```python
class EWSimulator:
    @staticmethod
    def calculate_jamming_effect(radar: Radar, jammer: Jammer, 
                                targets: List[Target] = None,
                                environment: Dict = None) -> Dict
    @staticmethod
    def simulate_radar_coverage(radar: Radar, resolution_km: float = 5) -> np.ndarray
```

#### NetworkEWSimulator
网络化电子战仿真器。

```python
class NetworkEWSimulator:
    @staticmethod
    def simulate_network_combat(radars: List[Radar], jammers: List[Jammer],
                               targets: List[Target], time_steps: int = 100) -> Dict
```

### 3. 设计模式模块 (`src.core.patterns`)

#### Strategy Pattern
策略模式，实现不同的对抗想定。

```python
class CombatScenario(ABC):
    def setup(config: Dict[str, Any])
    def execute() -> Dict[str, Any]
    def assess() -> Dict[str, Any]

class OneVsOneScenario(CombatScenario):
    # 一对一对抗

class ManyVsOneScenario(CombatScenario):
    # 多对一对抗

class ManyVsManyScenario(CombatScenario):
    # 多对多对抗

class ScenarioFactory:
    @classmethod
    def create_scenario(scenario_type: str) -> CombatScenario
```

#### Factory Pattern
工厂模式，创建实体对象。

```python
class EntityFactory:
    @staticmethod
    def create_entity(entity_type: str, config: Dict[str, Any]) -> Entity
    @staticmethod
    def create_radar(config: Dict[str, Any]) -> Radar
    @staticmethod
    def create_jammer(config: Dict[str, Any]) -> Jammer
    @staticmethod
    def create_target(config: Dict[str, Any]) -> Target
```

#### Observer Pattern
观察者模式，实现状态更新通知。

```python
class Observer(ABC):
    def update(subject: Subject, event: Dict[str, Any])

class Subject(ABC):
    def attach(observer: Observer)
    def detach(observer: Observer)
    def notify(event: Dict[str, Any])

class SimulationSubject(Subject):
    def start_simulation()
    def update_progress(progress: float)
    def complete_simulation(results: Dict[str, Any])
```

### 4. 可视化模块 (`src.visualization`)

#### EWVisualizer
电子战可视化器，创建各种可视化图表。

```python
class EWVisualizer:
    @staticmethod
    def create_coverage_map(radars, jammers, targets=None, bbox=None)
    @staticmethod
    def create_signal_analysis_plot(simulation_results)
    @staticmethod
    def create_spectrum_analysis(frequencies, powers, radar_freqs=None, jammer_freqs=None)
    @staticmethod
    def create_3d_terrain_visualization(terrain_data, radar_positions=None, jammer_positions=None)
```

### 5. 工具模块 (`src.utils`)

#### config_loader
配置加载工具。

```python
def load_radar_database(config_path: str = "config/radar_database.yaml") -> Dict[str, Any]
def load_scenarios(config_path: str = "config/scenarios.yaml") -> Dict[str, Any]
def load_environment_config(config_path: str = "config/environment.yaml") -> Dict[str, Any]
```

#### 通用工具函数
```python
def save_results(results: Dict[str, Any], filepath: str, format: str = "json") -> bool
def load_results(filepath: str) -> Optional[Dict[str, Any]]
def calculate_statistics(data: List[float]) -> Dict[str, float]
def format_lat_lon(lat: float, lon: float) -> str
def format_distance(distance_km: float) -> str
```

## 使用示例

### 基本使用流程
1. 加载配置
2. 创建想定
3. 设置实体参数
4. 执行仿真
5. 评估结果
6. 可视化展示

### 代码示例
```python
from src.core.patterns.strategy import ScenarioFactory
from src.visualization.geoviz import EWVisualizer

# 创建想定
scenario = ScenarioFactory.create_scenario("one_vs_one")

# 配置参数
config = {
    "radar": {...},
    "jammer": {...}
}

# 设置想定
scenario.setup(config)

# 执行仿真
results = scenario.execute()

# 评估结果
assessment = scenario.assess()

# 可视化
ew_map = EWVisualizer.create_coverage_map(scenario.radars, scenario.jammers)
```

## 配置说明

### 雷达数据库配置 (`config/radar_database.yaml`)
- 定义雷达和干扰机类型
- 包含技术参数和变体
- 支持自定义扩展

### 想定配置 (`config/scenarios.yaml`)
- 预定义的对抗想定
- 包含实体位置和参数
- 支持多种对抗模式

### 环境配置 (`config/environment.yaml`)
- 地形类型
- 大气条件
- 传播模型参数
