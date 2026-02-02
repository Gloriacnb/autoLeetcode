# AutoLeetcode

自动从截图分析并生成 LeetCode 题解的 Python 工具，支持多种大语言模型（LLM）提供商和 OCR 文本提取。

## 功能特点

- **自动监控**: 监控指定目录，自动识别新添加的截图
- **多 LLM 支持**: 支持 Gemini、OpenAI、Anthropic Claude、Ollama、智谱 AI 等多种模型
- **OCR 文本提取**: 支持本地 OCR 提取图片文本，让不支持图片的模型也能处理截图
- **智能代码生成**: 从题目截图自动生成 Python 解答代码
- **自动测试与修正**: 自动测试生成的代码，失败时智能修正（最多 3 次）
- **安全执行**: 沙箱化代码执行，支持超时和内存限制
- **便捷输出**: 测试通过的代码自动复制到剪贴板，并播放提示音

## 系统要求

- Python >= 3.9
- macOS / Linux / Windows
- [uv](https://github.com/astral-sh/uv) 包管理器

## 快速开始

### 1. 安装 uv

```bash
pip install uv
# 或访问 https://docs.astral.sh/uv/getting-started/installation/
```

### 2. 克隆项目

```bash
git clone https://github.com/your-repo/autoleetcode.git
cd autoleetcode
```

### 3. 安装依赖

```bash
# 基础安装
uv sync

# 如果需要使用 OCR 功能
uv sync --extra ocr
```

### 4. 配置

创建配置文件：

```bash
cp config.ini.template config.ini
```

编辑 `config.ini`，配置以下关键项：

```ini
[Paths]
# 截图监控目录（设置为你的截图保存路径）
SOURCE_SCREENSHOT_DIRECTORY = /path/to/screenshots

# 生成代码的输出目录
OUTPUT_CODE_DIRECTORY = /path/to/output

[LLM]
# LLM 提供商: gemini, openai, anthropic, ollama, zhipu
PROVIDER = gemini

# API 密钥（推荐使用环境变量设置）
# API_KEY = Your_API_Key_Here

# 模型名称
MODEL_NAME = gemini-2.5-flash
```

### 5. 验证配置

使用验证命令确保 API 配置正确：

```bash
uv run autoleetcode verify
```

带详细信息的验证：

```bash
uv run autoleetcode verify -v
```

指定提供商和 API Key 进行验证：

```bash
uv run autoleetcode verify --provider gemini --api-key YOUR_API_KEY
```

## 使用方法

### 基本使用

```bash
# 使用 uv 运行
uv run autoleetcode
```

程序将开始监控配置的目录，当检测到新的截图时自动处理。

### 工作流程

1. 截取 LeetCode 题目截图并保存到监控目录
2. 程序自动检测新截图
3. 根据配置，直接使用图片或通过 OCR 提取文本
4. LLM 分析并生成 Python 解答代码
5. 自动运行生成的代码
6. 如果运行失败，将错误信息发送给 LLM 进行修正（最多 3 次）
7. 测试通过后，代码自动复制到剪贴板并播放提示音

## 支持的 LLM 提供商

| 提供商 | 说明 | 获取 API Key |
|--------|------|--------------|
| `gemini` | Google Gemini（默认） | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `openai` | OpenAI GPT | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `anthropic` | Anthropic Claude | [Anthropic Console](https://console.anthropic.com/) |
| `ollama` | 本地模型 | 无需 API Key，需本地运行 Ollama |
| `zhipu` | 智谱 AI | [智谱 AI 开放平台](https://open.bigmodel.cn/) |

### 安装额外 LLM 支持

```bash
# 安装 OpenAI 支持
uv sync --extra openai

# 安装 Anthropic Claude 支持
uv sync --extra anthropic

# 安装 Ollama 支持
uv sync --extra ollama

# 安装智谱 AI 支持
uv sync --extra zhipu

# 安装所有 LLM 支持
uv sync --extra all
```

### 推荐模型

| 提供商 | 推荐模型 | 特点 |
|--------|----------|------|
| Gemini | `gemini-2.5-flash` | 快速、免费额度高 |
| Gemini | `gemini-2.0-pro-exp` | 能力更强 |
| OpenAI | `gpt-4o` | 综合能力强 |
| Anthropic | `claude-3-5-sonnet-20241022` | 代码质量高 |
| Ollama | `llama3.2-vision` | 本地运行、隐私安全 |
| 智谱 AI | `glm-4.7` | 编程专用模型，代码生成能力强 |

## OCR 文本提取

当使用不支持图片的 LLM 模型时，可以启用 OCR 功能从截图中提取文本。

### 安装 OCR 依赖

```bash
# 安装 PaddleOCR（推荐）
uv sync --extra paddleocr

# 或安装所有 OCR 功能
uv sync --extra ocr
```

### OCR 配置

在 `config.ini` 中配置 OCR：

```ini
[OCR]
# 是否启用 OCR 文本提取
ENABLE_OCR = true

# OCR 引擎: paddleocr
OCR_ENGINE = paddleocr

# 语言: ch=中英文, en=英文
LANGUAGE = ch

# 是否使用 GPU 加速
USE_GPU = false

# 是否启用图片预处理（提升 OCR 准确率）
ENABLE_PREPROCESSING = true

# 工作模式
# auto: 自动检测模型是否支持图片，不支持时使用 OCR
# text: 强制使用纯文本模式（只发送 OCR 提取的文本）
# hybrid: 混合模式（同时发送 OCR 文本和图片）
MODE = auto

# 目标 DPI（用于图片预处理）
TARGET_DPI = 300
```

### OCR 工作模式说明

| 模式 | 适用场景 | 发送内容 | 优点 | 缺点 |
|------|---------|---------|------|------|
| **auto** | 通用 | 模型支持图片时发送图片，否则发送 OCR 文本 | 自动适应，无需手动配置 | 可能不是最优选择 |
| **text** | 不支持图片的模型 | 只发送 OCR 提取的 Markdown 文本 | 减少 token 消耗 | 可能丢失视觉信息 |
| **hybrid** | 支持图片但理解能力弱 | 同时发送 OCR 文本和图片 | 信息最完整，准确率最高 | Token 消耗大 |

## 配置详解

### 环境变量设置 API Key

推荐使用环境变量设置 API Key，避免将敏感信息写入配置文件：

```bash
# Linux/macOS
export LLM_API_KEY="your_api_key_here"
# 或针对特定提供商
export GEMINI_API_KEY="your_gemini_key"
export OPENAI_API_KEY="your_openai_key"

# Windows (CMD)
set LLM_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:LLM_API_KEY="your_api_key_here"
```

### [Paths] 路径配置

```ini
SOURCE_SCREENSHOT_DIRECTORY = /path/to/screenshots  # 截图监控目录
OUTPUT_CODE_DIRECTORY = /path/to/output             # 代码输出目录
TEMP_SCREENSHOT_DIRECTORY = /path/to/temp           # 可选：临时目录
```

### [LLM] 语言模型配置

```ini
PROVIDER = gemini                    # LLM 提供商
API_KEY = your_api_key               # API 密钥（推荐使用环境变量）
MODEL_NAME = gemini-2.5-flash        # 模型名称
BASE_URL = http://localhost:11434/v1 # 可选：自定义端点（Ollama/代理）
PROMPT_FOR_CODE_GENERATION = ...     # 自定义提示词
```

### [Security] 安全配置

```ini
CODE_TIMEOUT = 10               # 代码执行超时（秒）
MAX_MEMORY_MB = 100             # 最大内存限制（MB）
ENABLE_AST_VALIDATION = true    # 启用 AST 代码验证
ALLOWED_EXTENSIONS = .png, .jpg, .jpeg  # 允许的图片格式
MAX_FILE_SIZE_MB = 10           # 最大文件大小（MB）
```

### [Logging] 日志配置

```ini
LOG_LEVEL = INFO                # 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_FILE = autoleetcode.log     # 可选：日志文件路径
CONSOLE_OUTPUT = true           # 控制台输出
```

## 高级用法

### 使用 Ollama 本地模型

1. 安装 [Ollama](https://ollama.ai/)
2. 拉取支持视觉的模型：
   ```bash
   ollama pull llama3.2-vision
   ```
3. 配置 `config.ini`：
   ```ini
   [LLM]
   PROVIDER = ollama
   MODEL_NAME = llama3.2-vision
   BASE_URL = http://localhost:11434/v1
   ```

### 开发环境安装

```bash
# 安装开发依赖
uv sync --extra dev

# 运行测试
uv run pytest

# 代码格式化
uv run black autoleetcode/

# 类型检查
uv run mypy autoleetcode/
```

## 项目结构

```
autoleetcode/
├── __init__.py
├── main.py                 # 主入口
├── api/
│   └── exceptions.py       # 异常定义
├── cli/                    # CLI 命令
│   ├── commands.py         # 命令路由
│   └── verifier.py         # API 验证工具
├── code/
│   └── parser.py           # 代码解析
├── config/
│   └── configuration.py    # 配置管理
├── file_handler/
│   └── path_utils.py       # 路径工具
├── llm/
│   ├── base.py             # LLM 基类
│   ├── factory.py          # LLM 工厂
│   ├── gemini_client.py    # Gemini 客户端
│   ├── openai_client.py    # OpenAI 客户端
│   ├── anthropic_client.py # Anthropic 客户端
│   ├── ollama_client.py    # Ollama 客户端
│   └── zhipu_client.py     # 智谱 AI 客户端
├── notification/
│   └── notifier.py         # 通知系统
├── ocr/                    # OCR 模块
│   ├── base.py             # OCR 基类
│   ├── factory.py          # OCR 工厂
│   ├── paddle_processor.py # PaddleOCR 实现
│   ├── preprocessor.py     # 图片预处理
│   └── formatter.py        # 文本格式化
├── security/
│   └── code_executor.py    # 代码执行器
└── utils/
    └── logging_config.py   # 日志配置
```

## 常见问题

### Q: API 验证失败怎么办？

A: 首先使用 `verify` 命令检查配置：
```bash
uv run autoleetcode verify -v
```

检查：
1. API Key 是否正确（不要有多余的空格或引号）
2. 网络连接是否正常
3. 是否有防火墙或代理限制
4. 使用环境变量而不是配置文件设置 API Key

### Q: VSCode 集成终端中 API 验证失败？

A: VSCode 的集成终端可能缓存了旧的环境变量。请尝试：
1. 重启 VSCode
2. 或使用独立的终端窗口（cmd/PowerShell）
3. 确保环境变量在用户级别设置，而不是仅在 VSCode 中

### Q: 代码执行超时怎么办？

A: 在 `config.ini` 的 `[Security]` 部分增加 `CODE_TIMEOUT` 值。

### Q: OCR 识别不准确怎么办？

A: 尝试以下方法：
1. 启用图片预处理：`ENABLE_PREPROCESSING = true`
2. 调整目标 DPI：`TARGET_DPI = 300`
3. 使用混合模式：`MODE = hybrid`
4. 确保截图清晰，文字大小适中

### Q: 支持哪些图片格式？

A: 默认支持 `.png`, `.jpg`, `.jpeg`，macOS 还支持 `.heif` 格式。

### Q: 如何获取 Gemini API Key？

A: 访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 免费获取。

## 许可证

MIT License
