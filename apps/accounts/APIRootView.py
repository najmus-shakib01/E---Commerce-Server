from django.urls import reverse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from apps.core.response import api_response

class AccountsAPIRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        def url(name):
            return request.build_absolute_uri(reverse(name))

        endpoints = {
            "register": {
                "url": url("register"),
                "method": "POST",
                "description": "Register a new user account.",
                "body": {"email": "string", "password": "string", "confirm_password": "string"},
            },
            "otp_verify": {
                "url": url("otp-verify"),
                "method": "POST",
                "description": "Verify OTP sent to email.",
                "body": {"email": "string", "otp": "6-digit string"},
            },
            "otp_resend": {
                "url": url("otp-resend"),
                "method": "POST",
                "description": "Resend OTP (max 3 times, then 1-hour cooldown).",
                "body": {"email": "string"},
            },
            "login": {
                "url": url("login"),
                "method": "POST",
                "description": "Login and receive JWT tokens.",
                "body": {"email": "string", "password": "string"},
            },
            "logout": {
                "url": url("logout"),
                "method": "POST",
                "description": "Logout and blacklist the refresh token.",
                "body": {"refresh": "string"},
                "auth": "Bearer token required",
            },
            "forgot_password": {
                "url": url("forgot-password"),
                "method": "POST",
                "description": "Request password reset link via email.",
                "body": {"email": "string"},
            },
            "reset_password": {
                "url": url("reset-password"),
                "method": "POST",
                "description": "Reset password using uid and token from email.",
                "body": {
                    "uid": "string",
                    "token": "string",
                    "password": "string",
                    "confirm_password": "string",
                },
            },
            "profile": {
                "url": url("profile"),
                "methods": ["GET", "PATCH"],
                "description": "Retrieve or update authenticated user profile.",
                "auth": "Bearer token required",
            },
            "google_login": {
                "url": url("google-login"),
                "method": "POST",
                "description": "Login or register via Google OAuth2 id_token.",
                "body": {"id_token": "string"},
            },
        }

        return api_response(True, "Accounts API Root", endpoints, 200)