from django.core.management.base import BaseCommand

from rag.embeddings import embed_text
from rag.models import Shop


class Command(BaseCommand):
    help = "Generate local multilingual embeddings for shops."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        queryset = Shop.objects.all()
        if not options["force"]:
            queryset = queryset.filter(embedding__isnull=True)
        updated = 0
        for shop in queryset.iterator(chunk_size=100):
            text = " ".join(filter(None, (
                shop.name, shop.name_el, shop.name_en, shop.category, shop.address
            )))
            shop.embedding = embed_text(text)
            shop.save(update_fields=("embedding",))
            updated += 1
            if updated % 100 == 0:
                self.stdout.write(f"Embedded {updated} shops")
        self.stdout.write(self.style.SUCCESS(f"Embedded {updated} shops"))
