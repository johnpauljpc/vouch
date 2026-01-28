from django.urls import path
from . import views


urlpatterns = [
    path("", view=views.AddressCreateListView.as_view()),
    path("<int:id>/", view=views.AddressDetailView.as_view()),
]