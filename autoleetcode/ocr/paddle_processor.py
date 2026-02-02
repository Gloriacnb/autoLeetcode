"""PaddleOCR 处理器实现"""

import logging
import os

from autoleetcode.ocr.base import BaseOCRProcessor
from autoleetcode.ocr.preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

# 禁用 oneDNN 以避免 Python 3.13 兼容性问题
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['OPENAI_AGENT_DISABLE'] = '1'

# 检查 PaddleOCR 是否可用
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR 未安装，请运行: uv sync --extra paddleocr")


class PaddleOCRProcessor(BaseOCRProcessor):
    """PaddleOCR 处理器"""

    def __init__(
        self,
        language: str = "ch",  # 中英文混合
        use_gpu: bool = False,
        preprocess: bool = True,
        preprocessing_options: list = None,
    ):
        """
        初始化 PaddleOCR 处理器

        Args:
            language: 语言设置 (ch=中英文, en=英文)
            use_gpu: 是否使用 GPU 加速
            preprocess: 是否启用图片预处理
            preprocessing_options: 预处理选项列表
        """
        if not PADDLEOCR_AVAILABLE:
            raise ImportError(
                "PaddleOCR 未安装，请运行: uv sync --extra paddleocr"
            )

        self.language = language
        self.use_gpu = use_gpu
        self.preprocess = preprocess
        self.preprocessing_options = preprocessing_options or [
            "adjust_dpi",
            "enhance_contrast",
            "remove_noise",
        ]

        # 初始化 PaddleOCR
        logger.info(f"初始化 PaddleOCR (语言={language}, GPU={use_gpu})")

        # 构建初始化参数，只包含支持的参数
        ocr_params = {
            'use_angle_cls': True,  # 使用方向分类器
            'lang': language,
        }

        # 添加 GPU 支持参数（如果需要）
        # 注意：新版本 PaddleOCR 可能不再支持 use_gpu 参数
        # GPU 支持通常通过安装 PaddlePaddle-GPU 版本自动启用

        self.ocr = PaddleOCR(**ocr_params)

    def extract_text(self, image_path: str) -> str:
        """
        从图片中提取文本

        Args:
            image_path: 图片文件路径

        Returns:
            提取的原始文本
        """
        # 1. 预处理图片
        processed_image_path = image_path
        if self.preprocess:
            logger.debug("开始图片预处理")
            processed_path = ImagePreprocessor.enhance_for_ocr(
                image_path,
                adjust_dpi="adjust_dpi" in self.preprocessing_options,
                enhance_contrast="enhance_contrast" in self.preprocessing_options,
                remove_noise="remove_noise" in self.preprocessing_options,
                adaptive_threshold=False,  # 默认不使用二值化，可能会影响识别
            )
            if processed_path:
                processed_image_path = processed_path

        # 2. 调用 PaddleOCR
        try:
            logger.debug(f"调用 PaddleOCR 识别: {processed_image_path}")
            # 注意：新版本 PaddleOCR 不支持 cls 参数，已在初始化时设置 use_angle_cls
            result = self.ocr.ocr(processed_image_path)

            # 3. 组合识别结果
            if not result or not result[0]:
                logger.warning("PaddleOCR 未识别到任何文本")
                return ""

            # PaddleOCR 返回格式: [[[bbox1], (text1, score1)], [[bbox2], (text2, score2)], ...]
            texts = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if text_info and len(text_info) >= 1:
                        text = text_info[0]
                        if text:
                            texts.append(text)

            extracted_text = "\n".join(texts)
            logger.info(f"OCR 提取完成，共 {len(texts)} 行文本")
            return extracted_text

        except NotImplementedError as e:
            # Python 3.13 兼容性问题
            error_msg = str(e)
            if 'ConvertPirAttribute2RuntimeAttribute' in error_msg or 'onednn' in error_msg.lower():
                logger.error("PaddleOCR 与当前 Python 版本不兼容")
                logger.error("建议：")
                logger.error("  1. 使用 Python 3.11 或 3.12（推荐 3.11）")
                logger.error("  2. 或使用 MODE=auto 让 LLM 直接处理图片")
                logger.error(f"详细错误: {e}")
                raise Exception(
                    "PaddleOCR 与 Python 3.13 不兼容。请使用 Python 3.11/3.12，或在配置中设置 MODE=auto。"
                ) from e
            else:
                logger.error(f"PaddleOCR 不支持的错误: {e}")
                raise
        except Exception as e:
            logger.error(f"PaddleOCR 识别失败: {e}")
            raise

    def get_supported_languages(self) -> list[str]:
        """
        返回支持的语言列表

        Returns:
            支持的语言代码列表
        """
        return ["ch", "en", "french", "german", "korean", "japan"]
