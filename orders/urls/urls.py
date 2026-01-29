from django.urls import path
from .. import views


urlpatterns = [
   path('', view=views.OrderListView.as_view()),
   path('<int:pk>/', view=views.OrderDetailView.as_view()),
   path('cancel/<int:pk>/', view=views.CancelOrderView.as_view()),
]