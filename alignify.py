#!/usr/bin/python -O

# Made by Emil Ernerfeldt (emil ernerfeldt at gmail . com)
# https://github.com/emilk/alignify
# Feel free to use, abuse, modify, redistribute.
# If you like Alignify, send me a mail and tell me!
# Oh, and this is my first python script, so beware of ugly code =)

# Usage:  cat test.txt | python alignify.py
# Or:     python alignify.py test.txt


import fileinput  # reads from stdin or from file given as argument
import re         # reg-ex

# For debugging
def spam(*stuff):
	#print 'SPAM: ', ''.join(map(str,stuff))
	pass
	
def debug_output(*stuff):
	print ''.join(map(str,stuff))
	
def output(*stuff):
	print ''.join(map(str,stuff))

def main():	
	lines = [];	
	for line in fileinput.input():
		lines.append(line);

	split_indent(lines, "\\t", parse_section);
	

# indent_re is regex describing the indent ("\t" or "[ ]")
def split_indent(lines, indent_re, recursor):
	spam("split_indent: ", len(lines), " lines");
	regex = "(" + indent_re + "*)(.*)"  # doesn't work with  [ ]{4}
	spam("regex: ", regex)
	beg = []
	end = []
	last_indent  = ""
	
	for line in lines:
		spam("line: '", line, "'")
		
		m = re.match(regex, line)
		tabs = m.group(1)
		rest = m.group(2)
		
		spam("tabs: '", tabs, "'")
		spam("rest: '", rest, "'")
				
		# Replace non-leading tabs with spaces. Any number of spaces >=2 will work.
		# Three picked to be future proof for smart-align
		rest = re.sub(r'\t', '   ', rest)
	
		if len(beg)>0 and last_indent!=tabs:
			spam("new block (old tabs: ", len(last_indent), ", now: ", len(tabs), ")")
			recursor(beg, end)
			beg = []
			end = []
	
		if re.match(r".*\s\s+.*", line)==None:
			# This line will have no effect later - it is a section cutoff:
			# This helps us separate out code indented with spaces.
			#debug_output("/////// SOLO LINE: '", line, "'")
			recursor(beg, end)
			beg = [tabs]
			end = [rest]
			recursor(beg, end)
			beg = []
			end = []
			#debug_output("/////// SOLO LINE END")
			continue
			
		beg.append(tabs)
		end.append(rest)
		last_indent = tabs
		
	recursor(beg, end)
	return


# Heuristic: returns true if the given lines seems to be indented with spaces
def looks_spacy(lines):
	if len(lines)==1:
		return False;
	#debug_output("////// looks_spacy: ", len(lines))
	nDicy      = 0  # Number of dangerous/ambiguous lines
	nExactly4  = 0  # Number of lines with exactly 4 spaces
	n4Plus     = 0  # Number of lines with at least 4 spaces

	for line in lines:
		if len(line)==0 or line[0]!=' ':
			# line did not start with space - does this disqualify us from tab-indenting?
			# only if the line contains a block separator:
			if re.match(r".*\s\s+.*", line):
				nDicy += 1
		
		if re.match(r'[ ]{4}[^ ].*', line):
			nExactly4 += 1
			
		if re.match(r'[ ]{4}.*', line):
			n4Plus += 1
			
	spam("nDicy: ", nDicy, "nExactly4: ", nExactly4, "n4Plus: ", n4Plus);
	
	if nDicy == 0:
		return True  # Clear-cut - no risks
		
	N = len(lines)
	
	if N < 5:
		return False  # Too small sample size - be conservative
		
	if nExactly4 >= N/2:
		return True  # Good enough
		
	if n4Plus >= N*3/4:
		return True  # Good enough
	
	if nDicy < 2 & N > 5:
		return True  # Good enough

	return False;


def parse_section(indents, lines):
	assert len(indents)==len(lines)
	
	if len(indents)==0:
		return
		
	if len(indents[0]) > 0:
		# There are tabs - send to parsing
		return parse_block(indents, lines)
		
	if looks_spacy(lines):
		spam("spaceIndented");
		#return split_indent(lines, "[ ]{4}", parse_block)
		return split_indent(lines, " ", parse_block)
	else:
		return parse_block(indents, lines)
	

# Takes a number of lines all with the same indentation
def parse_block(indents, lines):
	assert len(indents)==len(lines)
	
	if len(lines)==0:
		return
	spam("parse_block: ", len(lines))
	# Break up each line into beginning, spacing, and end.
	begs    = []
	spaces  = []
	ends    = []
	for ix, line in enumerate(lines):
		m = re.match(r"(.*?)(\s\s+)(.*)", line)
		if m!=None:
			spam("MATCH")
			begs.append(indents[ix] + m.group(1))
			spaces.append(m.group(2))
			ends.append(m.group(3))
		else:
			# No spacing in this line - handle preceding lines and continue:
			spam("NO MATCH")
			handle_block(begs, spaces, ends)
			begs    = []
			spaces  = []
			ends    = []
			output(indents[ix], line)
	spam("LOOP END")
	handle_block(begs, spaces, ends)
	return


# Takes a number of lines split by the first spacing (two or more tabs)
def handle_block(begs, spaces, ends):
	if len(begs)==0:
		return
	spam("handle_block: ", len(begs))
	longest_beg = ""
	longest_spaces = ""
	for ix, b in enumerate(begs):
		if len(b) > len(longest_beg):
			longest_beg = b
			longest_spaces = spaces[ix]
	
	align = len(longest_beg) + len(longest_spaces)
	spam("align: ", align)
	
	new_begs   = []
	new_lines  = []
	
	for ix, beg in enumerate(begs):
		pad_len = (align - len(beg))
		pad = " " * pad_len
		spam("pad_len: ", pad_len)
		#output(begs[ix], pad, ends[ix])
		new_begs.append(begs[ix] + pad)
		new_lines.append(ends[ix])
	
	parse_block(new_begs, new_lines)
		
main();
