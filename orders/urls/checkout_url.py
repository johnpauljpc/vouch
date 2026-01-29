from django.urls import path
from .. import views


urlpatterns = [
    path('checkout/', view=views.CheckoutView.as_view()),
]