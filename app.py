from flask import Flask
from config import Config
from extensions import db, login_manager  # ✅ import from extensions

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "routes.login"

    # import models *inside* the app context, so no circular import
    with app.app_context():
        from models import User, JournalEntry
        db.create_all()

    # register routes
    import routes
    app.register_blueprint(routes.bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
