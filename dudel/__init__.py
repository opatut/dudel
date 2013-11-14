from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown
from flask.ext.login import LoginManager, current_user

app = Flask(__name__)
app.config.from_pyfile("../config.py", silent=True)
db = SQLAlchemy(app)
markdown = Markdown(app, safe_mode="escape")
login_manager = LoginManager(app)

import dudel.models
import dudel.forms
import dudel.filters
import dudel.views

login_manager.login_view = "login"
