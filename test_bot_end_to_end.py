#!/usr/bin/env python3
"""
Simple bot system test to verify everything works end-to-end.
"""

from app import create_app, db
from app.models import Inquiry, BotResponse, InquiryResponse
from app.bot_service import InquiryBot
from datetime import datetime

def test_bot_end_to_end():
    """Test the bot system from inquiry creation to response."""
    
    app = create_app()
    with app.app_context():
        print("🧪 End-to-End Bot Test")
        print("=" * 40)
        
        # 1. Check bot responses exist
        bot_responses = BotResponse.query.filter_by(is_active=True).all()
        print(f"✅ Active bot responses: {len(bot_responses)}")
        
        if not bot_responses:
            print("❌ No active bot responses found!")
            return False
        
        # 2. Create test inquiry
        test_inquiry = Inquiry(
            name="Test User",
            email="test@example.com", 
            subject="Booking Question",
            message="I want to book a tour to Paris. How much does it cost?",
            status="new"
        )
        
        db.session.add(test_inquiry)
        db.session.flush()
        
        print(f"✅ Created test inquiry ID: {test_inquiry.id}")
        
        # 3. Test bot processing
        bot = InquiryBot()
        
        try:
            # Analyze the inquiry
            analysis = bot.analyze_inquiry(test_inquiry.message, test_inquiry.subject)
            print(f"✅ Bot analysis:")
            print(f"   Category: {analysis['category']}")
            print(f"   Confidence: {analysis['confidence']:.2f}")
            print(f"   Sentiment: {analysis['sentiment']}")
            
            # Generate response
            bot_response_data = bot.generate_response(test_inquiry)
            
            if bot_response_data:
                print(f"✅ Bot response generated:")
                print(f"   Length: {len(bot_response_data['text'])} characters")
                print(f"   Confidence: {bot_response_data['confidence']:.2f}")
                print(f"   Category: {bot_response_data['category']}")
                print(f"   Preview: {bot_response_data['text'][:100]}...")
                
                # Save the response
                inquiry_response = InquiryResponse(
                    inquiry_id=test_inquiry.id,
                    response_text=bot_response_data['text'],
                    is_bot_response=True,
                    bot_confidence=bot_response_data['confidence']
                )
                
                db.session.add(inquiry_response)
                test_inquiry.bot_processed = True
                test_inquiry.status = 'bot_responded'
                
                db.session.commit()
                print("✅ Response saved to database")
                
            else:
                print("❌ No bot response generated")
                db.session.rollback()
                return False
                
        except Exception as e:
            print(f"❌ Bot processing error: {e}")
            db.session.rollback()
            return False
        
        # 4. Verify the complete workflow
        saved_inquiry = Inquiry.query.get(test_inquiry.id)
        saved_responses = InquiryResponse.query.filter_by(inquiry_id=test_inquiry.id).all()
        
        print(f"✅ Workflow verification:")
        print(f"   Inquiry processed: {saved_inquiry.bot_processed}")
        print(f"   Status: {saved_inquiry.status}")
        print(f"   Responses saved: {len(saved_responses)}")
        
        if saved_responses:
            response = saved_responses[0]
            print(f"   Bot response: {response.is_bot_response}")
            print(f"   Confidence: {response.bot_confidence}")
        
        # Clean up test data
        db.session.delete(test_inquiry)
        for response in saved_responses:
            db.session.delete(response)
        db.session.commit()
        
        print("=" * 40)
        print("🎉 End-to-End Test PASSED!")
        print("\n📋 Test Summary:")
        print("   ✅ Bot responses available")
        print("   ✅ Inquiry analysis working")
        print("   ✅ Response generation working")
        print("   ✅ Database integration working")
        print("   ✅ Complete workflow functional")
        
        return True

if __name__ == "__main__":
    success = test_bot_end_to_end()
    if success:
        print("\n🚀 Bot system is fully operational!")
        print("   • Contact form: http://localhost:5000/contact")
        print("   • Admin panel: http://localhost:5000/admin/bot/responses")
    else:
        print("\n❌ Bot system has issues that need fixing.")
