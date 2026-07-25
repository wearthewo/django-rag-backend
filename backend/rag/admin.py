from django.contrib import admin

from .models import Settlement, Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "osm_type", "osm_id", "is_published")
    list_filter = ("category", "is_published")
    search_fields = ("name", "name_el", "name_en", "address")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "osm_type", "osm_id")
    search_fields = ("name", "name_el", "name_en")
