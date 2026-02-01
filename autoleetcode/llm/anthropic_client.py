"""Anthropic Claude API 客户端实现"""

from typing import Optional

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.api.exceptions import APIError

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API 客户端"""

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic 库未安装，请运行: uv sync --extra anthropic")

        super().__init__(api_key, model_name, base_url)
        if base_url:
            self.client = Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = Anthropic(api_key=api_key)

    def generate_code_from_screenshot(self, screenshot_path: str, prompt: str) -> str:
        """
        使用 Anthropic API 从截图生成代码

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
                image_data = f.read()

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data,
                                },
                            },
                        ],
                    }
                ],
            )

            if not response or not response.content:
                raise APIError("Anthropic API 返回空响应")

            return response.content[0].text

        except Exception as e:
            raise APIError(f"Anthropic API 调用失败: {e}")

    def fix_code(self, broken_code: str, error_message: str) -> str:
        """
        请求 Anthropic 修正代码

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
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            if response and response.content:
                return response.content[0].text
            else:
                return broken_code
        except Exception:
            return broken_code
