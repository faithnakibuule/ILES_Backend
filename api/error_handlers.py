# api/error_handlers.py
# Centralised error response format for the entire ILES backend.
# Every error returned by any view goes through this format:
# { "error": "human readable message", "code": "MACHINE_READABLE_CODE" }

from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    # First, let DRF do its default handling
    response = exception_handler(exc, context)

    if response is not None:
        # Map HTTP status codes to our error codes
        error_codes = {
            400: 'BAD_REQUEST',
            401: 'UNAUTHORIZED',
            403: 'PERMISSION_DENIED',
            404: 'NOT_FOUND',
            405: 'METHOD_NOT_ALLOWED',
            429: 'TOO_MANY_REQUESTS',
            500: 'SERVER_ERROR',
        }

        # Extract the human-readable message from DRF's response
        original_data = response.data

        if isinstance(original_data, dict) and 'detail' in original_data:
            # DRF puts most errors in a 'detail' key
            error_message = str(original_data['detail'])
        elif isinstance(original_data, list):
            error_message = original_data[0] if original_data else 'An error occurred.'
        elif isinstance(original_data, dict):
            # Validation errors: grab the first field's first error
            first_key = next(iter(original_data))
            first_val = original_data[first_key]
            if isinstance(first_val, list):
                error_message = f"{first_key}: {first_val[0]}"
            else:
                error_message = f"{first_key}: {first_val}"
        else:
            error_message = str(original_data)

        code = error_codes.get(response.status_code, 'ERROR')

        response.data = {
            'error': error_message,
            'code': code,
        }

        if response.status_code == 400:
            response.data['details'] = original_data

    return response
