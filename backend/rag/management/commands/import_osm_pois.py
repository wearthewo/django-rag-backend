from pathlib import Path

import osmium
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from rag.categories import OSM_CATEGORY_MAP
from rag.models import Settlement, Shop


def category_for(tags):
    for pair, category in OSM_CATEGORY_MAP.items():
        if tags.get(pair[0]) == pair[1]:
            return category
    return None


def address_for(tags):
    street = " ".join(filter(None, (tags.get("addr:street"), tags.get("addr:housenumber"))))
    return ", ".join(filter(None, (street, tags.get("addr:city"), tags.get("addr:postcode"))))


class POIHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.shop_records = {}
        self.settlement_records = {}
        self.imported_at = timezone.now()

    def node(self, node):
        if not node.location.valid():
            return
        if not (node.tags.get("name") or node.tags.get("name:el") or node.tags.get("name:en")):
            return
        tags = dict(node.tags)
        self._collect("node", node.id, tags, node.location.lon, node.location.lat)

    def area(self, area):
        tags = dict(area.tags)
        if not category_for(tags):
            return
        coordinates = []
        try:
            for ring in area.outer_rings():
                coordinates.extend((node.lon, node.lat) for node in ring if node.location.valid())
                break
        except (osmium.InvalidLocationError, RuntimeError):
            return
        if not coordinates:
            return
        lon = sum(item[0] for item in coordinates) / len(coordinates)
        lat = sum(item[1] for item in coordinates) / len(coordinates)
        osm_type = "way" if area.from_way() else "relation"
        self._collect(osm_type, area.orig_id(), tags, lon, lat)

    def _collect(self, osm_type, osm_id, tags, lon, lat):
        name = tags.get("name") or tags.get("name:el") or tags.get("name:en")
        if not name:
            return
        category = category_for(tags)
        place_kind = tags.get("place")
        is_settlement = place_kind in {"city", "town", "village", "suburb"}
        if not category and not is_settlement:
            return

        point = Point(lon, lat, srid=4326)
        if category and name:
            slug = f"{slugify(name)[:230] or 'shop'}-{osm_type}-{osm_id}"
            self.shop_records[(osm_type, osm_id)] = Shop(
                osm_type=osm_type,
                osm_id=osm_id,
                slug=slug,
                name=name,
                name_el=tags.get("name:el", ""),
                name_en=tags.get("name:en", ""),
                category=category,
                address=address_for(tags),
                phone=tags.get("contact:phone") or tags.get("phone", ""),
                website=tags.get("contact:website") or tags.get("website", ""),
                opening_hours=tags.get("opening_hours", ""),
                location=point,
                source_updated_at=self.imported_at,
                is_published=True,
            )

        if is_settlement:
            self.settlement_records[(osm_type, osm_id)] = Settlement(
                osm_type=osm_type,
                osm_id=osm_id,
                name=name,
                name_el=tags.get("name:el", ""),
                name_en=tags.get("name:en", ""),
                kind=place_kind,
                location=point,
            )

    def flush(self, batch_size=1000):
        self._upsert(
            Shop,
            self.shop_records,
            (
                "slug",
                "name",
                "name_el",
                "name_en",
                "category",
                "address",
                "phone",
                "website",
                "opening_hours",
                "location",
                "source_updated_at",
                "is_published",
            ),
            batch_size,
        )
        self._upsert(
            Settlement,
            self.settlement_records,
            ("name", "name_el", "name_en", "kind", "location"),
            batch_size,
        )

    @staticmethod
    def _upsert(model, records, update_fields, batch_size):
        existing = {
            (osm_type, osm_id): pk
            for osm_type, osm_id, pk in model.objects.filter(osm_id__isnull=False).values_list(
                "osm_type", "osm_id", "pk"
            )
        }
        creates = []
        updates = []
        for key, instance in records.items():
            if key in existing:
                instance.pk = existing[key]
                updates.append(instance)
            else:
                creates.append(instance)
        model.objects.bulk_create(creates, batch_size=batch_size, ignore_conflicts=True)
        model.objects.bulk_update(updates, update_fields, batch_size=batch_size)


class NodePOIHandler(osmium.SimpleHandler):
    """Fast initial import that avoids pyosmium's expensive area assembly pass."""

    def __init__(self):
        super().__init__()
        self.collector = POIHandler()

    @property
    def shop_records(self):
        return self.collector.shop_records

    @property
    def settlement_records(self):
        return self.collector.settlement_records

    def node(self, node):
        if not node.location.valid():
            return
        if not (node.tags.get("name") or node.tags.get("name:el") or node.tags.get("name:en")):
            return
        self.collector._collect(
            "node", node.id, dict(node.tags), node.location.lon, node.location.lat
        )

    def flush(self):
        self.collector.flush()


class Command(BaseCommand):
    help = "Idempotently import supported shops and settlements from an OSM PBF."

    def add_arguments(self, parser):
        parser.add_argument("file")
        parser.add_argument(
            "--nodes-only",
            action="store_true",
            help="Import named POI and settlement nodes without the slower area pass.",
        )

    def handle(self, *args, **options):
        source = Path(options["file"])
        if not source.exists():
            raise CommandError(f"File not found: {source}")
        handler = NodePOIHandler() if options["nodes_only"] else POIHandler()
        osm_source = (
            osmium.io.File(str(source), "pbf")
            if source.name.endswith(".osm.pbf.part")
            else str(source)
        )
        if options["nodes_only"]:
            handler.apply_file(osm_source)
        else:
            handler.apply_file(osm_source, locations=True, idx="flex_mem")
        handler.flush()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported/updated {len(handler.shop_records)} shops and "
                f"{len(handler.settlement_records)} settlements"
            )
        )
