from django.db import models
from django.utils.text import slugify

# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Product(TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_available = models.BooleanField(default=True)


    def save(self,*args, **kwargs ):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug = slug).exists():
                slug = f"{base_slug}-{counter}"
                counter +=1
            self.slug = slug
        
        super().save(*args, **kwargs)


    class Meta:
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.name} - {self.price}"
    
