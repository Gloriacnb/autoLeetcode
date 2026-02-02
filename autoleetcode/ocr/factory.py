"""OCR 处理器工厂"""

from autoleetcode.ocr.base import BaseOCRProcessor


class OCRProcessorFactory:
    """OCR 处理器工厂"""

    @staticmethod
    def create(engine: str = "paddleocr", **kwargs) -> BaseOCRProcessor:
        """
        创建 OCR 处理器实例

        Args:
            engine: OCR 引擎名称 (paddleocr, easyocr, tesseract)
            **kwargs: 引擎特定的参数

        Returns:
            OCR 处理器实例

        Raises:
            ValueError: 不支持的 OCR 引擎
        """
        if engine == "paddleocr":
            from autoleetcode.ocr.paddle_processor import PaddleOCRProcessor
            return PaddleOCRProcessor(**kwargs)
        else:
            raise ValueError(f"不支持的 OCR 引擎: {engine}")
