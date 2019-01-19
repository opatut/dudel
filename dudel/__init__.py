from flask import Flask
from flask_gravatar import Gravatar
from flask_mail import Mail
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import click

app = Flask('dudel')
app.config.from_pyfile("../config.py.example", silent=True)
app.config.from_pyfile("../config.py", silent=True)

api = Api(app)

db = SQLAlchemy(app)
ma = Marshmallow(app)

migrate = Migrate(app, db)

gravatar = Gravatar(app, size=48, rating='g', default='identicon', force_default=False, use_ssl=True, base_url=None)
mail = Mail(app)

from .access import Has, ANY, Not, HasScope
from .login import auth, require_access, check_access
from .commands import init, cron, test, seed
from dudel.test import TestCase
from dudel.models import *
import dudel.routes

app.cli.command()(init)
app.cli.command()(cron)
app.cli.command()(seed)
app.cli.command(with_appcontext=False, name='test')(test)

