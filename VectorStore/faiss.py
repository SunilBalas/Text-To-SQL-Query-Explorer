import faiss
import pickle
from typing import Dict, List

from Core.Base.vectorstore import BaseVectorStore
from Core.Enums.vectorstore import VectorStoreType
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import VectorstoreError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


class FAISSVectorStore(BaseVectorStore):
    vectorstore_type = VectorStoreType.FAISS.value.lower()

    def __init__(self, config: Dict):
        try:
            if not hasattr(self, "initialized"):
                super().__init__(config.get("model"))
                self.index = None
                self.text_chunks = []
                self.initialized = True
                logger.info("FAISSVectorStore initialized successfully")
        except Exception as e:
            raise VectorstoreError(f"Initialization error: {str(e)}")

    @exception_handler(show_ui=True)
    def build_index(self, chunks: List[str]) -> bool:
        try:
            logger.info(f"Building FAISS index with {len(chunks)} chunks")
            embeddings = self.model.encode(chunks, convert_to_numpy=True)
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(embeddings)
            self.text_chunks = chunks
            logger.info("FAISS index built successfully")
            return True
        except Exception as e:
            raise VectorstoreError(f"Build index error: {str(e)}")

    @exception_handler(show_ui=True)
    def retrieve(self, query: str, k: int = 3) -> List[str]:
        try:
            if self.index is None:
                raise ValueError("Index is not built or loaded")

            logger.info(f"Retrieving top {k} chunks for query: {query}")
            query_emb = self.model.encode([query], convert_to_numpy=True)
            D, I = self.index.search(query_emb, k)
            results = [self.text_chunks[i] for i in I[0]]
            logger.info(f"Retrieved {len(results)} chunks")
            return results
        except Exception as e:
            raise VectorstoreError(f"Retrieve error: {str(e)}")

    @exception_handler(show_ui=True)
    def save_index(self, path: str):
        try:
            if self.index is None:
                raise ValueError("No index to save. Build or load an index first.")
            
            logger.info(f"Saving FAISS index to Data/Indexes/{path}.index")
            faiss.write_index(self.index, f"Data/Indexes/{path}.index")
            
            logger.info(f"Saving chunks metadata to Data/Chunks/{path}_chunks.pkl")
            with open(f"Data/Chunks/{path}_chunks.pkl", "wb") as f:
                pickle.dump(self.text_chunks, f)
            logger.info("FAISS index and chunks saved successfully")
        except Exception as e:
            raise VectorstoreError(f"Save index error: {str(e)}")

    @exception_handler(show_ui=True)
    def load_index(self, path: str, chunks: List[str] = None):
        try:
            logger.info(f"Loading FAISS index from Data/Indexes/{path}.index")
            self.index = faiss.read_index(f"Data/Indexes/{path}.index")
            try:
                logger.info(
                    f"Loading chunks metadata from Data/Chunks/{path}_chunks.pkl"
                )
                with open(f"Data/Chunks/{path}_chunks.pkl", "rb") as f:
                    self.text_chunks = pickle.load(f)
            except FileNotFoundError:
                if chunks is None:
                    raise ValueError(
                        "Chunks must be provided if metadata file is missing."
                    )
                self.text_chunks = chunks
                logger.warning("Metadata file missing. Using provided chunks.")
            logger.info("FAISS index loaded successfully")
        except Exception as e:
            raise VectorstoreError(f"Load index error: {str(e)}")
