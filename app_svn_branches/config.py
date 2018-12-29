import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = r'sqlite:///E:\Development\temp\FlaskWebServer\svn_branches2.db'