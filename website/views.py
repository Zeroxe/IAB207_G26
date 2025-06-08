from flask import Blueprint, render_template, request, session, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .models import Event, Booking, Order, OrderItem, User
from .forms import ChangePasswordForm, ProfileUpdateForm
from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import check_password_hash, generate_password_hash
from . import db
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    active_events = Event.query.filter(
        Event.status.notin_(['Cancelled', 'Inactive']),
        Event.start_datetime > datetime.now()
    ).order_by(Event.start_datetime.asc()).all()

    return render_template('index.html', events=active_events)

@main_bp.route('/booking_history')
@login_required
def booking_history():
    user_orders = Order.query.filter_by(user_id=current_user.id).join(Event).order_by(desc(Order.order_date)).all()
    created_events = Event.query.filter_by(created_by=current_user.id).order_by(desc(Event.created_at)).all()

    order_history = []
    for order in user_orders:
        status = 'Event Cancelled' if order.event.current_status == 'Cancelled' else (
            'Event Completed' if order.event.current_status == 'Inactive' else order.order_status
        )
        order_details = {
            'id': order.id,
            'type': 'order',
            'event': order.event,
            'booking_date': order.order_date,
            'status': status,
            'total_price': order.total_amount,
            'order_items': order.order_items
        }
        order_history.append(order_details)

    event_summary = []
    for event in created_events:
        confirmed_bookings = [booking for booking in event.bookings if booking.booking_status == 'confirmed']
        total_bookings = sum(booking.quantity for booking in confirmed_bookings)
        total_revenue = sum(float(booking.total_price) for booking in confirmed_bookings)
        available_tickets = sum(ticket.quantity_available for ticket in event.ticket_types)

        event_details = {
            'event': event,
            'created_date': event.created_at,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'available_tickets': available_tickets,
            'status': event.current_status
        }
        event_summary.append(event_details)

    return render_template('events/booking_history.html', booking_history=order_history, creation_history=event_summary)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileUpdateForm(original_mobile=current_user.mobileNumber)

    if form.validate_on_submit():
        try:
            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash('The current password you entered is incorrect. Please try again.', 'danger')
                return render_template('auth/user_profile.html', form=form)

            changes = []

            if form.mobileNumber.data != current_user.mobileNumber:
                current_user.mobileNumber = form.mobileNumber.data
                changes.append('mobile number')

            if form.streetAddress.data != current_user.streetAddress:
                current_user.streetAddress = form.streetAddress.data
                changes.append('address')

            if form.new_password.data:
                current_user.password_hash = generate_password_hash(form.new_password.data)
                changes.append('password')

            current_user.updated_at = datetime.now()
            db.session.commit()

            if changes:
                flash(f"Your {', '.join(changes)} {'has' if len(changes) == 1 else 'have'} been updated successfully.", 'success')
            else:
                flash('No changes were made to your profile.', 'info')

            return redirect(url_for('main.profile'))

        except IntegrityError as e:
            db.session.rollback()
            if 'mobileNumber' in str(e):
                flash('The mobile number you entered is already associated with another account.', 'danger')
            else:
                flash('An error occurred while updating your profile. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

    if request.method == 'GET':
        form.firstName.data = current_user.firstName
        form.surname.data = current_user.surname
        form.email.data = current_user.email
        form.mobileNumber.data = current_user.mobileNumber
        form.streetAddress.data = current_user.streetAddress

    return render_template('auth/user_profile.html', form=form)