from datetime import datetime
import dateutil.rrule as rrule
import calendar
from flask import  flash
import subprocess
from lxml import etree as ET
import app_svn_branches.config as cf
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


DATETIME_FMT_DISPLAY = '%Y-%m-%d %H:%M'
DATETIME_FMT_IMPORT = '%d/%m/%Y %H:%M'
# ===============================================================================
# models
# ===============================================================================

class User(db.Model):
    #__table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), nullable=False)
    shortname = db.Column(db.Unicode(64), nullable=False, unique=True)
    from_date = db.Column(db.DateTime, nullable=True)
    to_date = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.Unicode(64), nullable=True)
    review_item = db.relationship("ReviewItem",
                                  back_populates='creator')  # the first argument references the class not the table!!!!!!
    reviewer = db.relationship("Review", back_populates='reviewer')


class ReviewType(db.Model):
    #__table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'review_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), nullable=False, unique=True)
    review_item = db.relationship("ReviewItem", back_populates='review_type', lazy=True)


class ReviewItem(db.Model):
    #__table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'review_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), nullable=False, unique=True)
    review_type_id = db.Column(db.Integer, db.ForeignKey('review_type.id'), nullable=False)
    reviewed_aspect = db.Column(db.Unicode(64), nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # The following line says: populate Review.review_item it with members froms this class: a list or a single member
    reviews = db.relationship("Review", back_populates='review_item',
                              lazy=True)  # the first argument references the class not the table!!!!!!
    review_type = db.relationship("ReviewType", back_populates='review_item', lazy=True)
    creator = db.relationship("User", back_populates='review_item', lazy=True)

    #def __init__(self, *args, **kwargs):
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
        flash('created        : {}'.format(self.creation_date.strftime(DATETIME_FMT_DISPLAY)))
        flash('review item    : {}'.format(self.name))
        review_type = getReviewType(id=self.review_type_id)
        flash('review type    : {}'.format(review_type.name))
        creator = getUser(id=self.creator_id)
        flash('reviewed aspect: {}'.format(self.reviewed_aspect))
        flash('creator        : {}'.format(creator.shortname))

    def getReviewCount(self):
        return len(self.reviews)

    def hasReviews(self):
        return (len(self.reviews) > 0)

    def __repr__(self):
        return "<ReviewItem: {} | reviews: {}>".format(self.name, len(self.reviews))


class Review(db.Model):
    # __table_args__ = {"schema": "dev_noadb"}
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Unicode(64), nullable=True)
    review_date = db.Column(db.DateTime, nullable=False)
    approved = db.Column(db.Boolean, default=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_item_id = db.Column(db.Integer, db.ForeignKey('review_item.id'), nullable=False)
    review_item = db.relationship("ReviewItem",
                                  back_populates='reviews')  # the first argument references the class not the table!!!!!!
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
#  database queries
#===============================================================================
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
            flash("""review "{i}" already exists in the database.""".format(i=review.id))
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


#===============================================================================
#  import
#===============================================================================

def update_from_repository_old_old():
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


def update_from_repository_old():
    '''
      @info import from a file:

            #05.11.2018;branch;2018-11-05_mod_petchem_main;;scellej;;;
            #05.11.2018;branch;2018-11-05_mod_petchem_v2_05a_product_family;;scellej;;;
            #06.11.2018;branch;2018-11-06_mod_petchem_margins_data_transfer;;scellej;;;
            #06.11.2018;branch;2018-11-06_mod_petchem_v2_05a_refactoring_agents;;scellej;;;
            #07.11.2018;branch;2018-11-07_smithk2_crossborderDEATv2;;smithk;;;
            07.11.2018;logged error review;EXAA Downloader;;rudnikp;renzt;07.11.2018;
    :return:
    '''

    # DATETIME_FMT_IMPORT = '%d/%m/%Y %H:%M'
    DATETIME_FMT_IMPORT = '%d.%m.%Y'
    repository_update = 'e:/development/temp/FlaskWebServer/update_from_repository.txt'
    repository_cmd = 'more "C:/workspace/data/temp/CodeReviewApp/update_from_repository.txt"'

    #result = subprocess.run([repository_cmd, ''], stdout=subprocess.PIPE)
    #print (result.stdout)
    #print(subprocess.check_output(repository_cmd, shell=True))
    #users = User.query.all()
    #data = getData()
    users = User.query.all()
    review_types = ReviewType.query.all()

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
        #print(fields)
        #continue
        review_item_create_date = datetime.strptime(fields[0], DATETIME_FMT_IMPORT)
        review_type = getReviewType(name=fields[1])
        review_item_name = fields[2]
        reviewed_aspect = fields[3]
        creator = getUser(shortname = fields[4])
        if creator is None:
            user = User(id=None, name= fields[4], shortname= fields[4], note=None, from_date=datetime.now(), to_date=None)
            creator_id = addUser(user)
            creator = getUser(shortname = fields[4])
        review_item = ReviewItem(id = None,
                                 name=review_item_name,
                                 review_type_id=review_type.id,
                                 reviewed_aspect=reviewed_aspect,
                                 creation_date = review_item_create_date,
                                 creator_id = creator.id)
        if addReviewItem(review_item):
            count +=1
        if len(fields)>=7 and len(fields[5].strip()) > 0:
            reviewer = getUser(shortname=fields[5])
            review_date = datetime.strptime(fields[6], DATETIME_FMT_IMPORT)
            review_note = ""
            if len(fields)>=8:
                review_note = fields[7]
            review = Review
            review = Review(id=None, approved=True,
                                          note=review_note,
                                          review_date=review_date,
                                          review_item_id=review_item.id,
                                          reviewer_id=reviewer.id)
            addReview(review, flash_details = True)


    if count == 0:
         flash("No new items found in repository!")


def get_update_from_repository():

    #filename = "E:/Development/temp/FlaskWebServer/svn_braches_export_jan_2019.xml"
    filename = cf.config.get_file_svn_xml()
    if os.path.isfile(filename) == False:
        raise ValueError("Could not find {f}".format(f=filename))

    f = open(filename,'r')
    return f.read()

    DATETIME_FMT_IMPORT = '%d.%m.%Y'
    repository_update = config.import_from_csv_file
    repository_cmd = 'CMD /S /C svn list --xml http://RBIKARMGTP001V.b2b.regn.net:8080/svn/Paula_Python/branches'
    #result = subprocess.run([repository_cmd, ''], stdout=subprocess.PIPE)
    #print (result.stdout)
    #print(subprocess.check_output(repository_cmd, shell=True))
    #users = User.query.all()
    #data = getData()
    users = User.query.all()
    review_types = ReviewType.query.all()

    output = subprocess.check_output(repository_cmd, shell=True)
    #output = output.decode('utf8')
    output = output.replace('\r','')
    output = output.replace('\n', '')
    #lst = output.split('\n')


def update_from_repository():
    '''
      @info import from a file:

            #05.11.2018;branch;2018-11-05_mod_petchem_main;;scellej;;;
            #05.11.2018;branch;2018-11-05_mod_petchem_v2_05a_product_family;;scellej;;;
            #06.11.2018;branch;2018-11-06_mod_petchem_margins_data_transfer;;scellej;;;
            #06.11.2018;branch;2018-11-06_mod_petchem_v2_05a_refactoring_agents;;scellej;;;
            #07.11.2018;branch;2018-11-07_smithk2_crossborderDEATv2;;smithk;;;
            07.11.2018;logged error review;EXAA Downloader;;rudnikp;renzt;07.11.2018;
    :return:
    '''

    # DATETIME_FMT_IMPORT = '%d/%m/%Y %H:%M'
    _datefmt_svn_xml = "%Y-%m-%dT%H:%M:%S.%fZ"

    output = get_update_from_repository()
    try:
        root = ET.fromstring(output)
    except Exception as e:
        print str(e)
    #remove empty strings
    #nMax = ReviewItem.query.with_entities(db.func.max(ReviewItem.id)).scalar()

    lst = list()
    repository_data = list(filter(lambda x: len(x.strip()) > 0, lst))
    print (root.tag)
    for el in root.findall('list'):
        print (el)

    count = 0
    for el in root.findall('list/entry'):
        print (el)
        name = el.find('name').text
        #if name

        name =  el.find('name').text
        creator_name = el.find('commit/author').text
        creation_date =  datetime.strptime(el.find('commit/date').text, _datefmt_svn_xml)
        review_type = getReviewType(name="branch")
        creator = getUser(shortname = creator_name)
        if creator is None:
            user = User(id=None, name= creator_name, shortname= creator_name, note=None, from_date=datetime.now(), to_date=None)
            creator_id = addUser(user)
            creator = getUser(shortname = creator_name)
        review_item = ReviewItem(id = None,
                                 name=name,
                                 review_type_id=review_type.id,
                                 reviewed_aspect="",
                                 creation_date = creation_date,
                                 creator_id = creator.id)
        if addReviewItem(review_item, flash_details = True):
            count +=1
    if count == 0:
         flash("No new items found in repository!")





#===============================================================================
# controlling functions
#===============================================================================
if __name__ == "__main__":
    update_from_repository()
