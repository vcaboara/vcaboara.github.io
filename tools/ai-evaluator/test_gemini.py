"""Quick test script to debug Gemini API connection."""
import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in .env")
    exit(1)

logger.info(f"API Key loaded: {GEMINI_API_KEY[:10]}...")

try:
    logger.info("1. Creating Gemini client...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("OK Client created successfully")

    logger.info("2. Listing available models...")
    models = client.models.list()
    logger.info("Available models:")
    for model in models:
        logger.info(f"  - {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            logger.info(f"    Supports: {model.supported_generation_methods}")

    logger.info("3. Testing simple generation with gemini-3-flash-preview...")

    response = client.models.generate_content(
        model='models/gemini-3-flash-preview',
        contents='Say "Hello, World!" in exactly those words.'
    )

    logger.info(f"OK Response received: {response.text}")
    logger.info("OK Gemini API connection working!")

except Exception as e:
    logger.error(f"Error: {type(e).__name__}")
    logger.error(f"  Message: {str(e)[:200]}")  # Truncate long messages
