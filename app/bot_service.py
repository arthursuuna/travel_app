"""
Intelligent Bot Response Service for handling user inquiries automatically.
"""

import re
from datetime import datetime
from flask import current_app
from app.models import BotResponse, Inquiry, InquiryResponse, Tour, db
from sqlalchemy import func

class InquiryBot:
    def __init__(self):
        self.keyword_patterns = {
            'booking': [
                r'\b(book|reserve|reservation|availability)\b',
                r'\b(available|free|open)\b',
                r'\b(when|date|schedule)\b'
            ],
            'pricing': [
                r'\b(price|cost|fee|payment|money|expensive|cheap)\b',
                r'\b(how much|total|amount)\b',
                r'\b(\$|USD|dollar|currency)\b'
            ],
            'location': [
                r'\b(where|location|place|destination)\b',
                r'\b(address|directions|map)\b',
                r'\b(meet|pickup|departure)\b'
            ],
            'duration': [
                r'\b(how long|duration|time|hours|days)\b',
                r'\b(start|end|finish)\b'
            ],
            'cancellation': [
                r'\b(cancel|refund|change|modify)\b',
                r'\b(policy|terms|conditions)\b'
            ],
            'requirements': [
                r'\b(need|require|bring|pack)\b',
                r'\b(equipment|gear|clothing)\b',
                r'\b(fitness|health|medical)\b'
            ],
            'weather': [
                r'\b(weather|rain|sun|temperature|climate)\b',
                r'\b(season|month|best time)\b'
            ],
            'group_size': [
                r'\b(group|people|participants|capacity)\b',
                r'\b(maximum|minimum|limit)\b'
            ],
            'transportation': [
                r'\b(transport|travel|flight|bus|car)\b',
                r'\b(airport|pickup|drop off)\b'
            ],
            'accommodation': [
                r'\b(hotel|stay|accommodation|lodge)\b',
                r'\b(room|bed|sleep)\b'
            ]
        }
        
        self.sentiment_patterns = {
            'positive': [r'\b(great|excellent|amazing|wonderful|perfect|love|excited)\b'],
            'negative': [r'\b(bad|terrible|awful|disappointed|angry|frustrated|horrible)\b'],
            'urgent': [r'\b(urgent|emergency|asap|immediately|now|quick)\b']
        }

    def analyze_inquiry(self, inquiry_text, inquiry_subject=None):
        """Analyze inquiry text to determine category, sentiment, and urgency."""
        text_lower = inquiry_text.lower()
        if inquiry_subject:
            text_lower += " " + inquiry_subject.lower()
        
        # Determine category
        category_scores = {}
        for category, patterns in self.keyword_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches
            category_scores[category] = score
        
        # Get primary category
        primary_category = max(category_scores, key=category_scores.get) if max(category_scores.values()) > 0 else 'general'
        confidence = category_scores[primary_category] / max(len(text_lower.split()) / 10, 1)
        
        # Determine sentiment
        sentiment = self._analyze_sentiment(text_lower)
        
        # Check urgency
        is_urgent = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.sentiment_patterns['urgent'])
        
        return {
            'category': primary_category,
            'confidence': min(confidence, 1.0),
            'sentiment': sentiment,
            'is_urgent': is_urgent,
            'keywords_found': [cat for cat, score in category_scores.items() if score > 0]
        }

    def _analyze_sentiment(self, text):
        """Simple sentiment analysis."""
        positive_score = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in self.sentiment_patterns['positive'])
        negative_score = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in self.sentiment_patterns['negative'])
        
        if negative_score > positive_score:
            return 'negative'
        elif positive_score > 0:
            return 'positive'
        return 'neutral'

    def generate_response(self, inquiry):
        """Generate an appropriate bot response for an inquiry."""
        try:
            print(f"🤖 Generating response for inquiry: {inquiry.message[:50]}...")
            
            # Analyze the inquiry
            analysis = self.analyze_inquiry(inquiry.message, inquiry.subject)
            print(f"🔍 Analysis result: {analysis}")
            
            if not analysis or not analysis.get('category'):
                print("❌ No analysis category found")
                return None
            
            category = analysis['category']
            confidence = analysis.get('confidence', 0.0)
            sentiment = analysis.get('sentiment', 'neutral')
            is_urgent = analysis.get('is_urgent', False)
            
            print(f"📊 Category: {category}, Confidence: {confidence:.2f}, Sentiment: {sentiment}")
            
            # Don't respond to negative sentiment or urgent inquiries automatically
            if sentiment == 'negative':
                print("❌ Declining to respond: negative sentiment detected")
                return None
                
            if is_urgent:
                print("❌ Declining to respond: urgent inquiry detected")
                return None
            
            # Find matching bot response template
            print(f"🔍 Looking for bot response: category={category}, confidence>={confidence}")
            
            bot_response = BotResponse.query.filter(
                BotResponse.category == category,
                BotResponse.is_active == True,
                BotResponse.confidence_threshold <= confidence
            ).first()
            
            if not bot_response:
                print(f"⚠️ No bot response found for category '{category}' with confidence {confidence}")
                print("🔍 Trying to find any active response for this category...")
                # Try to find any active response for this category
                bot_response = BotResponse.query.filter(
                    BotResponse.category == category,
                    BotResponse.is_active == True
                ).first()
            
            if not bot_response:
                print(f"⚠️ No active bot response found for category '{category}'")
                print("🔍 Trying general category...")
                # Try to find any general response
                bot_response = BotResponse.query.filter(
                    BotResponse.category == 'general',
                    BotResponse.is_active == True
                ).first()
            
            if bot_response:
                print(f"✅ Found bot response: {bot_response.category} (ID: {bot_response.id})")
                
                # Personalize the response
                response_text = self._personalize_response(bot_response.response_text, inquiry)
                
                # Determine if requires human review
                requires_review = (
                    confidence < 0.7 or 
                    sentiment == 'negative' or
                    is_urgent or
                    any(keyword in inquiry.message.lower() for keyword in ['complaint', 'problem', 'issue', 'disappointed'])
                )
                
                result = {
                    'text': response_text,
                    'category': category,
                    'confidence': confidence,
                    'requires_review': requires_review,
                    'bot_response_id': bot_response.id
                }
                
                print(f"✅ Generated response successfully: confidence={confidence:.2f}, requires_review={requires_review}")
                return result
            else:
                print("❌ No bot response found at all")
                return None
                
        except Exception as e:
            print(f"❌ Error in generate_response: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _personalize_response(self, template, inquiry):
        """Personalize bot response with user and inquiry details."""
        # Replace placeholders with actual data
        response = template.replace('{user_name}', inquiry.name)
        response = response.replace('{user_email}', inquiry.email)
        
        # Add tour-specific information if available
        if hasattr(inquiry, 'tour_interest'):
            # You could add logic to detect tour mentions in the inquiry
            pass
            
        return response

    def should_escalate_to_human(self, inquiry, analysis):
        """Determine if inquiry should be escalated to human admin."""
        escalation_reasons = []
        
        if analysis['sentiment'] == 'negative':
            escalation_reasons.append('Negative sentiment detected')
        
        if analysis['is_urgent']:
            escalation_reasons.append('Urgent inquiry')
        
        if analysis['confidence'] < 0.5:
            escalation_reasons.append('Low confidence in categorization')
        
        if any(keyword in inquiry.message.lower() for keyword in ['complaint', 'refund', 'problem', 'issue']):
            escalation_reasons.append('Potential complaint')
        
        return len(escalation_reasons) > 0, escalation_reasons

# Initialize bot instance
inquiry_bot = InquiryBot()
