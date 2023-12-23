import copy
import os
import gunicorn
from datetime import timedelta
from flask import Flask, redirect, render_template, session, url_for, jsonify
from main import *
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET")
# from flask_cors import CORS
#
# CORS(app)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI") + "callback/q"

# Set session timeout to 30 minutes
app.permanent_session_lifetime = timedelta(minutes=30)


# Session hygiene.
@app.route('/clear_session', methods=['GET'])
def clear_session():
    # Clear session data
    session.clear()
    return 'Session cleared', 200


# login to Spotify. Redirects to callback/q.
@app.route("/login")
def index():
    # Authorization
    response = app_Authorization(CLIENT_ID, REDIRECT_URI)
    return redirect(response)


# stores authorization token in session and redirects to homepage.
@app.route("/callback/q")
def callback():
    # verifier = request.args.get('verifier')
    authorization_header = user_Authorization(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    session['spotify_token'] = authorization_header
    return redirect(url_for('hello_world'))


@app.route('/url', methods=['GET'])
def get_playlist_url():
    playlist_id = request.args.get('playlist_id')
    # return jsonify(playlist_id)
    headers = authorize(CLIENT_ID, CLIENT_SECRET)
    playlist_data = grab_playlist_by_url(playlist_id, headers)
    return jsonify(playlist_data)


# returns cleaned tracks
@app.route('/clean', methods=['GET'])
def clean_playlist_url():
    playlist_id = request.args.get('playlist_id')
    # return jsonify(playlist_id)
    access_token, headers = authorize(CLIENT_ID, CLIENT_SECRET)
    playlist_data = grab_playlist_by_url(playlist_id, headers)
    cleaned_data = clean_up_list(headers, playlist_data)
    return jsonify(cleaned_data)


# renders homepage.
@app.route("/", methods=['GET', 'POST'])
def hello_world():
    userid = None
    myPlaylists = None
    clean_tracks = None
    playlist_tracks = None

    if 'spotify_token' in session:
        my_profile = fetch_profile(session['spotify_token'])
        if my_profile is not None:
            userid = my_profile['display_name']
            myPlaylists = get_user_playlists(my_profile, session['spotify_token'])

    if request.method == 'POST' or request.args.get('url'):
        playlist_url = request.form.get('url') if request.method == 'POST' else request.args.get('url')
        if 'spotify_token' not in session:
            headers = authorize(CLIENT_ID, CLIENT_SECRET)
        else:
            headers = session['spotify_token']
        playlist_tracks = grab_playlist_by_url(playlist_url, headers)
        cleaned_tracks = copy.deepcopy(playlist_tracks)
        clean_tracks = clean_up_list(headers, cleaned_tracks)

    return render_template("homePage.html", tracks=playlist_tracks, cleaned=clean_tracks, userPlaylists=myPlaylists,
                           userId=userid)


# create a playlist containing the cleaned tracks. User can specify name of playlist and whether it is public or private.
# Redirects to homepage.
@app.route("/cleansify", methods=['POST'])
def create_playlist():
    if request.method == 'POST':
        track_ids = request.form.getlist('track_ids')
        playlist_name = request.form.get('playlist_name')
        isPublic = False if request.form.get('playlist_type') == "private_playlist" else True
        my_profile = fetch_profile(session['spotify_token'])
        user_name = my_profile['id']
        create_new_playlist(user_name, track_ids, session['spotify_token'], isPublic, playlist_name)
    return redirect(url_for('hello_world'))


# Filter to change the color cleaned songs depending on how likely the located clean version of the track is accurate.
def certainty_color(level):
    if level == 'Potential swap':
        return '#FFA726'
    elif level == 'No match':
        return '#BF360C'
    else:
        return '#181818'


app.jinja_env.filters['certainty_color'] = certainty_color


# Log user out of spotify account and redirect to homepage.
@app.route('/logout')
def logout():
    session.pop('spotify_token', None)
    return redirect(url_for('hello_world'))


# main()
# _______________
# Setting up host and port
if __name__ == "__main__":
    app.run(debug=False)
    # app.run(host='0.0.0.0', port=8081)
