import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dudel import app, db
from dudel.models import *
from datetime import datetime, timedelta

db.drop_all()
db.create_all()

poll = Poll()
poll.title = "What is the best Coffee"
poll.due_date = datetime.utcnow() + timedelta(days=5)
db.session.add(poll)

poll = Poll()
poll.title = "AG-Treffen"
poll.due_date = datetime.utcnow() - timedelta(days=1)
db.session.add(poll)

db.session.commit()