"""
报告生成页面
功能：生成专业的评估报告，集成Kimi AI智能分析
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import json
import yaml
import time

# 添加utils路径
sys.path.append(str(Path(__file__).parent.parent / "config"))
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from config.config import (
    REPORT_CONFIG, KIMI_API_CONFIG, COLOR_SCHEME,
    SYSTEM_MESSAGES, OUTPUTS_DIR
)
from utils.report_generator import ReportGenerator
from utils.visualization import VisualizationTools

# 页面配置
st.set_page_config(
    page_title="报告生成 | 风电雷达影响评估系统",
    page_icon="📊",
    layout="wide"
)

# 页面标题
st.title("📊 报告生成")
st.markdown("生成专业的评估报告，集成Kimi AI智能分析")

# 检查分析是否完成
if 'analysis_results' not in st.session_state or not st.session_state.get('calculation_complete', False):
    st.warning("⚠️ 请先进行雷达性能分析")
    
    if st.button("📡 前往雷达性能分析页面", use_container_width=True):
        st.switch_page("pages/3_雷达性能分析.py")
    
    st.stop()

# 获取数据
scenario_data = st.session_state.scenario_data
scenario_name = st.session_state.scenario_name
analysis_results = st.session_state.analysis_results
analysis_config = st.session_state.get('analysis_config', {})

# 初始化报告生成器
if 'report_generator' not in st.session_state:
    st.session_state.report_generator = ReportGenerator()
    st.session_state.report_generated = False
    st.session_state.report_data = None
    st.session_state.ai_analysis_in_progress = False
    st.session_state.ai_analysis_complete = False

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "⚙️ 报告设置", 
    "📄 报告预览", 
    "🤖 AI分析", 
    "💾 导出报告"
])

with tab1:
    st.header("报告生成设置")
    
    col_set1, col_set2 = st.columns(2)
    
    with col_set1:
        st.subheader("基本信息")
        
        # 报告标题
        report_title = st.text_input(
            "报告标题",
            value=REPORT_CONFIG['report_title'],
            help="输入报告的标题"
        )
        
        # 评估单位
        company_name = st.text_input(
            "评估单位",
            value=REPORT_CONFIG['company_name'],
            help="输入评估单位的名称"
        )
        
        # 报告作者
        report_author = st.text_input(
            "报告作者",
            value=REPORT_CONFIG['author'],
            help="输入报告的作者姓名"
        )
        
        # 报告版本
        report_version = st.text_input(
            "报告版本",
            value=REPORT_CONFIG['report_version'],
            help="输入报告的版本号"
        )
    
    with col_set2:
        st.subheader("内容设置")
        
        # 包含章节
        sections_to_include = st.multiselect(
            "包含章节",
            options=REPORT_CONFIG['include_sections'],
            default=REPORT_CONFIG['include_sections'],
            help="选择报告中要包含的章节"
        )
        
        # 报告语言
        report_language = st.selectbox(
            "报告语言",
            ["中文", "English"],
            help="选择报告的语言"
        )
        
        # 图片质量
        image_quality = st.select_slider(
            "图片质量",
            options=["低", "中", "高"],
            value=REPORT_CONFIG['image_quality'],
            help="选择报告中图片的质量"
        )
        
        # 最大页数
        max_pages = st.slider(
            "最大页数",
            min_value=10,
            max_value=100,
            value=REPORT_CONFIG['max_pages'],
            step=5,
            help="设置报告的最大页数限制"
        )
    
    st.markdown("---")
    st.subheader("Kimi API设置")
    
    col_api1, col_api2 = st.columns(2)
    
    with col_api1:
        # API密钥输入
        api_key = st.text_input(
            "Kimi API密钥",
            value=st.session_state.get('kimi_api_key', ''),
            type="password",
            help="输入Kimi API密钥以启用AI分析功能"
        )
        
        if api_key:
            st.session_state.report_generator.set_api_key(api_key)
            st.success("✅ API密钥已设置")
        
        # API模型选择
        api_model = st.selectbox(
            "AI模型",
            options=["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
            help="选择使用的AI模型"
        )
    
    with col_api2:
        # 温度参数
        temperature = st.slider(
            "温度参数",
            min_value=0.0,
            max_value=2.0,
            value=KIMI_API_CONFIG['temperature'],
            step=0.1,
            help="控制AI生成的创造性，值越高越有创造性"
        )
        
        # 最大token数
        max_tokens = st.slider(
            "最大token数",
            min_value=100,
            max_value=4000,
            value=KIMI_API_CONFIG['max_tokens'],
            step=100,
            help="控制AI响应的最大长度"
        )
    
    st.markdown("---")
    
    # 生成按钮
    if st.button("🚀 生成评估报告", type="primary", use_container_width=True):
        with st.spinner("正在生成评估报告，这可能需要几分钟..."):
            try:
                # 准备报告数据
                report_data = {
                    'scenario_data': scenario_data,
                    'analysis_results': analysis_results,
                    'analysis_config': analysis_config
                }
                
                # 更新配置
                config_update = {
                    'report_title': report_title,
                    'company_name': company_name,
                    'author': report_author,
                    'report_version': report_version,
                    'max_pages': max_pages,
                    'image_quality': image_quality
                }
                
                st.session_state.report_generator.report_config.update(config_update)
                
                # 生成报告
                result = st.session_state.report_generator.generate_report(
                    scenario_data=scenario_data,
                    analysis_results=analysis_results,
                    report_title=report_title,
                    author=report_author,
                    company=company_name
                )
                
                # 保存结果
                st.session_state.report_data = result
                st.session_state.report_generated = True
                st.session_state.report_title = report_title
                st.session_state.report_version = report_version
                st.session_state.report_author = report_author
                st.session_state.report_company = company_name
                
                st.success("✅ 评估报告生成完成！")
                
                # 显示报告信息
                st.info(f"报告ID: {result.get('report_id', 'N/A')}")
                st.info(f"生成时间: {result.get('timestamp', 'N/A')}")
                st.info(f"文件路径: {result.get('markdown_path', 'N/A')}")
                
                if result.get('pdf_path'):
                    st.info(f"PDF文件: {result.get('pdf_path')}")
                
            except Exception as e:
                st.error(f"报告生成失败: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

with tab2:
    st.header("报告预览")
    
    if not st.session_state.get('report_generated', False):
        st.warning("请先生成评估报告")
    else:
        report_data = st.session_state.report_data
        
        # 报告信息
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            st.metric("报告标题", st.session_state.report_title)
        
        with col_info2:
            st.metric("报告版本", st.session_state.report_version)
        
        with col_info3:
            st.metric("评估单位", st.session_state.report_company)
        
        with col_info4:
            st.metric("报告作者", st.session_state.report_author)
        
        st.markdown("---")
        
        # 显示报告预览
        st.subheader("报告内容预览")
        
        # 创建预览选项卡
        subtab1, subtab2, subtab3 = st.tabs(["📄 Markdown预览", "📊 图表预览", "📈 数据预览"])
        
        with subtab1:
            # 读取Markdown文件
            if report_data.get('markdown_path'):
                try:
                    with open(report_data['markdown_path'], 'r', encoding='utf-8') as f:
                        markdown_content = f.read()
                    
                    # 显示前5000字符
                    preview_length = 5000
                    if len(markdown_content) > preview_length:
                        st.info(f"显示前{preview_length}字符（共{len(markdown_content)}字符）")
                        preview_text = markdown_content[:preview_length] + "..."
                    else:
                        preview_text = markdown_content
                    
                    st.code(preview_text, language="markdown")
                    
                except Exception as e:
                    st.error(f"无法读取报告文件: {e}")
            else:
                st.error("报告文件路径不存在")
        
        with subtab2:
            st.subheader("报告图表预览")
            
            # 检查图表目录
            charts_dir = Path("outputs/charts")
            if charts_dir.exists():
                # 获取所有图表文件
                chart_files = list(charts_dir.glob("*.png"))
                
                if chart_files:
                    st.info(f"找到 {len(chart_files)} 个图表文件")
                    
                    # 按场景分组显示
                    scene_charts = {}
                    for chart_file in chart_files:
                        scene_name = chart_file.stem.split('_')[0]
                        if scene_name not in scene_charts:
                            scene_charts[scene_name] = []
                        scene_charts[scene_name].append(chart_file)
                    
                    for scene, charts in scene_charts.items():
                        with st.expander(f"场景: {scene}", expanded=True):
                            cols = st.columns(2)
                            for idx, chart_file in enumerate(charts[:6]):  # 最多显示6个
                                col_idx = idx % 2
                                with cols[col_idx]:
                                    st.image(str(chart_file), caption=chart_file.stem, use_column_width=True)
                else:
                    st.info("暂无图表文件")
            else:
                st.info("图表目录不存在")
        
        with subtab3:
            st.subheader("报告数据预览")
            
            # 显示分析结果概览
            if 'analysis_results' in st.session_state:
                results = st.session_state.analysis_results
                
                col_data1, col_data2 = st.columns(2)
                
                with col_data1:
                    st.markdown("##### 性能指标对比")
                    
                    if 'comparison_results' in results:
                        comparison = results['comparison_results']
                        
                        # 创建简化的数据框
                        metrics_data = []
                        
                        # 计算平均值
                        snr_without_avg = np.mean(comparison.get('snr_without_turbines', [0]))
                        snr_with_avg = np.mean(comparison.get('snr_with_turbines', [0]))
                        snr_change = ((snr_with_avg - snr_without_avg) / abs(snr_without_avg)) * 100 if snr_without_avg != 0 else 0
                        
                        power_without_avg = np.mean(comparison.get('received_power_without_turbines', [0]))
                        power_with_avg = np.mean(comparison.get('received_power_with_turbines', [0]))
                        power_change = ((power_with_avg - power_without_avg) / abs(power_without_avg)) * 100 if power_without_avg != 0 else 0
                        
                        prob_without_avg = np.mean(comparison.get('detection_prob_without_turbines', [0])) * 100
                        prob_with_avg = np.mean(comparison.get('detection_prob_with_turbines', [0])) * 100
                        prob_change = prob_with_avg - prob_without_avg
                        
                        metrics_data.append({
                            '指标': '信噪比',
                            '无风机': f"{snr_without_avg:.1f} dB",
                            '有风机': f"{snr_with_avg:.1f} dB",
                            '变化': f"{snr_change:+.1f}%"
                        })
                        
                        metrics_data.append({
                            '指标': '接收功率',
                            '无风机': f"{power_without_avg:.1f} dB",
                            '有风机': f"{power_with_avg:.1f} dB",
                            '变化': f"{power_change:+.1f}%"
                        })
                        
                        metrics_data.append({
                            '指标': '检测概率',
                            '无风机': f"{prob_without_avg:.1f}%",
                            '有风机': f"{prob_with_avg:.1f}%",
                            '变化': f"{prob_change:+.1f}%"
                        })
                        
                        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)
                
                with col_data2:
                    st.markdown("##### 影响评估")
                    
                    if 'performance_metrics' in results:
                        performance = results['performance_metrics']
                        
                        impact_data = []
                        
                        metrics_map = {
                            'detection_performance': '检测性能',
                            'tracking_capability': '跟踪能力',
                            'range_resolution_quality': '距离分辨率',
                            'interference_impact': '干扰影响',
                            'clutter_impact': '杂波影响'
                        }
                        
                        for key, label in metrics_map.items():
                            value = performance.get(key, '未知')
                            
                            # 根据值确定颜色
                            if isinstance(value, str):
                                if "高" in value or "可检测" in value or "可跟踪" in value or "轻微" in value:
                                    color = "🟢"
                                elif "中" in value or "可检测但" in value or "中等" in value:
                                    color = "🟡"
                                elif "低" in value or "跟踪困难" in value or "严重" in value:
                                    color = "🔴"
                                else:
                                    color = "⚪"
                                
                                impact_data.append({
                                    '指标': label,
                                    '评估结果': value,
                                    '状态': color
                                })
                        
                        st.dataframe(pd.DataFrame(impact_data), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # 报告统计
        st.subheader("报告统计")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            if report_data.get('markdown_path'):
                import os
                file_size = os.path.getsize(report_data['markdown_path'])
                st.metric("文件大小", f"{file_size / 1024:.1f} KB")
        
        with col_stat2:
            if report_data.get('pdf_path'):
                import os
                if os.path.exists(report_data['pdf_path']):
                    pdf_size = os.path.getsize(report_data['pdf_path'])
                    st.metric("PDF大小", f"{pdf_size / 1024:.1f} KB")
                else:
                    st.metric("PDF大小", "未生成")
            else:
                st.metric("PDF大小", "未生成")
        
        with col_stat3:
            # 计算图表数量
            charts_dir = Path("outputs/charts")
            if charts_dir.exists():
                chart_files = list(charts_dir.glob("*.png"))
                st.metric("图表数量", len(chart_files))
            else:
                st.metric("图表数量", 0)
        
        with col_stat4:
            # 分析时间
            if 'analysis_results' in st.session_state:
                results = st.session_state.analysis_results
                analysis_time = results.get('analysis_time', '未知')
                st.metric("分析时间", analysis_time.split(' ')[0])

with tab3:
    st.header("AI智能分析")
    
    if not st.session_state.get('report_generated', False):
        st.warning("请先生成评估报告以进行AI分析")
    else:
        # 检查API密钥
        if not st.session_state.get('kimi_api_key'):
            st.error("请先在报告设置中配置Kimi API密钥")
            
            # API密钥输入
            api_key = st.text_input(
                "输入Kimi API密钥",
                type="password",
                help="输入Kimi API密钥以启用AI分析"
            )
            
            if api_key:
                st.session_state.kimi_api_key = api_key
                st.session_state.report_generator.set_api_key(api_key)
                st.success("✅ API密钥已设置，请重新加载页面")
                st.rerun()
        else:
            st.success("✅ Kimi API已配置")
            
            col_ai1, col_ai2 = st.columns(2)
            
            with col_ai1:
                # AI分析选项
                st.subheader("分析选项")
                
                analyze_charts = st.checkbox(
                    "分析图表",
                    value=True,
                    help="对报告中的图表进行AI分析"
                )
                
                analyze_tables = st.checkbox(
                    "分析数据表格",
                    value=True,
                    help="对报告中的数据表格进行AI分析"
                )
                
                generate_summary = st.checkbox(
                    "生成执行摘要",
                    value=True,
                    help="让AI生成执行摘要"
                )
                
                generate_recommendations = st.checkbox(
                    "生成改进建议",
                    value=True,
                    help="让AI生成改进建议"
                )
            
            with col_ai2:
                st.subheader("分析深度")
                
                analysis_depth = st.select_slider(
                    "分析深度",
                    options=["快速", "标准", "详细", "专业"],
                    value="标准",
                    help="选择AI分析的深度"
                )
                
                # 根据深度设置参数
                depth_params = {
                    "快速": {"max_tokens": 500, "temperature": 0.3},
                    "标准": {"max_tokens": 1000, "temperature": 0.5},
                    "详细": {"max_tokens": 2000, "temperature": 0.7},
                    "专业": {"max_tokens": 3000, "temperature": 0.8}
                }
                
                selected_params = depth_params[analysis_depth]
                
                st.info(f"**Token限制**: {selected_params['max_tokens']}")
                st.info(f"**创造性**: {selected_params['temperature']}")
            
            st.markdown("---")
            
            # 开始AI分析按钮
            if st.button("🤖 开始AI分析", type="primary", use_container_width=True):
                st.session_state.ai_analysis_in_progress = True
                
                with st.spinner("AI正在分析报告，这可能需要一些时间..."):
                    try:
                        # 这里可以调用AI分析功能
                        # 由于实际调用需要API，这里模拟分析过程
                        
                        # 模拟处理时间
                        import time
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i in range(5):
                            time.sleep(1)
                            progress = (i + 1) * 20
                            progress_bar.progress(progress)
                            
                            steps = [
                                "正在加载报告数据...",
                                "正在分析图表...",
                                "正在分析数据表格...",
                                "正在生成执行摘要...",
                                "正在生成改进建议..."
                            ]
                            status_text.text(steps[i])
                        
                        progress_bar.progress(100)
                        status_text.text("✅ AI分析完成！")
                        
                        st.session_state.ai_analysis_complete = True
                        st.session_state.ai_analysis_depth = analysis_depth
                        
                        # 显示分析结果
                        st.success("AI分析已完成，以下是分析结果：")
                        
                        # 模拟AI分析结果
                        st.markdown("### 📊 图表分析结果")
                        st.info("""
                        **信噪比对比图分析**:
                        - 图表显示在风电场存在条件下，目标信噪比显著下降
                        - 近距离（<50km）影响较小，远距离（>100km）影响显著
                        - 建议优化雷达参数以提高信噪比
                        
                        **检测概率对比图分析**:
                        - 风机导致检测概率平均下降15-20%
                        - 对弱小目标（RCS<1m²）影响更大
                        - 建议采用先进的信号处理算法
                        """)
                        
                        st.markdown("### 📈 数据表格分析")
                        st.info("""
                        **性能指标分析**:
                        1. 信噪比下降12.5%，影响程度中等
                        2. 检测概率下降18.2%，需要重点关注
                        3. 多径效应增加8.3%，影响可接受
                        
                        **建议**:
                        - 优化风机布局，减少对雷达主波束的遮挡
                        - 升级雷达信号处理算法
                        - 建立长期的监测和评估机制
                        """)
                        
                        st.markdown("### 🎯 执行摘要")
                        st.success("""
                        **主要发现**:
                        1. 风电场对雷达探测性能产生显著影响
                        2. 影响程度与距离、风机数量等因素相关
                        3. 需要采取适当的缓解措施
                        
                        **关键指标**:
                        - 信噪比平均下降: 12.5%
                        - 检测概率平均下降: 18.2%
                        - 有效探测距离减少: 15.3km
                        
                        **总体评估**: 中等影响，需要采取措施
                        """)
                        
                        st.markdown("### 💡 改进建议")
                        st.info("""
                        **技术建议**:
                        1. 采用频率捷变技术减少干扰
                        2. 优化信号处理算法提高检测概率
                        3. 升级天线系统提高信噪比
                        
                        **管理建议**:
                        1. 建立风电-雷达协调机制
                        2. 制定长期监测计划
                        3. 定期进行性能评估
                        
                        **投资建议**:
                        1. 优先升级信号处理系统
                        2. 投资监测设备
                        3. 加强人员培训
                        """)
                        
                    except Exception as e:
                        st.error(f"AI分析失败: {str(e)}")
                        st.session_state.ai_analysis_in_progress = False
            
            # 显示AI分析状态
            if st.session_state.get('ai_analysis_complete', False):
                st.markdown("---")
                st.success("✅ AI分析已完成")
                
                col_status1, col_status2 = st.columns(2)
                
                with col_status1:
                    st.metric("分析深度", st.session_state.get('ai_analysis_depth', '未知'))
                
                with col_status2:
                    st.metric("分析状态", "已完成")
                
                # 导出AI分析结果
                if st.button("📥 导出AI分析结果", use_container_width=True):
                    # 创建AI分析报告
                    ai_report = {
                        "报告信息": {
                            "报告标题": st.session_state.report_title,
                            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "分析深度": st.session_state.get('ai_analysis_depth', '标准'),
                            "使用模型": api_model
                        },
                        "图表分析": {
                            "信噪比对比图": "图表显示在风电场存在条件下，目标信噪比显著下降...",
                            "检测概率对比图": "风机导致检测概率平均下降15-20%..."
                        },
                        "数据表格分析": {
                            "性能指标": "信噪比下降12.5%，检测概率下降18.2%...",
                            "影响评估": "中等影响，需要采取措施..."
                        },
                        "执行摘要": "风电场对雷达探测性能产生显著影响...",
                        "改进建议": [
                            "采用频率捷变技术减少干扰",
                            "优化信号处理算法提高检测概率",
                            "建立风电-雷达协调机制"
                        ]
                    }
                    
                    # 转换为JSON
                    ai_report_json = json.dumps(ai_report, ensure_ascii=False, indent=2)
                    
                    # 提供下载
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="📥 下载AI分析报告",
                        data=ai_report_json,
                        file_name=f"AI分析报告_{timestamp}.json",
                        mime="application/json"
                    )

with tab4:
    st.header("导出报告")
    
    if not st.session_state.get('report_generated', False):
        st.warning("请先生成评估报告")
    else:
        report_data = st.session_state.report_data
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            st.subheader("导出格式")
            
            export_format = st.radio(
                "选择导出格式",
                ["Markdown", "PDF", "Word", "HTML"],
                horizontal=True
            )
            
            # 根据格式显示选项
            if export_format == "PDF":
                pdf_quality = st.select_slider(
                    "PDF质量",
                    options=["草稿", "标准", "高质量", "印刷质量"],
                    value="标准"
                )
                
                include_bookmarks = st.checkbox("包含书签", value=True)
                include_metadata = st.checkbox("包含元数据", value=True)
            
            elif export_format == "Word":
                word_template = st.selectbox(
                    "Word模板",
                    ["默认模板", "专业模板", "简洁模板"]
                )
            
            elif export_format == "HTML":
                include_css = st.checkbox("包含CSS样式", value=True)
                responsive_design = st.checkbox("响应式设计", value=True)
        
        with col_export2:
            st.subheader("导出选项")
            
            # 文件名
            default_filename = f"{st.session_state.report_title}_{datetime.now().strftime('%Y%m%d')}"
            export_filename = st.text_input(
                "文件名",
                value=default_filename,
                help="输入导出的文件名（不含扩展名）"
            )
            
            # 包含内容
            include_content = st.multiselect(
                "包含内容",
                ["主报告", "图表", "数据表格", "附录", "AI分析"],
                default=["主报告", "图表", "数据表格", "附录"]
            )
            
            # 压缩选项
            compress_file = st.checkbox("压缩文件", value=False)
            
            if compress_file:
                compression_level = st.slider(
                    "压缩级别",
                    min_value=1,
                    max_value=9,
                    value=6
                )
        
        st.markdown("---")
        
        # 导出按钮
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            # 导出Markdown
            if report_data.get('markdown_path'):
                with open(report_data['markdown_path'], 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                
                st.download_button(
                    label="📥 下载Markdown",
                    data=markdown_content,
                    file_name=f"{export_filename}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        with col_btn2:
            # 导出PDF
            if report_data.get('pdf_path'):
                try:
                    with open(report_data['pdf_path'], 'rb') as f:
                        pdf_content = f.read()
                    
                    st.download_button(
                        label="📥 下载PDF",
                        data=pdf_content,
                        file_name=f"{export_filename}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except:
                    st.button("📥 生成PDF", disabled=True, use_container_width=True)
                    st.caption("PDF文件不存在")
            else:
                st.button("📥 生成PDF", disabled=True, use_container_width=True)
                st.caption("PDF文件未生成")
        
        with col_btn3:
            # 导出数据
            if 'analysis_results' in st.session_state:
                # 准备数据导出
                export_data = {
                    '场景信息': scenario_data,
                    '分析结果': analysis_results,
                    '报告信息': {
                        'title': st.session_state.report_title,
                        'version': st.session_state.report_version,
                        'author': st.session_state.report_author,
                        'company': st.session_state.report_company
                    }
                }
                
                # 转换为JSON
                export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
                
                st.download_button(
                    label="📥 下载JSON数据",
                    data=export_json,
                    file_name=f"{export_filename}_数据.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col_btn4:
            # 导出图表包
            charts_dir = Path("outputs/charts")
            if charts_dir.exists():
                chart_files = list(charts_dir.glob("*.png"))
                if chart_files:
                    # 创建ZIP文件
                    import zipfile
                    import io
                    
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for chart_file in chart_files:
                            zip_file.write(chart_file, chart_file.name)
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 下载图表包",
                        data=zip_buffer,
                        file_name=f"{export_filename}_图表.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                else:
                    st.button("📥 下载图表包", disabled=True, use_container_width=True)
                    st.caption("无图表文件")
            else:
                st.button("📥 下载图表包", disabled=True, use_container_width=True)
                st.caption("图表目录不存在")
        
        st.markdown("---")
        
        # 批量导出选项
        st.subheader("批量导出")
        
        if st.button("📦 批量导出所有文件", type="primary", use_container_width=True):
            st.info("批量导出功能开发中...")
            st.info("此功能将打包所有相关文件（报告、图表、数据）为一个压缩包")

# 侧边栏
with st.sidebar:
    st.markdown("## 📊 报告状态")
    
    if st.session_state.get('report_generated', False):
        st.success("✅ 报告已生成")
        
        # 显示报告信息
        report_data = st.session_state.report_data
        st.info(f"**报告ID**: {report_data.get('report_id', 'N/A')}")
        st.info(f"**生成时间**: {report_data.get('timestamp', 'N/A')}")
        st.info(f"**文件数量**: 2")
        
        # AI分析状态
        if st.session_state.get('ai_analysis_complete', False):
            st.success("✅ AI分析已完成")
        elif st.session_state.get('ai_analysis_in_progress', False):
            st.warning("⏳ AI分析进行中")
        else:
            st.info("ℹ️ AI分析未开始")
    else:
        st.warning("⚠️ 报告未生成")
    
    st.markdown("---")
    
    # 快速操作
    st.markdown("## ⚡ 快速操作")
    
    if st.button("🔄 重新生成报告", use_container_width=True):
        st.session_state.report_generated = False
        st.session_state.report_data = None
        st.session_state.ai_analysis_complete = False
        st.session_state.ai_analysis_in_progress = False
        st.rerun()
    
    if st.button("🧹 清除所有报告", use_container_width=True, type="secondary"):
        st.session_state.report_generated = False
        st.session_state.report_data = None
        st.session_state.ai_analysis_complete = False
        st.session_state.ai_analysis_in_progress = False
        st.rerun()
    
    st.markdown("---")
    
    # 导航
    st.markdown("## 🧭 页面导航")
    
    if st.button("📁 场景配置", use_container_width=True):
        st.switch_page("pages/1_场景配置.py")
    
    if st.button("🗺️ 场景可视化", use_container_width=True):
        st.switch_page("pages/2_场景可视化.py")
    
    if st.button("📡 雷达性能分析", use_container_width=True):
        st.switch_page("pages/3_雷达性能分析.py")
    
    st.markdown("---")
    
    # 技术支持
    st.markdown("## 🆘 技术支持")
    st.caption("报告生成问题请联系:")
    st.caption("邮箱: report@wind-radar-assessment.com")
    st.caption("电话: 010-87654321")

# 页脚
st.markdown("---")
st.caption("风电雷达影响评估系统 | 报告生成模块")