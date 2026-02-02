"""类型化配置系统"""

import os
import configparser
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Tuple


class LogLevel(Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class PathsConfig:
    """路径相关配置"""

    source_screenshot_directory: Path
    output_code_directory: Path
    temp_screenshot_directory: Optional[Path] = None

    def __post_init__(self):
        # 将字符串转换为 Path 对象
        self.source_screenshot_directory = Path(self.source_screenshot_directory)
        self.output_code_directory = Path(self.output_code_directory)
        if self.temp_screenshot_directory:
            self.temp_screenshot_directory = Path(self.temp_screenshot_directory)

    def validate(self) -> List[str]:
        """验证路径配置"""
        errors = []
        if not self.source_screenshot_directory:
            errors.append("source_screenshot_directory 不能为空")
        if not self.output_code_directory:
            errors.append("output_code_directory 不能为空")
        return errors


@dataclass
class LLMConfig:
    """大语言模型配置 - 支持多种模型提供商"""

    provider: str  # 'gemini', 'openai', 'anthropic', 'ollama', etc.
    api_key: str
    model_name: str
    base_url: Optional[str] = None  # 用于自定义端点（如 Ollama）
    prompt: str = "请根据这张算法编程题目截图，生成一个Python语言的解答代码。代码应该完整、可运行，并包含必要的注释。请先输出题目名称，格式为 \"题目名称: [题目名称]\"，然后直接输出代码，不要包含多余的文字说明。"

    def validate(self) -> List[str]:
        """验证 LLM 配置"""
        errors = []
        if not self.provider:
            errors.append("provider 不能为空")
        if not self.api_key or self.api_key in {
            "YOUR_API_KEY_HERE",
            "Your_Gemini_API_Key",
            "Your_API_Key_Here",
        }:
            errors.append("请设置有效的 API 密钥")
        if not self.model_name:
            errors.append("model_name 不能为空")
        return errors


@dataclass
class SecurityConfig:
    """安全相关配置"""

    code_timeout: int = 10  # 代码执行超时（秒）
    max_memory_mb: int = 100  # 最大内存（MB）
    enable_ast_validation: bool = True
    allowed_file_extensions: List[str] = field(
        default_factory=lambda: [".png", ".jpg", ".jpeg"]
    )
    max_file_size_mb: int = 10

    def validate(self) -> List[str]:
        """验证安全配置"""
        errors = []
        if self.code_timeout <= 0:
            errors.append("code_timeout 必须大于 0")
        if self.code_timeout > 60:
            errors.append("code_timeout 不能超过 60 秒")
        if self.max_memory_mb <= 0:
            errors.append("max_memory_mb 必须大于 0")
        return errors


@dataclass
class LoggingConfig:
    """日志配置"""

    level: LogLevel = LogLevel.INFO
    log_file: Optional[str] = None
    console_output: bool = True

    def validate(self) -> List[str]:
        """验证日志配置"""
        errors = []
        if not isinstance(self.level, LogLevel):
            errors.append("level 必须是 LogLevel 枚举值")
        return errors


@dataclass
class OCRConfig:
    """OCR 配置"""

    # 是否启用 OCR
    enable_ocr: bool = False

    # OCR 引擎选择
    ocr_engine: str = "paddleocr"  # paddleocr, easyocr, tesseract

    # 语言设置
    language: str = "ch"  # ch=中英文, en=英文

    # 是否使用 GPU 加速
    use_gpu: bool = False

    # 是否启用图片预处理
    enable_preprocessing: bool = True

    # 预处理选项
    preprocessing_options: List[str] = field(
        default_factory=lambda: ["enhance_contrast", "remove_noise", "adjust_dpi"]
    )

    # 目标 DPI
    target_dpi: int = 300

    # 工作模式
    mode: str = "auto"  # auto=自动检测, text=纯文本, hybrid=混合模式

    def validate(self) -> List[str]:
        """验证 OCR 配置"""
        errors = []
        if self.enable_ocr and self.ocr_engine not in ["paddleocr", "easyocr", "tesseract"]:
            errors.append("不支持的 OCR 引擎")
        if self.mode not in ["auto", "text", "hybrid"]:
            errors.append("mode 必须是 auto, text 或 hybrid")
        if self.target_dpi <= 0:
            errors.append("target_dpi 必须大于 0")
        return errors


@dataclass
class AppConfig:
    """完整应用配置"""

    paths: PathsConfig
    llm: LLMConfig
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)

    def validate(self) -> List[str]:
        """验证所有配置部分"""
        all_errors = []
        all_errors.extend(self.paths.validate())
        all_errors.extend(self.llm.validate())
        all_errors.extend(self.security.validate())
        all_errors.extend(self.logging.validate())
        all_errors.extend(self.ocr.validate())
        return all_errors

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AppConfig":
        """
        从文件和环境变量加载配置

        优先级：
        1. 环境变量（最高）
        2. 配置文件
        3. 默认值

        Args:
            config_path: 配置文件路径，默认为 config.ini 或环境变量 AUTOLEETCODE_CONFIG

        Returns:
            AppConfig 实例

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        # 确定配置文件路径
        if config_path is None:
            config_path = os.getenv("AUTOLEETCODE_CONFIG", "config.ini")

        config = configparser.ConfigParser()

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"配置文件不存在: {config_path}\n"
                f"请将 config.ini.template 复制为 config.ini 并配置它。"
            )

        config.read(config_path, encoding="utf-8")

        # 加载路径配置
        paths = PathsConfig(
            source_screenshot_directory=os.getenv(
                "AUTOLEETCODE_SOURCE_DIR",
                config.get("Paths", "SOURCE_SCREENSHOT_DIRECTORY"),
            ),
            output_code_directory=os.getenv(
                "AUTOLEETCODE_OUTPUT_DIR",
                config.get("Paths", "OUTPUT_CODE_DIRECTORY"),
            ),
            temp_screenshot_directory=os.getenv("AUTOLEETCODE_TEMP_DIR"),
        )

        # 加载 LLM 配置
        # 检查是否有 [LLM] 部分（新格式）或 [GeminiAPI] 部分（旧格式）
        if config.has_section("LLM"):
            provider = os.getenv("LLM_PROVIDER", config.get("LLM", "PROVIDER", fallback="gemini"))

            # API_KEY 优先从环境变量读取，配置文件中是可选的
            api_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key and config.has_option("LLM", "API_KEY"):
                api_key = config.get("LLM", "API_KEY")

            if not api_key:
                raise ValueError(
                    "API 密钥未设置。请设置环境变量 LLM_API_KEY 或 GEMINI_API_KEY，"
                    "或在 config.ini 的 [LLM] 部分设置 API_KEY"
                )

            model_name = os.getenv(
                "LLM_MODEL",
                config.get("LLM", "MODEL_NAME", fallback="gemini-2.5-flash"),
            )
            base_url = os.getenv("LLM_BASE_URL") or config.get("LLM", "BASE_URL", fallback=None)
            if not base_url:
                base_url = None
            prompt = config.get(
                "LLM",
                "PROMPT_FOR_CODE_GENERATION",
                fallback=LLMConfig.prompt,
            )
        else:
            # 兼容旧格式
            provider = "gemini"
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key and config.has_option("GeminiAPI", "API_KEY"):
                api_key = config.get("GeminiAPI", "API_KEY")

            if not api_key:
                raise ValueError(
                    "API 密钥未设置。请设置环境变量 GEMINI_API_KEY，"
                    "或在 config.ini 的 [GeminiAPI] 部分设置 API_KEY"
                )

            model_name = os.getenv(
                "GEMINI_MODEL",
                config.get("GeminiAPI", "GEMINI_MODEL_NAME", fallback="gemini-2.5-flash"),
            )
            base_url = None
            prompt = config.get(
                "GeminiAPI",
                "PROMPT_FOR_CODE_GENERATION",
                fallback=LLMConfig.prompt,
            )

        llm = LLMConfig(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            prompt=prompt,
        )

        # 加载安全配置
        security = SecurityConfig(
            code_timeout=int(
                os.getenv("AUTOLEETCODE_TIMEOUT", config.get("Security", "CODE_TIMEOUT", fallback="10"))
            ),
            max_memory_mb=int(
                os.getenv("AUTOLEETCODE_MAX_MEMORY", config.get("Security", "MAX_MEMORY_MB", fallback="100"))
            ),
            enable_ast_validation=config.getboolean("Security", "ENABLE_AST_VALIDATION", fallback=True),
        )

        # 加载日志配置
        log_level_str = os.getenv("AUTOLEETCODE_LOG_LEVEL", config.get("Logging", "LOG_LEVEL", fallback="INFO"))
        logging = LoggingConfig(
            level=LogLevel(log_level_str.upper()),
            log_file=os.getenv("AUTOLEETCODE_LOG_FILE") or config.get("Logging", "LOG_FILE", fallback=None),
            console_output=config.getboolean("Logging", "CONSOLE_OUTPUT", fallback=True),
        )

        # 加载 OCR 配置
        ocr = OCRConfig(
            enable_ocr=os.getenv("OCR_ENABLE", config.getboolean("OCR", "ENABLE_OCR", fallback=False)),
            ocr_engine=os.getenv("OCR_ENGINE", config.get("OCR", "OCR_ENGINE", fallback="paddleocr")),
            language=os.getenv("OCR_LANGUAGE", config.get("OCR", "LANGUAGE", fallback="ch")),
            use_gpu=os.getenv("OCR_USE_GPU", config.getboolean("OCR", "USE_GPU", fallback=False)),
            enable_preprocessing=os.getenv("OCR_ENABLE_PREPROCESSING", config.getboolean("OCR", "ENABLE_PREPROCESSING", fallback=True)),
            target_dpi=int(os.getenv("OCR_TARGET_DPI", config.get("OCR", "TARGET_DPI", fallback="300"))),
            mode=os.getenv("OCR_MODE", config.get("OCR", "MODE", fallback="auto")),
        )

        return cls(paths=paths, llm=llm, security=security, logging=logging, ocr=ocr)
