from dudel import app, db
from dudel.models import Vote, User, Poll, PollType, Choice, VoteChoice, Application, AccessToken
from datetime import datetime, timedelta
import random

vowels = "aeoiu"
consonants = "bcdfghjklmnprstvw"

def init():
    """Creates an empty database."""
    db.drop_all()
    db.create_all()
    db.session.commit()

def cron():
    """Executes regular cleanup tasks."""

    from dudel.models import Poll

    for poll in Poll.query.filter_by(deleted=False).all():
        if poll.should_auto_delete:
            poll.deleted = True

    db.session.commit()

def test():
    """Runs unit tests."""
    import dudel.tests, unittest

    suite = unittest.TestLoader().loadTestsFromModule(dudel.tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

def _random_name():
    length = random.randint(5, 10)
    offset = random.randint(0, 100)
    return "".join([random.choice([vowels, consonants, consonants][(offset+i)%3]) for i in range(length)]).title()

def _random_votes(poll, n):
    for x in range(n):
        vote = Vote()
        # vote.name = "Voter %d" % (x+1)
        vote.name = _random_name()
        poll.votes.append(vote)

        for choice in poll.choices:
            vote_choice = VoteChoice()
            vote_choice.vote = vote
            vote_choice.choice = choice
            vote_choice.value = random.choice(poll.choice_values.all())

def _add_choices(poll, choices):
    for choice in choices:
        poll.choices.append(Choice(choice))

def seed():
    """Creates a database and with test data."""
    db.drop_all()
    db.create_all()

    user = User(login="test", display_name="Max Mustermann", email="test@example.com")
    user.set_password("hunter2")
    db.session.add(user)

    user2 = User(login="foo", display_name="Minna Musterfrau", email="test2@example.com")
    user2.set_password("hunter2")
    db.session.add(user2)

    poll_normal = Poll("Test: Type Normal", "test-normal", PollType.normal)
    poll_normal.owner = user
    db.session.add(poll_normal)
    _add_choices(poll_normal, ["Foo", "Bar", "Baz", "Foobar", "Bazfoo"])
    _random_votes(poll_normal, 8)

    poll_datetime = Poll("Test: Type Datetime", "test-datetime", PollType.datetime)
    poll_datetime.owner = user
    db.session.add(poll_datetime)

    poll_date = Poll("Test: Type Date", "test-date", PollType.date)
    poll_date.owner = user
    db.session.add(poll_date)
    _add_choices(poll_date, [datetime.today() + timedelta(days=x) for x in range(5)])

    # poll_large = Poll("Test: Large Poll", "test-large", PollType.normal)
    # poll_large.owner = user
    # db.session.add(poll_large)
    # _add_choices(poll_large, [_random_name() for i in range(40)])
    # _random_votes(poll_large, 40)

    poll_autodelete = Poll("Test: Autodelete", "test-autodelete", PollType.normal)
    poll_autodelete.owner = user
    poll_autodelete.created = datetime.utcnow() - timedelta(days=91)
    db.session.add(poll_autodelete)

    poll_numeric = Poll("Test: Type Numeric", "test-numeric", PollType.numeric, create_choice_values=False)
    poll_numeric.amount_minimum = 0
    poll_numeric.amount_maximum = 2
    poll_numeric.amount_step = 0.5
    poll_numeric.owner = user
    _add_choices(poll_numeric, ["Penguins", "Gnus", "Dromedaries", "Pythons"])
    db.session.add(poll_numeric)

    poll_owner = Poll("Test: Other owner", "test-owner", PollType.normal)
    poll_owner.owner = user2
    db.session.add(poll_owner)
    _add_choices(poll_owner, ["Left", "Right", "Middle"])
    _random_votes(poll_owner, 20)

    app = Application(client_id="", client_secret="", title="Test app", scope='*', redirect_url='foo')
    app.user = user
    db.session.add(app)

    token = AccessToken(id="testaccess")
    token.application = app
    token.user = user
    token.scope = '*'
    token.created_at = datetime.utcnow()
    token.expires_at = datetime.utcnow() + timedelta(days=14)
    db.session.add(token)

    db.session.commit()
