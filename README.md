# Vouch — E-Commerce Receipt Generator

An e-commerce backend that automatically generates professional digital receipts after a successful order. Once payment is confirmed, the system generates a PDF receipt, emails it to the customer, and uploads a copy to Cloudinary for record-keeping.

## Tech Stack

- **Backend:** Django 6, Django REST Framework, JWT auth (SimpleJWT)
- **Payments:** SQUAD payment gateway
- **Storage/Email:** Cloudinary, Resend (SMTP)
- **Receipts:** ReportLab (PDF)
- **Deploy:** Render (Postgres, ASGI)

## Project Structure

```
├── backend/                 # Django project
│   ├── config/              # Project settings (renamed from vouch)
│   ├── users/               # Auth (register, profile)
│   ├── products/            # Products + admin CRUD
│   ├── cart/                # Cart & cart items
│   ├── orders/              # Addresses, checkout, orders
│   └── payments/            # SQUAD integration, PDF receipts
├── frontend/                # (placeholder) React SPA
└── render.yaml              # Render blueprint (workingDir: backend)
```

## Getting Started

```bash
cd backend
python -m venv env && source env/bin/activate
pip install -r requirements.txt
# create a .env with the vars below
python manage.py migrate
python manage.py runserver
```

**Required env vars** (see `backend/config/settings.py`):

```
SECRET_KEY, DEBUG, DATABASE_URL
CLOUD_NAME, API_KEY, API_SECRET        # Cloudinary
RESEND_API_KEY, DEFAULT_FROM_EMAIL     # Resend email
SQUAD_SECRET_KEY, SQUAD_BASE_URL, SQUAD_CURRENCY
```

Interactive API docs are served at `/` (Swagger UI) and the OpenAPI schema at `/api/schema/`.

---

## API Reference

Base URL: `http://localhost:8000` (dev) — deployed URL in production.

Authentication uses **Bearer tokens** (`Authorization: Bearer <access_token>`). Most endpoints require the user to be logged in.

### Auth

| Method | Endpoint | Auth | Body | Description |
|--------|----------|------|------|-------------|
| POST | `/api/auth/register/` | No | `{ "email": "a@b.com", "password": "..." }` | Create account. `username` is auto-generated from the email prefix. |
| GET | `/api/auth/profile/` | Yes | — | Returns `{ id, username, email }` |
| POST | `/api/auth/token/` | No | `{ "email": "a@b.com", "password": "..." }` | Login → `{ access, refresh }` |
| POST | `/api/auth/token/refresh/` | No | `{ "refresh": "..." }` | Refresh access token |

### Products

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/products/list-create/` | No | List available products (superusers see all) |
| POST | `/api/products/list-create/` | Admin | Create product: `{ name, price, stock, description?, image? }` |
| GET | `/api/products/<id>/` | No | Product detail |
| PUT/PATCH/DELETE | `/api/products/<id>/` | Admin | Update / delete product |

### Cart

| Method | Endpoint | Auth | Body | Description |
|--------|----------|------|------|-------------|
| GET | `/api/cart/` | Yes | — | Get/create cart with items + `total` |
| POST | `/api/cart/items/` | Yes | `{ "product": <id>, "quantity": <n> }` | Add to cart (validates stock) |
| GET | `/api/cart/item/<id>/` | Yes | — | Get a cart item |
| PUT | `/api/cart/item/<id>/` | Yes | `{ "quantity": <n> }` | Update quantity (validates stock) |
| DELETE | `/api/cart/item/<id>/` | Yes | — | Remove item |
| DELETE | `/api/cart/clear/` | Yes | — | Clear the whole cart |

### Addresses

| Method | Endpoint | Auth | Body | Description |
|--------|----------|------|------|-------------|
| GET | `/api/addresses/` | Yes | — | List the user's addresses |
| POST | `/api/addresses/` | Yes | `{ full_name, phone, address, city, state, country? }` | Create address |
| GET/PUT/PATCH/DELETE | `/api/addresses/<id>/` | Yes | — | Retrieve / update / delete address |

### Orders

| Method | Endpoint | Auth | Body | Description |
|--------|----------|------|------|-------------|
| POST | `/api/checkout/` | Yes | `{ "shipping_address_id": <id> }` | Convert cart → order. Snapshots prices, **decrements stock**, clears cart. |
| GET | `/api/orders/` | Yes | — | List the user's orders (with items + address) |
| GET | `/api/orders/<id>/` | Yes | — | Order detail |
| PATCH | `/api/orders/cancel/<id>/` | Yes | `{}` | Cancel a pending, unpaid order (**restores stock**) |
| PATCH | `/api/orders/update-status/<id>/` | Admin | `{ "status": "paid" }` | Set status: `pending`/`paid`/`delivered`/`cancelled`/`failed` |

### Payments (SQUAD)

| Method | Endpoint | Auth | Body | Description |
|--------|----------|------|------|-------------|
| POST | `/api/payments/initiate/` | Yes | `{ "order_id": <id> }` | Initiate payment → returns `{ reference, checkout_url }` |
| GET | `/api/payments/verify/?reference=<ref>` | Yes | — | Verify a transaction server-side; marks order paid on success |
| GET/POST | `/api/payments/callback/` | No | — | SQUAD callback. Verifies the transaction before marking paid (HMAC-checked). |

### Payment flow

1. Checkout → creates a `pending` order.
2. `POST /api/payments/initiate/` → get `checkout_url`, redirect the customer to SQUAD.
3. SQUAD redirects back to the callback URL; the backend verifies the transaction server-side.
4. The frontend confirms with `GET /api/payments/verify/?reference=...`.
5. On success the `Payment` signal triggers receipt generation (PDF → Cloudinary → email).

## Useful Commands

```bash
python manage.py retry_receipts   # Retry receipts that failed email/upload
python manage.py collectstatic    # Before deploy (WhiteNoise)
```

## Deployment (Render)

`render.yaml` at the repo root runs the service inside `backend/` (`workingDir: backend`). Set all env vars listed above in the Render dashboard. The free tier spins down when idle — a UptimeRobot 5-minute ping keeps it warm.
