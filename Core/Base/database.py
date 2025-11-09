from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import DatabaseConnectionError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


class BaseDatabase(ABC):
    registry: Dict[str, "BaseDatabase"] = {}
    _instances: Dict[str, "BaseDatabase"] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "db_type"):
            BaseDatabase.registry[cls.db_type] = cls
            logger.debug("📌 Registered Database provider: %s", cls.db_type)

    def __new__(cls, *args, **kwargs):
        if hasattr(cls, "db_type"):
            if cls.db_type not in cls._instances:
                logger.debug("🆕 Creating new instance for DB: %s", cls.db_type)
                cls._instances[cls.db_type] = super().__new__(cls)
            else:
                logger.debug("♻️ Returning existing instance for DB: %s", cls.db_type)
            return cls._instances[cls.db_type]
        return super().__new__(cls)

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def execute(self, query: str, params: List[Tuple] = None) -> None:
        pass

    @abstractmethod
    def read(self, query, params=()):
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        pass

    @abstractmethod
    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        pass

    @exception_handler(show_ui=True)
    def get_schema(self) -> Dict[str, Dict[str, Any]]:
        """Fetch schema for all tables in the database"""
        try:
            logger.info(
                "📂 Fetching schema for database type: %s",
                getattr(self, "db_type", "unknown"),
            )
            schema = {}
            for table in self.get_tables():
                schema[table] = {
                    "columns": self.get_columns(table),
                    "foreign_keys": self.get_foreign_keys(table),
                }
            logger.info(
                "✅ Schema fetched successfully for DB: %s",
                getattr(self, "db_type", "unknown"),
            )
            return schema
        except Exception as e:
            logger.error("❌ Failed to fetch schema: %s", str(e))
            raise DatabaseConnectionError(f"Failed to fetch schema: {str(e)}")
