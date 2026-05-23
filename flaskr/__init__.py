import os
from authlib.integrations.flask_client import OAuth
from flask import Flask
from datetime import datetime

oauth = OAuth()

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),

        UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'uploads'),
        UPLOAD_URL='/static/uploads',
        GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", os.environ.get("GOOGLE_CLIENT_ID")),
        GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", os.environ.get("GOOGLE_CLIENT_SECRET"))
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    oauth.init_app(app)
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )


    # register the database commands
    from . import db

    db.init_app(app)

    # apply the blueprints to the app
    from .blueprints import auth
    from .blueprints import admin
    from .blueprints import user
    from .blueprints import archive

    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(archive.bp)

    # make url_for('index') == url_for('thesis.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the thesis blueprint a url_prefix, but for
    # the tutorial the thesis will be the main index
    app.add_url_rule("/", endpoint="index")

    app.jinja_env.filters['timeago'] = timeago

    return app


def timeago(date):
    if not date:
        return "unknown time"
    
    if isinstance(date, str):
        try:
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return date

    now = datetime.utcnow()
    diff = now - date
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000: 
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 31536000: 
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"
