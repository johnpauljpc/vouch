from django.urls import path
from . import views


urlpatterns = [
    path("list-create/", views.CreateListProducts.as_view(), name="product_list_create"),
    path("<int:pk>/", views.ProductDetail.as_view(), name="product_detail"),
]