# -*- coding: utf-8 -*-
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
import secrets
#from app_svn_branches.config import Config
from app_svn_branches.config import Config
from app_svn_branches.forms import LoginForm
from flask import render_template, flash, redirect
import babel
import subprocess

DATE_FMT = '%Y.%m.%d %H:%M'
INCOMING_DATE_FMT = '%d/%m/%Y %H:%M'
repository_update = 'e:/development/temp/FlaskWebServer/update_from_repository.txt'
repository_cmd = 'more "e:/development/temp/FlaskWebServer/update_from_repository.txt"'


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
#a = SQLAlchemy

#===============================================================================
# models
#===============================================================================

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    shortname = db.Column(db.Unicode, nullable=False, unique=True)
    from_date = db.Column(db.DateTime, nullable=True)
    to_date = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.Unicode, nullable=True)
    review_item = db.relationship("ReviewItem", back_populates='creator')  # the first argument references the class not the table!!!!!!
    reviewer = db.relationship("Review", back_populates='reviewer')

class ReviewType(db.Model):
    __tablename__ = 'review_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False,  unique=True)
    review_item = db.relationship("ReviewItem", back_populates='review_type', lazy=True)


class ReviewItem(db.Model):
    __tablename__ = 'review_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False,  unique=True)
    review_type_id = db.Column(db.Integer, db.ForeignKey('review_type.id'), nullable=False)
    reviewed_aspect = db.Column(db.Unicode, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #The following line says: populate Review.review_item it with members froms this class: a list or a single member
    reviews = db.relationship("Review", back_populates='review_item', lazy=True)# the first argument references the class not the table!!!!!!
    review_type = db.relationship("ReviewType", back_populates='review_item', lazy=True)
    creator = db.relationship("User", back_populates='review_item', lazy=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.date_joined = datetime.now()
        #self.token = secrets.token_urlsafe(64)

    def to_dict(self):
        """Get the object's properties as a dictionary."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "creation_date": self.date_joined.strftime(DATE_FMT),
            "reviews": [review.to_dict() for review in self.reviews]
        }

    def __repr__(self):
        return "<ReviewItem: {} | reviews: {}>".format(self.name, len(self.reviews))


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Unicode, nullable=True)
    review_date = db.Column(db.DateTime, nullable=False)
    approved = db.Column(db.Boolean, default=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_item_id = db.Column(db.Integer, db.ForeignKey('review_item.id'), nullable=False)
    review_item = db.relationship("ReviewItem", back_populates='reviews')# the first argument references the class not the table!!!!!!
    reviewer = db.relationship("User", back_populates='reviewer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'note': self.note,
            'review_date': self.review_date.strftime(DATE_FMT),
            'due_date': self.due_date.strftime(DATE_FMT) if self.due_date else None,
            'approved': self.approved,
            'review_item_id': self.review_item_id
        }

    def __repr__(self):
        return "<Review: {} | user: {}>".format(self.review_date.strftime(DATE_FMT), str(self.reviewer_id))


#===============================================================================
#
#===============================================================================

def format_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    #return babel.dates.format_datetime(value, format)
    if value and isinstance(value,datetime):
        return value.strftime(DATE_FMT)
    else:
        return "na"

app.jinja_env.filters['datetime'] = format_datetime


def addReviewItemIfNotExists(review_item):
    item = ReviewItem.query.filter_by(name=review_item.name).first()
    if item is None:
        nMax = ReviewItem.query.with_entities(db.func.max(ReviewItem.id)).scalar()
        if nMax is None:
            nMax = 1
        review_item.id = nMax + 1
        db.session.add(review_item)
        flash("""New review item "{i}" has been added to the database.""".format(i=review_item.name))



def getUserId(shortname = None, create = False):
    creator_id = None
    if shortname is not None:
        item = User.query.filter_by(shortname=shortname).first()
        if item is not None:
            creator_id = item.id
        elif create == True:
            user = User(id=None, name=shortname, shortname=shortname, note=None, from_date=datetime.now(), to_date=None)
            creator_id = addUserIfNotExists(user)
    return creator_id

def addUserIfNotExists(user):
    ret = None
    item = User.query.filter_by(shortname=user.shortname).first()
    if item is None:
        nMax = User.query.with_entities(db.func.max(User.id)).scalar()
        if nMax is None:
            nMax = 1
        user.id = nMax + 1
        ret = user.id
        db.session.add(user)
        flash("""New user "{u}" has been added to the database.""".format(u=user.shortname))
    else:
        ret = item.id

    return ret

def showReviewItems():
    review_items = ReviewItem.query.all()
    for review_item in review_items:
        #print(review_item.name)
        print("review item {ri} created by {u} on {dt}".format(ri=review_item.name,u=review_item.creator.name, dt=review_item.creation_date.strftime(DATE_FMT)))
        for review in review_item.reviews:
            print("reviewed by {u} on {dt}".format(u=review.reviewer.name, dt = review.review_date.strftime(DATE_FMT)))

def getData():
    '''
        @info: this function is not needed anymore because we do not need joins
        The same can be accomplished through class relationships
    :return:
    '''

    users = User.query.all()
    #review_items = ReviewItem.query.all()
    review_items = ReviewItem.query.outerjoin(Review, ReviewItem.id == Review.review_item_id).order_by(ReviewItem.creation_date).add_columns(
        ReviewItem.creation_date,
        ReviewItem.name,
        ReviewItem.type,
        ReviewItem.reviewed_aspect,
        ReviewItem.creator_id,
        Review.reviewer_id)
    #                                                                                          friendId).filter(
    #        users.id == friendships.friend_id).filter(friendships.user_id == userID).paginate(page, 1, False)
    data = list()
    for review_item in review_items:
        creation_date = review_item[1].strftime(DATE_FMT)
        name = review_item[2]
        type = review_item[3]
        reviewed_aspect = review_item[4]
        creator_id = review_item[5]
        reviewer_id = review_item[6]
        # print (review_item)
        creator = ""
        reviewer = ""
        for user in users:
            if user.id == creator_id:
                creator = user.name
            if user.id == reviewer_id:
                reviewer = user.name
        data.append([creation_date, name, type, reviewed_aspect, creator, reviewer])
        #select * from review_item where id not in (select review_item_id from review)
    #This is not necessary because of the outerjoin above
    #lst = Review.query.with_entities(Review.id).all()
    #unreviewed_items = db.engine.execute("select id, name, type reviewed_aspect,creation_date, creator_id  from review_item where id not in (select review_item_id from review)")
    #unreviewed_items = ReviewItem.query.filter_by(username='peter').first()
    #for item in unreviewed_items:
    #    print (item)
    return data

def update_from_repository():
    #result = subprocess.run([repository_cmd, ''], stdout=subprocess.PIPE)
    #print (result.stdout)
    #print(subprocess.check_output(repository_cmd, shell=True))
    #users = User.query.all()
    #data = getData()
    output = subprocess.check_output(repository_cmd, shell=True)
    output = output.decode('utf8')
    output = output.replace('\r','')
    lst = output.split('\n')
    #remove empty strings
    #nMax = ReviewItem.query.with_entities(db.func.max(ReviewItem.id)).scalar()
    repository_data = list(filter(lambda x: len(x.strip()) > 0, lst))
    repository_data = list(filter(lambda x: x.startswith("#") == False, repository_data))
    for line in repository_data:
        fields = line.split(';')
        review_item_create_date = datetime.strptime(fields[0], INCOMING_DATE_FMT)
        review_item_name = fields[1]
        review_item_type = fields[2]
        creator_id = getUserId(shortname = fields[3], create = True)
        review_item = ReviewItem(id = None,
                                 name=review_item_name,
                                 type=review_item_type,
                                 reviewed_aspect='',
                                 creation_date = review_item_create_date,
                                 creator_id = creator_id)
        addReviewItemIfNotExists(review_item)
        db.session.commit()
#===============================================================================
# response functions
#===============================================================================

@app.route('/hello')
def helloWorldHandler():
    return 'Hello World from Flask!'


@app.route('/index')
def index():
    #review_items = ReviewItem.query.order_by(ReviewItem.creation_date).all()
    review_items = ReviewItem.query.order_by(ReviewItem.creation_date).all()
    review_items = ReviewItem.query.outerjoin(Review, ReviewItem.id == Review.review_item_id).order_by(ReviewItem.creation_date, Review.review_date).all()

    return render_template('reviewed_items.html', title='Code reviews', review_items=review_items)
    #return render_template('reviewed_items.html', title='Code reviews', data=getData())


@app.route('/update')
def update():
    update_from_repository()
    return render_template('messages.html')
    #return render_template('reviewed_items.html', title='Code reviews', data=getData())


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
    return render_template('reviewed_items.html', title='Branches', data=data)

#===============================================================================
# controlling functions
#===============================================================================
def start_f1(switch = False):
    app.run(host='0.0.0.0', port= 8090) #http://127.0.0.1:8090/index;  http://127.0.0.1:8090/api/v1   http://127.0.0.1:8090/api/v1/accounts/prudnik3

if __name__ == "__main__":
    start_f1(True)
    #update_from_repository()

