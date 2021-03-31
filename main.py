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
spotify_token_url = 'https://accounts.spotify.com/api/token'
spotify_search_url = 'https://api.spotify.com/v1/search'
spotify_artist_url = 'https://api.spotify.com/v1/artists/'
lyrics_search_url = 'https://api.lyrics.ovh/v1/'

class Track:
    def __init__(self, data=None, lyrics=None):
        super().__init__()
        item = data['tracks']['items'][0]
        self.id = item['id']
        self.name = item['name']
        self.popularity = item['popularity']
        self.minute = int((int(item['duration_ms'])/(1000*60))%60)
        self.second = int((int(item['duration_ms'])/1000)%60)
        self.explicit = bool(item['explicit'])
        self.album = item['album']['name']
        self.img_src = item['album']['images'][2]['url']
        self.lyrics = lyrics['lyrics']
        self.next = data['tracks']['next']
        self.prev = data['tracks']['previous']

    def present(self):
        context = {}
        context['id'] = self.id
        context['name'] = self.name 
        context['popularity'] = self.popularity
        context['minute'] = self.minute
        context['second'] = self.second
        context['explicit'] = self.explicit
        context['album'] = self.album
        context['img_src'] = self.img_src
        context['lyrics'] = self.lyrics
        context['next'] = self.next
        context['prev'] = self.prev
        return context


class Artist:
    def __init__(self, data=None):
        super().__init__()
        self.id  = data['id']
        self.img_src = data['images'][2]['url']
        self.name = data['name']
        self.genres = data['genres']
        self.popularity = data['popularity']

    def present(self):
        context = {}
        context['id'] = self.id
        context['name'] = self.name 
        context['popularity'] = self.popularity
        context['img_src'] = self.img_src
        context['genres'] = self.genres
        return context

@app.route('/')
def show_index():
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    flask.session['token'] = oauth.fetch_token(token_url=spotify_token_url, client_id=client_id,
        client_secret=client_secret)

    return flask.render_template("index.html")

def get_artist(id, headers):
    response = requests.get(spotify_artist_url + id, headers=headers)
    data = json.loads(response.text)
    return Artist(data).present()

@app.route('/search', methods=['GET', 'POST'])
def post_search():
    if 'token' not in flask.session:
        return flask.redirect(flask.url_for('show_index'))

    context = {}
    if flask.request.method == 'POST':
        s_artist = flask.request.form['artist']
        s_track = flask.request.form['track']

        token = flask.session['token']
        params = {'q': f'track:{s_track} artist:{s_artist}', 'type': 'track', 'limit': 1}
        headers = {'Authorization': token['token_type'] + " " + token['access_token']}
        response = requests.get(spotify_search_url, params=params, headers=headers)
        data = json.loads(response.text)
        lyrics = json.loads(requests.get(lyrics_search_url + s_artist + '/' + s_track).text)

        artists = []
        for artist in data['tracks']['items'][0]['artists']:
            artists.append(get_artist(artist['id'], headers))

        context = Track(data, lyrics).present()
        context['artists'] = artists
        return flask.render_template("index.html", **context)
    return flask.render_template("index.html", **context)

