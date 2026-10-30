from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("studio/", include("studio.urls")),
    path("api/", api.urls),
    path("courses/", include("courses.urls")),
    # Сначала редакторские маршруты (/newspaper/editor/...), затем публичные.
    path("newspaper/editor/", include("newspaper.editor_urls")),
    path("newspaper/", include("newspaper.urls")),
    path("", include("materials.urls")),
    path("", include("main.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
