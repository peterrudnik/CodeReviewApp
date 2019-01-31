"""
    see http://flask.pocoo.org/docs/1.0/tutorial/views/
"""

import database
import functools
from datetime import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

blueprint = Blueprint('auth', __name__,
                      template_folder='templates',
                      static_folder='static')


@blueprint.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif database.getUser(shortname=username) is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            user = database.User(id=None, name= username, shortname= username, note=None, from_date=datetime.now(), to_date=None)
            creator_id = database.addUser(user, flash_details=True)
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('register.html')



@blueprint.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = database.getUser(shortname=username)

        if user is None:
            error = 'Incorrect username.'
        #elif not check_password_hash(user['password'], password):
        #    error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            #return redirect(url_for('index'))
            return redirect('/index')

        flash(error)

    #return render_template('auth/login.html')
    return render_template('login.html')


@blueprint.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = database.getUser(shortname=user_id)


@blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        user_id = session.get('user_id')
        if user_id is None:
        #if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view