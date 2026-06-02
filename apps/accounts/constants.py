from django.db import models

class UserRole(models.TextChoices):
    USER = "USER", "User"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"


class AuthProvider(models.TextChoices):
    EMAIL = "EMAIL", "Email"
    GOOGLE = "GOOGLE", "Google"


class GenderChoice(models.TextChoices):
    MALE = "Male", "Male"
    FEMALE = "Female", "Female"
    OTHER = "Other", "Other"


OTP_LENGTH = 6
OTP_EXPIRE_SECONDS = 60          
OTP_MAX_RETRY = 5
OTP_MAX_RESEND = 3
OTP_RESEND_COOLDOWN_SECONDS = 3600  
PASSWORD_RESET_EXPIRY_MINUTES = 10