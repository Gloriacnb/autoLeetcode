"""路径工具"""

import re
import os
from pathlib import Path
import logging

from autoleetcode.api.exceptions import FileHandlingError

logger = logging.getLogger("autoleetcode")


class PathUtils:
    """安全路径操作工具"""

    @staticmethod
    def sanitize_filename(title: str) -> str:
        """
        清理标题以创建安全的文件名

        Args:
            title: 问题标题

        Returns:
            清理后的文件名（不含扩展名）
        """
        # 移除非字母数字字符（除了空格和连字符）
        cleaned = re.sub(r"[^\w\s-]", "", title).strip()
        # 用下划线替换空格
        cleaned = re.sub(r"\s+", "_", cleaned)

        if not cleaned:
            logger.warning(f"标题 '{title}' 产生空文件名，使用默认值")
            return "untitled"

        return cleaned

    @staticmethod
    def get_code_path(output_dir: Path, title: str, screenshot_path: str) -> Path:
        """
        从截图和标题生成安全的代码路径

        Args:
            output_dir: 代码输出目录
            title: 问题标题
            screenshot_path: 原始截图路径

        Returns:
            解析后的 Path 对象

        Raises:
            FileHandlingError: 检测到路径遍历尝试
        """
        output_dir = Path(output_dir).resolve()

        # 清理标题
        sanitized_title = PathUtils.sanitize_filename(title)
        if not sanitized_title:
            sanitized_title = Path(screenshot_path).stem

        code_filename = f"{sanitized_title}.py"
        code_path = (output_dir / code_filename).resolve()

        # 确保路径在输出目录内（防止遍历攻击）
        try:
            code_path.relative_to(output_dir)
        except ValueError:
            logger.error(f"检测到路径遍历尝试: {code_path}")
            raise FileHandlingError(
                f"生成的路径 '{code_path}' 在输出目录之外"
            )

        logger.debug(f"生成代码路径: {code_path}")
        return code_path

    @staticmethod
    def validate_screenshot(
        screenshot_path: str, allowed_extensions: set, max_size_mb: int
    ) -> bool:
        """
        验证截图文件是否可以安全处理

        Args:
            screenshot_path: 截图路径
            allowed_extensions: 允许的文件扩展名集合
            max_size_mb: 最大文件大小（MB）

        Returns:
            True

        Raises:
            FileHandlingError: 验证失败
        """
        path = Path(screenshot_path)

        # 检查扩展名
        if path.suffix.lower() not in allowed_extensions:
            raise FileHandlingError(
                f"无效的文件扩展名: {path.suffix}. "
                f"允许的扩展名: {', '.join(allowed_extensions)}"
            )

        # 检查文件是否存在
        if not path.exists():
            raise FileHandlingError(f"文件不存在: {screenshot_path}")

        # 检查文件是否可读
        if not os.access(screenshot_path, os.R_OK):
            raise FileHandlingError(f"文件不可读: {screenshot_path}")

        # 检查文件大小
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise FileHandlingError(
                f"文件过大: {file_size_mb:.2f}MB "
                f"(最大: {max_size_mb}MB)"
            )

        logger.debug(f"截图验证通过: {screenshot_path}")
        return True
