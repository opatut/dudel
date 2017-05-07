from flask import jsonify
from dudel import app, auth
from dudel.schema import StatusSchema

@app.route("/login")
def login():
    user = User.query.first()
    token = user.generate_access_token()
    db.session.add(token)
    db.session.commit()
    return str(token)
