import re
import string 
import unicodedata
import time

class Querry_Result: 
    def __init__(self, success, track_id, query, track_name, artist):
        self.success = success
        self.track_id = track_id
        self.query = query
        self.track_name = track_name
        self.artist = artist
    
    
    def __repr__(self):
        return f"<Query_Result success={self.success} id={self.track_id} query='{self.query}' track_name='{self.track_name}' artist='{self.artist}'>"

class Group_Transfer:
    def __init__(self, tracks, tidal_session):
        self.tracks = tracks
        self.tidal_session = tidal_session
        
        self.transfer_manager = Transfer_Manager(tidal_session)
        self.successful_track_ids = [] 
        self.failed_tracks = []

    def transfer_tracks(self, advanced_query):
        for track in self.tracks:
            result = self.transfer_manager.quick_query(track)
            if result.success == False and advanced_query == True: result = self.transfer_manager.advanced_query(track)
            if result.success == True: self.successful_track_ids.append(result.track_id)
            else: self.failed_tracks.append(result)

class Transfer_Manager:
    def __init__(self, tidal_session):
        self.tidal_session = tidal_session

    def query_by_isrc(self, isrc):
            result = self.tidal_session.search(isrc)
            if result["tracks"]: return result
            else: return None

    def query_by_name_and_artist(self, track_name, artist):
        query = f"{name} {artist}"
        result = self.tidal_session.search(query)
        if result["tracks"]: return result["tracks"]
        else: return None

    def quick_query(self, track): 
        #Uses ISRC id to find track on Tidal.  If nothing's found, it'll attempt to query the track name / artist
        name = track['name']
        artist = track['artists'][0]['name']
        isrc = track['external_ids'].get('isrc')
        if(isrc):
            result = self.tidal_session.search(isrc)
            if result["tracks"]: return Querry_Result(True, result["tracks"][0].id, isrc, name, artist)

        query = f"{name} {artist}"
        results = self.tidal_session.search(query)

        if results["tracks"]: return Querry_Result(True, results["tracks"][0].id, query, name, artist)
        return Querry_Result(False, None, query, name, artist)
        
    def advanced_query(self, track):
        name = self.clean_track_name(track["name"])
        artist = self.clean_artist_name(track["artists"][0]["name"])
        
        cleaned_track = f"{name} {artist}"
        removed_punc = f"{self.remove_punctuation(name)} {self.remove_punctuation(artist)}"
        replaced_punc = f"{self.replace_punctuation_with_space(name)} {self.replace_punctuation_with_space(artist)}"
        removed_accents = f"{self.remove_accents(name)} {self.remove_accents(artist)}"
        
        queries = [cleaned_track, removed_punc, replaced_punc, removed_accents]

        for query in queries:
            result = self.tidal_session.search(query)
            if result["tracks"]: return Querry_Result(True, result["tracks"][0], query, name, artist)

        return Querry_Result(False, None, cleaned_track, name, artist)

    def clean_track_name(self, name):
        # Remove things like (Remastered), (Live), etc.
        name = re.sub(r"\s*[\(\[]?(Remastered|Live|Bonus Track|Explicit|Clean)[^\)\]]*[\)\]]?", "", name, flags=re.IGNORECASE)
        return name.strip()
    
    def clean_artist_name(self, name):
        # Remove everything after "feat.", "ft.", "&"
        name = re.sub(r"\s*(feat\.?|ft\.?|&).*", "", name, flags=re.IGNORECASE)
        return name.strip()

    def remove_punctuation(self, text): 
        return text.translate(str.maketrans('', '', string.punctuation))

    def replace_punctuation_with_space(self, text):
        return re.sub(rf"[{re.escape(string.punctuation)}]", " ", text)

    def remove_accents(self, text):
        normalized = unicodedata.normalize('NFD', text)
        return ''.join(c for c in normalized if not unicodedata.combining(c))
