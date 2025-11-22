from enum import Enum


class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    
class DataTypeIconMap(Enum):
    INTEGER = "🔢"
    BIGINT = "🔢"
    SMALLINT = "🔢"

    TEXT = "📝"
    CHAR = "📝"
    VARCHAR = "📝"
    CHARACTER_VARYING = "📝"
    CLOB = "📝"

    REAL = "📐"
    FLOAT = "📐"
    DOUBLE = "📐"
    NUMERIC = "📐"
    DECIMAL = "📐"

    BOOLEAN = "✅"
    BOOL = "✅"

    DATE = "📅"
    TIME = "⏱️"
    TIMESTAMP = "⏱️"
    TIMESTAMP_WITHOUT_TIME_ZONE = "⏱️"

    JSON = "📦"
    JSONB = "📦"
    BLOB = "📦"
    BYTEA = "📦"

    UUID = "🆔"

    DEFAULT = "📄"
