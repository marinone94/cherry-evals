"""CLI entry point for Cherry Evals."""

import click

from cherry_evals.cli.collections import collections
from cherry_evals.cli.discover import discover
from cherry_evals.cli.embed import embed
from cherry_evals.cli.ingest import ingest
from cherry_evals.cli.search import search


@click.group()
def cli():
    """Cherry Evals CLI."""
    pass


cli.add_command(ingest)
cli.add_command(embed)
cli.add_command(search)
cli.add_command(collections)
cli.add_command(discover)

if __name__ == "__main__":
    cli()
