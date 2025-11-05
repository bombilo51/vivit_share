from flask import Flask, render_template
from .config import config
from .extensions import db, migrate, login_manager

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .product import product as product_blueprint
    app.register_blueprint(product_blueprint, url_prefix='/product')

    # Simple index route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    return app
    