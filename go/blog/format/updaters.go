// Copyright 2012 Mike Bland. All rights reserved.

package format

import (
	"bufio"
	"bytes"
	"code.google.com/p/mike-bland/go/algorithm"
	"fmt"
	"io"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

var (
	// Matches an existing footnote reference from the text.
	// First group: note title; second group: note index
	kRef = regexp.MustCompile(
		`\["\(#([a-z-]+)-r([0-9]+)\)\. \^[0-9]+\^":#[a-z-]+-[0-9]+\]`)

	// Matches an existing footnote target from the text.
	// First group: note title; second group: note index
	kTarget = regexp.MustCompile(
		`^\["\(#([a-z-]+)-([0-9]+)\)\. \^[0-9]+\^":#[a-z-]+-r[0-9]+\]`)

	// Matches a new footnote from the text.
	// First group: note title; second group: note text
	kNewNote = regexp.MustCompile(`\[#([a-z-]+): ([^\]]+)\]`)

	// Matches a section headline.
	// First group: headline ID; second group: headline text
	kHeadline = regexp.MustCompile(`^h3\(section#([a-zA-Z0-9-]+)\)\. (.+)`)

	// Matches a Textile-style link.
	// Group: link text
	kTextileLink = regexp.MustCompile(`\[?"([^"]+)":[^ ]+\]?`)

	// Matches Textile link characters after a headline has been
	// processed.
	kHeadlineError = regexp.MustCompile(`["\[\]]`)
)

const (
	// Start-of-line pattern indicating the presence of a Table of
	// Contents.
	kTableOfContents = `p(toc).`
)

// Applies each updater to each line of input, writing the results to output.
func UpdatePost(updaters []Updater, input *bufio.Reader,
	output io.Writer) string {
	first_pass := updatePostPass(`first`, input, updaters,
		func(u Updater, l string, b *bufio.Writer) string {
			return u.ParseLineFirstPass(l, b)
		})
	second_pass := updatePostPass(`second`,
		bufio.NewReader(strings.NewReader(first_pass)), updaters,
		func(u Updater, l string, b *bufio.Writer) string {
			return u.ParseLineSecondPass(l, b)
		})
	_, err := io.WriteString(output, second_pass)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error writing to output: %s\n", err)
		os.Exit(1)
	}

	var msg bytes.Buffer
	for _, u := range updaters {
		m := u.UpdateMessage()
		if len(m) != 0 {
			if msg.Len() != 0 {
				msg.WriteString("; ")
			}
			msg.WriteString(m)
		}
	}
	return msg.String()
}

func updatePostPass(label string, input *bufio.Reader, updaters []Updater,
	parse func(Updater, string, *bufio.Writer) string) string {
	var buf bytes.Buffer
	writer := bufio.NewWriter(&buf)
	line, err := input.ReadString('\n')
	for ; err == nil; line, err = input.ReadString('\n') {
		for _, u := range updaters {
			line = parse(u, line, writer)
		}
		writer.WriteString(line)
	}
	if err != io.EOF {
		fmt.Fprintf(os.Stderr, "Error during %s pass: %s\n",
			label, err)
		os.Exit(1)
	}
	writer.Flush()
	return buf.String()
}

// Returns a properly-initialized FootnoteUpdater.
func NewFootnoteUpdater() *FootnoteUpdater {
	// notes contains the empty string as its first element to start the
	// footnote index at one when writing out the footnotes div.
	return &FootnoteUpdater{
		notes:           make([]string, 1),
		existing_order:  make([]int, 0),
		new_notes:       make([]string, 0),
		i:               1,
		num_new_notes:   0,
		in_footnote_div: false}
}

// Expands new footnotes and adjusts existing footnote references. Rewrites
// the footnote section to contain all footnotes in the correct order.
func (fnu *FootnoteUpdater) ParseLineFirstPass(
	line string, buf *bufio.Writer) string {
	if line == "<div class=\"footnote\">\n" {
		fnu.in_footnote_div = true
		fnu.i = 1
	}

	if !fnu.in_footnote_div {
		for m := kNewNote.FindStringSubmatchIndex(line); m != nil; m = kNewNote.FindStringSubmatchIndex(line) {
			title, text := line[m[2]:m[3]], line[m[4]:m[5]]
			line = fmt.Sprintf("%s[\"(#%s-r0). ^0^\":#%s-0]%s",
				line[:m[0]], title, title, line[m[1]:])
			fnu.new_notes = append(fnu.new_notes, text)
			fnu.num_new_notes++
		}

		for i, m := 0, kRef.FindStringSubmatchIndex(line); m != nil; m = kRef.FindStringSubmatchIndex(line[i:]) {
			title, n := line[m[2]+i:m[3]+i], line[m[4]+i:m[5]+i]
			ref := fmt.Sprintf(`["(#%s-r%d). ^%d^":#%s-%d]`,
				title, fnu.i, fnu.i, title, fnu.i)
			line = fmt.Sprintf(`%s%s%s`, line[:m[0]+i], ref,
				line[m[1]+i:])
			i += m[0] + len(ref)

			note := n
			if n == "0" {
				note = fmt.Sprintf(
					"[\"(#%s-%d). ^%d^\":#%s-r%d]%s\n",
					title, fnu.i, fnu.i, title, fnu.i,
					fnu.new_notes[0])
				fnu.new_notes = fnu.new_notes[1:]
			} else {
				j, _ := strconv.Atoi(n)
				fnu.existing_order = append(
					fnu.existing_order, j)
			}
			fnu.notes = append(fnu.notes, note)
			fnu.i++
		}
	} else if m := kTarget.FindStringSubmatchIndex(line); m != nil {
		title, index := line[m[2]:m[3]], line[m[4]:m[5]]
		i := 1
		for ; i != len(fnu.notes); i++ {
			note := fnu.notes[i]
			if note == index {
				fnu.notes[i] = fmt.Sprintf(
					`["(#%s-%d). ^%d^":#%s-r%d]%s`,
					title, i, i, title, i, line[m[1]:])
				break
			}
		}
		if i == len(fnu.notes) {
			fmt.Fprintf(os.Stderr,
				"Only %d references or new notes parsed, "+
					"but expected more; look for malformed new "+
					"notes, or malformed or missing references "+
					"for existing footnotes\n", fnu.i)
			os.Exit(1)
		}
	} else if line == "</div>\n" {
		fnu.in_footnote_div = false
	}
	return line
}

// Prints out all new and reordered footnotes in the footnote div.
func (fnu *FootnoteUpdater) ParseLineSecondPass(
	line string, buf *bufio.Writer) string {
	if line == "<div class=\"footnote\">\n" {
		fnu.in_footnote_div = true
	} else if fnu.in_footnote_div {
		if line == "</div>\n" {
			if len(fnu.notes) > 1 {
				buf.WriteString(fnu.notes[1])
			}
			for _, n := range fnu.notes[2:len(fnu.notes)] {
				buf.WriteString(fmt.Sprintf("\n%s", n))
			}
			fnu.in_footnote_div = false
		} else {
			line = ""
		}
	}
	return line
}

// Returns a message describing the number of new footnotes, whether or not
// existing footnotes were reordered, or the empty string if nothing changed.
func (fnu *FootnoteUpdater) UpdateMessage() (msg string) {
	msg = ""
	if fnu.num_new_notes != 0 {
		plural := ""
		if fnu.num_new_notes != 1 {
			plural = "s"
		}
		msg = fmt.Sprintf("%d new footnote%s", fnu.num_new_notes,
			plural)
	}
	if !sort.IntsAreSorted(fnu.existing_order) {
		if len(msg) != 0 {
			msg += ", "
		}
		msg += "existing footnotes reordered"
	}
	return
}

// Parses the existing Table of Contents and all section headlines.
func (tocu *TableOfContentsUpdater) ParseLineFirstPass(
	line string, buf *bufio.Writer) string {
	if tocu.in_toc {
		if line == "\n" {
			tocu.in_toc = false
		} else {
			tocu.prev = append(tocu.prev, line)
		}
	} else if strings.HasPrefix(line, kTableOfContents) {
		tocu.in_toc = true
		// +1 for the space between TOC and the first headline
		first := line[len(kTableOfContents)+1:]
		if len(first) != 0 {
			tocu.prev = append(tocu.prev, first)
		}
	} else if m := kHeadline.FindStringSubmatchIndex(line); m != nil {
		id, text := line[m[2]:m[3]], line[m[4]:m[5]]
		text = kRef.ReplaceAllLiteralString(text, ``)
		text = kNewNote.ReplaceAllLiteralString(text, ``)
		text = kTextileLink.ReplaceAllString(text, `$1`)

		if m := kHeadlineError.FindStringIndex(text); m != nil {
			fmt.Fprintf(os.Stderr, "Malformed link or footnote "+
				"in section headline: %s\n", text)
			os.Exit(1)
		}
		tocu.curr = append(tocu.curr,
			fmt.Sprintf("\"%s\":#%s\n", text, id))
	}
	return line
}

// Produces an updated Table of Contents.
func (tocu *TableOfContentsUpdater) ParseLineSecondPass(
	line string, buf *bufio.Writer) string {
	if tocu.in_toc {
		if line == "\n" {
			tocu.in_toc = false
			for _, h := range tocu.curr[1:] {
				buf.WriteString(h)
			}
		} else {
			line = ``
		}
	} else if strings.HasPrefix(line, kTableOfContents) {
		tocu.in_toc = true
		if len(tocu.curr) != 0 {
			line = fmt.Sprintf("%s %s", kTableOfContents,
				tocu.curr[0])
		}
	}
	return line
}

// Returns a message describing the number of new/changed headlines, and
// whether any existing headlines were reordered. Returns the empty string if
// nothing changed.
func (tocu *TableOfContentsUpdater) UpdateMessage() (msg string) {
	msg = ""
	prev := algorithm.SortedCopyStrings(tocu.prev)
	curr := algorithm.SortedCopyStrings(tocu.curr)
	diff := algorithm.SetDifferenceStrings(curr, prev)
	if n := len(diff); n != 0 {
		plural := ""
		if n != 1 {
			plural = "s"
		}
		msg = fmt.Sprintf("%d new/changed headline%s", n, plural)
	}

	before := algorithm.ContainsStrings(tocu.prev, curr)
	after := algorithm.ContainsStrings(tocu.curr, prev)

	if !algorithm.ElementsEqualStrings(before, after) {
		if len(msg) != 0 {
			msg += ", "
		}
		msg += "existing headlines reordered"
	}
	return
}
