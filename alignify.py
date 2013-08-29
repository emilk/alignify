#!/usr/bin/python
#
# Last edited 2013-08-23
# Made by Emil Ernerfeldt (emil ernerfeldt at gmail dot com)
# https://github.com/emilk/alignify
# Feel free to use, abuse, modify, redistribute.
#
# Usage:  cat test.txt | python alignify_cli.py
# Or:     python alignify_cli.py test.txt
#
# Or import and use as a python module
#
# Or use in Sublime Text 3:
# { "keys": ["super+shift+a"], "command": "alignify" }


import re  # reg-ex

# Options

# If set, will ignore empty lines and will not break on 
g_continuous = True


# For debugging
def spam(*stuff):
	#print( 'SPAM: ' + ''.join(map(str,stuff)) )
	pass


def alignify_string(s):
	lines = s.split('\n')
	return alignify_lines( lines )


def alignify_lines(lines):
	# Split into blocks of same indentation:
	left  = []
	right = []
	last_indent = None
	last_line   = False

	output = ""

	for ix, line in enumerate(lines):
		spam("line: '", line, "'")

		m    = re.match("(\t*)(.*)", line)
		tabs = m.group(1)
		meat = m.group(2)

		#spam("tabs: '", tabs, "'")
		#spam("meat: '", meat, "'")

		# Replace non-leading tabs with spaces. Any number of spaces will work.
		meat = re.sub(r'\t', '  ', meat)

		if last_indent != None and tabs != last_indent:
			# A change in indentation
			if g_continuous and (line == '' or last_line == ''):
				# single empty line ok
				pass
			else:
				spam("alignify_lines: indentation break: '", tabs, "'")
				output += align_and_collect(left, right)
				left  = []
				right = []

		left.append( tabs )
		right.append( tokenize(meat) )
		last_indent = tabs
		last_line = line

	output += align_and_collect(left, right)

	if len(output) > 0 and output[-1] == '\n':
		output = output[0:-1]

	return output


def tokenize(s):
	'''
	Input: a single line
	A token is a continuing block of code with no quoted spaces
	'''
	tokens = []
	n = len(s)
	i = 0
	while i < n:
		# Skip spaces:
		while i < n and s[i] == ' ':
			i += 1

		start = i

		while i < n and s[i] != ' ':
			c = s[i]

			if c == "'" or c == '"':
				i += 1
				while i < n:
					if s[i] == '\\':
						i += 2
					elif s[i] == c:
						i += 1
						break
					else:
						i += 1
			elif c == '-' and s[i+1] == '-':
				# -- one line Lua comment
				i = n
			elif c == '/' and s[i+1] == '/':
				# // one line C++ comment
				i = n
			elif c == '#' and len(tokens) == 0:
				# # one line Python comment
				# We only support these on single line,
				# else we get confused by Lua # operator
				i = n
			else:
				i += 1

		tokens.append( s[start:i] )

	return tokens


NONE = False


def align_and_collect(left_in, right_in):
	'''
	'left_in' is indentation + already aligned text
	'right_in' is tokens

	This function will move one token from each line to the left, and call align on those lines
	'''
	assert( len(left_in) == len(right_in) )

	n = len(right_in)

	if n == 0:
		return ''

	spam("align_and_collect: ", n)

	left_out  = []
	right_out = []

	output = ''

	for i,tokens in enumerate(right_in):
		if g_continuous:
			# No breaks!
			if len(tokens) == 0:
				left_out.append( left_in[i] )
				right_out.append( [] )
			else:
				left_out.append( left_in[i] + tokens[0] )
				right_out.append( tokens[1:] )
		else:
			if len(tokens) > 1:
				left_out.append( left_in[i] + tokens[0] )
				right_out.append( tokens[1:] )
			else:
				output += align(left_out, right_out)
				left_out  = []
				right_out = []
				if len(tokens) == 0:
					output += left_in[i] + '\n'
				else:
					output += left_in[i] + tokens[0] + '\n'


	output += align(left_out, right_out)

	#spam("align_and_collect output: ", output)
	return output


def align(left, right):
	assert(len(left) == len(right))
	if len(left) == 0:
		return ''

	num_right_tokens = 0	
	for _,tokens in enumerate(right):
		if len(tokens) > 0:
			num_right_tokens += 1

	if num_right_tokens == 0:
		return "\n".join(left) + "\n"

	spam("align: ", len(left))

	# Find widest 'left'
	widest = -1
	for ix, txt in enumerate(left):
		tokens = right[ix]
		if len(tokens) > 0:
			widest = max(widest, len(txt))

	# Append padded tokens onto 'left' to produce 'new_left':
	new_left = []

	for ix, line in enumerate(left):
		tokens = right[ix]
		if len(tokens) > 0:
			while len(line) < widest + 1:
				line += ' '
		new_left.append( line )

	spam('new_left: ', new_left)

	return align_and_collect(new_left, right)


if __name__ == '__main__':
	# CLI

	import fileinput  # reads from stdin or from file given as argument
	import sys

	lines = []
	for line in fileinput.input():
		lines.append(line)

	aligned = alignify_lines(lines)
	#print( aligned )
	sys.stdout.write( aligned )  # no trailing newline


def module_exists(module_name):
	try:
		__import__(module_name)
	except ImportError:
		return False
	else:
		return True


if module_exists('sublime_plugin'):
	# ST3 plugin
	import sublime_plugin

	class AlignifyCommand(sublime_plugin.TextCommand):
		'''
		def __init__(self, view):
			super(AlignifyCommand, self).__init__(view)
		'''

		def run(self, edit):
			for region in self.view.sel():
				if not region.empty():
					region = self.view.line(region) # Extend selection to full lines
					s = self.view.substr(region)
					s = alignify_string(s)
					self.view.replace(edit, region, s)
