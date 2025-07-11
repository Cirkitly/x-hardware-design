import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
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

# Cache file path
cache_file = "llm_cache.json"

def call_llm(prompt: str, use_cache: bool = True, max_tokens: int = 4096) -> str:
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

    try:
        from openai import AzureOpenAI

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )

        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            # --- START OF FIX: Add a reasonable timeout to prevent hanging ---
            timeout=30.0 
            # --- END OF FIX ---
        )

        response_text = response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"LLM error: {e}")
        raise

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