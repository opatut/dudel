import os, dudel, unittest, tempfile, json, flask
from contextlib import contextmanager

class ApiException(Exception):
    pass

def _request(method):
    def fn(self, url, data=None, *args, **kwargs):
        if data:
            kwargs['data'] = json.dumps(data)
            kwargs['content_type'] = 'application/json'
        kwargs['method'] = method.upper()

        if self.current_token:
            kwargs['headers'] = {
                'authorization': 'Bearer ' + self.current_token,
            }

        res = self.c.open(url, *args, **kwargs)
        res = json.loads(res.get_data())
        if res and 'error' in res:
            if 'stack' in res:
                print()
                print('Debug stack')
                print(res['stack'])
                print()
                print()
            raise ApiException(res['error'])
        return res
    return fn

class TestCase(unittest.TestCase):
    def setUp(self):
        self.current_token = None

        self.db_fd, self.filename = tempfile.mkstemp()

        dudel.app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + self.filename
        dudel.app.config['TESTING'] = True

        with dudel.app.app_context():
            dudel.commands.init()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.filename)

    @contextmanager
    def context(self, username=None):
        with dudel.app.test_client() as self.c:
            with dudel.app.app_context() as self.ctx:
                if username:
                    with getattr(self, 'as_' + username)() as user:
                        yield user
                else:
                    yield

    @contextmanager
    def as_admin(self):
        user = User(login='admin', display_name='admin', email='admin')
        user.set_password('hunter2')
        db.session.add(user)
        db.session.commit()

        access_token = user.generate_access_token()
        db.session.add(access_token)
        db.session.commit()

        prev = self.current_token
        self.current_token = access_token.id
        yield
        self.current_token = prev

    # API methods

    get = _request('get')
    put = _request('put')
    post = _request('post')
    delete = _request('delete')

from .users import *
from .access import *

