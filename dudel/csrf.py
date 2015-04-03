from flask import abort, session, request

from functools import wraps

from hashlib import sha512

from datetime import datetime

from random import randint

# Adopted from http://flask.pocoo.org/snippets/3/ and then greatly modified

class Protector(object):
    parameter = '_csrf_token'
    session_key = '_csrf_token'

    def __init__(self, app=None, parameter='_csrf_token', session_key='_csrf_token', abort_code=403, consume=False):
        self.parameter = parameter
        self.session_key = session_key
        self.abort_code = abort_code
        self.consume = consume

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        @self.app.before_request
        def autogenerate_token():
            if not self.session_key in session:
                self.generate_token()

    def inject_as(self, template_variable='CSRF'):
        @self.app.context_processor
        def inject_token():
            return {
                template_variable: self.get_token()
            }

    def check(self, consume=None):
        # Fetch the saved token from the session
        if consume == None: consume = self.consume
        if consume:
            saved_token = session.pop(self.session_key, None)
        else:
            saved_token = session.get(self.session_key, None)

        # Fetch the submitted token from the POST/GET parameters
        found_token = request.form.get(self.parameter, None) or request.args.get(self.parameter, None)

        # Check that both tokens exist and are equal
        return saved_token and found_token and saved_token == found_token


    def check_or_abort(self, code=None, consume=None):
        if not self.check(consume):
            abort(code if code != None else self.abort_code)


    # decorator to protect a whole view
    # this view can then not be accessed directly
    # use this for single-action views that redirect somewhere else and don't
    # show content
    def protect(self, code=None, consume=None):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                self.check_or_abort(code, consume)
                return fn(*args, **kwargs)
            return wrapper
        return decorator


    def generate_token(self):
        gen = sha512()
        gen.update(str(datetime.utcnow()))
        gen.update(self.app.config["SECRET_KEY"])
        gen.update("".join(chr(randint(30, 120)) for i in range(20)))

        token = gen.hexdigest()
        session[self.session_key] = token
        return token


    def get_token(self):
        return session.get(self.session_key, None) or self.generate_token()

