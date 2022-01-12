import os
SECRET_KEY = os.urandom(32)

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database.
db_url = 'postgresql://postgres@localhost:5432/fyuur'
SQLALCHEMY_DATABASE_URI = db_url

# Disable annoying deprecation warnings.
SQLALCHEMY_TRACK_MODIFICATIONS = False

