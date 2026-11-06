"""Pure pricing checks; no database required."""
from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase

from apps.core.services.pricing_service import calculate_order_totals, calculate_promo_discount


class PricingTests(TestCase):
    def test_percentage_discount_total(self):
        promo = SimpleNamespace(discount_type="percentage", discount_value=Decimal("25"), max_discount=None)
        self.assertEqual(calculate_order_totals(Decimal("200"), 2, promo)["total_amount"], Decimal("187.00"))

    def test_fixed_discount_cannot_exceed_subtotal(self):
        promo = SimpleNamespace(discount_type="fixed", discount_value=Decimal("500"), max_discount=None)
        self.assertEqual(calculate_order_totals(Decimal("200"), 2, promo)["discount_amount"], Decimal("200.00"))

    def test_discount_respects_maximum(self):
        promo = SimpleNamespace(discount_type="percentage", discount_value=Decimal("50"), max_discount=Decimal("20"))
        self.assertEqual(calculate_order_totals(Decimal("200"), 2, promo)["discount_amount"], Decimal("20.00"))

    def test_no_promo_has_zero_discount(self):
        self.assertEqual(calculate_promo_discount(None, Decimal("100")), Decimal("0.00"))

    def test_no_promo_total_includes_fees(self):
        self.assertEqual(calculate_order_totals(Decimal("100"), 1)["total_amount"], Decimal("120.00"))
