import sys
import os

# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from flask import Blueprint, request, jsonify
from flask_login import current_user
from flask_jwt_extended import create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from instances import csrf, jwt
from datetime import datetime, timedelta
from models import User


api_auth = Blueprint('api_auth', __name__, url_prefix='/v1/auth')


@api_auth.route('/login', methods=['POST'])
def login():
    try:
        username = request.json['username']
        password = request.json['password']

        user = User.query.filter_by(username=username).first()


        if not username or  not password:
            return jsonify({'message': 'Invalid fields'}), 400

        # Check if username is an email
        elif '@' in username:
            return jsonify({'message': 'username should not be an email'}), 400


        elif not user or not check_password_hash(user.password, password):
            return jsonify({
                "data": "null",
                "message": "Username or Password Incorrect",
                "status": "api-error"
            }), 400
        

        
        access_token = create_access_token(identity=username)
        return jsonify({
            "username": username,
            "access_token": access_token
            }), 200

    except Exception as e:
        return jsonify({
                "data": "Null",
                "message": "error {}".format(str(e)),
                "error": "api-error"
                }), 400
