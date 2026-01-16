"""
卡片组件模块 - 现代化军事科技风格的卡片组件
用于构建一致、美观的数据展示和交互界面
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from utils.style_utils import get_military_style

class MilitaryCards:
    """军事科技风格卡片组件集合"""
    
    @staticmethod
    def create_data_card(
        title: str,
        value: Union[int, float, str],
        unit: str = "",
        icon: str = "📊",
        trend: Optional[float] = None,
        trend_label: str = "变化",
        color: str = "#1a73e8",
        width: int = 1,
        help_text: Optional[str] = None
    ):
        """
        创建数据卡片
        
        参数:
            title: 卡片标题
            value: 显示值
            unit: 单位
            icon: 图标
            trend: 趋势值（正负表示升降）
            trend_label: 趋势标签
            color: 主色调
            width: 宽度（1-12）
            help_text: 帮助文本
        """
        col_span = f"span {width}"
        
        st.markdown(
            f"""
            <div style="
                grid-column: {col_span};
                background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(20, 20, 20, 0.9) 100%);
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
            ">
                <!-- 装饰性元素 -->
                <div style="
                    position: absolute;
                    top: 0;
                    right: 0;
                    width: 60px;
                    height: 60px;
                    background: radial-gradient(circle, {color}20 0%, transparent 70%);
                    border-radius: 0 12px 0 0;
                "></div>
                
                <div style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 1rem;
                ">
                    <div style="
                        background: {color}20;
                        width: 48px;
                        height: 48px;
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 1rem;
                        border: 1px solid {color}40;
                    ">
                        <span style="font-size: 1.5rem;">{icon}</span>
                    </div>
                    <div style="flex: 1;">
                        <div style="
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        ">
                            <h3 style="
                                margin: 0;
                                font-size: 1rem;
                                font-weight: 600;
                                color: #b0b0b0;
                            ">{title}</h3>
                            {f'<div style="color: #666; cursor: help;" title="{help_text}">?</div>' if help_text else ''}
                        </div>
                    </div>
                </div>
                
                <div style="
                    margin-bottom: 0.5rem;
                ">
                    <div style="
                        font-size: 2rem;
                        font-weight: 700;
                        color: {color};
                        line-height: 1;
                    ">
                        {value}
                        {f'<span style="font-size: 1rem; color: #b0b0b0; font-weight: 400;"> {unit}</span>' if unit else ''}
                    </div>
                </div>
                
                {MilitaryCards._render_trend_section(trend, trend_label, color)}
                
                <!-- 底部分隔线 -->
                <div style="
                    height: 1px;
                    background: linear-gradient(90deg, transparent, {color}40, transparent);
                    margin: 1rem 0;
                "></div>
                
                <!-- 时间戳 -->
                <div style="
                    font-size: 0.8rem;
                    color: #666;
                    text-align: right;
                ">
                    {datetime.now().strftime('%H:%M')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def _render_trend_section(trend: Optional[float], trend_label: str, color: str) -> str:
        """渲染趋势部分"""
        if trend is None:
            return ""
        
        trend_color = "#00e676" if trend > 0 else "#f44336" if trend < 0 else "#ff9800"
        trend_icon = "↗️" if trend > 0 else "↘️" if trend < 0 else "➡️"
        
        return f"""
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-top: 0.5rem;
            ">
                <span style="
                    font-size: 0.9rem;
                    color: #b0b0b0;
                ">{trend_label}</span>
                <span style="
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: {trend_color};
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                ">
                    {trend_icon} {abs(trend):.1f}%
                </span>
            </div>
        """
    
    @staticmethod
    def create_status_card(
        title: str,
        status: str,
        icon: str = "⚡",
        status_colors: Optional[Dict[str, str]] = None,
        sub_status: Optional[str] = None,
        details: Optional[List[str]] = None,
        action_text: Optional[str] = None,
        action_color: str = "#1a73e8",
        on_action_click: Optional[str] = None
    ):
        """
        创建状态卡片
        
        参数:
            title: 卡片标题
            status: 状态文本
            icon: 图标
            status_colors: 状态颜色映射
            sub_status: 子状态文本
            details: 详细信息列表
            action_text: 操作按钮文本
            action_color: 操作按钮颜色
            on_action_click: 点击操作按钮的JavaScript代码
        """
        if status_colors is None:
            status_colors = {
                "online": "#00e676",
                "offline": "#f44336",
                "warning": "#ff9800",
                "maintenance": "#ffc107"
            }
        
        status_color = status_colors.get(status.lower(), "#666")
        
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(20, 20, 20, 0.9) 100%);
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid {status_color}40;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                position: relative;
                overflow: hidden;
            ">
                <!-- 状态指示条 -->
                <div style="
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, {status_color}, {status_color}80, {status_color}20);
                "></div>
                
                <div style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 1rem;
                ">
                    <div style="
                        background: {status_color}20;
                        width: 48px;
                        height: 48px;
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 1rem;
                        border: 1px solid {status_color}40;
                    ">
                        <span style="font-size: 1.5rem;">{icon}</span>
                    </div>
                    <div style="flex: 1;">
                        <h3 style="
                            margin: 0 0 0.25rem 0;
                            font-size: 1.1rem;
                            font-weight: 600;
                            color: #ffffff;
                        ">{title}</h3>
                        <div style="
                            display: flex;
                            align-items: center;
                            gap: 0.5rem;
                        ">
                            <div style="
                                width: 8px;
                                height: 8px;
                                border-radius: 50%;
                                background-color: {status_color};
                                animation: pulse 2s infinite;
                            "></div>
                            <span style="
                                font-size: 0.9rem;
                                font-weight: 600;
                                color: {status_color};
                                text-transform: uppercase;
                                letter-spacing: 1px;
                            ">{status}</span>
                        </div>
                    </div>
                </div>
                
                {MilitaryCards._render_sub_status(sub_status)}
                {MilitaryCards._render_details(details)}
                {MilitaryCards._render_action(action_text, action_color, on_action_click)}
                
                <style>
                    @keyframes pulse {{
                        0% {{ opacity: 1; transform: scale(1); }}
                        50% {{ opacity: 0.5; transform: scale(1.1); }}
                        100% {{ opacity: 1; transform: scale(1); }}
                    }}
                </style>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def _render_sub_status(sub_status: Optional[str]) -> str:
        """渲染子状态"""
        if not sub_status:
            return ""
        
        return f"""
            <div style="
                background: rgba(255, 255, 255, 0.05);
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                border-left: 3px solid #1a73e8;
            ">
                <div style="
                    font-size: 0.9rem;
                    color: #b0b0b0;
                ">{sub_status}</div>
            </div>
        """
    
    @staticmethod
    def _render_details(details: Optional[List[str]]) -> str:
        """渲染详细信息"""
        if not details:
            return ""
        
        details_html = ""
        for i, detail in enumerate(details):
            details_html += f"""
                <div style="
                    display: flex;
                    align-items: center;
                    padding: 0.5rem 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                ">
                    <span style="
                        color: #666;
                        margin-right: 0.5rem;
                        font-size: 0.9rem;
                    ">•</span>
                    <span style="
                        font-size: 0.9rem;
                        color: #b0b0b0;
                    ">{detail}</span>
                </div>
            """
        
        return f"""
            <div style="
                margin-bottom: 1rem;
            ">
                {details_html}
            </div>
        """
    
    @staticmethod
    def _render_action(action_text: Optional[str], action_color: str, on_action_click: Optional[str]) -> str:
        """渲染操作按钮"""
        if not action_text:
            return ""
        
        click_handler = f"onclick=\"{on_action_click}\"" if on_action_click else ""
        
        return f"""
            <button {click_handler} style="
                width: 100%;
                background: linear-gradient(135deg, {action_color} 0%, {action_color}80 100%);
                border: none;
                border-radius: 8px;
                padding: 0.75rem 1rem;
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
            "
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px {action_color}40';"
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
            >
                {action_text}
            </button>
        """
    
    @staticmethod
    def create_config_card(
        title: str,
        icon: str = "⚙️",
        config_items: Optional[List[Dict[str, Any]]] = None,
        current_config: Optional[Dict[str, Any]] = None,
        editable: bool = True,
        on_save: Optional[str] = None,
        on_reset: Optional[str] = None
    ):
        """
        创建配置卡片
        
        参数:
            title: 卡片标题
            icon: 图标
            config_items: 配置项定义
            current_config: 当前配置值
            editable: 是否可编辑
            on_save: 保存操作的JavaScript代码
            on_reset: 重置操作的JavaScript代码
        """
        if config_items is None:
            config_items = []
        if current_config is None:
            current_config = {}
        
        config_html = ""
        for item in config_items:
            item_id = item.get('id', '')
            item_name = item.get('name', '')
            item_type = item.get('type', 'text')
            item_value = current_config.get(item_id, item.get('default', ''))
            item_options = item.get('options', [])
            item_help = item.get('help', '')
            
            config_html += MilitaryCards._render_config_item(
                item_id, item_name, item_type, item_value, item_options, item_help, editable
            )
        
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(20, 20, 20, 0.9) 100%);
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 1.5rem;
                ">
                    <div style="
                        background: rgba(26, 115, 232, 0.2);
                        width: 48px;
                        height: 48px;
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 1rem;
                        border: 1px solid rgba(26, 115, 232, 0.4);
                    ">
                        <span style="font-size: 1.5rem;">{icon}</span>
                    </div>
                    <div style="flex: 1;">
                        <h3 style="
                            margin: 0 0 0.25rem 0;
                            font-size: 1.1rem;
                            font-weight: 600;
                            color: #ffffff;
                        ">{title}</h3>
                        <div style="
                            font-size: 0.9rem;
                            color: #b0b0b0;
                        ">
                            配置项: {len(config_items)}
                        </div>
                    </div>
                </div>
                
                <div style="
                    margin-bottom: 1.5rem;
                ">
                    {config_html}
                </div>
                
                {MilitaryCards._render_config_actions(editable, on_save, on_reset)}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def _render_config_item(
        item_id: str,
        item_name: str,
        item_type: str,
        item_value: Any,
        item_options: List[Any],
        item_help: str,
        editable: bool
    ) -> str:
        """渲染配置项"""
        if item_type == 'select':
            options_html = ""
            for option in item_options:
                selected = "selected" if option['value'] == item_value else ""
                options_html += f'<option value="{option["value"]}" {selected}>{option["label"]}</option>'
            
            return f"""
                <div style="margin-bottom: 1rem;">
                    <label style="
                        display: block;
                        font-size: 0.9rem;
                        font-weight: 600;
                        color: #b0b0b0;
                        margin-bottom: 0.5rem;
                    ">
                        {item_name}
                        {f'<span style="color: #666; margin-left: 0.25rem; cursor: help;" title="{item_help}">?</span>' if item_help else ''}
                    </label>
                    <select id="{item_id}" style="
                        width: 100%;
                        padding: 0.75rem;
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        color: white;
                        font-size: 0.9rem;
                        {'cursor: not-allowed; opacity: 0.6;' if not editable else ''}
                    " {'disabled' if not editable else ''}>
                        {options_html}
                    </select>
                </div>
            """
        
        elif item_type == 'range':
            return f"""
                <div style="margin-bottom: 1rem;">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 0.5rem;
                    ">
                        <label style="
                            font-size: 0.9rem;
                            font-weight: 600;
                            color: #b0b0b0;
                        ">
                            {item_name}
                        </label>
                        <span style="
                            font-size: 0.9rem;
                            color: #1a73e8;
                            font-weight: 600;
                        ">{item_value}</span>
                    </div>
                    <input type="range" id="{item_id}" value="{item_value}" min="{item_options[0]}" max="{item_options[1]}" step="{item_options[2]}" style="
                        width: 100%;
                        height: 4px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 2px;
                        outline: none;
                        opacity: 0.7;
                        transition: opacity 0.2s;
                        -webkit-appearance: none;
                        {'cursor: not-allowed; opacity: 0.4;' if not editable else ''}
                    " {'disabled' if not editable else ''}
                    oninput="document.getElementById('{item_id}_value').textContent = this.value">
                </div>
            """
        
        else:  # text input
            return f"""
                <div style="margin-bottom: 1rem;">
                    <label style="
                        display: block;
                        font-size: 0.9rem;
                        font-weight: 600;
                        color: #b0b0b0;
                        margin-bottom: 0.5rem;
                    ">
                        {item_name}
                        {f'<span style="color: #666; margin-left: 0.25rem; cursor: help;" title="{item_help}">?</span>' if item_help else ''}
                    </label>
                    <input type="text" id="{item_id}" value="{item_value}" style="
                        width: 100%;
                        padding: 0.75rem;
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        color: white;
                        font-size: 0.9rem;
                        {'cursor: not-allowed; opacity: 0.6;' if not editable else ''}
                    " {'readonly' if not editable else ''}>
                </div>
            """
    
    @staticmethod
    def _render_config_actions(editable: bool, on_save: Optional[str], on_reset: Optional[str]) -> str:
        """渲染配置操作按钮"""
        if not editable:
            return ""
        
        buttons_html = ""
        if on_reset:
            buttons_html += f"""
                <button onclick="{on_reset}" style="
                    flex: 1;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 0.75rem 1rem;
                    color: white;
                    font-weight: 600;
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: all 0.2s;
                "
                onmouseover="this.style.background='rgba(255, 255, 255, 0.15)';"
                onmouseout="this.style.background='rgba(255, 255, 255, 0.1)';"
                >
                    🔄 重置
                </button>
            """
        
        if on_save:
            buttons_html += f"""
                <button onclick="{on_save}" style="
                    flex: 1;
                    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
                    border: none;
                    border-radius: 8px;
                    padding: 0.75rem 1rem;
                    color: white;
                    font-weight: 600;
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: all 0.2s;
                "
                onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(26, 115, 232, 0.4)';"
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
                >
                    💾 保存配置
                </button>
            """
        
        if not buttons_html:
            return ""
        
        return f"""
            <div style="
                display: flex;
                gap: 0.75rem;
            ">
                {buttons_html}
            </div>
        """
    
    @staticmethod
    def create_alert_card(
        title: str,
        message: str,
        alert_type: str = "info",  # info, success, warning, error
        icon: str = "",
        auto_close: bool = False,
        close_time: int = 5,
        action_text: Optional[str] = None,
        on_action_click: Optional[str] = None
    ):
        """
        创建告警卡片
        
        参数:
            title: 告警标题
            message: 告警消息
            alert_type: 告警类型
            icon: 自定义图标
            auto_close: 是否自动关闭
            close_time: 自动关闭时间（秒）
            action_text: 操作按钮文本
            on_action_click: 点击操作按钮的JavaScript代码
        """
        type_config = {
            "info": {"color": "#1a73e8", "icon": "ℹ️"},
            "success": {"color": "#00e676", "icon": "✅"},
            "warning": {"color": "#ff9800", "icon": "⚠️"},
            "error": {"color": "#f44336", "icon": "❌"}
        }
        
        config = type_config.get(alert_type, type_config["info"])
        alert_color = config["color"]
        alert_icon = icon if icon else config["icon"]
        
        auto_close_js = ""
        if auto_close:
            auto_close_js = f"""
                <script>
                    setTimeout(function() {{
                        var alert = document.getElementById('alert-{id(hash(title))}');
                        if (alert) {{
                            alert.style.opacity = '0';
                            alert.style.transform = 'translateX(100%)';
                            setTimeout(function() {{ alert.style.display = 'none'; }}, 300);
                        }}
                    }}, {close_time * 1000});
                </script>
            """
        
        action_button = ""
        if action_text and on_action_click:
            action_button = f"""
                <button onclick="{on_action_click}" style="
                    background: {alert_color};
                    border: none;
                    border-radius: 6px;
                    padding: 0.5rem 1rem;
                    color: white;
                    font-weight: 600;
                    font-size: 0.85rem;
                    cursor: pointer;
                    transition: all 0.2s;
                    margin-top: 0.75rem;
                "
                onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px {alert_color}40';"
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
                >
                    {action_text}
                </button>
            """
        
        st.markdown(
            f"""
            <div id="alert-{id(hash(title))}" style="
                background: linear-gradient(135deg, {alert_color}10 0%, {alert_color}05 100%);
                border-radius: 12px;
                padding: 1.25rem;
                border: 1px solid {alert_color}40;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            ">
                <div style="
                    display: flex;
                    align-items: flex-start;
                ">
                    <div style="
                        background: {alert_color}20;
                        width: 40px;
                        height: 40px;
                        border-radius: 10px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 1rem;
                        flex-shrink: 0;
                        border: 1px solid {alert_color}40;
                    ">
                        <span style="font-size: 1.25rem;">{alert_icon}</span>
                    </div>
                    <div style="flex: 1;">
                        <h4 style="
                            margin: 0 0 0.5rem 0;
                            font-size: 1rem;
                            font-weight: 600;
                            color: white;
                        ">{title}</h4>
                        <div style="
                            font-size: 0.9rem;
                            color: #b0b0b0;
                            line-height: 1.5;
                        ">{message}</div>
                        {action_button}
                    </div>
                </div>
            </div>
            {auto_close_js}
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def create_progress_card(
        title: str,
        current_value: Union[int, float],
        total_value: Union[int, float],
        unit: str = "",
        icon: str = "📈",
        show_percentage: bool = True,
        show_value: bool = True,
        color: str = "#1a73e8",
        animation: bool = True
    ):
        """
        创建进度卡片
        
        参数:
            title: 卡片标题
            current_value: 当前值
            total_value: 总值
            unit: 单位
            icon: 图标
            show_percentage: 是否显示百分比
            show_value: 是否显示数值
            color: 进度条颜色
            animation: 是否启用动画
        """
        percentage = (current_value / total_value * 100) if total_value > 0 else 0
        percentage = min(percentage, 100)
        
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(20, 20, 20, 0.9) 100%);
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 1rem;
                ">
                    <div style="
                        background: {color}20;
                        width: 48px;
                        height: 48px;
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 1rem;
                        border: 1px solid {color}40;
                    ">
                        <span style="font-size: 1.5rem;">{icon}</span>
                    </div>
                    <div style="flex: 1;">
                        <h3 style="
                            margin: 0 0 0.25rem 0;
                            font-size: 1rem;
                            font-weight: 600;
                            color: #ffffff;
                        ">{title}</h3>
                    </div>
                </div>
                
                <div style="
                    margin-bottom: 0.5rem;
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 0.5rem;
                    ">
                        {f'<span style="font-size: 2rem; font-weight: 700; color: {color};">{current_value}</span>' if show_value else ''}
                        {f'<span style="font-size: 0.9rem; color: #b0b0b0;">{unit}</span>' if unit else ''}
                    </div>
                    
                    <!-- 进度条容器 -->
                    <div style="
                        width: 100%;
                        height: 8px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 4px;
                        overflow: hidden;
                        position: relative;
                    ">
                        <!-- 进度条 -->
                        <div style="
                            width: {percentage}%;
                            height: 100%;
                            background: linear-gradient(90deg, {color}, {color}80);
                            border-radius: 4px;
                            position: relative;
                            {'animation: progress-animation 1.5s ease-out;' if animation else ''}
                        ">
                            <!-- 进度条光泽效果 -->
                            <div style="
                                position: absolute;
                                top: 0;
                                left: 0;
                                right: 0;
                                height: 50%;
                                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                                border-radius: 4px;
                            "></div>
                        </div>
                    </div>
                    
                    <!-- 进度信息 -->
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-top: 0.5rem;
                    ">
                        {f'<span style="font-size: 0.9rem; color: #b0b0b0;">进度</span>' if show_percentage else ''}
                        {f'<span style="font-size: 0.9rem; font-weight: 600; color: {color};">{percentage:.1f}%</span>' if show_percentage else ''}
                    </div>
                </div>
                
                {'<style>@keyframes progress-animation { from { width: 0%; } to { width: ' + f'{percentage}%' + '; } }</style>' if animation else ''}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def create_metric_grid(
        metrics: List[Dict[str, Any]],
        columns: int = 4,
        spacing: int = 1
    ):
        """
        创建指标网格
        
        参数:
            metrics: 指标列表
            columns: 列数
            spacing: 间距（rem）
        """
        grid_template_columns = f"repeat({columns}, 1fr)"
        
        metrics_html = ""
        for metric in metrics:
            metrics_html += f"""
                <div style="
                    {get_military_style('card')}
                ">
                    {MilitaryCards._render_metric(metric)}
                </div>
            """
        
        st.markdown(
            f"""
            <div style="
                display: grid;
                grid-template-columns: {grid_template_columns};
                gap: {spacing}rem;
                margin-bottom: 2rem;
            ">
                {metrics_html}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def _render_metric(metric: Dict[str, Any]) -> str:
        """渲染单个指标"""
        title = metric.get('title', '')
        value = metric.get('value', '')
        unit = metric.get('unit', '')
        icon = metric.get('icon', '📊')
        color = metric.get('color', '#1a73e8')
        trend = metric.get('trend')
        help_text = metric.get('help')
        
        trend_html = ""
        if trend is not None:
            trend_color = "#00e676" if trend > 0 else "#f44336" if trend < 0 else "#ff9800"
            trend_icon = "↗️" if trend > 0 else "↘️" if trend < 0 else "➡️"
            trend_html = f"""
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                    font-size: 0.8rem;
                    color: {trend_color};
                ">
                    {trend_icon} {abs(trend):.1f}%
                </div>
            """
        
        return f"""
            <div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 0.5rem;
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    ">
                        <span style="
                            color: {color};
                            font-size: 1.2rem;
                        ">{icon}</span>
                        <span style="
                            font-size: 0.85rem;
                            font-weight: 600;
                            color: #b0b0b0;
                        ">{title}</span>
                    </div>
                    {f'<span style="color: #666; font-size: 0.8rem; cursor: help;" title="{help_text}">?</span>' if help_text else ''}
                </div>
                
                <div style="
                    display: flex;
                    align-items: baseline;
                    gap: 0.25rem;
                    margin-bottom: 0.25rem;
                ">
                    <span style="
                        font-size: 1.5rem;
                        font-weight: 700;
                        color: {color};
                    ">{value}</span>
                    {f'<span style="font-size: 0.9rem; color: #b0b0b0;">{unit}</span>' if unit else ''}
                </div>
                
                {trend_html}
            </div>
        """

# 使用示例
def demo_cards():
    """演示所有卡片组件"""
    st.title("🎴 卡片组件演示")
    
    # 1. 数据卡片
    st.header("1. 数据卡片")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        MilitaryCards.create_data_card(
            title="检测概率",
            value=0.85,
            unit="%",
            icon="🎯",
            trend=5.2,
            color="#1a73e8"
        )
    
    with col2:
        MilitaryCards.create_data_card(
            title="虚警率",
            value=1.2e-4,
            icon="⚠️",
            trend=-2.1,
            color="#f44336"
        )
    
    with col3:
        MilitaryCards.create_data_card(
            title="航迹连续性",
            value=0.92,
            unit="%",
            icon="🛤️",
            trend=1.5,
            color="#00e676"
        )
    
    with col4:
        MilitaryCards.create_data_card(
            title="系统负载",
            value=65,
            unit="%",
            icon="⚡",
            trend=8.3,
            color="#ff9800"
        )
    
    # 2. 状态卡片
    st.header("2. 状态卡片")
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        MilitaryCards.create_status_card(
            title="雷达系统",
            status="online",
            icon="📡",
            sub_status="3/3雷达在线运行",
            details=["雷达1: 探测距离150km", "雷达2: 负载65%", "雷达3: 状态正常"],
            action_text="查看详情"
        )
    
    with col_status2:
        MilitaryCards.create_status_card(
            title="仿真引擎",
            status="running",
            icon="🚀",
            sub_status="运行时间: 2分30秒",
            details=["帧率: 24 FPS", "CPU使用: 45%", "内存使用: 2.1GB"],
            action_text="停止仿真"
        )
    
    # 3. 配置卡片
    st.header("3. 配置卡片")
    
    config_items = [
        {
            "id": "frequency",
            "name": "中心频率",
            "type": "range",
            "default": 3000,
            "options": [100, 10000, 100]
        },
        {
            "id": "bandwidth",
            "name": "带宽",
            "type": "select",
            "default": "medium",
            "options": [
                {"value": "narrow", "label": "窄带"},
                {"value": "medium", "label": "中带宽"},
                {"value": "wide", "label": "宽带"}
            ]
        },
        {
            "id": "power",
            "name": "发射功率",
            "type": "text",
            "default": "500 kW"
        }
    ]
    
    MilitaryCards.create_config_card(
        title="雷达参数配置",
        icon="⚙️",
        config_items=config_items,
        current_config={"frequency": 3000, "bandwidth": "medium", "power": "500 kW"}
    )
    
    # 4. 告警卡片
    st.header("4. 告警卡片")
    
    col_alert1, col_alert2 = st.columns(2)
    
    with col_alert1:
        MilitaryCards.create_alert_card(
            title="系统提示",
            message="仿真运行正常，所有组件工作状态良好。",
            alert_type="success"
        )
    
    with col_alert2:
        MilitaryCards.create_alert_card(
            title="注意",
            message="雷达#3负载达到85%，建议调整参数。",
            alert_type="warning",
            action_text="优化配置",
            on_action_click="alert('开始优化配置...')"
        )
    
    # 5. 进度卡片
    st.header("5. 进度卡片")
    col_prog1, col_prog2 = st.columns(2)
    
    with col_prog1:
        MilitaryCards.create_progress_card(
            title="仿真进度",
            current_value=150,
            total_value=300,
            unit="秒",
            icon="⏱️"
        )
    
    with col_prog2:
        MilitaryCards.create_progress_card(
            title="数据记录",
            current_value=1200,
            total_value=5000,
            unit="条",
            icon="💾"
        )
    
    # 6. 指标网格
    st.header("6. 指标网格")
    
    metrics = [
        {"title": "目标数", "value": 15, "unit": "个", "icon": "🛰️", "color": "#1a73e8", "trend": 3.2},
        {"title": "检测数", "value": 12, "unit": "个", "icon": "🎯", "color": "#00e676", "trend": 5.1},
        {"title": "虚警数", "value": 2, "unit": "个", "icon": "⚠️", "color": "#f44336", "trend": -1.2},
        {"title": "航迹数", "value": 8, "unit": "条", "icon": "🛤️", "color": "#9c27b0", "trend": 2.5},
        {"title": "CPU使用", "value": 45, "unit": "%", "icon": "⚡", "color": "#ff9800", "trend": 1.8},
        {"title": "内存使用", "value": 2.1, "unit": "GB", "icon": "💾", "color": "#03a9f4", "trend": 0.5},
        {"title": "网络延迟", "value": 24, "unit": "ms", "icon": "📶", "color": "#4caf50", "trend": -0.3},
        {"title": "数据吞吐", "value": 1.2, "unit": "Gbps", "icon": "🚀", "color": "#e91e63", "trend": 8.7}
    ]
    
    MilitaryCards.create_metric_grid(metrics, columns=4, spacing=1)

if __name__ == "__main__":
    demo_cards()