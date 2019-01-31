import database
from flask.blueprints import Blueprint
from app_svn_branches.forms import LoginForm, FormEditReview, FormNewReview, FormEditReviewItem,FormNewReviewItem, DATETIME_FMT_FORM
from flask import render_template, flash, redirect
from flask import Flask, jsonify, request, url_for, Response
from datetime import datetime
import dateutil.rrule as rrule
import calendar


blueprint = Blueprint('analysis', __name__,
                 template_folder='templates',
                 static_folder='static')



#===============================================================================
# utilities
#===============================================================================
def getBeginningAndEndOfMonth(dt):
    days = calendar.monthrange(dt.year,dt.month)
    return dt.replace(day=1),dt.replace(day=days[1])

# ===============================================================================
# analysis
# ===============================================================================

class ReviewInterval(object):
    def __init__(self, name, startdate, enddate):
        self.name = name
        self.startDate = startdate
        self.endDate = enddate
        self.review_item_creator_count = 0
        self.review_count = 0
        self.participation_count = 0

    def evaluate_review_item(self, dt):
        if dt >= self.startDate and dt <= self.endDate:
            self.review_item_creator_count += 1
            self.participation_count += 1

    def evaluate_review(self, dt):
        if dt >= self.startDate and dt <= self.endDate:
            self.review_count += 1
            self.participation_count += 1


class UserEvaluation(object):
    def __init__(self, user):
        self.user = user
        self.review_intervals = list()

    def getReviewInterval(self, interval_name):
        ret = None
        for review_interval in self.review_intervals:
            if review_interval.name == interval_name:
                ret = review_interval
                break
        return ret


def getReviewIntervals(startdate, enddate):
    lst = list()
    name = "all"
    lst.append(ReviewInterval(name, startdate, enddate))
    dt_year_range = rrule.rrule(rrule.YEARLY, dtstart=startdate, until=enddate)
    for dt in dt_year_range:
        name = dt.strftime("%Y")
        period_startdate, period_enddate = getBeginningAndEndOfMonth(dt)
        lst.append(ReviewInterval(name, period_startdate, period_enddate))

    dt_month_range = rrule.rrule(rrule.MONTHLY, dtstart=startdate, until=enddate)
    for dt in dt_month_range:
        name = "{m}/{y}".format(m=dt.strftime("%b"), y=dt.strftime("%Y"))
        period_startdate, period_enddate = getBeginningAndEndOfMonth(dt)
        lst.append(ReviewInterval(name, period_startdate, period_enddate))
    return lst


class UserAnalysis(object):
    def __init__(self, users, review_items, reviews):
        self.users = users
        self.review_items = review_items
        self.reviews = reviews
        self.startDate = None
        self.endDate = None
        self.userEvaluations = dict()
        self.review_intervals = None
        for user in users:
            self.userEvaluations[user.name] = UserEvaluation(user)
        if len(review_items):
            for review_item in review_items:
                if self.startDate is None or review_item.creation_date < self.startDate:
                    self.startDate = review_item.creation_date
                if self.endDate is None or review_item.creation_date > self.endDate:
                    self.endDate = review_item.creation_date
        if len(reviews):
            for review in reviews:
                if self.startDate is None or review.review_date < self.startDate:
                    self.startDate = review.review_date
                if self.endDate is None or review.review_date > self.endDate:
                    self.endDate = review.review_date
        if self.startDate is not None and self.endDate is not None:
            for user in users:
                self.userEvaluations[user.name].review_intervals = getReviewIntervals(self.startDate, self.endDate)
            for review_item in review_items:
                for review_interval in self.userEvaluations[review_item.creator.name].review_intervals:
                    review_interval.evaluate_review_item(review_item.creation_date)
            for review in reviews:
                for review_interval in self.userEvaluations[review.reviewer.name].review_intervals:
                    review_interval.evaluate_review(review.review_date)

    def getReviewInterval(self, user, interval_name):
        ret = None
        if user and user.name in self.userEvaluations.keys():
            for review_interval in self.userEvaluations[user.name].review_intervals:
                if review_interval.name == interval_name:
                    ret = review_interval
                    break
        return ret

    def getReviewIntervalNames(self):
        ret = list()
        if self.startDate is not None and self.endDate is not None:
            lst = getReviewIntervals(self.startDate, self.endDate)
            for item in lst:
                ret.append(item.name)
        return ret


def getUserAnalysis():
    """
        gets user evaluations form db
    :return: user evaluations
    """
    #db = database.get_db()
    users = database.User.query.all()
    review_items = database.ReviewItem.query.all()
    reviews = database.Review.query.all()
    userAnalysys = UserAnalysis(users, review_items, reviews)
    return userAnalysys


class Results(object):
    def __init__(self, review_items, reviews):
        self.review_items = review_items
        self.reviews = reviews

    def getReviewItemCount(self):
        return len(self.review_items)

    def getReviewCount(self):
        return len(self.reviews)

    def getReviewItemsWithoutReviewCount(self):
        ret = 0
        for review_item in self.review_items:
            if len(review_item.reviews) == 0:
                ret += 1
        return ret

    def getScore(self):
        n = self.getReviewCount() + self.getReviewItemsWithoutReviewCount()
        if (n) > 0:
            ret = (float(self.getReviewCount()) / float(n)) * 100.0
        else:
            ret = 0
        return ret

    def getCoverageScore(self):
        if self.getReviewItemCount() > 0:
            f_without = float(self.getReviewItemsWithoutReviewCount())
            f_count = float(self.getReviewItemCount())
            ret = ((f_count- f_without) / f_count) * 100.0
        else:
            ret = 0
        return ret

    def getAverageReviewCountScore(self):
        average_review_score = 0.0
        if self.getReviewItemCount() > 0:
            for review_item in self.review_items:
                average_review_score += review_item.getReviewCount()
            average_review_score /= float(self.getReviewItemCount())
        return average_review_score

    def getScoreString(self):
        score = self.getScore()
        return "Coverage {s:3.1f}% ({rin}/{ri}); number of reviews: {r}, review rate: {arc:3.3f}" \
               "".format(s=self.getCoverageScore(),
                         ri=self.getReviewItemCount(),
                         rin=self.getReviewItemsWithoutReviewCount(),
                         r=self.getReviewCount(),
                         arc=self.getAverageReviewCountScore())


def getResults():
    #db = database.get_db()
    review_items = database.ReviewItem.query.all()
    reviews = database.Review.query.all()
    results = Results(review_items, reviews)

    # results.review_item_count = len(review_items)
    # results.review_count = len(Review.query.all())
    # if len(review_items) >0:
    #    average_review_score = 0
    #    for review_item in review_items:
    #        average_review_score += len(review_item.reviews)
    #        if len(review_item.reviews) == 0:
    #            results.review_item_without_review_count += 1
    #    average_review_score /= len(review_items)
    return results


# ===============================================================================
# routes
# ===============================================================================
@blueprint.route('/', methods=['GET', 'POST'])
def show_analysis():
    userAnalysis = getUserAnalysis()
    return render_template('analysis.html',userAnalysis=userAnalysis, results= getResults())

