from dudel import ma
from dudel.models import User
from dudel.login import check_access
from dudel.access import Has

class UserSchema(ma.Schema):
    id = ma.Integer(required=True, missing=None, dump_only=True)
    login = ma.String(required=True, missing=None)
    display_name = ma.String(required=True, missing=None)
    email = ma.Email(required=True, missing=None)
    password = ma.String(required=True, load_only=True)

    @staticmethod
    def get_only(user):
        if check_access(Has('admin')):
            return None
        elif check_access(Has('user', user.id)):
            return ('id', 'login', 'display_name', 'email')
        else:
            return ('id', 'login', 'display_name')


class StatusSchema(ma.Schema):
    status = ma.String()
    user = ma.Nested(UserSchema(), missing=None)

