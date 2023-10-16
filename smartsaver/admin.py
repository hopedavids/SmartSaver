import sys
import os

# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from flask import Blueprint, render_template
from models import User, Wallet, Payment, Contact, Donation


admin = Blueprint('admin', __name__)

@admin.route('/webmaster')
def admin_login():
    return render_template('admin/login.html')


@admin.route('/webmaster/user-management')
def user_management():
    user = User.query.all()
    return render_template('admin/admin.html', users=user)


@admin.route('/webmaster/wallet-management')
def wallet_management():
    wallet = Wallet.query.all()
    return render_template('admin/user_wallet.html', wallets=wallet)

@admin.route('/webmaster/contact-management')
def contact_management():
    contact = Contact.query.all()
    return render_template('admin/user_contact.html', contacts=contact)

@admin.route('/webmaster/payment-management')
def payment_management():
    payment = Payment.query.all()
    return render_template('admin/user_payment.html', payments=payment)

@admin.route('/webmaster/donations-management')
def donation_management():
    donation = Donation.query.all()

    return render_template('admin/user_donations.html', donations=donation)