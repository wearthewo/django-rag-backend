from .models import Shop
from pgvector.django import CosineDistance
from .embeddings import embed_text
from .tools import haversine

def retrieve_shops(query, user_lat, user_lon, category=None, geo_cutoff_km=5, top_k=20):
    """
    Retrieve shops based on semantic similarity and optional category/geographic cutoff.

    Args:
        query (str): Text query for semantic search
        user_lat (float): User latitude
        user_lon (float): User longitude
        category (str, optional): Filter shops by category
        geo_cutoff_km (float, optional): Maximum distance to consider
        top_k (int, optional): Number of top results to consider for scoring

    Returns:
        list: List of Shop objects sorted by combined score
    """
    query_embedding = embed_text(query)

    # Step 1: Pre-filter by category if given
    qs = Shop.objects.all()
    if category:
        qs = qs.filter(category=category)

    # Step 2: Annotate with semantic distance
    qs = qs.annotate(semantic_distance=CosineDistance("embedding", query_embedding))

    # Step 3: Compute geographic distance and combined score
    results = []
    for shop in qs[:top_k]:  # Limit to top_k shops for efficiency
        geo_distance = haversine(user_lat, user_lon, shop.latitude, shop.longitude)

        # Skip shops outside the geographic cutoff
        if geo_distance > geo_cutoff_km:
            continue

        # Combined score = semantic similarity + normalized geo distance
        score = shop.semantic_distance + (geo_distance / 10)
        results.append((score, shop))

    # Step 4: Sort by combined score and return top 5
    results.sort(key=lambda x: x[0])
    return [shop for _, shop in results[:5]]
