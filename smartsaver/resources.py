import sys
import os

# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from flask import jsonify, request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from instances import db, login_manager, csrf, api
from api_models import authorizations, user_model, user_creation_model, user_login_model, wallet_model, wallet_create_model, payment_model, contact_model, contact_update_model, donation_model, donation_update_model
from api_auth import login
from models import User, Wallet, Payment, Contact, Donation


"""In this module, namespaces are defined and including the routes and views
    which are also defined here and associated with the models module.
"""




# define namespaces for the views
auth_ns = Namespace('authenticate', description="Login Endpoint", authorizations=authorizations)
user_ns = Namespace('user', description="All user operations.", authorizations=authorizations)
wallet_ns = Namespace('wallet', description="Wallet information", authorizations=authorizations)
pay_ns = Namespace('payment', description="All payments operations", authorizations=authorizations)
contact_ns = Namespace('contact', description="All Contact informations", authorizations=authorizations)
donation_ns = Namespace('donation', description="Donations operation", authorizations=authorizations)
# api_ns = Namespace('api', description='API namespace')





@login_manager.user_loader
def load_user(user_id):
    return User.query.get((user_id))


@auth_ns.route('')
class Authentication(Resource):
    """ Login Endpoint to access the endpoint and api resources.
        This allows users to retrieve a JWT which gives access
        to all eco_donate resources
    """

    @user_ns.expect(user_login_model)
    def post(self):
        """ This allows users to retrieve a JWT which gives access.
        """
        try:
            payload = request.get_json()
            username = api.payload['username']
            password = api.payload['password']

            user = User.query.filter_by(username=username).first()

            if not username or  not password:
                return {
                    "data": "null",
                    "message": "Username or Password Incorrect",
                    "status": "api-error"
                }, 400

            # Check if username is an email
            elif '@' in username:
                return {
                    "data": "null",
                    "message": "Username or Password Incorrect",
                    "status": "api-error"
                }, 400

            elif not user or not check_password_hash(user.password, password):
                return {
                    "data": "null",
                    "message": "Username or Password Incorrect",
                    "status": "api-error"
                }, 400

            access_token = create_access_token(identity=username)
            return {
                "username": username,
                "access_token": access_token
                }, 200

        except Exception as e:
            return {
                "data": "Null",
                "message": "error {}".format(str(e)),
                "error": "api-error"
                }, 400



@user_ns.route('')
class Users(Resource):
    """This defines the routes and views for
       POST and GET requests for the User Object.
    """

    @user_ns.doc(security="basicAuth")
    @user_ns.marshal_list_with(user_model)
    @jwt_required()
    def get(self):
        """ This method handles the GET HTTP method and returns
            response in a serialized way.
        """
        try:
            user = User.query.all()

            return user, 200
        
        except Exception as e:
            return ({
                "data": "Null",
                "message": "Error {}".format(str(e)),
                "status": "api-error"
            })

    
    @user_ns.doc(security="basicAuth")
    @user_ns.expect(user_creation_model, validate=True)
    @jwt_required()
    def post(self):
        """This method handles the POST and creates new uses based
            models defined.
        """
        try:
            # Access the request payload data using `request.get_json()`
            payload = request.get_json()
            
            # Validate the payload data against the user_creation_model
            if not api.payload:
                return {'message': 'Invalid payload'}, 400
            
            
            # Extract the data from the payload using marshal
            username = api.payload['username']
            email = api.payload['email']
            password = api.payload['password']

            # hashed the plain text password with the generate_password_hash method
            hashed_password = generate_password_hash(password, method='sha256')

            user = User.query.filter_by(username=username).first()

            if not username or  not email or not password:
                return {'message': 'Invalid fields'}, 400

            if '@' not in email or '@' in username:
                return {'message': 'Invalid Email or Username'}, 400
            
            if len(password) < 12:
                return {'message': 'password length is too short and is vunerable to bruteforce attacks'}, 400
            
            if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
                return {'message', 'sorry, your password isn\'t  strong enough'}, 400
            

            # inject the data into the User object
            user = User(username=username, email=email, password=hashed_password)
            
            # save the new instance into the database
            db.session.add(user)
            db.session.commit()

            # The wallets is created automatically
            wallet = Wallet(user_id=user.id)
            db.session.add(wallet)
            db.session.commit()

            # return successful message once passed
            return {'message': 'User created successfully'}, 201


        except Exception as e:
            return {
                'data': 'Null',
                'message': 'Error: {}'.format(str(e)),
                'status': 'api-error'
            }, 400





@user_ns.route('/<int:userid>')
class Users(Resource):
    """This class object defines the routes and views for
       User Authentication.
    """

    @user_ns.doc(security="basicAuth")
    @user_ns.marshal_list_with(user_model)
    @jwt_required()
    def get(self, userid):
        """ This method handles the GET HTTP method 
            and returns response in a serialized format.
        """
        #query the user object
        user = User.query.filter_by(id=userid).first()
        # return the user object with 200 StatusCode
        return user, 200
    
    @user_ns.doc(security="basicAuth")
    @user_ns.expect(user_creation_model, validate=False)
    @jwt_required()
    def put(self, userid):
        """ This method handles the PUT HTTP method and returns 
            the updated instance of the object 
        """
        try:
            payload = request.get_json()

            if not api.payload:
                return {'message': 'Invalid payload'}, 400

            # query the User object with a given user id
            user = User.query.filter_by(id=userid).first()

            if not user or ('username' not in payload and 'email' not in payload and 'email_confirm' not in payload):
                return {
                    'data': 'null',
                    'message': 'User not found or missing username/email',
                    'status': 'api-error'
                }, 400

            # update username if exists in payload
            if 'username' in payload:
                user.username = payload['username']
            
            # update email if exists in payload
            if 'email' in payload:
                user.email = payload['email']
            
            if 'email' in payload and '@' not in payload['email']:
                return {
                    'message': 'Email format is not valid',
                    'status': 'api-error'
                }, 400
            
            # update email_confirmation if exists in payload
            if 'email_confirm' in payload:
                user.email_confirm = payload['email_confirm']
            
            # add and save the User instance to the database
            db.session.commit()

            return ({
                'message': 'user details has been updated successfully',
                'status': 'success'
            }), 201


        except Exception as e:
            return {
                'data': 'Null',
                'message': 'Error: {}'.format(str(e)),
                'status': 'api-error'
            }, 400


    @user_ns.doc(security="basicAuth")
    @jwt_required()
    def delete(self, userid):
        """ This method handles the DELETE HTTP method 
            and returns when successful.
        """
        try:
            user = User.query.filter_by(id=userid).first()

            if not user:
                return ({
                        'message': 'User Id entered is not valid',
                        'status': 'api-error'
                    }), 400
            
            
            db.session.delete(user)
            db.session.commit()

            return ({
                    'message': 'user has been deleted successfully',
                    'status': 'success'
                }), 202

        except Exception as e:
            return {
                'data': 'Null',
                'message': 'Error: {}'.format(str(e)),
                'status': 'api-error'
            }, 400



@wallet_ns.route('')
class Wallet_Details(Resource):
    """This object defines the routes and views for GET requests
        to this endpoint.
    """

    @wallet_ns.doc(security="basicAuth")
    @wallet_ns.marshal_list_with(wallet_model)
    @jwt_required()
    def get(self):
        """The get method handles generic HTTP GET requests and returns
            response in a serialized way.
        """
        try:
            wallet = Wallet.query.all()
            return wallet
        
        except Exception as e:
            return ({
                "data": "Null",
                "message": "Error {}".format(str(e)),
                "status": "api-error"
            })


@wallet_ns.route('/<int:userid>')
class Wallet_Details(Resource):
    """ This object defines the routes and views for specific GET
        and PUT requests for this endpoint.
    """
    
    @wallet_ns.doc(security="basicAuth")
    @wallet_ns.marshal_list_with(wallet_model)
    @jwt_required()
    def get(self, userid):
        """ The get method filters for specific user id using HTTP GET
            requests and returns a serialized results.
        """
        try:
            # query the wallet using the given user id
            wallet = Wallet.query.filter_by(user_id=userid).first()

            return wallet, 200

            if not wallet or not userid:
                return {
                    'data': 'null',
                    'message': 'wallet details not found',
                    'status': 'api-error'
                }, 400
        
        except Exception as e:
            return {
                'data': 'Null',
                'message': 'Error: {}'.format(str(e)),
                'status': 'api-error'
            }, 400


    @wallet_ns.doc(security="basicAuth")
    @wallet_ns.expect(wallet_create_model, validate=True)
    @jwt_required()
    def put(self, userid):
        """ This method handles the HTTP PUT method and returns 
            the updated instance of the object 
        """
        try:
            # Extract the userid from the query parameters
            payload = request.get_json()

            if not api.payload:
                return {'message': 'Invalid payload'}, 400

            # query the wallet object for the specific user
            wallet = Wallet.query.filter_by(user_id=userid).first()

            if not str(payload['current_balance']).isdigit():
                return ({
                        'message': 'Input format is not valid',
                        'status': 'api-error'
                    }), 400

            if 'current_balance' in payload:
                wallet.current_balance += payload['current_balance']


            # now save the session
            db.session.commit()

            return ({
                    'message': 'Wallet balance has been updated successfully',
                    'status': 'updated successfully',
                }), 201


        except Exception as e:
            return {
                'data': 'Null',
                'message': 'Error: {}'.format(str(e)),
                'status': 'api-error'
            }, 400


    @wallet_ns.doc(security="basicAuth")
    @jwt_required()
    def delete(self, userid):
        """ This method handles HTTP DELETE requests. """

        try:
            payload = request.get_json()

            # query the wallet object for the specific user
            wallet = Wallet.query.filter_by(user_id=userid).first()

            if not wallet:
                return ({
                        'message': 'wallet details is not valid',
                        'status': 'api-error'
                    }), 400


            # now save the session
            db.session.delete(wallet)
            db.session.commit()

            return ({
                    'message': 'Wallet has been deleted successfully',
                    'status': 'deleted successfully'
                }), 202


        except Exception as e:
            return {
                'data': 'Null',
                'message': 'Error: {}'.format(str(e)),
                'status': 'api-error'
            }, 400




    


@pay_ns.route('')
class Payment_Info(Resource):
    """This object defines the routes and views for Payment and
        handles the defined resources.
    """

    @pay_ns.doc(security="basicAuth")
    @pay_ns.marshal_list_with(payment_model)
    @jwt_required()
    def get(self):
        """This method handles the HTTP GET method and provides the
            platform to retrieve payments informations.
        """
        try:
            payment = Payment.query.all()

            return payment, 200

        except Exception as e:
            return ({
                "data": "Null",
                "message": "Error {}".format(str(e)),
                "status": "api-error"
            }), 400



@contact_ns.route('')
class Contact_Details(Resource):
    """This defines the api views for Contact object and
        handles the defined resources for generic GET 
        and POST requests only.
    """

    @contact_ns.doc(security="basicAuth")
    @contact_ns.marshal_list_with(contact_model)
    @jwt_required()
    def get(self):
        """This method handles the HTTP GET method and provides the
            platform to retrieve payments informations.
        """
        try:
            contact = Contact.query.all()
            return contact, 200
        
        except Exception as e:
            return ({
                "data": "Null",
                "message": "Error {}".format(str(e)),
                "status": "api-error"
            }), 400
    

    @contact_ns.doc(security="basicAuth")
    @contact_ns.expect(contact_model, validate=True)
    @jwt_required()
    def post(self):
        """ This method is responsible to handle all POST requests
            made to the contact object.
        """
        try:
            payload = request.get_json()

            if not api.payload:
                    return ({
                        "data": "null",
                        "message": "Invalid payload",
                        "status": "api-error"
                        }), 400
            
            # Extract the data from the payload using marshal
            fullname = api.payload['fullname']
            address = api.payload['address']
            country = api.payload['country']
            aboutme = api.payload['aboutme']

            # check to know if the contact details exists
            contact = Contact.query.filter_by(full_name=fullname).first()

            if not fullname and  not address and not country and not aboutme:
                    return ({
                        "data": "null",
                        "message": "Invalid fields or payload format",
                        "status": "api-error"
                        }), 400
            
            if not str(fullname, address, country, aboutme):
                return ({
                        "data": "null",
                        "message": "fields must only contain strings",
                        "status": "api-error"
                        }), 400
            
            # create a new instance of the contact object
            contact = Contact(full_name=fullname, address=address, country=country, about_me=about_me)
            
            # save and commit the new instance to database
            db.session.add(contact)
            db.session.commit()


        except Exception as e:
            return ({
                "data": "Null",
                "message": "Error {}".format(str(e)),
                "status": "api-error"
            }), 400


@contact_ns.route('/<int:contact>')
class Contact_Details(Resource):
    """This defines the api views for Contact object and
        handles the defined resources for specific GET 
        and PUT and DELETE HTTP requests.
    """
    
    @contact_ns.doc(security="basicAuth")
    @contact_ns.marshal_list_with(contact_model)
    @jwt_required()
    def get(self, contact):
        """This method handles the GET HTTP request."""

        try:
            contact = Contact.query.filter_by(contact_id=contact).first()

            return contact, 200

            if not contact:
                return {
                        'data': 'null',
                        'message': 'contact details could not be fetched',
                        'status': 'api-error'
                    }, 400

        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400


    @contact_ns.doc(security="basicAuth")
    @contact_ns.expect(contact_update_model, validate=True)
    @jwt_required()
    def put(self, contact):
        """ This method handles the PUT request for the contact
            object.
        """
        try:
            payload = request.get_json()

            if not api.payload:
                return ({
                    "data": "null",
                    "message": "Invalid payload",
                    "status": "api-error"
                    }), 400
            
            contact = Contact.query.filter_by(contact_id=contact).first()

            if not ('fullname' in payload or 'address' in payload or 'country' in payload or 'aboutme' in payload):
                return ({
                    "data": "null",
                    "message": "sorry, the field is not valid",
                    "status": "api-error"
                    }), 400


            if not all(isinstance(payload.get(field), str) for field in ['fullname', 'address', 'country', 'aboutme']):
                return {
                    "data": "null",
                    "message": "Fields must only contain strings",
                    "status": "api-error"
                }, 400



            if 'fullname' in payload:
                contact.full_name = payload['fullname']
            
            if 'address' in payload:
                contact.address = payload['address']

            if 'country' in payload:
                contact.country = payload['country']
            
            if 'aboutme' in payload:
                contact.about_me = payload['aboutme']
            
            # save and commit the updated field in database
            db.session.commit()

            return ({
                    'message': 'Contact details has been updated successfully',
                    'status': 'updated successfully'
                }), 201


        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400

    
    @contact_ns.doc(security="basicAuth")
    @jwt_required()
    def delete(self, contact):
        """ This method handles the DELETE request for the contact
            object.
        """
        
        try:
            contact = Contact.query.filter_by(contact_id=contact).first()
            
            if not contact:
                return ({
                        'message': 'contact details is not valid or not found',
                        'status': 'api-error'
                    }), 400

            # now save the session
            db.session.delete(contact)
            db.session.commit()

            return ({
                    'message': 'Contact has been deleted successfully',
                    'status': 'deleted successfully'
                }), 202
        
        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400



@donation_ns.route('')
class Donations(Resource):
    """This object defines the routes and views for Donations and
        handles the defined resources.
    """

    @donation_ns.doc(security="basicAuth")
    @donation_ns.marshal_list_with(donation_model)
    @jwt_required()
    def get(self):
        """This method handles the HTTP GET method and provides the
            platform to retrieve donations.
        """
        try:
            donation = Donation.query.all()

            return donation

        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400
    
    
    @donation_ns.doc(security="basicAuth")
    @donation_ns.expect(donation_model)
    @jwt_required()
    def post(self):
        """ This method handles HTTP POST Request to the Donation Object"""

        try:
            payload = request.get_json()

            if not api.payload:
                    return ({
                        "data": "null",
                        "message": "Invalid payload",
                        "status": "api-error"
                        }), 400

            

            # Extract the data from the payload using marshal
            amount = api.payload['amount']
            user_id = api.payload['userid']
            tree_spieces = api.payload['tree_spieces']
            number_of_trees = api.payload['number_of_trees']
            region_to_plant = api.payload['region_to_plant']
            description = api.payload['description']

            if not amount and  not tree_spieces and not number_of_trees and not region_to_plant and not description:
                    return ({
                        "data": "null",
                        "message": "Invalid fields or payload format",
                        "status": "api-error"
                        }), 400
            
            if not str(tree_spieces, number_of_trees, region_to_plant, description):
                return ({
                        "data": "null",
                        "message": "fields must only contain strings",
                        "status": "api-error"
                        }), 400
            
            if not int(amount, user_id):
                return ({
                        "data": "null",
                        "message": "field must only contain integer/float value",
                        "status": "api-error"
                        }), 400

            donation = Donation(
                        amount=amount,
                        user_id=user_id,
                        tree_spieces=tree_spieces, 
                        number_of_trees=number_of_trees,
                        region_to_plant=region_to_plant,
                        description=description                        
                        )

            # save and commit changes
            db.session.add(donation)
            db.session.commit()

            return ({
                "message": "donations was successful",
                "status": "created successfully"
            }), 200

        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400
    

@donation_ns.route('/<int:donation_id>')
class Donations(Resource):
    """This is an extension of the donations that handles specific
        donations and HTTP methods.
    """

    @donation_ns.doc(security="basicAuth")
    @donation_ns.marshal_list_with(donation_model)
    @jwt_required()
    def get(self, donation_id):
        """ This method handles the specific HTTP GET method and 
            returns specific donations.
        """

        try:
            donation = Donation.query.filter_by(donation_id=donation_id).first()

            return donation, 200

            if not donation:
                return {
                        'data': 'null',
                        'message': 'donation details could not be fetched',
                        'status': 'api-error'
                    }, 400

        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400


    @donation_ns.doc(security="basicAuth")
    @donation_ns.expect(donation_update_model, validate=True)
    @jwt_required()
    def put(self, donation_id):
        """ This method handles the PUT request for the Donation
            object.
        """
        try:
            payload = request.get_json()

            if not api.payload:
                return ({
                    "data": "null",
                    "message": "Invalid payload",
                    "status": "api-error"
                    }), 400
            
            donation = Donation.query.filter_by(donation_id=donation_id).first()

            if not ('userid' in payload or 'amount' in payload or 'tree_spieces' in payload or 'number_of_trees' in payload or 'region_to_plant' in payload or 'description' in payload):
                return ({
                    "data": "null",
                    "message": "sorry, the field is not valid",
                    "status": "api-error"
                    }), 400


            if not all(isinstance(payload.get(field), str) for field in ['tree_spieces', 'region_to_plant', 'description']):
                return {
                    "data": "null",
                    "message": "Fields must only contain strings",
                    "status": "api-error"
                }, 400

            if not all(isinstance(payload.get(field), int) for field in ['amount', 'number_of_trees', 'userid']):
                return {
                    "data": "null",
                    "message": "Fields must only contain integers",
                    "status": "api-error"
                }, 400

            if 'userid' in payload:
                donation.user_id = payload['userid']
            
            if 'amount' in payload:
                donation.amount = payload['amount']

            if 'tree_spieces' in payload:
                donation.tree_spieces = payload['tree_spieces']
            
            if 'number_of_trees' in payload:
                donation.number_of_trees = payload['number_of_trees']
            
            if 'region_to_plant' in payload:
                donation.region_to_plant = payload['region_to_plant']
            
            if 'description' in payload:
                donation.description = payload['description']
            
            # save and commit the updated field in database
            db.session.commit()

            return ({
                    'message': 'donations has been updated successfully',
                    'status': 'updated successfully'
                }), 201


        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400
    

    @donation_ns.doc(security="basicAuth")
    @jwt_required()
    def delete(self, donation_id):
        """ This method handles the DELETE request for the donation
            object.
        """
        
        try:
            donation = Donation.query.filter_by(donation_id=donation_id).first()
            
            if not donation:
                return ({
                        'message': 'donation is not valid or not found',
                        'status': 'api-error'
                    }), 400

            # now save the session
            db.session.delete(donation)
            db.session.commit()

            return ({
                    'message': 'donation has been deleted successfully',
                    'status': 'deleted successfully'
                }), 202
        
        except Exception as e:
             return {
                    'data': 'null',
                    'message': 'Error {}'.format(str(e)),
                    'status': 'api-error'
                }, 400
