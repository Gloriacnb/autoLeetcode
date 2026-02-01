"""日志配置"""

import sys
import logging

from autoleetcode.config.configuration import LoggingConfig


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """
    配置应用日志

    Args:
        config: 日志配置

    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger("autoleetcode")
    logger.setLevel(getattr(logging, config.level.value))

    # 清除现有的 handlers
    logger.handlers.clear()

    # 设置日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件处理器（可选）
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
