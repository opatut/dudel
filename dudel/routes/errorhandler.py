from flask import jsonify
from dudel import app
import traceback

@app.errorhandler(501)
@app.errorhandler(500)
@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(401)
@app.errorhandler(400)
@app.errorhandler(Exception)
def error(err):
    code = err.code if hasattr(err, 'code') else 500
    return jsonify(
        status='error',
        code=code,
        error=str(err),
        **(dict(stack=traceback.format_exc()) if app.config["DEBUG"] else {}),
    ), code

# # also register on every exception in production mode
# if not app.config["DEBUG"]:
#     error = app.errorhandler(Exception)(error)
