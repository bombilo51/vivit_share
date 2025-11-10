from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
cors = CORS()


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))
