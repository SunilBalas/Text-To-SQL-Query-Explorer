from typing import Dict

from Core.Base.database import BaseDatabase

from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import DatabaseConnectionError
from Core.Utils.logger import Logger

# Import database so they self-register in BaseDatabase
from Database.sqlite import SQLiteDB
from Database.postgres import PostgresDB

logger = Logger.get_logger()

class DatabaseFactory:
    @staticmethod
    @exception_handler(show_ui=True)
    def get_database(db_type: str, config: Dict):
        logger.info("🏭 Resolving database type: %s", db_type)
        _class = BaseDatabase.registry.get(db_type)

        if not _class:
            logger.error("❌ Unsupported database type requested: %s", db_type)
            raise DatabaseConnectionError(f"Unsupported database type: {db_type}")

        logger.info("✅ Database class %s resolved successfully.", _class.__name__)
        return _class(config)
