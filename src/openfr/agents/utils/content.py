"""Anthropic/OpenAI content 格式兼容工具"""


def extract_text(content) -> str:
    """从 LLM response.content 中提取纯文本。

    OpenAI 格式: content 是 str
    Anthropic 格式: content 是 list[dict]，包含 {"type": "text", "text": "..."} 和 {"type": "thinking", ...}
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)
