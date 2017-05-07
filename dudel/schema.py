from dudel import ma
from dudel.models import User

class UserSchema(ma.Schema):
    id = ma.Integer(required=True, missing=None, dump_only=True)
    login = ma.String(required=True, missing=None)
    display_name = ma.String(required=True, missing=None)
    email = ma.Email(required=True, missing=None)
    password = ma.String(required=True, load_only=True)

class StatusSchema(ma.Schema):
    status = ma.String()
    user = ma.Nested(UserSchema(), missing=None)

