"""Estimate time for local embedding generation with embeddinggemma-300m."""

from sqlalchemy import func

from db.postgres.base import SessionLocal
from db.postgres.models import Dataset, Example


def estimate_embedding_time():
    """Estimate time to generate embeddings locally with embeddinggemma-300m."""
    db = SessionLocal()

    try:
        # Get MMLU dataset stats
        dataset = db.query(Dataset).filter(Dataset.name == "MMLU").first()
        if not dataset:
            print("MMLU dataset not found")
            return

        total_examples = (
            db.query(func.count(Example.id)).filter(Example.dataset_id == dataset.id).scalar()
        )

        print("=== Local Embedding Generation Time Estimates ===")
        print("Model: embeddinggemma-300m (Google's 300M parameter embedding model)")
        print(f"Total examples: {total_examples:,}")
        print("Average tokens per example: ~100")

        print("\n=== Hardware Scenarios ===")

        # CPU scenarios
        print("\n1. CPU (Consumer grade, e.g., AMD Ryzen 9 / Intel i9):")
        print("   Without batching:")
        cpu_single_throughput = 8  # examples per second
        cpu_single_time = total_examples / cpu_single_throughput
        print(f"     ~{cpu_single_throughput} examples/sec")
        print(f"     Total time: ~{cpu_single_time / 60:.1f} minutes ({cpu_single_time:.0f}s)")

        print("   With batching (batch_size=16):")
        cpu_batch_throughput = 20  # examples per second with batching
        cpu_batch_time = total_examples / cpu_batch_throughput
        print(f"     ~{cpu_batch_throughput} examples/sec")
        print(f"     Total time: ~{cpu_batch_time / 60:.1f} minutes ({cpu_batch_time:.0f}s)")

        # GPU scenarios
        print("\n2. GPU (Consumer grade, e.g., RTX 3080/3090, RTX 4070/4080):")
        print("   Without batching:")
        gpu_single_throughput = 50  # examples per second
        gpu_single_time = total_examples / gpu_single_throughput
        print(f"     ~{gpu_single_throughput} examples/sec")
        print(f"     Total time: ~{gpu_single_time / 60:.1f} minutes ({gpu_single_time:.0f}s)")

        print("   With batching (batch_size=32):")
        gpu_batch_throughput = 150  # examples per second with batching
        gpu_batch_time = total_examples / gpu_batch_throughput
        print(f"     ~{gpu_batch_throughput} examples/sec")
        print(f"     Total time: ~{gpu_batch_time / 60:.1f} minutes ({gpu_batch_time:.0f}s)")

        print("   With aggressive batching (batch_size=64):")
        gpu_aggressive_throughput = 250  # examples per second
        gpu_aggressive_time = total_examples / gpu_aggressive_throughput
        print(f"     ~{gpu_aggressive_throughput} examples/sec")
        print(
            f"     Total time: ~{gpu_aggressive_time / 60:.1f} minutes ({gpu_aggressive_time:.0f}s)"
        )

        print("\n3. High-end GPU (e.g., RTX 4090, A100):")
        print("   With aggressive batching (batch_size=128):")
        highend_throughput = 500  # examples per second
        highend_time = total_examples / highend_throughput
        print(f"     ~{highend_throughput} examples/sec")
        print(f"     Total time: ~{highend_time / 60:.1f} minutes ({highend_time:.0f}s)")

        print("\n=== Summary ===")
        print(f"Best case (high-end GPU): ~{highend_time / 60:.1f} minutes")
        print(f"Typical case (consumer GPU with batching): ~{gpu_batch_time / 60:.1f} minutes")
        print(f"Worst case (CPU without batching): ~{cpu_single_time / 60:.1f} minutes")

        print("\n=== Comparison with OpenAI API ===")
        print("OpenAI text-embedding-3-small:")
        print("  - Cost: $0.03")
        print("  - Time: ~2-5 minutes (with parallelization)")
        print("  - No local setup required")
        print("\nLocal embeddinggemma-300m:")
        print("  - Cost: $0.00 (after initial setup)")
        print("  - Time: 1-30 minutes depending on hardware")
        print("  - Requires local setup and potentially GPU")
        print("  - Reusable for future datasets at no cost")

        print("\n=== Recommendations ===")
        print("1. For MVP-0 (one-time): Use OpenAI API (faster, simpler, negligible cost)")
        print("2. For production (many datasets): Consider local if you have GPU available")
        print("3. Hybrid approach: Use API for prototyping, switch to local for scale")

    finally:
        db.close()


if __name__ == "__main__":
    estimate_embedding_time()
