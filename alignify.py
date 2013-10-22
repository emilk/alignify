#!/usr/bin/python
#
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
#
#
# Changelog:
# 2.0  - 2013-08-23
# 2.1  - 2013-10-20  -  Aligns numbers by decimal point
# 2.11 - 2013-10-21  -  Fixes for number alignment and g_continuous == False
# 2.12 - 2013-10-22  -  Fixed tokenizer bug
# 2.2  - 2013-10-22  -  Whitespace indentation compatibility


##########################################################################
# Global settings:

g_ignore_empty_lines = True
# Iff true, will continue aligning across empty lines.
# False is recommended for whole-file alignment (though that is not recommended per se).

g_continuous = True
'''
Iff true, will align 'foo' and 'bar' in:

one foo
two
three bar
'''

g_suffer_whitespace_indentation = True
'''
Allow whitespace indentation? The indentation width will be assumed to be an even number.
Even if you turn this on you can use alignify on code indented with tabs.

If true, algignify can be made to work with code that indents code using spaces.
Of course, you should never do such a thing. Spaces, as the name implies, is for spacing - not for indentation.
The only way to reliably tell indentation fro alignment is if one uses different characters for the two - hence the dogma:

	Indent with tabs, align with spaces  -  http://vim.wikia.com/wiki/Indent_with_tabs,_align_with_spaces

Still - sometimes you are forces to work on a project that uses the wrong indentation style.
You should of course conform to the coding guidelines, and hence, alignify has a compatibility mode.

Since space-indentation comes with an inherent ambiguity between what's indentation and what's alignment
enabling the compatibility mode may keep alignify from correctly aligning things like:

rgb = [
    255,
     0,
        0,
]

Of course, the ambiguity disappears with correctly indented code:

rgb = [
	255,
	 0,
	    0,
]

And for you with OCD, feast your eyes upon this:

rgb = [
	255,
	  0,
	  0,
]

Aaaah..........
'''

##########################################################################
# Actual code time!

import re  # Our one dependency - regular expressions


# For debugging
def spam(*stuff):
	#print( 'SPAM: ' + ''.join(map(str,stuff)) )
	pass


def alignify_string(s):
	lines = s.split('\n')
	return alignify_lines( lines )


def alignify_lines(lines):
	# Split into blocks of same indentation:
	left        = []
	right       = []
	last_indent = None
	last_line   = None

	output = ""

	for ix, line in enumerate(lines):
		spam("line: '", line, "'")

		if g_suffer_whitespace_indentation:
			# Try mathcing tabs first - if none, match spaces two and two
			m      = re.match("(\t+|(  )*)(.*)", line)
			indent = m.group(1)
			meat   = m.group(3)
		else:
			m      = re.match("(\t*)(.*)", line)
			indent = m.group(1)
			meat   = m.group(2)

		#spam("indent: '", indent, "'")
		#spam("meat:  '", meat, "'")

		# Replace non-leading tabs with spaces. Any number of spaces will work.
		meat = re.sub(r'\t', '  ', meat)
		tokens = tokenize(meat)

		if last_indent != None and indent != last_indent:
			# A change in indentation
			if g_ignore_empty_lines and (line == '' or last_line == ''):
				# Ignore empty line
				pass
			else:
				# A true change - align what we have so far:
				spam("alignify_lines: indentation break: '", indent, "'")
				output += align_and_collect(left, right)
				left  = []
				right = []

		left.append( indent )
		right.append( tokens )
		last_indent = indent
		last_line   = line

	output += align_and_collect(left, right)

	if output.endswith('\n'):
		output = output[0:-1]

	return output


def tokenize(s):
	'''
	Input: a single line
	A token is a continuing block of code with no unquoted spaces
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
			elif i+1 < n and c == '-' and s[i+1] == '-':
				# -- one line Lua comment
				i = n
			elif i+1 < n and c == '/' and s[i+1] == '/':
				# // one line C++ comment
				i = n
			elif i+1 < n and c == '#' and (s[i+1] == ' ' or len(tokens) == 0):
				# # one line Python comment
				# We only support these as the only token on a line, or with a space after.
				# Else we get confused by Lua # operator
				i = n
			else:
				i += 1

		tokens.append( s[start:i] )

	return tokens


def align_and_collect(left_in, right_in):
	'''
	'left_in' is indentation + already aligned text
	'right_in' is tokens

	This function will move one token from each line to the left, and call align on those lines
	'''
	assert( len(left_in) == len(right_in) )

	next_left   = []
	next_tokens = []
	next_right  = []

	output = ''

	for i,tokens in enumerate(right_in):
		if len(tokens) > 0:
			next_left.append( left_in[i] )
			next_tokens.append( tokens[0] )
			next_right.append( tokens[1:] )
		elif g_continuous:
			# No breaks!
			next_left.append( left_in[i] )
			next_tokens.append( None )
			next_right.append( [] )
		else:
			# Break on this line
			output += align(next_left, next_tokens, next_right)
			output += left_in[i] + '\n'
			next_left   = []
			next_tokens = []
			next_right  = []

	output += align(next_left, next_tokens, next_right)

	#spam("align_and_collect output: ", output)
	return output


RE_NUMBER = re.compile(r'^[+-]?\.?\d+.*$')  # any number followed by whatever (e.g. a comma)
RE_SIGN_OR_DIGIT = re.compile(r'^[\d+-]$')


def spaces(num):
	return num * ' '


def align(left, tokens, right):
	assert(len(left) == len(right) == len(tokens))
	n = len(left)
	if n == 0:
		return ''

	#######################################
	# Calculate target width:

	decimal_place         = [None] * n
	rightmost_decimal     = 0
	right_side_of_decimal = 0      # At most, how many characters right of a decimal point?
	align_width           = 0
	need_to_continue      = False

	for ix, token in enumerate(tokens):
		if token:
			need_to_continue = True
			more_to_come = (len(right[ix]) > 0)
			is_number = RE_NUMBER.match(token)

			if more_to_come or is_number:
				align_width = max(align_width, len(token) + 1)

			if is_number:
				decimal_place[ix] = 0
				for c in token:
					if RE_SIGN_OR_DIGIT.match(c):
						decimal_place[ix] += 1
					else:
						break
				spam("Number '%s' has decimal at %i" % (token, decimal_place[ix]))
				rightmost_decimal     = max(rightmost_decimal,     decimal_place[ix])
				right_side_of_decimal = max(right_side_of_decimal, 1 + len(token) - decimal_place[ix])

	align_width = max(align_width, rightmost_decimal + right_side_of_decimal)

	if not need_to_continue:
		return '\n'.join(left) + '\n'

	#######################################
	# Align tokens and move left:

	new_left = []

	for ix, token in enumerate(tokens):
		if token:
			if RE_NUMBER.match(token):
				# right-align:
				token = spaces(rightmost_decimal - decimal_place[ix]) + token

			more_to_come = (len(right[ix]) > 0)

			if more_to_come:
				token += spaces(align_width - len(token))

			new_left.append( left[ix] + token )
		else:
			new_left.append( left[ix] )

	return align_and_collect(new_left, right)


def print_help():
	print( "alignify.py [-t N] [file_name_1, ...]" )


def main(argv):
	'''
	CLI

	TODO:
   try:
		getopt.getopt(argv, "ht:", ["help"])
	except getopt.GetoptError:
		print_help()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print_help()
			sys.exit()
		elif opt in ("-t"):
			g_num_tabs = arg
	'''
	import fileinput  # reads from stdin or from file given as argument

	lines = []
	for line in fileinput.input():
		lines.append(line)

	aligned = alignify_lines(lines)
	#print( aligned )
	sys.stdout.write( aligned )  # no trailing newline


if __name__ == '__main__':
	import sys
   main(sys.argv[1:])  # Skip 'alignify.py' in argv


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
