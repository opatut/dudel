from flask import jsonify
from dudel import app, auth, ma
from dudel.resources.users import UserSchema

class StatusSchema(ma.Schema):
    status = ma.String()
    user = ma.Nested(UserSchema(), missing=None)

@app.route("/status")
def status():
    result = dict(status="ok", user=auth.user)
    return StatusSchema().jsonify(result)
