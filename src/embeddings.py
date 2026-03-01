import os
import time
from openai import OpenAI

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
BATCH_SIZE = 100

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=MODEL, input=batch)
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

        if i + BATCH_SIZE < len(texts):
            time.sleep(0.1)

    return all_embeddings


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
