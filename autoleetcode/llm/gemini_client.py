"""Gemini API 客户端实现"""

import google.generativeai as genai
import google.api_core.exceptions
from PIL import Image
from typing import Optional
import os
import io
import tempfile
import logging
import time

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.api.exceptions import APIError

logger = logging.getLogger(__name__)

# API 调用超时时间（毫秒）
DEFAULT_TIMEOUT_MS = 3 * 60 * 1000  # 3 分钟

# 注册 HEIF 格式支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False


class GeminiClient(BaseLLMClient):
    """Gemini API 客户端"""

    supports_vision = True

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        super().__init__(api_key, model_name, base_url)

        # 清理 API key（去除可能的空格和换行符）
        clean_api_key = api_key.strip()

        # 记录 API key 的前8个字符用于调试（不记录完整 key）
        key_preview = clean_api_key[:8] if len(clean_api_key) > 8 else clean_api_key
        logger.info(f"配置 Gemini API (key 前8位: {key_preview}...)")

        # 配置 API key
        genai.configure(api_key=clean_api_key)

        # 配置超时选项（兼容不同版本的库）
        try:
            self.http_options = genai.types.HttpOptions(timeout=DEFAULT_TIMEOUT_MS)
        except AttributeError:
            # 旧版本可能不支持 HttpOptions
            self.http_options = None

        self.model = genai.GenerativeModel(model_name)

        if not HEIF_AVAILABLE:
            print("警告: pillow-heif 未安装，可能无法处理 macOS HEIF 格式截图")
            print("安装方法: uv sync (pillow-heif 已添加到依赖)")

    def generate_code_from_screenshot(self, screenshot_path: str, prompt: str) -> str:
        """
        使用 Gemini API 从截图生成代码

        Args:
            screenshot_path: 截图文件路径
            prompt: 提示词

        Returns:
            API 响应的原始文本

        Raises:
            APIError: API 调用失败
        """
        try:
            logger.info(f"正在加载图片: {screenshot_path}")
            # 验证文件可以打开
            try:
                img = Image.open(screenshot_path)
                img.verify()  # 验证图片完整性
                # 重新打开，因为 verify() 会关闭文件
                img = Image.open(screenshot_path)
            except Exception as e:
                raise APIError(f"无法打开或验证图片文件 '{screenshot_path}': {e}")

            logger.info(f"正在调用 Gemini API (超时: {DEFAULT_TIMEOUT_MS/1000}秒)...")

            # 构建请求参数
            kwargs = {
                "generation_config": genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            }

            # 如果支持 http_options，添加它
            if self.http_options is not None:
                kwargs["request_options"] = genai.RequestOptions(http_options=self.http_options)

            response = self.model.generate_content([prompt, img], **kwargs)
            logger.info("Gemini API 响应已接收")

            if not (response and response.text):
                raise APIError("Gemini API 返回空响应")

            return response.text

        except APIError:
            raise  # 重新抛出我们的 API 错误
        except google.api_core.exceptions.ResourceExhausted as e:
            raise APIError(f"Gemini API 配额已用尽: {e}")
        except google.api_core.exceptions.InvalidArgument as e:
            raise APIError(f"Gemini API 参数无效: {e}")
        except Exception as e:
            raise APIError(f"Gemini API 调用失败: {e}")

    def fix_code(self, broken_code: str, error_message: str) -> str:
        """
        请求 Gemini 修正代码

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

        请修正这个错误，并只返回完整的、修正后的 Python 代码，不要包含任何额外的解释或 markdown 格式。
        """

        try:
            logger.info(f"正在调用 Gemini API 修正代码 (超时: {DEFAULT_TIMEOUT_MS/1000}秒)...")

            # 构建请求参数
            kwargs = {}
            if self.http_options is not None:
                kwargs["request_options"] = genai.RequestOptions(http_options=self.http_options)

            response = self.model.generate_content(prompt, **kwargs)
            logger.info("Gemini API 修正响应已接收")
            if response and response.text:
                return response.text
            else:
                return broken_code
        except Exception:
            # 如果修正失败，返回原始代码
            logger.warning("代码修正失败，返回原始代码")
            return broken_code

    def verify_connection(self) -> dict:
        """
        验证 Gemini API 连接和配置

        Returns:
            dict: 验证结果字典
        """
        provider = "GEMINI"
        model = self.model_name
        start_time = time.time()

        try:
            # 发送一个简单的测试请求
            # 注意：这里使用简化的调用方式以兼容不同版本的库
            test_response = self.model.generate_content("Hello")

            latency_ms = (time.time() - start_time) * 1000

            if test_response and test_response.text:
                return {
                    'success': True,
                    'message': '连接成功',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': {'response_preview': test_response.text[:100]},
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

        except google.api_core.exceptions.InvalidArgument as e:
            return {
                'success': False,
                'message': 'API Key 无效或参数错误',
                'provider': provider,
                'model': model,
                'latency_ms': (time.time() - start_time) * 1000,
                'details': {'error_type': 'InvalidArgument'},
                'error': e
            }

        except google.api_core.exceptions.PermissionDenied as e:
            return {
                'success': False,
                'message': 'API Key 无权限或已过期',
                'provider': provider,
                'model': model,
                'latency_ms': (time.time() - start_time) * 1000,
                'details': {'error_type': 'PermissionDenied'},
                'error': e
            }

        except google.api_core.exceptions.ResourceExhausted as e:
            return {
                'success': False,
                'message': 'API 配额已用尽',
                'provider': provider,
                'model': model,
                'latency_ms': (time.time() - start_time) * 1000,
                'details': {
                    'error_type': 'ResourceExhausted',
                    'suggestion': '请检查 https://aistudio.google.com/app/apikey_usage'
                },
                'error': e
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
