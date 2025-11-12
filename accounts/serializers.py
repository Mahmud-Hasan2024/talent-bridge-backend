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
        """Prevent users from creating admin accounts manually."""
        if validated_data.get('role') == 'admin':
            raise serializers.ValidationError("You cannot create an admin account.")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Safely block non-admins from changing role
        if 'role' in validated_data and not request.user.has_perm('accounts.is_admin_only'):
            validated_data.pop('role')

        return super().update(instance, validated_data)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        ref_name = "CustomUser"
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name',
            'address', 'phone_number', 'role'
        )
        read_only_fields = ('email',)

    def update(self, instance, validated_data):
        """Allow only admins (with custom permission) to change role."""
        request = self.context.get('request')

        # Prevent non-admins from changing role
        if 'role' in validated_data and not request.user.has_perm('accounts.is_admin_only'):
            validated_data.pop('role')

        instance = super().update(instance, validated_data)

        # Keep group sync logic
        instance.sync_group_with_role()
        return instance
    
    
class SimpleUserDetailSerializer(serializers.ModelSerializer):
    """Serializer used for nesting inside ApplicationSerializer."""
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')
