import logging
import os
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("ai-helper")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = [
    "deepseek/deepseek-chat:free",
    "qwen/qwq-32b:free",
    "google/gemini-2.0-pro-exp-02-05:free",
]

OCR_MODEL = "gemini-2.0-flash-001"

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
CAPTURE_COOLDOWN = 1.0
