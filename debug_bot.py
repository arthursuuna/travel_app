#!/usr/bin/env python3
"""
Debug script to test bot processing
"""

from app import create_app, db
from app.models import Inquiry, BotResponse, InquiryResponse
from app.bot_service import inquiry_bot

def debug_bot_processing():
    """Debug what's happening with bot processing"""
    app = create_app()
    with app.app_context():
        print("🔍 DEBUGGING BOT PROCESSING")
        print("=" * 50)
        
        # 1. Check if bot responses exist
        bot_responses = BotResponse.query.all()
        print(f"Bot responses in database: {len(bot_responses)}")
        
        for response in bot_responses:
            print(f"  - {response.category}: {response.trigger_keywords[:50]}... (active: {response.is_active}, threshold: {response.confidence_threshold})")
        
        print("\n" + "=" * 50)
        
        # 2. Test bot with sample text
        test_messages = [
            "I want to book a tour",
            "What are your prices?", 
            "I need to cancel my booking",
            "Where do you pick up customers?",
            "How long is the tour?",
            "What should I bring?",
            "Tell me about your company"
        ]
        
        print(f"🤖 Testing bot responses:")
        for message in test_messages:
            try:
                # Create a test inquiry object
                test_inquiry = Inquiry(
                    name="Test User",
                    email="test@example.com", 
                    subject="Test Subject",
                    message=message
                )
                
                print(f"\nTesting: '{message}'")
                
                # Test analysis first
                analysis = inquiry_bot.analyze_inquiry(message, "Test Subject")
                print(f"  Analysis: {analysis}")
                
                # Test bot response
                bot_response = inquiry_bot.generate_response(test_inquiry)
                
                if bot_response:
                    print(f"  ✅ Bot Response: {bot_response['category']} ({bot_response['confidence']:.2f})")
                    print(f"     Text: {bot_response['text'][:100]}...")
                else:
                    print(f"  ❌ No response generated")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 50)
        
        # 3. Check recent inquiries
        recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
        print(f"📋 Recent inquiries ({len(recent_inquiries)}):")
        for inquiry in recent_inquiries:
            responses = InquiryResponse.query.filter_by(inquiry_id=inquiry.id, is_bot_response=True).count()
            print(f"  - ID {inquiry.id}: {inquiry.status}, Bot processed: {inquiry.bot_processed}, Bot responses: {responses}")
            print(f"    Message: {inquiry.message[:80]}...")

if __name__ == "__main__":
    debug_bot_processing()
