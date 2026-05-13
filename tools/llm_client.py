"""
tools/llm_client.py
Unified LLM client — supports Anthropic Claude, OpenAI, and Groq.
All nodes call llm_client.invoke(prompt) — provider is transparent.
"""
import os
from loguru import logger
from config.settings import LLMConfig


class LLMClient:
    """
    Singleton LLM client. Reads LLM_PROVIDER from .env to pick backend.
    Supported: 'anthropic' (default), 'openai', 'groq'
    """

    def __init__(self):
        self.provider = LLMConfig.PROVIDER
        self.model    = LLMConfig.MODEL
        self._client  = None
        self._init_client()

    def _init_client(self):
        if self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=LLMConfig.API_KEY)
                logger.info(f"LLM | Anthropic ready | model={self.model}")
            except ImportError:
                logger.warning("LLM | anthropic not installed — falling back to openai")
                self.provider = "openai"
                self._init_openai()

        elif self.provider == "groq":
            try:
                from langchain_groq import ChatGroq
                self._client = ChatGroq(
                    api_key=os.getenv("GROQ_API_KEY"),
                    model_name=self.model or "llama-3.1-8b-instant",
                )
                logger.info(f"LLM | Groq ready | model={self.model}")
            except ImportError:
                logger.warning("LLM | groq not installed — falling back to openai")
                self.provider = "openai"
                self._init_openai()

        else:
            self._init_openai()

    def _init_openai(self):
        try:
            from langchain_openai import ChatOpenAI
            self._client = ChatOpenAI(
                api_key=LLMConfig.API_KEY,
                model=self.model or "gpt-4o",
            )
            logger.info(f"LLM | OpenAI ready | model={self.model}")
        except ImportError:
            logger.error("LLM | No LLM package found. Install anthropic, langchain-openai, or langchain-groq.")
            raise

    def invoke(self, prompt: str) -> str:
        """Single-turn LLM call. Returns plain string response."""
        try:
            if self.provider == "anthropic":
                import anthropic
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text.strip()
            else:
                response = self._client.invoke(prompt)
                return response.content.strip()
        except Exception as e:
            logger.error(f"LLM | invoke failed: {e}")
            raise


# Singleton — imported and reused by all nodes
llm_client = LLMClient()
