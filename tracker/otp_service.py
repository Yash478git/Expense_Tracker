import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from .models import EmailOTP


OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


def generate_otp():
    """
    Generate a secure 6-digit OTP.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def send_otp(email, purpose, user=None):
    """
    Generate, hash, store, and email an OTP.

    Returns:
        tuple: (success, message)
    """
    email = email.strip().lower()

    now = timezone.now()

    # Prevent OTP spam.
    recent_otp = (
        EmailOTP.objects
        .filter(
            email=email,
            purpose=purpose,
            is_used=False,
            created_at__gte=now - timedelta(
                seconds=OTP_RESEND_COOLDOWN_SECONDS
            ),
        )
        .order_by("-created_at")
        .first()
    )

    if recent_otp:
        return (
            False,
            "Please wait before requesting another OTP."
        )

    # Invalidate older unused OTPs for the same purpose.
    EmailOTP.objects.filter(
        email=email,
        purpose=purpose,
        is_used=False,
    ).update(
        is_used=True
    )

    otp = generate_otp()

    EmailOTP.objects.create(
        user=user,
        email=email,
        otp_hash=make_password(otp),
        purpose=purpose,
        expires_at=now + timedelta(
            minutes=OTP_EXPIRY_MINUTES
        ),
    )

    purpose_labels = {
        "registration": "registration",
        "password_change": "password change",
        "password_reset": "password reset",
    }

    purpose_label = purpose_labels.get(
        purpose,
        "account verification"
    )

    send_mail(
        subject="Expense Tracker - Your OTP",
        message=(
            f"Your Expense Tracker OTP for "
            f"{purpose_label} is: {otp}\n\n"
            f"This OTP will expire in "
            f"{OTP_EXPIRY_MINUTES} minutes.\n\n"
            "Do not share this OTP with anyone."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return (
        True,
        "OTP sent successfully."
    )


def verify_otp(email, purpose, otp):
    """
    Verify the latest valid OTP.

    Returns:
        tuple: (success, message, otp_record)
    """
    email = email.strip().lower()
    otp = otp.strip()

    otp_record = (
        EmailOTP.objects
        .filter(
            email=email,
            purpose=purpose,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if not otp_record:
        return (
            False,
            "Invalid or expired OTP.",
            None,
        )

    now = timezone.now()

    if otp_record.expires_at <= now:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])

        return (
            False,
            "This OTP has expired.",
            None,
        )

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])

        return (
            False,
            "Too many incorrect attempts. Request a new OTP.",
            None,
        )

    if not check_password(
        otp,
        otp_record.otp_hash
    ):
        otp_record.attempts += 1
        otp_record.save(
            update_fields=["attempts"]
        )

        remaining = max(
            OTP_MAX_ATTEMPTS - otp_record.attempts,
            0,
        )

        return (
            False,
            f"Incorrect OTP. {remaining} attempt(s) remaining.",
            None,
        )

    otp_record.is_used = True
    otp_record.save(
        update_fields=["is_used"]
    )

    return (
        True,
        "OTP verified successfully.",
        otp_record,
    )