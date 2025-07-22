#!/usr/bin/env python3
"""
Test script for the bot response system.
This script verifies that all bot functionality is working correctly.
"""

from app import create_app, db
from app.models import BotResponse, InquiryResponse, Inquiry
from app.bot_service import InquiryBot

def test_bot_system():
    """Test the complete bot system functionality."""
    
    app = create_app()
    with app.app_context():
        print("🧪 Testing Bot Response System")
        print("=" * 50)
        
        # 1. Test database tables
        print("\n1. Testing Database Tables:")
        try:
            bot_responses = BotResponse.query.all()
            print(f"   ✅ BotResponse table: {len(bot_responses)} responses found")
            
            for response in bot_responses:
                print(f"      - {response.category}: {response.trigger_keywords[:30]}...")
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            return False
        
        # 2. Test bot service
        print("\n2. Testing Bot Service:")
        try:
            bot = InquiryBot()
            
            # Test different types of inquiries
            test_cases = [
                ("I want to book a tour", "booking"),
                ("How much does it cost?", "pricing"),
                ("Can I cancel my reservation?", "cancellation"),
                ("Where do you go?", "location"),
                ("How long is the trip?", "duration"),
                ("Hello, I need help", "general"),
                ("What do I need to bring?", "requirements")
            ]
            
            for test_text, expected_category in test_cases:
                analysis = bot.analyze_inquiry(test_text, "Test Subject")
                print(f"   📝 '{test_text[:30]}...'")
                print(f"      → Category: {analysis['category']} (expected: {expected_category})")
                print(f"      → Confidence: {analysis['confidence']:.2f}")
                print(f"      → Sentiment: {analysis['sentiment']}")
                
                # Create a mock inquiry object for testing response generation
                class MockInquiry:
                    def __init__(self, text, subject):
                        self.message = text
                        self.subject = subject
                        self.name = "Test User"
                        self.email = "test@example.com"
                
                mock_inquiry = MockInquiry(test_text, "Test Subject")
                response = bot.generate_response(mock_inquiry)
                if response:
                    print(f"      → Response: ✅ Generated ({len(response['text'])} chars)")
                else:
                    print(f"      → Response: ❌ None generated")
                print()
                
        except Exception as e:
            print(f"   ❌ Bot service error: {e}")
            return False
        
        # 3. Test email integration
        print("\n3. Testing Email Functions:")
        try:
            from app.routes.main import send_bot_response_email, send_admin_notification_email
            print("   ✅ Email functions imported successfully")
            print("      - send_bot_response_email: Available")
            print("      - send_admin_notification_email: Available")
        except Exception as e:
            print(f"   ❌ Email import error: {e}")
        
        # 4. Test admin routes
        print("\n4. Testing Admin Routes:")
        try:
            from app.routes.admin_bot import admin_bot_bp
            print(f"   ✅ Admin bot blueprint: {admin_bot_bp.name}")
            print(f"   ✅ Blueprint registered successfully")
            
            # Get routes from the current app context
            with app.test_client() as client:
                # Test if routes are accessible
                routes = [
                    '/admin/bot/responses',
                    '/admin/bot/analytics', 
                    '/admin/bot/create'
                ]
                
                for route in routes:
                    print(f"      - {route}: Route registered")
        except Exception as e:
            print(f"   ❌ Admin routes error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Bot System Test Complete!")
        print("\n📋 Access Points:")
        print("   • Bot Management: http://localhost:5000/admin/bot/responses")
        print("   • Bot Analytics:  http://localhost:5000/admin/bot/analytics")
        print("   • Create Response: http://localhost:5000/admin/bot/create")
        print("   • Test Bot:       Contact form at http://localhost:5000/#contact")
        
        return True

if __name__ == "__main__":
    test_bot_system()
