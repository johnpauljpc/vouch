import io
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

import cloudinary.uploader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from ..models import Receipt


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

import io
import cloudinary.uploader

def upload_pdf_to_cloudinary(pdf_bytes: bytes, order_id: int) -> dict:
    file_obj = io.BytesIO(pdf_bytes)
    file_obj.name = f"receipt-order-{order_id}.pdf"  # helps Cloudinary detect filename/type

    public_id = f"receipt-order-{order_id}-{uuid.uuid4().hex}"

    return cloudinary.uploader.upload(
        file_obj,
        resource_type="raw",
        folder="receipts",
        public_id=public_id,
        overwrite=False,
        access_mode="public",  # important if your account has access control enabled
    )




def send_receipt_email(to_email: str, pdf_bytes: bytes, receipt_url: str):
    subject = "Your payment receipt"
    body = (
        "Hi,\n\n"
        "Your payment was successful. Your receipt is ready:\n"
        f"{receipt_url}\n\n"
        "Thank you for your purchase.\n"
        f"{getattr(settings, 'STORE_NAME', 'My Store')}"
    )

   
    email = EmailMessage(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email])
    email.attach("receipt.pdf", pdf_bytes, "application/pdf") 
    email.send(fail_silently=False)


def generate_upload_and_email_receipt_sync(order):
    receipt, _ = Receipt.objects.get_or_create(
        order=order,
        defaults={"receipt_number": _receipt_number(order.id)},
    )

    if receipt.cloudinary_url and receipt.emailed_at:
        return receipt

    pdf_bytes = None  # cache in memory once

    try:
        if not receipt.cloudinary_url:
            pdf_bytes = build_receipt_pdf(order)
            cloud = upload_pdf_to_cloudinary(pdf_bytes, order.id)

            receipt.cloudinary_url = cloud.get("secure_url", "")
            receipt.cloudinary_public_id = cloud.get("public_id", "")
            receipt.last_error = ""
            receipt.save(update_fields=["cloudinary_url", "cloudinary_public_id", "last_error", "updated_at"])

        if receipt.cloudinary_url and not receipt.emailed_at:
            if pdf_bytes is None:
                pdf_bytes = build_receipt_pdf(order)

            send_receipt_email(order.user.email, pdf_bytes, receipt.cloudinary_url)
            receipt.mark_emailed()

        return receipt

    except Exception as e:
        receipt.last_error = str(e)
        receipt.save(update_fields=["last_error", "updated_at"])
        raise
