"""CLI commands for agentic dataset discovery and ingestion."""

import json

import click


@click.command()
@click.argument("description")
@click.option("--hf-id", default=None, help="Direct HuggingFace dataset ID (skips discovery).")
@click.option("--hf-config", default=None, help="HuggingFace config/subset name.")
@click.option("--max-examples", default=None, type=int, help="Limit examples to ingest.")
@click.option("--discover-only", is_flag=True, help="Only discover, don't ingest.")
@click.option("--json-output", "--json", "json_flag", is_flag=True, help="JSON output.")
def discover(description, hf_id, hf_config, max_examples, discover_only, json_flag):
    """Discover and ingest arbitrary HuggingFace datasets using LLM.

    DESCRIPTION is a natural language query or a HuggingFace dataset ID.

    Examples:

        cherry-evals discover "medical question answering"

        cherry-evals discover "allenai/sciq" --max-examples 100

        cherry-evals discover "commonsense reasoning" --discover-only --json
    """
    from agents.ingestion_agent import IngestionAgent

    agent = IngestionAgent(max_examples=max_examples)

    if discover_only:
        result = agent.discover_dataset(description)
        if not result:
            if json_flag:
                click.echo(json.dumps({"error": "No matching dataset found."}))
            else:
                click.echo("No matching dataset found.")
            return

        if json_flag:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Dataset: {result.get('name', 'unknown')}")
            click.echo(f"  HuggingFace ID: {result.get('hf_dataset_id')}")
            click.echo(f"  Task type: {result.get('task_type')}")
            click.echo(f"  License: {result.get('license')}")
            click.echo(f"  Description: {result.get('description')}")
            click.echo(f"  Rationale: {result.get('rationale')}")
        return

    # Full ingestion
    click.echo(f"Starting agentic ingestion for: {description}")
    result = agent.ingest(
        description=description,
        hf_dataset_id=hf_id,
        hf_config=hf_config,
    )

    if json_flag:
        output = {
            "success": result.success,
            "dataset_name": result.dataset_name,
            "total_examples": result.total_examples,
            "splits": result.splits,
            "errors": result.errors,
        }
        if result.plan:
            output["explanation"] = result.plan.explanation
        click.echo(json.dumps(output, indent=2))
    else:
        if result.success:
            click.echo(f"Ingested {result.total_examples} examples from {result.dataset_name}")
            for split, count in result.splits.items():
                click.echo(f"  {split}: {count}")
            if result.plan:
                click.echo(f"  Parse logic: {result.plan.explanation}")
        else:
            click.echo(f"Ingestion failed for {result.dataset_name}")
            for err in result.errors:
                click.echo(f"  Error: {err}")
