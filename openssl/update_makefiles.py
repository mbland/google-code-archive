#! /usr/bin/python
# coding=UTF-8
"""
Automates updates to OpenSSL Makefiles.

Author: Mike Bland (mbland@acm.org)
        http://mike-bland.com/
Date:   2014-06-21
License: Creative Commons Attribution 4.0 International (CC By 4.0)
         http://creativecommons.org/licenses/by/4.0/deed.en_US
"""

import os
import os.path
import re
import shutil

BUILD_FILE_NAME = 'build.mk'


def UpdateFile(orig_name, update_func):
  updated_name = '%s.updated' % orig_name
  with open(orig_name, 'r') as orig:
    with open(updated_name, 'w') as updated:
      update_func(orig, updated)
  os.rename(updated_name, orig_name)


def UpdateMakefiles(arg, dirname, fnames):
  if 'Makefile' not in fnames: return
  has_build_file = BUILD_FILE_NAME in fnames

  makefile_name = os.path.join(dirname, 'Makefile')
  build_mk_name = os.path.join(dirname, BUILD_FILE_NAME)
  add_deps_name = has_build_file and build_mk_name or makefile_name


if __name__ == '__main__':
  for d in os.listdir('.'):
    if os.path.isdir(d):
      os.path.walk(d, UpdateMakefiles, None)
