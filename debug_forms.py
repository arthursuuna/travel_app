#!/usr/bin/env python3
"""
Debug script to test form validation for Travel App.
Run this to test form validation without submitting through the web interface.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.forms import InquiryResponseForm

def test_form_validation():
    """Test InquiryResponseForm validation with various inputs."""
    
    app = create_app()
    
    with app.test_request_context():
        print("=== Testing InquiryResponseForm Validation ===\n")
        
        # Test 1: Empty form
        print("Test 1: Empty form")
        form = InquiryResponseForm()
        form.process()  # Simulate form processing
        
        print(f"Valid: {form.validate()}")
        if form.errors:
            print("Errors:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
        print()
        
        # Test 2: Minimal valid form (status and priority only)
        print("Test 2: Minimal valid form (status and priority only)")
        form = InquiryResponseForm()
        form.status.data = "in_progress"
        form.priority.data = "medium"
        form.response.data = ""
        form.internal_notes.data = ""
        form.send_email.data = False
        
        print(f"Valid: {form.validate()}")
        if form.errors:
            print("Errors:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
        print()
        
        # Test 3: Full valid form
        print("Test 3: Full valid form")
        form = InquiryResponseForm()
        form.status.data = "resolved"
        form.priority.data = "medium"
        form.response.data = "Thank you for your inquiry. This has been resolved."
        form.internal_notes.data = "Customer satisfied with resolution."
        form.send_email.data = True
        
        print(f"Valid: {form.validate()}")
        if form.errors:
            print("Errors:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
        print()
        
        # Test 4: Invalid choices
        print("Test 4: Invalid choices")
        form = InquiryResponseForm()
        form.status.data = "invalid_status"
        form.priority.data = "invalid_priority"
        form.response.data = "Test response"
        
        print(f"Valid: {form.validate()}")
        if form.errors:
            print("Errors:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
        print()

if __name__ == "__main__":
    test_form_validation()
