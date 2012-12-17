// Copyright 2012 Mike Bland. All rights reserved.

// Standard Template Library-like algorithms not available in the go standard
// libraries or any other known, available packages.
//
// This template, or portions thereof, should be copied to the package
// containing the type on which these operations should be applied, with Type
// and TypeSlice replaced with the proper type names (using global
// search-and-replace). The closure arguments can be replaced with permanent,
// dedicated functions or inlined comparison code where deemed necessary for
// performance reasons. The idea being, in the absence of generics, making
// such copies for only the types that absolutely require them is the best way
// to reuse this code and get decent performance.
package template

import "sort"

type (
	Type      int
	TypeSlice []*Type
)

// The following three functions implement sort.Interface for SortedCopy().
// See http://golang.org/pkg/sort/#Interface for a detailed example.
func (s TypeSlice) Len() int           { return len(s) }
func (s TypeSlice) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }
func (s TypeSlice) Less(i, j int) bool { return *s[i] < *s[j] }

// Returns true if lhs and rhs contain identical string values. eq must
// implement l == r.
// Lower bound: O(1) when lengths are different.
// Upper bound: O(len(lhs)) when all elements are equal.
func ElementsEqual(lhs, rhs TypeSlice, eq func(l, r *Type) bool) bool {
	if len(lhs) != len(rhs) {
		return false
	}
	for i, v := range lhs {
		if !eq(v, rhs[i]) {
			return false
		}
	}
	return true
}

// Returns a sorted copy of l.
// TypeSlice must implement sort.Interface.
func SortedCopy(l TypeSlice) (r TypeSlice) {
	r = make(TypeSlice, 0, len(l))
	r = append(r, l...)
	sort.Sort(r)
	return
}

// Finds strings in lhs not present in rhs. lhs and rhs must be sorted. lt
// must implement l < r.
// Lower and upper bound: O(len(lhs))
func SetDifference(lhs, rhs TypeSlice, lt func(l, r *Type) bool) TypeSlice {
	r := make(TypeSlice, 0, len(lhs))
	i := 0
	for j := 0; i != len(lhs) && j != len(rhs); {
		if lt(lhs[i], rhs[j]) {
			r = append(r, lhs[i])
			i++
		} else if lt(rhs[j], lhs[i]) {
			j++
		} else {
			i++
			j++
		}
	}
	return append(r, lhs[i:]...)
}

// Returns elements of lhs also contained in rhs. The order of elements in lhs
// is preserved. rhs must be sorted. geq must implement l >= r.
// Lower and upper bound: O(len(lhs) log len(rhs)).
func SetIntersectionUnordered(lhs, rhs TypeSlice, geq func(l, r *Type) bool) (r TypeSlice) {
	r = make(TypeSlice, 0, len(lhs))
	for _, v := range lhs {
		if i := sort.Search(len(rhs), func(i int) bool { return geq(rhs[i], v) }); i != len(rhs) && rhs[i] == v {
			r = append(r, v)
		}
	}
	return
}
