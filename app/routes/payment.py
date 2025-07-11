"""
Payment routes for the Travel App.
Handles payment processing, confirmation, and related operations.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user
from app import db
from app.models import Booking, BookingStatus
from app.payment import (
    create_payment_intent,
    confirm_payment,
    simulate_payment_for_development,
)
from app.decorators import active_user_required

# Create payment blueprint
payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


@payment_bp.route("/process/<int:booking_id>")
@login_required
@active_user_required
def process_payment(booking_id):
    """
    Process payment for a booking.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Verify booking ownership
    if booking.user_id != current_user.id:
        flash("You can only pay for your own bookings.", "danger")
        return redirect(url_for("bookings.my_bookings"))

    # Check if booking is already paid
    if booking.status == BookingStatus.CONFIRMED:
        flash("This booking has already been paid for.", "info")
        return redirect(url_for("bookings.view_booking", booking_id=booking_id))

    # If simulation mode is enabled, skip Stripe and process payment immediately
    from app.payment import FORCE_SIMULATE_PAYMENT
    if FORCE_SIMULATE_PAYMENT:
        if simulate_payment_for_development(booking):
            flash("Payment processed successfully! ", "success")
        else:
            flash("Payment simulation failed.", "danger")
        return redirect(url_for("bookings.view_booking", booking_id=booking_id))

    # Otherwise, use Stripe logic
    intent = create_payment_intent(booking)
    if not intent:
        flash("Failed to initialize payment. Please try again.", "danger")
        return redirect(url_for("bookings.view_booking", booking_id=booking_id))
    return render_template(
        "payment/process.html",
        booking=booking,
        client_secret=intent.client_secret,
        stripe_public_key=current_app.config.get("STRIPE_PUBLIC_KEY"),
    )


@payment_bp.route("/confirm", methods=["POST"])
@login_required
@active_user_required
def confirm_payment_route():
    """
    Confirm payment after successful processing.
    """
    try:
        data = request.get_json()
        payment_intent_id = data.get("payment_intent_id")

        if not payment_intent_id:
            return jsonify({"success": False, "error": "Missing payment intent ID"})

        # Confirm payment
        success = confirm_payment(payment_intent_id)

        if success:
            return jsonify(
                {"success": True, "message": "Payment confirmed successfully!"}
            )
        else:
            return jsonify({"success": False, "error": "Payment confirmation failed"})

    except Exception as e:
        current_app.logger.error(f"Payment confirmation error: {str(e)}")
        return jsonify({"success": False, "error": "Payment confirmation failed"})


@payment_bp.route("/cancel/<int:booking_id>")
@login_required
@active_user_required
def cancel_payment(booking_id):
    """
    Cancel payment and return to booking.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Verify booking ownership
    if booking.user_id != current_user.id:
        flash("You can only cancel payment for your own bookings.", "danger")
        return redirect(url_for("bookings.my_bookings"))

    flash("Payment was cancelled. You can try again later.", "info")
    return redirect(url_for("bookings.view_booking", booking_id=booking_id))


@payment_bp.route("/success/<int:booking_id>")
@login_required
@active_user_required
def payment_success(booking_id):
    """
    Payment success page.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Verify booking ownership
    if booking.user_id != current_user.id:
        flash("You can only view your own bookings.", "danger")
        return redirect(url_for("bookings.my_bookings"))

    return render_template("payment/success.html", booking=booking)


@payment_bp.route("/failure/<int:booking_id>")
@login_required
@active_user_required
def payment_failure(booking_id):
    """
    Payment failure page.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Verify booking ownership
    if booking.user_id != current_user.id:
        flash("You can only view your own bookings.", "danger")
        return redirect(url_for("bookings.my_bookings"))

    return render_template("payment/failure.html", booking=booking)
