"""文本格式化器

将 OCR 提取的原始文本格式化为结构化的 Markdown。
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MarkdownFormatter:
    """将 OCR 提取的文本格式化为 Markdown"""

    @staticmethod
    def format_LeetCode_problem(raw_text: str) -> str:
        """
        将原始文本格式化为 LeetCode 题目格式的 Markdown

        识别模式：
        - 题目编号和标题
        - 难度级别
        - 题目描述
        - 示例（示例 1、示例 2...）
        - 约束条件
        - 提示

        Args:
            raw_text: OCR 提取的原始文本

        Returns:
            格式化后的 Markdown 文本
        """
        if not raw_text:
            return ""

        # 清理文本：去除多余空白
        text = re.sub(r'\n\s*\n', '\n\n', raw_text.strip())

        # 尝试提取各个部分
        parts = {
            "title": None,
            "difficulty": None,
            "description": None,
            "examples": [],
            "constraints": [],
            "hints": [],
        }

        # 1. 提取标题（通常在开头，可能是编号 + 标题）
        title_match = re.search(
            r'^(\d+\.\s*)?(.+?)\n',
            text
        )
        if title_match:
            potential_title = title_match.group(2).strip()
            # 简单的启发式：标题通常较短，不含"示例"、"约束"等关键词
            if len(potential_title) < 100 and "示例" not in potential_title and "约束" not in potential_title:
                parts["title"] = potential_title

        # 2. 提取难度级别
        difficulty_patterns = [
            r'难度[：:]\s*(简单|中等|困难|Easy|Medium|Hard)',
            r'(简单|中等|困难|Easy|Medium|Hard)',
        ]
        for pattern in difficulty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parts["difficulty"] = match.group(1)
                break

        # 3. 提取示例
        # LeetCode 示例通常以 "示例 1:" 或 "Example 1:" 开头
        example_pattern = r'(示例\s*\d+|Example\s*\d+)[：:]\s*\n(.*?)(?=(?:示例\s*\d+|Example\s*\d+|约束|提示|$))'
        example_matches = re.findall(example_pattern, text, re.IGNORECASE | re.DOTALL)
        for match in example_matches:
            example_title = match[0]
            example_content = match[1].strip()
            parts["examples"].append({
                "title": example_title,
                "content": example_content,
            })

        # 4. 提取约束条件
        # 约束通常以 "约束:" 或 "Constraints:" 开头，后面跟着列表
        constraints_pattern = r'(约束|Constraints)[：:]\s*\n(.*?)(?=(?:提示|$))'
        constraints_match = re.search(constraints_pattern, text, re.IGNORECASE | re.DOTALL)
        if constraints_match:
            constraints_text = constraints_match.group(2)
            # 将约束条件分割成列表（通常是数字开头的行）
            constraint_lines = re.findall(r'\s*[\d\-\.]+\s*(.*?)(?=\n|$)', constraints_text)
            parts["constraints"] = [line.strip() for line in constraint_lines if line.strip()]

        # 5. 提取提示
        hints_pattern = r'(提示|Hints?)[：:]\s*\n(.*?)(?=$)'
        hints_match = re.search(hints_pattern, text, re.IGNORECASE | re.DOTALL)
        if hints_match:
            hints_text = hints_match.group(2)
            # 将提示分割成列表
            hint_lines = re.findall(r'\s*[\d\-\.]+\s*(.*?)(?=\n|$)', hints_text)
            parts["hints"] = [line.strip() for line in hint_lines if line.strip()]

        # 如果没有提取到任何结构化信息，直接返回清理后的原始文本
        if not any([parts["title"], parts["examples"], parts["constraints"]]):
            logger.debug("未能识别 LeetCode 结构，返回原始文本")
            return f"# 题目\n\n{text}"

        # 构建 Markdown
        markdown_lines = []

        # 标题
        if parts["title"]:
            markdown_lines.append(f"# {parts['title']}")
            markdown_lines.append("")
        else:
            markdown_lines.append("# 题目")
            markdown_lines.append("")

        # 难度
        if parts["difficulty"]:
            markdown_lines.append(f"**难度**: {parts['difficulty']}")
            markdown_lines.append("")

        # 提取描述（标题和示例之间的部分）
        description_text = text
        if parts["title"]:
            # 移除标题行
            description_text = re.sub(r'^\d+\.\s*' + re.escape(parts["title"]) + r'\n', '', description_text)
            description_text = re.sub(r'^' + re.escape(parts["title"]) + r'\n', '', description_text)

        if parts["difficulty"]:
            # 移除难度行
            description_text = re.sub(r'难度[：:]\s*(简单|中等|困难|Easy|Medium|Hard)\n', '', description_text, flags=re.IGNORECASE)

        # 移除示例部分
        description_text = re.sub(example_pattern, '', description_text, flags=re.IGNORECASE | re.DOTALL)

        # 移除约束和提示
        description_text = re.sub(constraints_pattern, '', description_text, flags=re.IGNORECASE | re.DOTALL)
        description_text = re.sub(hints_pattern, '', description_text, flags=re.IGNORECASE | re.DOTALL)

        description_text = description_text.strip()
        if description_text:
            markdown_lines.append("## 题目描述")
            markdown_lines.append("")
            markdown_lines.append(description_text)
            markdown_lines.append("")

        # 示例
        if parts["examples"]:
            markdown_lines.append("## 示例")
            markdown_lines.append("")
            for example in parts["examples"]:
                markdown_lines.append(f"### {example['title']}")
                markdown_lines.append("")
                # 使用代码块包装示例内容，以保持格式
                markdown_lines.append(f"```\n{example['content']}\n```")
                markdown_lines.append("")

        # 约束
        if parts["constraints"]:
            markdown_lines.append("## 约束")
            markdown_lines.append("")
            for i, constraint in enumerate(parts["constraints"], 1):
                markdown_lines.append(f"{i}. {constraint}")
            markdown_lines.append("")

        # 提示
        if parts["hints"]:
            markdown_lines.append("## 提示")
            markdown_lines.append("")
            for i, hint in enumerate(parts["hints"], 1):
                markdown_lines.append(f"{i}. {hint}")
            markdown_lines.append("")

        return "\n".join(markdown_lines)

    @staticmethod
    def clean_ocr_errors(text: str) -> str:
        """
        清理常见的 OCR 识别错误

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return text

        # 常见的 OCR 错误修正
        corrections = {
            '0': 'O',  # 在某些上下文中
            '|': 'l',  # 在某些上下文中
        }

        # 这里可以添加更多修正规则
        # 目前保持简单，避免过度修正

        return text
