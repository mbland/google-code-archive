// Copyright 2012 Mike Bland. All rights reserved.

package algorithm

import (
	std "code.google.com/p/mike-bland/go/algorithm"
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
		std.ElementsEqualStrings(lhs, rhs)
	}
}

func BenchmarkElementsEqualStringsExp(b *testing.B) {
	for i := 0; i != b.N; i++ {
		ElementsEqualStrings(lhs, rhs)
	}
}

func BenchmarkSetDifferenceStringsStd(b *testing.B) {
	for i := 0; i != b.N; i++ {
		std.SetDifferenceStrings(lhs, rhs)
	}
}

func BenchmarkSetDifferenceStringsExp(b *testing.B) {
	for i := 0; i != b.N; i++ {
		SetDifferenceStrings(lhs, rhs)
	}
}

func BenchmarkSetIntersectionUnorderedStringsStd(b *testing.B) {
	for i := 0; i != b.N; i++ {
		std.SetIntersectionUnorderedStrings(lhs, rhs)
	}
}

func BenchmarkSetIntersectionUnorderedStringsExp(b *testing.B) {
	for i := 0; i != b.N; i++ {
		SetIntersectionUnorderedStrings(lhs, rhs)
	}
}
