from dudel import app, login_manager
from flask.ext.login import login_user, logout_user

_login_providers = {}


class login_provider(object):
    """decorator to register login providers"""
    def __init__(self, mode):
        self.mode = mode

    def __call__(self, func):
        """
        func(username, password) should return of of
        - a User object, on success
        - None, if the User was not found or the password is wrong
        - an error string, if an error occurred
        """
        _login_providers[self.mode] = func
        return func


def try_login(username, password):
    if not app.config["LOGIN_PROVIDERS"]:
        return "Login is disabled."

    for provider in app.config["LOGIN_PROVIDERS"]:
        if not provider in _login_providers:
            return None, "Invalid login provider: %s." % provider

        result = _login_providers[provider](username, password)

        from dudel.models.user import User
        if isinstance(result, User):
            # do the login
            login_user(result)
            return result, None
        elif isinstance(result, str):
            print("Login error: " + result)
            return None, result
        elif result == False or result == None:
            # User not found
            continue

    return None, None


def force_login(user):
    login_user(user)


def logout():
    logout_user()


@login_manager.user_loader
def get_user(username):
    from dudel.models.user import User
    return User.query.filter_by(username=username).first()

