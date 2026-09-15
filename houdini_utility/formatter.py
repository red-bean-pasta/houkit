import re


def snake_case(s):
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'[\s\-]+', '_', s)
    return s.lower()

def title_case(s):
    words = re.findall(r'[A-Za-z0-9]+', re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', s))
    return ' '.join(word.capitalize() for word in words)

def pascal_case(s):
    return title_case(s).replace(' ', '')


def affix_text(prefix: str, *affixes: int | str | float) -> str:
    """Concatenate a prefix directly with underscore-joined affixes.

    Example: affix_attribute_value("pane", 1, 2) -> "pane1_2"
             affix_attribute_value("pane_", 1, 2) -> "pane_1_2"
    """
    return prefix + "_".join(map(str, affixes))