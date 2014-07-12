#! /usr/bin/python2.7
# coding=UTF-8
"""
Automates updates to OpenSSL Makefiles.

Each automated change is incremental and idempotent; running the script more
than once will not produce any changes after the first run.

The changes generated by this script are part of the OpenSSL build system
refactoring described in:

  http://mike-bland.com/2014/06/26/makefile-refactoring.html

The changes are posted in the 'makefiles' branch of the mbland/openssl fork:

  https://github.com/mbland/openssl/commits/makefiles

This code is published at:

https://code.google.com/p/mike-bland/source/browse/openssl/update_makefiles.py

Author:  Mike Bland (mbland@acm.org)
         http://mike-bland.com/
Date:    2014-06-21
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
  """Defines SRC in Makefiles that currently don't have it.

  This only affected one file (crypto/jpake/Makefile), was worth automating
  anyway to make sure SRC was defined everywhere. It will be used to by future
  Makefile changes to include the appropriate .d files, which will are
  autogenerated by the compiler.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
  """
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
  """Ensures that .d files are removed as part of 'make clean'.

  .d files are autogenerated by the compiler when the -MMD and -MP flags are
  supported on the development platform. They are supported by recent versions
  of gcc and clang, and are far more efficient and reliable than the previous
  'makedepend'-based scheme, as discussed in:

  http://marc.info/?t=140420825100001&r=1&w=2
  https://groups.google.com/forum/#!topic/mailing.openssl.dev/m9XDCpmzWAg

  Args:
    infile: Makefile to read
    outfile: Makefile to write
  """
  CLEAN_OBJ_PATTERN = re.compile('rm .* \*\.o ')
  for line in infile:
    if CLEAN_OBJ_PATTERN.search(line) and line.find(' *.d ') == -1:
      print '%s: Adding .d files to "clean" target' % infile.name
      line = line.replace(' *.o ', ' *.o *.d ', 1)
      line = line.replace(' */*.o ', ' */*.o */*.d ', 1)
    print >>outfile, line,


def CreateNewMakefile(dirname, makefile_name, content):
  """Creates a new Makefile containing the file name and TOP variable.

  Args:
    dirname: directory into which the new Makefile will be written
    makefile_name: filename of the new Makefile
    content: string containing the Makefile content, which must contain two
      %s placeholders for (dirname/makefile_name, TOP)
  """
  TOP_PATTERN = re.compile('[^.%s]+' % os.path.sep)
  makefile_path = os.path.join(dirname, makefile_name)

  if not os.path.exists(makefile_path):
    print '%s: created' % makefile_path
    with open(makefile_path, 'w') as makefile:
      print >>makefile, content % (
          makefile_path, TOP_PATTERN.sub('..', dirname))


def CreateGnuMakefile(dirname):
  """Generates a new GNUmakefile.

  Since the current recursive make structure supports both GNU and BSD make,
  yet the syntax for the "include" directive is different between the two, we
  need to generate both a GNUmakefile and a BSDmakefile for each existing
  Makefile to include configure.mk and the .d files. When the changes are in
  place to switch to a single top-level {GNU,BSD}makefile, these intermediate
  {GNU,BSD}makefiles can go away.

  Args:
    dirname: directory into which the new GNUmakefile will be written
  """
  CreateNewMakefile(dirname, 'GNUmakefile',
'''#
# OpenSSL/%s
#

TOP= %s
include $(TOP)/configure.mk
include Makefile
-include $(SRC:.c=.d)''')


def CreateBsdMakefile(dirname):
  """Generates a new BSDmakefile.

  See the docstring for CreateGnuMakefile() for more details.

  Args:
    dirname: directory into which the new BSDmakefile will be written
  """
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
  """Add TOP to the recipe for the 'make files' target.

  Since TOP is now defined in {GNU,BSD}makefile, it needs to be passed
  explicitly to util/files.pl. The alternative would be to pass one of the
  {GNU,BSD}makefiles as an argument to util/files.pl, but that seems like
  overkill.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
  """
  FILES_SCRIPT = 'util/files.pl'
  UPDATE = '%s %s' % (FILES_SCRIPT, 'TOP=$(TOP)')
  for line in infile:
    if line.find(FILES_SCRIPT) != -1 and line.find(UPDATE) == -1:
      print '%s: Adding TOP as argument to files.pl' % infile.name
      line = line.replace(FILES_SCRIPT, UPDATE)
    print >>outfile, line,


def ReadConfigureVars(config_filename):
  """Reads the top-level variable definitions from config_filename.

  Args:
    config_filename: path to configure.mk (presumably)
  """
  config_vars = {}
  with open(config_filename, 'r') as config_file:
    for line in config_file:
      m = CONFIG_VAR_PATTERN.match(line)
      if m:
        config_vars[m.group(1)] = 1
  return config_vars


def Continues(line):
  """Returns True if the next line is a continuation of line."""
  return line.endswith('\\\n')


def RemoveConfigureVars(infile, outfile):
  """Strips definitions from infile that appear in configure.mk.

  ReadConfigureVars() needs to have been called and its results stored in
  CONFIG_VARS first. The variables defined in configure.mk will be stripped
  from all of the Makefiles, since configure.mk is included first in the
  {GNU,BSD}makefiles.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
  """
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
  """Trims the previous output from makedepend from the end of a makefile.

  See the docstring for AddDependencyFilesToCleanTargets() for more details on
  the generation of .d files, which are now used to replace the earlier
  'makedepend' output.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
  """
  for line in infile:
    if line == MAKE_DEPEND_LINE:
      print '%s: Removing "make depend" output' % infile.name
      return
    print >>outfile, line,


def RemoveDependTarget(infile, outfile):
  """Strip the depend target from all Makefiles.

  See the docstring for AddDependencyFilesToCleanTargets() for more details on
  the generation of .d files, which are now used to replace the earlier
  'makedepend' output.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
  """
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
  """Feeds configure.mk and Makefile.shared into the standard input of make.

  For now, the recursive make used to build shared libraries will remain in
  place. However, there's no clean and easy way to include configure.mk in
  Makefile.shared, given the current need to remain compatible with both GNU
  and BSD make, which have incompatible syntaxes for including other
  Makefiles. Both GNU and BSD make do support reading the input Makefile from
  standard input, so concatenating configure.mk and Makefile.shared to
  standard input achieves the same effect as an include directive.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
  """
  PATTERN = '$(MAKE) -f $(TOP)/Makefile.shared -e'
  NEW = 'cat $(TOP)/configure.mk $(TOP)/Makefile.shared | $(MAKE) -f -'
  for line in infile:
    if line.find(PATTERN) != -1:
      print '%s: Replacing Makefile.shared command' % infile.name
      line = line.replace(PATTERN, NEW)
    print >>outfile, line,


def UpdateFile(orig_name, update_func):
  """Applies update_func() to a Makefile.

  update_func() takes two arguments:
    infile: the Makefile to read
    outfile: the Makefile to write

  If update_func() finishes successfully (i.e. raises no exceptions), the
  original Makefile will be overwritten by the updated version.

  Args:
    orig_name: path to the Makefile to update
    update_func: function to transform the Makefile content
  """
  updated_name = '%s.updated' % orig_name
  with open(orig_name, 'r') as orig:
    with open(updated_name, 'w') as updated:
      update_func(orig, updated)
  os.rename(updated_name, orig_name)


def UpdateMakefiles(unused_arg, dirname, fnames):
  """Applies a series of updates to dirname/Makefile (if it exists).

  Passed to os.path.walk() to process all the Makefiles in the OpenSSL source
  tree.

  Args:
    unused_arg: ignored; required by the os.path.walk() interface
    dirname: current directory path
    fnames: list of contents in the current directory
  """
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


def ReplaceMakefileToken(s, orig_token, new_token):
  """Replaces instances in s of orig_token with new_token.

  Intended to process Make variable assignment expressions, variable
  definitions, target names, target prerequisites, and target recipes.
  Takes care to replace only instances of orig_token that correspond to
  full tokens, rather than substrings of larger tokens.

  Args:
    s: string to process
    orig_token: the original token to replace
    new_token: the replacement token
  Returns:
    s with every instance of orig_token replaced by new_token
  """
  SHELL_VAR_PREFIX = '$${'
  SVP_LEN = len(SHELL_VAR_PREFIX)
  l = []
  i = s.find(orig_token)
  begin_unreplaced_segment = 0
  while i != -1:
    end_token = i + len(orig_token)
    if ((i == 0 or s[i - 1] in '({ ') and s[end_token] in ' :=})' and
         (i < SVP_LEN or s[i - SVP_LEN:i] != SHELL_VAR_PREFIX)):
      if i != begin_unreplaced_segment:
        l.append(s[begin_unreplaced_segment:i])
      l.append(new_token)
      begin_unreplaced_segment = end_token
    i = s.find(orig_token, end_token)
  if begin_unreplaced_segment != len(s):
    l.append(s[begin_unreplaced_segment:])
  return ''.join(l)


class Makefile(object):
  """Representation of all of the variables and targets in a Makefile.

  Instances of this type are produced by CollectVarsAndTargets().

  Attributes:
    makefile: path to the Makefile
    variables: hash of variable name => Variable
    targets: a hash of target name => Target
  """

  class Variable(object):
    """Representation of a Makefile variable.

    Attributes:
      name: variable name
      definition: string containing the variable contents/definition
    """
    def __init__(self, name, definition):
      self.name = name
      self.definition = definition

  class Target(object):
    """Representation of a Makefile target.

    Attributes:
      name: target name
      prerequisites: string containing the names of targets and variables that
        are a prerequisite of the target
      recipe: string containing the commands used to build the target
    """
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
    """Adds a new Variable to the Makefile.

    Args:
      name: variable name
      definition: string containing the variable contents/definition
    Raises:
      AssertionError: if a variable is duplicated in a Makefile, i.e. if name
        is already present in self.variables
    """
    assert name not in self.variables, '%s: %s' % (self.makefile, name)
    self.variables[name] = Makefile.Variable(name, definition)

  def add_target(self, name, prerequisites, recipe):
    """Adds a new Target to the Makefile.

    Args:
      name: target name
      prerequisites: string containing the names of targets and variables that
        are a prerequisite of the target
      recipe: string containing the commands used to build the target
    Raises:
      AssertionError: if a target contains more than one recipe, i.e. if the
        a recipe is defined for both the existing target object and the new
        target
    """
    if name not in self.targets:
      self.targets[name] = Makefile.Target(name, prerequisites, recipe)
    else:
      target = self.targets[name]
      target.prerequisites = '%s %s' % (target.prerequisites, prerequisites)
      assert not (target.recipe and recipe), (
          '%s: duplicate recipes for %s' % (self.makefile, target))


def CollectVarsAndTargets(makefile_path, makefiles):
  """Parses a Makefile object from a Makefile.

  The result is stored as makefiles[makefile_path].

  Args:
    makefile_path: path to the Makefile to parse
    makefiles: hash of makefile_path -> Makefile
  """
  makefile = Makefile(makefile_path)
  with open(makefile_path, 'r') as infile:
    var_name = None
    definition = None
    target_name = None
    prerequisites = None
    recipe = None

    for line in infile:
      if var_name is not None:
        definition.append(line)
        if not Continues(line):
          makefile.add_var(var_name, ''.join(definition))
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
        makefile.add_target(target_name, prerequisites, ''.join(recipe))
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
          makefile.add_var(var_name, definition)
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

  makefiles[makefile_path] = makefile


def CollectVarsAndTargetsRecursive(makefiles, dirname, fnames):
  """Applies CollectVarsAndTargets() to dirname/Makefile (if it exists).

  Passed to os.path.walk() to process all the Makefiles in the OpenSSL source
  tree.

  Args:
    makefiles: hash of makefile_path -> Makefile; accumulates the results
    dirname: current directory path
    fnames: list of contents in the current directory
  """
  if 'Makefile' not in fnames: return
  CollectVarsAndTargets(os.path.join(dirname, 'Makefile'), makefiles)


def MapVarsAndTargetsToFiles(makefiles, all_vars, all_targets):
  """Transforms a set of Makefile objects to hashes of variables and targets.

  Results are accumulated in all_vars and all_targets.

  Args:
    makefiles: a hash of makefile path -> Makefile instance
    all_vars: a hash of variable name -> [(makefile path, definition)]
    all_targets: a hash of target name -> [(makefile path, prereqs, recipe)]
  """
  for mf in makefiles:
    for v in makefiles[mf].variables.values():
      if v.name not in all_vars:
        all_vars[v.name] = [(mf, v.definition)]
      else:
        all_vars[v.name].append((mf, v.definition))
    for t in makefiles[mf].targets.values():
      if t.name not in all_targets:
        all_targets[t.name] = [(mf, t.prerequisites, t.recipe)]
      else:
        all_targets[t.name].append((mf, t.prerequisites, t.recipe))


def PrintVarsAndTargets(items, preamble, common_only=False):
  """Prints a map of variable or target names to Makefiles and values.

  Output goes to standard output. For variable names, the variable defintions
  are printed. For target names, the prerequisites are printed.

  Args:
    items: hash of {variable or target name} -> [(makefile path, value)]
    preamble: a string to print before the variable or target information
    common_only: if True, only print objects appearing in more than one
      Makefile
  """
  if common_only:
    flattened = [i for i in items.items() if len(i[1]) != 1]
  else:
    flattened = [i for i in items.items()]

  def Cmp(lhs, rhs):
    """Used to sort by decreasing number of Makefiles and increasing name."""
    return -cmp(len(lhs[1]), len(rhs[1])) or cmp(lhs[0], rhs[0])
  flattened.sort(cmp=Cmp)

  print preamble
  print "%d items" % len(flattened)
  for i in flattened:
    print '%s: %s files' % (i[0], len(i[1]))
    for f in i[1]:
      print '  %s: %s' % (f[0], f[1]),


class MakefileInfo(object):
  """Contains all the Makefile information for the entire project.

  Attributes:
    top_makefiles: hash of makefile_path -> top-level Makefile objects
    top_vars: hash of vars -> [(top-level path, definition)]
    top_targets: hash of targets -> [(top-level path, prereqs, recipe)]
    all_makefiles: hash of makefile_path -> all Makefile objects
    all_vars: hash of vars -> [(makefile path, definition)]
    all_targets: hash of targets -> [(makefile path, prereqs, recipe)]
  """

  def __init__(self):
    self.top_makefiles = {}
    self.top_vars = {}
    self.top_targets = {}
    self.all_makefiles = {}
    self.all_vars = {}
    self.all_targets = {}

  def Init(self):
    """Parses the Makefiles and populates the attribute hashes."""
    CollectVarsAndTargets('configure.mk', self.top_makefiles)
    CollectVarsAndTargets('Makefile', self.top_makefiles)
    self.all_makefiles.update(self.top_makefiles)

    for d in os.listdir('.'):
      if os.path.isdir(d):
        os.path.walk(d, CollectVarsAndTargetsRecursive, self.all_makefiles)

    MapVarsAndTargetsToFiles(
        self.top_makefiles, self.top_vars, self.top_targets)
    MapVarsAndTargetsToFiles(
        self.all_makefiles, self.all_vars, self.all_targets)

  def PrintCommonVarsAndTargets(self):
    """Prints top-level vars and targets, then those in multiple files.

    See the docstring for PrintVarsAndTargets() for more details.
    """
    PrintVarsAndTargets(self.top_vars, '*** TOP-LEVEL VARS ***')
    PrintVarsAndTargets(self.top_targets, '*** TOP-LEVEL TARGETS ***')
    PrintVarsAndTargets(self.all_vars, '*** VARS ***', common_only=True)
    PrintVarsAndTargets(self.all_targets, '*** TARGETS ***', common_only=True)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--print_common',
        help='Print common targets and vars; skip updates',
        action='store_true')
  args = parser.parse_args()

  if args.print_common:
    info = MakefileInfo()
    info.Init()
    info.PrintCommonVarsAndTargets()
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
