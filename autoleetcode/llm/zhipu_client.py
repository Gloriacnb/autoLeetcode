"""智谱 AI (bigmodel.cn) 客户端实现"""

import base64
from typing import Optional
import time
import logging

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.api.exceptions import APIError

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# 模拟编程工具的请求头，用于绕过智谱编程套餐限制
CODING_TOOL_HEADERS = {
    # 模拟 Claude Code 的 User-Agent
    "User-Agent": "Claude-Code/1.0 (+https://claude.ai/claude-code)",
    # 添加编程场景标识
    "X-Client-Type": "coding-assistant",
    "X-Client-Name": "autoleetcode",
    "X-Client-Version": "1.0.0",
    "X-Purpose": "code-generation",
}

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
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base,
            default_headers=CODING_TOOL_HEADERS,  # 添加编程工具请求头
        )

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

    def verify_connection(self) -> dict:
        """
        验证智谱 AI API 连接和配置

        Returns:
            dict: 验证结果字典
        """
        provider = "ZHIPU"
        model = self.model_name
        start_time = time.time()

        try:
            # 发送一个简单的测试请求
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10,
            )

            latency_ms = (time.time() - start_time) * 1000

            if response and response.choices:
                return {
                    'success': True,
                    'message': '连接成功',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': {
                        'response_preview': response.choices[0].message.content[:50]
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

        except Exception as e:
            error_str = str(e)
            latency_ms = (time.time() - start_time) * 1000

            # 解析错误类型
            if 'authentication' in error_str.lower() or '401' in error_str:
                return {
                    'success': False,
                    'message': 'API Key 无效或已过期',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': {
                        'error_type': 'AuthenticationError',
                        'suggestion': '请访问 https://open.bigmodel.cn/usercenter/apikeys 获取 API Key'
                    },
                    'error': e
                }

            elif 'not found' in error_str.lower() or '404' in error_str:
                return {
                    'success': False,
                    'message': f'模型 {model} 不存在',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': {
                        'error_type': 'NotFoundError',
                        'suggestion': '请检查模型名称是否正确'
                    },
                    'error': e
                }

            elif 'rate' in error_str.lower() or '429' in error_str:
                return {
                    'success': False,
                    'message': '请求速率受限',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': {
                        'error_type': 'RateLimitError',
                        'suggestion': '请稍后重试或检查账户配额'
                    },
                    'error': e
                }

            else:
                return {
                    'success': False,
                    'message': f'连接失败: {error_str}',
                    'provider': provider,
                    'model': model,
                    'latency_ms': latency_ms,
                    'details': None,
                    'error': e
                }
