// Copyright 2012 Mike Bland. All rights reserved.

// Utilities for writing test assertions.
package testing

import (
	"fmt"
	"path/filepath"
	"runtime"
)

// Returns a string identifying the file and line of a test assertion failure.
//
// Somewhat stolen from the standard testing/testing.go:decorate(), this is
// used to implement helper functions (i.e. checkFoo()) that make use of
// t.Error() and other Testing.T methods. The t.*() functions grab the file
// and line from the call site. Since we're wrapping the t.*() functions in
// helpers, we need to grab the call site of the helper, not the t.*()
// invocation.
func FileAndLine() string {
	_, file, line, ok := runtime.Caller(2)
	if ok {
		return fmt.Sprintf("%s:%d", filepath.Base(file), line)
	}
	return "<unknown file>:1"
}
