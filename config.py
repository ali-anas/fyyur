import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# TODO-DONE: IMPLEMENT DATABASE URL
# connected to my local database server user - postgres, pass - test123
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:test123@localhost:5432/fyyur'
