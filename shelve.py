#!/usr/bin/env python


import bencode
import cPickle as pickle
import glob
import json
import os
from   pprint import pprint
import re
import readline
import subprocess
import sys
import whatapi


class Shelver:
  def __init__(self):
    self.config = json.loads(open('config.json').read())

  def torrents(self):
    for f in os.listdir(self.config['torrent_path']):
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
        torrent = bencode.bdecode(open('%s/%s' % (self.config['torrent_path'], f)).read())
        dl = '%s/%s' % (self.config['dl_path'], torrent['info']['name'])

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


if __name__ == '__main__':
  shelve = Shelver() 

  shelve.torrents()
