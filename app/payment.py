"""
Payment handling utilities for the Travel App.
This module contains functions for payment simulation.
"""

from flask import current_app
from app.models import Booking, BookingStatus, PaymentStatus
from app import db
from app.utils import send_booking_confirmation_email
from datetime import datetime

# Force simulation mode
FORCE_SIMULATE_PAYMENT = True


def simulate_payment_for_development(booking):
    """Simulate a successful payment for development/demo purposes."""
    try:
        # Update booking status
        booking.status = BookingStatus.CONFIRMED
        booking.payment_status = PaymentStatus.COMPLETED
        booking.payment_method = "Demo Payment"
        booking.payment_date = datetime.utcnow()
        booking.stripe_payment_intent_id = f"sim_{booking.booking_reference}"
        # Update tour revenue instantly
        tour = booking.tour
        if tour:
            tour.total_revenue += booking.total_amount
            db.session.add(tour)
        db.session.commit()

        # Send confirmation email
        try:
            send_booking_confirmation_email(booking)
        except Exception as e:
            current_app.logger.error(f"Failed to send confirmation email: {str(e)}")

        current_app.logger.info(
            f"Simulated payment successful for booking {booking.booking_reference}"
        )
        return True

    except Exception as e:
        current_app.logger.error(f"Payment simulation failed: {str(e)}")
        db.session.rollback()
        return False


def create_payment_intent(booking):
    """Create a simulated payment intent."""
    try:

        class SimulatedIntent:
            def __init__(self, booking):
                self.id = f"sim_{booking.booking_reference}"
                self.client_secret = "sim_secret_123"
                self.amount = int(booking.total_amount * 100)
                self.currency = "usd"
                self.status = "requires_payment_method"

        intent = SimulatedIntent(booking)
        booking.stripe_payment_intent_id = intent.id
        db.session.commit()
        return intent
    except Exception as e:
        current_app.logger.error(f"Failed to create payment intent: {str(e)}")
        return None


def confirm_payment(payment_intent_id):
    """Confirm a simulated payment."""
    try:
        booking = Booking.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        if not booking:
            current_app.logger.error(
                f"No booking found for payment {payment_intent_id}"
            )
            return False
        return simulate_payment_for_development(booking)
    except Exception as e:
        current_app.logger.error(f"Payment confirmation failed: {str(e)}")
        return False


def process_refund(booking, amount=None):
    """Simulate a refund process."""
    try:
        if not booking.stripe_payment_intent_id:
            return False
        booking.status = BookingStatus.CANCELLED
        booking.payment_status = PaymentStatus.REFUNDED
        db.session.commit()
        current_app.logger.info(
            f"Simulated refund for booking {booking.booking_reference}"
        )
        return True
    except Exception as e:
        current_app.logger.error(f"Refund simulation failed: {str(e)}")
        db.session.rollback()
        return False
