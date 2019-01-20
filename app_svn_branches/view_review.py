import database as db
from flask.blueprints import Blueprint
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect
from flask import Flask, jsonify, request, url_for, Response
import view_analysis
from datetime import datetime

blueprint = Blueprint('review', __name__,
                 template_folder='templates',
                 static_folder='static')

@blueprint.route('/new/<review_item_id>', methods=['GET', 'POST'])
def new_review(review_item_id):
    review_item = db.getReviewItem(id=review_item_id)
    form = FormNewReview()
    form.reviewer.choices = [(g.id, g.shortname) for g in db.User.query.order_by('shortname')]

    #if form.validate_on_submit():
    if request.method == 'POST':
        if form.validate() == False:
            for key, value in form.errors.items():
                flash("{k}: {v}".format(k=key,v=";".join(value)))  # spits out any and all errors**
            return render_template('review_item.html', form=form)
        else:
            reviewer = db.getUser(id=form.reviewer.data)
            form_review = db.Review(id=None, approved=form.approved.data,
                                          note=form.note.data,
                                          review_date=datetime.strptime(form.reviewed.data, DATETIME_FMT_FORM),
                                          review_item_id=review_item.id,
                                          reviewer_id=reviewer.id)
            db.addReview(form_review, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "edit review for {r}".format(r=review_item.name)
        return render_template('review.html', action = "new", action_text=action_text, form = form, results= view_analysis.getResults())



@blueprint.route('/edit/<id>', methods=['GET', 'POST'])
def edit_review(id):
    form = FormEditReview()
    review = db.getReview(id=id)
    form.reviewer.choices = [(g.id, g.shortname) for g in db.User.query.order_by('shortname')]
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
            reviewer = db.getUser(id=form.reviewer.data)
            form_review = db.Review(id=review.id, approved=form.approved.data,
                                          note=form.note.data,
                                          review_date=review.review_date,
                                          review_item_id = review.review_item_id,
                                          reviewer_id=reviewer.id)
            db.updateReview(form_review, flash_details = True)
            return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "edit review for {r} on {dt}".format(r=review.review_item.name, dt = datetime.strftime(review.review_date,DATETIME_FMT_FORM))
        return render_template('review.html', action = "edit", action_text=action_text, form = form, results= view_analysis.getResults())

@blueprint.route('/del/<id>', methods=['GET', 'POST'])
def delete_review(id):
    form = FormNewReview()
    review = db.getReview(id=id)
    form.reviewer.choices = [(g.id, g.shortname) for g in db.User.query.order_by('shortname')]
    if request.method == 'GET':
        form.note.data = review.note
        form.reviewer.data = review.reviewer.id
        form.reviewed.data = datetime.strftime(review.review_date,DATETIME_FMT_FORM)
        form.approved.data = review.approved
        form.note.data = review.note

    #if form.validate_on_submit():
    if request.method == 'POST':
          db.deleteReview(review, flash_details = True)
          return render_template('messages.html')
    elif request.method == 'GET':
        action_text = "delete review for {r} on {dt}".format(r=review.review_item.name, dt = datetime.strftime(review.review_date,DATETIME_FMT_FORM))
        return render_template('review.html', action = "delete", action_text=action_text, form = form, results= view_analysis.getResults())

