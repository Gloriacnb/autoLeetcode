"""异常类定义"""


class AutoLeetcodeError(Exception):
    """AutoLeetcode 基础异常类"""

    pass


class ConfigurationError(AutoLeetcodeError):
    """配置相关错误"""

    pass


class APIError(AutoLeetcodeError):
    """API 调用错误"""

    pass


class CodeExecutionError(AutoLeetcodeError):
    """代码执行错误"""

    pass


class CodeValidationError(AutoLeetcodeError):
    """代码验证错误"""

    pass


class FileHandlingError(AutoLeetcodeError):
    """文件处理错误"""

    pass
