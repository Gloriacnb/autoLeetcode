"""AutoLeetcode CLI 命令路由器"""

import argparse
import sys
import os


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='autoleetcode',
        description='AutoLeetcode - 自动化 LeetCode 题目解答工具'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # verify 子命令
    verify_parser = subparsers.add_parser(
        'verify',
        help='验证 LLM API 配置和连接'
    )
    verify_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细输出'
    )
    verify_parser.add_argument(
        '--provider',
        choices=['gemini', 'openai', 'anthropic', 'ollama', 'zhipu'],
        help='指定要验证的提供商（覆盖配置文件）'
    )
    verify_parser.add_argument(
        '--api-key',
        help='指定 API Key（覆盖配置文件和环境变量）'
    )
    verify_parser.add_argument(
        '--model',
        help='指定模型名称（覆盖配置文件）'
    )

    return parser


def handle_verify(args) -> int:
    """处理 verify 命令"""
    from autoleetcode.config.configuration import AppConfig
    from autoleetcode.cli.verifier import verify_api_connection

    try:
        # 加载配置
        config = AppConfig.load()

        # 确定要使用的参数（命令行参数优先）
        provider = args.provider or config.llm.provider
        api_key = args.api_key or config.llm.api_key
        model = args.model or config.llm.model_name
        base_url = config.llm.base_url

        # 执行验证
        return verify_api_connection(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            verbose=args.verbose
        )

    except FileNotFoundError as e:
        print(f"错误: {e}")
        return 2
    except Exception as e:
        print(f"错误: {e}")
        return 1


def main():
    """CLI 主入口"""
    parser = create_parser()

    # 如果没有提供参数，默认运行监控模式（向后兼容）
    if len(sys.argv) == 1:
        from autoleetcode.main import main as monitor_main
        monitor_main()
        return

    # 解析参数
    args = parser.parse_args()

    # 处理命令
    if args.command == 'verify':
        exit_code = handle_verify(args)
        sys.exit(exit_code)
    else:
        # 没有 recognized 命令，运行监控模式
        from autoleetcode.main import main as monitor_main
        monitor_main()


if __name__ == "__main__":
    main()
