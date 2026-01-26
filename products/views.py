from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView


from .models import Product
from .serializers import ProductSerializer
from .permissions import IsAdminOrReadOnly
# Create your views here.


class CreateListProducts(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


    def get_queryset(self):
        if not self.request.user.is_superuser:
            return Product.objects.filter(is_available = True)
        return super().get_queryset()

class ProductDetail(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


