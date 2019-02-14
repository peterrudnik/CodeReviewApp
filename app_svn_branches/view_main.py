import database
from flask.blueprints import Blueprint
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect, session
from flask import Flask, jsonify, request, url_for, Response
from flask import session
import view_analysis
from datetime import datetime
from datetime import datetime
import dateutil.rrule as rrule
import calendar
from sqlalchemy.orm import aliased
from auth import login_required


blueprint = Blueprint('main', __name__,
                 template_folder='templates',
                 static_folder='static')

@blueprint.route('/index')
@login_required
def index():
    # review_items = db.ReviewItem.query.order_by(db.ReviewItem.creation_date).all()
    # review_items = db.ReviewItem.query.order_by(db.ReviewItem.creation_date).all()
    # join neccessary because of the order_by
    # review_items = db.ReviewItem.query.outerjoin(Review, db.ReviewItem.id == Review.review_item_id).order_by(db.ReviewItem.creation_date, Review.review_date).all()

    # review_items = db.ReviewItem.query.outerjoin(Review, db.ReviewItem.id == Review.review_item_id).join(User, User.id == db.ReviewItem.creator_id).order_by(
    #    db.ReviewItem.creation_date, Review.review_date).all()
    # return render_template('review_items.html', title='Code reviews', review_items=review_items)

    return redirect('/review_item/sort/creation_date/asc')

    # return render_template('reviewed_items.html', title='Code reviews', data=getData())
    # @app.route('/sort_review_item/creation_date/asc')

@blueprint.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    #db = database.get_db()
    #database.update_from_repository()
    if request.method == 'POST':
        ret, import_review_items, import_reviews = database.get_update_from_file()
        form_items = request.form.getlist('check')
        for import_review_item in import_review_items:
            if import_review_item.review_item.name in form_items:
                import_review_item.confirmed_by_user = True
        for import_review in import_reviews:
            id = import_review.review_item.name + str(import_review.uid)
            if id in form_items:
                import_review.confirmed_by_user = True
        database.import_review_items(import_review_items)
        database.import_reviews(import_reviews)
        return render_template('messages.html', session = session)
    else:
        ret, import_review_items, import_reviews = database.get_update_from_file()
        if ret == False:
        #return render_template('messages.html', results=view_analysis.getResults(), session = session)
            return render_template('messages.html', session = session)
        else:
            return render_template('import.html', import_review_items=import_review_items, import_reviews=import_reviews, session = session)
    # return render_template('reviewed_items.html', title='Code reviews', data=getData())

@blueprint.route('/about', methods=['GET'])
@login_required
def show_about():
    about = list()
    about.append("Code review app written by Peter Rudnik")
    about.append("Berlin, Karlsruhe, Germany")
    about.append("project start: Dec 2018 ")
    about.append("last change: Jan 2019 ")

    return render_template('about.html', about=about, results=view_analysis.getResults(), session = session)


#@blueprint.route('/progress/<percent>', methods=['GET'])
@blueprint.route('/progress/<percent>', methods=['GET'])
@login_required
def show_progress(percent):
    #for i in range(10)
    progress = str(percent)
    return render_template('progress.html', progress=progress, results=view_analysis.getResults(), session = session)

# @app.route('/mylogin')
# def mylogin():
#    form = LoginForm()
#    return render_template('login.html', title='Sign In', form=form)

"""
@app.route('/mylogin', methods=['GET', 'POST'])
def mylogin():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        #return redirect('/api/v1/accounts/login')
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form)
"""

