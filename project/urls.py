from django.urls import include, path
from .views import EmailAPIView
from .routers import router

urlpatterns = [
    path("", include(router.urls)),
    path("send-notification/", EmailAPIView.as_view())
]
