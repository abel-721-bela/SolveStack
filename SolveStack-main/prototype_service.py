import os
import logging
from groq import AsyncGroq
from models import Problem
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class PrototypeService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            print(f"[AI] Groq API Key found (starts with {self.api_key[:8]}...)")
            self.client = AsyncGroq(api_key=self.api_key)
            self.model = "llama3-70b-8192"
        else:
            self.client = None
            logger.warning("GROQ_API_KEY not found in environment. AI roadmap features will be disabled.")

    async def generate_implementation_plan(self, problem: Problem) -> str:
        """
        Generate a professional 3-step implementation roadmap for a given problem using Groq.
        """
        if not self.client:
            return "AI Generation is currently unavailable (Missing GROQ_API_KEY)."

        tags = ', '.join(problem.tags) if problem.tags else 'N/A'
        prompt = f"""Given this engineering problem:
Title: {problem.title}
Description: {problem.description}
Tags: {tags}

Act as a Principal Software Engineer. Provide a high-impact, professional 3-step implementation plan to build a Minimum Viable Product (MVP) or solve the core technical challenge.

Format your response EXACTLY like this (nothing else, no extra lines):
1. [Step Name]: [Concise 2-sentence description focusing on architecture and tech stack]
2. [Step Name]: [Concise 2-sentence description focusing on core logic/implementation]
3. [Step Name]: [Concise 2-sentence description focusing on deployment/scaling]

Keep it highly technical and concrete. Avoid fluff or preamble."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior software architect. Respond ONLY with the numbered implementation steps in the exact format requested. No preamble, no extra commentary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=512,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating Groq roadmap: {error_msg}")
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                return "Rate limit reached. Please try again in a moment."
            return f"Failed to generate implementation plan: {error_msg}"


# Singleton
_prototype_service = None

def get_prototype_service():
    global _prototype_service
    if _prototype_service is None:
        _prototype_service = PrototypeService()
    return _prototype_service
