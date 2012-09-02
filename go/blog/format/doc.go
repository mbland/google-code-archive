// Copyright 2012 Mike Bland. All rights reserved.

// Functions and classes for updating Textile sources for mike-bland.com.
package format

import "bufio"

// Interface for classes which apply Textile blog post transformations. All
// Updater transformations must be idempotent.
type Updater interface {
	// Modifies line in place during the first pass through a file, and
	// writes extra output to buf if necessary.
	//
	// line should not be written to buf directly.
	ParseLineFirstPass(line string, buf *bufio.Writer) string

	// Modifies line in place during the second pass through a file, and
	// writes extra output to buf if necessary.
	//
	// line should not be written to buf directly.
	ParseLineSecondPass(line string, buf *bufio.Writer) string

	// Called after parsing is finished to provide a summary of changes
	// made. Returns the empty string if no changes were made.
	UpdateMessage() string
}

/*
   Parses new footnotes and updates the existing footnote numbers in a textile
   blog post. Should be allocated using NewFootnoteUpdater().

   FORMAT:

   Existing footnote references parsed from the format:

     ["(#note-title-r1). ^1^":#note-title-1]

   where "note-title" is a prefix unique to a particular post used for all
   notes in a post (though this isn't strictly necessary or enforced) and "1"
   is any nonnegative integer.

   Existing footnote targets (where the footnote text appears) are parsed from
   the "footnote" div at the bottom of the page from the format:

     ["(#note-title-1). ^1^":#note-title-r1]

   New notes are parsed from the format:

     [#note-title: New footnote text here.]

   The new footnote text is automatically placed in the footnote div at the
   bottom of the page in the correct relative order. All footnote references
   are expanded in the correct order, starting from "1".

   Does not handle recursive footnotes.

   WHY NOT USE NATIVE TEXTILE FOOTNOTES?

   Since the front page of my blog has the three most recent posts, if more
   than one post contains footnotes, there will be multiple DOM elements with
   the same ID, which is typically frowned upon and may make navigation
   difficult. With a prefix unique to the particular post, collisions are
   avoided. If, for whatever reason, I or someone else decides to concatenate
   all of the HTML for multiple posts into a single document other than for
   the front page of the blog, the uniqueness of each ID is preserved.

   Plus, updating all the footnote references upon insertion of a new note is
   a pain, as is determining the proper position of a new footnote in the
   first place. Inserting the new note in-line and letting this script figure
   out where to place it and update all the references accordingly makes the
   task much less tedious.
*/
type FootnoteUpdater struct {
	// By the time the footnotes div is encountered, notes will contain
	// the empty string at all positions where a footnote already exists,
	// and text for all positions where new footnotes were parsed from the
	// text.
	notes           []string

	// Queue of new notes parsed from the text, used to make sure the
	// elements of notes are in order relative to any preexisting footnote
	// references.
	new_notes       []string

	// Keeps track of the current footnote number
	i               int

	num_new_notes   int
	in_footnote_div bool
}

// Returns a properly-initialized FootnoteUpdater.
func NewFootnoteUpdater() *FootnoteUpdater {
	// notes contains the empty string as its first element to start the
	// footnote index at one when writing out the footnotes div.
	return &FootnoteUpdater{
		notes:           make([]string, 1),
		new_notes:       make([]string, 0),
		i:               1,
		num_new_notes:   0,
		in_footnote_div: false}
}

/*
   Parses headlines from a textile blog post to build a new Table of Contents.
   Will reorder existing headlines if a section is moved.

   Only supports one Table of Contents per blog post.

   FORMAT:

   If the first pass encounters a line starting with:

     p(toc).

   then during the first pass headlines will be parsed from the format

    h3(section#post-prefix-headline-suffix). Headline Text

   where "post-prefix" is a prefix unique to the specific page, to avoid
   collisions between multiple identical headlines on the same page when
   multiple posts are concatenated; and where "headline-suffix" is a suffix
   specific to the headline within the blog post.

   Also parses the following formats:

    h3(section#post-prefix-headline-is-link). "Headline Is Link":http://www.example.com
    h3(section#post-prefix-headline-with-link-embedded). Headline With "Link":http://www.example.com Embedded
    h3(section#post-prefix-headline-with-footnote). Headline With Footnote["(#note-title-r1). ^1^":#note-title-1]
    h3(section#post-prefix-headline-with-new-footnote). Headline With New Footnote[#note-title: Brand new footnote text]
    h3(section#post-prefix-headline-is-link-with-footnote). ["Headline Is Link With Footnote":http://www.example.com] ["(#note-title-r1). ^1^":#note-title-1]
    h3(section#post-prefix-headline-with-link-embedded-with-footnote). Headline With "Link":http://www.example.com Embedded With Footnote["(#note-title-r1). ^1^":#note-title-1]

   The resulting Table of Contents from the above examples would look like:

     p.(toc) "Headline Text":#post-prefix-headline-suffix
     "Headline Is Link":#post-prefix-headline-is-link
     "Headline With Link Embedded":#post-prefix-headline-with-link
     "Headline With Footnote":#post-prefix-headline-with-footnote
     "Headline With New Footnote":#post-prefix-headline-with-new footnote
     "Headline Is Link With Footnote":#post-prefix-headline-is-link-with-footnote
     "Headline With Link Embedded With Footnote":#post-prefix-headline-with-link-embedded-with-footnote

   During the second pass, a new Table of Contents paragraph is output in
   place of the existing one.
*/
type TableOfContentsUpdater struct {
	in_toc bool
	prev   []string
	curr   []string
}
