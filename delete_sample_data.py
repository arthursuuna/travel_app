"""
Delete Sample Data Script
========================
This script removes sample data from the database while preserving user accounts.

What it deletes:
- All tours
- All categories
- All bookings
- All reviews
- All payments
- All inquiries
- All tour itineraries

What it preserves:
- User accounts (so you don't lose your login)
- Database structure
"""

from app import create_app
from app.models import (
    db,
    Tour,
    Category,
    Booking,
    Review,
    Payment,
    Inquiry,
    TourItinerary,
)


def delete_sample_data():
    """
    Delete all sample data from the database.
    This removes tours, categories, bookings, etc. but keeps users.
    """
    app = create_app()

    with app.app_context():
        print("🗑️ Starting sample data deletion...")

        try:
            # Delete in order to avoid foreign key constraint issues

            # 1. Delete tour itineraries first (depends on tours)
            itinerary_count = TourItinerary.query.count()
            if itinerary_count > 0:
                TourItinerary.query.delete()
                print(f"✅ Deleted {itinerary_count} tour itineraries")

            # 2. Delete reviews (depends on tours and users)
            review_count = Review.query.count()
            if review_count > 0:
                Review.query.delete()
                print(f"✅ Deleted {review_count} reviews")

            # 3. Delete payments (depends on bookings)
            payment_count = Payment.query.count()
            if payment_count > 0:
                Payment.query.delete()
                print(f"✅ Deleted {payment_count} payments")

            # 4. Delete bookings (depends on tours and users)
            booking_count = Booking.query.count()
            if booking_count > 0:
                Booking.query.delete()
                print(f"✅ Deleted {booking_count} bookings")

            # 5. Delete tours (depends on categories)
            tour_count = Tour.query.count()
            if tour_count > 0:
                Tour.query.delete()
                print(f"✅ Deleted {tour_count} tours")

            # 6. Delete categories (no dependencies)
            category_count = Category.query.count()
            if category_count > 0:
                Category.query.delete()
                print(f"✅ Deleted {category_count} categories")

            # 7. Delete inquiries (no dependencies to tours)
            inquiry_count = Inquiry.query.count()
            if inquiry_count > 0:
                Inquiry.query.delete()
                print(f"✅ Deleted {inquiry_count} inquiries")

            # Commit all deletions
            db.session.commit()
            print("✅ Sample data deletion completed successfully!")
            print("👤 User accounts preserved - you can still log in")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during deletion: {str(e)}")
            raise

        finally:
            # Verify what's left
            print("\n📊 Remaining data:")
            from app.models import User

            print(f"   Users: {User.query.count()}")
            print(f"   Categories: {Category.query.count()}")
            print(f"   Tours: {Tour.query.count()}")
            print(f"   Bookings: {Booking.query.count()}")
            print(f"   Reviews: {Review.query.count()}")


if __name__ == "__main__":
    delete_sample_data()
