from rest_framework.response import Response

def api_response(status_bool: bool, message: str, data, status_code: int = 200):
    return Response(
        {"status": status_bool, "message": message, "data": data},
        status=status_code,
    )

def success_response(*, message: str, data=None, http_status=200):
    resp = api_response(status_bool=True, message=message, data=data)
    resp.status_code = http_status
    return resp

def error_response(*, message: str, data=None, http_status=400):
    resp = api_response(status_bool=False, message=message, data=data)
    resp.status_code = http_status
    return resp