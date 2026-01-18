"""LangChain-based LLM abstraction supporting multiple providers."""

from typing import Any

import structlog
from langchain_openai import ChatOpenAI

from app.config import Settings

logger = structlog.get_logger()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LLM:
    """Wrapper around LangChain supporting OpenRouter and Google Gemini."""

    def __init__(self, settings: Settings):
        """Initialize the LLM with settings."""
        self.settings = settings
        self._chat: Any = None

    def create_chat(self) -> Any:
        """Create or return cached chat model instance."""
        if self._chat is not None:
            return self._chat

        provider = self.settings.llm_provider.lower()

        if provider == "openrouter":
            self._chat = ChatOpenAI(
                model=self.settings.llm_model,
                openai_api_key=self.settings.openrouter_api_key,
                openai_api_base=OPENROUTER_BASE_URL,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Doc-to-3D Explorer",
                },
            )
            logger.info(
                "llm_initialized",
                provider="openrouter",
                model=self.settings.llm_model,
            )
        elif provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            self._chat = ChatGoogleGenerativeAI(
                model=self.settings.llm_model,
                google_api_key=self.settings.google_api_key,
                temperature=self.settings.llm_temperature,
                max_output_tokens=self.settings.llm_max_tokens,
                convert_system_message_to_human=True,
            )
            logger.info(
                "llm_initialized",
                provider="google",
                model=self.settings.llm_model,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        return self._chat

    async def generate(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        chat = self.create_chat()
        response = await chat.ainvoke(prompt)
        return response.content

    async def generate_json(self, prompt: str) -> str:
        """Generate a JSON response from the LLM.

        The prompt should instruct the LLM to return valid JSON.
        """
        chat = self.create_chat()
        response = await chat.ainvoke(prompt)
        content = response.content

        # Strip markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return content.strip()
