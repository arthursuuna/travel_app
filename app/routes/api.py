"""
REST API endpoints for mobile apps and third-party integration.
Implements NFR15 - REST APIs for integration with mobile apps or third-party booking services.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import jwt
from werkzeug.security import check_password_hash

from app.models import User, Tour, Booking, Category, Review, Inquiry, db
from app.decorators import validate_json, admin_required, active_user_required
from app.api_utils import rate_limit, get_api_documentation

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API Authentication decorator
def api_auth_required(f):
    """
    API authentication using Bearer token or API key.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')
        
        # Check for Bearer token
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                user = User.query.get(payload['user_id'])
                if user and user.is_active:
                    request.current_user = user
                    return f(*args, **kwargs)
            except jwt.InvalidTokenError:
                pass
        
        # Check for API key (simple implementation)
        elif api_key:
            user = User.query.filter_by(api_key=api_key, is_active=True).first()
            if user:
                request.current_user = user
                return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
    
    return decorated

def api_response(data=None, message='Success', status_code=200, errors=None):
    """
    Standardized API response format.
    """
    response = {
        'status': 'success' if status_code < 400 else 'error',
        'message': message,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response), status_code

def paginate_query(query, page=1, per_page=20):
    """
    Helper function to paginate query results.
    """
    pagination = query.paginate(
        page=page, 
        per_page=min(per_page, 100),  # Max 100 items per page
        error_out=False
    )
    
    return {
        'items': pagination.items,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_num': pagination.next_num,
            'prev_num': pagination.prev_num
        }
    }

# Authentication Endpoints
@api_bp.route('/auth/login', methods=['POST'])
@rate_limit(requests_per_minute=10)  # More restrictive for auth endpoints
@validate_json
def api_login():
    """
    API authentication endpoint.
    Returns JWT token for subsequent API calls.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return api_response(
                message='Email and password required',
                status_code=400,
                errors={'email': 'Required', 'password': 'Required'}
            )
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password) and user.is_active:
            # Generate JWT token
            token_payload = {
                'user_id': user.id,
                'email': user.email,
                'exp': datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
            }
            
            token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return api_response(data={
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'created_at': user.created_at.isoformat()
                }
            }, message='Login successful')
        
        return api_response(
            message='Invalid credentials',
            status_code=401,
            errors={'credentials': 'Invalid email or password'}
        )
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, "API login error")
        return api_response(message='Internal server error', status_code=500)

@api_bp.route('/auth/register', methods=['POST'])
@rate_limit(requests_per_minute=5)  # Very restrictive for registration
@validate_json
def api_register():
    """
    API user registration endpoint.
    """
    try:
        data = request.get_json()
        required_fields = ['username', 'email', 'password']
        
        # Validate required fields
        errors = {}
        for field in required_fields:
            if not data.get(field):
                errors[field] = 'Required'
        
        if errors:
            return api_response(
                message='Validation failed',
                status_code=400,
                errors=errors
            )
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return api_response(
                message='Email already registered',
                status_code=409,
                errors={'email': 'Email already exists'}
            )
        
        if User.query.filter_by(username=data['username']).first():
            return api_response(
                message='Username already taken',
                status_code=409,
                errors={'username': 'Username already exists'}
            )
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', ''),
            role='user'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return api_response(
            data={
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            },
            message='User registered successfully',
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        from app.logging_config import log_error
        log_error(current_app, e, "API registration error")
        return api_response(message='Internal server error', status_code=500)

# Tours Endpoints
@api_bp.route('/tours', methods=['GET'])
@rate_limit(requests_per_minute=100)  # Higher limit for read operations
def api_tours_list():
    """
    Get list of tours with pagination and filtering.
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', 'active')
        
        # Build query
        query = Tour.query
        
        if status == 'active':
            query = query.filter_by(status='active')
        elif status:
            query = query.filter_by(status=status)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search:
            query = query.filter(
                Tour.title.contains(search) | 
                Tour.description.contains(search)
            )
        
        # Order by creation date
        query = query.order_by(Tour.created_at.desc())
        
        # Paginate
        result = paginate_query(query, page, per_page)
        
        # Format tours data
        tours_data = []
        for tour in result['items']:
            tours_data.append({
                'id': tour.id,
                'title': tour.title,
                'description': tour.description,
                'price': float(tour.price),
                'duration': tour.duration,
                'max_participants': tour.max_participants,
                'available_spots': tour.available_spots,
                'departure_date': tour.departure_date.isoformat() if tour.departure_date else None,
                'return_date': tour.return_date.isoformat() if tour.return_date else None,
                'location': tour.location,
                'difficulty_level': tour.difficulty_level,
                'category': {
                    'id': tour.category.id,
                    'name': tour.category.name
                } if tour.category else None,
                'status': tour.status,
                'image_url': f"/static/images/tours/{tour.image_filename}" if tour.image_filename else None,
                'created_at': tour.created_at.isoformat()
            })
        
        return api_response(data={
            'tours': tours_data,
            'pagination': result['pagination']
        })
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, "API tours list error")
        
        # Handle specific database errors
        if 'database' in str(e).lower() or 'operational' in str(e).lower():
            return api_response(message='Database error', status_code=503)
        
        return api_response(message='Internal server error', status_code=500)

@api_bp.route('/tours/<int:tour_id>', methods=['GET'])
@rate_limit(requests_per_minute=100)
def api_tour_detail(tour_id):
    """
    Get detailed information about a specific tour.
    """
    try:
        tour = Tour.query.get(tour_id)
        if not tour:
            return api_response(message='Tour not found', status_code=404)
        
        # Get tour reviews
        reviews = Review.query.filter_by(tour_id=tour_id, is_approved=True).all()
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'user': {
                    'username': review.user.username
                },
                'created_at': review.created_at.isoformat()
            })
        
        tour_data = {
            'id': tour.id,
            'title': tour.title,
            'description': tour.description,
            'price': float(tour.price),
            'duration': tour.duration,
            'max_participants': tour.max_participants,
            'available_spots': tour.available_spots,
            'departure_date': tour.departure_date.isoformat() if tour.departure_date else None,
            'return_date': tour.return_date.isoformat() if tour.return_date else None,
            'location': tour.location,
            'difficulty_level': tour.difficulty_level,
            'category': {
                'id': tour.category.id,
                'name': tour.category.name,
                'description': tour.category.description
            } if tour.category else None,
            'status': tour.status,
            'image_url': f"/static/images/tours/{tour.image_filename}" if tour.image_filename else None,
            'inclusions': tour.inclusions,
            'exclusions': tour.exclusions,
            'itinerary': tour.itinerary,
            'requirements': tour.requirements,
            'reviews': reviews_data,
            'average_rating': tour.average_rating,
            'total_reviews': len(reviews_data),
            'created_at': tour.created_at.isoformat()
        }
        
        return api_response(data={'tour': tour_data})
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, f"API tour detail error for tour {tour_id}")
        
        # Handle specific database errors
        if 'database' in str(e).lower() or 'operational' in str(e).lower():
            return api_response(message='Database error', status_code=503)
        
        return api_response(message='Internal server error', status_code=500)

# Categories Endpoints
@api_bp.route('/categories', methods=['GET'])
@rate_limit(requests_per_minute=100)
def api_categories_list():
    """
    Get list of tour categories.
    """
    try:
        categories = Category.query.filter_by(is_active=True).all()
        
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'image_url': f"/static/images/categories/{category.image_filename}" if category.image_filename else None,
                'tour_count': category.tours.filter_by(status='active').count()
            })
        
        return api_response(data={'categories': categories_data})
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, "API categories list error")
        return api_response(message='Internal server error', status_code=500)

# Bookings Endpoints
@api_bp.route('/bookings', methods=['GET'])
@rate_limit(requests_per_minute=60)
@api_auth_required
def api_bookings_list():
    """
    Get user's bookings.
    """
    try:
        user = request.current_user
        bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
        
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'tour': {
                    'id': booking.tour.id,
                    'title': booking.tour.title,
                    'departure_date': booking.tour.departure_date.isoformat() if booking.tour.departure_date else None,
                    'location': booking.tour.location
                },
                'participants': booking.participants,
                'total_cost': float(booking.total_cost),
                'status': booking.status,
                'booking_date': booking.booking_date.isoformat(),
                'special_requests': booking.special_requests,
                'created_at': booking.created_at.isoformat()
            })
        
        return api_response(data={'bookings': bookings_data})
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, "API bookings list error")
        return api_response(message='Internal server error', status_code=500)

@api_bp.route('/bookings', methods=['POST'])
@rate_limit(requests_per_minute=20)  # More restrictive for creation
@api_auth_required
@validate_json
def api_create_booking():
    """
    Create a new booking.
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['tour_id', 'participants']
        errors = {}
        for field in required_fields:
            if not data.get(field):
                errors[field] = 'Required'
        
        if errors:
            return api_response(
                message='Validation failed',
                status_code=400,
                errors=errors
            )
        
        tour_id = data['tour_id']
        participants = data['participants']
        
        # Validate tour
        tour = Tour.query.get(tour_id)
        if not tour or tour.status != 'active':
            return api_response(
                message='Tour not found or not available',
                status_code=404
            )
        
        # Check availability
        if tour.available_spots < participants:
            return api_response(
                message='Not enough spots available',
                status_code=400,
                errors={'participants': f'Only {tour.available_spots} spots available'}
            )
        
        # Create booking
        booking = Booking(
            user_id=user.id,
            tour_id=tour_id,
            participants=participants,
            total_cost=tour.price * participants,
            booking_date=tour.departure_date,
            special_requests=data.get('special_requests', ''),
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return api_response(
            data={
                'booking': {
                    'id': booking.id,
                    'tour_id': booking.tour_id,
                    'participants': booking.participants,
                    'total_cost': float(booking.total_cost),
                    'status': booking.status,
                    'created_at': booking.created_at.isoformat()
                }
            },
            message='Booking created successfully',
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        from app.logging_config import log_error
        log_error(current_app, e, "API create booking error")
        return api_response(message='Internal server error', status_code=500)

@api_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@rate_limit(requests_per_minute=60)
@api_auth_required
def api_booking_detail(booking_id):
    """
    Get detailed information about a specific booking.
    """
    try:
        user = request.current_user
        booking = Booking.query.filter_by(id=booking_id, user_id=user.id).first()
        
        if not booking:
            return api_response(message='Booking not found', status_code=404)
        
        booking_data = {
            'id': booking.id,
            'tour': {
                'id': booking.tour.id,
                'title': booking.tour.title,
                'description': booking.tour.description,
                'departure_date': booking.tour.departure_date.isoformat() if booking.tour.departure_date else None,
                'return_date': booking.tour.return_date.isoformat() if booking.tour.return_date else None,
                'location': booking.tour.location,
                'duration': booking.tour.duration
            },
            'participants': booking.participants,
            'total_cost': float(booking.total_cost),
            'status': booking.status,
            'booking_date': booking.booking_date.isoformat(),
            'special_requests': booking.special_requests,
            'emergency_contact_name': booking.emergency_contact_name,
            'emergency_contact_phone': booking.emergency_contact_phone,
            'dietary_requirements': booking.dietary_requirements,
            'created_at': booking.created_at.isoformat(),
            'updated_at': booking.updated_at.isoformat() if booking.updated_at else None
        }
        
        return api_response(data={'booking': booking_data})
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, f"API booking detail error for booking {booking_id}")
        return api_response(message='Internal server error', status_code=500)

# User Profile Endpoints
@api_bp.route('/profile', methods=['GET'])
@rate_limit(requests_per_minute=60)
@api_auth_required
def api_user_profile():
    """
    Get user profile information.
    """
    try:
        user = request.current_user
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'bio': user.bio,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        
        return api_response(data={'user': user_data})
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, "API user profile error")
        return api_response(message='Internal server error', status_code=500)

# Search Endpoints
@api_bp.route('/search', methods=['GET'])
@rate_limit(requests_per_minute=60)
def api_search():
    """
    Global search across tours and categories.
    """
    try:
        query_text = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query_text:
            return api_response(
                message='Search query required',
                status_code=400,
                errors={'q': 'Search query is required'}
            )
        
        # Search tours
        tours_query = Tour.query.filter(
            Tour.status == 'active',
            (Tour.title.contains(query_text) | 
             Tour.description.contains(query_text) |
             Tour.location.contains(query_text))
        ).order_by(Tour.created_at.desc())
        
        result = paginate_query(tours_query, page, per_page)
        
        # Format results
        tours_data = []
        for tour in result['items']:
            tours_data.append({
                'id': tour.id,
                'title': tour.title,
                'description': tour.description[:200] + '...' if len(tour.description) > 200 else tour.description,
                'price': float(tour.price),
                'duration': tour.duration,
                'location': tour.location,
                'difficulty_level': tour.difficulty_level,
                'image_url': f"/static/images/tours/{tour.image_filename}" if tour.image_filename else None
            })
        
        return api_response(data={
            'results': tours_data,
            'pagination': result['pagination'],
            'query': query_text
        })
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, "API search error")
        return api_response(message='Internal server error', status_code=500)

# Health Check Endpoint
@api_bp.route('/health', methods=['GET'])
@rate_limit(requests_per_minute=30)
def api_health():
    """
    API health check endpoint.
    """
    try:
        # Simple database connectivity check
        db.session.execute('SELECT 1')
        
        return api_response(data={
            'status': 'healthy',
            'version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        })
        
    except Exception as e:
        from app.logging_config import log_error
        log_error(current_app, e, "API health check error")
        return api_response(
            message='Service unhealthy',
            status_code=503,
            data={'database': 'disconnected'}
        )

# API Documentation Endpoint
@api_bp.route('/docs', methods=['GET'])
@rate_limit(requests_per_minute=20)
def api_documentation():
    """
    API documentation endpoint.
    """
    docs = get_api_documentation()
    return api_response(data=docs)

# Error handlers for API
@api_bp.errorhandler(404)
def api_not_found(error):
    return api_response(message='Endpoint not found', status_code=404)

@api_bp.errorhandler(405)
def api_method_not_allowed(error):
    return api_response(message='Method not allowed', status_code=405)

@api_bp.errorhandler(500)
def api_internal_error(error):
    return api_response(message='Internal server error', status_code=500)
