import spotipy
import tidalapi
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import time
load_dotenv()  # Load values from .env
TIDAL_SESSION_FILE = ".tidal_session_cache.json"
SPOTIFY_SESSION_FILE = ".spotify_session_cache.json"

def get_spotify_client():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-library-read",
        cache_path= SPOTIFY_SESSION_FILE,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

def get_tidal_client():
    session = tidalapi.Session()
    if os.path.exists(TIDAL_SESSION_FILE):
        with open(TIDAL_SESSION_FILE, "r") as f:
            data = json.load(f)
        try:
            session.load_oauth_session(
                token_type=data["token_type"],
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expiry_time=datetime.fromtimestamp(data["expiry_time"])
            )
            if(session.check_login()):
                print("Tidal Session Restored")
                return session
            else: 
                print("Tidal Session Expired!  Reauthenticating...")
        except Exception as e:
            print("Failed to load stored Tidal session: ", e)

    #If saved login fails:
    session.login_oauth_simple()
    session_data = {
            "token_type": session.token_type,
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expiry_time": session.expiry_time.timestamp()
    }

    with open(TIDAL_SESSION_FILE, "w") as f:
            json.dump(session_data, f)

    print("New Tidal session created and saved.")
    return session

def log_out_spotify():
    if os.path.exists(SPOTIFY_SESSION_FILE):
        os.remove(SPOTIFY_SESSION_FILE)
        print("Logged out of spotify!")

def log_out_tidal():
    if os.path.exists(TIDAL_SESSION_FILE):
        os.remove(TIDAL_SESSION_FILE)
        print("Logged out of Tidal!")
