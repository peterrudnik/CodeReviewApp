from flask_wtf import FlaskForm
from wtforms import Field, StringField, PasswordField, BooleanField, SubmitField, DateTimeField, SelectField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from wtforms.fields.html5 import DateTimeLocalField, DateTimeField, DateField
from wtforms import widgets


from datetime import datetime
DATETIME_FMT_FORM = '%Y-%m-%d %H:%M'



#--------------------------------------------------------------------------------------------------
# validators
#--------------------------------------------------------------------------------------------------
'''
class MyDateTimeField(Field):
    """
    This field is the base for most of the more complicated fields, and
    represents an ``<input type="text">``.
    """
    widget = widgets.TextInput()

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = datetime.strptime(valuelist[0], DATE_FMT)
        elif self.data is None:
            self.data = ''

    def _value(self):
        return self.data
'''


#--------------------------------------------------------------------------------------------------
# validators
#--------------------------------------------------------------------------------------------------

class DatetimeFormatValidator(object):
    def __init__(self, format=DATETIME_FMT_FORM, message=None):
        self.format = format
        if not message:
            message = u'Format is: {f}'.format(f=format)
        self.message = message

    def __call__(self, form, field):
        if field.data and len(field.data.strip()) > 0: # empty field should be checked by DataRequired validator
            try:
                self.data = datetime.strptime(field.data, DATETIME_FMT_FORM)
            except Exception as e:
                raise ValidationError(self.message)

datetimeFormatValidator = DatetimeFormatValidator

#--------------------------------------------------------------------------------------------------
# forms
#--------------------------------------------------------------------------------------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class FormNewReviewItem(FlaskForm):
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S',validators=[InputRequired()])
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    #created = DateTimeLocalField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired(), DatetimeFormatValidator(format='%Y-%m-%d %H:%M:%S')])
    created = StringField('created', validators=[DataRequired(),DatetimeFormatValidator(format=DATETIME_FMT_FORM)])
    review_item = StringField('review item', validators=[InputRequired()])
    creator = SelectField('creator', coerce=int,validators=[DataRequired()])
    review_type = SelectField('review type', coerce=int,validators=[InputRequired()])
    reviewed_aspect = StringField('reviewed aspect')
    submit = SubmitField('submit')

class FormEditReviewItem(FlaskForm):
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S',validators=[InputRequired()])
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    #created = DateTimeLocalField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired(), DatetimeFormatValidator(format='%Y-%m-%d %H:%M:%S')])
    created = StringField('created', validators=[DataRequired(),DatetimeFormatValidator(format=DATETIME_FMT_FORM)])
    #review_item = StringField('review item', validators=[InputRequired()])
    creator = SelectField('creator', coerce=int,validators=[DataRequired()])
    review_type = SelectField('review type', coerce=int,validators=[InputRequired()])
    reviewed_aspect = StringField('reviewed aspect')
    submit = SubmitField('submit')

class FormNewReview(FlaskForm):
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S',validators=[InputRequired()])
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    #created = DateTimeLocalField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired(), DatetimeFormatValidator(format='%Y-%m-%d %H:%M:%S')])
    #review_item = SelectField('review type', coerce=int,validators=[InputRequired()])
    reviewed= StringField('reviewed', validators=[DataRequired(), DatetimeFormatValidator(format=DATETIME_FMT_FORM)])
    reviewer = SelectField('reviewer', coerce=int)
    approved = BooleanField('approved')
    note = StringField('note')
    submit = SubmitField('submit')

class FormEditReview(FlaskForm):
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S',validators=[InputRequired()])
    #created = DateTimeField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    #created = DateTimeLocalField('created', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired(), DatetimeFormatValidator(format='%Y-%m-%d %H:%M:%S')])
    #review_item = SelectField('review type', coerce=int,validators=[InputRequired()])
    #reviewed= StringField('reviewed', validators=[DataRequired(), DatetimeFormatValidator(format=DATETIME_FMT_FORM)])
    reviewer = SelectField('reviewer', coerce=int)
    approved = BooleanField('approved')
    note = StringField('note')
    submit = SubmitField('submit')