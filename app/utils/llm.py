"""LangChain-based LLM abstraction for Google Gemini."""

import structlog
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import Settings

logger = structlog.get_logger()


class LLM:
    """Wrapper around LangChain's Google Generative AI integration."""

    def __init__(self, settings: Settings):
        """Initialize the LLM with settings."""
        self.settings = settings
        self._chat: ChatGoogleGenerativeAI | None = None

    def create_chat(self) -> ChatGoogleGenerativeAI:
        """Create or return cached chat model instance."""
        if self._chat is None:
            self._chat = ChatGoogleGenerativeAI(
                model=self.settings.llm_model,
                google_api_key=self.settings.google_api_key,
                temperature=self.settings.llm_temperature,
                convert_system_message_to_human=True,
            )
            logger.info("llm_initialized", model=self.settings.llm_model)
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
