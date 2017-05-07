from flask import jsonify
from dudel import app, auth
from dudel.schema import StatusSchema

@app.route("/status")
def status():
    result = dict(status="ok", user=auth.user)
    return StatusSchema().jsonify(result)
