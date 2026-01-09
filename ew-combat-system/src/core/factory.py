"""
实体工厂类
"""
from typing import Dict, Any, List, Optional
import yaml
import json
from pathlib import Path
from .entities import (
    EntityType, Radar, Jammer, Target, Position, 
    RadarParameters, JammerParameters, 
    EntityState
)
from .entities.target import Aircraft, Missile, Ship
from .simulation import PropagationModel

class EntityFactory:
    """实体工厂"""
    
    _radar_templates = {}
    _jammer_templates = {}
    _target_templates = {}
    
    @classmethod
    def load_templates(cls, config_path: str = "config/radar_database.yaml"):
        """从配置文件加载模板"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                cls._load_default_templates()
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 加载雷达模板
            if 'radar_types' in config:
                for radar_type, data in config['radar_types'].items():
                    cls._radar_templates[radar_type] = {
                        'base': data.get('base_params', {}),
                        'variants': data.get('variants', [])
                    }
            
            # 加载干扰机模板
            if 'jammer_types' in config:
                for jammer_type, data in config['jammer_types'].items():
                    cls._jammer_templates[jammer_type] = {
                        'base': data.get('base_params', {}),
                        'variants': data.get('variants', [])
                    }
            
            # 加载目标模板
            if 'target_types' in config:
                for target_type, data in config['target_types'].items():
                    cls._target_templates[target_type] = {
                        'base': data.get('base_params', {}),
                        'variants': data.get('variants', [])
                    }
                    
        except Exception as e:
            print(f"加载模板失败: {e}")
            cls._load_default_templates()
    
    @classmethod
    def _load_default_templates(cls):
        """加载默认模板"""
        cls._radar_templates = {
            'early_warning': {
                'base': {
                    'name': '预警雷达',
                    'frequency': 3.0,
                    'power': 200.0,
                    'gain': 40.0,
                    'beamwidth': 1.5
                },
                'variants': []
            }
        }
        
        cls._jammer_templates = {
            'standoff_jammer': {
                'base': {
                    'name': '远距支援干扰机',
                    'power': 1000.0,
                    'gain': 15.0,
                    'beamwidth': 60.0
                },
                'variants': []
            }
        }
    
    @classmethod
    def create_radar(cls, config: Dict[str, Any]) -> Radar:
        """创建雷达实体"""
        # 获取雷达类型
        radar_type = config.get('type', 'early_warning')
        variant_name = config.get('variant', '')
        
        # 获取模板
        template = cls._radar_templates.get(radar_type, {})
        
        # 查找具体型号
        variant_config = None
        for variant in template.get('variants', []):
            if variant.get('name') == variant_name or variant.get('id') == variant_name:
                variant_config = variant
                break
        
        if not variant_config:
            # 使用默认配置
            base_params = template.get('base', {})
            variant_config = {'params': base_params.copy()}
        
        # 合并参数
        params = variant_config.get('params', {}).copy()
        
        # 应用覆盖参数
        params_override = config.get('params_override', {})
        params.update(params_override)
        
        # 从config中获取直接指定的参数
        for key in ['frequency', 'power', 'gain', 'beamwidth', 'range_max']:
            if key in config:
                params[key] = config[key]
        
        # 位置
        position_config = config.get('position', {})
        position = Position(
            lat=position_config.get('lat', config.get('lat', 39.9)),
            lon=position_config.get('lon', config.get('lon', 116.4)),
            alt=position_config.get('alt', config.get('alt', 0.0))
        )
        
        # 创建雷达参数对象
        radar_params = RadarParameters(
            frequency=params.get('frequency', 3.0),
            power=params.get('power', 100.0),
            gain=params.get('gain', 40.0),
            beamwidth=params.get('beamwidth', 1.5),
            pulse_width=params.get('pulse_width', 1.0),
            prf=params.get('prf', 1000.0),
            sensitivity=params.get('sensitivity', -120.0),
            range_max=params.get('range_max', 300.0),
            altitude_max=params.get('altitude_max', 25000.0),
            scan_pattern=params.get('scan_pattern', 'circular'),
            scan_rate=params.get('scan_rate', 6.0)
        )
        
        # 创建雷达实体
        radar = Radar(
            id=config.get('id', f"radar_{id(config)}"),
            name=config.get('variant', variant_config.get('name', '未知雷达')),
            entity_type=EntityType.RADAR,
            position=position,
            radar_params=radar_params,
            state=EntityState.ACTIVE,
            parameters=params
        )
        
        return radar
    
    @classmethod
    def create_jammer(cls, config: Dict[str, Any]) -> Jammer:
        """创建干扰机实体"""
        # 获取干扰机类型
        jammer_type = config.get('type', 'standoff_jammer')
        variant_name = config.get('variant', '')
        
        # 获取模板
        template = cls._jammer_templates.get(jammer_type, {})
        
        # 查找具体型号
        variant_config = None
        for variant in template.get('variants', []):
            if variant.get('name') == variant_name or variant.get('id') == variant_name:
                variant_config = variant
                break
        
        if not variant_config:
            # 使用默认配置
            base_params = template.get('base', {})
            variant_config = {'params': base_params.copy()}
        
        # 合并参数
        params = variant_config.get('params', {}).copy()
        
        # 应用覆盖参数
        params_override = config.get('params_override', {})
        params.update(params_override)
        
        # 从config中获取直接指定的参数
        for key in ['power', 'gain', 'beamwidth', 'range_effective']:
            if key in config:
                params[key] = config[key]
        
        # 位置
        position_config = config.get('position', {})
        position = Position(
            lat=position_config.get('lat', config.get('lat', 40.0)),
            lon=position_config.get('lon', config.get('lon', 116.5)),
            alt=position_config.get('alt', config.get('alt', 0.0))
        )
        
        # 创建干扰机参数对象
        jammer_params = JammerParameters(
            frequency_range=params.get('frequency_range', (0.5, 18.0)),
            power=params.get('power', 1000.0),
            gain=params.get('gain', 15.0),
            beamwidth=params.get('beamwidth', 60.0),
            eirp=params.get('eirp', 80.0),
            jam_types=params.get('jam_types', ['阻塞', '扫频', '灵巧']),
            response_time=params.get('response_time', 2.0),
            bandwidth=params.get('bandwidth', 100.0)
        )
        
        # 创建干扰机实体
        jammer = Jammer(
            id=config.get('id', f"jammer_{id(config)}"),
            name=config.get('variant', variant_config.get('name', '未知干扰机')),
            entity_type=EntityType.JAMMER,
            position=position,
            jammer_params=jammer_params,
            state=EntityState.ACTIVE,
            parameters=params
        )
        
        return jammer
    
    @classmethod
    def create_target(cls, config: Dict[str, Any]) -> Target:
        """创建目标实体"""
        target_type = config.get('type', 'aircraft')
        
        # 获取模板
        template = cls._target_templates.get(target_type, {})
        
        # 查找具体型号
        variant_name = config.get('variant', '')
        variant_config = None
        for variant in template.get('variants', []):
            if variant.get('name') == variant_name or variant.get('id') == variant_name:
                variant_config = variant
                break
        
        if not variant_config:
            # 使用默认配置
            base_params = template.get('base', {})
            variant_config = {'params': base_params.copy()}
        
        # 合并参数
        params = variant_config.get('params', {}).copy()
        
        # 应用覆盖参数
        params_override = config.get('params_override', {})
        params.update(params_override)
        
        # 从config中获取直接指定的参数
        for key in ['rcs', 'speed', 'altitude']:
            if key in config:
                params[key] = config[key]
        
        # 位置
        position_config = config.get('position', {})
        position = Position(
            lat=position_config.get('lat', config.get('lat', 40.0)),
            lon=position_config.get('lon', config.get('lon', 116.5)),
            alt=position_config.get('alt', config.get('alt', params.get('altitude', 10000.0)))
        )
        
        # 轨迹
        trajectory = config.get('trajectory', [])
        
        # 创建目标
        target = Target(
            id=config.get('id', f"target_{id(config)}"),
            name=config.get('name', variant_config.get('name', '未知目标')),
            entity_type=EntityType.TARGET,
            position=position,
            rcs=params.get('rcs', 1.0),
            speed=params.get('speed', 300.0),
            trajectory=trajectory
        )
        
        # 设置额外的参数
        target.parameters = params
        
        return target
    
    @classmethod
    def create_entity(cls, entity_type: str, config: Dict[str, Any]):
        """通用实体创建方法"""
        if entity_type == 'radar':
            return cls.create_radar(config)
        elif entity_type == 'jammer':
            return cls.create_jammer(config)
        elif entity_type == 'target':
            return cls.create_target(config)
        else:
            raise ValueError(f"未知的实体类型: {entity_type}")
    
    @classmethod
    def create_from_template(cls, template_name: str, config_overrides: Dict = None) -> Dict: # type: ignore
        """从模板创建实体"""
        if config_overrides is None:
            config_overrides = {}
        
        # 这里可以实现从预设模板加载
        # 简化实现
        if template_name == 'basic_radar':
            base_config = {
                'type': 'early_warning',
                'name': '基本雷达',
                'frequency': 3.0,
                'power': 100.0
            }
        elif template_name == 'basic_jammer':
            base_config = {
                'type': 'standoff_jammer',
                'name': '基本干扰机',
                'power': 1000.0
            }
        else:
            base_config = {}
        
        base_config.update(config_overrides)
        
        # 根据模板名称决定创建什么类型的实体
        if 'radar' in template_name:
            return cls.create_radar(base_config) # type: ignore
        elif 'jammer' in template_name:
            return cls.create_jammer(base_config) # type: ignore
        elif 'target' in template_name:
            return cls.create_target(base_config) # type: ignore
        else:
            raise ValueError(f"未知的模板: {template_name}")
    
    @classmethod
    def batch_create_entities(cls, configs: List[Dict[str, Any]]) -> Dict[str, List]:
        """批量创建实体"""
        entities = {
            'radars': [],
            'jammers': [],
            'targets': []
        }
        
        for config in configs:
            entity_type = config.get('entity_type')
            
            if entity_type == 'radar':
                radar = cls.create_radar(config)
                entities['radars'].append(radar)
            elif entity_type == 'jammer':
                jammer = cls.create_jammer(config)
                entities['jammers'].append(jammer)
            elif entity_type == 'target':
                target = cls.create_target(config)
                entities['targets'].append(target)
        
        return entities
