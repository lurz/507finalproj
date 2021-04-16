
# Play with Lyrics

This is a Flask app which can help the user access and play the songs on Spotify with lyrics displayed along side. It's a single page app with a widget and multiple navigation bars to select from.

## Environment

We need the following packages in your Python3 environment. You can also find all the requirements in `requirements.txt`.  

1. certifi==2020.12.5
2. chardet==4.0.0
3. click==7.1.2
4. Flask==1.1.2
5. gunicorn==20.1.0
6. idna==2.10
7. itsdangerous==1.1.0
8. Jinja2==2.11.3
9. MarkupSafe==1.1.1
10. oauthlib==3.1.0
11. requests==2.25.1
12. requests-oauthlib==1.3.0
13. urllib3==1.26.4
14. Werkzeug==1.0.1

The best practice is to build up a virtual environment in your working directory. Try to start with the following commands:  
`$ cd workdir/`  
`$ python3 -m venv venv`  
`$ . venv/bin/activate`  
`$ pip install -r requirements.txt`  

## API keys

We need a client key and a client secret from the Spotify API. You will need your Spotify account to apply for the developer account and create a new app on the dashboard. If you can't create your own API secrets, please let me know.  

We also need a secret key generated for the Flask session. You can use the following command  
`$ python -c 'import os; print(os.urandom(16))'`  

When you have all the keys and secrets generated, please copy them into the file `secrets.py` in the working directory with the following variable names  
`CLIENT_ID = ''     #spotify api id`  
`CLIENT_SECRET = '' #spotify secret`  
`SECRET_KEY = ''    #used for flask session`  

## Running the code

To run the server, you could use the following command:  

1. Run in development mode: `python3 main.py`  
2. In your browser, enter `localhost:5000` to access the webpage

## Interact with the App

In the top search bar, enter your favorite artist and song name, such as Taylor Swift and Love Story. Click 'search' to start the search.  

On the left side of the screen, you will have a Spotify widget to play the song. On the right, you have a navigation bar to select from 'Lyrics', 'Artists' and 'Recommendations'. Tab 'Lyrics' will display the track information as well as the lyrics. Tab 'artists' will display all the artists who performed in the song and their basic infos such as popularity and genres. Tab 'recommendations' will display all the similar songs to the song you searched. You could initial another search by simply click on the link.
