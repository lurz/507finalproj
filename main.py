from models import Track, Artist, Recommendation
import sqlite3
from flask import g
import flask
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import json
import secrets as secrets

# constants
app = flask.Flask(__name__)
app.secret_key = secrets.SECRET_KEY
client_id = secrets.CLIENT_ID
client_secret = secrets.CLIENT_SECRET
DATABASE = './sql/spotify.sqlite3'
spotify_token_url = 'https://accounts.spotify.com/api/token'
spotify_search_url = 'https://api.spotify.com/v1/search'
spotify_artist_url = 'https://api.spotify.com/v1/artists/'
spotify_recom_url = 'https://api.spotify.com/v1/recommendations'
spotify_track_url = 'https://api.spotify.com/v1/tracks/'
lyrics_search_url = 'https://api.lyrics.ovh/v1/'


# DB related functions
def make_dicts(cursor, row):
    '''Helper function for get_db
    Return dictionary of cached data instead of raw list

    Parameters
    ----------
    Internal variables

    Returns
    -------
    dict :
        dictionary of cached data
    '''
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    '''open database file

    Parameters
    ----------
    None

    Returns
    -------
    db : reference
    '''
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db


def init_db():
    '''Initialize database when starting the server
    Read the schema.sql file and execute the DROP and
    CREATE schemas.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    with app.app_context():
        db = get_db()
        with app.open_resource('./sql/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    '''close the connection to database when the server stops

    Parameters
    ----------
    exception: internal variable

    Returns
    -------
    None
    '''
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def show_index():
    '''Show the index page of the flask app.
    Get the OAuth2 session token with the client id and secret.

    Parameters
    ----------
    None

    Returns
    -------
    flask template with index.html
    '''
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    flask.session['token'] = oauth.fetch_token(token_url=spotify_token_url, client_id=client_id,
                                               client_secret=client_secret)

    return flask.render_template("index.html")


def get_artist(id, headers):
    '''Fetch artist data from Spotify API.

    Parameters
    ----------
    id : string
        Artist ID string (22 bytes)
    headers : dict
        http header with authentication token

    Returns
    -------
    Artist : obj
        the artist object with data loaded
    '''
    response = requests.get(spotify_artist_url + id, headers=headers)
    if not response.ok:
        return None
    data = json.loads(response.text)
    if 'error' in data:
        return None
    return Artist(data=data)


def get_track_img(id, headers):
    '''Fetch track image url from Spotify API.

    Parameters
    ----------
    id : string
        Track ID string (22 bytes)
    headers : dict
        http header with authentication token

    Returns
    -------
    string :
        the track image url
    '''
    response = requests.get(spotify_track_url + id, headers=headers)
    if not response.ok:
        return ""
    data = json.loads(response.text)
    if ('error' in data) or ('album' not in data) or len(
            data['album']['images']) < 3:
        return ""
    return data['album']['images'][2]['url']


def get_recommendations(artist_id, track_id, genres, headers):
    '''Fetch recommendation tracks data from Spotify API.

    Parameters
    ----------
    artist_id : string
        Artist ID string (22 bytes)
    track_id : string
        Track ID string (22 bytes)
    genres : list
        list of genres strings of the seed track
    headers : dict
        http header with authentication token

    Returns
    -------
    list :
        A list of the recommendation object with data loaded
    '''
    result = []
    params = {
        'seed_artists': artist_id,
        'seed_genres': genres,
        'seed_tracks': track_id,
        'limit': 5}
    response = requests.get(spotify_recom_url, params=params, headers=headers)
    if not response.ok:
        return result
    data = json.loads(response.text)
    if 'error' in data:
        return result
    for track in data['tracks']:
        current_recom = Recommendation(
            track, get_track_img(
                track['id'], headers))
        result.append(current_recom)
    return result


def search_cache(s_artist, s_track):
    '''Search the requested artist and track data
    in the database. Match the best fit in the database.
    If not in the cache, return None

    Parameters
    ----------
    s_artist : string
        Requested artist name
    s_track : string
        Requested track name

    Returns
    -------
    (track, artist, recommendation) : tuple
        Return a tuple of cached data, including the track object,
        a list of artist objects and a list of recommendation objects.
    '''
    db = get_db()
    cur = db.cursor()
    sql = "SELECT T.id FROM track T, artist A, bond B WHERE B.artistid=A.id AND B.trackid=T.id AND T.trackname LIKE ? AND A.artistname LIKE ?"
    cur.execute(sql, (s_track + '%', s_artist + '%', ))
    data = cur.fetchall()
    if len(data) == 0:
        return (None, None, None)
    track_id = data[0]['id']
    sql = "SELECT * FROM track WHERE id=?"
    cur.execute(sql, (track_id, ))
    current_track = Track(db=cur.fetchall()[0])

    sql = "SELECT A.id, A.artistname, A.popularity, A.imgsrc, A.genres FROM bond B, artist A WHERE B.trackid=? AND B.artistid=A.id"
    cur.execute(sql, (track_id, ))
    raw_artists = cur.fetchall()
    artists = []
    for r in raw_artists:
        artists.append(Artist(db=r))

    sql = "SELECT * FROM recommendation WHERE trackid=?"
    cur.execute(sql, (track_id, ))
    raw_recomms = cur.fetchall()
    recommendations = []
    for r in raw_recomms:
        recommendations.append(Recommendation(db=r))

    return (current_track, artists, recommendations)


def store_cache(current_track, artists, recommendations):
    '''Store the fetched data in the database
    If the data entry is already in the database,
    we ignore the insert command.

    Parameters
    ----------
    current_track : obj
        track object
    artists : list
        list of artist objects
    recommendations : list
        list of recommendation objects

    Returns
    -------
    None
    '''
    db = get_db()
    cur = db.cursor()
    sql = 'INSERT OR IGNORE INTO track (id, trackname, popularity, minute, second, ' \
        'ifexplicit, albumname, imgsrc, lyrics)  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    cur.execute(sql, current_track.db_tuple())
    for artist in artists:
        sql = 'INSERT OR IGNORE INTO artist (id, artistname, popularity, imgsrc, genres)  ' \
            'VALUES (?, ?, ?, ?, ?)'
        cur.execute(sql, artist.db_tuple())
        sql = 'INSERT OR IGNORE INTO bond (trackid, artistid)  VALUES (?, ?)'
        cur.execute(sql, (current_track.id, artist.id, ))
    for recommend in recommendations:
        sql = 'INSERT OR IGNORE INTO recommendation (id, trackid, trackname, minute, second, ' \
              'ifexplicit, imgsrc, artists, urltrack)  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(sql, recommend.db_tuple(current_track.id))

    db.commit()


@app.route('/search', methods=['GET', 'POST'])
def post_search():
    '''Get the artist and track name from the route
    Fetch the data either from Spotify API or database
    If no data is extracted or an error occurs, return
    the error message to the template. Store the fetched
    data in the database accordingly.

    Parameters
    ----------
    None

    Returns
    -------
    flask template of index.html
    '''
    if 'token' not in flask.session:
        return flask.redirect(flask.url_for('show_index'))
    token = flask.session['token']
    headers = {
        'Authorization': token['token_type'] + " " + token['access_token']}

    # Get requested artist and track name
    context = {}
    s_artist = None
    s_track = None
    if flask.request.method == 'POST':
        s_artist = flask.request.form['artist']
        s_track = flask.request.form['track']
    if flask.request.method == 'GET':
        s_artist = flask.request.args.get('artist')
        s_track = flask.request.args.get('track')

    # First search from cache
    current_track, artists, recommendations = search_cache(s_artist, s_track)
    if current_track:
        print('-- FROM DATABASE --')
        context = current_track.present()
        context['artists'] = [x.present() for x in artists]
        context['recommendations'] = recommendations

        return flask.render_template("index.html", **context)

    # Get search result from Spotify
    print('-- FROM SPOTIFY API --')
    params = {
        'q': f'track:{s_track} artist:{s_artist}',
        'type': 'track',
        'limit': 1}
    response = requests.get(spotify_search_url, params=params, headers=headers)
    # Invalid spotify request
    if not response.ok:
        context['error'] = 'Sorry! Invalid request. Please try again later.'
        print(response.text)
        return flask.render_template("index.html", **context)

    data = json.loads(response.text)
    # Error in the search result
    if ('error' in data) or ('tracks' not in data) or (
            data['tracks']['total'] == 0):
        context['error'] = 'No result. Please try another search.'
        print(response.text)
        return flask.render_template("index.html", **context)

    current_track = Track(data=data)

    # Get artists and recommendations
    artists = []
    recommendations = []
    for artist in data['tracks']['items'][0]['artists']:
        current_artist = get_artist(artist['id'], headers)
        if not current_artist:
            continue
        artists.append(current_artist)
        recommendations += get_recommendations(
            artist['id'], current_track.id, current_artist.genres, headers)

    # Get lyrics
    if len(artists) == 0:
        current_track.lyrics = "No lyrics available"
    else:
        try:
            response = requests.get(
                lyrics_search_url +
                artists[0].name +
                '/' +
                current_track.name,
                timeout=1)
            if not response.ok:
                current_track.lyrics = "No lyrics available"
            else:
                lyrics = json.loads(response.text)
                current_track.lyrics = lyrics['lyrics']
        except BaseException:
            current_track.lyrics = "No lyrics available."

    context = current_track.present()
    context['artists'] = [x.present() for x in artists]
    context['recommendations'] = [x.present() for x in recommendations]

    # store in DB
    store_cache(current_track, artists, recommendations)

    return flask.render_template("index.html", **context)


if __name__ == '__main__':
    init_db()
    app.run(threaded=True, port=5000)
