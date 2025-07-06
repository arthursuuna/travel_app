"""
Sample data script for the Travel App.
This script creates sample categories and tours for testing.
"""

from app import create_app, db
from app.models import Category, Tour, User, UserRole
from datetime import date, timedelta


def create_sample_data():
    """Create sample categories and tours."""

    app = create_app()
    with app.app_context():
        # Create categories
        categories_data = [
            {
                "name": "Adventure",
                "description": "Thrilling adventures and outdoor activities",
            },
            {
                "name": "Cultural",
                "description": "Explore rich cultures and historical sites",
            },
            {
                "name": "Relaxation",
                "description": "Peaceful getaways and spa experiences",
            },
            {"name": "Family", "description": "Fun activities for the whole family"},
            {"name": "Luxury", "description": "Premium experiences and accommodations"},
        ]

        categories = []
        for cat_data in categories_data:
            category = Category.query.filter_by(name=cat_data["name"]).first()
            if not category:
                category = Category(
                    name=cat_data["name"], description=cat_data["description"]
                )
                db.session.add(category)
                categories.append(category)
            else:
                categories.append(category)

        db.session.commit()
        print(f"✅ Created {len(categories)} categories")

        # Create sample tours
        tours_data = [
            {
                "name": "Himalayan Trek Adventure",
                "destination": "Nepal",
                "description": "Experience the majestic Himalayas with this 10-day trekking adventure. Visit ancient monasteries, meet friendly locals, and witness breathtaking mountain views.",
                "price": 1299.99,
                "duration": 10,
                "max_participants": 12,
                "category": "Adventure",
                "image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            },
            {
                "name": "Paris Cultural Experience",
                "destination": "France",
                "description": "Immerse yourself in the art, culture, and cuisine of Paris. Visit world-famous museums, charming neighborhoods, and iconic landmarks including the stunning Eiffel Tower.",
                "price": 899.99,
                "duration": 7,
                "max_participants": 20,
                "category": "Cultural",
                "image_url": "https://images.unsplash.com/photo-1431274172761-fca41d930114?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            },
            {
                "name": "Bali Wellness Retreat",
                "destination": "Indonesia",
                "description": "Rejuvenate your mind and body in this peaceful Balinese retreat. Enjoy yoga sessions, spa treatments, and meditation in beautiful natural settings.",
                "price": 1599.99,
                "duration": 14,
                "max_participants": 15,
                "category": "Relaxation",
                "image_url": "https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            },
            {
                "name": "Disney World Family Fun",
                "destination": "Orlando, USA",
                "description": "Create magical memories with your family at Disney World. Enjoy thrilling rides, meet beloved characters, and experience the magic of Disney.",
                "price": 799.99,
                "duration": 5,
                "max_participants": 25,
                "category": "Family",
                "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            },
            {
                "name": "Santorini Luxury Getaway",
                "destination": "Greece",
                "description": "Experience the ultimate luxury in Santorini. Stay in premium villas, enjoy private yacht tours, and dine at world-class restaurants.",
                "price": 2499.99,
                "duration": 8,
                "max_participants": 8,
                "category": "Luxury",
                "image_url": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            },
            {
                "name": "Amazon Rainforest Expedition",
                "destination": "Brazil",
                "description": "Explore the incredible biodiversity of the Amazon rainforest. Spot exotic wildlife, learn about indigenous cultures, and experience nature at its finest.",
                "price": 1899.99,
                "duration": 12,
                "max_participants": 10,
                "category": "Adventure",
                "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            },
        ]

        created_tours = 0
        for tour_data in tours_data:
            tour = Tour.query.filter_by(title=tour_data["name"]).first()
            if not tour:
                # Find category
                category = Category.query.filter_by(name=tour_data["category"]).first()

                tour = Tour(
                    title=tour_data["name"],
                    destination=tour_data["destination"],
                    description=tour_data["description"],
                    price=tour_data["price"],
                    duration_days=tour_data["duration"],
                    max_participants=tour_data["max_participants"],
                    category_id=category.id if category else None,
                    image_url=tour_data["image_url"],
                    available_from=date.today(),
                    available_to=date.today() + timedelta(days=365),
                )
                db.session.add(tour)
                created_tours += 1

        db.session.commit()
        print(f"✅ Created {created_tours} tours")

        # Create admin user if it doesn't exist
        admin = User.query.filter_by(email="admin@travelapp.com").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@travelapp.com",
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("✅ Created admin user (admin@travelapp.com / admin123)")

        print("\n🎉 Sample data created successfully!")
        print("\n📋 Admin Login:")
        print("   Email: admin@travelapp.com")
        print("   Password: admin123")
        print("\n🌍 Visit http://localhost:5000/tours to see your tours!")


if __name__ == "__main__":
    create_sample_data()
