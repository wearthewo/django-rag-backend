import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import SimpleTestCase, override_settings
from requests import RequestException
from rest_framework.test import APIClient

from .intent import infer_categories, normalize_search_text
from .ollama import deterministic_answer, generate_answer
from .serializers import RecommendationRequestSerializer, ShopSerializer

ATHENS_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [[23.70, 37.95], [23.77, 37.95], [23.77, 38.01], [23.70, 38.01], [23.70, 37.95]]
    ],
}


class CategoryIntentTests(SimpleTestCase):
    def test_infers_greek_and_english_shop_categories(self):
        self.assertEqual(infer_categories("Θέλω ένα ήσυχο καφέ με Wi-Fi"), ["cafe"])
        self.assertEqual(infer_categories("Where is the nearest pharmacy?"), ["pharmacy"])

    def test_supports_multiple_explicit_intents(self):
        self.assertEqual(infer_categories("cafe or bookstore"), ["cafe", "books"])

    def test_does_not_force_a_category_for_an_ambiguous_question(self):
        self.assertEqual(infer_categories("What is nearby?"), [])

    def test_normalization_removes_greek_accents(self):
        self.assertEqual(normalize_search_text("ΦΑΡΜΑΚΕΊΟ"), "φαρμακειο")


class RecommendationValidationTests(SimpleTestCase):
    def payload(self, area=None):
        return {"question": "quiet cafe", "language": "en", "area": area or ATHENS_POLYGON}

    def test_accepts_valid_polygon(self):
        serializer = RecommendationRequestSerializer(data=self.payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertGreater(serializer.validated_data["area"]["area_km2"], 0)

    def test_rejects_self_intersecting_polygon(self):
        area = {
            "type": "Polygon",
            "coordinates": [
                [[23.70, 37.95], [23.77, 38.01], [23.77, 37.95], [23.70, 38.01], [23.70, 37.95]]
            ],
        }
        serializer = RecommendationRequestSerializer(data=self.payload(area))
        self.assertFalse(serializer.is_valid())
        self.assertIn("area", serializer.errors)

    def test_rejects_polygon_outside_greece(self):
        area = {
            "type": "Polygon",
            "coordinates": [[[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]],
        }
        serializer = RecommendationRequestSerializer(data=self.payload(area))
        self.assertFalse(serializer.is_valid())

    def test_rejects_malformed_nested_coordinates_without_crashing(self):
        area = {"type": "Polygon", "coordinates": [[[[23.70, 37.95]]]]}
        serializer = RecommendationRequestSerializer(data=self.payload(area))
        self.assertFalse(serializer.is_valid())
        self.assertIn("area", serializer.errors)


class PublicSerializerTests(SimpleTestCase):
    def test_shop_response_does_not_expose_embedding(self):
        shop = SimpleNamespace(
            id=1,
            slug="test-shop",
            name="Test Shop",
            display_name_el="Δοκιμή",
            display_name_en="Test Shop",
            category="cafe",
            address="Athens",
            phone="",
            website="",
            opening_hours="24/7",
            location=Point(23.72, 37.98),
        )
        data = ShopSerializer(shop).data
        self.assertNotIn("embedding", data)
        self.assertEqual(data["latitude"], 37.98)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    REST_FRAMEWORK={"DEFAULT_THROTTLE_CLASSES": []},
)
class RecommendationApiTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("rag.views.generate_answer", return_value="Try [S1].")
    @patch("rag.views.find_shops")
    def test_returns_grounded_answer_and_shops(self, find_shops, _generate):
        find_shops.return_value = [{"reference": "S1", "name": "Cafe"}]
        response = self.client.post(
            "/api/v1/recommendations",
            {"question": "quiet cafe", "language": "en", "area": ATHENS_POLYGON},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["shops"][0]["reference"], "S1")

    def test_invalid_coordinates_return_400(self):
        response = self.client.post(
            "/api/v1/recommendations",
            {"question": "cafe", "language": "en", "area": {"type": "Polygon", "coordinates": []}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("rag.views.stream_answer", return_value=iter(("Try [S1].",)))
    @patch("rag.views.find_shops", return_value=[{"reference": "S1", "name": "Cafe"}])
    def test_sse_accept_header_is_supported(self, _find, _stream):
        response = self.client.post(
            "/api/v1/recommendations?stream=true",
            {"question": "quiet cafe", "language": "en", "area": ATHENS_POLYGON},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")

    def test_sse_validation_error_has_a_json_body(self):
        response = self.client.post(
            "/api/v1/recommendations?stream=true",
            {"question": "cafe", "language": "en", "area": {"type": "Polygon", "coordinates": []}},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("area", json.loads(response.content))

    def test_metadata_requests_do_not_consume_recommendation_rate_limit(self):
        for _ in range(65):
            response = self.client.get("/api/v1/categories")
            self.assertEqual(response.status_code, 200)


class OllamaFallbackTests(SimpleTestCase):
    def test_empty_results_are_useful(self):
        self.assertIn("No matching shops", deterministic_answer([], "en"))

    @patch("rag.ollama.requests.post", side_effect=RequestException("offline"))
    def test_unavailable_ollama_falls_back(self, _post):
        shops = [{"reference": "S1", "name": "Local Cafe"}]
        answer = generate_answer("cafe", "en", shops)
        self.assertIn("[S1]", answer)
