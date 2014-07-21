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
VAR_DEFINITION_PATTERN = re.compile('([^# \t=]+) *=')
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
  TOP_ARG = '%s %s' % (FILES_SCRIPT, 'TOP=$(TOP')
  UPDATE = '%s)' % TOP_ARG
  for line in infile:
    if line.find(FILES_SCRIPT) != -1 and line.find(TOP_ARG) == -1:
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
      m = VAR_DEFINITION_PATTERN.match(line)
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
    m = VAR_DEFINITION_PATTERN.match(line)
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


def UpdateMakefilesStage0(unused_arg, dirname, fnames):
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


def SplitPreservingWhitespace(s):
  """Splits s into both its whitespace and nonwhitespace components.

  Used instead of split() to ensure that directory name replacement doesn't
  alter indentation and other whitespace features.

  Args:
    s: string to split
  Returns:
    a list of strings containing all-whitespace and all-nonwhitespace tokens
      from s
  """
  current = []
  result = []
  SPACE = ' \t\n\x0b\x0c\r'
  parse_space = s and s[0] in SPACE
  for i, c in enumerate(s):
    if parse_space:
      if c not in SPACE:
        result.append(''.join(current))
        current = []
        parse_space = False
    else:
      if c in SPACE:
        result.append(''.join(current))
        current = []
        parse_space = True
    current.append(c)
  if current:
    result.append(''.join(current))
  return result


def NormalizeRelativeDirectory(value, prefix, makefile_path):
  """Updates value with relative directory paths normalized to the top dir.

  Args:
    value: string to normalize
    prefix: the prefix to strip from value before examining the rest of value
    makefile_path: the Makefile containing value, relative to the top dir
  Returns:
    a copy of value with any relative path values normalized relative to the
      top dir
  """
  TOP = '$(TOP'
  s = value[len(prefix):]
  makefile_dir = os.path.dirname(makefile_path)
  if s.startswith(TOP):
    i = s.find(')', len(TOP))
    assert i != -1, '%s: incomplete TOP variable: %s' % (makefile_path, value)
    s = s[i + 1:]
    if s:
      assert s[0] == os.path.sep, '%s: malformed TOP variable: %s' % (
          makefile_path, value)
      s = s[1:]
    return '%s%s' % (prefix, os.path.normpath(os.path.join('.', s)))
  elif s.startswith('.'):
    return '%s%s' % (prefix, os.path.normpath(os.path.join(makefile_dir, s)))
  return value


class Makefile(object):
  """Representation of all of the variables and targets in a Makefile.

  Instances of this type are produced by ParseMakefile().

  Attributes:
    makefile: path to the Makefile
    variables: hash of variable name => Variable
    targets: a hash of target name => Target
    common_vars: names of variables that also appear in other Makefiles
    common_targets: names of targets that also appear in other Makefiles
    top_vars: names of variables that also appear in top-level Makefiles
    top_targets: names of targets that also appear in top-level Makefiles
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
    mfdir = os.path.dirname(makefile)
    self.suffix = mfdir and '_%s' % mfdir.replace(os.path.sep, '_') or ''
    self.variables = {}
    self.targets = {}
    # We need to update TOP and SRC everywhere, including the
    # {GNU,BSD}makefiles.
    self.common_vars = set(['TOP', 'SRC'])
    self.common_targets = set()
    self.top_vars = set()
    self.top_targets = set()

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

  def LocalTargetMap(self):
    """Returns a hash of target name -> local name for self.common_targets.

    Omits targets that are defined in terms of variables and suffix targets.
    """
    targets = {}
    for t in self.common_targets:
      if t[0] != '.' and '$' not in t:
        targets[t] = '%s%s' % (t, self.suffix)
    return targets

  def LocalVariableMap(self):
    """Returns a hash of var name -> local name for self.common_vars."""
    variables = {}
    for v in self.common_vars:
      variables[v] = '%s%s' % (v, self.suffix)
    return variables

  def UpdateVariableWithDirectoryName(self, variable):
    """Returns a new variable definition based on the Makefile's directory.

    Args:
      variable: the variable to update
    Returns:
      a string containing an updated definition for variable where the
        Makefile's directory has been injected everywhere it needs to be
      None if no replacement was made
    """
    # Try the version without the suffix, too, in case the script is being run
    # against a fresh working copy.
    if variable not in self.variables:
      assert variable.endswith(self.suffix), '%s: unknown variable: %s' % (
        self.makefile, variable)
      variable = variable[:-len(self.suffix)]
    assert variable in self.variables, '%s: unknown variable: %s' % (
      self.makefile, variable)
    v = self.variables[variable]
    if not v.definition:
      return None

    rel_dirs = []
    mfdir = os.path.dirname(self.makefile)

    if variable.startswith('INCLUDE') and (
      '-I..' in v.definition or '-I$(TOP' in v.definition):
      # In {crypto, fips}/Makefile, the INCLUDES_ version is passed to
      # subdirectories.
      if mfdir in ('crypto', 'fips') and variable.startswith('INCLUDES'):
        mfdir = os.path.join(mfdir, 'dummy')

      for i, s in enumerate(values):
        values[i] = NormalizeRelativeDirectory(s, '-I',
            os.path.join(mfdir, mfname))
      return ''.join(values)

    # TODO: finish implementing
    return None


  def UpdateTargetWithDirectoryName(self, target):
    """Returns a new target definition based on the Makefile's directory.

    Args:
      target: the target to update
    Returns:
      a Target object with an updated definition where the Makefile's
        directory has been injected everywhere it needs to be
      None if no replacement was made
    """
    # Try the version without the suffix, too, in case the script is being run
    # against a fresh working copy.
    if target not in self.targets:
      assert target.endswith(self.suffix), '%s: unknown target: %s' % (
      self.makefile, target)
      target = target[:-len(self.suffix)]
    assert target in self.targets, '%s: unknown target: %s' % (
      self.makefile, target)
    t = self.targets[target]
    mfdir = os.path.dirname(self.makefile)
    # TODO: implement
    return None


def ParseMakefile(makefile_path, makefiles):
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

      var_match = VAR_DEFINITION_PATTERN.match(line)
      target_match = TARGET_PATTERN.match(line)
      assert not (var_match and target_match), (
        '%s: %s\n  var: %s\n  target:%s' %
        (makefile.name, line, var_match.group(1), target_match.group(1)))

      if var_match:
        var_name = var_match.group(1)
        definition = line[var_match.end():]
        if not Continues(line):
          makefile.add_var(var_name, definition)
          var_name = None
          definition = None
        else:
          definition = [definition]

      elif target_match:
        target_name = target_match.group(1)
        prerequisites = line[target_match.end():]
        if not Continues(line):
          recipe = []
        else:
          prerequisites = [prerequisites]

  if recipe is not None:
    makefile.add_target(target_name, prerequisites, ''.join(recipe))
  makefiles[makefile_path] = makefile


def ParseMakefileRecursive(makefiles, dirname, fnames):
  """Applies ParseMakefile() to dirname/Makefile (if it exists).

  Passed to os.path.walk() to process all the Makefiles in the OpenSSL source
  tree.

  Args:
    makefiles: hash of makefile_path -> Makefile; accumulates the results
    dirname: current directory path
    fnames: list of contents in the current directory
  """
  if 'Makefile' not in fnames: return
  ParseMakefile(os.path.join(dirname, 'Makefile'), makefiles)


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
    ParseMakefile('configure.mk.org', self.top_makefiles)
    ParseMakefile('Makefile', self.top_makefiles)
    self.all_makefiles.update(self.top_makefiles)

    for d in os.listdir('.'):
      if os.path.isdir(d):
        os.path.walk(d, ParseMakefileRecursive, self.all_makefiles)

    MapVarsAndTargetsToFiles(
        self.top_makefiles, self.top_vars, self.top_targets)
    MapVarsAndTargetsToFiles(
        self.all_makefiles, self.all_vars, self.all_targets)

    for m in self.all_makefiles.values():
      m.top_targets.update([t for t in m.targets if t in self.top_targets])
      m.top_vars.update([v for v in m.variables if v in self.top_vars])

    for v, files in self.all_vars.iteritems():
      if len(files) != 1:
        for f in files:
          self.all_makefiles[f[0]].common_vars.add(v)
    for t, files in self.all_targets.iteritems():
      if len(files) != 1:
        for f in files:
          self.all_makefiles[f[0]].common_targets.add(t)

  def PrintCommonVarsAndTargets(self):
    """Prints top-level vars and targets, then those in multiple files.

    See the docstring for PrintVarsAndTargets() for more details.
    """
    PrintVarsAndTargets(self.top_vars, '*** TOP-LEVEL VARS ***')
    PrintVarsAndTargets(self.top_targets, '*** TOP-LEVEL TARGETS ***')
    PrintVarsAndTargets(self.all_vars, '*** VARS ***', common_only=True)
    PrintVarsAndTargets(self.all_targets, '*** TARGETS ***', common_only=True)


def HasVarOpen(segment):
  """Returns True if segment contains a Make variable opening."""
  for open_delim, close_delim in [('$(', ')'), ('${', '}')]:
    open_pos = segment.rfind(open_delim)
    close_pos = segment.rfind(close_delim)
    if open_pos != -1 and (close_pos == -1 or close_pos < open_pos):
      return True
  return False


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
  START_DELIM = '({ '
  END_DELIM = ' :=})'
  l = []
  i = s.find(orig_token)
  begin_unreplaced_segment = 0

  while i != -1:
    end_token = i + len(orig_token)
    if ((i == 0 or s[i - 1] in START_DELIM) and
         (end_token == len(s) or s[end_token] in END_DELIM) and
         (i < SVP_LEN or s[i - SVP_LEN:i] != SHELL_VAR_PREFIX) and
         (s[0] != '\t' or HasVarOpen(s[begin_unreplaced_segment:i]))):
      if i != begin_unreplaced_segment:
        l.append(s[begin_unreplaced_segment:i])
      l.append(new_token)
      begin_unreplaced_segment = end_token
    i = s.find(orig_token, end_token)
  if begin_unreplaced_segment != len(s):
    l.append(s[begin_unreplaced_segment:])
  return ''.join(l)


def UpdateTargetNames(infile, outfile, targets):
  """Updates names of targets appearing in other Makefiles.

  Only processes variable definitions, target names, and target prerequisites;
  recipes and comments are ignored. Changes the names of targets that also
  appear in other Makefiles to have a directory-specific suffix, and replaces
  those original targets with dependency-only targets that depend on the
  Makefile-local versions.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
    targets: hash of target name -> Makefile-specific target name
  """
  continued = False
  updated = False

  for line in infile:
    if continued:
      var_match = None
      target_match = None
    else:
      var_match = VAR_DEFINITION_PATTERN.match(line)
      target_match = TARGET_PATTERN.match(line)
      assert not (var_match and target_match), (
        '%s: %s\n  var: %s\n  target:%s' %
        (makefile.name, line, var_match.group(1), target_match.group(1)))

    if target_match:
      target_name = target_match.group(1)
      if target_name in targets:
        # Emit a prerequisite-only top-level rule if not yet present.
        replacement_rule = '%s: %s' % (target_name, targets[target_name])
        if line.startswith(replacement_rule):
          print >>outfile, line,
          continue
        print >>outfile, replacement_rule
        updated = True

    if continued or var_match or target_match:
      orig_line = line
      for orig_t in targets:
        line = ReplaceMakefileToken(line, orig_t, targets[orig_t])
      continued = Continues(line)
      updated = updated or line != orig_line

    print >>outfile, line,

  if updated:
    print '%s: updated common targets' % infile.name


def UpdateVariableNames(infile, outfile, variables):
  """Updates names of variables appearing in other Makefiles.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
    variables: hash of variable name -> Makefile-specific variable name
  """
  updated = False

  for line in infile:
    orig_line = line
    for orig_v in variables:
      line = ReplaceMakefileToken(line, orig_v, variables[orig_v])
    updated = updated or line != orig_line
    print >>outfile, line,

  if updated:
    print '%s: updated common variables' % infile.name


def EmitSuffixTargetRules(infile, outfile, variables, suffix):
  """Emits suffix target rules if needed.

  Different Makefiles set different values for variables used in default make
  rules. For those Makefiles, we redefine the default to use Makefile-specific
  variable values.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
    variables: hash of variable name -> Makefile-specific variable name
    suffix: Makefile-specific suffix string
  """
  suffix_targets = {}
  last_line_blank = False

  if 'CFLAGS' in variables:
    suffix_targets['.c.o:'] = (
        '\t$(CC) $(CFLAGS%s) $(CPPFLAGS) -c -o $@ $<' % suffix)
  if 'ASFLAGS' in variables:
    suffix_targets['.s.o:'] = '\t$(AS) $(ASFLAGS%s) -o $@ $<' % suffix
  if 'CPP' in variables:
    suffix_targets['.S.s:'] = '\t$(CPP%s) $(CPPFLAGS) -o $@ $<' % suffix

  for line in infile:
    tmp = {}
    tmp.update(suffix_targets)
    for t in suffix_targets:
      if line.startswith(t):
        del tmp[t]
    suffix_targets = tmp
    last_line_blank = line == '\n'
    print >>outfile, line,

  targets_to_emit = suffix_targets.keys()
  if not targets_to_emit:
    return

  targets_to_emit.sort()
  if not last_line_blank:
    print >>outfile
  for t in targets_to_emit:
    print >>outfile, t
    print >>outfile, suffix_targets[t]
  print '%s: emitted suffix target rules' % infile.name


def UpdateRecursiveMakeArgs(infile, outfile, suffix):
  """Updates recursive make commands that pass command-line variables.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
    suffix: Makefile-specific suffix string for the current makefile
  """
  old_includes = ' INCLUDES='
  new_includes = ' INCLUDES%s_$$i=' % suffix
  for line in infile:
    if '$(MAKE)' in line and old_includes in line:
      line = line.replace(old_includes, new_includes)
      print '%s: updated recursive make command line' % infile.name
    print >>outfile, line,


def UpdateMakefilesStage1(info, dirname, fnames):
  """Applies a series of updates to dirname/Makefile (if it exists).

  Passed to os.path.walk() to process all the Makefiles in the OpenSSL source
  tree. Performs heavier-duty changes than UpdateMakefilesStage0.

  Args:
    info: MakefileInfo object
    dirname: current directory path
    fnames: list of contents in the current directory
  """
  if 'Makefile' not in fnames: return
  makefile_name = os.path.join(dirname, 'Makefile')
  makefile = info.all_makefiles[makefile_name]
  target_map = makefile.LocalTargetMap()
  variable_map = makefile.LocalVariableMap()
  gnu_makefile_name = os.path.join(dirname, 'GNUmakefile')
  bsd_makefile_name = os.path.join(dirname, 'BSDmakefile')

  def UpdateTargetNamesHelper(infile, outfile):
    """Binds the local target map to UpdateTargetNames()."""
    UpdateTargetNames(infile, outfile, target_map)

  def UpdateVariableNamesHelper(infile, outfile):
    """Binds the local variable map to UpdateVariableNames()."""
    UpdateVariableNames(infile, outfile, variable_map)

  def EmitSuffixTargetRulesHelper(infile, outfile):
    """Binds the local variable map and suffix to EmitSuffixTargetRules()."""
    EmitSuffixTargetRules(infile, outfile, variable_map, makefile.suffix)

  def UpdateRecursiveMakeArgsHelper(infile, outfile):
    """Binds the local Makefile suffix to UpdateRecursiveMakeArgs()."""
    UpdateRecursiveMakeArgs(infile, outfile, makefile.suffix)

  UpdateFile(makefile_name, UpdateTargetNamesHelper)
  UpdateFile(makefile_name, UpdateVariableNamesHelper)
  UpdateFile(gnu_makefile_name, UpdateVariableNamesHelper)
  UpdateFile(bsd_makefile_name, UpdateVariableNamesHelper)
  UpdateFile(makefile_name, EmitSuffixTargetRulesHelper)
  UpdateFile(makefile_name, UpdateRecursiveMakeArgsHelper)


def UpdateDirectoryPaths(infile, outfile, makefile):
  """Updates every file and directory name to be relative to the top level.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
    makefile: Makefile object containing current variable and target info
  """
  skip_lines = 0
  updated = False
  for line in infile:
    if skip_lines:
      skip_lines -= 1
      continue

    update = None
    var_match = VAR_DEFINITION_PATTERN.match(line)
    target_match = TARGET_PATTERN.match(line)
    assert not (var_match and target_match), (
      '%s: %s\n  var: %s\n  target:%s' %
      (makefile.name, line, var_match.group(1), target_match.group(1)))

    if var_match:
      v = makefile.UpdateVariableWithDirectoryName(var_match.group(1))
      if v:
        update = '%s%s' % (var_match.group(0), v)
    #elif target_match:
    #  t = makefile.UpdateTargetWithDirectoryName(target_match.group(1))
    #  if t:
    #    update = '%s:%s%s' % (t.name, t.prerequisites, t.recipe)

    if update:
      print >>outfile, update
      skip_lines = update.count('\n')
      updated = True
    else:
      print >>outfile, line,

  if updated:
    print '%s: updated directory paths' % infile.name


def EliminateRecursiveMake(infile, outfile):
  """Removes all recursive make invocations and any now-empty targets.

  Args:
    info: MakefileInfo object
    dirname: current directory path
    fnames: list of contents in the current directory
  """
  for line in infile:
    if True:
      print '%s: eliminated recursive make' % infile.name
    print >>outfile, line,


def UpdateMakefilesStage2(info, dirname, fnames):
  """Applies a series of updates to dirname/Makefile (if it exists).

  Passed to os.path.walk() to process all the Makefiles in the OpenSSL source
  tree. Performs the final changes needed to "flip the switch" over to a
  nonrecursive make structure.

  Args:
    info: MakefileInfo object
    dirname: current directory path
    fnames: list of contents in the current directory
  """
  if 'Makefile' not in fnames: return
  makefile_name = os.path.join(dirname, 'Makefile')
  makefile = info.all_makefiles[makefile_name]
  gnu_makefile_name = os.path.join(dirname, 'GNUmakefile')
  bsd_makefile_name = os.path.join(dirname, 'BSDmakefile')

  def UpdateDirectoryPathsHelper(infile, outfile):
    """Binds the local Makefile to UpdateDirectoryPaths()."""
    UpdateDirectoryPaths(infile, outfile, makefile)

  UpdateFile(makefile_name, UpdateDirectoryPathsHelper)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--print_common',
        help='Print common targets and vars; skip updates',
        action='store_true')
  parser.add_argument('--makefile',
        help='Print all targets and vars for a Makefile; skip updates')
  args = parser.parse_args()

  if args.print_common or args.makefile:
    info = MakefileInfo()
    info.Init()
    if args.print_common:
      info.PrintCommonVarsAndTargets()
    elif args.makefile:
      print info.all_makefiles[args.makefile]
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
      os.path.walk(d, UpdateMakefilesStage0, None)

  CreateGnuMakefile('.')
  CreateBsdMakefile('.')
  UpdateFile('Makefile.org', RemoveConfigureVars)
  UpdateFile('Makefile.fips', RemoveConfigureVars)
  UpdateFile('Makefile.shared', RemoveConfigureVars)

  info = MakefileInfo()
  info.Init()

  for d in os.listdir('.'):
    if os.path.isdir(d):
      os.path.walk(d, UpdateMakefilesStage1, info)

  for d in os.listdir('.'):
    if os.path.isdir(d):
      os.path.walk(d, UpdateMakefilesStage2, info)

  # TODO:
  # - Add SRC_* vars to top-level SRC, to include all .d files
  # - Remove lib{crypto,ssl} targets from subdirs
  # - Remove: DIR TOP top subdirs
  # - Expand all files that are present in the directory
