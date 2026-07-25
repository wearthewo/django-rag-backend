import json
import socket
from urllib.parse import urlparse

from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .categories import CATEGORIES
from .models import Settlement, Shop
from .ollama import generate_answer, stream_answer
from .renderers import EventStreamRenderer
from .search import find_shops
from .serializers import RecommendationRequestSerializer, SettlementSerializer, ShopSerializer
from .throttles import RecommendationRateThrottle


def _sse(event, payload):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _tcp_reachable(url, default_port):
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or default_port
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


class RecommendationView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer, EventStreamRenderer)
    throttle_classes = (RecommendationRateThrottle,)

    def post(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        shops = find_shops(values["question"], values["area"], values.get("filters", {}))
        wants_stream = request.query_params.get("stream") == "true" or "text/event-stream" in request.headers.get("Accept", "")
        if wants_stream:
            return self._stream(values, shops)
        answer = generate_answer(values["question"], values["language"], shops)
        return Response({"answer": answer, "shops": shops, "count": len(shops)})

    def _stream(self, values, shops):
        def events():
            yield _sse("metadata", {"count": len(shops), "language": values["language"]})
            yield _sse("shops", shops)
            try:
                for chunk in stream_answer(values["question"], values["language"], shops):
                    yield _sse("answer_delta", {"text": chunk})
                yield _sse("done", {"ok": True})
            except Exception:
                yield _sse("error", {"code": "generation_failed", "message": "Answer generation failed."})

        response = StreamingHttpResponse(events(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class ShopDetailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request, slug):
        shop = get_object_or_404(Shop, slug=slug, is_published=True)
        return Response(ShopSerializer(shop).data)


class CategoryListView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request):
        return Response([
            {"key": key, **labels}
            for key, labels in CATEGORIES.items()
        ])


class LocationListView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = ()

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response([])
        settlements = Settlement.objects.filter(
            Q(name__icontains=query) | Q(name_el__icontains=query) | Q(name_en__icontains=query)
        ).order_by("name")[:10]
        return Response(SettlementSerializer(settlements, many=True).data)


class HealthView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    throttle_classes = ()

    def get(self, request):
        checks = {"database": False, "valkey": False, "ollama": False}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks["database"] = cursor.fetchone()[0] == 1
        except Exception:
            pass
        if settings.PROBE_OPTIONAL_SERVICES:
            checks["valkey"] = _tcp_reachable(settings.VALKEY_URL, 6379)
            checks["ollama"] = _tcp_reachable(settings.OLLAMA_URL, 11434)
        required_healthy = checks["database"]
        return Response(
            {"status": "ok" if required_healthy else "degraded", "checks": checks},
            status=status.HTTP_200_OK if required_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
