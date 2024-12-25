import logging
import os

import dotenv
import logging_loki
from logging.handlers import RotatingFileHandler

dotenv.load_dotenv()  # Loads .env file if present

def create_logger():
    """
    Creates and returns a logger named 'custom_logger' at DEBUG level.
    
    Handlers:
        1. RotatingFileHandler (writes to 'app.log', rotates at 5MB, keeps 3 backups)
        2. StreamHandler (stdout)
        3. LokiHandler (if LOKI_URL is defined in environment variables)
    """
    logger_name = 'custom_logger'
    
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        file_handler = RotatingFileHandler(
            filename='app.log',
            maxBytes=5_000_000,  # 5 MB
            backupCount=3,       # keep up to 3 old log files
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to create file handler: {e}. Using only stream handler.")

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    loki_url = os.getenv("LOKI_URL")
    if loki_url:
        try:
            loki_user = os.getenv("LOKI_USER") or ""       # optional
            loki_pass = os.getenv("LOKI_PASSWORD") or ""   # optional
            # A set of tags (labels) to associate with each log
            tags = {"application": "my_app", "environment": os.getenv("ENV", "dev")}
            
            loki_handler = logging_loki.LokiHandler(
                url=loki_url,
                tags=tags,
                auth=(loki_user, loki_pass) if loki_user or loki_pass else None,
                version="1",  # or "0" depending on your Loki setup
                # mode="blocking"  # optional; set to 'blocking' if you want to block when Loki is down
            )
            loki_handler.setLevel(logging.DEBUG)
            loki_handler.setFormatter(formatter)
            logger.addHandler(loki_handler)
        except Exception as e:
            logger.warning(f"Failed to configure Loki handler: {e}")

    return logger

# Example usage
if __name__ == "__main__":
    logger = create_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
