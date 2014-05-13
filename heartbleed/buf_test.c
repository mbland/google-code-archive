/*
 * Example unit test demonstrating how to detect buffer errors.
 *
 * Author:  Mike Bland (mbland@acm.org, http://mike-bland.com/)
 * Date:    2014-05-13
 * License: Creative Commons Attribution 4.0 International (CC By 4.0)
 *          http://creativecommons.org/licenses/by/4.0/deed.en_US
 *
 * URL:
 * https://code.google.com/p/mike-bland/source/browse/heartbleed/buf_test.c
 *
 * This is an example unit test demonstrating how to test for potential buffer
 * handling issues in general as described in the "Heartbleed: Break It Up,
 * Break It Down" section of "Goto Fail, Heartbleed, and Unit Testing
 * Culture":
 *
 * http://martinfowler.com/articles/testing-culture.html
 *
 * USAGE:
 * -----
 * To build and execute the test:
 *   $ cc -g buf_test.c -o buf_test
 *   $ ./buf_test
 *
 * All of the test cases should fail; TestNullInput() will segfault if
 * uncommented. As an exercise, modify func() to get all the tests to pass.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t buf_size_t;

#define MAX_BUF_SIZE (buf_size_t)-1

uint8_t *func(uint8_t *input, size_t sz) {
  buf_size_t buf_sz = sz;
  uint8_t *buf = malloc(buf_sz);
  memcpy(buf, input, (buf_size_t)(buf_sz + 10));
  return buf;
}

/* input and expected must be allocated on the heap */
typedef struct {
  const char *test_case_name;
  uint8_t    *input;
  size_t      size;
  uint8_t    *expected;
} FuncFixture;

static FuncFixture SetUp(const char *const test_case_name) {
  FuncFixture fixture;
  memset(&fixture, 0, sizeof(fixture));
  fixture.test_case_name = test_case_name;
  return fixture;
}

static void TearDown(FuncFixture fixture) {
  free(fixture.input);
  free(fixture.expected);
}

static int ExecuteFunc(FuncFixture fixture) {
  int result = 0;
  uint8_t *buf = func(fixture.input, fixture.size);

  if (fixture.expected == NULL) {
    if (buf != NULL) {
      fprintf(stderr, "%s failed:\n  expected: NULL\n"
                      "  received: \"%s\" (length %lu)\n",
              fixture.test_case_name, buf, strlen((char*)buf));
      result = 1;
    }
  } else if (buf == NULL) {
    fprintf(stderr, "%s failed:\n  expected: \"%s\" (length %lu)\n"
                    "  received NULL\n",
            fixture.test_case_name, fixture.expected,
            strlen((char*)fixture.expected));
    result = 1;
  } else if (strcmp((char*)buf, (char*)fixture.expected)) {
    fprintf(stderr, "%s failed:\n  expected: \"%s\" (length %lu)\n"
                    "  received: \"%s\" (length %lu)\n",
            fixture.test_case_name, fixture.expected,
            strlen((char*)fixture.expected), buf, strlen((char*)buf));
    result = 1;
  }
  free(buf);
  TearDown(fixture);
  return result;
}

static int TestNullInput() {
  FuncFixture fixture = SetUp(__func__);

  fixture.input = NULL;
  fixture.size = 0;
  fixture.expected = NULL;
  return ExecuteFunc(fixture);
}

static int TestEmptyInput() {
  FuncFixture fixture = SetUp(__func__);

  fixture.input = (uint8_t*)strdup("");
  fixture.size = 0;
  fixture.expected = NULL;
  return ExecuteFunc(fixture);
}

static int TestOnlyCopySpecifiedNumberOfCharacters() {
  FuncFixture fixture = SetUp(__func__);

  fixture.input = (uint8_t*)strdup("This is an OK input");
  fixture.expected = (uint8_t*)strdup("This");
  fixture.size = strlen((char*)fixture.expected);
  return ExecuteFunc(fixture);
}

static int TestMaxInputSize() {
  FuncFixture fixture = SetUp(__func__);

  fixture.size = MAX_BUF_SIZE;
  fixture.input = (uint8_t*)malloc(fixture.size + 1);
  memset(fixture.input, '#', fixture.size);
  fixture.input[fixture.size] = '\0';
  fixture.expected = (uint8_t*)strdup((char*)fixture.input);
  return ExecuteFunc(fixture);
}

static int TestOverMaxInputSize() {
  FuncFixture fixture = SetUp(__func__);

  fixture.size = MAX_BUF_SIZE + 1;
  fixture.input = (uint8_t*)malloc(fixture.size + 1);
  memset(fixture.input, '#', fixture.size);
  fixture.input[fixture.size] = '\0';
  fixture.expected = NULL;
  return ExecuteFunc(fixture);
}

int main(int argc, char* argv[]) {
  int num_failed =
      /* Including TestNullInput() will cause a segfault unless func() is
       * fixed */
      /* TestNullInput() + */
      TestEmptyInput() +
      TestOnlyCopySpecifiedNumberOfCharacters() +
      TestMaxInputSize() +
      TestOverMaxInputSize() +
      0;
  if (num_failed != 0) {
    printf("%d test%s failed\n", num_failed, num_failed != 1 ? "s" : "");
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
