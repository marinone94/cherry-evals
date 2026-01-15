"""Generate embeddings for datasets."""

import click

from cherry_evals.embeddings.openai_embeddings import generate_embeddings_for_dataset


@click.command()
@click.argument("dataset", type=str)
@click.option(
    "--model",
    default="text-embedding-3-small",
    type=click.Choice(["text-embedding-3-small", "text-embedding-3-large"], case_sensitive=False),
    help="OpenAI embedding model to use",
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
def embed(dataset: str, model: str, batch_size: int, limit: int | None):
    """Generate embeddings for a dataset.

    DATASET: Name of the dataset to generate embeddings for (e.g., MMLU)
    """
    click.echo(f"Starting embedding generation for {dataset}")
    click.echo(f"Model: {model}")
    click.echo(f"Batch size: {batch_size}")
    if limit:
        click.echo(f"Limit: {limit} examples")

    try:
        stats = generate_embeddings_for_dataset(
            dataset_name=dataset, model=model, batch_size=batch_size, limit=limit
        )
        click.echo(f"\n✓ Embedding generation complete: {stats}")
    except Exception as e:
        click.echo(f"\n✗ Error generating embeddings: {e}", err=True)
        raise click.Abort()
