from pathlib import Path
import sqlite3
import streamlit as st
from typing import Any, Dict, List, Tuple

from Core.Base.database import BaseDatabase
from Core.Enums.database import DatabaseType
from Core.Utils.error_handler import exception_handler
from Core.Utils.exception import DatabaseConnectionError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


class SQLiteDB(BaseDatabase):
    db_type = DatabaseType.SQLITE.value.lower()

    @exception_handler(show_ui=True)
    def __init__(self, config: Dict):
        if not hasattr(self, "initialized"):
            self.config = config
            self.connection = None
            self.cursor = None
            self.db_path = Path("Data/DBs")
            self.initialized = True
            logger.info("🗄️ SQLiteDB initialized with config: %s", self.config)

    @exception_handler(show_ui=True)
    def connect(self):
        try:
            if self.connection is None:
                db_file = f"{self.db_path}/{self.config.get('dbname')}.db"
                if "db_bytes" in st.session_state:
                    with open(db_file, "wb") as f:
                        f.write(st.session_state.db_bytes)
                        
                logger.info("🔌 Connecting to SQLite database: %s", db_file)
                self.connection = sqlite3.connect(db_file)
                self.cursor = self.connection.cursor()
                logger.info("✅ Connection established successfully.")
        except Exception as e:
            raise DatabaseConnectionError(f"SQLite connection failed: {str(e)}")

    @exception_handler(show_ui=True)
    def execute(self, query: str, params: List[Tuple] = None):
        try:
            self.connect()
            logger.info("⚡ Executing query: %s", query)

            if params is not None:
                self.cursor.executemany(query, params)
                logger.debug("📌 Parameters: %s", params[:5])  # log only first 5 params
            else:
                self.cursor.execute(query)

            self.connection.commit()
            logger.info("✅ Query executed and committed successfully.")
        except Exception as e:
            raise DatabaseConnectionError(f"SQLite execution failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def read(self, query: str, params: Tuple = ()):
        try:
            self.connect()
            logger.info("📖 Reading data with query: %s", query)
            self.cursor.execute(query, params)

            rows = self.cursor.fetchall()
            columns = (
                [desc[0] for desc in self.cursor.description]
                if self.cursor.description
                else []
            )
            logger.info("✅ Read %d rows.", len(rows))
            return rows, columns
        except Exception as e:
            raise DatabaseConnectionError(f"SQLite read failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def get_tables(self) -> List[str]:
        try:
            self.connect()
            logger.info("📊 Fetching table list...")
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            tables = [row[0] for row in self.cursor.fetchall()]
            logger.info("✅ Found %d tables: %s", len(tables), tables)
            return tables
        except Exception as e:
            raise DatabaseConnectionError(f"SQLite get_tables failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        try:
            self.connect()
            logger.info("📌 Fetching columns for table: %s", table)
            self.cursor.execute(f"PRAGMA table_info({table});")
            columns = [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "pk": bool(col[5]),
                }
                for col in self.cursor.fetchall()
            ]
            logger.info("✅ Found %d columns in %s", len(columns), table)
            return columns
        except Exception as e:
            raise DatabaseConnectionError(f"SQLite get_columns failed: {str(e)}")
        finally:
            self.close()

    @exception_handler(show_ui=True)
    def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        try:
            self.connect()
            logger.info("🔑 Fetching foreign keys for table: %s", table)
            self.cursor.execute(f"PRAGMA foreign_key_list({table});")
            fks = [
                {"from": fk[3], "to_table": fk[2], "to_column": fk[4]}
                for fk in self.cursor.fetchall()
            ]
            logger.info("✅ Found %d foreign keys in %s", len(fks), table)
            return fks
        except Exception as e:
            raise DatabaseConnectionError(f"SQLite get_foreign_keys failed: {str(e)}")
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
                logger.info("🔒 SQLite connection closed.")
            self.connection, self.cursor = None, None
        except Exception as e:
            raise DatabaseConnectionError(f"SQLite close failed: {str(e)}")
