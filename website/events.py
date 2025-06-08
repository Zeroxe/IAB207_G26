from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
    session,
)
from .models import Event, Comment, ticket_type, Order, OrderItem, Booking, User, Genre
from .forms import (
    EventForm,
    TicketForm,
    CommentForm,
    CheckoutForm,
    BookingForm,
    EditCommentForm,
)
from . import db
import os
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from decimal import Decimal
from datetime import datetime

eventbp = Blueprint("event", __name__, url_prefix="/events")


@eventbp.route("/<int:id>")
def details(id):
    event = db.session.query(Event).filter_by(id=id).first()
    if not event:
        abort(404)
    cform = CommentForm()
    comments = event.comments.order_by(Comment.created_at.desc()).all()
    return render_template(
        "events/event_Details.html", event=event, form=cform, comments=comments
    )


@eventbp.route("/eventspage")
def allevents():
    search_text = request.args.get("search", "").strip()
    genre_filter = request.args.get("genre", "")
    query = Event.query

    if genre_filter:
        genre = Genre.query.filter_by(name=genre_filter).first()
        if genre:
            query = query.filter_by(genre_id=genre.id)

    if search_text:
        query = query.filter(
            (Event.name.ilike(f"%{search_text}%"))
            | (Event.description.ilike(f"%{search_text}%"))
        )

    events = query.order_by(Event.start_datetime.asc()).all()
    genres = db.session.scalars(db.select(Genre)).all()

    return render_template(
        "events/allevents.html",
        events=events,
        genres=genres,
        selected_genre=genre_filter,
        search_text=search_text,
    )


def check_upload_file(uploaded_file_data):
    if not uploaded_file_data or not uploaded_file_data.filename:
        return None

    filename = secure_filename(uploaded_file_data.filename)
    upload_folder_abs = os.path.join(current_app.root_path, "static", "img", "events")

    if not os.path.exists(upload_folder_abs):
        os.makedirs(upload_folder_abs, exist_ok=True)

    upload_path_abs = os.path.join(upload_folder_abs, filename)

    try:
        uploaded_file_data.save(upload_path_abs)

        db_upload_path = os.path.join("img", "events", filename).replace(os.sep, "/")
        flash(f"Image uploaded successfully: {filename}", "success")
        return db_upload_path
    except Exception as e:
        current_app.logger.error(f"Failed to save uploaded file: {e}")
        flash(f"Error uploading image: {str(e)}", "danger")
        return None


@eventbp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = EventForm()
    ticketform = TicketForm()

    try:
        genres = db.session.scalars(db.select(Genre)).all()
        form.genre.choices = [(genre.id, genre.name) for genre in genres]
    except Exception as e:
        current_app.logger.error("Error loading genres for event creation")
        flash("Error loading page data. Please check genre setup.", "danger")
        form.genre.choices = []

    if request.method == "POST":
        if form.validate() and ticketform.validate():
            image_filename_to_save = None
            if form.image.data and form.image.data.filename:
                image_filename_to_save = check_upload_file(form.image.data)
            elif form.image_url.data and form.image_url.data.strip():
                image_filename_to_save = form.image_url.data.strip()

            new_event = Event(
                name=form.name.data,
                description=form.description.data,
                image_filename=image_filename_to_save,
                start_datetime=form.start_datetime.data,
                location=form.location.data,
                venue=form.venue.data,
                genre_id=form.genre.data,
                created_by=current_user.id,
                status="Open",
                age_limit=form.age_limit.data,
                length=form.length.data,
                artist_info=form.artist_info.data,
                policies=form.policies.data,
            )
            try:
                db.session.add(new_event)
                db.session.flush()
                if (
                    ticketform.general_price.data is not None
                    and ticketform.general_quantity.data is not None
                ):
                    general_ticket = ticket_type(
                        event_id=new_event.id,
                        type_name="General Admission",
                        price=ticketform.general_price.data,
                        quantity_available=ticketform.general_quantity.data,
                    )
                    db.session.add(general_ticket)
                if (
                    ticketform.vip_price.data is not None
                    and ticketform.vip_quantity.data is not None
                ):
                    vip_ticket = ticket_type(
                        event_id=new_event.id,
                        type_name="VIP",
                        price=ticketform.vip_price.data,
                        quantity_available=ticketform.vip_quantity.data,
                    )
                    db.session.add(vip_ticket)

                db.session.commit()
                flash(f'Event "{new_event.name}" created successfully!', "success")
                return redirect(url_for("event.details", id=new_event.id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating event: {e}")
                flash(f"Error creating event: {str(e)}", "danger")
    return render_template(
        "events/event_Creation.html",
        form=form,
        ticketform=ticketform,
        title="Create New Event",
    )


@eventbp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(id):
    event_to_edit = db.session.query(Event).filter_by(id=id).first_or_404()

    if event_to_edit.created_by != current_user.id:
        flash("You are not authorized to edit this event.", "danger")
        return redirect(url_for("event.details", id=id))

    form = EventForm()
    ticketform = TicketForm()

    if request.method == "GET":
        form.name.data = event_to_edit.name
        form.description.data = event_to_edit.description
        form.start_datetime.data = event_to_edit.start_datetime
        form.location.data = event_to_edit.location
        form.venue.data = event_to_edit.venue
        form.age_limit.data = event_to_edit.age_limit
        form.length.data = event_to_edit.length
        form.artist_info.data = event_to_edit.artist_info
        form.policies.data = event_to_edit.policies

        if event_to_edit.image_filename and event_to_edit.image_filename.startswith(
            "http"
        ):
            form.image_url.data = event_to_edit.image_filename

    try:
        genres = db.session.scalars(db.select(Genre)).all()
        form.genre.choices = [(genre.id, genre.name) for genre in genres]
    except Exception:
        current_app.logger.error(f"Could not load database")
        flash("Error loading database")
        form.genre.choices = []

    if request.method == "POST":
        if form.validate() and ticketform.validate():
            current_image_filename = event_to_edit.image_filename
            form.populate_obj(event_to_edit)

            image_filename_to_save = current_image_filename

            if form.image.data and form.image.data.filename:
                new_image_filename = check_upload_file(form.image.data)
                if new_image_filename:
                    image_filename_to_save = new_image_filename

            elif form.image_url.data and form.image_url.data.strip():
                image_filename_to_save = form.image_url.data.strip()

            event_to_edit.image_filename = image_filename_to_save

            ticket_types_to_update = {
                "General Admission": (
                    ticketform.general_price.data,
                    ticketform.general_quantity.data,
                ),
                "VIP": (ticketform.vip_price.data, ticketform.vip_quantity.data),
            }

            for type_name_key, (
                price_data,
                limit_data,
            ) in ticket_types_to_update.items():
                existing_ticket = event_to_edit.ticket_types.filter_by(
                    type_name=type_name_key
                ).first()
                if price_data is not None and limit_data is not None:
                    if existing_ticket:
                        sold_tickets = sum(
                            booking.quantity
                            for booking in existing_ticket.bookings
                            if booking.booking_status == "confirmed"
                        )

                        if limit_data < sold_tickets:
                            flash(
                                f"Cannot set {type_name_key} quantity to {limit_data}. {sold_tickets} tickets have already been sold.",
                                "danger",
                            )
                            return render_template(
                                "events/event_edit.html",
                                form=form,
                                ticketform=ticketform,
                                event_id=event_to_edit.id,
                                event=event_to_edit,
                                title=f"Edit Event: {event_to_edit.name}",
                            )

                        existing_ticket.price = float(price_data)
                        existing_ticket.quantity_available = limit_data - sold_tickets
                    else:
                        new_ticket = ticket_type(
                            event_id=event_to_edit.id,
                            type_name=type_name_key,
                            price=float(price_data),
                            quantity_available=limit_data,
                        )
                        db.session.add(new_ticket)
                elif existing_ticket:
                    sold_tickets = sum(
                        booking.quantity
                        for booking in existing_ticket.bookings
                        if booking.booking_status == "confirmed"
                    )
                    if sold_tickets > 0:
                        flash(
                            f"Cannot remove {type_name_key} tickets. {sold_tickets} tickets have already been sold.",
                            "danger",
                        )
                        return render_template(
                            "events/event_edit.html",
                            form=form,
                            ticketform=ticketform,
                            event_id=event_to_edit.id,
                            event=event_to_edit,
                            title=f"Edit Event: {event_to_edit.name}",
                        )
                    db.session.delete(existing_ticket)
            try:
                db.session.commit()
                flash(f'Event "{event_to_edit.name}" updated successfully!', "success")
                return redirect(url_for("event.details", id=event_to_edit.id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error updating event: {e}")
                flash(f"Error updating event: {str(e)}", "danger")
    return render_template(
        "events/event_edit.html",
        form=form,
        ticketform=ticketform,
        event_id=event_to_edit.id,
        event=event_to_edit,
        title=f"Edit Event: {event_to_edit.name}",
    )


@eventbp.route("/<int:id>/cancel_confirm", methods=["GET"])
@login_required
def cancel_confirm(id):
    event = db.session.query(Event).filter_by(id=id).first_or_404()
    if event.created_by != current_user.id:
        flash("You are not authorized to cancel this event.", "danger")
        return redirect(url_for("event.details", id=id))
    if event.status == "Cancelled":
        flash("This event has already been cancelled.", "info")
        return redirect(url_for("event.details", id=id))
    return render_template(
        "events/cancel_confirm.html", event=event, csrf_token=generate_csrf
    )


@eventbp.route("/<int:id>/cancel_confirmed", methods=["POST"])
@login_required
def cancel_event_confirmed(id):
    event = db.session.query(Event).filter_by(id=id).first_or_404()
    if event.created_by != current_user.id:
        flash("You are not authorized to cancel this event.", "danger")
        return redirect(url_for("event.details", id=id))
    if event.status == "Cancelled":
        flash("This event has already been cancelled.", "info")
        return redirect(url_for("event.details", id=id))
    try:
        event.status = "Cancelled"
        db.session.commit()
        flash(f'The event "{event.name}" has been successfully cancelled.', "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cancelling event: {e}")
        flash(f"Error cancelling event: {str(e)}", "danger")
    return redirect(url_for("event.details", id=id))


@eventbp.route("/<int:id>/comment", methods=["POST"])
@login_required
def comment(id):
    form = CommentForm()
    event = db.session.query(Event).filter_by(id=id).first_or_404()
    if form.validate_on_submit():
        new_comment = Comment(
            text=form.text.data, event_id=event.id, user_id=current_user.id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Your comment has been added successfully.", "success")
    else:
        for field, errors_list in form.errors.items():
            for error in errors_list:
                flash(f"Error in {getattr(form, field).label.text}: {error}", "danger")
    return redirect(url_for("event.details", id=id))


@eventbp.route("/<int:event_id>/comment/<int:comment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_comment(event_id, comment_id):
    comment = db.session.query(Comment).filter_by(id=comment_id).first_or_404()
    event = db.session.query(Event).filter_by(id=event_id).first_or_404()

    if comment.user_id != current_user.id:
        flash("You can only edit your own comments.", "danger")
        return redirect(url_for("event.details", id=event_id))

    form = EditCommentForm()

    if request.method == "GET":
        form.text.data = comment.text

    if form.validate_on_submit():
        comment.text = form.text.data
        comment.edited_at = datetime.now()
        comment.is_edited = True
        db.session.commit()
        flash("Your comment has been updated successfully.", "success")
        return redirect(url_for("event.details", id=event_id))

    return render_template(
        "events/edit_comment.html", form=form, comment=comment, event=event
    )


@eventbp.route("/<int:event_id>/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(event_id, comment_id):
    comment = db.session.query(Comment).filter_by(id=comment_id).first_or_404()

    if comment.user_id != current_user.id:
        flash("You can only delete your own comments.", "danger")
        return redirect(url_for("event.details", id=event_id))

    db.session.delete(comment)
    db.session.commit()
    flash("Your comment has been deleted successfully.", "success")
    return redirect(url_for("event.details", id=event_id))


@eventbp.route("/<int:id>/book", methods=["GET", "POST"])
@login_required
def book_tickets(id):
    event = db.session.query(Event).filter_by(id=id).first_or_404()
    form = BookingForm()
    if event.current_status in ["Cancelled", "Sold Out", "Completed", "Inactive"]:
        flash(
            f"Sorry, this event is {event.current_status.lower()} and not available for booking.",
            "warning",
        )
        return redirect(url_for("event.details", id=id))
    ticket_types = event.ticket_types.filter(ticket_type.quantity_available > 0).all()
    if not ticket_types:
        flash("Sorry, there are no tickets available for this event.", "warning")
        return redirect(url_for("event.details", id=id))
    if form.validate_on_submit():
        cart_items = []
        total_amount = Decimal("0.00")
        for ticket in ticket_types:
            quantity_field = f"quantity_{ticket.id}"
            quantity = request.form.get(quantity_field, type=int)
            if quantity and quantity > 0:
                if quantity > ticket.quantity_available:
                    flash(
                        f"Sorry, only {ticket.quantity_available} {ticket.type_name} tickets are available.",
                        "danger",
                    )
                    return render_template(
                        "events/ticket_booking.html",
                        event=event,
                        ticket_types=ticket_types,
                        form=form,
                    )
            if quantity > 10:
                flash("Maximum 10 tickets per type per transaction.", "danger")
                return render_template(
                    "events/ticket_booking.html",
                    event=event,
                    ticket_types=ticket_types,
                    form=form,
                )
            subtotal = Decimal(str(ticket.price)) * quantity
            cart_items.append(
                {
                    "ticket_type_id": ticket.id,
                    "ticket_type_name": ticket.type_name,
                    "price": Decimal(str(ticket.price)),
                    "quantity": quantity,
                    "subtotal": subtotal,
                }
            )
            total_amount += subtotal

        if not cart_items:
            flash("Please select at least one ticket to proceed.", "warning")
            return render_template(
                "events/ticket_booking.html",
                event=event,
                ticket_types=ticket_types,
                form=form,
            )
        try:
            order = Order(
                user_id=current_user.id,
                event_id=event.id,
                total_amount=total_amount,
                order_status="confirmed",
            )
            db.session.add(order)
            db.session.flush()
            for item in cart_items:
                ticket = (
                    db.session.query(ticket_type)
                    .filter_by(id=item["ticket_type_id"])
                    .first()
                )
                if not ticket or ticket.quantity_available < item["quantity"]:
                    raise ValueError(
                        f"Insufficient tickets available for {item['ticket_type_name']}"
                    )
                order_item = OrderItem(
                    order_id=order.id,
                    ticket_type_id=item["ticket_type_id"],
                    quantity=item["quantity"],
                    unit_price=item["price"],
                    subtotal=item["subtotal"],
                )
                db.session.add(order_item)
                ticket.quantity_available -= item["quantity"]
                booking = Booking(
                    user_id=current_user.id,
                    event_id=event.id,
                    order_id=order.id,
                    ticket_type_id=item["ticket_type_id"],
                    quantity=item["quantity"],
                    total_price=item["subtotal"],
                    booking_status="confirmed",
                )
                db.session.add(booking)
            remaining_tickets = sum(t.quantity_available for t in event.ticket_types)
            if remaining_tickets == 0:
                event.status = "Sold Out"
            db.session.commit()
            flash(
                f'🎉 Congratulations! Your booking for "{event.name}" has been confirmed!',
                "success",
            )
            return redirect(
                url_for("event.booking_confirmation", id=event.id, order_id=order.id)
            )
        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")
            return render_template(
                "events/ticket_booking.html",
                event=event,
                ticket_types=ticket_types,
                form=form,
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Booking error: {e}")
            flash(
                "Sorry, there was an error processing your booking. Please try again.",
                "danger",
            )
            return render_template(
                "events/ticket_booking.html",
                event=event,
                ticket_types=ticket_types,
                form=form,
            )
    return render_template(
        "events/ticket_booking.html", event=event, ticket_types=ticket_types, form=form
    )


@eventbp.route("/<int:id>/checkout", methods=["GET", "POST"])
@login_required
def checkout(id):
    event = db.session.query(Event).filter_by(id=id).first_or_404()

    cart = session.get("cart")
    if not cart or cart.get("event_id") != event.id:
        flash(
            "Your cart is empty or has expired. Please select tickets again.", "warning"
        )
        return redirect(url_for("event.book_tickets", id=id))

    form = CheckoutForm()

    if form.validate_on_submit():
        try:
            order = Order(
                user_id=current_user.id,
                event_id=event.id,
                total_amount=Decimal(str(cart["total_amount"])),
                order_status="pending",
            )
            db.session.add(order)
            db.session.flush()

            for item in cart["items"]:
                ticket = (
                    db.session.query(ticket_type)
                    .filter_by(id=item["ticket_type_id"])
                    .first()
                )
                if not ticket or ticket.quantity_available < item["quantity"]:
                    raise ValueError(
                        f"Insufficient tickets available for {item['ticket_type_name']}"
                    )

                order_item = OrderItem(
                    order_id=order.id,
                    ticket_type_id=item["ticket_type_id"],
                    quantity=item["quantity"],
                    unit_price=item["price"],
                    subtotal=item["subtotal"],
                )
                db.session.add(order_item)

                ticket.quantity_available -= item["quantity"]

                booking = Booking(
                    user_id=current_user.id,
                    event_id=event.id,
                    order_id=order.id,
                    ticket_type_id=item["ticket_type_id"],
                    quantity=item["quantity"],
                    total_price=item["subtotal"],
                    booking_status="confirmed",
                )
                db.session.add(booking)

            order.order_status = "confirmed"

            remaining_tickets = sum(t.quantity_available for t in event.ticket_types)
            if remaining_tickets == 0:
                event.status = "Sold Out"

            db.session.commit()

            session.pop("cart", None)

            flash(
                f'🎉 Congratulations! Your booking for "{event.name}" has been confirmed!',
                "success",
            )
            return redirect(
                url_for("event.booking_confirmation", id=event.id, order_id=order.id)
            )

        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")
            return redirect(url_for("event.book_tickets", id=id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Booking error: {e}")
            flash(
                "Sorry, there was an error processing your booking. Please try again.",
                "danger",
            )
            return redirect(url_for("event.book_tickets", id=id))

    return render_template("events/checkout.html", event=event, cart=cart, form=form)


@eventbp.route("/<int:id>/booking_confirmation/<int:order_id>")
@login_required
def booking_confirmation(id, order_id):
    event = db.session.query(Event).filter_by(id=id).first_or_404()
    order = (
        db.session.query(Order)
        .filter_by(id=order_id, user_id=current_user.id)
        .first_or_404()
    )

    order_items = []
    for item in order.order_items:
        order_items.append(
            {
                "ticket_type_name": item.ticket_type.type_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
        )

    return render_template(
        "events/booking_confirmation.html",
        event=event,
        order=order,
        order_items=order_items,
    )


@eventbp.route("/cart/clear")
@login_required
def clear_cart():
    session.pop("cart", None)
    flash("Your cart has been cleared.", "info")
    return redirect(request.referrer or url_for("event.allevents"))
