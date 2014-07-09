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
CONFIG_VAR_PATTERN = re.compile('([^ \t=]+) *=')
CONFIG_VARS = {}


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


def AddDependencyFilesToCleanTargets(infile, outfile):
  CLEAN_OBJ_PATTERN = re.compile('rm .* \*\.o ')
  for line in infile:
    if CLEAN_OBJ_PATTERN.search(line) and line.find(' *.d ') == -1:
      print '%s: Adding .d files to "clean" target' % infile.name
      line = line.replace(' *.o ', ' *.o *.d ', 1)
      line = line.replace(' */*.o ', ' */*.o */*.d ', 1)
    print >>outfile, line,


def CreateNewMakefile(dirname, makefile_name, content):
  TOP_PATTERN = re.compile('[^.%s]+' % os.path.sep)
  makefile_path = os.path.join(dirname, makefile_name)

  if not os.path.exists(makefile_path):
    print '%s: created' % makefile_path
    with open(makefile_path, 'w') as makefile:
      print >>makefile, content % (
          makefile_path, TOP_PATTERN.sub('..', dirname))


def CreateGnuMakefile(dirname):
  CreateNewMakefile(dirname, 'GNUmakefile',
'''#
# OpenSSL/%s
#

TOP= %s
include $(TOP)/configure.mk
include Makefile
-include $(SRC:.c=.d)''')


def CreateBsdMakefile(dirname):
  CreateNewMakefile(dirname, 'BSDmakefile',
'''#
# OpenSSL/%s
#

TOP= %s
.include "$(TOP)/configure.mk"
.include "Makefile"
.for d in $(SRC:.c=.d)
.sinclude "$(d)"
.endfor''')


def ReadConfigureVars(config_filename):
  config_vars = {}
  with open(config_filename, 'r') as config_file:
    for line in config_file:
      m = CONFIG_VAR_PATTERN.match(line)
      if m:
        config_vars[m.group(1)] = 1
  return config_vars


def RemoveConfigureVars(infile, outfile):
  skip_next_line = False
  for line in infile:
    m = CONFIG_VAR_PATTERN.match(line)
    if (m and m.group(1) in CONFIG_VARS) or skip_next_line:
      if not skip_next_line:
        print '%s: Removing variable %s' % (infile.name, m.group(1))
      skip_next_line = line.endswith('\\\n')
    else:
      print >>outfile, line,


def RemoveOldMakeDependOutput(infile, outfile):
  for line in infile:
    if line == MAKE_DEPEND_LINE:
      print '%s: Removing "make depend" output' % infile.name
      return
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
  UpdateFile(makefile_name, AddDependencyFilesToCleanTargets)
  CreateGnuMakefile(dirname)
  CreateBsdMakefile(dirname)
  UpdateFile(makefile_name, RemoveConfigureVars)
  UpdateFile(makefile_name, RemoveOldMakeDependOutput)


if __name__ == '__main__':
  # Read the top-level configure file, if it exists.
  if os.path.exists('configure.mk.org'):
    CONFIG_VARS = ReadConfigureVars('configure.mk.org')
    # Adding TOP since it's defined in each Makefile
    CONFIG_VARS['TOP'] = 1
    # MAKEDEPEND is on its way out, too.
    CONFIG_VARS['MAKEDEPEND'] = 1

  for d in os.listdir('.'):
    if os.path.isdir(d):
      os.path.walk(d, UpdateMakefiles, None)

  CreateGnuMakefile('.')
  CreateBsdMakefile('.')
  UpdateFile('Makefile.org', RemoveConfigureVars)
  UpdateFile('Makefile.fips', RemoveConfigureVars)
