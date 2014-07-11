#! /usr/bin/python2.7
# coding=UTF-8
"""
Unit tests for the tricksier bits of update_makefiles.py.

Author:  Mike Bland (mbland@acm.org)
         http://mike-bland.com/
Date:    2014-07-11
License: Creative Commons Attribution 4.0 International (CC By 4.0)
         http://creativecommons.org/licenses/by/4.0/deed.en_US
"""

import update_makefiles

import cStringIO
import unittest


class SplitMakeVarsTest(unittest.TestCase):

  def testEmptyString(self):
    self.assertListEqual([], update_makefiles.SplitMakeVars(''))

  def testNoMakeVarsPresent(self):
    self.assertListEqual(['foo bar baz'],
        update_makefiles.SplitMakeVars('foo bar baz'))

  def testSingleMakeVar(self):
    self.assertListEqual(['foo ', '$(BAR)', ' baz'],
        update_makefiles.SplitMakeVars('foo $(BAR) baz'))

  def testMultipleMakeVars(self):
    self.assertListEqual(['$(FOO)', ' bar ', '$(BAZ)'],
        update_makefiles.SplitMakeVars('$(FOO) bar $(BAZ)'))

  def testHandleCurlyBraces(self):
    self.assertListEqual(['${FOO}', ' bar ', '$(BAZ)'],
        update_makefiles.SplitMakeVars('${FOO} bar $(BAZ)'))

  def testIgnoreShellVars(self):
    self.assertListEqual(['$${FOO} bar ', '$(BAZ)'],
        update_makefiles.SplitMakeVars('$${FOO} bar $(BAZ)'))

  def testIgnoreDollarSignNotFollowedByParenOrBrace(self):
    self.assertListEqual(['${FOO}', ' bar $baz'],
        update_makefiles.SplitMakeVars('${FOO} bar $baz'))

  def testIgnoreDollarSignAtEndOfLine(self):
    self.assertListEqual(['${FOO}', ' bar baz $'],
        update_makefiles.SplitMakeVars('${FOO} bar baz $'))


if __name__ == '__main__':
  unittest.main()
