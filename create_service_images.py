#!/usr/bin/env python3
"""
Generate placeholder images for the services page.
This script creates placeholder images for services, airlines, and other elements.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import random


def create_placeholder_image(width, height, text, bg_color, text_color, filename):
    """Create a placeholder image with text"""
    # Create image
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to use a default font, fall back to basic font if not available
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()

    # Get text size and position
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text
    draw.text((x, y), text, fill=text_color, font=font)

    # Save image
    img.save(filename)
    print(f"Created: {filename}")


def create_service_images():
    """Create placeholder images for services"""

    # Service images
    services = [
        ("flights.jpg", "Flight Services", (135, 206, 235)),  # Sky blue
        (
            "tour-guides.jpg",
            "Professional\nTour Guides",
            (60, 179, 113),
        ),  # Medium sea green
        ("happy-travelers.jpg", "Happy Travelers", (255, 165, 0)),  # Orange
        ("accommodation.jpg", "Luxury Hotels", (106, 90, 205)),  # Slate blue
        ("transportation.jpg", "Ground Transport", (220, 20, 60)),  # Crimson
        ("travel-insurance.jpg", "Travel Insurance", (47, 79, 79)),  # Dark slate gray
        ("hero-bg.jpg", "Travel Services", (0, 102, 204)),  # Blue
        ("cta-bg.jpg", "Start Your Journey", (40, 167, 69)),  # Green
    ]

    services_dir = "d:/travel_app/app/static/images/services"
    os.makedirs(services_dir, exist_ok=True)

    for filename, text, color in services:
        create_placeholder_image(
            800, 600, text, color, (255, 255, 255), os.path.join(services_dir, filename)
        )


def create_airline_images():
    """Create placeholder images for airlines"""

    airlines = [
        ("emirates.png", "Emirates", (255, 0, 0)),  # Red
        ("qatar.png", "Qatar Airways", (128, 0, 128)),  # Purple
        ("british.png", "British Airways", (0, 0, 255)),  # Blue
        ("lufthansa.png", "Lufthansa", (255, 255, 0)),  # Yellow
        ("singapore.png", "Singapore Airlines", (0, 128, 128)),  # Teal
        ("turkish.png", "Turkish Airlines", (220, 20, 60)),  # Crimson
    ]

    airlines_dir = "d:/travel_app/app/static/images/airlines"
    os.makedirs(airlines_dir, exist_ok=True)

    for filename, text, color in airlines:
        create_placeholder_image(
            200, 100, text, (255, 255, 255), color, os.path.join(airlines_dir, filename)
        )


def create_realistic_service_images():
    """Create more realistic looking service images"""

    # More realistic service images with gradients and better styling
    services_dir = "d:/travel_app/app/static/images/services"

    # Flight services - sky theme
    img = Image.new("RGB", (800, 600), (135, 206, 235))
    draw = ImageDraw.Draw(img)

    # Add gradient effect
    for y in range(600):
        color_intensity = int(255 * (y / 600))
        draw.rectangle(
            [(0, y), (800, y + 1)], fill=(135, 206, 235 - color_intensity // 4)
        )

    # Add airplane silhouette (simple)
    draw.ellipse([300, 250, 500, 350], fill=(255, 255, 255))
    draw.rectangle([350, 290, 450, 310], fill=(255, 255, 255))

    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()

    draw.text((250, 400), "Flight Services", fill=(255, 255, 255), font=font)
    img.save(os.path.join(services_dir, "flights.jpg"))

    print("Created realistic service images")


def main():
    """Main function to create all placeholder images"""
    print("Creating placeholder images for services page...")

    try:
        create_service_images()
        create_airline_images()
        create_realistic_service_images()

        print("\n✅ All placeholder images created successfully!")
        print("📁 Service images: d:/travel_app/app/static/images/services/")
        print("📁 Airline images: d:/travel_app/app/static/images/airlines/")
        print("\n💡 You can replace these placeholder images with real photos later.")

    except Exception as e:
        print(f"❌ Error creating images: {str(e)}")
        print("Make sure you have the Pillow library installed: pip install Pillow")


if __name__ == "__main__":
    main()
