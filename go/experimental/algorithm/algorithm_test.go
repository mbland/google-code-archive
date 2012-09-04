package algorithm

import (
	msbtest "code.google.com/p/mike-bland/go/testing"
	"testing"
)

func checkElementsEqualStrings(msg string, a, b []string, t *testing.T) {
	if !ElementsEqualStrings(a, b) {
		t.Errorf("%s: %s not equal:\na: %s\nb: %s",
			msbtest.FileAndLine(), msg, a, b)
	}
}

func checkElementsNotEqualStrings(msg string, a, b []string, t *testing.T) {
	if ElementsEqualStrings(a, b) {
		t.Errorf("%s: %s equal, expected not:\na: %s\nb: %s",
			msbtest.FileAndLine(), msg, a, b)
	}
}

func TestElementsEqualStrings(t *testing.T) {
	checkElementsEqualStrings("empty slices", []string{}, []string{}, t)
	checkElementsEqualStrings("single element slices",
		[]string{"a"}, []string{"a"}, t)
	checkElementsEqualStrings("multiple element slices",
		[]string{"a", "b", "c"}, []string{"a", "b", "c"}, t)
}

func TestElementsNotEqualStrings(t *testing.T) {
	checkElementsNotEqualStrings("single element slices",
		[]string{"a"}, []string{"b"}, t)

	checkElementsNotEqualStrings("multiple element slices, last",
		[]string{"a", "b", "c"}, []string{"a", "b", "d"}, t)
	checkElementsNotEqualStrings("multiple element slices, middle",
		[]string{"a", "b", "c"}, []string{"a", "e", "c"}, t)
	checkElementsNotEqualStrings("multiple element slices, first",
		[]string{"a", "b", "c"}, []string{"f", "b", "c"}, t)
	checkElementsNotEqualStrings("multiple element slices, last",
		[]string{"a", "b", "g"}, []string{"a", "b", "c"}, t)
	checkElementsNotEqualStrings("multiple element slices, middle",
		[]string{"a", "h", "c"}, []string{"a", "b", "c"}, t)
	checkElementsNotEqualStrings("multiple element slices, first",
		[]string{"i", "b", "c"}, []string{"a", "b", "c"}, t)

	checkElementsNotEqualStrings("empty vs. nonempty slices",
		[]string{}, []string{"a"}, t)
	checkElementsNotEqualStrings("nonempty vs. empty slices",
		[]string{}, []string{"a"}, t)
	checkElementsNotEqualStrings("shorter vs. longer slices",
		[]string{"a", "b", "c"}, []string{"a", "b", "c", "d"}, t)
	checkElementsNotEqualStrings("longer vs. shorter slices",
		[]string{"a", "b", "c", "d"}, []string{"a", "b", "c"}, t)
}

func TestSortedCopyStrings(t *testing.T) {
	checkElementsEqualStrings("empty slices",
		[]string{}, SortedCopyStrings([]string{}), t)
	checkElementsEqualStrings("single element slices",
		[]string{"a"}, SortedCopyStrings([]string{"a"}), t)
	checkElementsEqualStrings("multiple element slices, already sorted",
		[]string{"a", "b", "c"},
		SortedCopyStrings([]string{"a", "b", "c"}), t)
	checkElementsEqualStrings(
		"multiple element slices, original not sorted",
		[]string{"a", "b", "c"},
		SortedCopyStrings([]string{"c", "a", "b"}), t)
}

func checkSetDifferenceStrings(msg string, expected, a, b []string,
	t *testing.T) {
	actual := SetDifferenceStrings(a, b)
	if !ElementsEqualStrings(expected, actual) {
		t.Errorf("%s: %s SetDifferenceStrings result unexpected:\n"+
			"a:        %s\n"+
			"b:        %s\n"+
			"expected: %s\n"+
			"actual:   %s\n",
			msbtest.FileAndLine(), msg, a, b, expected, actual)
	}
}

func TestSetDifferenceStrings(t *testing.T) {
	// Precondition: inputs must be sorted.
	checkSetDifferenceStrings("empty vs. empty",
		[]string{},
		[]string{}, []string{}, t)
	checkSetDifferenceStrings("equal single element",
		[]string{},
		[]string{"a"}, []string{"a"}, t)
	checkSetDifferenceStrings("equal multiple element",
		[]string{},
		[]string{"a", "b", "c"}, []string{"a", "b", "c"}, t)
	checkSetDifferenceStrings("empty vs. single element",
		[]string{},
		[]string{}, []string{"a"}, t)
	checkSetDifferenceStrings("single element vs. empty",
		[]string{"a"},
		[]string{"a"}, []string{}, t)
	checkSetDifferenceStrings("empty vs. multiple element",
		[]string{},
		[]string{}, []string{"a", "b", "c"}, t)
	checkSetDifferenceStrings("multiple element vs. empty",
		[]string{"a", "b", "c"},
		[]string{"a", "b", "c"}, []string{}, t)
	checkSetDifferenceStrings("different single element",
		[]string{"a"},
		[]string{"a"}, []string{"b"}, t)
	checkSetDifferenceStrings("different single element",
		[]string{"b"},
		[]string{"b"}, []string{"a"}, t)
	checkSetDifferenceStrings("first element not present",
		[]string{"a"},
		[]string{"a", "b", "c"}, []string{"b", "c"}, t)
	checkSetDifferenceStrings("first element not present",
		[]string{},
		[]string{"b", "c"}, []string{"a", "b", "c"}, t)
	checkSetDifferenceStrings("second element not present",
		[]string{"b"},
		[]string{"a", "b", "c"}, []string{"a", "c"}, t)
	checkSetDifferenceStrings("second element not present",
		[]string{},
		[]string{"a", "c"}, []string{"a", "b", "c"}, t)
	checkSetDifferenceStrings("third element not present",
		[]string{"c"},
		[]string{"a", "b", "c"}, []string{"a", "b"}, t)
	checkSetDifferenceStrings("third element not present",
		[]string{},
		[]string{"a", "b"}, []string{"a", "b", "c"}, t)
	checkSetDifferenceStrings("first and second not present",
		[]string{"a", "b"},
		[]string{"a", "b", "c"}, []string{"c"}, t)
	checkSetDifferenceStrings("first and second not present",
		[]string{},
		[]string{"c"}, []string{"a", "b", "c"}, t)
	checkSetDifferenceStrings("first and third not present",
		[]string{"a", "c"},
		[]string{"a", "b", "c"}, []string{"b"}, t)
	checkSetDifferenceStrings("first and third not present",
		[]string{},
		[]string{"b"}, []string{"a", "b", "c"}, t)
	checkSetDifferenceStrings("all different",
		[]string{"a", "b", "c"},
		[]string{"a", "b", "c"}, []string{"k", "l", "m"}, t)
	checkSetDifferenceStrings("all different",
		[]string{"k", "l", "m"},
		[]string{"k", "l", "m"}, []string{"a", "b", "c"}, t)
}

func checkContainsStrings(msg string, expected, a, b []string, t *testing.T) {
	actual := ContainsStrings(a, b)
	if !ElementsEqualStrings(expected, actual) {
		t.Errorf("%s: %s ContainsStrings result unexpected:\n"+
			"a:        %s\n"+
			"b:        %s\n"+
			"expected: %s\n"+
			"actual:   %s\n",
			msbtest.FileAndLine(), msg, a, b, expected, actual)
	}
}

func TestContainsStrings(t *testing.T) {
	// Precondition: RHS must be sorted
	checkContainsStrings("empty vs. empty", []string{},
		[]string{}, []string{}, t)
	checkContainsStrings("single element vs. empty", []string{},
		[]string{"a"}, []string{}, t)
	checkContainsStrings("empty vs. single element", []string{},
		[]string{}, []string{"a"}, t)
	checkContainsStrings("multiple element vs. empty", []string{},
		[]string{"a", "b", "c"}, []string{}, t)
	checkContainsStrings("empty vs. multiple element", []string{},
		[]string{}, []string{"a", "b", "c"}, t)
	checkContainsStrings("equal single element", []string{"a"},
		[]string{"a"}, []string{"a"}, t)
	checkContainsStrings("different single element", []string{},
		[]string{"a"}, []string{"b"}, t)
	checkContainsStrings("different single element", []string{},
		[]string{"b"}, []string{"a"}, t)
	checkContainsStrings("all equal sorted", []string{"a", "b", "c"},
		[]string{"a", "b", "c"}, []string{"a", "b", "c"}, t)
	checkContainsStrings("all equal unsorted", []string{"c", "a", "b"},
		[]string{"c", "a", "b"}, []string{"a", "b", "c"}, t)
	checkContainsStrings("first element missing", []string{"a", "b"},
		[]string{"c", "a", "b"}, []string{"a", "b"}, t)
	checkContainsStrings("second element missing", []string{"c", "b"},
		[]string{"c", "a", "b"}, []string{"b", "c"}, t)
	checkContainsStrings("third element missing", []string{"c", "a"},
		[]string{"c", "a", "b"}, []string{"a", "c"}, t)
	checkContainsStrings("first and second elements missing",
		[]string{"b"},
		[]string{"c", "a", "b"}, []string{"b"}, t)
	checkContainsStrings("first and third elements missing",
		[]string{"a"},
		[]string{"c", "a", "b"}, []string{"a"}, t)
	checkContainsStrings("second and third elements missing",
		[]string{"c"},
		[]string{"c", "a", "b"}, []string{"c"}, t)
	checkContainsStrings("all different",
		[]string{},
		[]string{"c", "a", "b"}, []string{"d", "e", "f"}, t)
}
