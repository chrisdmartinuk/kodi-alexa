#!/usr/bin/env python

"""
The MIT License (MIT)
Copyright (c) 2015 Maker Musings && m0ngr31
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# For a complete discussion, see http://forum.kodi.tv/showthread.php?tid=254502

import datetime
import json
import requests
import time
import urllib
import os
import random
import re
import string
import sys

# These are words that we ignore when doing a non-exact match on show names
STOPWORDS = [
  "a",
  "about",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "for",
  "from",
  "how",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "this",
  "to",
  "was",
  "what",
  "when",
  "where",
  "will",
  "with",
]

def remove_the(name):
  # Very naive method to remove a leading "the" from the given string
  if name[:4].lower() == "the ":
    return name[4:]
  else:
    return name

# These two methods construct the JSON-RPC message and send it to the Kodi player
def SendCommand(command):
  # Change this to the IP address of your Kodi server or always pass in an address
  KODI = os.getenv('KODI_ADDRESS', '127.0.0.1')
  PORT = int(os.getenv('KODI_PORT', 8089))
  USER = os.getenv('KODI_USERNAME', 'kodi')
  PASS = os.getenv('KODI_PASSWORD', '')
  
  url = "http://%s:%d/jsonrpc" % (KODI, PORT)
  try:
    r = requests.post(url, data=command, auth=(USER, PASS))
  except:
    return {}
  return json.loads(r.text)

def RPCString(method, params=None):
  j = {"jsonrpc":"2.0", "method":method, "id":1}
  if params:
    j["params"] = params
  return json.dumps(j)
  
# Match heard string to something in the results
def matchHeard(heard, results, lookingFor='label'):
  located = None
  
  heard_minus_the = remove_the(heard)
  print heard
  sys.stdout.flush()
  heard_list = set([x for x in heard.split() if x not in STOPWORDS])
  
  for result in results:
    # Strip out non-ascii symbols and lowercase it
    ascii_name = result[lookingFor].encode('ascii', 'replace')
    result_name = str(ascii_name).lower().translate(None, string.punctuation)
    
    # Direct comparison
    if heard == result_name:
      located = result
      break
      
    # Remove 'the'
    if remove_the(result_name) == heard_minus_the:
      located = result
      break
      
    # Remove parentheses
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    if heard == removed_paren:
      located = result
      break
      
  if not located:
    print 'not located on the first round of checks'
    sys.stdout.flush()
    # Loop through results again and be a little more liberal with what is accepted
    for result in results:
      # Strip out non-ascii symbols and lowercase it
      ascii_name = result[lookingFor].encode('ascii', 'replace')
      result_name = str(ascii_name).lower().translate(None, string.punctuation)
      
      print(heard_minus_the)
      sys.stdout.flush()
      print result_name
      sys.stdout.flush()
      # Just look for substring
      if result_name.find(heard_minus_the) != -1:
        located = result
        break

      # Last resort -- take out some useless words and see if we have a match with
      # >= 60% of the heard phrase
      result_list = set([x for x in result_name.split() if x not in STOPWORDS])
      matched_words = [x for x in heard_list if x in result_list]
      print matched_words
      sys.stdout.flush()
      if len(matched_words) > 0:
        percentage = float(len(matched_words)) / float(len(heard_list))
        if percentage > float(0.6):
          located = result
          break
        
  return located


# This is a little weak because if there are multiple active players,
# it only returns the first one and assumes it's the one you want.
# In practice, this works OK in common cases.

def GetPlayerID():
  info = SendCommand(RPCString("Player.GetActivePlayers"))
  result = info.get("result", [])
  if len(result) > 0:
    return result[0].get("playerid")
  else:
    return None
    
def ClearPlaylist():
  return SendCommand(RPCString("Playlist.Clear", {"playlistid": 0}))
  
def ClearVideoPlaylist():
  return SendCommand(RPCString("Playlist.Clear", {"playlistid": 1}))

def StartPlaylist():
  return SendCommand(RPCString("Player.Open", {"item": {"playlistid": 0}}))
  
def AddSongToPlaylist(song_id):
  return SendCommand(RPCString("Playlist.Add", {"playlistid": 0, "item": {"songid": int(song_id)}}))
  
def PrepEpisodePlayList(ep_id):
  return SendCommand(RPCString("Playlist.Add", {"playlistid": 1, "item": {"episodeid": int(ep_id)}}))

def PrepMoviePlaylist(movie_id):
   return SendCommand(RPCString("Playlist.Add", {"playlistid": 1, "item": {"movieid": int(movie_id)}}))
   
def StartVideoPlaylist():
  return SendCommand(RPCString("Player.Open", {"item": {"playlistid": 1}}))

def AddSongsToPlaylist(song_ids):
  songs_array = []
  
  for song_id in song_ids:
    temp_song = {}
    temp_song['songid'] = song_id
    songs_array.append(temp_song)
  
  random.shuffle(songs_array)
    
  return SendCommand(RPCString("Playlist.Add", {"playlistid": 0, "item": songs_array}))

def GetPlaylistItems():
  return SendCommand(RPCString("Playlist.GetItems", {"playlistid": 0}))
  
def GetVideoPlaylistItems():
  return SendCommand(RPCString("Playlist.GetItems", {"playlistid": 1}))
  

# Tell Kodi to update its video or music libraries

def UpdateVideo():
  return SendCommand(RPCString("VideoLibrary.Scan"))
  
def CleanVideo():
  return SendCommand(RPCString("VideoLibrary.Clean"))

def UpdateMusic():
  return SendCommand(RPCString("AudioLibrary.Scan"))

def CleanMusic():
  return SendCommand(RPCString("AudioLibrary.Clean"))


# Perform UI actions that match the normal remote control buttons

def PageUp():
  return SendCommand(RPCString("Input.ExecuteAction", {"action":"pageup"}))

def PageDown():
  return SendCommand(RPCString("Input.ExecuteAction", {"action":"pagedown"}))

def ToggleWatched():
  return SendCommand(RPCString("Input.ExecuteAction", {"action":"togglewatched"}))

def Info():
  return SendCommand(RPCString("Input.Info"))

def Menu():
  return SendCommand(RPCString("Input.ContextMenu"))

def Home():
  return SendCommand(RPCString("Input.Home"))

def Select():
  return SendCommand(RPCString("Input.Select"))

def Up():
  return SendCommand(RPCString("Input.Up"))

def Down():
  return SendCommand(RPCString("Input.Down"))

def Left():
  return SendCommand(RPCString("Input.Left"))

def Right():
  return SendCommand(RPCString("Input.Right"))

def Back():
  return SendCommand(RPCString("Input.Back"))

def PlayPause():
  playerid = GetPlayerID()
  if playerid is not None:
    return SendCommand(RPCString("Player.PlayPause", {"playerid":playerid}))
    
def PlaySkip():
  playerid = GetPlayerID()
  if playerid is not None:
    return SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "next"}))
    
def PlayPrev():
  playerid = GetPlayerID()
  if playerid is not None:
    SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "previous"}))
    return SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "previous"}))
    
def PlayStartOver():
  playerid = GetPlayerID()
  if playerid is not None:
    return SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "previous"}))

def Stop():
  playerid = GetPlayerID()
  if playerid is not None:
    return SendCommand(RPCString("Player.Stop", {"playerid":playerid}))

def Replay():
  playerid = GetPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Seek", {"playerid":playerid, "value":"smallbackward"}))
    
def GetMusicArtists():
  data = SendCommand(RPCString("AudioLibrary.GetArtists"))
  return data

def GetArtistAlbums(artist_id):
  data = SendCommand(RPCString("AudioLibrary.GetAlbums", {"filter": {"artistid": int(artist_id)}}))
  return data
  
def GetArtistSongs(artist_id):
  data = SendCommand(RPCString("AudioLibrary.GetSongs", {"filter": {"artistid": int(artist_id)}}))
  return data

def GetTvShows():
  data = SendCommand(RPCString("VideoLibrary.GetTVShows"))
  return data
  
def GetMovies():
  data = SendCommand(RPCString("VideoLibrary.GetMovies"))
  return data
  
def GetUnwatchedMovies():
  data = SendCommand(RPCString("VideoLibrary.GetMovies", {"filter":{"field":"playcount", "operator":"lessthan", "value":"1"}}))
  return data

def GetEpisodesFromShow(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id)}))
  return data

def GetUnwatchedEpisodesFromShow(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id), "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}}))
  return data
  
def GetNewestEpisodeFromShow(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":1},"tvshowid": int(show_id), "sort":{"method":"dateadded", "order":"descending"}}))
  if 'episodes' in data['result']:
    episode = data['result']['episodes'][0]
    return episode['episodeid']
  else:
    return None
  
def GetNextUnwatchedEpisode(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":1},"tvshowid": int(show_id), "filter":{"field":"lastplayed", "operator":"greaterthan", "value":"0"}, "properties":["season", "episode", "lastplayed", "firstaired"], "sort":{"method":"lastplayed", "order":"descending"}}))
  if 'episodes' in data['result']:
    episode = data['result']['episodes'][0]
    episode_season = episode['season']
    episode_number = episode['episode']
    
    next_episode = GetSpecificEpisode(show_id, episode_season, int(episode_number) + 1)
    
    if next_episode:
      return next_episode
    else:
      next_episode = GetSpecificEpisode(show_id, int(episode_season) + 1, 1)
      
      if next_episode:
        return next_episode
      else:
        return None
  else:
    return None

def GetLastWatchedShow():
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":1}, "filter":{"field":"playcount", "operator":"greaterthan", "value":"0"}, "filter":{"field":"lastplayed", "operator":"greaterthan", "value":"0"}, "sort":{"method":"lastplayed", "order":"descending"}, "properties":["tvshowid"]}))
  return data
  
def GetSpecificEpisode(show_id, season, episode):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id), "season": int(season), "properties": ["season", "episode"]}))
  if 'episodes' in data['result']:
    correct_id = None
    for episode_data in data['result']['episodes']:
      if int(episode_data['episode']) == int(episode):
        correct_id = episode_data['episodeid']
        break
        
    return correct_id
  else:
    return None
  
def GetEpisodesFromShowDetails(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id), "properties": ["season", "episode"]}))
  return data
  
# Returns a list of dictionaries with information about episodes that have been watched. 
# May take a long time if you have lots of shows and you set max to a big number

def GetWatchedEpisodes(max=90):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"greaterthan", "value":"0"}, "properties":["playcount", "showtitle", "season", "episode", "lastplayed" ]}))
  return data['result']['episodes']


# Returns a list of dictionaries with information about unwatched episodes. Useful for
# telling/showing users what's ready to be watched. Setting max to very high values
# can take a long time.

def GetUnwatchedEpisodes(max=90):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}, "sort":{"method":"dateadded", "order":"descending"}, "properties":["title", "playcount", "showtitle", "tvshowid", "dateadded" ]}))
  answer = []
  shows = set([d['tvshowid'] for d in data['result']['episodes']])
  show_info = {}
  for show in shows:
    show_info[show] = GetShowDetails(show=show)
  for d in data['result']['episodes']:
    showinfo = show_info[d['tvshowid']]
    answer.append({'title':d['title'], 'episodeid':d['episodeid'], 'show':d['showtitle'], 'label':d['label'], 'dateadded':datetime.datetime.strptime(d['dateadded'], "%Y-%m-%d %H:%M:%S")})
  return answer


# Grabs the artwork for the specified show. Could be modified to return other interesting data.

def GetShowDetails(show=0):
  data = SendCommand(RPCString("VideoLibrary.GetTVShowDetails", {'tvshowid':show, 'properties':['art']}))
  return data['result']['tvshowdetails']


# Information about the video that's currently playing

def GetVideoPlayItem():
  playerid = GetPlayerID()
  if playerid:
    data = SendCommand(RPCString("Player.GetItem", {"playerid":playerid, "properties":["episode","showtitle", "tvshowid", "season", "description"]}))
    return data["result"]["item"]


# Returns information useful for building a progress bar to show a video's play time

def GetVideoPlayStatus():
  playerid = GetPlayerID()
  if playerid:
    data = SendCommand(RPCString("Player.GetProperties", {"playerid":playerid, "properties":["percentage","speed","time","totaltime"]}))
    if 'result' in data:
      hours = data['result']['totaltime']['hours']
      speed = data['result']['speed']
      if hours > 0:
        total = '%d:%02d:%02d' % (hours, data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
        cur = '%d:%02d:%02d' % (data['result']['time']['hours'], data['result']['time']['minutes'], data['result']['time']['seconds'])
      else:
        total = '%02d:%02d' % (data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
        cur = '%02d:%02d' % (data['result']['time']['minutes'], data['result']['time']['seconds'])
      return {'state':'play' if speed > 0 else 'pause', 'time':cur, 'total':total, 'pct':data['result']['percentage']}
  return {'state':'stop'}
  
def launch_chrome(url):
    print 'launch_chrome(%s)' + url
    url = '?kiosk=yes&mode=showSite&stopPlayback=yes&url='+url
    SendCommand(RPCString('Addons.ExecuteAddon',{'addonid':'plugin.program.chrome.launcher','params':[url]}))     
    return