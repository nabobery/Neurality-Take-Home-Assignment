from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

router = DefaultRouter()
router.register(r'', DocumentViewSet, basename='documents')

urlpatterns = [
    path('', include(router.urls)),  # This will include endpoints such as:
    # POST /api/documents/upload/ for document uploads,
    # POST /api/documents/ask/ for asking questions.
]