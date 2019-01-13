import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    #SQLALCHEMY_DATABASE_URI = r'sqlite:///E:\Development\temp\FlaskWebServer\code_reviews.db'
    credentials = os.environ['MYSQL_CODEREVIEW'] # in the form username:passw
    SQLALCHEMY_DATABASE_URI = r'mysql+pymysql://{c}@localhost/codereview'.format(c=credentials)


