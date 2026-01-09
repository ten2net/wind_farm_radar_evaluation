"""
数据管理模块
"""
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import yaml
import csv
import h5py
import warnings
warnings.filterwarnings('ignore')

class DataManager:
    """数据管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        self.results_dir = self.data_dir / "results"
        self.temp_dir = self.data_dir / "temp"
        self.cache_dir = self.data_dir / "cache"
        
        # 创建子目录
        for directory in [self.results_dir, self.temp_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_simulation_results(self, results: Dict[str, Any], 
                              scenario_name: str = None) -> str:
        """保存仿真结果"""
        if scenario_name is None:
            scenario_name = results.get('scenario_name', 'unknown')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{scenario_name}_{timestamp}"
        
        # 保存为JSON
        json_path = self.results_dir / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 保存为CSV（如果包含表格数据）
        if 'radar_results' in results:
            csv_path = self.results_dir / f"{filename}_radar_results.csv"
            df = pd.DataFrame(results['radar_results'])
            df.to_csv(csv_path, index=False, encoding='utf-8')
        
        if 'jammer_results' in results:
            csv_path = self.results_dir / f"{filename}_jammer_results.csv"
            df = pd.DataFrame(results['jammer_results'])
            df.to_csv(csv_path, index=False, encoding='utf-8')
        
        return str(json_path)
    
    def load_simulation_results(self, filepath: str) -> Optional[Dict[str, Any]]:
        """加载仿真结果"""
        path = Path(filepath)
        
        if not path.exists():
            return None
        
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif path.suffix == '.csv':
            df = pd.read_csv(path)
            return df.to_dict('records')
        else:
            return None
    
    def save_entity_data(self, entities: Dict[str, List], 
                        filename: str = None) -> str:
        """保存实体数据"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"entities_{timestamp}"
        
        # 转换为可序列化的格式
        serializable_entities = {}
        for entity_type, entity_list in entities.items():
            serializable_entities[entity_type] = [
                entity.to_dict() if hasattr(entity, 'to_dict') else dict(entity)
                for entity in entity_list
            ]
        
        # 保存
        filepath = self.data_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_entities, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def load_entity_data(self, filepath: str) -> Dict[str, List]:
        """加载实体数据"""
        path = Path(filepath)
        
        if not path.exists():
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def save_to_hdf5(self, data: Dict[str, np.ndarray], 
                    filename: str) -> str:
        """保存到HDF5文件"""
        filepath = self.data_dir / f"{filename}.h5"
        
        with h5py.File(filepath, 'w') as f:
            for key, value in data.items():
                f.create_dataset(key, data=value)
        
        return str(filepath)
    
    def load_from_hdf5(self, filepath: str) -> Dict[str, np.ndarray]:
        """从HDF5文件加载"""
        path = Path(filepath)
        
        if not path.exists():
            return {}
        
        data = {}
        with h5py.File(path, 'r') as f:
            for key in f.keys():
                data[key] = f[key][:]
        
        return data
    
    def cache_data(self, key: str, data: Any, 
                  expire_seconds: int = 3600) -> None:
        """缓存数据"""
        cache_data = {
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'expire_seconds': expire_seconds
        }
        
        cache_path = self.cache_dir / f"{key}.pkl"
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        cache_path = self.cache_dir / f"{key}.pkl"
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 检查是否过期
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            expire_seconds = cache_data.get('expire_seconds', 3600)
            
            if (datetime.now() - cache_time).seconds > expire_seconds:
                # 删除过期缓存
                cache_path.unlink()
                return None
            
            return cache_data['data']
        except Exception:
            return None
    
    def clear_cache(self, pattern: str = "*") -> None:
        """清理缓存"""
        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
            except Exception:
                pass
    
    def export_to_excel(self, data_dict: Dict[str, pd.DataFrame], 
                       filename: str) -> str:
        """导出到Excel"""
        filepath = self.results_dir / f"{filename}.xlsx"
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        
        return str(filepath)
    
    def import_from_excel(self, filepath: str) -> Dict[str, pd.DataFrame]:
        """从Excel导入"""
        path = Path(filepath)
        
        if not path.exists():
            return {}
        
        data = {}
        try:
            xls = pd.ExcelFile(path)
            for sheet_name in xls.sheet_names:
                data[sheet_name] = pd.read_excel(xls, sheet_name)
        except Exception as e:
            print(f"导入Excel失败: {e}")
        
        return data
    
    def backup_data(self, backup_name: str = None) -> str:
        """备份数据"""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_dir = self.data_dir / "backups" / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份结果文件
        for result_file in self.results_dir.glob("*.json"):
            try:
                backup_file = backup_dir / result_file.name
                backup_file.write_bytes(result_file.read_bytes())
            except Exception as e:
                print(f"备份文件失败 {result_file}: {e}")
        
        # 备份配置文件
        config_dir = Path("config")
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                try:
                    backup_file = backup_dir / f"config_{config_file.name}"
                    backup_file.write_bytes(config_file.read_bytes())
                except Exception as e:
                    print(f"备份配置文件失败 {config_file}: {e}")
        
        return str(backup_dir)
    
    def restore_backup(self, backup_path: str) -> bool:
        """恢复备份"""
        backup_dir = Path(backup_path)
        
        if not backup_dir.exists():
            return False
        
        try:
            # 恢复结果文件
            for backup_file in backup_dir.glob("*.json"):
                if not backup_file.name.startswith("config_"):
                    result_file = self.results_dir / backup_file.name
                    result_file.write_bytes(backup_file.read_bytes())
            
            # 恢复配置文件
            for backup_file in backup_dir.glob("config_*.yaml"):
                config_file = Path("config") / backup_file.name[7:]  # 移除"config_"前缀
                config_file.parent.mkdir(parents=True, exist_ok=True)
                config_file.write_bytes(backup_file.read_bytes())
            
            return True
        except Exception as e:
            print(f"恢复备份失败: {e}")
            return False
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        stats = {
            'total_results': 0,
            'total_size_mb': 0.0,
            'file_types': {},
            'recent_files': []
        }
        
        # 统计结果文件
        for result_file in self.results_dir.glob("*"):
            if result_file.is_file():
                stats['total_results'] += 1
                stats['total_size_mb'] += result_file.stat().st_size / (1024 * 1024)
                
                # 统计文件类型
                file_type = result_file.suffix.lower()
                stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1
                
                # 记录最近文件
                mtime = datetime.fromtimestamp(result_file.stat().st_mtime)
                stats['recent_files'].append({
                    'name': result_file.name,
                    'size_mb': result_file.stat().st_size / (1024 * 1024),
                    'modified': mtime.isoformat()
                })
        
        # 按修改时间排序
        stats['recent_files'].sort(key=lambda x: x['modified'], reverse=True)
        stats['recent_files'] = stats['recent_files'][:10]  # 只保留最近10个
        
        return stats
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """清理旧文件"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        deleted_count = 0
        
        for result_file in self.results_dir.glob("*"):
            if result_file.is_file() and result_file.stat().st_mtime < cutoff_time:
                try:
                    result_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"删除文件失败 {result_file}: {e}")
        
        return deleted_count
    
    def export_summary_report(self, output_format: str = "html") -> str:
        """导出数据摘要报告"""
        stats = self.get_data_statistics()
        
        if output_format == "html":
            return self._generate_html_report(stats)
        elif output_format == "markdown":
            return self._generate_markdown_report(stats)
        else:
            return json.dumps(stats, indent=2)
    
    def _generate_html_report(self, stats: Dict) -> str:
        """生成HTML报告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>数据管理报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>数据管理报告</h1>
            <p>生成时间: {datetime.now().isoformat()}</p>
            
            <h2>统计概览</h2>
            <ul>
                <li>总结果文件数: {stats['total_results']}</li>
                <li>总数据大小: {stats['total_size_mb']:.2f} MB</li>
            </ul>
            
            <h2>文件类型统计</h2>
            <table>
                <tr><th>文件类型</th><th>数量</th></tr>
        """
        
        for file_type, count in stats['file_types'].items():
            html += f"<tr><td>{file_type}</td><td>{count}</td></tr>"
        
        html += """
            </table>
            
            <h2>最近文件</h2>
            <table>
                <tr><th>文件名</th><th>大小(MB)</th><th>修改时间</th></tr>
        """
        
        for file_info in stats['recent_files']:
            html += f"<tr><td>{file_info['name']}</td><td>{file_info['size_mb']:.2f}</td><td>{file_info['modified']}</td></tr>"
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _generate_markdown_report(self, stats: Dict) -> str:
        """生成Markdown报告"""
        markdown = f"""# 数据管理报告
        
生成时间: {datetime.now().isoformat()}

## 统计概览
- 总结果文件数: {stats['total_results']}
- 总数据大小: {stats['total_size_mb']:.2f} MB

## 文件类型统计
| 文件类型 | 数量 |
|---------|------|
"""
        
        for file_type, count in stats['file_types'].items():
            markdown += f"| {file_type} | {count} |\n"
        
        markdown += """
## 最近文件
| 文件名 | 大小(MB) | 修改时间 |
|--------|----------|----------|
"""
        
        for file_info in stats['recent_files']:
            markdown += f"| {file_info['name']} | {file_info['size_mb']:.2f} | {file_info['modified']} |\n"
        
        return markdown
