from models import Track, Artist, Recommendation
import sqlite3
from flask import g
import flask
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import json
import secrets as secrets

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


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('./sql/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def show_index():
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    flask.session['token'] = oauth.fetch_token(token_url=spotify_token_url, client_id=client_id,
        client_secret=client_secret)

    return flask.render_template("index.html")

def get_artist(id, headers):
    response = requests.get(spotify_artist_url + id, headers=headers)
    if not response.ok:
        return None
    data = json.loads(response.text)
    if 'error' in data:
        return None
    return Artist(data)

def get_track_img(id, headers):
    response = requests.get(spotify_track_url + id, headers=headers)
    if not response.ok:
        return ""
    data = json.loads(response.text)
    if ('error' in data) or ('album' not in data) or len(data['album']['images'])  < 3:
        return ""
    return data['album']['images'][2]['url']

def get_recommendations(artist_id, track_id, genres, headers):
    result = []
    params = {'seed_artists': artist_id, 'seed_genres': genres, 'seed_tracks': track_id, 'limit': 5}
    response = requests.get(spotify_recom_url, params=params, headers=headers)
    if not response.ok:
        return result
    data = json.loads(response.text)
    if 'error' in data:
        return result
    for track in data['tracks']:
        current_recom = Recommendation(track, get_track_img(track['id'], headers))
        result.append(current_recom.present())
    return result


@app.route('/search', methods=['GET', 'POST'])
def post_search():
    if 'token' not in flask.session:
        return flask.redirect(flask.url_for('show_index'))

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

    # Get search result from Spotify
    token = flask.session['token']
    params = {'q': f'track:{s_track} artist:{s_artist}', 'type': 'track', 'limit': 1}
    headers = {'Authorization': token['token_type'] + " " + token['access_token']}
    response = requests.get(spotify_search_url, params=params, headers=headers)
    # Invalid spotify request
    if not response.ok:
        context['error'] = 'Sorry! Invalid request. Please try again later.'
        print (response.text)
        return flask.render_template("index.html", **context)
    
    data = json.loads(response.text)
    # Error in the search result
    if ('error' in data) or ('tracks' not in data) or (data['tracks']['total'] == 0):
        context['error'] = 'Error. Please try another search.'
        print (response.text)
        return flask.render_template("index.html", **context)
    
    current_track = Track(data)

    # Get artists and recommendations
    artists = []
    recommendations = []
    for artist in data['tracks']['items'][0]['artists']:
        current_artist = get_artist(artist['id'], headers)
        if not current_artist:
            continue
        artists.append(current_artist.present())
        recommendations += get_recommendations(artist['id'], current_track.id, current_artist.genres, headers)

    # Get lyrics
    if len(artists) == 0:
        current_track.lyrics = "No lyrics available"
    else:
        try:
            response = requests.get(lyrics_search_url + artists[0]['name'] + '/' + current_track.name, timeout=1)
            if not response.ok:
                current_track.lyrics = "No lyrics available"
            else:
                lyrics = json.loads(response.text)
                current_track.lyrics = lyrics['lyrics']
        except:
            current_track.lyrics = "No lyrics available."
        
    context = current_track.present()
    context['artists'] = artists
    context['recommendations'] = recommendations

    # DB
    db = get_db()
    cur = db.cursor()
    sql = 'INSERT INTO track (id, trackname, popularity, minute, second, ' \
              'ifexplicit, albumname, imgsrc, lyrics)  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    print (current_track.db_tuple())
    cur.execute(sql, current_track.db_tuple())
    db.commit()

    return flask.render_template("index.html", **context)

if __name__ == '__main__':
    init_db()
    app.run(threaded=True, port=5000)
