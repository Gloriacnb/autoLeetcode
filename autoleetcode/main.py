"""AutoLeetcode 主程序入口"""

import sys
import os
import time
import re
from pathlib import Path
from typing import Tuple
import logging

from autoleetcode.config.configuration import AppConfig
from autoleetcode.utils.logging_config import setup_logging
from autoleetcode.llm.factory import LLMClientFactory
from autoleetcode.security.code_executor import CodeExecutor
from autoleetcode.code.parser import CodeParser
from autoleetcode.notification.notifier import Notifier
from autoleetcode.file_handler.path_utils import PathUtils
from autoleetcode.api.exceptions import AutoLeetcodeError

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 全局 logger
logger = logging.getLogger("autoleetcode")

# 最大代码修正尝试次数
MAX_FIX_ATTEMPTS = 3


class CodeFixer:
    """处理代码测试和修正循环"""

    def __init__(self, llm_client, code_executor: CodeExecutor, max_attempts: int = 3):
        self.llm_client = llm_client
        self.code_executor = code_executor
        self.max_attempts = max_attempts

    def test_and_fix(self, code_path: Path, initial_code: str) -> Tuple[bool, str]:
        """
        测试代码并在失败时尝试修正

        Args:
            code_path: 代码文件路径
            initial_code: 初始生成的代码

        Returns:
            (成功, 最终代码) 元组
        """
        current_code = initial_code

        for attempt in range(self.max_attempts):
            logger.info(f"测试代码 (第 {attempt + 1}/{self.max_attempts} 次)")

            # 写入当前代码到文件
            code_path.write_text(current_code, encoding="utf-8")

            # 测试代码
            success, error = self.code_executor.execute(str(code_path))

            if success:
                logger.info("代码测试通过")
                return True, current_code

            logger.warning(f"代码测试失败: {error}")

            # 尝试修正代码
            if attempt < self.max_attempts - 1:
                logger.info("请求 Gemini API 修正代码...")
                try:
                    fixed_response = self.llm_client.fix_code(current_code, error)
                    _, current_code = CodeParser.extract_code_from_markdown(fixed_response)
                except Exception as e:
                    logger.error(f"修正代码失败: {e}")
                    break

        logger.error(f"代码在 {self.max_attempts} 次尝试后仍然失败")
        return False, current_code


class ScreenshotProcessor:
    """协调截图处理工作流"""

    def __init__(self, config: AppConfig):
        self.config = config

        # 创建 LLM 客户端
        self.llm_client = LLMClientFactory.create(
            provider=config.llm.provider,
            api_key=config.llm.api_key,
            model_name=config.llm.model_name,
            base_url=config.llm.base_url,
        )
        logger.info(f"已配置 {config.llm.provider} LLM 客户端 (模型: {config.llm.model_name})")

        # 创建代码执行器
        self.code_executor = CodeExecutor(
            timeout=config.security.code_timeout,
            max_memory_mb=config.security.max_memory_mb,
        )

        # 创建代码修正器
        self.code_fixer = CodeFixer(self.llm_client, self.code_executor, max_attempts=MAX_FIX_ATTEMPTS)

        # 创建通知器
        self.notifier = Notifier()

    def process_screenshot(self, screenshot_path: str) -> None:
        """
        处理单个截图

        Args:
            screenshot_path: 截图文件路径
        """
        try:
            # 验证截图
            PathUtils.validate_screenshot(
                screenshot_path,
                set(self.config.security.allowed_file_extensions),
                self.config.security.max_file_size_mb,
            )

            # 生成代码
            logger.info("正在处理截图，请求 LLM 生成代码...")
            response = self.llm_client.generate_code_from_screenshot(
                screenshot_path, self.config.llm.prompt
            )

            # 解析响应
            title, generated_code = CodeParser.extract_code_from_markdown(response)
            logger.info(f"提取到代码: {title}")

            # 生成输出路径
            code_path = PathUtils.get_code_path(
                self.config.paths.output_code_directory, title, screenshot_path
            )

            # 确保输出目录存在
            code_path.parent.mkdir(parents=True, exist_ok=True)

            # 测试并修正代码
            success, final_code = self.code_fixer.test_and_fix(code_path, generated_code)

            # 保存最终代码
            code_path.write_text(final_code, encoding="utf-8")
            logger.info(f"代码已保存到: {code_path}")

            # 通知用户
            if success:
                self.notifier.notify_success(final_code)

        except AutoLeetcodeError as e:
            logger.error(f"处理错误: {e}")
        except Exception as e:
            logger.exception(f"处理截图时发生意外错误: {e}")


class ScreenshotMonitor(FileSystemEventHandler):
    """监控截图目录以获取新文件"""

    def __init__(self, config: AppConfig, processor: ScreenshotProcessor):
        super().__init__()
        self.config = config
        self.processor = processor
        self.processing = False
        self.last_processed_time = 0
        self.cooldown_period = 2.0  # 处理间隔（秒）

    def on_created(self, event):
        """处理新文件创建事件"""
        if event.is_directory:
            return

        screenshot_path = event.src_path

        # 检查是否为图像文件
        if not screenshot_path.lower().endswith(
            tuple(self.config.security.allowed_file_extensions)
        ):
            return

        # 防抖：避免快速连续的文件创建
        current_time = time.time()

        if (current_time - self.last_processed_time < self.cooldown_period) or self.processing:
            logger.debug("跳过文件（冷却期间或正在处理）")
            return

        # 等待文件完全写入（检查文件大小稳定）
        max_wait = 5  # 最多等待5秒
        check_interval = 0.5
        last_size = -1
        stable_count = 0

        for _ in range(int(max_wait / check_interval)):
            try:
                current_size = os.path.getsize(screenshot_path)
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 2:  # 文件大小连续2次检查不变
                        break
                else:
                    stable_count = 0
                    last_size = current_size
                time.sleep(check_interval)
            except OSError:
                time.sleep(check_interval)
                continue

        logger.info(f"检测到新截图: {screenshot_path}")
        self.processing = True
        self.last_processed_time = current_time

        try:
            self.processor.process_screenshot(screenshot_path)
        finally:
            self.processing = False

    def start(self):
        """开始监控截图目录"""
        source_dir = str(self.config.paths.source_screenshot_directory)

        if not Path(source_dir).exists():
            raise FileNotFoundError(f"源目录不存在: {source_dir}")

        observer = Observer()
        observer.schedule(self, source_dir, recursive=False)
        observer.start()

        logger.info(f"正在监控目录: {source_dir}")
        return observer


def main():
    """应用入口点"""
    try:
        # 加载配置
        config = AppConfig.load()

        # 验证配置
        errors = config.validate()
        if errors:
            print("配置错误:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)

        # 设置日志
        global logger
        logger = setup_logging(config.logging)
        logger.info("AutoLeetcode 启动中...")
        logger.info(f"LLM 提供商: {config.llm.provider}")
        logger.info(f"LLM 模型: {config.llm.model_name}")

        # 创建输出目录
        output_dir = config.paths.output_code_directory
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录已就绪: {output_dir}")

        # 清理临时目录（如果存在）
        if config.paths.temp_screenshot_directory:
            temp_dir = config.paths.temp_screenshot_directory
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir)
                logger.info(f"已删除临时目录: {temp_dir}")

        # 初始化处理器和监控器
        processor = ScreenshotProcessor(config)
        monitor = ScreenshotMonitor(config, processor)

        # 开始监控（阻塞调用）
        observer = monitor.start()

        logger.info("正在监控截图... (按 Ctrl+C 停止)")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("正在关闭...")
            observer.stop()
            observer.join()
            logger.info("已关闭")

    except AutoLeetcodeError as e:
        logger.error(f"应用错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"意外错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
