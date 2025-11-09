from enum import Enum


class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"