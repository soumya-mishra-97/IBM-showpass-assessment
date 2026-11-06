# Scenario-to-Test Matrix

Checkout and authentication scenarios covered by the project's Django tests.

| ID | Scenario / problem | Expected HTTP | Why it matters / exact behavior | Test |
|---|---|---|---|---|
| 01 | Nonexistent promo | 404 | `Promo code not found` | `test_01_missing_promo_returns_404` |
| 02 | Soft-deleted promo | 404 | Do not expose deleted codes to customers | `test_02_soft_deleted_promo_returns_404` |
| 03 | Validity starts tomorrow | 400 | `Promo code is not yet valid` | `test_03_not_yet_valid_returns_400` |
| 04 | Promo expiry passed | 400 | `Promo code has expired` | `test_04_expired_promo_returns_400` |
| 05 | `current_uses >= max_uses` | 400 | `Promo code usage limit reached` | `test_05_exhausted_promo_returns_400` |
| 06 | Promo linked to another event | 400 | **Exact:** `Promo code is not valid for this event` | `test_06_wrong_event_message_exact` |
| 07 | Two tickets but minimum is three | 400 | `Minimum 3 tickets required for this promo code` | `test_07_minimum_ticket_quantity` |
| 08 | Valid 25% promo, 2 × ₹100 | 201 | Discount ₹50, total ₹187, one usage increment | `test_08_order_201_correct_amount_and_usage` |
| 09 | Validate without buying | 200 | Usage remains unchanged | `test_09_promo_validation_alone_does_not_consume_code` |
| 10 | Fixed discount ₹500 vs subtotal ₹200 | 201 | Cap discount at ₹200, total ₹37 | `test_10_fixed_discount_is_capped_at_subtotal` |
| 11 | Percentage discount limited by max ₹20 | 201 | Total ₹217 | `test_11_max_discount_cap` |
| 12 | Not enough ticket inventory | 400 | No order, no promo used | `test_12_insufficient_inventory_does_not_consume_promo` |
| 13 | Global promo (`event=None`) | 200 | Valid across events | `test_13_global_promo_allowed_for_both_events` |
| 14 | Invalid promo during checkout | 404 | No payment record | `test_14_invalid_promo_does_not_create_payment` |
| 15 | Simulated failure during payment creation | N/A service exception | Roll back order, tickets, reserved counts, usage | `test_15_payment_failure_rolls_back_everything` |
| 16 | Same section repeated in request | 400 | Prevent double counting or oversell | `test_16_duplicate_section_rejected` |
| 17 | Unknown event | 404 | Proper resource error | `test_17_unknown_event_rejected` |
| Auth | Missing Bearer token | 401 | No anonymous access | `tests/test_auth.py` |

## Example calculation

`2 × ₹100 = ₹200 subtotal`

`2 × ₹12 service = ₹24`

`2 × ₹5 facility = ₹10`

`₹3 order-level processing fee`

`25% × ₹200 = ₹50 discount`

`Final = ₹200 + ₹24 + ₹10 + ₹3 − ₹50 = ₹187`

Fees are defined in `apps/core/services/pricing_service.py`.

## Pricing unit tests

`tests/test_pricing.py` checks the percentage discount, fixed discount subtotal cap, maximum discount cap, no-promo discount, and no-promo total without database access.

## Run

```bash
python manage.py test tests -v 2
```
