"""
Payment handling utilities for the Travel App.
This module contains functions for Stripe payment integration.
"""

import stripe
from flask import current_app
from app.models import Booking, BookingStatus
from app import db
from app.utils import send_booking_confirmation_email


def initialize_stripe():
    """Initialize Stripe with the secret key."""
    stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")


def create_payment_intent(booking):
    """
    Create a Stripe Payment Intent for a booking.

    Args:
        booking (Booking): The booking object

    Returns:
        dict: Payment intent response or None if failed
    """
    try:
        initialize_stripe()

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(booking.total_amount * 100),  # Convert to cents
            currency="usd",
            metadata={
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "user_id": booking.user_id,
                "tour_id": booking.tour_id,
            },
            description=f"Booking for {booking.tour.title} - {booking.booking_reference}",
        )

        # Store payment intent ID
        booking.stripe_payment_intent_id = intent.id
        booking.payment_method = "stripe"
        db.session.commit()

        return intent

    except Exception as e:
        current_app.logger.error(f"Failed to create payment intent: {str(e)}")
        return None


def confirm_payment(payment_intent_id):
    """
    Confirm a payment and update booking status.

    Args:
        payment_intent_id (str): Stripe Payment Intent ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        initialize_stripe()

        # Retrieve payment intent
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status == "succeeded":
            # Find booking by payment intent ID
            booking = Booking.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if booking:
                # Update booking status
                booking.status = BookingStatus.CONFIRMED
                booking.payment_status = "paid"
                booking.payment_date = db.func.now()
                db.session.commit()

                # Send confirmation email
                try:
                    send_booking_confirmation_email(booking)
                except Exception as e:
                    current_app.logger.error(
                        f"Failed to send confirmation email: {str(e)}"
                    )

                return True

        return False

    except Exception as e:
        current_app.logger.error(f"Failed to confirm payment: {str(e)}")
        return False


def process_refund(booking, amount=None):
    """
    Process a refund for a cancelled booking.

    Args:
        booking (Booking): The booking object
        amount (float, optional): Refund amount (defaults to full amount)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        initialize_stripe()

        if not booking.stripe_payment_intent_id:
            return False

        # Get payment intent
        intent = stripe.PaymentIntent.retrieve(booking.stripe_payment_intent_id)

        if intent.status == "succeeded":
            # Create refund
            refund_amount = int(
                (amount or booking.total_amount) * 100
            )  # Convert to cents

            refund = stripe.Refund.create(
                payment_intent=booking.stripe_payment_intent_id,
                amount=refund_amount,
                metadata={
                    "booking_id": booking.id,
                    "booking_reference": booking.booking_reference,
                },
            )

            # Update booking
            booking.payment_status = "refunded"
            booking.refund_amount = refund_amount / 100  # Convert back to dollars
            db.session.commit()

            return True

        return False

    except Exception as e:
        current_app.logger.error(f"Failed to process refund: {str(e)}")
        return False


def simulate_payment_for_development(booking):
    """
    Simulate payment for development environment.

    Args:
        booking (Booking): The booking object

    Returns:
        bool: Always returns True for simulation
    """
    try:
        # Simulate successful payment
        booking.status = BookingStatus.CONFIRMED
        booking.payment_status = "paid"
        booking.payment_method = "simulated"
        booking.payment_date = db.func.now()
        db.session.commit()

        # Send confirmation email
        try:
            send_booking_confirmation_email(booking)
        except Exception as e:
            current_app.logger.error(f"Failed to send confirmation email: {str(e)}")

        current_app.logger.info(
            f"Simulated payment for booking {booking.booking_reference}"
        )
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to simulate payment: {str(e)}")
        return False
