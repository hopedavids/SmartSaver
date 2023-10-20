import sys
import os

# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from flask_restx import fields
from instances import api




authorizations = {
    "basicAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

user_model = api.model(
    "User", {
        "id": fields.Integer,
        "username": fields.String,
        "email": fields.String,
        "email_confirm": fields.Boolean,
        "created_date": fields.DateTime(dt_format='iso8601'),
        "email_confirm_at": fields.DateTime(dt_format='iso8601')
    }
)

user_login_model = api.model(
    "User", {
        "username": fields.String(required=True),
        "password": fields.String(required=True)
    }
)


user_creation_model = api.model(
    "User", {
        "username": fields.String(required=True),
        "email": fields.String(required=True),
        "password": fields.String(required=True),
        "email_confirm": fields.Boolean(default=False)
    }
)


api_auth =  {
        "username": fields.String,
        "email": fields.String,
        'login_date': fields.DateTime(dt_format='iso8601')

    }


wallet_model = api.model(
    "Wallet", {
        "wallet_id": fields.String,
        "user": fields.Nested(user_model),       
        "current_balance": fields.Float,
        "previous_balance": fields.Float,
        "created_at": fields.DateTime(dt_format='iso8601'),
        "updated_at": fields.DateTime(dt_format='iso8601')
    }
)

wallet_create_model = api.model(
    "Wallet", {
        "current_balance": fields.Float(required=True)
    }
)


contact_model = api.model(
    "Contact", {
        "contact_id": fields.Integer,
        "user": fields.Nested(user_model),
        "fullname": fields.String,
        "address": fields.String,
        "country": fields.String,
        "description": fields.String
    }
)

contact_update_model = api.model(
    "Contact", {
        "fullname": fields.String(required=True),
        "address": fields.String(required=True),
        "country": fields.String(required=True),
        "aboutme": fields.String(required=True)
    }
)

transfer_model = api.model(
    "Transfer_Money", {
        "transfer_id": fields.Integer,
        "user": fields.Nested(user_model),
        "amount": fields.Float,
        "walletID": fields.String,
        "recipientemail": fields.String,
        "recipientfullname": fields.String,
        "get_certified": fields.Boolean,
        "timestamp": fields.DateTime(dt_format='iso8601')
    }
)

transfer_update_model = api.model(
    "Transfer_Money", {
        "userid": fields.Integer(required=True),
        "amount": fields.Integer(required=True),
        "walletID": fields.String(required=True),
        "recipientemail": fields.String(required=True),
        "recipientfullname": fields.String(required=True),
    }
)

payment_model = api.model(
    "Payment", {
        "payment_id": fields.Integer,
        "wallet_id": fields.String,
        "transfer": fields.Nested(transfer_model),
        "amount": fields.Float,
        "timestamp": fields.DateTime(dt_format='iso8601')
    }
)