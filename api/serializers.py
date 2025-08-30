from django.contrib.auth.models import User
from rest_framework import serializers
from accounts.models import Status
from courses.models import Course, Enrollment

def is_teacher(user: User) -> bool:
    return user.groups.filter(name="Teacher").exists()

class UserPublicSerializer(serializers.ModelSerializer):
    is_teacher = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "date_joined", "is_teacher"]

    def get_is_teacher(self, obj):
        return is_teacher(obj)

class UserPrivateSerializer(UserPublicSerializer):
    class Meta(UserPublicSerializer.Meta):
        fields = UserPublicSerializer.Meta.fields + ["email"]

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "password", "email", "first_name", "last_name"]

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(pwd)
        user.save()
        from django.contrib.auth.models import Group
        grp, _ = Group.objects.get_or_create(name="Student")
        user.groups.add(grp)
        return user

class StatusSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model = Status
        fields = ["id", "user", "text", "created_at"]

class CourseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "title", "start_date", "end_date"]
