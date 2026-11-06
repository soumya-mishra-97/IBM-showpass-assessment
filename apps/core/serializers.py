from rest_framework import serializers
from .models import Event, EventSection, Order, Ticket


class EventSectionSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()

    class Meta:
        model = EventSection
        fields = ("id", "name", "price", "capacity", "reserved", "available")

    def get_available(self, obj) -> int:
        return max(0, obj.capacity - obj.reserved)


class EventSerializer(serializers.ModelSerializer):
    sections = EventSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ("id", "name", "starts_at", "sections")


class PromoValidateSerializer(serializers.Serializer):
    code = serializers.CharField(allow_blank=True, required=False, default="")
    event_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class OrderLineInputSerializer(serializers.Serializer):
    section_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class OrderCreateSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(min_value=1)
    sections = OrderLineInputSerializer(many=True, allow_empty=False)
    promo_code = serializers.CharField(allow_blank=True, required=False, default="")


class TicketSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "section", "section_name", "unit_price")


class OrderReadSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source="event.name", read_only=True)
    promo_code_text = serializers.SerializerMethodField()
    payment_status = serializers.CharField(source="payment.status", read_only=True)
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "event", "event_name", "promo_code", "promo_code_text", "status",
            "subtotal", "service_fee", "facility_fee", "processing_fee",
            "discount_amount", "total_amount", "payment_status", "tickets", "created_at",
        )

    def get_promo_code_text(self, obj) -> str | None:
        return obj.promo_code.code if obj.promo_code_id else None


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    username = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class PromoValidateResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    code = serializers.CharField()
    discount_type = serializers.ChoiceField(choices=["percentage", "fixed"])
    discount_value = serializers.CharField()
    max_discount = serializers.CharField(allow_null=True)
    message = serializers.CharField()
