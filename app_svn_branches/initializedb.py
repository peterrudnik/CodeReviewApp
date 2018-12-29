"""Script for initializing your database.

Note that dropping your existing tables is an opt-in operation.
If you want to drop tables before you create tables, set an environment
variable called "DEVELOPMENT" to be "True".
"""
from app_svn_branches.app import db
from app_svn_branches.app import ReviewItem, Review, User
from datetime import datetime, timedelta
from random import randint


#from app import db

#if bool(os.environ.get('DEVELOPMENT', '')):
#    db.drop_all()

def create_db():
    db.drop_all()
    db.create_all()
    for i in range(1,10):
        from_date = datetime(year=2018, month=1, day=1)
        name = "user {i}".format(i=i)
        shortname = "u{i}".format(i=i)
        user = User(id = i, name=name, shortname=shortname, note=None, from_date = from_date, to_date = None)
        db.session.add(user)
    for i in range(1,20):
        review_item_create_date = datetime(year=2018, month=randint(1, 12), day=randint(1, 28), hour=randint(9, 18))
        review_item_name = "{dt}-branch-example-{i}".format(dt = datetime.strftime(review_item_create_date,"%Y-%m-%d"), i=i)
        review_item_id = i
        creator_id = randint(1, 8)
        review_item = ReviewItem(id = review_item_id, name=review_item_name, type='branch', reviewed_aspect='new function x', creation_date = review_item_create_date, creator_id = creator_id)
        db.session.add(review_item)

        if i < 14:
            reviewer_id = creator_id + 1
            review_item_review_date = review_item_create_date + timedelta(days = 10)
            review = Review(id = i, note=None, review_date=review_item_review_date, approved=True, reviewer_id = reviewer_id, review_item_id = review_item_id )
            db.session.add(review)



    db.session.commit()
#===============================================================================
# controlling functions
#===============================================================================
if __name__ == "__main__":
    create_db()
