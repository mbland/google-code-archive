#! /usr/bin/python2.7
# coding=UTF-8
"""
Automates moving dclean actions to clean targets in OpenSSL Makefiles.

As per RT openssl.org #3497.

https://code.google.com/p/mike-bland/source/browse/openssl/move_dclean_to_clean.py

Author:  Mike Bland (mbland@acm.org)
         http://mike-bland.com/
Date:    2014-06-21
License: Creative Commons Attribution 4.0 International (CC By 4.0)
         http://creativecommons.org/licenses/by/4.0/deed.en_US
"""

import update_makefiles

import os
import os.path


def MoveDcleanActionsToCleanTarget(infile, outfile, makefile):
  """Moves all dclean actions to clean targets, then removes dclean targets.

  Args:
    infile: Makefile to read
    outfile: Makefile to write
    makefile: update_makefiles.Makefile object containing current variable and
      target info
  """
  clean_target = 'clean' in makefile.targets and makefile.targets['clean']
  dclean_target = 'dclean' in makefile.targets and makefile.targets['dclean']
  updated_clean_target = False
  deleted_dclean_target = False
  skip_if_followed_by_blank = False
  skip_lines = 0
  for line in infile:
    if skip_lines:
      skip_lines -= 1
      continue
    if skip_if_followed_by_blank:
      skip_if_followed_by_blank = False
      if line == '\n':
        continue

    target_match = update_makefiles.TARGET_PATTERN.match(line)
    if target_match:
      target_name = target_match.group(1)

      if target_name == 'clean' and dclean_target:
        prerequisites = [clean_target.prerequisites.rstrip()]
        prerequisites.append(dclean_target.prerequisites.rstrip())
        prerequisites = ' '.join([p for p in prerequisites if p])

        recursive_clean = '\t@target=clean; $(RECURSIVE_MAKE)\n'
        recursive_dclean = '\t@target=dclean; $(RECURSIVE_MAKE)\n'

        has_recursive_clean = recursive_clean in clean_target.recipe
        clean_recipe = clean_target.recipe.replace(recursive_clean, '')
        recipe = [clean_target.recipe.rstrip()]

        dclean_recipe = dclean_target.recipe.replace(recursive_dclean, '')
        recipe.append(dclean_recipe.rstrip())
        if has_recursive_clean:
          recipe.append(recursive_clean.rstrip())
        recipe = '\n'.join([r for r in recipe if r])

        updated_clean = 'clean:%s\n%s' % (prerequisites, recipe)
        skip_lines = clean_target.num_lines - 1
        print >>outfile, updated_clean
        updated_clean_target = True
        continue

      elif target_name == 'dclean':
        skip_lines = dclean_target.num_lines - 1
        deleted_dclean_target = True
        skip_if_followed_by_blank = True
        continue

    print >>outfile, line,

  assert (updated_clean_target and deleted_dclean_target) or not (
          updated_clean_target or deleted_dclean_target)

  if updated_clean_target:
    print '%s: moved dclean actions to clean target' % infile.name


def UpdateMakefile(makefile_info, dirname, fnames):
  """Calls MoveDcleanActionsToCleanTarget() on Makefiles during os.path.walk().

  Args:
    makefile_info: update_makefiles.MakefileInfo object
    dirname: current directory path
    fnames: list of contents in the current directory
  """
  if 'Makefile' not in fnames: return
  makefile_path = os.path.join(dirname, 'Makefile')
  makefile = info.all_makefiles[makefile_path]

  def MoveDcleanActionsToCleanTargetBinder(infile, outfile):
    """Binds the local Makefile to MoveDcleanActionsToCleanTarget()."""
    MoveDcleanActionsToCleanTarget(infile, outfile, makefile)

  update_makefiles.UpdateFile(makefile_path,
      MoveDcleanActionsToCleanTargetBinder)


if __name__ == '__main__':
  info = update_makefiles.MakefileInfo()
  info.Init()

  for d in os.listdir('.'):
    if os.path.isdir(d):
      os.path.walk(d, UpdateMakefile, info)

