from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "SUPER_ADMIN"
        )


class IsOwnerProfile(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user