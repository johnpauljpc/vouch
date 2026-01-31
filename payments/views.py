import uuid
import hmac
import hashlib
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema,OpenApiParameter, OpenApiTypes
from .models import Order, Payment
from .serializers import InitiateSquadPaymentSerializer
from .squad_client import squad_initiate_payment, squad_verify_transaction



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
        tx_status = (tx.get("transaction_status") or "").lower()  # e.g. Success / Failed / Pending / Abandoned
        order = payment.order

        with transaction.atomic():
            if tx_status == "success":
                payment.status = "success"
                payment.paid_at = timezone.now()
                payment.save(update_fields=["status", "paid_at"])

                order.is_paid = True
                order.status = "paid"
                order.save(update_fields=["is_paid", "status"])

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

            # For failed/abandoned/pending: keep order pending so user can retry
            payment.status = "failed" if tx_status in ("failed", "abandoned") else "pending"
            payment.paid_at = None
            payment.save(update_fields=["status", "paid_at"])

            if not order.is_paid and order.status != "cancelled":
                order.status = "pending"
                order.save(update_fields=["status"])

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
    parameters=[
        OpenApiParameter(
            name="x-squad-encrypted-body",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=True,
            description="HMAC SHA512 of raw request body using SQUAD secret key (uppercase hex)."
        )
    ],
)
class SquadWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        header_hash = request.META.get("HTTP_X_SQUAD_ENCRYPTED_BODY")
        if not header_hash:
            return Response({"detail": "Missing x-squad-encrypted-body."}, status=status.HTTP_400_BAD_REQUEST)

        # Compute HMAC SHA512 of raw payload with your secret key (uppercase hex)
        computed = hmac.new(
            key=settings.SQUAD_SECRET_KEY.encode("utf-8"),
            msg=request.body,
            digestmod=hashlib.sha512,
        ).hexdigest().upper()

        if not hmac.compare_digest(computed, header_hash.upper()):
            return Response({"detail": "Invalid webhook signature."}, status=status.HTTP_400_BAD_REQUEST)

        event = request.data
        body = event.get("Body") or {}
        tx_ref = body.get("transaction_ref") or event.get("TransactionRef")
        tx_status = (body.get("transaction_status") or "").lower()  # "Success"

        if not tx_ref:
            return Response({"detail": "Missing transaction_ref."}, status=status.HTTP_400_BAD_REQUEST)

        payment = get_object_or_404(Payment, reference=tx_ref)
        order = payment.order

        # Idempotency: if already success, do nothing (avoids double value)
        if payment.status == "success" and order.is_paid:
            return Response(
                {"response_code": 200, "transaction_reference": tx_ref, "response_description": "Already processed"},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            if tx_status == "success":
                payment.status = "success"
                payment.paid_at = timezone.now()
                payment.save(update_fields=["status", "paid_at"])

                order.is_paid = True
                order.status = "paid"
                order.save(update_fields=["is_paid", "status"])
            else:
                # If you receive non-success webhook, mark failed/pending as you prefer
                payment.status = "failed"
                payment.paid_at = None
                payment.save(update_fields=["status", "paid_at"])

                if order.status != "cancelled":
                    order.is_paid = False
                    order.status = "pending"
                    order.save(update_fields=["is_paid", "status"])

        # Squad expects a 200 response acknowledging receipt (see docs examples)
        return Response(
            {"response_code": 200, "transaction_reference": tx_ref, "response_description": "Success"},
            status=status.HTTP_200_OK,
        )






@api_view(['GET'])
def payment_callback(request):
    """
    Handle payment gateway callback using DRF.
    """
    # Extract data from JSON body or form data
    transaction_id = request.GET.get("reference")
    print(">>>>>>>>>>  ", transaction_id)
    payment = Payment.objects.filter(reference = transaction_id).first()
    print(">>>>>>>>>>  ", payment)
    status_value = payment.status
    amount = payment.amount



    if not transaction_id:
        return Response(
            {"error": "Missing transaction_id"},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "message": "Thank You for your payment, it will be verified",
        "transaction_id": transaction_id,
        "status": status_value,
        "amount": amount,
    }, status=status.HTTP_200_OK)
