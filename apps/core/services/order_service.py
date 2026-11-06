"""Use-case orchestration: inventory, promo validation, price, order and payment.

Never validate usage limits outside the transaction and then assume the result
is still valid during order creation; that introduces a race condition.
"""
from django.db import transaction
from django.db.models import F
from apps.core.models import Event, EventSection, PromoCode, Order, Ticket, Payment
from apps.core.services.promo_service import validate_promo_code
from apps.core.services.pricing_service import calculate_order_totals
from apps.core.utils.exceptions import BadRequestError, NotFoundError


def create_order(*, user, event_id, sections_data, promo_code_str=""):
    if not sections_data:
        raise BadRequestError("At least one ticket section is required")
    if len(sections_data) != len({item["section_id"] for item in sections_data}):
        raise BadRequestError("Duplicate ticket sections are not allowed")

    total_quantity = sum(item["quantity"] for item in sections_data)
    if total_quantity < 1:
        raise BadRequestError("At least one ticket is required")

    with transaction.atomic():
        event = Event.objects.filter(pk=event_id, is_active=True).first()
        if event is None:
            raise NotFoundError("Event not found")

        promo = None
        if promo_code_str:
            normalized = str(promo_code_str).strip().upper()
            # all_objects includes soft-deleted rows; validation below rejects them.
            # On PostgreSQL this locks the row until COMMIT/ROLLBACK.
            locked_promo = (
                PromoCode.all_objects.select_for_update()
                .filter(code=normalized).first()
            )
            result = validate_promo_code(normalized, event.id, total_quantity, promo=locked_promo)
            promo = result["promo"]

        # Sort lock acquisition order to reduce deadlock risk across order requests.
        sections_by_id = {}
        subtotal = 0
        for item in sorted(sections_data, key=lambda section: section["section_id"]):
            section = (
                EventSection.objects.select_for_update()
                .filter(pk=item["section_id"], event_id=event.id).first()
            )
            if section is None:
                raise BadRequestError("Ticket section is not valid for this event")
            if section.capacity - section.reserved < item["quantity"]:
                raise BadRequestError(f"Not enough tickets available in {section.name}")
            sections_by_id[section.id] = (section, item["quantity"])
            subtotal += section.price * item["quantity"]

        totals = calculate_order_totals(subtotal, total_quantity, promo)
        order = Order.objects.create(user=user, event=event, promo_code=promo, **totals)
        for section, quantity in sections_by_id.values():
            Ticket.objects.bulk_create([
                Ticket(order=order, section=section, unit_price=section.price)
                for _ in range(quantity)
            ])
            EventSection.objects.filter(pk=section.pk).update(reserved=F("reserved") + quantity)

        # Payment record created, not charged. A gateway is deliberately out of scope.
        Payment.objects.create(order=order, amount=order.total_amount, status=Payment.PENDING)
        if promo is not None:
            PromoCode.objects.filter(pk=promo.pk).update(current_uses=F("current_uses") + 1)
        return order
