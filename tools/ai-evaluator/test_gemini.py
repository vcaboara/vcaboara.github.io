"""Quick test script to debug Gemini API connection."""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

print(f"API Key loaded: {GEMINI_API_KEY[:10]}...")

try:
    print("\n1. Creating Gemini client...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("OK Client created successfully")

    print("\n2. Listing available models...")
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(f"  - {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"    Supports: {model.supported_generation_methods}")
    
    print("\n3. Testing simple generation with gemini-3-flash-preview...")
    
    response = client.models.generate_content(
        model='models/gemini-3-flash-preview',
        contents='Say "Hello, World!" in exactly those words.'
    )

    print(f"OK Response received: {response.text}")
    print("\nOK Gemini API connection working!")

except Exception as e:
    print(f"\nX Error: {type(e).__name__}")
    print(f"  Message: {str(e)[:200]}")  # Truncate long messages
