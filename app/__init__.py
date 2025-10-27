# First load the env variables
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_session import Session
from flask_migrate import Migrate

from app.extensions import db
from app.models import *
from app.utils.tasks import initialize_tasks

from .routes.blueprints import register_blueprints

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.FlaskAppConfig')

    Session(app) # Server-side session management

    db.init_app(app)
    migrate.init_app(app, db)

    register_blueprints(app)

    with app.app_context():
        initialize_tasks()

    return app
