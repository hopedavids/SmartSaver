from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail





"""This is where initialization of the app and db takes place."""

api = Api()

db = SQLAlchemy()

jwt = JWTManager()

csrf = CSRFProtect()

login_manager = LoginManager()

login_manager.login_view = 'user_auth.signin'

mail = Mail()

