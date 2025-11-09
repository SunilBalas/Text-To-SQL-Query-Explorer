import functools
import streamlit as st

from Core.Utils.exception import AppError
from Core.Utils.logger import Logger

logger = Logger.get_logger()


def exception_handler(show_ui: bool = True):
    """
    Decorator for global exception handling.
    - Logs all errors.
    - Optionally shows Streamlit error message.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except AppError as e:
                logger.error(f"Application Error in {func.__name__}: {e.message}")
                if show_ui:
                    st.error(f"⚠️ {e.message}")

            except Exception as e:
                logger.exception(f"Unexpected Error in {func.__name__}: {str(e)}")
                if show_ui:
                    st.error("❌ Something went wrong. Please try again.")

        return wrapper

    return decorator
