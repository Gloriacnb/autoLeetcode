"""智谱 AI (bigmodel.cn) 客户端实现"""

import base64
from typing import Optional

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.api.exceptions import APIError

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ZhipuClient(BaseLLMClient):
    """智谱 AI API 客户端"""

    # 智谱 AI 编程专用端点
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4/"

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI 库未安装，请运行: uv sync --extra zhipu")

        super().__init__(api_key, model_name, base_url)

        # 使用编程专用端点或自定义端点
        api_base = base_url if base_url else self.DEFAULT_BASE_URL
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def generate_code_from_screenshot(self, screenshot_path: str, prompt: str) -> str:
        """
        使用智谱 AI API 从截图生成代码

        Args:
            screenshot_path: 截图文件路径
            prompt: 提示词

        Returns:
            API 响应的原始文本

        Raises:
            APIError: API 调用失败
        """
        try:
            base64_image = self._encode_image(screenshot_path)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
            )

            if not response or not response.choices:
                raise APIError("智谱 AI API 返回空响应")

            return response.choices[0].message.content

        except Exception as e:
            raise APIError(f"智谱 AI API 调用失败: {e}")

    def fix_code(self, broken_code: str, error_message: str) -> str:
        """
        请求智谱 AI 修正代码

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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )

            if response and response.choices:
                return response.choices[0].message.content
            else:
                return broken_code
        except Exception:
            return broken_code
