import os, sys, random
from datetime import datetime
from dotenv import load_dotenv
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO
from flask_mail import Message

# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from instances import db, mail, csrf
from models import Wallet, Donation, Contact, Payment


main = Blueprint('main', __name__)


load_dotenv('.env')


@main.route('/eco-donate')
def landing_page():
    return render_template('frontend/land-page.html')



@main.route('/profile', methods = ['GET', 'POST'])
@login_required
def index():
    # derive the user id from the user session
    user_id = current_user.id

    user = current_user.username
    user_email = current_user.email
    user_creation = current_user.created_date
    created_user_format = user_creation.strftime("%B %d, %Y %H:%M:%S")

    wallet = Wallet.query.filter_by(user_id=user_id).first()
    
    if wallet is None:
        # Handle the case when the wallet doesn't exist
        # For example, you can create a new wallet for the user
        wallet = Wallet(user_id=user_id, current_balance=0, previous_balance=0)
        db.session.add(wallet)
        db.session.commit()
    
    wallet_id = wallet.wallet_id
    current_balance = wallet.current_balance
    previous_balance = wallet.previous_balance

    created_at = wallet.created_at
    created_date_format = created_at.strftime("%B %d, %Y %H:%M:%S")
    
    updated_at = wallet.updated_at
    updated_date_format = updated_at.strftime("%B %d, %Y %H:%M:%S")

    try:
        if request.method == 'POST':
            amount = request.form['amount']
            region = request.form['region']
            tree_spieces = request.form['spieces']
            description = request.form['description']
            get_certified = request.form.get('get_certified', False)

            number_of_trees = amount
            minimum_length = 20

            # contact details
            fullname = request.form['fullname']
            address = request.form['address']
            country = request.form['country']
            about_me = request.form['aboutme']
        
            if any(len(text) < minimum_length for text in ([description, about_me])):
                flash("description should be more than 20 words", 'danger')
                return redirect(url_for("main.index"))

            if (not fullname or not address or not country or not about_me or not description):
                flash('kindly fill all fields correctly', 'danger')
                return redirect(url_for("main.index"))
            
            if any(text.isupper() for text in [fullname,country, address, about_me, description]):
                flash("kindly use alphanumeric or lowercase", 'danger')
                return redirect(url_for("main.index"))

            
            if amount:
                # check if amount is matches or less than the wallet balance
                if float(amount) > current_balance:
                    flash("Dear Donor, you have insufficient Fund in your account", 'warning')
                    return redirect(url_for("main.index"))
                
            # make the donotion happen
            current_balance -= int(amount)
            wallet.current_balance = current_balance

            donation = Donation(
                            user_id=user_id, 
                            amount=amount,
                            region_to_plant=region,
                            tree_spieces=tree_spieces,
                            number_of_trees=number_of_trees,
                            description=description
                            )

            contact = Contact(
                            user_id=user_id,
                            full_name=fullname,
                            address=address,
                            country=country,
                            about_me=about_me
                            )

            db.session.add_all([wallet, donation, contact])
            db.session.commit()

            # query the donation object to retrieve the id
            donation = Donation.query.filter_by(user_id=user_id).first()

            donate_wallet = os.environ.get('DONATE_WALLET')
            payment = Payment(
                        wallet_id=donate_wallet, 
                        amount=amount, 
                        donation_id=donation.donation_id
                        )

            wallet=Wallet.query.filter_by(wallet_id=donate_wallet).first()
            wallet.current_balance = amount

            db.session.add_all([payment, wallet])
            db.session.commit()

            

            flash("Congratulations! Your tree planting donations was successful!!", 'success')

            return redirect(url_for('main.gratitude'))

        tree_images = ['tree.jpeg', 'tree1.jpg', 'tree3.jpg', 'tree4.jpg', 'tree5.jpg', 'tree6.jpg', 'tree7.jpg', 'tree8.jpg']

        random_tree = random.choice(tree_images)

        return render_template('backend/index.html',
                                tree=random_tree,
                                user=user,
                                email=user_email,
                                created_date=created_user_format,
                                wallet_id=wallet_id,
                                current_balance=current_balance,
                                previous_balance=previous_balance,
                                created_at=created_date_format,
                                updated_at=updated_date_format
                                )
    except Exception as e:
        # flash('fatal error caught from exeptions: {}'.format(str(e)), 'danger')
        error = 'Error -> {}'.format(str(e))
        print(error)
        return redirect(url_for("main.transaction"))


@main.route('/transactions')
@login_required
def transaction():
    page = request.args.get('page', 1, type=int)
    user_id = current_user.id
    user = current_user.username
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.contact_id.desc()).paginate(page=page, per_page=2)
    donations = Donation.query.filter_by(user_id=user_id).order_by(Donation.donation_id.desc()).paginate(page=page, per_page=2)
    
    offset_donations = Donation.query.filter_by(user_id=user_id).order_by(Donation.donation_id.desc()).all()
    wallets = Wallet.query.filter_by(user_id=user_id).all()
    
    transaction = zip(wallets, offset_donations)
    data = zip(donations, contacts)

    return render_template('backend/pages/tables.html', data=data, transactions=transaction, user=user)


@main.route('/thank-you')
@login_required
def gratitude():
    
    user = current_user.username

    return render_template('backend/pages/thank-you.html', user=user)


@main.route('/view-certificate')
@login_required
def view_certificate():
    # query the contact object for the full name
    user_id = current_user.id

    contact = Contact.query.filter_by(user_id=user_id).order_by(Contact.contact_id.desc()).first()
    donation = Donation.query.filter_by(user_id=user_id).order_by(Donation.donation_id.desc()).first()

    # Obtain data for the certificate (e.g., recipient's name, donation amount)
    recipient_name = contact.full_name
    country = contact.country
    donation_amount = '$'+ str(donation.amount)
    region_to_plant = 'in ' + donation.region_to_plant
    certify_date = 'Date: ' + datetime.now().strftime("%B %d, %Y")

    # Generate the certificate content
    generate_certificate_content(recipient_name, country, donation_amount, region_to_plant, certify_date)

    # get the file path
    filepath = 'certify/certificate.pdf'

    # Return the PDF file to the user for viewing in the browser
    return send_file(filepath, mimetype='application/pdf', as_attachment=False)


@main.route('/mail-certificate')
@login_required
def email_certificate():
    try:
        # query the contact object for the full name
        user_id = current_user.id
        email = current_user.email
        contact = Contact.query.filter_by(user_id=user_id).order_by(Contact.contact_id.desc()).first()
        donation = Donation.query.filter_by(user_id=user_id).order_by(Donation.donation_id.desc()).first()


        # Obtain data for the certificate (e.g., recipient's name, donation amount)
        recipient_name = contact.full_name
        country = contact.country
        donation_amount = '$'+ str(donation.amount)
        region_to_plant = 'in ' + donation.region_to_plant
        certify_date = 'Date: ' + datetime.now().strftime("%B %d, %Y")

        # Generate the certificate content
        pdf_buffer = generate_certificate_content(recipient_name, country, donation_amount, region_to_plant, certify_date)

        # get the file path
        filepath = 'certify/certificate.pdf'

        # Send the certificate as an email attachment
        send_certificate(email, filepath)

        # Return a response to the user
        flash("The certificate has been successfully sent to your email", "success")
        return redirect(url_for('main.gratitude'))
    
    except Exception as e:
        error = "{}".format(str(e))
        print(error)
        flash("The was an error in email transit", "danger")
        return redirect(url_for('main.gratitude'))


def send_certificate(email, filepath):
    with open(filepath, 'rb') as file:
        pdf_content = file.read()

    message = Message("Certificate of Donation", sender=os.environ.get('MAIL_SENDER'), recipients=[email])
    message.attach("certificate.pdf", "application/pdf", pdf_content)
    mail.send(message)


def generate_certificate_content(recipient_name, country, donation_amount, region_to_plant, certify_date):
    pdf_buffer = BytesIO()

    # Create a new PDF file
    pdf = canvas.Canvas('certify/certificate.pdf', pagesize=letter)


    # Set up the certificate layout
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(letter[0] / 2, 8 * inch, "ECO-DONATE")

    pdf.drawCentredString(letter[0] / 2, 7 * inch, "Certificate of Donation")

    # Add nice designs to the edges of the sheet
    pdf.setStrokeColorRGB(0.2, 0.5, 0.7)
    pdf.setLineWidth(3)
    pdf.line(0.5 * inch, 0.5 * inch, 0.5 * inch, letter[1] - 0.5 * inch)
    pdf.line(letter[0] - 0.5 * inch, 0.5 * inch, letter[0] - 0.5 * inch, letter[1] - 0.5 * inch)
    pdf.line(0.5 * inch, 0.5 * inch, letter[0] - 0.5 * inch, 0.5 * inch)
    pdf.line(0.5 * inch, letter[1] - 0.5 * inch, letter[0] - 0.5 * inch, letter[1] - 0.5 * inch)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(letter[0] / 2, 6 * inch, "This is to certify that")
    pdf.drawCentredString(letter[0] / 2, 5.5 * inch, recipient_name)
    pdf.drawCentredString(letter[0] / 2, 5 * inch, country)

    pdf.drawCentredString(letter[0] / 2, 4 * inch, "has generously donated")
    pdf.drawCentredString(letter[0] / 2, 3.5 * inch, donation_amount)
    pdf.drawCentredString(letter[0] / 2, 2.8 * inch, "towards the cause of planting trees and combating climate change")
    pdf.drawCentredString(letter[0] / 2, 2.5 * inch, region_to_plant)

    pdf.setFont("Helvetica-Oblique", 12)
    pdf.drawCentredString(letter[0] / 2, 1.5 * inch, certify_date)

    # Save and close the PDF file
    pdf.save()

    # Move the buffer's file pointer to the beginning of the buffer
    pdf_buffer.seek(0)

    return pdf_buffer
