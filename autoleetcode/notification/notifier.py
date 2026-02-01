"""通知系统（声音和剪贴板）"""

import platform
import subprocess
import pyperclip
import logging

logger = logging.getLogger("autoleetcode")


class Notifier:
    """处理通知（声音、剪贴板）"""

    @staticmethod
    def copy_to_clipboard(text: str) -> None:
        """
        复制文本到剪贴板

        Args:
            text: 要复制的文本
        """
        try:
            pyperclip.copy(text)
            logger.info("代码已复制到剪贴板")
        except Exception as e:
            logger.error(f"复制到剪贴板失败: {e}")

    @staticmethod
    def play_success_sound() -> None:
        """播放成功提示音"""
        try:
            system = platform.system()
            if system == "Windows":
                import winsound

                winsound.Beep(500, 500)
                logger.debug("播放 Windows 成功音")
            elif system == "Darwin":  # macOS
                subprocess.run(["say", "代码已生成"])
                logger.debug("播放 macOS 成功音")
            elif system == "Linux":
                subprocess.run(["notify-send", "AutoLeetcode", "代码已生成"])
                logger.debug("发送 Linux 桌面通知")
        except Exception as e:
            logger.warning(f"播放成功音失败: {e}")

    @staticmethod
    def notify_success(text: str) -> None:
        """
        通知用户代码生成成功

        Args:
            text: 生成的代码文本
        """
        Notifier.copy_to_clipboard(text)
        Notifier.play_success_sound()
