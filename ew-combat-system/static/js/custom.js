// 电子战仿真系统自定义JavaScript

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    initTooltips();
    
    // 初始化动画
    initAnimations();
    
    // 初始化图表
    initCharts();
});

// 工具提示初始化
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

// 显示工具提示
function showTooltip(event) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = event.target.dataset.tooltip;
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + window.scrollX}px`;
    tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 10}px`;
    
    event.target._tooltip = tooltip;
}

// 隐藏工具提示
function hideTooltip(event) {
    if (event.target._tooltip) {
        event.target._tooltip.remove();
        delete event.target._tooltip;
    }
}

// 动画初始化
function initAnimations() {
    // 为雷达元素添加扫描动画
    const radarElements = document.querySelectorAll('.radar-element');
    radarElements.forEach(element => {
        element.classList.add('radar-sweep');
    });
}

// 图表初始化
function initCharts() {
    // 这里可以添加图表初始化代码
    // 例如使用Chart.js或Plotly创建图表
}

// 格式化距离显示
function formatDistance(distanceKm) {
    if (distanceKm < 1) {
        return `${(distanceKm * 1000).toFixed(0)} m`;
    } else if (distanceKm < 1000) {
        return `${distanceKm.toFixed(1)} km`;
    } else {
        return `${(distanceKm / 1000).toFixed(1)} Mm`;
    }
}

// 格式化功率显示
function formatPower(powerW) {
    if (powerW < 1e-3) {
        return `${(powerW * 1e6).toFixed(1)} nW`;
    } else if (powerW < 1) {
        return `${(powerW * 1e3).toFixed(1)} mW`;
    } else if (powerW < 1e3) {
        return `${powerW.toFixed(1)} W`;
    } else if (powerW < 1e6) {
        return `${(powerW / 1e3).toFixed(1)} kW`;
    } else {
        return `${(powerW / 1e6).toFixed(1)} MW`;
    }
}

// 格式化频率显示
function formatFrequency(freqGHz) {
    if (freqGHz < 1e-3) {
        return `${(freqGHz * 1e6).toFixed(1)} kHz`;
    } else if (freqGHz < 1) {
        return `${(freqGHz * 1e3).toFixed(1)} MHz`;
    } else {
        return `${freqGHz.toFixed(1)} GHz`;
    }
}

// 导出功能
function exportToJSON(data, filename) {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
}

// 导入功能
function importFromJSON(file, callback) {
    const reader = new FileReader();
    
    reader.onload = function(event) {
        try {
            const data = JSON.parse(event.target.result);
            callback(null, data);
        } catch (error) {
            callback(error);
        }
    };
    
    reader.onerror = function(error) {
        callback(error);
    };
    
    reader.readAsText(file);
}