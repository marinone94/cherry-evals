"""Verify embeddings in Qdrant."""

from db.qdrant.client import get_qdrant_client


def verify_embeddings(collection_name: str = "mmlu_embeddings"):
    """Verify embeddings are properly stored in Qdrant."""
    client = get_qdrant_client()

    # Check if collection exists
    if not client.collection_exists(collection_name):
        print(f"✗ Collection '{collection_name}' does not exist")
        return

    # Get collection info
    collection_info = client.get_collection(collection_name)
    print(f"✓ Collection: {collection_name}")
    print(f"  Vectors count: {collection_info.points_count:,}")
    print(f"  Vector size: {collection_info.config.params.vectors.size}")
    print(f"  Distance: {collection_info.config.params.vectors.distance}")

    # Get a sample point
    print("\n=== Sample Point ===")
    results = client.scroll(
        collection_name=collection_name, limit=1, with_payload=True, with_vectors=False
    )

    if results[0]:
        point = results[0][0]
        print(f"Point ID: {point.id}")
        print(f"Payload: {point.payload}")
    else:
        print("No points found")

    # Test a simple search
    print("\n=== Test Search ===")
    # Search for a point using its own vector
    if results[0]:
        sample_id = results[0][0].id
        # Get the vector for this point
        sample_point = client.retrieve(
            collection_name=collection_name, ids=[sample_id], with_vectors=True
        )
        if sample_point:
            sample_vector = sample_point[0].vector
            # Search for similar vectors
            search_results = client.query_points(
                collection_name=collection_name, query=sample_vector, limit=3
            ).points
            print(f"Found {len(search_results)} similar vectors:")
            for i, result in enumerate(search_results, 1):
                print(f"  {i}. ID: {result.id}, Score: {result.score:.4f}")
                print(f"     Question: {result.payload.get('question', 'N/A')[:100]}...")
                print(f"     Subject: {result.payload.get('subject', 'N/A')}")


if __name__ == "__main__":
    verify_embeddings()
