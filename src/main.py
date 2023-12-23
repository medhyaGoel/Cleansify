# This library contains functions that access spotify API to detox playlists
import json
import secrets
import re
import requests
import base64
from flask import request

# Spotify URLS
BASE_URL = 'https://api.spotify.com/v1/'
AUTH_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
SPOTIFY_PROFILE_URL = "https://api.spotify.com/v1/me"

# Server-side Parameters
SCOPE = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public ' \
        'playlist-modify-private'
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


def create_new_playlist(user_name, track_ids, token, isPublic, playlist_name):
    # create blank playlist
    url = f'https://api.spotify.com/v1/users/{user_name}/playlists'
    token["Content-Type"] = "application/json"
    body = {
        'name': playlist_name,
        'public': isPublic,
        'description': "Crafted with Cleansify"
    }
    response = requests.post(url, headers=token, json=body)
    playlist_id = response.json()['id']


    # add tracks
    track_ids = json.loads(track_ids[0])
    track_ids = ['spotify:track:' + item for item in track_ids]

    add_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    body = {
        'uris': track_ids,
        'position': 0
    }
    response = requests.post(add_url, headers=token, json=body)
    return response.json()


# Authorization of application with spotify
def app_Authorization(client_id, redirect_uri):

    state = secrets.token_urlsafe(16)

    auth_query_parameters = {
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "scope": SCOPE,
        "state": state
    }
    resp = requests.get(
        url=SPOTIFY_AUTH_URL,
        params=auth_query_parameters,
        allow_redirects=True
    )
    return resp.url


# User has allowed us to access their spotify
def user_Authorization(client_id, client_secret, redirect_uri):
    auth_token = request.args['code']
    if not auth_token:
        app_Authorization(client_id)
    else:
        code_payload = {
            "grant_type": "authorization_code",
            "code": str(auth_token),
            "redirect_uri": redirect_uri
        }
        base64encoded = base64.b64encode((client_id + ":" + client_secret).encode("ascii")).decode("ascii")
        headers = {'content-type': 'application/x-www-form-urlencoded',
                   "Authorization": "Basic {}".format(base64encoded)}
        post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

        # Tokens are Returned to Application
        response_data = json.loads(post_request.text)
        access_token = response_data["access_token"]

        # Use the access token to access Spotify API
        authorization_header = {"Authorization": "Bearer {}".format(access_token)}
        return authorization_header


# grab the playlist at the given url
def grab_playlist_by_url(playlist_url, header):
    match = re.search(r'playlist/([a-zA-Z0-9_-]+)', playlist_url)
    playlist_id = match.group(1) if match else None
    PLAYLIST_URL = 'https://api.spotify.com/v1/playlists/' + playlist_id
    playlist_response = requests.get(PLAYLIST_URL, headers=header)
    return playlist_response.json()


def fetch_profile(headers):
    response = requests.get(SPOTIFY_PROFILE_URL, headers=headers)
    return response.json()


# create clean version of playlist
def clean_up_list(header, playlist):
    clean_versions = []
    # collect clean_versions
    for track in playlist['tracks']['items']:
        # if track is clean, add it to clean_versions
        if not track['track']['explicit']:
            track['track']['certainty'] = "Original"
            clean_versions.append(track['track'])
        else:
            # search for clean version
            title_string = '+'.join(track['track']['name'].split())
            artist_string = ""
            if track['track']['artists'] is not None:
                artist_string = "artist%3D"
                for artist in track['track']['artists']:
                    artist_string += '+'.join(artist['name'].split())

            SEARCH_URL = 'https://api.spotify.com/v1/search?q=' + title_string + '+clean%2C+' + artist_string + '&type=track'
            search_results = requests.get(SEARCH_URL, headers=header).json()
            # iterate through search results and append first result marked not explicit
            isAdded = False
            for result in search_results['tracks']['items']:
                if not result['explicit']:
                    clean_versions.append(result)
                    result['certainty'] = 'Potential swap'
                    isAdded = True
                    break
            if not isAdded:
                track['track']['certainty'] = 'No match'
                clean_versions.append(track['track'])

    return clean_versions


# grab all the playlists of the given user_id
def get_user_playlists(profile, headers):
    url = f'https://api.spotify.com/v1/users/{profile["id"]}/playlists'
    response = requests.get(url, headers=headers)
    return response.json()


def authorize(client_id, client_secret):
    # POST
    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })

    # convert the response to JSON
    auth_response_data = auth_response.json()

    # save the access token
    access_token = auth_response_data['access_token']
    print(f"access token is {access_token}")

    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    return headers
