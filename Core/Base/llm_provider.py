from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_core.prompts import PromptTemplate
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import LLMProviderError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


class BaseLLMProvider(ABC):
    registry: Dict[str, "BaseLLMProvider"] = {}
    _instances: Dict[str, "BaseLLMProvider"] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "llm_type"):
            BaseLLMProvider.registry[cls.llm_type] = cls
            logger.debug("📌 Registered LLM provider: %s", cls.llm_type)

    def __new__(cls, *args, **kwargs):
        if hasattr(cls, "llm_type"):
            if cls.llm_type not in cls._instances:
                logger.debug("🆕 Creating new LLM instance: %s", cls.llm_type)
                cls._instances[cls.llm_type] = super().__new__(cls)
            else:
                logger.debug("♻️ Returning existing LLM instance: %s", cls.llm_type)
            return cls._instances[cls.llm_type]
        return super().__new__(cls)

    @abstractmethod
    def create_prompt_template(self) -> PromptTemplate:
        """Create and return a PromptTemplate instance"""
        pass

    @abstractmethod
    @exception_handler(show_ui=True)
    def generate(self, prompt_template: PromptTemplate, query: Dict[str, Any]) -> str:
        """Generate output from LLM based on provided prompt and query"""
        try:
            logger.info(
                "🤖 Generating response using LLM provider: %s",
                getattr(self, "llm_type", "unknown"),
            )
        except Exception as e:
            logger.error("❌ LLM generation failed: %s", str(e))
            raise LLMProviderError(f"Failed to generate response: {str(e)}")
