from django.urls import path
from . import views


urlpatterns = [
    path('', view=views.CartDetailView.as_view()),
    path('items/', view=views.AddCartItemView.as_view()),
    path('item/<int:item_id>/', view=views.CartItemView.as_view()), #Updates and deletes item
    path("clear/", view=views.ClearCartView.as_view()),
]