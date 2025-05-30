import os
import sys
import readchar
from clearConsole import clear_console
from authenticate import get_spotify_client, get_tidal_client, log_out_spotify, log_out_tidal
from load_playlists import load_playlists
import time

spotify_session = None
tidal_session = None

def start():
    global spotify_session, tidal_session
    clear_console()
    print("Authenticating Spotify...")
    spotify_session = get_spotify_client()
    print("Spotify Authenticated!")

    print("Authenticating Tidal...")
    tidal_session = get_tidal_client()
    print("Tidal Authenticated!")

    if spotify_session is not None and tidal_session is not None:
        print("\nAuthentication sucessful!  Running program :)")
        time.sleep(1.5)
    run()

def run():
    if spotify_session is None or tidal_session is None:
        print("Error durring authentication.  Goodbye")
        sys.exit(0)

    while True:
        clear_console()
        print("Welcome to Tidalfy!")
        print("[0]Transfer Playlists\n[1]Albums\n[l]Log Out\n[e]Exit")
        answer = readchar.readkey()
        if(answer == '0'): 
            clear_console()
            load_playlists(spotify_session, tidal_session, 5)
        #elif(answer == '1'): load_albums()
        elif answer == 'l': 
            log_out()
        elif answer == 'e':
            clear_console()
            print("Thank you, have a good day!  :)")
            readchar.readkey()
            clear_console()
            sys.exit(0)
        else: clear_console()


def log_out():
    needs_restart = False
    while True:
        clear_console()
        print("Log out of Spotify? (y/n)")
        print("You may need to log out of spotify on your browser before restarting program.")
        log_out_sp = readchar.readkey()

        if log_out_sp == 'y':
            log_out_spotify()
            needs_restart = True
            break
        elif log_out_sp == 'n':
            break

    while True:
        clear_console()
        print("Log out of Tidal? (y/n)")
        log_out_tid = readchar.readkey()

        if log_out_tid == 'y': 
            log_out_tidal()
            needs_restart = True
            break
        elif log_out_tid == 'n':
            break

    if needs_restart == True:
        clear_console()
        print("Logged out of sessions.  Press any key to restart...")
        readchar.readkey()
        python = sys.executable
        os.execl(python, python, *sys.argv)

    else:
        print("Remaining logged in!")
        time.sleep(1)
        return
start()
