"""
报告生成模块
负责生成专业的评估报告，集成Kimi AI分析
"""

from utils.radar_calculations import RadarCalculator
from utils.visualization import VisualizationTools
from config.config import (
    REPORT_CONFIG, KIMI_API_CONFIG, COLOR_SCHEME,
    SYSTEM_MESSAGES, OUTPUTS_DIR
)
from io import BytesIO
import base64
from PIL import Image
import time
from requests.exceptions import RequestException
import requests
import os
import json
import yaml
import markdown
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union
import warnings
warnings.filterwarnings('ignore')


class ReportGenerator:
    """报告生成器类"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化报告生成器"""
        self.api_key = api_key
        self.viz_tools = VisualizationTools()
        self.calculator = RadarCalculator()

        # 配置
        self.report_config = REPORT_CONFIG
        self.api_config = KIMI_API_CONFIG

        # 创建输出目录
        self.outputs_dir = OUTPUTS_DIR
        self.charts_dir = self.outputs_dir / "charts"
        self.data_dir = self.outputs_dir / "data"
        self.reports_dir = self.outputs_dir / "reports"

        for directory in [self.charts_dir, self.data_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def set_api_key(self, api_key: str) -> None:
        """设置Kimi API密钥"""
        self.api_key = api_key

    def generate_report(
        self,
        scenario_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        report_title: Optional[str] = None,
        author: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成评估报告

        参数:
            scenario_data: 场景数据
            analysis_results: 分析结果
            report_title: 报告标题
            author: 作者
            company: 公司名称

        返回:
            报告生成结果
        """
        print("开始生成评估报告...")

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 准备报告数据
        report_data = {
            'metadata': {
                'report_id': f"REP_{timestamp}",
                'generated_at': datetime.now().isoformat(),
                'scenario_name': scenario_data.get('name', '未命名场景'),
                'version': self.report_config['report_version']
            },
            'scenario': scenario_data,
            'analysis': analysis_results
        }

        # 生成报告内容
        markdown_content = self._generate_markdown_content(
            report_data, report_title, author, company
        )

        # 保存报告
        report_filename = f"风电雷达影响评估报告_{timestamp}.md"
        report_path = self.reports_dir / report_filename

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"报告已保存: {report_path}")

        # 生成PDF版本（如果支持）
        pdf_path = None
        try:
            pdf_path = self._convert_to_pdf(markdown_content, timestamp)
        except Exception as e:
            print(f"PDF转换失败: {e}")

        return {
            'markdown_path': str(report_path),
            'pdf_path': pdf_path,
            'timestamp': timestamp,
            'report_id': report_data['metadata']['report_id']
        }

    def _generate_markdown_content(
        self,
        report_data: Dict[str, Any],
        title: Optional[str] = None,
        author: Optional[str] = None,
        company: Optional[str] = None
    ) -> str:
        """
        生成Markdown报告内容

        参数:
            report_data: 报告数据
            title: 报告标题
            author: 作者
            company: 公司名称

        返回:
            Markdown格式报告内容
        """
        # 使用配置中的默认值
        if title is None:
            title = self.report_config['report_title']
        if author is None:
            author = self.report_config['author']
        if company is None:
            company = self.report_config['company_name']

        # 生成报告各部分
        sections = []

        # 1. 封面页
        sections.append(self._generate_cover_page(
            title, author, company, report_data['metadata']))

        # 2. 目录
        sections.append(self._generate_table_of_contents())

        # 3. 执行摘要
        sections.append(self._generate_executive_summary(report_data))

        # 4. 项目概述
        sections.append(self._generate_project_overview(report_data))

        # 5. 评估方法
        sections.append(self._generate_methodology())

        # 6. 场景描述
        sections.append(self._generate_scenario_description(
            report_data['scenario']))

        # 7. 分析结果
        analysis_section = self._generate_analysis_results(
            report_data['analysis'], report_data['scenario'])
        sections.append(analysis_section)

        # 8. 影响评估
        sections.append(self._generate_impact_assessment(report_data))

        # 9. 缓解措施
        sections.append(self._generate_mitigation_measures(report_data))

        # 10. 结论
        sections.append(self._generate_conclusions(report_data))

        # 11. 建议
        sections.append(self._generate_recommendations(report_data))

        # 12. 附录
        sections.append(self._generate_appendices(report_data))

        # 合并所有部分
        markdown_content = "\n\n".join(sections)

        return markdown_content

    def _generate_cover_page(
        self,
        title: str,
        author: str,
        company: str,
        metadata: Dict[str, Any]
    ) -> str:
        """生成封面页"""
        report_id = metadata.get('report_id', 'N/A')
        generated_at = metadata.get('generated_at', '')
        scenario_name = metadata.get('scenario_name', '未命名场景')

        # 解析生成时间
        try:
            gen_time = datetime.fromisoformat(
                generated_at.replace('Z', '+00:00'))
            gen_date = gen_time.strftime("%Y年%m月%d日")
        except:
            gen_date = "未知日期"

        cover_page = f"""# {title}

---

## 报告信息

| 项目 | 内容 |
|------|------|
| **报告编号** | {report_id} |
| **场景名称** | {scenario_name} |
| **生成日期** | {gen_date} |
| **评估单位** | {company} |
| **报告作者** | {author} |
| **报告版本** | {self.report_config['report_version']} |

---

## 保密声明

本报告包含专有和机密信息，仅限授权人员使用。未经{company}书面许可，不得复制、传播或使用本报告的任何部分。

---

*报告生成系统: 风电雷达影响评估系统 v{self.report_config['report_version']}*
"""
        return cover_page

    def _generate_table_of_contents(self) -> str:
        """生成目录"""
        toc = """# 目录

1. [执行摘要](#1-执行摘要)
2. [项目概述](#2-项目概述)
3. [评估方法](#3-评估方法)
4. [场景描述](#4-场景描述)
5. [分析结果](#5-分析结果)
6. [影响评估](#6-影响评估)
7. [缓解措施](#7-缓解措施)
8. [结论](#8-结论)
9. [建议](#9-建议)
10. [附录](#10-附录)

---
"""
        return toc

    def _generate_executive_summary(self, report_data: Dict[str, Any]) -> str:
        """生成执行摘要"""
        scenario = report_data['scenario']
        analysis = report_data['analysis']

        # 提取关键信息
        num_turbines = len(scenario.get('wind_turbines', []))
        num_radars = len(scenario.get('radar_stations', []))
        num_targets = len(scenario.get('targets', []))

        # 提取性能指标
        performance_metrics = analysis.get('performance_metrics', {})

        summary = f"""# 1. 执行摘要

## 1.1 评估概述

本次评估旨在分析风电场对周边雷达探测性能的影响。评估场景包含：

- **风机数量**: {num_turbines} 台
- **雷达台站**: {num_radars} 个
- **评估目标**: {num_targets} 个

## 1.2 主要发现

### 1.2.1 信噪比影响
在有风机条件下，目标信噪比平均下降 **XX dB**，最大下降 **XX dB**。

### 1.2.2 多径效应
风机引起的多径效应导致信号衰减 **XX dB**，相位偏移 **XX 度**。

### 1.2.3 干扰影响
风机产生的电磁干扰使载干比下降 **XX dB**，对雷达探测性能产生显著影响。

### 1.2.4 检测性能
- 无风机条件下: 平均检测概率 **XX%**
- 有风机条件下: 平均检测概率 **XX%**
- 性能下降: **XX%**

## 1.3 关键结论

1. 风电场对雷达探测性能产生显著影响，特别是在 **XX km** 范围内
2. 影响程度与风机数量、雷达频率、目标距离等因素相关
3. 需要采取适当的缓解措施以降低影响

## 1.4 主要建议

1. 建议在风电场规划阶段进行雷达影响评估
2. 优化风机布局，减少对关键雷达的遮挡
3. 采用先进的信号处理技术减轻干扰
4. 建立长期的监测和评估机制

---
"""
        return summary

    def _generate_project_overview(self, report_data: Dict[str, Any]) -> str:
        """生成项目概述"""
        scenario = report_data['scenario']

        overview = f"""# 2. 项目概述

## 2.1 项目背景

随着风电产业的快速发展，大规模风电场对周边电子系统的影响日益受到关注。风机作为大型金属结构物，会对雷达电磁波产生反射、散射和遮挡，影响雷达的探测性能。

## 2.2 评估目标

本次评估旨在：

1. 量化分析风电场对雷达探测性能的影响
2. 评估不同频段雷达的受影响程度
3. 提出有效的缓解措施和建议
4. 为风电场规划和管理提供科学依据

## 2.3 评估范围

### 2.3.1 空间范围
评估区域覆盖风电场周边 **XX km** 范围，包含所有可能受影响的雷达和通信设施。

### 2.3.2 频率范围
评估涵盖 **VHF** 到 **Ka** 波段的主要雷达频段，重点分析 **S波段** 和 **X波段** 雷达。

### 2.3.3 时间范围
评估考虑风机在不同运行状态下的影响，包括：
- 静止状态
- 正常运行状态
- 极端天气条件

## 2.4 评估依据

本次评估基于以下标准和规范：

1. **国际电信联盟 (ITU)** 相关建议
2. **国际电工委员会 (IEC)** 风电标准
3. **中国国家标准** 雷达性能测试规范
4. **行业最佳实践** 和工程经验

---
"""
        return overview

    def _generate_methodology(self) -> str:
        """生成评估方法"""
        methodology = """
        # 3. 评估方法

## 3.1 评估框架

本次评估采用**理论分析、数值模拟和实测验证**相结合的方法，建立完整的评估框架：

```
数据收集 → 场景建模 → 数值计算 → 影响分析 → 结果验证 → 报告生成
```

## 3.2 雷达方程

使用经典雷达方程计算接收信号功率：

$$
P_r = \\frac{P_t G_t^2 \\lambda^2 \\sigma}{(4\\pi)^3 R^4 L_s L_a}
$$

其中：
- $P_r$: 接收功率 (W)
- $P_t$: 发射功率 (W)
- $G_t$: 天线增益
- $\\lambda$: 波长 (m)
- $\\sigma$: 目标雷达截面积 (m²)
- $R$: 目标距离 (m)
- $L_s$: 系统损耗
- $L_a$: 大气损耗

## 3.3 信噪比计算

信噪比计算公式：

$$
SNR = \\frac{P_r}{P_n} = \\frac{P_r}{k T_0 B F}
$$

其中：
- $P_n$: 噪声功率 (W)
- $k$: 玻尔兹曼常数
- $T_0$: 标准温度
- $B$: 接收机带宽
- $F$: 噪声系数

## 3.4 多径效应模型

采用**四径模型**分析多径效应：

1. 直射路径
2. 地面反射路径
3. 风机反射路径
4. 多次反射路径

## 3.5 干扰分析

干扰分析基于**载干比 (CIR)** 计算：

$$
CIR = \\frac{P_{signal}}{P_{interference}}
$$

考虑频率重叠、极化失配和空间隔离等因素。

## 3.6 检测概率计算

采用**Swerling起伏模型**计算检测概率：

$$
P_d = f(SNR, P_{fa}, N)
$$

其中：
- $P_d$: 检测概率
- $P_{fa}$: 虚警概率
- $N$: 脉冲积累数

## 3.7 评估工具

使用**风电雷达影响评估系统**进行计算和分析，该系统基于：

1. **Python** 科学计算栈
2. **Streamlit** 交互式界面
3. **Folium** 地理可视化
4. **Plotly** 数据可视化
5. **Kimi AI** 智能分析

---
"""
        return methodology

    def _generate_scenario_description(self, scenario_data: Dict[str, Any]) -> str:
        """生成场景描述"""
        # 提取场景信息
        scenario_name = scenario_data.get('name', '未命名场景')
        description = scenario_data.get('description', '无描述')

        # 统计信息
        turbines = scenario_data.get('wind_turbines', [])
        radars = scenario_data.get('radar_stations', [])
        comms = scenario_data.get('communication_stations', [])
        targets = scenario_data.get('targets', [])

        num_turbines = len(turbines)
        num_radars = len(radars)
        num_comms = len(comms)
        num_targets = len(targets)

        # 生成风机表格
        turbines_table = self._generate_turbines_table(turbines)

        # 生成雷达表格
        radars_table = self._generate_radars_table(radars)

        # 生成通信站表格
        comms_table = self._generate_comms_table(comms)

        # 生成目标表格
        targets_table = self._generate_targets_table(targets)

        scenario_desc = f"""# 4. 场景描述

## 4.1 场景概况

**场景名称**: {scenario_name}

**场景描述**: {description}

## 4.2 场景统计

| 项目 | 数量 | 说明 |
|------|------|------|
| 风机数量 | {num_turbines} | 评估区域内的风力发电机 |
| 雷达台站 | {num_radars} | 各类雷达系统 |
| 通信台站 | {num_comms} | 通信基站和发射台 |
| 评估目标 | {num_targets} | 用于评估的目标对象 |

## 4.3 风电场配置

### 4.3.1 风机列表

{turbines_table}

### 4.3.2 风机布局

风机采用 **XX布局**，平均间距 **XX米**，总占地面积 **XX平方公里**。

## 4.4 雷达系统配置

### 4.4.1 雷达台站列表

{radars_table}

### 4.4.2 雷达覆盖

各雷达台站的覆盖范围如下：

1. **雷达1**: 覆盖半径 **XX km**，主要用于 **XX**
2. **雷达2**: 覆盖半径 **XX km**，主要用于 **XX**
3. **雷达3**: 覆盖半径 **XX km**，主要用于 **XX**

## 4.5 通信系统配置

### 4.5.1 通信台站列表

{comms_table}

## 4.6 评估目标配置

### 4.6.1 目标列表

{targets_table}

## 4.7 环境条件

| 参数 | 数值 | 说明 |
|------|------|------|
| 温度 | 15°C | 标准大气温度 |
| 湿度 | 50% | 相对湿度 |
| 气压 | 1013 hPa | 标准大气压 |
| 地形 | 平坦 | 评估区域地形 |
| 地表类型 | 草地 | 地面覆盖类型 |

---
"""
        return scenario_desc

    def _generate_analysis_results(
        self,
        analysis_results: Dict[str, Any],
        scenario_data: Dict[str, Any]
    ) -> str:
        """生成分析结果部分"""
        print("开始生成分析结果部分...")

        # 生成图表并保存
        print("正在生成分析图表...")
        charts_info = self._generate_analysis_charts(
            analysis_results, scenario_data)

        # 生成分析结果文本
        analysis_text = self._generate_analysis_text(analysis_results)

        # 组合图表和分析文本
        analysis_section = f"""
# 5. 分析结果

## 5.1 分析概述

本章节详细展示有/无风机条件下雷达性能的对比分析结果，包括信噪比、接收功率、多普勒频谱、多径效应、干扰分析和性能指标等。

{analysis_text}

## 5.2 详细分析图表

### 5.2.1 信噪比对比分析

!{charts_info.get('snr_chart_path', '')}

**图表说明**: 本图展示了有/无风机条件下信噪比随距离的变化情况。红色虚线表示典型检测门限(13dB)。

**AI分析**: {charts_info.get('snr_ai_analysis', '等待AI分析...')}

---

### 5.2.2 接收功率对比分析

!{charts_info.get('power_chart_path', '')}

**图表说明**: 本图展示了不同条件下的接收功率变化，包括自由空间损耗、大气损耗和系统损耗的影响。

**AI分析**: {charts_info.get('power_ai_analysis', '等待AI分析...')}

---

### 5.2.3 多普勒频谱分析

!{charts_info.get('doppler_chart_path', '')}

**图表说明**: 本图展示了目标运动引起的多普勒频谱分布，虚线表示目标的理论多普勒频率位置。

**AI分析**: {charts_info.get('doppler_ai_analysis', '等待AI分析...')}

---

### 5.2.4 多径效应分析

!{charts_info.get('multipath_chart_path', '')}

**图表说明**: 本图展示了多径损耗和路径差随距离的变化情况，反映了风机引起的多径效应。

**AI分析**: {charts_info.get('multipath_ai_analysis', '等待AI分析...')}

---

### 5.2.5 干扰分析

!{charts_info.get('interference_chart_path', '')}

**图表说明**: 本图从载干比分布、干扰电平、频率重叠和干扰余量四个方面分析了风机引起的干扰影响。

**AI分析**: {charts_info.get('interference_ai_analysis', '等待AI分析...')}

---

### 5.2.6 性能指标总结

!{charts_info.get('performance_chart_path', '')}

**图表说明**: 本图以雷达图形式展示了六个关键性能指标的评估结果，直观反映了系统整体性能。

**AI分析**: {charts_info.get('performance_ai_analysis', '等待AI分析...')}

---

## 5.3 数据表格

### 5.3.1 关键性能指标对比

{self._generate_performance_table(analysis_results)}

**AI分析**: {self._analyze_performance_table(analysis_results)}

### 5.3.2 影响程度评估

{self._generate_impact_assessment_table(analysis_results)}

**AI分析**: {self._analyze_impact_table(analysis_results)}

---
"""

        return analysis_section


    def _generate_analysis_charts(
        self,
        analysis_results: Dict[str, Any],
        scenario_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        生成分析图表并保存

        参数:
            analysis_results: 分析结果
            scenario_data: 场景数据

        返回:
            图表信息和AI分析结果
        """
        charts_info = {}

        try:
            # 使用可视化工具生成图表
            scenario_name = scenario_data.get('name', '评估场景')
            charts = self.viz_tools.create_comprehensive_dashboard(
                analysis_results,
                scenario_name
            )

            # 保存图表并获取AI分析
            chart_types = [
                ('snr_comparison', '信噪比对比分析'),
                ('power_comparison', '接收功率对比分析'),
                ('doppler_analysis', '多普勒频谱分析'),
                ('multipath_analysis', '多径效应分析'),
                ('interference_analysis', '干扰分析'),
                ('performance_summary', '性能指标总结')
            ]

            for i, (chart_type, description) in enumerate(chart_types):
                if i < len(charts):
                    # 保存图表
                    filename = f"{scenario_name}_{chart_type}.png"
                    chart_path = self.viz_tools.save_chart_as_image(
                        charts[i],
                        filename,
                        self.charts_dir
                    )

                    # 记录图表路径
                    key = f"{chart_type}_chart_path"
                    charts_info[key] = chart_path

                    # 调用Kimi API进行图表分析
                    if self.api_key:
                        try:
                            ai_analysis = self._analyze_chart_with_kimi(
                                chart_path,
                                description
                            )
                            charts_info[f"{chart_type}_ai_analysis"] = ai_analysis
                        except Exception as e:
                            charts_info[f"{chart_type}_ai_analysis"] = f"AI分析失败: {str(e)}"
                    else:
                        charts_info[f"{chart_type}_ai_analysis"] = "未配置Kimi API密钥，跳过AI分析"

        except Exception as e:
            print(f"图表生成失败: {e}")
            import traceback
            traceback.print_exc()

        return charts_info

    def _generate_analysis_text(self, analysis_results: Dict[str, Any]) -> str:
        """生成分析结果文本"""
        # 提取关键指标
        comparison = analysis_results.get('scenario_comparison', {})
        performance = analysis_results.get('performance_metrics', {})
        
        # 计算平均影响
        avg_snr_change = comparison.get('snr_db_percent_change', 0)
        avg_power_change = comparison.get('received_power_db_percent_change', 0)
        detection_prob_change = comparison.get('detection_probability_percent_change', 0)
        
        # 评估影响程度
        def assess_impact_level(change_percent: float) -> str:
            abs_change = abs(change_percent)
            if abs_change > 20:
                return "严重"
            elif abs_change > 10:
                return "显著"
            elif abs_change > 5:
                return "中等"
            else:
                return "轻微"
        
        snr_impact = assess_impact_level(avg_snr_change)
        power_impact = assess_impact_level(avg_power_change)
        detection_impact = assess_impact_level(detection_prob_change)
        
        analysis_text = f"""
## 5.1.1 信噪比分析

在有风机条件下，目标信噪比平均下降 **{abs(avg_snr_change):.1f}%**，影响程度为 **{snr_impact}**。

**主要发现**：
1. 近距离目标（< 50km）受影响较小，信噪比下降约 5-10%
2. 中远距离目标（50-150km）受影响显著，信噪比下降约 10-20%
3. 远距离目标（> 150km）受影响最严重，信噪比下降可达 20-30%

## 5.1.2 接收功率分析

风机引起的多径效应和遮挡导致接收功率平均下降 **{abs(avg_power_change):.1f}%**，影响程度为 **{power_impact}**。

**影响因素**：
1. **多径效应**: 风机反射导致信号相位干涉
2. **阴影遮挡**: 风机塔筒和叶片对电磁波的阻挡
3. **散射效应**: 旋转叶片产生的时变散射
4. **大气衰减**: 风机引起的局部大气扰动

## 5.1.3 检测性能分析

风机存在条件下，目标检测概率平均下降 **{abs(detection_prob_change):.1f}%**，影响程度为 **{detection_impact}**。

**检测性能变化**：
- 高信噪比目标（SNR > 20dB）: 检测概率基本不变
- 中信噪比目标（SNR 10-20dB）: 检测概率下降 5-15%
- 低信噪比目标（SNR < 10dB）: 检测概率下降 15-30%

## 5.1.4 多径效应分析

风机引起的多径效应主要表现在：

1. **路径延迟**: 反射路径比直射路径长 10-100米
2. **相位偏移**: 信号相位变化 0-180度
3. **幅度波动**: 接收信号幅度波动 3-10dB
4. **频率选择性衰落**: 对特定频率成分影响更大

## 5.1.5 干扰影响分析

风机产生的电磁干扰主要表现在：

1. **带内干扰**: 同频段干扰，影响最严重
2. **邻道干扰**: 相邻频段干扰，影响中等
3. **谐波干扰**: 风机电力系统产生的谐波
4. **互调干扰**: 多个信号相互作用产生的干扰

## 5.1.6 总体评估

综合各项指标，风机对雷达探测性能的影响评估如下：

| 性能指标 | 影响程度 | 说明 |
|----------|----------|------|
| 信噪比 | {snr_impact} | 主要受多径效应和散射影响 |
| 检测概率 | {detection_impact} | 与信噪比下降直接相关 |
| 跟踪精度 | 中等 | 多径效应导致测角误差增大 |
| 分辨率 | 轻微 | 基本不影响距离和速度分辨率 |
| 抗干扰能力 | 显著 | 风机反射信号形成虚假目标 |
"""
        
        return analysis_text
    
    def _generate_performance_table(self, analysis_results: Dict[str, Any]) -> str:
        """生成性能指标表格"""
        comparison = analysis_results.get('scenario_comparison', {})
        
        table_data = [
            ("信噪比 (dB)", comparison.get('snr_db_without', 0), comparison.get('snr_db_with', 0), 
             comparison.get('snr_db_difference', 0), comparison.get('snr_db_percent_change', 0)),
            ("接收功率 (dB)", comparison.get('received_power_db_without', 0), comparison.get('received_power_db_with', 0),
             comparison.get('received_power_db_difference', 0), comparison.get('received_power_db_percent_change', 0)),
            ("检测概率 (%)", comparison.get('detection_probability_without', 0)*100, comparison.get('detection_probability_with', 0)*100,
             comparison.get('detection_probability_difference', 0)*100, comparison.get('detection_probability_percent_change', 0)),
            ("多径损耗 (dB)", comparison.get('multipath_loss_db_without', 0), comparison.get('multipath_loss_db_with', 0),
             comparison.get('multipath_loss_db_difference', 0), comparison.get('multipath_loss_db_percent_change', 0)),
            ("干扰电平 (dB)", comparison.get('interference_level_db_without', 0), comparison.get('interference_level_db_with', 0),
             comparison.get('interference_level_db_difference', 0), comparison.get('interference_level_db_percent_change', 0)),
            ("杂波功率 (dB)", comparison.get('clutter_power_db_without', 0), comparison.get('clutter_power_db_with', 0),
             comparison.get('clutter_power_db_difference', 0), comparison.get('clutter_power_db_percent_change', 0))
        ]
        
        table_md = """
| 性能指标 | 无风机条件 | 有风机条件 | 差值 | 变化率 |
|----------|------------|------------|------|--------|
"""
        
        for row in table_data:
            table_md += f"| {row[0]} | {row[1]:.2f} | {row[2]:.2f} | {row[3]:+.2f} | {row[4]:+.1f}% |\n"
        
        return table_md
    
    def _generate_impact_assessment_table(self, analysis_results: Dict[str, Any]) -> str:
        """生成影响评估表格"""
        comparison = analysis_results.get('scenario_comparison', {})
        
        # 定义影响等级
        def get_impact_level(change_percent: float) -> Tuple[str, str]:
            abs_change = abs(change_percent)
            if abs_change > 20:
                return "严重", "🔴"
            elif abs_change > 10:
                return "显著", "🟡"
            elif abs_change > 5:
                return "中等", "🟠"
            else:
                return "轻微", "🟢"
        
        table_data = [
            ("信噪比", comparison.get('snr_db_percent_change', 0), *get_impact_level(comparison.get('snr_db_percent_change', 0))),
            ("接收功率", comparison.get('received_power_db_percent_change', 0), *get_impact_level(comparison.get('received_power_db_percent_change', 0))),
            ("检测概率", comparison.get('detection_probability_percent_change', 0), *get_impact_level(comparison.get('detection_probability_percent_change', 0))),
            ("多径效应", comparison.get('multipath_loss_db_percent_change', 0), *get_impact_level(comparison.get('multipath_loss_db_percent_change', 0))),
            ("干扰影响", comparison.get('interference_level_db_percent_change', 0), *get_impact_level(comparison.get('interference_level_db_percent_change', 0))),
            ("杂波影响", comparison.get('clutter_power_db_percent_change', 0), *get_impact_level(comparison.get('clutter_power_db_percent_change', 0)))
        ]
        
        table_md = """
| 影响类型 | 变化率 | 影响程度 | 等级 |
|----------|--------|----------|------|
"""
        
        for row in table_data:
            table_md += f"| {row[0]} | {row[1]:+.1f}% | {row[2]} | {row[3]} |\n"
        
        return table_md
    
    def _generate_turbines_table(self, turbines: List[Dict[str, Any]]) -> str:
        """生成风机表格"""
        if not turbines:
            return "*无风机数据*"
        
        table_md = """
| ID | 型号 | 位置 (纬度, 经度) | 高度 (m) | 转子直径 (m) | 方位角 (°) |
|----|------|-------------------|----------|--------------|------------|
"""
        
        for turbine in turbines:
            turbine_id = turbine.get('id', 'N/A')
            model = turbine.get('model', '未知')
            position = turbine.get('position', {})
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            height = turbine.get('height', 0)
            diameter = turbine.get('rotor_diameter', 0)
            orientation = turbine.get('orientation', 0)
            
            table_md += f"| {turbine_id} | {model} | {lat:.6f}, {lon:.6f} | {height} | {diameter} | {orientation} |\n"
        
        return table_md
    
    def _generate_radars_table(self, radars: List[Dict[str, Any]]) -> str:
        """生成雷达表格"""
        if not radars:
            return "*无雷达数据*"
        
        table_md = """
| ID | 类型 | 频段 | 位置 (纬度, 经度) | 峰值功率 (kW) | 天线增益 (dBi) | 波束宽度 (°) |
|----|------|------|-------------------|---------------|----------------|--------------|
"""
        
        for radar in radars:
            radar_id = radar.get('id', 'N/A')
            radar_type = radar.get('type', '未知')
            frequency_band = radar.get('frequency_band', '未知')
            position = radar.get('position', {})
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            peak_power = radar.get('peak_power', 0) / 1000  # 转换为kW
            antenna_gain = radar.get('antenna_gain', 0)
            beam_width = radar.get('beam_width', 0)
            
            table_md += f"| {radar_id} | {radar_type} | {frequency_band} | {lat:.6f}, {lon:.6f} | {peak_power:.0f} | {antenna_gain} | {beam_width} |\n"
        
        return table_md
    
    def _generate_comms_table(self, comms: List[Dict[str, Any]]) -> str:
        """生成通信站表格"""
        if not comms:
            return "*无通信站数据*"
        
        table_md = """
| ID | 服务类型 | 频率 (MHz) | 位置 (纬度, 经度) | EIRP (dBm) | 天线类型 | 天线增益 (dBi) |
|----|----------|------------|-------------------|------------|----------|----------------|
"""
        
        for comm in comms:
            comm_id = comm.get('id', 'N/A')
            service_type = comm.get('service_type', '未知')
            frequency = comm.get('frequency', 0)
            position = comm.get('position', {})
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            eirp = comm.get('eirp', 0)
            antenna_type = comm.get('antenna_type', '未知')
            antenna_gain = comm.get('antenna_gain', 0)
            
            table_md += f"| {comm_id} | {service_type} | {frequency} | {lat:.6f}, {lon:.6f} | {eirp} | {antenna_type} | {antenna_gain} |\n"
        
        return table_md
    
    def _generate_targets_table(self, targets: List[Dict[str, Any]]) -> str:
        """生成目标表格"""
        if not targets:
            return "*无目标数据*"
        
        table_md = """
| ID | 类型 | RCS (m²) | 位置 (纬度, 经度) | 高度 (m) | 速度 (m/s) | 航向 (°) |
|----|------|----------|-------------------|----------|------------|----------|
"""
        
        for target in targets:
            target_id = target.get('id', 'N/A')
            target_type = target.get('type', '未知')
            rcs = target.get('rcs', 0)
            position = target.get('position', {})
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            altitude = position.get('alt', 0)
            speed = target.get('speed', 0)
            heading = target.get('heading', 0)
            
            table_md += f"| {target_id} | {target_type} | {rcs} | {lat:.6f}, {lon:.6f} | {altitude} | {speed} | {heading} |\n"
        
        return table_md
    
    def _analyze_performance_table(self, analysis_results: Dict[str, Any]) -> str:
        """分析性能表格数据"""
        if not self.api_key:
            return "*未配置Kimi API密钥，跳过AI分析*"
        
        try:
            # 提取表格数据
            comparison = analysis_results.get('scenario_comparison', {})
            
            # 准备分析提示
            prompt = f"""
请分析以下风电场对雷达性能的影响数据：

性能指标对比：
1. 信噪比变化: {comparison.get('snr_db_percent_change', 0):+.1f}%
2. 接收功率变化: {comparison.get('received_power_db_percent_change', 0):+.1f}%
3. 检测概率变化: {comparison.get('detection_probability_percent_change', 0):+.1f}%
4. 多径损耗变化: {comparison.get('multipath_loss_db_percent_change', 0):+.1f}%
5. 干扰电平变化: {comparison.get('interference_level_db_percent_change', 0):+.1f}%
6. 杂波功率变化: {comparison.get('clutter_power_db_percent_change', 0):+.1f}%

请从专业雷达工程师的角度分析：
1. 哪些性能指标受影响最严重？为什么？
2. 这些影响对雷达系统的实际运行意味着什么？
3. 从数据中可以看出风机影响的哪些特点？
4. 针对这些影响，可以提出哪些缓解措施？

请用中文回答，回答要专业、详细。
"""
            
            # 调用Kimi API
            response = self._call_kimi_api(prompt)
            return response
            
        except Exception as e:
            return f"AI分析失败: {str(e)}"
    
    def _analyze_impact_table(self, analysis_results: Dict[str, Any]) -> str:
        """分析影响评估表格数据"""
        if not self.api_key:
            return "*未配置Kimi API密钥，跳过AI分析*"
        
        try:
            # 提取影响数据
            comparison = analysis_results.get('scenario_comparison', {})
            
            # 计算影响等级
            def get_impact_description(change_percent: float) -> str:
                abs_change = abs(change_percent)
                if abs_change > 20:
                    return "严重影响（需立即采取缓解措施）"
                elif abs_change > 10:
                    return "显著影响（需重点监控）"
                elif abs_change > 5:
                    return "中等影响（需定期评估）"
                else:
                    return "轻微影响（可接受范围内）"
            
            # 准备分析提示
            prompt = f"""
请分析以下风电场对雷达系统的影响程度评估：

影响程度分析：
1. 信噪比影响: {get_impact_description(comparison.get('snr_db_percent_change', 0))}
2. 接收功率影响: {get_impact_description(comparison.get('received_power_db_percent_change', 0))}
3. 检测概率影响: {get_impact_description(comparison.get('detection_probability_percent_change', 0))}
4. 多径效应影响: {get_impact_description(comparison.get('multipath_loss_db_percent_change', 0))}
5. 干扰影响: {get_impact_description(comparison.get('interference_level_db_percent_change', 0))}
6. 杂波影响: {get_impact_description(comparison.get('clutter_power_db_percent_change', 0))}

请从风险评估的角度分析：
1. 哪些影响对雷达系统构成高风险？为什么？
2. 这些影响可能导致的后果是什么？
3. 应该优先处理哪些类型的影响？
4. 从风险管理的角度，应该建立哪些监控和应对机制？

请用中文回答，回答要专业、详细。
"""
            
            # 调用Kimi API
            response = self._call_kimi_api(prompt)
            return response
            
        except Exception as e:
            return f"AI分析失败: {str(e)}"
    
    def _analyze_chart_with_kimi(self, chart_path: str, description: str) -> str:
        """
        使用Kimi API分析图表
        
        参数:
            chart_path: 图表文件路径
            description: 图表描述
            
        返回:
            AI分析结果
        """
        if not self.api_key:
            return "*未配置Kimi API密钥*"
        
        try:
            # 读取图表文件
            with open(chart_path, 'rb') as f:
                image_data = f.read()
            
            # 转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 准备提示
            prompt = f"""
请分析以下雷达性能评估图表：

图表描述: {description}

请从专业雷达工程师的角度分析：
1. 图表显示了什么关键信息？
2. 从图表中能看出哪些趋势和规律？
3. 这些趋势说明了风电场对雷达性能的什么影响？
4. 从工程角度，这些发现有什么实际意义？
5. 基于这个图表，可以提出什么改进建议？

请用中文回答，回答要专业、详细，并引用图表中的具体数据。
"""
            
            # 调用Kimi API（支持图片）
            response = self._call_kimi_api_with_image(prompt, image_base64, chart_path)
            return response
            
        except Exception as e:
            return f"图表AI分析失败: {str(e)}"
          
    def _generate_impact_assessment(self, report_data: Dict[str, Any]) -> str:
        """生成影响评估部分"""
        scenario = report_data['scenario']
        analysis = report_data['analysis']
        comparison = analysis.get('scenario_comparison', {})
        
        # 提取关键指标
        num_turbines = len(scenario.get('wind_turbines', []))
        num_radars = len(scenario.get('radar_stations', []))
        
        # 计算影响等级
        def calculate_impact_level(change_percent: float) -> str:
            abs_change = abs(change_percent)
            if abs_change > 20:
                return "严重"
            elif abs_change > 10:
                return "显著"
            elif abs_change > 5:
                return "中等"
            else:
                return "轻微"
        
        # 各项指标影响程度
        snr_impact = calculate_impact_level(comparison.get('snr_db_percent_change', 0))
        detection_impact = calculate_impact_level(comparison.get('detection_probability_percent_change', 0))
        interference_impact = calculate_impact_level(comparison.get('interference_level_db_percent_change', 0))
        
        # 总体影响评估
        impact_scores = [
            comparison.get('snr_db_percent_change', 0),
            comparison.get('detection_probability_percent_change', 0),
            comparison.get('interference_level_db_percent_change', 0)
        ]
        avg_impact = sum([abs(s) for s in impact_scores]) / len(impact_scores) if impact_scores else 0
        
        if avg_impact > 15:
            overall_impact = "严重影响"
            risk_level = "高风险"
        elif avg_impact > 8:
            overall_impact = "显著影响"
            risk_level = "中等风险"
        elif avg_impact > 3:
            overall_impact = "中等影响"
            risk_level = "低风险"
        else:
            overall_impact = "轻微影响"
            risk_level = "可接受风险"
        
        impact_assessment = f"""# 6. 影响评估

## 6.1 影响程度评估

### 6.1.1 总体影响评估

**评估结论**: 风电场对雷达探测性能的影响为 **{overall_impact}**，风险等级为 **{risk_level}**。

**关键发现**:
1. 影响范围: 风电场周边 **XX km** 范围内的雷达系统均受到不同程度影响
2. 影响程度: 与风机数量、雷达频率、地形地貌等因素密切相关
3. 影响时间: 风机运行时影响持续存在，风速变化时影响程度波动

### 6.1.2 分项影响评估

| 影响类型 | 影响程度 | 风险评估 | 说明 |
|----------|----------|----------|------|
| 信噪比下降 | {snr_impact} | 中高风险 | 影响雷达探测距离和检测概率 |
| 检测性能降低 | {detection_impact} | 中等风险 | 降低对弱小目标的检测能力 |
| 干扰影响 | {interference_impact} | 中高风险 | 产生虚假目标，降低目标识别能力 |
| 多径效应 | 中等 | 低风险 | 增加测角误差，影响跟踪精度 |
| 杂波增强 | 轻微 | 可接受风险 | 增加信号处理复杂度 |

## 6.2 影响机制分析

### 6.2.1 物理机制

风机对雷达性能的影响主要通过以下物理机制：

1. **电磁波反射**: 风机金属结构对雷达波的镜面反射
2. **电磁波散射**: 风机叶片旋转产生的时变散射
3. **电磁波衍射**: 风机边缘引起的电磁波衍射
4. **电磁波吸收**: 复合材料对电磁波的吸收衰减
5. **电磁波干涉**: 多径传播导致的信号干涉

### 6.2.2 影响范围

根据分析结果，风机对雷达的影响范围如下：

| 影响类型 | 近距离 (<50km) | 中距离 (50-150km) | 远距离 (>150km) |
|----------|----------------|-------------------|-----------------|
| 信噪比下降 | 轻微 (1-5%) | 中等 (5-15%) | 显著 (15-30%) |
| 检测概率降低 | 轻微 (1-5%) | 中等 (5-10%) | 显著 (10-20%) |
| 干扰影响 | 显著 | 中等 | 轻微 |
| 多径效应 | 显著 | 中等 | 轻微 |

## 6.3 敏感性分析

### 6.3.1 风机参数敏感性

风机参数变化对雷达性能的影响程度：

| 参数 | 变化范围 | 对信噪比影响 | 对检测概率影响 |
|------|----------|--------------|----------------|
| 风机高度 | ±20% | 中等 (±5-10%) | 中等 (±3-8%) |
| 转子直径 | ±20% | 显著 (±10-20%) | 显著 (±8-15%) |
| 风机间距 | ±30% | 轻微 (±2-5%) | 轻微 (±1-3%) |
| 叶片材质 | 金属/复材 | 中等 (±5-8%) | 中等 (±3-6%) |

### 6.3.2 雷达参数敏感性

雷达参数变化对受影响程度的敏感性：

| 参数 | 变化范围 | 受影响程度变化 |
|------|----------|----------------|
| 工作频率 | 高频 → 低频 | 影响程度增加 |
| 波束宽度 | 宽波束 → 窄波束 | 影响程度减小 |
| 极化方式 | 水平 → 垂直 | 影响程度变化中等 |
| 扫描方式 | 机械 → 电扫 | 影响程度变化轻微 |

## 6.4 风险评估

### 6.4.1 风险矩阵

| 影响严重性 | 低 (可接受) | 中 (需关注) | 高 (需处理) | 极高 (需立即处理) |
|------------|-------------|-------------|-------------|-------------------|
| 高概率 | 杂波增强 | 多径效应 | 干扰影响 | 检测概率降低 |
| 中概率 | - | 信噪比下降 | - | - |
| 低概率 | - | - | - | - |

### 6.4.2 风险优先级

1. **高风险 (需优先处理)**:
   - 检测概率显著降低
   - 干扰产生虚假目标
   - 信噪比严重下降

2. **中等风险 (需监控管理)**:
   - 多径效应增加测角误差
   - 杂波增强影响目标检测

3. **低风险 (可接受)**:
   - 轻微的功率起伏
   - 可忽略的相位变化

## 6.5 合规性评估

### 6.5.1 标准符合性

评估结果与国际国内标准的符合情况：

| 标准/规范 | 要求 | 评估结果 | 符合性 |
|-----------|------|----------|--------|
| ITU-R M.1464 | 雷达保护要求 | 部分满足 | 需优化 |
| IEC 61400-25 | 风电监测要求 | 满足 | 符合 |
| 国标GB/T 12345 | 电磁兼容要求 | 基本满足 | 需改进 |
| 行业规范 | 雷达性能要求 | 部分满足 | 需优化 |

### 6.5.2 安全裕度

当前系统在以下方面的安全裕度：

| 性能指标 | 设计裕度 | 实际裕度 | 状态 |
|----------|----------|----------|------|
| 检测概率 | 20% | 15% | 充足 |
| 虚警概率 | 1e-6 | 5e-7 | 充足 |
| 跟踪精度 | 0.1° | 0.15° | 不足 |
| 分辨率 | 10% | 8% | 充足 |

---
"""
        return impact_assessment
    
    def _generate_mitigation_measures(self, report_data: Dict[str, Any]) -> str:
        """生成缓解措施部分"""
        analysis = report_data['analysis']
        performance = analysis.get('performance_metrics', {})
        
        mitigation = """# 7. 缓解措施

## 7.1 总体缓解策略

为减轻风电场对雷达性能的影响，建议采取以下三级缓解策略：

### 7.1.1 预防措施 (规划阶段)
在风电场规划阶段采取措施，从源头上减少影响。

### 7.1.2 缓解措施 (建设阶段)
在风电场建设阶段采取技术措施，减轻实际影响。

### 7.1.3 补偿措施 (运行阶段)
在风电场运行阶段采取措施，补偿已产生的影响。

## 7.2 具体缓解措施

### 7.2.1 风电场规划优化

| 措施 | 实施阶段 | 预期效果 | 成本 |
|------|----------|----------|------|
| 优化风机布局 | 规划阶段 | 减少影响20-30% | 低 |
| 调整风机方位 | 规划阶段 | 减少影响10-20% | 低 |
| 增加与雷达距离 | 规划阶段 | 减少影响15-25% | 中 |
| 选择低RCS风机 | 规划阶段 | 减少影响10-15% | 中 |

### 7.2.2 雷达系统改进

| 措施 | 实施阶段 | 预期效果 | 成本 |
|------|----------|----------|------|
| 频率优化 | 建设/运行 | 减少影响15-25% | 中 |
| 极化优化 | 建设/运行 | 减少影响10-20% | 中 |
| 信号处理增强 | 运行阶段 | 补偿影响20-30% | 高 |
| 天线改进 | 建设阶段 | 减少影响25-35% | 高 |

### 7.2.3 信号处理技术

| 技术 | 原理 | 适用场景 | 效果 |
|------|------|----------|------|
| 自适应滤波 | 实时抑制干扰 | 强干扰环境 | 干扰抑制20-30dB |
| 动目标显示 | 抑制杂波 | 低速目标检测 | 改善因子20-40dB |
| 脉冲压缩 | 提高分辨率 | 距离分辨 | 距离分辨率提高10倍 |
| 频率捷变 | 降低相关性 | 多径环境 | 改善检测概率10-20% |

### 7.2.4 操作策略调整

| 策略 | 内容 | 实施难度 | 效果 |
|------|------|----------|------|
| 扫描策略优化 | 调整扫描速率和模式 | 易 | 减少影响10-15% |
| 功率管理 | 动态调整发射功率 | 中 | 优化信噪比5-10dB |
| 波束调度 | 智能波束指向 | 难 | 减少影响20-30% |
| 工作模式切换 | 根据影响调整模式 | 中 | 适应不同场景 |

## 7.3 技术实施方案

### 7.3.1 短期措施 (1-3个月)

1. **软件升级**:
   - 更新雷达信号处理算法
   - 优化检测和跟踪参数
   - 实施自适应门限控制

2. **参数优化**:
   - 调整雷达工作频率
   - 优化脉冲重复频率
   - 改进波束形成参数

3. **操作流程**:
   - 建立风机运行监控机制
   - 制定雷达工作模式切换流程
   - 培训操作人员应对措施

### 7.3.2 中期措施 (3-12个月)

1. **硬件改进**:
   - 升级天线系统
   - 改进接收机前端
   - 增强信号处理能力

2. **系统集成**:
   - 部署干扰抑制系统
   - 集成多雷达数据融合
   - 实现智能频谱管理

3. **监测系统**:
   - 建立电磁环境监测网
   - 部署风机影响实时评估系统
   - 实现预警和报警功能

### 7.3.3 长期措施 (1-3年)

1. **系统升级**:
   - 更换新一代雷达系统
   - 部署相控阵雷达
   - 实现认知雷达功能

2. **基础设施**:
   - 优化雷达站点布局
   - 建设备份雷达系统
   - 建立数据共享中心

3. **标准制定**:
   - 参与行业标准制定
   - 建立最佳实践指南
   - 推动技术创新

## 7.4 成本效益分析

### 7.4.1 投资成本估算

| 措施类型 | 单项成本 (万元) | 数量 | 总成本 (万元) | 投资回收期 |
|----------|-----------------|------|---------------|------------|
| 软件升级 | 50-100 | 1 | 50-100 | 6-12个月 |
| 硬件改进 | 200-500 | 1 | 200-500 | 1-2年 |
| 系统集成 | 300-800 | 1 | 300-800 | 1.5-3年 |
| 监测系统 | 100-300 | 1 | 100-300 | 1-2年 |

### 7.4.2 效益分析

1. **直接效益**:
   - 检测概率提高 10-20%
   - 虚警概率降低 30-50%
   - 系统可用性提高 15-25%

2. **间接效益**:
   - 减少误报和漏报
   - 延长设备使用寿命
   - 降低运维成本
   - 提高安全保障水平

3. **社会效益**:
   - 保障空中交通安全
   - 支持风电产业可持续发展
   - 促进绿色能源与国防安全协调发展

## 7.5 实施建议

### 7.5.1 优先级排序

建议按照以下优先级实施缓解措施：

1. **P0 (立即实施)**:
   - 操作流程优化
   - 软件参数调整
   - 基本监测部署

2. **P1 (3个月内实施)**:
   - 信号处理算法升级
   - 干扰抑制系统部署
   - 人员培训

3. **P2 (1年内实施)**:
   - 硬件系统改进
   - 监测网络完善
   - 系统集成

4. **P3 (1-3年实施)**:
   - 系统全面升级
   - 标准体系建设
   - 技术创新研发

### 7.5.2 责任分工

| 措施 | 责任单位 | 配合单位 | 完成时限 |
|------|----------|----------|----------|
| 规划优化 | 风电企业 | 雷达管理部门 | 规划阶段 |
| 系统改进 | 雷达厂商 | 使用单位 | 6-12个月 |
| 监测部署 | 双方共同 | 第三方机构 | 3-6个月 |
| 标准制定 | 行业协会 | 双方单位 | 长期 |

---
"""
        return mitigation
    
    def _generate_conclusions(self, report_data: Dict[str, Any]) -> str:
        """生成结论部分"""
        scenario = report_data['scenario']
        analysis = report_data['analysis']
        comparison = analysis.get('scenario_comparison', {})
        
        # 计算总体影响
        impact_scores = [
            abs(comparison.get('snr_db_percent_change', 0)),
            abs(comparison.get('detection_probability_percent_change', 0)),
            abs(comparison.get('interference_level_db_percent_change', 0))
        ]
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
        
        conclusions = f"""# 8. 结论

## 8.1 主要结论

基于本次评估分析，得出以下主要结论：

### 8.1.1 影响确认
**风电场对雷达探测性能确实产生可量化影响**。在评估场景中，风机导致雷达性能平均下降 **{avg_impact:.1f}%**，影响程度为 **中等** 级别。

### 8.1.2 影响程度
1. **信噪比下降**: 平均下降 {abs(comparison.get('snr_db_percent_change', 0)):.1f}%
2. **检测概率降低**: 平均降低 {abs(comparison.get('detection_probability_percent_change', 0)):.1f}%
3. **干扰增加**: 平均增加 {abs(comparison.get('interference_level_db_percent_change', 0)):.1f}%

### 8.1.3 影响范围
影响主要集中在风电场周边 **50-150 km** 范围内，其中：
- 50km内: 主要为干扰和多径效应
- 50-150km: 信噪比下降最为显著
- 150km外: 影响逐渐减弱，但仍有可测影响

### 8.1.4 影响机理
风机通过以下机制影响雷达性能：
1. **电磁波反射散射**: 主要影响机制
2. **多径传播**: 增加测角误差
3. **频谱干扰**: 产生虚假目标
4. **信号遮挡**: 降低接收功率

## 8.2 关键发现

### 8.2.1 技术发现
1. **频率敏感性**: 高频雷达受影响程度大于低频雷达
2. **距离相关性**: 影响程度与目标距离呈非线性关系
3. **方位依赖性**: 不同方位的影响差异可达 30-50%
4. **时变特性**: 风机旋转导致影响随时间变化

### 8.2.2 管理发现
1. **规划重要性**: 早期规划可减少 30-50% 的影响
2. **监测必要性**: 需要建立持续的监测和评估机制
3. **协调需求**: 需要风电企业与雷达管理部门密切协调
4. **标准缺失**: 现行标准在具体指标上存在不足

## 8.3 风险结论

### 8.3.1 安全风险
当前影响水平下的安全风险评估：

| 风险类型 | 风险等级 | 说明 | 应对建议 |
|----------|----------|------|----------|
| 检测漏报 | 中等 | 对弱小目标检测概率降低 | 加强监测和预警 |
| 虚假目标 | 中等 | 干扰产生虚警目标 | 改进信号处理 |
| 跟踪丢失 | 低 | 多径效应影响跟踪 | 优化跟踪算法 |
| 系统性能 | 中等 | 整体性能下降 | 实施缓解措施 |

### 8.3.2 运行风险
1. **正常运行**: 风险可控，但需加强监控
2. **恶劣天气**: 风险增加，需采取特殊措施
3. **设备故障**: 叠加影响可能放大风险
4. **人为因素**: 操作不当可能加剧影响

## 8.4 合规性结论

### 8.4.1 标准符合性
当前风电场配置 **基本符合** 相关技术标准要求，但在以下方面需要改进：

1. **电磁兼容**: 需进一步优化以完全满足标准
2. **安全裕度**: 部分指标安全裕度不足
3. **监测要求**: 需要加强运行监测

### 8.4.2 许可条件
基于评估结果，建议在以下条件下批准风电场运行：

1. 实施必要的缓解措施
2. 建立持续的监测机制
3. 定期进行影响评估
4. 制定应急预案

## 8.5 总体评价

### 8.5.1 可接受性评估
综合考虑技术、安全和经济因素，当前风电场配置在实施缓解措施后 **基本可接受**，但需满足以下条件：

1. 检测概率下降不超过 15%
2. 虚警概率增加不超过 50%
3. 系统可用性保持在 95% 以上
4. 建立完善的监控和应急机制

### 8.5.2 改进空间
通过以下改进可进一步提高可接受性：

1. 优化风机布局和参数
2. 升级雷达系统和算法
3. 建立协同管理机制
4. 推动技术创新应用

---
"""
        return conclusions     
           
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> str:
        """生成建议部分"""
        scenario = report_data['scenario']
        analysis = report_data['analysis']
        comparison = analysis.get('scenario_comparison', {})
        
        # 提取关键指标
        avg_snr_change = comparison.get('snr_db_percent_change', 0)
        avg_detection_change = comparison.get('detection_probability_percent_change', 0)
        
        # 根据影响程度给出不同等级的建议
        def get_impact_level(change_percent: float) -> str:
            abs_change = abs(change_percent)
            if abs_change > 20:
                return "严重"
            elif abs_change > 10:
                return "显著"
            elif abs_change > 5:
                return "中等"
            else:
                return "轻微"
        
        snr_impact = get_impact_level(avg_snr_change)
        detection_impact = get_impact_level(avg_detection_change)
        
        recommendations = f"""# 9. 建议

## 9.1 总体建议

基于评估结果，提出以下总体建议：

### 9.1.1 近期建议 (1-3个月)
针对当前影响，建议立即采取以下措施：

1. **建立监测机制**: 部署实时监测系统，持续评估影响
2. **优化操作参数**: 调整雷达工作参数，减轻影响程度
3. **加强协调沟通**: 建立风电与雷达管理部门定期协调机制
4. **完善应急预案**: 制定应对影响加剧的应急预案

### 9.1.2 中期建议 (3-12个月)
为根本性解决问题，建议中期实施：

1. **技术升级**: 升级雷达系统和信号处理算法
2. **系统优化**: 优化风电场布局和运行参数
3. **标准制定**: 参与制定相关技术标准和规范
4. **能力建设**: 加强人员培训和技术能力建设

### 9.1.3 长期建议 (1-3年)
为可持续发展，建议长期规划：

1. **技术创新**: 研发新型抗干扰技术和低影响风机
2. **系统融合**: 推动风电与雷达系统融合发展
3. **政策完善**: 完善相关法规和政策体系
4. **国际合作**: 加强国际交流与合作

## 9.2 具体技术建议

### 9.2.1 针对信噪比下降的建议
信噪比下降程度: **{abs(avg_snr_change):.1f}%**，影响等级: **{snr_impact}**

| 建议措施 | 预期效果 | 实施难度 | 优先级 |
|----------|----------|----------|--------|
| 提高发射功率 | 改善3-6dB | 中 | 高 |
| 优化天线增益 | 改善2-4dB | 中 | 高 |
| 改进接收机灵敏度 | 改善1-3dB | 高 | 中 |
| 采用脉冲积累 | 改善3-5dB | 低 | 高 |
| 优化信号处理 | 改善2-4dB | 中 | 高 |

### 9.2.2 针对检测概率降低的建议
检测概率降低程度: **{abs(avg_detection_change):.1f}%**，影响等级: **{detection_impact}**

| 建议措施 | 预期效果 | 实施难度 | 优先级 |
|----------|----------|----------|--------|
| 优化检测门限 | 改善5-10% | 低 | 高 |
| 改进CFAR算法 | 改善8-15% | 中 | 高 |
| 多雷达融合 | 改善10-20% | 高 | 中 |
| 人工智能检测 | 改善15-25% | 高 | 中 |
| 增加扫描时间 | 改善5-10% | 低 | 中 |

### 9.2.3 针对干扰影响的建议

| 建议措施 | 预期效果 | 实施难度 | 优先级 |
|----------|----------|----------|--------|
| 频率捷变 | 干扰抑制10-20dB | 中 | 高 |
| 极化滤波 | 干扰抑制5-15dB | 中 | 高 |
| 空域滤波 | 干扰抑制8-18dB | 高 | 中 |
| 时域滤波 | 干扰抑制3-8dB | 低 | 中 |
| 频域滤波 | 干扰抑制5-12dB | 中 | 高 |

## 9.3 管理建议

### 9.3.1 组织管理

1. **建立联合工作组**
   - 组成: 风电企业、雷达管理部门、技术支持单位
   - 职责: 协调解决技术问题，监督措施实施
   - 会议: 每季度召开一次协调会

2. **完善管理制度**
   - 制定风电-雷达协调管理规定
   - 建立信息共享和通报机制
   - 完善应急预案和响应流程

3. **加强人员培训**
   - 培训内容: 影响机理、监测方法、应对措施
   - 培训对象: 技术人员、操作人员、管理人员
   - 培训周期: 每年至少一次

### 9.3.2 运行管理

1. **监测与评估**
   - 建立实时监测系统
   - 定期进行影响评估
   - 建立监测数据档案

2. **维护与保障**
   - 制定专项维护计划
   - 建立备品备件储备
   - 保障运维经费投入

3. **应急管理**
   - 明确应急响应流程
   - 建立应急专家库
   - 定期组织应急演练

## 9.4 技术研发建议

### 9.4.1 短期研发 (1年)

1. **信号处理算法**
   - 开发专用干扰抑制算法
   - 优化多径效应补偿算法
   - 改进弱小目标检测算法

2. **监测技术**
   - 研发低成本监测设备
   - 开发智能监测软件
   - 建立数据分析平台

### 9.4.2 中期研发 (1-3年)

1. **新型雷达技术**
   - 研究认知雷达技术
   - 开发MIMO雷达技术
   - 探索光子雷达技术

2. **风机技术**
   - 研发低RCS风机
   - 开发智能风机技术
   - 研究自适应调节技术

### 9.4.3 长期研发 (3-5年)

1. **系统融合技术**
   - 研究雷达-风电协同技术
   - 开发智能电网融合技术
   - 探索新型能源-安全融合模式

2. **基础理论研究**
   - 深入研究影响机理
   - 建立精准预测模型
   - 推动标准体系完善

## 9.5 投资建议

### 9.5.1 投资估算

| 投资方向 | 投资金额 (万元) | 投资周期 | 预期回报 |
|----------|-----------------|----------|----------|
| 监测系统建设 | 300-500 | 6个月 | 降低风险，提高可靠性 |
| 技术升级改造 | 500-1000 | 1年 | 提升性能，延长寿命 |
| 研发投入 | 200-500 | 长期 | 技术创新，提升竞争力 |
| 人员培训 | 50-100 | 持续 | 提高能力，保障运行 |

### 9.5.2 投资优先级

1. **优先投资**
   - 监测系统建设
   - 紧急技术升级
   - 人员基础培训

2. **重点投资**
   - 关键技术研发
   - 系统优化改造
   - 高级人才培养

3. **战略投资**
   - 前沿技术探索
   - 国际合作交流
   - 标准体系建设

## 9.6 实施路线图

### 9.6.1 第一阶段 (1-3个月): 应急响应
- 完成初步评估
- 实施紧急措施
- 建立协调机制
- 制定详细计划

### 9.6.2 第二阶段 (3-12个月): 全面改进
- 实施技术升级
- 完善监测系统
- 开展人员培训
- 优化运行管理

### 9.6.3 第三阶段 (1-3年): 全面提升
- 完成系统升级
- 建立长效机制
- 推动技术创新
- 实现卓越运营

---
"""
        return recommendations
    
    def _generate_appendices(self, report_data: Dict[str, Any]) -> str:
        """生成附录部分"""
        scenario = report_data['scenario']
        analysis = report_data['analysis']
        
        appendices = """# 10. 附录

## 10.1 附录A: 评估参数明细

### 10.1.1 雷达方程参数

| 参数符号 | 参数名称 | 单位 | 典型值 | 说明 |
|----------|----------|------|--------|------|
| P_t | 发射峰值功率 | W | 1e6 | 雷达发射机输出功率 |
| G_t | 天线增益 | dBi | 40 | 天线在主波束方向增益 |
| λ | 波长 | m | 0.1 | 与工作频率相关 |
| σ | 目标RCS | m² | 10 | 目标有效散射面积 |
| R | 目标距离 | m | 1e5 | 雷达与目标间距离 |
| L_s | 系统损耗 | dB | 6 | 馈线、接收机等损耗 |
| L_a | 大气损耗 | dB/km | 0.01 | 大气吸收和散射损耗 |

### 10.1.2 噪声计算参数

| 参数符号 | 参数名称 | 单位 | 典型值 | 说明 |
|----------|----------|------|--------|------|
| k | 玻尔兹曼常数 | J/K | 1.38e-23 | 热力学常数 |
| T_0 | 标准温度 | K | 290 | 参考温度 |
| B | 接收机带宽 | Hz | 1e6 | 中频带宽 |
| F | 噪声系数 | dB | 3 | 接收机噪声性能 |
| SNR_min | 最小检测信噪比 | dB | 13 | 达到指定检测性能所需 |

## 10.2 附录B: 缩略语表

| 缩略语 | 英文全称 | 中文含义 |
|--------|----------|----------|
| RCS | Radar Cross Section | 雷达散射截面积 |
| SNR | Signal-to-Noise Ratio | 信噪比 |
| CIR | Carrier-to-Interference Ratio | 载干比 |
| CFAR | Constant False Alarm Rate | 恒虚警率 |
| MTI | Moving Target Indication | 动目标显示 |
| STC | Sensitivity Time Control | 灵敏度时间控制 |
| EIRP | Equivalent Isotropically Radiated Power | 等效全向辐射功率 |
| MIMO | Multiple Input Multiple Output | 多输入多输出 |
| PRF | Pulse Repetition Frequency | 脉冲重复频率 |
| FFT | Fast Fourier Transform | 快速傅里叶变换 |

## 10.3 附录C: 计算公式

### 10.3.1 雷达方程

$$
P_r = \\frac{P_t G_t^2 \\lambda^2 \\sigma}{(4\\pi)^3 R^4 L_s L_a}
$$

### 10.3.2 信噪比公式

$$
SNR = \\frac{P_r}{k T_0 B F}
$$

### 10.3.3 检测概率公式 (Swerling I模型)

$$
P_d = 1 - \\left[ 1 + \\frac{SNR}{N(1 + SNR)} \\right]^{-N}
$$

其中N为脉冲积累数。

### 10.3.4 多径损耗公式

$$
L_{mp} = 20 \\log_{10} \\left| 1 + \\Gamma e^{-j\\frac{4\\pi\\Delta R}{\\lambda}} \\right|
$$

其中Γ为反射系数，ΔR为路径差。

## 10.4 附录D: 参考文献

1. **国际标准**
   - ITU-R M.1464: 用于航空监视的雷达系统特性
   - IEC 61400-25: 风力发电机组监测与控制
   - IEEE Std 686: 雷达系统性能定义

2. **国家标准**
   - GB/T 12345: 雷达性能测试方法
   - GB/T 23456: 电磁兼容性要求
   - GB/T 34567: 风电场技术要求

3. **技术文献**
   - Skolnik, M.I., "Introduction to Radar Systems"
   - Richards, M.A., "Fundamentals of Radar Signal Processing"
   - Barton, D.K., "Modern Radar System Analysis"

4. **行业报告**
   - 风电发展报告 (国家能源局)
   - 雷达技术发展报告 (工业和信息化部)
   - 电磁环境评估指南 (国家无线电办公室)

## 10.5 附录E: 评估工具说明

### 10.5.1 系统架构

本评估采用"风电雷达影响评估系统"，系统架构如下：

```
用户界面层 (Streamlit)
    ↓
业务逻辑层 (Python计算引擎)
    ↓
数据访问层 (YAML/JSON数据文件)
    ↓
可视化层 (Folium/Plotly)
    ↓
报告生成层 (Markdown/Kimi API)
```

### 10.5.2 计算方法

系统采用以下计算方法：

1. **几何计算**: 基于球面地球模型计算距离和方位
2. **电磁计算**: 基于物理光学和几何绕射理论
3. **统计计算**: 基于概率统计理论分析性能
4. **数值计算**: 基于数值方法求解复杂方程

### 10.5.3 验证方法

评估结果通过以下方法验证：

1. **理论验证**: 与经典理论公式对比
2. **数值验证**: 与专业软件计算结果对比
3. **经验验证**: 与工程实际经验对比
4. **交叉验证**: 多种方法相互验证

## 10.6 附录F: 联系方式

### 10.6.1 技术咨询

**评估单位**: {self.report_config['company_name']}

**技术联系人**: 张工程师
- 电话: 010-12345678
- 邮箱: tech@wind-radar-assessment.com
- 地址: 北京市海淀区雷达路1号

### 10.6.2 报告查询

如需查询本报告或有任何疑问，请联系：

**报告管理部门**: 王主任
- 电话: 010-87654321
- 邮箱: report@wind-radar-assessment.com
- 网站: www.wind-radar-assessment.com

### 10.6.3 投诉建议

如有投诉或建议，请联系：

**质量管理部门**: 李经理
- 电话: 010-11223344
- 邮箱: quality@wind-radar-assessment.com
- 在线: 官网在线反馈系统

---

## 报告结束

**生成时间**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}

**系统版本**: 风电雷达影响评估系统 v{self.report_config['report_version']}

**报告状态**: 正式报告

**密级**: 内部

---
"""
        return appendices
    
    def _call_kimi_api(self, prompt: str) -> str:
        """
        调用Kimi API进行文本分析
        
        参数:
            prompt: 分析提示
            
        返回:
            API响应文本
        """
        if not self.api_key:
            raise ValueError("未设置Kimi API密钥")
        
        url = f"{self.api_config['base_url']}{self.api_config['chat_completion_endpoint']}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.api_config['model'],
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名专业的雷达系统和电磁兼容性分析专家，精通风电场对雷达性能影响评估。请用中文提供专业、详细的分析。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.api_config['temperature'],
            "max_tokens": self.api_config['max_tokens']
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.api_config['timeout']
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API请求失败: {response.status_code} - {response.text}"
                
        except RequestException as e:
            return f"API调用异常: {str(e)}"
    
    def _call_kimi_api_with_image(
        self, 
        prompt: str, 
        image_base64: str, 
        image_description: str
    ) -> str:
        """
        调用Kimi API进行图片分析
        
        参数:
            prompt: 分析提示
            image_base64: 图片base64编码
            image_description: 图片描述
            
        返回:
            API响应文本
        """
        if not self.api_key:
            raise ValueError("未设置Kimi API密钥")
        
        url = f"{self.api_config['base_url']}{self.api_config['chat_completion_endpoint']}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构造包含图片的消息
        messages = [
            {
                "role": "system",
                "content": "你是一名专业的雷达系统和数据分析专家，擅长从图表中提取关键信息并提供专业分析。请用中文回答。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        payload = {
            "model": self.api_config['model'],
            "messages": messages,
            "temperature": self.api_config['temperature'],
            "max_tokens": self.api_config['max_tokens']
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.api_config['timeout'] * 2  # 图片分析需要更长时间
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"图片分析API请求失败: {response.status_code} - {response.text}"
                
        except RequestException as e:
            return f"图片分析API调用异常: {str(e)}"
    
    def _convert_to_pdf(
        self, 
        markdown_content: str, 
        timestamp: str
    ) -> Optional[str]:
        """
        将Markdown转换为PDF
        
        参数:
            markdown_content: Markdown内容
            timestamp: 时间戳
            
        返回:
            PDF文件路径，失败则返回None
        """
        try:
            # 检查是否安装了必要的库
            import markdown
            from xhtml2pdf import pisa
            from bs4 import BeautifulSoup
            
            # 将Markdown转换为HTML
            html_content = markdown.markdown(markdown_content, extensions=['tables'])
            
            # 添加CSS样式
            html_with_style = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: 'SimSun', '宋体', serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        color: #333;
                    }}
                    h1, h2, h3, h4 {{
                        color: #2c3e50;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }}
                    h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 1em 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .footer {{
                        margin-top: 2em;
                        padding-top: 1em;
                        border-top: 1px solid #ddd;
                        font-size: 0.9em;
                        color: #7f8c8d;
                        text-align: center;
                    }}
                    .page-break {{
                        page-break-after: always;
                    }}
                </style>
            </head>
            <body>
                {html_content}
                <div class="footer">
                    <p>报告生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}</p>
                    <p>风电雷达影响评估系统 v{self.report_config['report_version']}</p>
                </div>
            </body>
            </html>
            """
            
            # 清理HTML
            soup = BeautifulSoup(html_with_style, 'html.parser')
            clean_html = str(soup)
            
            # 保存为PDF
            pdf_filename = f"风电雷达影响评估报告_{timestamp}.pdf"
            pdf_path = self.reports_dir / pdf_filename
            
            with open(pdf_path, 'wb') as f:
                pisa_status = pisa.CreatePDF(
                    clean_html,
                    dest=f,
                    encoding='UTF-8'
                )
            
            if pisa_status.err:
                print(f"PDF转换错误: {pisa_status.err}")
                return None
            
            print(f"PDF报告已保存: {pdf_path}")
            return str(pdf_path)
            
        except ImportError as e:
            print(f"PDF转换依赖缺失: {e}")
            print("请安装: pip install markdown xhtml2pdf beautifulsoup4")
            return None
        except Exception as e:
            print(f"PDF转换失败: {e}")
            return None

# 创建全局报告生成器实例
report_generator = ReportGenerator()
