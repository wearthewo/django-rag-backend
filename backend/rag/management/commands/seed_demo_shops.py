from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from rag.models import Settlement, Shop


DEMO_SHOPS = (
    ("Athens Coffee Lab", "Καφέ Αθήνας", "Athens Café", "cafe", 23.7275, 37.9838, "24/7"),
    ("Plaka Books", "Βιβλία Πλάκας", "Plaka Books", "books", 23.7308, 37.9722, "Mo-Sa 09:00-20:00"),
    ("Syntagma Pharmacy", "Φαρμακείο Συντάγματος", "Syntagma Pharmacy", "pharmacy", 23.7348, 37.9755, "24/7"),
)


class Command(BaseCommand):
    help = "Create a tiny Athens dataset for local UI development."

    def handle(self, *args, **options):
        for index, (name, name_el, name_en, category, lon, lat, hours) in enumerate(DEMO_SHOPS, 1):
            Shop.objects.update_or_create(
                osm_type="demo", osm_id=index,
                defaults={
                    "slug": f"{category}-athens-{index}",
                    "name": name,
                    "name_el": name_el,
                    "name_en": name_en,
                    "category": category,
                    "address": "Athens, Greece",
                    "opening_hours": hours,
                    "location": Point(lon, lat, srid=4326),
                },
            )
        Settlement.objects.update_or_create(
            osm_type="demo", osm_id=1,
            defaults={
                "name": "Athens", "name_el": "Αθήνα", "name_en": "Athens", "kind": "city",
                "location": Point(23.7275, 37.9838, srid=4326),
            },
        )
        self.stdout.write(self.style.SUCCESS("Demo shops are ready"))
