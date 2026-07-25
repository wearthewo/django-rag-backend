from celery import shared_task

from .embeddings import embed_text
from .models import Shop


@shared_task(rate_limit="30/m")
def embed_shop(shop_id):
    shop = Shop.objects.get(pk=shop_id)
    text = " ".join(filter(None, (shop.name, shop.name_el, shop.name_en, shop.category, shop.address)))
    shop.embedding = embed_text(text)
    shop.save(update_fields=("embedding",))
