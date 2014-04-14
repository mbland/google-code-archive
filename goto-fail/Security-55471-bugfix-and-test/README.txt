Security-55471 proof-of-concept patch, test, and build script
-------------------------------------------------------------

Author:  Mike Bland (mbland@acm.org, http://mike-bland.com/)
Date:    2014-02-24
License: Creative Commons Attribution 4.0 International (CC By 4.0)
         http://creativecommons.org/licenses/by/4.0/deed.en_US

Tarball URL: http://goo.gl/tnvIUm
Browse URL:
https://code.google.com/p/mike-bland/source/browse/goto-fail/Security-55471-bugfix-and-test/

This package contains a patch to Apple's Security-55471/libsecurity_ssl source
code, as well as include stubs and a build script that enable just the
proof-of-concept code changes and test to compile and execute.

The build.sh script will download the source from:

  http://opensource.apple.com/tarballs/Security/Security-55471.tar.gz
  http://opensource.apple.com/tarballs/CF/CF-855.11.tar.gz

Then it will apply the patch, build the changes and execute the test.

A detailed analysis and discussion of the "goto fail" bug is available at:

  http://goo.gl/eSS7r2

Developed on an OS X 10.9.2 system using:
  $ xcodebuild -version
  Xcode 5.1.1
  Build version 5B1008
