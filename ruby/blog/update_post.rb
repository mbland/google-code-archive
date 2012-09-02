#! /usr/local/bin/ruby
# Copyright 2012 Mike Bland. All rights reserved.
#
# Updates a textile blog post by expanding non-textile features.
#
# Makes some of the formatting I use in my blog that isn't baked into textile
# easier to maintain, particularly footnotes and tables of contents.
#
# Reads input from standard input and prints result to standard output. All
# updates are idempotent.

require 'stringio'

# Parses an existing footnote reference from the text.
# First group: note title; second group: note index
REF = /\["\(#([a-z-]+)-r([0-9]+)\)\. \^[0-9]+\^":#[a-z-]+-[0-9]+\]/

# Parses an existing footnote target from the text.
# Group: note title
TARGET = /^\["\(#([a-z-]+)-[0-9]+\)\. \^[0-9]+\^":#[a-z-]+-r[0-9]+\]/

# Parses a new footnote from the text.
# First group: note title; second group: note text
NEW_NOTE = /\[#([a-z-]+): ([^\]]+)\]/

# Start-of-line pattern indicating the presence of a Table of Contents.
TABLE_OF_CONTENTS = 'p(toc). '

# Pattern for parsing a headline.
# First group: headline ID; second group: headline text
HEADLINE = /^h3\(section#([a-zA-Z0-9-]+)\)\. (.+)$/


# Parses new notes and updates the footnote numbers in a textile blog post.
#
# Format
# ------
# Existing footnote references parsed from the format:
#
#   ["(#note-title-r1). ^1^":#note-title-1]
#
# where "note-title" is a prefix unique to a particular post used for all
# notes in a post (though this isn't strictly necessary or enforced) and "1"
# is any nonnegative integer.
#
# Existing footnote targets (where the footnote text appears) are parsed from
# the "footnote" div at the bottom of the page from the format:
#
#   ["(#note-title-1). ^1^":#note-title-r1]
#
# New notes are parsed from the format:
#
#   [#note-title: New footnote text here.]
#
# The new footnote text is automatically placed in the footnote div at the
# bottom of the page in the correct relative order. All footnote references
# are expanded in the correct order, starting from "1".
#
# Does not handle recursive footnotes.
#
# Why not use native Textile footnotes?
# -------------------------------------
# Since the front page of my blog has the three most recent posts, if more
# than one post contains footnotes, there will be multiple DOM elements
# with the same ID, which is typically frowned upon and may make navigation
# difficult. With a prefix unique to the particular post, collisions are
# avoided. If, for whatever reason, I or someone else decides to concatenate
# all of the HTML for multiple posts into a single document other than for the
# front page of the blog, the uniqueness of each ID is preserved.
#
# Plus, updating all the footnote references upon insertion of a new note is a
# pain, as is determining the proper position of a new footnote in the first
# place. Inserting the new note in-line and letting this script figure out
# where to place it and update all the references accordingly makes the task
# much less tedious.
class FootnoteUpdater
  def initialize
    # By the time the footnotes div is encountered, notes will contain the
    # empty string at all positions where a footnote already exists, and text
    # for all positions where new footnotes were parsed from the text.
    # Contains the empty string to start the footnote index at one when
    # writing out the footnotes div.
    @notes = ['']

    # Queue of new notes parsed from the text, used to make sure the elements
    # of notes are in order relative to any preexisting footnote references.
    @new_notes = []

    # Keeps track of the current footnote number.
    @i = 1

    @num_new_notes = 0
    @in_footnote_div = false
  end

  # Modifies line in place during the first pass through a file, and writes
  # extra output to buffer if necessary.
  #
  # line should not be written to buffer directly.
  def parse_line_first_pass(line, buffer)
    if line == "<div class=\"footnote\">\n"
      @in_footnote_div = true
      @i = 1
    end

    if not @in_footnote_div
      # First pass: Expand any new footnote references and capture their
      # text.
      start = 0
      while match = line.match(NEW_NOTE, start)
        title, note_text = match[1], match[2]
        # Use zeros as index placeholders until the next pass.
        replacement = "[\"(##{title}-r0). ^0^\":##{title}-0]"
        line.replace "#{match.pre_match}#{replacement}#{match.post_match}"
        start = match.pre_match.length + replacement.length
        @new_notes.push note_text
        @num_new_notes += 1
      end

      # Second pass: Update footnote numbers.
      start = 0
      while match = line.match(REF, start)
        title, index = match[1], match[2]
        replacement = "[\"(##{title}-r#{@i}). ^#{@i}^\":##{title}-#{@i}]"
        line.replace "#{match.pre_match}#{replacement}#{match.post_match}"
        start = match.pre_match.length + replacement.length
        @notes.push((index != '0') ? '' :
                    "[\"(##{title}-#{@i})\. ^#{@i}^\":##{title}-r#{@i}]" +
                    "#{@new_notes.shift}")
        @i += 1
      end

    elsif match = line.match(TARGET)
      ref, title = match[0], match[1]

      # Insert new notes before this preexisting one.
      while @i < @notes.size and not @notes[@i].empty?
        buffer.write "#{@notes[@i]}\n\n"
        @i += 1
      end

      # Error recovery: We shouldn't exhaust @notes unless a new note or
      # existing reference failed to parse.
      if @i == @notes.size
        $stderr.puts("Only #{@i - 1} references or new notes parsed, " +
                     "but expected more; look for malformed new notes, " +
                     "or malformed or missing references for existing " +
                     "footnotes\n")
        exit 1
      end

      line.sub!(ref, "[\"(##{title}-#{@i}). ^#{@i}^\":##{title}-r#{@i}]")
      @i += 1

    elsif line == "</div>\n" and @i < @notes.size
      # Insert remaining notes just before closing the div.
      @notes[@i..@notes.size].each {|note| buffer.write "\n#{note}\n"}
    end
  end

  # Modifies line in place during the second pass through a file, and writes
  # extra output to buffer if necessary.
  #
  # line should not be written to buffer directly.
  def parse_line_second_pass(line, buffer)
    # Nop
  end

  # Called after parsing is finished to provide a summary of changes made.
  # Returns nil if no changes were made.
  def update_message
    return @num_new_notes != 0 ? "#{@num_new_notes} new footnotes" : nil
  end
end


# Parses headlines from a textile blog post to build a new Table of Contents.
#
# Only supports one Table of Contents per blog post.
#
# Format
# ------
# If the first pass encounters a line starting with:
#
#   p(toc).
#
# then during the first pass headlines will be parsed from the format
#
#  h3(section#post-prefix-headline-suffix). Headline Text
#
# where "post-prefix" is a prefix unique to the specific page, to avoid
# collisions between multiple identical headlines on the same page when
# multiple posts are concatenated; and where "headline-suffix" is a suffix
# specific to the headline within the blog post.
#
# Also parses the following formats (assuming they fit on a single line):
#
#  h3(section#post-prefix-headline-is-link). "Headline Is
#    Link":http://www.example.com
#  h3(section#post-prefix-headline-with-link-embedded). Headline With
#    "Link":http://www.example.com Embedded
#  h3(section#post-prefix-headline-with-footnote). Headline With
#    Footnote["(#note-title-r1). ^1^":#note-title-1]
#  h3(section#post-prefix-headline-with-new-footnote). Headline With
#    New Footnote[#note-title: Brand new footnote text]
#  h3(section#post-prefix-headline-is-link-with-footnote). ["Headline Is
#    Link With Footnote":http://www.example.com]
#    ["(#note-title-r1). ^1^":#note-title-1]
#  h3(section#post-prefix-headline-with-link-embedded-with-footnote). Headline
#    With "Link":http://www.example.com Embedded With
#    Footnote["(#note-title-r1). ^1^":#note-title-1]
#
# The resulting Table of Contents from the above examples would look like:
#
#   p.(toc) "Headline Text":#post-prefix-headline-suffix
#   "Headline Is Link":#post-prefix-headline-is-link
#   "Headline With Link Embedded":#post-prefix-headline-with-link
#   "Headline With Footnote":#post-prefix-headline-with-footnote
#   "Headline With New Footnote":#post-prefix-headline-with-new footnote
#   "Headline Is Link With Footnote":
#     #post-prefix-headline-is-link-with-footnote
#   "Headline With Link Embedded With Footnote":
#     #post-prefix-headline-with-link-embedded-with-footnote
#
# During the second pass, a new Table of Contents paragraph is output in place
# of the existing one.
class TableOfContentsUpdater
  def initialize
    @in_toc = false
    @existing_headlines = []
    @headlines = []
  end

  # Modifies line in place during the first pass through a file, and writes
  # extra output to buffer if necessary.
  #
  # line should not be written to buffer directly.
  def parse_line_first_pass(line, buffer)
    if @in_toc
      if line == "\n"
        @in_toc = false
      else
        @existing_headlines.push line[0..-1]
      end
    elsif line.start_with? TABLE_OF_CONTENTS
      @in_toc = true
      first_headline = line[TABLE_OF_CONTENTS.length..-1]
      @existing_headlines.push first_headline if not first_headline.empty?
    elsif match = line.match(HEADLINE)
      id, text = match[1], match[2]
      text.gsub!(REF, '')
      text.gsub!(NEW_NOTE, '')
      text.gsub!(/\[?"([^"]+)":[^ ]+\]?/, '\1')

      # If quotation marks or brackets still appear, we're in trouble.
      if text.match(/["\[\]]/)
        $stderr.puts("Malformed link or footnote in section headline: " +
                     "#{text}\n")
        exit 1
      end
      @headlines.push "\"#{text}\":##{id}\n"
    end
  end

  # Modifies line in place during the second pass through a file, and writes
  # extra output to buffer if necessary.
  #
  # line should not be written to buffer directly.
  def parse_line_second_pass(line, buffer)
    if @in_toc
      if line == "\n"
        @in_toc = false
        if not @headlines.empty?
          @headlines[1..@headlines.length].each {|h| buffer.write "#{h}"}
        end
      else
        line.replace ''
      end
    elsif line.start_with? TABLE_OF_CONTENTS
      @in_toc = true
      if not @headlines.empty?  
        line.replace "#{TABLE_OF_CONTENTS}#{@headlines[0]}"
      end
    end
  end

  # Called after parsing is finished to provide a summary of changes made.
  # Returns nil if no changes were made.
  def update_message
    changes = @headlines - @existing_headlines
    result = changes.empty? ? '' : "#{changes.size} new/changed headlines"

    before = @existing_headlines & @headlines
    after = @headlines & @existing_headlines
    if before != after
      result += ', ' if not result.empty?
      result += 'existing headlines reordered'
    end
    return result.empty? ? nil : result
  end
end


# def main
if __FILE__ == $0
  if not ARGV.empty?
    $stderr.puts("This command takes no arguments")
    $stderr.puts("Usage: #{$0} < blog_post_file > output_file")
    exit 1
  end

  updaters = [FootnoteUpdater.new, TableOfContentsUpdater.new]
  first_pass_buffer = StringIO.new('')

  $stdin.each do |line|
    updaters.each {|u| u.parse_line_first_pass(line, first_pass_buffer)}
    first_pass_buffer.write line
  end

  # Write to a second pass buffer, since we don't want to print to standard
  # output if there were any errors.
  first_pass_buffer.rewind
  second_pass_buffer = StringIO.new('')

  first_pass_buffer.each do |line|
    updaters.each {|u| u.parse_line_second_pass(line, second_pass_buffer)}
    second_pass_buffer.write line
  end

  first_pass_buffer.close
  second_pass_buffer.rewind
  second_pass_buffer.each {|line| print line}
  second_pass_buffer.close
  updates = updaters.map{|u| u.update_message}.select{|m| m != nil}
  $stderr.puts "#{updates.join '; '}\n" if not updates.empty?
end
