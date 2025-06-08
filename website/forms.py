from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields import (
    TextAreaField,
    SubmitField,
    StringField,
    PasswordField,
    DateField,
    TimeField,
    IntegerField,
    SelectField,
    DateTimeLocalField,
    DecimalField,
    HiddenField,
    FieldList,
    FormField,
    BooleanField,
)
from wtforms.validators import (
    InputRequired,
    Length,
    Email,
    EqualTo,
    Regexp,
    NumberRange,
    ValidationError,
    Optional,
    URL,
)
from datetime import datetime


class LoginForm(FlaskForm):
    email = StringField(
        "Email Address",
        validators=[InputRequired(), Email("Please enter a valid email")],
    )
    password = PasswordField(
        "Password", validators=[InputRequired("Enter user password")]
    )
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    firstName = StringField("First Name", validators=[InputRequired(), Length(max=100)])
    surname = StringField("Surname", validators=[InputRequired(), Length(max=100)])
    email = StringField(
        "Email Address",
        validators=[
            InputRequired(),
            Email("Please enter a valid email"),
            Length(max=100),
        ],
    )
    mobileNumber = StringField(
        "Mobile Number",
        validators=[
            InputRequired(),
            Length(min=7, max=15, message="Field must be between 7 and 15 characters."),
            Regexp(
                r"^\+?[0-9\s\-()]*$",
                message="Please only input valid phone characters.",
            ),
        ],
    )
    streetAddress = StringField(
        "Street Address", validators=[InputRequired(), Length(max=150)]
    )
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            EqualTo("confirm", message="Passwords should match"),
            Regexp(
                r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,}$',
                message="Password must be at least 8 characters and contain at least one uppercase letter, one symbol, and one number.",
            ),
        ],
    )
    confirm = PasswordField("Confirm Password", validators=[InputRequired()])
    submit = SubmitField("Register")


class TicketTypeForm(FlaskForm):
    type_name = StringField(
        "Ticket Type Name (e.g., General, VIP)",
        validators=[InputRequired(), Length(max=100)],
    )
    price = DecimalField(
        "Price ($)",
        validators=[
            InputRequired(),
            NumberRange(min=0, message="Price cannot be negative."),
        ],
        places=2,
    )
    quantity_available = IntegerField(
        "Number of Tickets Available",
        validators=[
            InputRequired(),
            NumberRange(min=1, message="Must be a positive number."),
        ],
    )
    description = TextAreaField(
        "Ticket Description", validators=[Optional(), Length(max=500)]
    )


class EventForm(FlaskForm):
    name = StringField(
        "Event Name",
        validators=[InputRequired(message="Please name your event."), Length(max=120)],
    )
    description = TextAreaField(
        "Event Description", validators=[Optional(), Length(max=2000)]
    )
    image = FileField(
        "Main Event Image",
        validators=[
            Optional(),
            FileAllowed(
                [
                    ".jpg, .png, .jpeg only. This will be the main image for your event display."
                ]
            ),
        ],
    )
    image_url = StringField("Or Image URL", validators=[Optional(), URL()])
    start_datetime = DateTimeLocalField(
        "Start Date and Time", format="%Y-%m-%dT%H:%M", validators=[InputRequired()]
    )
    location = StringField("Location", validators=[InputRequired(), Length(max=100)])
    venue = StringField("Venue Name", validators=[Optional(), Length(max=100)])
    genre = SelectField(
        "Genre",
        coerce=int,
        validators=[InputRequired(message="Please select the appropriate genre")],
    )
    artist_info = TextAreaField(
        "Artist Details", validators=[Optional(), Length(max=2000)]
    )
    age_limit = IntegerField(
        "Age Limit (Enter 0 for all ages))",
        validators=[Optional(), NumberRange(min=0, max=99)],
    )
    length = StringField(
        "Show Length (e.g 3 Hours)", validators=[Optional(), Length(max=50)]
    )
    policies = TextAreaField("Event Rules", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Create Event")

    def validate_start_datetime(self, field):
        if field.data and field.data <= datetime.now():
            raise ValidationError("Event start date and time must be in the future.")


class TicketForm(FlaskForm):
    general_price = DecimalField(
        "General Ticket Price ($)",
        validators=[
            Optional(),
            NumberRange(min=0, message="Price cannot be negative."),
        ],
        places=2,
    )
    general_quantity = IntegerField(
        "Total General Tickets (including sold)",
        validators=[
            Optional(),
            NumberRange(min=1, message="Must be a positive number."),
        ],
    )
    general_description = TextAreaField(
        "General Ticket Description", validators=[Optional(), Length(max=500)]
    )
    vip_price = DecimalField(
        "VIP Ticket Price ($)",
        validators=[
            Optional(),
            NumberRange(min=0, message="Price cannot be negative."),
        ],
        places=2,
    )
    vip_quantity = IntegerField(
        "Total VIP Tickets (including sold)",
        validators=[
            Optional(),
            NumberRange(min=1, message="Must be a positive number."),
        ],
    )
    vip_description = TextAreaField(
        "VIP Ticket Description", validators=[Optional(), Length(max=500)]
    )

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        validation_passed = True
        if not self.general_price.data and not self.vip_price.data:
            self.general_price.errors.append(
                "At least one ticket type must be provided."
            )
            validation_passed = False
        if self.general_price.data and not self.general_quantity.data:
            self.general_quantity.errors.append(
                "Quantity is required when price is specified."
            )
            validation_passed = False
        if self.vip_price.data and not self.vip_quantity.data:
            self.vip_quantity.errors.append(
                "Quantity is required when price is specified."
            )
            validation_passed = False
        return validation_passed


class OrderItemForm(FlaskForm):
    ticket_type_id = HiddenField("Ticket Type ID", validators=[InputRequired()])
    quantity = IntegerField(
        "Quantity",
        validators=[
            InputRequired(),
            NumberRange(min=1, max=10, message="Quantity must be between 1 and 10"),
        ],
    )


class CartForm(FlaskForm):
    event_id = HiddenField("Event ID", validators=[InputRequired()])
    items = FieldList(FormField(OrderItemForm), min_entries=0)
    submit = SubmitField("Add to Cart")


class CheckoutForm(FlaskForm):
    special_notes = TextAreaField(
        "Special Notes or Requests", validators=[Optional(), Length(max=500)]
    )
    agree_terms = BooleanField(
        "I agree to the terms and conditions",
        validators=[
            InputRequired(message="You must agree to the terms and conditions")
        ],
    )
    submit = SubmitField("Complete Purchase")


class BookingSearchForm(FlaskForm):
    booking_id = IntegerField("Booking ID", validators=[Optional()])
    user_email = StringField("User Email", validators=[Optional(), Email()])
    event_name = StringField("Event Name", validators=[Optional(), Length(max=120)])
    booking_status = SelectField(
        "Booking Status",
        choices=[
            ("", "All Statuses"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        validators=[Optional()],
    )
    date_from = DateField("From Date", validators=[Optional()])
    date_to = DateField("To Date", validators=[Optional()])
    submit = SubmitField("Search")


class CommentForm(FlaskForm):
    text = TextAreaField(
        "Comment",
        validators=[
            InputRequired("Please enter a comment"),
            Length(
                min=1, max=400, message="Comment must be between 1 and 400 characters"
            ),
        ],
    )
    submit = SubmitField("Post Comment")

    def validate_text(self, field):
        if field.data and field.data.strip() == "":
            raise ValidationError("Comment cannot be empty or just whitespace")
        if field.data and len(field.data.strip()) < 1:
            raise ValidationError("Comment must contain at least one character")


class EventStatusForm(FlaskForm):
    status = SelectField(
        "Event Status",
        choices=[
            ("Open", "Open"),
            ("Sold Out", "Sold Out"),
            ("Cancelled", "Cancelled"),
            ("Completed", "Completed"),
        ],
        validators=[InputRequired()],
    )
    reason = TextAreaField(
        "Reason for Status Change", validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField("Update Status")


class BookingForm(FlaskForm):
    submit = SubmitField("Proceed to Checkout")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[InputRequired("Please enter your current password")],
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            InputRequired("Please enter a new password"),
            EqualTo("confirm_password", message="Passwords should match"),
            Regexp(
                r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,}$',
                message="Password must be at least 8 characters and contain at least one uppercase letter, one symbol, and one number.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[InputRequired("Please confirm your new password")],
    )
    submit = SubmitField("Change Password")


class ProfileUpdateForm(FlaskForm):
    firstName = StringField("First Name", render_kw={"readonly": True})
    surname = StringField("Surname", render_kw={"readonly": True})
    email = StringField("Email Address", render_kw={"readonly": True})
    mobileNumber = StringField(
        "Mobile Number",
        validators=[
            InputRequired("Mobile number is required"),
            Length(
                min=7,
                max=15,
                message="Mobile number must be between 7 and 15 characters.",
            ),
            Regexp(
                r"^\+?[0-9\s\-()]*$",
                message="Please enter a valid phone number (numbers, spaces, +, -, () only).",
            ),
        ],
    )
    streetAddress = StringField(
        "Street Address",
        validators=[
            InputRequired("Street address is required"),
            Length(
                min=5, max=150, message="Address must be between 5 and 150 characters."
            ),
        ],
    )
    current_password = PasswordField(
        "Current Password (required to save changes)",
        validators=[
            InputRequired("Please enter your current password to save changes")
        ],
    )
    new_password = PasswordField(
        "New Password (leave blank to keep current)",
        validators=[
            Optional(),
            EqualTo("confirm_password", message="New passwords must match"),
            Regexp(
                r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,}$',
                message="Password must be at least 8 characters and contain at least one uppercase letter, one symbol, and one number.",
            ),
        ],
    )
    confirm_password = PasswordField("Confirm New Password", validators=[Optional()])
    submit = SubmitField("Update Profile")

    def __init__(self, original_mobile=None, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_mobile = original_mobile

    def validate_mobileNumber(self, field):
        if field.data != self.original_mobile:
            from .models import User

            existing_user = User.query.filter_by(mobileNumber=field.data).first()
            if existing_user:
                raise ValidationError(
                    "This mobile number is already registered to another account."
                )

    def validate_new_password(self, field):
        if field.data and not self.confirm_password.data:
            raise ValidationError("Please confirm your new password.")
        if not field.data and self.confirm_password.data:
            raise ValidationError(
                "Please enter a new password or leave both password fields blank."
            )


class EditCommentForm(FlaskForm):
    text = TextAreaField(
        "Edit Comment",
        validators=[
            InputRequired("Please enter a comment"),
            Length(
                min=1, max=400, message="Comment must be between 1 and 400 characters"
            ),
        ],
    )
    submit = SubmitField("Update Comment")

    def validate_text(self, field):
        if field.data and field.data.strip() == "":
            raise ValidationError("Comment cannot be empty or just whitespace")
        if field.data and len(field.data.strip()) < 1:
            raise ValidationError("Comment must contain at least one character")
