from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .APIRootView import AccountsAPIRootView
from .views import (
    ForgotPasswordView,
    GoogleAuthView,
    LoginView,
    LogoutView,
    OTPResendView,
    OTPVerifyView,
    ProfileView,
    RegisterView,
    ResetPasswordView,
    GoogleCallbackView,
)

urlpatterns = [
    path("", AccountsAPIRootView.as_view(), name="accounts-api-root"),
    path("register/", RegisterView.as_view(), name="register"),
    path("otp-verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("otp-resend/", OTPResendView.as_view(), name="otp-resend"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/<str:uid>/<str:token>/", ResetPasswordView.as_view(), name="reset-password"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("auth/google-login/", GoogleAuthView.as_view(), name="google-login"),
    path("auth/google-callback/", GoogleCallbackView.as_view(), name="google-callback"),
]