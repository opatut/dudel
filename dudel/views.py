from dudel import app, db
from dudel.models import *
from flask import render_template

@app.route("/")
def index():
    polls = Poll.query.all()
    return render_template("index.html", polls=polls)
