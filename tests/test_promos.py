"""The eight key checkout scenarios, including exact HTTP error messages."""
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.core.models import Event, EventSection, PromoCode, Order, Ticket, Payment


class PromoScenarioTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="SecureTest123!")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        self.event = Event.objects.create(name="Checkout Event A", starts_at=now + timedelta(days=7))
        self.other_event = Event.objects.create(name="Checkout Event B", starts_at=now + timedelta(days=8))
        self.section = EventSection.objects.create(event=self.event, name="Regular", price=Decimal("100.00"), capacity=20)
        self.promo = PromoCode.objects.create(
            code="save25", event=self.event, discount_type="percentage",
            discount_value=Decimal("25"), max_uses=5, min_tickets=1,
            valid_from=now - timedelta(days=1), valid_to=now + timedelta(days=1),
        )

    def request_order(self, code="SAVE25", quantity=2):
        return self.client.post("/api/orders/", {
            "event_id": self.event.pk,
            "sections": [{"section_id": self.section.pk, "quantity": quantity}],
            "promo_code": code,
        }, format="json")

    def request_validation(self, code="SAVE25", quantity=2, event_id=None):
        return self.client.post("/api/promos/validate/", {
            "code": code, "event_id": event_id or self.event.id, "quantity": quantity,
        }, format="json")

    def test_01_missing_promo_returns_404(self):
        response = self.request_validation("DOESNOTEXIST")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(str(response.data["detail"]), "Promo code not found")

    def test_02_soft_deleted_promo_returns_404(self):
        self.promo.soft_delete()
        self.assertEqual(self.request_validation().status_code, 404)
        self.assertEqual(self.request_order().status_code, 404)

    def test_03_not_yet_valid_returns_400(self):
        self.promo.valid_from = timezone.now() + timedelta(days=1)
        self.promo.save()
        response = self.request_validation()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data["detail"]), "Promo code is not yet valid")

    def test_04_expired_promo_returns_400(self):
        self.promo.valid_to = timezone.now() - timedelta(seconds=1)
        self.promo.save()
        response = self.request_validation()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data["detail"]), "Promo code has expired")

    def test_05_exhausted_promo_returns_400(self):
        self.promo.current_uses = self.promo.max_uses
        self.promo.save()
        response = self.request_order()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data["detail"]), "Promo code usage limit reached")
        self.assertEqual(Order.objects.count(), 0)

    def test_06_wrong_event_message_exact(self):
        self.promo.event = self.other_event
        self.promo.save()
        response = self.request_order()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data["detail"]), "Promo code is not valid for this event")

    def test_07_minimum_ticket_quantity(self):
        self.promo.min_tickets = 3
        self.promo.save()
        response = self.request_order(quantity=2)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data["detail"]), "Minimum 3 tickets required for this promo code")

    def test_08_order_201_correct_amount_and_usage(self):
        response = self.request_order(code=" save25 ", quantity=2)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("200.00"))
        self.assertEqual(Decimal(response.data["service_fee"]), Decimal("24.00"))
        self.assertEqual(Decimal(response.data["facility_fee"]), Decimal("10.00"))
        self.assertEqual(Decimal(response.data["processing_fee"]), Decimal("3.00"))
        self.assertEqual(Decimal(response.data["discount_amount"]), Decimal("50.00"))
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("187.00"))
        self.assertEqual(response.data["payment_status"], "pending")
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)
        self.assertEqual(Payment.objects.count(), 1)
        self.promo.refresh_from_db()
        self.section.refresh_from_db()
        self.assertEqual(self.promo.current_uses, 1)
        self.assertEqual(self.section.reserved, 2)

    def test_09_promo_validation_alone_does_not_consume_code(self):
        response = self.request_validation()
        self.assertEqual(response.status_code, 200)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.current_uses, 0)

    def test_10_fixed_discount_is_capped_at_subtotal(self):
        self.promo.discount_type = "fixed"
        self.promo.discount_value = Decimal("500")
        self.promo.save()
        response = self.request_order(quantity=2)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Decimal(response.data["discount_amount"]), Decimal("200.00"))
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("37.00"))

    def test_11_max_discount_cap(self):
        self.promo.max_discount = Decimal("20.00")
        self.promo.save()
        response = self.request_order(quantity=2)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Decimal(response.data["discount_amount"]), Decimal("20.00"))
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("217.00"))

    def test_12_insufficient_inventory_does_not_consume_promo(self):
        self.section.capacity = 1
        self.section.save()
        response = self.request_order(quantity=2)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.current_uses, 0)

    def test_13_global_promo_allowed_for_both_events(self):
        self.promo.event = None
        self.promo.save()
        response = self.request_validation(event_id=self.other_event.id)
        self.assertEqual(response.status_code, 200)

    def test_14_invalid_promo_does_not_create_payment(self):
        response = self.request_order(code="MISSING")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Payment.objects.count(), 0)

    def test_15_payment_failure_rolls_back_everything(self):
        from unittest.mock import patch
        with patch("apps.core.services.order_service.Payment.objects.create", side_effect=RuntimeError("gateway demo failure")):
            with self.assertRaises(RuntimeError):
                from apps.core.services.order_service import create_order
                create_order(user=self.user, event_id=self.event.pk,
                             sections_data=[{"section_id": self.section.pk, "quantity": 2}],
                             promo_code_str="SAVE25")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)
        self.section.refresh_from_db()
        self.promo.refresh_from_db()
        self.assertEqual(self.section.reserved, 0)
        self.assertEqual(self.promo.current_uses, 0)

    def test_16_duplicate_section_rejected(self):
        response = self.client.post("/api/orders/", {
            "event_id": self.event.pk,
            "sections": [
                {"section_id": self.section.pk, "quantity": 1},
                {"section_id": self.section.pk, "quantity": 1},
            ], "promo_code": "SAVE25",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_17_unknown_event_rejected(self):
        response = self.client.post("/api/orders/", {
            "event_id": 999999,
            "sections": [{"section_id": self.section.pk, "quantity": 1}],
        }, format="json")
        self.assertEqual(response.status_code, 404)
