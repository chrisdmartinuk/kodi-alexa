#!/usr/bin/env python
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
from googleapiclient.discovery import build
import pprint


sys.path += [os.path.dirname(__file__)]
import kodi

def main():
    findNetflixID("delete")
    return

def findNetflixID(search_term):
    
    url = 'http://flixsearch.io/search/'+search_term.replace(' ','-')+'?subtitle=&language=&country=3&media_type=&sort=popularity-desc'
    kodi.launch_chrome( url )
        
    #html = response.text
    #m =  re.search('Matching Titles: \"'+search_term+'\"</h3><em><strong>([0-9]*) match.*</strong></em>', html, flags=re.IGNORECASE )
    #if m is None:
    # print("found none")
    # return None
    #numMatches = int( m.group(1) )
    return
if __name__ == "__main__":
    main()
  