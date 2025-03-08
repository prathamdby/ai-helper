import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ai-helper")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)
