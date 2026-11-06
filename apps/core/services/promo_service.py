"""Promo validation business rules. Service accepts plain inputs, not HTTP objects."""
from django.utils import timezone
from apps.core.models import PromoCode
from apps.core.utils.exceptions import BadRequestError, NotFoundError


def validate_promo_code(code, event_id, quantity, *, promo=None):
    """Return {'valid': True, 'promo': PromoCode} or raise 400/404.

    The optional promo argument is used by order_service after acquiring a
    database row lock. Never call this with an untrusted caller-supplied object.
    """
    normalized = str(code or "").strip().upper()
    if not normalized:
        raise NotFoundError("Promo code not found")

    if promo is None:
        promo = PromoCode.objects.filter(code=normalized).first()

    if promo is None or promo.deleted_at is not None or promo.code != normalized:
        raise NotFoundError("Promo code not found")

    now = timezone.now()
    if now < promo.valid_from:
        raise BadRequestError("Promo code is not yet valid")
    if now > promo.valid_to:
        raise BadRequestError("Promo code has expired")
    if promo.current_uses >= promo.max_uses:
        raise BadRequestError("Promo code usage limit reached")
    if promo.event_id is not None and promo.event_id != event_id:
        # Exact wording matters for the scenario test.
        raise BadRequestError("Promo code is not valid for this event")
    if quantity < promo.min_tickets:
        raise BadRequestError(f"Minimum {promo.min_tickets} tickets required for this promo code")
    return {"valid": True, "promo": promo}
