import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel
from backend.config import GEMINI_API_KEY

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

NON_LEGAL_ADVICE_INSTRUCTION = """
SYSTEM ROLE & CONSTRAINTS:
You are an objective legal document parsing assistant.
CRITICAL CONSTRAINT: You MUST NEVER provide legal advice, predict case outcomes, or tell the user what they "should" or "must" do.
Provide strictly factual classifications, structural analysis, and information extraction.
All structured output must strictly conform to the requested JSON schema.
"""

class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(self, schema: Type[T], prompt: str, system_instruction: str = "") -> T:
        """Generates structured Pydantic object output from LLM prompt."""
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini API client: {e}")

    def generate_structured(self, schema: Type[T], prompt: str, system_instruction: str = "") -> T:
        combined_instruction = f"{NON_LEGAL_ADVICE_INSTRUCTION}\n{system_instruction}".strip()
        
        if not self.client:
            raise ValueError("GEMINI_API_KEY is missing or invalid. Gemini client unavailable.")

        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=combined_instruction,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.1
        )

        # Retry once on failure
        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config
                )
                if response.text:
                    parsed_data = json.loads(response.text)
                    return schema.model_validate(parsed_data)
            except Exception as e:
                logger.warning(f"Gemini API call attempt {attempt + 1} failed: {e}")
                if attempt == 1:
                    raise RuntimeError(f"Gemini API structured generation failed after retry: {e}")
        
        raise RuntimeError("Failed to generate structured LLM output.")
