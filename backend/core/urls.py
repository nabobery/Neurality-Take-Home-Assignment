from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/documents/', include('chat.urls')),  # Routes all document-related endpoints to the chat app.
]