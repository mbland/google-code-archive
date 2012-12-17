// Copyright 2012 Mike Bland. All rights reserved.

package algorithm

import (
	std "code.google.com/p/mike-bland/go/algorithm/string"
	"code.google.com/p/mike-bland/go/experimental/algorithm"
	exp "code.google.com/p/mike-bland/go/experimental/algorithm/string"
	"testing"
)

var (
	lhs = []string{
		"a",
		"b",
		"c",
		"d",
		"e",
		"f",
		"g",
		"h",
		"i",
		"j",
	}
	rhs = []string{
		"a",
		"b",
		"c",
		"d",
		"e",
		"f",
		"g",
		"h",
		"i",
		"j",
	}
)

func BenchmarkElementsEqualStringsStd(b *testing.B) {
	for i := 0; i != b.N; i++ {
		std.ElementsEqual(lhs, rhs)
	}
}

func BenchmarkElementsEqualStringsExp(b *testing.B) {
	for i := 0; i != b.N; i++ {
		exp.ElementsEqual(lhs, rhs)
	}
}

func BenchmarkSetDifferenceStringsStd(b *testing.B) {
	for i := 0; i != b.N; i++ {
		std.SetDifference(lhs, rhs)
	}
}

func BenchmarkSetDifferenceStringsExp(b *testing.B) {
	for i := 0; i != b.N; i++ {
		exp.SetDifference(lhs, rhs)
	}
}

func BenchmarkSetIntersectionUnorderedStringsStd(b *testing.B) {
	for i := 0; i != b.N; i++ {
		std.SetIntersectionUnordered(lhs, rhs)
	}
}

func BenchmarkSetIntersectionUnorderedStringsExp(b *testing.B) {
	for i := 0; i != b.N; i++ {
		exp.SetIntersectionUnordered(lhs, rhs)
	}
}

// Same example types as taken from the standard sort package example, plus
// different Comparators. These will be used to implement different versions
// of ElementsEqual() for Organ types, and compare the performance of the
// hardcoded versions with the generic ElementsEqual() that uses Comparators.
type (
	Grams int
	Organ struct {
		Name   string
		Weight Grams
	}
	Organs                []*Organ
	OrganNameComparator   struct{ Lhs, Rhs Organs }
	OrganWeightComparator struct{ Lhs, Rhs Organs }
	OrganComparator       struct{ Lhs, Rhs Organs }
)

func NewOrganNameComparator(lhs, rhs Organs) *OrganNameComparator {
	return &OrganNameComparator{lhs, rhs}
}

func (c *OrganNameComparator) Lengths() (len_lhs, len_rhs int) {
	return len(c.Lhs), len(c.Rhs)
}

func (c *OrganNameComparator) LhsLess(i, j int) bool {
	return c.Lhs[i].Name < c.Rhs[j].Name
}

func (c *OrganNameComparator) RhsLess(i, j int) bool {
	return c.Rhs[j].Name < c.Lhs[i].Name
}

func (c *OrganNameComparator) Equal(i, j int) bool {
	return c.Lhs[i].Name == c.Rhs[j].Name
}

func NewOrganWeightComparator(lhs, rhs Organs) *OrganWeightComparator {
	return &OrganWeightComparator{lhs, rhs}
}

func (c *OrganWeightComparator) Lengths() (len_lhs, len_rhs int) {
	return len(c.Lhs), len(c.Rhs)
}

func (c *OrganWeightComparator) LhsLess(i, j int) bool {
	return c.Lhs[i].Weight < c.Rhs[j].Weight
}

func (c *OrganWeightComparator) RhsLess(i, j int) bool {
	return c.Rhs[j].Weight < c.Lhs[i].Weight
}

func (c *OrganWeightComparator) Equal(i, j int) bool {
	return c.Lhs[i].Weight == c.Rhs[j].Weight
}

func NewOrganComparator(lhs, rhs Organs) *OrganComparator {
	return &OrganComparator{lhs, rhs}
}

func (c *OrganComparator) Lengths() (len_lhs, len_rhs int) {
	return len(c.Lhs), len(c.Rhs)
}

func (c *OrganComparator) LhsLess(i, j int) bool {
	return c.Lhs[i].Name < c.Rhs[j].Name ||
		(c.Lhs[i].Name == c.Rhs[j].Name &&
			c.Lhs[i].Weight < c.Rhs[j].Weight)
}

func (c *OrganComparator) RhsLess(i, j int) bool {
	return c.Rhs[j].Name < c.Lhs[i].Name ||
		(c.Rhs[j].Name == c.Lhs[i].Name &&
			c.Rhs[j].Weight < c.Lhs[i].Weight)

}

func (c *OrganComparator) Equal(i, j int) bool {
	return c.Lhs[i].Name == c.Rhs[j].Name &&
		c.Lhs[i].Weight == c.Rhs[j].Weight
}

func OrganNameElementsEqual(lhs, rhs Organs) bool {
	if len(lhs) != len(rhs) {
		return false
	}
	for i, v := range lhs {
		if v.Name != rhs[i].Name {
			return false
		}
	}
	return true
}

func OrganWeightElementsEqual(lhs, rhs Organs) bool {
	if len(lhs) != len(rhs) {
		return false
	}
	for i, v := range lhs {
		if v.Weight != rhs[i].Weight {
			return false
		}
	}
	return true
}

func OrganElementsEqual(lhs, rhs Organs) bool {
	if len(lhs) != len(rhs) {
		return false
	}
	for i, v := range lhs {
		if v.Name != rhs[i].Name || v.Weight != rhs[i].Weight {
			return false
		}
	}
	return true
}

func OrganElementsEqualClosure(lhs, rhs Organs, eq func(l, r Organ) bool) bool {
	if len(lhs) != len(rhs) {
		return false
	}
	for i, v := range lhs {
		if !eq(*v, *rhs[i]) {
			return false
		}
	}
	return true
}

var (
	lhs_organs = Organs{
		{"brain", 1340},
		{"heart", 290},
		{"liver", 1494},
		{"pancreas", 131},
		{"prostate", 62},
		{"spleen", 162},
	}
	rhs_organs = Organs{
		{"brain", 1340},
		{"heart", 290},
		{"liver", 1494},
		{"pancreas", 131},
		{"prostate", 62},
		{"spleen", 162},
	}
)

func BenchmarkOrganNameElementsEqualHardcoded(b *testing.B) {
	for i := 0; i != b.N; i++ {
		OrganNameElementsEqual(lhs_organs, rhs_organs)
	}
}

func BenchmarkOrganNameElementsEqualClosure(b *testing.B) {
	for i := 0; i != b.N; i++ {
		OrganElementsEqualClosure(lhs_organs, rhs_organs,
			func(l, r Organ) bool { return l.Name == r.Name })
	}
}

func BenchmarkOrganNameElementsEqualGeneric(b *testing.B) {
	for i := 0; i != b.N; i++ {
		algorithm.ElementsEqual(NewOrganNameComparator(lhs_organs, rhs_organs))
	}
}

func BenchmarkOrganWeightElementsEqualHardcoded(b *testing.B) {
	for i := 0; i != b.N; i++ {
		OrganWeightElementsEqual(lhs_organs, rhs_organs)
	}
}

func BenchmarkOrganWeightElementsEqualClosure(b *testing.B) {
	for i := 0; i != b.N; i++ {
		OrganElementsEqualClosure(lhs_organs, rhs_organs,
			func(l, r Organ) bool { return l.Weight == r.Weight })
	}
}

func BenchmarkOrganWeightElementsEqualGeneric(b *testing.B) {
	for i := 0; i != b.N; i++ {
		algorithm.ElementsEqual(NewOrganWeightComparator(lhs_organs, rhs_organs))
	}
}

func BenchmarkOrganElementsEqualHardcoded(b *testing.B) {
	for i := 0; i != b.N; i++ {
		OrganElementsEqual(lhs_organs, rhs_organs)
	}
}

func BenchmarkOrganElementsEqualClosure(b *testing.B) {
	for i := 0; i != b.N; i++ {
		OrganElementsEqualClosure(lhs_organs, rhs_organs,
			func(l, r Organ) bool { return l.Name == r.Name && l.Weight == r.Weight })
	}
}

func BenchmarkOrganElementsEqualGeneric(b *testing.B) {
	for i := 0; i != b.N; i++ {
		algorithm.ElementsEqual(NewOrganComparator(lhs_organs, rhs_organs))
	}
}
