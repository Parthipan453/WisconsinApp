"""Stripe Checkout integration for application fee payments."""

import stripe
from django.conf import settings

from ..models import Application, FeePayment


class StripePaymentError(Exception):
    """Raised when a Stripe operation fails."""


def _configure() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise StripePaymentError(
            "Stripe is not configured. Set STRIPE_SECRET_KEY in the environment."
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(
    application: Application,
    payment: FeePayment,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """Create a Stripe Checkout Session for an application fee payment.

    `success_url` and `cancel_url` should include the literal
    `{CHECKOUT_SESSION_ID}` placeholder so Stripe injects the session id.
    """
    _configure()
    try:
        return stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": payment.currency.lower(),
                        "product_data": {
                            "name": f"Application Fee — {application.Reference_id}",
                        },
                        "unit_amount": int(payment.amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            customer_email=application.applicant.email,
            client_reference_id=application.Reference_id,
            metadata={
                "application_id": str(application.application_id),
                "payment_id": str(payment.id),
                "reference_id": application.Reference_id,
            },
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as exc:
        raise StripePaymentError(f"Stripe error: {exc}") from exc


def retrieve_checkout_session(session_id: str) -> stripe.checkout.Session:
    _configure()
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as exc:
        raise StripePaymentError(f"Stripe error: {exc}") from exc


def verify_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify a Stripe webhook signature and return the parsed event."""
    secret = settings.STRIPE_WEBHOOK_SECRET
    if not secret:
        raise StripePaymentError("Stripe webhook secret is not configured.")
    try:
        return stripe.Webhook.construct_event(payload, sig_header, secret)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise StripePaymentError(f"Stripe webhook verification failed: {exc}") from exc
