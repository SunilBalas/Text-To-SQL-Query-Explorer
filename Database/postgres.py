from pathlib import Path
from typing import Any, Dict, List, Tuple

import psycopg2
from psycopg2.extras import DictCursor

from Core.Base.database import BaseDatabase
from Core.Enums.database import DatabaseType
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import DatabaseConnectionError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


class PostgresDB(BaseDatabase):
    db_type = DatabaseType.POSTGRES.value.lower()

    @exception_handler(show_ui=True)
    def __init__(self, config: Dict):
        if not hasattr(self, "initialized"):
            self.config = config
            self.connection = None
            self.cursor = None
            self.db_path = Path("Data/DBs")
            self.initialized = True
            logger.info("🗄️ PostgresDB initialized with config: %s", self.config)

    @exception_handler(show_ui=True)
    def connect(self):
        try:
            if self.connection is None:
                db_file = f"{self.db_path}/{self.config.get('dbname')}.db"
                logger.info("🔌 Connecting to Postgres database: %s", db_file)

                self.connection = psycopg2.connect(
                    dbname=self.config.get("dbname"),
                    user=self.config.get("user"),
                    password=self.config.get("password"),
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 5432),
                )

                self.cursor = self.connection.cursor(cursor_factory=DictCursor)
                logger.info("✅ Connection established successfully.")
        except Exception as e:
            logger.exception("❌ Failed to connect to Postgres database.")
            raise DatabaseConnectionError(f"Postgres connection failed: {str(e)}")

    @exception_handler(show_ui=True)
    def execute(self, query: str, params: List[Tuple] = None):
        self.connect()
        try:
            if params:
                logger.debug("📥 Executing query with params: %s", query)
                self.cursor.executemany(query, params)
            else:
                logger.debug("📥 Executing query: %s", query)
                self.cursor.execute(query)

            self.connection.commit()
            logger.info("✅ Query executed successfully.")
        except Exception as e:
            logger.error("❌ Query execution failed: %s", str(e))
            self.connection.rollback()
            raise DatabaseConnectionError(f"Postgres execution failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def read(self, query: str, params=()):
        self.connect()
        try:
            logger.debug("📥 Running read query: %s", query)
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            logger.info("✅ Query read successful, fetched %d rows.", len(rows))
            return rows, columns
        except Exception as e:
            logger.error("❌ Query read failed: %s", str(e))
            raise DatabaseConnectionError(f"Postgres read failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def get_tables(self) -> List[str]:
        self.connect()
        try:
            self.cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public';
                """
            )
            tables = [row[0] for row in self.cursor.fetchall()]
            logger.info("📋 Found tables: %s", tables)
            return tables
        except Exception as e:
            logger.error("❌ Failed to fetch tables: %s", str(e))
            raise DatabaseConnectionError(f"Postgres get_tables failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        self.connect()
        try:
            # Fetch column details
            self.cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s;
                """,
                (table,),
            )
            columns_data = self.cursor.fetchall()

            # Fetch primary key columns
            self.cursor.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = %s;
                """,
                (table,),
            )
            pk_columns = {row[0] for row in self.cursor.fetchall()}

            # Merge info
            columns = [
                {
                    "name": col[0],
                    "type": col[1],
                    "notnull": col[2] == "NO",
                    "default": col[3],
                    "pk": col[0] in pk_columns,
                }
                for col in columns_data
            ]

            logger.info("📋 Columns for table %s: %s", table, columns)
            return columns
        except Exception as e:
            logger.error("❌ Failed to fetch columns for table %s: %s", table, str(e))
            raise DatabaseConnectionError(f"Postgres get_columns failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        self.connect()
        try:
            self.cursor.execute(
                """
                SELECT
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
                """,
                (table,),
            )
            fks = [
                {"from": fk[0], "to_table": fk[1], "to_column": fk[2]}
                for fk in self.cursor.fetchall()
            ]
            logger.info("🔑 Foreign keys for table %s: %s", table, fks)
            return fks
        except Exception as e:
            logger.error(
                "❌ Failed to fetch foreign keys for table %s: %s", table, str(e)
            )
            raise DatabaseConnectionError(f"Postgres get_foreign_keys failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
                logger.debug("🛑 Cursor closed.")
            if self.connection:
                self.connection.close()
                logger.info("🔒 Postgres connection closed.")
            self.connection, self.cursor = None, None
        except Exception as e:
            logger.exception("❌ Error while closing Postgres connection.")
            raise DatabaseConnectionError(f"Postgres close failed: {str(e)}")
