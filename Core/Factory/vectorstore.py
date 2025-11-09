from typing import Dict
from Core.Base.vectorstore import BaseVectorStore
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import VectorstoreError
from Core.Utils.logger import Logger

# Import vector stores so they self-register in BaseVectorStore
from VectorStore.faiss import FAISSVectorStore

logger = Logger.get_logger()


class VectorStoreFactory:
    @staticmethod
    @exception_handler(show_ui=True)
    def get_vectorstore(vectorstore_type: str, config: Dict):
        logger.info(
            "🔎 Resolving VectorStore provider: %s", vectorstore_type
        )
        _class = BaseVectorStore.registry.get(vectorstore_type)

        if not _class:
            logger.error(
                "❌ Unsupported VectorStore type: %s", vectorstore_type
            )
            raise VectorstoreError(
                f"Unsupported VectorStore type: {vectorstore_type}"
            )

        logger.info(
            "✅ VectorStore provider %s resolved successfully.", _class.__name__
        )
        return _class(config)
