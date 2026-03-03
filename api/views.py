from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def test_api(request):
    return Response({
        "message": "ILES API is working with REST Framework!",
        "status": "success"
    })