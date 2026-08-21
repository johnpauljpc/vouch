import uuid
import hmac
import hashlib
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema,OpenApiParameter, OpenApiTypes
from .models import Order, Payment
from .serializers import InitiateSquadPaymentSerializer
from .utils.squad_client import squad_initiate_payment, squad_verify_transaction


def _verify_squad_signature(raw_body: bytes, signature: str) -> bool:
    """HMAC-SHA512 of the raw request body, uppercase hex, per SQUAD docs."""
    expected = hmac.new(
        settings.SQUAD_SECRET_KEY.encode(), raw_body, hashlib.sha512
    ).hexdigest().upper()
    return hmac.compare_digest(signature.upper(), expected)


def _apply_verified_transaction(payment, tx: dict):
    """Applies a verified SQUAD transaction payload to the payment + order."""
    tx_status = (tx.get("transaction_status") or "").lower()
    order = payment.order

    with transaction.atomic():
        if tx_status == "success":
            payment.status = "success"
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at"])

            order.is_paid = True
            order.status = "paid"
            order.save(update_fields=["is_paid", "status"])

            return "success", "paid"

        payment.status = "failed" if tx_status in ("failed", "abandoned") else "pending"
        payment.paid_at = None
        payment.save(update_fields=["status", "paid_at"])

        if not order.is_paid and order.status != "cancelled":
            order.status = "pending"
            order.save(update_fields=["status"])

        return payment.status, order.status


class InitiateSquadPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=InitiateSquadPaymentSerializer)
    def post(self, request):
        ser = InitiateSquadPaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        order = get_object_or_404(Order, id=ser.validated_data["order_id"], user=request.user)

        if order.is_paid or order.status == "paid":
            return Response({"detail": "Order already paid."}, status=status.HTTP_400_BAD_REQUEST)

        # amount must be in kobo
        amount_kobo = int(Decimal(order.total_amount) * 100)

        # unique reference for each attempt
        reference = f"SQ_ORDER_{order.id}_{uuid.uuid4().hex[:10]}"

        # Payment is OneToOne; we reuse it on retries
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "reference": reference,
                "amount": order.total_amount,
                "status": "pending",
            },
        )
        if not created:
            payment.reference = reference
            payment.amount = order.total_amount
            payment.status = "pending"
            payment.paid_at = None
            payment.save(update_fields=["reference", "amount", "status", "paid_at"])

        customer_name = getattr(request.user, "get_full_name", lambda: "")() or getattr(request.user, "email", "")

        code, data = squad_initiate_payment(
            email=request.user.email,
            amount_kobo=amount_kobo,
            transaction_ref=payment.reference,
            customer_name=customer_name,
        )

        # Typical response shape: { success: true, data: { checkout_url: ... } }
        if code not in (200, 201) or not data.get("success"):
            return Response(
                {"detail": "SQUAD initiation failed.", "squad": data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        checkout_url = (data.get("data") or {}).get("checkout_url")
        if not checkout_url:
            return Response(
                {"detail": "SQUAD did not return checkout_url.", "squad": data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "order_id": order.id,
                "reference": payment.reference,
                "amount": str(payment.amount),
                "checkout_url": checkout_url,
            },
            status=status.HTTP_201_CREATED,
        )




class VerifySquadPaymentView(APIView):
    permission_classes = [IsAuthenticated]


    @extend_schema(
            parameters=[
                 OpenApiParameter( name="reference", description="Order reference code (alternative to pk lookup)", required=False, type=str, location=OpenApiParameter.QUERY, ),
        ]
            
    )
    def get(self, request):
        reference = request.query_params.get("reference")
        if not reference:
            return Response({"detail": "reference is required."}, status=status.HTTP_400_BAD_REQUEST)

        payment = get_object_or_404(Payment, reference=reference)

        # Ensure user owns the order
        if payment.order.user_id != request.user.id:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        code, data = squad_verify_transaction(reference)
        if code != 200 or not data.get("success"):
            return Response({"detail": "SQUAD verify failed.", "squad": data}, status=status.HTTP_400_BAD_REQUEST)

        tx = data.get("data") or {}
        payment_status, order_status = _apply_verified_transaction(payment, tx)
        order = payment.order

        if payment_status == "success":
            return Response(
                {
                    "detail": "Payment verified successfully.",
                    "reference": payment.reference,
                    "payment_status": payment.status,
                    "order_id": order.id,
                    "order_status": order.status,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "detail": "Payment not successful yet.",
                "reference": payment.reference,
                "transaction_status": tx.get("transaction_status"),
                "payment_status": payment.status,
                "order_id": order.id,
                "order_status": order.status,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT},
    methods=["GET", "POST"],
    parameters=[
        OpenApiParameter(
            name="reference",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description="SQUAD transaction reference returned on redirect (GET).",
        ),
        OpenApiParameter(
            name="x-squad-encrypted-body",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=False,
            description="HMAC SHA512 of raw request body using SQUAD secret key (uppercase hex)."
        )
    ],
)
@api_view(["GET", "POST"])
def payment_callback(request):
    """
    Server-side SQUAD callback (browser redirect or webhook).

    Verifies the transaction with SQUAD before marking the payment/order as
    paid - never trusts the client.
    """
    if request.method == "GET":
        transaction_id = request.query_params.get("reference")
    else:
        transaction_id = (request.data or {}).get("reference")

    if not transaction_id:
        return Response(
            {"error": "Missing reference."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.method == "POST":
        signature = request.headers.get("x-squad-encrypted-body")
        if signature and not _verify_squad_signature(request.body, signature):
            return Response(
                {"error": "Invalid signature."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    payment = Payment.objects.filter(reference=transaction_id).first()
    if not payment:
        return Response(
            {"error": "Payment not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    code, data = squad_verify_transaction(transaction_id)
    if code != 200 or not data.get("success"):
        return Response(
            {"detail": "SQUAD verification failed.", "squad": data},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    _apply_verified_transaction(payment, data.get("data") or {})

    if request.method == "GET" and settings.FRONTEND_URL:
        result = "success" if payment.status == "success" else "failed"
        return redirect(
            f"{settings.FRONTEND_URL}/payment/result"
            f"?status={result}&reference={transaction_id}"
        )

    return Response(
        {
            "message": "Thank you for your payment, it will be verified.",
            "transaction_id": transaction_id,
            "status": payment.status,
            "amount": str(payment.amount),
        },
        status=status.HTTP_200_OK,
    )
