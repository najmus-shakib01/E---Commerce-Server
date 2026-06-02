from django.urls import path
from .views import (
    ContactFormView,
    AdminInquiryListView,
    AdminInquiryDetailView,
    AdminInquiryMarkReadView,
    AdminInquiryReplyView,
)
from .APIRootView import ContactAPIRootView

app_name = "contact"

urlpatterns = [
    # ── API Root ──────────────────────────────────────────────────────────────
    path("", ContactAPIRootView.as_view(), name="api-root"),

    # ── Public ───────────────────────────────────────────────────────────────
    path("submit/", ContactFormView.as_view(), name="contact-submit"),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("admin/",                              AdminInquiryListView.as_view(),   name="admin-list"),
    path("admin/<uuid:id>/",                    AdminInquiryDetailView.as_view(), name="admin-detail"),
    path("admin/<uuid:id>/mark-read/",          AdminInquiryMarkReadView.as_view(), name="admin-mark-read"),
    path("admin/<uuid:id>/reply/",              AdminInquiryReplyView.as_view(),  name="admin-reply"),
]