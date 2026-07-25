import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
EMBEDDING_DIMENSIONS = 1024


def embed_text(text: str):
    """Create a multilingual embedding through local Ollama, never an external API."""
    if not settings.EMBEDDINGS_ENABLED:
        return None
    try:
        response = requests.post(
            f"{settings.OLLAMA_URL}/api/embed",
            json={"model": settings.EMBEDDING_MODEL, "input": text.strip()},
            timeout=(2, settings.OLLAMA_TIMEOUT),
        )
        response.raise_for_status()
        embeddings = response.json().get("embeddings", [])
        if not embeddings or len(embeddings[0]) != EMBEDDING_DIMENSIONS:
            logger.warning("Ollama returned an unexpected embedding shape")
            return None
        return embeddings[0]
    except (requests.RequestException, ValueError, TypeError):
        logger.info("Local embedding model unavailable; using lexical search")
        return None
