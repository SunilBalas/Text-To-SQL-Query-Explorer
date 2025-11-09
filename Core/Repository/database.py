from typing import Dict
from Core.Factory.database import DatabaseFactory


class DatabaseRepository:
    def __init__(self, db_type: str, config: Dict):
        self.obj = DatabaseFactory.get_database(db_type, config)
