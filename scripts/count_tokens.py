"""Count tokens for MMLU dataset examples using tiktoken."""

import tiktoken
from sqlalchemy import select

from db.postgres.base import SessionLocal
from db.postgres.models import Dataset, Example


def format_example_for_embedding(example: Example) -> str:
    """Format an example as it would be embedded.

    Typically we'd embed the question + choices together.
    """
    text = example.question
    if example.choices:
        # Add choices to the text
        choices_text = " ".join(example.choices)
        text = f"{text} {choices_text}"
    return text


def count_tokens():
    """Count total tokens for all MMLU examples."""
    # Initialize tokenizer (cl100k_base is used for text-embedding models)
    encoding = tiktoken.get_encoding("cl100k_base")

    db = SessionLocal()

    try:
        # Get MMLU dataset
        stmt = select(Dataset).where(Dataset.name == "MMLU")
        dataset = db.execute(stmt).scalar_one_or_none()

        if not dataset:
            print("MMLU dataset not found")
            return

        # Get all examples
        examples = db.query(Example).filter(Example.dataset_id == dataset.id).all()

        print(f"Counting tokens for {len(examples)} examples...")

        total_tokens = 0
        min_tokens = float("inf")
        max_tokens = 0
        token_counts = []

        for example in examples:
            text = format_example_for_embedding(example)
            tokens = encoding.encode(text)
            num_tokens = len(tokens)

            total_tokens += num_tokens
            min_tokens = min(min_tokens, num_tokens)
            max_tokens = max(max_tokens, num_tokens)
            token_counts.append(num_tokens)

        avg_tokens = total_tokens / len(examples)

        # Calculate costs
        # Pricing as of 2024:
        # text-embedding-3-small: $0.020 per 1M tokens
        # text-embedding-3-large: $0.130 per 1M tokens

        cost_small = (total_tokens / 1_000_000) * 0.020
        cost_large = (total_tokens / 1_000_000) * 0.130

        print("\n=== Token Count Statistics ===")
        print(f"Total examples: {len(examples):,}")
        print(f"Total tokens: {total_tokens:,}")
        print(f"Average tokens per example: {avg_tokens:.1f}")
        print(f"Min tokens: {min_tokens}")
        print(f"Max tokens: {max_tokens}")

        print("\n=== Cost Estimates ===")
        print("text-embedding-3-small ($0.020 per 1M tokens):")
        print(f"  Total cost: ${cost_small:.4f}")
        print(f"  Cost per example: ${cost_small / len(examples):.6f}")

        print("\ntext-embedding-3-large ($0.130 per 1M tokens):")
        print(f"  Total cost: ${cost_large:.4f}")
        print(f"  Cost per example: ${cost_large / len(examples):.6f}")

        # Show distribution
        print("\n=== Token Distribution ===")
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        token_counts.sort()
        for p in percentiles:
            idx = int(len(token_counts) * p / 100)
            print(f"P{p}: {token_counts[idx]} tokens")

    finally:
        db.close()


if __name__ == "__main__":
    count_tokens()
