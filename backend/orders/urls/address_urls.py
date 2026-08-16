from django.urls import path
from .. import views


urlpatterns = [
    path("", view=views.AddressCreateListView.as_view()),
    path("<int:pk>/", view=views.AddressDetailView.as_view()),
]