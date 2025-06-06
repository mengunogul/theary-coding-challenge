from django.urls import path
from . import views

urlpatterns = [
    path("", views.TreeAPIView.as_view(), name="tree-api"),
    path("clone", views.TreeCloneAPIView.as_view(), name="tree-clone-api"),
]
