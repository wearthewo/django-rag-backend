from .retriever import retrieve_shops
from .tools import haversine

def shortest_shop_agent(user_lat, user_lon, query, category=None, geo_cutoff_km=5):
    """
    Find the best shop based on semantic similarity and geographic proximity.

    Args:
        user_lat (float): User latitude
        user_lon (float): User longitude
        query (str): Text query describing the shop
        category (str, optional): Filter by category
        geo_cutoff_km (float, optional): Maximum distance to consider

    Returns:
        dict: Best shop info with name and distance, or None if no shop within cutoff
    """
    # Step 1: Retrieve shops based on semantic similarity and optional category
    shops = retrieve_shops(query, user_lat, user_lon, category)

    best_shop = None
    best_score = float("inf")

    # Step 2: Evaluate each shop with combined score
    for shop in shops:
        distance = haversine(user_lat, user_lon, shop.latitude, shop.longitude)

        # Skip shops outside the geographic cutoff
        if distance > geo_cutoff_km:
            continue

        # Combined score: semantic similarity + geo distance normalized (e.g., divide by 10)
        score = shop.semantic_distance + (distance / 10)

        if score < best_score:
            best_score = score
            best_shop = shop

    if not best_shop:
        return None  # No shop within cutoff

    return {
        "shop": best_shop.name,
        "category": best_shop.category,
        "distance_km": round(haversine(user_lat, user_lon, best_shop.latitude, best_shop.longitude), 2),
        "semantic_score": round(best_shop.semantic_distance, 3),
        "combined_score": round(best_score, 3)
    }
