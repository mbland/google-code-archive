// Copyright 2012 Mike Bland. All rights reserved.

// Standard Template Library-like algorithms not available in the go standard
// libraries or any other known, available packages.
//
// This package contains experiements with more generic algorithms based on
// the Comparator, Collector, and Sorter interfaces.
//
// Each of the Comparator, Collector, and Sorter interfaces are assumed to
// contain two collections of the same type, or collections of different types
// that can be meaningfully compared. The collections are assumed to be
// slices, indexable by an integer value. The two collections are referred to
// as "Lhs" and "Rhs", for left-hand side and right-hand side, repectively.
package algorithm

// Interface for comparing elements between the Lhs and Rhs collections.
type Comparator interface {
	// Returns (len(Lhs), len(Rhs)).
	Lengths() (int, int)

	// Returns true if Lhs[i] < Rhs[j].
	LhsLess(i, j int) bool

	// Returns true if Rhs[j] < Lhs[i]. Notice the index order is the same
	// as LhsLess().
	RhsLess(i, j int) bool

	// Returns true if Lhs[i] == Rhs[j]
	Equal(i, j int) bool
}

// Interface for comparing and collecting elements from Lhs and Rhs in a third
// collection, Result.
type Collector interface {
	Comparator

	// Adds Lhs[i] to the result collection
	CollectLhs(i int)

	// Adds Rhs[i] to the result collection
	CollectRhs(i int)

	// Adds Lhs[i:j] to the result collection
	CollectLhsSlice(i, j int)

	// Adds Rhs[i:j] to the result collection
	CollectRhsSlice(i, j int)
}

// Interface for searching for elements in Lhs that appear in Rhs and
// collecting the results.
type Searcher interface {
	Collector

	// Searches for Lhs[i] in Rhs using the same semantics as
	// sort.Search().
	Search(i int) int
}

// Returns true if c.Lhs and c.Rhs contain identical values.
// Lower bound: O(1) when lengths are different.
// Upper bound: O(len(c.Lhs)) when all elements are equal.
func ElementsEqual(c Comparator) bool {
	len_lhs, len_rhs := c.Lengths()
	if len_lhs != len_rhs {
		return false
	}
	for i := 0; i != len_lhs; i++ {
		if !c.Equal(i, i) {
			return false
		}
	}
	return true
}

// Finds elements in c.Lhs not present in c.Rhs. c.Lhs and c.Rhs must be
// sorted.
// Lower and upper bound: O(len(c.Lhs))
func SetDifference(c Collector) {
	len_lhs, len_rhs := c.Lengths()
	i := 0
	for j := 0; i != len_lhs && j != len_rhs; {
		if c.LhsLess(i, j) {
			c.CollectLhs(i)
			i++
		} else if c.RhsLess(i, j) {
			j++
		} else {
			i++
			j++
		}
	}
	c.CollectLhsSlice(i, len_lhs)
}

// Returns elements of s.Lhs also contained in s.Rhs. The order of elements in
// s.Lhs is preserved.
// Lower and upper bound: O(len(c.Lhs) log len(c.Rhs)).
func Contains(s Searcher) {
	lhs_len, rhs_len := s.Lengths()
	for i := 0; i != lhs_len; i++ {
		if j := s.Search(i); j != rhs_len && s.Equal(i, j) {
			s.CollectLhs(i)
		}
	}
}
