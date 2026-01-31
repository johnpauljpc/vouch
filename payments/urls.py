from django.urls import path
from .views import InitiateSquadPaymentView, VerifySquadPaymentView, SquadWebhookView

urlpatterns = [
    path("initiate/", InitiateSquadPaymentView.as_view(), name="squad-initiate"),
    path("verify/", VerifySquadPaymentView.as_view(), name="squad-verify"),
    path("webhook/", SquadWebhookView.as_view(), name="squad-webhook"),
]
