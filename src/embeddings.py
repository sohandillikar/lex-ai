import os
from openai import OpenAI

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
# OpenAI allows 2048 inputs/request, 300k tokens total. ~500 tokens/chunk -> ~400 safe.
BATCH_SIZE = 200

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

    return all_embeddings


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
