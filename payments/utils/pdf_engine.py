from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.conf import settings
import io
from django.utils import timezone
from decimal import Decimal


def _receipt_number(order_id: int) -> str:
    return f"RCPT-{order_id:06d}"

def build_receipt_pdf(order) -> bytes:
    """
    Assumes:
      - order.user.email
      - order.items.all() yields items with product_name, quantity, unit_price
      - order.paid_at (optional)
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    store_name = getattr(settings, "STORE_NAME", "My Store")

    y = height - 60
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, store_name)
    y -= 26

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Receipt #: {_receipt_number(order.id)}")
    y -= 16
    c.drawString(50, y, f"Order ID: {order.id}")
    y -= 16
    c.drawString(50, y, f"Customer: {order.user.email}")
    y -= 16

    paid_at = getattr(order, "paid_at", None) or timezone.now()
    c.drawString(50, y, f"Paid at: {paid_at.strftime('%Y-%m-%d %H:%M')}")
    y -= 24

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Items")
    y -= 16

    c.setFont("Helvetica", 11)
    total = Decimal("0.00")

    for item in order.items.all():
        line_total = item.quantity * item.price
        total += line_total

        c.drawString(50, y, f"{item.product.name} (x{item.quantity})")
        c.drawRightString(width - 50, y, f"{line_total:.2f}")
        y -= 14

        if y < 120:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Total")
    c.drawRightString(width - 50, y, f"{total:.2f}")

    y -= 40
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Thank you for your purchase!")

    c.showPage()
    c.save()

    buf.seek(0)
    return buf.getvalue()