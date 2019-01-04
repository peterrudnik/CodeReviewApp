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
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect
import babel
import subprocess

DATETIME_FMT_DISPLAY = DATETIME_FMT_FORM
DATETIME_FMT_IMPORT = '%d/%m/%Y %H:%M'
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
            "type": self.review_type.name,
            "creation_date": self.date_joined.strftime(DATETIME_FMT_DISPLAY),
            "reviews": [review.to_dict() for review in self.reviews]
        }
    
    def flash(self):
        flash('created        : {}'.format(self.creation_date.strftime(DATETIME_FMT_DISPLAY)))
        flash('review item    : {}'.format(self.name))
        review_type = getReviewType(id=self.review_type_id)
        flash('review type    : {}'.format(review_type.name))
        creator = getUser(id=self.creator_id)
        flash('reviewed aspect: {}'.format(self.reviewed_aspect))
        flash('creator        : {}'.format(creator.shortname))

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
            'review_date': self.review_date.strftime(DATETIME_FMT_DISPLAY),
            'due_date': self.due_date.strftime(DATETIME_FMT_DISPLAY) if self.due_date else None,
            'approved': self.approved,
            'review_item_id': self.review_item_id
        }

    def __repr__(self):
        return "<Review: {} | user: {}>".format(self.review_date.strftime(DATETIME_FMT_DISPLAY), str(self.reviewer_id))


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
        return value.strftime(DATETIME_FMT_DISPLAY)
    else:
        return "na"

app.jinja_env.filters['datetime'] = format_datetime

def getReviewItem(name = None, id = None):
    item = None
    if name is not None:
        item = ReviewItem.query.filter_by(name=name).first()
    if id is not None:
        item = ReviewItem.query.filter_by(id=id).first()
    return item

def flashReviewItem(review_item):
    flash('created        : {}'.format(review_item.creation_date.strftime(DATETIME_FMT_DISPLAY)))
    flash('review item    : {}'.format(review_item.name))
    review_type = getReviewType(id=review_item.review_type_id)
    flash('review type    : {}'.format(review_type.name))
    creator = getUser(id=review_item.creator_id)
    flash('reviewed aspect: {}'.format(review_item.reviewed_aspect))
    flash('creator        : {}'.format(creator.shortname))


def addReviewItem(review_item, flash_details = False):
    ret = False
    try:
        item = ReviewItem.query.filter_by(name=review_item.name).first()
        if item is None:
            nMax = ReviewItem.query.with_entities(db.func.max(ReviewItem.id)).scalar()
            if nMax is None:
                nMax = 1
            review_item.id = nMax + 1
            db.session.add(review_item)
            db.session.commit()
            flash("""New review item "{i}" has been added to the database.""".format(i=review_item.name))
            if flash_details:
                flashReviewItem(review_item)
            ret = True
        else:
            flash("""review item "{i}" already exists in the database.""".format(i=review_item.name))
    except Exception as e:
        flash(str(e))
    return ret


def updateReviewItem(review_item_in, flash_details = False):
    ret = False
    try:
        review_item = ReviewItem.query.filter_by(id=review_item_in.id).first()
        if review_item is not None:
            review_item.name = review_item_in.name
            review_item.creation_date = review_item_in.creation_date
            review_item.creator_id = review_item_in.creator_id
            review_item.reviewed_aspect = review_item_in.reviewed_aspect
            review_item.review_type_id = review_item_in.review_type_id
            db.session.commit()
            flash("""Updated review item "{i}" """.format(i=review_item.name))
            if flash_details:
                flashReviewItem(review_item)
            ret = True
        else:
            flash("""review item "{i}" does not exist in the database.""".format(i=review_item_in.name))
    except Exception as e:
        flash(str(e))
    return ret


def deleteReviewItem(review_item_in, flash_details = False):
    ret = False
    try:
        review_item = ReviewItem.query.filter_by(id=review_item_in.id).first()
        if review_item is not None:
            msgs = list()
            msgs.append("""deleted review_item "{n}" created {dt}""".format(dt=review_item.creation_date.strftime(DATETIME_FMT_DISPLAY),
                                                       n=review_item.name))

            reviews = Review.query.filter_by(review_item_id=review_item_in.id).all()
            if len(reviews) > 0:
                for review in reviews:
                    msgs.append("""deleted review "{i}" for {ri}""".format(i=review.review_date.strftime(DATETIME_FMT_DISPLAY),
                                                           ri=review.review_item.name))

                #db.session.delete(reviews)
                db.session.query(Review).filter(Review.review_item_id==review_item_in.id).delete()
            db.session.delete(review_item)
            db.session.commit()
            for msg in msgs:
                flash(msg)
            if flash_details:
                #flashReviewItem(review_item)
                review_item.flash()
            ret = True
        else:
            flash("""review item"{i}" does not exist in the database.""".format(i=review_item_in.name))
    except Exception as e:
        flash(str(e))
    return ret




def getReview(id = None):
    item = None
    if id is not None:
        item = Review.query.filter_by(id=id).first()
    return item

def flashReview(review):
    flash('review item: {}'.format(review.review_item.name))
    flash('reviewed        : {}'.format(review.review_date.strftime(DATETIME_FMT_DISPLAY)))
    reviewer = getUser(id=review.reviewer_id)
    flash('reviewer        : {}'.format(reviewer.shortname))
    flash('note        : {}'.format(review.note))
    flash('approved        : {}'.format(review.approved))

def addReview(review, flash_details = False):
    ret = False
    try:
        item = Review.query.filter_by(id=review.id).first()
        if item is None:
            nMax = Review.query.with_entities(db.func.max(Review.id)).scalar()
            if nMax is None:
                nMax = 1
            review.id = nMax + 1
            db.session.add(review)
            db.session.commit()
            flash("""New review "{i}" has been added to the database.""".format(i=review.review_date.strftime(DATETIME_FMT_DISPLAY)))
            if flash_details:
                flashReview(review)
            ret = True
        else:
            flash("""review item "{i}" already exists in the database.""".format(i=review_item.name))
    except Exception as e:
        flash(str(e))
    return ret


def updateReview(review_in, flash_details = False):
    ret = False
    try:
        review = Review.query.filter_by(id=review_in.id).first()
        if review is not None:
            #review_item.name = review_item_in.name
            review.review_date = review_in.review_date
            review.reviewer_id = review_in.reviewer_id
            review.note = review_in.note
            review.approved = review_in.approved
            db.session.commit()
            flash("""Updated review "{i}" for {ri}""".format(i=review.review_date.strftime(DATETIME_FMT_DISPLAY), ri=review.review_item.name))
            if flash_details:
                flashReview(review)
            ret = True
        else:
            flash("""review"{i}" does not exist in the database.""".format(i=review_in.review_date.strftime(DATETIME_FMT_DISPLAY)))
    except Exception as e:
        flash(str(e))
    return ret




def deleteReview(review_in, flash_details = False):
    ret = False
    try:
        review = Review.query.filter_by(id=review_in.id).first()
        if review is not None:
            msg ="""deleted review "{i}" for {ri}""".format(i=review.review_date.strftime(DATETIME_FMT_DISPLAY),
                                                       ri=review.review_item.name)
            db.session.delete(review)
            db.session.commit()
            flash(msg)
            if flash_details:
                flashReview(review)
            ret = True
        else:
            flash("""review"{i}" does not exist in the database.""".format(i=review_in.review_date.strftime(DATETIME_FMT_DISPLAY)))
    except Exception as e:
        flash(str(e))
    return ret



def getUser(shortname = None, id = None):
    item = None
    if shortname is not None:
        item = User.query.filter_by(shortname=shortname).first()
    if id is not None:
        item = User.query.filter_by(id=id).first()
    return item

def addUser(user):
    item = User.query.filter_by(shortname=user.shortname).first()
    if item is None:
        nMax = User.query.with_entities(db.func.max(User.id)).scalar()
        if nMax is None:
            nMax = 1
        user.id = nMax + 1
        ret = user.id
        db.session.add(user)
        flash("""New user "{u}" has been added to the database.""".format(u=user.shortname))

def getReviewType(name= None, id = None ):
    item = None
    if name is not None:
        item = ReviewType.query.filter_by(name=name).first()
    if id is not None:
        item = ReviewType.query.filter_by(id=id).first()
    return item


def showReviewItems():
    review_items = ReviewItem.query.all()
    for review_item in review_items:
        #print(review_item.name)
        print("review item {ri} created by {u} on {dt}".format(ri=review_item.name,u=review_item.creator.name, dt=review_item.creation_date.strftime(DATETIME_FMT_DISPLAY)))
        for review in review_item.reviews:
            print("reviewed by {u} on {dt}".format(u=review.reviewer.name, dt = review.review_date.strftime(DATETIME_FMT_DISPLAY)))
"""
def getData():
    '''
        @info: this function is not needed anymore because we do not need joins
        The same can be accomplished through class relationships
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
        creation_date = review_item[1].strftime(DATETIME_FMT_DISPLAY)
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
"""

def update_from_repository():
    #result = subprocess.run([repository_cmd, ''], stdout=subprocess.PIPE)
    #print (result.stdout)
    #print(subprocess.check_output(repository_cmd, shell=True))
    #users = User.query.all()
    #data = getData()
    #users = User.query.all()
    #review_types = ReviewType.query.all()

    output = subprocess.check_output(repository_cmd, shell=True)
    output = output.decode('utf8')
    output = output.replace('\r','')
    lst = output.split('\n')
    #remove empty strings
    #nMax = ReviewItem.query.with_entities(db.func.max(ReviewItem.id)).scalar()
    repository_data = list(filter(lambda x: len(x.strip()) > 0, lst))
    repository_data = list(filter(lambda x: x.startswith("#") == False, repository_data))
    review_type = getReviewType(name = "branch")
    count = 0
    for line in repository_data:
        fields = line.split(';')
        review_item_create_date = datetime.strptime(fields[0], DATETIME_FMT_IMPORT)
        review_item_name = fields[1]
        creator = getUser(shortname = fields[2])
        if creator is None:
            user = User(id=None, name= fields[2], shortname= fields[2], note=None, from_date=datetime.now(), to_date=None)
            creator_id = addUser(user)
            creator = getUser(shortname = fields[2])
        review_item = ReviewItem(id = None,
                                 name=review_item_name,
                                 review_type_id=review_type.id,
                                 reviewed_aspect='',
                                 creation_date = review_item_create_date,
                                 creator_id = creator.id)
        if addReviewItem(review_item):
            count +=1
    if count == 0:
         flash("No new items found in repository!")
#===============================================================================
# response functions
#===============================================================================


@app.route('/index')
def index():
    #review_items = ReviewItem.query.order_by(ReviewItem.creation_date).all()
    #review_items = ReviewItem.query.order_by(ReviewItem.creation_date).all()
    #join neccessary because of the order_by
    #review_items = ReviewItem.query.outerjoin(Review, ReviewItem.id == Review.review_item_id).order_by(ReviewItem.creation_date, Review.review_date).all()

    #review_items = ReviewItem.query.outerjoin(Review, ReviewItem.id == Review.review_item_id).join(User, User.id == ReviewItem.creator_id).order_by(
    #    ReviewItem.creation_date, Review.review_date).all()
    #return render_template('review_items.html', title='Code reviews', review_items=review_items)

    return redirect('/sort_review_item/creation_date/asc')

    #return render_template('reviewed_items.html', title='Code reviews', data=getData())
    #@app.route('/sort_review_item/creation_date/asc')

@app.route('/sort_review_item/<field>/<direction>')
def overview(field,direction):
    order_by_1 = ReviewItem.creation_date
    order_by_2 = Review.review_date
    order_by_3 = None
    if field == "name":
        order_by_1 = ReviewItem.name
    if field == "creator":
        order_by_1 = order_by_1 = User.name
        order_by_2 = ReviewItem.creation_date
        order_by_3 = Review.review_date
    if field == "review_type":
        order_by_1 = ReviewType.name
        order_by_2 = order_by_1 = User.name
        order_by_3 = ReviewItem.creation_date
    if field == "reviewed_aspect":
        order_by_1 = ReviewItem.reviewed_aspect
    review_items = ReviewItem.query.outerjoin(
        Review, ReviewItem.id == Review.review_item_id).join(
        User, User.id == ReviewItem.creator_id).join(
        ReviewType, ReviewType.id == ReviewItem.review_type_id).order_by(
        order_by_1, order_by_2, None).all()
    return render_template('review_items.html', title='Code reviews', review_items=review_items)



@app.route('/update')
def update():
    update_from_repository()
    return render_template('messages.html')
    #return render_template('reviewed_items.html', title='Code reviews', data=getData())

@app.route('/new_review_item', methods=['GET', 'POST'])
def new_review_item():
    form = FormNewReviewItem()
    form.review_type.choices = [(g.id, g.name) for g in ReviewType.query.order_by('name')]
    form.creator.choices = [(g.id, g.shortname) for g in User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            review_type = getReviewType(id=form.review_type.data)
            creator = getUser(id=form.creator.data)
            form_review_item = ReviewItem(id=None, name=form.review_item.data, review_type_id=review_type.id,
                                          reviewed_aspect='new function x',
                                          creation_date=datetime.strptime(form.created.data, DATETIME_FMT_FORM),
                                          creator_id=creator.id)
            addReviewItem(form_review_item, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "new review item"
        return render_template('review_item.html', action = "new", action_text=action_text, form = form)


@app.route('/edit_review_item/<id>', methods=['GET', 'POST'])
def edit_review_item(id):
    form = FormEditReviewItem()
    review_item = getReviewItem(id=id)
    if request.method == 'GET':
        form.created.data= datetime.strftime(review_item.creation_date,DATETIME_FMT_FORM)
        form.reviewed_aspect.data = review_item.reviewed_aspect
        form.creator.data = review_item.creator.id
        form.review_type.data = review_item.review_type.id
    form.review_type.choices = [(g.id, g.name) for g in ReviewType.query.order_by('name')]
    form.creator.choices = [(g.id, g.shortname) for g in User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            review_type = getReviewType(id=form.review_type.data)
            creator = getUser(id=form.creator.data)
            form_review_item = ReviewItem(id=review_item.id, name=review_item.name, review_type_id=review_type.id,
                                          reviewed_aspect=form.reviewed_aspect.data,
                                          creation_date=datetime.strptime(form.created.data, DATETIME_FMT_FORM),
                                          creator_id=creator.id)
            updateReviewItem(form_review_item, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "edit review item {r}".format(r=review_item.name)
        return render_template('review_item.html', action = "edit", action_text=action_text, form = form)


@app.route('/del_review_item/<id>', methods=['GET', 'POST'])
def delete_review_item(id):
    form = FormNewReviewItem()
    review_item = getReviewItem(id=id)
    if request.method == 'GET':
        form.review_item.data = review_item.name
        form.created.data= datetime.strftime(review_item.creation_date,DATETIME_FMT_FORM)
        form.reviewed_aspect.data = review_item.reviewed_aspect
        form.creator.data = review_item.creator.id
        form.review_type.data = review_item.review_type.id
    form.review_type.choices = [(g.id, g.name) for g in ReviewType.query.order_by('name')]
    form.creator.choices = [(g.id, g.shortname) for g in User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            deleteReviewItem(review_item, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "delete review item {r}".format(r=review_item.name)
        return render_template('review_item.html', action = "delete", action_text=action_text, form = form)



@app.route('/new_review/<review_item_id>', methods=['GET', 'POST'])
def new_review(review_item_id):
    review_item = getReviewItem(id=review_item_id)
    form = FormNewReview()
    form.reviewer.choices = [(g.id, g.shortname) for g in User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            reviewer = getUser(id=form.reviewer.data)
            form_review = Review(id=None, approved=form.approved.data,
                                          note=form.note.data,
                                          review_date=datetime.strptime(form.reviewed.data, DATETIME_FMT_FORM),
                                          review_item_id=review_item.id,
                                          reviewer_id=reviewer.id)
            addReview(form_review, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "edit review for {r}".format(r=review_item.name)
        return render_template('review.html', action = "new", action_text=action_text, form = form)



@app.route('/edit_review/<id>', methods=['GET', 'POST'])
def edit_review(id):
    form = FormEditReview()
    review = getReview(id=id)
    form.reviewer.choices = [(g.id, g.shortname) for g in User.query.order_by('shortname')]
    if request.method == 'GET':
        form.note.data = review.note
        form.reviewer.data = review.reviewer.id
        form.approved.data = review.approved
        form.note.data = review.note

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            reviewer = getUser(id=form.reviewer.data)
            form_review = Review(id=review.id, approved=form.approved.data,
                                          note=form.note.data,
                                          review_date=review.review_date,
                                          review_item_id = review.review_item_id,
                                          reviewer_id=reviewer.id)
            updateReview(form_review, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "edit review for {r} on {dt}".format(r=review.review_item.name, dt = datetime.strftime(review.review_date,DATETIME_FMT_FORM))
        return render_template('review.html', action = "edit", action_text=action_text, form = form)

@app.route('/del_review/<id>', methods=['GET', 'POST'])
def delete_review(id):
    form = FormNewReview()
    review = getReview(id=id)
    form.reviewer.choices = [(g.id, g.shortname) for g in User.query.order_by('shortname')]
    if request.method == 'GET':
        form.note.data = review.note
        form.reviewer.data = review.reviewer.id
        form.reviewed.data = datetime.strftime(review.review_date,DATETIME_FMT_FORM)
        form.approved.data = review.approved
        form.note.data = review.note

    #if form.validate_on_submit():
    if request.method == 'POST':
          deleteReview(review, flash_details = True)
          return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "delete review for {r} on {dt}".format(r=review.review_item.name, dt = datetime.strftime(review.review_date,DATETIME_FMT_FORM))
        return render_template('review.html', action = "delete", action_text=action_text, form = form)


class UserEvaluation(object):
    def __init__(self,user):
        self.user = user
        self.review_item_creator_count = 0
        self.review_count = 0
        self.count = 0

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    users = User.query.all()
    userEvaluations = dict()
    for user in users:
        userEvaluations[user.name] = UserEvaluation(user)

    review_items = ReviewItem.query.all()
    for review_item in review_items:
        userEvaluations[review_item.creator.name].review_item_creator_count += 1
        userEvaluations[review_item.creator.name].count += 1
    reviews = Review.query.all()
    for review in reviews:
        userEvaluations[review.reviewer.name].review_count += 1
        userEvaluations[review.reviewer.name].count += 1
    return render_template('analysis.html',userEvaluations=userEvaluations)


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


#===============================================================================
# controlling functions
#===============================================================================
def start_f1(switch = False):
    app.run(host='0.0.0.0', port= 8090) #http://127.0.0.1:8090/index;  http://127.0.0.1:8090/api/v1   http://127.0.0.1:8090/api/v1/accounts/prudnik3

if __name__ == "__main__":
    start_f1(True)
    #update_from_repository()

