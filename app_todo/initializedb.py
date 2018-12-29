"""Script for initializing your database.

Note that dropping your existing tables is an opt-in operation.
If you want to drop tables before you create tables, set an environment
variable called "DEVELOPMENT" to be "True".
"""
from app_todo.app import db
#from app import db

#if bool(os.environ.get('DEVELOPMENT', '')):
#    db.drop_all()

def create_db():
    #db.drop_all()
    db.create_all()


#===============================================================================
# controlling functions
#===============================================================================
if __name__ == "__main__":
    create_db()
