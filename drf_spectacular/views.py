from rest_framework.response import Response
from rest_framework.views import APIView


class SpectacularAPIView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"detail": "OpenAPI schema is unavailable in the local test shim."})


class SpectacularSwaggerView(APIView):
    url_name = None

    def get(self, request, *args, **kwargs):
        return Response({"detail": "Swagger UI is unavailable in the local test shim."})


class SpectacularRedocView(APIView):
    url_name = None

    def get(self, request, *args, **kwargs):
        return Response({"detail": "ReDoc UI is unavailable in the local test shim."})
