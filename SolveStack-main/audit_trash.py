"""Deep audit - check ALL titles for quality issues."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import engine
from sqlalchemy import text
import re

conn = engine.connect()
rows = conn.execute(text(
    "SELECT ps_id, title, source, description FROM problems ORDER BY ps_id"
)).fetchall()

print(f"Total: {len(rows)}\n")

issues = []

for row in rows:
    ps_id, title, source, desc = row
    t = (title or "").strip()
    d = (desc or "")[:300]
    flags = []
    
    # 1. Non-English chars (CJK, Cyrillic, Arabic, Thai, etc.)
    non_latin = sum(1 for c in t if ord(c) > 127 and not c in '—–''""•…é​ñü')
    if non_latin > 2:
        flags.append(f"non_latin({non_latin})")
    
    # 2. Encoding artifacts: ?, â€, Ã, Â, etc.
    if 'â€' in t or 'Ã' in t or 'Â' in t or '\x00' in t:
        flags.append("encoding_artifacts")
    if '\\u' in t or '&#' in t or '&amp;' in t or '&lt;' in t:
        flags.append("html_entities")
    
    # 3. Starts with [P] [D] [R] tags (reddit noise)
    if re.match(r'^\[?[PDR]\]?\s', t):
        # Not necessarily trash, but flag for review
        pass
    
    # 4. Title is too short or meaningless
    if len(t) < 10:
        flags.append(f"too_short({len(t)})")
    
    # 5. Title looks like a stack trace / error dump
    if t.count('.') > 5 and t.count(' ') < 3:
        flags.append("looks_like_path")
    
    # 6. Excessive punctuation
    punct_ratio = sum(1 for c in t if c in '!@#$%^&*(){}[]|\\<>') / max(len(t), 1)
    if punct_ratio > 0.15:
        flags.append(f"excessive_punct({punct_ratio:.0%})")
    
    # 7. Looks like code, not a title
    if any(kw in t for kw in ['import ', 'from ', 'def ', 'class ', 'function ', 'const ', 'var ', 'let ']):
        if t.count(' ') < 4:
            flags.append("code_fragment")
    
    # 8. Check for garbled/mojibake patterns
    if re.search(r'[ÃÂ¢¡¿]+', t):
        flags.append("mojibake")
    
    # 9. Non-English description (even if title looks OK)
    if d:
        desc_non_latin = sum(1 for c in d[:200] if ord(c) > 127 and not c in '—–''""•…éñü')
        if desc_non_latin > 20:
            flags.append(f"non_english_desc({desc_non_latin})")
    
    if flags:
        safe = t[:70].encode('ascii', errors='replace').decode('ascii')
        issues.append((ps_id, safe, source, flags))

print(f"Problems with issues: {len(issues)}\n")
for ps_id, title, source, flags in sorted(issues, key=lambda x: -len(x[3])):
    print(f"  PS#{ps_id:3d} [{', '.join(flags)}]")
    print(f"         ({source}) {title}")
    print()

conn.close()
