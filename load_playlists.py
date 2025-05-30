import os
import string
import re
import time
from threading import Thread
import readchar
from clearConsole import clear_console
from transfer_manager import Transfer_Manager, Group_Transfer

def get_playlists(sp):
    all_playlists = []
    offset = 0
    playlist_request_limit = 50

    while True: 
        response = sp.current_user_playlists(limit=playlist_request_limit, offset=offset)
        all_playlists.extend(response['items'])
        if response['next'] is None:
            break
        offset += playlist_request_limit
    return all_playlists

#####################################################
def print_page(page): 
    option_num = 0
    for playlist in page:
        print(f"[{option_num}]{playlist['name']}")
        option_num += 1


#####################################################
def get_menu_pages(playlists, playlists_per_page):
    pages = [[]]
    current_page = pages[0]
    i = 0

    for playlist in playlists: 
        current_page.append(playlist) 
        i += 1
        if(i == playlists_per_page):
            pages.append([])
            current_page = pages[-1]
            i = 0
    return pages
#######################################################
def get_tracks_from_playlist(spotify_session, playlist):
    all_tracks = []

    print("Getting Tracks...", end="")
    offset = 0
    limit = 100

    while True:
        response = spotify_session.playlist_items(playlist['id'], offset=offset, limit=limit)
        all_tracks.extend(response['items'])
        if (response['next'] is None):
            break
        else: 
            offset += limit
            print(".", end="", flush=True)
    
    clear_console()
    print(f"{len(all_tracks)} Tracks Recieved!")
    return all_tracks

def query_track(tidal_session, track): 
    transfer_manager = Transfer_Manager(tidal_session)
    return transfer_manager.quick_query(track)    

def retry_failed_track(tidal_session, track_result):
    fixed_track = None
    while True:
        clear_console()
        print(f"{track_result['name']} | {track_result['artist']}")

        query_name = input("Query Name: ")
        query_artist = input("Query Artist: ")

        query = f"{query_name} {query_artist}"
        results = tidal_session.search(query)

        top_tracks = results['tracks'][:8]
        clear_console()
        if(len(top_tracks) == 0):
            print("No results found")
            break
        
        print("Select a track to add to playlist: ")
        print("[0]Cancel")
        for i, track in enumerate(top_tracks):
            print(f"[{i+1}]{track.name} | {track.artist.name}")

        selected_track = readchar.readkey()

        if selected_track == '0': break
        else: 
            try:
                selected_track_to_int = int(selected_track) - 1
                if 0 <= selected_track_to_int < len(top_tracks):
                    fixed_track = top_tracks[selected_track_to_int].id
                    return fixed_track

            except (ValueError, IndexError):
                print("Invalid selection.")
                break

    return fixed_track

def view_failed_tracks(tidal_session, failed_tracks):
    lines_to_write = []
    fixed_tracks = []
    while True:
        clear_console()
        print("Enter track number to manually query track.")
        print("[q] Exit")
        print("[0]Save failed tracks as file")
        
        i = 1
        for track in failed_tracks:
            track_name = track.track_name
            track_artist = track.artist

            line = f"{track_name} | {track_artist}"
            lines_to_write.append(line)
            print(f"[{i}]{track_name} | {track_artist}")
            i += 1
        
        option = input("")

        if(option == '0'):
            clear_console()
            print("Warning: This action will overwrite previous saved file.  Continue?\n[0]No\n[1]Yes")
            cont = readchar.readkey()
            if(cont == '0'): break
            elif(cont == '1'):
                save_file = True
                with open("failed_tracks.txt", "w") as f:
                    for line in lines_to_write:
                        f.write(line + "\n")

            print("File Saved!\nPress any key to return")
            readchar.readkey()
            break
        elif(option == 'q'): return fixed_tracks
        else: 
            print("Trying fixed tracks")
            try:
                option_to_int = int(option) - 1
                if(option_to_int>= 0 and option_to_int<= len(failed_tracks)):
                    track_id = retry_failed_track(tidal_session, failed_tracks[option_to_int])
                    if track_id is not None: 
                        fixed_tracks.append(track_id)
                        clear_console()
                        failed_tracks.pop(option_to_int)
                else: break

            finally: pass
    return fixed_tracks
            
def transfer_playlist(spotify_session, tidal_session, playlist):
    clear_console()
    user = tidal_session.user
    raw_track_data = get_tracks_from_playlist(spotify_session, playlist)
    all_tracks = []

    for raw_track in raw_track_data:
        all_tracks.append(raw_track['track'])

    print("Atempting to transfer...")
    time.sleep(0.25)

    group = Group_Transfer(all_tracks, tidal_session)
    thread = Thread(target=group.transfer_tracks, args=(True,))
    thread.start()

    while thread.is_alive():
        successful = len(group.successful_track_ids)
        failed = len(group.failed_tracks)
        total_attempted = successful + failed 

        clear_console()
        print("Pulling tracks from Tidal... this may take awhile.")
        print(f"Attempted {total_attempted} of {len(group.tracks)} tracks!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        time.sleep(.2) 

    thread.join()

    readchar.readkey() 
    clear_console()
    print(f"{len(group.successful_track_ids)} of {len(group.tracks)} tracks successfully added!")
    print(f"Would you like to see which tracks failed?\n[0]No\n[1]Yes")
    see_failed_tracks = readchar.readkey()
    if(see_failed_tracks == '1'): 
        fixed_tracks = view_failed_tracks(tidal_session, group.failed_tracks)
        if(len(fixed_tracks) > 0): successful_tracks.extend(fixed_tracks)
    while True:
        clear_console()
        print("Generate Playlist?\n[0]No\n[1]Yes")
        generate_playlist = readchar.readkey()
        
        if(generate_playlist == '0'): return
        elif(generate_playlist == '1'): break
        
    clear_console()
    print("Creating Playlist...")
    new_tidal_playlist = user.create_playlist(playlist['name'], "Created with Tidalfy")
    new_tidal_playlist.add(successful_tracks)
    print("Playlist transfered successfully!  Press any key to continue.")
    
#######################################################
def run_menu(pages):
    clear_console()
    page_index = 0
    while True:
        clear_console()
        print("PLAYLISTS:")
        print_page(pages[page_index])
        print(f"[{page_index + 1}/{len(pages)}]")
        key = readchar.readkey()
        clear_console()
        if key == readchar.key.RIGHT:
            page_index += 1
            if page_index >= len(pages): page_index = 0
        elif key == readchar.key.LEFT:
            page_index -= 1
            if page_index < 0: page_index = len(pages) - 1
        else: 
            try: 
                keyToInt= int(key)
                if (keyToInt >= 0 and keyToInt < len(pages[page_index])): 
                    while True:
                        selected_playlist = pages[page_index][keyToInt]
                        print(f"Playlist: {selected_playlist['name']}?")
                        print("[0]Back\n[1]Transfer")
                        confirm = readchar.readkey()
                        if (confirm == '0'): break
                        elif (confirm == '1'): return selected_playlist
            finally:
                pass


######################################################
def load_playlists(spotify_session, tidal_session, playlists_per_page):
    selected_playlist = None
    print("Loading...")
    playlists = get_playlists(spotify_session)
    pages = get_menu_pages(playlists, playlists_per_page)
    selected_playlist = run_menu(pages)
    if (selected_playlist is not None): transfer_playlist(spotify_session, tidal_session, selected_playlist)


