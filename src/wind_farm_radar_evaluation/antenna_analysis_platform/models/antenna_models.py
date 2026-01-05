"""
天线数据模型定义
使用Python数据类定义天线系统的基本参数和配置
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from enum import Enum
import json
from datetime import datetime

class AntennaType(str, Enum):
    """天线类型枚举"""
    DIPOLE = "dipole"  # 偶极子天线
    PATCH = "patch"    # 微带贴片天线
    HORN = "horn"      # 喇叭天线
    PARABOLIC = "parabolic"  # 抛物面天线
    ARRAY = "array"    # 阵列天线
    YAGI = "yagi"      # 八木天线
    HELICAL = "helical"  # 螺旋天线
    LOG_PERIODIC = "log_periodic"  # 对数周期天线
    CUSTOM = "custom"  # 自定义天线

class PolarizationType(str, Enum):
    """极化类型枚举"""
    LINEAR_VERTICAL = "vertical"  # 线极化-垂直
    LINEAR_HORIZONTAL = "horizontal"  # 线极化-水平
    CIRCULAR_RIGHT = "right_circular"  # 右旋圆极化
    CIRCULAR_LEFT = "left_circular"  # 左旋圆极化
    DUAL = "dual"  # 双极化
    SLANT_45 = "slant_45"  # 45度斜极化

class FeedType(str, Enum):
    """馈电类型枚举"""
    EDGE_FED = "edge_fed"  # 边馈
    COAXIAL_FED = "coaxial_fed"  # 同轴馈电
    APERTURE_COUPLED = "aperture_coupled"  # 口径耦合
    PROXIMITY_COUPLED = "proximity_coupled"  # 邻近耦合
    WAVEGUIDE = "waveguide"  # 波导馈电

@dataclass
class MaterialProperties:
    """材料属性"""
    name: str
    dielectric_constant: float  # 介电常数
    loss_tangent: float  # 损耗角正切
    conductivity: float = 0.0  # 电导率 (S/m)
    permeability: float = 1.0  # 磁导率
    thickness: float = 1.6  # 厚度 (mm)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'dielectric_constant': self.dielectric_constant,
            'loss_tangent': self.loss_tangent,
            'conductivity': self.conductivity,
            'permeability': self.permeability,
            'thickness': self.thickness
        }

@dataclass
class Substrate:
    """基板材料"""
    material: MaterialProperties
    height: float  # 基板高度 (mm)
    size_x: float  # 基板X方向尺寸 (mm)
    size_y: float  # 基板Y方向尺寸 (mm)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'material': self.material.to_dict(),
            'height': self.height,
            'size_x': self.size_x,
            'size_y': self.size_y
        }

@dataclass
class Element:
    """天线阵元"""
    name: str
    type: AntennaType
    position: Tuple[float, float, float]  # (x, y, z) 位置 (mm)
    orientation: Tuple[float, float, float] = (0, 0, 0)  # (roll, pitch, yaw) 角度 (度)
    amplitude: float = 1.0  # 激励幅度
    phase: float = 0.0  # 激励相位 (度)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'type': self.type.value,
            'position': self.position,
            'orientation': self.orientation,
            'amplitude': self.amplitude,
            'phase': self.phase
        }

@dataclass
class AntennaGeometry:
    """天线几何结构"""
    elements: List[Element] = field(default_factory=list)
    substrate: Optional[Substrate] = None
    ground_plane: Optional[Tuple[float, float]] = None  # 地平面尺寸 (mm)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'elements': [elem.to_dict() for elem in self.elements],
            'substrate': self.substrate.to_dict() if self.substrate else None,
            'ground_plane': self.ground_plane
        }

@dataclass
class FeedNetwork:
    """馈电网络"""
    type: FeedType
    impedance: float = 50.0  # 特性阻抗 (Ω)
    matching_network: Optional[Dict[str, Any]] = None
    power_splitter: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'type': self.type.value,
            'impedance': self.impedance,
            'matching_network': self.matching_network,
            'power_splitter': self.power_splitter
        }

@dataclass
class AntennaParameters:
    """天线基本参数
    
    注意：dataclass要求没有默认值的字段放在有默认值的字段之前
    """
    # 基本信息（无默认值）
    name: str
    antenna_type: AntennaType
    frequency_range: Tuple[float, float]  # 工作频段 (GHz)
    center_frequency: float  # 中心频率 (GHz)
    
    # 电气参数（无默认值）
    gain: float  # 增益 (dBi)
    bandwidth: float  # 带宽 (%)
    vswr: float  # 电压驻波比
    polarization: PolarizationType
    
    # 几何参数（无默认值）
    geometry: AntennaGeometry
    
    # 馈电网络（无默认值）
    feed_network: FeedNetwork
    
    # 辐射参数（无默认值）
    beamwidth_e: float  # E面波束宽度 (度)
    beamwidth_h: float  # H面波束宽度 (度)
    
    # 以下字段有默认值
    cross_pol_discrimination: float = 20.0  # 交叉极化鉴别度 (dB)
    sidelobe_level: float = -20.0  # 副瓣电平 (dB)
    front_to_back_ratio: float = 25.0  # 前后比 (dB)
    
    # 效率参数
    efficiency: float = 0.8  # 辐射效率
    input_power: float = 1.0  # 输入功率 (W)
    max_power: float = 10.0  # 最大输入功率 (W)
    
    # 元数据
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'antenna_type': self.antenna_type.value,
            'frequency_range': self.frequency_range,
            'center_frequency': self.center_frequency,
            'gain': self.gain,
            'bandwidth': self.bandwidth,
            'vswr': self.vswr,
            'polarization': self.polarization.value,
            'geometry': self.geometry.to_dict(),
            'feed_network': self.feed_network.to_dict(),
            'beamwidth_e': self.beamwidth_e,
            'beamwidth_h': self.beamwidth_h,
            'cross_pol_discrimination': self.cross_pol_discrimination,
            'sidelobe_level': self.sidelobe_level,
            'front_to_back_ratio': self.front_to_back_ratio,
            'efficiency': self.efficiency,
            'input_power': self.input_power,
            'max_power': self.max_power,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AntennaParameters':
        """从字典创建天线参数"""
        # 创建MaterialProperties
        substrate_data = data.get('geometry', {}).get('substrate')
        if substrate_data:
            material_data = substrate_data.get('material')
            if material_data:
                material = MaterialProperties(**material_data)
                substrate = Substrate(
                    material=material,
                    height=substrate_data.get('height', 1.6),
                    size_x=substrate_data.get('size_x', 30.0),
                    size_y=substrate_data.get('size_y', 40.0)
                )
            else:
                substrate = None
        else:
            substrate = None
        
        # 创建Elements
        elements = []
        elements_data = data.get('geometry', {}).get('elements', [])
        for elem_data in elements_data:
            elem_data = elem_data.copy()  # 避免修改原始数据
            elem_data['type'] = AntennaType(elem_data.get('type', 'patch'))
            element = Element(**elem_data)
            elements.append(element)
        
        # 创建AntennaGeometry
        geometry = AntennaGeometry(
            elements=elements,
            substrate=substrate,
            ground_plane=data.get('geometry', {}).get('ground_plane')
        )
        
        # 创建FeedNetwork
        feed_data = data.get('feed_network', {})
        if feed_data:
            feed_data = feed_data.copy()  # 避免修改原始数据
            feed_data['type'] = FeedType(feed_data.get('type', 'coaxial_fed'))
            feed_network = FeedNetwork(**feed_data)
        else:
            feed_network = FeedNetwork(type=FeedType.COAXIAL_FED)
        
        # 创建AntennaParameters
        antenna_data = data.copy()
        
        # 移除已处理的字段
        antenna_data.pop('geometry', None)
        antenna_data.pop('feed_network', None)
        
        # 转换枚举类型
        if 'antenna_type' in antenna_data:
            antenna_data['antenna_type'] = AntennaType(antenna_data['antenna_type'])
        if 'polarization' in antenna_data:
            antenna_data['polarization'] = PolarizationType(antenna_data['polarization'])
        
        return cls(
            **antenna_data,
            geometry=geometry,
            feed_network=feed_network
        )

@dataclass
class AntennaArray:
    """天线阵列配置"""
    name: str
    elements: List[AntennaParameters]
    layout: str  # 布局类型: linear, planar, circular
    spacing: Tuple[float, float]  # 阵元间距 (mm)
    rows: int  # 行数
    columns: int  # 列数
    taper_type: str = "uniform"  # 幅度锥削类型
    phase_shift: List[float] = field(default_factory=list)  # 相位偏移列表
    
    def get_element_positions(self) -> List[Tuple[float, float, float]]:
        """获取阵元位置"""
        positions = []
        dx, dy = self.spacing
        
        for i in range(self.rows):
            for j in range(self.columns):
                x = j * dx - (self.columns - 1) * dx / 2
                y = i * dy - (self.rows - 1) * dy / 2
                positions.append((x, y, 0))
        
        return positions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'elements': [elem.to_dict() for elem in self.elements],
            'layout': self.layout,
            'spacing': self.spacing,
            'rows': self.rows,
            'columns': self.columns,
            'taper_type': self.taper_type,
            'phase_shift': self.phase_shift
        }

# 预定义材料库
PREDEFINED_MATERIALS = {
    'FR4': MaterialProperties(
        name="FR4",
        dielectric_constant=4.4,
        loss_tangent=0.02,
        conductivity=0.0,
        thickness=1.6
    ),
    'ROGERS_RT5880': MaterialProperties(
        name="Rogers RT5880",
        dielectric_constant=2.2,
        loss_tangent=0.0009,
        conductivity=0.0,
        thickness=0.787
    ),
    'AIR': MaterialProperties(
        name="Air",
        dielectric_constant=1.0,
        loss_tangent=0.0,
        conductivity=0.0
    ),
    'COPPER': MaterialProperties(
        name="Copper",
        dielectric_constant=1.0,
        loss_tangent=0.0,
        conductivity=5.8e7
    )
}

# 预定义天线模板
def create_dipole_antenna(name: str = "Half-wave Dipole") -> AntennaParameters:
    """创建半波偶极子天线模板"""
    geometry = AntennaGeometry(
        elements=[
            Element(
                name="dipole_element",
                type=AntennaType.DIPOLE,
                position=(0, 0, 0),
                orientation=(0, 0, 0)
            )
        ]
    )
    
    feed_network = FeedNetwork(
        type=FeedType.COAXIAL_FED,
        impedance=73.0
    )
    
    return AntennaParameters(
        name=name,
        antenna_type=AntennaType.DIPOLE,
        frequency_range=(0.8, 1.2),
        center_frequency=1.0,
        gain=2.15,
        bandwidth=10.0,
        vswr=1.5,
        polarization=PolarizationType.LINEAR_VERTICAL,
        geometry=geometry,
        feed_network=feed_network,
        beamwidth_e=78.0,
        beamwidth_h=180.0,
        cross_pol_discrimination=30.0,
        sidelobe_level=-13.0,
        front_to_back_ratio=0.0,
        efficiency=0.95,
        description="半波偶极子天线，工作频率1GHz"
    )

def create_patch_antenna(name: str = "Microstrip Patch") -> AntennaParameters:
    """创建微带贴片天线模板"""
    substrate = Substrate(
        material=PREDEFINED_MATERIALS['FR4'],
        height=1.6,
        size_x=30.0,
        size_y=40.0
    )
    
    geometry = AntennaGeometry(
        elements=[
            Element(
                name="patch_element",
                type=AntennaType.PATCH,
                position=(0, 0, 0),
                orientation=(0, 0, 0)
            )
        ],
        substrate=substrate,
        ground_plane=(50.0, 50.0)
    )
    
    feed_network = FeedNetwork(
        type=FeedType.EDGE_FED,
        impedance=50.0
    )
    
    return AntennaParameters(
        name=name,
        antenna_type=AntennaType.PATCH,
        frequency_range=(2.4, 2.5),
        center_frequency=2.45,
        gain=7.0,
        bandwidth=3.0,
        vswr=1.2,
        polarization=PolarizationType.LINEAR_HORIZONTAL,
        geometry=geometry,
        feed_network=feed_network,
        beamwidth_e=80.0,
        beamwidth_h=60.0,
        cross_pol_discrimination=25.0,
        sidelobe_level=-15.0,
        front_to_back_ratio=20.0,
        efficiency=0.85,
        description="2.4GHz微带贴片天线，FR4基板"
    )

# 天线模板库
ANTENNA_TEMPLATES = {
    'dipole': create_dipole_antenna(),
    'patch': create_patch_antenna()
}