"""OCR 文本提取模块

支持多种 OCR 引擎从 LeetCode 截图中提取题目文本。
"""

from autoleetcode.ocr.base import BaseOCRProcessor
from autoleetcode.ocr.factory import OCRProcessorFactory

__all__ = ["BaseOCRProcessor", "OCRProcessorFactory"]
