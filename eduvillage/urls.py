from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import bootstrap_admin

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/bootstrap-admin/", bootstrap_admin),

    # ✅ ONLY YOUR CUSTOM JWT
    path("api/", include("core.urls")),
    path("api/", include("courses.urls")),

    # optional HTML routes
    path("", include("courses.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)