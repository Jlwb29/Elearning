from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts.views import SignUpView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("people/", include("accounts.urls")),   
    path("signup/", SignUpView.as_view(), name="signup"),
    path("courses/", include("courses.urls")),  
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("chat/", include("rtchat.urls")),  
    path("api/v1/", include("api.urls"))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)