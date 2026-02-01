"""Gemini API 客户端实现"""

import google.generativeai as genai
import google.api_core.exceptions
from PIL import Image
from typing import Optional
import os
import io
import tempfile

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.api.exceptions import APIError

# 注册 HEIF 格式支持
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False


class GeminiClient(BaseLLMClient):
    """Gemini API 客户端"""

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        super().__init__(api_key, model_name, base_url)
        genai.configure(api_key=api_key)
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
            # 验证文件可以打开
            try:
                img = Image.open(screenshot_path)
                img.verify()  # 验证图片完整性
                # 重新打开，因为 verify() 会关闭文件
                img = Image.open(screenshot_path)
            except Exception as e:
                raise APIError(f"无法打开或验证图片文件 '{screenshot_path}': {e}")

            response = self.model.generate_content([prompt, img])

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
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text
            else:
                return broken_code
        except Exception:
            # 如果修正失败，返回原始代码
            return broken_code
