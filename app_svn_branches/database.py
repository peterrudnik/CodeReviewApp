from datetime import datetime
import dateutil.rrule as rrule
import calendar
from flask import flash
import subprocess
from lxml import etree as ET
import app_svn_branches.config as cf
import os
from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy import Index
import click
from flask import current_app, g
from flask.cli import with_appcontext
import app_svn_branches.GeneralClasses as gencls
import re
import locale
import dateutil
from dateutil.parser import parse
import shlex
import copy
import threading
import time

_db = SQLAlchemy()

DATETIME_FMT_DISPLAY = '%Y-%m-%d %H:%M'
DATETIME_FMT_IMPORT = '%d/%m/%Y %H:%M'
_DATETIME_FMT_SVN_XML = "%Y-%m-%dT%H:%M:%S.%fZ"


# ===============================================================================
# db
# ===============================================================================
def get_db():
    return _db

    if 'db' not in g:
        g.db = _db
        # sqlite3.connect(
        # current_app.config['DATABASE'],
        # detect_types=sqlite3.PARSE_DECLTYPES
        # )
        # g.db.row_factory = db.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


# ===============================================================================
# utilities
# ===============================================================================
use_flash = True


def myflash(msg):
    global use_flash
    try:
        if use_flash:
            flash(msg)
        else:
            print (msg)
    except Exception as e:
        raise


# ===============================================================================
# models
# ===============================================================================

class User(_db.Model):
    # __table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'tblqa_coderview_user'
    id = _db.Column(_db.Integer, primary_key=True)
    name = _db.Column(_db.Unicode(64), nullable=False)
    shortname = _db.Column(_db.Unicode(64), nullable=False, unique=True)
    from_date = _db.Column(_db.DateTime, nullable=True)
    to_date = _db.Column(_db.DateTime, nullable=True)
    note = _db.Column(_db.Unicode(64), nullable=True)
    review_item = _db.relationship("ReviewItem",
                                   back_populates='creator')  # the first argument references the class not the table!!!!!!
    reviewer = _db.relationship("Review", back_populates='reviewer')


class ReviewType(_db.Model):
    # __table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'tblqa_coderview_review_type'
    id = _db.Column(_db.Integer, primary_key=True)
    name = _db.Column(_db.Unicode(64), nullable=False, unique=True)
    review_item = _db.relationship("ReviewItem", back_populates='review_type', lazy=True)


class ReviewItem(_db.Model):
    # __table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'tblqa_coderview_review_item'
    id = _db.Column(_db.Integer, primary_key=True)
    name = _db.Column(_db.Unicode(128), nullable=False, unique=True)
    review_type_id = _db.Column(_db.Integer, _db.ForeignKey('tblqa_coderview_review_type.id'), nullable=False)
    note = _db.Column(_db.Unicode(512), nullable=False)
    creation_date = _db.Column(_db.DateTime, nullable=False)
    creator_id = _db.Column(_db.Integer, _db.ForeignKey('tblqa_coderview_user.id'), nullable=False)
    # The following line says: populate Review.review_item it with members froms this class: a list or a single member
    reviews = _db.relationship("Review", back_populates='review_item',
                               lazy=True)  # the first argument references the class not the table!!!!!!
    review_type = _db.relationship("ReviewType", back_populates='review_item', lazy=True)
    creator = _db.relationship("User", back_populates='review_item', lazy=True)

    # def __init__(self, *args, **kwargs):
    #    super(ReviewItem).__init__(*args, **kwargs)
    #    # self.date_joined = datetime.now()
    #    # self.token = secrets.token_urlsafe(64)

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
        myflash('created        : {}'.format(self.creation_date.strftime(DATETIME_FMT_DISPLAY)))
        myflash('review item    : {}'.format(self.name))
        review_type = getReviewType(id=self.review_type_id)
        myflash('review type    : {}'.format(review_type.name))
        creator = getUser(id=self.creator_id)
        myflash('note: {}'.format(self.note))
        myflash('creator        : {}'.format(creator.shortname))

    def getReviewCount(self):
        return len(self.reviews)

    def hasReviews(self):
        return (len(self.reviews) > 0)

    def __repr__(self):
        return "<ReviewItem: {} | reviews: {}>".format(self.name, len(self.reviews))


class Review(_db.Model):
    # __table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'tblqa_coderview_review'
    id = _db.Column(_db.Integer, primary_key=True)
    note = _db.Column(_db.Unicode(256), nullable=True)
    review_date = _db.Column(_db.DateTime, nullable=False)
    approved = _db.Column(_db.Boolean, default=False)
    errors = _db.Column(_db.Integer, default = 0)
    duration = _db.Column(_db.Integer, nullable=True)
    reviewer_id = _db.Column(_db.Integer, _db.ForeignKey('tblqa_coderview_user.id'), nullable=False)
    review_item_id = _db.Column(_db.Integer, _db.ForeignKey('tblqa_coderview_review_item.id'), nullable=False)
    review_item = _db.relationship("ReviewItem",
                                   back_populates='reviews')  # the first argument references the class not the table!!!!!!
    reviewer = _db.relationship("User", back_populates='reviewer', lazy=True)
    __table_args__ = (_db.Index('reviewer_date_idx', review_date, reviewer_id),
    )
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


# ===============================================================================
#  database queries
# ===============================================================================

#------------------------------------------------------------------------------------------------
# user
#------------------------------------------------------------------------------------------------

def getUser(shortname=None, id=None):
    item = None
    if shortname is not None:
        item = User.query.filter_by(shortname=shortname).first()
    if id is not None:
        item = User.query.filter_by(id=id).first()
    return item


def addUser(user, flash_details=False):
    ret = None
    try:
        db = get_db()
        if len(user.shortname.strip()) == 0:
            print ("hello")

        user_queried = User.query.filter_by(shortname=user.shortname).first()
        if user_queried is None:
            nMax = User.query.with_entities(db.func.max(User.id)).scalar()
            if nMax is None:
                nMax = 1
            user.id = nMax + 1
            ret = user.id
            db.session.add(user)
            if flash_details == True:
                myflash("""New user "{u}" has been added to the database.""".format(u=user.shortname))
        else:
            ret = user_queried.id
        return ret
    except Exception as e:
        myflash(str(e))

#------------------------------------------------------------------------------------------------
# review types
#------------------------------------------------------------------------------------------------

def getReviewType(name=None, id=None):
    item = None
    if name is not None:
        item = ReviewType.query.filter_by(name=name).first()
    if id is not None:
        item = ReviewType.query.filter_by(id=id).first()
    return item



#------------------------------------------------------------------------------------------------
# review items
#------------------------------------------------------------------------------------------------
def getReviewItem(name=None, id=None):
    item = None
    if name is not None:
        item = ReviewItem.query.filter_by(name=name).first()
    if id is not None:
        item = ReviewItem.query.filter_by(id=id).first()
    return item

def flashReviewItem(review_item):
    myflash(u'created        : {}'.format(review_item.creation_date.strftime(DATETIME_FMT_DISPLAY)))
    myflash(u'review item    : {}'.format(review_item.name))
    review_type = getReviewType(id=review_item.review_type_id)
    myflash(u'review type    : {}'.format(review_type.name))
    creator = getUser(id=review_item.creator_id)
    myflash(u'note: {}'.format(review_item.note))
    myflash(u'creator        : {}'.format(creator.shortname))


def addReviewItem(review_item, flash_details=False):
    ret = False
    try:
        db = get_db()

        #if review_item.name == u"2018-02-16_mod_NetExport_DEFR_D1_ts_D1_MR_forecast_implementation":
        #    print "hello"

        item = ReviewItem.query.filter_by(name=review_item.name).first()
        if item is None:
            nMax = ReviewItem.query.with_entities(db.func.max(ReviewItem.id)).scalar()
            if nMax is None:
                nMax = 1
            review_item.id = nMax + 1
            db.session.add(review_item)
            db.session.commit()
            myflash(u"""New review item "{i}" has been added to the database.""".format(i=review_item.name))
            if flash_details:
                flashReviewItem(review_item)
            ret = True
        else:
            myflash(u"""review item "{i}" already exists in the database.""".format(i=review_item.name))
    except Exception as e:
        myflash(str(e))
    return ret


def updateReviewItem(review_item_in, flash_details=False):
    ret = False
    try:
        db = get_db()
        review_item = ReviewItem.query.filter_by(id=review_item_in.id).first()
        if review_item is not None:
            review_item.name = review_item_in.name
            review_item.creation_date = review_item_in.creation_date
            review_item.creator_id = review_item_in.creator_id
            review_item.note = review_item_in.note
            review_item.review_type_id = review_item_in.review_type_id
            db.session.commit()
            myflash(u"""Updated review item "{i}" """.format(i=review_item.name))
            if flash_details:
                flashReviewItem(review_item)
            ret = True
        else:
            myflash(u"""review item "{i}" does not exist in the database.""".format(i=review_item_in.name))
    except Exception as e:
        myflash(str(e))
    return ret


def deleteReviewItem(review_item_in, flash_details=False):
    ret = False
    try:
        db = get_db()
        review_item = ReviewItem.query.filter_by(id=review_item_in.id).first()
        if review_item is not None:
            msgs = list()
            msgs.append("""deleted review_item "{n}" created {dt}""".format(
                dt=review_item.creation_date.strftime(DATETIME_FMT_DISPLAY),
                n=review_item.name))

            reviews = Review.query.filter_by(review_item_id=review_item_in.id).all()
            if len(reviews) > 0:
                for review in reviews:
                    msgs.append(
                        """deleted review "{i}" for {ri}""".format(i=review.review_date.strftime(DATETIME_FMT_DISPLAY),
                                                                   ri=review.review_item.name))

                # db.session.delete(reviews)
                db.session.query(Review).filter(Review.review_item_id == review_item_in.id).delete()
            db.session.delete(review_item)
            db.session.commit()
            for msg in msgs:
                myflash(msg)
            if flash_details:
                # flashReviewItem(review_item)
                review_item.flash()
            ret = True
        else:
            myflash("""review item"{i}" does not exist in the database.""".format(i=review_item_in.name))
    except Exception as e:
        myflash(str(e))
    return ret

def showReviewItems():
    review_items = ReviewItem.query.all()
    for review_item in review_items:
        # print(review_item.name)
        print("review item {ri} created by {u} on {dt}".format(ri=review_item.name, u=review_item.creator.name,
                                                               dt=review_item.creation_date.strftime(
                                                                   DATETIME_FMT_DISPLAY)))
        for review in review_item.reviews:
            print("reviewed by {u} on {dt}".format(u=review.reviewer.name,
                                                   dt=review.review_date.strftime(DATETIME_FMT_DISPLAY)))

#------------------------------------------------------------------------------------------------
# reviews
#------------------------------------------------------------------------------------------------
def getReview(id=None, reviewer_id = None, review_date = None):
    item = None
    if id is not None:
        item = Review.query.filter_by(id=id).first()
    if reviewer_id is not None and review_date is not None:
        item = Review.query.filter_by(reviewer_id=reviewer_id, review_date=review_date).first()
    return item


def flashReview(review):
    myflash('review item: {}'.format(review.review_item.name))
    myflash('reviewed        : {}'.format(review.review_date.strftime(DATETIME_FMT_DISPLAY)))
    reviewer = getUser(id=review.reviewer_id)
    myflash('reviewer        : {}'.format(reviewer.shortname))
    myflash('note        : {}'.format(review.note))
    myflash('approved        : {}'.format(review.approved))


def addReview(review, flash_details=False):
    ret = False
    try:
        db = get_db()
        item = Review.query.filter_by(review_date=review.review_date, reviewer_id = review.reviewer_id).first()
        if item is None:
            nMax = Review.query.with_entities(db.func.max(Review.id)).scalar()
            if nMax is None:
                nMax = 1
            review.id = nMax + 1
            db.session.add(review)
            db.session.commit()
            myflash("""New review "{i}" has been added to the database.""".format(
                i=review.review_date.strftime(DATETIME_FMT_DISPLAY)))
            if flash_details:
                flashReview(review)
            ret = True
        else:
            myflash("""review "{i}" already exists in the database.""".format(i=review.id))
    except Exception as e:
        myflash(str(e))
    return ret


def updateReview(review_in, flash_details=False):
    ret = False
    try:
        db = get_db()
        review = Review.query.filter_by(id=review_in.id).first()
        if review is not None:
            # review_item.name = review_item_in.name
            review.review_date = review_in.review_date
            review.reviewer_id = review_in.reviewer_id
            review.note = review_in.note
            review.approved = review_in.approved
            db.session.commit()
            myflash("""Updated review "{i}" for {ri}""".format(i=review.review_date.strftime(DATETIME_FMT_DISPLAY),
                                                               ri=review.review_item.name))
            if flash_details:
                flashReview(review)
            ret = True
        else:
            myflash("""review"{i}" does not exist in the database.""".format(
                i=review_in.review_date.strftime(DATETIME_FMT_DISPLAY)))
    except Exception as e:
        myflash(str(e))
    return ret


def deleteReview(review_in, flash_details=False):
    ret = False
    try:
        db = get_db()
        review = Review.query.filter_by(id=review_in.id).first()
        if review is not None:
            msg = """deleted review "{i}" for {ri}""".format(i=review.review_date.strftime(DATETIME_FMT_DISPLAY),
                                                             ri=review.review_item.name)
            db.session.delete(review)
            db.session.commit()
            myflash(msg)
            if flash_details:
                flashReview(review)
            ret = True
        else:
            myflash("""review"{i}" does not exist in the database.""".format(
                i=review_in.review_date.strftime(DATETIME_FMT_DISPLAY)))
    except Exception as e:
        myflash(str(e))
    return ret



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
        ReviewItem.note,
        ReviewItem.creator_id,
        Review.reviewer_id)
    #                                                                                          friendId).filter(
    #        users.id == friendships.friend_id).filter(friendships.user_id == userID).paginate(page, 1, False)
    data = list()
    for review_item in review_items:
        creation_date = review_item[1].strftime(DATETIME_FMT_DISPLAY)
        name = review_item[2]
        type = review_item[3]
        note = review_item[4]
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
        data.append([creation_date, name, type, note, creator, reviewer])
        #select * from review_item where id not in (select review_item_id from review)
    #This is not necessary because of the outerjoin above
    #lst = Review.query.with_entities(Review.id).all()
    #unreviewed_items = db.engine.execute("select id, name, type note,creation_date, creator_id  from review_item where id not in (select review_item_id from review)")
    #unreviewed_items = ReviewItem.query.filter_by(username='peter').first()
    #for item in unreviewed_items:
    #    print (item)
    return data
"""


# ===============================================================================
#  import
# ===============================================================================

# ===============================================================================
#
# ===============================================================================

class ImportReviewItem(gencls.Item):
    def __init__(self, name=None, creator_id=None, creation_date=None, last_commit_dt=None, note=None, review_type_id = None):
        super(gencls.Item, self).__init__()
        self.review_item =  ReviewItem(id=None,
                                     name=name,
                                     review_type_id=review_type_id,
                                     note=note,
                                     creation_date=creation_date,
                                     creator_id=creator_id)
        self.last_commit_dt = last_commit_dt
        self.new_user = None

    def toString(self):
        sep = ','
        s = ""
        if self.review_item.creation_date is not None:
            s += self.review_item.creation_date.strftime("%Y-%m-%d") + sep
        else:
            s += "" + sep
        #if self.last_commit_dt is not None:
        #    s += self.last_commit_dt.strftime("%Y-%m-%d") + sep
        #else:
        #    s += "" + sep
        if self.review_item.review_type_id is not None:
            s += str(self.review_item.review_type_id) + sep
        else:
            s += "" + sep
        if self.review_item.name is not None:
            s += self.review_item.name + sep
        else:
            s += "" + sep
        if self.review_item.note is not None:
            s += self.review_item.note + sep
        else:
            s += "" + sep
        if self.review_item.creator_id is not None:
            s += str(self.review_item.creator_id)
        elif self.new_user is not None:
            s += self.new_user.shortname
        else:
            s += ""
        return s

    def check(self, importLine):
        ret = True
        msg = ""
        if self.review_item.creation_date is None:
            if importLine.name is None:
                importLine.name = ""
            if importLine.creation_date is None:
                importLine.creation_date = ""
            msg = "Cound not identifiy creation date: {dt} for review item {ri}" \
                  "".format(dt=importLine.creation_date, ri=importLine.name)
            ret = False
    
        if self.review_item.review_type_id is None:
            if importLine.review_type is None:
                importLine.review_type = ""
            msg = "Unknown review type: {rt}".format(rt=importLine.review_type)
            ret = False
        return ret, msg


# -----------------------------------------------------------------------------------------------------------------
class ImportReview(gencls.Item):
    def __init__(self, name=None, reviewer_id=None, review_date=None, note=None, review_item_id = None,approved = False ):
        super(gencls.Item, self).__init__()
        self.review = Review(id=None,
                        approved=approved,
                        note=note,
                        review_date=review_date,
                        review_item_id=review_item_id,
                        reviewer_id=reviewer_id)
        self.new_user = None
        self.new_review_item = None

    def toString(self):
        sep = ','
        s = ""
        if self.review.review_date is not None:
            s += self.review.review_date.strftime("%Y-%m-%d") + sep
        else:
            s += "" + sep
        if self.review.review_item_id is not None:
            s += str(self.review.review_item_id) + sep
        else:
            s += "" + sep
        if self.review.note is not None:
            s += self.review.note + sep
        else:
            s += "" + sep
        if self.review.reviewer_id is not None:
            s += str(self.review.reviewer_id)
        elif self.new_user is not None:
            s += self.new_user.shortname
        else:
            s += ""
        if self.review.approved is not None and self.review.approved == True:
            s += "yes" + sep
        else:
            s += "no" + sep
        return s

    def check(self, importLine):
        ret = True
        msg = ""
        self.review.review_date = getDate(importLine.review_date)
        if self.review.review_date is None:
            if importLine.review_date is None:
                importLine.review_date = ""
            msg = "Cound not identifiy review date: {dt}" \
                    "".format(dt=importLine.review_date)
            ret = False

        return ret, msg

class ImportLine(object):
    def __init__(self, creation_date = None,
                 review_type = None,
                 name = None,
                 creator = None,
                 review_item_note=None,
                 review_date = None,
                 reviewer = None,
                 review_note = None,
                 errors = None,
                 duration = None):
        self.line_number = None
        self.line = None
        self.creation_date = creation_date
        self.review_type = review_type
        self.name = name
        self.review_item_note = review_item_note
        self.creator = creator
        self.reviewer = reviewer
        self.review_date = review_date
        self.review_note = review_note
        self.hasReview = False
        self.errors = errors
        self.duration = duration

    def check(self):
        if self.creator is not None and len(self.creator.strip()) == 0:
            print "hello"
        if u"rudnikp" in self.creator and "renzt" in self.creator:
            print "hello"
        if u"rudnikp" in self.creator and "scelle" in self.creator:
            print "hello"
        if self.hasReview == True:
            if self.reviewer is not None and len(self.reviewer.strip()) == 0:
                print "hello"
            if u"rudnikp" in self.reviewer and "renzt" in self.reviewer:
                print "hello"
            if u"rudnikp" in self.reviewer and "scelle" in self.reviewer:
                print "hello"


# -----------------------------------------------------------------------------------------------------------------
def getDate(str):
    review_date = None
    #28-Nov-18
    #04/12/2018
    datefmts = [DATETIME_FMT_IMPORT, "%d-%b-%y", "%d/%m/%Y"]
    for datefmt in datefmts:
        try:
            review_date = datetime.strptime(str, DATETIME_FMT_IMPORT)
            break
        except Exception as e:
            pass
    if  review_date is None:
        try:
            review_date = parse(str)
        except Exception as e:
            pass


    return review_date


# -----------------------------------------------------------------------------------------------------------------
def import_review_items(review_items):
    count_new_review_items = 0
    count_new_users = 0
    for import_item in review_items:
        #print (import_item.toString())
        if import_item.new_user is not None:
            creator_id = addUser(import_item.new_user)
            #creator = getUser(shortname=import_item.new_user.shortname)
            import_item.review_item.creator_id = creator_id
        if addReviewItem(import_item.review_item):
             count_new_review_items += 1

def import_reviews(reviews):
    count_new_reviews = 0
    count_new_users = 0
    for import_item in reviews:
        #print (import_item.toString())
        if import_item.new_user is not None:
            creator_id = addUser(import_item.new_user)
            #creator = getUser(shortname=import_item.new_user.shortname)
            import_item.review.reviewer_id = creator_id
        if import_item.new_review_item is not None:
           review_item = getReviewItem(name = import_item.new_review_item.name)
           if review_item is None:
               myflash("Could not find review item {ri} when importing reviews".format(ri = import_item.new_review_item.name))
           import_item.review.review_item_id = review_item.id
        if addReview(import_item.review):
             count_new_reviews += 1





# -----------------------------------------------------------------------------------------------------------------
def update_from_file(has_request=True):
    '''
      @info import from a file
    :return:
    '''
    global use_flash
    if has_request == False:
        use_flash = False

    # DATETIME_FMT_IMPORT = '%d/%m/%Y %H:%M'
    DATETIME_FMT_IMPORT = '%d.%m.%Y'
    users = User.query.all()
    review_types = ReviewType.query.all()

    filename = cf.config.get_file_csv()
    if os.path.isfile(filename) == False:
        myflash("File does not exist file {f}".format(f=filename))
        return

    locale.setlocale(locale.LC_ALL, "us")
    try:
        with open(filename, "r") as inFile:
            # output = inFile.read()

            # output = output.decode('utf8')
            # output = output.replace('\r','')
            # lst = output.split('\n')
            # remove empty strings
            # nMax = ReviewItem.query.with_entities(db.func.max(ReviewItem.id)).scalar()
            # repository_data = list(filter(lambda x: len(x.strip()) > 0, lst))
            # repository_data = list(filter(lambda x: x.startswith("#") == False, repository_data))
            #review_type = getReviewType(name="branch")
            # review_types = ReviewType.query.all()
            #review_type = getReviewType(name="branch")

            note_user = u"by import {dt}".format(dt=datetime.now().strftime("%Y-%m-%d %H:%M"))
            review_items = gencls.ItemColl()
            reviews = gencls.ItemColl()
            count_review_items = 0
            count_reviews = 0
            line_number = 0
            for line in inFile:
                line_number += 1
                line = line.strip().decode("utf8")
                if (len(line) == 0):
                    continue
                if line.startswith(u"#"):
                    continue

                #fields = line.split(u',')
                #fields = [p for p in re.split("( |\\\".*?\\\"|'.*?')", test) if p.strip()]
                fields = gencls.LineSplitter.split(line,quotechar =u'"', splitchar = u";")

                for index, field in enumerate(fields):
                    fields[index] = field.strip()
                # print(fields)
                # continue
                if fields[2]=="2018-06-19_smithk2_addFrAvailCapacitiesWebTable":
                    print ("hello")
                if len(fields) < 5:
                    myflash("Not enough fields in line {ln} : {line}".format(ln=str(line_number), line = line))
                importLine = ImportLine(creation_date=fields[0],
                                        review_type = fields[1],
                                        name = fields[2],
                                        review_item_note = fields[3],
                                        creator = fields[4])
                importLine.line_number = line_number
                importLine.line = line
                if len(fields) >= 7:
                    importLine.reviewer = fields[5]
                    importLine.review_date = fields[6]
                    if len(importLine.reviewer) >0 and len(importLine.review_date) > 0:
                        importLine.hasReview = True
                if len(fields) > 7:
                    try:
                        importLine.duration = int(fields[7])
                    except ValueError:
                        pass
                if len(fields) > 8:
                    try:
                        importLine.errors = int(fields[8])
                    except ValueError:
                        pass
                if len(fields) > 11:
                    importLine.review_note = fields[11]


                #importLine.check()

                review_item = getReviewItem(name = importLine.name)
                if review_item is None:
                    item = ImportReviewItem()
                    #item.review_item.creation_date = datetime.strptime(importLine.creation_date, DATETIME_FMT_IMPORT)
                    item.review_item.creation_date = getDate(importLine.creation_date)
                    review_type = getReviewType(name=importLine.review_type)
                    if review_type is not None:
                        item.review_item.review_type_id = review_type.id
                    item.review_item.name = importLine.name
                    item.review_item.note = importLine.review_item_note

                    if importLine.creator is None or len(importLine.creator.strip()) == 0:
                        if importLine.name is None:
                            importLine.name = ""
                        msg = "Cound not identifiy user for review item {ri}" \
                              "".format(ri=importLine.name)
                        myflash("Error in line {ln}:{msg}".format(msg=msg, ln=line_number))
                        continue

                    creator = getUser(shortname=importLine.creator)
                    # mark for creation of a new user if not exists
                    if creator is None:
                        shortname = importLine.creator
                        item.new_user = User(id=None, name=shortname, shortname=shortname, note=note_user,
                                             from_date=item.review_item.creation_date,
                                             to_date=None)
                    else:
                        item.review_item.creator_id = creator.id
                        
                    check, msg = item.check(importLine)
                    if check == False:
                        myflash("Error in line {ln}:{msg}".format(msg=msg, ln = line_number))
                        continue

                    review_items.add(item)
                    count_review_items += 1
                    review_item = item.review_item
                    #review_item = getReviewItem(name=item.review_item.name)


                # handle reviews
                if review_item is not None and importLine.review_date is not None and len(importLine.review_date)>0\
                        and importLine.reviewer is not None and len(importLine.reviewer)>0:
                    item = ImportReview(review_item_id=review_item.id, approved=True)
                    if review_item.id is None:
                        item.new_review_item = copy.deepcopy(review_item)
                    item.review.review_date = getDate(importLine.review_date)
                    item.review.duration = importLine.duration
                    item.review.note = importLine.review_note
                    item.review.errors = importLine.errors
                    # mark for creation of a new user if not exists
                    reviewer = getUser(shortname=fields[5])
                    # if we don't have a reviewer there cannot be any reviews
                    # so we only check for existing reviews in the else branch
                    if reviewer is None:
                        shortname = fields[5]
                        item.new_user = User(id=None, name=shortname, shortname=shortname, note=note_user,
                                             from_date=item.review.review_date,
                                             to_date=None)
                    else:
                        item.review.reviewer_id = reviewer.id
                        #is the reviewalready in? identify by date and user
                        #don't know the user id, but if it a new user then it must be a new review
                        review = getReview(reviewer_id=reviewer.id, review_date=item.review.review_date)
                        if review is not None:
                            continue

                    check, msg = item.check(importLine)
                    if check == False:
                        myflash("Error in line {ln}:{msg}".format(msg=msg, ln=line_number))
                        continue
                    reviews.add(item)
                    count_reviews += 1

            if count_review_items == 0:
                myflash("No new review items found in repository!")
            else:
                # review_item_list_sorted = review_item_list.coll.sort(key = lambda x: x.dt, reverse=False )
                review_items.sort(key=lambda x: x.review_item.creation_date, reverse=False)
                # for item in review_item_list:
                #    print(item.toString())
                filename = cf.config.get_file_csv()
                filename = filename.replace(".csv", "_review_items.csv")
                # csv_file = fil.changeExtension(svn_file, ".csv")
                with open(filename, 'w') as outFile:
                    for item in review_items:
                        outFile.write(item.toString().encode('utf8') + "\n")
                import_review_items(review_items)

            if count_reviews == 0:
                myflash("No new reviews found in repository!")
            else:
                # review_item_list_sorted = review_item_list.coll.sort(key = lambda x: x.dt, reverse=False )
                reviews.sort(key=lambda x: x.review.review_date, reverse=False)
                # for item in review_item_list:
                #    print(item.toString())
                filename = cf.config.get_file_csv()
                filename = filename.replace(".csv", "_reviews.csv")
                # csv_file = fil.changeExtension(svn_file, ".csv")
                with open(filename, 'w') as outFile:
                    for item in reviews:
                        outFile.write(item.toString().encode('utf8') + "\n")
                import_reviews(reviews)


    except Exception as e:
        myflash("Unable to read file {f} : {e}".format(f=filename, e=str(e)))
        raise
    finally:
        locale.setlocale(locale.LC_ALL, u"")


# -----------------------------------------------------------------------------------------------------------------
def export_svn_branches_to_xml():
    svn_url = cf.config.get_svn_url()
    repository_cmd = "CMD /S /C svn list --xml {svn_url}".format(svn_url=svn_url)
    # result = subprocess.Popen([repository_cmd, ''], stdout=subprocess.PIPE)
    output = subprocess.check_output(repository_cmd, shell=True)

    filename = cf.config.get_file_svn_xml()
    with open(filename, 'w') as outFile:
        outFile.write(output.decode('utf8'))

# -----------------------------------------------------------------------------------------------------------------
def update_from_repository(has_request=True, skip_export=False):
    global use_flash
    if has_request == False:
        use_flash = False

    try:
        if skip_export == False:
            export_svn_branches_to_xml()

        filename = cf.config.get_file_svn_xml()
        with open(filename, 'r') as inFile:
            output = inFile.read()
            #output = output.decode('utf8')

        root = ET.fromstring(output)
    except Exception as e:
        myflash(str(e))
        return

    #review_types = ReviewType.query.all()
    review_type = getReviewType(name=u"branch")

    note = "by import {dt}".format(dt=datetime.now().strftime("%Y-%m-%d %H:%M"))
    review_items = gencls.ItemColl()
    for el in root.findall('list/entry'):
        # print (el)
        item = ImportReviewItem(review_type_id = review_type.id, note = note)
        item.review_item.name = el.find('name').text.decode("utf8")
        result = re.search("([0-9]{4}).([0-9]{2}).([0-9]{2})",  item.review_item.name, re.IGNORECASE)
        if result != None:
            try:
                item.review_item.creation_date = datetime(year=int(result.group(1)), month=int(result.group(2)), day=int(result.group(3)))
            except Exception as e:
                print ("branch ignored: {n} date conversion error: {e}".format(n=item.review_item.name, e=str(e)))
                continue
        else:
            print ("branch ignored: {n}".format(n=item.review_item.name))
            continue
        shortname = el.find('commit/author').text.decode("utf8")
        creator = getUser(shortname=shortname)
        if creator is None:
            item.new_user = shortname
            item.new_user = User(id=None, name=shortname, shortname=shortname, note=note, from_date=item.review_item.creation_date,
                    to_date=None)
        else:
            item.review_item.creator_id = creator.id

        item.last_commit_dt = datetime.strptime(el.find('commit/date').text, _DATETIME_FMT_SVN_XML)

        review_items.add(item)

    # review_item_list_sorted = review_item_list.coll.sort(key = lambda x: x.dt, reverse=False )
    review_items.sort(key=lambda x: item.review_item.creation_date, reverse=False)

    # for item in review_item_list:
    #    print(item.toString())

    filename = cf.config.get_file_svn_xml()
    filename = filename.replace(".xml",".csv")
    #csv_file = fil.changeExtension(svn_file, ".csv")
    with open(filename, 'w') as outFile:
        for item in review_items:
            outFile.write(item.toString().decode('utf8') + "\n")

    import_review_items(review_items)



class ImportingThread(threading.Thread):
    def __init__(self):
        self.progress = 0
        super(threading.Thread).__init__()

    def run(self):
        # Your exporting stuff goes here ...
        for _ in range(10):
            time.sleep(1)
            self.progress += 10




# ===============================================================================
# controlling functions
# ===============================================================================
if __name__ == "__main__":
    pass