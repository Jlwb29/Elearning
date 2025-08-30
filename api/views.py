from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    UserPublicSerializer, UserPrivateSerializer, SignupSerializer,
    StatusSerializer, CourseMiniSerializer
)
from accounts.models import Status
from courses.models import Course, Enrollment

class IsSelfOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj == request.user

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")

    def get_permissions(self):
        if self.action in ["create"]:  
            return [permissions.AllowAny()]
        if self.action in ["destroy"]:
            return [permissions.IsAdminUser()]
        if self.action in ["partial_update", "update", "me", "statuses", "courses"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            return SignupSerializer
        if self.action in ["me", "partial_update", "update"]:
            return UserPrivateSerializer
        if self.action == "retrieve":
            obj = getattr(self, "get_object", lambda: None)()
            if obj and (self.request.user.is_staff or obj == self.request.user):
                return UserPrivateSerializer
        return UserPublicSerializer

    def list(self, request, *args, **kwargs):
        qs = self.queryset
        q = request.query_params.get("q")
        role = (request.query_params.get("role") or "").upper()
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        if role in {"TEACHER", "STUDENT"}:
            qs = qs.filter(groups__name=role).distinct()
        page = self.paginate_queryset(qs)
        ser = UserPublicSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        user = request.user
        if request.method == "PATCH":
            ser = UserPrivateSerializer(user, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
        else:
            ser = UserPrivateSerializer(user)
        return Response(ser.data)

    @action(detail=True, methods=["get", "post"])
    def statuses(self, request, pk=None):
        user = self.get_object()
        if request.method == "POST":
            if request.user != user and not request.user.is_staff:
                return Response({"detail": "You can only post for yourself."}, status=403)
            ser = StatusSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            Status.objects.create(user=user, text=ser.validated_data["text"])
        qs = Status.objects.filter(user=user).order_by("-created_at")
        page = self.paginate_queryset(qs)
        ser = StatusSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)

    @action(detail=True, methods=["get"])
    def courses(self, request, pk=None):
        user = self.get_object()
        role = (request.query_params.get("role") or "").upper()
        if role == "TEACHER":
            qs = Course.objects.filter(
                Q(created_by=user) | Q(enrollments__user=user, enrollments__role="TEACHER")
            ).distinct()
        elif role == "STUDENT":
            qs = Course.objects.filter(enrollments__user=user, enrollments__role="STUDENT").distinct()
        else:
            qs = Course.objects.filter(Q(created_by=user) | Q(enrollments__user=user)).distinct()
        page = self.paginate_queryset(qs.order_by("title"))
        ser = CourseMiniSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(ser.data)
