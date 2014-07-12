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

  def testParseInnermostNestedVariable(self):
    self.assertListEqual(['$(function0 $(function1 ', '$(foo)', ') bar)'],
        update_makefiles.SplitMakeVars(
            '$(function0 $(function1 $(foo)) bar)'))

  def testParseMultipleNestedVariables(self):
    self.assertListEqual(
        ['$(function0 $(function1 ', '$(foo)', ') ', '${bar}', ')'],
        update_makefiles.SplitMakeVars(
            '$(function0 $(function1 $(foo)) ${bar})'))


class ReplaceMakefileTokenTest(unittest.TestCase):

  def testNoReplacement(self):
    self.assertEqual('$(BAR)',
        update_makefiles.ReplaceMakefileToken('$(BAR)', 'FOO', 'FOO_new'))

  def testBasicReplacement(self):
    self.assertEqual('$(FOO_new)',
        update_makefiles.ReplaceMakefileToken('$(FOO)', 'FOO', 'FOO_new'))

  def testReplacementNotNeeded(self):
    self.assertEqual('$(FOO_new)',
        update_makefiles.ReplaceMakefileToken('$(FOO_new)', 'FOO', 'FOO_new'))

  def testDoNotReplaceSubstring(self):
    self.assertEqual('$(FOOFOOFOO)',
        update_makefiles.ReplaceMakefileToken(
            '$(FOOFOOFOO)', 'FOO', 'FOO_new'))

  def testReplacementCurlyBraces(self):
    self.assertEqual('${FOO_new}',
        update_makefiles.ReplaceMakefileToken('${FOO}', 'FOO', 'FOO_new'))

  def testReplacementSubstitutionReference(self):
    self.assertEqual('${FOO_new:.d=.c}',
        update_makefiles.ReplaceMakefileToken(
            '${FOO:.d=.c}', 'FOO', 'FOO_new'))

  def testReplacementInFunction(self):
    self.assertEqual('$(origin FOO_new)',
        update_makefiles.ReplaceMakefileToken(
            '$(origin FOO)', 'FOO', 'FOO_new'))

  def testMultipleReplacementInFunction(self):
    self.assertEqual('$(origin FOO_new bar FOO_new)',
        update_makefiles.ReplaceMakefileToken(
            '$(origin FOO bar FOO)', 'FOO', 'FOO_new'))

  def testReplaceVariableNameInAssignment(self):
    self.assertEqual('FOO_new = bar baz',
        update_makefiles.ReplaceMakefileToken(
            'FOO = bar baz', 'FOO', 'FOO_new'))

  def testReplaceVariableNameInAssignmentNoSpace(self):
    self.assertEqual('FOO_new=bar baz',
        update_makefiles.ReplaceMakefileToken(
            'FOO=bar baz', 'FOO', 'FOO_new'))

  def testReplaceVariableExpansionInAssignment(self):
    self.assertEqual('FOO=$(BAR_new) baz',
        update_makefiles.ReplaceMakefileToken(
            'FOO=$(BAR) baz', 'BAR', 'BAR_new'))

  def testReplaceTargetName(self):
    self.assertEqual('foo_new: bar baz',
        update_makefiles.ReplaceMakefileToken(
            'foo: bar baz', 'foo', 'foo_new'))

  def testReplaceTargetVariableName(self):
    self.assertEqual('$(FOO_new): bar baz',
        update_makefiles.ReplaceMakefileToken(
            '$(FOO): bar baz', 'FOO', 'FOO_new'))

  def testReplaceTargetPartialVariableName(self):
    self.assertEqual('$(FOO_new)_suffix: bar baz',
        update_makefiles.ReplaceMakefileToken(
            '$(FOO)_suffix: bar baz', 'FOO', 'FOO_new'))

  def testReplaceTargetPrerequisiteTarget(self):
    self.assertEqual('foo: bar_new baz',
        update_makefiles.ReplaceMakefileToken(
            'foo: bar baz', 'bar', 'bar_new'))

  def testReplaceTargetPrerequisiteVariable(self):
    self.assertEqual('foo: $(BAR_new) baz',
        update_makefiles.ReplaceMakefileToken(
            'foo: $(BAR) baz', 'BAR', 'BAR_new'))

  def testReplaceTargetSpecificVariableAssignment(self):
    self.assertEqual('foo: BAR_new = baz',
        update_makefiles.ReplaceMakefileToken(
            'foo: BAR = baz', 'BAR', 'BAR_new'))

  def testReplaceTargetSpecificVariableAssignmentNoSpace(self):
    self.assertEqual('foo: BAR_new=baz',
        update_makefiles.ReplaceMakefileToken(
            'foo: BAR=baz', 'BAR', 'BAR_new'))

  def testIgnoreShellVariableInTargetRecipe(self):
    self.assertEqual('\tfrob $$FOO bar',
        update_makefiles.ReplaceMakefileToken(
            '\tfrob $$FOO bar', 'FOO', 'FOO_bad'))

  def testIgnoreShellVariableInTargetRecipeCurlyBraces(self):
    self.assertEqual('\tfrob $${FOO} bar',
        update_makefiles.ReplaceMakefileToken(
            '\tfrob $${FOO} bar', 'FOO', 'FOO_bad'))


if __name__ == '__main__':
  unittest.main()
