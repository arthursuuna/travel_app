"""
Reporting utilities for the Travel App.
This module contains functions for generating reports and analytics.
"""

from flask import current_app
from app.models import Booking, Tour, User, BookingStatus
from app import db
from sqlalchemy import func, extract, and_
from datetime import datetime, timedelta
import json


def get_booking_statistics(start_date=None, end_date=None):
    """
    Get booking statistics for a date range.

    Args:
        start_date (date, optional): Start date for the report
        end_date (date, optional): End date for the report

    Returns:
        dict: Statistics dictionary
    """
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Base query for all bookings in the database
        base_query = Booking.query

        # Total bookings
        total_bookings = base_query.count()

        # Confirmed bookings
        confirmed_bookings = base_query.filter(
            Booking.status == BookingStatus.CONFIRMED
        ).count()

        # Cancelled bookings
        cancelled_bookings = base_query.filter(
            Booking.status == BookingStatus.CANCELLED
        ).count()

        # Pending bookings
        pending_bookings = base_query.filter(
            Booking.status == BookingStatus.PENDING
        ).count()

        # Completed bookings
        completed_bookings = base_query.filter(
            Booking.status == BookingStatus.COMPLETED
        ).count()

        # Total revenue (all tours)
        total_revenue = db.session.query(func.sum(Tour.total_revenue)).scalar() or 0

        # Average booking amount (all bookings)
        avg_booking_amount = (
            base_query.with_entities(func.avg(Booking.total_amount)).scalar() or 0
        )

        # Total participants (all bookings)
        total_participants = (
            base_query.with_entities(func.sum(Booking.participants)).scalar() or 0
        )

        return {
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "pending_bookings": pending_bookings,
            "completed_bookings": completed_bookings,
            "total_revenue": float(total_revenue),
            "avg_booking_amount": float(avg_booking_amount),
            "total_participants": total_participants,
            "conversion_rate": (
                (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0
            ),
            "cancellation_rate": (
                (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
            ),
        }

    except Exception as e:
        current_app.logger.error(f"Error generating booking statistics: {str(e)}")
        return None


def get_popular_tours(limit=10):
    """
    Get the most popular tours based on booking count.

    Args:
        limit (int): Number of tours to return

    Returns:
        list: List of tour dictionaries with booking counts
    """
    try:
        popular_tours = (
            db.session.query(
                Tour.id,
                Tour.title,
                Tour.destination,
                Tour.price,
                func.count(Booking.id).label("booking_count"),
                func.sum(Booking.participants).label("total_participants"),
                func.sum(Booking.total_amount).label("total_revenue"),
            )
            .join(Booking, Tour.id == Booking.tour_id)
            .filter(Booking.status == BookingStatus.CONFIRMED)
            .group_by(Tour.id)
            .order_by(func.count(Booking.id).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": tour.id,
                "title": tour.title,
                "destination": tour.destination,
                "price": float(tour.price),
                "booking_count": tour.booking_count,
                "total_participants": tour.total_participants,
                "total_revenue": float(tour.total_revenue),
            }
            for tour in popular_tours
        ]

    except Exception as e:
        current_app.logger.error(f"Error getting popular tours: {str(e)}")
        return []


def get_monthly_revenue_data(months=12):
    """
    Get monthly revenue data for the last N months.

    Args:
        months (int): Number of months to include

    Returns:
        list: List of monthly revenue data
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        monthly_data = (
            db.session.query(
                extract("year", Booking.created_at).label("year"),
                extract("month", Booking.created_at).label("month"),
                func.sum(Booking.total_amount).label("revenue"),
                func.count(Booking.id).label("bookings"),
            )
            .filter(
                and_(
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date,
                    Booking.status == BookingStatus.CONFIRMED,
                )
            )
            .group_by(
                extract("year", Booking.created_at),
                extract("month", Booking.created_at),
            )
            .order_by(
                extract("year", Booking.created_at),
                extract("month", Booking.created_at),
            )
            .all()
        )

        return [
            {
                "year": int(data.year),
                "month": int(data.month),
                "revenue": float(data.revenue),
                "bookings": data.bookings,
                "month_name": datetime(int(data.year), int(data.month), 1).strftime(
                    "%B %Y"
                ),
            }
            for data in monthly_data
        ]

    except Exception as e:
        current_app.logger.error(f"Error getting monthly revenue data: {str(e)}")
        return []


def get_user_statistics():
    """
    Get user statistics.

    Returns:
        dict: User statistics
    """
    try:
        total_users = User.query.count()
        active_users = User.query.filter(User.is_active == True).count()
        admin_users = User.query.filter(User.is_admin == True).count()

        # Users who have made bookings
        users_with_bookings = (
            db.session.query(func.count(func.distinct(Booking.user_id))).scalar() or 0
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "users_with_bookings": users_with_bookings,
            "booking_conversion_rate": (
                (users_with_bookings / total_users * 100) if total_users > 0 else 0
            ),
        }

    except Exception as e:
        current_app.logger.error(f"Error getting user statistics: {str(e)}")
        return None


def generate_comprehensive_report():
    """
    Generate a comprehensive report with all statistics.

    Returns:
        dict: Comprehensive report data
    """
    try:
        report = {
            "generated_at": datetime.now().isoformat(),
            "booking_stats": get_booking_statistics(),
            "popular_tours": get_popular_tours(),
            "monthly_revenue": get_monthly_revenue_data(),
            "user_stats": get_user_statistics(),
        }

        return report

    except Exception as e:
        current_app.logger.error(f"Error generating comprehensive report: {str(e)}")
        return None


def export_bookings_to_csv(start_date=None, end_date=None):
    """
    Export bookings to CSV format.

    Args:
        start_date (date, optional): Start date for export
        end_date (date, optional): End date for export

    Returns:
        str: CSV content
    """
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        bookings = Booking.query.filter(
            and_(Booking.created_at >= start_date, Booking.created_at <= end_date)
        ).all()

        csv_content = "Booking Reference,Tour Title,User Email,Travel Date,Participants,Total Amount,Status,Created At\n"

        for booking in bookings:
            csv_content += f"{booking.booking_reference},{booking.tour.title},{booking.user.email},{booking.travel_date},{booking.participants},{booking.total_amount},{booking.status.name},{booking.created_at}\n"

        return csv_content

    except Exception as e:
        current_app.logger.error(f"Error exporting bookings to CSV: {str(e)}")
        return None
