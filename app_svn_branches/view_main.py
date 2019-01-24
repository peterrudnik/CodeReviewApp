import database as db
from flask.blueprints import Blueprint
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect
from flask import Flask, jsonify, request, url_for, Response
import view_analysis
from datetime import datetime
from datetime import datetime
import dateutil.rrule as rrule
import calendar
from sqlalchemy.orm import aliased


blueprint = Blueprint('main', __name__,
                 template_folder='templates',
                 static_folder='static')


@blueprint.route('/index')
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

@blueprint.route('/update')
def update():
    db.update_from_repository()
    return render_template('messages.html', results=view_analysis.getResults())
    # return render_template('reviewed_items.html', title='Code reviews', data=getData())

@blueprint.route('/about', methods=['GET'])
def show_about():
    about = list()
    about.append("Code review app written by Peter Rudnik")
    about.append("Berlin, Karlsruhe, Germany")
    about.append("project start: Dec 2018 ")
    about.append("last change: Jan 2019 ")

    return render_template('about.html', about=about, results=view_analysis.getResults())

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

