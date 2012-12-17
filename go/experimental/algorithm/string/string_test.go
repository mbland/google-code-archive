package string

import (
	msbtest "code.google.com/p/mike-bland/go/testing"
	"testing"
)

func checkElementsEqual(msg string, a, b []string, t *testing.T) {
	if !ElementsEqual(a, b) {
		t.Errorf("%s: %s not equal:\na: %s\nb: %s",
			msbtest.FileAndLine(), msg, a, b)
	}
}

func checkElementsNotEqual(msg string, a, b []string, t *testing.T) {
	if ElementsEqual(a, b) {
		t.Errorf("%s: %s equal, expected not:\na: %s\nb: %s",
			msbtest.FileAndLine(), msg, a, b)
	}
}

func TestElementsEqual(t *testing.T) {
	checkElementsEqual("empty slices", []string{}, []string{}, t)
	checkElementsEqual("single element slices",
		[]string{"a"}, []string{"a"}, t)
	checkElementsEqual("multiple element slices",
		[]string{"a", "b", "c"}, []string{"a", "b", "c"}, t)
}

func TestElementsNotEqual(t *testing.T) {
	checkElementsNotEqual("single element slices",
		[]string{"a"}, []string{"b"}, t)

	checkElementsNotEqual("multiple element slices, last",
		[]string{"a", "b", "c"}, []string{"a", "b", "d"}, t)
	checkElementsNotEqual("multiple element slices, middle",
		[]string{"a", "b", "c"}, []string{"a", "e", "c"}, t)
	checkElementsNotEqual("multiple element slices, first",
		[]string{"a", "b", "c"}, []string{"f", "b", "c"}, t)
	checkElementsNotEqual("multiple element slices, last",
		[]string{"a", "b", "g"}, []string{"a", "b", "c"}, t)
	checkElementsNotEqual("multiple element slices, middle",
		[]string{"a", "h", "c"}, []string{"a", "b", "c"}, t)
	checkElementsNotEqual("multiple element slices, first",
		[]string{"i", "b", "c"}, []string{"a", "b", "c"}, t)

	checkElementsNotEqual("empty vs. nonempty slices",
		[]string{}, []string{"a"}, t)
	checkElementsNotEqual("nonempty vs. empty slices",
		[]string{}, []string{"a"}, t)
	checkElementsNotEqual("shorter vs. longer slices",
		[]string{"a", "b", "c"}, []string{"a", "b", "c", "d"}, t)
	checkElementsNotEqual("longer vs. shorter slices",
		[]string{"a", "b", "c", "d"}, []string{"a", "b", "c"}, t)
}

func TestSortedCopy(t *testing.T) {
	checkElementsEqual("empty slices",
		[]string{}, SortedCopy([]string{}), t)
	checkElementsEqual("single element slices",
		[]string{"a"}, SortedCopy([]string{"a"}), t)
	checkElementsEqual("multiple element slices, already sorted",
		[]string{"a", "b", "c"},
		SortedCopy([]string{"a", "b", "c"}), t)
	checkElementsEqual(
		"multiple element slices, original not sorted",
		[]string{"a", "b", "c"},
		SortedCopy([]string{"c", "a", "b"}), t)
}

func checkSetDifference(msg string, expected, a, b []string,
	t *testing.T) {
	actual := SetDifference(a, b)
	if !ElementsEqual(expected, actual) {
		t.Errorf("%s: %s SetDifference result unexpected:\n"+
			"a:        %s\n"+
			"b:        %s\n"+
			"expected: %s\n"+
			"actual:   %s\n",
			msbtest.FileAndLine(), msg, a, b, expected, actual)
	}
}

func TestSetDifference(t *testing.T) {
	// Precondition: inputs must be sorted.
	checkSetDifference("empty vs. empty",
		[]string{},
		[]string{}, []string{}, t)
	checkSetDifference("equal single element",
		[]string{},
		[]string{"a"}, []string{"a"}, t)
	checkSetDifference("equal multiple element",
		[]string{},
		[]string{"a", "b", "c"}, []string{"a", "b", "c"}, t)
	checkSetDifference("empty vs. single element",
		[]string{},
		[]string{}, []string{"a"}, t)
	checkSetDifference("single element vs. empty",
		[]string{"a"},
		[]string{"a"}, []string{}, t)
	checkSetDifference("empty vs. multiple element",
		[]string{},
		[]string{}, []string{"a", "b", "c"}, t)
	checkSetDifference("multiple element vs. empty",
		[]string{"a", "b", "c"},
		[]string{"a", "b", "c"}, []string{}, t)
	checkSetDifference("different single element",
		[]string{"a"},
		[]string{"a"}, []string{"b"}, t)
	checkSetDifference("different single element",
		[]string{"b"},
		[]string{"b"}, []string{"a"}, t)
	checkSetDifference("first element not present",
		[]string{"a"},
		[]string{"a", "b", "c"}, []string{"b", "c"}, t)
	checkSetDifference("first element not present",
		[]string{},
		[]string{"b", "c"}, []string{"a", "b", "c"}, t)
	checkSetDifference("second element not present",
		[]string{"b"},
		[]string{"a", "b", "c"}, []string{"a", "c"}, t)
	checkSetDifference("second element not present",
		[]string{},
		[]string{"a", "c"}, []string{"a", "b", "c"}, t)
	checkSetDifference("third element not present",
		[]string{"c"},
		[]string{"a", "b", "c"}, []string{"a", "b"}, t)
	checkSetDifference("third element not present",
		[]string{},
		[]string{"a", "b"}, []string{"a", "b", "c"}, t)
	checkSetDifference("first and second not present",
		[]string{"a", "b"},
		[]string{"a", "b", "c"}, []string{"c"}, t)
	checkSetDifference("first and second not present",
		[]string{},
		[]string{"c"}, []string{"a", "b", "c"}, t)
	checkSetDifference("first and third not present",
		[]string{"a", "c"},
		[]string{"a", "b", "c"}, []string{"b"}, t)
	checkSetDifference("first and third not present",
		[]string{},
		[]string{"b"}, []string{"a", "b", "c"}, t)
	checkSetDifference("all different",
		[]string{"a", "b", "c"},
		[]string{"a", "b", "c"}, []string{"k", "l", "m"}, t)
	checkSetDifference("all different",
		[]string{"k", "l", "m"},
		[]string{"k", "l", "m"}, []string{"a", "b", "c"}, t)
}

func checkSetIntersectionUnordered(msg string, expected, a, b []string,
	t *testing.T) {
	actual := SetIntersectionUnordered(a, b)
	if !ElementsEqual(expected, actual) {
		t.Errorf("%s: %s SetIntersectionUnordered result unexpected:\n"+
			"a:        %s\n"+
			"b:        %s\n"+
			"expected: %s\n"+
			"actual:   %s\n",
			msbtest.FileAndLine(), msg, a, b, expected, actual)
	}
}

func TestSetIntersectionUnordered(t *testing.T) {
	// Precondition: RHS must be sorted
	checkSetIntersectionUnordered("empty vs. empty", []string{},
		[]string{}, []string{}, t)
	checkSetIntersectionUnordered("single element vs. empty", []string{},
		[]string{"a"}, []string{}, t)
	checkSetIntersectionUnordered("empty vs. single element", []string{},
		[]string{}, []string{"a"}, t)
	checkSetIntersectionUnordered("multiple element vs. empty", []string{},
		[]string{"a", "b", "c"}, []string{}, t)
	checkSetIntersectionUnordered("empty vs. multiple element", []string{},
		[]string{}, []string{"a", "b", "c"}, t)
	checkSetIntersectionUnordered("equal single element", []string{"a"},
		[]string{"a"}, []string{"a"}, t)
	checkSetIntersectionUnordered("different single element", []string{},
		[]string{"a"}, []string{"b"}, t)
	checkSetIntersectionUnordered("different single element", []string{},
		[]string{"b"}, []string{"a"}, t)
	checkSetIntersectionUnordered("all equal sorted", []string{"a", "b", "c"},
		[]string{"a", "b", "c"}, []string{"a", "b", "c"}, t)
	checkSetIntersectionUnordered("all equal unsorted", []string{"c", "a", "b"},
		[]string{"c", "a", "b"}, []string{"a", "b", "c"}, t)
	checkSetIntersectionUnordered("first element missing", []string{"a", "b"},
		[]string{"c", "a", "b"}, []string{"a", "b"}, t)
	checkSetIntersectionUnordered("second element missing", []string{"c", "b"},
		[]string{"c", "a", "b"}, []string{"b", "c"}, t)
	checkSetIntersectionUnordered("third element missing", []string{"c", "a"},
		[]string{"c", "a", "b"}, []string{"a", "c"}, t)
	checkSetIntersectionUnordered("first and second elements missing",
		[]string{"b"},
		[]string{"c", "a", "b"}, []string{"b"}, t)
	checkSetIntersectionUnordered("first and third elements missing",
		[]string{"a"},
		[]string{"c", "a", "b"}, []string{"a"}, t)
	checkSetIntersectionUnordered("second and third elements missing",
		[]string{"c"},
		[]string{"c", "a", "b"}, []string{"c"}, t)
	checkSetIntersectionUnordered("all different",
		[]string{},
		[]string{"c", "a", "b"}, []string{"d", "e", "f"}, t)
}
