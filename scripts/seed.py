import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dudel import app, db
from dudel.models import *
from datetime import datetime, timedelta
import random

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

for x in range(8):
    vote = Vote()
    vote.name = "Peep %d" % x
    poll.votes.append(vote)

    for choice in poll.choices:
        vote_choice = VoteChoice()
        vote_choice.vote = vote
        vote_choice.choice = choice
        vote_choice.value = random.choice(["yes", "no", "maybe"])

poll = Poll()
poll.title = "AG-Treffen"
poll.due_date = datetime.utcnow() - timedelta(days=1)
poll.slug = "ag"
poll.type = "date"
db.session.add(poll)

db.session.commit()
