from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class CookieJWTAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT to also read the access token from
    an HttpOnly cookie named 'access_token'.
    Falls back to the Authorization header automatically.
    """

    def authenticate(self, request):        
        raw_token = request.COOKIES.get("access_token")
        if raw_token:
            try:
                validated = self.get_validated_token(raw_token)
                return self.get_user(validated), validated
            except (InvalidToken, TokenError):
                pass  

        return super().authenticate(request)