"""Markdown 代码解析器"""

import re
import logging

logger = logging.getLogger("autoleetcode")


class CodeParser:
    """从 Gemini API 响应中解析代码"""

    @staticmethod
    def extract_code_from_markdown(text: str) -> tuple[str, str]:
        """
        从 markdown 文本中提取标题和代码

        Args:
            text: Gemini API 返回的响应文本

        Returns:
            (标题, 代码) 元组
        """
        # 提取标题
        title_match = re.search(r"题目名称:\s*(.+?)\n", text)
        title = title_match.group(1).strip() if title_match else "Untitled"

        # 尝试从 python 代码块中提取代码
        code_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
        if not code_match:
            # 尝试通用代码块
            code_match = re.search(r"```(.*?)```", text, re.DOTALL)

        if code_match:
            code = code_match.group(1).strip()
            logger.debug(f"从 markdown 块中提取了 '{title}' 的代码")
        else:
            # 如果没有代码块，则假定整个文本（去除标题后）都是代码
            code = re.sub(r"题目名称:\s*(.+?)\n", "", text, 1).strip()
            logger.debug(f"将整个文本作为 '{title}' 的代码")

        return title, code
