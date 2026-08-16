from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username','email', 'password']
        extra_kwargs = {'password': {'write_only': True}, 
                        'username': {'read_only':True}}

    def create(self, validated_data):
        email = validated_data.get('email')
        base_username = email.split('@')[0]

        username = base_username
        counter = 1 
      
        while CustomUser.objects.filter(username = username).exists():
            username = f"{base_username}{counter}"
            counter +=1
        validated_data["username"] = username

        return CustomUser.objects.create_user(**validated_data)



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']