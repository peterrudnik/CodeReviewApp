import database
from flask.blueprints import Blueprint
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem,FormDeleteReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect, session
from flask import Flask, jsonify, request, url_for, Response
import view_analysis
from datetime import datetime
from datetime import datetime
import dateutil.rrule as rrule
import calendar
from sqlalchemy.orm import aliased
from auth import login_required


blueprint = Blueprint('review_item', __name__,
                 template_folder='templates',
                 static_folder='static')


@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def new_review_item():
    action_text = "new review item"
    #db = database.get_db()
    form = FormNewReviewItem()
    form.review_type.choices = [(g.id, g.name) for g in database.ReviewType.query.order_by('name')]
    #form.creator.choices = [(g.id, g.shortname) for g in database.User.query.order_by('shortname')]
    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            #return render_template('review_item.html', form=form, datefmt = DATETIME_FMT_FORM)
            return render_template('review_item.html', action="new", action_text=action_text, form=form,
                                   datefmt=DATETIME_FMT_FORM, results=view_analysis.getResults(), session=session)
        else:
            review_type = database.getReviewType(id=form.review_type.data)
            #creator = database.getUser(id=form.creator.data)
            creator = database.getUser(shortname=form.creator.data)
            form_review_item = database.ReviewItem(id=None, name=form.review_item.data, review_type_id=review_type.id,
                                          note='new function x',
                                          creation_date=datetime.strptime(form.created.data, DATETIME_FMT_FORM),
                                          creator_id=creator.id)
            database.addReviewItem(form_review_item, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        form.creator.data = session['user_id']
        form.created.data = datetime.strftime(datetime.now(), DATETIME_FMT_FORM)
        return render_template('review_item.html', action = "new", action_text=action_text, form = form,
                               datefmt = DATETIME_FMT_FORM, results= view_analysis.getResults(), session = session)


@blueprint.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_review_item(id):
    #db = database.get_db()
    form = FormEditReviewItem()
    review_item = database.getReviewItem(id=id)
    action_text = "edit review item: {r}".format(r=review_item.name)
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
            return render_template('review_item.html', action="edit", action_text=action_text, form=form,
                                   datefmt=DATETIME_FMT_FORM, results=view_analysis.getResults(), session=session)
        else:
            review_type = database.getReviewType(id=form.review_type.data)
            creator = database.getUser(id=form.creator.data)
            form_review_item = database.ReviewItem(id=review_item.id, name=review_item.name, review_type_id=review_type.id,
                                          note=form.note.data,
                                          creation_date=datetime.strptime(form.created.data, DATETIME_FMT_FORM),
                                          creator_id=creator.id)
            database.updateReviewItem(form_review_item, flash_details = True)
            return render_template('messages.html', session = session)
    elif request.method == 'GET':
        return render_template('review_item.html', action = "edit", action_text=action_text, form = form,
                               datefmt=DATETIME_FMT_FORM,results= view_analysis.getResults(), session = session)


@blueprint.route('/del/<id>', methods=['GET', 'POST'])
@login_required
def delete_review_item(id):
    #db = database.get_db()
    form = FormDeleteReviewItem()
    review_item = database.getReviewItem(id=id)
    if request.method == 'GET':
        form.review_item.data = review_item.name
        form.created.data= datetime.strftime(review_item.creation_date,DATETIME_FMT_FORM)
        form.note.data = review_item.note
        form.creator.data = review_item.creator.id
        form.review_type.data = review_item.review_type.name
    #form.review_type.choices = [(g.id, g.name) for g in database.ReviewType.query.order_by('name')]
    #form.creator.choices = [(g.id, g.shortname) for g in database.User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form, session = session)
        else:
            database.deleteReviewItem(review_item, flash_details = True)
            return render_template('messages.html', session = session)
    elif request.method == 'GET':
        action_text = "delete review item: {r}".format(r=review_item.name)
        return render_template('review_item.html', action = "delete", action_text=action_text, form = form, results= view_analysis.getResults(), session = session)





@blueprint.route('/sort/<field>/<direction>')
@login_required
def overview(field,direction):
    '''
    user_alias = aliased(database.User, name='user_alias')
    order_by_1 = database.ReviewItem.creation_date
    order_by_2 = database.Review.review_date
    order_by_3 = None
    if field == "name":
        order_by_1 = database.ReviewItem.name
        if direction == "desc":
            order_by_1 = database.ReviewItem.name.desc()
    if field == "creator":
        order_by_1 = database.User.name
        order_by_2 = database.ReviewItem.creation_date
        order_by_3 = database.Review.review_date
        if direction == "desc":
            order_by_1 = database.User.name.desc()
    if field == "review_type":
        order_by_1 = database.ReviewType.name
        order_by_2 = database.User.name
        order_by_3 = database.ReviewItem.creation_date
        if direction == "desc":
            order_by_1 = database.ReviewType.name.desc()
    if field == "reviewer":
        order_by_1 = user_alias.name
        order_by_2 = database.Review.review_date
        if direction == "desc":
            order_by_1 = user_alias.name.desc()
    review_items = database.ReviewItem.query.outerjoin(
        database.Review, database.ReviewItem.id == database.Review.review_item_id).join(
        database.User, database.User.id == database.ReviewItem.creator_id).join(
        database.ReviewType, database.ReviewType.id == database.ReviewItem.review_type_id).join(
        user_alias, user_alias.id == database.Review.reviewer_id).order_by(
        order_by_1, order_by_2, order_by_3).all()
    '''
    #db = database.get_db()
    review_items = database.ReviewItem.query.all()
    results = view_analysis.getResults()
    return render_template('review_items.html', title='Code reviews', review_items=review_items, results= results, session = session)

