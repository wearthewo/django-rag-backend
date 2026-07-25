from django.contrib.gis.db import models
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import HnswIndex, VectorField


class Shop(models.Model):
    osm_type = models.CharField(max_length=16, blank=True)
    osm_id = models.BigIntegerField(null=True, blank=True)
    slug = models.SlugField(max_length=280, unique=True)
    name = models.CharField(max_length=255)
    name_el = models.CharField(max_length=255, blank=True)
    name_en = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=80, db_index=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=80, blank=True)
    website = models.URLField(blank=True)
    opening_hours = models.CharField(max_length=255, blank=True)
    location = models.PointField(geography=True, srid=4326, spatial_index=True)
    embedding = VectorField(dimensions=1024, null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    local_overrides = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("osm_type", "osm_id"),
                condition=models.Q(osm_id__isnull=False),
                name="unique_osm_shop",
            )
        ]
        indexes = [
            models.Index(fields=("category", "is_published"), name="rag_shop_category_idx"),
            GinIndex(fields=("name",), name="shop_name_trgm", opclasses=("gin_trgm_ops",)),
            GinIndex(fields=("name_el",), name="shop_name_el_trgm", opclasses=("gin_trgm_ops",)),
            GinIndex(fields=("name_en",), name="shop_name_en_trgm", opclasses=("gin_trgm_ops",)),
            HnswIndex(
                name="shop_embedding_hnsw",
                fields=("embedding",),
                m=16,
                ef_construction=64,
                opclasses=("vector_cosine_ops",),
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def display_name_el(self):
        return self.local_overrides.get("name_el") or self.name_el or self.name

    @property
    def display_name_en(self):
        return self.local_overrides.get("name_en") or self.name_en or self.name


class Settlement(models.Model):
    osm_type = models.CharField(max_length=16)
    osm_id = models.BigIntegerField()
    name = models.CharField(max_length=255)
    name_el = models.CharField(max_length=255, blank=True)
    name_en = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=40, blank=True)
    location = models.PointField(geography=True, srid=4326, spatial_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("osm_type", "osm_id"), name="unique_osm_settlement")
        ]

    def __str__(self):
        return self.name
