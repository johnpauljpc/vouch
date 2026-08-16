from django.urls import path
from .views import InitiateSquadPaymentView, VerifySquadPaymentView, payment_callback

urlpatterns = [
    path("initiate/", InitiateSquadPaymentView.as_view(), name="squad-initiate"),
    path("verify/", VerifySquadPaymentView.as_view(), name="squad-verify"),
    # path("webhook/", SquadWebhookView.as_view(), name="squad-webhook"),
    path("callback/", view=payment_callback),
]
