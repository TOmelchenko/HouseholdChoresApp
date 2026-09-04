from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create_household, name="create_household"),
    path("join/", views.join_household, name="join_household"),
    path("chores/", views.my_chores, name="my_chores"),
    path("chores/<int:assignment_id>/complete/", views.complete_chore, name="complete_chore"),
    path("chores/<int:assignment_id>/undo/", views.undo_chore, name="undo_chore"),
]
