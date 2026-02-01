"""LLM 客户端工厂"""

from typing import Optional

from autoleetcode.llm.base import BaseLLMClient
from autoleetcode.llm.gemini_client import GeminiClient
from autoleetcode.llm.openai_client import OpenAIClient
from autoleetcode.llm.anthropic_client import AnthropicClient
from autoleetcode.llm.ollama_client import OllamaClient
from autoleetcode.api.exceptions import ConfigurationError


class LLMClientFactory:
    """LLM 客户端工厂"""

    SUPPORTED_PROVIDERS = {
        "gemini": GeminiClient,
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "ollama": OllamaClient,
    }

    @classmethod
    def create(
        cls, provider: str, api_key: str, model_name: str, base_url: Optional[str] = None
    ) -> BaseLLMClient:
        """
        创建 LLM 客户端实例

        Args:
            provider: 提供商名称 ('gemini', 'openai', 'anthropic', 'ollama')
            api_key: API 密钥
            model_name: 模型名称
            base_url: 可选的自定义 API 端点

        Returns:
            BaseLLMClient 实例

        Raises:
            ConfigurationError: 不支持的提供商
        """
        provider = provider.lower()

        if provider not in cls.SUPPORTED_PROVIDERS:
            raise ConfigurationError(
                f"不支持的 LLM 提供商: {provider}. "
                f"支持的提供商: {', '.join(cls.SUPPORTED_PROVIDERS.keys())}"
            )

        client_class = cls.SUPPORTED_PROVIDERS[provider]
        return client_class(api_key=api_key, model_name=model_name, base_url=base_url)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """获取支持的提供商列表"""
        return list(cls.SUPPORTED_PROVIDERS.keys())
