"""OpenAI embedding generation."""

import time
from typing import Any

from openai import OpenAI
from qdrant_client.models import PointStruct
from sqlalchemy import select

from cherry_evals.config import settings
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


def generate_embeddings_for_dataset(
    dataset_name: str,
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
    limit: int | None = None,
) -> dict[str, Any]:
    """Generate embeddings for all examples in a dataset using OpenAI API.

    Args:
        dataset_name: Name of the dataset (e.g., "MMLU")
        model: OpenAI embedding model to use
        batch_size: Number of examples to process in each batch
        limit: Optional limit on number of examples (for testing)

    Returns:
        Dictionary with generation statistics
    """
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)

    # Get Qdrant client
    qdrant = get_qdrant_client()

    # Get vector size for the model
    vector_size = 1536 if "3-small" in model else 3072  # 3-large has 3072 dimensions

    # Create collection name
    collection_name = f"{dataset_name.lower()}_embeddings"

    # Create Qdrant collection
    create_collection(qdrant, collection_name, vector_size)

    # Get database session
    db = SessionLocal()

    try:
        # Get dataset
        stmt = select(Dataset).where(Dataset.name == dataset_name)
        dataset = db.execute(stmt).scalar_one_or_none()

        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_name}")

        # Get examples
        query = db.query(Example).filter(Example.dataset_id == dataset.id)
        if limit:
            query = query.limit(limit)

        examples = query.all()
        total_examples = len(examples)

        print(f"Generating embeddings for {total_examples} examples...")
        print(f"Model: {model}")
        print(f"Batch size: {batch_size}")

        total_embeddings = 0
        total_tokens = 0
        start_time = time.time()

        # Process in batches
        for i in range(0, total_examples, batch_size):
            batch = examples[i : i + batch_size]
            batch_texts = [format_example_for_embedding(ex) for ex in batch]

            # Generate embeddings
            response = client.embeddings.create(input=batch_texts, model=model)

            # Prepare points for Qdrant
            points = []
            for j, (example, embedding_data) in enumerate(zip(batch, response.data)):
                point = PointStruct(
                    id=example.id,
                    vector=embedding_data.embedding,
                    payload={
                        "example_id": example.id,
                        "dataset_id": dataset.id,
                        "dataset_name": dataset_name,
                        "question": example.question[:500],  # Truncate for payload
                        "subject": example.example_metadata.get("subject")
                        if example.example_metadata
                        else None,
                        "split": example.example_metadata.get("split")
                        if example.example_metadata
                        else None,
                    },
                )
                points.append(point)

            # Upsert to Qdrant
            upsert_vectors(qdrant, collection_name, points)

            total_embeddings += len(batch)
            total_tokens += response.usage.total_tokens

            # Progress update
            if (i // batch_size + 1) % 10 == 0 or i + batch_size >= total_examples:
                elapsed = time.time() - start_time
                rate = total_embeddings / elapsed
                print(
                    f"Progress: {total_embeddings}/{total_examples} "
                    f"({total_embeddings / total_examples * 100:.1f}%) "
                    f"- {rate:.1f} examples/sec"
                )

            # Rate limiting: OpenAI has limits, sleep briefly between batches
            if i + batch_size < total_examples:
                time.sleep(0.1)

        elapsed_time = time.time() - start_time

        # Calculate cost
        # text-embedding-3-small: $0.020 per 1M tokens
        # text-embedding-3-large: $0.130 per 1M tokens
        cost_per_million = 0.020 if "3-small" in model else 0.130
        total_cost = (total_tokens / 1_000_000) * cost_per_million

        stats = {
            "dataset_name": dataset_name,
            "model": model,
            "collection_name": collection_name,
            "total_examples": total_examples,
            "total_embeddings": total_embeddings,
            "total_tokens": total_tokens,
            "elapsed_seconds": elapsed_time,
            "examples_per_second": total_embeddings / elapsed_time,
            "total_cost_usd": total_cost,
        }

        print("\n✓ Embedding generation complete!")
        print(f"  Total embeddings: {total_embeddings}")
        print(f"  Total tokens: {total_tokens:,}")
        print(f"  Elapsed time: {elapsed_time:.1f}s")
        print(f"  Rate: {stats['examples_per_second']:.1f} examples/sec")
        print(f"  Total cost: ${total_cost:.4f}")
        print(f"  Qdrant collection: {collection_name}")

        return stats

    finally:
        db.close()
