"""
侧边栏组件 - 现代化导航侧边栏
"""

import streamlit as st
from utils.style_utils import get_military_style

def show_sidebar():
    """显示侧边栏"""
    with st.sidebar:
        # 侧边栏头部
        st.markdown(
            """
            <div class="sidebar-header">
                <h3>🎯 导航面板</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 页面导航
        pages = {
            "概览": "🏠 系统概览",
            "想定生成": "🎯 AI想定生成",
            "雷达配置": "📡 雷达配置",
            "目标配置": "🛰️ 目标配置", 
            "仿真配置": "⚙️ 仿真参数",
            "仿真运行": "🚀 仿真运行",
            "结果可视化": "📊 结果可视化",
            "性能评估": "📈 性能评估"
        }
        
        # 页面选择
        selected_page = st.radio(
            "选择页面",
            list(pages.values()),
            label_visibility="collapsed"
        )
        
        # 更新当前页面
        for key, value in pages.items():
            if value == selected_page:
                st.session_state.current_page = key
        
        st.markdown("---")
        
        # 用户设置
        st.markdown(
            """
            <div class="sidebar-section">
                <h4>⚙️ 用户设置</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 主题选择
        theme = st.selectbox(
            "主题模式",
            ["深色", "浅色", "自动"],
            index=0
        )
        
        # 单位制
        units = st.radio(
            "单位制",
            ["公制 (km, m/s)", "英制 (mi, ft/s)"],
            horizontal=True
        )
        
        # 自动保存
        auto_save = st.checkbox("自动保存配置", value=True)
        
        # 更新用户设置
        st.session_state.user_settings.update({
            "theme": theme.lower(),
            "units": "metric" if "公制" in units else "imperial",
            "auto_save": auto_save
        })
        
        st.markdown("---")
        
        # 快速操作
        st.markdown(
            """
            <div class="sidebar-section">
                <h4>⚡ 快速操作</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 刷新数据", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("💾 保存配置", use_container_width=True):
                save_configuration()
        
        if st.button("🚀 开始新仿真", use_container_width=True, type="primary"):
            st.switch_page("pages/6_🚀_仿真运行.py")
        
        st.markdown("---")
        
        # 系统信息
        show_system_info()

def save_configuration():
    """保存配置"""
    import json
    from pathlib import Path
    
    config_data = {
        "radar_configs": st.session_state.get("radar_configs", []),
        "target_configs": st.session_state.get("target_configs", []),
        "simulation_config": st.session_state.get("simulation_config", {}),
        "user_settings": st.session_state.get("user_settings", {}),
        "save_time": datetime.now().isoformat()
    }
    
    config_dir = Path("data/configs")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    st.success(f"配置已保存: {config_file.name}")

def show_system_info():
    """显示系统信息"""
    import psutil
    import platform
    
    st.markdown(
        """
        <div class="sidebar-section">
            <h4>📊 系统状态</h4>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # CPU使用率
    cpu_percent = psutil.cpu_percent()
    st.progress(cpu_percent/100, text=f"CPU: {cpu_percent:.1f}%")
    
    # 内存使用率
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    st.progress(memory_percent/100, text=f"内存: {memory_percent:.1f}%")
    
    # 磁盘使用率
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    st.progress(disk_percent/100, text=f"磁盘: {disk_percent:.1f}%")
    
    # 系统信息
    st.markdown(
        f"""
        <div class="system-info">
            <small>
                <strong>系统:</strong> {platform.system()} {platform.release()}<br>
                <strong>Python:</strong> {platform.python_version()}<br>
                <strong>内存:</strong> {memory.used//(1024**3)}/{memory.total//(1024**3)} GB
            </small>
        </div>
        """,
        unsafe_allow_html=True
    )