"""Deterministic fixtures; safe to rerun for learning (does not clear orders)."""
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token
from apps.core.models import Event, EventSection, PromoCode


class Command(BaseCommand):
    help = "Create a demo user, event, ticket sections and promo-code test scenarios."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        user, created = User.objects.get_or_create(username="learner", defaults={"email": "learner@example.invalid"})
        if created:
            user.set_password("Learning@123")
            user.save()
        Token.objects.get_or_create(user=user)

        now = timezone.now()
        event, _ = Event.objects.get_or_create(name="ShowPass Tech Festival", defaults={"starts_at": now + timedelta(days=30)})
        other, _ = Event.objects.get_or_create(name="Design Leadership Summit", defaults={"starts_at": now + timedelta(days=35)})
        regular, _ = EventSection.objects.get_or_create(
            event=event, name="Regular", defaults={"price": Decimal("100.00"), "capacity": 150}
        )
        EventSection.objects.get_or_create(event=event, name="VIP", defaults={"price": Decimal("250.00"), "capacity": 40})
        EventSection.objects.get_or_create(event=other, name="Regular", defaults={"price": Decimal("120.00"), "capacity": 70})

        variants = [
            ("SAVE25", event, "percentage", "25.00", 1, 100, now - timedelta(days=1), now + timedelta(days=20), None),
            ("FLAT30", None, "fixed", "30.00", 1, 100, now - timedelta(days=1), now + timedelta(days=20), None),
            ("CAP20", event, "percentage", "50.00", 1, 100, now - timedelta(days=1), now + timedelta(days=20), "20.00"),
            ("FUTURE", event, "percentage", "10.00", 1, 100, now + timedelta(days=1), now + timedelta(days=20), None),
            ("EXPIRED", event, "fixed", "10.00", 1, 100, now - timedelta(days=20), now - timedelta(days=1), None),
            ("MIN3", event, "percentage", "10.00", 3, 100, now - timedelta(days=1), now + timedelta(days=20), None),
            ("WRONGEVENT", other, "percentage", "10.00", 1, 100, now - timedelta(days=1), now + timedelta(days=20), None),
            ("EXHAUSTED", event, "fixed", "10.00", 1, 0, now - timedelta(days=1), now + timedelta(days=20), None),
            ("DELETED", event, "fixed", "10.00", 1, 100, now - timedelta(days=1), now + timedelta(days=20), None),
        ]
        for code, promo_event, dtype, value, minimum, limit, start, end, cap in variants:
            p, _ = PromoCode.all_objects.get_or_create(
                code=code, defaults={
                    "event": promo_event,
                    "discount_type": dtype,
                    "discount_value": Decimal(value),
                    "min_tickets": minimum,
                    "max_uses": limit,
                    "valid_from": start,
                    "valid_to": end,
                    "max_discount": Decimal(cap) if cap else None,
                },
            )
            if code == "DELETED" and p.deleted_at is None:
                p.soft_delete()

        self.stdout.write(self.style.SUCCESS("Local demo initialized (existing orders preserved)."))
        self.stdout.write("Login: learner / Learning@123")
        self.stdout.write(f"Example: event_id={event.pk}, section_id={regular.pk}; SAVE25 = 25%")
        self.stdout.write("Demo credentials are only for local development; change for real use.")
