import flask
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import json
import secrets as secrets

app = flask.Flask(__name__)
client_id = secrets.CLIENT_ID
client_secret = secrets.CLIENT_SECRET
spotify_token_url = 'https://accounts.spotify.com/api/token'

@app.route('/')
def hello_world():
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    token = oauth.fetch_token(token_url=spotify_token_url, client_id=client_id,
        client_secret=client_secret)

    params = {'q': 'justin bieber', 'type': 'artist', 'limit': 1}
    headers = {'Authorization': token['token_type'] + " " + token['access_token']}
    response = requests.get('https://api.spotify.com/v1/search', params=params, headers=headers)
    data = json.loads(response.text)

    context = {'items': data['artists']['items'], 'images': data['artists']['items'][0]['images'][0]}
    return flask.render_template("index.html", **context)