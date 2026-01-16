"""
Kimi API工具 - 与Kimi大模型集成
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class KimiAPI:
    """Kimi API客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn/v1"):
        """初始化Kimi API客户端"""
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_scenario(self, prompt: str, **kwargs) -> Optional[Dict[str, Any]]:
        """生成战场想定"""
        try:
            # 构建系统提示
            system_prompt = """你是一个军事仿真专家，专门生成战场想定。请根据用户描述生成详细的战场想定配置，包括：
            1. 想定名称和类型
            2. 红蓝双方兵力配置
            3. 战场环境条件
            4. 雷达和目标参数
            5. 任务目标和约束
            
            请以JSON格式返回，包含以下字段：
            - name: 想定名称
            - type: 想定类型
            - region: 战场区域
            - time: 想定时间
            - red_forces: 红方兵力配置
            - blue_forces: 蓝方兵力配置
            - environment: 环境条件
            - mission_description: 任务描述
            - radar_configs: 雷达配置列表
            - target_configs: 目标配置列表
            
            确保所有参数符合军事仿真要求。"""
            
            # 构建消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # API参数
            params = {
                "model": "moonshot-v1-8k",
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000)
            }
            
            # 调用API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=params,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 提取生成的文本
            content = result["choices"][0]["message"]["content"]
            
            # 尝试从文本中提取JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个内容
                json_str = content
            
            # 解析JSON
            scenario_data = json.loads(json_str)
            
            logger.info(f"成功生成想定: {scenario_data.get('name')}")
            return scenario_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"原始内容: {content}")
            return None
        except Exception as e:
            logger.error(f"生成想定时发生错误: {e}")
            return None
    
    def analyze_performance(self, metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析性能数据"""
        try:
            # 构建系统提示
            system_prompt = """你是一个军事仿真性能分析专家。请分析提供的性能指标数据，提供：
            1. 性能概况总结
            2. 关键发现
            3. 改进建议
            4. 风险评估
            
            以JSON格式返回分析结果。"""
            
            # 准备数据
            data_str = json.dumps(metrics_data, ensure_ascii=False, indent=2)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下性能数据：\n\n{data_str}"}
            ]
            
            params = {
                "model": "moonshot-v1-8k",
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 1500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=params,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                analysis = {"analysis": content}
            
            return analysis
            
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
            return None
    
    def optimize_configuration(self, current_config: Dict[str, Any], 
                              performance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """优化配置参数"""
        try:
            system_prompt = """你是一个雷达系统优化专家。根据当前配置和性能数据，提供优化建议：
            1. 识别性能瓶颈
            2. 建议参数调整
            3. 预期改进效果
            4. 实施注意事项"""
            
            config_str = json.dumps(current_config, ensure_ascii=False, indent=2)
            perf_str = json.dumps(performance_data, ensure_ascii=False, indent=2)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"当前配置：\n{config_str}\n\n性能数据：\n{perf_str}"}
            ]
            
            params = {
                "model": "moonshot-v1-8k",
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 1500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=params,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            return {"optimization_suggestions": content}
            
        except Exception as e:
            logger.error(f"配置优化失败: {e}")
            return None


def generate_scenario_with_kimi(api_key: str, description: str, **kwargs) -> Optional[Dict[str, Any]]:
    """使用Kimi API生成想定"""
    kimi = KimiAPI(api_key)
    return kimi.generate_scenario(description, **kwargs)
  
  
  # test_key ="sk-y2fL6muUqPQbGphXV9ccUTd8S44XBYQ4IuSj3oIj14l8YZYl"