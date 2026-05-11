import hashlib
import re
import html
import unicodedata
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from text_utils import deep_clean_title, deep_clean_description

class DataCleaner:
    """
    Centralized data cleaning and normalization layer for SolveStack.
    Ensures deterministic output and extracts features for deduplication and scoring.
    """
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        # Canonical mapping for tech tags
        self.canonical_tags = {
            "reactjs": "react",
            "react.js": "react",
            "nodejs": "node",
            "node.js": "node",
            "javascript": "js",
            "typescript": "ts",
            "c++": "cpp",
            "c#": "csharp",
            "py": "python",
            "ipynb": "jupyter-notebook",
            "golang": "go",
            "postgresql": "postgres",
            "mongodb": "mongo",
            "kubernetes": "k8s",
            "docker-compose": "docker",
        }

    def clean_problem(self, raw_problem: dict) -> dict:
        """
        Processes a raw problem dictionary into a cleaned and feature-enriched record.
        """
        # 1. Start with metadata and raw fields
        problem = {
            "source": raw_problem.get("source"),
            "source_id": raw_problem.get("source_id"),
            "author_name": raw_problem.get("author_name"),
            "author_id": raw_problem.get("author_id"),
            "reference_link": raw_problem.get("reference_link"),
            "date": self._parse_date(raw_problem.get("date")),
            "scraped_at": raw_problem.get("scraped_at", datetime.utcnow()),
            "cleaned_at": datetime.utcnow(),
            "clean_version": self.version,
            
            # Preserving RAW fields
            "raw_title": raw_problem.get("raw_title", ""),
            "raw_description": raw_problem.get("raw_description", ""),
            "raw_tags": raw_problem.get("raw_tags", []),
        }

        # 2. Basic Cleaning
        problem["cleaned_title"] = self._basic_clean(problem["raw_title"])
        problem["cleaned_description"] = self._basic_clean(problem["raw_description"])
        
        # 2.5 Deep Cleaning — remove HTML entities, smart quotes, markdown artifacts
        problem["cleaned_title"] = deep_clean_title(problem["cleaned_title"])
        problem["cleaned_description"] = deep_clean_description(problem["cleaned_description"])
        
        # 3. Normalization
        problem["tags"] = self._normalize_tags(problem["raw_tags"])
        problem["normalized_title"] = self._normalize_title(problem["cleaned_title"])
        
        # For backward compatibility
        problem["title"] = problem["cleaned_title"]
        problem["description"] = problem["cleaned_description"]
        problem["suggested_tech"] = ", ".join(problem["tags"])

        # 4. Feature Extraction & Hashing
        # Aggressive Title Normalization for Hashing
        norm_title = str(problem["normalized_title"] or "")
        hash_slug = re.sub(r'[^a-z0-9]', '', norm_title)
        problem["title_hash"] = self._generate_hash(hash_slug)
        
        # Metrics
        cleaned_title = str(problem["cleaned_title"] or "")
        cleaned_desc = str(problem["cleaned_description"] or "")
        
        problem["text_length"] = len(cleaned_title) + len(cleaned_desc)
        problem["word_count"] = len(cleaned_desc.split())
        
        has_code, code_count = self._detect_code(str(problem["raw_description"] or ""))
        problem["has_code_block"] = has_code
        problem["num_code_blocks"] = code_count
        
        # Gibberish & Technicality Checks
        problem["is_gibberish"] = self._is_gibberish(cleaned_title, cleaned_desc)
        problem["is_technical"] = self._check_technicality(cleaned_title, cleaned_desc, problem["tags"])

        # Passthrough scoring fields
        for field in ["upvotes", "downvotes", "comment_count", "engagement_score", "difficulty_score"]:
            problem[field] = raw_problem.get(field, 0 if "score" not in field else 0.0)

        problem["difficulty_level"] = self._calculate_difficulty_level(problem["cleaned_title"], problem["cleaned_description"], problem["tags"])

        return problem

    def _is_gibberish(self, title: str, description: str) -> bool:
        """Detects if content looks like low-quality noise or random characters."""
        content = f"{title} {description}"
        if not content.strip(): return True
        
        # 1. Word to Char ratio (gibberish often lacks spaces or has too many symbols)
        words = content.split()
        if len(words) == 0: return True
        avg_word_len = len(content) / len(words)
        if avg_word_len > 15 or avg_word_len < 2: return True
        
        # 2. Excessive non-ASCII
        non_ascii = len(re.findall(r'[^\x00-\x7F]', content))
        if non_ascii > len(content) * 0.3: return True
        
        return False

    def _is_non_english(self, text: str) -> bool:
        """Detects non-English text by checking for CJK, Cyrillic, Arabic, Thai, Devanagari, etc."""
        if not text:
            return False
        
        # Count characters in non-Latin script ranges
        cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff'       # CJK Unified
                   or '\u3040' <= c <= '\u30ff'                       # Hiragana/Katakana
                   or '\uac00' <= c <= '\ud7af'                       # Korean Hangul
                   or '\u3400' <= c <= '\u4dbf')                      # CJK Extension A
        cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
        arabic = sum(1 for c in text if '\u0600' <= c <= '\u06ff'     # Arabic
                     or '\u0590' <= c <= '\u05ff')                    # Hebrew
        thai = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
        devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097f')
        
        non_latin_total = cjk + cyrillic + arabic + thai + devanagari
        
        # If more than 2 non-Latin script chars in the title, it's non-English
        if non_latin_total > 2:
            return True
        
        # Also check ratio: if >20% of alphabetic chars are non-Latin
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars > 5 and non_latin_total / alpha_chars > 0.2:
            return True
        
        return False

    def _has_encoding_artifacts(self, text: str) -> bool:
        """Detects mojibake / encoding corruption patterns."""
        if not text:
            return False
        # Common mojibake patterns from UTF-8 decoded as Latin-1 or CP1252
        mojibake_patterns = ['â€', 'Ã¢', 'Ã©', 'Ã¨', 'Ã¼', 'Â', 'ï»¿', 'Ã', 'â€™', 'â€œ']
        for pat in mojibake_patterns:
            if pat in text:
                return True
        return False

    def passes_quality_gate(self, cleaned_problem: dict) -> tuple:
        """
        Comprehensive quality gate for scraped problems.
        Returns (passes: bool, reason: str).
        If passes=False, the problem should be rejected.
        """
        title = cleaned_problem.get("title", "") or cleaned_problem.get("cleaned_title", "") or ""
        desc = cleaned_problem.get("description", "") or cleaned_problem.get("cleaned_description", "") or ""
        
        # 1. Title too short
        if len(title.strip()) < 5:
            return False, "title_too_short"
        
        # 2. Non-English title
        if self._is_non_english(title):
            return False, "non_english_title"
        
        # 3. Non-English description (if description is primarily non-English)
        if desc and len(desc) > 50 and self._is_non_english(desc[:300]):
            return False, "non_english_description"
        
        # 4. Encoding artifacts / mojibake
        if self._has_encoding_artifacts(title):
            return False, "encoding_artifacts_title"
        
        # 5. Gibberish detection (existing)
        if self._is_gibberish(title, desc):
            return False, "gibberish"
        
        # 6. Code dump as title (mostly symbols/punctuation, not a real title)
        alpha_in_title = sum(1 for c in title if c.isalpha())
        if len(title) > 10 and alpha_in_title / len(title) < 0.3:
            return False, "code_dump_title"
        
        # 7. Title is just a file path or error code
        if re.match(r'^[A-Za-z0-9_/\\\.\-:]+$', title.strip()) and len(title.split()) <= 1:
            return False, "filepath_title"
        
        return True, "ok"

    def _check_technicality(self, title: str, description: str, raw_tags: Optional[List[str]]) -> bool:
        """Heuristic check for technical intent vs personal stories/meta content."""
        content = f"{title} {description}".lower()
        
        tags = list(raw_tags) if raw_tags else []
        tech_indicators = ["how to", "error", "exception", "broken", "implement", "deploy", "config", "bug", "crash"]
        tech_density = sum(1 for w in tech_indicators if w in content)
        
        # Low-signal personal markers
        personal_markers = ["career", "salary", "feeling", "unhappy", "hated", "medical", "diagnosis", "marriage", "wife", "boss", "new job"]
        personal_density = sum(1 for w in personal_markers if w in content)
        
        if personal_density > tech_density + 2:
            return False
            
        if tech_density == 0 and len(tags) == 0:
            return False
            
        return True

    def _calculate_difficulty_level(self, title: str, description: str, tags: List[str]) -> int:
        """
        Determines the difficulty level (1=Beginner, 2=Intermediate, 3=Advanced) based on keyword heuristics.
        """
        content = f"{title} {description}".lower()
        
        advanced_keywords = [
            "distributed", "concurrency", "scaling", "optimization", "orchestration", 
            "kubernetes", "k8s", "microservices", "architecture", "performance", "throughput", 
            "latency", "bottleneck", "memory leak", "race condition", "deadlock", "kernel", "compiler"
        ]
        
        beginner_keywords = [
            "how to", "beginner", "getting started", "tutorial", "simple", "basic", "install", 
            "setup", "error", "typo", "css", "html", "syntax", "what is"
        ]
        
        advanced_hits = sum(1 for kw in advanced_keywords if kw in content)
        beginner_hits = sum(1 for kw in beginner_keywords if kw in content)
        
        # Tag based boosts
        advanced_tags = ["c++", "cpp", "rust", "go", "golang", "kubernetes", "k8s", "docker", "aws", "gcp"]
        if any(tag in advanced_tags for tag in tags):
            advanced_hits += 2
            
        if advanced_hits >= 1:
            return 3 # Advanced
        elif beginner_hits >= 1 and advanced_hits == 0:
            return 1 # Beginner
        else:
            return 2 # Intermediate

    def _basic_clean(self, text: str) -> str:
        """Removes HTML noise and normalizes whitespace while preserving content."""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove HTML tags but preserve content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace but keep single spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _normalize_title(self, title: str) -> str:
        """Lowers case, trims, and removes common noise prefixes."""
        if not title:
            return ""
            
        title = str(title).lower()
        
        # Remove common prefixes (case-insensitive due to .lower() above)
        prefixes = [
            r'^ask hn:', r'^show hn:', r'^poll:', 
            r'^github issue:', r'^problem:', r'^issue:',
            r'^question:', r'^help:', r'^urgent:', r'^psa:'
        ]
        for pattern in prefixes:
            title = re.sub(pattern, '', title).strip()
            
        return title

    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """Standardizes tags via canonical mapping."""
        if not tags:
            return []
            
        normalized = set()
        for tag in tags:
            if not tag or not isinstance(tag, str): continue
            
            # Basic cleanup
            tag = tag.lower().strip().replace(' ', '-')
            
            # Map to canonical
            tag = self.canonical_tags.get(tag, tag)
            
            if tag:
                normalized.add(tag)
                
        return sorted(list(normalized))

    def _generate_hash(self, text: str) -> str:
        """Generates a SHA-256 hash of the normalized text."""
        if not text:
            return ""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _detect_code(self, text: str) -> Tuple[bool, int]:
        """Detects presence and count of code blocks."""
        if not text:
            return False, 0
            
        # Common markdown code block pattern
        blocks = re.findall(r'```', text)
        count = len(blocks) // 2
        
        # Also check for <code> or [code] artifacts if any left
        if count == 0:
            count = len(re.findall(r'\[code\]|<code>', text.lower()))
            
        return count > 0, count

    def _parse_date(self, date_val) -> date:
        """Ensures date is a python date object."""
        if isinstance(date_val, date):
            return date_val
        if isinstance(date_val, datetime):
            return date_val.date()
        
        if isinstance(date_val, str):
            try:
                # Expecting YYYY-MM-DD
                return datetime.strptime(date_val[:10], '%Y-%m-%d').date()
            except:
                return date.today()
                
        return date.today()
