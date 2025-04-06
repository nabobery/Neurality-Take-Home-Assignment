import os
import logging
from django.conf import settings

class LoggerSetup:
    """
    Configures and provides a logger instance for the application.
    Logs to both a file and the console.
    """
    _logger = None

    @classmethod
    def get_logger(cls, name: str = __name__, level: int = logging.INFO) -> logging.Logger:
        """
        Gets a configured logger instance.

        Args:
            name (str): The name for the logger (usually __name__).
            level (int): The minimum logging level (e.g., logging.INFO, logging.DEBUG).

        Returns:
            logging.Logger: The configured logger instance.
        """
        if cls._logger is None:
            cls._logger = cls._setup_logger(name, level)
        return cls._logger

    @classmethod
    def _setup_logger(cls, name: str, level: int) -> logging.Logger:
        """Sets up the logger configuration."""
        # Ensure the logs directory exists
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, 'service.log')

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Prevent adding handlers multiple times if logger already exists with handlers
        if not logger.handlers:
            # Create handlers (file and console)
            file_handler = logging.FileHandler(log_file_path)
            stream_handler = logging.StreamHandler()

            # Create formatter and set it for both handlers
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            stream_handler.setFormatter(formatter)

            # Add handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)

        return logger

# Example of getting the logger (optional, just for demonstration)
# logger = LoggerSetup.get_logger(__name__)
# logger.info("Logger configured via LoggerSetup class.") 