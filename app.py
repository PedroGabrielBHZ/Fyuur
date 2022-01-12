# pyright: reportGeneralTypeIssues=false
#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from datetime import datetime as dt
from flask import Flask
from flask import render_template
from flask import request
# from flask import Response
from flask import flash
from flask import redirect
from flask import url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from logging import Formatter, FileHandler
# from flask_wtf import Form
# from flask_wtf.csrf import CSRFProtect
from forms import *
from models import Artist
from models import Contact
from models import Venue
from models import Show
from forms import ArtistForm
from forms import VenueForm
from forms import ShowForm 

# import json
import dateutil.parser
import babel
import logging
import sys

#----------------------------------------------------------------------------#
# Typing
#----------------------------------------------------------------------------#
from typing import Dict
from typing import List
from typing import Union


#----------------------------------------------------------------------------#
# App Config
#----------------------------------------------------------------------------#
app = Flask(__name__)

# TODO: Investigate this.
moment = Moment(app)

app.config.from_object('config')

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: Use this. Not now, though.
# csrf = CSRFProtect(app)


#----------------------------------------------------------------------------#
# Filters
#----------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers
#----------------------------------------------------------------------------#
@app.route('/')
def index():
  return render_template('pages/home.html')


#----------------------------------------------------------------------------#
#  Venues
#----------------------------------------------------------------------------#
@app.route('/venues')
def venues():

    # Instantiate empty resulting data
    data = []

    # Instantiate venues data
    venuesPerCity: Dict[str, List] = {}

    # Iterate through all venues grouping them by city
    for venue in Venue.query.all():

        # Get venue's upcoming shows
        relatedShows = Show.query.filter_by(venue_id=venue.id)

        # Count upcoming shows based on current date-time
        upcoming_shows_count = relatedShows.filter(Show.start > dt.now()).count()

        # Instantiate venue data to be displayed
        venueData = {
                'id': venue.id,
                'name': venue.name,
                'upcoming_shows_count': upcoming_shows_count,
        }

        # Fetch venue's contact information
        contact = Contact.query.get(venue.contact_id)

        # Construct grouping key based on venue's tuple of state and city
        city = str(contact.state) + '$' + str(contact.city)

        # City is not yet a key: instantiate a list with current venue
        if city not in venuesPerCity:
            venuesPerCity[city] = [venueData]

        # City points to existing data: append current venue data
        else:
            venuesPerCity[city].append(venueData)

    # Iterate through venues per city data
    for cityState, venues in venuesPerCity.items():

        # ...
        data.append({
            'city': cityState.split('$')[0],
            'state': cityState.split('$')[1],
            'venues': venues,
        })

    # Render data to the user
    return render_template('pages/venues.html', areas=data, form=VenueForm());


@app.route('/venues/search', methods=['POST'])
def search_venues():
    
    # Fetch search string from page's form
    search: str = request.form.get('search_term')

    # Fetch venues through wildcarding
    venues = Venue.query.filter(Venue.name.ilike(f'%{search}%')).all()

    # Instantiate response data
    data: List[Dict[str, Union[str, int]]] = []

    for venue in venues:

        # Get venue's upcoming shows
        relatedShows = Show.query.filter_by(venue_id=venue.id)

        # Count upcoming shows based on current date-time
        upcoming_shows_count = relatedShows.filter(Show.start > dt.now()).count()

        # Instantiate venue data to be displayed
        data.append({
                'id': venue.id,
                'name': venue.name,
                'upcoming_shows_count': upcoming_shows_count,
        })

    # Instantiate response
    response = {
            'count': len(data),
            'data': data,
    }

    return render_template('pages/search_venues.html',
                           results = response,
                           search_term = request.form.get('search_term', ''),
                           form = VenueForm())


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    
    # Fetch venue by id
    venue = Venue.query.get(venue_id)

    # Fetch shows by fetched venue
    shows = Show.query.filter_by(venue_id = venue.id).all()

    # Instantiate list of upcoming and past shows
    pastShows: List[Dict[str, str]] = []
    upcomingShows: List[Dict[str, str]] = []

    for show in shows:

        artist = Artist.query.get(show.artist_id)

        showData = {
            'artist_id': show.artist_id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': str(show.start),
        }

        if show.start < dt.now():
            pastShows.append(showData)

        else:
            upcomingShows.append(showData)

    venueContactInfo = Contact.query.get(venue.contact_id)
    
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venueContactInfo.address,
        "city": venueContactInfo.city,
        "state": venueContactInfo.state,
        "phone": venueContactInfo.phone,
        "website": venueContactInfo.website_link,
        "facebook_link": venueContactInfo.facebook_link,
        "image_link": venueContactInfo.image_link,
        "past_shows": pastShows,
        "upcoming_shows": upcomingShows,
        "past_shows_count": len(pastShows),
        "upcoming_shows_count": len(upcomingShows),

        # Hard-coded while I'm stuck
        "seeking_talent": True,
        "seeking_description": "Hardcoded description which means nothing."
    }

    return render_template('pages/show_venue.html', venue=data, form=VenueForm)


#----------------------------------------------------------------------------#
#  Create Venue
#----------------------------------------------------------------------------#
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  return render_template('forms/new_venue.html', form=VenueForm())


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    error = False
    form = VenueForm(request.form)

   # FIXME: Investigate this.
   # if not form.validate():
   #      flash('Something bad happened!')
   #      return render_template('forms/new_venue.html', form = form)

    try:

        # Fetch form data.
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        website = request.form['website_link']
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']

        # Instantiate a contact
        contact = Contact(city = city,
                          state = state,
                          address = address,
                          phone = phone,
                          image_link = image_link,
                          facebook_link = facebook_link,
                          website_link = website)

        db.session.add(contact)
        db.session.commit()

        contact_id = contact.id

        venue_created = Venue(name = name,
                              genres = genres,
                              contact_id = contact_id)

        db.session.add(venue_created)
        db.session.commit()

    except:

        db.session.rollback()

        print(sys.exc_info())

        error = True

    finally:
        db.session.close()

    # FIXME: Remove this quickfix
    name = 'shabbles'

    if not error:
        print('ValidationError')
        flash('Venue ' + name + ' was successfully listed!')

    else:
        flash('An error occurred. Venue ' + name + ' could not be listed.')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()

    except:
        db.session.rollback()

    finally:
        db.session.close()


    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page,
    # have it so that clicking that button delete it from the db then 
    # redirect the user to the homepage.

    # -> Not now, thanks.
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

    data = [{ 'id': a.id, 'name': a.name} for a in Artist.query.all()]

    return render_template('pages/artists.html',
                           artists = data,
                           form = ArtistForm())

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # ... 
    search = request.form.get('search_term')

    # ... 
    artists = Artist.query.filter(Artist.name.ilike(f'%{search}')).all()

    # ... 
    data = []

    # ... 
    for a in artists:
        relatedShows = Show.query.filter_by(artist_id = a.id)
        upcoming_shows_count = relatedShows.filter(Show.start > dt.now()).count()
        artistData = {
                'id': a.id,
                'name': a.name,
                'num_upcoming_shows': upcoming_shows_count,
        }
        data.append(artistData)

    response = {
            'count': len(data),
            'data': data,
    }

    return render_template('pages/search_artists.html',
                           results = response,
                           search_term = request.form.get('search_term', ''),
                           form = ArtistForm())

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    # ...
    data = []

    # ...
    artist = Artist.query.get(artist_id)

    # ...
    artistContact = Contact.query.get(artist.contact_id)

    # ...
    shows = Show.query.filter_by(artist_id = artist.id).all()

    # ...
    pastShows = []
    upcomingShows = []

    # ...
    for s in shows:

        # ...
        venue = Venue.query.get(s.venue_id)
        venueContact = Contact.query.get(venue.contact_id)

        # ...
        show = {
            'venue_id': s.venue_id,
            'venue_name': venue.name,
            'venue_image_link': venueContact.image_link,
            'start_time': str(s.start),
        }

        if s.start < dt.now():
            pastShows.append(show)

        else:
            upcomingShows.append(show)

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artistContact.city,
        'state': artistContact.state,
        'phone': artistContact.phone,
        'website': artistContact.website_link,
        'facebook_link': artistContact.facebook_link,
        'image_link': artistContact.image_link,
        'past_shows': pastShows,
        'upcoming_shows': upcomingShows,
        'past_shows_count': len(pastShows),
        'upcoming_shows_count': len(upcomingShows),
    }

    return render_template('pages/show_artist.html',
                           artist = data,
                           form = ArtistForm())

#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    # ...
    # artist = {}

    # ...
    form = ArtistForm()

    # ...
    artist = Artist.query.get(artist_id)

    # ...
    artistContact = Contact.query.get(artist.contact_id)

    # ...
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artistContact.city
    form.state.data = artistContact.state
    form.facebook_link.data = artistContact.facebook_link
    form.image_link.data = artistContact.image_link
    form.website_link.data = artistContact.website_link
    form.phone.data = artistContact.phone
    
    # ...
    returnArtist = {
            'id': artist.id,
            'name': artist.name,
    }

    return render_template('forms/edit_artist.html',
                           form = form,
                           artist = returnArtist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    # ...
    error = False

    # ...
    form = ArtistForm(request.form)

    # ...
    if not form.validate():
        flash('Bad input.')
        return render_template('forms/edit_artist.html', form = form)

    # ...
    try:
        # ...
        artist = Artist.query.get(artist_id)

        # ...
        artistContact = Contact.query.get(artist.contact_id)

        # ...
        artist.name = request.form['name']
        artist.genres = request.form.getlist['genres']
        artistContact.city = request.form['city']
        artistContact.state = request.form['state']
        artistContact.phone = request.form['phone']
        artistContact.image_link = request.form['image_link']
        artistContact.website_link = request.form['website']
        artistContact.facebook_link = request.form['facebook_link']

        # ...
        db.session.commit()

    # ...
    except:
        db.session.rollback()
        print(sys.exc_info())
        error = True

    # ...
    finally:
        db.session.close()

    # ...
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully edited.')

    else:
        flash('Artist ' + request.form['name'] + ' could not be edited.')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    # ...
    form = VenueForm()

    # ...
    venue = Venue.query.get(venue_id)

    # ...
    venueContact = Contact.query.get(venue.contact_id)

    # ...
    form.name.data = venue.name
    form.genres.data = venue.genres

    # ...
    form.city.data = venueContact.city
    form.state.data = venueContact.state
    form.phone.data = venueContact.phone
    form.address.data = venueContact.address
    form.website_link.data = venueContact.website_link
    form.image_link.data = venueContact.image_link
    form.facebook_link.data = venueContact.facebook_link

    # ...
    venue = {
        'id': venue.id,
        'name': venue.name,
    }

    # ...
    return render_template('forms/edit_venue.html', form = form, venue = venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    # ...
    error = None

    # ...
    form = VenueForm(request.form)

    # ...
    if form.validate() is False:
        flash('Bad input.')

        # ...
        return render_template('forms/edit_venue.html', form = form)

    # ...
    try:
        # ...
        venue = Venue.query.get(venue_id)
        venueContact = Contact.query.get(selectedVenue.contact_id)

        # ...
        venueContact.city = request.form['city']
        venueContact.state = request.form['state']
        venueContact.phone = request.form['phone']
        venueContact.address = request.form['address']
        venueContact.website_link = request.form['website']
        venueContact.image_link = request.form['image_link']
        venueContact.facebook_link = request.form['facebook_link']

        # ...
        venue.name = request.form['name']
        venue.genres = request.form.getlist('genres')

        # ...
        db.session.commit()

    # ...
    except:
        db.session.rollback()
        print(sys.exc_info())
        error = True

    # ...
    finally:
        db.session.close()

    # ...
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully edited.')

    # ...
    else:
        flash('Venue ' + request.form['name'] + ' could not be edited.')

    # ...
    return redirect(url_for('show_venue', venue_id = venue_id))


#----------------------------------------------------------------------------#
#  Create Artist
#----------------------------------------------------------------------------#
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    # ...
    error = None

    # ...
    form = ArtistForm(request.form)

    # FIXME: Investigate this.
    #  if not form.validate():
    #      flash('Something bad happened.')
    #      return render_template('forms/new_artist.html', form = form)

    # ...
    try:

        # Fetch form data.
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        image_link = request.form['image_link']
        website_link = request.form['website_link']
        facebook_link = request.form['facebook_link']

        # ...
        contact = Contact(city = city,
                          state = state,
                          phone = phone,
                          facebook_link = facebook_link,
                          image_link = image_link,
                          website_link = website_link)

        # ...
        db.session.add(contact)
        db.session.commit()

        # ...
        contact_id = contact.id

        # ...
        artist_created = Artist(name = name,
                                genres = genres,
                                contact_id = contact_id)

        # ...
        db.session.add(artist_created)

        # ...
        db.session.commit()

    # ...
    except:
        db.session.rollback()
        print(sys.exc_info())
        error = True

    # ...
    finally:
        db.session.close()

    # ...
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

    # ...
    else:
      flash('An error occurred. Artist ' + name + ' could not be listed.')

    # ...
    return render_template('pages/home.html', form = form)


#----------------------------------------------------------------------------#
#  Shows
#----------------------------------------------------------------------------#
@app.route('/shows')
def shows():

    # ...
    data = []

    # ...
    shows = Show.query.all()

    # ...
    for s in shows:

        # ...
        venue = Venue.query.filter_by(id = s.venue_id).first()

        # ...
        artist = Artist.query.filter_by(id = s.artist_id).first()

        # ...
        artistContact = Contact.query.filter_by(id = artist.contact_id)

        # ...
        show_data = {
          'venue_id': s.venue_id,
          'venue_name': venue.name,
          'artist_id': s.artist_id,
          'artist_name': artist.name,
          'artist_image_link': artistContact.image_link,
          'start_time': str(s.start)
        }

        data.append(show_data)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():

    form = ShowForm()

    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # ...
    error = False

    # ...
    form = ShowForm()

    # ...
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']
        show_created = Show(artist_id = artist_id,
                            venue_id = venue_id,
                            start_time = start_time)

        # ...
        db.session.add(show_created)

        # ...
        db.session.commit()

    # ...
    except:
        db.session.rollback()
        print(sys.exc_info())
        error = True

    # ...
    finally:
        db.session.close()

    # ...
    if not error:
        flash('Show was successfully listed!') 

    # ...
    else:
        flash('An error occurred. Show could not be listed.')

    # ...
    return render_template('pages/home.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
