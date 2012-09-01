// Copyright 2012 Mike Bland. All rights reserved.

// Standard Template Library-like algorithms not available in the go standard
// libraries or any other known, available packages.
package algorithm

import "sort"

// Returns true if lhs and rhs contain identical string values.
func ElementsEqualStrings(lhs, rhs []string) bool {
	if len(lhs) != len(rhs) {
		return false
	}
	for i, v := range lhs {
		if v != rhs[i] {
			return false
		}
	}
	return true
}

// Returns a sorted copy of l.
func SortedCopyStrings(l []string) (r []string) {
	r = make([]string, 0, len(l))
	r = append(r, l...)
	sort.Strings(r)
	return
}

// Finds strings in lhs not present in rhs. lhs and rhs must be sorted.
func SetDifferenceStrings(lhs, rhs []string) []string {
	r := make([]string, 0, len(lhs))
	i := 0
	for j := 0; i != len(lhs) && j != len(rhs); {
		if lhs[i] < rhs[j] {
			r = append(r, lhs[i])
			i++
		} else if rhs[j] < lhs[i] {
			j++
		} else {
			i++
			j++
		}
	}
	return append(r, lhs[i:]...)
}

// Returns elements of lhs also contained in rhs. The order of elements in lhs
// is preserved. rhs must be sorted.
func ContainsStrings(lhs, rhs []string) (r []string) {
	r = make([]string, 0, len(lhs))
	for _, v := range lhs {
		if i := sort.SearchStrings(rhs, v); i != len(rhs) && rhs[i] == v {
			r = append(r, v)
		}
	}
	return
}
