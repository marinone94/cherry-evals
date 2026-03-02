"""Embedding generation for datasets using provider interface."""

import time
from typing import Any

from qdrant_client.models import PointStruct
from sqlalchemy import select

from cherry_evals.embeddings.google_embeddings import GoogleEmbeddingProvider
from cherry_evals.embeddings.provider import EmbeddingProvider
from db.postgres.base import SessionLocal
from db.postgres.models import Dataset, Example
from db.qdrant.client import create_collection, get_qdrant_client, upsert_vectors


def format_example_for_embedding(example: Example) -> str:
    """Format an example for embedding generation.

    Combines question and choices into a single text.
    """
    text = example.question
    if example.choices:
        choices_text = " ".join(example.choices)
        text = f"{text} {choices_text}"
    return text


def _get_provider(model: str) -> EmbeddingProvider:
    """Get embedding provider for a given model name."""
    # Google models
    if model.startswith("text-embedding-"):
        return GoogleEmbeddingProvider(model=model)

    raise ValueError(f"Unknown embedding model: {model}. Available: text-embedding-004")


def generate_embeddings_for_dataset(
    dataset_name: str,
    model: str = "text-embedding-004",
    batch_size: int = 100,
    limit: int | None = None,
) -> dict[str, Any]:
    """Generate embeddings for all examples in a dataset.

    Args:
        dataset_name: Name of the dataset (e.g., "MMLU")
        model: Embedding model to use (e.g., "text-embedding-004")
        batch_size: Number of examples to process in each batch
        limit: Optional limit on number of examples (for testing)

    Returns:
        Dictionary with generation statistics
    """
    provider = _get_provider(model)
    qdrant = get_qdrant_client()

    collection_name = f"{dataset_name.lower()}_embeddings"
    create_collection(qdrant, collection_name, provider.dimensions)

    db = SessionLocal()

    try:
        stmt = select(Dataset).where(Dataset.name == dataset_name)
        dataset = db.execute(stmt).scalar_one_or_none()

        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_name}")

        query = db.query(Example).filter(Example.dataset_id == dataset.id)
        if limit:
            query = query.limit(limit)

        examples = query.all()
        total_examples = len(examples)

        print(f"Generating embeddings for {total_examples} examples...")
        print(f"Model: {provider.model_name} ({provider.dimensions} dims)")
        print(f"Batch size: {batch_size}")

        total_embeddings = 0
        start_time = time.time()

        for i in range(0, total_examples, batch_size):
            batch = examples[i : i + batch_size]
            batch_texts = [format_example_for_embedding(ex) for ex in batch]

            vectors = provider.embed_batch(batch_texts)

            points = []
            for example, vector in zip(batch, vectors):
                point = PointStruct(
                    id=example.id,
                    vector=vector,
                    payload={
                        "example_id": example.id,
                        "dataset_id": dataset.id,
                        "dataset_name": dataset_name,
                        "question": example.question[:500],
                        "subject": example.example_metadata.get("subject")
                        if example.example_metadata
                        else None,
                        "split": example.example_metadata.get("split")
                        if example.example_metadata
                        else None,
                    },
                )
                points.append(point)

            upsert_vectors(qdrant, collection_name, points)
            total_embeddings += len(batch)

            if (i // batch_size + 1) % 10 == 0 or i + batch_size >= total_examples:
                elapsed = time.time() - start_time
                rate = total_embeddings / elapsed if elapsed > 0 else 0
                print(
                    f"Progress: {total_embeddings}/{total_examples} "
                    f"({total_embeddings / total_examples * 100:.1f}%) "
                    f"- {rate:.1f} examples/sec"
                )

            # Brief pause between batches to respect rate limits
            if i + batch_size < total_examples:
                time.sleep(0.1)

        elapsed_time = time.time() - start_time

        stats = {
            "dataset_name": dataset_name,
            "model": provider.model_name,
            "dimensions": provider.dimensions,
            "collection_name": collection_name,
            "total_examples": total_examples,
            "total_embeddings": total_embeddings,
            "elapsed_seconds": elapsed_time,
            "examples_per_second": total_embeddings / elapsed_time if elapsed_time > 0 else 0,
        }

        print("\nEmbedding generation complete!")
        print(f"  Total embeddings: {total_embeddings}")
        print(f"  Elapsed time: {elapsed_time:.1f}s")
        print(f"  Rate: {stats['examples_per_second']:.1f} examples/sec")
        print(f"  Qdrant collection: {collection_name}")

        return stats

    finally:
        db.close()
