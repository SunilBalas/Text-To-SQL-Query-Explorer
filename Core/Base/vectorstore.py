from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer

from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import VectorstoreError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


class BaseVectorStore(ABC):
    registry = {}
    _instances = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "vectorstore_type"):
            BaseVectorStore.registry[cls.vectorstore_type] = cls
            logger.debug("📌 Registered VectorStore: %s", cls.vectorstore_type)

    def __new__(cls, *args, **kwargs):
        if hasattr(cls, "vectorstore_type"):
            if cls.vectorstore_type not in cls._instances:
                logger.debug(
                    "🆕 Creating new VectorStore instance: %s", cls.vectorstore_type
                )
                cls._instances[cls.vectorstore_type] = super().__new__(cls)
            else:
                logger.debug(
                    "♻️ Reusing existing VectorStore instance: %s", cls.vectorstore_type
                )
            return cls._instances[cls.vectorstore_type]
        return super().__new__(cls)

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        try:
            logger.info("⚙️ Initializing SentenceTransformer model: %s", model)
            self.model = SentenceTransformer(model)
            logger.info("✅ Model loaded successfully: %s", model)
        except Exception as e:
            logger.error("❌ Failed to load SentenceTransformer model: %s", str(e))
            raise VectorstoreError(f"Model initialization failed: {str(e)}")

    @abstractmethod
    @exception_handler(show_ui=True)
    def build_index(self, chunks: List[str]):
        """Build index from list of text chunks"""
        pass

    @abstractmethod
    @exception_handler(show_ui=True)
    def retrieve(self, query: str, k: int = 3) -> List[str]:
        """Retrieve top-k similar chunks"""
        pass

    @abstractmethod
    @exception_handler(show_ui=True)
    def save_index(self, path: str):
        """Persist index and metadata"""
        pass

    @abstractmethod
    @exception_handler(show_ui=True)
    def load_index(self, path: str, chunks: List[str]):
        """Load index and metadata"""
        pass
