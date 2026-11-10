from django.urls import path
from payments.views import (
    InitiatePaymentView,
    PaymentSuccessView,
    PaymentFailView,
    PaymentCancelView,
)

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="payment-initiate-body"),
    path("initiate/<int:job_id>/", InitiatePaymentView.as_view(), name="payment-initiate"),
    path("success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("fail/", PaymentFailView.as_view(), name="payment-fail"),
    path("cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
    path("ipn/", PaymentSuccessView.as_view(), name="payment-ipn"),
]