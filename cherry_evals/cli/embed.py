"""Generate embeddings for datasets."""

import io
import json
import sys

import click

from cherry_evals.embeddings.generate import generate_embeddings_for_dataset


@click.command()
@click.argument("dataset", type=str)
@click.option(
    "--model",
    default="gemini-embedding-001",
    type=click.Choice(["gemini-embedding-001"], case_sensitive=False),
    help="Embedding model to use",
)
@click.option(
    "--batch-size",
    default=100,
    help="Batch size for API calls",
    type=int,
)
@click.option(
    "--limit",
    default=None,
    help="Limit number of examples to embed (for testing)",
    type=int,
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Output result as JSON (machine-parseable)",
)
def embed(dataset: str, model: str, batch_size: int, limit: int | None, json_output: bool):
    """Generate embeddings for a dataset.

    DATASET: Name of the dataset to generate embeddings for (e.g., MMLU)
    """
    if json_output:
        _null = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = _null
        try:
            stats = generate_embeddings_for_dataset(
                dataset_name=dataset, model=model, batch_size=batch_size, limit=limit
            )
        except Exception as e:
            sys.stdout = old_stdout
            click.echo(
                json.dumps({"status": "error", "message": f"Failed to generate embeddings: {e}"})
            )
            raise SystemExit(1)
        finally:
            sys.stdout = old_stdout
        click.echo(
            json.dumps(
                {
                    "status": "success",
                    "dataset_name": stats["dataset_name"],
                    "model": stats["model"],
                    "total_embeddings": stats["total_embeddings"],
                    "elapsed_seconds": stats["elapsed_seconds"],
                }
            )
        )
    else:
        click.echo(f"Starting embedding generation for {dataset}")
        click.echo(f"Model: {model}")
        click.echo(f"Batch size: {batch_size}")
        if limit:
            click.echo(f"Limit: {limit} examples")

        try:
            stats = generate_embeddings_for_dataset(
                dataset_name=dataset, model=model, batch_size=batch_size, limit=limit
            )
            click.echo(f"\nDone: {stats['total_embeddings']} embeddings generated")
        except Exception as e:
            click.echo(f"\nError generating embeddings: {e}", err=True)
            raise click.Abort()
