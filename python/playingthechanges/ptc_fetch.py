#! /usr/bin/python
# coding=UTF-8
"""
Fetches the MP3 files from playingthechanges.com to import into iTunes.

Author:  Mike Bland (mbland@acm.org)
         http://mike-bland.com/
Date:    2014-03-13
License: Creative Commons Attribution 4.0 International (CC By 4.0)
         http://creativecommons.org/licenses/by/4.0/deed.en_US

Grabs all the MP3 links from the http://playingthechanges.com/ page and
downloads each file into the current directory, then updates the tag info for
each MP3.

If you don't have the requests module installed, you may need to
install pip, the Python Package Index installer:
  https://pypi.python.org/pypi
  http://www.pip-installer.org/en/latest/installing.html

Then:
  $ sudo pip install requests

Requires the id3lib tools. For OS X, install Homebrew: http://brew.sh/

Then:
  $ brew install id3lib

Written with hints from:
  http://ubuntuforums.org/showthread.php?t=1542894
  http://docs.python-requests.org/en/latest/user/quickstart/

More info:
  http://mike-bland.com/2014/03/17/playing-the-changes-hack-continued.html
"""

import contextlib
import os
import os.path
import re
import requests
import subprocess
import sys


PTC_COM='http://www.playingthechanges.com'

ROOT_WEIGHTS = {
  'C':      0,
  'F':      1,
  'Bb':     2,
  'Eb':     3,
  'Ab':     4,
  'Db':     5,
  'Fsharp': 6,
  'B':      7,
  'E':      8,
  'A':      9,
  'D':     10,
  'G':     11,
}

SUFFIX_WEIGHTS = {
  'Maj7':   0,
  'min7':   1,
  '7':      2,
  'min7b5': 3,
  '7b9b13': 4,
  '7b913':  5,
}

# I'd intended to use the proper unicode flat (U+266D) and sharp (U+266F),
# but iTunes doesn't grok them.
ROOT_REWRITES = {
  'C':      'C',
  'F':      'F',
  'Bb':     'Bb',
  'Eb':     'Eb',
  'Ab':     'Ab',
  'Db':     'Db',
  'Fsharp': 'F#',
  'B':      'B',
  'E':      'E',
  'A':      'A',
  'D':      'D',
  'G':      'G',
}

SUFFIX_REWRITES = {
  'Maj7':   'Maj7',
  'min7':   '-7',
  '7':      '7',
  'min7b5': '-7(b5)',
  '7b9b13': '7(b9,b13)',
  '7b913':  '7(b9,13)',
}


def FetchPtcFiles():
  """Scrapes and fetches the list of MP3 files from playingthechanges.com."""
  with contextlib.closing(requests.get('%s/' % PTC_COM)) as index_page:
    mp3_links = re.findall('downloads/.*\.mp3', index_page.text)
  for i, link in enumerate(mp3_links):
    print 'Fetching %2d of %d: %s' % (i + 1, len(mp3_links), link)
    with contextlib.closing(requests.get('%s/%s' % (PTC_COM, link))) as mp3:
      with open(os.path.basename(link), 'wb') as fd:
        for chunk in mp3.iter_content(1<<20):
          fd.write(chunk)


class BadChordFileNameException(Exception):
  """Raised when a chord file name does not match the expected format."""
  pass


def SplitFileName(file_name):
  """Returns the tuple (root, suffix) based on a chord's file name.

  Args:
    file_name: corresponds to a chord file from playingthechanges.com
  Returns:
    a (chord root, chord suffix) tuple
  Raises:
    BadChordFileNameException: if the file does not end with .mp3 or if either
      the chord root or chord suffix does not correspond to an expected value
      within ROOT_WEIGHTS and SUFFIX_WEIGHTS, respectively
  """
  kMp3Suffix = '.mp3'
  if not file_name.endswith(kMp3Suffix):
    raise BadChordFileNameException('Bad chord file name: %s' % file_name)

  suffix_start = 1
  if file_name[1] == 'b':
    suffix_start = 2
  elif file_name.startswith('sharp', 1):
    suffix_start = 6
  root = file_name[:suffix_start]
  suffix = file_name[suffix_start:-len(kMp3Suffix)]

  if root not in ROOT_WEIGHTS:
    raise BadChordFileNameException('Unknown chord root in file name: %s' %
                                    file_name)
  if suffix not in SUFFIX_WEIGHTS:
    raise BadChordFileNameException('Unknown chord suffix in file name: %s' %
                                    file_name)
  return (root, suffix)


def CompareChordFileNames(lhs, rhs):
  """Defines an ordering for split chord file names.

  Suffix order weight trumps root order. Root order is defined by walking the
  circle of fourths up from C. Both are defined in ROOT_WEIGHTS and
  SUFFIX_WEIGHTS.

  Args:
    lhs: left-hand tuple of (root, suffix)
    rhs: right-hand tuple of (root, suffix)
  Returns:
    -1 if lhs < rhs
    0  if lhs == rhs
    1  if lhs > rhs
  """
  return (cmp(SUFFIX_WEIGHTS[lhs[1]], SUFFIX_WEIGHTS[rhs[1]]) or
          cmp(ROOT_WEIGHTS[lhs[0]], ROOT_WEIGHTS[rhs[0]]))
  

def ChordName(file_name):
  """Generates the chord name from the (root, suffix) file name tuple."""
  return u'%s%s' % (ROOT_REWRITES[file_name[0]], SUFFIX_REWRITES[file_name[1]])


def UpdateMp3Tags():
  mp3s = [SplitFileName(i) for i in os.listdir('.') if i.endswith('.mp3')]
  mp3s.sort(CompareChordFileNames)
  for i, mp3 in enumerate(mp3s):
    mp3_file = '%s%s.mp3' % mp3
    print 'Updating: %s' % mp3_file
    command = ['/usr/local/bin/id3tag',
               '--artist=Paul Del Nero',
               '--album=Playing the Changes',
               '--song=%s' % ChordName(mp3),
               '--track=%d' % (i + 1),
               '--total=%d' % len(mp3s),
               mp3_file]
    return_code = subprocess.call(command)
    if return_code:
      print >> sys.stderr, ('Error updating %s (return code %d) with '
          'command: %s' % (mp3_file, return_code, ' '.join(command)))
      sys.exit(return_code)
  print "Updated %d mp3%s" % (len(mp3s), len(mp3s) != 1 and 's' or '')


if __name__ == '__main__':
  FetchPtcFiles()
  UpdateMp3Tags()
