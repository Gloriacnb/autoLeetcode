"""API 验证器模块"""

import sys
import os
from typing import Optional, Dict

# 设置 UTF-8 编码输出（兼容 Windows）
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


class Colors:
    """终端颜色代码"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

    # 检测是否支持颜色
    _supports_color = sys.stdout.isatty() and os.environ.get('TERM') != 'dumb'

    @classmethod
    def _colorize(cls, text: str, color: str) -> str:
        """应用颜色（如果支持）"""
        if cls._supports_color:
            return f"{color}{text}{cls.END}"
        return text

    @classmethod
    def green(cls, text: str) -> str:
        return cls._colorize(text, cls.GREEN)

    @classmethod
    def red(cls, text: str) -> str:
        return cls._colorize(text, cls.RED)

    @classmethod
    def yellow(cls, text: str) -> str:
        return cls._colorize(text, cls.YELLOW)

    @classmethod
    def blue(cls, text: str) -> str:
        return cls._colorize(text, cls.BLUE)

    @classmethod
    def bold(cls, text: str) -> str:
        return cls._colorize(text, cls.BOLD)


def format_api_key(api_key: str) -> str:
    """格式化 API Key 用于显示"""
    if len(api_key) <= 8:
        return api_key[:4] + '...'
    return api_key[:4] + '...' + api_key[-4:]


def format_latency(latency_ms: float) -> str:
    """格式化延迟时间"""
    return f"{latency_ms:,.0f}ms"


def print_header(title: str, width: 50):
    """打印标题头部"""
    print(Colors.bold(title))
    print("=" * width)


def print_verification_header(provider: str, model: str, api_key: str):
    """打印验证头部信息"""
    print()
    print(f"{Colors.blue('提供商:')}: {provider}")
    print(f"{Colors.blue('模型:')}: {model}")
    print(f"{Colors.blue('API Key:')}: {format_api_key(api_key)}")
    print()
    print("正在验证连接...")
    print()


def print_success(result: Dict, verbose: bool = False):
    """打印验证成功信息"""
    print(f"{Colors.green('[OK]')} 验证成功")
    print(f"  {result['message']} (延迟: {format_latency(result['latency_ms'])})")

    if verbose and result.get('details'):
        details = result['details']
        print()
        print("详细信息:")
        if 'response_preview' in details:
            print(f"  响应预览: {details['response_preview']}")
        if 'model_id' in details:
            print(f"  模型 ID: {details['model_id']}")
        if 'installed_models' in details:
            print(f"  已安装模型: {', '.join(details['installed_models'][:5])}")
            if len(details['installed_models']) > 5:
                print(f"    (共 {len(details['installed_models'])} 个模型)")


def print_failure(result: Dict, verbose: bool = False):
    """打印验证失败信息"""
    print(f"{Colors.red('[FAIL]')} 验证失败")
    print(f"  {Colors.red(result['message'])}")

    details = result.get('details')
    if details:
        suggestion = details.get('suggestion')
        if suggestion:
            print()
            print(f"{Colors.yellow('建议:')}")
            print(f"  * {suggestion}")

        if verbose:
            error_type = details.get('error_type')
            if error_type:
                print()
                print(f"错误类型: {error_type}")

            if 'installed_models' in details:
                installed = details['installed_models']
                print()
                print(f"已安装的模型 ({len(installed)}):")
                for model in installed[:10]:
                    print(f"  - {model}")
                if len(installed) > 10:
                    print(f"  ... 还有 {len(installed) - 10} 个模型")

    if verbose and result.get('error'):
        print()
        print("错误详情:")
        print(f"  {type(result['error']).__name__}: {result['error']}")


def verify_api_connection(provider: str, api_key: str, model: str,
                          base_url: Optional[str] = None,
                          verbose: bool = False) -> int:
    """
    验证 API 连接

    Args:
        provider: 提供商名称
        api_key: API 密钥
        model: 模型名称
        base_url: 可选的自定义端点
        verbose: 是否显示详细信息

    Returns:
        int: 退出码 (0=成功, 1=失败, 2=配置错误)
    """
    from autoleetcode.llm.factory import LLMClientFactory
    from autoleetcode.api.exceptions import AutoLeetcodeError

    print_header("AutoLeetcode API 验证", 50)

    try:
        # 创建客户端
        client = LLMClientFactory.create(
            provider=provider,
            api_key=api_key,
            model_name=model,
            base_url=base_url,
        )

        print_verification_header(provider.upper(), model, api_key)

        # 执行验证
        result = client.verify_connection()

        if result['success']:
            print_success(result, verbose)
            print()
            return 0
        else:
            print_failure(result, verbose)
            print()
            return 1

    except ValueError as e:
        print()
        print(f"{Colors.red('[ERROR]')} 配置错误")
        print(f"  {str(e)}")
        print()
        return 2

    except ImportError as e:
        print()
        print(f"{Colors.red('[ERROR]')} 依赖错误")
        print(f"  {str(e)}")
        print()
        return 2

    except AutoLeetcodeError as e:
        print()
        print(f"{Colors.red('[ERROR]')} 应用错误")
        print(f"  {str(e)}")
        print()
        return 1

    except KeyboardInterrupt:
        print()
        print(f"{Colors.yellow('[CANCEL]')} 验证已取消")
        print()
        return 130

    except Exception as e:
        print()
        print(f"{Colors.red('[ERROR]')} 意外错误")
        if verbose:
            print(f"  {type(e).__name__}: {str(e)}")
        else:
            print(f"  使用 -v 查看详细错误信息")
        print()
        return 1
