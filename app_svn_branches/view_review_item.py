import database
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


blueprint = Blueprint('review_item', __name__,
                 template_folder='templates',
                 static_folder='static')


@blueprint.route('/new', methods=['GET', 'POST'])
def new_review_item():
    #db = database.get_db()
    form = FormNewReviewItem()
    form.review_type.choices = [(g.id, g.name) for g in db.ReviewType.query.order_by('name')]
    form.creator.choices = [(g.id, g.shortname) for g in db.User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            review_type = database.getReviewType(id=form.review_type.data)
            creator = database.getUser(id=form.creator.data)
            form_review_item = database.ReviewItem(id=None, name=form.review_item.data, review_type_id=review_type.id,
                                          note='new function x',
                                          creation_date=datetime.strptime(form.created.data, DATETIME_FMT_FORM),
                                          creator_id=creator.id)
            database.addReviewItem(form_review_item, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "new review item"
        return render_template('review_item.html', action = "new", action_text=action_text, form = form, results= view_analysis.getResults())


@blueprint.route('/edit/<id>', methods=['GET', 'POST'])
def edit_review_item(id):
    #db = database.get_db()
    form = FormEditReviewItem()
    review_item = database.getReviewItem(id=id)
    if request.method == 'GET':
        form.created.data= datetime.strftime(review_item.creation_date,DATETIME_FMT_FORM)
        form.note.data = review_item.note
        form.creator.data = review_item.creator.id
        form.review_type.data = review_item.review_type.id
    form.review_type.choices = [(g.id, g.name) for g in database.ReviewType.query.order_by('name')]
    form.creator.choices = [(g.id, g.shortname) for g in database.User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            review_type = database.getReviewType(id=form.review_type.data)
            creator = database.getUser(id=form.creator.data)
            form_review_item = database.ReviewItem(id=review_item.id, name=review_item.name, review_type_id=review_type.id,
                                          note=form.note.data,
                                          creation_date=datetime.strptime(form.created.data, DATETIME_FMT_FORM),
                                          creator_id=creator.id)
            database.updateReviewItem(form_review_item, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "edit review item {r}".format(r=review_item.name)
        return render_template('review_item.html', action = "edit", action_text=action_text, form = form, results= view_analysis.getResults())


@blueprint.route('/del/<id>', methods=['GET', 'POST'])
def delete_review_item(id):
    #db = database.get_db()
    form = FormNewReviewItem()
    review_item = database.getReviewItem(id=id)
    if request.method == 'GET':
        form.review_item.data = review_item.name
        form.created.data= datetime.strftime(review_item.creation_date,DATETIME_FMT_FORM)
        form.note.data = review_item.note
        form.creator.data = review_item.creator.id
        form.review_type.data = review_item.review_type.id
    form.review_type.choices = [(g.id, g.name) for g in database.ReviewType.query.order_by('name')]
    form.creator.choices = [(g.id, g.shortname) for g in database.User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            database.deleteReviewItem(review_item, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "delete review item {r}".format(r=review_item.name)
        return render_template('review_item.html', action = "delete", action_text=action_text, form = form, results= view_analysis.getResults())





@blueprint.route('/sort/<field>/<direction>')
def overview(field,direction):
    '''
    user_alias = aliased(db.User, name='user_alias')
    order_by_1 = db.ReviewItem.creation_date
    order_by_2 = db.Review.review_date
    order_by_3 = None
    if field == "name":
        order_by_1 = db.ReviewItem.name
        if direction == "desc":
            order_by_1 = db.ReviewItem.name.desc()
    if field == "creator":
        order_by_1 = db.User.name
        order_by_2 = db.ReviewItem.creation_date
        order_by_3 = db.Review.review_date
        if direction == "desc":
            order_by_1 = db.User.name.desc()
    if field == "review_type":
        order_by_1 = db.ReviewType.name
        order_by_2 = db.User.name
        order_by_3 = db.ReviewItem.creation_date
        if direction == "desc":
            order_by_1 = db.ReviewType.name.desc()
    if field == "reviewer":
        order_by_1 = user_alias.name
        order_by_2 = db.Review.review_date
        if direction == "desc":
            order_by_1 = user_alias.name.desc()
    review_items = db.ReviewItem.query.outerjoin(
        db.Review, db.ReviewItem.id == db.Review.review_item_id).join(
        db.User, db.User.id == db.ReviewItem.creator_id).join(
        db.ReviewType, db.ReviewType.id == db.ReviewItem.review_type_id).join(
        user_alias, user_alias.id == db.Review.reviewer_id).order_by(
        order_by_1, order_by_2, order_by_3).all()
    '''
    #db = database.get_db()
    review_items = database.ReviewItem.query.all()
    results = view_analysis.getResults()
    return render_template('review_items.html', title='Code reviews', review_items=review_items, results= results)

