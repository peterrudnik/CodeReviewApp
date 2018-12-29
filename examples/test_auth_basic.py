from flask import Flask, jsonify, request, Response
from flask import g
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret key here'
auth = HTTPBasicAuth()

users = {
    "john": "hello",
    "susan": "bye"
}

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@app.route('/')
@auth.login_required
def get_resource():
    return jsonify({ 'data': 'Hello, %s!' % g.user.username })


if __name__ == '__main__':
    app.run()