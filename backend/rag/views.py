from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from .serializers import ShopSerializer
from .retriever import retrieve_shops 

class ShopSearchView(APIView): 
    permission_classes = [IsAuthenticated]

    @ratelimit(key='user', rate = '20/m', block=True) 
    def get(self, request): 
        query = request.query_params.get('query', '') 
        user_lat = float(request.query_params.get('lat', '0')) 
        user_lon = float(request.query_params.get('lon', '0')) 
        category = request.query_params.get('category', None) 

        cache_key = f"shop_search:{query}:{user_lat}:{user_lon}:{category}" 
        cached_result = cache.get(cache_key) 
        if cached_result: 
            return Response(cached_result) 

        shops = retrieve_shops(query, user_lat, user_lon, category) 
        serializer = ShopSerializer(shops, many=True) 
        result = serializer.data 

        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes 

        return Response(result)

