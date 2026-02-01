"""Ollama API 客户端实现（本地模型）"""

import base64
from typing import Optional

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.api.exceptions import APIError

try:
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class OllamaClient(BaseLLMClient):
    """Ollama API 客户端（本地模型）"""

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
