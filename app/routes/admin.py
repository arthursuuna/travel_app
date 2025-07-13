"""
Admin blueprint for the Travel App.
This module handles all admin-related routes including inquiry management, user management, and system administration.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import db, Inquiry, User, UserRole, Tour, Booking
from app.decorators import admin_required
from app.forms import InquiryResponseForm, InquiryAssignForm, InquiryFilterForm
from app.utils import send_email
from sqlalchemy import or_, desc
from datetime import datetime

# Create admin blueprint
admin_inquiry_bp = Blueprint("admin_inquiry", __name__, url_prefix="/admin")


@admin_inquiry_bp.route("/")
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard with overview statistics.
    """
    # Get inquiry statistics
    total_inquiries = Inquiry.query.count()
    new_inquiries = Inquiry.query.filter_by(status="new").count()
    urgent_inquiries = Inquiry.query.filter(
        (Inquiry.priority == "urgent") | 
        ((Inquiry.status != "resolved") & (Inquiry.status != "closed"))
    ).count()
    
    # Get recent inquiries
    recent_inquiries = Inquiry.query.order_by(desc(Inquiry.created_at)).limit(5).all()
    
    # Get system statistics
    total_users = User.query.count()
    total_tours = Tour.query.count()
    total_bookings = Booking.query.count()
    
    return render_template(
        "admin/dashboard.html",
        total_inquiries=total_inquiries,
        new_inquiries=new_inquiries,
        urgent_inquiries=urgent_inquiries,
        recent_inquiries=recent_inquiries,
        total_users=total_users,
        total_tours=total_tours,
        total_bookings=total_bookings,
        title="Admin Dashboard"
    )


@admin_inquiry_bp.route("/inquiries")
@login_required
@admin_required
def inquiries():
    """
    Manage all customer inquiries.
    """
    # Initialize filter form
    filter_form = InquiryFilterForm()
    
    # Populate admin users for assignment dropdown
    admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
    filter_form.assigned_to_id.choices = [(None, "All Admins")] + [
        (admin.id, admin.full_name) for admin in admin_users
    ]
    
    # Start with base query
    query = Inquiry.query
    
    # Apply filters from request args
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    inquiry_type = request.args.get("inquiry_type", "")
    assigned_to_id = request.args.get("assigned_to_id", "")
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    
    # Set form defaults
    filter_form.status.data = status
    filter_form.priority.data = priority
    filter_form.inquiry_type.data = inquiry_type
    filter_form.assigned_to_id.data = int(assigned_to_id) if assigned_to_id else None
    filter_form.search.data = search
    
    # Apply filters
    if status:
        query = query.filter(Inquiry.status == status)
    if priority:
        query = query.filter(Inquiry.priority == priority)
    if inquiry_type:
        query = query.filter(Inquiry.inquiry_type == inquiry_type)
    if assigned_to_id:
        query = query.filter(Inquiry.assigned_to_id == assigned_to_id)
    if search:
        query = query.filter(
            or_(
                Inquiry.subject.contains(search),
                Inquiry.message.contains(search),
                Inquiry.name.contains(search),
                Inquiry.email.contains(search)
            )
        )
    
    # Order by urgency and date
    query = query.order_by(
        desc(Inquiry.priority == "urgent"),
        desc(Inquiry.status == "new"),
        desc(Inquiry.created_at)
    )
    
    # Paginate results
    inquiries = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get counts for statistics
    status_counts = {
        "new": Inquiry.query.filter_by(status="new").count(),
        "in_progress": Inquiry.query.filter_by(status="in_progress").count(),
        "resolved": Inquiry.query.filter_by(status="resolved").count(),
        "closed": Inquiry.query.filter_by(status="closed").count(),
    }
    
    return render_template(
        "admin/inquiries.html",
        inquiries=inquiries,
        filter_form=filter_form,
        status_counts=status_counts,
        admin_users=admin_users,
        title="Manage Inquiries"
    )


@admin_inquiry_bp.route("/inquiries/<int:id>")
@login_required
@admin_required
def inquiry_detail(id):
    """
    View detailed information about a specific inquiry.
    """
    inquiry = Inquiry.query.get_or_404(id)
    
    # Initialize response form
    response_form = InquiryResponseForm()
    response_form.status.data = inquiry.status
    response_form.priority.data = inquiry.priority
    
    # Initialize assignment form
    assign_form = InquiryAssignForm()
    admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
    assign_form.assigned_to_id.choices = [(None, "Unassigned")] + [
        (admin.id, admin.full_name) for admin in admin_users
    ]
    assign_form.assigned_to_id.data = inquiry.assigned_to_id
    
    return render_template(
        "admin/inquiry_detail.html",
        inquiry=inquiry,
        response_form=response_form,
        assign_form=assign_form,
        admin_users=admin_users,
        title=f"Inquiry: {inquiry.subject}"
    )


@admin_inquiry_bp.route("/inquiries/<int:id>/respond", methods=["POST"])
@login_required
@admin_required
def respond_to_inquiry(id):
    """
    Respond to a customer inquiry.
    """
    inquiry = Inquiry.query.get_or_404(id)
    response_form = InquiryResponseForm()
    
    if response_form.validate_on_submit():
        try:
            # Update inquiry
            inquiry.admin_response = response_form.response.data
            inquiry.internal_notes = response_form.internal_notes.data
            inquiry.status = response_form.status.data
            inquiry.priority = response_form.priority.data
            inquiry.last_response_at = datetime.utcnow()
            inquiry.response_count += 1
            
            # Mark as resolved if status is resolved or closed
            if inquiry.status in ["resolved", "closed"]:
                inquiry.is_resolved = True
                if not inquiry.resolved_at:
                    inquiry.resolved_at = datetime.utcnow()
            else:
                inquiry.is_resolved = False
                inquiry.resolved_at = None
            
            db.session.commit()
            
            # Send email response if requested
            if response_form.send_email.data and response_form.response.data:
                subject = f"Re: {inquiry.subject}"
                
                html_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #007bff;">Travel App</h1>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <h2 style="color: #333; margin-top: 0;">Response to Your Inquiry</h2>
                        <p>Dear {inquiry.name},</p>
                        <p>Thank you for contacting Travel App. Here's our response to your inquiry:</p>
                    </div>
                    
                    <div style="background: #ffffff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0;">{response_form.response.data.replace(chr(10), '<br>')}</p>
                    </div>
                    
                    <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #004085;">
                            <strong>Original Inquiry:</strong><br>
                            <strong>Subject:</strong> {inquiry.subject}<br>
                            <strong>Date:</strong> {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}
                        </p>
                    </div>
                    
                    <p style="color: #6c757d; font-size: 14px;">
                        If you have any further questions, please don't hesitate to contact us.
                    </p>
                    
                    <hr style="margin: 30px 0; border: 1px solid #e9ecef;">
                    
                    <div style="text-align: center; color: #6c757d; font-size: 12px;">
                        <p>Travel App Customer Support<br>
                        <a href="mailto:support@travelapp.com" style="color: #007bff;">support@travelapp.com</a></p>
                    </div>
                </div>
                """
                
                body = f"""Dear {inquiry.name},

Thank you for contacting Travel App. Here's our response to your inquiry:

{response_form.response.data}

Original Inquiry:
Subject: {inquiry.subject}
Date: {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}

If you have any further questions, please don't hesitate to contact us.

Best regards,
Travel App Customer Support
support@travelapp.com
"""
                
                send_email(subject, [inquiry.email], body, html_body)
                flash("Response sent and email notification delivered!", "success")
            else:
                flash("Inquiry updated successfully!", "success")
                
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the inquiry.", "danger")
    else:
        # Log validation errors for debugging
        if response_form.errors:
            for field, errors in response_form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", "danger")
        else:
            flash("Please correct the errors in the form.", "danger")
    
    return redirect(url_for("admin_inquiry.inquiry_detail", id=id))


@admin_inquiry_bp.route("/inquiries/<int:id>/assign", methods=["POST"])
@login_required
@admin_required
def assign_inquiry(id):
    """
    Assign an inquiry to an admin user.
    """
    inquiry = Inquiry.query.get_or_404(id)
    assign_form = InquiryAssignForm()
    
    # Populate choices
    admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
    assign_form.assigned_to_id.choices = [(None, "Unassigned")] + [
        (admin.id, admin.full_name) for admin in admin_users
    ]
    
    if assign_form.validate_on_submit():
        try:
            inquiry.assigned_to_id = assign_form.assigned_to_id.data if assign_form.assigned_to_id.data else None
            
            # Update status to in_progress if assigning and currently new
            if inquiry.assigned_to_id and inquiry.status == "new":
                inquiry.status = "in_progress"
            
            db.session.commit()
            
            assigned_to = User.query.get(inquiry.assigned_to_id) if inquiry.assigned_to_id else None
            if assigned_to:
                flash(f"Inquiry assigned to {assigned_to.full_name}!", "success")
            else:
                flash("Inquiry unassigned!", "success")
                
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while assigning the inquiry.", "danger")
    
    return redirect(url_for("admin_inquiry.inquiry_detail", id=id))


@admin_inquiry_bp.route("/inquiries/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_inquiry(id):
    """
    Delete an inquiry (admin only).
    """
    inquiry = Inquiry.query.get_or_404(id)
    
    try:
        subject = inquiry.subject
        db.session.delete(inquiry)
        db.session.commit()
        flash(f'Inquiry "{subject}" deleted successfully!', "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the inquiry.", "danger")
    
    return redirect(url_for("admin_inquiry.inquiries"))


@admin_inquiry_bp.route("/inquiries/bulk-action", methods=["POST"])
@login_required
@admin_required
def bulk_inquiry_action():
    """
    Perform bulk actions on multiple inquiries.
    """
    action = request.form.get("action")
    inquiry_ids = request.form.getlist("inquiry_ids")
    
    if not inquiry_ids:
        flash("No inquiries selected.", "warning")
        return redirect(url_for("admin_inquiry.inquiries"))
    
    try:
        inquiries = Inquiry.query.filter(Inquiry.id.in_(inquiry_ids)).all()
        
        if action == "mark_resolved":
            for inquiry in inquiries:
                inquiry.status = "resolved"
                inquiry.is_resolved = True
                inquiry.resolved_at = datetime.utcnow()
            flash(f"{len(inquiries)} inquiries marked as resolved.", "success")
            
        elif action == "mark_in_progress":
            for inquiry in inquiries:
                inquiry.status = "in_progress"
                inquiry.is_resolved = False
                inquiry.resolved_at = None
            flash(f"{len(inquiries)} inquiries marked as in progress.", "success")
            
        elif action == "set_high_priority":
            for inquiry in inquiries:
                inquiry.priority = "high"
            flash(f"{len(inquiries)} inquiries set to high priority.", "success")
            
        elif action == "delete":
            for inquiry in inquiries:
                db.session.delete(inquiry)
            flash(f"{len(inquiries)} inquiries deleted.", "success")
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while performing the bulk action.", "danger")
    
    return redirect(url_for("admin_inquiry.inquiries"))


@admin_inquiry_bp.route("/api/inquiry-stats")
@login_required
@admin_required
def inquiry_stats_api():
    """
    API endpoint for inquiry statistics (for dashboard widgets).
    """
    stats = {
        "total": Inquiry.query.count(),
        "new": Inquiry.query.filter_by(status="new").count(),
        "in_progress": Inquiry.query.filter_by(status="in_progress").count(),
        "resolved": Inquiry.query.filter_by(status="resolved").count(),
        "urgent": Inquiry.query.filter_by(priority="urgent").count(),
        "unassigned": Inquiry.query.filter_by(assigned_to_id=None).count(),
    }
    
    return jsonify(stats)
