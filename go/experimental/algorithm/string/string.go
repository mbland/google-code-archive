// Copyright 2012 Mike Bland. All rights reserved.

// Implementation of algorithm interfaces for []string, plus convenience
// wrappers for algorithms.

package string

import "code.google.com/p/mike-bland/go/experimental/algorithm"
import "sort"

// Returns a sorted copy of l.
func SortedCopy(l []string) (r []string) {
	r = make([]string, 0, len(l))
	r = append(r, l...)
	sort.Strings(r)
	return
}

type StringComparator struct {
	Lhs, Rhs []string
}

type StringCollector struct {
	StringComparator
	Result []string
}

// Rhs must be sorted.
type StringSearcher struct {
	StringCollector
}

// Returns an initialized StringCollector.
func NewStringCollector(lhs, rhs []string) *StringCollector {
	return &StringCollector{
		StringComparator{lhs, rhs},
		make([]string, 0, len(lhs)),
	}
}

// Returns an initialized StringSearcher.
func NewStringSearcher(lhs, rhs []string) *StringSearcher {
	return &StringSearcher{*NewStringCollector(lhs, rhs)}
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

func (s *StringSearcher) Search(i int) int {
	return sort.SearchStrings(s.Rhs, s.Lhs[i])
}

// Returns true if lhs and rhs contain identical string values.
func ElementsEqual(lhs, rhs []string) bool {
	return algorithm.ElementsEqual(&StringComparator{lhs, rhs})
}

// Finds strings in lhs not present in rhs. lhs and rhs must be sorted.
func SetDifference(lhs, rhs []string) []string {
	c := NewStringCollector(lhs, rhs)
	algorithm.SetDifference(c)
	return c.Result
}

// Returns elements of lhs also contained in rhs. The order of elements in lhs
// is preserved. rhs must be sorted.
func SetIntersectionUnordered(lhs, rhs []string) []string {
	s := NewStringSearcher(lhs, rhs)
	algorithm.SetIntersectionUnordered(s)
	return s.Result
}
