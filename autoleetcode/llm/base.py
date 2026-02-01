"""LLM 客户端抽象基类"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥
            model_name: 模型名称
            base_url: 可选的自定义 API 端点
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url

    @abstractmethod
    def generate_code_from_screenshot(self, screenshot_path: str, prompt: str) -> str:
        """
        从截图生成代码

        Args:
            screenshot_path: 截图文件路径
            prompt: 提示词

        Returns:
            API 响应的原始文本
        """
        pass

    @abstractmethod
    def fix_code(self, broken_code: str, error_message: str) -> str:
        """
        请求修正代码

        Args:
            broken_code: 有问题的代码
            error_message: 错误信息

        Returns:
            修正后的代码
        """
        pass
