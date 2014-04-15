#! /bin/sh
#
# Build script for the heartbleed_test.c example.
#
# Author:  Mike Bland (mbland@acm.org, http://mike-bland.com/)
# Date:    2014-04-15
# License: Creative Commons Attribution 4.0 International (CC By 4.0)
#          http://creativecommons.org/licenses/by/4.0/deed.en_US
# URL:     http://goo.gl/erKNJm
#
# What this script does
# ---------------------
# If needed, it will download the OpenSSL source packages and unpack them in
# the current directory, build each version, then build and run
# heartbleed_test.c for each version.

HEARTBLEED_TEST_URL=https://mike-bland.googlecode.com/git/heartbleed/heartbleed_test.c
HEARTBLEED_TEST=$(basename ${HEARTBLEED_TEST_URL} .c)
BUGGY_VERSION=openssl-1.0.1-beta1
FIXED_VERSION=openssl-1.0.1g
OPENSSL_SOURCE_URL=http://www.openssl.org/source/

for version in ${BUGGY_VERSION} ${FIXED_VERSION}
do
  tarball=${version}.tar.gz
  if test ! -f ${tarball}; then
    package=${OPENSSL_SOURCE_URL}${tarball}
    echo "Downloading ${package}"
    /usr/bin/curl -O ${package}
    if test $? -ne 0; then
      echo "Failed to download ${package}"
      echo "Aborting..."
      exit 1
    fi
  fi

  if test ! -d ${version}; then
    echo "Unpacking ${tarball}"
    /usr/bin/gzip -dc ${tarball} | /usr/bin/tar xf -
    if test $? -ne 0; then
      echo "Unpacking ${tarball} failed"
      echo "Aborting..."
      exit 1
    fi
  fi
done

for version in ${BUGGY_VERSION} ${FIXED_VERSION}
do
  echo "Building ${version}..."
  pushd ${version}

  if ! test -f crypto/buildinf.h; then
    if ! ./config; then
      echo "Failed to configure ${version}"
      echo "Aborting..."
      exit 1
    fi
  fi

  if ! make; then
    echo "Failed to build ${version}"
    echo "Aborting..."
    exit 1
  fi
  popd
done


HEARTBLEED_TEST_FILE=$(basename ${HEARTBLEED_TEST_URL})

if ! test -f ${HEARTBLEED_TEST_FILE}; then
  echo "Downloading ${HEARTBLEED_TEST_URL}..."
  /usr/bin/curl -O ${HEARTBLEED_TEST_URL}
  if test $? -ne 0; then
    echo "Failed to download ${HEARTBLEED_TEST_URL}"
    echo "Aborting..."
    exit 1
  fi

  echo "Linking ${HEARTBLEED_TEST_FILE} into each version..."
	for version in ${BUGGY_VERSION} ${FIXED_VERSION}
  do
    if ! /bin/ln ${HEARTBLEED_TEST_FILE} ${version}/test; then
      echo "Failed to link ${HEARTBLEED_TEST_FILE} into ${version}/test"
      echo "Aborting..."
      exit 1
    fi
  done
fi

for version in ${BUGGY_VERSION} ${FIXED_VERSION}
do
  echo "Building and executing heartbleed_test for ${version}..."
  makefile=${version}/test/Makefile
  if grep -q ${HEARTBLEED_TEST} ${makefile}; then
    echo "${makefile} already updated..."
  else
    echo "Adding ${HEARTBLEED_TEST} to ${makefile}..."
    /bin/cat >>${makefile} <<END
${HEARTBLEED_TEST}.o: ${HEARTBLEED_TEST}.c
${HEARTBLEED_TEST}: ${HEARTBLEED_TEST}.o \$(DLIBCRYPTO)
	@target=${HEARTBLEED_TEST}; \$(BUILD_CMD)
END
    if test ! $? -eq 0; then
      echo "Failed to append ${HEARTBLEED_TEST} target to ${makefile}"
      echo "Aborting..."
      exit 1
    fi
  fi

  echo "Building ${HEARTBLEED_TEST} for ${version}..."
  pushd ${version}

  if ! make TESTS=${HEARTBLEED_TEST} test; then
    echo "Failed to build ${HEARTBLEED_TEST} for ${version}"
    echo "Aborting..."
    exit 1
  fi

  popd
  test_program=${version}/test/heartbleed_test
  echo "******** EXECUTING ${test_program} ********"
  result="PASSED"
  if ! ${test_program}; then
    result="FAILED"
  fi
  echo "******** ${test_program} ${result} ********"
done
