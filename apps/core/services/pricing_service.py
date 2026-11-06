"""Pure price calculations: testable without Django or a database."""
from decimal import Decimal, ROUND_HALF_UP

SERVICE_FEE_PER_TICKET = Decimal("12.00")
FACILITY_FEE_PER_TICKET = Decimal("5.00")
PROCESSING_FEE = Decimal("3.00")


def round_money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_promo_discount(promo_code, subtotal):
    if promo_code is None:
        return Decimal("0.00")
    subtotal = Decimal(str(subtotal))
    discount_value = Decimal(str(promo_code.discount_value))
    if promo_code.discount_type == "percentage":
        discount = subtotal * discount_value / Decimal("100")
    elif promo_code.discount_type == "fixed":
        discount = discount_value
    else:
        return Decimal("0.00")
    if promo_code.max_discount is not None:
        discount = min(discount, Decimal(str(promo_code.max_discount)))
    discount = min(discount, subtotal)
    return round_money(max(discount, Decimal("0.00")))


def calculate_order_totals(subtotal, quantity, promo_code=None):
    subtotal = round_money(subtotal)
    service_fee = round_money(SERVICE_FEE_PER_TICKET * quantity)
    facility_fee = round_money(FACILITY_FEE_PER_TICKET * quantity)
    discount_amount = calculate_promo_discount(promo_code, subtotal)
    total_amount = round_money(subtotal + service_fee + facility_fee + PROCESSING_FEE - discount_amount)
    return {
        "subtotal": subtotal,
        "service_fee": service_fee,
        "facility_fee": facility_fee,
        "processing_fee": PROCESSING_FEE,
        "discount_amount": discount_amount,
        "total_amount": total_amount,
    }
