"""Unit tests for database models."""

from sqlalchemy import inspect

from db.postgres.models import Collection, CollectionExample, Dataset, Example


def test_dataset_model_fields():
    """Test that Dataset model has correct fields."""
    mapper = inspect(Dataset)

    assert "id" in mapper.columns
    assert "name" in mapper.columns
    assert "source" in mapper.columns
    assert "license" in mapper.columns
    assert "task_type" in mapper.columns
    assert "description" in mapper.columns
    assert "stats" in mapper.columns
    assert "created_at" in mapper.columns
    assert "updated_at" in mapper.columns


def test_dataset_relationships():
    """Test that Dataset has correct relationships."""
    mapper = inspect(Dataset)
    relationships = mapper.relationships

    assert "examples" in relationships
    assert relationships["examples"].direction.name == "ONETOMANY"


def test_example_model_fields():
    """Test that Example model has correct fields."""
    mapper = inspect(Example)

    assert "id" in mapper.columns
    assert "dataset_id" in mapper.columns
    assert "question" in mapper.columns
    assert "answer" in mapper.columns
    assert "choices" in mapper.columns
    assert "example_metadata" in mapper.columns
    assert "created_at" in mapper.columns


def test_example_relationships():
    """Test that Example has correct relationships."""
    mapper = inspect(Example)
    relationships = mapper.relationships

    assert "dataset" in relationships
    assert "collection_examples" in relationships
    assert relationships["dataset"].direction.name == "MANYTOONE"
    assert relationships["collection_examples"].direction.name == "ONETOMANY"


def test_collection_model_fields():
    """Test that Collection model has correct fields."""
    mapper = inspect(Collection)

    assert "id" in mapper.columns
    assert "name" in mapper.columns
    assert "description" in mapper.columns
    assert "user_id" in mapper.columns
    assert "created_at" in mapper.columns
    assert "updated_at" in mapper.columns


def test_collection_relationships():
    """Test that Collection has correct relationships."""
    mapper = inspect(Collection)
    relationships = mapper.relationships

    assert "collection_examples" in relationships
    assert relationships["collection_examples"].direction.name == "ONETOMANY"


def test_collection_example_model_fields():
    """Test that CollectionExample model has correct fields."""
    mapper = inspect(CollectionExample)

    assert "id" in mapper.columns
    assert "collection_id" in mapper.columns
    assert "example_id" in mapper.columns
    assert "added_at" in mapper.columns


def test_collection_example_relationships():
    """Test that CollectionExample has correct relationships."""
    mapper = inspect(CollectionExample)
    relationships = mapper.relationships

    assert "collection" in relationships
    assert "example" in relationships
    assert relationships["collection"].direction.name == "MANYTOONE"
    assert relationships["example"].direction.name == "MANYTOONE"


def test_dataset_table_name():
    """Test that Dataset has correct table name."""
    assert Dataset.__tablename__ == "datasets"


def test_example_table_name():
    """Test that Example has correct table name."""
    assert Example.__tablename__ == "examples"


def test_collection_table_name():
    """Test that Collection has correct table name."""
    assert Collection.__tablename__ == "collections"


def test_collection_example_table_name():
    """Test that CollectionExample has correct table name."""
    assert CollectionExample.__tablename__ == "collection_examples"
