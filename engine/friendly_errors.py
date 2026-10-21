"""
FoxVC Everyday Language Error Explainer & Beginner Diagnostics
Translates compiler and syntax errors into warm, plain everyday language for beginners.
"""

import re
from typing import Optional


def explain_error_in_everyday_language(err_msg: str, source: str) -> Optional[str]:
    lines = source.splitlines() if source else []
    
    # Extract line number if present
    line_no = 1
    m_line = re.search(r"\[Line\s+(\d+)", str(err_msg))
    if m_line:
        try:
            line_no = int(m_line.group(1))
        except ValueError:
            pass

    faulty_line = lines[line_no - 1].strip() if (lines and 1 <= line_no <= len(lines)) else (lines[0].strip() if lines else "")

    # 1. Unclosed quotation mark
    if faulty_line.count('"') % 2 != 0 or faulty_line.count("'") % 2 != 0:
        quote_char = '"' if faulty_line.count('"') % 2 != 0 else "'"
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   It looks like you opened a quotation mark ({quote_char}) but forgot to close it.\n"
            f"   Try wrapping your full message in matching quotes, for example:\n"
            f"   --> {faulty_line}{quote_char}"
        )

    # 2. Used 'print' or 'echo' or 'console.log' instead of 'say'
    if re.match(r"^(print|echo|console\.log|printf)\b", faulty_line, re.IGNORECASE):
        suggested = re.sub(r"^(print|echo|console\.log|printf)\s*", "say ", faulty_line, flags=re.IGNORECASE)
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   In FoxVC, we use the keyword 'say' instead of 'print' to show text on the screen.\n"
            f"   Try changing it to:\n"
            f"   --> {suggested}"
        )

    # 3. Trailing math operator (e.g. "x = 10 +")
    m_trailing_op = re.search(r"[\+\-\*\/\%]\s*$", faulty_line)
    if m_trailing_op:
        op = m_trailing_op.group(0).strip()
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   You have a math operator ('{op}') at the end of the line, but nothing comes after it.\n"
            f"   Finish the calculation with a number or variable, like:\n"
            f"   --> {faulty_line} 5"
        )

    # 4. Unquoted text in 'say' statement (e.g. 'say hello' where hello has no quotes)
    m_say_unquoted = re.match(r"^say\s+([A-Za-z_][A-Za-z0-9_]*)$", faulty_line)
    if m_say_unquoted:
        word = m_say_unquoted.group(1)
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   FoxVC tried to find a variable named '{word}', but it hasn't been created yet.\n"
            f"   If you meant to print the word itself, wrap it in quotation marks:\n"
            f"   --> say \"{word}\""
        )

    # 5. Missing parentheses or brackets
    if faulty_line.count('(') != faulty_line.count(')'):
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   There is a missing parenthesis on this line. Make sure every '(' has a closing ')'."
        )
    if faulty_line.count('[') != faulty_line.count(']'):
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   There is an unclosed square bracket on this line. Make sure every '[' has a closing ']'."
        )

    # 6. Misspelled 'say' keyword
    m_typo_say = re.match(r"^([a-zA-Z]{1,4})\s+[\"']", faulty_line)
    if m_typo_say and m_typo_say.group(1).lower() != "say":
        rest = faulty_line[len(m_typo_say.group(1)):].strip()
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   Did you mean to use 'say'? In FoxVC, 'say' is the command to display text.\n"
            f"   Try:\n"
            f"   --> say {rest}"
        )

    # 7. Unexpected INDENT
    if "INDENT" in err_msg:
        return (
            f"💡 Everyday Fix (Line {line_no}):\n"
            f"   This line has extra spaces at the very beginning.\n"
            f"   In FoxVC, top-level lines shouldn't be indented—only code inside a loop or function needs spaces."
        )

    return (
        f"💡 Everyday Fix (Line {line_no}):\n"
        f"   Check line {line_no} for any typos, missing quotation marks, or incomplete math."
    )
