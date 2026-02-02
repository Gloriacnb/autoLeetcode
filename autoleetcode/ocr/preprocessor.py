"""图片预处理工具

通过增强图片质量提升 OCR 准确率。
"""

import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 依赖检查
try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL 未安装，图片预处理功能不可用")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV 未安装，高级图片预处理功能不可用")


class ImagePreprocessor:
    """图片预处理工具"""

    @staticmethod
    def enhance_for_ocr(
        image_path: str,
        adjust_dpi: bool = True,
        enhance_contrast: bool = True,
        remove_noise: bool = True,
        adaptive_threshold: bool = False,
        target_dpi: int = 300,
        contrast_factor: float = 1.5,
        max_size: int = 4000,  # PaddleOCR 推荐的最大尺寸
    ) -> Optional[str]:
        """
        增强图片以提高 OCR 准确率

        处理步骤：
        1. 调整分辨率到目标 DPI
        2. 增强对比度
        3. 去噪
        4. 自适应二值化（可选）

        Args:
            image_path: 原始图片路径
            adjust_dpi: 是否调整分辨率
            enhance_contrast: 是否增强对比度
            remove_noise: 是否去噪
            adaptive_threshold: 是否进行自适应二值化
            target_dpi: 目标 DPI
            contrast_factor: 对比度增强因子

        Returns:
            处理后的临时图片路径，如果处理失败返回 None
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL 未安装，跳过图片预处理")
            return None

        try:
            # 打开图片
            img = Image.open(image_path)

            # 转换为 RGB 模式（如果是 RGBA 或其他模式）
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 0. 首先检查并调整图片大小（在所有其他处理之前）
            # PaddleOCR 推荐最大尺寸为 4000
            if max(img.width, img.height) > max_size:
                # 计算缩放比例，保持宽高比
                if img.width > img.height:
                    new_width = max_size
                    new_height = int(img.height * (max_size / img.width))
                else:
                    new_height = max_size
                    new_width = int(img.width * (max_size / img.height))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"图片大小已调整为: {new_width}x{new_height}")

            # 1. 调整分辨率
            if adjust_dpi:
                img = ImagePreprocessor._adjust_dpi(img, target_dpi)

            # 2. 增强对比度
            if enhance_contrast:
                img = ImagePreprocessor._enhance_contrast(img, contrast_factor)

            # 3. 去噪
            if remove_noise:
                img = ImagePreprocessor._remove_noise(img)

            # 4. 自适应二值化（需要 OpenCV）
            if adaptive_threshold and CV2_AVAILABLE:
                # 转换为 OpenCV 格式
                img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
                img_array = ImagePreprocessor._adaptive_threshold(img_array)
                # 转回 PIL
                img = Image.fromarray(img_array)

            # 保存到临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
            img.save(temp_path, "PNG")
            Path(temp_path).close() if hasattr(Path(temp_path), 'close') else None

            import os
            os.close(temp_fd)

            logger.debug(f"图片预处理完成: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"图片预处理失败: {e}")
            return None

    @staticmethod
    def _adjust_dpi(image: Image.Image, target_dpi: int = 300) -> Image.Image:
        """
        调整图片分辨率

        Args:
            image: PIL 图片对象
            target_dpi: 目标 DPI

        Returns:
            调整后的图片
        """
        # 获取当前 DPI（如果有的话）
        current_dpi = image.info.get('dpi', (72, 72))[0]

        if current_dpi >= target_dpi:
            return image

        # 计算缩放比例
        scale = target_dpi / current_dpi
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)

        # 使用高质量的 LANCZOS 重采样
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def _enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
        """
        增强对比度

        Args:
            image: PIL 图片对象
            factor: 增强因子（1.0 = 无变化，>1.0 = 增强对比度）

        Returns:
            增强后的图片
        """
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    @staticmethod
    def _remove_noise(image: Image.Image) -> Image.Image:
        """
        去噪

        Args:
            image: PIL 图片对象

        Returns:
            去噪后的图片
        """
        # 使用中值滤波器去噪
        return image.filter(ImageFilter.MedianFilter(size=3))

    @staticmethod
    def _adaptive_threshold(image_array, block_size: int = 11, C: int = 2):
        """
        自适应二值化（需要 OpenCV）

        Args:
            image_array: OpenCV 图片数组（灰度图）
            block_size: 邻域块大小（必须是奇数）
            C: 从均值或加权均值中减去的常数

        Returns:
            二值化后的图片数组
        """
        if not CV2_AVAILABLE:
            return image_array

        # 确保块大小是奇数
        if block_size % 2 == 0:
            block_size += 1

        # 自适应阈值
        return cv2.adaptiveThreshold(
            image_array,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,
            C,
        )
