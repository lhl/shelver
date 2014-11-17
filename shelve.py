#!/usr/bin/env python


# ptk
from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu

from pygments.token import Token
from pygments.style import Style


import bencode
import cPickle as pickle
import eyed3
import glob
import json
import os
from   pprint import pprint
import re
import readline
import subprocess
import sys
import whatapi


# UTF-8 Hack
reload(sys)
sys.setdefaultencoding("utf-8")


terms = []

class Shelver:
  def __init__(self):
    try:
      self.config = json.loads(open('config.json').read())
    except:
      self.config = json.loads(open('%s/config.json' % os.path.dirname(os.path.abspath(__file__))).read())


  def folders(self):
    global terms

    for f in os.listdir(os.getcwd()):
      original = '%s/%s' % (os.getcwd(), f)

      # autocomplete
      parts = []
      artists = []
      albums = []
      years = []

      # skip symlinks
      if os.path.islink(f):
          continue
      
      # skip files
      if os.path.isfile(f):
        continue

      # Look for MP3 info
      try:
        mp3s = glob.glob('./%s/*.mp3' % f)
      except:
        print f
        mp3s = None
        sys.exit()
      if not mp3s:
        continue
      
      ### Parse ID3 Tags
      mp3 = eyed3.load(mp3s[0])
      if mp3 and mp3.tag:
        if mp3.tag.recording_date:
          years.append('%s' % mp3.tag.recording_date.year)
        if mp3.tag.artist:
          artists.append(mp3.tag.artist.strip())
        if mp3.tag.album_artist:
          artists.append(mp3.tag.album_artist)
        if mp3.tag.album:
          albums.append(mp3.tag.album.strip())


      ### Parse Folder

      # Replace underscores 
      f = f.replace('_', ' ')

      # Replace underscores 
      f = f.replace('_', ' ')

      # Dashes to parts 
      parts = f.split('-')
      parts = [part.strip() for part in parts]
      '''
      # If we want a separate copy (only makes sense w/ ' _ ' split
      for part in parts[:]:
        parts.extend(part.split('-'))
      '''
      years.extend(re.findall(r'\b\d\d\d\d\b', f))

      ### UI
      cli = CommandLineInterface(style=shelverStyle,
                                 layout=Layout(before_input=DefaultPrompt('> '),
                                               menus=[CompletionsMenu()]),
                                 line=Line(completer=shelverCompleter()),
                                 create_async_autocompleters=True,
                                )

      print 'FOLDER : %s' % f

      # Prefill
      cli.layout.before_input = DefaultPrompt('artist > ')
      terms = artists + parts
      artist = cli.read_input()
      artist = artist.text
      if not artist:
        print "Skipping..."
        print
        continue 

      cli.layout.before_input = DefaultPrompt('year   > ')
      terms = years
      year = cli.read_input()
      year = year.text
      if not year:
        print "Skipping..."
        print
        continue 

      cli.layout.before_input = DefaultPrompt('album  > ')
      terms = albums + parts
      album = cli.read_input()
      album = album.text
      if not album:
        print "Skipping..."
        print
        continue 

      def hook():
        readline.insert_text('%s - %s - %s' % (artist, year, album))
        readline.redisplay()
      readline.set_pre_input_hook(hook)
      result = raw_input('[btmv] > ')
      if not result:
        print "Skipping..."
        print
        continue 

      if result:
        subprocess.call(['btmv',
                         original,
                         result
                       ])
      print
    

  def torrents(self):
    torrent_path = '%s/watch' % os.getcwd()
    dl_path = os.getcwd()
    if not os.path.isdir(torrent_path):
      torrent_path = self.config['torrent_path']
      dl_path = self.config['dl_path']

    for f in os.listdir(torrent_path):
      t = f.split('.torrent')[0]
      try:
        matches = re.match('(.*) - (.*) - (\d\d\d\d) (.*)', t)

        # Artist
        artist = matches.group(1)

        # Title
        title = matches.group(2)

        # Year
        year = matches.group(3)

        # Format
        extra = matches.group(4)

        # Get Folder
        torrent = bencode.bdecode(open('%s/%s' % (torrent_path, f)).read())
        dl = '%s/%s' % (dl_path, torrent['info']['name'])

        # Doesn't exist - well we're not moving it then
        if not os.path.exists(dl):
          print 'MISSING: %s' % t
          continue

        # Skip if is symlink (moved already)
        if os.path.islink(dl):
          # print 'SYMLINK: %s' % torrent['info']['name']
          continue

        if os.path.isdir(dl):
          print 'TORRENT: %s' % t
          print 'FOLDER : %s' % torrent['info']['name']

          # Prefill
          def hook_artist():
            readline.insert_text(artist.encode('utf8'))
            readline.redisplay()
          readline.set_pre_input_hook(hook_artist)
          artist = raw_input('artist > ')

          def hook_year():
            readline.insert_text(year)
            readline.redisplay()
          readline.set_pre_input_hook(hook_year)
          year = raw_input('year   > ')

          def hook_title():
            readline.insert_text(title.encode('utf8'))
            readline.redisplay()
          readline.set_pre_input_hook(hook_title)
          title = raw_input('title  > ')

          def hook():
            readline.insert_text('%s - %s - %s' % (artist, year, title))
            readline.redisplay()
          readline.set_pre_input_hook(hook)
          result = raw_input('[btmv] > ')

          if result:
            subprocess.call(['btmv',
                             dl,
                             result
                           ])
          print


        if os.path.isfile(dl):
          print 'TORRENT: %s' % t
          print 'FILE   : %s' % torrent['info']['name']

          # Prefill
          def hook():
            readline.insert_text(torrent['info']['name'])
            readline.redisplay()
          readline.set_pre_input_hook(hook)

          result = raw_input('[btmv] > ')

          if result:
            subprocess.call(['btmv',
                             dl,
                             '_misc/%s' % result
                           ])
          print


      except (KeyboardInterrupt, SystemExit):
        sys.exit()

      except:
        # not music
        pass
  
  def whatlogin(self):
    try:
      cookies = pickle.load(open('cookies.dat', 'rb'))
      what = whatapi.WhatAPI(username=self.config['user'], password=self.config['password'], cookies=cookies)
    except:
      what = whatapi.WhatAPI(username=self.config['user'], password=self.config['password'])

    # Logged In
    pickle.dump(what.session.cookies, open('cookies.dat', 'wb'))

    '''
    # Unfortunately torrent does not have torrent id
    torrent = bencode.bdecode(open(f).read())
    print f
    pprint(torrent)
    '''


class shelverCompleter(Completer):
  def get_completions(self, document):
    global terms
    word_before_cursor = document.get_word_before_cursor()
    for a in terms:
      if a.startswith(word_before_cursor):
        yield Completion(a, -len(word_before_cursor))


class shelverStyle(Style):
  styles = { Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
             Token.Menu.Completions.Completion:         'bg:#008888 #ffffff',
             Token.Menu.Completions.ProgressButton:     'bg:#003333',
             Token.Menu.Completions.ProgressBar:        'bg:#00aaaa',
           }


if __name__ == '__main__':
  shelve = Shelver() 

  shelve.torrents()

  shelve.folders()
