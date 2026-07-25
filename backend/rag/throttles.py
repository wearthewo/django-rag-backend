from django.core.cache.backends.locmem import LocMemCache
from rest_framework.throttling import AnonRateThrottle

_throttle_cache = LocMemCache("api-throttles", {"TIMEOUT": 3600})


class RecommendationRateThrottle(AnonRateThrottle):
    cache = _throttle_cache
    scope = "recommendations"
