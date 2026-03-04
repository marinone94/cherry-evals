"""Search examples from the CLI."""

import json

import click

from core.search.keyword import keyword_search
from db.postgres.base import SessionLocal


@click.command()
@click.argument("query")
@click.option("--dataset", default=None, help="Filter by dataset name")
@click.option("--subject", default=None, help="Filter by subject")
@click.option("--limit", default=20, type=int, help="Maximum number of results to return")
@click.option(
    "--mode",
    default="keyword",
    type=click.Choice(["keyword", "hybrid", "intelligent"]),
    help="Search mode to use",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Output results as JSON (machine-parseable)",
)
def search(
    query: str,
    dataset: str | None,
    subject: str | None,
    limit: int,
    mode: str,
    json_output: bool,
) -> None:
    """Search evaluation examples.

    QUERY: The search query string.
    """
    db = SessionLocal()
    try:
        if mode == "keyword":
            results, total = keyword_search(
                db=db,
                query=query,
                dataset_name=dataset,
                subject=subject,
                limit=limit,
            )
        elif mode == "hybrid":
            try:
                from core.search.hybrid import hybrid_search

                results, total = hybrid_search(
                    db=db,
                    query=query,
                    dataset_name=dataset,
                    subject=subject,
                    limit=limit,
                )
            except Exception as e:
                if json_output:
                    click.echo(
                        json.dumps(
                            {
                                "status": "warning",
                                "message": f"Hybrid search failed, falling back to keyword: {e}",
                            }
                        ),
                        err=True,
                    )
                else:
                    click.echo(f"Hybrid search failed, falling back to keyword: {e}", err=True)
                results, total = keyword_search(
                    db=db,
                    query=query,
                    dataset_name=dataset,
                    subject=subject,
                    limit=limit,
                )
        else:
            # intelligent mode
            try:
                from core.search.intelligent import intelligent_search

                results, total, metadata = intelligent_search(
                    db=db,
                    query=query,
                    limit=limit,
                )
            except Exception as e:
                if json_output:
                    click.echo(
                        json.dumps(
                            {
                                "status": "warning",
                                "message": (
                                    f"Intelligent search failed, falling back to keyword: {e}"
                                ),
                            }
                        ),
                        err=True,
                    )
                else:
                    click.echo(f"Intelligent search failed, falling back to keyword: {e}", err=True)
                results, total = keyword_search(
                    db=db,
                    query=query,
                    dataset_name=dataset,
                    subject=subject,
                    limit=limit,
                )

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "query": query,
                        "mode": mode,
                        "total": total,
                        "results": results,
                    }
                )
            )
        else:
            click.echo(f"Search: {query!r}  mode={mode}  total={total}")
            click.echo("")
            for i, result in enumerate(results, 1):
                score_str = f"  score={result['score']:.4f}" if result.get("score") else ""
                click.echo(f"{i}. [{result['dataset_name']}] (id={result['id']}){score_str}")
                click.echo(f"   {result['question'][:120]}")
                click.echo("")

    except Exception as e:
        if json_output:
            click.echo(json.dumps({"status": "error", "message": f"Search failed: {e}"}))
            raise SystemExit(1)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    finally:
        db.close()
