"""OCR 抽象基类"""

from abc import ABC, abstractmethod
from typing import list


class BaseOCRProcessor(ABC):
    """OCR 处理器抽象基类"""

    @abstractmethod
    def extract_text(self, image_path: str) -> str:
        """
        从图片中提取文本

        Args:
            image_path: 图片文件路径

        Returns:
            提取的原始文本
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """返回支持的语言列表"""
        pass
