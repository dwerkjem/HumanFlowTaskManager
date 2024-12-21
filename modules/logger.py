import logging
import logging_loki
import dotenv


handler = logging_loki.LokiHandler(
    url="https://my-loki-instance/loki/api/v1/push", 
    tags={"application": "my-app"},
    auth=("username", "password"),
    version="1",
)

def create_logger():
    logger = logging.getLogger("Human-Flow-Task-Manager-Logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

