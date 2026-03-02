"""Export collection examples to Langfuse as a dataset."""

from langfuse import Langfuse

from cherry_evals.config import settings


class LangfuseExportError(Exception):
    """Raised when Langfuse export fails."""


def export_to_langfuse(
    examples,
    dataset_name: str,
    dataset_description: str | None = None,
    dataset_names: dict[int, str] | None = None,
) -> dict:
    """Export examples as a Langfuse dataset.

    Creates a dataset in Langfuse and adds each example as a dataset item.
    Returns a summary dict with dataset name and item count.
    """
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        raise LangfuseExportError(
            "Langfuse credentials not configured. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env"
        )

    dataset_names = dataset_names or {}

    client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_base_url,
    )

    try:
        client.create_dataset(
            name=dataset_name,
            description=dataset_description or "Exported from Cherry Evals collection",
        )

        count = 0
        for ex in examples:
            input_data = {"question": ex.question}
            if ex.choices:
                input_data["choices"] = ex.choices

            expected = {"answer": ex.answer} if ex.answer else None

            metadata = dict(ex.example_metadata) if ex.example_metadata else {}
            metadata["cherry_evals_id"] = ex.id
            metadata["dataset_id"] = ex.dataset_id
            ds_name = dataset_names.get(ex.dataset_id)
            if ds_name:
                metadata["dataset_name"] = ds_name

            client.create_dataset_item(
                dataset_name=dataset_name,
                input=input_data,
                expected_output=expected,
                metadata=metadata,
            )
            count += 1

        client.flush()
        return {"dataset_name": dataset_name, "items_exported": count}

    except LangfuseExportError:
        raise
    except Exception as e:
        raise LangfuseExportError(f"Langfuse export failed: {e}") from e
