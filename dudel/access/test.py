from dudel import db
from dudel.models import User, Poll
from dudel.test import TestCase

from . import Has, ANY, Not

class TestCase(TestCase):
    def test_simple_has(self):
        x = Has('foo', 'bar')
        self.assertEqual(x.test('foo', 'bar'), True)
        self.assertEqual(x.test('foo', 'baz'), False)
        self.assertEqual(x.test('foo', ANY), False)

    def test_simple_any(self):
        x = Has('foo', ANY)
        self.assertEqual(x.test('foo', 'bar'), True)
        self.assertEqual(x.test('foo', 'baz'), True)
        self.assertEqual(x.test('foo', ANY), True)
        self.assertEqual(x.test('bla', ANY), False)
        self.assertEqual(x.test('foo', ANY, 'nom'), False)

    def test_user_attributes(self):
        with self.context():
            u = User(login='foo', display_name='Foo Display', email='foo@example.com')
            u.set_password('hunter2')
            db.session.add(u)
            db.session.commit()

            p = Poll()
            p.owner = u
            db.session.add(p)
            db.session.commit()

            self.assertEqual(Has('user', u.id)(u.attributes), True)
            self.assertEqual(Has('user', '-15123')(u.attributes), False)
            self.assertEqual(Has('user', ANY)(u.attributes), True)

            rule = Has('poll_owner', p.id)
            self.assertEqual(rule.matches(u.attributes), True)

            rule = Has('poll_owner', p.id) and Has('user', u.id)
            self.assertEqual(rule.matches(u.attributes), True)

            rule = Not(Has('poll_owner', p.id) and Has('user', u.id))
            self.assertEqual(rule.matches(u.attributes), False)

            rule = Has('poll_owner', 'Foo') or Has('user', u.id)
            self.assertEqual(rule.matches(u.attributes), False)
