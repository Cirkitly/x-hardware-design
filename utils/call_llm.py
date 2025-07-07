import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
import requests

# (logging setup is the same)
load_dotenv()
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
cache_file = "llm_cache.json"

def call_llm(prompt: str, use_cache: bool = True) -> str:
    logger.info(f"PROMPT: {prompt}")
    cache = {}
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            logger.warning("Failed to load cache, starting with empty cache")
        if prompt in cache:
            logger.info(f"RESPONSE (from cache): {cache[prompt]}")
            return cache[prompt]

    model = os.getenv("LLM_MODEL", "llama3")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
        # --- START OF IMPROVED ERROR HANDLING ---
        if response.status_code != 200:
            try:
                # Try to get the specific error from Ollama's response
                error_msg = response.json().get("error", response.text)
            except json.JSONDecodeError:
                error_msg = response.text
            raise requests.exceptions.HTTPError(f"Ollama API Error: {error_msg}")
        # --- END OF IMPROVED ERROR HANDLING ---

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama server: {e}")
        raise Exception(f"Ollama connection error: {e}")

    try:
        response_text = response.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"Failed to parse Ollama response: {e}")
        raise Exception(f"Parsing error: {e}")

    logger.info(f"RESPONSE: {response_text}")
    if use_cache:
        cache[prompt] = response_text
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    return response_text

if __name__ == "__main__":
    test_prompt = "Hi."
    print("Making call...")
    response = call_llm(test_prompt, use_cache=False)
    print(f"Response: {response}")