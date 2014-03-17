#! /usr/bin/python
# coding=UTF-8
"""
Test for the ptc_fetch.py script.

Author:  Mike Bland (mbland@acm.org)
         http://mike-bland.com/
Date:    2014-03-13
License: Creative Commons Attribution 4.0 International (CC By 4.0)
         http://creativecommons.org/licenses/by/4.0/deed.en_US

If you don't have the fake_filesystem and mox modules installed, you may need
to install pip, the Python Package Index installer:
  https://pypi.python.org/pypi
  http://www.pip-installer.org/en/latest/installing.html

Then:
  $ pip install pyfakefs
  $ pip install mox

More info:
  http://mike-bland.com/2014/03/17/playing-the-changes-hack-continued.html
"""

import ptc_fetch

import cStringIO
import fake_filesystem
import mox
import sys
import unittest


class RequestStub(object):
  """Stub used to model a requests.Request object for testing."""
  def __init__(self, text=''):
    self.text = text
    self.closed = False

  def close(self):
    self.closed = True

  def iter_content(self, _):
    return iter(self.text)


class FetchPtcFilesTest(unittest.TestCase):
  def setUp(self):
    self._fs = fake_filesystem.FakeFilesystem()
    self._os = fake_filesystem.FakeOsModule(self._fs)
    self._real_os_path = ptc_fetch.os.path
    ptc_fetch.os.path = self._os.path

    self._mox = mox.Mox()
    self._mox.StubOutWithMock(ptc_fetch, 'requests')

  def tearDown(self):
    self._mox.UnsetStubs()
    ptc_fetch.os.path = self._real_os_path

  def CallFetchPtcFiles(self):
    self._real_stdout = sys.stdout
    self._real_stderr = sys.stderr
    sys.stdout = cStringIO.StringIO()
    sys.stderr = cStringIO.StringIO()
    self._real_open = __builtins__.open
    __builtins__.open = fake_filesystem.FakeFileOpen(self._fs)

    try:
      ptc_fetch.FetchPtcFiles()
    finally:
      self._stdout = sys.stdout.getvalue()
      self._stderr = sys.stderr.getvalue()
      sys.stdout = self._real_stdout
      sys.stderr = self._real_stderr
      __builtins__.open = self._real_open

  def testNoLinksScraped(self):
    initial_req = RequestStub()
    ptc_fetch.requests.get('%s/' % ptc_fetch.PTC_COM).AndReturn(initial_req)
    self._mox.ReplayAll()
    self.CallFetchPtcFiles()
    self._mox.VerifyAll()
    self.assertTrue(initial_req.closed)

  def testSingleFileDownload(self):
    initial_req = RequestStub(
        '<td class="download"><a href="downloads/CMaj7.mp3" target="_blank">'
        'CMaj7 <img src="images/redArrow.gif" border="0" align="absmiddle">'
        '</a></td>')
    ptc_fetch.requests.get('%s/' % ptc_fetch.PTC_COM).AndReturn(initial_req)

    cmaj7_req = RequestStub('CMaj7 sound data')
    ptc_fetch.requests.get(
        '%s/downloads/CMaj7.mp3' % ptc_fetch.PTC_COM).AndReturn(cmaj7_req)

    self._mox.ReplayAll()
    self.CallFetchPtcFiles()
    self._mox.VerifyAll()

    self.assertEqual('Fetching  1 of 1: downloads/CMaj7.mp3\n', self._stdout)

    self.assertTrue(initial_req.closed)
    self.assertTrue(cmaj7_req.closed)

    self.assertEqual('CMaj7 sound data',
                     self._fs.GetObject('CMaj7.mp3').contents)

  def testMultipleFileDownload(self):
    initial_req = RequestStub(
        '<td class="download"><a href="downloads/CMaj7.mp3" '
        'target="_blank">CMaj7 <img src="images/redArrow.gif" border="0" '
        'align="absmiddle"></a></td>\n\n'

        '<td bgcolor="#F1F1F1" class="download"><a '
        'href="downloads/Fmin7.mp3">F&ndash;7 <img src="images/redArrow.gif" '
        'border="0" align="absmiddle"></a> </td>\n\n'

        '<td class="download"><a href="downloads/Bb7.mp3">B<img '
        'src="images/flat.gif" width="5" height="13" hspace="2" border="0" '
        'align="absmiddle">7 <img src="images/redArrow.gif" border="0" '
        'align="absmiddle"></a> </td>\n')
    ptc_fetch.requests.get('%s/' % ptc_fetch.PTC_COM).AndReturn(initial_req)

    cmaj7_req = RequestStub('CMaj7 sound data')
    ptc_fetch.requests.get(
        '%s/downloads/CMaj7.mp3' % ptc_fetch.PTC_COM).AndReturn(cmaj7_req)

    fmin7_req = RequestStub('F-7 sound data')
    ptc_fetch.requests.get(
        '%s/downloads/Fmin7.mp3' % ptc_fetch.PTC_COM).AndReturn(fmin7_req)

    bflat7_req = RequestStub('B♭7 sound data')
    ptc_fetch.requests.get(
        '%s/downloads/Bb7.mp3' % ptc_fetch.PTC_COM).AndReturn(bflat7_req)

    self._mox.ReplayAll()
    self.CallFetchPtcFiles()
    self._mox.VerifyAll()

    self.assertEqual('Fetching  1 of 3: downloads/CMaj7.mp3\n'
                     'Fetching  2 of 3: downloads/Fmin7.mp3\n'
                     'Fetching  3 of 3: downloads/Bb7.mp3\n', self._stdout)

    self.assertTrue(initial_req.closed)
    self.assertTrue(cmaj7_req.closed)
    self.assertTrue(fmin7_req.closed)
    self.assertTrue(bflat7_req.closed)

    self.assertEqual('CMaj7 sound data',
                     self._fs.GetObject('CMaj7.mp3').contents)
    self.assertEqual('F-7 sound data',
                     self._fs.GetObject('Fmin7.mp3').contents)
    self.assertEqual('B♭7 sound data',
                     self._fs.GetObject('Bb7.mp3').contents)


class SplitFileNameTest(unittest.TestCase):
  def testNaturalRootChordFileName(self):
    self.assertTupleEqual(('C', 'Maj7'),
                          ptc_fetch.SplitFileName('CMaj7.mp3'))

  def testFlatRootChordFileName(self):
    self.assertTupleEqual(('Bb', 'min7'),
                          ptc_fetch.SplitFileName('Bbmin7.mp3'))

  def testSharpRootChordFileName(self):
    self.assertTupleEqual(('Fsharp', '7'),
                          ptc_fetch.SplitFileName('Fsharp7.mp3'))

  def testRaisesIfFileNameDoesNotEndInMp3(self):
    self.assertRaisesRegexp(ptc_fetch.BadChordFileNameException,
                            'Bad chord file name: CMaj7',
                            ptc_fetch.SplitFileName, 'CMaj7')

  def testRaisesIfFileNameChordRootIsUnknown(self):
    # The code doesn't account for enharmonic spellings; this test would
    # need to be updated if it did.
    self.assertRaisesRegexp(ptc_fetch.BadChordFileNameException,
                            'Unknown chord root in file name: CbMaj7.mp3',
                            ptc_fetch.SplitFileName, 'CbMaj7.mp3')

  def testRaisesIfFileNameChordSuffixIsUnknown(self):
    # The code doesn't account for suffix variations; this test would
    # need to be updated if it did.
    self.assertRaisesRegexp(ptc_fetch.BadChordFileNameException,
                            'Unknown chord suffix in file name: CMajor7.mp3',
                            ptc_fetch.SplitFileName, 'CMajor7.mp3')


class CompareChordFileNamesTest(unittest.TestCase):
  def testEqualChords(self):
    self.assertEqual(0,
        ptc_fetch.CompareChordFileNames(('C', 'Maj7'), ('C', 'Maj7')))

  def testEqualRootLhsSuffixLessThanRhs(self):
    self.assertGreater(0,
        ptc_fetch.CompareChordFileNames(('Db', 'min7'), ('Db', '7')))

  def testEqualRootLhsSuffixGreaterThanRhs(self):
    self.assertLess(0,
        ptc_fetch.CompareChordFileNames(('E', '7b9b13'), ('E', 'min7b5')))

  def testEqualSuffixLhsRootLessThanRhs(self):
    # May seem counterintuitive, but we're walking the circle of fourths up
    # from C, which places F before Eb.
    self.assertGreater(0,
        ptc_fetch.CompareChordFileNames(('F', 'min7'), ('Eb', 'min7')))

  def testEqualSuffixLhsRootGreaterThanRhs(self):
    self.assertLess(0,
        ptc_fetch.CompareChordFileNames(('Fsharp', '7'), ('F', '7')))

  def testLhsSuffixLessTrumpsLhsRootGreater(self):
    self.assertGreater(0,
        ptc_fetch.CompareChordFileNames(('G', 'min7'), ('B', '7')))

  def testLhsSuffixGreaterTrumpsLhsRootLess(self):
    self.assertLess(0,
        ptc_fetch.CompareChordFileNames(('B', '7'), ('G', 'min7')))


class ChordNameTest(unittest.TestCase):
  def testSanity(self):
    self.assertEqual('F#7(b9,b13)',
                     ptc_fetch.ChordName(
                         ptc_fetch.SplitFileName('Fsharp7b9b13.mp3')))


class UpdateMp3TagsTest(unittest.TestCase):
  def setUp(self):
    self._fs = fake_filesystem.FakeFilesystem()
    self._os = fake_filesystem.FakeOsModule(self._fs)
    self._real_os = ptc_fetch.os
    ptc_fetch.os = self._os
    self._subprocess_call_args = []

    self._raise_error_on_file = None

  def tearDown(self):
    ptc_fetch.os = self._real_os

  def FakeSubprocessCall(self, args):
    self._subprocess_call_args.append(args)
    return args[-1] == self._raise_error_on_file and 1 or 0

  def CallUpdateMp3Tags(self):
    """Executes UpdateMp3Tags() and captures the stdout and stderr streams."""
    self._real_stdout = sys.stdout
    self._real_stderr = sys.stderr
    sys.stdout = cStringIO.StringIO()
    sys.stderr = cStringIO.StringIO()

    self._real_subprocess_call = ptc_fetch.subprocess.call
    ptc_fetch.subprocess.call = self.FakeSubprocessCall

    try:
      ptc_fetch.UpdateMp3Tags()
    finally:
      self._stdout = sys.stdout.getvalue()
      self._stderr = sys.stderr.getvalue()
      sys.stdout = self._real_stdout
      sys.stderr = self._real_stderr
      ptc_fetch.subprocess.call = self._real_subprocess_call

  def testNoFiles(self):
    self.CallUpdateMp3Tags()
    self.assertEquals('Updated 0 mp3s\n', self._stdout)

  def testOneFile(self):
    self._fs.CreateFile('CMaj7.mp3')
    self.CallUpdateMp3Tags()
    self.assertEquals('Updating: CMaj7.mp3\n'
                      'Updated 1 mp3\n', self._stdout)
    self.assertEqual(1, len(self._subprocess_call_args))
    self.assertListEqual(['/usr/local/bin/id3tag',
                          '--artist=Paul Del Nero',
                          '--album=Playing the Changes',
                          u'--song=CMaj7',
                          '--track=1',
                          '--total=1',
                          'CMaj7.mp3'],
                         self._subprocess_call_args[0])

  def testTwoFiles(self):
    self._fs.CreateFile('Bbmin7.mp3')
    self._fs.CreateFile('CMaj7.mp3')
    self.CallUpdateMp3Tags()
    self.assertEqual('Updating: CMaj7.mp3\n'
                     'Updating: Bbmin7.mp3\n'
                     'Updated 2 mp3s\n', self._stdout)
    self.assertEqual('', self._stderr)
    self.assertEqual(2, len(self._subprocess_call_args))
    self.assertListEqual(
        [u'--song=CMaj7', '--track=1', '--total=2', 'CMaj7.mp3'],
        self._subprocess_call_args[0][3:7])
    self.assertListEqual(
        [u'--song=Bb-7', '--track=2', '--total=2', 'Bbmin7.mp3'],
        self._subprocess_call_args[1][3:7])

  def testSubprocessCallFails(self):
    self._fs.CreateFile('Bbmin7.mp3')
    self._fs.CreateFile('C7b913.mp3')
    self._fs.CreateFile('Fsharp7b9b13.mp3')
    self._raise_error_on_file = 'Fsharp7b9b13.mp3'

    # Apparently self.assertRaises() doesn't catch SystemExit.
    try:
      self.CallUpdateMp3Tags()
    except SystemExit:
      pass
    else:
      self.fail('SystemExit not raised')

    self.assertEqual('Updating: Bbmin7.mp3\n'
                     'Updating: Fsharp7b9b13.mp3\n', self._stdout)
    self.assertEqual(
        'Error updating Fsharp7b9b13.mp3 (return code 1) with command: '
        '/usr/local/bin/id3tag --artist=Paul Del Nero '
        '--album=Playing the Changes --song=F#7(b9,b13) '
        '--track=2 --total=3 Fsharp7b9b13.mp3\n', self._stderr)
    self.assertEqual(2, len(self._subprocess_call_args))
    self.assertListEqual(
        [u'--song=Bb-7', '--track=1', '--total=3', 'Bbmin7.mp3'],
        self._subprocess_call_args[0][3:7])
    self.assertListEqual(
        [u'--song=F#7(b9,b13)', '--track=2', '--total=3', 'Fsharp7b9b13.mp3'],
        self._subprocess_call_args[1][3:7])


if __name__ == '__main__':
  unittest.main()
