import logging
from logging.handlers import RotatingFileHandler
import os

log_file = "bot.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_logs():
    try:
        with open(log_file, "r") as f:
            return "<pre>" + f.read() + "</pre>"
    except FileNotFoundError:
        return None