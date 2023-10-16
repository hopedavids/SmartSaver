import sys
import os

# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from models import User, Wallet
from instances import db, mail, csrf
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import re, random

load_dotenv('.env')


user_auth = Blueprint('user_auth', __name__)



@user_auth.route('/account/signin', methods=['GET', 'POST'])
def signin():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            remember = request.form.get('remember', False)

            user = User.query.filter_by(username=username).first()
            
            if not username or not password:
                flash('Enter a valid username and password', 'warning')
                return redirect(url_for('user_auth.signin'))

            if user and not check_password_hash(user.password, password):
                flash("Invalid username or password", 'danger')
                return redirect(url_for('user_auth.signin'))

            elif not user:    
                flash("Enter a valid username or password", 'danger')
                return redirect(url_for('user_auth.signin'))

            else:
                if user.email_confirm == True:

                    login_user(user, remember=remember)
                    user = current_user
                    flash("Login successful, welcome back", 'success')
                    return redirect(url_for('main.index'))
                
                flash("Your account is not Verified", 'warning')
                    
        return render_template('backend/accounts/signin.html')
    
    except Exception as e:
        error = "{}".format(str(e))
        print(error)
        return render_template('backend/accounts/signin.html')



@user_auth.route('/account/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm password']

            user = User.query.filter_by(email=email).first()
            
            if not username or not email or not password:
                flash('Kindly fill all fields!', 'danger')
                return redirect(url_for('user_auth.register'))
            
            if username.isupper() or email.isupper():
                flash('Email and Username must be lowercase!', 'danger')
                return redirect(url_for('user_auth.register'))

            if user:
                flash('username or email taken', 'danger')

                return redirect(url_for('user_auth.register'))

            if password:
                if password != confirm_password:
                    flash('Passwords do not match', 'danger')

                    return redirect(url_for('user_auth.register'))

            
                minimum_length = 8

                if len(password) < minimum_length:
                    flash('Password should be at least {} characters long'.format(minimum_length), 'error')
                    return redirect(url_for('user_auth.register'))

                if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
                    flash('Password should contain alphanumeric', 'danger')

                    return redirect(url_for('user_auth.register'))
        
            new_user = User(username=username, email=email, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

            #email verfication
            otp = generate_otp()
            send_otp(email, otp)
            session['otp'] = otp

            flash('Enter the code sent to your email here', 'info')
            return redirect(url_for('user_auth.confirm'))
        
        return render_template('backend/accounts/register.html')

    except Exception as e:
        error = '{}'.format(str(e))
        flash(error, 'danger')
        return render_template('backend/accounts/register.html')



def generate_otp():
    otp = ''.join([str(random.randint(0, 9)) for i in range(6)])
    return otp


def send_otp(email, otp):
    message = Message('One Time Password', sender=os.environ.get('MAIL_SENDER'), recipients=[email])
    message.body = 'Your OTP is: {}'.format(otp)
    mail.send(message)

    session['email'] = email



@user_auth.route('/account/confirm', methods=['GET', 'POST'])
def confirm():
    # email = request.args.get('email')
    # otp = request.args.get('otp')
    if request.method == 'POST':
        # email = request.args.get('email')
        otp = request.form.get('otp')
        
        stored_otp = session.get('otp')
        email = session.get('email')

        if otp == stored_otp:
            # Find the user in the database
            user = User.query.filter_by(email=email).first()

            if user:
                # Update the user's account status to True which indicates verified
                user.email_confirm = True
                db.session.commit()

                # create a wallet for the user account
                wallet = Wallet(user_id=user.id)
                db.session.add(wallet)
                db.session.commit()
                # send a notification to the user indicating account has been verified
                flash('Your account has been verified. Kindly Signin', 'success')
                # redirect the user to signin after verification
                return redirect(url_for('user_auth.signin'))
            else:
                # send a warning notification to the user
                flash('User not found.', 'warning')
        else:
            # send a warning notification to the user
            flash('Invalid OTP.', 'danger')
    
    # if the request method is not POST, then the page below is rendered
    return render_template('backend/accounts/verification.html')




@user_auth.route('/account/signout')
@login_required
def signout():
    """signout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()

    flash('You are Signout', 'warning')
    return redirect(url_for('user_auth.signin'))


@user_auth.route('/account/password-reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        email = request.form['email']

        # check if email is valid and registered in the database
        user = User.query.filter_by(email=email).first()

        if user.email_confirm is True:
            #email verfication
            otp = generate_otp()
            send_otp(email, otp)
            session['otp'] = otp
            return redirect(url_for('user_auth.verify'))
        
        flash('sorry, your email account is not valid with us', 'danger')

    return render_template('backend/accounts/reset_password.html')


@user_auth.route('/account/verify-email', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':

        # email = request.args.get('email')
        otp = request.form.get('otp')
        
        stored_otp = session.get('otp')
        email = session.get('email')

        if otp == stored_otp:
            flash('Email has been confirmed!, reset password now', 'success')
            return redirect(url_for('user_auth.change_password'))

    return render_template('backend/accounts/email_verify.html')


@user_auth.route('/account/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('password does not match', 'danger')

        minimum_length = 8

        if len(password) < minimum_length:
            flash('Password should be at least {} characters long'.format(minimum_length), 'error')
            return redirect(url_for('user_auth.register'))

        if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            flash('Password should contain alphanumeric', 'danger')
            return redirect(url_for('user_auth.register'))

        # get the email from the session
        email = session.get('email')
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(password)

        db.session.commit()

        flash('Your password was reset successfully', 'alert')
        return redirect(url_for('user_auth.signin'))

    return render_template('backend/accounts/change_password.html')
