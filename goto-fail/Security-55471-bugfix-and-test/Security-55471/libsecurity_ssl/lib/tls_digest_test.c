/*
 * Test file for the TLS handshake algorithm
 *
 * Part of the complete "goto fail" patch-and-test demonstration package:
 * http://goo.gl/tnvIUm
 *
 * Author:  Mike Bland (mbland@acm.org, http://mike-bland.com/)
 * Date:    2014-02-24
 * License: Creative Commons Attribution 4.0 International (CC By 4.0)
 *          http://creativecommons.org/licenses/by/4.0/deed.en_US
 */

#include "tls_digest.h"
/* Needed for the __security_debug() stub function */
#include "../../utilities/src/debugging.h"

#include <stdlib.h>
#include <stdio.h>

enum HandshakeResult {
    SUCCESS = 0,
    INIT_FAILURE = 1,
    UPDATE_CLIENT_FAILURE = 2,
    UPDATE_SERVER_FAILURE = 3,
    UPDATE_PARAMS_FAILURE = 4,
    FINAL_FAILURE = 5,
};

static const char* const HandshakeResultString(enum HandshakeResult r) {
  switch (r) {
#define HANDSHAKE_RESULT_CASE(x) case x:\
    return #x;\
    break
  HANDSHAKE_RESULT_CASE(SUCCESS);
  HANDSHAKE_RESULT_CASE(INIT_FAILURE);
  HANDSHAKE_RESULT_CASE(UPDATE_CLIENT_FAILURE);
  HANDSHAKE_RESULT_CASE(UPDATE_SERVER_FAILURE);
  HANDSHAKE_RESULT_CASE(UPDATE_PARAMS_FAILURE);
  HANDSHAKE_RESULT_CASE(FINAL_FAILURE);
#undef HANDSHAKE_RESULT_CASE
  default:
    break;
  }
  fprintf(stderr, "%s:%d: %s: FATAL ERROR: unknown HandshakeResult value: "
                  "%d\n", __FILE__, __LINE__, __func__, r);
  abort();
  return 0;
}

typedef struct
{
    HashReference ref;
    SSLBuffer client;
    SSLBuffer server;
    SSLBuffer params;
    SSLBuffer output;
    const char *test_case_name;
    enum HandshakeResult expected;
} HashHandshakeTestFixture;

static int HashHandshakeTestFailInit(SSLBuffer *digestCtx) {
  return INIT_FAILURE;
}

/* As a complete contrivance for the sake of this proof-of-concept, we'll
 * return a failure based on data->length.
 */
static int HashHandshakeTestUpdate(SSLBuffer *digestCtx,
    const SSLBuffer *data) {
  return (int)data->length;
}

static int HashHandshakeTestFailFinal(SSLBuffer *digestCtx,
    SSLBuffer *digest) {
  return FINAL_FAILURE;
}

static HashHandshakeTestFixture MakeFixture(const char *test_case_name) {
  HashHandshakeTestFixture fixture;
  fixture.ref = SSLHashNull;
  fixture.ref.update = HashHandshakeTestUpdate;
  fixture.test_case_name = test_case_name; 
  fixture.client.length = SUCCESS;
  fixture.server.length = SUCCESS;
  fixture.params.length = SUCCESS;
  return fixture;
}

/* Executes the handshake and returns zero if the result matches expected, one
 * otherwise. */
static int ExecuteHandshake(HashHandshakeTestFixture fixture) {
  const enum HandshakeResult actual = HashHandshake(
      &fixture.ref, &fixture.client, &fixture.server, &fixture.params,
      &fixture.output);

  if (actual != fixture.expected) {
    printf("%s failed: expected %s, received %s\n", fixture.test_case_name,
           HandshakeResultString(fixture.expected),
           HandshakeResultString(actual));
    return 1;
  }
  return 0;
}

static int TestHandshakeSuccess() {
  HashHandshakeTestFixture fixture = MakeFixture(__func__);
  fixture.expected = SUCCESS;
  return ExecuteHandshake(fixture);
}

static int TestHandshakeInitFailure() {
  HashHandshakeTestFixture fixture = MakeFixture(__func__);
  fixture.expected = INIT_FAILURE;
  fixture.ref.init = HashHandshakeTestFailInit;
  return ExecuteHandshake(fixture);
}

static int TestHandshakeUpdateClientFailure() {
  HashHandshakeTestFixture fixture = MakeFixture(__func__);
  fixture.expected = UPDATE_CLIENT_FAILURE;
  fixture.client.length = UPDATE_CLIENT_FAILURE;
  return ExecuteHandshake(fixture);
}

static int TestHandshakeUpdateServerFailure() {
  HashHandshakeTestFixture fixture = MakeFixture(__func__);
  fixture.expected = UPDATE_SERVER_FAILURE;
  fixture.server.length = UPDATE_SERVER_FAILURE;
  return ExecuteHandshake(fixture);
}

static int TestHandshakeUpdateParamsFailure() {
  HashHandshakeTestFixture fixture = MakeFixture(__func__);
  fixture.expected = UPDATE_PARAMS_FAILURE;
  fixture.params.length = UPDATE_PARAMS_FAILURE;
  return ExecuteHandshake(fixture);
}

static int TestHandshakeFinalFailure() {
  HashHandshakeTestFixture fixture = MakeFixture(__func__);
  fixture.expected = FINAL_FAILURE;
  fixture.ref.final = HashHandshakeTestFailFinal;
  return ExecuteHandshake(fixture);
}

/* A stub to allow linking this example */
void __security_debug(CFStringRef scope,
                      const char *function, const char *file, int line,
                      CFStringRef format, ...) {
}

int main(int argc, char *argv[]) {
  int num_failed = TestHandshakeSuccess() +
      TestHandshakeInitFailure() +
      TestHandshakeUpdateClientFailure() +
      TestHandshakeUpdateServerFailure() +
      TestHandshakeUpdateParamsFailure() +
      TestHandshakeFinalFailure();

  if (num_failed != 0) {
    printf("%d test%s failed\n", num_failed, num_failed != 1 ? "s" : "");
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
