'''
Created on 21.12.2018

@author: prudnik
'''

from datetime import datetime
from flask import Flask, jsonify, request, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPTokenAuth
import json
from passlib.hash import pbkdf2_sha256 as hasher
from datetime import datetime
#import secrets
from app_todo.config import Config
from app_todo.forms import LoginForm
from flask import render_template, flash, redirect

DATE_FMT = '%d/%m/%Y %H:%M:%S'
INCOMING_DATE_FMT = '%d/%m/%Y %H:%M:%S'


#from flask import g
#import sqlite3

#_DATABASE = 'E:/Development/temp/FlaskWebServer/todo_old.db'

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost:5432/flask_todo'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'
#app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///E:\Development\temp\FlaskWebServer\app.db'
app.config.from_object(Config)
#auth = HTTPTokenAuth(scheme='Token')
db = SQLAlchemy(app)

#===============================================================================
# models
#===============================================================================

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    note = db.Column(db.Unicode)
    creation_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    profile = db.relationship("Profile", back_populates='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'note': self.note,
            'creation_date': self.creation_date.strftime(DATE_FMT),
            'due_date': self.due_date.strftime(DATE_FMT) if self.due_date else None,
            'completed': self.completed,
            'profile_id': self.profile_id
        }

    def __repr__(self):
        return "<Task: {} | owner: {}>".format(self.name, self.profile.username)


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode, nullable=False)
    email = db.Column(db.Unicode, nullable=False)
    password = db.Column(db.Unicode, nullable=False)
    date_joined = db.Column(db.DateTime, nullable=False)
    token = db.Column(db.Unicode, nullable=False)
    tasks = db.relationship("Task", back_populates='profile', lazy=True)

    def __init__(self, *args, **kwargs):
        super(Profile).__init__(*args, **kwargs)
        self.date_joined = datetime.now()
        #self.token = secrets.token_urlsafe(64)

    def to_dict(self):
        """Get the object's properties as a dictionary."""

        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "date_joined": self.date_joined.strftime(DATE_FMT),
            "tasks": [task.to_dict() for task in self.tasks]
        }

    def __repr__(self):
        return "<Profile: {} | tasks: {}>".format(self.username, len(self.tasks))
#===============================================================================
# 
#===============================================================================
'''
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(_DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
'''
#===============================================================================
#  testing
#===============================================================================


@app.route('/hello')
def helloWorldHandler():
    return 'Hello World from Flask!'

@app.route('/index')
def helloWorldHandler():
    return 'Hello World from Flask!'

#@app.route('/mylogin')
#def mylogin():
#    form = LoginForm()
#    return render_template('login.html', title='Sign In', form=form)


@app.route('/mylogin', methods=['GET', 'POST'])
def mylogin():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        #return redirect('/api/v1/accounts/login')
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form)


@app.route('/show', methods=['GET', 'POST'])
def showBranches():
    data = list()
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    data.append(['2018-01-01_branch1', 'branch', 'function1' 'aaa1' , 'bbb1' , '2018-03-03'])
    return render_template('reviewed_items.html', title='Braches', data=data)


#===============================================================================
#  to do
#===============================================================================
def forbidden_response():
    """Return an HTTP response when the user is forbidden."""
    response = Response(
        mimetype="application/json",
        response=json.dumps({'error': 'You do not have permission to access this profile.'}),
        status=403
    )
    return response


def notfound_response():
    """Return an HTTP response when a nonexistant profile has been searched for."""
    response = Response(
        mimetype="application/json",
        response=json.dumps({'error': 'The profile does not exist'}),
        status=404
    )
    return response

def get_profile(username):
    """Check if the requested profile exists."""
    return Profile.query.filter_by(username=username).first()


#@auth.verify_token
def verify_token(token):
    """Verify that the incoming request has the expected token."""
    if token:
        username = token.split(':')[0]
        profile = get_profile(username)
        return token == profile.token


def authenticate(response, profile):
    """Authenticate an outgoing response with the user's token."""
    token = f'{profile.username}:{profile.token}'
    response.set_cookie('auth_token', value=token)
    return response


@app.route('/api/v1')
def index():
    """List of routes for this API."""
    output = {
        'info': 'GET /api/v1',
        'register': 'POST /api/v1/accounts',
        'single profile detail': 'GET /api/v1/accounts/<username>',
        'edit profile': 'PUT /api/v1/accounts/<username>',
        'delete profile': 'DELETE /api/v1/accounts/<username>',
        'login': 'POST /api/v1/accounts/login',
        'logout': 'GET /api/v1/accounts/logout',
        "user's tasks": 'GET /api/v1/accounts/<username>/tasks',
        "create task": 'POST /api/v1/accounts/<username>/tasks',
        "task detail": 'GET /api/v1/accounts/<username>/tasks/<id>',
        "task update": 'PUT /api/v1/accounts/<username>/tasks/<id>',
        "delete task": 'DELETE /api/v1/accounts/<username>/tasks/<id>'
    }
    response = jsonify(output)
    return response


@app.route('/api/v1/accounts', methods=['POST'])
def register():
    """Add a new user profile if it doesn't already exist."""
    needed = ['username', 'email', 'password', 'password2']
    if all([key in request.form for key in needed]):
        username = request.form['username']
        profile = get_profile(username)
        if not profile:
            if request.form['password'] == request.form['password2']:
                new_profile = Profile(
                    username=username,
                    email=request.form['email'],
                    password=hasher.hash(request.form['password']),
                )
                db.session.add(new_profile)
                db.session.commit()

                response = Response(
                    response=json.dumps({"msg": 'Profile created'}),
                    status=201,
                    mimetype="application/json"
                )
                return authenticate(response, new_profile)

            response = jsonify({"error": "Passwords don't match"})
            response.status_code = 400
            return response

        response = jsonify({'error': f'Username "{username}" is already taken'})
        response.status_code = 400
        return response

    response = jsonify({'error': 'Some fields are missing'})
    response.status_code = 400
    return response


@app.route('/api/v1/accounts/login', methods=['POST'])
def login():
    """Authenticate a user."""
    needed = ['username', 'password']
    if all([key in request.forms for key in needed]):
        profile = get_profile(request.forms['username'])
        if profile and hasher.verify(request.forms['password'], profile.password):
            response = Response(
                response=json.dumps({'msg': 'Authenticated'}),
                mimetype="application/json",
                status=200
            )
            return authenticate(response, profile)
        response.status_code = 400
        return {'error': 'Incorrect username/password combination.'}
    response.status_code = 400
    return {'error': 'Some fields are missing'}


@app.route('/api/v1/accounts/logout', methods=["GET"])
def logout():
    """Log a user out."""
    return jsonify({'msg': 'Logged out.'})


@app.route('/api/v1/accounts/<username>', methods=["GET"])
#@auth.login_required
def profile_detail(username):
    """Get the detail for an individual profile."""
    profile = get_profile(username)
    if profile:
        response = Response(
            mimetype="application/json",
            response=json.dumps(profile.to_dict()),
        )
        return authenticate(response, profile)
    return notfound_response()


@app.route('/api/v1/accounts/<username>/tasks', methods=['GET'])
#@auth.login_required
def task_list(username):
    """List all of the tasks for one user."""
    profile = get_profile(username)
    if profile:
        tasks = [task.to_dict() for task in profile.tasks.all()]
        output = {'username': username, 'tasks': tasks}
        response = Response(
            mimetype="application/json",
            response=json.dumps(output)
        )
        return authenticate(response, profile)
    return notfound_response()


@app.route('/api/v1/accounts/<username>/tasks', methods=['POST'])
#@auth.login_required
def create_task(username):
    """List all of the tasks for one user."""
    profile = get_profile(username)
    if profile:
        task = Task(
            name=request.form['name'],
            note=request.form['note'],
            creation_date=datetime.now(),
            due_date=datetime.strptime(due_date, INCOMING_DATE_FMT) if due_date else None,
            completed=request.form['completed'],
            profile_id=profile.id,
        )
        db.session.add(task)
        db.session.commit()
        output = {'msg': 'posted'}
        response = Response(
            mimetype="application/json",
            response=json.dumps(output),
            status=201
        )
        return authenticate(response, profile)
    return notfound_response()


@app.route('/api/v1/accounts/<username>/tasks/<int:task_id>', methods=['GET'])
#@auth.login_required
def task_detail(username, task_id):
    """Get the detail for one task if that task belongs to the provided user."""
    profile = get_profile(username)
    if profile:
        task = Task.query.get(task_id)
        if task in profile.tasks:
            output = {'username': username, 'task': task.to_dict()}
            response = Response(
                mimetype="application/json",
                response=json.dumps(output)
            )
            return authenticate(response, profile)
    return notfound_response()


@app.route('/api/v1/accounts/<username>/tasks/<int:task_id>', methods=['PUT'])
#@auth.login_required
def task_update(username, task_id):
    """Update one task if that task belongs to the provided user."""
    profile = get_profile(username)
    if profile:
        task = Task.query.get(task_id)
        if task in profile.tasks:
            if 'name' in request.form:
                task.name = request.form['name']
            if 'note' in request.form:
                task.note = request.form['note']
            if 'completed' in request.form:
                task.completed = request.form['completed']
            if 'due_date' in request.form:
                due_date = request.form['due_date']
                task.due_date = datetime.strptime(due_date, INCOMING_DATE_FMT) if due_date else None
            db.session.add(task)
            db.session.commit()
            output = {'username': username, 'task': task.to_dict()}
            response = Response(
                mimetype="application/json",
                response=json.dumps(output)
            )
            return authenticate(response, profile)
    return notfound_response()


@app.route('/api/v1/accounts/<username>/tasks/<int:task_id>', methods=['GET'])
#@auth.login_required
def task_delete(username, task_id):
    """Delete one task if that task belongs to the provided user."""
    profile = get_profile(username)
    if profile:
        task = Task.query.get(task_id)
        if task in profile.tasks:
            db.session.delete(task)
            db.session.commit()
            output = {'username': username, 'msg': 'Deleted.'}
            response = Response(
                mimetype="application/json",
                response=json.dumps(output)
            )
            return authenticate(response, profile)
    return notfound_response()

#===============================================================================
# controlling functions
#===============================================================================
def start_f1(switch = False):
    app.run(host='0.0.0.0', port= 8090) #http://127.0.0.1:8090/index;  http://127.0.0.1:8090/api/v1   http://127.0.0.1:8090/api/v1/accounts/prudnik3

if __name__ == "__main__":
    start_f1(True)

