"""
Migration script to initialize bot response system.
Run this after adding the new models to create sample bot responses.
"""

from app import create_app, db
from app.models import BotResponse
from flask import current_app

def create_sample_bot_responses():
    """Create sample bot responses for common inquiry types."""
    
    sample_responses = [
        {
            'trigger_keywords': 'booking,reserve,availability,book,reservation',
            'response_text': '''Hello {user_name}!

Thank you for your interest in booking with us. Here's how you can make a reservation:

🎯 **Easy Booking Steps:**
1. Browse our available tours at: /tours
2. Select your preferred tour and date
3. Click "Book Now" and follow the booking process
4. Complete payment to confirm your reservation

💡 **Need Help Choosing?**
If you need help finding the perfect tour, please let me know:
- Your preferred destination
- Travel dates
- Group size
- Budget range

I'll be happy to recommend something suitable!

Best regards,
Travel App Bot 🤖''',
            'category': 'booking',
            'confidence_threshold': 0.6
        },
        {
            'trigger_keywords': 'price,cost,fee,payment,money,expensive,cheap,how much',
            'response_text': '''Hi {user_name}!

Our tour prices vary depending on several factors:

💰 **Pricing Factors:**
- Destination and duration
- Group size and season
- Included services and accommodation level
- Time of booking (early bird discounts available!)

🔍 **Find Current Pricing:**
1. Visit our tours page: /tours
2. Select your preferred tour
3. Choose your travel dates
4. View detailed cost breakdown

💳 **Payment Options:**
- Full payment at booking
- Installment plans available
- Multiple payment methods accepted

For specific pricing questions, please mention which tour interests you and I'll provide detailed information.

Best regards,
Travel App Bot 🤖''',
            'category': 'pricing',
            'confidence_threshold': 0.6
        },
        {
            'trigger_keywords': 'cancel,refund,change,modify,policy',
            'response_text': '''Hello {user_name}!

Here's our cancellation and modification policy:

📋 **Cancellation Policy:**
- ✅ FREE cancellation up to 48 hours before departure
- 💰 50% refund for cancellations 24-48 hours before departure  
- ❌ No refund for cancellations less than 24 hours before departure

🔄 **To Cancel or Modify Your Booking:**
1. Log into your account dashboard: /dashboard
2. Find your booking under "My Bookings"
3. Use the "Cancel" or "Modify" options
4. Follow the guided process

🆘 **Need Help?**
For special circumstances or if you need assistance with the process, please contact our support team with your booking reference number.

We understand plans can change and we'll do our best to help!

Best regards,
Travel App Bot 🤖''',
            'category': 'cancellation',
            'confidence_threshold': 0.7
        },
        {
            'trigger_keywords': 'location,where,address,directions,meet,pickup',
            'response_text': '''Hi {user_name}!

Meeting points and locations vary by tour:

📍 **Finding Your Meeting Point:**
1. Visit the specific tour page
2. Check the "Meeting Point" section in tour details
3. Look for departure location and time information

🏨 **Common Meeting Points:**
- Hotel lobbies (for multi-day tours)
- Central city locations (easy to find)
- Airport terminals (for fly-in tours)
- Our tour operator offices

📧 **Detailed Information:**
After booking, you'll receive:
- Exact coordinates and detailed directions
- Contact information for your guide
- Maps and landmark references

For specific location questions, please mention your tour name and I'll provide more details!

Best regards,
Travel App Bot 🤖''',
            'category': 'location',
            'confidence_threshold': 0.6
        },
        {
            'trigger_keywords': 'duration,how long,time,hours,days,start,end',
            'response_text': '''Hi {user_name}!

Tour durations vary by destination and type:

⏱️ **Duration Information:**
- Day tours: 6-12 hours
- Multi-day tours: 2-14 days  
- Adventure tours: 3-21 days
- Cultural tours: 1-10 days

📅 **Tour Schedule Details:**
Each tour page includes:
- Total duration
- Daily itinerary breakdown
- Start and end times
- Activity schedules

🔍 **Find Specific Duration:**
1. Browse tours at: /tours
2. Select your interested tour
3. Check the "Duration" and "Itinerary" sections

For questions about a specific tour's timing, please mention the tour name and I'll provide detailed schedule information!

Best regards,
Travel App Bot 🤖''',
            'category': 'duration',
            'confidence_threshold': 0.6
        },
        {
            'trigger_keywords': 'general,help,information,question,contact,support',
            'response_text': '''Hello {user_name}!

Welcome to Affordable Escapes! I'm here to help you with:

🎯 **Popular Topics I Can Help With:**
- 📅 Booking and reservations
- 💰 Pricing and payment options  
- 📍 Tour locations and meeting points
- 📝 Cancellation and modification policies
- ⏰ Tour durations and schedules
- 🎒 What to bring and requirements

📱 **Quick Links:**
- Browse Tours: /tours
- Your Dashboard: /dashboard  
- About Us: /about
- Contact Form: /contact

🤖 **How I Work:**
I can instantly help with common questions! For complex inquiries or if you prefer human assistance, our support team is always available.

❓ **Need Specific Help?**
Just ask me about:
- A particular tour
- Booking process
- Pricing information
- Travel requirements

How can I assist you today?

Best regards,
Travel App Bot 🤖''',
            'category': 'general',
            'confidence_threshold': 0.3
        },
        {
            'trigger_keywords': 'requirements,need,require,bring,pack,equipment,gear',
            'response_text': '''Hi {user_name}!

Here's what you typically need for our tours:

🎒 **General Requirements:**
- Valid passport (for international tours)
- Comfortable walking shoes
- Weather-appropriate clothing
- Basic personal items

📋 **Tour-Specific Requirements:**
Each tour has unique requirements listed on its page:
- Fitness level needed
- Special equipment (if any)
- Clothing recommendations  
- Medical considerations

🔍 **Find Specific Requirements:**
1. Visit the tour page you're interested in
2. Check the "What to Bring" section
3. Review "Requirements" and "Recommendations"

🏥 **Health & Safety:**
- Check if vaccinations are required
- Inform us of any medical conditions
- Review travel insurance options

For detailed packing lists and requirements for a specific tour, please mention the tour name!

Best regards,
Travel App Bot 🤖''',
            'category': 'requirements',
            'confidence_threshold': 0.6
        }
    ]
    
    for response_data in sample_responses:
        # Check if response already exists
        existing = BotResponse.query.filter_by(category=response_data['category']).first()
        if not existing:
            bot_response = BotResponse(**response_data)
            db.session.add(bot_response)
            print(f"Created bot response for category: {response_data['category']}")
        else:
            print(f"Bot response for category {response_data['category']} already exists")
    
    try:
        db.session.commit()
        print("✅ Bot response system migration completed successfully!")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Run the migration."""
    app = create_app()
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("📊 Database tables created/verified")
        
        # Create sample bot responses
        create_sample_bot_responses()

if __name__ == "__main__":
    main()
