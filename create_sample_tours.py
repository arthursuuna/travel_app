"""
Sample data creator for tours
Run this to populate the database with sample tours for testing
"""

from datetime import date
from app import create_app, db
from app.models import Tour, Category
from datetime import date


def create_sample_tours():
    app = create_app()

    with app.app_context():
        # Create categories if they don't exist
        categories_data = [
            {"name": "Adventure", "description": "Thrilling outdoor experiences"},
            {"name": "Cultural", "description": "Explore local culture and history"},
            {"name": "Beach", "description": "Relaxing beach getaways"},
            {"name": "Safari", "description": "Wildlife and nature tours"},
            {"name": "City Tours", "description": "Urban exploration and sightseeing"},
        ]

        for cat_data in categories_data:
            existing_category = Category.query.filter_by(name=cat_data["name"]).first()
            if not existing_category:
                category = Category(**cat_data)
                db.session.add(category)

        db.session.commit()

        # Get category IDs
        adventure_cat = Category.query.filter_by(name="Adventure").first()
        cultural_cat = Category.query.filter_by(name="Cultural").first()
        beach_cat = Category.query.filter_by(name="Beach").first()
        safari_cat = Category.query.filter_by(name="Safari").first()
        city_cat = Category.query.filter_by(name="City Tours").first()

        # Sample tours data
        tours_data = [
            {
                "title": "Rwenzori Mountains Adventure",
                "destination": "Rwenzori Mountains, Uganda",
                "description": "Experience the breathtaking beauty of the Rwenzori Mountains, also known as the Mountains of the Moon. This 7-day trekking adventure takes you through diverse ecosystems, from tropical rainforest to alpine meadows and glacial peaks.",
                "price": 1500.00,
                "duration_days": 7,
                "max_participants": 12,
                "category_id": adventure_cat.id if adventure_cat else None,
                "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                "is_active": True,
                "available_from": date(2024, 1, 1),
                "available_to": date(2024, 12, 31),
            },
            {
                "title": "Murchison Falls Safari",
                "destination": "Murchison Falls National Park, Uganda",
                "description": "Discover Uganda's largest national park on this 4-day safari. Witness the magnificent Murchison Falls, spot the Big Five, and enjoy boat cruises on the Nile River.",
                "price": 800.00,
                "duration_days": 4,
                "max_participants": 8,
                "category_id": safari_cat.id if safari_cat else None,
                "image_url": "https://images.unsplash.com/photo-1547036967-23d11aacaee0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                "is_active": True,
            },
            {
                "title": "Kampala City Cultural Tour",
                "destination": "Kampala, Uganda",
                "description": "Explore the vibrant capital city of Uganda. Visit historical sites, bustling markets, cultural centers, and experience local cuisine. Perfect for understanding Ugandan culture and history.",
                "price": 150.00,
                "duration_days": 1,
                "max_participants": 20,
                "category_id": cultural_cat.id if cultural_cat else None,
                "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                "is_active": True,
            },
            {
                "title": "Lake Bunyonyi Relaxation",
                "destination": "Lake Bunyonyi, Uganda",
                "description": "Unwind at the beautiful Lake Bunyonyi, known as the 'Place of Many Little Birds'. Enjoy canoeing, island hopping, and stunning sunset views in this peaceful paradise.",
                "price": 400.00,
                "duration_days": 3,
                "max_participants": 15,
                "category_id": beach_cat.id if beach_cat else None,
                "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                "is_active": True,
            },
            {
                "title": "Gorilla Trekking Bwindi",
                "destination": "Bwindi Impenetrable Forest, Uganda",
                "description": "Once-in-a-lifetime experience to see mountain gorillas in their natural habitat. This 3-day tour includes trekking through ancient forests and encountering these magnificent creatures.",
                "price": 2000.00,
                "duration_days": 3,
                "max_participants": 8,
                "category_id": adventure_cat.id if adventure_cat else None,
                "image_url": "https://images.unsplash.com/photo-1547036967-23d11aacaee0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                "is_active": True,
            },
            {
                "title": "Queen Elizabeth Wildlife Safari",
                "destination": "Queen Elizabeth National Park, Uganda",
                "description": "Explore Uganda's most popular national park. See tree-climbing lions, elephants, hippos, and over 600 bird species. Includes game drives and boat cruises.",
                "price": 900.00,
                "duration_days": 4,
                "max_participants": 10,
                "category_id": safari_cat.id if safari_cat else None,
                "image_url": "https://images.unsplash.com/photo-1516426122078-c23e76319801?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                "is_active": False,  # This one is currently unavailable
            },
        ]

        # Create tours
        for tour_data in tours_data:
            existing_tour = Tour.query.filter_by(title=tour_data["title"]).first()
            if not existing_tour:
                tour = Tour(**tour_data)
                db.session.add(tour)

        db.session.commit()
        print("Sample tours created successfully!")


if __name__ == "__main__":
    create_sample_tours()
