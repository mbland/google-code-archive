#! /bin/sh
#
# Build script for the tls_digest_test.c example and the proof-of-concept
# HashHandshake() function update to sslKeyExchange.c
#
# Part of the complete "goto fail" patch-and-test demonstration package:
# http://goo.gl/tnvIUm
#
# Author:  Mike Bland (mbland@acm.org, http://mike-bland.com/)
# Date:    2014-02-24
# License: Creative Commons Attribution 4.0 International (CC By 4.0)
#          http://creativecommons.org/licenses/by/4.0/deed.en_US
#
# What this script does
# ---------------------
# If needed, it will download the source packages from Apple and unpack them
# in the current directory, then apply the bugfix-and-test patch. Once the
# code is in place and the patch has been applied, it will use Xcode to build
# the code and execute tls_digest_test.
#
# You may need to set MAC_OS_SDK_VERSION below if you're not running
# Mavericks or otherwise targeting it as a platform.
#
# Details
# -------
# Since building the entire OS X Security library depends on headers and
# libraries not readily accessible, this script only compiles tls_digest.c and
# sslKeyExchange.c in addition to the  tls_digest_test binary.
#
# sslKeyExchange.o is not linked into tls_digest_test; it is compiled as
# verification that the HashHandshake() function extracted from several
# sslKeyExchange.c functions does compile.
#
# The very last command executes the tls_digest_test binary. It produces no
# output and a zero exit code on success, and prints error messages and a
# nonzero exit code on failure.
#
# How I got this to work
# ----------------------
# Within the Security-55471/libsecurity_ssl directory, I captured the output
# of:
#
# $ xcodebuild -n -configuration Debug -target libsecurity_ssl
#
# From that output I extracted the compile commands for tls_digest.c and
# sslKeyExchange.c and reformatted them as below, and produced a compile
# command for tls_digest_test.
#
# I added a libsecurity_ssl/include_stubs directory (and the corresponding -I
# flag below) to stub out the inaccessible corecrypto headers needed to
# compile sslKeyExchange.c, and added a symlink from that directory to the
# unpacked CF-855.11 source to avoid having to stub CoreFoundation headers.

MAC_OS_SDK_VERSION=MacOSX10.9
LIBSECURITY_SSL_ROOT=Security-55471/libsecurity_ssl
USAGE="Usage: $0 [help|clean]"

while test $# -ne 0; do
  case $1 in
  help|-h|-help|--help)
    echo ${USAGE}
    exit
    ;;
  clean)
    pushd ${LIBSECURITY_SSL_ROOT}
    xcodebuild -configuration Debug clean
    exit
    ;;
  *)
    echo "Unknown argument: $1"
    echo ${USAGE}
    exit 1
    ;;
  esac
  shift
done

SEC_URL="http://opensource.apple.com/tarballs/Security/Security-55471.tar.gz"
CF_URL="http://opensource.apple.com/tarballs/CF/CF-855.11.tar.gz"

for package in ${SEC_URL} ${CF_URL}
do
  tarball=$(/usr/bin/basename ${package})
  if test ! -f ${tarball}; then
    echo "Downloading ${package}"
    /usr/bin/curl -O ${package}
    if test $? -ne 0; then
      echo "Failed to download ${tarball}"
      echo "Aborting..."
      exit 1
    fi
    echo "Unpacking ${tarball}"
    /usr/bin/gzip -dc ${tarball} | /usr/bin/tar xf -
    if test $? -ne 0; then
      echo "Unpacking ${tarball} failed"
      echo "Aborting..."
      exit 1
    fi
  fi
done

BUGFIX_AND_TEST_PATCH=Security-55471-bugfix-and-test.patch
TLS_DIGEST=${LIBSECURITY_SSL_ROOT}/lib/tls_digest.c

if $(grep -q HashHandshake ${TLS_DIGEST}); then
  echo "Patch already applied..."
else
  if test ! -f ${BUGFIX_AND_TEST_PATCH}; then
    echo "${BUGFIX_AND_TEST_PATCH} not present in this directory"
    echo "Aborting..."
    exit 1
  fi

  echo "Applying ${BUGFIX_AND_TEST_PATCH}"
  /usr/bin/patch -p0 < ${BUGFIX_AND_TEST_PATCH}

  if test $? -ne 0; then
    echo "Failed to apply patch: ${BUGFIX_AND_TEST_PATCH}"
    echo "Aborting..."
    exit 1
  fi
fi

BUILD_OBJS_DIR=${LIBSECURITY_SSL_ROOT}/build/libsecurity_ssl.build/Debug/libsecurity_ssl.build/Objects-normal/x86_64

if test ! -f ${BUILD_OBJS_DIR}/tls_digest.dia; then
  # This will fail, but will produce the serialized diagnostics files and
  # directories needed by the rest of the script.
  echo "***   RUNNING PRELIMINARY XCODEBUILD TO GENERATE SERIALIZED   ***"
  echo "*** DIAGNOSTICS FILES; SOME ERRORS WILL APPEAR IN THE OUTPUT. ***"
  echo "***                   THESE ARE EXPECTED.                     ***"
  echo
  pushd ${LIBSECURITY_SSL_ROOT}
  xcodebuild -configuration Debug -target libsecurity_ssl
  popd
  echo
  echo "*** THE ABOVE ERRORS WERE EXPECTED; THE ACTUAL BUILDING ***"
  echo "***                     BEGINS NOW                      ***"
  echo
fi

COMPILE="/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang\
 -x c -arch x86_64 -fmessage-length=0 -fdiagnostics-show-note-include-stack\
 -fmacro-backtrace-limit=0 -std=gnu99 -Wno-trigraphs -fpascal-strings -O0\
 -Werror -Wno-missing-field-initializers -Wmissing-prototypes\
 -Wno-missing-braces -Wparentheses -Wswitch -Wno-unused-function\
 -Wno-unused-label -Wno-unused-parameter -Wunused-variable -Wunused-value\
 -Wno-empty-body -Wno-uninitialized -Wno-unknown-pragmas -Wno-shadow\
 -Wno-four-char-constants -Wno-conversion -Wno-constant-conversion\
 -Wno-int-conversion -Wno-bool-conversion -Wno-enum-conversion\
 -Wshorten-64-to-32 -Wpointer-sign -Wno-newline-eof -DDEBUG=1 -isysroot\
 /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/${MAC_OS_SDK_VERSION}.sdk\
 -fasm-blocks -fstrict-aliasing -Wno-deprecated-declarations\
 -mmacosx-version-min=10.9 -g -Wno-sign-conversion\
 -I${LIBSECURITY_SSL_ROOT}/build/libsecurity_ssl.build/Debug/libsecurity_ssl.build/libsecurity_ssl.hmap\
 -I${LIBSECURITY_SSL_ROOT}/build/Debug/include\
 -I${LIBSECURITY_SSL_ROOT}\
 -I${LIBSECURITY_SSL_ROOT}/../regressions\
 -I${LIBSECURITY_SSL_ROOT}/../include\
 -I${LIBSECURITY_SSL_ROOT}/build/Debug/derived_src\
 -I${LIBSECURITY_SSL_ROOT}/../utilities\
 -I${LIBSECURITY_SSL_ROOT}/../libsecurity_keychain\
 -I${LIBSECURITY_SSL_ROOT}/../libsecurity_keychain/libDER\
 -I${LIBSECURITY_SSL_ROOT}/build/Debug\
 -I/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/${MAC_OS_SDK_VERSION}.sdk/System/Library/Frameworks/CoreServices.framework/Frameworks/CarbonCore.framework/Headers\
 -I/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include\
 -I${LIBSECURITY_SSL_ROOT}/build/libsecurity_ssl.build/Debug/libsecurity_ssl.build/DerivedSources/x86_64\
 -I${LIBSECURITY_SSL_ROOT}/build/libsecurity_ssl.build/Debug/libsecurity_ssl.build/DerivedSources\
 -I${LIBSECURITY_SSL_ROOT}/include_stubs\
 -Wmost -Wno-four-char-constants -Wno-unknown-pragmas\
 -F${LIBSECURITY_SSL_ROOT}/build/libsecurity_ssl.build/Debug -MMD -MT dependencies -MF"

set -ex

${COMPILE} ${BUILD_OBJS_DIR}/tls_digest.d --serialize-diagnostics\
 ${BUILD_OBJS_DIR}/tls_digest.dia\
 -c ${LIBSECURITY_SSL_ROOT}/lib/tls_digest.c -o\
 ${BUILD_OBJS_DIR}/tls_digest.o

${COMPILE} ${BUILD_OBJS_DIR}/sslKeyExchange.d --serialize-diagnostics\
 ${BUILD_OBJS_DIR}/sslKeyExchange.dia\
 -c ${LIBSECURITY_SSL_ROOT}/lib/sslKeyExchange.c -o\
 ${BUILD_OBJS_DIR}/sslKeyExchange.o

TLS_DIGEST_TEST=${BUILD_OBJS_DIR}/tls_digest_test
${COMPILE} ${BUILD_OBJS_DIR}/tls_digest_test.d --serialize-diagnostics\
 ${BUILD_OBJS_DIR}/tls_digest_test.dia\
 ${LIBSECURITY_SSL_ROOT}/lib/tls_digest_test.c\
 ${LIBSECURITY_SSL_ROOT}/lib/tls_digest.c\
 ${LIBSECURITY_SSL_ROOT}/lib/sslMemory.c\
 ${LIBSECURITY_SSL_ROOT}/lib/sslDigests.c\
 -framework CoreFoundation -o ${TLS_DIGEST_TEST}

set +ex

echo "Executing ${TLS_DIGEST_TEST}"
${BUILD_OBJS_DIR}/tls_digest_test

if test $? -ne 0; then
  echo "Test failed"
  exit 1
fi
echo "Test passed"
