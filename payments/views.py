import uuid
import requests
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from jobs.models import Job
from payments.models import Payment


class InitiatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id=None):
        # Accept job_id from either URL param or request body
        target_job_id = job_id or request.data.get("job_id") or request.data.get("job")
        if not target_job_id:
            return Response({"detail": "job_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        job = get_object_or_404(Job, id=target_job_id)

        if request.user.role != "admin" and job.employer != request.user:
            return Response({"detail": "You can only feature your own jobs."}, status=status.HTTP_403_FORBIDDEN)

        if job.is_featured:
            return Response({"detail": "This job is already featured."}, status=status.HTTP_400_BAD_REQUEST)

        tran_id = f"TB-{job.id}-{uuid.uuid4().hex[:8].upper()}"
        amount = 500.00

        payment = Payment.objects.create(
            user=request.user,
            job=job,
            tran_id=tran_id,
            amount=amount,
            status="PENDING",
        )

        init_url = (
            "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            if settings.SSL_IS_SANDBOX
            else "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
        )

        backend_base = settings.BACKEND_URL.rstrip("/")
        cus_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email

        payload = {
            "store_id": settings.SSL_STORE_ID,
            "store_passwd": settings.SSL_STORE_PASS,
            "total_amount": f"{amount:.2f}",
            "currency": "BDT",
            "tran_id": tran_id,
            "success_url": f"{backend_base}/api/v1/payments/success/",
            "fail_url": f"{backend_base}/api/v1/payments/fail/",
            "cancel_url": f"{backend_base}/api/v1/payments/cancel/",
            "ipn_url": f"{backend_base}/api/v1/payments/ipn/",
            "cus_name": cus_name,
            "cus_email": request.user.email,
            "cus_add1": request.user.address or "Dhaka, Bangladesh",
            "cus_city": "Dhaka",
            "cus_postcode": "1200",
            "cus_country": "Bangladesh",
            "cus_phone": request.user.phone_number or "01700000000",
            "shipping_method": "NO",
            "num_of_item": 1,
            "product_name": f"Feature Job #{job.id} - {job.title[:30]}",
            "product_category": "Job Portal Service",
            "product_profile": "non-physical-goods",
            "value_a": str(job.id),
            "value_b": str(request.user.id),
        }

        try:
            res = requests.post(init_url, data=payload, timeout=15)
            res_data = res.json()
        except Exception as e:
            payment.status = "FAILED"
            payment.save(update_fields=["status"])
            return Response(
                {"detail": "Could not connect to SSLCommerz.", "error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if res_data.get("status") == "SUCCESS" and res_data.get("GatewayPageURL"):
            return Response(
                {
                    "payment_url": res_data["GatewayPageURL"],
                    "GatewayPageURL": res_data["GatewayPageURL"],
                    "tran_id": tran_id,
                },
                status=status.HTTP_200_OK,
            )

        payment.status = "FAILED"
        payment.save(update_fields=["status"])
        return Response(
            {
                "detail": res_data.get("failedreason", "SSLCommerz initialization failed."),
                "ssl_response": res_data,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@method_decorator(csrf_exempt, name="dispatch")
class PaymentSuccessView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.POST or request.data
        tran_id = data.get("tran_id")
        val_id = data.get("val_id")
        job_id_fallback = data.get("value_a")
        frontend_url = settings.FRONTEND_URL.rstrip("/")

        payment = Payment.objects.filter(tran_id=tran_id).select_related("job").first()

        # Validate with SSLCommerz validation server
        val_url = (
            "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
            if settings.SSL_IS_SANDBOX
            else "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"
        )
        params = {
            "val_id": val_id,
            "store_id": settings.SSL_STORE_ID,
            "store_passwd": settings.SSL_STORE_PASS,
            "format": "json",
        }

        is_valid = False
        try:
            if val_id:
                val_res = requests.get(val_url, params=params, timeout=15).json()
                if val_res.get("status") in ["VALID", "VALIDATED"]:
                    is_valid = True
            elif data.get("status") == "VALID":
                is_valid = True
        except Exception:
            # In sandbox, if SSLCommerz POSTed status=VALID directly
            if data.get("status") == "VALID":
                is_valid = True

        if is_valid:
            if payment:
                payment.status = "COMPLETED"
                payment.val_id = val_id
                payment.save(update_fields=["status", "val_id"])
                if payment.job:
                    payment.job.is_featured = True
                    payment.job.save(update_fields=["is_featured"])
                    return redirect(f"{frontend_url}/dashboard/employer/my-jobs?payment=success&job={payment.job.id}")
            elif job_id_fallback:
                Job.objects.filter(id=job_id_fallback).update(is_featured=True)
                return redirect(f"{frontend_url}/dashboard/employer/my-jobs?payment=success&job={job_id_fallback}")

        if payment:
            payment.status = "FAILED"
            payment.save(update_fields=["status"])
        return redirect(f"{frontend_url}/dashboard/employer/my-jobs?payment=failed")


@method_decorator(csrf_exempt, name="dispatch")
class PaymentFailView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        tran_id = (request.POST or request.data).get("tran_id")
        if tran_id:
            Payment.objects.filter(tran_id=tran_id).update(status="FAILED")
        return redirect(f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/employer/my-jobs?payment=failed")


@method_decorator(csrf_exempt, name="dispatch")
class PaymentCancelView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        tran_id = (request.POST or request.data).get("tran_id")
        if tran_id:
            Payment.objects.filter(tran_id=tran_id).update(status="CANCELLED")
        return redirect(f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/employer/my-jobs?payment=cancelled")