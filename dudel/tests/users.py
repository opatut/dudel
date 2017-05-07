import json
from dudel import db, auth
from dudel.tests import TestCase
from dudel.models import User
from pydash import pick

class UsersTest(TestCase):
    def test_empty_db(self):
        with self.context():
            users = self.get('/users')
            self.assertEqual(users, [])

    def test_registration(self):
        with self.context():
            user = self.post('/users', dict(
                email='foo@example.com',
                login='foo',
                display_name='Foo Display',
                password='hunter2',
            ))

            self.assertIsInstance(user['id'], int)
            self.assertEqual(user['email'], 'foo@example.com')
            self.assertEqual(user['login'], 'foo')
            self.assertEqual(user['display_name'], 'Foo Display')
            self.assertNotIn('password', user)

            users = self.get('/users')
            self.assertEqual(len(users), 1)
            self.assertEqual(users, [user])

    def test_get_single(self):
        with self.context():
            u = User(login='foo', display_name='Foo Display', email='foo@example.com')
            u.set_password('hunter2')
            db.session.add(u)
            db.session.commit()

            user = self.get('/users/{}'.format(u.id))
            self.assertEqual(user, pick(u, ['email', 'display_name', 'id', 'login']))

    def test_me(self):
        with self.context('admin'):
            user = self.get('/users/me')
            self.assertIsNotNone(user)
            self.assertEqual(user['login'], 'admin')
