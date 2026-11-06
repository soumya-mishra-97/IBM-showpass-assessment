"""Database layer: stores events, ticket inventory, promos, orders and payments.

Business rules do NOT live here: see services/*.py.
"""
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ActivePromoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    objects = ActivePromoManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class Event(models.Model):
    name = models.CharField(max_length=150)
    starts_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class EventSection(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="sections")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    capacity = models.PositiveIntegerField()
    reserved = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "name"], name="unique_event_section")]

    def __str__(self):
        return f"{self.event.name}: {self.name}"


class PromoCode(SoftDeleteModel):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    DISCOUNT_TYPES = [(PERCENTAGE, "Percentage"), (FIXED, "Fixed")]

    code = models.CharField(max_length=50, unique=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT, null=True, blank=True, related_name="promos")
    discount_type = models.CharField(max_length=12, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       validators=[MinValueValidator(0)])
    min_tickets = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    max_uses = models.PositiveIntegerField(default=100)
    current_uses = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class Order(models.Model):
    CREATED = "created"
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="showpass_orders")
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="orders")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2)
    facility_fee = models.DecimalField(max_digits=12, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default=CREATED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")
    section = models.ForeignKey(EventSection, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


class Payment(models.Model):
    PENDING = "pending"
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
