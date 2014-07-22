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

import StringIO
import unittest


class HasVarOpenTest(unittest.TestCase):

  def testNoVarOpen(self):
    self.assertFalse(update_makefiles.HasVarOpen(''))
    self.assertFalse(update_makefiles.HasVarOpen('FOO'))

  def testHasVarOpen(self):
    self.assertTrue(update_makefiles.HasVarOpen('$(FOO'))
    self.assertTrue(update_makefiles.HasVarOpen('${FOO'))
    self.assertTrue(update_makefiles.HasVarOpen('$( FOO'))
    self.assertTrue(update_makefiles.HasVarOpen('${ FOO'))

  def testNotOpenEarlierVar(self):
    self.assertFalse(update_makefiles.HasVarOpen('$(FOO) BAR'))
    self.assertFalse(update_makefiles.HasVarOpen('${FOO} BAR'))
    self.assertFalse(update_makefiles.HasVarOpen('$( FOO ) BAR'))
    self.assertFalse(update_makefiles.HasVarOpen('${ FOO } BAR'))

  def testOpenEarlierVar(self):
    self.assertTrue(update_makefiles.HasVarOpen('$(FOO) $(BAR'))
    self.assertTrue(update_makefiles.HasVarOpen('${FOO} ${BAR'))
    self.assertTrue(update_makefiles.HasVarOpen('$( FOO ) $( BAR'))
    self.assertTrue(update_makefiles.HasVarOpen('${ FOO } ${ BAR'))


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

  def testIgnoreRecipeArgThatMatchesVarName(self):
    self.assertEqual('\tfrob FOO=$(FOO_new) bar',
        update_makefiles.ReplaceMakefileToken(
            '\tfrob FOO=$(FOO) bar', 'FOO', 'FOO_new'))


class SplitPreservingWhitespaceTest(unittest.TestCase):

  def testEmptyString(self):
    self.assertEqual([],
        update_makefiles.SplitPreservingWhitespace(''))

  def testSingleWhitespaceString(self):
    self.assertEqual([' '],
        update_makefiles.SplitPreservingWhitespace(' '))
    self.assertEqual(['\t'],
        update_makefiles.SplitPreservingWhitespace('\t'))
    self.assertEqual(['\n'],
        update_makefiles.SplitPreservingWhitespace('\n'))
    self.assertEqual(['\r'],
        update_makefiles.SplitPreservingWhitespace('\r'))
    self.assertEqual(['\x0b'],
        update_makefiles.SplitPreservingWhitespace('\x0b'))
    self.assertEqual(['\x0c'],
        update_makefiles.SplitPreservingWhitespace('\x0c'))

  def testSingleNonwhitespaceString(self):
    self.assertEqual(['a'],
        update_makefiles.SplitPreservingWhitespace('a'))

  def testCombinedString(self):
    self.assertEqual(['\t', 'foo', ' ', 'bar', '\n'],
        update_makefiles.SplitPreservingWhitespace('\tfoo bar\n'))
    self.assertEqual(['\t \n', 'foo', '\t \n', 'bar', '\t \n'],
        update_makefiles.SplitPreservingWhitespace(
            '\t \nfoo\t \nbar\t \n'))


class NormalizeRelativeDirectoryTest(unittest.TestCase):

  def testLeavePathAlone(self):
    self.assertEqual('foo',
        update_makefiles.NormalizeRelativeDirectory(
            'foo', '', 'foo/Makefile'))

  def testReplaceTopPathByItself(self):
    self.assertEqual('-I.',
        update_makefiles.NormalizeRelativeDirectory(
            '-I$(TOP_foo)', '-I', 'foo/Makefile'))

  def testReplaceTopPathWithChild(self):
    self.assertEqual('-Lbar/baz',
        update_makefiles.NormalizeRelativeDirectory(
            '-L$(TOP)/bar/baz', '-L', 'foo/Makefile'))

  def testReplaceSingleDotWithMakefilePath(self):
    self.assertEqual('foo/bar',
        update_makefiles.NormalizeRelativeDirectory(
            './bar', '', 'foo/Makefile'))

  def testReplaceDoubleDotWithParentPath(self):
    self.assertEqual('foo/baz',
        update_makefiles.NormalizeRelativeDirectory(
            '../baz', '', 'foo/bar/Makefile'))

  def testReplaceDoubleDotsWithGrandparentPath(self):
    self.assertEqual('baz',
        update_makefiles.NormalizeRelativeDirectory(
            '../../baz', '', 'foo/bar/Makefile'))

  def testReplaceDoubleDotsWithTopDir(self):
    self.assertEqual('.',
        update_makefiles.NormalizeRelativeDirectory(
            '../..', '', 'foo/bar/Makefile'))


class UpdateDirectoryPaths(unittest.TestCase):

    def ParseAndUpdate(self, makefile_dir, orig, expected):
      infile = StringIO.StringIO(orig)
      infile.name = '%s/Makefile' % makefile_dir
      self.makefile = update_makefiles.ParseMakefile(infile)
      infile.seek(0)
      outfile = StringIO.StringIO()
      update_makefiles.UpdateDirectoryPaths(infile, outfile, self.makefile)
      self.assertMultiLineEqual(expected, outfile.getvalue())

    def testReplaceIncludePaths(self):
      # Using crypto/Makefile because it has normal and special cases.
      orig = (
"""INCLUDE_crypto=	-I. -I$(TOP_crypto) -I../include $(ZLIB_INCLUDE)
INCLUDES_crypto=	-I.. -I../.. -I../modes -I../asn1 -I../evp -I../../include $(ZLIB_INCLUDE)
""")
      expected = (
"""INCLUDE_crypto=	-Icrypto -I. -Iinclude $(ZLIB_INCLUDE)
INCLUDES_crypto=	-Icrypto -I. -Icrypto/modes -Icrypto/asn1 -Icrypto/evp -Iinclude $(ZLIB_INCLUDE)
""")
      self.ParseAndUpdate('crypto', orig, expected)
      self.ParseAndUpdate('crypto', expected, expected)

    def testDoNotEatUnaffectedLines(self):
      orig = (
"""INCLUDE_crypto=	-I. -I$(TOP_crypto) -I../include $(ZLIB_INCLUDE)
# INCLUDES_crypto targets sudbirs!
INCLUDES_crypto=	-I.. -I../.. -I../modes -I../asn1 -I../evp -I../../include $(ZLIB_INCLUDE)
RM_crypto=             rm -f
""")
      expected = (
"""INCLUDE_crypto=	-Icrypto -I. -Iinclude $(ZLIB_INCLUDE)
# INCLUDES_crypto targets sudbirs!
INCLUDES_crypto=	-Icrypto -I. -Icrypto/modes -Icrypto/asn1 -Icrypto/evp -Iinclude $(ZLIB_INCLUDE)
RM_crypto=             rm -f
""")
      self.ParseAndUpdate('crypto', orig, expected)
      self.ParseAndUpdate('crypto', expected, expected)

    def testFipsObjListProcessingIsIdempotent(self):
      orig = (
"""FIPS_OBJ_LISTS=sha/lib hmac/lib rand/lib des/lib aes/lib dsa/lib rsa/lib \
            dh/lib utl/lib ecdsa/lib ecdh/lib cmac/lib
""")
      expected = (
"""FIPS_OBJ_LISTS=fips/sha/lib fips/hmac/lib fips/rand/lib fips/des/lib fips/aes/lib fips/dsa/lib fips/rsa/lib \
            fips/dh/lib fips/utl/lib fips/ecdsa/lib fips/ecdh/lib fips/cmac/lib
""")
      self.ParseAndUpdate('fips', orig, expected)
      self.ParseAndUpdate('fips', expected, expected)


if __name__ == '__main__':
  unittest.main()
