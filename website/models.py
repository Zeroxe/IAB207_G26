from . import db
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), index=True, unique=False, nullable=False)
    surname = db.Column(db.String(100), index=True, unique=False, nullable=False)
    email = db.Column(db.String(100), index=True, nullable=False, unique=True)
    mobileNumber = db.Column(db.String(15), index=True, nullable=False, unique=True)
    streetAddress = db.Column(db.String(150), index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='attendee')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    events_created = db.relationship('Event', foreign_keys='Event.created_by', backref='creator_user', lazy='dynamic')

    def __repr__(self):
        return f"User: {self.firstName} {self.surname} ({self.role})"

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    events = db.relationship('Event', backref='genre_info', lazy='dynamic')

    def __repr__(self):
        return f"Genre: {self.name}"

class ticket_type(db.Model):
    __tablename__ = 'ticket_type'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    type_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"Ticket Type: {self.type_name} - ${self.price} ({self.quantity_available} available)"

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    start_datetime = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    venue = db.Column(db.String(100), nullable=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=False)
    artist_info = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Open', nullable=False)
    age_limit = db.Column(db.Integer, nullable=True)
    length = db.Column(db.String(50), nullable=True)
    policies = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticket_types = db.relationship('ticket_type', backref='event', lazy='dynamic', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='event', lazy='dynamic', cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='event', lazy='dynamic', cascade="all, delete-orphan")

    @property
    def current_status(self):
        if self.status == 'Cancelled':
            return 'Cancelled'
        if self.status == 'Completed':
            return 'Completed'
        if self.start_datetime and self.start_datetime < datetime.now():
            return 'Inactive'
        if self.ticket_types:
            total_available = sum(ticket.quantity_available for ticket in self.ticket_types)
            if total_available == 0:
                return 'Sold Out'
        return 'Open'

    def __repr__(self):
        return f"Event: {self.name}"

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(400), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    edited_at = db.Column(db.DateTime, nullable=True)
    is_edited = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

    def __repr__(self):
        return f"Comment: {self.text[:50]}..."

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    order_status = db.Column(db.String(20), default='pending', nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    user = db.relationship('User', backref='orders')
    event = db.relationship('Event', backref='orders')
    order_items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan")

    def __repr__(self):
        return f"Order #{self.id} - {self.order_status} (${self.total_amount})"

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey('ticket_type.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    ticket_type = db.relationship('ticket_type', backref='order_items')

    def __repr__(self):
        return f"OrderItem: {self.quantity}x {self.ticket_type.type_name if self.ticket_type else 'Unknown'}"

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey('ticket_type.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    booking_status = db.Column(db.String(20), default='confirmed', nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    ticket_type_booked = db.relationship('ticket_type', backref='bookings')
    order = db.relationship('Order', backref='bookings')

    def __repr__(self):
        return f"Booking #{self.id} - {self.quantity} tickets for event {self.event_id} ({self.booking_status})"

class event_status(db.Model):
    __tablename__ = 'event_status'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    status_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"Status: {self.status} on {self.status_date}"