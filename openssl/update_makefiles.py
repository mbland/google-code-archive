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

MAKE_DEPEND_LINE = '# DO NOT DELETE THIS LINE -- make depend depends on it.\n'


def AddSrcVarIfNeeded(infile, outfile):
  src_var = None
  for line in infile:
    if line.startswith('LIBSRC=') and not src_var:
      src_var = 'LIBSRC'
    elif line.startswith('SRC='):
      src_var = 'SRC'
    if line == MAKE_DEPEND_LINE:
      if src_var is not None and src_var != 'SRC':
        print '%s: Adding SRC variable' % infile.name
        print >>outfile, 'SRC= $(%s)' % src_var
    print >>outfile, line,


def UpdateFile(orig_name, update_func):
  updated_name = '%s.updated' % orig_name
  with open(orig_name, 'r') as orig:
    with open(updated_name, 'w') as updated:
      update_func(orig, updated)
  os.rename(updated_name, orig_name)


def UpdateMakefiles(arg, dirname, fnames):
  if 'Makefile' not in fnames: return
  makefile_name = os.path.join(dirname, 'Makefile')

  UpdateFile(makefile_name, AddSrcVarIfNeeded)


if __name__ == '__main__':
  for d in os.listdir('.'):
    if os.path.isdir(d):
      os.path.walk(d, UpdateMakefiles, None)
