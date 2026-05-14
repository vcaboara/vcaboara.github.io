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
    print("✓ Client created successfully")
    
    print("\n2. Testing simple generation...")
    response = client.models.generate_content(
        model='gemini-1.5-pro',
        contents='Say "Hello, World!" in exactly those words.',
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=50
        )
    )
    
    print(f"✓ Response received: {response.text}")
    print("\n✓ Gemini API connection working!")
    
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    print(f"\nFull error details:")
    import traceback
    traceback.print_exc()
