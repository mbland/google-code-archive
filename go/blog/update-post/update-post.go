// Copyright 2012 Mike Bland. All rights reserved.

// Updates a textile blog post by expanding non-textile features.
//
// Makes some of the formatting I use in my blog that isn't baked into textile
// easier to maintain, particularly footnotes and tables of contents.
//
// Reads input from standard input and prints result to standard output. All
// updates are idempotent.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"code.google.com/p/mike-bland/go/blog/format"
	"os"
)

func usage() {
	fmt.Fprintf(os.Stderr, "This command takes no arguments\n")
	fmt.Fprintf(os.Stderr, "usage: %s < blog_post_file > output_file\n",
		os.Args[0])
	os.Exit(1)
}

func main() {
	flag.Usage = usage
	flag.Parse()
	if len(flag.Args()) != 0 {
		usage()
	}
	msg := format.UpdatePost(
		[]format.Updater{
			format.NewFootnoteUpdater(),
			new(format.TableOfContentsUpdater),
		},
		bufio.NewReader(os.Stdin), os.Stdout)
	if len(msg) != 0 {
		fmt.Fprintln(os.Stderr, msg)
	}
}
