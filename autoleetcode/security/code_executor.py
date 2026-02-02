"""沙箱化代码执行器"""

import ast
import subprocess
import signal
import os
import sys
from typing import Tuple

# Windows 兼容性：resource 模块仅在 Unix 系统上可用
if sys.platform != "win32":
    from resource import getrlimit, setrlimit, RLIMIT_NOFILE

from autoleetcode.api.exceptions import CodeValidationError, CodeExecutionError


class UnsafeCodeError(CodeValidationError):
    """代码不安全错误"""

    pass


class CodeExecutor:
    """
    沙箱化 Python 代码执行器

    提供：
    - AST 验证以检测危险操作
    - 超时强制
    - 资源限制（文件描述符）
    """

    # 禁止的 AST 节点类型
    FORBIDDEN_NODES = (ast.Import, ast.ImportFrom)

    # 禁止的模块
    FORBIDDEN_MODULES = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "pickle",
        "socket",
        "urllib",
        "requests",
        "http",
        "ftplib",
    }

    # 禁止的内置函数
    FORBIDDEN_FUNCTIONS = {"eval", "exec", "compile", "__import__"}

    # 禁止的文件操作属性
    FORBIDDEN_FILE_ATTRS = {"open", "remove", "rmdir", "mkdir"}

    def __init__(self, timeout: int = 10, max_memory_mb: int = 100):
        """
        初始化代码执行器

        Args:
            timeout: 代码执行超时时间（秒）
            max_memory_mb: 最大内存限制（MB）
        """
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    def validate_code(self, code: str) -> None:
        """
        使用 AST 验证代码安全性

        Args:
            code: 要验证的 Python 代码

        Raises:
            UnsafeCodeError: 代码包含危险操作
            CodeValidationError: 代码语法错误
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise CodeValidationError(f"语法错误: {e}")

        # 遍历 AST 检测危险节点
        for node in ast.walk(tree):
            # 检查导入语句
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_name = None
                if isinstance(node, ast.Import):
                    module_name = node.names[0].name.split(".")[0]
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module.split(".")[0] if node.module else None

                if module_name in self.FORBIDDEN_MODULES:
                    raise UnsafeCodeError(f"禁止导入的模块: {module_name}")

            # 检查危险函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_FUNCTIONS:
                        raise UnsafeCodeError(f"禁止的函数调用: {node.func.id}")

                # 检查文件操作
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.FORBIDDEN_FILE_ATTRS:
                        raise UnsafeCodeError(f"禁止的文件操作: {node.func.attr}")

    def execute(self, code_path: str) -> Tuple[bool, str]:
        """
        执行代码文件并返回结果

        Args:
            code_path: 代码文件路径

        Returns:
            (成功, 错误信息) 元组

        Raises:
            UnsafeCodeError: 代码未通过安全验证
        """
        # 首先验证代码
        try:
            with open(code_path, "r", encoding="utf-8") as f:
                code = f.read()
            self.validate_code(code)
        except UnsafeCodeError as e:
            raise
        except Exception as e:
            return False, f"代码验证错误: {e}"

        # 设置资源限制（仅 Unix 系统）
        preexec_fn = None
        if sys.platform != "win32":
            def limit_resources():
                # 限制文件描述符数量
                soft, hard = getrlimit(RLIMIT_NOFILE)
                setrlimit(RLIMIT_NOFILE, (16, hard))
            preexec_fn = limit_resources  # 在子进程中应用限制

        # 执行代码
        try:
            result = subprocess.run(
                ["python", code_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout,
                preexec_fn=preexec_fn,  # Unix 系统上应用资源限制
                check=False,
            )

            if result.returncode != 0:
                return False, result.stderr or result.stdout
            return True, ""

        except subprocess.TimeoutExpired:
            return False, f"代码执行超时 ({self.timeout}s)"
        except FileNotFoundError:
            return False, "错误: 未找到 python 命令，请确保 Python 已安装并添加到 PATH"
        except Exception as e:
            return False, f"代码执行错误: {e}"
