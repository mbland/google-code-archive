// Copyright 2012 Mike Bland. All rights reserved.

package format

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"code.google.com/p/mike-bland/go/algorithm"
	"os"
	"regexp"
	"strings"
)

var (
	// Matches an existing footnote reference from the text.
	// First group: note title; second group: note index
	REF = regexp.MustCompile(
		`\["\(#([a-z-]+)-r([0-9]+)\)\. \^[0-9]+\^":#[a-z-]+-[0-9]+\]`)

	// Matches an existing footnote target from the text.
	// Group: note title
	TARGET = regexp.MustCompile(
		`^\["\(#([a-z-]+)-[0-9]+\)\. \^[0-9]+\^":#[a-z-]+-r[0-9]+\]`)

	// Matches a new footnote from the text.
	// First group: note title; second group: note text
	NEW_NOTE = regexp.MustCompile(`\[#([a-z-]+): ([^\]]+)\]`)

	// Matches a section headline.
	// First group: headline ID; second group: headline text
	HEADLINE = regexp.MustCompile(`^h3\(section#([a-zA-Z0-9-]+)\)\. (.+)`)

	// Matches a Textile-style link.
	// Group: link text
	TEXTILE_LINK = regexp.MustCompile(`\[?"([^"]+)":[^ ]+\]?`)

	// Matches Textile link characters after a headline has been
	// processed.
	HEADLINE_ERROR = regexp.MustCompile(`["\[\]]`)
)

const (
	// Start-of-line pattern indicating the presence of a Table of
	// Contents.
	TABLE_OF_CONTENTS = `p(toc).`
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

// Expands new footnotes and adjusts existing footnote references. Rewrites
// the footnote section to contain all footnotes in the correct order.
func (fnu *FootnoteUpdater) ParseLineFirstPass(
	line string, buf *bufio.Writer) string {
	if line == "<div class=\"footnote\">\n" {
		fnu.in_footnote_div = true
		fnu.i = 1
	}

	if !fnu.in_footnote_div {
		for m := NEW_NOTE.FindStringSubmatchIndex(line); m != nil; m = NEW_NOTE.FindStringSubmatchIndex(line) {
			title, text := line[m[2]:m[3]], line[m[4]:m[5]]
			line = fmt.Sprintf("%s[\"(#%s-r0). ^0^\":#%s-0]%s",
				line[:m[0]], title, title, line[m[1]:])
			fnu.new_notes = append(fnu.new_notes, text)
			fnu.num_new_notes++
		}

		for i, m := 0, REF.FindStringSubmatchIndex(line); m != nil; m = REF.FindStringSubmatchIndex(line[i:]) {
			title, n := line[m[2]+i:m[3]+i], line[m[4]+i:m[5]+i]
			ref := fmt.Sprintf(`["(#%s-r%d). ^%d^":#%s-%d]`,
				title, fnu.i, fnu.i, title, fnu.i)
			line = fmt.Sprintf(`%s%s%s`, line[:m[0]+i], ref,
				line[m[1]+i:])
			i += m[0] + len(ref)

			note := ""
			if n == "0" {
				note = fmt.Sprintf(
					`["(#%s-%d). ^%d^":#%s-r%d]%s`,
					title, fnu.i, fnu.i, title, fnu.i,
					fnu.new_notes[0])
				fnu.new_notes = fnu.new_notes[1:]
			}
			fnu.notes = append(fnu.notes, note)
			fnu.i++
		}
	} else if match := TARGET.FindStringSubmatchIndex(line); match != nil {
		for fnu.i < len(fnu.notes) && len(fnu.notes[fnu.i]) != 0 {
			buf.WriteString(fnu.notes[fnu.i])
			buf.WriteString("\n\n")
			fnu.i++
		}

		if fnu.i == len(fnu.notes) {
			fmt.Fprintf(os.Stderr,
				"Only %d references or new notes parsed, "+
					"but expected more; look for malformed new "+
					"notes, or malformed or missing references "+
					"for existing footnotes\n", fnu.i)
			os.Exit(1)
		}

		title := line[match[2]:match[3]]
		line = fmt.Sprintf(`["(#%s-%d). ^%d^":#%s-r%d]%s`,
			title, fnu.i, fnu.i, title, fnu.i, line[match[1]:])
		fnu.i++

	} else if line == "</div>\n" && fnu.i < len(fnu.notes) {
		for _, n := range fnu.notes[fnu.i:] {
			buf.WriteString(fmt.Sprintf("\n%s\n", n))
		}
	}
	return line
}

// Nop, as all processing is done in ParseLineFirstPass().
func (fnu *FootnoteUpdater) ParseLineSecondPass(
	line string, buf *bufio.Writer) string {
	return line
}

// Returns a message describing the number of new footnotes, or the empty
// string if no new footnotes were processed.
func (fnu *FootnoteUpdater) UpdateMessage() string {
	if fnu.num_new_notes != 0 {
		plural := ""
		if fnu.num_new_notes != 1 {
			plural = "s"
		}
		return fmt.Sprintf("%d new footnote%s", fnu.num_new_notes,
			plural)
	}
	return ""
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
	} else if strings.HasPrefix(line, TABLE_OF_CONTENTS) {
		tocu.in_toc = true
		// +1 for the space between TOC and the first headline
		first := line[len(TABLE_OF_CONTENTS)+1:]
		if len(first) != 0 {
			tocu.prev = append(tocu.prev, first)
		}
	} else if match := HEADLINE.FindStringSubmatchIndex(line); match != nil {
		id := line[match[2]:match[3]]
		text := line[match[4]:match[5]]
		text = REF.ReplaceAllLiteralString(text, ``)
		text = NEW_NOTE.ReplaceAllLiteralString(text, ``)
		text = TEXTILE_LINK.ReplaceAllString(text, `$1`)

		if match := HEADLINE_ERROR.FindStringIndex(text); match != nil {
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
	} else if strings.HasPrefix(line, TABLE_OF_CONTENTS) {
		tocu.in_toc = true
		if len(tocu.curr) != 0 {
			line = fmt.Sprintf("%s %s", TABLE_OF_CONTENTS,
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
