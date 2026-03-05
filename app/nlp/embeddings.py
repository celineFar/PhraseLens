"""Embedding generation using sentence-transformers and ChromaDB vector store."""

import logging

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None

COLLECTION_NAME = "passages"


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_dir)
    return _chroma_client


def get_collection() -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def add_passages_to_chroma(
    passage_ids: list[str],
    texts: list[str],
    metadatas: list[dict],
) -> None:
    """Embed and store passages in ChromaDB."""
    collection = get_collection()
    embeddings = embed_texts(texts)
    collection.upsert(
        ids=passage_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


def query_similar(query: str, n_results: int = 20, where: dict | None = None) -> dict:
    """Query ChromaDB for passages similar to the query text."""
    collection = get_collection()
    query_embedding = embed_texts([query])[0]

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    return collection.query(**kwargs)


def chroma_has_passage(passage_id: str) -> bool:
    """Check if a passage is already stored in ChromaDB."""
    collection = get_collection()
    result = collection.get(ids=[passage_id], include=[])
    return len(result["ids"]) > 0


def chroma_passage_count() -> int:
    """Return the number of passages stored in ChromaDB."""
    collection = get_collection()
    return collection.count()
