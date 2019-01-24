"""Script for initializing your database.

Note that dropping your existing tables is an opt-in operation.
If you want to drop tables before you create tables, set an environment
variable called "DEVELOPMENT" to be "True".
"""
from app_svn_branches.app import db, create_app
from app_svn_branches.database import ReviewItem, Review, ReviewType, User
from datetime import datetime, timedelta
from random import randint


from database import db

#if bool(os.environ.get('DEVELOPMENT', '')):
#    db.drop_all()

def create_db():
    app = create_app()
    db.drop_all(app = app)
    db.create_all(app = app)

    with app.app_context():
        db.session.add(ReviewType(id=1, name=u"branch"))
        db.session.add(ReviewType(id=2, name=u"function"))
        db.session.add(ReviewType(id=3, name=u"error"))
        db.session.add(ReviewType(id=4, name=u"module"))

        from_date = datetime(year=2018, month=1, day=1)
        db.session.add(User(id=1, name=u"heinz", shortname=u"hz", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=2, name=u"charlotte", shortname=u"ch", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=3, name=u"werner", shortname=u"wn", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=4, name=u"gabriela", shortname=u"gb", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=5, name=u"marie", shortname=u"mr", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=6, name=u"otto", shortname=u"ot", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=7, name=u"peter", shortname=u"pt", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=8, name=u"monika", shortname=u"mk", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=9, name=u"klaus", shortname=u"kl", note=u"developer", from_date=from_date, to_date=None))
        db.session.add(User(id=10, name=u"gernot", shortname=u"gt", note=u"developer", from_date=from_date, to_date=None))

        review_id = 1
        for i in range(1,20):
            review_item_create_date = datetime(year=2018, month=randint(1, 12), day=randint(1, 28), hour=randint(9, 18))
            review_item_name = u"{dt}-branch-example-{i}".format(dt = datetime.strftime(review_item_create_date,"%Y-%m-%d"), i=i)
            review_item_id = i
            creator_id = randint(1, 8)
            review_type_id = 1
            if i in [3, 5, 7]:
                review_type_id = 2
            if i in [2, 10, 11]:
                review_type_id = 3
            reviewed_aspect = u'new function x'
            review_item = ReviewItem(id = review_item_id, name=review_item_name, review_type_id=review_type_id, reviewed_aspect=reviewed_aspect, creation_date = review_item_create_date, creator_id = creator_id)
            db.session.add(review_item)

            if i < 14:
                reviewer_id = creator_id + 1
                review_item_review_date = review_item_create_date + timedelta(days = 10)
                approved = True
                if i in [3,5,7]:
                    approved = False

                if i in [2,4]:
                    review = Review(id = review_id, note=None, review_date=review_item_review_date, approved=False,
                                    reviewer_id = reviewer_id, review_item_id = review_item_id )
                    db.session.add(review)
                    review_id +=1
                    review_item_review_date = review_item_create_date + timedelta(days=11)
                    review = Review(id=review_id, note=u"second review", review_date=review_item_review_date, approved=False,
                                    reviewer_id=reviewer_id, review_item_id=review_item_id)
                    db.session.add(review)
                    review_id += 1
                    review_item_review_date = review_item_create_date + timedelta(days=12)
                    review = Review(id=review_id, note=u"third review", review_date=review_item_review_date, approved=True,
                                    reviewer_id=reviewer_id, review_item_id=review_item_id)
                    db.session.add(review)
                    review_id += 1
                else:
                    review = Review(id=review_id, note=None, review_date=review_item_review_date, approved=True,
                                    reviewer_id=reviewer_id, review_item_id=review_item_id)
                    db.session.add(review)
                    review_id += 1

        db.session.commit()
#===============================================================================
# controlling functions
#===============================================================================
if __name__ == "__main__":
    create_db()
