from common.permissions import IsSuperAdminUser
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import LoginSerializer, UserAdminCreateUpdateSerializer, UserSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"success": True, "message": "Successfully logged out."})
        except Exception:
            return Response(
                {"success": False, "message": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"success": True, "user": UserSerializer(request.user).data})


class RegisterAdminView(APIView):
    """
    Allows self-service or initial admin registration.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        role = request.data.get("role", "SUPERADMIN").upper()

        if not email or "@" not in email:
            return Response(
                {"success": False, "message": "A valid email address is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not password or len(password) < 8:
            return Response(
                {"success": False, "message": "Password must be at least 8 characters long."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"success": False, "message": "An account with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_roles = ["SUPERADMIN", "CONTENT_EDITOR", "FINANCE_AUDITOR", "MODERATOR"]
        if role not in allowed_roles:
            role = "SUPERADMIN"

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=True,
            is_superuser=(role == "SUPERADMIN"),
            capabilities=["*"] if role == "SUPERADMIN" else ["content:read", "content:write"],
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "message": "Admin account created successfully.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class UserAdminViewSet(viewsets.ModelViewSet):
    """
    Sub-admin provisioning: strictly guarded by SuperAdmin privileges.
    """

    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsSuperAdminUser]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserAdminCreateUpdateSerializer
        return UserSerializer
