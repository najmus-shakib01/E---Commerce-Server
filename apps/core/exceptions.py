import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled Server Exception in request context:")
        return _build(
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="server error",
            data=None,
        )

    if isinstance(exc, ValidationError):
        return _build(
            http_status=response.status_code,
            message="validation error",
            data={"errors": response.data},
        )

    message = _default_message_for_status(response.status_code)
    return _build(
        http_status=response.status_code,
        message=message,
        data=None,
    )

def _build(*, http_status: int, message: str, data):
    return Response(
        {
            "status": False,
            "message": message,
            "data": data,
        },
        status=http_status,
    )

def _default_message_for_status(code: int) -> str:
    if code == 404:
        return "not found"
    if code == 403:
        return "permission denied"
    if code == 401:
        return "authentication failed"
    if code >= 500:
        return "server error"
    return "error"