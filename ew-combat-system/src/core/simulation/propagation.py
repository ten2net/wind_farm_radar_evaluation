"""
信号传播模型
实现复杂的电磁波传播计算
"""
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class TerrainProfile:
    """地形剖面数据"""
    elevations: np.ndarray
    distances: np.ndarray
    resolution: float = 100.0  # 米
    
    def get_elevation_at(self, distance: float) -> float:
        """获取指定距离处的高程"""
        if len(self.elevations) == 0:
            return 0.0
        
        idx = np.searchsorted(self.distances, distance)
        if idx == 0:
            return self.elevations[0]
        elif idx == len(self.elevations):
            return self.elevations[-1]
        else:
            # 线性插值
            x0, x1 = self.distances[idx-1], self.distances[idx]
            y0, y1 = self.elevations[idx-1], self.elevations[idx]
            return y0 + (y1 - y0) * (distance - x0) / (x1 - x0)
    
    def get_max_obstacle(self) -> Tuple[float, float]:
        """获取最大障碍物位置和高度"""
        if len(self.elevations) == 0:
            return 0.0, 0.0
        
        max_idx = np.argmax(self.elevations)
        return self.distances[max_idx], self.elevations[max_idx]

class SignalPropagation:
    """信号传播计算类"""
    
    @staticmethod
    def free_space_path_loss(frequency: float, distance: float) -> float:
        """
        自由空间路径损耗
        frequency: GHz
        distance: km
        返回: 损耗(dB)
        """
        # FSPL(dB) = 20log10(d) + 20log10(f) + 32.44
        return 20 * np.log10(distance) + 20 * np.log10(frequency) + 32.44
    
    @staticmethod
    def two_ray_path_loss(frequency: float, distance: float, 
                          ht: float, hr: float) -> float:
        """
        双径传播模型
        ht: 发射高度(m)
        hr: 接收高度(m)
        """
        # 临界距离
        d_critical = 4 * ht * hr * frequency * 1e9 / 299792458
        
        if distance * 1000 <= d_critical:
            return SignalPropagation.free_space_path_loss(frequency, distance)
        else:
            return 40 * np.log10(distance) - 20 * np.log10(ht) - 20 * np.log10(hr)
    
    @staticmethod
    def itur_p525_path_loss(frequency: float, distance: float,
                           ht: float, hr: float, terrain: str = "flat") -> float:
        """
        ITU-R P.525建议书传播模型
        """
        # 基础自由空间损耗
        fspl = SignalPropagation.free_space_path_loss(frequency, distance)
        
        # 地形修正因子
        terrain_factors = {
            "flat": 0,           # 平原
            "rolling_hills": 10,  # 丘陵
            "mountainous": 20,    # 山地
            "urban": 15,          # 城市
            "suburban": 8,        # 郊区
            "sea": -5,           # 海面
            "desert": 5,         # 沙漠
            "forest": 12         # 森林
        }
        
        terrain_correction = terrain_factors.get(terrain, 0)
        
        # 高度修正
        height_correction = -20 * np.log10((ht + hr) / 2)
        
        return fspl + terrain_correction + height_correction
    
    @staticmethod
    def atmospheric_absorption(frequency: float, distance: float,
                              temperature: float = 15, humidity: float = 50,
                              pressure: float = 1013.25) -> float:
        """
        大气吸收损耗
        简化的ITU-R P.676模型
        temperature: °C
        humidity: %
        pressure: hPa
        返回: 损耗(dB)
        """
        # 转换单位为km
        d_km = distance
        
        # 氧气吸收 (dB/km)
        gamma_o = 0
        if frequency < 1:
            gamma_o = 0.1
        elif frequency < 10:
            gamma_o = 0.2 + 0.1 * frequency
        else:
            gamma_o = 0.5 + 0.05 * frequency
        
        # 水蒸气吸收 (dB/km)
        gamma_w = 0.1 * humidity / 100
        
        # 温度和压力修正
        temp_factor = 1 + 0.01 * (temperature - 15)
        pressure_factor = pressure / 1013.25
        
        total_absorption = (gamma_o + gamma_w) * d_km * temp_factor * pressure_factor
        
        return total_absorption
    
    @staticmethod
    def rain_attenuation(frequency: float, distance: float,
                        rain_rate: float) -> float:
        """
        降雨衰减
        rain_rate: mm/h
        返回: 衰减(dB)
        """
        # 简化的降雨衰减模型
        k = 0.1  # 衰减系数
        alpha = 1.0  # 衰减指数
        
        if frequency < 10:
            k = 0.01
        elif frequency < 20:
            k = 0.1
        else:
            k = 0.5
        
        return k * (rain_rate ** alpha) * distance
    
    @staticmethod
    def fog_attenuation(frequency: float, distance: float,
                       visibility: float) -> float:
        """
        雾衰减
        visibility: km
        返回: 衰减(dB)
        """
        if visibility <= 0.05:  # 浓雾
            attenuation = 0.5 * distance
        elif visibility <= 0.5:  # 雾
            attenuation = 0.1 * distance
        elif visibility <= 1:  # 薄雾
            attenuation = 0.05 * distance
        else:
            attenuation = 0
        
        return attenuation
    
    @staticmethod
    def calculate_line_of_sight(terrain: TerrainProfile, 
                               transmitter_height: float,
                               receiver_height: float,
                               earth_radius: float = 6371000) -> bool:
        """
        计算视线(LOS)条件
        考虑地球曲率和地形
        返回: True表示视线通，False表示被遮挡
        """
        if len(terrain.distances) == 0:
            return True
        
        total_distance = terrain.distances[-1]
        
        # 考虑地球曲率
        effective_earth_radius = earth_radius * 4/3  # 标准大气折射
        
        for i, d in enumerate(terrain.distances):
            # 发射机到地形点的视线
            h_tx = transmitter_height + terrain.elevations[0]
            h_terrain = terrain.elevations[i]
            
            # 地球曲率修正
            earth_bulge = (d * (total_distance - d)) / (2 * effective_earth_radius)
            h_terrain_effective = h_terrain + earth_bulge
            
            # 计算视线高度
            h_los = h_tx - (h_tx - receiver_height) * (d / total_distance)
            
            # 如果视线被遮挡
            if h_terrain_effective > h_los:
                return False
        
        return True
    
    @staticmethod
    def diffraction_loss(terrain: TerrainProfile, 
                        frequency: float,
                        transmitter_height: float,
                        receiver_height: float) -> float:
        """
        计算绕射损耗
        使用简化的刃形绕射模型
        返回: 损耗(dB)
        """
        if len(terrain.elevations) == 0:
            return 0
        
        # 找到最高障碍物
        max_obstacle_idx = np.argmax(terrain.elevations)
        max_obstacle_height = terrain.elevations[max_obstacle_idx]
        obstacle_distance = terrain.distances[max_obstacle_idx]
        
        total_distance = terrain.distances[-1]
        
        # 计算障碍物参数
        h = max_obstacle_height - (
            transmitter_height + (receiver_height - transmitter_height) * 
            obstacle_distance / total_distance
        )
        
        if h <= 0:
            return 0  # 无绕射
        
        # 计算Fresnel参数
        wavelength = 299792458 / (frequency * 1e9)
        d1 = obstacle_distance
        d2 = total_distance - obstacle_distance
        
        v = h * np.sqrt(2 * (d1 + d2) / (wavelength * d1 * d2))
        
        # 计算绕射损耗
        if v <= 0:
            loss = 0
        elif v <= 1:
            loss = 6 + 9 * v - 1.27 * v**2
        elif v <= 2.4:
            loss = 13 + 20 * np.log10(v)
        else:
            loss = 20 + 10 * np.log10(v) + 0.003 * v**2
        
        return loss
    
    @staticmethod
    def knife_edge_diffraction(frequency: float, distance: float,
                              obstacle_height: float, obstacle_distance: float) -> float:
        """
        刃形绕射模型
        返回: 绕射损耗(dB)
        """
        wavelength = 299792458 / (frequency * 1e9)
        
        # Fresnel参数
        d1 = obstacle_distance
        d2 = distance - obstacle_distance
        
        v = obstacle_height * np.sqrt(2 * (d1 + d2) / (wavelength * d1 * d2))
        
        # 计算绕射损耗
        if v <= 0:
            return 0
        elif v <= 1:
            return 6 + 9 * v - 1.27 * v**2
        elif v <= 2.4:
            return 13 + 20 * np.log10(v)
        else:
            return 20 + 10 * np.log10(v) + 0.003 * v**2
    
    @staticmethod
    def multipath_fading(distance: float, frequency: float,
                        reflection_coefficient: float = 0.5) -> float:
        """
        多径衰落计算
        reflection_coefficient: 反射系数
        返回: 衰落深度(dB)
        """
        # 简化的瑞利衰落模型
        wavelength = 299792458 / (frequency * 1e9)
        
        # 路径差
        path_difference = wavelength / 4
        
        # 衰落深度
        fading_depth = 20 * np.log10(1 + reflection_coefficient)
        
        return fading_depth
    
    @staticmethod
    def total_path_loss(frequency: float, distance: float,
                       ht: float, hr: float,
                       terrain: TerrainProfile = None,
                       terrain_type: str = "flat",
                       rain_rate: float = 0,
                       fog_visibility: float = 10,
                       temperature: float = 15,
                       humidity: float = 50,
                       pressure: float = 1013.25) -> float:
        """
        计算总路径损耗
        包括自由空间损耗、大气吸收、降雨衰减、绕射损耗等
        返回: 总损耗(dB)
        """
        # 基础自由空间损耗
        total_loss = SignalPropagation.free_space_path_loss(frequency, distance)
        
        # 大气吸收
        total_loss += SignalPropagation.atmospheric_absorption(
            frequency, distance, temperature, humidity, pressure
        )
        
        # 降雨衰减
        if rain_rate > 0:
            total_loss += SignalPropagation.rain_attenuation(
                frequency, distance, rain_rate
            )
        
        # 雾衰减
        if fog_visibility < 10:
            total_loss += SignalPropagation.fog_attenuation(
                frequency, distance, fog_visibility
            )
        
        # 地形绕射
        if terrain is not None:
            if not SignalPropagation.calculate_line_of_sight(terrain, ht, hr):
                diff_loss = SignalPropagation.diffraction_loss(
                    terrain, frequency, ht, hr
                )
                total_loss += diff_loss
        else:
            # 使用简化地形模型
            total_loss += SignalPropagation.itur_p525_path_loss(
                frequency, distance, ht, hr, terrain_type
            )
        
        return total_loss
    
    @staticmethod
    def calculate_effective_range(transmit_power: float, transmit_gain: float,
                                 receive_sensitivity: float, frequency: float,
                                 target_rcs: float = 1.0,
                                 propagation_conditions: Dict = None) -> float:
        """
        计算雷达有效作用距离
        transmit_power: 发射功率(W)
        transmit_gain: 发射增益(dBi)
        receive_sensitivity: 接收灵敏度(dBm)
        frequency: 频率(GHz)
        target_rcs: 目标RCS(m²)
        返回: 有效作用距离(km)
        """
        if propagation_conditions is None:
            propagation_conditions = {}
        
        # 雷达方程: R^4 = (Pt * G^2 * λ^2 * σ) / ((4π)^3 * Smin)
        Pt = transmit_power
        G = 10**(transmit_gain/10)  # dB to linear
        λ = 299792458 / (frequency * 1e9)
        σ = target_rcs
        
        # 接收灵敏度转换为W
        Smin_w = 10**((receive_sensitivity - 30)/10)  # dBm to W
        
        # 理想情况下的最大距离
        R4_ideal = (Pt * G**2 * λ**2 * σ) / ((4*np.pi)**3 * Smin_w)
        R_ideal = R4_ideal**0.25 / 1000  # 转换为km
        
        # 考虑传播损耗
        if propagation_conditions:
            # 简化的传播损耗修正
            propagation_loss = SignalPropagation.total_path_loss(
                frequency, R_ideal, 
                propagation_conditions.get('ht', 50),
                propagation_conditions.get('hr', 10000),
                terrain_type=propagation_conditions.get('terrain', 'flat'),
                rain_rate=propagation_conditions.get('rain_rate', 0)
            )
            
            # 修正后的距离
            R_effective = R_ideal * 10**(-propagation_loss/40)
        else:
            R_effective = R_ideal
        
        return R_effective
    
    @staticmethod
    def calculate_fresnel_zones(frequency: float, distance: float,
                               point_distance: float) -> List[float]:
        """
        计算菲涅尔区半径
        frequency: 频率(GHz)
        distance: 总距离(km)
        point_distance: 计算点到发射机的距离(km)
        返回: 各阶菲涅尔区半径列表
        """
        wavelength = 299792458 / (frequency * 1e9)
        d1 = point_distance * 1000  # 转换为米
        d2 = (distance - point_distance) * 1000
        
        fresnel_zones = []
        for n in range(1, 4):  # 计算前3阶菲涅尔区
            radius = np.sqrt(n * wavelength * d1 * d2 / (d1 + d2))
            fresnel_zones.append(radius)
        
        return fresnel_zones
    
    @staticmethod
    def calculate_doppler_shift(frequency: float, radial_velocity: float) -> float:
        """
        计算多普勒频移
        frequency: 载波频率(GHz)
        radial_velocity: 径向速度(m/s)
        返回: 多普勒频移(Hz)
        """
        c = 299792458  # 光速
        f_shift = 2 * radial_velocity * frequency * 1e9 / c
        return f_shift

class PropagationModel:
    """传播模型封装类"""
    
    def __init__(self, frequency: float, distance: float, 
                 terrain_type: str = "flat", atmosphere: str = "standard"):
        """
        初始化传播模型
        frequency: 频率(GHz)
        distance: 距离(km)
        terrain_type: 地形类型
        atmosphere: 大气条件
        """
        self.frequency = frequency
        self.distance = distance
        self.terrain_type = terrain_type
        self.atmosphere = atmosphere
        
        # 大气参数映射
        self.atmosphere_params = {
            "standard": {"temperature": 15, "humidity": 50, "pressure": 1013.25, "rain_rate": 0},
            "anomalous": {"temperature": 20, "humidity": 80, "pressure": 1013.25, "rain_rate": 0},
            "rainy": {"temperature": 15, "humidity": 90, "pressure": 1013.25, "rain_rate": 25},
            "sandstorm": {"temperature": 25, "humidity": 30, "pressure": 1013.25, "rain_rate": 0}
        }
    
    def free_space_loss(self) -> float:
        """计算自由空间损耗"""
        return SignalPropagation.free_space_path_loss(self.frequency, self.distance)
    
    def two_ray_loss(self, ht: float, hr: float) -> float:
        """计算双径模型损耗"""
        return SignalPropagation.two_ray_path_loss(self.frequency, self.distance, ht, hr)
    
    def atmospheric_absorption(self) -> float:
        """计算大气吸收损耗"""
        params = self.atmosphere_params.get(self.atmosphere, self.atmosphere_params["standard"])
        return SignalPropagation.atmospheric_absorption(
            self.frequency, self.distance,
            params["temperature"], params["humidity"], params["pressure"]
        )
    
    def rain_attenuation(self) -> float:
        """计算降雨衰减"""
        params = self.atmosphere_params.get(self.atmosphere, self.atmosphere_params["standard"])
        return SignalPropagation.rain_attenuation(
            self.frequency, self.distance, params["rain_rate"]
        )
    
    def total_loss(self, ht: float = 50, hr: float = 10000, 
                  terrain_profile: TerrainProfile = None) -> float:
        """计算总传播损耗"""
        params = self.atmosphere_params.get(self.atmosphere, self.atmosphere_params["standard"])
        
        return SignalPropagation.total_path_loss(
            frequency=self.frequency,
            distance=self.distance,
            ht=ht,
            hr=hr,
            terrain=terrain_profile,
            terrain_type=self.terrain_type,
            rain_rate=params["rain_rate"],
            temperature=params["temperature"],
            humidity=params["humidity"],
            pressure=params["pressure"]
        )
    
    def calculate_received_power(self, transmit_power: float, 
                               transmit_gain: float, receive_gain: float) -> float:
        """
        计算接收功率
        transmit_power: 发射功率(W)
        transmit_gain: 发射增益(dBi)
        receive_gain: 接收增益(dBi)
        返回: 接收功率(dBm)
        """
        # 发射ERP
        transmit_erp_db = 10 * np.log10(transmit_power) + transmit_gain
        
        # 总传播损耗
        total_loss_db = self.total_loss()
        
        # 接收功率
        received_power_db = transmit_erp_db - total_loss_db + receive_gain
        
        return received_power_db
