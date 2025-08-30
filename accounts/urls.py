from django.urls import path
from .views import me_redirect, user_home, people_search

urlpatterns = [
    path("search/", people_search, name="people_search"),
    path("me/", me_redirect, name="me"),
    path("u/<str:username>/", user_home, name="user_home"),
]
