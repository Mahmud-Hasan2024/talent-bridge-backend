from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from accounts.models import User


class UserCreateSerializer(BaseUserCreateSerializer):
    role = serializers.ChoiceField(choices=[('employer', 'Employer'), ('seeker', 'Job Seeker')])

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'password', 'first_name', 'last_name',
            'address', 'phone_number', 'role'
        )

    def create(self, validated_data):
        if validated_data.get('role') == 'admin':
            raise serializers.ValidationError("You cannot create an admin account.")
        return super().create(validated_data)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        ref_name = "CustomUser"
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name',
            'address', 'phone_number', 'role', 'is_active', 'date_joined',
        )
        read_only_fields = ('email', 'date_joined')

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if 'role' in validated_data and not (request and getattr(request.user, 'role', '') == 'admin'):
            validated_data.pop('role', None)
        return super().update(instance, validated_data)


class SimpleUserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')