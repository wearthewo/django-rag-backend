import logging
import math

from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F
from django.db.models.functions import Greatest
from pgvector.django import CosineDistance

from .embeddings import embed_text
from .intent import infer_categories
from .models import Shop
from .serializers import ShopSerializer

logger = logging.getLogger(__name__)


def _is_open_now(shop):
    return shop.opening_hours.strip().lower() == "24/7"


def find_shops(question, area, filters):
    polygon = area["geometry"]
    centroid = polygon.centroid
    centroid.srid = 4326
    queryset = Shop.objects.filter(is_published=True, location__intersects=polygon)

    selected_categories = filters.get("categories", [])
    inferred_categories = infer_categories(question) if not selected_categories else []
    categories = selected_categories or inferred_categories
    if categories:
        queryset = queryset.filter(category__in=categories)

    max_distance = filters.get("max_distance_km")
    queryset = queryset.annotate(distance=Distance("location", centroid))
    if max_distance:
        queryset = queryset.filter(distance__lte=max_distance * 1000)

    queryset = queryset.annotate(
        lexical_similarity=Greatest(
            TrigramSimilarity("name", question),
            TrigramSimilarity("name_el", question),
            TrigramSimilarity("name_en", question),
        )
    )

    query_embedding = None
    try:
        query_embedding = embed_text(question)
    except Exception:
        logger.exception("Embedding failed; continuing with lexical search")

    if query_embedding:
        queryset = queryset.annotate(
            semantic_distance=CosineDistance("embedding", query_embedding)
        ).order_by(F("semantic_distance").asc(nulls_last=True), "-lexical_similarity", "distance")
    else:
        queryset = queryset.order_by("-lexical_similarity", "distance")

    candidates = list(queryset[:200])
    if filters.get("open_now"):
        candidates = [shop for shop in candidates if _is_open_now(shop)]

    default_radius = max(math.sqrt(area["area_km2"] / math.pi), 1.0)
    radius_km = max_distance or default_radius
    ranked = []
    for shop in candidates:
        distance_km = shop.distance.km
        semantic_distance = getattr(shop, "semantic_distance", None)
        semantic = 0.0 if semantic_distance is None else max(0.0, min(1.0, 1 - float(semantic_distance)))
        lexical = max(0.0, min(float(shop.lexical_similarity or 0), 1.0))
        proximity = max(0.0, 1 - distance_km / radius_km)
        score = 0.55 * semantic + 0.25 * lexical + 0.20 * proximity
        if not categories and semantic < 0.35 and lexical < 0.12:
            continue
        ranked.append((score, distance_km, semantic, lexical, shop))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    results = []
    for index, (score, distance_km, semantic, lexical, shop) in enumerate(ranked[:20], start=1):
        data = ShopSerializer(shop).data
        data.update({
            "reference": f"S{index}",
            "distance_km": round(distance_km, 2),
            "match_reason": _match_reason(semantic, lexical, distance_km, bool(categories)),
        })
        results.append(data)
    return results


def _match_reason(semantic, lexical, distance_km, category_match=False):
    if semantic >= 0.65:
        return f"Strong meaning match, {distance_km:.1f} km from the area centre"
    if lexical >= 0.35:
        return f"Text match, {distance_km:.1f} km from the area centre"
    if category_match:
        return f"Category match, {distance_km:.1f} km from the area centre"
    return f"Nearby option, {distance_km:.1f} km from the area centre"
