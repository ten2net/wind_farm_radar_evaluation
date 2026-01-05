"""
雷达数据控制器模块
处理雷达数据的CRUD操作和业务逻辑
使用MVC模式中的控制器角色，协调模型和视图
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from models.radar_models import (
    RadarSystem, RadarModel, RadarFactory, RadarBand, 
    PlatformType, MissionType, TransmitterParameters, 
    AntennaParameters, SignalProcessing, PRESET_RADARS
)
from models.simulation_models import TargetParameters, SimulationScenario
from services.performance_calculator import RadarPerformanceCalculator, PerformanceAnalyzer


class RadarController:
    """雷达数据控制器 - 单例模式确保数据一致性"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RadarController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.radar_system = RadarSystem()
        self.performance_calculator = RadarPerformanceCalculator()
        self.performance_analyzer = PerformanceAnalyzer(self.performance_calculator)
        self._current_editing_radar = None
        self._radar_cache = {}  # 雷达性能缓存
        self._initialized = True
    
    def get_all_radars(self) -> Dict[str, RadarModel]:
        """获取所有雷达"""
        return self.radar_system.radars
    
    def get_radar_by_id(self, radar_id: str) -> Optional[RadarModel]:
        """根据ID获取雷达"""
        return self.radar_system.get_radar(radar_id)
    
    def get_radars_by_band(self, band: RadarBand) -> List[RadarModel]:
        """根据频段获取雷达"""
        return self.radar_system.get_radars_by_band(band)
    
    def get_radars_by_platform(self, platform: PlatformType) -> List[RadarModel]:
        """根据平台类型获取雷达"""
        return [radar for radar in self.radar_system.radars.values() 
                if radar.platform == platform]
    
    def create_radar(self, radar_data: Dict[str, Any]) -> Tuple[bool, str, Optional[RadarModel]]:
        """
        创建新雷达
        
        Args:
            radar_data: 雷达数据字典
            
        Returns:
            (成功标志, 消息, 雷达对象)
        """
        try:
            # 验证必要字段
            required_fields = ['name', 'type', 'platform']
            for field in required_fields:
                if field not in radar_data:
                    return False, f"缺少必要字段: {field}", None
            
            # 生成雷达ID
            radar_id = radar_data.get('radar_id', f"RAD_{uuid.uuid4().hex[:8].upper()}")
            
            # 使用工厂创建雷达
            radar = RadarFactory.create_radar(radar_data['type'], radar_id, radar_data['name'])
            if not radar:
                return False, f"不支持的雷达类型: {radar_data['type']}", None
            
            # 设置平台类型
            platform_str = radar_data['platform']
            platform_map = {
                '地面机动': PlatformType.GROUND_MOBILE,
                '机载': PlatformType.AIRBORNE,
                '舰载': PlatformType.SHIPBORNE,
                '固定阵地': PlatformType.FIXED
            }
            radar.platform = platform_map.get(platform_str, PlatformType.GROUND_MOBILE)
            
            # 设置任务类型
            mission_strs = radar_data.get('mission_types', [])
            mission_map = {
                '远程预警': MissionType.EARLY_WARNING,
                '反隐身': MissionType.ANTI_STEALTH,
                '空中预警': MissionType.AIRBORNE_AWACS,
                '指挥控制': MissionType.COMMAND_CONTROL,
                '区域防空': MissionType.AREA_DEFENSE,
                '火控': MissionType.FIRE_CONTROL,
                '海事监视': MissionType.MARITIME_SURVEILLANCE
            }
            radar.mission_types = [mission_map[m] for m in mission_strs if m in mission_map]
            
            # 设置发射机参数
            if 'transmitter' in radar_data:
                tx_data = radar_data['transmitter']
                radar.transmitter = TransmitterParameters(
                    frequency_hz=tx_data.get('frequency_hz', 0),
                    power_w=tx_data.get('power_w', 0),
                    pulse_width_s=tx_data.get('pulse_width_s', 0),
                    prf_hz=tx_data.get('prf_hz', 1000)
                )
            
            # 设置天线参数
            if 'antenna' in radar_data:
                ant_data = radar_data['antenna']
                radar.antenna = AntennaParameters(
                    gain_dbi=ant_data.get('gain_dbi', 0),
                    azimuth_beamwidth=ant_data.get('azimuth_beamwidth', 0),
                    elevation_beamwidth=ant_data.get('elevation_beamwidth', 0)
                )
            
            # 设置信号处理参数
            if 'signal_processing' in radar_data:
                sp_data = radar_data['signal_processing']
                radar.signal_processing = SignalProcessing(
                    mti_filter=sp_data.get('mti_filter', ''),
                    doppler_channels=sp_data.get('doppler_channels', 0),
                    max_tracking_targets=sp_data.get('max_tracking_targets', 0)
                )
            
            # 设置其他参数
            radar.theoretical_range_km = radar_data.get('theoretical_range_km', 0)
            radar.deployment_method = radar_data.get('deployment_method', '')
            
            # 验证雷达参数
            if not radar.validate_parameters():
                return False, "雷达参数验证失败", None
            
            # 添加到系统
            if self.radar_system.add_radar(radar):
                # 清除缓存
                if radar_id in self._radar_cache:
                    del self._radar_cache[radar_id]
                
                return True, f"雷达 {radar_id} 创建成功", radar
            else:
                return False, "添加雷达到系统失败", None
                
        except Exception as e:
            return False, f"创建雷达时发生错误: {str(e)}", None
    
    def update_radar(self, radar_id: str, radar_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        更新雷达数据
        
        Args:
            radar_id: 雷达ID
            radar_data: 更新数据
            
        Returns:
            (成功标志, 消息)
        """
        try:
            radar = self.radar_system.get_radar(radar_id)
            if not radar:
                return False, f"未找到雷达: {radar_id}"
            
            # 更新基本属性
            if 'name' in radar_data:
                radar.name = radar_data['name']
            
            if 'platform' in radar_data:
                platform_str = radar_data['platform']
                platform_map = {
                    '地面机动': PlatformType.GROUND_MOBILE,
                    '机载': PlatformType.AIRBORNE,
                    '舰载': PlatformType.SHIPBORNE,
                    '固定阵地': PlatformType.FIXED
                }
                radar.platform = platform_map.get(platform_str, PlatformType.GROUND_MOBILE)
            
            # 更新任务类型
            if 'mission_types' in radar_data:
                mission_strs = radar_data['mission_types']
                mission_map = {
                    '远程预警': MissionType.EARLY_WARNING,
                    '反隐身': MissionType.ANTI_STEALTH,
                    '空中预警': MissionType.AIRBORNE_AWACS,
                    '指挥控制': MissionType.COMMAND_CONTROL,
                    '区域防空': MissionType.AREA_DEFENSE,
                    '火控': MissionType.FIRE_CONTROL,
                    '海事监视': MissionType.MARITIME_SURVEILLANCE
                }
                radar.mission_types = [mission_map[m] for m in mission_strs if m in mission_map]
            
            # 更新发射机参数
            if 'transmitter' in radar_data:
                tx_data = radar_data['transmitter']
                if radar.transmitter:
                    # 更新现有参数
                    if 'frequency_hz' in tx_data:
                        radar.transmitter.frequency_hz = tx_data['frequency_hz']
                    if 'power_w' in tx_data:
                        radar.transmitter.power_w = tx_data['power_w']
                    if 'pulse_width_s' in tx_data:
                        radar.transmitter.pulse_width_s = tx_data['pulse_width_s']
                    if 'prf_hz' in tx_data:
                        radar.transmitter.prf_hz = tx_data['prf_hz']
                else:
                    # 创建新参数
                    radar.transmitter = TransmitterParameters(
                        frequency_hz=tx_data.get('frequency_hz', 0),
                        power_w=tx_data.get('power_w', 0),
                        pulse_width_s=tx_data.get('pulse_width_s', 0),
                        prf_hz=tx_data.get('prf_hz', 1000)
                    )
            
            # 更新天线参数
            if 'antenna' in radar_data:
                ant_data = radar_data['antenna']
                if radar.antenna:
                    if 'gain_dbi' in ant_data:
                        radar.antenna.gain_dbi = ant_data['gain_dbi']
                    if 'azimuth_beamwidth' in ant_data:
                        radar.antenna.azimuth_beamwidth = ant_data['azimuth_beamwidth']
                    if 'elevation_beamwidth' in ant_data:
                        radar.antenna.elevation_beamwidth = ant_data['elevation_beamwidth']
                else:
                    radar.antenna = AntennaParameters(
                        gain_dbi=ant_data.get('gain_dbi', 0),
                        azimuth_beamwidth=ant_data.get('azimuth_beamwidth', 0),
                        elevation_beamwidth=ant_data.get('elevation_beamwidth', 0)
                    )
            
            # 更新信号处理参数
            if 'signal_processing' in radar_data:
                sp_data = radar_data['signal_processing']
                if radar.signal_processing:
                    if 'mti_filter' in sp_data:
                        radar.signal_processing.mti_filter = sp_data['mti_filter']
                    if 'doppler_channels' in sp_data:
                        radar.signal_processing.doppler_channels = sp_data['doppler_channels']
                    if 'max_tracking_targets' in sp_data:
                        radar.signal_processing.max_tracking_targets = sp_data['max_tracking_targets']
                else:
                    radar.signal_processing = SignalProcessing(
                        mti_filter=sp_data.get('mti_filter', ''),
                        doppler_channels=sp_data.get('doppler_channels', 0),
                        max_tracking_targets=sp_data.get('max_tracking_targets', 0)
                    )
            
            # 更新其他参数
            if 'theoretical_range_km' in radar_data:
                radar.theoretical_range_km = radar_data['theoretical_range_km']
            if 'deployment_method' in radar_data:
                radar.deployment_method = radar_data['deployment_method']
            
            # 验证更新后的参数
            if not radar.validate_parameters():
                return False, "雷达参数验证失败"
            
            # 清除缓存
            if radar_id in self._radar_cache:
                del self._radar_cache[radar_id]
            
            return True, f"雷达 {radar_id} 更新成功"
            
        except Exception as e:
            return False, f"更新雷达时发生错误: {str(e)}"
    
    def delete_radar(self, radar_id: str) -> Tuple[bool, str]:
        """
        删除雷达
        
        Args:
            radar_id: 雷达ID
            
        Returns:
            (成功标志, 消息)
        """
        if radar_id not in self.radar_system.radars:
            return False, f"未找到雷达: {radar_id}"
        
        del self.radar_system.radars[radar_id]
        
        # 清除缓存
        if radar_id in self._radar_cache:
            del self._radar_cache[radar_id]
        
        return True, f"雷达 {radar_id} 删除成功"
    
    def get_radar_performance(self, radar_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取雷达性能数据（带缓存）
        
        Args:
            radar_id: 雷达ID
            use_cache: 是否使用缓存
            
        Returns:
            性能数据字典
        """
        if use_cache and radar_id in self._radar_cache:
            return self._radar_cache[radar_id]
        
        radar = self.get_radar_by_id(radar_id)
        if not radar:
            return None
        
        performance = self.performance_calculator.calculate_system_performance(radar)
        
        # 添加基本信息
        performance.update({
            'radar_id': radar_id,
            'radar_name': radar.name,
            'band': radar.get_band().value,
            'platform': radar.platform.value,
            'mission_types': [m.value for m in radar.mission_types],
            'calculation_time': datetime.now().isoformat()
        })
        
        # 缓存结果（有效期5分钟）
        if use_cache:
            self._radar_cache[radar_id] = performance
        
        return performance
    
    def compare_radars(self, radar_ids: List[str]) -> Dict[str, Any]:
        """
        比较多个雷达的性能
        
        Args:
            radar_ids: 雷达ID列表
            
        Returns:
            比较结果
        """
        radars = [self.get_radar_by_id(rid) for rid in radar_ids if self.get_radar_by_id(rid)]
        
        if not radars:
            return {'error': '未找到有效的雷达'}
        
        return self.performance_calculator.compare_radars(radars)
    
    def generate_performance_report(self, radar_id: str) -> Optional[Dict[str, Any]]:
        """
        生成雷达性能报告
        
        Args:
            radar_id: 雷达ID
            
        Returns:
            性能报告
        """
        radar = self.get_radar_by_id(radar_id)
        if not radar:
            return None
        
        return self.performance_analyzer.generate_performance_report(radar)
    
    def search_radars(self, query: str, filters: Dict[str, Any] = None) -> List[RadarModel]:
        """
        搜索雷达
        
        Args:
            query: 搜索关键词
            filters: 过滤条件
            
        Returns:
            匹配的雷达列表
        """
        filters = filters or {}
        results = []
        
        for radar_id, radar in self.radar_system.radars.items():
            # 关键词搜索
            if query and query.lower() not in radar.name.lower() and query not in radar_id:
                continue
            
            # 频段过滤
            if 'band' in filters and filters['band']:
                if radar.get_band().value != filters['band']:
                    continue
            
            # 平台过滤
            if 'platform' in filters and filters['platform']:
                if radar.platform.value != filters['platform']:
                    continue
            
            # 任务类型过滤
            if 'mission_type' in filters and filters['mission_type']:
                mission_values = [m.value for m in radar.mission_types]
                if filters['mission_type'] not in mission_values:
                    continue
            
            results.append(radar)
        
        return results
    
    def export_radar_config(self, radar_id: str) -> Optional[Dict[str, Any]]:
        """
        导出雷达配置
        
        Args:
            radar_id: 雷达ID
            
        Returns:
            配置字典
        """
        radar = self.get_radar_by_id(radar_id)
        if not radar:
            return None
        
        config = {
            'radar_id': radar_id,
            'name': radar.name,
            'type': self._get_radar_type(radar),
            'platform': radar.platform.value,
            'mission_types': [m.value for m in radar.mission_types],
            'deployment_method': radar.deployment_method,
            'theoretical_range_km': radar.theoretical_range_km,
            'export_time': datetime.now().isoformat()
        }
        
        # 发射机参数
        if radar.transmitter:
            config['transmitter'] = {
                'frequency_hz': radar.transmitter.frequency_hz,
                'power_w': radar.transmitter.power_w,
                'pulse_width_s': radar.transmitter.pulse_width_s,
                'prf_hz': radar.transmitter.prf_hz
            }
        
        # 天线参数
        if radar.antenna:
            config['antenna'] = {
                'gain_dbi': radar.antenna.gain_dbi,
                'azimuth_beamwidth': radar.antenna.azimuth_beamwidth,
                'elevation_beamwidth': radar.antenna.elevation_beamwidth
            }
        
        # 信号处理参数
        if radar.signal_processing:
            config['signal_processing'] = {
                'mti_filter': radar.signal_processing.mti_filter,
                'doppler_channels': radar.signal_processing.doppler_channels,
                'max_tracking_targets': radar.signal_processing.max_tracking_targets
            }
        
        return config
    
    def import_radar_config(self, config: Dict[str, Any]) -> Tuple[bool, str, Optional[RadarModel]]:
        """
        导入雷达配置
        
        Args:
            config: 配置字典
            
        Returns:
            (成功标志, 消息, 雷达对象)
        """
        return self.create_radar(config)
    
    def get_system_summary(self) -> Dict[str, Any]:
        """
        获取系统摘要
        
        Returns:
            系统摘要信息
        """
        summary = self.radar_system.get_performance_summary()
        
        # 添加雷达列表
        radar_list = []
        for radar_id, radar in self.radar_system.radars.items():
            radar_list.append({
                'id': radar_id,
                'name': radar.name,
                'band': radar.get_band().value,
                'platform': radar.platform.value,
                'range_km': radar.theoretical_range_km
            })
        
        summary['radars'] = radar_list
        summary['last_updated'] = datetime.now().isoformat()
        
        return summary
    
    def _get_radar_type(self, radar: RadarModel) -> str:
        """获取雷达类型字符串"""
        if hasattr(radar, '__class__'):
            class_name = radar.__class__.__name__
            if class_name == 'EarlyWarningRadar':
                return 'early_warning'
            elif class_name == 'AirborneRadar':
                return 'airborne'
            elif class_name == 'FireControlRadar':
                return 'fire_control'
            elif class_name == 'MaritimeRadar':
                return 'maritime'
        
        return 'unknown'
    
    def clear_cache(self):
        """清除性能缓存"""
        self._radar_cache.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取控制器统计信息"""
        return {
            'total_radars': len(self.radar_system.radars),
            'cache_size': len(self._radar_cache),
            'bands_represented': len(set(r.get_band() for r in self.radar_system.radars.values())),
            'platforms_represented': len(set(r.platform for r in self.radar_system.radars.values())),
            'last_operation': datetime.now().isoformat()
        }


class RadarDataValidator:
    """雷达数据验证器"""
    
    @staticmethod
    def validate_radar_data(radar_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证雷达数据
        
        Args:
            radar_data: 雷达数据
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        # 验证必要字段
        required_fields = ['name', 'type', 'platform']
        for field in required_fields:
            if field not in radar_data:
                errors.append(f"缺少必要字段: {field}")
        
        # 验证雷达类型
        valid_types = ['early_warning', 'airborne', 'fire_control', 'maritime']
        if 'type' in radar_data and radar_data['type'] not in valid_types:
            errors.append(f"无效的雷达类型: {radar_data['type']}")
        
        # 验证平台类型
        valid_platforms = ['地面机动', '机载', '舰载', '固定阵地']
        if 'platform' in radar_data and radar_data['platform'] not in valid_platforms:
            errors.append(f"无效的平台类型: {radar_data['platform']}")
        
        # 验证频率范围
        if 'transmitter' in radar_data and 'frequency_hz' in radar_data['transmitter']:
            freq = radar_data['transmitter']['frequency_hz']
            if freq < 1e6 or freq > 100e9:
                errors.append(f"频率超出合理范围: {freq} Hz")
        
        # 验证功率
        if 'transmitter' in radar_data and 'power_w' in radar_data['transmitter']:
            power = radar_data['transmitter']['power_w']
            if power <= 0 or power > 10e6:
                errors.append(f"功率值不合理: {power} W")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_transmitter_parameters(tx_params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证发射机参数"""
        errors = []
        
        if 'frequency_hz' in tx_params and tx_params['frequency_hz'] <= 0:
            errors.append("频率必须大于0")
        
        if 'power_w' in tx_params and tx_params['power_w'] <= 0:
            errors.append("功率必须大于0")
        
        if 'pulse_width_s' in tx_params and tx_params['pulse_width_s'] <= 0:
            errors.append("脉冲宽度必须大于0")
        
        return len(errors) == 0, errors


# 测试代码
if __name__ == "__main__":
    # 创建控制器实例
    controller = RadarController()
    
    # 测试获取系统摘要
    summary = controller.get_system_summary()
    print("系统摘要:")
    print(f"雷达总数: {summary['total_radars']}")
    print(f"频段分布: {summary['band_distribution']}")
    
    # 测试创建新雷达
    new_radar_data = {
        'name': '测试雷达',
        'type': 'early_warning',
        'platform': '地面机动',
        'mission_types': ['远程预警', '反隐身'],
        'transmitter': {
            'frequency_hz': 500e6,
            'power_w': 100000,
            'pulse_width_s': 100e-6
        },
        'antenna': {
            'gain_dbi': 30.0,
            'azimuth_beamwidth': 5.0,
            'elevation_beamwidth': 10.0
        },
        'theoretical_range_km': 200
    }
    
    success, message, radar = controller.create_radar(new_radar_data)
    print(f"\n创建雷达结果: {success}, {message}")
    
    if success and radar:
        # 测试获取性能
        performance = controller.get_radar_performance(radar.radar_id)
        print(f"\n雷达性能 - 最大探测距离: {performance['max_detection_range_km']:.1f} km")
        
        # 测试生成报告
        report = controller.generate_performance_report(radar.radar_id)
        print(f"\n性能报告摘要:\n{report['summary']}")
    
    # 测试控制器统计
    stats = controller.get_statistics()
    print(f"\n控制器统计: {stats}")