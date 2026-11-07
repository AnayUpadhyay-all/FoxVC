"""
FoxVC Text Processing Shelf.
Unicode-aware text utilities that complement the basic string helpers in shelf file.

The shelf works with Python Unicode code points, not user-perceived grapheme clusters.
It uses only the Python standard library.
"""

import textwrap
import unicodedata
from typing import Any, Dict


def fox_text_normalize(value: Any, form: str = "NFC") -> str:
    """Normalize text using NFC, NFD, NFKC, or NFKD."""
    return unicodedata.normalize(str(form), str(value))


def fox_case_fold(value: Any) -> str:
    """Return Unicode-aware caseless text for comparisons."""
    return str(value).casefold()


def fox_word_count(value: Any) -> int:
    """Count whitespace-separated words."""
    return len(str(value).split())


def fox_line_count(value: Any) -> int:
    """Count logical lines; an empty string has zero lines."""
    return len(str(value).splitlines())


def fox_truncate_text(value: Any, max_length: Any, suffix: Any = "…") -> str:
    """Truncate to at most max_length code points, including the suffix."""
    text = str(value)
    limit = int(max_length)
    marker = str(suffix)

    if limit < 0:
        raise ValueError("max_length must be non-negative")
    if len(text) <= limit:
        return text
    if limit == 0:
        return ""
    if len(marker) >= limit:
        return marker[:limit]
    return text[:limit - len(marker)] + marker


def fox_wrap_text(value: Any, width: Any = 80) -> str:
    """Wrap text to a positive column width."""
    column_width = int(width)
    if column_width < 1:
        raise ValueError("width must be at least 1")
    return textwrap.fill(str(value), width=column_width)


def fox_slugify(value: Any, separator: Any = "-") -> str:
    """
    Build a readable Unicode-aware slug.
    Combining marks are removed; letters and digits from all scripts are retained.
    """
    text = unicodedata.normalize("NFKD", str(value)).casefold()
    delimiter = str(separator)
    output = []
    pending_separator = False

    for char in text:
        if unicodedata.category(char).startswith("M"):
            continue
        if char.isalnum():
            if pending_separator and output and delimiter:
                output.append(delimiter)
            output.append(char)
            pending_separator = False
        else:
            pending_separator = True

    return "".join(output).strip(delimiter) if delimiter else "".join(output)


def fox_text_length(value: Any) -> int:
    """Return the number of Unicode code points, not grapheme clusters."""
    return len(str(value))


def fox_code_point_at(value: Any, index: Any) -> int:
    """Return a code point at index, or -1 when the index is out of range."""
    text = str(value)
    position = int(index)
    if position < 0:
        position += len(text)
    if position < 0 or position >= len(text):
        return -1
    return ord(text[position])


def fox_from_code_point(value: Any) -> str:
    """Create one Unicode scalar character from an integer code point."""
    point = int(value)
    if point < 0 or point > 0x10FFFF or 0xD800 <= point <= 0xDFFF:
        raise ValueError("code point must be a valid Unicode scalar value")
    return chr(point)


def fox_reverse_text(value: Any) -> str:
    """Reverse Unicode code points; combining sequences are not grapheme-aware."""
    return str(value)[::-1]


def fox_is_alpha(value: Any) -> bool:
    """Return whether text contains letters and only combining marks alongside them."""
    text = str(value)
    if not text:
        return False
    has_letter = False
    for char in text:
        category = unicodedata.category(char)
        if category.startswith("L"):
            has_letter = True
        elif not category.startswith("M"):
            return False
    return has_letter


def fox_is_digit(value: Any) -> bool:
    """Return whether every character is a Unicode digit (false for empty text)."""
    return str(value).isdigit()


def fox_is_whitespace(value: Any) -> bool:
    """Return whether every character is whitespace (false for empty text)."""
    return str(value).isspace()


def get_text_shelf() -> Dict[str, Any]:
    """Return the public FoxVC names exposed by `fuse text`."""
    return {
        "normalizeText": fox_text_normalize,
        "caseFold": fox_case_fold,
        "wordCount": fox_word_count,
        "lineCount": fox_line_count,
        "truncateText": fox_truncate_text,
        "wrapText": fox_wrap_text,
        "slugify": fox_slugify,
        "textLength": fox_text_length,
        "codePointAt": fox_code_point_at,
        "fromCodePoint": fox_from_code_point,
        "reverseText": fox_reverse_text,
        "isAlpha": fox_is_alpha,
        "isDigit": fox_is_digit,
        "isWhitespace": fox_is_whitespace,
    }
