from django.urls import path

from .views import CategoryListView, HealthView, LocationListView, RecommendationView, ShopDetailView

urlpatterns = [
    path("recommendations", RecommendationView.as_view(), name="recommendations"),
    path("shops/<slug:slug>", ShopDetailView.as_view(), name="shop-detail"),
    path("categories", CategoryListView.as_view(), name="categories"),
    path("locations", LocationListView.as_view(), name="locations"),
    path("health", HealthView.as_view(), name="health"),
]
