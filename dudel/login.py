from flask import has_request_context, request, g
from werkzeug.local import LocalProxy

from dudel.models import AccessToken


class Auth(object):
    def __init__(self, user, token):
        self.user = user
        self.token = token

_no_login = Auth(None, None)

def _get_auth():
    if g.get('auth', None) is None:
        _load_auth()

    auth = g.get('auth', None)
    return auth


def _load_auth():
    token = request.headers.get('Authorization', None)

    if token:
        token_type, token_value = token.split(' ', 1)

        if token_type and token_type.lower() == 'bearer':
            access_token = AccessToken.query.get(token_value)

            if access_token:
                g.auth = Auth(access_token.user, access_token)
                return

    g.auth = _no_login

def set_auth(user, token):
    g.auth = Auth(user, token)

### 

auth = LocalProxy(_get_auth)
all = ['auth']
