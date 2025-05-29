from django.urls import path
from . import views

urlpatterns = [
    path("", views.TreeAPIView.as_view(), name="index"),
]
