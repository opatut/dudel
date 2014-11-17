import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dudel import app, db
from dudel.models import *
from datetime import datetime, timedelta
import random

def fill_with_random_votes(poll, n):
    for x in range(n):
        vote = Vote()
        vote.name = "Voter %d" % (x+1)
        poll.votes.append(vote)

        for choice in poll.choices:
            vote_choice = VoteChoice()
            vote_choice.vote = vote
            vote_choice.choice = choice
            vote_choice.value = random.choice(poll.choice_values.all())

db.drop_all()
db.create_all()

poll = Poll()
poll.title = "What is the best Coffee"
poll.due_date = datetime.utcnow() + timedelta(days=5)
poll.slug = "coffee"
poll.type = "normal"
db.session.add(poll)

for x in range(5):
    choice = Choice()
    choice.text = "Blend no. %d" % x
    poll.choices.append(choice)

fill_with_random_votes(poll, 8)

poll = Poll()
poll.title = "AG-Treffen"
poll.due_date = datetime.utcnow() - timedelta(days=1)
poll.slug = "ag"
poll.type = "date"
db.session.add(poll)

poll = Poll()
poll.title = "Large Poll"
poll.due_date = datetime.utcnow() + timedelta(days=7)
poll.slug = "large-poll"
poll.type = "date"
db.session.add(poll)

for x in range(21):
    choice = Choice()
    choice.date = datetime.utcnow().replace(hour=10,minute=0,second=0,microsecond=0) + timedelta(days=x+7)
    poll.choices.append(choice)
    choice = Choice()
    choice.date = datetime.utcnow().replace(hour=12,minute=0,second=0,microsecond=0) + timedelta(days=x+7)
    poll.choices.append(choice)

fill_with_random_votes(poll, 42)

db.session.commit()
