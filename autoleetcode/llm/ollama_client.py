"""Ollama API 客户端实现（本地模型）"""

import base64
from typing import Optional
import time
import logging

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.api.exceptions import APIError

logger = logging.getLogger(__name__)

try:
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class OllamaClient(BaseLLMClient):
    """Ollama API 客户端（本地模型）"""

    supports_vision = True

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama 库未安装，请运行: uv sync --extra ollama")

        # Ollama 不需要 api_key，base_url 默认为本地
        super().__init__(api_key or "dummy", model_name, base_url or "http://localhost:11434")
        self.client = Client(host=self.base_url)

    def generate_code_from_screenshot(self, screenshot_path: str, prompt: str) -> str:
        """
        使用 Ollama 从截图生成代码

        Args:
            screenshot_path: 截图文件路径
            prompt: 提示词

        Returns:
            API 响应的原始文本

        Raises:
            APIError: API 调用失败
        """
        try:
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            response = self.client.generate(
                model=self.model_name,
                prompt=f"{prompt}\n[图片已附上]",
                images=[image_data],
            )

            if not response or not response.get("response"):
                raise APIError("Ollama API 返回空响应")

            return response["response"]

        except Exception as e:
            raise APIError(f"Ollama API 调用失败: {e}")

    def generate_code_from_text(self, text: str, prompt: str) -> str:
        """
        从文本生成代码

        Args:
            text: 题目文本（Markdown 格式）
            prompt: 提示词

        Returns:
            API 响应的原始文本

        Raises:
            APIError: API 调用失败
        """
        try:
            full_prompt = f"{prompt}\n\n【题目内容】\n{text}"

            response = self.client.generate(
                model=self.model_name,
                prompt=full_prompt,
            )

            if not response or not response.get("response"):
                raise APIError("Ollama API 返回空响应")

            return response["response"]

        except Exception as e:
            raise APIError(f"Ollama API 调用失败: {e}")

    def fix_code(self, broken_code: str, error_message: str) -> str:
        """
        请求 Ollama 修正代码

        Args:
            broken_code: 有问题的代码
            error_message: 错误信息

        Returns:
            修正后的代码
        """
        prompt = f"""
        以下是一个有问题的 Python 代码：
        ```python
        {broken_code}
        ```

        当运行这段代码时，出现了以下错误：
        ```
        {error_message}
        ```

        请修正这个错误，并只返回完整的、修正后的 Python 代码。
        """

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
            )

            if response and response.get("response"):
                return response["response"]
            else:
                return broken_code
        except Exception:
            return broken_code

    def verify_connection(self) -> dict:
        """
        验证 Ollama API 连接和配置

        Returns:
            dict: 验证结果字典
        """
        provider = "OLLAMA"
        model = self.model_name
        start_time = time.time()

        try:
            # 首先检查本地服务是否运行
            import requests
            try:
                # 尝试连接 Ollama 服务
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                return {
                    'success': False,
                    'message': '无法连接到 Ollama 服务',
                    'provider': provider,
                    'model': model,
                    'latency_ms': (time.time() - start_time) * 1000,
                    'details': {
                        'error_type': 'ConnectionError',
                        'suggestion': '请确保 Ollama 服务正在运行: ollama serve'
                    },
                    'error': Exception('Ollama service not running')
                }
            except requests.exceptions.Timeout:
                return {
                    'success': False,
                    'message': '连接 Ollama 服务超时',
                    'provider': provider,
                    'model': model,
                    'latency_ms': (time.time() - start_time) * 1000,
                    'details': {
                        'error_type': 'Timeout',
                        'suggestion': '请检查 Ollama 服务是否正常运行'
                    },
                    'error': Exception('Connection timeout')
                }

            # 检查模型是否已安装
            models_data = response.json()
            installed_models = [m['name'] for m in models_data.get('models', [])]

            # Ollama 模型名称可能包含 tag (e.g., "llama2:latest")
            model_name_without_tag = model.split(':')[0]
            is_installed = any(m.split(':')[0] == model_name_without_tag or m == model for m in installed_models)

            if not is_installed:
                return {
                    'success': False,
                    'message': f'模型 {model} 未安装',
                    'provider': provider,
                    'model': model,
                    'latency_ms': (time.time() - start_time) * 1000,
                    'details': {
                        'error_type': 'ModelNotFound',
                        'installed_models': installed_models,
                        'suggestion': f'请运行: ollama pull {model}'
                    },
                    'error': Exception(f'Model {model} not found')
                }

            # 发送一个简单的测试请求
            test_response = self.client.generate(
                model=self.model_name,
                prompt="Hi",
            )

            latency_ms = (time.time() - start_time) * 1000

            if test_response and test_response.get("response"):
                return {
                    'success': True,
                    'message': '连接成功',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': {
                        'response_preview': test_response.get("response", "")[:100],
                        'installed_models': installed_models
                    },
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'message': 'API 返回空响应',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': None,
                    'error': Exception('Empty response')
                }

        except ImportError:
            return {
                'success': False,
                'message': 'requests 库未安装',
                'provider': provider,
                'model': model,
                'latency_ms': (time.time() - start_time) * 1000,
                'details': {
                    'suggestion': '请安装 requests 库: pip install requests'
                },
                'error': Exception('requests not installed')
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'连接失败: {str(e)}',
                'provider': provider,
                'model': model,
                'latency_ms': (time.time() - start_time) * 1000,
                'details': None,
                'error': e
            }
