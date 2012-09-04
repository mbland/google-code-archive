// Copyright 2012 Mike Bland. All rights reserved.

// Standard Template Library-like algorithms not available in the go standard
// libraries or any other known, available packages.
//
// This package contains experiements with more generic algorithms based on
// the Comparator, Collector, and Sorter interfaces.
package algorithm

import "sort"

// Interface for types that maintain two collections of the same type, refered
// to as "Lhs" and "Rhs" (for left-hand side and right-hand side
// respectively), and perform comparison operations on elements between the
// two collections.
type Comparator interface {
	// Returns (len(Rhs), len(Rhs))
	Lengths() (int, int)

	// Returns true if Rhs[i] < Rhs[j]
	LhsLess(i, j int) bool

	// Returns true if Rhs[j] < Rhs[i]
	RhsLess(i, j int) bool

	// Returns true if Rhs[i] == Rhs[j]
	Equal(i, j int) bool
}

// Interface for types that maintain two collections of the same type, refered
// to as "Rhs" and "Rhs" (for left-hand side and right-hand side
// respectively), and collect elements from both in a third collection.
type Collector interface {
	Comparator

	// Adds Rhs[i] to the result collection
	CollectLhs(i int)

	// Adds Rhs[i] to the result collection
	CollectRhs(i int)

	// Adds Rhs[i:j] to the result collection
	CollectLhsSlice(i, j int)

	// Adds Rhs[i:j] to the result collection
	CollectRhsSlice(i, j int)
}

// Interface for types that maintain two collections of the same type, refered
// to as "Lhs" and "Rhs" (for left-hand side and right-hand side
// respectively), and search for elements in Lhs that appear in Rhs. Rhs must
// be sorted.
type Searcher interface {
	Collector

	// Searches for Lhs[i] in Rhs using the same semantics as
	// sort.Search().
	Search(i int) int
}

type StringComparator struct {
	Lhs, Rhs []string
}

func (c *StringComparator) Lengths() (len_lhs int, len_rhs int) {
	len_lhs, len_rhs = len(c.Lhs), len(c.Rhs)
	return
}

func (c *StringComparator) LhsLess(i, j int) bool {
	return c.Lhs[i] < c.Rhs[j]
}

func (c *StringComparator) RhsLess(i, j int) bool {
	return c.Rhs[j] < c.Lhs[i]
}

func (c *StringComparator) Equal(i, j int) bool {
	return c.Lhs[i] == c.Rhs[j]
}

type StringCollector struct {
	StringComparator
	Result []string
}

func (c *StringCollector) CollectLhs(i int) {
	c.Result = append(c.Result, c.Lhs[i])
}

func (c *StringCollector) CollectRhs(i int) {
	c.Result = append(c.Result, c.Rhs[i])
}

func (c *StringCollector) CollectLhsSlice(i, j int) {
	c.Result = append(c.Result, c.Lhs[i:j]...)
}

func (c *StringCollector) CollectRhsSlice(i, j int) {
	c.Result = append(c.Result, c.Rhs[i:j]...)
}

func NewStringCollector(lhs, rhs []string) (*StringCollector) {
	return &StringCollector{
		StringComparator{lhs, rhs},
		make([]string, 0, len(lhs)),
	}
}

type StringSearcher struct {
	StringCollector
}

func (s *StringSearcher) Search(i int) int {
	return sort.SearchStrings(s.Rhs, s.Lhs[i])
}

func NewStringSearcher(lhs, rhs []string) (*StringSearcher) {
	return &StringSearcher{*NewStringCollector(lhs, rhs)}
}

// Returns true if c.Lhs and c.Rhs contain identical values.
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

// Returns true if lhs and rhs contain identical string values.
func ElementsEqualStrings(lhs, rhs []string) bool {
	return ElementsEqual(&StringComparator{lhs, rhs})
}

// Returns a sorted copy of l.
func SortedCopyStrings(l []string) (r []string) {
	r = make([]string, 0, len(l))
	r = append(r, l...)
	sort.Strings(r)
	return
}

// Finds elements in lhs not present in rhs. lhs and rhs must be sorted.
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

// Finds strings in lhs not present in rhs. lhs and rhs must be sorted.
func SetDifferenceStrings(lhs, rhs []string) []string {
	c := NewStringCollector(lhs, rhs)
	SetDifference(c)
	return c.Result
}

// Returns elements of lhs also contained in rhs. The order of elements in lhs
// is preserved. rhs must be sorted.
func Contains(s Searcher) {
	lhs_len, rhs_len := s.Lengths()
	for i := 0; i != lhs_len; i++ {
		if j := s.Search(i); j != rhs_len && s.Equal(i, j) {
			s.CollectLhs(i)
		}
	}
	return
}

// Returns elements of lhs also contained in rhs. The order of elements in lhs
// is preserved. rhs must be sorted.
func ContainsStrings(lhs, rhs []string) []string {
	s := NewStringSearcher(lhs, rhs)
	Contains(s)
	return s.Result
}
