#! /usr/bin/python2.7
# coding=UTF-8
"""
Automates updates to OpenSSL Makefiles.

Author: Mike Bland (mbland@acm.org)
        http://mike-bland.com/
Date:   2014-06-21
License: Creative Commons Attribution 4.0 International (CC By 4.0)
         http://creativecommons.org/licenses/by/4.0/deed.en_US
"""

import argparse
import os
import os.path
import re
import shutil
import sys

MAKE_DEPEND_LINE = '# DO NOT DELETE THIS LINE -- make depend depends on it.\n'
CONFIG_VAR_PATTERN = re.compile('([^# \t=]+) *=')
CONFIG_VARS = {}
TARGET_PATTERN = re.compile('([^#\t=]+):')


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


def AddTopToFilesTarget(infile, outfile):
  FILES_SCRIPT = 'util/files.pl'
  UPDATE = '%s %s' % (FILES_SCRIPT, 'TOP=$(TOP)')
  for line in infile:
    if line.find(FILES_SCRIPT) != -1 and line.find(UPDATE) == -1:
      print '%s: Adding TOP as argument to files.pl' % infile.name
      line = line.replace(FILES_SCRIPT, UPDATE)
    print >>outfile, line,


def ReadConfigureVars(config_filename):
  config_vars = {}
  with open(config_filename, 'r') as config_file:
    for line in config_file:
      m = CONFIG_VAR_PATTERN.match(line)
      if m:
        config_vars[m.group(1)] = 1
  return config_vars


def Continues(line):
  return line.endswith('\\\n')


def RemoveConfigureVars(infile, outfile):
  skip_next_line = False
  for line in infile:
    m = CONFIG_VAR_PATTERN.match(line)
    if (m and m.group(1) in CONFIG_VARS) or skip_next_line:
      if not skip_next_line:
        print '%s: Removing variable %s' % (infile.name, m.group(1))
      skip_next_line = Continues(line)
    else:
      print >>outfile, line,


def RemoveOldMakeDependOutput(infile, outfile):
  for line in infile:
    if line == MAKE_DEPEND_LINE:
      print '%s: Removing "make depend" output' % infile.name
      return
    print >>outfile, line,


def RemoveDependTarget(infile, outfile):
  removing_target = False
  for line in infile:
    if removing_target:
      if line.startswith('\t') or line == '\n':
        continue
      removing_target = False
    elif line.startswith('depend:'):
      print '%s: Removing "make depend" target' % infile.name
      removing_target = True
      continue
    print >>outfile, line,


def CatConfigureAndMakefileShared(infile, outfile):
  PATTERN = '$(MAKE) -f $(TOP)/Makefile.shared -e'
  NEW = 'cat $(TOP)/configure.mk $(TOP)/Makefile.shared | $(MAKE) -f -'
  for line in infile:
    if line.find(PATTERN) != -1:
      print '%s: Replacing Makefile.shared command' % infile.name
      line = line.replace(PATTERN, NEW)
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
  UpdateFile(makefile_name, AddTopToFilesTarget)
  UpdateFile(makefile_name, RemoveConfigureVars)
  UpdateFile(makefile_name, RemoveOldMakeDependOutput)
  UpdateFile(makefile_name, RemoveDependTarget)
  UpdateFile(makefile_name, CatConfigureAndMakefileShared)


class MakefileObjects(object):
  class Variable(object):
    def __init__(self, name, definition):
      self.name = name
      self.definition = definition


  class Target(object):
    def __init__(self, name, prerequisites, recipe):
      self.name = name
      self.prerequisites = prerequisites
      self.recipe = recipe


  def __init__(self, makefile):
    self.makefile = makefile
    self._suffix = '_%s' % os.path.dirname(makefile).replace(os.path.sep, '_')
    self.variables = {}
    self.targets = {}

  def __str__(self):
    variable_names = self.variables.keys()
    variable_names.sort()
    target_names = self.targets.keys()
    target_names.sort()
    return '%s:\n  vars:\n    %s\n  targets:\n    %s' % (
        self.makefile,
        '\n    '.join(variable_names), '\n    '.join(target_names))

  def add_var(self, name, definition):
    assert name not in self.variables, '%s: %s' % (self.makefile, name)
    self.variables[name] = MakefileObjects.Variable(name, definition)

  def add_target(self, name, prerequisites, recipe):
    if name not in self.targets:
      self.targets[name] = MakefileObjects.Target(name, prerequisites, recipe)
    else:
      target = self.targets[name]
      target.prerequisites = '%s %s' % (target.prerequisites, prerequisites)
      assert not (target.recipe and recipe), (
          '%s: duplicate recipes for %s' % (self.makefile, target))


def CollectVarsAndTargets(makefile_path, all_objects):
  objects = MakefileObjects(makefile_path)
  with open(makefile_path, 'r') as makefile:
    var_name = None
    definition = None
    target_name = None
    prerequisites = None
    recipe = None

    for line in makefile:
      if var_name is not None:
        definition.append(line)
        if not Continues(line):
          objects.add_var(var_name, ''.join(definition))
          var_name = None
          definition_name = None
        continue

      if target_name is not None:
        if recipe is None:
          prerequisites.append(line)
          if not Continues(line):
            prerequisites = ''.join(prerequisites)
            recipe = []
          continue

        if line.startswith('\t'):
          recipe.append(line)
          continue
        objects.add_target(target_name, prerequisites, ''.join(recipe))
        target_name = None
        prerequisites = None
        recipe = None

      config_match = CONFIG_VAR_PATTERN.match(line)
      target_match = TARGET_PATTERN.match(line)
      assert not (config_match and target_match), (
        '%s: %s\n  var: %s\n  target:%s' %
        (makefile.name, line, config_match.group(1), target_match.group(1)))

      if config_match:
        var_name = config_match.group(1)
        definition = line[config_match.end():]
        if not Continues(line):
          objects.add_var(var_name, definition)
          var_name = None
          definition = None
        else:
          definition = [definition]

      elif target_match:
        target_name = target_match.group(1)
        if target_name.endswith('.o'):
          target_name = None
          continue
        prerequisites = line[target_match.end():]
        if not Continues(line):
          recipe = []
        else:
          prerequisites = [prerequisites]

  all_objects[makefile_path] = objects


def CollectVarsAndTargetsRecursive(arg, dirname, fnames):
  if 'Makefile' not in fnames: return
  CollectVarsAndTargets(os.path.join(dirname, 'Makefile'), arg)


def MapVarsAndTargetsToFiles(makefile_objects, all_vars, all_targets):
  for mf in makefile_objects:
    for v in makefile_objects[mf].variables.values():
      all_vars[v.name] = (mf, v.definition)
    for t in makefile_objects[mf].targets.values():
      all_targets[t.name] = (mf, t.prerequisites, t.recipe)


def PrintCommonItems(items, preamble):
  flattened = [i for i in items.items() if len(i[1]) != 1]
  def Cmp(lhs, rhs):
    return cmp(len(lhs[1]), len(rhs[1]))
  flattened.sort(cmp=Cmp, reverse=True)

  print preamble
  print "%d items" % len(flattened)
  for i in flattened:
    print '%s: %s files' % (i[0], len(i[1]))
    for f in i[1]:
      print '  %s: %s' % (f[0], f[1])


def PrintCommonVarsAndTargets():
  top_objects = {}
  CollectVarsAndTargets('configure.mk', top_objects)
  CollectVarsAndTargets('Makefile', top_objects)
  top_vars = {}
  top_targets = {}
  MapVarsAndTargetsToFiles(top_objects, top_vars, top_targets)
  print '*** TOP-LEVEL VARS ***'
  for i in top_vars: print i
  print '*** TOP-LEVEL TARGETS ***'
  for i in top_targets: print i

  all_objects = {}
  all_vars = {}
  all_targets = {}
  all_objects.update(top_objects)
  all_vars.update(top_vars)
  all_targets.update(top_targets)
  for d in os.listdir('.'):
      if os.path.isdir(d):
        os.path.walk(d, CollectVarsAndTargetsRecursive, all_objects)

  MapVarsAndTargetsToFiles(all_objects, all_vars, all_targets)
  PrintCommonItems(all_vars, '*** VARS ***')
  PrintCommonItems(all_targets, '*** TARGETS ***')


def MapFilesToCommonVarsAndTargets(all_vars, all_targets):
  files = {}
  for i in all_vars.items:
    if i[1] in files:
      files[i[1]].add_var(i[0])
    else:
      files[i[1]] = MakefileObjects(i[1], variable=i[0])


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--common',
        help='Print common targets and vars; skip updates',
        action='store_true')
  args = parser.parse_args()

  if args.common:
    PrintCommonVarsAndTargets()
    sys.exit(0)

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
  UpdateFile('Makefile.shared', RemoveConfigureVars)

  # TODO: Strip remaining top-level vars from Makefiles when lower-level
  # Makefiles are included from the top-level.
