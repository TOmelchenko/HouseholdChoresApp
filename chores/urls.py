from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.create_household, name="create_household"),
]
