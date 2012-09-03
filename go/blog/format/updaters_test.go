package format

import (
	"bufio"
	"bytes"
	msbtest "code.google.com/p/mike-bland/go/testing"
	"strings"
	"testing"
)

func checkUpdate(expected_msg, expected_result, original string,
	updaters []Updater, t *testing.T) {
	b := new(bytes.Buffer)
	output := bufio.NewWriter(b)
	msg := UpdatePost(updaters,
		bufio.NewReader(strings.NewReader(original)),
		output)
	output.Flush()
	result := b.String()

	if result != expected_result {
		t.Errorf("%s: updated blog text does not match "+
			"expectation:\nexpected:\n%s\n--------\nactual:\n%s",
			msbtest.FileAndLine(), expected_result, result)
	}
	if msg != expected_msg {
		t.Errorf("%s: blog update message does not match "+
			"expectation:\nexpected:\n%s\n--------\nactual:\n%s",
			msbtest.FileAndLine(), expected_msg, msg)
	}
}

func TestFootnoteUpdaterEmptyPost(t *testing.T) {
	checkUpdate("", "", "", []Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterNothingToUpdate(t *testing.T) {
	checkUpdate("",
		"nothing to update here\n",
		"nothing to update here\n",
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterExpandNewFootnote(t *testing.T) {
	const original = `A new footnote to expand.[#test-doc: New note.]

<div class="footnote">
</div>
`
	const expected = `A new footnote to expand.["(#test-doc-r1). ^1^":#test-doc-1]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]New note.
</div>
`
	checkUpdate("1 new footnote", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterNewNoteAfterExisting(t *testing.T) {
	const original = `Existing footnote.["(#test-doc-r1). ^1^":#test-doc-1] A new footnote to expand.[#test-doc: New note.]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]Existing note.
</div>
`
	const expected = `Existing footnote.["(#test-doc-r1). ^1^":#test-doc-1] A new footnote to expand.["(#test-doc-r2). ^2^":#test-doc-2]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]Existing note.

["(#test-doc-2). ^2^":#test-doc-r2]New note.
</div>
`
	checkUpdate("1 new footnote", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterNewNoteBeforeExisting(t *testing.T) {
	const original = `A new footnote to expand.[#test-doc: New note.] Existing footnote.["(#test-doc-r1). ^1^":#test-doc-1]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]Existing note.
</div>
`
	const expected = `A new footnote to expand.["(#test-doc-r1). ^1^":#test-doc-1] Existing footnote.["(#test-doc-r2). ^2^":#test-doc-2]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]New note.

["(#test-doc-2). ^2^":#test-doc-r2]Existing note.
</div>
`
	checkUpdate("1 new footnote", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterNewNoteBetweenExisting(t *testing.T) {
	const original = `Existing footnote.["(#test-doc-r1). ^1^":#test-doc-1] A new footnote to expand.[#test-doc: New note.] Existing footnote.["(#test-doc-r2). ^2^":#test-doc-2]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]First existing note.

["(#test-doc-2). ^2^":#test-doc-r2]Second existing note.
</div>
`
	const expected = `Existing footnote.["(#test-doc-r1). ^1^":#test-doc-1] A new footnote to expand.["(#test-doc-r2). ^2^":#test-doc-2] Existing footnote.["(#test-doc-r3). ^3^":#test-doc-3]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]First existing note.

["(#test-doc-2). ^2^":#test-doc-r2]New note.

["(#test-doc-3). ^3^":#test-doc-r3]Second existing note.
</div>
`
	checkUpdate("1 new footnote", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterExistingNoteBetweenNew(t *testing.T) {
	const original = `A new footnote to expand.[#test-doc: First new note.] Existing footnote.["(#test-doc-r1). ^1^":#test-doc-1] A new footnote to expand.[#test-doc: Second new note.] Existing footnote.["(#test-doc-r2). ^2^":#test-doc-2]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]First existing note.

["(#test-doc-2). ^2^":#test-doc-r2]Second existing note.
</div>
`
	const expected = `A new footnote to expand.["(#test-doc-r1). ^1^":#test-doc-1] Existing footnote.["(#test-doc-r2). ^2^":#test-doc-2] A new footnote to expand.["(#test-doc-r3). ^3^":#test-doc-3] Existing footnote.["(#test-doc-r4). ^4^":#test-doc-4]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]First new note.

["(#test-doc-2). ^2^":#test-doc-r2]First existing note.

["(#test-doc-3). ^3^":#test-doc-r3]Second new note.

["(#test-doc-4). ^4^":#test-doc-r4]Second existing note.
</div>
`
	checkUpdate("2 new footnotes", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterThreeNewNotesInARow(t *testing.T) {
	const original = `A new footnote to expand.[#test-doc: First new note.] A new footnote to expand.[#test-doc: Second new note.] A new footnote to expand.[#test-doc: Third new note.] Existing footnote.["(#test-doc-r1). ^1^":#test-doc-1]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]Existing note.
</div>
`
	const expected = `A new footnote to expand.["(#test-doc-r1). ^1^":#test-doc-1] A new footnote to expand.["(#test-doc-r2). ^2^":#test-doc-2] A new footnote to expand.["(#test-doc-r3). ^3^":#test-doc-3] Existing footnote.["(#test-doc-r4). ^4^":#test-doc-4]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]First new note.

["(#test-doc-2). ^2^":#test-doc-r2]Second new note.

["(#test-doc-3). ^3^":#test-doc-r3]Third new note.

["(#test-doc-4). ^4^":#test-doc-r4]Existing note.
</div>
`
	checkUpdate("3 new footnotes", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterReorderExistingFootnotes(t *testing.T) {
	const original = `These two footnotes have been reordered.["(#test-doc-r2). ^2^":#test-doc-2] This may happen during editing.["(#test-doc-r1). ^1^":#test-doc-1]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]Original first note.

["(#test-doc-2). ^2^":#test-doc-r2]Original second note.
</div>
`
	const expected = `These two footnotes have been reordered.["(#test-doc-r1). ^1^":#test-doc-1] This may happen during editing.["(#test-doc-r2). ^2^":#test-doc-2]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]Original second note.

["(#test-doc-2). ^2^":#test-doc-r2]Original first note.
</div>
`
	checkUpdate("existing footnotes reordered", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterReorderExistingFootnotesWithNewFootnotes(t *testing.T) {
	const original = `This is a new note.[#test-doc: First new note.] These two footnotes have been reordered.["(#test-doc-r2). ^2^":#test-doc-2] Here's another new note.[#test-doc: Second new note.] This may happen during editing.["(#test-doc-r1). ^1^":#test-doc-1] One more new note.[#test-doc: Third new note.]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]Original first note.

["(#test-doc-2). ^2^":#test-doc-r2]Original second note.
</div>
`
	const expected = `This is a new note.["(#test-doc-r1). ^1^":#test-doc-1] These two footnotes have been reordered.["(#test-doc-r2). ^2^":#test-doc-2] Here's another new note.["(#test-doc-r3). ^3^":#test-doc-3] This may happen during editing.["(#test-doc-r4). ^4^":#test-doc-4] One more new note.["(#test-doc-r5). ^5^":#test-doc-5]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]First new note.

["(#test-doc-2). ^2^":#test-doc-r2]Original second note.

["(#test-doc-3). ^3^":#test-doc-r3]Second new note.

["(#test-doc-4). ^4^":#test-doc-r4]Original first note.

["(#test-doc-5). ^5^":#test-doc-r5]Third new note.
</div>
`
	checkUpdate("3 new footnotes, existing footnotes reordered", expected, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterTenExistingFootnotesNoChange(t *testing.T) {
	// This makes sure that the order of existing footnotes is not
	// misreported as having changed, since ["1", ..., "10"] will be
	// reported as unsorted.
	const original = `First.["(#test-doc-r1). ^1^":#test-doc-1] Second.["(#test-doc-r2). ^2^":#test-doc-2] Third.["(#test-doc-r3). ^3^":#test-doc-3]

Fourth.["(#test-doc-r4). ^4^":#test-doc-4] Fifth.["(#test-doc-r5). ^5^":#test-doc-5] Sixth.["(#test-doc-r6). ^6^":#test-doc-6]

Seventh.["(#test-doc-r7). ^7^":#test-doc-7] Eighth.["(#test-doc-r8). ^8^":#test-doc-8] Ninth.["(#test-doc-r9). ^9^":#test-doc-9]

Tenth.["(#test-doc-r10). ^10^":#test-doc-10]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]First note.

["(#test-doc-2). ^2^":#test-doc-r2]Second note.

["(#test-doc-3). ^3^":#test-doc-r3]Third note.

["(#test-doc-4). ^4^":#test-doc-r4]Fourth note.

["(#test-doc-5). ^5^":#test-doc-r5]Fifth note.

["(#test-doc-6). ^6^":#test-doc-r6]Sixth note.

["(#test-doc-7). ^7^":#test-doc-r7]Seventh note.

["(#test-doc-8). ^8^":#test-doc-r8]Eighth note.

["(#test-doc-9). ^9^":#test-doc-r9]Ninth note.

["(#test-doc-10). ^10^":#test-doc-r10]Tenth note.
</div>
`
	checkUpdate("", original, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestFootnoteUpdaterExtraParagraphsInAnExistingFootnoteArePreserved(t *testing.T) {
	const original = `This existing reference's text should be preserved.["(#test-doc-r1). ^1^":#test-doc-1]

<div class="footnote">
["(#test-doc-1). ^1^":#test-doc-r1]This is the first line of the first note.

Shouldn't matter how many lines it has.

bq.. Even if it appears as a blockquote or something.

A multiple line blockquote.

p. They should all be preserved.
</div>
`
	checkUpdate("", original, original,
		[]Updater{NewFootnoteUpdater()}, t)
}

func TestTableOfContentsUpdaterEmptyPost(t *testing.T) {
	checkUpdate("", "", "", []Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterNothingToUpdate(t *testing.T) {
	checkUpdate("",
		"nothing to update here\n",
		"nothing to update here\n",
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterFirstNewHeadline(t *testing.T) {
	const original = `p(toc).

h3(section#test-doc-first). First Headline
`
	const expected = `p(toc). "First Headline":#test-doc-first

h3(section#test-doc-first). First Headline
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterChangeExistingHeadlines(t *testing.T) {
	const original = `p(toc). "Old Headline":#test-doc-old

h3(section#test-doc-new). New Headline
`
	const expected = `p(toc). "New Headline":#test-doc-new

h3(section#test-doc-new). New Headline
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterReorderExistingHeadlines(t *testing.T) {
	const original = `p(toc). "Headline C":#test-doc-c
"Headline A":#test-doc-a
"Headline B":#test-doc-b

h3(section#test-doc-a). Headline A

h3(section#test-doc-b). Headline B

h3(section#test-doc-c). Headline C
`
	const expected = `p(toc). "Headline A":#test-doc-a
"Headline B":#test-doc-b
"Headline C":#test-doc-c

h3(section#test-doc-a). Headline A

h3(section#test-doc-b). Headline B

h3(section#test-doc-c). Headline C
`
	checkUpdate("existing headlines reordered", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterHeadlineIsLink(t *testing.T) {
	const original = `p(toc).

h3(section#test-doc-headline-is-link). "Headline Is Link":http://www.example.com/
`
	const expected = `p(toc). "Headline Is Link":#test-doc-headline-is-link

h3(section#test-doc-headline-is-link). "Headline Is Link":http://www.example.com/
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterHeadlineWithLinkEmbedded(t *testing.T) {
	const original = `p(toc).

h3(section#test-doc-headline-with-link-embedded). Headline With "Link":http://www.example.com/ Embedded
`
	const expected = `p(toc). "Headline With Link Embedded":#test-doc-headline-with-link-embedded

h3(section#test-doc-headline-with-link-embedded). Headline With "Link":http://www.example.com/ Embedded
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterHeadlineWithFootnote(t *testing.T) {
	const original = `p(toc).

h3(section#test-doc-headline-with-footnote). Headline With Footnote["(#test-doc-r1). ^1^":#test-doc-1]
`
	const expected = `p(toc). "Headline With Footnote":#test-doc-headline-with-footnote

h3(section#test-doc-headline-with-footnote). Headline With Footnote["(#test-doc-r1). ^1^":#test-doc-1]
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterHeadlineWithNewFootnote(t *testing.T) {
	const original = `p(toc).

h3(section#test-doc-headline-with-new-footnote). Headline With New Footnote[#test-doc: It shouldn't matter which order the parsers are run in for this to work]
`
	const expected = `p(toc). "Headline With New Footnote":#test-doc-headline-with-new-footnote

h3(section#test-doc-headline-with-new-footnote). Headline With New Footnote[#test-doc: It shouldn't matter which order the parsers are run in for this to work]
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterHeadlineIsLinkWithFootnote(t *testing.T) {
	const original = `p(toc).

h3(section#test-doc-headline-is-link-with-footnote). ["Headline Is Link With Footnote":http://www.example.com/][#test-doc: New note.]
`
	const expected = `p(toc). "Headline Is Link With Footnote":#test-doc-headline-is-link-with-footnote

h3(section#test-doc-headline-is-link-with-footnote). ["Headline Is Link With Footnote":http://www.example.com/][#test-doc: New note.]
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

func TestTableOfContentsUpdaterHeadlineWithLinkEmbeddedWithFootnote(
	t *testing.T) {
	const original = `p(toc).

h3(section#test-doc-headline-with-link-embedded-with-footnote). Headline With ["Link":http://www.example.com/] Embedded With Footnote[#test-doc: Brackets around link for extra security, and parsing drama.]
`
	const expected = `p(toc). "Headline With Link Embedded With Footnote":#test-doc-headline-with-link-embedded-with-footnote

h3(section#test-doc-headline-with-link-embedded-with-footnote). Headline With ["Link":http://www.example.com/] Embedded With Footnote[#test-doc: Brackets around link for extra security, and parsing drama.]
`
	checkUpdate("1 new/changed headline", expected, original,
		[]Updater{new(TableOfContentsUpdater)}, t)
}

// TODO(msb): golden file test
