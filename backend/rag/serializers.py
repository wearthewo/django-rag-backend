import json

from django.conf import settings
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from rest_framework import serializers

from .models import Settlement, Shop

GREECE_BOUNDS = (19.0, 34.0, 30.0, 42.2)


class SearchFiltersSerializer(serializers.Serializer):
    categories = serializers.ListField(
        child=serializers.CharField(max_length=80), required=False, default=list
    )
    open_now = serializers.BooleanField(required=False, default=False)
    max_distance_km = serializers.FloatField(required=False, min_value=0.1, max_value=100)


class RecommendationRequestSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=2, max_length=500)
    language = serializers.ChoiceField(choices=("el", "en"), default="el")
    area = serializers.JSONField()
    filters = SearchFiltersSerializer(required=False, default=dict)

    def validate_area(self, value):
        try:
            geometry = GEOSGeometry(json.dumps(value), srid=4326)
        except (GDALException, GEOSException, TypeError, ValueError) as exc:
            raise serializers.ValidationError("Area must be valid GeoJSON.") from exc
        if geometry.geom_type != "Polygon":
            raise serializers.ValidationError("Area must be a GeoJSON Polygon.")
        if geometry.empty or not geometry.valid:
            raise serializers.ValidationError("Area must be a valid, non-self-intersecting polygon.")
        min_x, min_y, max_x, max_y = geometry.extent
        gr_min_x, gr_min_y, gr_max_x, gr_max_y = GREECE_BOUNDS
        if min_x < gr_min_x or min_y < gr_min_y or max_x > gr_max_x or max_y > gr_max_y:
            raise serializers.ValidationError("Area must be within Greece.")
        projected = geometry.clone()
        projected.transform(3035)
        area_km2 = projected.area / 1_000_000
        if area_km2 <= 0 or area_km2 > settings.MAX_SEARCH_AREA_KM2:
            raise serializers.ValidationError(
                f"Area must be no larger than {settings.MAX_SEARCH_AREA_KM2:g} km²."
            )
        return {"geojson": value, "geometry": geometry, "area_km2": area_km2}


class ShopSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    name_el = serializers.CharField(source="display_name_el", read_only=True)
    name_en = serializers.CharField(source="display_name_en", read_only=True)

    class Meta:
        model = Shop
        fields = (
            "id", "slug", "name", "name_el", "name_en", "category", "address",
            "phone", "website", "opening_hours", "latitude", "longitude",
        )

    def get_latitude(self, obj):
        return obj.location.y

    def get_longitude(self, obj):
        return obj.location.x


class SettlementSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Settlement
        fields = ("id", "name", "name_el", "name_en", "kind", "latitude", "longitude")

    def get_latitude(self, obj):
        return obj.location.y

    def get_longitude(self, obj):
        return obj.location.x
