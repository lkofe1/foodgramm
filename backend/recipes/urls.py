from django.urls import path

from .views import recipe_short_link_redirect

urlpatterns = [
    path('<int:pk>/', recipe_short_link_redirect, name='short_link'),
]
