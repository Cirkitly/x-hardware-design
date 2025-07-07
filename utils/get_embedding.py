import os
import requests
import logging
import json

logger = logging.getLogger("llm_logger")

def get_embedding(text: str, model: str = None) -> list[float]:
    """
    Generates an embedding for the given text using the Ollama API.
    """
    if model is None:
        model = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")

    try:
        # --- START OF CHANGE ---
        # Use the correct, dedicated endpoint for embedding models.
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": model,
                "prompt": text,
            }
        )
        # --- END OF CHANGE ---
        
        if response.status_code != 200:
            try:
                error_msg = response.json().get("error", response.text)
            except json.JSONDecodeError:
                error_msg = response.text
            raise requests.exceptions.HTTPError(f"Ollama API Error: {error_msg}")

        # The response from /api/embeddings is just {"embedding": [...]}, so this works.
        embedding = response.json().get("embedding")
        if not embedding:
            raise ValueError("API response did not contain an embedding.")
            
        logger.info(f"Successfully generated embedding for text: '{text[:50]}...'")
        return embedding

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama for embedding: {e}")
        raise Exception(f"Ollama connection error for embedding: {e}")
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise

# (The __main__ block remains the same)
if __name__ == "__main__":
    try:
        print("Fetching embedding for 'Hello, world!'...")
        embedding_vector = get_embedding("Hello, world!")
        print(f"Successfully got a vector of dimension: {len(embedding_vector)}")
        print(f"First 5 values: {embedding_vector[:5]}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure Ollama is running and you have pulled the embedding model with 'ollama pull mxbai-embed-large'.")