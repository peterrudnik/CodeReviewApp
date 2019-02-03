# -*- coding: utf-8 -*-
'''
Created on 21.12.2018

@author: prudnik
'''

from datetime import datetime
from flask import Flask, jsonify, request, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import aliased
#from flask_mysqldb import MySQL
from flask_httpauth import HTTPTokenAuth
import json
from passlib.hash import pbkdf2_sha256 as hasher
from datetime import datetime
import dateutil.rrule as rrule
import calendar
#import secrets
#from app_svn_branches.c    onfig import Config
#from app_svn_branches.config import Config
import app_svn_branches.config as config_module
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect
import babel
#from database import db
import database

import auth
import view_main
import view_review_item
import view_review
import view_user
import view_analysis

DATETIME_FMT_DISPLAY = DATETIME_FMT_FORM

#from flask import g
#import sqlite3

#_DATABASE = 'E:/Development/temp/FlaskWebServer/todo_old.db'

#app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost:5432/flask_todo'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'
#app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///E:\Development\temp\FlaskWebServer\app.db'
#app.config.from_object(Config)
#auth = HTTPTokenAuth(scheme='Token')
#db = SQLAlchemy(app)
#a = SQLAlchemy


#===============================================================================
#   app factory,  jinja setup
#===============================================================================

def format_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    #return babel.dates.format_datetime(value, format)
    if value and isinstance(value,datetime):
        return value.strftime(DATETIME_FMT_DISPLAY)
    else:
        return "na"

def filter_path(value, path):
    if value.startswith(path):
        return "highlight-menu"
    else:
        return "na"


def create_app():
    '''
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
    db.init_app(app)
    app.register_blueprint(people, url_prefix='')
    return app
    '''
    db = database.get_db()
    app = Flask(__name__)
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost:5432/flask_todo'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'
    # app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///E:\Development\temp\FlaskWebServer\app.db'
    #app.app_context()
    app.config.from_object(config_module)
    db.init_app(app)
    #app.register_blueprint(view_main.blueprint, url_prefix='/')
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(view_main.blueprint)
    app.register_blueprint(view_review_item.blueprint, url_prefix='/review_item')
    app.register_blueprint(view_review.blueprint, url_prefix='/review')
    app.register_blueprint(view_user.blueprint, url_prefix='/user')
    app.register_blueprint(view_analysis.blueprint, url_prefix='/analysis')
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['filterpath'] = filter_path
    # auth = HTTPTokenAuth(scheme='Token')
    #db = SQLAlchemy(app)
    # a = SQLAlchemy
    return app

#global app
#app = create_app()

#app = None

#===============================================================================
# response functions
#===============================================================================

#===============================================================================
# controlling functions
#===============================================================================

def start_app():
    # Because this is just a demonstration we set up the database like this.
    #if not os.path.isfile('/tmp/test.db'):
    #  setup_database(app)
    #app.run()
    app = create_app()
    app.run(host='0.0.0.0', port= 8090) #http://127.0.0.1:8090/index;  http://127.0.0.1:8090/api/v1   http://127.0.0.1:8090/api/v1/accounts/prudnik3

if __name__ == "__main__":
    start_app()
    #update_from_repository()

