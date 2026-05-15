gituser
Okl}$47d
import requests
import json
import time
import logging
from typing import List, Dict, Any

logging.getLogger(__name__).setLevel(logging.INFO)

class JobGenerator:
    """Handles communication with the Gemini API to generate job summaries."""
    
    # Use the specific model designed for fast, high-quality text generation
    MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
    API_URL_TEMPLATE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key="
    
    # NOTE: The API key is intentionally left blank. The environment will provide it at runtime.
    API_KEY = "" 

    # --- CRITICAL SYSTEM INSTRUCTION FOR HIGH-QUALITY OUTPUT ---
    SYSTEM_INSTRUCTION = (
        "You are an expert career analyst focusing exclusively on high-leverage "
        "DevOps, SRE, and Platform Engineering roles. Your task is to generate "
        "a concise, one-paragraph summary for a job listing. "
        "The summary MUST be designed for a highly skilled Principal/Staff Engineer "
        "who is looking for roles focused on **systemic impact**, **deep technical challenges** "
        "like Ollama/LLM infrastructure, **security**, or **advanced automation**. "
        "Focus on the *most valuable* technical skills (Kubernetes, Python, advanced CI/CD) "
        "and mention any high-value keywords (Principal, Equity, Bonus, Ollama) if they "
        "are relevant to the role's implied seniority or compensation."
    )

    def __init__(self):
        """Initializes the JobGenerator."""
        self.api_url = self.API_URL_TEMPLATE + self.API_KEY
        self.headers = {'Content-Type': 'application/json'}

    def _call_gemini_api(self, prompt: str) -> str:
        """
        Calls the Gemini API with exponential backoff.
        Returns the generated text or an error message.
        """
        max_retries = 5
        base_delay = 1.0  # seconds

        payload = {
            "contents": [{ "parts": [{ "text": prompt }] }],
            "systemInstruction": {
                "parts": [{ "text": self.SYSTEM_INSTRUCTION }]
            },
            "tools": [{ "google_search": {} }] # Use search for grounding/latest information
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
                response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
                
                result = response.json()
                
                # Check for generated content
                candidate = result.get('candidates', [{}])[0]
                text_part = candidate.get('content', {}).get('parts', [{}])[0].get('text')
                
                if text_part:
                    return text_part.strip()
                
                logging.error(f"API response missing generated text. Response: {result}")
                return "Error: AI failed to generate summary text."

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logging.warning(f"API call failed ({e}). Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    logging.error(f"API call failed after {max_retries} attempts: {e}")
                    return f"Error: Failed to reach AI service after multiple retries."
            except Exception as e:
                logging.error(f"An unexpected error occurred during API processing: {e}")
                return "Error: Internal processing failure."

        return "Error: Unknown failure in API call logic."

    def generate_job_summary(self, job_title: str, company: str, location: str) -> str:
        """Generates a summary for a specific job listing."""
        prompt = (
            f"Generate a one-paragraph job summary for this role, prioritizing high-leverage "
            f"and specialized details: {job_title} at {company} in {location}."
        )
        return self._call_gemini_api(prompt)
