"""
教学视图
天线理论与分析方法的教学中心
包含基础知识、设计指南、分析方法、实际案例等内容
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from pathlib import Path
import yaml
import json
import sys
import os
import base64
from io import BytesIO
from enum import Enum

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.antenna_models import AntennaType, PolarizationType, PREDEFINED_MATERIALS
    from services.pattern_generator import get_pattern_generator_service
    from services.visualization_service import get_visualization_service
    from utils.config import AppConfig
    from utils.helpers import format_frequency, format_gain, format_percentage
except ImportError as e:
    st.warning(f"部分模块导入失败: {e}")

class EducationView:
    """教学视图类"""
    
    def __init__(self, config=None):
        self.config = config
        self.pattern_service = None
        self.viz_service = None
        
        # 尝试初始化服务
        try:
            from services.pattern_generator import get_pattern_generator_service
            from services.visualization_service import get_visualization_service
            self.pattern_service = get_pattern_generator_service()
            self.viz_service = get_visualization_service()
        except ImportError:
            pass
        
        # 确保content有值
        self.content = self._create_default_content()
        self.load_educational_content()
    
    def load_educational_content(self):
        """加载教学内容"""
        try:
            # 创建教学内容目录
            current_dir = Path(__file__).parent
            content_dir = current_dir.parent / "data" / "education"
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否有教学内容文件
            content_file = content_dir / "content.yaml"
            
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    loaded_content = yaml.safe_load(f)
                    if loaded_content is not None:
                        self.content = loaded_content
                    else:
                        st.warning("教学内容文件为空，使用默认内容")
            else:
                st.info("首次使用，创建默认教学内容...")
                # 保存默认内容
                with open(content_file, 'w', encoding='utf-8') as f:
                    yaml.dump(self.content, f, allow_unicode=True, default_flow_style=False)
                    
        except Exception as e:
            st.warning(f"加载教学内容失败，使用默认内容: {e}")
    
    def _create_default_content(self) -> Dict[str, Any]:
        """创建默认教学内容"""
        return {
            'fundamentals': [
                {
                    'id': 'fundamentals_1',
                    'title': '天线基本原理',
                    'sections': [
                        {
                            'title': '天线定义',
                            'content': """
                            **天线** 是将导行波与自由空间波相互转换的装置，是无线通信系统的关键组成部分。
                            
                            ## 主要功能
                            1. **发射天线**: 将高频电流转换为电磁波辐射
                            2. **接收天线**: 将电磁波转换为高频电流
                            
                            ## 基本参数
                            - **频率范围**: 天线能够有效工作的频率范围
                            - **阻抗**: 天线的输入阻抗，通常为50Ω或75Ω
                            - **极化**: 电磁波的电场方向
                            - **增益**: 天线在特定方向上的辐射能力
                            """
                        },
                        {
                            'title': '辐射原理',
                            'content': """
                            ## 电流辐射理论
                            根据麦克斯韦方程组，变化的电场产生磁场，变化的磁场产生电场。
                            
                            ### 偶极子辐射
                            最简单的天线是偶极子天线，其辐射场为：
                            
                            $$
                            E_θ = \\frac{jI_0l}{2λr} \\sqrt{\\frac{μ_0}{ε_0}} \\sin θ e^{-jkr}
                            $$
                            
                            其中：
                            - $I_0$: 电流幅度
                            - $l$: 偶极子长度
                            - $λ$: 波长
                            - $r$: 观察点到天线的距离
                            - $θ$: 观察方向与天线轴的夹角
                            """
                        },
                        {
                            'title': '天线类型',
                            'content': """
                            ## 常见天线类型
                            
                            ### 1. 线天线
                            - 偶极子天线
                            - 单极天线
                            - 螺旋天线
                            - 八木天线
                            
                            ### 2. 口径天线
                            - 喇叭天线
                            - 抛物面天线
                            - 微带天线
                            - 缝隙天线
                            
                            ### 3. 阵列天线
                            - 直线阵列
                            - 平面阵列
                            - 相控阵天线
                            """
                        }
                    ]
                },
                {
                    'id': 'fundamentals_2',
                    'title': '关键参数详解',
                    'sections': [
                        {
                            'title': '增益和方向性',
                            'content': """
                            ## 增益 (Gain)
                            增益表示天线在特定方向上的辐射能力，单位是dBi（相对于各向同性辐射器）。
                            
                            $$
                            G = 4π \\frac{P(θ, φ)}{P_{in}}
                            $$
                            
                            其中 $P(θ, φ)$ 是单位立体角内的辐射功率，$P_{in}$ 是输入功率。
                            
                            ## 方向性 (Directivity)
                            方向性表示天线在最大辐射方向上的辐射强度与平均辐射强度的比值：
                            
                            $$
                            D = 4π \\frac{U_{max}}{P_{rad}}
                            $$
                            
                            其中 $U_{max}$ 是最大辐射强度，$P_{rad}$ 是总辐射功率。
                            
                            ## 增益与方向性的关系
                            $$
                            G = ηD
                            $$
                            
                            其中 $η$ 是天线效率。
                            """
                        },
                        {
                            'title': '波束宽度',
                            'content': """
                            ## 波束宽度 (Beamwidth)
                            波束宽度描述天线主瓣的宽度，通常定义为辐射功率下降3dB（或10dB）时的角度宽度。
                            
                            ### 1. 半功率波束宽度 (HPBW)
                            功率下降3dB（场强下降√2倍）时的角度宽度。
                            
                            ### 2. 第一零点波束宽度 (FNBW)
                            主瓣两侧第一个零点的角度间隔。
                            
                            ## 影响因素
                            - 天线尺寸
                            - 工作频率
                            - 照射分布
                            - 阵列配置
                            
                            ## 典型值
                            - 偶极子天线: ~78°
                            - 微带贴片: ~60-90°
                            - 抛物面天线: ~1-10°
                            - 喇叭天线: ~10-30°
                            """
                        },
                        {
                            'title': '副瓣和前后比',
                            'content': """
                            ## 副瓣电平 (Sidelobe Level)
                            副瓣电平表示副瓣相对于主瓣的增益差值，通常希望副瓣电平越低越好。
                            
                            $$
                            SLL = 20\\log_{10}\\left(\\frac{E_{sidelobe}}{E_{mainlobe}}\\right) \\text{ dB}
                            $$
                            
                            ## 前后比 (Front-to-Back Ratio)
                            前后比表示主瓣增益与后瓣（180°方向）增益的比值：
                            
                            $$
                            FBR = 20\\log_{10}\\left(\\frac{E_{front}}{E_{back}}\\right) \\text{ dB}
                            $$
                            
                            ## 设计目标
                            - 低副瓣: <-20dB
                            - 高前后比: >20dB
                            """
                        },
                        {
                            'title': '极化和轴比',
                            'content': """
                            ## 极化 (Polarization)
                            极化描述电磁波电场矢量的方向随时间变化的规律。
                            
                            ### 1. 线极化
                            - 垂直极化
                            - 水平极化
                            - ±45°斜极化
                            
                            ### 2. 圆极化
                            - 右旋圆极化 (RHCP)
                            - 左旋圆极化 (LHCP)
                            
                            ## 轴比 (Axial Ratio)
                            轴比描述极化椭圆的长轴与短轴之比：
                            
                            $$
                            AR = \\frac{E_{major}}{E_{minor}}
                            $$
                            
                            或表示为分贝：
                            
                            $$
                            AR_{dB} = 20\\log_{10}(AR)
                            $$
                            
                            ## 轴比分类
                            - 完美圆极化: AR = 1 (0dB)
                            - 良好圆极化: AR < 3dB
                            - 中等圆极化: 3dB < AR < 6dB
                            - 接近线极化: AR > 6dB
                            """
                        },
                        {
                            'title': '效率和带宽',
                            'content': """
                            ## 效率 (Efficiency)
                            天线效率描述天线将输入功率转换为辐射功率的能力。
                            
                            ### 1. 辐射效率
                            $$
                            η_r = \\frac{P_{rad}}{P_{in}}
                            $$
                            
                            ### 2. 孔径效率
                            $$
                            η_a = \\frac{A_{eff}}{A_{phys}}
                            $$
                            
                            其中 $A_{eff}$ 是有效孔径，$A_{phys}$ 是物理孔径。
                            
                            ### 3. 总效率
                            $$
                            η_{total} = η_r \\times η_a
                            $$
                            
                            ## 带宽 (Bandwidth)
                            带宽表示天线性能满足要求的频率范围。
                            
                            ### 1. 相对带宽
                            $$
                            BW = \\frac{f_h - f_l}{f_c} \\times 100\\%
                            $$
                            
                            其中 $f_h$ 和 $f_l$ 是上下限频率，$f_c$ 是中心频率。
                            
                            ### 2. 带宽分类
                            - 窄带: < 5%
                            - 宽带: 5-20%
                            - 超宽带: > 20%
                            """
                        }
                    ]
                }
            ],
            'antenna_types': [
                {
                    'id': 'dipole',
                    'name': '偶极子天线',
                    'description': '最简单的天线类型，由两根对称的导体组成',
                    'parameters': {
                        '频率范围': 'HF-VHF',
                        '增益': '2.15 dBi',
                        '波束宽度': '78°',
                        '阻抗': '73 Ω',
                        '极化': '线极化',
                        '带宽': '10-20%'
                    },
                    'applications': [
                        '广播电台',
                        '电视接收',
                        '业余无线电',
                        'RFID系统'
                    ],
                    'formulas': [
                        '半波长: L = λ/2 = c/(2f)',
                        '输入阻抗: Z_in ≈ 73Ω (理想)',
                        '方向性: D = 1.64 (2.15 dBi)'
                    ]
                },
                {
                    'id': 'patch',
                    'name': '微带贴片天线',
                    'description': '低剖面天线，易于与微波电路集成',
                    'parameters': {
                        '频率范围': 'UHF-SHF',
                        '增益': '5-8 dBi',
                        '波束宽度': '60-90°',
                        '阻抗': '50 Ω',
                        '极化': '线/圆极化',
                        '带宽': '1-5%'
                    },
                    'applications': [
                        '移动通信',
                        'GPS',
                        'WiFi路由器',
                        '卫星通信'
                    ],
                    'formulas': [
                        '贴片宽度: W = c/(2f_r√((ε_r+1)/2))',
                        '有效介电常数: ε_eff = (ε_r+1)/2 + (ε_r-1)/2(1+12h/W)^{-1/2}',
                        '贴片长度: L = c/(2f_r√ε_eff) - 2ΔL'
                    ]
                },
                {
                    'id': 'horn',
                    'name': '喇叭天线',
                    'description': '波导到自由空间的过渡结构，高增益天线',
                    'parameters': {
                        '频率范围': 'SHF-EHF',
                        '增益': '10-25 dBi',
                        '波束宽度': '10-30°',
                        '阻抗': '波导阻抗',
                        '极化': '线极化',
                        '带宽': '10-20%'
                    },
                    'applications': [
                        '微波中继',
                        '雷达系统',
                        '卫星地面站',
                        '天线测量'
                    ],
                    'formulas': [
                        '增益: G = 4πA_eff/λ²',
                        '3dB波束宽度: HPBW ≈ 70λ/D (度)',
                        '喇叭长度: L = (D²)/(8λ) (最优增益)'
                    ]
                },
                {
                    'id': 'parabolic',
                    'name': '抛物面天线',
                    'description': '高增益定向天线，利用抛物面反射器聚焦电磁波',
                    'parameters': {
                        '频率范围': 'UHF-EHF',
                        '增益': '30-60 dBi',
                        '波束宽度': '1-10°',
                        '阻抗': '50 Ω',
                        '极化': '线/圆极化',
                        '带宽': '5-10%'
                    },
                    'applications': [
                        '卫星通信',
                        '射电天文',
                        '雷达系统',
                        '深空通信'
                    ],
                    'formulas': [
                        '增益: G = (πD/λ)²η',
                        '3dB波束宽度: HPBW ≈ 70λ/D (度)',
                        '焦距: f = D/4 (标准抛物面)'
                    ]
                },
                {
                    'id': 'array',
                    'name': '阵列天线',
                    'description': '多个天线单元按一定规律排列组成',
                    'parameters': {
                        '频率范围': '依单元而定',
                        '增益': '随单元数增加',
                        '波束宽度': '可电子控制',
                        '阻抗': '依设计而定',
                        '极化': '可多样',
                        '带宽': '依单元而定'
                    },
                    'applications': [
                        '相控阵雷达',
                        '5G基站',
                        'MIMO系统',
                        '波束成形系统'
                    ],
                    'formulas': [
                        '阵列因子: AF = Σ w_n e^{j(nkd sinθ + φ_n)}',
                        '波束指向: θ_0 = arcsin(λΔφ/(2πd))',
                        '波束宽度: HPBW ≈ 0.886λ/(Nd cosθ_0) (均匀阵列)'
                    ]
                }
            ],
            'design_guidelines': [
                {
                    'id': 'design_1',
                    'title': '天线设计流程',
                    'steps': [
                        {
                            'step': 1,
                            'title': '需求分析',
                            'content': '明确应用场景、频率、增益、波束宽度、极化等要求'
                        },
                        {
                            'step': 2,
                            'title': '选型',
                            'content': '根据需求选择合适的天线类型'
                        },
                        {
                            'step': 3,
                            'title': '参数计算',
                            'content': '计算天线的基本尺寸和参数'
                        },
                        {
                            'step': 4,
                            'title': '仿真验证',
                            'content': '使用仿真软件验证设计性能'
                        },
                        {
                            'step': 5,
                            'title': '优化调整',
                            'content': '根据仿真结果优化天线参数'
                        },
                        {
                            'step': 6,
                            'title': '制作测试',
                            'content': '制作实物并进行实际测试'
                        },
                        {
                            'step': 7,
                            'title': '改进完善',
                            'content': '根据测试结果进一步改进设计'
                        }
                    ]
                },
                {
                    'id': 'design_2',
                    'title': '设计要点',
                    'points': [
                        {
                            'title': '频率选择',
                            'content': '根据应用选择合适频段，考虑频谱分配、传播特性、器件成本等'
                        },
                        {
                            'title': '增益平衡',
                            'content': '在增益、波束宽度、尺寸之间取得平衡，高增益通常意味着大尺寸'
                        },
                        {
                            'title': '阻抗匹配',
                            'content': '确保天线输入阻抗与馈线特性阻抗匹配，降低反射损耗'
                        },
                        {
                            'title': '极化匹配',
                            'content': '发射和接收天线的极化方式应匹配，避免极化损失'
                        },
                        {
                            'title': '带宽设计',
                            'content': '考虑工作带宽要求，宽带设计通常更复杂'
                        },
                        {
                            'title': '结构考虑',
                            'content': '考虑机械强度、重量、安装方式、环境适应性等'
                        },
                        {
                            'title': '成本控制',
                            'content': '在满足性能要求的前提下控制成本'
                        }
                    ]
                },
                {
                    'id': 'design_3',
                    'title': '常见问题与解决',
                    'problems': [
                        {
                            'problem': '增益不足',
                            'cause': '天线尺寸过小、效率低、匹配差',
                            'solution': '增加天线尺寸、改进匹配、提高效率'
                        },
                        {
                            'problem': '带宽过窄',
                            'cause': '天线Q值过高、匹配网络带宽窄',
                            'solution': '采用宽带匹配、降低Q值、使用宽带天线结构'
                        },
                        {
                            'problem': '副瓣过高',
                            'cause': '照射不均匀、边缘绕射',
                            'solution': '优化照射分布、添加边缘处理、采用低副瓣设计'
                        },
                        {
                            'problem': '交叉极化差',
                            'cause': '结构不对称、馈电不对称',
                            'solution': '改进结构对称性、优化馈电方式'
                        },
                        {
                            'problem': '效率低',
                            'cause': '导体损耗、介质损耗、匹配损耗',
                            'solution': '选用低损耗材料、改进匹配、优化结构'
                        }
                    ]
                }
            ],
            'analysis_methods': [
                {
                    'id': 'analysis_1',
                    'title': '方向图分析',
                    'methods': [
                        {
                            'name': '解析法',
                            'description': '基于天线结构推导理论方向图',
                            'advantages': '计算快速、物理意义明确',
                            'limitations': '只能处理简单结构',
                            'applications': '偶极子、阵列等规则天线'
                        },
                        {
                            'name': '矩量法 (MoM)',
                            'description': '基于积分方程的数值方法',
                            'advantages': '适用于线天线、精度高',
                            'limitations': '计算量大、内存需求高',
                            'applications': '线天线、微带天线'
                        },
                        {
                            'name': '有限元法 (FEM)',
                            'description': '基于偏微分方程的数值方法',
                            'advantages': '适用于复杂结构、任意材料',
                            'limitations': '计算复杂、需网格划分',
                            'applications': '复杂结构天线'
                        },
                        {
                            'name': '时域有限差分法 (FDTD)',
                            'description': '直接求解麦克斯韦方程',
                            'advantages': '宽带分析、直观',
                            'limitations': '时间步长限制、数值色散',
                            'applications': '宽带天线、瞬态分析'
                        },
                        {
                            'name': '物理光学法 (PO)',
                            'description': '基于几何光学的近似方法',
                            'advantages': '计算快速、适用于大电尺寸',
                            'limitations': '忽略绕射、精度有限',
                            'applications': '反射面天线'
                        }
                    ]
                },
                {
                    'id': 'analysis_2',
                    'title': '参数提取方法',
                    'parameters': [
                        {
                            'name': '增益测量',
                            'methods': ['比较法', '绝对法', '三天线法'],
                            'equipment': '标准增益天线、信号源、接收机'
                        },
                        {
                            'name': '方向图测量',
                            'methods': ['远场法', '紧缩场法', '近场扫描'],
                            'equipment': '转台、探头、接收系统'
                        },
                        {
                            'name': '极化测量',
                            'methods': ['旋转源法', '线极化法', '圆极化法'],
                            'equipment': '极化可调源、探头'
                        },
                        {
                            'name': '阻抗测量',
                            'methods': ['网络分析仪法', '时域反射法'],
                            'equipment': '矢量网络分析仪'
                        },
                        {
                            'name': '效率测量',
                            'methods': ['辐射计法', '量热法', '惠勒帽法'],
                            'equipment': '辐射计、功率计、屏蔽罩'
                        }
                    ]
                },
                {
                    'id': 'analysis_3',
                    'title': '仿真软件介绍',
                    'software': [
                        {
                            'name': 'HFSS',
                            'company': 'Ansys',
                            'methods': ['FEM'],
                            'features': '高精度、参数化、优化',
                            'applications': '复杂天线、微波器件'
                        },
                        {
                            'name': 'CST',
                            'company': 'Dassault',
                            'methods': ['FIT', 'FEM', 'MoM'],
                            'features': '多方法、时频域、系统级',
                            'applications': '宽带天线、阵列'
                        },
                        {
                            'name': 'FEKO',
                            'company': 'Altair',
                            'methods': ['MoM', 'PO', 'UTD'],
                            'features': '混合方法、大电尺寸',
                            'applications': '电大尺寸、车载天线'
                        },
                        {
                            'name': 'ADS',
                            'company': 'Keysight',
                            'methods': ['电路仿真'],
                            'features': '系统仿真、电路设计',
                            'applications': '匹配网络、系统级'
                        },
                        {
                            'name': 'radarsimpy',
                            'company': '开源',
                            'methods': ['数值仿真'],
                            'features': 'Python库、灵活',
                            'applications': '雷达系统、天线阵列'
                        }
                    ]
                }
            ],
            'case_studies': [
                {
                    'id': 'case_1',
                    'title': '2.4GHz WiFi天线设计',
                    'description': '设计用于无线路由器的微带贴片天线',
                    'requirements': {
                        '频率': '2.4-2.5 GHz',
                        '增益': '>7 dBi',
                        '波束宽度': '60-90°',
                        'VSWR': '<2',
                        '极化': '线极化',
                        '尺寸': '小型化'
                    },
                    'design_steps': [
                        '选择FR4基板 (ε_r=4.4, h=1.6mm)',
                        '计算贴片尺寸: W=30mm, L=28mm',
                        '设计同轴馈电位置',
                        '优化匹配网络',
                        '仿真验证'
                    ],
                    'results': {
                        '增益': '7.2 dBi',
                        '波束宽度': '75°',
                        'VSWR': '1.8',
                        '带宽': '150 MHz',
                        '效率': '85%'
                    }
                },
                {
                    'id': 'case_2',
                    'title': 'X波段喇叭天线',
                    'description': '设计用于天线测试的标准增益喇叭',
                    'requirements': {
                        '频率': '8-12 GHz',
                        '增益': '20 dBi',
                        '波束宽度': '15°',
                        'VSWR': '<1.5',
                        '极化': '线极化',
                        '前后比': '>30 dB'
                    },
                    'design_steps': [
                        '选择波导尺寸: WR90',
                        '设计喇叭张角',
                        '计算喇叭长度',
                        '优化渐变段',
                        '仿真验证'
                    ],
                    'results': {
                        '增益': '20.5 dBi',
                        '波束宽度': '14°',
                        'VSWR': '1.3',
                        '带宽': '4 GHz',
                        '前后比': '35 dB'
                    }
                },
                {
                    'id': 'case_3',
                    'title': '5G基站阵列天线',
                    'description': '设计用于5G基站的8×8微带阵列天线',
                    'requirements': {
                        '频率': '3.5 GHz',
                        '增益': '>20 dBi',
                        '波束宽度': '±15°扫描',
                        '副瓣电平': '<-20 dB',
                        '极化': '双极化',
                        '带宽': '200 MHz'
                    },
                    'design_steps': [
                        '设计单元天线',
                        '确定阵列间距: 0.5λ',
                        '设计馈电网络',
                        '优化幅度锥削',
                        '仿真扫描特性'
                    ],
                    'results': {
                        '增益': '22 dBi',
                        '扫描范围': '±15°',
                        '副瓣电平': '-22 dB',
                        'VSWR': '<1.8',
                        '隔离度': '>25 dB'
                    }
                }
            ],
            'resources': [
                {
                    'id': 'books',
                    'title': '推荐书籍',
                    'items': [
                        {
                            'title': '天线理论',
                            'author': 'C.A. Balanis',
                            'edition': '第4版',
                            'description': '天线领域的经典教材，内容全面深入'
                        },
                        {
                            'title': '微带天线',
                            'author': 'I.J. Bahl, P. Bhartia',
                            'edition': '第2版',
                            'description': '微带天线设计的权威参考书'
                        },
                        {
                            'title': '阵列天线',
                            'author': 'R.C. Hansen',
                            'edition': '第2版',
                            'description': '阵列天线设计的经典著作'
                        },
                        {
                            'title': '天线测量',
                            'author': 'A. Repjar, A. Densmore',
                            'edition': '第3版',
                            'description': '天线测量技术全面指南'
                        },
                        {
                            'title': '雷达系统导论',
                            'author': 'M.I. Skolnik',
                            'edition': '第3版',
                            'description': '雷达系统设计的权威参考'
                        }
                    ]
                },
                {
                    'id': 'websites',
                    'title': '学习网站',
                    'items': [
                        {
                            'title': 'IEEE天线与传播学会',
                            'url': 'https://www.ieeeaps.org',
                            'description': '天线领域的权威学术组织'
                        },
                        {
                            'title': 'Antenna-Theory.com',
                            'url': 'https://www.antenna-theory.com',
                            'description': '免费的天线理论教程'
                        },
                        {
                            'title': 'CST知识库',
                            'url': 'https://www.cst.com/knowledge',
                            'description': 'CST仿真软件教程和案例'
                        },
                        {
                            'title': 'ANSYS学习中心',
                            'url': 'https://www.ansys.com/training-center',
                            'description': 'HFSS等仿真软件学习资源'
                        },
                        {
                            'title': 'GitHub天线项目',
                            'url': 'https://github.com/topics/antenna',
                            'description': '开源天线项目和代码'
                        }
                    ]
                },
                {
                    'id': 'software',
                    'title': '仿真软件',
                    'items': [
                        {
                            'title': 'HFSS',
                            'company': 'Ansys',
                            'type': '商业',
                            'description': '三维全波电磁场仿真'
                        },
                        {
                            'title': 'CST Studio Suite',
                            'company': 'Dassault',
                            'type': '商业',
                            'description': '多物理场仿真平台'
                        },
                        {
                            'title': 'FEKO',
                            'company': 'Altair',
                            'type': '商业',
                            'description': '计算电磁学软件'
                        },
                        {
                            'title': 'OpenEMS',
                            'company': '开源',
                            'type': '免费',
                            'description': '时域有限差分法仿真'
                        },
                        {
                            'title': 'NEC2',
                            'company': '开源',
                            'type': '免费',
                            'description': '数值电磁代码'
                        }
                    ]
                },
                {
                    'id': 'datasets',
                    'title': '数据集',
                    'items': [
                        {
                            'title': '天线测量数据库',
                            'source': '多家实验室',
                            'size': '1000+天线',
                            'description': '各种天线的实测数据'
                        },
                        {
                            'title': '材料数据库',
                            'source': '多家供应商',
                            'size': '500+材料',
                            'description': '天线材料参数数据库'
                        },
                        {
                            'title': '标准天线库',
                            'source': 'NIST',
                            'size': '50+标准',
                            'description': '标准天线模型和参数'
                        },
                        {
                            'title': '卫星天线数据',
                            'source': 'NASA',
                            'size': '100+天线',
                            'description': '卫星天线设计和测试数据'
                        },
                        {
                            'title': '5G天线数据库',
                            'source': '3GPP',
                            'size': '200+天线',
                            'description': '5G天线技术规范和数据'
                        }
                    ]
                }
            ]
        }
    
    def render(self, sidebar_config: Dict[str, Any] = None):
        """渲染教学视图"""
        st.title("📚 天线理论与教学中心")
        
        # 创建主标签页
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏫 基础知识", 
            "📡 天线类型", 
            "🔧 设计指南",
            "📊 分析方法",
            "🎯 案例研究",
            "📖 学习资源"
        ])
        
        with tab1:
            self._render_fundamentals()
        
        with tab2:
            self._render_antenna_types()
        
        with tab3:
            self._render_design_guidelines()
        
        with tab4:
            self._render_analysis_methods()
        
        with tab5:
            self._render_case_studies()
        
        with tab6:
            self._render_learning_resources()
    
    def _render_fundamentals(self):
        """渲染基础知识部分"""
        st.markdown("## 🏫 天线理论基础")
        
        # 基础知识目录
        fundamentals = self.content.get('fundamentals', [])
        
        for chapter in fundamentals:
            with st.expander(f"### {chapter.get('title', '未命名章节')}", expanded=True):
                sections = chapter.get('sections', [])
                for section in sections:
                    st.markdown(f"#### {section.get('title', '')}")
                    st.markdown(section.get('content', ''))
                    st.markdown("---")
        
        # 交互式基础知识
        st.markdown("## 🎮 交互式学习")
        
        col1, col2 = st.columns(2)
        
        with col1:
            concept = st.selectbox(
                "选择概念",
                ["增益与方向性", "波束宽度", "极化", "轴比", "带宽", "效率"],
                index=0
            )
        
        with col2:
            visualization_type = st.selectbox(
                "可视化类型",
                ["示意图", "公式推导", "参数关系", "典型数值"],
                index=0
            )
        
        # 概念可视化
        if concept == "增益与方向性":
            self._visualize_gain_directivity(visualization_type)
        elif concept == "波束宽度":
            self._visualize_beamwidth(visualization_type)
        elif concept == "极化":
            self._visualize_polarization(visualization_type)
        elif concept == "轴比":
            self._visualize_axial_ratio(visualization_type)
        elif concept == "带宽":
            self._visualize_bandwidth(visualization_type)
        elif concept == "效率":
            self._visualize_efficiency(visualization_type)
    
    def _visualize_gain_directivity(self, viz_type: str):
        """可视化增益与方向性"""
        if viz_type == "示意图":
            # 创建方向性示意图
            fig = go.Figure()
            
            # 各向同性辐射
            theta = np.linspace(0, 2*np.pi, 100)
            r = np.ones_like(theta)
            x_iso = r * np.cos(theta)
            y_iso = r * np.sin(theta)
            
            fig.add_trace(go.Scatter(
                x=x_iso, y=y_iso,
                mode='lines',
                name='各向同性辐射',
                line=dict(color='blue', width=2, dash='dot'),
                fill='toself',
                fillcolor='rgba(0, 0, 255, 0.1)'
            ))
            
            # 定向天线
            theta_d = np.linspace(-np.pi/4, np.pi/4, 50)
            r_d = 2 + np.cos(theta_d * 4)  # 定向波束
            x_dir = r_d * np.cos(theta_d)
            y_dir = r_d * np.sin(theta_d)
            
            # 对称部分
            x_dir_full = np.concatenate([x_dir, x_dir[::-1]])
            y_dir_full = np.concatenate([y_dir, -y_dir[::-1]])
            
            fig.add_trace(go.Scatter(
                x=x_dir_full, y=y_dir_full,
                mode='lines',
                name='定向天线',
                line=dict(color='red', width=3),
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.2)'
            ))
            
            fig.update_layout(
                title="增益与方向性示意图",
                xaxis_title="",
                yaxis_title="",
                showlegend=True,
                height=400,
                yaxis=dict(scaleanchor="x", scaleratio=1),
                annotations=[
                    dict(
                        x=0, y=0,
                        text="天线位置",
                        showarrow=True,
                        arrowhead=2,
                        ax=0, ay=30
                    ),
                    dict(
                        x=1.5, y=0,
                        text="各向同性辐射",
                        showarrow=False,
                        font=dict(color="blue", size=12)
                    ),
                    dict(
                        x=2.5, y=1.2,
                        text="定向波束",
                        showarrow=False,
                        font=dict(color="red", size=12)
                    )
                ]
            )
            
            st.plotly_chart(fig, width='stretch')
            
        elif viz_type == "公式推导":
            st.markdown("""
            ## 增益公式推导
            
            ### 1. 方向性定义
            方向性 $D$ 定义为最大辐射强度与平均辐射强度的比值：
            
            $$
            D = \\frac{U_{max}}{U_{avg}} = \\frac{U_{max}}{P_{rad}/(4π)}
            $$
            
            其中：
            - $U_{max}$: 最大辐射强度 (W/sr)
            - $P_{rad}$: 总辐射功率 (W)
            - $U_{avg}$: 平均辐射强度 (W/sr)
            
            ### 2. 增益定义
            增益 $G$ 定义为最大辐射强度与各向同性辐射强度之比：
            
            $$
            G = \\frac{U_{max}}{P_{in}/(4π)} = η \\cdot D
            $$
            
            其中：
            - $P_{in}$: 输入功率 (W)
            - $η = P_{rad}/P_{in}$: 天线效率
            
            ### 3. 对数表示
            增益通常用分贝表示：
            
            $$
            G_{dBi} = 10\\log_{10}(G)
            $$
            
            dBi 表示相对于各向同性辐射器的增益。
            """)
        
        elif viz_type == "参数关系":
            # 创建交互式参数关系图
            col1, col2 = st.columns(2)
            
            with col1:
                efficiency = st.slider("天线效率", 0.1, 1.0, 0.8, 0.1)
                freq = st.slider("频率 (GHz)", 0.1, 30.0, 2.4, 0.1)
            
            with col2:
                directivity = st.slider("方向性 (倍数)", 1.0, 100.0, 10.0, 1.0)
            
            # 计算增益
            gain_linear = efficiency * directivity
            gain_db = 10 * np.log10(gain_linear)
            
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 效率 | {efficiency:.2f} |
            | 方向性 | {directivity:.1f} (倍数) |
            | 增益 | {gain_linear:.1f} (倍数) |
            | 增益 | {gain_db:.1f} dBi |
            
            ## 关系公式
            
            $$
            G = η \\times D = {efficiency:.2f} \\times {directivity:.1f} = {gain_linear:.1f}
            $$
            
            $$
            G_{dBi} = 10\\log_{10}(G) = 10\\log_{10}({gain_linear:.1f}) = {gain_db:.1f} \\text{ dBi}
            $$
            """)
        
        else:  # 典型数值
            data = {
                '天线类型': ['各向同性', '偶极子', '微带贴片', '喇叭天线', '抛物面天线'],
                '方向性 (倍数)': [1.0, 1.64, 5.0, 100.0, 1000.0],
                '典型效率': [1.0, 0.95, 0.85, 0.9, 0.7],
                '典型增益 (dBi)': [0.0, 2.15, 7.0, 20.0, 30.0]
            }
            
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch')
            
            # 创建条形图
            fig = go.Figure(data=[
                go.Bar(
                    x=df['天线类型'],
                    y=df['典型增益 (dBi)'],
                    marker_color=['blue', 'green', 'orange', 'red', 'purple'],
                    text=df['典型增益 (dBi)'],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="不同天线类型的典型增益",
                xaxis_title="天线类型",
                yaxis_title="增益 (dBi)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
    
    def _visualize_beamwidth(self, viz_type: str):
        """可视化波束宽度"""
        if viz_type == "示意图":
            # 创建波束宽度示意图
            fig = go.Figure()
            
            # 主瓣
            theta = np.linspace(-np.pi, np.pi, 200)
            pattern = np.exp(-(theta**2) * 10)  # 高斯波束
            pattern_db = 10 * np.log10(pattern + 1e-10)
            pattern_db = pattern_db - np.max(pattern_db)  # 归一化
            
            # 绘制方向图
            fig.add_trace(go.Scatter(
                x=np.degrees(theta),
                y=pattern_db,
                mode='lines',
                name='方向图',
                line=dict(color='blue', width=3)
            ))
            
            # 标记峰值
            fig.add_trace(go.Scatter(
                x=[0],
                y=[0],
                mode='markers+text',
                name='峰值',
                marker=dict(color='red', size=10),
                text=['峰值'],
                textposition='top center',
                showlegend=False
            ))
            
            # 标记3dB点
            threshold = -3
            # 找到交叉点
            crossing_idx = np.where(np.diff(np.sign(pattern_db - threshold)))[0]
            
            if len(crossing_idx) >= 2:
                angle1 = np.degrees(theta[crossing_idx[0]])
                angle2 = np.degrees(theta[crossing_idx[-1]])
                beamwidth = angle2 - angle1
                
                # 添加标记线
                fig.add_shape(
                    type="line",
                    x0=angle1, y0=threshold, x1=angle2, y1=threshold,
                    line=dict(color="green", width=2, dash="dash"),
                )
                
                fig.add_annotation(
                    x=(angle1 + angle2)/2,
                    y=threshold + 1,
                    text=f"HPBW: {beamwidth:.1f}°",
                    showarrow=False,
                    font=dict(color="green", size=12)
                )
            
            # 标记10dB点
            threshold = -10
            crossing_idx = np.where(np.diff(np.sign(pattern_db - threshold)))[0]
            
            if len(crossing_idx) >= 2:
                angle1 = np.degrees(theta[crossing_idx[0]])
                angle2 = np.degrees(theta[crossing_idx[-1]])
                
                fig.add_shape(
                    type="line",
                    x0=angle1, y0=threshold, x1=angle2, y1=threshold,
                    line=dict(color="orange", width=2, dash="dot"),
                )
            
            # 标记副瓣
            fig.add_annotation(
                x=60, y=-20,
                text="副瓣",
                showarrow=True,
                arrowhead=2,
                ax=0, ay=-30
            )
            
            fig.update_layout(
                title="波束宽度示意图",
                xaxis_title="角度 (°)",
                yaxis_title="增益 (dB)",
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
        elif viz_type == "公式推导":
            st.markdown("""
            ## 波束宽度公式
            
            ### 1. 半功率波束宽度 (HPBW)
            功率下降3dB（场强下降√2倍）时的角度宽度。
            
            对于均匀照射的矩形口径：
            
            $$
            HPBW ≈ 51\\frac{λ}{D} \\text{ (度)}
            $$
            
            其中：
            - $λ$: 波长
            - $D$: 口径尺寸
            
            ### 2. 第一零点波束宽度 (FNBW)
            主瓣两侧第一个零点的角度间隔。
            
            对于均匀照射口径：
            
            $$
            FNBW ≈ 114\\frac{λ}{D} \\text{ (度)}
            $$
            
            ### 3. 与增益的关系
            对于理想口径天线：
            
            $$
            G = \\frac{4π}{θ_{HPBW} φ_{HPBW}}
            $$
            
            其中 $θ_{HPBW}$ 和 $φ_{HPBW}$ 是两个主平面的半功率波束宽度（弧度）。
            """)
        
        elif viz_type == "参数关系":
            col1, col2 = st.columns(2)
            
            with col1:
                freq = st.slider("频率 (GHz)", 0.1, 30.0, 10.0, 0.1)
                aperture_type = st.selectbox("口径形状", ["矩形", "圆形"])
            
            with col2:
                if aperture_type == "矩形":
                    width = st.slider("口径宽度 (cm)", 1.0, 100.0, 10.0, 1.0)
                    height = st.slider("口径高度 (cm)", 1.0, 100.0, 10.0, 1.0)
                else:
                    diameter = st.slider("直径 (cm)", 1.0, 100.0, 10.0, 1.0)
            
            # 计算
            wavelength = 3e8 / (freq * 1e9)  # 波长(m)
            
            if aperture_type == "矩形":
                # 矩形口径
                hpbm_e = 51 * wavelength / (width/100)  # 度
                hpbm_h = 51 * wavelength / (height/100)  # 度
                
                gain = 4 * np.pi * (width/100) * (height/100) / wavelength**2
                gain_db = 10 * np.log10(gain)
                
                st.markdown(f"""
                ### 计算结果
                
                | 参数 | 值 |
                |------|-----|
                | 频率 | {freq:.1f} GHz |
                | 波长 | {wavelength*100:.2f} cm |
                | 口径尺寸 | {width} × {height} cm |
                | E面HPBW | {hpbm_e:.1f}° |
                | H面HPBW | {hpbm_h:.1f}° |
                | 理论增益 | {gain_db:.1f} dBi |
                """)
            else:
                # 圆形口径
                hpbm = 58 * wavelength / (diameter/100)  # 度
                
                gain = (np.pi * diameter/100 / wavelength)**2
                gain_db = 10 * np.log10(gain)
                
                st.markdown(f"""
                ### 计算结果
                
                | 参数 | 值 |
                |------|-----|
                | 频率 | {freq:.1f} GHz |
                | 波长 | {wavelength*100:.2f} cm |
                | 直径 | {diameter} cm |
                | HPBW | {hpbm:.1f}° |
                | 理论增益 | {gain_db:.1f} dBi |
                """)
        
        else:  # 典型数值
            data = {
                '天线类型': ['偶极子', '微带贴片', '喇叭天线', '抛物面天线', '相控阵'],
                '典型HPBW': ['78°', '60-90°', '10-30°', '1-10°', '可调'],
                '影响因素': ['长度', '尺寸/基板', '口径/长度', '焦距/直径', '单元数/间距'],
                '应用': ['全向通信', '移动设备', '微波中继', '卫星通信', '雷达系统']
            }
            
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch')
            
            # 可视化
            beamwidths = [78, 75, 20, 5, 5]  # 示例值
            types = df['天线类型']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=types,
                    y=beamwidths,
                    marker_color=['blue', 'green', 'orange', 'red', 'purple'],
                    text=beamwidths,
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="不同天线类型的典型波束宽度",
                xaxis_title="天线类型",
                yaxis_title="半功率波束宽度 (°)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
    
    def _visualize_polarization(self, viz_type: str):
        """可视化极化"""
        if viz_type == "示意图":
            # 创建极化示意图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("线极化", "圆极化", "椭圆极化", "倾斜极化"),
                specs=[[{'type': 'scatter'}, {'type': 'scatter'}],
                       [{'type': 'scatter'}, {'type': 'scatter'}]]
            )
            
            t = np.linspace(0, 2*np.pi, 100)
            
            # 1. 线极化（垂直）
            x1 = np.zeros_like(t)
            y1 = np.sin(t)
            fig.add_trace(go.Scatter(x=x1, y=y1, mode='lines', 
                                    line=dict(color='blue', width=3),
                                    name='垂直极化'), row=1, col=1)
            
            # 2. 圆极化
            x2 = np.cos(t)
            y2 = np.sin(t)
            fig.add_trace(go.Scatter(x=x2, y=y2, mode='lines',
                                    line=dict(color='green', width=3),
                                    fill='toself',
                                    fillcolor='rgba(0, 255, 0, 0.1)',
                                    name='圆极化'), row=1, col=2)
            
            # 3. 椭圆极化
            x3 = 0.7 * np.cos(t)
            y3 = 0.3 * np.sin(t)
            fig.add_trace(go.Scatter(x=x3, y=y3, mode='lines',
                                    line=dict(color='orange', width=3),
                                    fill='toself',
                                    fillcolor='rgba(255, 165, 0, 0.1)',
                                    name='椭圆极化'), row=2, col=1)
            
            # 4. 倾斜极化
            theta = np.deg2rad(45)
            x4 = np.cos(t) * np.cos(theta) - np.sin(t) * np.sin(theta)
            y4 = np.cos(t) * np.sin(theta) + np.sin(t) * np.cos(theta)
            fig.add_trace(go.Scatter(x=x4, y=y4, mode='lines',
                                    line=dict(color='red', width=3),
                                    name='45°极化'), row=2, col=2)
            
            # 更新布局
            for i in range(1, 3):
                for j in range(1, 3):
                    fig.update_xaxes(title_text="E_x", row=i, col=j, range=[-1.2, 1.2])
                    fig.update_yaxes(title_text="E_y", row=i, col=j, range=[-1.2, 1.2])
            
            fig.update_layout(
                title="不同极化类型示意图",
                height=500,
                showlegend=False
            )
            
            st.plotly_chart(fig, width='stretch')
            
        elif viz_type == "公式推导":
            st.markdown("""
            ## 极化公式
            
            ### 1. 极化椭圆参数
            电场矢量可表示为：
            
            $$
            \\vec{E}(t) = E_x\\cos(ωt)\\hat{x} + E_y\\cos(ωt + δ)\\hat{y}
            $$
            
            其中：
            - $E_x$, $E_y$: 两个正交分量的幅度
            - $δ$: 两个分量之间的相位差
            
            ### 2. 极化分类
            - **线极化**: $δ = 0$ 或 $δ = π$
            - **圆极化**: $E_x = E_y$ 且 $δ = ±π/2$
            - **椭圆极化**: 其他情况
            
            ### 3. 轴比
            轴比定义为极化椭圆的长轴与短轴之比：
            
            $$
            AR = \\frac{E_{major}}{E_{minor}} = \\frac{\\sqrt{E_x^2 + E_y^2 + \\sqrt{E_x^4 + E_y^4 + 2E_x^2E_y^2\\cos(2δ)}}}{\\sqrt{E_x^2 + E_y^2 - \\sqrt{E_x^4 + E_y^4 + 2E_x^2E_y^2\\cos(2δ)}}}
            $$
            
            ### 4. 倾斜角
            极化椭圆的倾斜角：
            
            $$
            τ = \\frac{1}{2}\\arctan\\left(\\frac{2E_xE_y\\cos δ}{E_x^2 - E_y^2}\\right)
            $$
            """)
        
        elif viz_type == "参数关系":
            col1, col2 = st.columns(2)
            
            with col1:
                E_x = st.slider("E_x 幅度", 0.0, 1.0, 1.0, 0.1)
                E_y = st.slider("E_y 幅度", 0.0, 1.0, 0.5, 0.1)
            
            with col2:
                delta = st.slider("相位差 δ (度)", -180.0, 180.0, 90.0, 5.0)
                delta_rad = np.deg2rad(delta)
            
            # 计算极化参数
            # 长轴和短轴
            A_sq = E_x**2 + E_y**2
            B_sq = np.sqrt(E_x**4 + E_y**4 + 2*E_x**2*E_y**2*np.cos(2*delta_rad))
            
            E_major = np.sqrt((A_sq + B_sq)/2)
            E_minor = np.sqrt((A_sq - B_sq)/2)
            
            if E_minor > 0:
                AR = E_major / E_minor
                AR_db = 20 * np.log10(AR)
            else:
                AR = float('inf')
                AR_db = float('inf')
            
            # 倾斜角
            if E_x != E_y:
                tau = 0.5 * np.arctan2(2*E_x*E_y*np.cos(delta_rad), E_x**2 - E_y**2)
                tau_deg = np.degrees(tau)
            else:
                tau_deg = 45.0  # 圆极化时
            
            # 判断极化类型
            if np.abs(delta) < 1e-3 or np.abs(delta - 180) < 1e-3:
                pol_type = "线极化"
            elif np.abs(E_x - E_y) < 1e-3 and np.abs(np.abs(delta) - 90) < 1e-3:
                pol_type = "圆极化"
                if delta > 0:
                    pol_type += " (右旋)"
                else:
                    pol_type += " (左旋)"
            else:
                pol_type = "椭圆极化"
            
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 极化类型 | {pol_type} |
            | 长轴幅度 | {E_major:.3f} |
            | 短轴幅度 | {E_minor:.3f} |
            | 轴比 (线性) | {AR:.3f} |
            | 轴比 (dB) | {AR_db:.2f} dB |
            | 倾斜角 | {tau_deg:.1f}° |
            
            ## 参数关系
            极化状态由 $E_x$、$E_y$ 和 $δ$ 共同决定：
            - 当 $E_y = 0$ 时为垂直极化
            - 当 $E_x = 0$ 时为水平极化
            - 当 $E_x = E_y$ 且 $δ = ±90°$ 时为圆极化
            """)
        
        else:  # 典型数值
            data = {
                '极化类型': ['垂直线极化', '水平线极化', '45°线极化', '右旋圆极化', '左旋圆极化', '椭圆极化'],
                'E_x': [1.0, 0.0, 0.707, 0.707, 0.707, 0.8],
                'E_y': [0.0, 1.0, 0.707, 0.707, 0.707, 0.4],
                'δ (°)': [0, 0, 0, 90, -90, 45],
                '轴比 (dB)': [np.inf, np.inf, np.inf, 0, 0, 3.0],
                '应用': ['电视广播', 'WiFi', '卫星通信', 'GPS', '北斗', '雷达']
            }
            
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch')
    
    def _visualize_axial_ratio(self, viz_type: str):
        """可视化轴比"""
        if viz_type == "示意图":
            # 创建轴比示意图
            fig = go.Figure()
            
            # 不同轴比的椭圆
            t = np.linspace(0, 2*np.pi, 100)
            
            # 完美圆极化 (AR=1)
            x1 = np.cos(t)
            y1 = np.sin(t)
            fig.add_trace(go.Scatter(x=x1, y=y1, mode='lines',
                                    name='AR=1 (0dB) 完美圆极化',
                                    line=dict(color='green', width=3)))
            
            # 良好圆极化 (AR=1.5)
            x2 = 0.75 * np.cos(t)
            y2 = 0.5 * np.sin(t)
            fig.add_trace(go.Scatter(x=x2, y=y2, mode='lines',
                                    name='AR=1.5 (3.5dB) 良好圆极化',
                                    line=dict(color='blue', width=2, dash='dash')))
            
            # 中等圆极化 (AR=2)
            x3 = 0.8 * np.cos(t)
            y3 = 0.4 * np.sin(t)
            fig.add_trace(go.Scatter(x=x3, y=y3, mode='lines',
                                    name='AR=2 (6dB) 中等圆极化',
                                    line=dict(color='orange', width=2)))
            
            # 接近线极化 (AR=5)
            x4 = 0.9 * np.cos(t)
            y4 = 0.18 * np.sin(t)
            fig.add_trace(go.Scatter(x=x4, y=y4, mode='lines',
                                    name='AR=5 (14dB) 接近线极化',
                                    line=dict(color='red', width=2, dash='dot')))
            
            fig.update_layout(
                title="不同轴比的极化椭圆",
                xaxis_title="E_x",
                yaxis_title="E_y",
                showlegend=True,
                height=500,
                xaxis=dict(scaleanchor="y", scaleratio=1),
                annotations=[
                    dict(
                        x=0, y=0,
                        text="圆心",
                        showarrow=True,
                        arrowhead=2,
                        ax=0, ay=30
                    )
                ]
            )
            
            st.plotly_chart(fig, width='stretch')
        
        elif viz_type == "公式推导":
            st.markdown("""
            ## 轴比公式推导
            
            ### 1. 轴比定义
            轴比定义为极化椭圆的长轴与短轴之比：
            
            $$
            AR = \\frac{E_{major}}{E_{minor}} ≥ 1
            $$
            
            或用分贝表示：
            
            $$
            AR_{dB} = 20\\log_{10}(AR)
            $$
            
            ### 2. 计算长轴和短轴
            对于电场矢量 $\\vec{E}(t) = E_x\\cos(ωt)\\hat{x} + E_y\\cos(ωt + δ)\\hat{y}$：
            
            长轴和短轴由下式给出：
            
            $$
            E_{major}^2 = \\frac{1}{2}\\left[E_x^2 + E_y^2 + \\sqrt{(E_x^2 - E_y^2)^2 + 4E_x^2E_y^2\\cos^2δ}\\right]
            $$
            
            $$
            E_{minor}^2 = \\frac{1}{2}\\left[E_x^2 + E_y^2 - \\sqrt{(E_x^2 - E_y^2)^2 + 4E_x^2E_y^2\\cos^2δ}\\right]
            $$
            
            ### 3. 特殊情况
            - **线极化**: $δ = 0$ 或 $π$，则 $AR = ∞$
            - **圆极化**: $E_x = E_y$ 且 $δ = ±π/2$，则 $AR = 1$
            - **一般椭圆极化**: $1 < AR < ∞$
            
            ### 4. 轴比与圆极化纯度
            轴比是衡量圆极化纯度的重要指标：
            - AR < 3dB: 良好圆极化
            - 3dB < AR < 6dB: 中等圆极化
            - AR > 6dB: 接近线极化
            """)
        
        elif viz_type == "参数关系":
            col1, col2 = st.columns(2)
            
            with col1:
                AR_linear = st.slider("轴比 (线性)", 1.0, 10.0, 2.0, 0.1)
            
            with col2:
                # 计算对应的dB值
                AR_db = 20 * np.log10(AR_linear)
                
                # 判断质量
                if AR_linear < 1.41:  # 3dB
                    quality = "良好圆极化"
                    color = "green"
                elif AR_linear < 2.0:  # 6dB
                    quality = "中等圆极化"
                    color = "orange"
                else:
                    quality = "接近线极化"
                    color = "red"
            
            # 生成椭圆
            t = np.linspace(0, 2*np.pi, 100)
            
            # 假设长轴为1，则短轴为1/AR
            E_major = 1.0
            E_minor = 1.0 / AR_linear
            
            # 椭圆参数
            a = E_major
            b = E_minor
            
            # 椭圆方程
            x = a * np.cos(t)
            y = b * np.sin(t)
            
            fig = go.Figure(data=[
                go.Scatter(x=x, y=y, mode='lines',
                          line=dict(color=color, width=3),
                          fill='toself',
                          fillcolor=f'rgba({255 if color=="red" else 0}, {255 if color=="green" else 0}, 0, 0.1)')
            ])
            
            fig.update_layout(
                title=f"轴比: {AR_linear:.2f} ({AR_db:.1f} dB) - {quality}",
                xaxis_title="E_x",
                yaxis_title="E_y",
                xaxis=dict(scaleanchor="y", scaleratio=1, range=[-1.2, 1.2]),
                yaxis=dict(range=[-1.2, 1.2]),
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 轴比 (线性) | {AR_linear:.2f} |
            | 轴比 (dB) | {AR_db:.1f} dB |
            | 极化质量 | {quality} |
            | 长轴幅度 | {E_major:.2f} |
            | 短轴幅度 | {E_minor:.2f} |
            """)
        
        else:  # 典型数值
            data = {
                '应用领域': ['卫星通信', 'GPS导航', '雷达系统', '移动通信', 'RFID'],
                '典型轴比': ['< 3dB', '< 1.5dB', '< 6dB', '< 3dB', '< 6dB'],
                '要求': ['高圆极化纯度', '极高圆极化纯度', '中等圆极化纯度', '高圆极化纯度', '中等圆极化纯度'],
                '典型天线': ['螺旋天线', '微带天线', '抛物面天线', '贴片天线', '偶极子天线']
            }
            
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch')
            
            # 创建条形图显示不同应用的要求
            fig = go.Figure(data=[
                go.Bar(
                    x=df['应用领域'],
                    y=[3, 1.5, 6, 3, 6],  # 对应的轴比dB值
                    marker_color=['blue', 'green', 'orange', 'red', 'purple'],
                    text=['3dB', '1.5dB', '6dB', '3dB', '6dB'],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="不同应用领域的轴比要求",
                xaxis_title="应用领域",
                yaxis_title="最大轴比 (dB)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
    
    def _visualize_bandwidth(self, viz_type: str):
        """可视化带宽"""
        if viz_type == "示意图":
            # 创建带宽示意图
            fig = go.Figure()
            
            # 频响曲线
            f = np.linspace(0.5, 1.5, 200)
            f0 = 1.0  # 中心频率
            
            # 理想带通响应
            response = 1 / (1 + ((f - f0) / 0.1)**6)
            response_db = 10 * np.log10(response + 1e-10)
            
            fig.add_trace(go.Scatter(
                x=f, y=response_db,
                mode='lines',
                name='频响曲线',
                line=dict(color='blue', width=3)
            ))
            
            # 标记中心频率
            fig.add_trace(go.Scatter(
                x=[f0], y=[0],
                mode='markers+text',
                name='中心频率',
                marker=dict(color='green', size=10),
                text=['f₀'],
                textposition='top center',
                showlegend=False
            ))
            
            # 标记-3dB点
            threshold = -3
            # 找到交叉点
            above_threshold = response_db >= threshold
            if np.any(above_threshold):
                idx = np.where(above_threshold)[0]
                f_low = f[idx[0]]
                f_high = f[idx[-1]]
                bandwidth = f_high - f_low
                bw_percent = bandwidth / f0 * 100
                
                # 添加标记
                fig.add_shape(type="line",
                             x0=f_low, y0=threshold, x1=f_high, y1=threshold,
                             line=dict(color="red", width=2, dash="dash"))
                
                fig.add_annotation(x=f_low, y=threshold, text=f"f₁={f_low:.2f}",
                                  showarrow=True, arrowhead=2, ax=0, ay=-30)
                fig.add_annotation(x=f_high, y=threshold, text=f"f₂={f_high:.2f}",
                                  showarrow=True, arrowhead=2, ax=0, ay=-30)
                
                fig.add_annotation(x=(f_low+f_high)/2, y=threshold+1,
                                  text=f"BW={bandwidth:.2f} ({bw_percent:.1f}%)",
                                  showarrow=False, font=dict(color="red", size=12))
            
            fig.update_layout(
                title="天线带宽示意图",
                xaxis_title="频率 (归一化)",
                yaxis_title="增益 (dB)",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
        elif viz_type == "公式推导":
            st.markdown("""
            ## 带宽公式
            
            ### 1. 带宽定义
            带宽表示天线性能满足要求的频率范围。
            
            #### 绝对带宽
            $$
            BW = f_h - f_l
            $$
            
            #### 相对带宽
            $$
            BW_{\\%} = \\frac{f_h - f_l}{f_c} \\times 100\\%
            $$
            
            其中：
            - $f_l$: 下限频率
            - $f_h$: 上限频率
            - $f_c = (f_l + f_h)/2$: 中心频率
            
            ### 2. 不同定义的带宽
            
            #### 3dB带宽
            增益下降3dB（功率下降一半）时的带宽。
            
            #### 10dB带宽
            增益下降10dB时的带宽。
            
            #### VSWR带宽
            电压驻波比不超过某值（如2:1）时的带宽。
            
            #### 阻抗带宽
            输入阻抗匹配（如S11<-10dB）时的带宽。
            
            ### 3. 带宽与Q值的关系
            
            对于谐振天线：
            
            $$
            BW_{\\%} = \\frac{1}{Q} \\times 100\\%
            $$
            
            其中Q是天线的品质因数。
            """)
        
        elif viz_type == "参数关系":
            col1, col2 = st.columns(2)
            
            with col1:
                center_freq = st.slider("中心频率 (GHz)", 0.1, 10.0, 2.4, 0.1)
                antenna_type = st.selectbox("天线类型", 
                                           ["窄带天线", "宽带天线", "超宽带天线"])
            
            with col2:
                if antenna_type == "窄带天线":
                    bw_percent = st.slider("相对带宽 (%)", 0.1, 5.0, 2.0, 0.1)
                elif antenna_type == "宽带天线":
                    bw_percent = st.slider("相对带宽 (%)", 5.0, 20.0, 10.0, 0.5)
                else:  # 超宽带
                    bw_percent = st.slider("相对带宽 (%)", 20.0, 100.0, 50.0, 5.0)
            
            # 计算
            bw_abs = center_freq * bw_percent / 100
            f_low = center_freq - bw_abs/2
            f_high = center_freq + bw_abs/2
            
            # 评估
            if bw_percent < 5:
                bw_type = "窄带"
                evaluation = "适用于点频或窄带系统"
            elif bw_percent < 20:
                bw_type = "宽带"
                evaluation = "适用于多频段或宽带系统"
            else:
                bw_type = "超宽带"
                evaluation = "适用于UWB或脉冲系统"
            
            st.markdown(f"""
            ### 带宽参数
            
            | 参数 | 值 |
            |------|-----|
            | 中心频率 | {center_freq:.2f} GHz |
            | 相对带宽 | {bw_percent:.1f}% |
            | 绝对带宽 | {bw_abs:.3f} GHz |
            | 下限频率 | {f_low:.3f} GHz |
            | 上限频率 | {f_high:.3f} GHz |
            | 带宽类型 | {bw_type} |
            | 应用建议 | {evaluation} |
            """)
            
            # 绘制频响
            f = np.linspace(f_low * 0.8, f_high * 1.2, 200)
            response = 1 / (1 + ((f - center_freq) / (bw_abs/2))**6)
            response_db = 10 * np.log10(response + 1e-10)
            
            fig = go.Figure(data=[
                go.Scatter(x=f, y=response_db, mode='lines',
                          line=dict(color='blue', width=3),
                          name='频响')
            ])
            
            # 标记带宽
            fig.add_shape(type="rect",
                         x0=f_low, y0=-20, x1=f_high, y1=0,
                         line=dict(color="red", width=1),
                         fillcolor="rgba(255, 0, 0, 0.1)")
            
            fig.update_layout(
                title="天线频响曲线",
                xaxis_title="频率 (GHz)",
                yaxis_title="增益 (dB)",
                height=300
            )
            
            st.plotly_chart(fig, width='stretch')
        
        else:  # 典型数值
            data = {
                '天线类型': ['偶极子', '微带贴片', '螺旋天线', '喇叭天线', '对数周期天线'],
                '典型带宽 (%)': ['10-20%', '1-5%', '10-20%', '10-20%', '50-200%'],
                '带宽限制因素': ['谐振长度', '高Q谐振', '螺旋参数', '波导模式', '结构比例'],
                '扩展方法': ['加粗导体', '多层结构', '优化螺距', '双模喇叭', '优化比例']
            }
            
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch')
    
    def _visualize_efficiency(self, viz_type: str):
            """可视化效率"""
            if viz_type == "示意图":
                # 创建效率示意图
                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=("效率组成", "功率流向"),
                    specs=[[{'type': 'pie'}, {'type': 'sankey'}]]
                )
                
                # 饼图 - 效率组成
                labels = ['辐射效率', '匹配效率', '导体损耗', '介质损耗', '其他损耗']
                values = [0.7, 0.9, 0.85, 0.9, 0.95]
                
                fig.add_trace(go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    marker_colors=['#636efa', '#00cc96', '#ab63fa', '#ffa15a', '#19d3f3']
                ), row=1, col=1)
                
                # 桑基图 - 功率流向
                fig.add_trace(go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=["输入功率", "反射功率", "匹配网络", "导体损耗", 
                              "介质损耗", "辐射功率", "热损耗"],
                        color=["blue", "red", "green", "orange", "purple", "lightblue", "gray"]
                    ),
                    link=dict(
                        source=[0, 0, 2, 2, 2, 3, 4],  # 源节点索引
                        target=[1, 2, 3, 4, 5, 6, 6],  # 目标节点索引
                        value=[10, 90, 10, 5, 75, 10, 5],  # 流量值
                        color=["rgba(255,0,0,0.5)", "rgba(0,255,0,0.5)", 
                              "rgba(255,165,0,0.5)", "rgba(128,0,128,0.5)",
                              "rgba(173,216,230,0.5)", "rgba(128,128,128,0.5)", 
                              "rgba(128,128,128,0.5)"]
                    )
                ), row=1, col=2)
                
                fig.update_layout(
                    title_text="天线效率分析",
                    height=400
                )
                
                st.plotly_chart(fig, width='stretch')
                
            elif viz_type == "公式推导":
                st.markdown("""
                ## 效率公式
                
                ### 1. 总效率
                天线总效率定义为辐射功率与输入功率之比：
                
                $$
                η_{total} = \\frac{P_{rad}}{P_{in}}
                $$
                
                总效率可以分解为多个分量效率的乘积：
                
                $$
                η_{total} = η_r \\times η_c \\times η_d \\times η_m \\times \\cdots
                $$
                
                ### 2. 分量效率
                
                #### 辐射效率
                $$
                η_r = \\frac{P_{rad}}{P_{acc}}
                $$
                
                其中 $P_{acc}$ 是天线接受的净功率。
                
                #### 导体效率
                $$
                η_c = \\frac{P_{acc} - P_{c,loss}}{P_{acc}}
                $$
                
                $P_{c,loss}$ 是导体损耗功率。
                
                #### 介质效率
                $$
                η_d = \\frac{P_{acc} - P_{d,loss}}{P_{acc}}
                $$
                
                $P_{d,loss}$ 是介质损耗功率。
                
                #### 匹配效率
                $$
                η_m = 1 - |Γ|^2
                $$
                
                其中 $Γ$ 是反射系数。
                
                ### 3. 增益与效率的关系
                $$
                G = η_{total} \\times D
                $$
                
                其中 $D$ 是方向性。
                """)
            
            elif viz_type == "参数关系":
                col1, col2 = st.columns(2)
                
                with col1:
                    radiation_eff = st.slider("辐射效率", 0.1, 1.0, 0.8, 0.05)
                    conductor_eff = st.slider("导体效率", 0.1, 1.0, 0.9, 0.05)
                
                with col2:
                    dielectric_eff = st.slider("介质效率", 0.1, 1.0, 0.9, 0.05)
                    matching_eff = st.slider("匹配效率", 0.1, 1.0, 0.85, 0.05)
                
                # 计算总效率
                total_efficiency = radiation_eff * conductor_eff * dielectric_eff * matching_eff
                
                # 计算增益（假设方向性为10）
                directivity = 10  # 线性值
                gain_linear = total_efficiency * directivity
                gain_db = 10 * np.log10(gain_linear)
                
                st.markdown(f"""
                ### 效率计算
                
                | 效率分量 | 值 |
                |------|-----|
                | 辐射效率 | {radiation_eff:.2f} |
                | 导体效率 | {conductor_eff:.2f} |
                | 介质效率 | {dielectric_eff:.2f} |
                | 匹配效率 | {matching_eff:.2f} |
                | **总效率** | **{total_efficiency:.3f}** |
                
                ### 增益计算
                
                假设方向性 = {directivity:.1f} (线性) = {10*np.log10(directivity):.1f} dBi
                
                $$
                G = η_{total} \\times D = {total_efficiency:.3f} \\times {directivity:.1f} = {gain_linear:.3f}
                $$
                
                $$
                G_{dBi} = 10\\log_{10}(G) = 10\\log_{10}({gain_linear:.3f}) = {gain_db:.1f} \\text{ dBi}
                $$
                
                ### 效率评估
                """)
                
                if total_efficiency > 0.8:
                    st.success("✅ 优秀效率")
                elif total_efficiency > 0.6:
                    st.warning("🟡 良好效率")
                elif total_efficiency > 0.4:
                    st.info("🟠 中等效率")
                else:
                    st.error("🔴 低效率")
            
            else:  # 典型数值
                data = {
                    '天线类型': ['偶极子', '微带贴片', '喇叭天线', '抛物面天线', '相控阵'],
                    '典型总效率': ['85-95%', '60-85%', '80-95%', '50-75%', '60-80%'],
                    '主要损耗': ['导体损耗', '介质损耗', '波导损耗', '遮挡/溢出', '馈电网络'],
                    '提高方法': ['加粗导体', '低损耗基板', '优化渐变', '优化馈源', '低损耗移相器']
                }
                
                df = pd.DataFrame(data)
                st.dataframe(df, width='stretch')
                
                # 创建条形图
                efficiencies = [0.9, 0.75, 0.9, 0.65, 0.7]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=df['天线类型'],
                        y=efficiencies,
                        marker_color=['blue', 'green', 'orange', 'red', 'purple'],
                        text=[f"{e*100:.0f}%" for e in efficiencies],
                        textposition='auto'
                    )
                ])
                
                fig.update_layout(
                    title="不同天线类型的典型效率",
                    xaxis_title="天线类型",
                    yaxis_title="总效率",
                    yaxis_tickformat=".0%",
                    height=400
                )
                
                st.plotly_chart(fig, width='stretch')
    
    def _render_antenna_types(self):
        """渲染天线类型部分"""
        st.markdown("## 📡 天线类型大全")
        
        # 天线类型选择
        antenna_types = self.content.get('antenna_types', [])
        
        # 创建标签页显示不同类型
        tab_titles = [f"{i+1}. {ant['name']}" for i, ant in enumerate(antenna_types)]
        tabs = st.tabs(tab_titles)
        
        for i, (tab, antenna) in enumerate(zip(tabs, antenna_types)):
            with tab:
                self._render_antenna_type_detail(antenna, i)
        
        # 天线比较
        st.markdown("## ⚖️ 天线类型比较")
        
        selected_types = st.multiselect(
            "选择要比较的天线类型",
            [ant['name'] for ant in antenna_types],
            default=[antenna_types[0]['name'], antenna_types[1]['name']]
        )
        
        if len(selected_types) >= 2:
            self._compare_antenna_types(selected_types, antenna_types)
    
    def _render_antenna_type_detail(self, antenna: Dict[str, Any], index: int):
        """渲染天线类型详情"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {antenna['name']}")
            st.markdown(f"**描述:** {antenna['description']}")
            
            st.markdown("#### 📊 关键参数")
            params = antenna.get('parameters', {})
            
            for key, value in params.items():
                st.markdown(f"**{key}:** {value}")
            
            st.markdown("#### 📈 典型应用")
            applications = antenna.get('applications', [])
            
            for app in applications:
                st.markdown(f"- {app}")
        
        with col2:
            # 显示天线示意图
            self._display_antenna_schematic(antenna['id'], index)
            
            st.markdown("#### 📐 设计公式")
            formulas = antenna.get('formulas', [])
            
            for formula in formulas:
                st.markdown(f"- {formula}")
        
        # 方向图示例
        st.markdown("#### 📡 方向图示例")
        self._display_antenna_pattern_example(antenna['id'])
        
        # 设计要点
        st.markdown("#### 💡 设计要点")
        
        if antenna['id'] == 'dipole':
            tips = [
                "长度通常为半波长(λ/2)",
                "阻抗约为73Ω，需要匹配网络",
                "带宽受导体直径影响",
                "全向辐射，适用于广播"
            ]
        elif antenna['id'] == 'patch':
            tips = [
                "尺寸由工作频率和介电常数决定",
                "厚度影响带宽和效率",
                "馈电位置影响阻抗匹配",
                "易于实现圆极化"
            ]
        elif antenna['id'] == 'horn':
            tips = [
                "增益由口径尺寸决定",
                "长度影响相位中心和旁瓣",
                "有多种变体（角锥、圆锥、喇叭等）",
                "宽带性能好"
            ]
        elif antenna['id'] == 'parabolic':
            tips = [
                "增益与直径平方成正比",
                "焦距影响照射效率和旁瓣",
                "表面精度要求高（通常<λ/16）",
                "馈源遮挡影响效率"
            ]
        else:  # array
            tips = [
                "阵元间距通常为0.5λ",
                "阵列因子决定方向图",
                "幅度和相位控制波束形状",
                "互耦影响性能"
            ]
        
        for tip in tips:
            st.markdown(f"- {tip}")
    
    def _display_antenna_schematic(self, antenna_id: str, index: int):
        """显示天线示意图"""
        # 创建简单的示意图
        if antenna_id == 'dipole':
            # 偶极子天线示意图
            fig = go.Figure()
            
            # 偶极子臂
            fig.add_shape(type="line", x0=-0.5, y0=0, x1=0.5, y1=0,
                         line=dict(color="red", width=3))
            
            # 馈电点
            fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers',
                                    marker=dict(color="blue", size=10)))
            
            fig.update_layout(
                title="偶极子天线",
                xaxis_range=[-1, 1],
                yaxis_range=[-0.5, 0.5],
                height=200,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
        elif antenna_id == 'patch':
            # 微带贴片示意图
            fig = go.Figure()
            
            # 贴片
            fig.add_shape(type="rect", x0=-0.4, y0=-0.3, x1=0.4, y1=0.3,
                         line=dict(color="blue", width=2),
                         fillcolor="lightblue")
            
            # 馈电点
            fig.add_trace(go.Scatter(x=[0.2], y=[0], mode='markers',
                                    marker=dict(color="red", size=8)))
            
            # 地平面
            fig.add_shape(type="rect", x0=-0.5, y0=-0.4, x1=0.5, y1=-0.45,
                         line=dict(color="black", width=1),
                         fillcolor="gray")
            
            fig.update_layout(
                title="微带贴片天线",
                xaxis_range=[-0.6, 0.6],
                yaxis_range=[-0.5, 0.5],
                height=200,
                showlegend=False
            )
            
        elif antenna_id == 'horn':
            # 喇叭天线示意图
            fig = go.Figure()
            
            # 喇叭轮廓
            x = [-0.3, -0.1, 0.1, 0.3]
            y_top = [0.1, 0.05, 0.05, 0.2]
            y_bottom = [-0.1, -0.05, -0.05, -0.2]
            
            fig.add_trace(go.Scatter(x=x, y=y_top, mode='lines',
                                    line=dict(color="orange", width=3)))
            fig.add_trace(go.Scatter(x=x, y=y_bottom, mode='lines',
                                    line=dict(color="orange", width=3)))
            
            # 波导
            fig.add_shape(type="rect", x0=-0.4, y0=-0.08, x1=-0.3, y1=0.08,
                         line=dict(color="gray", width=2),
                         fillcolor="lightgray")
            
            fig.update_layout(
                title="喇叭天线",
                xaxis_range=[-0.5, 0.5],
                yaxis_range=[-0.3, 0.3],
                height=200,
                showlegend=False
            )
            
        elif antenna_id == 'parabolic':
            # 抛物面天线示意图
            fig = go.Figure()
            
            # 抛物面
            x = np.linspace(-0.4, 0.4, 50)
            y = 0.1 * x**2 - 0.2
            
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines',
                                    line=dict(color="green", width=3),
                                    fill='tozeroy',
                                    fillcolor="rgba(0,255,0,0.1)"))
            
            # 馈源
            fig.add_trace(go.Scatter(x=[0], y=[0.1], mode='markers',
                                    marker=dict(color="red", size=10)))
            
            # 支撑杆
            fig.add_shape(type="line", x0=0, y0=0.1, x1=0, y1=-0.1,
                         line=dict(color="black", width=2, dash="dash"))
            
            fig.update_layout(
                title="抛物面天线",
                xaxis_range=[-0.5, 0.5],
                yaxis_range=[-0.3, 0.3],
                height=200,
                showlegend=False
            )
            
        else:  # array
            # 阵列天线示意图
            fig = go.Figure()
            
            # 阵元
            for i in range(-2, 3):
                for j in range(-1, 2):
                    fig.add_trace(go.Scatter(x=[i*0.2], y=[j*0.2], mode='markers',
                                           marker=dict(color="purple", size=8)))
            
            # 馈电网络示意
            for i in range(-2, 3):
                fig.add_shape(type="line", x0=i*0.2, y0=-0.3, x1=i*0.2, y1=-0.4,
                             line=dict(color="gray", width=1))
            
            fig.update_layout(
                title="阵列天线",
                xaxis_range=[-0.6, 0.6],
                yaxis_range=[-0.5, 0.5],
                height=200,
                showlegend=False
            )
        
        st.plotly_chart(fig, width='stretch')
    
    def _display_antenna_pattern_example(self, antenna_id: str):
        """显示天线方向图示例"""
        # 生成示例方向图
        theta = np.linspace(0, 180, 181)
        
        if antenna_id == 'dipole':
            # 偶极子方向图
            pattern = np.abs(np.sin(np.deg2rad(theta)))
            title = "偶极子天线方向图 (全向)"
            
        elif antenna_id == 'patch':
            # 微带贴片方向图
            pattern = np.cos(np.deg2rad(theta - 90))**2
            pattern[theta < 60] = 0
            pattern[theta > 120] = 0
            title = "微带贴片天线方向图"
            
        elif antenna_id == 'horn':
            # 喇叭天线方向图
            pattern = np.exp(-((theta - 90)**2) / (2 * 15**2))
            title = "喇叭天线方向图"
            
        elif antenna_id == 'parabolic':
            # 抛物面天线方向图
            pattern = np.exp(-((theta - 90)**2) / (2 * 5**2))
            pattern = pattern + 0.1 * np.exp(-((theta - 70)**2) / (2 * 10**2))  # 副瓣
            pattern = pattern + 0.1 * np.exp(-((theta - 110)**2) / (2 * 10**2))  # 副瓣
            title = "抛物面天线方向图"
            
        else:  # array
            # 阵列天线方向图
            pattern = np.abs(np.sin(5 * np.deg2rad(theta - 90)))
            pattern = pattern / np.max(pattern)
            title = "阵列天线方向图"
        
        # 转换为dB
        pattern_db = 20 * np.log10(pattern + 1e-10)
        pattern_db = pattern_db - np.max(pattern_db)  # 归一化
        
        # 创建图表
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=theta, y=pattern_db,
            mode='lines',
            line=dict(color='blue', width=3),
            name='E面'
        ))
        
        # 添加H面（对于某些天线）
        if antenna_id in ['horn', 'parabolic']:
            pattern_h = pattern_db + np.random.normal(0, 2, len(pattern_db))
            fig.add_trace(go.Scatter(
                x=theta, y=pattern_h,
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name='H面'
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="角度 (°)",
            yaxis_title="增益 (dB)",
            height=300,
            showlegend=True
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _compare_antenna_types(self, selected_types: List[str], antenna_types: List[Dict[str, Any]]):
        """比较天线类型"""
        # 筛选选中的天线
        selected_antennas = [ant for ant in antenna_types if ant['name'] in selected_types]
        
        if len(selected_antennas) < 2:
            return
        
        # 创建比较表格
        comparison_data = []
        
        for antenna in selected_antennas:
            params = antenna.get('parameters', {}).copy()
            params['天线类型'] = antenna['name']
            params['描述'] = antenna['description'][:50] + '...'  # 截断描述
            
            comparison_data.append(params)
        
        # 转换为DataFrame
        df = pd.DataFrame(comparison_data)
        
        # 重新排列列，让天线类型在第一列
        cols = ['天线类型'] + [col for col in df.columns if col != '天线类型']
        df = df[cols]
        
        st.dataframe(df, width='stretch')
        
        # 创建雷达图比较
        st.markdown("#### 📊 性能雷达图")
        
        # 提取关键参数并归一化
        parameters_to_compare = ['增益', '波束宽度', '带宽', '效率']
        
        fig = go.Figure()
        
        for antenna in selected_antennas:
            params = antenna.get('parameters', {})
            values = []
            
            for param in parameters_to_compare:
                if param in params:
                    value_str = params[param]
                    # 尝试提取数值
                    import re
                    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", value_str)
                    if numbers:
                        value = float(numbers[0])
                    else:
                        value = 0
                else:
                    value = 0
                
                # 归一化（简单方法）
                if param == '增益':
                    # 假设增益范围 0-30 dBi
                    normalized = min(value / 30, 1.0)
                elif param == '波束宽度':
                    # 假设波束宽度范围 1-180度，越小越好
                    normalized = 1 - min(value / 180, 1.0)
                elif param == '带宽':
                    # 提取百分比
                    normalized = min(value / 100, 1.0)
                elif param == '效率':
                    # 效率已经是0-1
                    normalized = value
                else:
                    normalized = 0
                
                values.append(normalized)
            
            # 闭合雷达图
            values.append(values[0])
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=parameters_to_compare + [parameters_to_compare[0]],
                name=antenna['name'],
                fill='toself'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 应用建议
        st.markdown("#### 💡 应用建议")
        
        for antenna in selected_antennas:
            apps = antenna.get('applications', [])
            if apps:
                st.markdown(f"**{antenna['name']}适用场景:**")
                for app in apps[:3]:  # 只显示前3个应用
                    st.markdown(f"- {app}")
                st.markdown("")
    
    def _render_design_guidelines(self):
        """渲染设计指南"""
        st.markdown("## 🔧 天线设计指南")
        
        guidelines = self.content.get('design_guidelines', [])
        
        for guideline in guidelines:
            with st.expander(f"### {guideline['title']}", expanded=True):
                if 'steps' in guideline:
                    st.markdown("#### 📋 设计步骤")
                    for step in guideline['steps']:
                        st.markdown(f"**{step['step']}. {step['title']}**")
                        st.markdown(f"{step['content']}")
                        st.markdown("")
                
                elif 'points' in guideline:
                    st.markdown("#### 💡 设计要点")
                    for point in guideline['points']:
                        st.markdown(f"**{point['title']}**")
                        st.markdown(f"{point['content']}")
                        st.markdown("")
                
                elif 'problems' in guideline:
                    st.markdown("#### ⚠️ 常见问题与解决")
                    for problem in guideline['problems']:
                        st.markdown(f"**问题:** {problem['problem']}")
                        st.markdown(f"**原因:** {problem['cause']}")
                        st.markdown(f"**解决:** {problem['solution']}")
                        st.markdown("---")
        
        # 交互式设计工具
        st.markdown("## 🎮 交互式设计工具")
        
        design_tool = st.selectbox(
            "选择设计工具",
            ["尺寸计算器", "阻抗匹配", "带宽估算", "增益估算", "材料选择"],
            index=0
        )
        
        if design_tool == "尺寸计算器":
            self._render_size_calculator()
        elif design_tool == "阻抗匹配":
            self._render_impedance_matching()
        elif design_tool == "带宽估算":
            self._render_bandwidth_estimator()
        elif design_tool == "增益估算":
            self._render_gain_estimator()
        else:  # 材料选择
            self._render_material_selector()
    
    def _render_size_calculator(self):
        """渲染尺寸计算器"""
        st.markdown("### 📏 天线尺寸计算器")
        
        col1, col2 = st.columns(2)
        
        with col1:
            antenna_type = st.selectbox(
                "天线类型",
                ["半波偶极子", "微带贴片", "四分之一波长单极子", "螺旋天线", "抛物面天线"],
                index=0
            )
            
            freq = st.number_input("工作频率 (GHz)", 0.1, 100.0, 2.4, 0.1)
        
        with col2:
            if antenna_type == "微带贴片":
                substrate_er = st.number_input("基板介电常数", 1.0, 10.0, 4.4, 0.1)
                substrate_height = st.number_input("基板厚度 (mm)", 0.1, 10.0, 1.6, 0.1)
        
        # 计算
        wavelength = 300 / freq  # 自由空间波长 (mm)
        
        if antenna_type == "半波偶极子":
            length = wavelength / 2
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 工作频率 | {freq} GHz |
            | 自由空间波长 | {wavelength:.1f} mm |
            | **偶极子长度** | **{length:.1f} mm** |
            | 每臂长度 | {length/2:.1f} mm |
            
            ### 设计说明
            - 半波偶极子总长度 = λ/2
            - 实际长度需考虑末端效应，通常缩短2-5%
            - 导体直径影响带宽和阻抗
            """)
        
        elif antenna_type == "微带贴片":
            # 微带贴片尺寸计算（简化）
            width = 300 / (2 * freq) * np.sqrt(2 / (substrate_er + 1))
            
            # 有效介电常数
            er_eff = (substrate_er + 1) / 2 + (substrate_er - 1) / (2 * np.sqrt(1 + 12 * substrate_height / width))
            
            # 长度（考虑边缘效应）
            delta_L = 0.412 * substrate_height * (er_eff + 0.3) * (width/substrate_height + 0.264) / \
                     ((er_eff - 0.258) * (width/substrate_height + 0.8))
            
            length = 300 / (2 * freq * np.sqrt(er_eff)) - 2 * delta_L
            
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 工作频率 | {freq} GHz |
            | 基板介电常数 | {substrate_er} |
            | 基板厚度 | {substrate_height} mm |
            | 有效介电常数 | {er_eff:.3f} |
            | **贴片宽度** | **{width:.1f} mm** |
            | **贴片长度** | **{length:.1f} mm** |
            
            ### 设计说明
            - 贴片宽度主要决定谐振频率
            - 贴片长度考虑边缘效应修正
            - 馈电位置影响输入阻抗
            - 实际设计需仿真优化
            """)
        
        elif antenna_type == "四分之一波长单极子":
            length = wavelength / 4
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 工作频率 | {freq} GHz |
            | 自由空间波长 | {wavelength:.1f} mm |
            | **单极子长度** | **{length:.1f} mm** |
            
            ### 设计说明
            - 四分之一波长单极子需接地平面
            - 输入阻抗约为36.5Ω
            - 高度为λ/4时辐射电阻最大
            """)
        
        elif antenna_type == "螺旋天线":
            circumference = wavelength
            turn_spacing = wavelength / 4
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 工作频率 | {freq} GHz |
            | 自由空间波长 | {wavelength:.1f} mm |
            | **螺旋周长** | **{circumference:.1f} mm** |
            | **圈间距** | **{turn_spacing:.1f} mm** |
            
            ### 设计说明
            - 周长≈λ时工作于轴向辐射模式
            - 圈间距影响轴比和带宽
            - 圈数影响增益和波束宽度
            """)
        
        else:  # 抛物面天线
            diameter = st.number_input("抛物面直径 (m)", 0.1, 10.0, 1.0, 0.1)
            focal_length = diameter / 4  # 标准抛物面
            
            # 计算增益
            gain_db = 20 * np.log10(diameter * freq * 10) + 20  # 简化公式
            
            # 计算波束宽度
            beamwidth = 70 * wavelength/1000 / diameter  # 度
            
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | 工作频率 | {freq} GHz |
            | 抛物面直径 | {diameter} m |
            | **焦距** | **{focal_length:.2f} m** |
            | **理论增益** | **{gain_db:.1f} dBi** |
            | **3dB波束宽度** | **{beamwidth:.2f}°** |
            
            ### 设计说明
            - 焦距/直径比影响照射效率和旁瓣
            - 表面精度要求通常小于λ/16
            - 馈源位置和设计关键
            """)
    
    def _render_impedance_matching(self):
        """渲染阻抗匹配工具"""
        st.markdown("### 🔌 阻抗匹配设计")
        
        col1, col2 = st.columns(2)
        
        with col1:
            z_antenna = st.number_input("天线阻抗 (Ω)", 1.0, 300.0, 73.0, 1.0)
            z_feed = st.number_input("馈线阻抗 (Ω)", 1.0, 300.0, 50.0, 1.0)
            freq = st.number_input("频率 (GHz)", 0.1, 100.0, 2.4, 0.1)
        
        with col2:
            match_type = st.selectbox(
                "匹配类型",
                ["L型网络", "π型网络", "T型网络", "传输线匹配", "单支节匹配"],
                index=0
            )
        
        # 计算反射系数
        gamma = (z_antenna - z_feed) / (z_antenna + z_feed)
        vswr = (1 + abs(gamma)) / (1 - abs(gamma))
        return_loss = -20 * np.log10(abs(gamma))
        
        st.markdown(f"""
        ### 匹配分析
        
        | 参数 | 值 |
        |------|-----|
        | 天线阻抗 | {z_antenna} Ω |
        | 馈线阻抗 | {z_feed} Ω |
        | 反射系数 | {abs(gamma):.3f} |
        | VSWR | {vswr:.2f} |
        | 回波损耗 | {return_loss:.1f} dB |
        """)
        
        # 匹配评估
        if vswr < 1.5:
            st.success("✅ 良好匹配")
        elif vswr < 2.0:
            st.warning("🟡 中等匹配")
        else:
            st.error("🔴 匹配不良，建议使用匹配网络")
        
        # 匹配网络设计
        if match_type == "L型网络":
            st.markdown("""
            ### L型匹配网络设计
            
            L型网络有两种拓扑：
            
            1. **串联电感 + 并联电容**
            2. **串联电容 + 并联电感**
            
            选择依据：
            - 当天线阻抗 > 馈线阻抗时，使用串联电感+并联电容
            - 当天线阻抗 < 馈线阻抗时，使用串联电容+并联电感
            
            计算公式：
            
            $$
            Q = \\sqrt{\\frac{R_{high}}{R_{low}} - 1}
            $$
            
            $$
            X_{series} = Q \\times R_{low}
            $$
            
            $$
            X_{shunt} = \\frac{R_{high}}{Q}
            $$
            """)
            
            # 计算示例
            if z_antenna > z_feed:
                R_high, R_low = z_antenna, z_feed
            else:
                R_high, R_low = z_feed, z_antenna
            
            Q = np.sqrt(R_high/R_low - 1)
            X_series = Q * R_low
            X_shunt = R_high / Q
            
            # 计算元件值
            freq_hz = freq * 1e9
            L_series = X_series / (2 * np.pi * freq_hz)
            C_shunt = 1 / (2 * np.pi * freq_hz * X_shunt)
            
            st.markdown(f"""
            ### 计算结果
            
            | 参数 | 值 |
            |------|-----|
            | Q值 | {Q:.2f} |
            | 串联电抗 | {X_series:.1f} Ω |
            | 并联电抗 | {X_shunt:.1f} Ω |
            | 串联电感 | {L_series*1e9:.1f} nH |
            | 并联电容 | {C_shunt*1e12:.1f} pF |
            """)
    
    def _render_bandwidth_estimator(self):
        """渲染带宽估算器"""
        st.markdown("### 📶 带宽估算器")
        
        col1, col2 = st.columns(2)
        
        with col1:
            antenna_type = st.selectbox(
                "天线类型",
                ["偶极子", "微带贴片", "螺旋天线", "喇叭天线", "抛物面天线"],
                index=0
            )
            
            center_freq = st.number_input("中心频率 (GHz)", 0.1, 100.0, 2.4, 0.1)
        
        with col2:
            if antenna_type == "偶极子":
                diameter_ratio = st.slider("直径/波长比", 0.001, 0.1, 0.005, 0.001)
            elif antenna_type == "微带贴片":
                substrate_height = st.number_input("基板厚度 (mm)", 0.1, 10.0, 1.6, 0.1)
                substrate_er = st.number_input("介电常数", 1.0, 10.0, 4.4, 0.1)
        
        # 带宽估算
        if antenna_type == "偶极子":
            # 偶极子带宽与直径的关系
            bw_percent = 100 * (1.1 * diameter_ratio**0.5)  # 简化公式
            bw_abs = center_freq * bw_percent / 100
            
            st.markdown(f"""
            ### 带宽估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 偶极子 |
            | 直径/波长比 | {diameter_ratio:.4f} |
            | 中心频率 | {center_freq} GHz |
            | **估算带宽** | **{bw_percent:.1f}%** |
            | **绝对带宽** | **{bw_abs:.3f} GHz** |
            
            ### 说明
            - 偶极子带宽随导体直径增加而增加
            - 典型带宽：细导线(~1%)，粗导线(~10%)
            - 可使用锥形或笼形结构增加带宽
            """)
        
        elif antenna_type == "微带贴片":
            # 微带贴片带宽估算
            bw_percent = 100 * (3.77 * (substrate_height/1.6) * 
                              ((substrate_er - 1) / substrate_er**2))  # 简化公式
            bw_percent = max(1, min(bw_percent, 20))  # 限制范围
            bw_abs = center_freq * bw_percent / 100
            
            st.markdown(f"""
            ### 带宽估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 微带贴片 |
            | 基板厚度 | {substrate_height} mm |
            | 介电常数 | {substrate_er} |
            | 中心频率 | {center_freq} GHz |
            | **估算带宽** | **{bw_percent:.1f}%** |
            | **绝对带宽** | **{bw_abs:.3f} GHz** |
            
            ### 说明
            - 微带贴片带宽与基板厚度成正比
            - 与介电常数成反比
            - 可通过以下方法增加带宽：
              1. 增加基板厚度
              2. 降低介电常数
              3. 使用多层结构
              4. 采用缝隙耦合馈电
            """)
        
        elif antenna_type == "螺旋天线":
            bw_percent = 15  # 典型值
            bw_abs = center_freq * bw_percent / 100
            
            st.markdown(f"""
            ### 带宽估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 螺旋天线 |
            | 中心频率 | {center_freq} GHz |
            | **典型带宽** | **{bw_percent}%** |
            | **绝对带宽** | **{bw_abs:.3f} GHz** |
            
            ### 说明
            - 螺旋天线具有较宽带宽
            - 带宽受螺旋参数（圈数、螺距、直径）影响
            - 轴向模螺旋天线典型带宽：10-20%
            """)
        
        elif antenna_type == "喇叭天线":
            bw_percent = 40  # 典型值
            bw_abs = center_freq * bw_percent / 100
            
            st.markdown(f"""
            ### 带宽估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 喇叭天线 |
            | 中心频率 | {center_freq} GHz |
            | **典型带宽** | **{bw_percent}%** |
            | **绝对带宽** | **{bw_abs:.3f} GHz** |
            
            ### 说明
            - 喇叭天线具有很宽带宽
            - 带宽受波导模式限制
            - 典型带宽：可达40%以上
            - 双模或多模喇叭可进一步增加带宽
            """)
        
        else:  # 抛物面天线
            bw_percent = 10  # 典型值
            bw_abs = center_freq * bw_percent / 100
            
            st.markdown(f"""
            ### 带宽估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 抛物面天线 |
            | 中心频率 | {center_freq} GHz |
            | **典型带宽** | **{bw_percent}%** |
            | **绝对带宽** | **{bw_abs:.3f} GHz** |
            
            ### 说明
            - 抛物面天线带宽主要受馈源限制
            - 典型带宽：5-15%
            - 宽带馈源可实现更宽带宽
            - 双反射面可改善带宽特性
            """)
    
    def _render_gain_estimator(self):
        """渲染增益估算器"""
        st.markdown("### 📡 增益估算器")
        
        col1, col2 = st.columns(2)
        
        with col1:
            antenna_type = st.selectbox(
                "天线类型",
                ["偶极子", "微带贴片", "喇叭天线", "抛物面天线", "阵列天线"],
                index=0
            )
        
        with col2:
            freq = st.number_input("频率 (GHz)", 0.1, 100.0, 2.4, 0.1)
        
        # 根据天线类型获取参数
        if antenna_type == "偶极子":
            gain = 2.15  # dBi
            st.markdown(f"""
            ### 增益估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 半波偶极子 |
            | 频率 | {freq} GHz |
            | **理论增益** | **{gain} dBi** |
            
            ### 说明
            - 半波偶极子理论增益：2.15 dBi
            - 实际增益受地面影响
            - 可使用反射器或引向器增加增益
            """)
        
        elif antenna_type == "微带贴片":
            patch_size = st.number_input("贴片尺寸 (mm)", 1.0, 100.0, 30.0, 1.0)
            
            # 简化增益估算
            gain = 6 + 10 * np.log10(patch_size/30)  # 经验公式
            
            st.markdown(f"""
            ### 增益估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 微带贴片 |
            | 频率 | {freq} GHz |
            | 贴片尺寸 | {patch_size} mm |
            | **估算增益** | **{gain:.1f} dBi** |
            
            ### 说明
            - 微带贴片典型增益：5-8 dBi
            - 增益与电尺寸相关
            - 可通过以下方法提高增益：
              1. 增加贴片尺寸
              2. 使用高介电常数基板
              3. 采用阵列结构
            """)
        
        elif antenna_type == "喇叭天线":
            aperture = st.number_input("口径尺寸 (cm)", 1.0, 100.0, 10.0, 1.0)
            
            # 增益估算公式
            wavelength = 30 / freq  # cm
            gain_db = 10 * np.log10(4 * np.pi * (aperture/wavelength)**2 * 0.5)  # 假设效率50%
            
            st.markdown(f"""
            ### 增益估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 喇叭天线 |
            | 频率 | {freq} GHz |
            | 波长 | {wavelength:.1f} cm |
            | 口径尺寸 | {aperture} cm |
            | **估算增益** | **{gain_db:.1f} dBi** |
            
            ### 说明
            - 喇叭天线增益与口径面积成正比
            - 与波长平方成反比
            - 典型效率：50-80%
            - 可通过增加口径尺寸或优化喇叭形状提高增益
            """)
        
        elif antenna_type == "抛物面天线":
            diameter = st.number_input("直径 (m)", 0.1, 10.0, 1.0, 0.1)
            
            # 增益估算
            gain_db = 20 * np.log10(diameter * freq * 10) + 20  # 简化公式
            
            st.markdown(f"""
            ### 增益估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 抛物面天线 |
            | 频率 | {freq} GHz |
            | 直径 | {diameter} m |
            | **估算增益** | **{gain_db:.1f} dBi** |
            
            ### 说明
            - 抛物面天线增益与直径平方成正比
            - 与波长平方成反比
            - 典型效率：50-75%
            - 增益公式：$G = (πD/λ)^2 η$
            """)
        
        else:  # 阵列天线
            n_elements = st.number_input("阵元数量", 2, 1000, 16, 2)
            element_gain = st.number_input("单元增益 (dBi)", 0.0, 20.0, 5.0, 0.5)
            
            # 阵列增益估算
            array_gain = element_gain + 10 * np.log10(n_elements)
            
            st.markdown(f"""
            ### 增益估算
            
            | 参数 | 值 |
            |------|-----|
            | 天线类型 | 阵列天线 |
            | 阵元数量 | {n_elements} |
            | 单元增益 | {element_gain} dBi |
            | **阵列增益** | **{array_gain:.1f} dBi** |
            
            ### 说明
            - 理想阵列增益 = 单元增益 + 10log₁₀(N)
            - 实际增益受互耦、馈电损耗等影响
            - 阵元间距影响栅瓣和扫描特性
            - 加权降低副瓣会减小增益
            """)
    
    def _render_material_selector(self):
        """渲染材料选择器"""
        st.markdown("### 📦 天线材料选择")
        
        col1, col2 = st.columns(2)
        
        with col1:
            application = st.selectbox(
                "应用场景",
                ["高频/微波", "低频/广播", "移动设备", "基站", "航空航天", "低成本"],
                index=0
            )
            
            freq_range = st.selectbox(
                "频率范围",
                ["HF (<30MHz)", "VHF (30-300MHz)", "UHF (300MHz-3GHz)", 
                 "微波 (3-30GHz)", "毫米波 (>30GHz)"],
                index=2
            )
        
        with col2:
            requirement = st.multiselect(
                "特殊要求",
                ["低损耗", "高稳定性", "轻量化", "耐候性", "柔韧性", "低成本"],
                default=["低损耗"]
            )
            
            environment = st.selectbox(
                "工作环境",
                ["室内", "室外温和", "室外严酷", "航空航天", "水下", "特殊"],
                index=0
            )
        
        # 推荐材料
        materials = []
        
        if application == "高频/微波" or "低损耗" in requirement:
            materials.extend([
                {"名称": "Rogers RO4350B", "介电常数": 3.48, "损耗角正切": 0.0037, 
                 "特点": "高频低损耗，稳定性好", "适用": "微波电路，基站天线"},
                {"名称": "PTFE/玻璃布", "介电常数": 2.2-2.5, "损耗角正切": 0.0009, 
                 "特点": "超低损耗，成本高", "适用": "高频精密天线"},
                {"名称": "陶瓷基板", "介电常数": 9-10, "损耗角正切": 0.002, 
                 "特点": "高介电常数，小型化", "适用": "小型化天线"}
            ])
        
        if application == "移动设备" or "低成本" in requirement:
            materials.extend([
                {"名称": "FR4", "介电常数": 4.4, "损耗角正切": 0.02, 
                 "特点": "成本低，工艺成熟", "适用": "消费电子，WiFi天线"},
                {"名称": "PET薄膜", "介电常数": 3.2, "损耗角正切": 0.005, 
                 "特点": "柔韧，可弯曲", "适用": "柔性天线"}
            ])
        
        if application == "基站" or "高稳定性" in requirement:
            materials.extend([
                {"名称": "Rogers RT5880", "介电常数": 2.2, "损耗角正切": 0.0009, 
                 "特点": "低损耗，热稳定性好", "适用": "基站，卫星通信"},
                {"名称": "铝基板", "介电常数": 3.0, "损耗角正切": 0.003, 
                 "特点": "散热好，机械强度高", "适用": "大功率天线"}
            ])
        
        if application == "航空航天":
            materials.extend([
                {"名称": "石英纤维", "介电常数": 3.8, "损耗角正切": 0.001, 
                 "特点": "低热膨胀，高强度", "适用": "航空航天天线"},
                {"名称": "聚酰亚胺", "介电常数": 3.5, "损耗角正切": 0.002, 
                 "特点": "耐高温，耐辐射", "适用": "空间应用"}
            ])
        
        # 去重
        seen = set()
        unique_materials = []
        for mat in materials:
            key = mat["名称"]
            if key not in seen:
                seen.add(key)
                unique_materials.append(mat)
        
        # 显示推荐材料
        st.markdown("### 💡 推荐材料")
        
        df = pd.DataFrame(unique_materials)
        st.dataframe(df, width='stretch')
        
        # 材料比较
        st.markdown("### 📊 材料性能比较")
        
        if len(unique_materials) >= 2:
            # 创建雷达图
            parameters = ["介电常数", "损耗角正切", "成本", "稳定性", "工艺性"]
            
            fig = go.Figure()
            
            for mat in unique_materials[:3]:  # 最多比较3种材料
                values = []
                
                for param in parameters:
                    if param == "介电常数":
                        value = mat["介电常数"]
                        normalized = 1 - (value - 2) / 8  # 2-10映射到1-0
                    elif param == "损耗角正切":
                        value = mat["损耗角正切"]
                        normalized = 1 - value * 100  # 越小越好
                    elif param == "成本":
                        # 估算成本
                        if "Rogers" in mat["名称"]:
                            normalized = 0.3
                        elif "FR4" in mat["名称"]:
                            normalized = 0.9
                        else:
                            normalized = 0.6
                    elif param == "稳定性":
                        if "航空航天" in mat["特点"] or "高稳定性" in mat["特点"]:
                            normalized = 0.9
                        else:
                            normalized = 0.6
                    else:  # 工艺性
                        if "FR4" in mat["名称"] or "成本低" in mat["特点"]:
                            normalized = 0.9
                        else:
                            normalized = 0.5
                    
                    values.append(max(0.1, min(1.0, normalized)))
                
                # 闭合雷达图
                values.append(values[0])
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=parameters + [parameters[0]],
                    name=mat["名称"],
                    fill='toself'
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # 选择建议
        st.markdown("### 💡 选择建议")
        
        if "低损耗" in requirement and freq_range in ["微波", "毫米波"]:
            st.success("推荐使用Rogers RO4350B或PTFE材料，损耗低，高频性能好")
        elif "低成本" in requirement and application == "移动设备":
            st.success("推荐使用FR4材料，成本低，工艺成熟，适合批量生产")
        elif "高稳定性" in requirement and environment in ["室外严酷", "航空航天"]:
            st.success("推荐使用石英纤维或聚酰亚胺材料，耐候性好，稳定性高")
        elif "柔韧性" in requirement:
            st.success("推荐使用PET薄膜材料，柔韧可弯曲，适合可穿戴设备")
    
    def _render_analysis_methods(self):
        """渲染分析方法"""
        st.markdown("## 📊 天线分析方法")
        
        methods = self.content.get('analysis_methods', [])
        
        for method in methods:
            with st.expander(f"### {method['title']}", expanded=True):
                if 'methods' in method:
                    st.markdown("#### 🔬 分析方法比较")
                    
                    df = pd.DataFrame(method['methods'])
                    st.dataframe(df, width='stretch')
                    
                elif 'parameters' in method:
                    st.markdown("#### 📈 参数提取方法")
                    
                    for param in method['parameters']:
                        st.markdown(f"**{param['name']}**")
                        st.markdown(f"方法: {', '.join(param['methods'])}")
                        st.markdown(f"设备: {param['equipment']}")
                        st.markdown("---")
                
                elif 'software' in method:
                    st.markdown("#### 💻 仿真软件")
                    
                    for software in method['software']:
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            st.markdown(f"**{software['name']}**")
                            st.markdown(f"*{software['company']}*")
                        
                        with col2:
                            st.markdown(f"**方法:** {', '.join(software['methods'])}")
                            st.markdown(f"**特点:** {software['features']}")
                            st.markdown(f"**应用:** {software['applications']}")
                        
                        st.markdown("---")
        
        # 分析方法选择指南
        st.markdown("## 🎯 分析方法选择指南")
        
        col1, col2 = st.columns(2)
        
        with col1:
            antenna_size = st.selectbox(
                "天线电尺寸",
                ["小电尺寸 (<1λ)", "中等电尺寸 (1-10λ)", "大电尺寸 (>10λ)"],
                index=0
            )
            
            analysis_type = st.selectbox(
                "分析类型",
                ["方向图分析", "阻抗分析", "宽带分析", "系统级分析"],
                index=0
            )
        
        with col2:
            accuracy = st.selectbox(
                "精度要求",
                ["工程估算", "设计验证", "高精度分析"],
                index=1
            )
            
            resources = st.selectbox(
                "计算资源",
                ["有限", "中等", "充足"],
                index=1
            )
        
        # 推荐分析方法
        recommendations = []
        
        if antenna_size == "小电尺寸" and accuracy == "工程估算":
            recommendations.append("解析法 - 快速，物理意义明确")
        
        if accuracy == "设计验证":
            if antenna_size == "小电尺寸":
                recommendations.append("矩量法 (MoM) - 精度高，适合线天线")
                recommendations.append("有限元法 (FEM) - 适合复杂结构")
            elif antenna_size == "中等电尺寸":
                recommendations.append("有限元法 (FEM) - 适合复杂介质")
                recommendations.append("时域有限差分法 (FDTD) - 适合宽带分析")
        
        if antenna_size == "大电尺寸":
            recommendations.append("物理光学法 (PO) - 计算快速，适合反射面")
            recommendations.append("混合方法 (MoM+PO) - 平衡精度和速度")
        
        if analysis_type == "系统级分析":
            recommendations.append("系统仿真 (如ADS) - 适合电路和系统联合仿真")
        
        if resources == "有限":
            recommendations = [r for r in recommendations if "快速" in r or "解析" in r]
        
        st.markdown("### 💡 推荐分析方法")
        
        for i, rec in enumerate(set(recommendations), 1):
            st.markdown(f"{i}. {rec}")
        
        # 仿真流程示例
        st.markdown("### 📋 典型仿真流程")
        
        steps = [
            "1. 几何建模 - 创建天线三维模型",
            "2. 材料定义 - 设置材料属性",
            "3. 边界条件 - 设置辐射边界、对称面等",
            "4. 网格划分 - 生成计算网格",
            "5. 求解设置 - 设置频率、扫频范围等",
            "6. 求解计算 - 运行仿真",
            "7. 后处理 - 提取方向图、阻抗等参数",
            "8. 优化 - 根据结果优化设计"
        ]
        
        for step in steps:
            st.markdown(step)
    
    def _render_case_studies(self):
        """渲染案例研究"""
        st.markdown("## 🎯 天线设计案例研究")
        
        cases = self.content.get('case_studies', [])
        
        for case in cases:
            with st.expander(f"### {case['title']}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**描述:** {case['description']}")
                    
                    st.markdown("#### 📋 设计要求")
                    requirements = case.get('requirements', {})
                    
                    for key, value in requirements.items():
                        st.markdown(f"**{key}:** {value}")
                    
                    st.markdown("#### 📐 设计步骤")
                    steps = case.get('design_steps', [])
                    
                    for i, step in enumerate(steps, 1):
                        st.markdown(f"{i}. {step}")
                
                with col2:
                    st.markdown("#### 📊 设计结果")
                    results = case.get('results', {})
                    
                    for key, value in results.items():
                        st.markdown(f"**{key}:** {value}")
                
                # 设计要点和经验
                st.markdown("#### 💡 设计要点")
                
                if case['id'] == 'case_1':
                    points = [
                        "使用FR4基板平衡成本和性能",
                        "同轴馈电位置影响阻抗匹配",
                        "考虑实际安装环境对性能的影响",
                        "批量生产时注意公差控制"
                    ]
                elif case['id'] == 'case_2':
                    points = [
                        "波导到喇叭的渐变段设计关键",
                        "喇叭张角影响增益和波束宽度平衡",
                        "加工精度影响高频性能",
                        "考虑防水设计（室外应用）"
                    ]
                else:  # case_3
                    points = [
                        "单元设计考虑互耦影响",
                        "馈电网络设计复杂，需仿真优化",
                        "幅度锥削降低副瓣电平",
                        "考虑扫描时的阻抗匹配"
                    ]
                
                for point in points:
                    st.markdown(f"- {point}")
                
                # 方向图示例
                st.markdown("#### 📡 方向图示例")
                self._display_case_pattern(case['id'])
                
                st.markdown("---")
    
    def _display_case_pattern(self, case_id: str):
        """显示案例方向图"""
        theta = np.linspace(0, 180, 181)
        
        if case_id == 'case_1':
            # WiFi天线方向图
            pattern = np.exp(-((theta - 90)**2) / (2 * 40**2))
            pattern = pattern + 0.2 * np.exp(-((theta - 50)**2) / (2 * 20**2))
            pattern = pattern + 0.2 * np.exp(-((theta - 130)**2) / (2 * 20**2))
            title = "WiFi微带贴片天线方向图"
        
        elif case_id == 'case_2':
            # 喇叭天线方向图
            pattern = np.exp(-((theta - 90)**2) / (2 * 7**2))
            pattern = pattern + 0.1 * np.exp(-((theta - 60)**2) / (2 * 5**2))
            pattern = pattern + 0.1 * np.exp(-((theta - 120)**2) / (2 * 5**2))
            pattern = pattern + 0.05 * np.exp(-((theta - 30)**2) / (2 * 10**2))
            pattern = pattern + 0.05 * np.exp(-((theta - 150)**2) / (2 * 10**2))
            title = "X波段喇叭天线方向图"
        
        else:  # case_3
            # 阵列天线方向图
            pattern = np.abs(np.sin(8 * np.deg2rad(theta - 90)))
            pattern = pattern / np.max(pattern)
            pattern = pattern + 0.1 * np.abs(np.sin(4 * np.deg2rad(theta - 90)))
            title = "5G基站阵列天线方向图"
        
        # 转换为dB
        pattern_db = 20 * np.log10(pattern + 1e-10)
        pattern_db = pattern_db - np.max(pattern_db)  # 归一化
        
        # 创建图表
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=theta, y=pattern_db,
            mode='lines',
            line=dict(color='blue', width=3),
            name='方向图'
        ))
        
        # 标记副瓣
        if case_id == 'case_2':
            fig.add_annotation(x=60, y=-20, text="副瓣", 
                              showarrow=True, arrowhead=2, ax=0, ay=-30)
            fig.add_annotation(x=120, y=-20, text="副瓣", 
                              showarrow=True, arrowhead=2, ax=0, ay=-30)
        
        fig.update_layout(
            title=title,
            xaxis_title="角度 (°)",
            yaxis_title="增益 (dB)",
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    
    def _render_learning_resources(self):
        """渲染学习资源"""
        st.markdown("## 📖 天线学习资源")
        
        resources = self.content.get('resources', [])
        
        for resource in resources:
            with st.expander(f"### {resource['title']}", expanded=True):
                items = resource.get('items', [])
                
                for item in items:
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.markdown(f"**{item['title']}**")
                        
                        if 'author' in item:
                            st.markdown(f"*{item['author']}*")
                        
                        if 'edition' in item:
                            st.markdown(f"版本: {item['edition']}")
                        
                        if 'company' in item:
                            st.markdown(f"公司: {item['company']}")
                        
                        if 'type' in item:
                            st.markdown(f"类型: {item['type']}")
                        
                        if 'source' in item:
                            st.markdown(f"来源: {item['source']}")
                    
                    with col2:
                        st.markdown(item['description'])
                        
                        if 'url' in item:
                            st.markdown(f"[访问网站]({item['url']})")
                    
                    st.markdown("---")
        
        # 学习路径建议
        st.markdown("## 🎓 学习路径建议")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 👶 初学者")
            st.markdown("""
            1. 天线基本概念
            2. 常见天线类型
            3. 基本参数理解
            4. 简单设计方法
            """)
            
            st.markdown("**推荐资源:**")
            st.markdown("- 天线理论 (Balanis) 前几章")
            st.markdown("- Antenna-Theory.com 网站")
            st.markdown("- 本平台基础知识模块")
        
        with col2:
            st.markdown("### 👨‍🎓 中级学者")
            st.markdown("""
            1. 深入天线理论
            2. 设计方法学习
            3. 仿真软件使用
            4. 实际设计案例
            """)
            
            st.markdown("**推荐资源:**")
            st.markdown("- 天线理论完整学习")
            st.markdown("- HFSS/CST 教程")
            st.markdown("- 实际项目实践")
        
        with col3:
            st.markdown("### 👨‍🔬 高级专家")
            st.markdown("""
            1. 前沿天线技术
            2. 复杂系统设计
            3. 测量与测试
            4. 标准与规范
            """)
            
            st.markdown("**推荐资源:**")
            st.markdown("- IEEE期刊基准")
            st.markdown("- 专业会议资料")
            st.markdown("- 实际工程项目")
        
        # 学习工具
        st.markdown("## 🛠️ 学习工具")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📱 移动应用")
            st.markdown("""
            - **Antenna Calculator** - 天线计算器
            - **RF Toolkit** - 射频工具箱
            - **Satellite Tracker** - 卫星跟踪
            - **Electronics Assistant** - 电子助手
            """)
        
        with col2:
            st.markdown("### 💻 在线工具")
            st.markdown("""
            - **在线计算器** - 各种天线参数计算
            - **仿真云平台** - 在线电磁仿真
            - **数据可视化** - 结果分析和可视化
            - **协作平台** - 团队协作设计
            """)
        
        # 社区和论坛
        st.markdown("## 👥 社区与论坛")
        
        communities = [
            {"名称": "IEEE天线与传播协会", "网址": "https://www.ieeeaps.org", 
             "描述": "专业学术组织，会议、期刊、标准"},
            {"名称": "StackExchange RF标签", "网址": "https://ham.stackexchange.com", 
             "描述": "问答社区，天线和射频问题"},
            {"名称": "Reddit天线板块", "网址": "https://www.reddit.com/r/antennas", 
             "描述": "天线爱好者和专业人士社区"},
            {"名称": "LinkedIn天线组", "网址": "https://www.linkedin.com/groups", 
             "描述": "专业人士网络，招聘和讨论"},
            {"名称": "GitHub天线项目", "网址": "https://github.com/topics/antenna", 
             "描述": "开源天线项目和代码"}
        ]
        
        for comm in communities:
            st.markdown(f"**[{comm['名称']}]({comm['网址']})** - {comm['描述']}")

def render_education(config: AppConfig, sidebar_config: Dict[str, Any]):
    """
    渲染教学视图的主函数
    """
    try:
        education_view = EducationView(config)
        education_view.render(sidebar_config)
    except Exception as e:
        st.error(f"教学视图渲染错误: {e}")
        st.exception(e)

if __name__ == "__main__":
    # 测试代码
    config = AppConfig()
    sidebar_config = {
        'page': 'education',
        'antenna_config': {},
        'simulation_settings': {},
        'analysis_settings': {},
        'visualization_settings': {},
        'actions': {}
    }
    
    st.set_page_config(layout="wide")
    render_education(config, sidebar_config)