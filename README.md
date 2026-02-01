# AutoLeetcode

自动从截图分析并生成 LeetCode 题解的 Python 工具，支持多种大语言模型（LLM）提供商。

## 功能特点

- **自动监控**: 监控指定目录，自动识别新添加的截图
- **多 LLM 支持**: 支持 Gemini、OpenAI、Anthropic Claude、Ollama 等多种模型
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
uv sync
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
# LLM 提供商: gemini, openai, anthropic, ollama
PROVIDER = gemini

# API 密钥（也可通过环境变量 LLM_API_KEY 设置）
API_KEY = Your_API_Key_Here

# 模型名称
MODEL_NAME = gemini-2.5-flash
```

#### 支持的 LLM 提供商

| 提供商 | 说明 | 获取 API Key |
|--------|------|--------------|
| `gemini` | Google Gemini（默认） | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `openai` | OpenAI GPT | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `anthropic` | Anthropic Claude | [Anthropic Console](https://console.anthropic.com/) |
| `ollama` | 本地模型 | 无需 API Key，需本地运行 Ollama |
| `zhipu` | 智谱 AI | [智谱 AI 开放平台](https://open.bigmodel.cn/) |

#### 安装额外 LLM 支持

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

## 使用方法

### 基本使用

```bash
# 方式一：使用 uv 运行
uv run autoleetcode

# 方式二：直接使用命令（如果已安装）
autoleetcode
```

程序将开始监控配置的目录，当检测到新的截图时自动处理。

### 工作流程

1. 截取 LeetCode 题目截图并保存到监控目录
2. 程序自动检测新截图
3. LLM 分析截图并生成 Python 解答代码
4. 自动运行生成的代码
5. 如果运行失败，将错误信息发送给 LLM 进行修正（最多 3 次）
6. 测试通过后，代码自动复制到剪贴板并播放提示音

## 配置详解

### [Paths] 路径配置

```ini
SOURCE_SCREENSHOT_DIRECTORY = /path/to/screenshots  # 截图监控目录
OUTPUT_CODE_DIRECTORY = /path/to/output             # 代码输出目录
TEMP_SCREENSHOT_DIRECTORY = /path/to/temp           # 可选：临时目录
```

### [LLM] 语言模型配置

```ini
PROVIDER = gemini                    # LLM 提供商
API_KEY = your_api_key               # API 密钥
MODEL_NAME = gemini-2.5-flash        # 模型名称
BASE_URL = http://localhost:11434/v1 # 可选：自定义端点（Ollama/代理）
PROMPT_FOR_CODE_GENERATION = ...     # 自定义提示词
```

#### 推荐模型

| 提供商 | 推荐模型 | 特点 |
|--------|----------|------|
| Gemini | `gemini-2.5-flash` | 快速、免费额度高 |
| Gemini | `gemini-2.0-pro-exp` | 能力更强 |
| OpenAI | `gpt-4o` | 综合能力强 |
| Anthropic | `claude-3-5-sonnet-20241022` | 代码质量高 |
| Ollama | `llama3.2-vision` | 本地运行、隐私安全 |
| 智谱 AI | `glm-4.7` | 编程专用模型，代码生成能力强 |
| 智谱 AI | `glm-4.6` | 编程模型 |

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

### 环境变量设置 API Key

```bash
export LLM_API_KEY="your_api_key_here"
```

在 `config.ini` 中可以省略 `API_KEY` 配置。

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
├── security/
│   └── code_executor.py    # 代码执行器
└── utils/
    └── logging_config.py   # 日志配置
```

## 常见问题

### Q: 代码执行超时怎么办？

A: 在 `config.ini` 的 `[Security]` 部分增加 `CODE_TIMEOUT` 值。

### Q: 如何禁用代码自动测试？

A: 目前不支持禁用，但可以将 `MAX_FIX_ATTEMPTS` 设置为 0 来减少测试次数（需修改代码）。

### Q: 支持哪些图片格式？

A: 默认支持 `.png`, `.jpg`, `.jpeg`，macOS 还支持 `.heif` 格式。

### Q: 如何获取 Gemini API Key？

A: 访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 免费获取。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
