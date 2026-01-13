# 文件: src/core/analysis/combat_tables.py
"""
对抗分析查找表系统
基于文章中的表1-4实现
"""

class CombatAnalysisTables:
    """对抗分析查找表（基于文章表1-4）"""
    
    # 表1: 阶段有效性因素（考虑平台照明）
    STAGE_EFFECTIVENESS_WITH_ILLUMINATION = {
        'search': {
            'NJ': 0.8,    # 噪声干扰
            'CP': 0.9,    # 覆盖脉冲干扰
            'MFT': 1.0,   # 多假目标干扰
            'RGPO': -0.9, # 距离门拖引
            'VGPO': -0.9  # 速度门拖引
        },
        'acquisition': {
            'NJ': 0.9, 'CP': 0.9, 'MFT': 1.0, 'RGPO': -0.9, 'VGPO': -0.9
        },
        'tracking': {
            'NJ': -0.9, 'CP': -0.9, 'MFT': 0.0, 'RGPO': 0.9, 'VGPO': 0.8
        },
        'guidance': {
            'NJ': -0.9, 'CP': -0.9, 'MFT': 0.0, 'RGPO': 0.8, 'VGPO': 0.9
        }
    }
    
    # 表1: 阶段有效性因素（忽略平台照明）
    STAGE_EFFECTIVENESS_WITHOUT_ILLUMINATION = {
        'search': {
            'NJ': 0.8, 'CP': 0.9, 'MFT': 1.0, 'RGPO': 0.2, 'VGPO': 0.2
        },
        'acquisition': {
            'NJ': 0.9, 'CP': 0.9, 'MFT': 1.0, 'RGPO': 0.1, 'VGPO': 0.1
        },
        'tracking': {
            'NJ': 0.5, 'CP': 0.5, 'MFT': 0.0, 'RGPO': 0.9, 'VGPO': 0.8
        },
        'guidance': {
            'NJ': 0.5, 'CP': 0.5, 'MFT': 0.0, 'RGPO': 0.8, 'VGPO': 0.9
        }
    }
    
    # 表2: 技术交互因素
    TECH_INTERACTION = {
        'NJ': {'NJ': 0.0, 'CP': 0.0, 'MFT': 0.2, 'RGPO': -0.3, 'VGPO': -0.3},
        'CP': {'NJ': 0.0, 'CP': 0.0, 'MFT': 0.1, 'RGPO': 0.2, 'VGPO': 0.2},
        'MFT': {'NJ': 0.2, 'CP': 0.1, 'MFT': 0.0, 'RGPO': -0.2, 'VGPO': -0.2},
        'RGPO': {'NJ': -0.3, 'CP': 0.2, 'MFT': -0.2, 'RGPO': 0.0, 'VGPO': 0.2},
        'VGPO': {'NJ': -0.3, 'CP': 0.2, 'MFT': -0.2, 'RGPO': 0.2, 'VGPO': 0.0}
    }
    
    # 表3: 带宽调整因素
    BW_ADJUSTMENT = {
        'N': {1: 0.0, 2: None, 3: None, 4: None, 5: None},  # 窄带
        'M': {1: -0.1, 2: -0.2, 3: -0.35, 4: None, 5: None}, # 中带
        'W': {1: -0.15, 2: -0.25, 3: -0.4, 4: -0.6, 5: -0.8} # 宽带
    }
    
    # 表4: 阶段交互因素
    STAGE_INTERACTION = {
        'search': {'search': 0.1, 'acquisition': 0.0, 'tracking': 0.0, 'guidance': 0.0},
        'acquisition': {'search': 0.2, 'acquisition': 0.1, 'tracking': 0.0, 'guidance': 0.0},
        'tracking': {'search': 0.3, 'acquisition': 0.2, 'tracking': 0.1, 'guidance': 0.0},
        'guidance': {'search': 0.4, 'acquisition': 0.3, 'tracking': 0.2, 'guidance': 0.1}
    }
    
    def __init__(self, consider_illumination=True):
        """
        初始化查找表
        
        参数:
            consider_illumination: 是否考虑平台照明效应
        """
        self.consider_illumination = consider_illumination
        self.stage_effectiveness = (
            self.STAGE_EFFECTIVENESS_WITH_ILLUMINATION 
            if consider_illumination 
            else self.STAGE_EFFECTIVENESS_WITHOUT_ILLUMINATION
        )
    
    def get_stage_effectiveness(self, radar_stage, jamming_technique):
        """
        获取阶段有效性因素
        
        参数:
            radar_stage: 雷达阶段 (search, acquisition, tracking, guidance)
            jamming_technique: 干扰技术 (NJ, CP, MFT, RGPO, VGPO)
            
        返回:
            有效性因子 (float)
        """
        return self.stage_effectiveness.get(radar_stage, {}).get(jamming_technique, 0.0)
    
    def get_tech_interaction(self, tech1, tech2):
        """
        获取技术交互因素
        
        参数:
            tech1: 第一种干扰技术
            tech2: 第二种干扰技术
            
        返回:
            交互因子 (float)
        """
        return self.TECH_INTERACTION.get(tech1, {}).get(tech2, 0.0)
    
    def get_bw_adjustment(self, bw_type, assigned_targets):
        """
        获取带宽调整因素
        
        参数:
            bw_type: 带宽类型 (N, M, W)
            assigned_targets: 分配的目标数量
            
        返回:
            调整因子 (float or None)
        """
        bw_table = self.BW_ADJUSTMENT.get(bw_type, {})
        return bw_table.get(assigned_targets, None)
    
    def get_stage_interaction(self, stage1, stage2):
        """
        获取阶段交互因素
        
        参数:
            stage1: 第一阶段
            stage2: 第二阶段
            
        返回:
            交互因子 (float)
        """
        return self.STAGE_INTERACTION.get(stage1, {}).get(stage2, 0.0)