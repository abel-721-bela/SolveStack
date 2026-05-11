
import re
import html
import unicodedata

def clean_text(text: str) -> str:
    """
    Robustly clean text by:
    1. Decoding HTML entities (e.g., &#x27; -> ', &amp; -> &)
    2. Normalizing unicode characters (e.g., full-width punctuation to standard)
    3. Removing URLs
    4. Removing HTML tags
    5. Normalizing whitespace
    6. Stripping leading/trailing spaces
    """
    if not text:
        return ""

    # 1. Decode HTML entities multiple times (in case of double encoding)
    # Using html.unescape which is robust
    text = html.unescape(text)
    
    # 2. Normalize Unicode characters (NFKC handles full-width characters)
    # This converts things like the full-width colon "：" to standard ":"
    text = unicodedata.normalize('NFKC', text)

    # 3. Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # 4. Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # 5. Normalize whitespace (including tabs, newlines, and non-breaking spaces)
    # Replace \xa0 (non-breaking space) and other variants with standard space
    text = re.sub(r'\s+', ' ', text)
    
    # 6. Final strip
    return text.strip()

def deep_clean_title(title: str) -> str:
    """
    Aggressively clean a title for clear, readable display.
    Handles:
    - Double-encoded HTML entities (&amp;quot; -> ")
    - Smart quotes/dashes -> ASCII equivalents
    - Markdown artifacts (backticks, code fences)
    - Control characters
    - Surrounding quotes
    - Excessive punctuation
    """
    if not title:
        return ""

    # 1. Multi-pass HTML entity decoding (handles double/triple encoding)
    for _ in range(3):
        decoded = html.unescape(title)
        if decoded == title:
            break
        title = decoded

    # 2. Normalize Unicode (NFKC: compatibility decomposition + canonical composition)
    title = unicodedata.normalize('NFKC', title)

    # 3. Replace smart quotes and dashes with ASCII equivalents
    replacements = {
        '\u2018': "'", '\u2019': "'",   # Smart single quotes
        '\u201C': '"', '\u201D': '"',   # Smart double quotes
        '\u2013': '-', '\u2014': '-',   # En-dash, em-dash
        '\u2026': '...',                # Ellipsis
        '\u00A0': ' ',                  # Non-breaking space
        '\u200B': '',                   # Zero-width space
        '\u200C': '', '\u200D': '',     # Zero-width non-joiner/joiner
        '\uFEFF': '',                   # BOM
    }
    for old, new in replacements.items():
        title = title.replace(old, new)

    # 4. Remove control characters (keep printable + basic whitespace)
    title = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', title)

    # 5. Remove markdown artifacts
    title = re.sub(r'```[\s\S]*?```', '', title)  # Fenced code blocks
    title = re.sub(r'`([^`]*)`', r'\1', title)     # Inline code (keep content)
    title = re.sub(r'\*\*([^*]*)\*\*', r'\1', title)  # Bold
    title = re.sub(r'\*([^*]*)\*', r'\1', title)       # Italic
    title = re.sub(r'^#{1,6}\s+', '', title)            # Heading markers

    # 6. Remove HTML tags
    title = re.sub(r'<[^>]+>', '', title)

    # 7. Remove URLs
    title = re.sub(r'https?://\S+', '', title)

    # 8. Clean up log-line prefixes (e.g., "04-27 13:18:32.957 E AndroidRuntime:")
    title = re.sub(r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d+\s+\d+\s+\w+\s+\w+:\s*', '', title)

    # 9. Remove surrounding quotes
    title = title.strip()
    if len(title) >= 2 and title[0] == title[-1] and title[0] in ('"', "'"):
        title = title[1:-1].strip()

    # 10. Normalize whitespace
    title = re.sub(r'\s+', ' ', title)

    # 11. Remove trailing/leading punctuation clutter
    title = title.strip(' .,;:!?-')

    # 12. Capitalize first letter if lowercase
    if title and title[0].islower():
        title = title[0].upper() + title[1:]

    return title.strip()


def deep_clean_description(description: str) -> str:
    """
    Clean description text for readable display.
    Removes code blocks, stack traces, and excessive technical noise
    while keeping the core problem statement.
    """
    if not description:
        return ""

    # 1. Multi-pass HTML entity decoding
    for _ in range(3):
        decoded = html.unescape(description)
        if decoded == description:
            break
        description = decoded

    # 2. Normalize Unicode
    description = unicodedata.normalize('NFKC', description)

    # 3. Replace smart quotes/dashes
    replacements = {
        '\u2018': "'", '\u2019': "'",
        '\u201C': '"', '\u201D': '"',
        '\u2013': '-', '\u2014': '-',
        '\u2026': '...',
        '\u00A0': ' ',
        '\u200B': '', '\u200C': '', '\u200D': '',
        '\uFEFF': '',
    }
    for old, new in replacements.items():
        description = description.replace(old, new)

    # 4. Remove control characters
    description = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', description)

    # 5. Remove fenced code blocks entirely
    description = re.sub(r'```[\s\S]*?```', ' [code snippet] ', description)

    # 6. Remove inline code backticks (keep content)
    description = re.sub(r'`([^`]*)`', r'\1', description)

    # 7. Remove HTML tags
    description = re.sub(r'<[^>]+>', '', description)

    # 8. Remove URLs
    description = re.sub(r'https?://\S+', '', description)

    # 9. Remove stack trace lines
    description = re.sub(r'^\s*(at\s+[\w.$]+\(.*?\))\s*$', '', description, flags=re.MULTILINE)
    description = re.sub(r'^\s*\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+.*$', '', description, flags=re.MULTILINE)

    # 10. Normalize whitespace
    description = re.sub(r'\n{3,}', '\n\n', description)
    description = re.sub(r'[ \t]+', ' ', description)

    return description.strip()


def is_mostly_english(text: str, threshold: float = 0.8) -> bool:
    """
    Heuristic to check if a string is mostly English based on Latin characters and common English punctuation.
    Useful for filtering out purely Chinese/Russian/etc. content if desired.
    """
    if not text:
        return True
    
    # Count Latin characters, numbers, and basic punctuation
    total_chars = len(text)
    latin_chars = len(re.findall(r'[a-zA-Z0-9\s.,!?;:\'\"()\[\]\-]', text))
    
    return (latin_chars / total_chars) >= threshold if total_chars > 0 else True

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Safely truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
