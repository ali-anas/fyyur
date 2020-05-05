#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import SQLALCHEMY_DATABASE_URI #importing local db URI from config
from sqlalchemy import func
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config['SECRET_KEY'] = 'any secret string' # see : https://stackoverflow.com/questions/47687307/how-do-you-solve-the-error-keyerror-a-secret-key-is-required-to-use-csrf-whe
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO-DONE: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'   #changed table name from 'Venue' => 'venue' for easy to use in database conn.
    # given default values at last to let some forms works -> post-venue, post-artists
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500), default="")
    facebook_link = db.Column(db.String(120))
    # TODO-DONE: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String(120), default="")
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), default="") # assumed len of description mot more than 500
    shows = db.relationship('Show', backref="venue", lazy=True)

    def __repr__(self):
      return '<Venue {}>'.format(self.name)

class Artist(db.Model):
    __tablename__ = 'artist'  # #changed table name from 'Artist' => 'artist' for easy to use in database conn.

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String())) #changed genres to array of strings
    image_link = db.Column(db.String(500), default="")
    facebook_link = db.Column(db.String(120))
    # TODO-DONE: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120), default="")
    seeking_venue =  db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), default="")
    shows = db.relationship('Show', backref="artist", lazy=True)

    def __repr__(self):
      return '<Artist {}>'.format(self.name)

# TODO-DONE: Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
          return '<Show {}{}>'.format(self.artist_id, self.venue_id)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO-DONE: replace with real venues data.
        # num_shows should be aggregated based on number of upcoming shows per venue.

  # query all areas
  areas = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  
  # data[] contains data of area as dictionary
  data = []
  # print(areas)


  for curr_area in areas:
    # get venues in curr_area
    all_venues = Venue.query.filter_by(state=curr_area.state).filter_by(city=curr_area.city).all()
    # venue_details[] - there can be multiple venues in curr_area
    # stores each venue in dictionary
    all_venues_details = []
    for curr_venue in all_venues:
      all_venues_details.append({
        "id": curr_venue.id,
        "name": curr_venue.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id==curr_venue.id).filter(Show.start_time>datetime.now()).all())
        })

    data.append({
        "city": curr_area.city,
        "state": curr_area.state,
        "venues": all_venues_details
        })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO-DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term=request.form.get('search_term', '')
  # @see : https://stackoverflow.com/questions/20363836/postgresql-ilike-query-with-sqlalchemy
  all_matching_results = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  matching_result_data = []

  
  for result in all_matching_results:
    matching_result_data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all())
      })

  # make response dictionary from all_matching results
  response = {
    "count": len(all_matching_results),
    "data": matching_result_data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO-DONE: replace with real venue data from the venues table, using venue_id
  
  # get venue with <venue_id> from database 
  venue = Venue.query.get(venue_id)

  # if we did not get any venue corresponding to <venue_id>
  if not venue:
    return render_template('errors/404.html')

  # if we got venue
  # then populate details of upcoming_shows[] and past_shows[]
  # query -> get all upcoming/past shows with corresponding artists details
  query_on_upcoming = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()
  query_on_past = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()

  upcoming_shows_with_artists_details = []
  past_shows_with_artists_details = []


  for curr_show in query_on_upcoming:
    upcoming_shows_with_artists_details.append({
      "artist_id": curr_show.artist_id,
      "artist_name": curr_show.artist.name,
      "artist_image_link": curr_show.artist.image_link,
      "start_time": curr_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  for curr_show in query_on_past:
    past_shows_with_artists_details.append({
      "artist_id": curr_show.artist_id,
      "artist_name": curr_show.artist.name,
      "artist_image_link": curr_show.artist.image_link,
      "start_time": curr_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  # populate data[] to be sent to view
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows_with_artists_details,
    "upcoming_shows": upcoming_shows_with_artists_details,
    "past_shows_count": len(past_shows_with_artists_details),
    "upcoming_shows_count": len(upcoming_shows_with_artists_details)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO-DONE: insert form data as a new Venue record in the db, instead
  # TODO-DONE: modify data to be the data object returned from db insertion
  error = False
  try:
    # get details
    venue = Venue(
      name = request.form['name']
      ,city = request.form['city']
      ,state = request.form['state']
      ,address = request.form['address']
      ,phone = request.form['phone']
      ,genres = request.form.getlist('genres')
      ,facebook_link = request.form['facebook_link']
      # uncomment following lines if there is corresponding input space avilable in the form
      # ,image_link = request.form['image_link']
      # ,website = request.form['website']
      # ,seeking_talent = True if 'seeking_talent' in request.form else False
      # ,seeking_description = request.form['seeking_description']
    )

    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    # TODO-DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO-DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash(f'An error occurred. Venue {venue_id} could not be deleted.')
  else:
    flash(f'Venue {venue_id} was successfully deleted.')


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  # return None <- originally
  # replaced code to render home page
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO-DONE: replace with real data returned from querying the database

  data = db.session.query(Artist).all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO-DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  search_term=request.form.get('search_term', '')
  all_matching_results = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  matching_result_data = []

  
  for result in all_matching_results:
    matching_result_data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == result.id).filter(Show.start_time > datetime.now()).all())
      })

  # make response dictionary from all_matching results
  response = {
    "count": len(all_matching_results),
    "data": matching_result_data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO-DONE: replace with real venue data from the venues table, using venue_id
  
  query_on_artist = db.session.query(Artist).get(artist_id)

  # if query on artist fails
  if not query_on_artist:
    return render_template('error/404.html')

  # if we got artist
  # then populate details of upcoming_shows[] and past_shows[]
  # query -> get all upcoming/past shows with corresponding their venue details
  query_on_upcoming = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
  query_on_past = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

  upcoming_shows = []
  past_shows = []


  for curr_show in query_on_upcoming:
    upcoming_shows.append({
      "venue_id": curr_show.venue_id,
      "venue_name": curr_show.venue.name,
      "venue_image_link": curr_show.venue.image_link,
      "start_time": curr_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  for curr_show in query_on_past:
    past_shows.append({
      "venue_id": curr_show.venue_id,
      "venue_name": curr_show.venue.name,
      "venue_image_link": curr_show.venue.image_link,
      "start_time": curr_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  # populate data[] to be sent to view
  data = {
    "id": query_on_artist.id,
    "name": query_on_artist.name,
    "genres": query_on_artist.genres,
    "city": query_on_artist.city,
    "state": query_on_artist.state,
    "phone": query_on_artist.phone,
    "website": query_on_artist.website,
    "facebook_link": query_on_artist.facebook_link,
    "seeking_venue": query_on_artist.seeking_venue,
    "seeking_description": query_on_artist.seeking_description,
    "image_link": query_on_artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  
  # TODO-DONE: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get(artist_id)

  # populate form values with existing data
  # id should remain same
  if artist:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    # uncomment following lines if there is corresponding input space avilable in the form
    # form.image_link.data = artist.image_link
    # form.website.data = artist.website
    # form.seeking_venue.data = artist.seeking_venue
    # form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO-DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  error = False
  artist = Artist.query.get(artist_id)

  try:
    # update with new values
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    # uncomment following lines if there is corresponding input space avilable in the form
    # artist.image_link = request.form['image_link']
    # artist.website = request.form['website']
    # artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    # artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred while updating details.')
  else:
    flash('Artist updated successfully!.')
  
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  
  # TODO-DONE: populate form with values from venue with ID <venue_id>

  venue = Venue.query.get(venue_id)

  # populate form details with existing ones
  if venue:
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    # uncomment these lines if there are corresponding inputs options in form venue/<venue-id>/edit
    # form.image_link.data = venue.image_link
    # form.website.data = venue.website
    # form.seeking_talent.data = venue.seeking_talent
    # form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO-DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  venue = Venue.query.get(venue_id)

  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    # uncomment these lines if there are corresponding inputs options in form venue/<venue-id>/edit
    # venue.image_link = request.form['image_link']
    # venue.website = request.form['website']
    # venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    # venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash(f'An error occurred while updating Venue.')
  else:
    flash(f'Venue updated successfully!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO-DONE: insert form data as a new Venue record in the db, instead
  # TODO-DONE: modify data to be the data object returned from db insertion
  error = False
  try:
    artist = Artist(
    name = request.form['name']
    ,city = request.form['city']
    ,state = request.form['state']
    ,phone = request.form['phone']
    ,genres = request.form.getlist('genres')
    ,facebook_link = request.form['facebook_link']
    # uncomment following lines if there is corresponding input in the form
    # ,image_link = request.form['image_link']
    # ,website = request.form['website']
    # ,seeking_venue = True if 'seeking_venue' in request.form else False
    # ,seeking_description = request.form['seeking_description']
    )
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # TODO-DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    
  # on successful db insert, flash success
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO-DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  

  # all shows with corresponding artist and venues details
  query_on_shows = db.session.query(Show).join(Artist).join(Venue).all()

  data = []
  for curr_show in query_on_shows:
    data.append({
      "venue_id": curr_show.venue_id,
      "venue_name": curr_show.venue.name,
      "artist_id": curr_show.artist_id,
      "artist_name": curr_show.artist.name,
      "artist_image_link": curr_show.artist.image_link,
      "start_time": curr_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO-DONE: insert form data as a new Show record in the db, instead

  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    # new show object
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # TODO-Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing
    flash('An error occurred. Show could not be listed.')
  # on successful db insert, flash success
  else:
    flash('Show was successfully listed!')

  return render_template('pages/home.html')

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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
