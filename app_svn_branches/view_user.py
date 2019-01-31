import database
from flask.blueprints import Blueprint
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect
from flask import Flask, jsonify, request, url_for, Response
import view_analysis
from datetime import datetime

blueprint = Blueprint('user', __name__,
                 template_folder='templates',
                 static_folder='static')

@blueprint.route('/', methods=['GET'])
def show_users():
    #db = database.get_db()
    users = database.User.query.all()
    return render_template('users.html',users=users, results= view_analysis.getResults())

