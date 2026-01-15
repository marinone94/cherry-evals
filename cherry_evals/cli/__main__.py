"""CLI entry point for Cherry Evals."""

import click

from cherry_evals.cli.ingest import ingest


@click.group()
def cli():
    """Cherry Evals CLI."""
    pass


cli.add_command(ingest)

if __name__ == "__main__":
    cli()
