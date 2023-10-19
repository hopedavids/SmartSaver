import os, sys
import psycopg2
from flask import Flask
from dotenv import load_dotenv
from datetime import timedelta
# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)


from flask_session import Session
from flask_restx import apidoc
from instances import api, db, jwt, login_manager, csrf, mail
from sqlalchemy.dialects.postgresql import psycopg2
from resources import auth_ns, user_ns, wallet_ns, pay_ns, transfer_ns, contact_ns
from user_auth import user_auth as user_auth_blueprint
from main import main as main_blueprint
from api_auth import api_auth as api_auth_blueprint
from admin import admin as admin_blueprint
from google import google as google_blueprint
from frontend_views import frontend_views as frontend_views_blueprint


load_dotenv('.flaskenv')
load_dotenv('.env')


""" This is the main application that serves as the pivort and blueprint
    for other modules.All API endpoints would be defined here with route
    and views for the APIs to function.Also, this would serve other
    resources and modules.
"""


def create_app():
    """This method initialize and registers the app and the restful API
        including the namespaces
    """

    app = Flask(__name__)


    # configure the SQLite database, relative to the app instance folder
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('POSTGRES_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True

    # app.config["GOOGLE_OAUTH_CLIENT_ID"] = "624564857118-mt3fdl8vkm69erqnigtshkr3tct2v2gt.apps.googleusercontent.com"
    # app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = "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"

    
    # adding the secret to the app and JWT
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY')

    # adding email verification to the app
    app.config['MAIL_SERVER'] = os.environ.get('EMAIL_SERVER')
    app.config['MAIL_PORT'] = os.environ.get('EMAIL_PORT')
    app.config['MAIL_USERNAME'] = os.environ.get('PUSH_EMAIL')
    app.config['MAIL_PASSWORD'] = os.environ.get('PUSH_EMAIL_PASSWD')
    app.config['MAIL_SENDER'] = os.environ.get('MAIL_SENDER')
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True


    # adding extra security parameters for sessions
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    

    # Use a secure session storage
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)


    # initializing the JWTManager
    jwt.init_app(app)

    # creating and initializing the Login Manager instance class
    login_manager.init_app(app)


    # register namespace Users
    api.add_namespace(auth_ns)
    api.add_namespace(user_ns)
    api.add_namespace(wallet_ns)
    api.add_namespace(pay_ns)
    api.add_namespace(transfer_ns)
    api.add_namespace(contact_ns)
    # api.add_namespace(api_ns)

    api.init_app(app)
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    
    # adding and registering the blueprint
    app.register_blueprint(user_auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_auth_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(frontend_views_blueprint)

    @api.documentation
    def customize_swagger_ui():
        return {
            "basePath": "/api",  # Modify the base path here
            'info': {
                'title': 'My API',
                'version': '1.0',
            },
        }

    # API documentation route
    @app.route('/v1/api/docs')
    def swagger_ui():
        return apidoc.ui_for(api)


    with app.app_context():
        db.create_all()

    return app
