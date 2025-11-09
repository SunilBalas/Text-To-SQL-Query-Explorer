from typing import Dict
from Core.Base.llm_provider import BaseLLMProvider
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import LLMProviderError
from Core.Utils.logger import Logger

# Import your actual LLMs so they register in BaseLLMProvider
from LLM.groq import GroqLLM

logger = Logger.get_logger()


class LLMProviderFactory:
    @staticmethod
    @exception_handler(show_ui=True)
    def get_llm_provider(llm_type: str, config: Dict):
        logger.info("🔎 Resolving LLM provider: %s", llm_type)
        _class = BaseLLMProvider.registry.get(llm_type)

        if not _class:
            logger.error("❌ Unsupported LLM provider type: %s", llm_type)
            raise LLMProviderError(f"Unsupported LLM type: {llm_type}")

        logger.info("✅ LLM provider %s resolved successfully.", _class.__name__)
        return _class(config)
