from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import  CustomUser


# Register your models here.
# admin.py


class CustomUserAdmin(UserAdmin):
    model = CustomUser
  

admin.site.register(CustomUser, CustomUserAdmin)
