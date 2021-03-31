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
spotify_recom_url = 'https://api.spotify.com/v1/recommendations'
spotify_track_url = 'https://api.spotify.com/v1/tracks/'
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
        if self.second < 10:
            self.second = '0' + str(self.second)
        else:
            self.second = str(self.second)
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
        if len(data['genres']) > 3:
            self.genres = data['genres'][0:3]
        else:
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

class Recommendation:
    def __init__(self, item=None, img_src=None):
        super().__init__()
        self.id = item['id']
        self.name = item['name']
        self.minute = int((int(item['duration_ms'])/(1000*60))%60)
        self.second = int((int(item['duration_ms'])/1000)%60)
        if self.second < 10:
            self.second = '0' + str(self.second)
        else:
            self.second = str(self.second)
        self.explicit = bool(item['explicit'])
        self.artists = []
        self.img_src = img_src
        for artist in item['artists']:
            self.artists.append(artist['name'])
        self.url = f'/search?artist={self.artists[0]}&track={self.name}'

    def present(self):
        context = {}
        context['id'] = self.id
        context['name'] = self.name 
        context['minute'] = self.minute
        context['second'] = self.second
        context['explicit'] = self.explicit
        context['artists'] = self.artists
        context['img_src'] = self.img_src
        context['url'] = self.url
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
    return Artist(data)

def get_track_img(id, headers):
    response = requests.get(spotify_track_url + id, headers=headers)
    data = json.loads(response.text)
    return data['album']['images'][2]['url']

def get_recommendations(artist_id, track_id, genres, headers):
    params = {'seed_artists': artist_id, 'seed_genres': genres, 'seed_tracks': track_id, 'limit': 5}
    response = requests.get(spotify_recom_url, params=params, headers=headers)
    data = json.loads(response.text)
    result = []
    for track in data['tracks']:
        current_recom = Recommendation(track, get_track_img(track['id'], headers))
        result.append(current_recom.present())
    return result


@app.route('/search', methods=['GET', 'POST'])
def post_search():
    if 'token' not in flask.session:
        return flask.redirect(flask.url_for('show_index'))

    context = {}
    s_artist = None
    s_track = None
    if flask.request.method == 'POST':
        s_artist = flask.request.form['artist']
        s_track = flask.request.form['track']
    if flask.request.method == 'GET':
        s_artist = flask.request.args.get('artist')
        s_track = flask.request.args.get('track')

    token = flask.session['token']
    params = {'q': f'track:{s_track} artist:{s_artist}', 'type': 'track', 'limit': 1}
    headers = {'Authorization': token['token_type'] + " " + token['access_token']}
    response = requests.get(spotify_search_url, params=params, headers=headers)
    data = json.loads(response.text)
    lyrics = json.loads(requests.get(lyrics_search_url + s_artist + '/' + s_track).text)

    current_track = Track(data, lyrics)
    artists = []
    recommendations = []
    for artist in data['tracks']['items'][0]['artists']:
        current_artist = get_artist(artist['id'], headers)
        artists.append(current_artist.present())
        recommendations += get_recommendations(artist['id'], current_track.id, current_artist.genres, headers)

    context = current_track.present()
    context['artists'] = artists
    context['recommendations'] = recommendations
    return flask.render_template("index.html", **context)

