import logging
import os
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from apps.accounts.models import UserProfile
from apps.core.response import api_response
from . import services
from .serializers import (
    ForgotPasswordSerializer,
    GoogleAuthSerializer,
    LoginSerializer,
    LogoutSerializer,
    OTPResendSerializer,
    OTPVerifySerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
)
logger = logging.getLogger(__name__)  #

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = services.register_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return api_response(True, "Registration successful. OTP sent to your email.", data, 201)


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = services.verify_otp(
            email=serializer.validated_data["email"],
            otp_input=serializer.validated_data["otp"],
        )
        return api_response(True, "Email verified successfully.", data, 200)


class OTPResendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = services.resend_otp(email=serializer.validated_data["email"])
        return api_response(True, "OTP resent successfully.", data, 200)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = services.login_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            request=request,
        )
        return api_response(True, "Login successful.", data, 200)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.logout_user(refresh_token=serializer.validated_data["refresh"])
        return api_response(True, "Logged out successfully.", None, 200)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.forgot_password(email=serializer.validated_data["email"])
        return api_response(
            True,
            "If an account exists with this email, a reset link has been sent.",
            None,
            200,
        )

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reset_password(
            uid=uid,
            token=token,
            new_password=serializer.validated_data["password"],
        )
        return api_response(True, "Password reset successful.", None, 200)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            serializer = UserProfileSerializer(profile, context={'request': request})
            return api_response(True, "Profile retrieved.", serializer.data, 200)
        except Exception as e:
            logger.error(f"Profile GET error: {str(e)}")
            return api_response(False, f"Error fetching profile: {str(e)}", None, 500)

    def patch(self, request):
        try:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            serializer = UserProfileSerializer(
                profile,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            if not serializer.is_valid():
                print("=== VALIDATION ERRORS ===", serializer.errors)  
                return api_response(False, "Validation error", serializer.errors, 400)
            serializer.save()
            return api_response(True, "Profile updated successfully.", serializer.data, 200)
        except Exception as e:
            logger.error(f"Profile PATCH error: {str(e)}")
            return api_response(False, f"Error updating profile: {str(e)}", None, 500)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = services.google_authenticate(
            id_token_str=serializer.validated_data["id_token"]
        )

        if data.get('tokens'):
            print(f"Access token length: {len(data['tokens'].get('access', ''))}")
            print(f"Refresh token length: {len(data['tokens'].get('refresh', ''))}")
        
        return api_response(True, "Google login successful.", data, 200)

class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        error = request.GET.get("error")

        if error or not code:
            return redirect(f"{settings.FRONTEND_BASE_URL}/login?error=google_auth_failed")

        try:
            id_token_str = services.google_auth_code_exchange(code)
            data = services.google_authenticate(id_token_str)
            
            access_token = data["tokens"]["access"]  
            refresh_token = data["tokens"]["refresh"]  

            redirect_url = f"{settings.FRONTEND_BASE_URL}/oauth/success#access={access_token}&refresh={refresh_token}"
            return redirect(redirect_url)
        except Exception as e:
            print("Google Callback Error:", e)
            return redirect(f"{settings.FRONTEND_BASE_URL}/login?error=google_auth_failed")