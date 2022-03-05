from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'amen'

    from website.auth.auth import auth
    app.register_blueprint(auth, url_prefix='/')

    from website.home.home import home
    app.register_blueprint(home, url_prefix='/')

    from website.console.console import console
    app.register_blueprint(console, url_prefix='/')

    from website.tendy.tendy import tendy
    app.register_blueprint(tendy, url_prefix='/')

    from website.counter.counter import counter
    app.register_blueprint(counter, url_prefix='/')

    return app
