import logging
import os
from datetime import datetime

class Logger:
    _logger = None

    @classmethod
    def get_logger(cls, name: str = "AppLogger") -> logging.Logger:
        """Singleton logger instance"""
        if cls._logger is None:
            cls._logger = logging.getLogger(name)
            cls._logger.setLevel(logging.DEBUG)

            # Create logs directory
            log_dir = "Logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

            # File Handler
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)

            # Console Handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)

            # Add Handlers
            cls._logger.addHandler(fh)
            cls._logger.addHandler(ch)

        return cls._logger
