import django.contrib.gis.db.models.fields
import django.contrib.postgres.operations
import pgvector.django.vector
from django.contrib.postgres.indexes import GinIndex
from django.db import migrations, models
from pgvector.django import HnswIndex, VectorExtension


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        django.contrib.postgres.operations.CreateExtension("postgis"),
        django.contrib.postgres.operations.CreateExtension("pg_trgm"),
        VectorExtension(),
        migrations.CreateModel(
            name="Settlement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("osm_type", models.CharField(max_length=16)),
                ("osm_id", models.BigIntegerField()),
                ("name", models.CharField(max_length=255)),
                ("name_el", models.CharField(blank=True, max_length=255)),
                ("name_en", models.CharField(blank=True, max_length=255)),
                ("kind", models.CharField(blank=True, max_length=40)),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("osm_type", "osm_id"), name="unique_osm_settlement"
                    )
                ]
            },
        ),
        migrations.CreateModel(
            name="Shop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("osm_type", models.CharField(blank=True, max_length=16)),
                ("osm_id", models.BigIntegerField(blank=True, null=True)),
                ("slug", models.SlugField(max_length=280, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("name_el", models.CharField(blank=True, max_length=255)),
                ("name_en", models.CharField(blank=True, max_length=255)),
                ("category", models.CharField(db_index=True, max_length=80)),
                ("address", models.TextField(blank=True)),
                ("phone", models.CharField(blank=True, max_length=80)),
                ("website", models.URLField(blank=True)),
                ("opening_hours", models.CharField(blank=True, max_length=255)),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326),
                ),
                (
                    "embedding",
                    pgvector.django.vector.VectorField(blank=True, dimensions=1024, null=True),
                ),
                ("source_updated_at", models.DateTimeField(blank=True, null=True)),
                ("is_published", models.BooleanField(db_index=True, default=True)),
                ("local_overrides", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["category", "is_published"], name="rag_shop_category_idx"),
                    GinIndex(fields=("name",), name="shop_name_trgm", opclasses=("gin_trgm_ops",)),
                    GinIndex(
                        fields=("name_el",), name="shop_name_el_trgm", opclasses=("gin_trgm_ops",)
                    ),
                    GinIndex(
                        fields=("name_en",), name="shop_name_en_trgm", opclasses=("gin_trgm_ops",)
                    ),
                    HnswIndex(
                        name="shop_embedding_hnsw",
                        fields=("embedding",),
                        m=16,
                        ef_construction=64,
                        opclasses=("vector_cosine_ops",),
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(osm_id__isnull=False),
                        fields=("osm_type", "osm_id"),
                        name="unique_osm_shop",
                    )
                ],
            },
        ),
    ]
