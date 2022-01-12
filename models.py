# pyright: reportGeneralTypeIssues=false

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Instantiate flask app
app = Flask(__name__)

# Add external app's configuration
app.config.from_object('config')

# Instantiate DB abstraction/integration
db = SQLAlchemy(app)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    contact_id = db.Column(db.Integer, db.ForeignKey('Contact.id'))


class Contact(db.Model):
    __tablename__ = 'Contact'

    id = db.Column(db.Integer, primary_key = True)
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    state = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    image_link = db.Column(db.String(120))


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key = True)
    start = db.Column(db.DateTime)
    artist_id = db.Column(db.Integer,
                          db.ForeignKey('Artist.id'),
                          nullable=False)
    venue_id = db.Column(db.Integer,
                         db.ForeignKey('Venue.id'),
                         nullable=False)


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    contact_id = db.Column(db.Integer, db.ForeignKey('Contact.id'))


db.create_all()
