"""
Humanize Service — AI-powered plain-English explanations for technical problems.

Strategy:
  1. Try Gemini API first (google-generativeai)
  2. If Gemini fails / is rate-limited, fall back to Groq API (llama)
  3. If both fail, generate a heuristic summary from title + description
"""

import os
import re
import time
import json
import requests
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Track which provider to use (switches to Groq when Gemini is exhausted)
_active_provider = "gemini"
_gemini_failures = 0
_MAX_GEMINI_FAILURES = 3  # Switch to Groq after 3 consecutive Gemini failures


SYSTEM_PROMPT = """You are a friendly explainer. Given a technical problem title and description from a developer forum or GitHub issue, write a **1-2 sentence plain English explanation** of what the problem is about.

Rules:
- Write for someone who is NOT a programmer. Avoid jargon.
- Do NOT repeat the title verbatim.
- Do NOT mention specific code, variable names, file paths, or error codes.
- Do NOT include any code snippets, brackets, or technical syntax.
- Focus on WHAT the person is trying to do and WHY it's not working.
- Keep it between 15-40 words. Write COMPLETE sentences that end with a period.
- Do NOT use markdown formatting, bullet points, or quotes.
- Do NOT start with "The user" or "A developer". Start directly with the action or situation.
- Your response must be ONLY the explanation — nothing else.

Examples:
- Title: "Debugging Jupyter Notebook in VS Code"
  → Having trouble finding and fixing errors in a coding notebook because heavy software libraries take too long to reload every time a change is made.

- Title: "PostgreSQL Error canceling statement due to statement timeout"
  → A database query is being automatically stopped because it takes too long to fetch thousands of records at once.

- Title: "How do I resolve this circular import?"
  → Two parts of a program depend on each other in a loop, causing the software to crash when it tries to start up.
"""


def _call_gemini(title: str, description: str) -> Optional[str]:
    """Call Google Gemini API for humanized explanation."""
    global _gemini_failures, _active_provider

    if not GEMINI_API_KEY:
        return None

    # Truncate description to avoid token limits
    desc_snippet = (description or "")[:500]

    user_prompt = f"Title: {title}\nDescription: {desc_snippet}\n\nPlain English explanation:"

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_PROMPT + "\n\n" + user_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 200,
                "topP": 0.8
            }
        }

        response = requests.post(url, json=payload, timeout=15)

        if response.status_code == 429:
            # Rate limited — switch to Groq
            print(f"  WARN Gemini rate limited (429). Switching to Groq.")
            _gemini_failures = _MAX_GEMINI_FAILURES
            _active_provider = "groq"
            return None

        if response.status_code != 200:
            print(f"  WARN Gemini HTTP {response.status_code}: {response.text[:100]}")
            _gemini_failures += 1
            if _gemini_failures >= _MAX_GEMINI_FAILURES:
                print(f"  WARN Gemini failed {_gemini_failures} times. Switching to Groq.")
                _active_provider = "groq"
            return None

        data = response.json()
        # Extract text from Gemini response
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                result = parts[0].get("text", "").strip()
                # Clean up any markdown or quotes
                result = result.strip('"\'')
                result = re.sub(r'^[\-\*•]\s*', '', result)
                _gemini_failures = 0  # Reset on success
                return result

        return None

    except requests.Timeout:
        print(f"  WARN Gemini timeout")
        _gemini_failures += 1
        if _gemini_failures >= _MAX_GEMINI_FAILURES:
            _active_provider = "groq"
        return None
    except Exception as e:
        print(f"  WARN Gemini error: {type(e).__name__}: {str(e)[:80]}")
        _gemini_failures += 1
        if _gemini_failures >= _MAX_GEMINI_FAILURES:
            _active_provider = "groq"
        return None


def _call_groq(title: str, description: str) -> Optional[str]:
    """Call Groq API (LLaMA) for humanized explanation."""
    if not GROQ_API_KEY:
        return None

    desc_snippet = (description or "")[:500]
    user_prompt = f"Title: {title}\nDescription: {desc_snippet}\n\nPlain English explanation:"

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 200,
            "top_p": 0.8
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 429:
            print(f"  WARN Groq rate limited (429).")
            return None

        if response.status_code != 200:
            print(f"  WARN Groq HTTP {response.status_code}: {response.text[:100]}")
            return None

        data = response.json()
        choices = data.get("choices", [])
        if choices:
            result = choices[0].get("message", {}).get("content", "").strip()
            result = result.strip('"\'')
            result = re.sub(r'^[\-\*•]\s*', '', result)
            return result

        return None

    except requests.Timeout:
        print(f"  WARN Groq timeout")
        return None
    except Exception as e:
        print(f"  WARN Groq error: {type(e).__name__}: {str(e)[:80]}")
        return None


def _heuristic_summary(title: str, description: str) -> str:
    """
    Generate a basic heuristic summary when both APIs fail.
    Strips technical jargon and creates a readable sentence.
    """
    # Use title as base, clean it up
    clean_title = title.strip().rstrip('.')

    # Extract first meaningful sentence from description
    if description:
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', description)
        # Find first sentence that's not too short and not code
        for sent in sentences[:3]:
            sent = sent.strip()
            if len(sent) > 20 and not sent.startswith(('import ', 'from ', 'def ', 'class ', '{', '```')):
                # Truncate if too long
                if len(sent) > 120:
                    sent = sent[:117] + "..."
                return f"{clean_title} - {sent}"

    return f"{clean_title}."


def humanize_problem(title: str, description: str) -> Tuple[str, str]:
    """
    Generate a plain-English explanation for a technical problem.

    Returns:
        Tuple of (explanation_text, provider_used)
        provider_used is one of: "gemini", "groq", "heuristic"
    """
    global _active_provider

    explanation = None
    provider = "heuristic"

    # 1. Try Gemini first (unless we've switched to Groq)
    if _active_provider == "gemini":
        explanation = _call_gemini(title, description)
        if explanation:
            provider = "gemini"

    # 2. Fallback to Groq
    if not explanation:
        explanation = _call_groq(title, description)
        if explanation:
            provider = "groq"

    # 3. Fallback to heuristic
    if not explanation:
        explanation = _heuristic_summary(title, description)
        provider = "heuristic"

    # Final validation & cleanup
    if explanation:
        explanation = _post_process_explanation(explanation, title)
    
    # Ensure it's not just the title repeated
    if explanation and _is_just_title_copy(title, explanation):
        explanation = _heuristic_summary(title, description)
        provider = "heuristic"

    return explanation, provider


def _post_process_explanation(explanation: str, title: str) -> str:
    """Clean up and validate the generated explanation."""
    if not explanation:
        return explanation
    
    # Strip markdown formatting
    explanation = re.sub(r'\*\*|__|~~|`', '', explanation)
    explanation = re.sub(r'^[\-\*•]\s*', '', explanation)
    explanation = explanation.strip().strip('"\'')
    
    # Remove any code snippets that leaked through
    explanation = re.sub(r'```[\s\S]*?```', '', explanation)
    explanation = re.sub(r'`[^`]+`', '', explanation)
    explanation = re.sub(r'\[code snippet\]', '', explanation, flags=re.IGNORECASE)
    explanation = re.sub(r'\[code\].*?\[/code\]', '', explanation, flags=re.IGNORECASE|re.DOTALL)
    
    # Remove file paths
    explanation = re.sub(r'\S+/\S+\.\w{1,5}', '', explanation)
    
    # Remove lines that look like code (contain = { } ; import etc.)
    lines = explanation.split('\n')
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like code
        code_indicators = ['import ', 'from ', 'def ', 'class ', 'const ', 'var ', 'let ', ' = ', '();', '{}', '//']
        if any(ci in line for ci in code_indicators) and len(line) < 100:
            continue
        clean_lines.append(line)
    
    explanation = ' '.join(clean_lines)
    
    # Collapse whitespace
    explanation = re.sub(r'\s+', ' ', explanation).strip()
    
    # Ensure it ends with proper punctuation
    if explanation and explanation[-1] not in '.!?':
        # Try to find the last complete sentence
        last_period = max(explanation.rfind('.'), explanation.rfind('!'), explanation.rfind('?'))
        if last_period > len(explanation) * 0.5:  # If we have at least half the text as complete sentence
            explanation = explanation[:last_period + 1]
        else:
            # Just add a period
            explanation = explanation.rstrip(',;:-') + '.'
    
    return explanation.strip()


def _is_just_title_copy(title: str, explanation: str) -> bool:
    """Check if the explanation is just a copy/paraphrase of the title."""
    title_lower = title.lower().strip().rstrip('.')
    expl_lower = explanation.lower().strip().rstrip('.')

    # Exact match or starts with title
    if expl_lower == title_lower:
        return True
    if expl_lower.startswith(title_lower):
        # Check if only a few extra words were added
        extra = expl_lower[len(title_lower):].strip()
        if len(extra.split()) < 5:
            return True

    return False


# Singleton access
_humanize_service = None

def get_humanize_service():
    """Return the module-level functions (no state needed)."""
    return humanize_problem
