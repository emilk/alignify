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
	
	
def output(*stuff):
	print ''.join(map(str,stuff))


def main():
	indents  = []
	lines    = []
	indent   = ""
	
	for line in fileinput.input():
		spam("Read line: ", line)
		m = re.match(r"(\t*)(.*)", line)
		tabs = m.group(1)
		rest = m.group(2)
				
		# Replace non-leading tabs with spaces. Any number of spaces >=2 will work.
		# Three picked to b future proof for smart-align
		rest = re.sub(r'\t', '   ', rest);  
	
		if len(lines)>0 and indent!=tabs:
			spam("new block (old tabs: ", len(indent), ", now: ", len(tabs), ")")
			parse_block(indents, lines)
			indents  = []
			lines    = []
	
		spam("APPENDING")
		indents.append(tabs)
		lines.append(rest)
		indent = tabs
		
	parse_block(indents, lines)
	return


# Takes a number of lines all with the same indentation
def parse_block(indents, lines):
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
