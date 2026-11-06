# IBM Checkout - Assessment

A Django REST API and dashboard for ticket checkout with promo-code validation. Orders, ticket reservations, pending payments, and promo usage are saved in one database transaction.

## Problem statement

A customer buying tickets may apply a promo code. Checkout must validate the code, calculate the correct total, check availability, and create the order. **A failed checkout must leave inventory and promo usage unchanged.**

## Requirements

- Accept existing, non-deleted promos within their validity window and usage limit.
- Match event-specific promos to the selected event; allow global promos.
- Enforce minimum ticket quantity and available inventory.
- Apply fixed or percentage discounts, capped at the configured maximum and ticket subtotal.
- Create the order, tickets, and pending payment together.
- Consume one promo use only when the order succeeds. Validation alone consumes nothing.

## Solution

| Component | Responsibility |
| --- | --- |
| [views.py](apps/core/views.py) | Authentication, HTTP requests, and responses |
| [serializers.py](apps/core/serializers.py) | Request validation and response schemas |
| [promo_service.py](apps/core/services/promo_service.py) | Promo eligibility rules |
| [pricing_service.py](apps/core/services/pricing_service.py) | Fees, discounts, and `Decimal` calculations |
| [order_service.py](apps/core/services/order_service.py) | Checkout transaction and inventory updates |
| [models.py](apps/core/models.py) | Events, sections, promos, orders, tickets, and payments |

```text
Request → Authenticate → Validate input → Begin transaction
  → Check event and promo → Check ticket availability → Calculate total
  → Create order and tickets → Reserve inventory → Create pending payment
  → Increment promo usage → Commit → Return 201
```

An exception inside `transaction.atomic()` rolls back all related database writes. Checkout validates the promo again inside the transaction, even if the customer previously checked it through the validation endpoint.

## Pricing example

For two ₹100 tickets with the 25% `SAVE25` promo:

| Item | Amount |
| --- | ---: |
| Tickets | ₹200 |
| Service fee: ₹12 per ticket | ₹24 |
| Facility fee: ₹5 per ticket | ₹10 |
| Processing fee per order | ₹3 |
| Promo discount | −₹50 |
| **Total** | **₹187** |

## Technical specifications

- Python 3.10+, Django 5.2, Django REST Framework, SQLite.
- OpenAPI schema and locally served Swagger UI via drf-spectacular.
- Django templates, vanilla JavaScript/CSS, Times New Roman, and uppercase interface text.
- Bearer token authentication; order history is restricted to the current user and the latest 30 orders.
- Quantities range from 1 to 20 per section; duplicate sections are rejected.
- Money uses `Decimal`, two decimal places, and `ROUND_HALF_UP`.

Detailed request flow, data model, and configuration: [Technical workflow](docs/WORKFLOW.md).

## Local use

With the project environment active:

```bash
python manage.py runserver 127.0.0.1:8000
```

| Page | URL |
| --- | --- |
| Dashboard | http://127.0.0.1:8000/ |
| Swagger UI | http://127.0.0.1:8000/api/docs/ |
| OpenAPI schema | http://127.0.0.1:8000/api/schema/ |
| Staff administration | http://127.0.0.1:8000/admin/ |

The VS Code launch configuration **IBM Checkout** also starts the server.

Demo data is managed by `python manage.py seed_demo`. The local demo account is `learner` / `Learning@123`; it has no staff access.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/login/` | Return an authentication token |
| GET | `/api/events/` | List active events and available sections |
| POST | `/api/promos/validate/` | Validate a promo without consuming usage |
| POST | `/api/orders/` | Create an order and reserve tickets |
| GET | `/api/orders/` | List the current user's recent orders |

All API operations except login require `Authorization: Bearer <token>`. In Swagger, execute login, copy the returned token, and paste it into **Authorize** without the `Bearer` prefix. Request and response schemas are available in Swagger.

## Validation

```bash
python manage.py check
python manage.py test tests -v 2
```

Coverage and expected responses: [Test matrix](docs/TEST_MATRIX.md).

## Limitations

- Payment is a pending database record; no funds are charged.
- SQLite does not implement the row locks requested by `select_for_update()`. Production concurrency requires a database such as PostgreSQL and dedicated concurrency tests.
- Tokens have no expiry or rotation. Production also requires HTTPS, managed secrets, checkout idempotency, and payment reconciliation.
- Browser totals are estimates; backend calculations are authoritative.
