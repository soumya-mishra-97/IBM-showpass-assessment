"""HTTP layer: authentication, validation and serialization only."""
from django.contrib.auth import authenticate
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from .models import Event, Order
from .utils.exceptions import NotFoundError
from .serializers import (
    EventSerializer, OrderCreateSerializer, OrderReadSerializer, PromoValidateSerializer,
    LoginRequestSerializer, LoginResponseSerializer, ErrorResponseSerializer,
    PromoValidateResponseSerializer,
)
from .services.promo_service import validate_promo_code
from .services.order_service import create_order


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(tags=["Authentication"], request=LoginRequestSerializer,
                   responses={200: LoginResponseSerializer, 401: ErrorResponseSerializer})
    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request=request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.username})


class EventListView(APIView):
    @extend_schema(tags=["Events"], responses=EventSerializer(many=True))
    def get(self, request):
        events = Event.objects.filter(is_active=True).prefetch_related("sections").order_by("starts_at")
        return Response(EventSerializer(events, many=True).data)


class PromoValidateView(APIView):
    @extend_schema(tags=["Promotions"], request=PromoValidateSerializer,
                   responses={200: PromoValidateResponseSerializer, 400: ErrorResponseSerializer,
                              404: ErrorResponseSerializer})
    def post(self, request):
        serializer = PromoValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not Event.objects.filter(pk=data["event_id"], is_active=True).exists():
            raise NotFoundError("Event not found")
        result = validate_promo_code(data["code"], data["event_id"], data["quantity"])
        promo = result["promo"]
        return Response({
            "valid": True,
            "code": promo.code,
            "discount_type": promo.discount_type,
            "discount_value": str(promo.discount_value),
            "max_discount": str(promo.max_discount) if promo.max_discount is not None else None,
            "message": "Promo code is valid; usage is counted only when an order is created",
        })


class OrderListCreateView(APIView):
    @extend_schema(tags=["Orders"], responses=OrderReadSerializer(many=True))
    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .select_related("event", "promo_code", "payment")
            .prefetch_related("tickets__section")[:30]
        )
        return Response(OrderReadSerializer(orders, many=True).data)

    @extend_schema(tags=["Orders"], request=OrderCreateSerializer,
                   responses={201: OrderReadSerializer, 400: ErrorResponseSerializer,
                              404: ErrorResponseSerializer})
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order = create_order(
            user=request.user,
            event_id=data["event_id"],
            sections_data=data["sections"],
            promo_code_str=data["promo_code"],
        )
        # Reload related data for stable serialization.
        order = Order.objects.select_related("event", "promo_code", "payment").prefetch_related("tickets__section").get(pk=order.pk)
        return Response(OrderReadSerializer(order).data, status=status.HTTP_201_CREATED)
