"""Utilities for turning formatted assistant text into speech-friendly text."""
import re


def clean_text_for_tts(text: str) -> str:
    """Remove Markdown/control symbols that should never be spoken aloud."""
    value = str(text or "")
    # Fenced and inline code: keep the words, remove Markdown delimiters.
    value = re.sub(r"```[\w+-]*\s*", "", value)
    value = value.replace("```", "").replace("`", "")
    # Images/links: retain human-readable label only.
    value = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    # Headings, bold/italic/strike markers, blockquote and list decoration.
    value = re.sub(r"^\s{0,3}#{1,6}\s*", "", value, flags=re.MULTILINE)
    value = re.sub(r"\*{1,3}|_{1,3}|~~", "", value)
    value = re.sub(r"^\s*>\s?", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*[-*+]\s+", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*\d+[.)]\s+", "", value, flags=re.MULTILINE)
    # Decorative separators and HTML tags.
    value = re.sub(r"^\s*[-_=]{3,}\s*$", "", value, flags=re.MULTILINE)
    value = re.sub(r"<[^>]+>", "", value)
    # Avoid reading isolated punctuation/emoji-like decoration.
    value = re.sub(r"[\u200b\ufeff]", "", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()
