from dudel import api, auth, db
from dudel.login import set_auth
from functools import wraps
from flask_restful import Resource, reqparse
from pydash import omit
from flask import request, abort

from .schema import UserSchema
from .tests import *

def get_data(schema, *args, **kwargs):
    result = schema.load(request.get_json() or {}, *args, **kwargs)
    if result.errors:
        raise Exception(result.errors)
    return result.data

def with_data(schema, *args, **kwargs):
    def wrapper(fn):
        @wraps(fn)
        def fn2(self, *args2, **kwargs2):
            data = get_data(schema, *args, **kwargs)
            return fn(self, data, *args2, **kwargs2)
        return fn2
    return wrapper

class UserSingle(Resource):
    def _get_user(self, user_id):
        if user_id == 'me':
            return auth.user
        elif isinstance(user_id, int):
            return User.query.get(user_id)
        else:
            abort(404)

    def get(self, user_id):
        user = self._get_user(user_id)
        schema = UserSchema()
        return schema.dump(user).data if user else None

    @with_data(UserSchema(partial=True))
    def put(self, data, user_id):
        password = data.pop('password', None)
        user = self._get_user(user_id)

        for k, v in data.items(): setattr(user, k, v)
        if password: user.set_password(password)
        db.session.commit()

        return UserSchema().dump(user).data


class UserList(Resource):
    @with_data(UserSchema(partial=('id',)))
    def post(self, data):
        password = data.pop('password')

        user = User(**data)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        token = user.generate_access_token()
        db.session.add(user)
        db.session.commit()

        set_auth(user, token)

        return UserSchema(only=UserSchema.get_only(user)).dump(user).data, 201

    def get(self):
        users = User.query.all()
        schema = UserSchema(many=True)
        return schema.dump(users).data

api.add_resource(UserList, '/users')
api.add_resource(UserSingle, '/users/<int:user_id>', '/users/<user_id>')
