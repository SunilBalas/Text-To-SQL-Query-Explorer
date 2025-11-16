class AppError(Exception):
    """Base class for all custom exceptions."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class DatabaseConnectionError(AppError):
    """Raised when a DB connection fails."""
    pass

class QueryExecutionError(AppError):
    """Raised when SQL query execution fails."""
    pass

class VectorstoreError(AppError):
    """Raised when Vector DB operations fail."""
    pass

class LLMProviderError(AppError):
    """Raised when LLM Provider has issues."""
    pass

class FileIOError(AppError):
    """Raised for Streamlit app related errors."""
    pass