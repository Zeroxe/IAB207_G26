from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from sqlalchemy.exc import IntegrityError
from .models import User
from .forms import LoginForm, RegisterForm
from . import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    error = None
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user is None:
            error = 'Incorrect username'
        elif not check_password_hash(user.password_hash, password):
            error = 'Incorrect password'
        if error is None:
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash(error)
    return render_template('user.html', form=login_form, heading='Login')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        firstName = form.firstName.data
        surname = form.surname.data
        phoneNumber = form.mobileNumber.data
        address = form.streetAddress.data
        pwd = form.password.data
        email = form.email.data

        existing_user_email = db.session.scalar(db.select(User).where(User.email == email))
        existing_user_mobile = db.session.scalar(db.select(User).where(User.mobileNumber == phoneNumber))

        if existing_user_email:
            flash('Email already registered, please try another')
            return redirect(url_for('auth.register'))

        if existing_user_mobile:
            flash('Mobile number already registered, please try another')
            return redirect(url_for('auth.register'))

        pwd_hash = generate_password_hash(pwd)
        new_user = User(firstName=firstName, surname=surname, mobileNumber=phoneNumber, streetAddress=address, password_hash=pwd_hash, email=email)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('You successfully registered your account')
            return redirect(url_for('main.index'))
        except IntegrityError as e:
            db.session.rollback()
            error_message = str(e.orig).lower()
            if 'email' in error_message:
                flash('Email already registered, please try another')
            elif 'mobile' in error_message or 'phone' in error_message:
                flash('Mobile number already registered, please try another')
            else:
                flash('Registration failed due to duplicate information. Please check your details.')
            return redirect(url_for('auth.register'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.')
            return redirect(url_for('auth.register'))
    else:
        return render_template('user.html', form=form, heading='Register')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
